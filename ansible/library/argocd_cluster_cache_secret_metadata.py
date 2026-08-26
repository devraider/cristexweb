#!/usr/bin/python3
"""List Argo cluster Secret metadata without requesting Secret values."""
from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

_ALLOWED_TOP_LEVEL = {"apiVersion", "kind", "metadata", "items"}
_ALLOWED_ITEM_TOP_LEVEL = {"apiVersion", "kind", "metadata"}


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "kubeconfig": {"type": "path", "required": True},
            "namespace": {"type": "str", "required": True},
            "label_selector": {"type": "str", "required": True},
        },
        supports_check_mode=True,
    )
    try:
        from kubernetes import client, config

        config.load_kube_config(config_file=module.params["kubeconfig"])
        payload = client.ApiClient().call_api(
            "/api/v1/namespaces/{namespace}/secrets",
            "GET",
            path_params={"namespace": module.params["namespace"]},
            query_params=[("labelSelector", module.params["label_selector"])],
            header_params={
                "Accept": "application/json;as=PartialObjectMetadataList;g=meta.k8s.io;v=v1"
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
        if not isinstance(payload, dict) or set(payload) != _ALLOWED_TOP_LEVEL:
            module.fail_json(msg="SECRET_METADATA_GUARD: metadata-only list response required")
        if payload.get("kind") != "PartialObjectMetadataList" or not isinstance(payload.get("items"), list):
            module.fail_json(msg="SECRET_METADATA_GUARD: malformed metadata list response")
        items = []
        for item in payload["items"]:
            if not isinstance(item, dict) or set(item) != _ALLOWED_ITEM_TOP_LEVEL:
                module.fail_json(msg="SECRET_METADATA_GUARD: list item contained Secret data")
            metadata = item.get("metadata")
            if not isinstance(metadata, dict):
                module.fail_json(msg="SECRET_METADATA_GUARD: malformed Secret metadata")
            items.append(
                {
                    "apiVersion": item.get("apiVersion"),
                    "kind": item.get("kind"),
                    "metadata": {
                        "name": metadata.get("name"),
                        "namespace": metadata.get("namespace"),
                        "labels": metadata.get("labels") or {},
                        "uid": metadata.get("uid"),
                        "resourceVersion": metadata.get("resourceVersion"),
                    },
                }
            )
        module.exit_json(changed=False, items=items, metadata_only=True)
    except Exception as exc:  # pragma: no cover - remote API path
        module.fail_json(msg=f"RESOURCE_METADATA_GUARD: metadata request failed ({type(exc).__name__})")


if __name__ == "__main__":
    main()
