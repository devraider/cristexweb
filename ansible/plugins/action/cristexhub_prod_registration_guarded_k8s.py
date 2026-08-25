from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import ActionModule as KubernetesActionModule

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
LEGACY_TRANSITION_UIDS = {
    "Application": "e2016a99-2c4f-4e2e-ac28-0640cafa2a8e",
    "AppProject": "6c04c48c-7d71-46c3-b4d0-7fc9f437f5d6",
}
LEGACY_TRANSITION_SPEC_HASHES = {
    "Application": "efcaa04cff588189490810ec3dc2d799e9d09d9deb2e6ce45475d61f75021c34",
    "AppProject": "7b51035757a7684cffb823339379e7fd3d80ada29a51a3bdc205b2f4b30027bf",
}
LEGACY_TRANSITION_MANIFEST_HASHES = {
    "Application": "29a3bd87c83d881e73f6e50739e9b510d89f58d2d851be93276658f1ad35bdf1",
    "AppProject": "4625c40d6030961d799f7b04b386f5a840273bc96b5d7031a507bf48ab57afa2",
}
LEGACY_TRANSITION_METADATA_HASH = "a4ef801de0c6aaf91a3c44e718afa10d17ab11727ce9b06b3d40727fd4c3ad30"
EXPECTED_IDENTITIES = {
    "argoproj.io/v1alpha1|AppProject|argocd|cristexhub-prod",
    "argoproj.io/v1alpha1|Application|argocd|cristexhub-prod",
    "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod",
    "rbac.authorization.k8s.io/v1|RoleBinding|cristexhub-prod|argocd-application-controller-cristexhub-prod",
    "v1|Secret|argocd|argocd-cluster-cristexhub-prod",
}
TRANSITION_KINDS = {"Application", "AppProject"}


def _valid_transition_kinds(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) <= 2
        and len(value) == len(set(value))
        and set(value) <= TRANSITION_KINDS
    )


def valid_transition_pair(legacy: Any, target: Any) -> bool:
    if not _valid_transition_kinds(legacy) or not _valid_transition_kinds(target):
        return False
    if set(legacy) & set(target) or set(legacy) | set(target) != TRANSITION_KINDS:
        return False
    return (len(legacy), len(target)) in {(2, 0), (1, 1), (0, 2)}


EXPECTED_HASHES: dict[tuple[str, str, str, str], str] = {('argoproj.io/v1alpha1', 'AppProject', 'argocd', 'cristexhub-prod'): '113dcb263ec958430385b802e387658cd0f71b58751768b3a7ab5ffbb348b61b',
 ('argoproj.io/v1alpha1', 'Application', 'argocd', 'cristexhub-prod'): '107356ed772eec987ab8c4f19b05b2ebb5a84ddf21bd0f483044e434084a8c5a',
 ('rbac.authorization.k8s.io/v1', 'Role', 'cristexhub-prod', 'argocd-application-controller-cristexhub-prod'): 'c40a189cdf4a3b864fae8bb64f06b0473aae2b47771f1c22ddf4a86f0f669fc4',
 ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'cristexhub-prod', 'argocd-application-controller-cristexhub-prod'): 'd0f0b78eb5960d368631b4d0ed9dd0371bacf19efa0e1c7ba01599d94bb75a83',
 ('v1', 'Secret', 'argocd', 'argocd-cluster-cristexhub-prod'): '3d8901d60df585bf9b5110e99fee323266acb9d8e41dbf55d174d82a1358d538'}

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
_TRANSITION_MAX_CONFLICT_RETRIES = 3


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
        "destination": {"name": _TRANSITION_ALIAS, "server": "", "namespace": _TRANSITION_NAMESPACE},
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


_TRANSITION_FINAL_PROJECT_SPEC = _transition_project_spec([{"name": _TRANSITION_ALIAS, "namespace": _TRANSITION_NAMESPACE}])
_TRANSITION_TEMP_PROJECT_SPEC = _transition_project_spec([
    {"server": _TRANSITION_OLD_SERVER, "namespace": _TRANSITION_NAMESPACE},
    {"name": _TRANSITION_ALIAS, "namespace": _TRANSITION_NAMESPACE},
])
_TRANSITION_LEGACY_PROJECT_SPEC = _transition_project_spec([{"server": _TRANSITION_OLD_SERVER, "namespace": _TRANSITION_NAMESPACE}])
_TRANSITION_FINAL_APPLICATION_SPEC = _transition_application_spec()
_TRANSITION_LEGACY_APPLICATION_SPEC = copy.deepcopy(_TRANSITION_FINAL_APPLICATION_SPEC)
_TRANSITION_LEGACY_APPLICATION_SPEC["destination"] = {"server": _TRANSITION_OLD_SERVER, "namespace": _TRANSITION_NAMESPACE}
_TRANSITION_UIDS = {
    "AppProject": LEGACY_TRANSITION_UIDS["AppProject"],
    "Application": LEGACY_TRANSITION_UIDS["Application"],
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
        "legacy" if project_spec == _TRANSITION_LEGACY_PROJECT_SPEC else None
    )
    application_state = (
        "final" if application_spec == _TRANSITION_FINAL_APPLICATION_SPEC else
        "legacy" if application_spec == _TRANSITION_LEGACY_APPLICATION_SPEC else None
    )
    if project_state is None or application_state is None:
        raise ValueError("transition object scope is not an exact legacy, transitional, or final form")
    if (project_state, application_state) in {("legacy", "final"), ("final", "legacy")}:
        raise ValueError("unsafe mixed transition state")
    return project_state, application_state


