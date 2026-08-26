from __future__ import annotations

import copy
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

EXPECTED = {
    ("argoproj.io/v1alpha1", "AppProject", "argocd", "cristexhub-prod"),
    ("argoproj.io/v1alpha1", "Application", "argocd", "cristexhub-prod"),
    ("rbac.authorization.k8s.io/v1", "Role", "cristexhub-prod", "argocd-application-controller-cristexhub-prod"),
    ("rbac.authorization.k8s.io/v1", "RoleBinding", "cristexhub-prod", "argocd-application-controller-cristexhub-prod"),
    ("v1", "Secret", "argocd", "argocd-cluster-cristexhub-prod"),
}
ARGS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
TRANSITION_ARGS = {"transition", "state", "kubeconfig", "project_definition", "application_definition"}
EXPECTED_REPOSITORY_ROOT = "/home/paul/projects/cristexweb"
TASK_SUFFIX = "/ansible/roles/cristexhub_prod_registration/tasks/main.yml"
EXPECTED_CLUSTER_NAMESPACES = "cristexhub-dev,cristexhub-prod"
ALIAS_TRANSITION_UIDS = {
    "Application": "e2016a99-2c4f-4e2e-ac28-0640cafa2a8e",
    "AppProject": "6c04c48c-7d71-46c3-b4d0-7fc9f437f5d6",
}
ALIAS_TRANSITION_SPEC_HASHES = {
    "Application": "9029099765f684eefcb75d1304064e94e690718d5af9f7e80b783e4bc577408e",
    "AppProject": "59cd297c33dd12a0063cded64e132e77e70dcd2b3bebee2dd207686a2d9ab239",
}
ALIAS_TRANSITION_MANIFEST_HASHES = {
    "Application": "107356ed772eec987ab8c4f19b05b2ebb5a84ddf21bd0f483044e434084a8c5a",
    "AppProject": "113dcb263ec958430385b802e387658cd0f71b58751768b3a7ab5ffbb348b61b",
}
ALIAS_TRANSITION_METADATA_HASH = "a4ef801de0c6aaf91a3c44e718afa10d17ab11727ce9b06b3d40727fd4c3ad30"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_registration/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_registration/defaults/main.yml"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/bootstrap_cristexhub_prod_registration.yml"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/bootstrap-cristexhub-prod-registration"
_INVENTORY_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/inventory.local.yml"
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_ACTION_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/action/cristexhub_prod_registration_guarded_k8s.py"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_PYTHON_SOURCE = Path("/usr/bin/python3")
_KUBECONFIG_SOURCE = Path("/etc/rancher/k3s/k3s.yaml")
_EXPECTED_OPERATOR = "paul"
_EXPECTED_TASK_NAMES = {
    False: "Reconcile registration source without synchronization",
    True: "Reconcile exact bounded PROD direct-server transition",
}
_EXPECTED_TASK_ACTION = "cristexhub_prod_registration_guarded_k8s"
_ACTION_CANONICAL_SHA256 = "235d8f2e631658427f9924ee61ff066b1fce278847bd36c557eb5dc82d0ad030"
_WRAPPER_CANONICAL_SHA256 = "0d6f0362ef90c4badbdcb8f131e9b211ba02a7aea49e2a4bc44636159eea1b87"
_TASK_SHA256 = "a8d5d08d1298223add2bae2c4e6756693bf3904b575eaa97ef6ea4bd3bfc7fdd"
_DEFAULTS_SHA256 = "0ca75dfa3eacdaecd14c98810a8a071a904538c7ca7528d6888aaebe4f5c2a57"
_PLAYBOOK_SHA256 = "05f22011b423c7aafff5a93d4aa5ba2cd4d41f56fe2ff41b842f032f793a7458"
_INVENTORY_SHA256 = "652a8455f8a050005ab783d20d4e60a0cd034d8a6439f1cffe551a91102773b0"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_PYTHON_SHA256 = "17b78e0a93175e86f9ac03141924fd7a7f0c0c52e66b34bfa0de20ffef989df1"
_SOURCE_CLOSURE_SHA256 = "2d0c1878f262b6ef95940f5a78b9f878d747ef8a19ea472799b7c414d6bc1306"
EXPECTED_SOURCE_CLOSURE_ENTRIES = [
    "cristexhub-prod=8bdd846ebe3d745a6abd9cd7eefaa8f9b1b3f9340e1910f1756736309c7b1467",
    "cristexhub-prod=81bf9a7e2c3bcfefc78540725a4b8f797eb34b037e693680504b33ac1a12f4a1",
    "argocd-application-controller-cristexhub-prod=f5606f2b58299fb1ce67dab48273513e57dd0ca0613795f9d976b1509fd33977",
    "argocd-application-controller-cristexhub-prod=1957e9e7ab1cc9cbedf9ff70273cb6f5567eec41082300302bb17fecba6b37f5",
    "argocd-cluster-cristexhub-prod=c6b7534728865115014979ea4d6aeeedd9f28fc7ff415bad8795bcc1dfd75193",
]
EXPECTED_IDENTITIES = {
    "argoproj.io/v1alpha1|AppProject|argocd|cristexhub-prod",
    "argoproj.io/v1alpha1|Application|argocd|cristexhub-prod",
    "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod",
    "rbac.authorization.k8s.io/v1|RoleBinding|cristexhub-prod|argocd-application-controller-cristexhub-prod",
    "v1|Secret|argocd|argocd-cluster-cristexhub-prod",
}
TRANSITION_KINDS = {"Application", "AppProject"}


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _canonical_file_hash(path: Path, symbol: str) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            rf"(?m)^({re.escape(symbol)}\s*=\s*[\"'])([0-9a-f]{{64}})([\"']\s*)$",
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
    argv = sys.argv[1:]
    extra_values: list[str] = []
    selection_argv = False
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument in ("-e", "--extra-vars"):
            if index + 1 >= len(argv):
                return False
            extra_values.append(argv[index + 1])
            index += 2
            continue
        if argument.startswith("-e=") or argument.startswith("--extra-vars="):
            extra_values.append(argument.split("=", 1)[1])
        elif argument in ("-t", "-S", "--start-at-task", "--step", "--tags", "--skip-tags") or argument.startswith(("-t=", "-S=", "--start-at-task=", "--step=", "--tags=", "--skip-tags=")):
            selection_argv = True
        elif argument in ("-i", "--inventory", "--limit"):
            if index + 1 >= len(argv):
                return False
            expected = ".ansible/inventory.local.yml" if argument in ("-i", "--inventory") else "crtxweb"
            if argv[index + 1] != expected:
                selection_argv = True
            index += 1
        index += 1
    return (
        not selection_argv
        and (not extra_values or extra_values == ["cristexhub_prod_registration_approved=true"])
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
    )
    if any(not path.is_file() or path.is_symlink() or _sha256(path) != digest for path, digest in expected):
        return False
    try:
        inventory_state = _INVENTORY_SOURCE.stat(follow_symlinks=False)
        config_state = _ANSIBLE_CONFIG_SOURCE.stat(follow_symlinks=False)
        controller_state = _CONTROLLER_SOURCE.stat(follow_symlinks=False)
        return (
            stat.S_IMODE(inventory_state.st_mode) == 0o600
            and inventory_state.st_uid == os.getuid()
            and stat.S_IMODE(config_state.st_mode) == 0o644
            and config_state.st_uid == os.getuid()
            and stat.S_ISREG(controller_state.st_mode)
            and not _CONTROLLER_SOURCE.is_symlink()
            and stat.S_IMODE(controller_state.st_mode) & 0o111
            and _canonical_file_hash(_ACTION_SOURCE, "_ACTION_CANONICAL_SHA256") == _ACTION_CANONICAL_SHA256
            and _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected") == _WRAPPER_CANONICAL_SHA256
        )
    except OSError:
        return False


