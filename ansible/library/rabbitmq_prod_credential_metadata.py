#!/usr/bin/python3
"""Read only RabbitMQ-related Secret metadata without requesting Secret data."""
from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

_TOP_LEVEL = {"apiVersion", "kind", "metadata"}
_METADATA_ALLOWED = {
    "name",
    "namespace",
    "uid",
    "resourceVersion",
    "labels",
}


def _metadata(client: object, namespace: str, name: str) -> dict:
    payload = client.call_api(
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
        collection_formats={},
        _preload_content=True,
        _request_timeout=30,
    )
    if not isinstance(payload, dict) or set(payload) != _TOP_LEVEL:
        raise ValueError("metadata-only Secret response required")
    if payload.get("apiVersion") != "meta.k8s.io/v1" or payload.get("kind") != "PartialObjectMetadata":
        raise ValueError("malformed metadata-only Secret response")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or not set(metadata).issubset(_METADATA_ALLOWED):
        raise ValueError("Secret payload or unsupported metadata returned")
    labels = metadata.get("labels", {})
    if not isinstance(labels, dict):
        raise ValueError("malformed Secret labels")
    required = ("name", "namespace", "uid", "resourceVersion")
    if any(not isinstance(metadata.get(key), str) or not metadata[key] for key in required):
        raise ValueError("incomplete Secret metadata")
    return {
        "apiVersion": payload["apiVersion"],
        "kind": payload["kind"],
        "metadata": {
            "name": metadata["name"],
            "namespace": metadata["namespace"],
            "uid": metadata["uid"],
            "resourceVersion": metadata["resourceVersion"],
            "labels": labels,
        },
    }


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "kubeconfig": {"type": "path", "required": True},
            "resources": {
                "type": "list",
                "elements": "dict",
                "required": True,
                "options": {
                    "namespace": {"type": "str", "required": True},
                    "name": {"type": "str", "required": True},
                },
            },
        },
        supports_check_mode=True,
    )
    try:
        from kubernetes import client, config

        config.load_kube_config(config_file=module.params["kubeconfig"])
        api = client.ApiClient()
        items = []
        for resource in module.params["resources"]:
            items.append(_metadata(api, resource["namespace"], resource["name"]))
        module.exit_json(changed=False, items=items, metadata_only=True)
    except Exception as exc:  # pragma: no cover - provider path
        module.fail_json(msg=f"SECRET_METADATA_GUARD: {type(exc).__name__}")


if __name__ == "__main__":
    main()
