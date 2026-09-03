#!/usr/bin/python3
"""Read one Kubernetes object's metadata without requesting Secret data."""
from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

_PARTIAL_METADATA_API_VERSION = "meta.k8s.io/v1"
_PARTIAL_METADATA_KIND = "PartialObjectMetadata"
_PARTIAL_METADATA_ACCEPT = (
    "application/json;as=PartialObjectMetadata;g=meta.k8s.io;v=v1"
)
_ALLOWED_TOP_LEVEL_KEYS = {"apiVersion", "kind", "metadata"}
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


def _metadata(payload: object) -> dict[str, object] | None:
    """Validate the negotiated partial response and return a safe projection."""
    if not isinstance(payload, dict) or set(payload) != _ALLOWED_TOP_LEVEL_KEYS:
        return None
    if (
        payload.get("apiVersion") != _PARTIAL_METADATA_API_VERSION
        or payload.get("kind") != _PARTIAL_METADATA_KIND
    ):
        return None
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or not set(metadata).issubset(_ALLOWED_METADATA_KEYS):
        return None
    required = ("name", "namespace", "uid", "resourceVersion")
    if any(not isinstance(metadata.get(key), str) or not metadata[key] for key in required):
        return None
    labels = metadata.get("labels", {})
    annotations = metadata.get("annotations", {})
    if not isinstance(labels, dict) or not isinstance(annotations, dict):
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
    # caller needs only identity, labels, annotations, UID, and resourceVersion.
    return {
        "name": metadata["name"],
        "namespace": metadata["namespace"],
        "uid": metadata["uid"],
        "resourceVersion": metadata["resourceVersion"],
        "labels": dict(labels),
        "annotations": dict(annotations),
    }


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "kubeconfig": {"type": "path", "required": True},
            "api_path": {"type": "str", "required": True},
            "resource_kind": {"type": "str", "required": True},
            "resource_api_version": {"type": "str", "required": True},
        },
        supports_check_mode=True,
    )
    api_path = module.params["api_path"]
    resource_kind = module.params["resource_kind"]
    if not api_path.startswith("/") or "?" in api_path or "#" in api_path:
        module.fail_json(msg="ROTATION_METADATA_GUARD: invalid fixed API path")
    try:
        from kubernetes import client, config

        config.load_kube_config(config_file=module.params["kubeconfig"])
        payload = client.ApiClient().call_api(
            api_path,
            "GET",
            path_params={},
            query_params=[],
            header_params={"Accept": _PARTIAL_METADATA_ACCEPT},
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
    result = _metadata(payload)
    if result is None:
        module.fail_json(msg="ROTATION_METADATA_GUARD: partial metadata response required")
    # Secret requests are accepted only as PartialObjectMetadata.  This check
    # is intentionally based on the caller's fixed kind, never on response data.
    if resource_kind == "Secret" and "data" in payload:
        module.fail_json(msg="ROTATION_METADATA_GUARD: Secret data was returned")
    module.exit_json(
        changed=False,
        metadata=result,
        resource_kind=resource_kind,
        resource_api_version=module.params["resource_api_version"],
        metadata_only=True,
    )


if __name__ == "__main__":
    main()