def _wrapper_binding_valid(token: str) -> bool:
    attestation_path = os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ATTESTATION_FILE", "")
    pid_text = os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_WRAPPER_PID", "")
    starttime = os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_WRAPPER_STARTTIME", "")
    wrapper_path = os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_WRAPPER_PATH", "")
    wrapper_sha = os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_WRAPPER_SHA256", "")
    try:
        pid = int(pid_text)
        state = os.stat(attestation_path, follow_symlinks=False)
        content = Path(attestation_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return False
    return (
        os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ENTRYPOINT") == "v2"
        and re.fullmatch(r"[0-9a-f]{64}", token) is not None
        and pid > 1 and _ancestor(pid) and _proc_starttime(pid) == starttime
        and state.st_uid == os.getuid() and stat.S_ISREG(state.st_mode)
        and not stat.S_ISLNK(state.st_mode) and stat.S_IMODE(state.st_mode) == 0o600
        and state.st_nlink == 1 and Path(wrapper_path) == _WRAPPER_SOURCE
        and wrapper_sha == _sha256(_WRAPPER_SOURCE)
        and _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected") == _WRAPPER_CANONICAL_SHA256
        and content == f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\\n"
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_OPERATOR") == _EXPECTED_OPERATOR
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_CONTROLLER") == str(_CONTROLLER_SOURCE)
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_PYTHON") == str(_PYTHON_SOURCE)
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_KUBECONFIG") == str(_KUBECONFIG_SOURCE)
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_TASK_SHA256") == _sha256(_TASK_SOURCE)
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_DEFAULTS_SHA256") == _sha256(_DEFAULTS_SOURCE)
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_PLAYBOOK_SHA256") == _sha256(_PLAYBOOK_SOURCE)
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_INVENTORY_SHA256") == _sha256(_INVENTORY_SOURCE)
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ANSIBLE_CONFIG_SHA256") == _sha256(_ANSIBLE_CONFIG_SOURCE)
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ACTION_SHA256") == _sha256(_ACTION_SOURCE)
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_CONTROLLER_SHA256") == _sha256(_CONTROLLER_SOURCE)
        and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_PYTHON_SHA256") == _sha256(_PYTHON_SOURCE)
    )


def _valid_transition_kinds(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) <= 2
        and len(value) == len(set(value))
        and set(value) <= TRANSITION_KINDS
    )


