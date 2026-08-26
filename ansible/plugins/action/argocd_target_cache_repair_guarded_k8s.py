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
_PYTHON_SOURCE = Path("/usr/bin/python3.13")
_KUBECONFIG_SOURCE = Path("/etc/rancher/k3s/k3s.yaml")
_K8S_JSON_PATCH_SOURCE = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core/plugins/action/k8s_json_patch.py")
_K8S_JSON_PATCH_REAL_SOURCE = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core/plugins/action/k8s_info.py")
_EXPECTED_OPERATOR = "paul"
_TASK_SUFFIX = "/ansible/roles/argocd_target_cache_repair/tasks/main.yml"
_EXPECTED_TASK_NAMES = {
    "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod": "Apply only the exact target-cache repair PROD Role patch",
    "v1|ConfigMap|argocd|argocd-cm": "Apply only the exact target-cache repair ConfigMap patch",
    "apps/v1|StatefulSet|argocd|argocd-application-controller": "Apply only the exact target-cache repair controller StatefulSet patch",
}
_EXPECTED_ACTION = "argocd_target_cache_repair_guarded_k8s"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_PYTHON_SHA256 = "17b78e0a93175e86f9ac03141924fd7a7f0c0c52e66b34bfa0de20ffef989df1"
_INVENTORY_SHA256 = "652a8455f8a050005ab783d20d4e60a0cd034d8a6439f1cffe551a91102773b0"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_K8S_JSON_PATCH_SHA256 = "3f4a8318615ea5401fdea6d1177c181ad11e31e48eaf7f8f0fa6554a053fb16b"
_ACTION_CANONICAL_SHA256 = "91d3cae4bb72cbea66b1e7ef14360a1439c3cf102ddb3ad97819084e82b361fc"
_WRAPPER_CANONICAL_SHA256 = "39b3ee06dde22201688d59f29a06131d9f92d76273b20e668a2c30a5f42beee2"
_TASK_SHA256 = "7078a73e292a456bea252a72f389e548b4d49e926469cebddcda230b3af6f84d"
_DEFAULTS_SHA256 = "9c29d84393b18c56ca769fde990944f031ac9d042c2b618a014dbc5b0699a2c0"
_PLAYBOOK_SHA256 = "31bd84fa42af384ae3b94498b0e624033bdac847162aed06903728bb3ed88a5f"
_CONFIGMAP_SHA256 = "bc167b1f4d2ccb20223c67bceb067459fed6a8057a6b4119aa0bd1dc9909c082"
_ROLE_SHA256 = "9a12af899b86acdac58ad34ce707f8558d45dede27c4e362926c488be1fb44f9"
_STATEFULSET_SHA256 = "6921a5e7c28e33d20c6c30b64bd8b70749eaf4319071e4b54088c2c76b53cdd0"
_EXPECTED_UIDS = {
    "v1|ConfigMap|argocd|argocd-cm": "848966ad-8d11-41ff-8a26-5e17532f7a81",
    "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod": "7ea319e9-2ad3-4f49-b529-e19eeb944690",
    "apps/v1|StatefulSet|argocd|argocd-application-controller": "d18d7475-4dec-48ee-a284-b5a4d4629b01",
}
_ARGS = {"state", "definition", "kubeconfig", "prestate_binding"}
_EXPECTED_TARGET_IDENTITIES_ORDER = (
    "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod",
    "v1|ConfigMap|argocd|argocd-cm",
    "apps/v1|StatefulSet|argocd|argocd-application-controller",
)
_EXPECTED_TARGET_IDENTITIES = set(_EXPECTED_TARGET_IDENTITIES_ORDER)
_EXPECTED_INCLUSION = """- apiGroups:\n    - ''\n  kinds:\n    - ConfigMap\n    - Service\n    - ServiceAccount\n  clusters:\n    - https://kubernetes.default.svc\n- apiGroups:\n    - apps\n  kinds:\n    - Deployment\n  clusters:\n    - https://kubernetes.default.svc\n- apiGroups:\n    - networking.k8s.io\n  kinds:\n    - Ingress\n    - NetworkPolicy\n  clusters:\n    - https://kubernetes.default.svc\n"""
_EXPECTED_ROLE_RULE = {"apiGroups": [""], "resources": ["serviceaccounts"], "verbs": ["get", "list", "watch"]}
_LEGACY_CONFIGMAP_DATA = {
    "admin.enabled": "true",
    "application.instanceLabelKey": "argocd.argoproj.io/instance",
    "resource.respectRBAC": "strict",
    "timeout.reconciliation": "180s",
}
_LEGACY_ROLE_RULES = [
    {"apiGroups": [""], "resources": ["configmaps", "services"], "verbs": ["get", "list", "watch", "create", "patch"]},
    {"apiGroups": ["apps"], "resources": ["deployments"], "verbs": ["get", "list", "watch", "create", "patch"]},
    {"apiGroups": ["networking.k8s.io"], "resources": ["networkpolicies", "ingresses"], "verbs": ["get", "list", "watch", "create", "patch"]},
]
_LEGACY_CONTROLLER_ANNOTATIONS = {
    "checksum/cmd-params": "719e10663b1773800849f9da2234f3544e4c368d6b3f5568026bd4f71f303278",
    "checksum/cm": "7311652314f5f1ec5d55f2e282f2ad0189c91a93a9079c8947fb42be3b7fd21e",
    "checksum/cristexhub-dev-read-rbac": "23e8f7a228ebe53a9e7fde8ffc4ccf97dcb6a6dd433f70ed3b879e13d8558da1",
}
_EXPECTED_DEFINITION_HASHES = {
    "v1|ConfigMap|argocd|argocd-cm": "9aaac655d5ba9613b626738679ef793e20a7cf85c4e4f5511f1297d393d14c6f",
    "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod": "b360dc15ff78580772e2d74c6720796865a6b9e4303033d1ad822880e0a493e5",
    "apps/v1|StatefulSet|argocd|argocd-application-controller": "f4db45d6c8665af9197b2dcd698c3d40de485e584c0b6ad35afcded354887807",
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
    return (
        value is True
        or (type(value).__name__ == "_AnsibleTaggedBool" and bool(value))
        or (type(value).__name__ == "_AnsibleTaggedStr" and value == "true")
    )


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
        (_ACTION_SOURCE, _ACTION_CANONICAL_SHA256, 0o644, os.getuid()),
    )
    for path, digest, mode, owner in expected:
        try:
            state = path.stat(follow_symlinks=False)
            if (
                not path.is_file()
                or path.is_symlink()
                or stat.S_IMODE(state.st_mode) != mode
                or state.st_uid != owner
                or (
                    _canonical_file_hash(path, "_ACTION_CANONICAL_SHA256") != digest
                    if path == _ACTION_SOURCE
                    else _sha256(path) != digest
                )
            ):
                return False
        except OSError:
            return False
    try:
        controller = _CONTROLLER_SOURCE.stat(follow_symlinks=False)
        python = _PYTHON_SOURCE.stat(follow_symlinks=False)
        json_patch = _K8S_JSON_PATCH_SOURCE.lstat()
        json_patch_real = _K8S_JSON_PATCH_REAL_SOURCE.stat()
        return (
            stat.S_IMODE(controller.st_mode) == 0o775
            and controller.st_uid == os.getuid()
            and _sha256(_CONTROLLER_SOURCE) == _CONTROLLER_SHA256
            and stat.S_IMODE(python.st_mode) == 0o755
            and python.st_uid == 0
            and _sha256(_PYTHON_SOURCE) == _PYTHON_SHA256
            and _ACTION_SOURCE == Path(str(_ACTION_SOURCE)).resolve()
            and stat.S_ISREG(_ACTION_SOURCE.stat(follow_symlinks=False).st_mode)
            and _canonical_file_hash(_ACTION_SOURCE, "_ACTION_CANONICAL_SHA256") == _ACTION_CANONICAL_SHA256
            and _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected") == _WRAPPER_CANONICAL_SHA256
            and (stat.S_ISLNK(json_patch.st_mode) or stat.S_ISREG(json_patch.st_mode))
            and _K8S_JSON_PATCH_SOURCE.resolve() == _K8S_JSON_PATCH_REAL_SOURCE
            and stat.S_ISREG(json_patch_real.st_mode)
            and stat.S_IMODE(json_patch_real.st_mode) == 0o644
            and json_patch_real.st_uid == os.getuid()
            and _sha256(_K8S_JSON_PATCH_REAL_SOURCE) == _K8S_JSON_PATCH_SHA256
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


def _prestate_binding_valid(binding: dict[str, Any]) -> bool:
    if not isinstance(binding, dict):
        return False
    identity = binding.get("identity")
    expected_keys = {
        "identity", "apiVersion", "kind", "namespace", "name", "uid",
        "resourceVersion", "generation", "observed_generation", "current_revision",
        "update_revision", "state", "observed_data", "observed_rules",
        "observed_annotations", "observed_spec", "observed_labels",
    }
    return (
        set(binding) == expected_keys
        and identity in _EXPECTED_TARGET_IDENTITIES
        and binding.get("uid") == _EXPECTED_UIDS[identity]
        and re.fullmatch(r"[0-9a-fA-F-]{36}", str(binding.get("uid", ""))) is not None
        and re.fullmatch(r"[0-9]+", str(binding.get("resourceVersion", ""))) is not None
        and re.fullmatch(r"[0-9]+", str(binding.get("generation", ""))) is not None
        and binding.get("state") in {"legacy", "target"}
        and binding.get("apiVersion") == identity.split("|", 1)[0]
        and binding.get("kind") == identity.split("|", 2)[1]
        and "|".join((str(binding.get("apiVersion")), str(binding.get("kind")), str(binding.get("namespace")), str(binding.get("name")))) == identity
        and isinstance(binding.get("observed_data"), dict)
        and isinstance(binding.get("observed_rules"), list)
        and isinstance(binding.get("observed_annotations"), dict)
        and isinstance(binding.get("observed_spec"), dict)
        and isinstance(binding.get("observed_labels"), dict)
    )


def _preflight_binding_valid(binding: Any) -> bool:
    expected_keys = {
        "attestation_sha256", "object_count", "legacy_count", "target_count",
        "identities", "prestate_bindings", "transition_plan", "no_delete_path",
        "source_hashes", "definition_hashes", "task_sha256", "defaults_sha256",
        "playbook_sha256", "configmap_sha256", "role_sha256", "statefulset_sha256",
        "inventory_sha256", "ansible_config_sha256", "action_sha256",
        "controller_sha256", "python_sha256", "target_identities",
    }
    if not isinstance(binding, dict) or set(binding) != expected_keys:
        return False
    prestates = binding.get("prestate_bindings")
    identities = binding.get("identities")
    if identities != list(_EXPECTED_TARGET_IDENTITIES_ORDER) or binding.get("target_identities") != list(_EXPECTED_TARGET_IDENTITIES_ORDER):
        return False
    if not isinstance(prestates, list) or len(prestates) != 3:
        return False
    if [entry.get("identity") for entry in prestates] != list(_EXPECTED_TARGET_IDENTITIES_ORDER):
        return False
    if not all(_prestate_binding_valid(entry) for entry in prestates):
        return False
    legacy = [entry["identity"] for entry in prestates if entry.get("state") == "legacy"]
    return (
        binding.get("attestation_sha256") == hashlib.sha256(os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_TOKEN", "").encode()).hexdigest()
        and str(binding.get("object_count")) == "3"
        and str(binding.get("legacy_count")) == str(len(legacy))
        and str(binding.get("target_count")) == str(3 - len(legacy))
        and binding.get("transition_plan") == legacy
        and binding.get("source_hashes") == {
            identity: digest for identity, digest in zip(_EXPECTED_TARGET_IDENTITIES_ORDER, (_ROLE_SHA256, _CONFIGMAP_SHA256, _STATEFULSET_SHA256))
        }
        and binding.get("definition_hashes") == [
            _EXPECTED_DEFINITION_HASHES[identity]
            for identity in _EXPECTED_TARGET_IDENTITIES_ORDER
        ]
        and binding.get("task_sha256") == _TASK_SHA256
        and binding.get("defaults_sha256") == _DEFAULTS_SHA256
        and binding.get("playbook_sha256") == _PLAYBOOK_SHA256
        and binding.get("configmap_sha256") == _CONFIGMAP_SHA256
        and binding.get("role_sha256") == _ROLE_SHA256
        and binding.get("statefulset_sha256") == _STATEFULSET_SHA256
        and binding.get("inventory_sha256") == _INVENTORY_SHA256
        and binding.get("ansible_config_sha256") == _ANSIBLE_CONFIG_SHA256
        and binding.get("action_sha256") == _sha256(_ACTION_SOURCE)
        and binding.get("controller_sha256") == _CONTROLLER_SHA256
        and binding.get("python_sha256") == _PYTHON_SHA256
        and _strict_true(binding.get("no_delete_path"))
    )


def _canonical(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _legacy_statefulset_spec(definition: dict[str, Any]) -> dict[str, Any]:
    spec = json.loads(json.dumps(definition["spec"]))
    spec["template"]["metadata"]["annotations"] = _LEGACY_CONTROLLER_ANNOTATIONS
    return spec


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
        if observed != _LEGACY_CONFIGMAP_DATA:
            raise ValueError("ConfigMap is not the exact pre-repair state")
        return test + [{"op": "test", "path": "/data", "value": observed}, {"op": "add", "path": "/data/resource.inclusions", "value": _EXPECTED_INCLUSION}]
    if identity == "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod":
        observed = binding.get("observed_rules")
        if observed != _LEGACY_ROLE_RULES:
            raise ValueError("PROD Role is not the exact pre-repair state")
        return test + [{"op": "test", "path": "/rules", "value": observed}, {"op": "replace", "path": "/rules", "value": definition["rules"]}]
    observed = binding.get("observed_annotations")
    if observed != _LEGACY_CONTROLLER_ANNOTATIONS:
        raise ValueError("controller is not the exact pre-repair state")
    observed_spec = binding.get("observed_spec")
    if observed_spec != _legacy_statefulset_spec(definition):
        raise ValueError("controller spec prestate is not the exact legacy closure")
    return test + [
        {"op": "test", "path": "/spec", "value": observed_spec},
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
        definition = args.get("definition")
        identity = _identity(definition) if isinstance(definition, dict) else ""
        if str(getattr(self._task, "name", "")) != _EXPECTED_TASK_NAMES.get(identity) or self._task.action != _EXPECTED_ACTION:
            return {"changed": False, "failed": True, "msg": "TASK_SELECTION_GUARD: unexpected target-cache repair task identity"}
        if set(args) != _ARGS or args.get("state") != "present" or args.get("kubeconfig") != str(_KUBECONFIG_SOURCE):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unexpected target-cache repair arguments"}
        token = os.environ.get("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_TOKEN", "")
        preflight = task_vars.get("argocd_target_cache_repair_internal_preflight_binding")
        if (
            not _strict_true(task_vars.get("argocd_target_cache_repair_approved"))
            or task_vars.get("argocd_target_cache_repair_state") != "present"
        ):
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: missing target-cache repair approval"}
        if not _wrapper_binding_valid(token):
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: missing target-cache repair wrapper binding"}
        if not _preflight_binding_valid(preflight):
            return {"changed": False, "failed": True, "msg": "PREFLIGHT_GUARD: invalid target-cache repair preflight binding"}
        binding = args.get("prestate_binding")
        if not isinstance(definition, dict) or not isinstance(binding, dict):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: exact definition and prestate binding required"}
        identity = _identity(definition)
        expected_source = {"v1|ConfigMap|argocd|argocd-cm": (_CONFIGMAP_SOURCE, _CONFIGMAP_SHA256), "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod": (_ROLE_SOURCE, _ROLE_SHA256), "apps/v1|StatefulSet|argocd|argocd-application-controller": (_STATEFULSET_SOURCE, _STATEFULSET_SHA256)}
        if identity not in expected_source or _canonical(definition) != _EXPECTED_DEFINITION_HASHES[identity]:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unknown or drifted target-cache definition"}
        expected_binding = next((entry for entry in preflight["prestate_bindings"] if entry.get("identity") == identity), None)
        if (
            _sha256(expected_source[identity][0]) != expected_source[identity][1]
            or binding.get("identity") != identity
            or binding.get("uid") != _EXPECTED_UIDS[identity]
            or expected_binding is None
            or _canonical(binding) != _canonical(expected_binding)
        ):
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
