from __future__ import annotations

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

EXPECTED_REPOSITORY_ROOT = "/home/paul/projects/cristexweb"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/argocd_target_cache_repair/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/argocd_target_cache_repair/defaults/main.yml"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/bootstrap_argocd_target_cache_repair.yml"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/bootstrap-argocd-target-cache-repair"
_ACTION_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/action/argocd_target_cache_repair_guarded_k8s.py"
_CONFIGMAP_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/argocd/config/configmap-argocd-cm.yaml"
_ROLE_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/cristexhub-prod-registration/rbac/role-argocd-application-controller-cristexhub-prod.yaml"
_STATEFULSET_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/argocd/runtime/statefulset-argocd-application-controller.yaml"
_INVENTORY_SOURCE = Path("/home/paul/projects/cristexweb/ansible/.ansible/inventory.local.yml")
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_PYTHON_SOURCE = Path("/usr/bin/python3")
_KUBECONFIG_SOURCE = Path("/etc/rancher/k3s/k3s.yaml")
_EXPECTED_OPERATOR = "paul"
_TASK_SUFFIX = "/ansible/roles/argocd_target_cache_repair/tasks/main.yml"
_EXPECTED_TASK_NAME = "Apply only the exact target-cache repair patches"
_EXPECTED_ACTION = "argocd_target_cache_repair_guarded_k8s"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_PYTHON_SHA256 = "17b78e0a93175e86f9ac03141924fd7a7f0c0c52e66b34bfa0de20ffef989df1"
_ACTION_CANONICAL_SHA256 = "61c10f1362be0094f3749bbb056932708cd1b10bff6ad378f708f7aba8027046"
_WRAPPER_CANONICAL_SHA256 = "da7756c63fcd2bab2b53640a8e8850a4dd8379722f3f4853d46caf21aef21947"
_TASK_SHA256 = "099d73d24c0e868883caf1bbb59c7ba0e6dc1c5be4d689baac19731879792a28"
_DEFAULTS_SHA256 = "dff5ec4f0b87ca298e4bfac9b19a0ac6748ce09dd20ed67e63c674bd71288905"
_PLAYBOOK_SHA256 = "eb1a22aa4a75438a8ad9f84b64c105059655fc03e5aae7d6ac76b12aa63195b7"
_CONFIGMAP_SHA256 = "bc167b1f4d2ccb20223c67bceb067459fed6a8057a6b4119aa0bd1dc9909c082"
_ROLE_SHA256 = "9a12af899b86acdac58ad34ce707f8558d45dede27c4e362926c488be1fb44f9"
_STATEFULSET_SHA256 = "aa96028f0ab939d68b26d393c98f7ce0f8ae2c5d14525753a4292679c372329e"
_EXPECTED_UIDS = {
    "v1|ConfigMap|argocd|argocd-cm": "848966ad-8d11-41ff-8a26-5e17532f7a81",
    "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod": "7ea319e9-2ad3-4f49-b529-e19eeb944690",
    "apps/v1|StatefulSet|argocd|argocd-application-controller": "d18d7475-4dec-48ee-a284-b5a4d4629b01",
}
_ARGS = {"state", "definition", "kubeconfig", "prestate_binding"}
_EXPECTED_TARGET_IDENTITIES = set(_EXPECTED_UIDS)
_EXPECTED_INCLUSION = """- apiGroups:\n    - ''\n  kinds:\n    - ConfigMap\n    - Service\n    - ServiceAccount\n  clusters:\n    - https://kubernetes.default.svc\n- apiGroups:\n    - apps\n  kinds:\n    - Deployment\n  clusters:\n    - https://kubernetes.default.svc\n- apiGroups:\n    - networking.k8s.io\n  kinds:\n    - Ingress\n    - NetworkPolicy\n  clusters:\n    - https://kubernetes.default.svc\n"""
_EXPECTED_ROLE_RULE = {"apiGroups": [""], "resources": ["serviceaccounts"], "verbs": ["get", "list", "watch"]}
_EXPECTED_DEFINITION_HASHES = {
    "v1|ConfigMap|argocd|argocd-cm": "9aaac655d5ba9613b626738679ef793e20a7cf85c4e4f5511f1297d393d14c6f",
    "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod": "b360dc15ff78580772e2d74c6720796865a6b9e4303033d1ad822880e0a493e5",
    "apps/v1|StatefulSet|argocd|argocd-application-controller": "ff4f2de8fbc72c7677c862b04b96f749be784de5ccf7ad32cce0dda9824caa65",
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
        return hashlib.sha256(source.encode()).hexdigest() if count == 1 else ""
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


def _proc_cmdline(pid: int) -> list[str]:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        return [part.decode("utf-8", "strict") for part in raw[:-1].split(b"\0")] if raw.endswith(b"\0") else []
    except (OSError, UnicodeError):
        return []


def _strict_true(value: Any) -> bool:
    return value is True or (type(value).__name__ == "_AnsibleTaggedBool" and bool(value))


def _expected_argv() -> list[str]:
    argv = [
        str(_CONTROLLER_SOURCE),
        "-i", ".ansible/inventory.local.yml",
        "playbooks/bootstrap_argocd_target_cache_repair.yml",
        "--diff", "--limit", "crtxweb",
        "--extra-vars", "argocd_target_cache_repair_approved=true",
    ]
    if bool(context.CLIARGS.get("check")):
        argv.append("--check")
    return argv


def _selection_is_canonical() -> bool:
    inventory = context.CLIARGS.get("inventory") or []
    inventory = [inventory] if isinstance(inventory, str) else list(inventory)
    return (
        sys.argv == _expected_argv()
        and context.CLIARGS.get("start_at_task") is None
        and context.CLIARGS.get("step") in (None, False)
        and list(context.CLIARGS.get("tags") or []) in ([], ["all"])
        and not list(context.CLIARGS.get("skip_tags") or [])
        and context.CLIARGS.get("subset") == "crtxweb"
        and bool(context.CLIARGS.get("diff"))
        and inventory in [[".ansible/inventory.local.yml"], [str(_INVENTORY_SOURCE)]]
        and not any(os.environ.get(name) for name in ("ANSIBLE_LIBRARY", "ANSIBLE_ACTION_PLUGINS", "ANSIBLE_ROLES_PATH", "ANSIBLE_COLLECTIONS_PATH"))
    )


def _source_closure_valid() -> bool:
    expected = (
        (_TASK_SOURCE, _TASK_SHA256, 0o644, os.getuid()),
        (_DEFAULTS_SOURCE, _DEFAULTS_SHA256, 0o644, os.getuid()),
        (_PLAYBOOK_SOURCE, _PLAYBOOK_SHA256, 0o644, os.getuid()),
        (_CONFIGMAP_SOURCE, _CONFIGMAP_SHA256, 0o644, os.getuid()),
        (_ROLE_SOURCE, _ROLE_SHA256, 0o644, os.getuid()),
        (_STATEFULSET_SOURCE, _STATEFULSET_SHA256, 0o644, os.getuid()),
        (_INVENTORY_SOURCE, _INVENTORY_SHA256, 0o600, os.getuid()),
        (_ANSIBLE_CONFIG_SOURCE, _ANSIBLE_CONFIG_SHA256, 0o644, os.getuid()),
    )
    for path, digest, mode, owner in expected:
        try:
            state = path.stat(follow_symlinks=False)
            if not path.is_file() or path.is_symlink() or stat.S_IMODE(state.st_mode) != mode or state.st_uid != owner or _sha256(path) != digest:
                return False
        except OSError:
            return False
    try:
        controller = _CONTROLLER_SOURCE.stat(follow_symlinks=False)
        python = _PYTHON_SOURCE.stat(follow_symlinks=False)
        return (
            stat.S_IMODE(controller.st_mode) == 0o775 and controller.st_uid == os.getuid() and _sha256(_CONTROLLER_SOURCE) == _CONTROLLER_SHA256
            and stat.S_IMODE(python.st_mode) == 0o755 and python.st_uid == 0 and _sha256(_PYTHON_SOURCE) == _PYTHON_SHA256
            and _canonical_file_hash(_ACTION_SOURCE, "_ACTION_CANONICAL_SHA256") == _ACTION_CANONICAL_SHA256
            and _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected") == _WRAPPER_CANONICAL_SHA256
        )
    except OSError:
        return False


def _wrapper_binding_valid(token: str) -> bool:
    attestation_path = os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_ATTESTATION_FILE", "")
    pid_text = os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_WRAPPER_PID", "")
    starttime = os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_WRAPPER_STARTTIME", "")
    wrapper_path = os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_WRAPPER_PATH", "")
    wrapper_sha = os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_WRAPPER_SHA256", "")
    try:
        pid = int(pid_text)
        state = os.stat(attestation_path, follow_symlinks=False)
        content = Path(attestation_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return False
    return (
        os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_ENTRYPOINT") == "v1"
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG_SOURCE)
        and re.fullmatch(r"[0-9a-f]{64}", token) is not None
        and pid > 1 and _ancestor(pid) and _proc_starttime(pid) == starttime
        and stat.S_ISREG(state.st_mode) and not stat.S_ISLNK(state.st_mode)
        and stat.S_IMODE(state.st_mode) == 0o600 and state.st_uid == os.getuid() and state.st_nlink == 1
        and Path(wrapper_path) == _WRAPPER_SOURCE and wrapper_sha == _sha256(_WRAPPER_SOURCE)
        and _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected") == _WRAPPER_CANONICAL_SHA256
        and _proc_cmdline(pid) == ["/bin/dash", str(_WRAPPER_SOURCE), "check" if bool(context.CLIARGS.get("check")) else "apply"]
        and content == f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\n"
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_OPERATOR") == _EXPECTED_OPERATOR
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_CONTROLLER") == str(_CONTROLLER_SOURCE)
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_PYTHON") == str(_PYTHON_SOURCE)
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_KUBECONFIG") == str(_KUBECONFIG_SOURCE)
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_CONTROLLER_SHA256") == _CONTROLLER_SHA256
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_PYTHON_SHA256") == _PYTHON_SHA256
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_TASK_SHA256") == _TASK_SHA256
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_DEFAULTS_SHA256") == _DEFAULTS_SHA256
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_PLAYBOOK_SHA256") == _PLAYBOOK_SHA256
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_CONFIGMAP_SHA256") == _CONFIGMAP_SHA256
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_ROLE_SHA256") == _ROLE_SHA256
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_STATEFULSET_SHA256") == _STATEFULSET_SHA256
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_INVENTORY_SHA256") == _INVENTORY_SHA256
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_ANSIBLE_CONFIG_SHA256") == _ANSIBLE_CONFIG_SHA256
        and os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_ACTION_SHA256") == _sha256(_ACTION_SOURCE)
    )


def _identity(value: dict[str, Any]) -> str:
    metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
    return "|".join((str(value.get("apiVersion", "")), str(value.get("kind", "")), str(metadata.get("namespace", "")), str(metadata.get("name", ""))))


def _canonical(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _patch_for(definition: dict[str, Any], binding: dict[str, Any]) -> list[dict[str, Any]]:
    identity = _identity(definition)
    if identity not in _EXPECTED_TARGET_IDENTITIES or binding.get("identity") != identity or binding.get("uid") != _EXPECTED_UIDS[identity]:
        raise ValueError("target identity or UID drift")
    if binding.get("state") != "legacy" or not re.fullmatch(r"[0-9]+", str(binding.get("resourceVersion", ""))):
        raise ValueError("target is not an exact legacy prestate")
    test = [
        {"op": "test", "path": "/metadata/uid", "value": binding["uid"]},
        {"op": "test", "path": "/metadata/resourceVersion", "value": str(binding["resourceVersion"])},
    ]
    if identity == "v1|ConfigMap|argocd|argocd-cm":
        observed = binding.get("observed_data")
        if not isinstance(observed, dict) or "resource.inclusions" in observed:
            raise ValueError("ConfigMap is not the exact pre-repair state")
        return test + [{"op": "test", "path": "/data", "value": observed}, {"op": "add", "path": "/data/resource.inclusions", "value": _EXPECTED_INCLUSION}]
    if identity == "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod":
        observed = binding.get("observed_rules")
        if not isinstance(observed, list) or _EXPECTED_ROLE_RULE in observed:
            raise ValueError("PROD Role is not the exact pre-repair state")
        return test + [{"op": "test", "path": "/rules", "value": observed}, {"op": "replace", "path": "/rules", "value": definition["rules"]}]
    observed = binding.get("observed_annotations")
    if not isinstance(observed, dict) or "cristex.io/target-cache-repair" in observed:
        raise ValueError("controller is not the exact pre-repair state")
    observed_spec = binding.get("observed_spec")
    if not isinstance(observed_spec, dict):
        raise ValueError("controller spec prestate is required")
    return test + [
        {"op": "test", "path": "/spec", "value": observed_spec},
        {"op": "test", "path": "/spec/template/metadata/annotations", "value": observed},
        {"op": "replace", "path": "/spec/template/metadata/annotations", "value": definition["spec"]["template"]["metadata"]["annotations"]},
    ]


def _dispatch(self: Any, tmp: str | None, task_vars: dict[str, Any], definition: dict[str, Any], patch: list[dict[str, Any]]) -> dict[str, Any]:
    identity = _identity(definition)
    _, _, namespace, name = identity.split("|", 3)
    original_action, original_args = self._task.action, self._task.args
    self._task.action = "kubernetes.core.k8s_json_patch"
    self._task.args = {"api_version": definition["apiVersion"], "kind": definition["kind"], "namespace": namespace, "name": name, "kubeconfig": str(_KUBECONFIG_SOURCE), "patch": patch}
    try:
        action = PatchActionModule(self._task, self._connection, self._play_context, self._loader, self._templar, getattr(self, "_shared_loader_obj", None))
        return action.run(tmp=tmp, task_vars=task_vars)
    finally:
        self._task.action, self._task.args = original_action, original_args


class ActionModule(KubernetesActionModule):
    """Permit only one exact CAS patch for the three target-cache repair objects."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        task_vars = task_vars or {}
        args = self._task.args
        source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        if source != EXPECTED_REPOSITORY_ROOT + _TASK_SUFFIX or not _selection_is_canonical() or not _source_closure_valid():
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical target-cache repair invocation"}
        if str(getattr(self._task, "name", "")) != _EXPECTED_TASK_NAME or self._task.action != _EXPECTED_ACTION:
            return {"changed": False, "failed": True, "msg": "TASK_SELECTION_GUARD: unexpected target-cache repair task identity"}
        if set(args) != _ARGS or args.get("state") != "present" or args.get("kubeconfig") != str(_KUBECONFIG_SOURCE):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unexpected target-cache repair arguments"}
        token = os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_TOKEN", "")
        if not _strict_true(task_vars.get("argocd_target_cache_repair_approved")) or task_vars.get("argocd_target_cache_repair_state") != "present" or not _wrapper_binding_valid(token):
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: missing target-cache repair wrapper binding"}
        definition = args.get("definition")
        binding = args.get("prestate_binding")
        if not isinstance(definition, dict) or not isinstance(binding, dict):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: exact definition and prestate binding required"}
        identity = _identity(definition)
        expected_source = {"v1|ConfigMap|argocd|argocd-cm": (_CONFIGMAP_SOURCE, _CONFIGMAP_SHA256), "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod": (_ROLE_SOURCE, _ROLE_SHA256), "apps/v1|StatefulSet|argocd|argocd-application-controller": (_STATEFULSET_SOURCE, _STATEFULSET_SHA256)}
        if identity not in expected_source or _canonical(definition) != _EXPECTED_DEFINITION_HASHES[identity]:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unknown or drifted target-cache definition"}
        if _sha256(expected_source[identity][0]) != expected_source[identity][1] or binding.get("identity") != identity or binding.get("uid") != _EXPECTED_UIDS[identity]:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: source or prestate drift"}
        try:
            patch = _patch_for(definition, binding)
        except (TypeError, ValueError, KeyError):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: exact target-cache prestate required"}
        check_mode = bool(context.CLIARGS.get("check") or getattr(self._task, "check_mode", False))
        if check_mode:
            return {"changed": True, "patch_operation_count": len(patch), "identity": identity}
        result = _dispatch(self, tmp, task_vars, definition, patch)
        if result.get("failed"):
            return result
        return {**result, "identity": identity, "patch_operation_count": len(patch)}