def valid_transition_pair(alias: Any, target: Any) -> bool:
    """Validate the two complete endpoint sets used by the transition."""
    if not _valid_transition_kinds(alias) or not _valid_transition_kinds(target):
        return False
    if set(alias) & set(target) or set(alias) | set(target) != TRANSITION_KINDS:
        return False
    return (len(alias), len(target)) in {(2, 0), (1, 1), (0, 2)}


def valid_transition_state(alias: Any, target: Any, transitional: Any) -> bool:
    if not all(_valid_transition_kinds(value) for value in (alias, target, transitional)):
        return False
    sets = [set(alias), set(target), set(transitional)]
    if any(left & right for index, left in enumerate(sets) for right in sets[index + 1:]):
        return False
    if set().union(*sets) != TRANSITION_KINDS:
        return False
    allowed = {
        (('AppProject', 'Application'), (), ()),
        (('Application',), (), ('AppProject',)),
        ((), ('Application',), ('AppProject',)),
        ((), ('AppProject', 'Application'), ()),
    }
    return (tuple(sorted(alias)), tuple(sorted(target)), tuple(sorted(transitional))) in allowed


EXPECTED_HASHES: dict[tuple[str, str, str, str], str] = {('argoproj.io/v1alpha1', 'AppProject', 'argocd', 'cristexhub-prod'): '4625c40d6030961d799f7b04b386f5a840273bc96b5d7031a507bf48ab57afa2',
 ('argoproj.io/v1alpha1', 'Application', 'argocd', 'cristexhub-prod'): '29a3bd87c83d881e73f6e50739e9b510d89f58d2d851be93276658f1ad35bdf1',
 ('rbac.authorization.k8s.io/v1', 'Role', 'cristexhub-prod', 'argocd-application-controller-cristexhub-prod'): 'c40a189cdf4a3b864fae8bb64f06b0473aae2b47771f1c22ddf4a86f0f669fc4',
 ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'cristexhub-prod', 'argocd-application-controller-cristexhub-prod'): 'd0f0b78eb5960d368631b4d0ed9dd0371bacf19efa0e1c7ba01599d94bb75a83',
 ('v1', 'Secret', 'argocd', 'argocd-cluster-cristexhub-prod'): '80bb4f88a9f3436f8a61e02de206207d6822681fd1f005c64f21c507273a4e11'}

def canonical(value: dict[str, Any]) -> str:
    """Hash desired objects while ignoring only the bound metadata.resourceVersion."""
    normalized = json.loads(json.dumps(value))
    metadata = normalized.get("metadata")
    if isinstance(metadata, dict) and "resourceVersion" in metadata:
        metadata.pop("resourceVersion")
    return hashlib.sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def object_identity(value: dict[str, Any]) -> tuple[str, str, str, str]:
    metadata = value.get("metadata")
    if not isinstance(metadata, dict):
        metadata = value
    return (
        str(value.get("apiVersion", "")),
        str(value.get("kind", "")),
        str(metadata.get("namespace", "")),
        str(metadata.get("name", "")),
    )


