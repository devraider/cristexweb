#!/usr/bin/python3
"""Evaluate a complete NetworkPolicy inventory against one MongoDB Pod.

The module is deliberately pure and value-free: Kubernetes discovery is done by
 the role, then this module evaluates the returned objects without contacting an
 API.  Every policy must be structurally valid.  Invalid or unsupported selector
 input is reported as invalid so the caller can fail closed rather than silently
 missing a policy that overlaps the MongoDB Pod.
"""
from __future__ import annotations

from typing import Any

from ansible.module_utils.basic import AnsibleModule

_ALLOWED_SELECTOR_KEYS = {"matchLabels", "matchExpressions"}
_ALLOWED_EXPRESSION_KEYS = {"key", "operator", "values"}
_ALLOWED_OPERATORS = {"In", "NotIn", "Exists", "DoesNotExist"}
_EXPECTED_API_VERSION = "networking.k8s.io/v1"
_EXPECTED_KIND = "NetworkPolicy"


def _identity(policy: Any, index: int) -> str:
    """Return a stable identity, including a safe placeholder for bad input."""
    if not isinstance(policy, dict):
        return f"<policy:{index}>"
    metadata = policy.get("metadata")
    if not isinstance(metadata, dict):
        return f"<policy:{index}>"
    values = (
        policy.get("apiVersion"),
        policy.get("kind"),
        metadata.get("namespace"),
        metadata.get("name"),
    )
    if not all(isinstance(value, str) and value for value in values):
        return f"<policy:{index}>"
    return "|".join(values)


def _string_map(value: Any) -> bool:
    return isinstance(value, dict) and all(
        isinstance(key, str) and bool(key) and isinstance(item, str)
        for key, item in value.items()
    )


def _selector_shape_valid(selector: Any) -> bool:
    """Validate LabelSelector shape without evaluating it against labels."""
    if not isinstance(selector, dict) or not set(selector).issubset(_ALLOWED_SELECTOR_KEYS):
        return False
    match_labels = selector.get("matchLabels", {})
    if not _string_map(match_labels):
        return False
    expressions = selector.get("matchExpressions", [])
    if not isinstance(expressions, list):
        return False
    for expression in expressions:
        if not isinstance(expression, dict):
            return False
        if not set(expression).issubset(_ALLOWED_EXPRESSION_KEYS):
            return False
        key = expression.get("key")
        operator = expression.get("operator")
        if not isinstance(key, str) or not key or operator not in _ALLOWED_OPERATORS:
            return False
        values = expression.get("values", [])
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            return False
        if operator in {"In", "NotIn"} and not values:
            return False
        if operator in {"Exists", "DoesNotExist"} and values:
            return False
    return True


def _selector_matches(selector: Any, labels: Any) -> bool:
    """Apply Kubernetes LabelSelector semantics to one label map.

    In particular, NotIn matches when a label is absent, as does the Kubernetes
    set-selector implementation.  Exists and DoesNotExist require an empty
    values list; In and NotIn require at least one value.
    """
    if not _selector_shape_valid(selector) or not _string_map(labels):
        return False
    match_labels = selector.get("matchLabels", {})
    for key, expected in match_labels.items():
        if labels.get(key) != expected:
            return False
    for expression in selector.get("matchExpressions", []):
        key = expression["key"]
        operator = expression["operator"]
        values = expression.get("values", [])
        present = key in labels
        actual = labels.get(key)
        if operator == "In" and (not present or actual not in values):
            return False
        if operator == "NotIn" and present and actual in values:
            return False
        if operator == "Exists" and not present:
            return False
        if operator == "DoesNotExist" and present:
            return False
    return True


def _invalid_result(status: str, identity: str) -> dict[str, Any]:
    return {
        "selector_status": status,
        "inventory_policy_identities": [],
        "matched_policy_identities": [],
        "invalid_policy_identities": [identity],
        "terminating_policy_identities": [],
    }


def _evaluate(policies: Any, pod_labels: Any, expected_namespace: Any) -> dict[str, Any]:
    """Evaluate every inventory entry; never silently ignore malformed input."""
    if not isinstance(policies, list):
        return _invalid_result("invalid-inventory", "<inventory>")
    if not _string_map(pod_labels) or not isinstance(expected_namespace, str) or not expected_namespace:
        return _invalid_result("invalid-input", "<input>")

    inventory: list[str] = []
    matched: list[str] = []
    invalid: list[str] = []
    terminating: list[str] = []
    for index, policy in enumerate(policies):
        identity = _identity(policy, index)
        inventory.append(identity)
        if not isinstance(policy, dict):
            invalid.append(identity)
            continue
        metadata = policy.get("metadata")
        spec = policy.get("spec")
        if not isinstance(metadata, dict) or not isinstance(spec, dict):
            invalid.append(identity)
            continue
        if (
            policy.get("apiVersion") != _EXPECTED_API_VERSION
            or policy.get("kind") != _EXPECTED_KIND
            or metadata.get("namespace") != expected_namespace
            or not isinstance(metadata.get("name"), str)
            or not metadata.get("name")
            or "podSelector" not in spec
        ):
            invalid.append(identity)
            continue
        if "deletionTimestamp" in metadata:
            deletion_timestamp = metadata.get("deletionTimestamp")
            if deletion_timestamp is None:
                pass
            elif isinstance(deletion_timestamp, str) and deletion_timestamp:
                terminating.append(identity)
                invalid.append(identity)
            else:
                invalid.append(identity)
        selector = spec.get("podSelector")
        if not _selector_shape_valid(selector):
            invalid.append(identity)
            continue
        if _selector_matches(selector, pod_labels):
            matched.append(identity)

    duplicate_identities = {
        identity for identity in inventory if inventory.count(identity) > 1
    }
    invalid.extend(duplicate_identities)
    invalid = sorted(set(invalid))
    terminating = sorted(set(terminating))
    return {
        "selector_status": "valid" if not invalid else "invalid-selector",
        "inventory_policy_identities": inventory,
        "matched_policy_identities": sorted(matched),
        "invalid_policy_identities": invalid,
        "terminating_policy_identities": terminating,
    }


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "policies": {"type": "list", "required": True},
            "pod_labels": {"type": "dict", "required": True},
            "expected_namespace": {"type": "str", "required": True},
        },
        supports_check_mode=True,
    )
    result = _evaluate(
        module.params["policies"],
        module.params["pod_labels"],
        module.params["expected_namespace"],
    )
    module.exit_json(changed=False, **result)


if __name__ == "__main__":
    main()
