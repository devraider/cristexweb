#!/usr/bin/python3
"""Read only RabbitMQ-related Secret metadata without requesting Secret data."""
from __future__ import annotations

import copy

from ansible.module_utils.basic import AnsibleModule

_PARTIAL_METADATA_API_VERSION = "meta.k8s.io/v1"
_PARTIAL_METADATA_KIND = "PartialObjectMetadata"
_PARTIAL_METADATA_ACCEPT = (
    "application/json;as=PartialObjectMetadata;g=meta.k8s.io;v=v1"
)
_TOP_LEVEL = {"apiVersion", "kind", "metadata"}
_METADATA_ALLOWED = {
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
_CANONICAL_LABELS = {
    ("shared-services", "shared-rabbitmq-cristexhub-prod"): {
        "app.kubernetes.io/managed-by": "infisical",
        "app.kubernetes.io/part-of": "shared-rabbitmq",
        "cristex.io/value-owner": "infisical-cloud",
    },
    ("cristexhub-prod", "cristexhub-prod-runtime"): {
        "app.kubernetes.io/managed-by": "infisical",
        "app.kubernetes.io/part-of": "cristexhub",
        "cristex.io/value-owner": "infisical-cloud",
    },
    ("cristexhub-prod", "cristexhub-prod-ghcr-pull"): {
        "app.kubernetes.io/managed-by": "infisical",
        "app.kubernetes.io/part-of": "cristexhub",
        "cristex.io/value-owner": "infisical-cloud",
    },
}
_CANONICAL_ANNOTATION = "secrets.infisical.com/version"


def _metadata(client: object, namespace: str, name: str) -> dict:
    """Fetch and validate only metadata for the requested Secret identity."""
    payload = client.call_api(
        "/api/v1/namespaces/{namespace}/secrets/{name}",
        "GET",
        path_params={"namespace": namespace, "name": name},
        query_params=[],
        header_params={"Accept": _PARTIAL_METADATA_ACCEPT},
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
    if metadata.get("name") != name or metadata.get("namespace") != namespace:
        raise ValueError("Secret identity changed during metadata read")
    required = ("name", "namespace", "uid", "resourceVersion")
    if any(not isinstance(metadata.get(key), str) or not metadata[key] for key in required):
        raise ValueError("incomplete Secret metadata")
    labels = metadata.get("labels", {})
    annotations = metadata.get("annotations", {})
    if not isinstance(labels, dict) or not isinstance(annotations, dict):
        raise ValueError("malformed Secret labels or annotations")
    if any(not isinstance(key, str) or not key for key in labels):
        raise ValueError("malformed Secret label key")
    if any(not isinstance(key, str) or not key for key in annotations):
        raise ValueError("malformed Secret annotation key")
    if any(not isinstance(value, str) for value in labels.values()):
        raise ValueError("malformed Secret label value")
    if any(not isinstance(value, str) for value in annotations.values()):
        raise ValueError("malformed Secret annotation value")
    expected_labels = _CANONICAL_LABELS.get((namespace, name))
    if expected_labels is None:
        raise ValueError("unsupported Secret identity")
    if labels != expected_labels:
        raise ValueError("noncanonical Secret labels")
    if set(annotations) != {_CANONICAL_ANNOTATION} or not annotations[_CANONICAL_ANNOTATION]:
        raise ValueError("noncanonical Secret annotations")
    owner_references = metadata.get("ownerReferences", [])
    if not isinstance(owner_references, list):
        raise ValueError("malformed Secret owner references")
    if owner_references != []:
        raise ValueError("owned Secret refused")
    deletion_timestamp = metadata.get("deletionTimestamp")
    if deletion_timestamp is not None:
        if not isinstance(deletion_timestamp, str) or not deletion_timestamp:
            raise ValueError("malformed Secret deletion timestamp")
        raise ValueError("terminating Secret refused")
    returned_metadata = copy.deepcopy(metadata)
    # Kubernetes omits an empty optional ownerReferences field.  Normalize it
    # so callers can bind the no-owner contract without dropping any other
    # legitimate PartialObjectMetadata fields.
    returned_metadata.setdefault("ownerReferences", [])
    return {
        "apiVersion": payload["apiVersion"],
        "kind": payload["kind"],
        "metadata": returned_metadata,
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
