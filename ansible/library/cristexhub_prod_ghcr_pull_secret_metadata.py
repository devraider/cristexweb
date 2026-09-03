#!/usr/bin/python3
"""Read only the metadata of the CristexHub PROD GHCR pull Secret.

The request negotiates PartialObjectMetadata and rejects every response that is
not the exact metadata representation.  The module never requests, returns, or
parses Secret data; the InfisicalStaticSecret source declaration is the sole
source of the type/key contract.
"""
from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

_PARTIAL_API_VERSION = "meta.k8s.io/v1"
_PARTIAL_KIND = "PartialObjectMetadata"
_ALLOWED_TOP_LEVEL = {"apiVersion", "kind", "metadata"}
_ALLOWED_METADATA = {
    "annotations",
    "creationTimestamp",
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
    "uid",
}


def _status(exc):
    value = getattr(getattr(exc, "status", None), "value", None)
    return value if value is not None else getattr(exc, "status", None)


def _call(api_client, namespace, name):
    return api_client.call_api(
        "/api/v1/namespaces/{namespace}/secrets/{name}",
        "GET",
        path_params={"namespace": namespace, "name": name},
        query_params=[],
        header_params={
            "Accept": "application/json;as=PartialObjectMetadata;g=meta.k8s.io;v=v1"
        },
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


def main():
    module = AnsibleModule(
        argument_spec={
            "kubeconfig": {"type": "path", "required": True},
            "namespace": {"type": "str", "required": True},
            "name": {"type": "str", "required": True},
        },
        supports_check_mode=True,
    )
    try:
        from kubernetes import client, config
    except ImportError as exc:  # pragma: no cover - host-only dependency
        module.fail_json(msg="GHCR_METADATA_GUARD: Kubernetes client unavailable")
    try:
        config.load_kube_config(config_file=module.params["kubeconfig"])
        payload = _call(
            client.ApiClient(), module.params["namespace"], module.params["name"]
        )
    except Exception as exc:  # pragma: no cover - host-only API path
        status = _status(exc)
        module.fail_json(
            msg="GHCR_METADATA_GUARD: metadata request failed with sanitized status %s"
            % (status if status is not None else "unknown")
        )

    if not isinstance(payload, dict) or set(payload) != _ALLOWED_TOP_LEVEL:
        module.fail_json(msg="GHCR_METADATA_GUARD: non-metadata response refused")
    if payload.get("apiVersion") != _PARTIAL_API_VERSION or payload.get("kind") != _PARTIAL_KIND:
        module.fail_json(msg="GHCR_METADATA_GUARD: partial metadata representation required")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or not set(metadata).issubset(_ALLOWED_METADATA):
        module.fail_json(msg="GHCR_METADATA_GUARD: unexpected metadata response shape")
    if metadata.get("name") != module.params["name"] or metadata.get("namespace") != module.params["namespace"]:
        module.fail_json(msg="GHCR_METADATA_GUARD: target identity changed during read")
    if not isinstance(metadata.get("uid"), str) or not metadata["uid"]:
        module.fail_json(msg="GHCR_METADATA_GUARD: target UID missing")
    if not isinstance(metadata.get("resourceVersion"), str) or not metadata["resourceVersion"]:
        module.fail_json(msg="GHCR_METADATA_GUARD: target resourceVersion missing")
    if "data" in payload or "stringData" in payload or "type" in payload:
        module.fail_json(msg="GHCR_METADATA_GUARD: Secret data representation refused")
    module.exit_json(
        changed=False,
        metadata_only=True,
        metadata={
            "apiVersion": payload["apiVersion"],
            "kind": payload["kind"],
            "name": metadata["name"],
            "namespace": metadata["namespace"],
            "uid": metadata["uid"],
            "resourceVersion": metadata["resourceVersion"],
            "labels": metadata.get("labels") or {},
            "annotations": metadata.get("annotations") or {},
            "ownerReferences": metadata.get("ownerReferences") or [],
            "deletionTimestamp": metadata.get("deletionTimestamp"),
        },
    )


if __name__ == "__main__":
    main()
