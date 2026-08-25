#!/usr/bin/python
"""Read Kubernetes metadata without requesting Secret objects or values.

Object requests negotiate PartialObjectMetadata. Collection requests use the
separate PartialObjectMetadataList representation required by the Kubernetes
API. Producer collections are inventoried with partial metadata first, then
only the non-Secret producer CRs are fetched to inspect their target references;
no Secret endpoint is ever requested with a full-object representation.
"""

from __future__ import annotations

from urllib.parse import quote

from ansible.module_utils.basic import AnsibleModule


_PARTIAL_METADATA_API_VERSION = "meta.k8s.io/v1"
_PARTIAL_METADATA_KIND = "PartialObjectMetadata"
_PARTIAL_METADATA_LIST_KIND = "PartialObjectMetadataList"
_PARTIAL_METADATA_ACCEPT = (
    "application/json;as=PartialObjectMetadata;g=meta.k8s.io;v=v1"
)
_PARTIAL_METADATA_LIST_ACCEPT = (
    "application/json;as=PartialObjectMetadataList;g=meta.k8s.io;v=v1"
)
_PARTIAL_METADATA_TOP_LEVEL_KEYS = {"apiVersion", "kind", "metadata"}
_PARTIAL_METADATA_LIST_TOP_LEVEL_KEYS = {"apiVersion", "kind", "metadata", "items"}
_PARTIAL_METADATA_LIST_METADATA_KEYS = {
    "continue",
    "remainingItemCount",
    "resourceVersion",
}
_PARTIAL_METADATA_METADATA_KEYS = {
    "annotations",
    "clusterName",
    "creationTimestamp",
    "deletionGracePeriodSeconds",
    "deletionTimestamp",
    "finalizers",
    "generateName",
    "generation",
    "labels",
    "managedFields",
    "name",
    "namespace",
    "ownerReferences",
    "resourceVersion",
    "selfLink",
    "uid",
    "continue",
    "remainingItemCount",
}
_NOT_FOUND = {404, 410}
_REQUIRED_MANAGED_FIELD_KEYS = {
    "manager",
    "operation",
    "apiVersion",
    "fieldsType",
    "fieldsV1",
}
_ALLOWED_MANAGED_FIELD_KEYS = _REQUIRED_MANAGED_FIELD_KEYS | {"time", "subresource"}


def _fields_v1(value, root=True):
    if not isinstance(value, dict) or (root and not value):
        return False
    for key, child in value.items():
        if not isinstance(key, str) or not key:
            return False
        if key != "." and not key.startswith(("f:", "k:", "v:")):
            return False
        if isinstance(child, dict):
            if not _fields_v1(child, root=False):
                return False
        elif child is not None:
            return False
    return True


def _managed_fields(value):
    if not isinstance(value, list) or not value:
        return False
    for entry in value:
        if not isinstance(entry, dict):
            return False
        if not _REQUIRED_MANAGED_FIELD_KEYS.issubset(entry) or not set(entry).issubset(_ALLOWED_MANAGED_FIELD_KEYS):
            return False
        if not isinstance(entry["manager"], str) or not entry["manager"]:
            return False
        if entry["operation"] not in {"Apply", "Update"}:
            return False
        if not isinstance(entry["apiVersion"], str) or not entry["apiVersion"]:
            return False
        if entry["fieldsType"] != "FieldsV1" or not _fields_v1(entry["fieldsV1"]):
            return False
        if "subresource" in entry and entry["subresource"] not in (None, ""):
            return False
    return True


def _metadata(value):
    """Return metadata only after proving an exact partial-object response."""
    if not isinstance(value, dict) or set(value) != _PARTIAL_METADATA_TOP_LEVEL_KEYS:
        return None
    if (
        value.get("apiVersion") != _PARTIAL_METADATA_API_VERSION
        or value.get("kind") != _PARTIAL_METADATA_KIND
    ):
        return None
    metadata = value.get("metadata")
    if not isinstance(metadata, dict) or not set(metadata).issubset(_PARTIAL_METADATA_METADATA_KEYS):
        return None
    if "managedFields" in metadata and not _managed_fields(metadata["managedFields"]):
        return None
    return {
        key: metadata[key]
        for key in _PARTIAL_METADATA_METADATA_KEYS
        if key in metadata
    }


def _empty_partial_metadata_list(metadata):
    """Accept only Kubernetes' exact null-items representation of an empty list."""
    if not isinstance(metadata, dict):
        return False
    # k3s can serialize an empty collection as items:null.  A continuation token
    # or positive remaining count would make that ambiguous and is rejected.
    return (
        metadata.get("continue", "") in ("", None)
        and metadata.get("remainingItemCount") in (None, 0)
    )


