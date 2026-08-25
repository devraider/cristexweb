from __future__ import annotations

from copy import deepcopy
from typing import Any

from ansible.plugins.action import ActionBase


# Only API-generated identity bookkeeping may be ignored.  Deletion state is
# deliberately retained: a terminating object is not an acceptable source
# match, even when its remaining spec is unchanged.
_METADATA_DROPS = {
    "creationTimestamp",
    "generation",
    "managedFields",
    "resourceVersion",
    "selfLink",
    "uid",
}

# These fields are generated from the allocator's chosen Service IP family
# when the source omits them.  They are handled pairwise below so an explicit
# source value is never hidden.  In particular, traffic policy and session
# affinity are behavior/security controls and are never dropped.
_SERVICE_SPEC_DROPS = {
    "clusterIP",
    "clusterIPs",
    "ipFamilies",
    "ipFamilyPolicy",
}
_SERVICE_DEFAULTS = {
    "internalTrafficPolicy": "Cluster",
    "sessionAffinity": "None",
    "publishNotReadyAddresses": False,
}
_STATEFULSET_DEFAULTS = {
    ("spec", "revisionHistoryLimit"): 10,
    ("spec", "minReadySeconds"): 0,
    ("spec", "podManagementPolicy"): "OrderedReady",
    ("spec", "ordinals", "start"): 0,
    ("spec", "updateStrategy", "type"): "RollingUpdate",
    ("spec", "updateStrategy", "rollingUpdate", "partition"): 0,
    ("spec", "updateStrategy", "rollingUpdate", "maxUnavailable"): 1,
}


def _clean(value: Any, *, kind: str, path: tuple[str, ...] = ()) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if path == ("metadata",) and key in _METADATA_DROPS:
                continue
            if (
                path == ("metadata", "annotations")
                and key == "kubectl.kubernetes.io/last-applied-configuration"
            ):
                continue
            result[key] = _clean(child, kind=kind, path=path + (key,))
        if path == ("metadata", "annotations") and not result:
            return None
        return result
    if isinstance(value, list):
        return [_clean(child, kind=kind, path=path) for child in value]
    return value


def _normalized(obj: dict[str, Any]) -> dict[str, Any]:
    """Remove only non-authoritative API bookkeeping from one object."""
    kind = str(obj.get("kind", ""))
    result = _clean(deepcopy(obj), kind=kind)
    metadata = result.get("metadata")
    if isinstance(metadata, dict) and metadata.get("annotations") is None:
        metadata.pop("annotations", None)
    # Status is observed state, not desired source.  Deletion metadata remains
    # in metadata and is checked explicitly by the source role.
    result.pop("status", None)
    return result


def _get_path(value: dict[str, Any], path: tuple[str, ...]) -> tuple[bool, Any]:
    current: Any = value
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return False, None
        current = current[key]
    return True, current


def _set_path(value: dict[str, Any], path: tuple[str, ...], item: Any) -> None:
    current = value
    for key in path[:-1]:
        child = current.get(key)
        if not isinstance(child, dict):
            child = {}
            current[key] = child
        current = child
    current[path[-1]] = deepcopy(item)


def _pop_path(value: dict[str, Any], path: tuple[str, ...]) -> None:
    current: Any = value
    for key in path[:-1]:
        if not isinstance(current, dict):
            return
        current = current.get(key)
    if isinstance(current, dict):
        current.pop(path[-1], None)


def _effective_pair(desired: dict[str, Any], live: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Normalize API defaults without hiding a non-default behavior change.

    Kubernetes writes allocator fields and documented defaults into returned
    objects even when the source omitted them.  For each such field, a live
    value is ignored only when the source omitted the field.  Defaults are
    copied to the omitted side only when the observed value is the documented
    default; an explicit non-default value therefore remains a drift.
    """
    normalized_desired = _normalized(desired)
    normalized_live = _normalized(live)
    kind = str(normalized_desired.get("kind", normalized_live.get("kind", "")))

    if kind == "Service":
        desired_spec = normalized_desired.setdefault("spec", {})
        live_spec = normalized_live.setdefault("spec", {})
        for field in _SERVICE_SPEC_DROPS:
            if field not in desired_spec:
                live_spec.pop(field, None)
        for field, default in _SERVICE_DEFAULTS.items():
            desired_has = field in desired_spec
            live_has = field in live_spec
            if not desired_has and live_has and live_spec[field] == default:
                desired_spec[field] = deepcopy(default)
            elif desired_has and not live_has and desired_spec[field] == default:
                live_spec[field] = deepcopy(default)

    if kind == "StatefulSet":
        for path, default in _STATEFULSET_DEFAULTS.items():
            desired_has, desired_value = _get_path(normalized_desired, path)
            live_has, live_value = _get_path(normalized_live, path)
            if not desired_has and live_has and live_value == default:
                _set_path(normalized_desired, path, default)
            elif desired_has and not live_has and desired_value == default:
                _set_path(normalized_live, path, default)

    return normalized_desired, normalized_live


def _normalized_pair(desired: dict[str, Any], live: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Public test seam for the pairwise effective-spec comparison."""
    return _effective_pair(desired, live)


class ActionModule(ActionBase):
    """Compare source and API objects without applying or reading secret values."""

    TRANSFERS_FILES = False

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = super().run(tmp, task_vars)
        desired = self._task.args.get("desired")
        live = self._task.args.get("live")
        if not isinstance(desired, dict) or not isinstance(live, dict):
            return {
                **result,
                "changed": False,
                "failed": True,
                "msg": "FULL_SPEC_GUARD: object input missing",
            }
        normalized_desired, normalized_live = _effective_pair(desired, live)
        if normalized_desired != normalized_live:
            return {
                **result,
                "changed": False,
                "failed": True,
                "msg": "FULL_SPEC_GUARD: normalized Kubernetes object drift",
            }
        return {**result, "changed": False, "failed": False}