def _transition_plan(project_state: str, application_state: str) -> list[str]:
    states = (project_state, application_state)
    if states == ("final", "final"):
        return []
    if states == ("legacy", "legacy"):
        return ["AppProject:transition", "Application:final", "AppProject:final"]
    if states == ("transition", "legacy"):
        return ["Application:final", "AppProject:final"]
    if states == ("transition", "final"):
        return ["AppProject:final"]
    raise ValueError("unsupported transition state")


def _transition_api_path(kind: str) -> str:
    resource = "appprojects" if kind == "AppProject" else "applications"
    return f"/apis/{_TRANSITION_API_VERSION}/namespaces/{_TRANSITION_ARGO_NAMESPACE}/{resource}/{_TRANSITION_NAME}"


def _transition_get(api: Any, kind: str) -> dict[str, Any]:
    result = api.call_api(_transition_api_path(kind), "GET", path_params={}, query_params=[], header_params={"Accept": "application/json"}, body=None, post_params=[], files={}, response_type="object", auth_settings=["BearerToken"], async_req=False, _return_http_data_only=True, collection_formats={}, _request_timeout=30)
    if not isinstance(result, dict):
        raise ValueError("transition GET did not return an object")
    return result


def _transition_put(api: Any, kind: str, body: dict[str, Any]) -> Any:
    return api.call_api(_transition_api_path(kind), "PUT", path_params={}, query_params=[], header_params={"Accept": "application/json", "Content-Type": "application/json"}, body=body, post_params=[], files={}, response_type="object", auth_settings=["BearerToken"], async_req=False, _return_http_data_only=True, collection_formats={}, _request_timeout=30)


def _transition_cas_update(
    api: Any,
    kind: str,
    desired_spec: dict[str, Any],
    allowed_current_specs: list[dict[str, Any]],
    retries: int = _TRANSITION_MAX_CONFLICT_RETRIES,
) -> bool:
    try:
        from kubernetes.client.rest import ApiException
    except ImportError:  # pragma: no cover
        ApiException = Exception  # type: ignore[assignment,misc]
    for _attempt in range(retries):
        current = _transition_get(api, kind)
        expected_uid = _TRANSITION_UIDS[kind]
        if not _transition_metadata_safe(current, kind) or current.get("metadata", {}).get("uid") != expected_uid:
            raise ValueError(f"{kind} identity changed during transition")
        if current.get("spec") == desired_spec:
            return False
        if current.get("spec") not in allowed_current_specs:
            raise ValueError(f"{kind} changed to an unsafe transition state")
        resource_version = current.get("metadata", {}).get("resourceVersion")
        if not isinstance(resource_version, str) or not resource_version.isdigit():
            raise ValueError(f"{kind} has no numeric resourceVersion")
        body = {
            "apiVersion": _TRANSITION_API_VERSION,
            "kind": kind,
            "metadata": {"name": _TRANSITION_NAME, "namespace": _TRANSITION_ARGO_NAMESPACE, "uid": expected_uid, "resourceVersion": resource_version, "labels": copy.deepcopy(_TRANSITION_LABELS)},
            "spec": copy.deepcopy(desired_spec),
        }
        try:
            _transition_put(api, kind, body)
            return True
        except ApiException as exc:
            if getattr(exc, "status", None) == 409:
                continue
            raise
    raise RuntimeError(f"{kind} resourceVersion conflict did not converge after {retries} retries")