def bound_prestate(bindings: Any, object_identity: tuple[str, str, str, str]) -> dict[str, Any] | None:
    if not isinstance(bindings, list):
        return None
    matches = [
        entry for entry in bindings
        if isinstance(entry, dict)
        and (
            entry.get("apiVersion"),
            entry.get("kind"),
            entry.get("namespace", ""),
            entry.get("name"),
        ) == object_identity
    ]
    return matches[0] if len(matches) == 1 else None


_TRANSITION_LABELS = {
    "app.kubernetes.io/name": "cristexhub-prod",
    "app.kubernetes.io/part-of": "cristexhub",
    "app.kubernetes.io/managed-by": "ansible",
    "cristex.io/component": "cristexhub-prod-registration",
}
_TRANSITION_PROJECT_WHITELIST = [
    {"group": "", "kind": "ConfigMap"},
    {"group": "", "kind": "Service"},
    {"group": "apps", "kind": "Deployment"},
    {"group": "networking.k8s.io", "kind": "NetworkPolicy"},
    {"group": "networking.k8s.io", "kind": "Ingress"},
]
_TRANSITION_REPOSITORY = "ssh://git@ssh.github.com:443/devraider/cristexhub.git"
_TRANSITION_REVISION = "751885a42798d282e168131db147f13694a0a621"
_TRANSITION_OLD_SERVER = "https://kubernetes.default.svc"
_TRANSITION_ALIAS = "cristexhub-prod-local"
_TRANSITION_NAMESPACE = "cristexhub-prod"
_TRANSITION_API_VERSION = "argoproj.io/v1alpha1"
_TRANSITION_ARGO_NAMESPACE = "argocd"
_TRANSITION_NAME = "cristexhub-prod"


def _transition_project_spec(destinations: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "sourceRepos": [_TRANSITION_REPOSITORY],
        "destinations": copy.deepcopy(destinations),
        "clusterResourceWhitelist": [],
        "namespaceResourceWhitelist": copy.deepcopy(_TRANSITION_PROJECT_WHITELIST),
        "orphanedResources": {"warn": True},
    }


def _transition_application_spec() -> dict[str, Any]:
    return {
        "project": _TRANSITION_NAME,
        "source": {
            "repoURL": _TRANSITION_REPOSITORY,
            "targetRevision": _TRANSITION_REVISION,
            "path": "infra/kubernetes/cristexhub-prod",
        },
        "destination": {"server": _TRANSITION_OLD_SERVER, "namespace": _TRANSITION_NAMESPACE},
        "syncPolicy": {
            "automated": {"prune": False, "selfHeal": True, "allowEmpty": False},
            "syncOptions": [
                "CreateNamespace=false",
                "Prune=false",
                "ServerSideApply=false",
                "Replace=false",
                "FailOnSharedResource=true",
            ],
        },
    }


# The final source is direct-server. The alias forms are accepted only as the
# bounded pre-state after the cache-scope transition, and the temporary
# project form is the sole bridge that keeps the Application authorized.
_TRANSITION_FINAL_PROJECT_SPEC = _transition_project_spec([{"server": _TRANSITION_OLD_SERVER, "namespace": _TRANSITION_NAMESPACE}])
_TRANSITION_TEMP_PROJECT_SPEC = _transition_project_spec([
    {"server": _TRANSITION_OLD_SERVER, "namespace": _TRANSITION_NAMESPACE},
    {"name": _TRANSITION_ALIAS, "namespace": _TRANSITION_NAMESPACE},
])
_TRANSITION_ALIAS_PROJECT_SPEC = _transition_project_spec([{"name": _TRANSITION_ALIAS, "namespace": _TRANSITION_NAMESPACE}])
_TRANSITION_FINAL_APPLICATION_SPEC = _transition_application_spec()
_TRANSITION_ALIAS_APPLICATION_SPEC = copy.deepcopy(_TRANSITION_FINAL_APPLICATION_SPEC)
_TRANSITION_ALIAS_APPLICATION_SPEC["destination"] = {"name": _TRANSITION_ALIAS, "server": "", "namespace": _TRANSITION_NAMESPACE}
_TRANSITION_UIDS = {
    "AppProject": ALIAS_TRANSITION_UIDS["AppProject"],
    "Application": ALIAS_TRANSITION_UIDS["Application"],
}


def _transition_identity(kind: str) -> tuple[str, str, str, str]:
    return (_TRANSITION_API_VERSION, kind, _TRANSITION_ARGO_NAMESPACE, _TRANSITION_NAME)


