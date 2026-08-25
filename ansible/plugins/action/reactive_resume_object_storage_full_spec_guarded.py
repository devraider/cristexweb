from __future__ import annotations

from copy import deepcopy
from typing import Any

from ansible.plugins.action import ActionBase


_METADATA_DROPS = {
    "creationTimestamp",
    "deletionGracePeriodSeconds",
    "deletionTimestamp",
    "generation",
    "managedFields",
    "resourceVersion",
    "selfLink",
    "uid",
}
_SERVICE_SPEC_DROPS = {
    "allocateLoadBalancerNodePorts",
    "clusterIP",
    "clusterIPs",
    "externalIPs",
    "externalName",
    "externalTrafficPolicy",
    "healthCheckNodePort",
    "internalTrafficPolicy",
    "ipFamilies",
    "ipFamilyPolicy",
    "loadBalancerClass",
    "loadBalancerSourceRanges",
    "publishNotReadyAddresses",
    "sessionAffinity",
    "sessionAffinityConfig",
}


def _clean(value: Any, *, kind: str, path: tuple[str, ...] = ()) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if path == ("metadata",) and key in _METADATA_DROPS:
                continue
            if path == ("metadata", "annotations") and key == "kubectl.kubernetes.io/last-applied-configuration":
                continue
            if kind == "Service" and path == ("spec",) and key in _SERVICE_SPEC_DROPS:
                continue
            if kind == "Service" and path == ("spec", "ports") and key == "nodePort":
                continue
            if kind == "ServiceAccount" and path == () and key in {"secrets", "imagePullSecrets"}:
                continue
            if kind == "ConfigMap" and path == () and key in {"binaryData", "immutable"}:
                continue
            if kind == "StatefulSet" and path == ("spec",) and key in {"minReadySeconds", "revisionHistoryLimit", "ordinals"}:
                continue
            if kind == "StatefulSet" and path == ("spec", "updateStrategy", "rollingUpdate") and child in ({}, None):
                continue
            result[key] = _clean(child, kind=kind, path=path + (key,))
        if path == ("metadata", "annotations") and not result:
            return None
        return result
    if isinstance(value, list):
        return [_clean(child, kind=kind, path=path) for child in value]
    return value


def _normalized(obj: dict[str, Any]) -> dict[str, Any]:
    kind = str(obj.get("kind", ""))
    result = _clean(deepcopy(obj), kind=kind)
    if result.get("metadata", {}).get("annotations") is None:
        result["metadata"].pop("annotations", None)
    result.pop("status", None)
    return result


class ActionModule(ActionBase):
    """Compare source and API objects without applying or reading secret values."""

    TRANSFERS_FILES = False

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        result = super().run(tmp, task_vars)
        desired = self._task.args.get("desired")
        live = self._task.args.get("live")
        if not isinstance(desired, dict) or not isinstance(live, dict):
            return {**result, "changed": False, "failed": True, "msg": "FULL_SPEC_GUARD: object input missing"}
        if _normalized(desired) != _normalized(live):
            return {**result, "changed": False, "failed": True, "msg": "FULL_SPEC_GUARD: normalized Kubernetes object drift"}
        return {**result, "changed": False, "failed": False}
