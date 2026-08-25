#!/usr/bin/python
"""Read Kubernetes PartialObjectMetadata without requesting object data."""

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


_PARTIAL_METADATA_ACCEPT = (
    "application/json;as=PartialObjectMetadata;g=meta.k8s.io;v=v1"
)
_NOT_FOUND = {404, 410}


def _metadata(value):
    if not isinstance(value, dict):
        return None
    metadata = value.get("metadata")
    if not isinstance(metadata, dict):
        return None
    # Explicitly copy only metadata fields.  The module never returns the API
    # body, which prevents Secret data/stringData from entering Ansible facts.
    return {
        key: metadata[key]
        for key in (
            "name",
            "namespace",
            "labels",
            "annotations",
            "ownerReferences",
            "finalizers",
            "deletionTimestamp",
            "deletionGracePeriodSeconds",
            "managedFields",
            "uid",
            "resourceVersion",
            "generation",
            "creationTimestamp",
        )
        if key in metadata
    }


def main():
    module = AnsibleModule(
        argument_spec={
            "kubeconfig": {"type": "path", "required": True},
            "api_path": {"type": "str", "required": True},
        },
        supports_check_mode=True,
    )
    try:
        from kubernetes import client, config
    except ImportError as exc:
        module.fail_json(msg="METADATA_API: kubernetes client dependency unavailable: %s" % exc)

    try:
        config.load_kube_config(config_file=module.params["kubeconfig"])
        api_client = client.ApiClient()
        value = api_client.call_api(
            module.params["api_path"],
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
        )
    except Exception as exc:  # pragma: no cover - exercised on the host
        status = getattr(getattr(exc, "status", None), "value", None)
        if status is None:
            status = getattr(exc, "status", None)
        if status in _NOT_FOUND:
            module.exit_json(changed=False, found=False, api_available=False, metadata={})
        module.fail_json(msg="METADATA_API: metadata-only request failed: %s" % exc)

    metadata = _metadata(value)
    if metadata is None:
        module.exit_json(changed=False, found=False, api_available=True, metadata={})
    module.exit_json(changed=False, found=True, api_available=True, metadata=metadata)


if __name__ == "__main__":
    main()
