from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import ActionModule as KubernetesActionModule
from ansible_collections.kubernetes.core.plugins.action.k8s_json_patch import ActionModule as PatchActionModule


EXPECTED_IDENTITIES = {
    ("v1", "Secret", "argocd", "argocd-cluster-cristexhub-dev"),
    ("v1", "Secret", "argocd", "argocd-cluster-cristexhub-prod"),
    ("v1", "Secret", "argocd", "argocd-cluster-reactive-resume-dev"),
}
ARGS = {"state", "definition", "kubeconfig", "prestate_binding"}
TASK_SUFFIX = "/ansible/roles/argocd_cluster_cache_scope_transition/tasks/main.yml"
EXPECTED_REPOSITORY_ROOT = "/home/paul/projects/cristexweb"
EXPECTED_SERVER = "https://kubernetes.default.svc"
EXPECTED_TARGET_NAMESPACES = "cristexhub-dev,cristexhub-prod"
EXPECTED_CLUSTER_RESOURCES = "false"
EXPECTED_CONFIG = "{}"
LEGACY_NAMESPACES = {
    "argocd-cluster-cristexhub-dev": "cristexhub-dev",
    "argocd-cluster-cristexhub-prod": "cristexhub-prod",
    "argocd-cluster-reactive-resume-dev": "cristexhub-dev",
}
EXPECTED_COMPONENTS = {
    "argocd-cluster-cristexhub-dev": "cristexhub-dev-registration",
    "argocd-cluster-cristexhub-prod": "cristexhub-prod-registration",
    "argocd-cluster-reactive-resume-dev": "reactive-resume-dev-argocd-registration",
}
EXPECTED_NAMES = {
    "argocd-cluster-cristexhub-dev": "cristexhub-dev-local",
    "argocd-cluster-cristexhub-prod": "cristexhub-prod-local",
    "argocd-cluster-reactive-resume-dev": "reactive-resume-dev-local",
}
EXPECTED_HASHES = {
    ("v1", "Secret", "argocd", "argocd-cluster-cristexhub-dev"): "e0004f299746e11f5be387556abc89544889106452c376995d1df9c3e47941c2",
    ("v1", "Secret", "argocd", "argocd-cluster-cristexhub-prod"): "80bb4f88a9f3436f8a61e02de206207d6822681fd1f005c64f21c507273a4e11",
    ("v1", "Secret", "argocd", "argocd-cluster-reactive-resume-dev"): "56a6232806695ddced609cebc519f16a9431d8fbbb75b77eebb8a82423fec764",
}
EXPECTED_LABELS = {
    "app.kubernetes.io/part-of": "cristexhub",
    "app.kubernetes.io/managed-by": "ansible",
    "argocd.argoproj.io/secret-type": "cluster",
}
PRESTATE_FIELDS = {
    "apiVersion",
    "kind",
    "namespace",
    "name",
    "identity",
    "uid",
    "resourceVersion",
    "legacy_namespaces",
    "target_namespaces",
    "observed_namespaces",
}


