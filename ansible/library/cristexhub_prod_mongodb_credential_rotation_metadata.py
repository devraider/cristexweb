#!/usr/bin/python3
"""Read Kubernetes metadata, and optionally a non-secret CR spec, without Secret data."""
from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

_PARTIAL_METADATA_API_VERSION = "meta.k8s.io/v1"
_PARTIAL_METADATA_KIND = "PartialObjectMetadata"
_PARTIAL_METADATA_ACCEPT = (
    "application/json;as=PartialObjectMetadata;g=meta.k8s.io;v=v1"
)
_FULL_OBJECT_ACCEPT = "application/json"
_ALLOWED_TOP_LEVEL_KEYS = {"apiVersion", "kind", "metadata"}
_ALLOWED_SPEC_TOP_LEVEL_KEYS = {"apiVersion", "kind", "metadata", "spec", "status"}
_ALLOWED_METADATA_KEYS = {
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
}
_ALLOWED_OWNER_REFERENCE_KEYS = {
    "apiVersion",
    "blockOwnerDeletion",
    "controller",
    "kind",
    "name",
    "uid",
}


def _metadata(payload: object) -> dict[str, object] | None:
    """Validate and safely project Kubernetes object metadata."""
    if not isinstance(payload, dict) or not set(payload).issuperset(_ALLOWED_TOP_LEVEL_KEYS):
        return None
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or not set(metadata).issubset(_ALLOWED_METADATA_KEYS):
        return None
    required = ("name", "namespace", "uid", "resourceVersion")
    if any(not isinstance(metadata.get(key), str) or not metadata[key] for key in required):
        return None
    labels = metadata.get("labels", {})
    annotations = metadata.get("annotations", {})
    owner_references = metadata.get("ownerReferences", [])
    deletion_timestamp = metadata.get("deletionTimestamp")
    if not isinstance(labels, dict) or not isinstance(annotations, dict):
        return None
    if not isinstance(owner_references, list):
        return None
    if deletion_timestamp is not None and not isinstance(deletion_timestamp, str):
        return None
    if any(not isinstance(key, str) or not key for key in labels):
        return None
    if any(not isinstance(key, str) or not key for key in annotations):
        return None
    if any(not isinstance(value, str) for value in labels.values()):
        return None
    if any(not isinstance(value, str) for value in annotations.values()):
        return None
    # Never return managedFields or any unrequested response member.  The
    # caller receives only identity, labels, annotations, ownerReferences,
    # UID, resourceVersion, deletion state, and an explicitly requested CR spec.
    projected_owner_references: list[dict[str, object]] = []
    for reference in owner_references:
        if not isinstance(reference, dict) or not set(reference).issubset(_ALLOWED_OWNER_REFERENCE_KEYS):
            return None
        if any(
            not isinstance(reference.get(key), str) or not reference[key]
            for key in ("apiVersion", "kind", "name", "uid")
        ):
            return None
        for key in ("controller", "blockOwnerDeletion"):
            if key in reference and not isinstance(reference[key], bool):
                return None
        projected_owner_references.append(dict(reference))
    return {
        "name": metadata["name"],
        "namespace": metadata["namespace"],
        "uid": metadata["uid"],
        "resourceVersion": metadata["resourceVersion"],
        "deletionTimestamp": deletion_timestamp,
        "labels": dict(labels),
        "annotations": dict(annotations),
        "ownerReferences": projected_owner_references,
    }


def _response_shape_valid(
    payload: object,
    resource_kind: str,
    resource_api_version: str,
    include_spec: bool,
) -> bool:
    if not isinstance(payload, dict):
        return False
    if include_spec:
        if set(payload) - _ALLOWED_SPEC_TOP_LEVEL_KEYS:
            return False
        return (
            payload.get("apiVersion") == resource_api_version
            and payload.get("kind") == resource_kind
            and isinstance(payload.get("spec"), dict)
            and "data" not in payload
            and "stringData" not in payload
        )
    return (
        set(payload) == _ALLOWED_TOP_LEVEL_KEYS
        and payload.get("apiVersion") == _PARTIAL_METADATA_API_VERSION
        and payload.get("kind") == _PARTIAL_METADATA_KIND
    )


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "kubeconfig": {"type": "path", "required": True},
            "api_path": {"type": "str", "required": True},
            "resource_kind": {"type": "str", "required": True},
            "resource_api_version": {"type": "str", "required": True},
            "expected_name": {"type": "str", "required": True},
            "expected_namespace": {"type": "str", "required": True},
            "include_spec": {"type": "bool", "default": False},
        },
        supports_check_mode=True,
    )
    api_path = module.params["api_path"]
    resource_kind = module.params["resource_kind"]
    include_spec = module.params["include_spec"]
    if not api_path.startswith("/") or "?" in api_path or "#" in api_path:
        module.fail_json(msg="ROTATION_METADATA_GUARD: invalid fixed API path")
    if resource_kind == "Secret" and include_spec:
        module.fail_json(msg="ROTATION_METADATA_GUARD: Secret specs are forbidden")
    try:
        from kubernetes import client, config

        config.load_kube_config(config_file=module.params["kubeconfig"])
        payload = client.ApiClient().call_api(
            api_path,
            "GET",
            path_params={},
            query_params=[],
            header_params={"Accept": _FULL_OBJECT_ACCEPT if include_spec else _PARTIAL_METADATA_ACCEPT},
            body=None,
            post_params=[],
            files={},
            response_type="object",
            auth_settings=["BearerToken"],
            async_req=False,
            _return_http_data_only=True,
            _preload_content=True,
            _request_timeout=30,
        )
    except Exception as exc:  # pragma: no cover - remote API path
        module.fail_json(
            msg="ROTATION_METADATA_GUARD: metadata request failed (%s)"
            % type(exc).__name__
        )
    if not _response_shape_valid(payload, resource_kind, module.params["resource_api_version"], include_spec):
        module.fail_json(msg="ROTATION_METADATA_GUARD: exact response identity or shape required")
    result = _metadata(payload)
    if result is None:
        module.fail_json(msg="ROTATION_METADATA_GUARD: invalid metadata response")
    if result["name"] != module.params["expected_name"] or result["namespace"] != module.params["expected_namespace"]:
        module.fail_json(msg="ROTATION_METADATA_GUARD: response identity mismatch")
    module.exit_json(
        changed=False,
        metadata=result,
        spec=payload.get("spec", {}) if include_spec else {},
        resource_kind=resource_kind,
        resource_api_version=module.params["resource_api_version"],
        metadata_only=not include_spec,
        spec_only=include_spec,
    )


if __name__ == "__main__":
    main()
