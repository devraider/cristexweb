#!/usr/bin/python3
"""Fetch Kubernetes Secret metadata without negotiating a full Secret object."""

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


_ALLOWED_TOP_LEVEL = {"apiVersion", "kind", "metadata"}


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "kubeconfig": {"type": "path", "required": True},
            "namespace": {"type": "str", "required": True},
            "name": {"type": "str", "required": True},
            "kind": {"type": "str", "default": "Secret", "choices": ["Secret", "ConfigMap"]},
        },
        supports_check_mode=True,
    )
    try:
        from kubernetes import client, config

        config.load_kube_config(config_file=module.params["kubeconfig"])
        resource = "secrets" if module.params["kind"] == "Secret" else "configmaps"
        payload = client.ApiClient().call_api(
            f"/api/v1/namespaces/{{namespace}}/{resource}/{{name}}",
            "GET",
            path_params={
                "namespace": module.params["namespace"],
                "name": module.params["name"],
            },
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
        if not isinstance(payload, dict) or payload.get("kind") != "PartialObjectMetadata":
            module.fail_json(msg="SECRET_METADATA_GUARD: metadata-only response required")
        if set(payload) != _ALLOWED_TOP_LEVEL:
            module.fail_json(msg="SECRET_METADATA_GUARD: response contained non-metadata fields")
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            module.fail_json(msg="SECRET_METADATA_GUARD: malformed metadata response")
        module.exit_json(
            changed=False,
            found=True,
            metadata={
                "name": metadata.get("name"),
                "namespace": metadata.get("namespace"),
                "labels": metadata.get("labels") or {},
                "uid": metadata.get("uid"),
                "resourceVersion": metadata.get("resourceVersion"),
            },
        )
    except Exception as exc:  # pragma: no cover - remote API path
        if getattr(exc, "status", None) == 404:
            module.exit_json(changed=False, found=False, metadata={})
        module.fail_json(msg=f"RESOURCE_METADATA_GUARD: metadata request failed ({type(exc).__name__})")


if __name__ == "__main__":
    main()