def canonical(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def object_identity(value: dict[str, Any]) -> tuple[str, str, str, str]:
    metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
    return (
        str(value.get("apiVersion", "")),
        str(value.get("kind", "")),
        str(metadata.get("namespace", "")),
        str(metadata.get("name", "")),
    )


def _expected_string_data(name: str, namespaces: str) -> dict[str, str]:
    return {
        "name": EXPECTED_NAMES[name],
        "server": EXPECTED_SERVER,
        "namespaces": namespaces,
        "clusterResources": EXPECTED_CLUSTER_RESOURCES,
        "config": EXPECTED_CONFIG,
    }


def transition_patch(prestate_binding: dict[str, Any], definition: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the sole permitted data-field CAS patch for one owned cluster Secret."""
    identity = object_identity(definition)
    name = identity[3]
    if identity not in EXPECTED_IDENTITIES:
        raise ValueError("unknown cluster Secret identity")
    if set(prestate_binding) != PRESTATE_FIELDS:
        raise ValueError("incomplete cluster Secret prestate binding")
    if prestate_binding.get("identity") != "|".join(identity):
        raise ValueError("cluster Secret prestate identity mismatch")
    if prestate_binding.get("legacy_namespaces") != LEGACY_NAMESPACES[name]:
        raise ValueError("cluster Secret legacy scope mismatch")
    if prestate_binding.get("target_namespaces") != EXPECTED_TARGET_NAMESPACES:
        raise ValueError("cluster Secret target scope mismatch")
    if prestate_binding.get("observed_namespaces") != prestate_binding.get("legacy_namespaces"):
        raise ValueError("cluster Secret is not in the exact legacy state")
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", str(prestate_binding.get("uid", ""))):
        raise ValueError("invalid cluster Secret UID binding")
    if not re.fullmatch(r"[0-9]+", str(prestate_binding.get("resourceVersion", ""))):
        raise ValueError("invalid cluster Secret resourceVersion binding")
    target = definition.get("stringData")
    metadata = definition.get("metadata")
    if (
        definition.get("apiVersion") != "v1"
        or definition.get("kind") != "Secret"
        or not isinstance(metadata, dict)
        or metadata.get("namespace") != "argocd"
        or metadata.get("name") != name
        or definition.get("type") != "Opaque"
        or set(definition) != {"apiVersion", "kind", "metadata", "type", "stringData"}
        or not isinstance(target, dict)
        or target != _expected_string_data(name, EXPECTED_TARGET_NAMESPACES)
        or metadata.get("labels") != {**EXPECTED_LABELS, "cristex.io/component": EXPECTED_COMPONENTS[name]}
    ):
        raise ValueError("drifted cluster Secret target definition")
    old_encoded = base64.b64encode(str(prestate_binding["legacy_namespaces"]).encode()).decode()
    new_encoded = base64.b64encode(EXPECTED_TARGET_NAMESPACES.encode()).decode()
    return [
        {"op": "test", "path": "/metadata/uid", "value": prestate_binding["uid"]},
        {"op": "test", "path": "/metadata/resourceVersion", "value": str(prestate_binding["resourceVersion"])},
        {"op": "test", "path": "/data/namespaces", "value": old_encoded},
        {"op": "replace", "path": "/data/namespaces", "value": new_encoded},
    ]


def _strict_true(value: Any) -> bool:
    return value is True or (type(value).__name__ == "_AnsibleTaggedBool" and bool(value))


def _dispatch_patch(
    self: Any,
    tmp: str | None,
    task_vars: dict[str, Any],
    definition: dict[str, Any],
    patch: list[dict[str, Any]],
) -> dict[str, Any]:
    identity = object_identity(definition)
    original_action, original_args = self._task.action, self._task.args
    self._task.action = "kubernetes.core.k8s_json_patch"
    self._task.args = {
        "api_version": "v1",
        "kind": "Secret",
        "name": identity[3],
        "namespace": "argocd",
        "kubeconfig": "/etc/rancher/k3s/k3s.yaml",
        "patch": patch,
    }
    try:
        patch_action = PatchActionModule(
            self._task,
            self._connection,
            self._play_context,
            self._loader,
            self._templar,
            getattr(self, "_shared_loader_obj", None),
        )
        return patch_action.run(tmp=tmp, task_vars=task_vars)
    finally:
        self._task.action, self._task.args = original_action, original_args


class ActionModule(KubernetesActionModule):
    """Permit only one CAS patch on one of the three owned Argo cluster Secrets."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        args = self._task.args
        task_vars = task_vars or {}
        if source != EXPECTED_REPOSITORY_ROOT + TASK_SUFFIX:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical cache transition task source"}
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if context.CLIARGS.get("start_at_task") or context.CLIARGS.get("step") or tags not in ([], ["all"]) or skip_tags:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: task selection controls are forbidden"}
        definition = args.get("definition")
        binding = args.get("prestate_binding")
        if set(args) != ARGS or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml":
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing cache transition arguments"}
        if not isinstance(definition, dict) or not isinstance(binding, dict):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: target and prestate binding are required"}
        identity = object_identity(definition)
        if identity not in EXPECTED_IDENTITIES or canonical(definition) != EXPECTED_HASHES.get(identity):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unknown or drifted cluster Secret source"}
        token = os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_TOKEN", "")
        attestation = os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_ATTESTATION_FILE", "")
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except (OSError, ValueError):
            state, content = None, ""
        binding_from_vars = task_vars.get("argocd_cluster_cache_scope_transition_internal_preflight_binding", {})
        valid_binding = (
            isinstance(binding_from_vars, dict)
            and binding_from_vars.get("source_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding_from_vars.get("object_count") in (3, "3")
            and binding_from_vars.get("no_delete_path") is True
            and binding_from_vars.get("target_namespaces") == EXPECTED_TARGET_NAMESPACES
            and isinstance(binding_from_vars.get("prestate_bindings"), list)
            and len(binding_from_vars["prestate_bindings"]) == 3
            and all(isinstance(entry, dict) and set(entry) == PRESTATE_FIELDS for entry in binding_from_vars["prestate_bindings"])
            and binding in binding_from_vars["prestate_bindings"]
        )
        try:
            patch = transition_patch(binding, definition)
        except (TypeError, ValueError):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: invalid cache transition prestate"}
        valid = (
            valid_binding
            and os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and state is not None
            and stat.S_ISREG(state.st_mode)
            and not stat.S_ISLNK(state.st_mode)
            and stat.S_IMODE(state.st_mode) == 0o600
            and state.st_uid == os.getuid()
            and content == f"{token}:entrypoint"
            and _strict_true(task_vars.get("argocd_cluster_cache_scope_transition_approved"))
            and task_vars.get("argocd_cluster_cache_scope_transition_state") == "present"
        )
        if not valid:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: cache transition requires the guarded attestation and binding"}
        if bool(context.CLIARGS.get("check") or getattr(self._task, "check_mode", False)):
            return {"changed": True, "transition": "legacy-to-shared", "patch_operation_count": len(patch)}
        return _dispatch_patch(self, tmp, task_vars, definition, patch)