def _transition_metadata_safe(obj: dict[str, Any], kind: str) -> bool:
    metadata = obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {}
    if object_identity(obj) != _transition_identity(kind) or metadata.get("labels") != _TRANSITION_LABELS:
        return False
    if metadata.get("ownerReferences", []) or metadata.get("finalizers", []):
        return False
    if metadata.get("deletionTimestamp") not in (None, "") or metadata.get("deletionGracePeriodSeconds") not in (None, 0):
        return False
    allowed = {"name", "namespace", "uid", "resourceVersion", "generation", "creationTimestamp", "managedFields", "labels", "annotations"}
    return not (set(metadata) - allowed)


def _transition_classify(project: dict[str, Any], application: dict[str, Any]) -> tuple[str, str]:
    if not _transition_metadata_safe(project, "AppProject") or not _transition_metadata_safe(application, "Application"):
        raise ValueError("foreign, terminating, or metadata-drifted transition object")
    project_spec = project.get("spec")
    application_spec = application.get("spec")
    project_state = (
        "final" if project_spec == _TRANSITION_FINAL_PROJECT_SPEC else
        "transition" if project_spec == _TRANSITION_TEMP_PROJECT_SPEC else
        "alias" if project_spec == _TRANSITION_ALIAS_PROJECT_SPEC else None
    )
    application_state = (
        "final" if application_spec == _TRANSITION_FINAL_APPLICATION_SPEC else
        "alias" if application_spec == _TRANSITION_ALIAS_APPLICATION_SPEC else None
    )
    if project_state is None or application_state is None:
        raise ValueError("transition object scope is not an exact alias, transitional, or final form")
    # Only states reachable by the ordered three-step plan are accepted. In
    # particular, a final project with an alias Application is unsafe because
    # the alias would no longer be authorized by the project.
    if (project_state, application_state) not in {
        ("alias", "alias"),
        ("transition", "alias"),
        ("transition", "final"),
        ("final", "final"),
    }:
        raise ValueError("unsafe mixed transition state")
    return project_state, application_state


def _transition_plan(project_state: str, application_state: str) -> list[str]:
    states = (project_state, application_state)
    if states == ("final", "final"):
        return []
    if states == ("alias", "alias"):
        return ["AppProject:transition", "Application:final", "AppProject:final"]
    if states == ("transition", "alias"):
        return ["Application:final", "AppProject:final"]
    if states == ("transition", "final"):
        return ["AppProject:final"]
    raise ValueError("unsupported transition state")


