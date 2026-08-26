from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import stat
import sys
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
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/argocd_cluster_cache_scope_transition/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/argocd_cluster_cache_scope_transition/defaults/main.yml"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/bootstrap_argocd_cluster_cache_scope_transition.yml"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/bootstrap-argocd-cluster-cache-scope-transition"
_INVENTORY_SOURCE = Path("/home/paul/projects/cristexweb/ansible/.ansible/inventory.local.yml")
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_ACTION_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/action/argocd_cluster_cache_scope_transition_guarded_k8s.py"
_METADATA_MODULE_SOURCE = _REPOSITORY_ROOT / "ansible/library/argocd_cluster_cache_secret_metadata.py"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_PYTHON_SOURCE = Path("/usr/bin/python3")
_KUBECONFIG_SOURCE = Path("/etc/rancher/k3s/k3s.yaml")
_EXPECTED_OPERATOR = "paul"
_EXPECTED_TASK_NAME = "Apply only legacy cluster Secret scope patches with exact CAS bindings"
_EXPECTED_TASK_ACTION = "argocd_cluster_cache_scope_transition_guarded_k8s"
_ACTION_CANONICAL_SHA256 = "ebcc9d980a8fc5daa31107679cf0ae05d3d24ca0abcb8787c76acbf5ca257d3b"
_WRAPPER_CANONICAL_SHA256 = "22314904d86ead629a88ff3d61f355d3b871d6ffb8404b5f015519a37fb24a5d"
_TASK_SHA256 = "88a0aeb6ab7ff6a4470808ee72606ad9f0a9e79b88f4ff31a6dbfccfa43ee21e"
_DEFAULTS_SHA256 = "e5cf4171ce426332d7d16411797460a5c66280512d629fd924019848784f2b30"
_PLAYBOOK_SHA256 = "c44ee2507e08cb2a52a3c091a0d47776e61e98e90a1e2d233da068553345a7b7"
_INVENTORY_SHA256 = "652a8455f8a050005ab783d20d4e60a0cd034d8a6439f1cffe551a91102773b0"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_METADATA_MODULE_SHA256 = "67ed8c212e61aed4994dd24deb8b1b750da468567b26ec502b31d5cba744f379"
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
EXPECTED_SOURCE_HASHES = {
    ("v1", "Secret", "argocd", "argocd-cluster-cristexhub-dev"): "4fe913fe414a6d9ffa93286c7ba0c760ebc2671bcc90c202dccfc645b7f209c9",
    ("v1", "Secret", "argocd", "argocd-cluster-cristexhub-prod"): "c6b7534728865115014979ea4d6aeeedd9f28fc7ff415bad8795bcc1dfd75193",
    ("v1", "Secret", "argocd", "argocd-cluster-reactive-resume-dev"): "9e59d72f0085490e77f89be74a91a4f4d882f9ba07e89b334bd8ef7feef466d2",
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


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _canonical_file_hash(path: Path, symbol: str) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            rf"(?m)^({re.escape(symbol)}\s*=\s*[\"\'])([0-9a-f]{{64}})([\"\']\s*)$",
            rf"\g<1>{'0' * 64}\g<3>",
            source,
        )
        if count != 1:
            return ""
        return hashlib.sha256(source.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _proc_starttime(pid: int) -> str:
    try:
        return Path(f"/proc/{pid}/stat").read_text().split()[21]
    except (OSError, IndexError):
        return ""


def _ancestor(pid: int) -> bool:
    current = os.getpid()
    seen: set[int] = set()
    while current > 1 and current not in seen:
        if current == pid:
            return True
        seen.add(current)
        try:
            status = Path(f"/proc/{current}/status").read_text()
            current = int(next(line for line in status.splitlines() if line.startswith("PPid:")).split()[1])
        except (OSError, StopIteration, ValueError):
            return False
    return False


def _selection_is_canonical() -> bool:
    tags = list(context.CLIARGS.get("tags") or [])
    skip_tags = list(context.CLIARGS.get("skip_tags") or [])
    inventory = context.CLIARGS.get("inventory") or []
    if isinstance(inventory, str):
        inventory = [inventory]
    forbidden = ("--start-at-task", "--step", "--tags", "--skip-tags")
    selection_argv = any(
        argument in ("-t", "-S")
        or argument.startswith("-t=")
        or argument.startswith("-S=")
        or (argument.startswith("-t") and len(argument) > 2)
        or argument.startswith("--start-at-task=")
        or argument.startswith("--step=")
        or argument.startswith("--tags=")
        or argument.startswith("--skip-tags=")
        or argument in forbidden
        for argument in sys.argv[1:]
    )
    return (
        not selection_argv
        and context.CLIARGS.get("start_at_task") is None
        and context.CLIARGS.get("step") in (None, False)
        and tags in ([], ["all"])
        and not skip_tags
        and context.CLIARGS.get("subset") == "crtxweb"
        and bool(context.CLIARGS.get("diff"))
        and inventory in [[".ansible/inventory.local.yml"], [str(_INVENTORY_SOURCE)]]
    )


def _source_closure_valid() -> bool:
    expected = (
        (_TASK_SOURCE, _TASK_SHA256),
        (_DEFAULTS_SOURCE, _DEFAULTS_SHA256),
        (_PLAYBOOK_SOURCE, _PLAYBOOK_SHA256),
        (_INVENTORY_SOURCE, _INVENTORY_SHA256),
        (_ANSIBLE_CONFIG_SOURCE, _ANSIBLE_CONFIG_SHA256),
        (_METADATA_MODULE_SOURCE, _METADATA_MODULE_SHA256),
    )
    if any(not path.is_file() or path.is_symlink() or _sha256(path) != digest for path, digest in expected):
        return False
    try:
        inventory_state = _INVENTORY_SOURCE.stat(follow_symlinks=False)
        config_state = _ANSIBLE_CONFIG_SOURCE.stat(follow_symlinks=False)
        return (
            stat.S_IMODE(inventory_state.st_mode) == 0o600
            and inventory_state.st_uid == os.getuid()
            and stat.S_IMODE(config_state.st_mode) == 0o644
            and config_state.st_uid == os.getuid()
            and _canonical_file_hash(_ACTION_SOURCE, "_ACTION_CANONICAL_SHA256") == _ACTION_CANONICAL_SHA256
            and _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected") == _WRAPPER_CANONICAL_SHA256
        )
    except OSError:
        return False


def _wrapper_binding_valid(token: str) -> bool:
    attestation_path = os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_ATTESTATION_FILE", "")
    pid_text = os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_WRAPPER_PID", "")
    starttime = os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_WRAPPER_STARTTIME", "")
    wrapper_path = os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_WRAPPER_PATH", "")
    wrapper_sha = os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_WRAPPER_SHA256", "")
    try:
        pid = int(pid_text)
        state = os.stat(attestation_path, follow_symlinks=False)
        content = Path(attestation_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return False
    return (
        os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_ENTRYPOINT") == "v2"
        and re.fullmatch(r"[0-9a-f]{64}", token) is not None
        and pid > 1
        and _ancestor(pid)
        and _proc_starttime(pid) == starttime
        and state.st_uid == os.getuid()
        and stat.S_ISREG(state.st_mode)
        and not stat.S_ISLNK(state.st_mode)
        and stat.S_IMODE(state.st_mode) == 0o600
        and state.st_nlink == 1
        and Path(wrapper_path) == _WRAPPER_SOURCE
        and wrapper_sha == _sha256(_WRAPPER_SOURCE)
        and _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected") == _WRAPPER_CANONICAL_SHA256
        and content == f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\n"
        and os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_OPERATOR") == _EXPECTED_OPERATOR
        and os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_CONTROLLER") == str(_CONTROLLER_SOURCE)
        and os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_PYTHON") == str(_PYTHON_SOURCE)
        and os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_KUBECONFIG") == str(_KUBECONFIG_SOURCE)
        and os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_CONTROLLER_SHA256") == _sha256(_CONTROLLER_SOURCE)
        and os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_PYTHON_SHA256") == _sha256(_PYTHON_SOURCE)
    )


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
        if (
            source != str(_TASK_SOURCE)
            or getattr(self._task, "name", None) != _EXPECTED_TASK_NAME
            or getattr(self._task, "action", None) != _EXPECTED_TASK_ACTION
        ):
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical cache transition task source"}
        if not _selection_is_canonical():
            return {"changed": False, "failed": True, "msg": "TASK_SELECTION_GUARD: complete guarded cache play is required"}
        definition = args.get("definition")
        binding = args.get("prestate_binding")
        if set(args) != ARGS or args.get("state") != "present" or args.get("kubeconfig") != str(_KUBECONFIG_SOURCE):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing cache transition arguments"}
        if not isinstance(definition, dict) or not isinstance(binding, dict):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: target and prestate binding are required"}
        identity = object_identity(definition)
        if identity not in EXPECTED_IDENTITIES or canonical(definition) != EXPECTED_HASHES.get(identity):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unknown or drifted cluster Secret source"}
        token = os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_TOKEN", "")
        binding_from_vars = task_vars.get("argocd_cluster_cache_scope_transition_internal_preflight_binding", {})
        closure = ":".join(
            f"{identity[3]}={EXPECTED_SOURCE_HASHES[identity]}" for identity in sorted(EXPECTED_IDENTITIES)
        )
        expected_binding_keys = {
            "source_sha256", "object_count", "target_namespaces", "prestate_bindings", "no_delete_path",
            "source_closure_sha256", "task_sha256", "defaults_sha256", "playbook_sha256",
            "inventory_sha256", "ansible_config_sha256", "metadata_module_sha256", "wrapper_sha256", "action_sha256",
            "controller_sha256", "python_sha256", "operator", "kubeconfig",
        }
        valid_binding = (
            isinstance(binding_from_vars, dict)
            and set(binding_from_vars) == expected_binding_keys
            and binding_from_vars.get("source_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding_from_vars.get("source_closure_sha256") == hashlib.sha256(closure.encode()).hexdigest()
            and binding_from_vars.get("object_count") in (3, "3")
            and binding_from_vars.get("no_delete_path") is True
            and binding_from_vars.get("target_namespaces") == EXPECTED_TARGET_NAMESPACES
            and isinstance(binding_from_vars.get("prestate_bindings"), list)
            and len(binding_from_vars["prestate_bindings"]) == 3
            and all(isinstance(entry, dict) and set(entry) == PRESTATE_FIELDS for entry in binding_from_vars["prestate_bindings"])
            and binding in binding_from_vars["prestate_bindings"]
            and binding_from_vars.get("task_sha256") == _TASK_SHA256
            and binding_from_vars.get("defaults_sha256") == _DEFAULTS_SHA256
            and binding_from_vars.get("playbook_sha256") == _PLAYBOOK_SHA256
            and binding_from_vars.get("inventory_sha256") == _INVENTORY_SHA256
            and binding_from_vars.get("ansible_config_sha256") == _ANSIBLE_CONFIG_SHA256
            and binding_from_vars.get("metadata_module_sha256") == _METADATA_MODULE_SHA256
            and binding_from_vars.get("wrapper_sha256") == os.environ.get("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_WRAPPER_SHA256")
            and binding_from_vars.get("action_sha256") == _sha256(_ACTION_SOURCE)
            and binding_from_vars.get("controller_sha256") == _sha256(_CONTROLLER_SOURCE)
            and binding_from_vars.get("python_sha256") == _sha256(_PYTHON_SOURCE)
            and binding_from_vars.get("operator") == _EXPECTED_OPERATOR
            and binding_from_vars.get("kubeconfig") == str(_KUBECONFIG_SOURCE)
        )
        try:
            patch = transition_patch(binding, definition)
        except (TypeError, ValueError):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: invalid cache transition prestate"}
        valid = (
            valid_binding
            and _source_closure_valid()
            and _wrapper_binding_valid(token)
            and _strict_true(task_vars.get("argocd_cluster_cache_scope_transition_approved"))
            and task_vars.get("argocd_cluster_cache_scope_transition_state") == "present"
        )
        if not valid:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: cache transition requires the canonical wrapper, source closure, and binding"}
        if bool(context.CLIARGS.get("check") or getattr(self._task, "check_mode", False)):
            return {"changed": True, "transition": "legacy-to-shared", "patch_operation_count": len(patch)}
        return _dispatch_patch(self, tmp, task_vars, definition, patch)