def _metadata_list(value):
    """Return metadata for every item in an exact partial-metadata list."""
    if not isinstance(value, dict) or set(value) != _PARTIAL_METADATA_LIST_TOP_LEVEL_KEYS:
        return None
    if (
        value.get("apiVersion") != _PARTIAL_METADATA_API_VERSION
        or value.get("kind") != _PARTIAL_METADATA_LIST_KIND
        or not isinstance(value.get("metadata"), dict)
        or not set(value["metadata"]).issubset(_PARTIAL_METADATA_LIST_METADATA_KEYS)
    ):
        return None
    if not _empty_partial_metadata_list(value["metadata"]):
        return None
    raw_items = value.get("items")
    if raw_items is None:
        raw_items = []
    if not isinstance(raw_items, list):
        return None
    items = []
    for item in raw_items:
        metadata = _metadata(item)
        if metadata is None:
            return None
        items.append(metadata)
    return items


def _status(exc):
    value = getattr(getattr(exc, "status", None), "value", None)
    return value if value is not None else getattr(exc, "status", None)


def _call(api_client, path, accept):
    return api_client.call_api(
        path,
        "GET",
        path_params={},
        query_params=[],
        header_params={"Accept": accept},
        body=None,
        post_params=[],
        files={},
        response_type="object",
        auth_settings=["BearerToken"],
        async_req=False,
        _return_http_data_only=True,
        _preload_content=True,
    )


def _producer_targets(value, expected_kind, expected_api_version, expected_metadata):
    """Extract only target identities from a non-Secret producer CR."""
    if not isinstance(value, dict):
        return None
    if value.get("kind") != expected_kind or value.get("apiVersion") != expected_api_version:
        return None
    metadata = value.get("metadata")
    if not isinstance(metadata, dict):
        return None
    if (
        metadata.get("name") != expected_metadata.get("name")
        or metadata.get("namespace") != expected_metadata.get("namespace")
        or not isinstance(expected_metadata.get("uid"), str)
        or not expected_metadata.get("uid")
        or metadata.get("uid") != expected_metadata.get("uid")
        or not isinstance(expected_metadata.get("resourceVersion"), str)
        or not expected_metadata.get("resourceVersion")
        or metadata.get("resourceVersion") != expected_metadata.get("resourceVersion")
    ):
        return None
    spec = value.get("spec")
    if not isinstance(spec, dict):
        return None
    raw_targets = []
    if expected_kind == "InfisicalStaticSecret":
        raw_targets = spec.get("targets")
        if not isinstance(raw_targets, list):
            return None
        normalized = []
        for target in raw_targets:
            if not isinstance(target, dict):
                return None
            normalized.append(target)
    elif expected_kind == "InfisicalSecret":
        raw_targets = []
        for target in spec.get("managedKubeSecretReferences", []):
            if not isinstance(target, dict):
                return None
            raw_targets.append(target)
        target = spec.get("managedSecretReference")
        if target is not None:
            if not isinstance(target, dict):
                return None
            raw_targets.append(target)
        if not raw_targets:
            return None
        normalized = [
            {
                "name": target.get("secretName"),
                "namespace": target.get("secretNamespace"),
                "kind": "Secret",
            }
            for target in raw_targets
        ]
    elif expected_kind == "InfisicalPushSecret":
        push = spec.get("push", {})
        if not isinstance(push, dict):
            return None
        normalized = []
        secret = push.get("secret")
        if secret is not None:
            if not isinstance(secret, dict):
                return None
            normalized.append({
                "name": secret.get("secretName"),
                "namespace": secret.get("secretNamespace"),
                "kind": "Secret",
            })
        generators = push.get("generators", [])
        if not isinstance(generators, list):
            return None
        generator_targets = [
            {
                "name": generator.get("destinationSecretName"),
                "namespace": metadata.get("namespace"),
                "kind": "Secret",
            }
            for generator in generators
            if isinstance(generator, dict)
        ]
        if len(generator_targets) != len(generators):
            return None
        normalized.extend(generator_targets)
        if not normalized:
            return None
    elif expected_kind == "InfisicalDynamicSecret":
        target = spec.get("managedSecretReference")
        if target is None:
            return None
        if isinstance(target, dict):
            normalized = [{
                "name": target.get("secretName"),
                "namespace": target.get("secretNamespace"),
                "kind": "Secret",
            }]
        else:
            return None
    elif expected_kind == "ExternalSecret":
        target = spec.get("target", {})
        if not isinstance(target, dict):
            return None
        normalized = [{
            "name": target.get("name", metadata.get("name")),
            "namespace": metadata.get("namespace"),
            "kind": "Secret",
        }]
    elif expected_kind == "SealedSecret":
        template = spec.get("template", {})
        if not isinstance(template, dict):
            return None
        template_metadata = template.get("metadata", {})
        if not isinstance(template_metadata, dict):
            return None
        normalized = [{
            "name": template_metadata.get("name", metadata.get("name")),
            "namespace": template_metadata.get("namespace", metadata.get("namespace")),
            "kind": "Secret",
        }]
    elif expected_kind == "SecretProviderClass":
        raw_targets = spec.get("secretObjects", [])
        if not isinstance(raw_targets, list):
            return None
        normalized = [
            {
                "name": target.get("secretName"),
                "namespace": metadata.get("namespace"),
                "kind": "Secret",
            }
            for target in raw_targets
            if isinstance(target, dict)
        ]
        if len(normalized) != len(raw_targets):
            return None
    else:
        return None
    sanitized = []
    for target in normalized:
        # Do not return templates, values, status, or any other producer body.
        if not isinstance(target, dict) or not all(
            key in target for key in ("name", "namespace", "kind")
        ):
            return None
        if not all(
            isinstance(target[key], str) and target[key]
            for key in ("name", "namespace", "kind")
        ):
            return None
        sanitized.append({
            "name": target["name"],
            "namespace": target["namespace"],
            "kind": target["kind"],
        })
    return sanitized