def run_alias_transition(kubeconfig: str, project_definition: dict[str, Any], application_definition: dict[str, Any], check_mode: bool) -> dict[str, Any]:
    if object_identity(project_definition) != _transition_identity("AppProject") or object_identity(application_definition) != _transition_identity("Application"):
        raise ValueError("exact AppProject/Application identities required")
    if project_definition.get("spec") != _TRANSITION_FINAL_PROJECT_SPEC or application_definition.get("spec") != _TRANSITION_FINAL_APPLICATION_SPEC:
        raise ValueError("final transition definitions drifted")
    from kubernetes import client, config
    config.load_kube_config(config_file=kubeconfig)
    api = client.ApiClient()
    project = _transition_get(api, "AppProject")
    application = _transition_get(api, "Application")
    project_state, application_state = _transition_classify(project, application)
    plan = _transition_plan(project_state, application_state)
    if check_mode:
        return {"changed": bool(plan), "transition_steps": plan, "transition_change_count": len(plan)}
    changed: list[str] = []
    for step in plan:
        kind, target = step.split(":", 1)
        desired = _TRANSITION_TEMP_PROJECT_SPEC if (kind, target) == ("AppProject", "transition") else _TRANSITION_FINAL_PROJECT_SPEC if kind == "AppProject" else _TRANSITION_FINAL_APPLICATION_SPEC
        allowed = (
            [_TRANSITION_LEGACY_PROJECT_SPEC]
            if (kind, target) == ("AppProject", "transition")
            else [_TRANSITION_LEGACY_APPLICATION_SPEC]
            if kind == "Application"
            else [_TRANSITION_TEMP_PROJECT_SPEC]
        )
        if _transition_cas_update(api, kind, desired, allowed):
            changed.append(step)
    final_project = _transition_get(api, "AppProject")
    final_application = _transition_get(api, "Application")
    if _transition_classify(final_project, final_application) != ("final", "final"):
        raise RuntimeError("alias transition did not converge to final state")
    return {"changed": bool(changed), "transition_steps": changed, "transition_change_count": len(changed)}


class ActionModule(KubernetesActionModule):
    """Permit only the five-object, guarded CristexHub PROD registration."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        args = self._task.args
        transition_mode = args.get("transition") is True
        definition = args.get("definition") if not transition_mode else args.get("project_definition")
        task_vars = task_vars or {}
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if context.CLIARGS.get("start_at_task") or context.CLIARGS.get("step") or tags not in ([], ["all"]) or skip_tags:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: task selection controls are forbidden"}
        repository_root = str(Path(os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")).resolve())
        if repository_root != EXPECTED_REPOSITORY_ROOT or source != EXPECTED_REPOSITORY_ROOT + TASK_SUFFIX:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical registration task source"}
        if transition_mode:
            if set(args) != TRANSITION_ARGS or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml":
                return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing alias transition arguments"}
            application_definition = args.get("application_definition")
            if not isinstance(definition, dict) or not isinstance(application_definition, dict):
                return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: alias transition definitions are required"}
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
        if meta.get("labels", {}).get("cristex.io/component") != "cristexhub-prod-registration" or meta.get("labels", {}).get("app.kubernetes.io/managed-by") != "ansible":
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: ownership labels drifted"}
        token = os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_TOKEN", "")
        attestation = os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ATTESTATION_FILE", "")
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except (OSError, ValueError):
            state, content = None, ""
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
                "legacy_transition_kinds",
                "target_transition_kinds",
                "legacy_transition_change_count",
                "legacy_transition_uids",
                "legacy_transition_spec_hashes",
                "legacy_transition_manifest_hashes",
                "legacy_transition_metadata_hash",
                "prestate_object_count",
                "prestate_bindings",
                "transition_change_count",
                "no_delete_path",
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
            and valid_transition_pair(
                binding.get("legacy_transition_kinds"),
                binding.get("target_transition_kinds"),
            )
            and str(binding.get("legacy_transition_change_count")) == str(len(binding.get("legacy_transition_kinds")))
            and binding.get("legacy_transition_uids") == LEGACY_TRANSITION_UIDS
            and binding.get("legacy_transition_spec_hashes") == LEGACY_TRANSITION_SPEC_HASHES
            and binding.get("legacy_transition_manifest_hashes") == LEGACY_TRANSITION_MANIFEST_HASHES
            and binding.get("legacy_transition_metadata_hash") == LEGACY_TRANSITION_METADATA_HASH
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
            and str(binding.get("transition_change_count")) in ("0", "1", "2")
            and str(binding.get("transition_change_count")) == str(binding.get("legacy_transition_change_count"))
            and strict_true(binding.get("no_delete_path"))
        )
        prestate = bound_prestate(binding.get("prestate_bindings"), identity)
        resource_version = meta.get("resourceVersion")
        if not valid_binding or (not transition_mode and (prestate is None or resource_version != prestate.get("resourceVersion"))):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: missing or changed UID/resourceVersion precondition"}
        valid = (
            valid_binding
            and os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and state is not None and stat.S_ISREG(state.st_mode) and not stat.S_ISLNK(state.st_mode)
            and stat.S_IMODE(state.st_mode) == 0o600 and state.st_uid == os.getuid()
            and content == f"{token}:entrypoint"
            and strict_true(task_vars.get("cristexhub_prod_registration_approved"))
            and task_vars.get("cristexhub_prod_registration_state") == "present"
        )
        if not valid:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: registration requires the guarded attestation and complete preflight binding"}
        if transition_mode:
            try:
                return run_alias_transition(
                    args["kubeconfig"],
                    definition,
                    application_definition,
                    bool(context.CLIARGS.get("check") or getattr(self._task, "check_mode", False)),
                )
            except Exception as exc:
                return {"changed": False, "failed": True, "msg": f"PROD_ALIAS_TRANSITION_GUARD: {type(exc).__name__}"}
        self._task.action = "kubernetes.core.k8s"
        return super().run(tmp=tmp, task_vars=task_vars)
