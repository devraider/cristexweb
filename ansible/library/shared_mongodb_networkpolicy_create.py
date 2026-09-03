#!/usr/bin/python3
"""Create one NetworkPolicy only when the named object is still absent.

This focused module deliberately performs a GET followed by a POST and never
updates an existing object.  A concurrent creator therefore produces a
conflict/fail-closed result instead of being silently reconciled.
"""

from __future__ import annotations

import re

from ansible.module_utils.basic import AnsibleModule


def _resource_dict(resource):
    if hasattr(resource, "to_dict"):
        return resource.to_dict()
    if isinstance(resource, dict):
        return resource
    return {}


def main():
    module = AnsibleModule(
        argument_spec={
            "api_version": {"type": "str", "required": True},
            "kind": {"type": "str", "required": True},
            "namespace": {"type": "str", "required": True},
            "name": {"type": "str", "required": True},
            "kubeconfig": {"type": "str", "required": True},
            "definition": {"type": "dict", "required": True},
        },
        supports_check_mode=True,
    )
    params = module.params
    definition = params["definition"]
    if (
        params["api_version"] != "networking.k8s.io/v1"
        or params["kind"] != "NetworkPolicy"
        or params["namespace"] != "shared-services"
        or params["name"] != definition.get("metadata", {}).get("name")
        or definition.get("metadata", {}).get("namespace") != "shared-services"
    ):
        module.fail_json(msg="CREATE_ONLY_GUARD: unexpected NetworkPolicy identity")
    if module.check_mode:
        module.exit_json(changed=True, method="create", check_mode=True)
    try:
        from kubernetes import client, config
        from kubernetes.client.rest import ApiException
        from kubernetes.dynamic import DynamicClient

        config.load_kube_config(config_file=params["kubeconfig"])
        dynamic = DynamicClient(client.ApiClient())
        resource = dynamic.resources.get(
            api_version=params["api_version"], kind=params["kind"]
        )
        try:
            existing = resource.get(
                name=params["name"], namespace=params["namespace"]
            )
        except ApiException as exc:
            if exc.status != 404:
                module.fail_json(msg="CREATE_ONLY_GUARD: pre-create GET failed")
        else:
            existing_metadata = _resource_dict(existing).get("metadata", {})
            module.fail_json(
                msg="CREATE_ONLY_CONFLICT: NetworkPolicy appeared before create",
                conflict=True,
                existing_uid=existing_metadata.get("uid", ""),
                existing_resource_version=existing_metadata.get("resourceVersion", ""),
            )
        try:
            created = resource.create(
                body=definition,
                namespace=params["namespace"],
            )
        except ApiException as exc:
            if exc.status == 409:
                module.fail_json(
                    msg="CREATE_ONLY_CONFLICT: concurrent NetworkPolicy creator",
                    conflict=True,
                )
            module.fail_json(msg="CREATE_ONLY_GUARD: NetworkPolicy create failed")
        result = _resource_dict(created)
        metadata = result.get("metadata", {})
        if (
            metadata.get("name") != params["name"]
            or metadata.get("namespace") != params["namespace"]
            or not isinstance(metadata.get("uid"), str)
            or not metadata.get("uid")
            or not isinstance(metadata.get("resourceVersion"), str)
            or not re.fullmatch(r"[0-9]+", metadata.get("resourceVersion", ""))
        ):
            module.fail_json(msg="CREATE_ONLY_GUARD: create response identity incomplete")
        module.exit_json(
            changed=True,
            method="create",
            resource=result,
            created_uid=metadata["uid"],
            created_resource_version=metadata["resourceVersion"],
        )
    except ImportError:
        module.fail_json(msg="CREATE_ONLY_GUARD: Kubernetes client unavailable")


if __name__ == "__main__":
    main()