def _transition_prestate_objects(prestate: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(prestate, dict) or not isinstance(prestate.get("results"), list):
        raise ValueError("complete transition prestate is required")
    objects: dict[str, dict[str, Any]] = {}
    for result in prestate["results"]:
        if not isinstance(result, dict) or not isinstance(result.get("resources"), list) or len(result["resources"]) != 1:
            continue
        obj = result["resources"][0]
        if isinstance(obj, dict) and obj.get("kind") in TRANSITION_KINDS:
            objects[obj["kind"]] = obj
    project = objects.get("AppProject")
    application = objects.get("Application")
    if project is None or application is None:
        raise ValueError("both transition objects are required")
    return project, application


def _transition_patch(kind: str, target: str, resource_version: str | None = None) -> list[dict[str, Any]]:
    if kind == "AppProject" and target == "transition":
        expected = _TRANSITION_ALIAS_PROJECT_SPEC
        destination = _TRANSITION_TEMP_PROJECT_SPEC["destinations"]
    elif kind == "Application" and target == "final":
        expected = _TRANSITION_ALIAS_APPLICATION_SPEC
        destination = _TRANSITION_FINAL_APPLICATION_SPEC["destination"]
    elif kind == "AppProject" and target == "final":
        expected = _TRANSITION_TEMP_PROJECT_SPEC
        destination = _TRANSITION_FINAL_PROJECT_SPEC["destinations"]
    else:
        raise ValueError("unsupported direct-server transition patch")
    destination_path = "/spec/destinations" if kind == "AppProject" else "/spec/destination"
    if resource_version is None or not re.fullmatch(r"[0-9]+", str(resource_version)):
        raise ValueError("transition resourceVersion is required")
    return [
        {"op": "test", "path": "/metadata/uid", "value": _TRANSITION_UIDS[kind]},
        {"op": "test", "path": "/metadata/resourceVersion", "value": str(resource_version)},
        {"op": "test", "path": "/metadata/labels", "value": copy.deepcopy(_TRANSITION_LABELS)},
        {"op": "test", "path": "/spec", "value": copy.deepcopy(expected)},
        {"op": "replace", "path": destination_path, "value": copy.deepcopy(destination)},
    ]


def _dispatch_transition_patch(
    self: Any,
    tmp: str | None,
    task_vars: dict[str, Any],
    kind: str,
    target: str,
    resource_version: str,
) -> dict[str, Any]:
    patch = _transition_patch(kind, target, resource_version)
    original_action, original_args = self._task.action, self._task.args
    self._task.action = "kubernetes.core.k8s_json_patch"
    self._task.args = {
        "api_version": _TRANSITION_API_VERSION,
        "kind": kind,
        "name": _TRANSITION_NAME,
        "namespace": _TRANSITION_ARGO_NAMESPACE,
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


def _fresh_transition_objects(self: Any, tmp: str | None, task_vars: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    objects: dict[str, dict[str, Any]] = {}
    for kind in ("AppProject", "Application"):
        result = self._execute_module(
            module_name="kubernetes.core.k8s_info",
            module_args={
                "api_version": _TRANSITION_API_VERSION,
                "kind": kind,
                "name": _TRANSITION_NAME,
                "namespace": _TRANSITION_ARGO_NAMESPACE,
                "kubeconfig": str(_KUBECONFIG_SOURCE),
            },
            task_vars=task_vars,
            tmp=tmp,
        )
        if not isinstance(result, dict) or result.get("failed") or not isinstance(result.get("resources"), list) or len(result["resources"]) != 1:
            raise ValueError("fresh transition prestate query failed")
        obj = result["resources"][0]
        if not isinstance(obj, dict) or obj.get("kind") != kind:
            raise ValueError("fresh transition response kind drifted")
        objects[kind] = obj
    return objects["AppProject"], objects["Application"]


def run_direct_server_transition(self: Any, tmp: str | None, task_vars: dict[str, Any], project_definition: dict[str, Any], application_definition: dict[str, Any], check_mode: bool) -> dict[str, Any]:
    if object_identity(project_definition) != _transition_identity("AppProject") or object_identity(application_definition) != _transition_identity("Application"):
        raise ValueError("exact AppProject/Application identities required")
    if project_definition.get("spec") != _TRANSITION_FINAL_PROJECT_SPEC or application_definition.get("spec") != _TRANSITION_FINAL_APPLICATION_SPEC:
        raise ValueError("direct-server final definitions drifted")
    prestate = task_vars.get("cristexhub_prod_registration_internal_prestate_recheck") if not check_mode else None
    if not isinstance(prestate, dict):
        prestate = task_vars.get("cristexhub_prod_registration_internal_prestate")
    project, application = _transition_prestate_objects(prestate)
    project_state, application_state = _transition_classify(project, application)
    plan = _transition_plan(project_state, application_state)
    binding = task_vars.get("cristexhub_prod_registration_internal_preflight_binding", {})
    if binding.get("transition_plan") != plan or str(binding.get("transition_change_count")) != str(len(plan)):
        raise ValueError("transition plan changed after guarded preflight")
    if check_mode:
        return {"changed": bool(plan), "transition_steps": plan, "transition_change_count": len(plan), "patch_dispatch": "kubernetes.core.k8s_json_patch"}
    changed: list[str] = []
    expected_states = {
        "AppProject:transition": ("alias", "alias"),
        "Application:final": ("transition", "alias"),
        "AppProject:final": ("transition", "final"),
    }
    for step in plan:
        kind, target = step.split(":", 1)
        fresh_project, fresh_application = _fresh_transition_objects(self, tmp, task_vars)
        current_state = _transition_classify(fresh_project, fresh_application)
        if current_state != expected_states[step]:
            raise ValueError("transition state changed before per-step CAS")
        current = fresh_project if kind == "AppProject" else fresh_application
        resource_version = current.get("metadata", {}).get("resourceVersion")
        result = _dispatch_transition_patch(self, tmp, task_vars, kind, target, str(resource_version))
        if result.get("failed"):
            return result
        if result.get("changed"):
            changed.append(step)
    return {"changed": bool(changed), "transition_steps": changed, "transition_change_count": len(changed), "patch_dispatch": "kubernetes.core.k8s_json_patch"}


class ActionModule(KubernetesActionModule):
    """Permit only the five-object, guarded CristexHub PROD registration."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        args = self._task.args
        transition_mode = args.get("transition") is True
        definition = args.get("definition") if not transition_mode else args.get("project_definition")
        task_vars = task_vars or {}
        if (
            source != str(_TASK_SOURCE)
            or getattr(self._task, "action", None) != _EXPECTED_TASK_ACTION
            or getattr(self._task, "name", None) != _EXPECTED_TASK_NAMES[transition_mode]
        ):
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical registration task source/action/name"}
        if not _selection_is_canonical():
            return {"changed": False, "failed": True, "msg": "TASK_SELECTION_GUARD: complete guarded PROD registration is required"}
        repository_root = str(Path(os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")).resolve())
        if repository_root != EXPECTED_REPOSITORY_ROOT or source != EXPECTED_REPOSITORY_ROOT + TASK_SUFFIX:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical registration task source"}
        if transition_mode:
            if set(args) != TRANSITION_ARGS or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml":
                return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing direct-server transition arguments"}
            application_definition = args.get("application_definition")
            if not isinstance(definition, dict) or not isinstance(application_definition, dict):
                return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: direct-server transition definitions are required"}
            if canonical(definition) != EXPECTED_HASHES[("argoproj.io/v1alpha1", "AppProject", "argocd", "cristexhub-prod")]:
                return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: drifted AppProject transition definition"}
            if canonical(application_definition) != EXPECTED_HASHES[("argoproj.io/v1alpha1", "Application", "argocd", "cristexhub-prod")]:
                return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: drifted Application transition definition"}
        else:
            if not isinstance(definition, dict) or set(args) != ARGS or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml" or args.get("wait") is not False or args.get("wait_timeout") != 60:
                return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing registration arguments"}
        meta = definition.get("metadata") or {}
        identity = (definition.get("apiVersion"), definition.get("kind"), meta.get("namespace", ""), meta.get("name", ""))
        if identity not in EXPECTED or canonical(definition) != EXPECTED_HASHES.get(identity):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unknown or drifted registration object"}
        if identity == ("v1", "Secret", "argocd", "argocd-cluster-cristexhub-prod"):
            string_data = definition.get("stringData") or {}
            if string_data.get("namespaces") != EXPECTED_CLUSTER_NAMESPACES or string_data.get("clusterResources") != "false":
                return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unbounded Argo cluster namespace scope"}
        if meta.get("labels", {}).get("cristex.io/component") != "cristexhub-prod-registration" or meta.get("labels", {}).get("app.kubernetes.io/managed-by") != "ansible":
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: ownership labels drifted"}
        token = os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_TOKEN", "")
        binding = task_vars.get("cristexhub_prod_registration_internal_preflight_binding", {})
        expected_names = sorted(identity[3] for identity in EXPECTED)
        strict_true = lambda value: (
            value is True or
            (type(value).__name__ == "_AnsibleTaggedBool" and bool(value)) or
            (type(value).__name__ == "_AnsibleTaggedStr" and value == "true")
        )
        valid_binding = (
            isinstance(binding, dict)
            and set(binding) == {
                "attestation_sha256",
                "manifest_names",
                "manifest_identities",
                "prestate_names",
                "prestate_identities",
                "object_count",
                "namespace_contract",
                "repository_contract",
                "revision",
                "alias_transition_kinds",
                "target_transition_kinds",
                "transitional_transition_kinds",
                "alias_transition_change_count",
                "alias_transition_uids",
                "alias_transition_spec_hashes",
                "alias_transition_manifest_hashes",
                "alias_transition_metadata_hash",
                "prestate_object_count",
                "prestate_bindings",
                "transition_change_count",
                "transition_plan",
                "no_delete_path",
                "task_sha256",
                "defaults_sha256",
                "playbook_sha256",
                "inventory_sha256",
                "ansible_config_sha256",
                "wrapper_sha256",
                "action_sha256",
                "controller_sha256",
                "python_sha256",
                "operator",
                "kubeconfig",
                "source_closure_sha256",
            }
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding.get("manifest_names") == expected_names
            and set(binding.get("manifest_identities", [])) == EXPECTED_IDENTITIES
            and len(binding.get("manifest_identities", [])) == len(EXPECTED_IDENTITIES)
            and binding.get("prestate_names") == expected_names
            and set(binding.get("prestate_identities", [])) == EXPECTED_IDENTITIES
            and len(binding.get("prestate_identities", [])) == len(EXPECTED_IDENTITIES)
            and binding.get("object_count") in (5, "5")
            and strict_true(binding.get("namespace_contract"))
            and strict_true(binding.get("repository_contract"))
            and binding.get("revision") == "751885a42798d282e168131db147f13694a0a621"
            and valid_transition_state(
                binding.get("alias_transition_kinds"),
                binding.get("target_transition_kinds"),
                binding.get("transitional_transition_kinds"),
            )
            and isinstance(binding.get("transitional_transition_kinds"), list)
            and binding.get("transitional_transition_kinds") in ([], ["AppProject"])
            and str(binding.get("alias_transition_change_count")) == str(len(binding.get("alias_transition_kinds")))
            and binding.get("alias_transition_uids") == ALIAS_TRANSITION_UIDS
            and binding.get("alias_transition_spec_hashes") == ALIAS_TRANSITION_SPEC_HASHES
            and binding.get("alias_transition_manifest_hashes") == ALIAS_TRANSITION_MANIFEST_HASHES
            and binding.get("alias_transition_metadata_hash") == ALIAS_TRANSITION_METADATA_HASH
            and str(binding.get("prestate_object_count")) == "5"
            and isinstance(binding.get("prestate_bindings"), list)
            and len(binding.get("prestate_bindings")) == 5
            and len({object_identity(entry) for entry in binding.get("prestate_bindings") if isinstance(entry, dict)}) == 5
            and len({entry.get("uid") for entry in binding.get("prestate_bindings") if isinstance(entry, dict)}) == 5
            and all(
                isinstance(entry, dict)
                and set(entry) == {"apiVersion", "kind", "namespace", "name", "identity", "uid", "resourceVersion", "generation"}
                and object_identity(entry) in EXPECTED
                and entry.get("identity") == "|".join(object_identity(entry))
                and re.fullmatch(r"[0-9a-fA-F-]{36}", str(entry.get("uid", ""))) is not None
                and re.fullmatch(r"[0-9]+", str(entry.get("resourceVersion", ""))) is not None
                and re.fullmatch(r"[0-9]+", str(entry.get("generation", ""))) is not None
                for entry in binding.get("prestate_bindings")
            )
            and str(binding.get("transition_change_count")) in ("0", "1", "2", "3")
            and isinstance(binding.get("transition_plan"), list)
            and str(binding.get("transition_change_count")) == str(len(binding.get("transition_plan")))
            and strict_true(binding.get("no_delete_path"))
            and binding.get("task_sha256") == _TASK_SHA256
            and binding.get("defaults_sha256") == _DEFAULTS_SHA256
            and binding.get("playbook_sha256") == _PLAYBOOK_SHA256
            and binding.get("inventory_sha256") == _INVENTORY_SHA256
            and binding.get("ansible_config_sha256") == _ANSIBLE_CONFIG_SHA256
            and binding.get("wrapper_sha256") == os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_WRAPPER_SHA256")
            and binding.get("action_sha256") == os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ACTION_SHA256")
            and binding.get("controller_sha256") == _CONTROLLER_SHA256
            and binding.get("python_sha256") == _PYTHON_SHA256
            and binding.get("operator") == _EXPECTED_OPERATOR
            and binding.get("kubeconfig") == str(_KUBECONFIG_SOURCE)
            and binding.get("source_closure_sha256") == _SOURCE_CLOSURE_SHA256
        )
        prestate = bound_prestate(binding.get("prestate_bindings"), identity)
        resource_version = meta.get("resourceVersion")
        if not valid_binding or (not transition_mode and (prestate is None or resource_version != prestate.get("resourceVersion"))):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: missing or changed UID/resourceVersion precondition"}
        valid = (
            valid_binding
            and _source_closure_valid()
            and _wrapper_binding_valid(token)
            and strict_true(task_vars.get("cristexhub_prod_registration_approved"))
            and task_vars.get("cristexhub_prod_registration_state") == "present"
        )
        if not valid:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: registration requires the guarded attestation and complete preflight binding"}
        if transition_mode:
            try:
                return run_direct_server_transition(
                    self,
                    tmp,
                    task_vars,
                    definition,
                    application_definition,
                    bool(context.CLIARGS.get("check") or getattr(self._task, "check_mode", False)),
                )
            except Exception as exc:
                return {"changed": False, "failed": True, "msg": f"PROD_ALIAS_TRANSITION_GUARD: {type(exc).__name__}"}
        self._task.action = "kubernetes.core.k8s"
        return super().run(tmp=tmp, task_vars=task_vars)