def main():
    module = AnsibleModule(
        argument_spec={
            "kubeconfig": {"type": "path", "required": True},
            "api_path": {"type": "str", "required": True},
            "collection": {"type": "bool", "default": False},
            "resource_kind": {"type": "str", "required": False, "default": ""},
            "resource_api_version": {"type": "str", "required": False, "default": ""},
        },
        supports_check_mode=True,
    )
    try:
        from kubernetes import client, config
    except ImportError as exc:
        module.fail_json(msg="METADATA_API: kubernetes client dependency unavailable: %s" % exc)

    if module.params["collection"] and module.params["resource_kind"] == "Secret":
        module.fail_json(
            msg="METADATA_API: refusing collection target inspection for Secret resources"
        )

    try:
        config.load_kube_config(config_file=module.params["kubeconfig"])
        api_client = client.ApiClient()
        collection = module.params["collection"]
        value = _call(
            api_client,
            module.params["api_path"],
            _PARTIAL_METADATA_LIST_ACCEPT if collection else _PARTIAL_METADATA_ACCEPT,
        )
    except Exception as exc:  # pragma: no cover - exercised on the host
        status = _status(exc)
        if status in _NOT_FOUND:
            module.exit_json(changed=False, found=False, api_available=False, metadata={})
        module.fail_json(
            msg="METADATA_API: metadata-only request failed with sanitized status %s"
            % (status if status is not None else "unknown")
        )

    if collection:
        metadata_list = _metadata_list(value)
        if metadata_list is None:
            module.fail_json(
                msg=(
                    "METADATA_API: response was not the exact meta.k8s.io/v1 "
                    "PartialObjectMetadataList closure"
                )
            )
        targets = []
        try:
            for metadata in metadata_list:
                if not module.params["resource_kind"] or not module.params["resource_api_version"]:
                    module.fail_json(msg="METADATA_API: producer kind and apiVersion are required")
                path = module.params["api_path"].rstrip("/") + "/" + quote(metadata["name"], safe="")
                producer = _call(api_client, path, "application/json")
                producer_targets = _producer_targets(
                    producer,
                    module.params["resource_kind"],
                    module.params["resource_api_version"],
                    metadata,
                )
                if producer_targets is None:
                    module.fail_json(msg="METADATA_API: producer response closure failed")
                targets.extend(producer_targets)
        except Exception as exc:  # pragma: no cover - exercised on the host
            status = _status(exc)
            if status in _NOT_FOUND:
                module.fail_json(msg="METADATA_API: producer disappeared during inventory")
            if isinstance(exc, SystemExit):
                raise
            module.fail_json(
                msg="METADATA_API: producer target inspection failed with sanitized status %s"
                % (status if status is not None else "unknown")
            )
        module.exit_json(
            changed=False,
            found=bool(metadata_list),
            api_available=True,
            metadata={"items": metadata_list},
            targets=targets,
        )

    metadata = _metadata(value)
    if metadata is None:
        module.fail_json(
            msg=(
                "METADATA_API: response was not the exact "
                "meta.k8s.io/v1 PartialObjectMetadata closure"
            )
        )
    module.exit_json(changed=False, found=True, api_available=True, metadata=metadata)


if __name__ == "__main__":
    main()
