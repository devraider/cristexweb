from __future__ import annotations

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
    ("argoproj.io/v1alpha1", "AppProject", "argocd", "reactive-resume-dev"),
    ("argoproj.io/v1alpha1", "Application", "argocd", "reactive-resume-dev"),
    ("rbac.authorization.k8s.io/v1", "Role", "cristexhub-dev", "argocd-application-controller-reactive-resume-dev"),
    ("rbac.authorization.k8s.io/v1", "RoleBinding", "cristexhub-dev", "argocd-application-controller-reactive-resume-dev"),
    ("v1", "Secret", "argocd", "argocd-cluster-reactive-resume-dev"),
}
EXPECTED_HANDOFF = {
    ("apps/v1", "Deployment", "cristexhub-dev", "reactive-resume-dev"),
    ("networking.k8s.io/v1", "Ingress", "cristexhub-dev", "reactive-resume-dev-private"),
    ("batch/v1", "Job", "cristexhub-dev", "reactive-resume-dev-migrate"),
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-default-deny"),
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-egress"),
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-route-allow-traefik"),
    ("v1", "Service", "cristexhub-dev", "reactive-resume-dev"),
    ("v1", "ServiceAccount", "cristexhub-dev", "reactive-resume-dev"),
}
ARGS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
TASK_SUFFIX = "/ansible/roles/reactive_resume_dev_argocd_registration/tasks/main.yml"
EXPECTED_REVISION = "dd7d4cedd902e68266d9713d1dbb8e90f0b529b1"
EXPECTED_HASHES: dict[tuple[str, str, str, str], str] = {
    ("argoproj.io/v1alpha1", "Application", "argocd", "reactive-resume-dev"): "c3efab9afeb81cc28c5e7ee7142c9e1eaf7352d507e110d381c4810ac0578aaa",
    ("argoproj.io/v1alpha1", "AppProject", "argocd", "reactive-resume-dev"): "1a9abdaedca1ea155342087f85c255b2ed0545770379b2912352aac0997ace02",
    ("v1", "Secret", "argocd", "argocd-cluster-reactive-resume-dev"): "7bc10653f97ab05c96f515b555a51b9f7a6f219722e694facff518f278da14ea",
    ("rbac.authorization.k8s.io/v1", "Role", "cristexhub-dev", "argocd-application-controller-reactive-resume-dev"): "223fd10d51f8aad55d28b40a0f1bd85c6a44fb809e9d276aff256a18450e3f8e",
    ("rbac.authorization.k8s.io/v1", "RoleBinding", "cristexhub-dev", "argocd-application-controller-reactive-resume-dev"): "0d1c6d8b3bea0e358296ad96ef33ccfb7aaa545e753688cfcd79f0b0c57085ee",
}


def canonical(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _strict_true(value: Any) -> bool:
    return value is True or (type(value).__name__ == "_AnsibleTaggedBool" and bool(value)) or (type(value).__name__ == "_AnsibleTaggedStr" and value == "true")


class ActionModule(KubernetesActionModule):
    """Permit only the five-object, non-synchronizing RR DEV registration."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        repository_root = str(Path(os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")).resolve())
        if source != repository_root + TASK_SUFFIX:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical Reactive Resume DEV registration task source"}
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if context.CLIARGS.get("start_at_task") or context.CLIARGS.get("step") or tags not in ([], ["all"]) or skip_tags:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: task selection controls are forbidden"}
        if not isinstance(definition, dict) or set(args) != ARGS or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml" or args.get("wait") is not False or args.get("wait_timeout") != 60:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing Reactive Resume DEV registration arguments"}
        meta = definition.get("metadata") or {}
        identity = (definition.get("apiVersion"), definition.get("kind"), meta.get("namespace", ""), meta.get("name"))
        if identity not in EXPECTED or canonical(definition) != EXPECTED_HASHES.get(identity):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unknown or drifted Reactive Resume DEV registration object"}
        if meta.get("labels", {}).get("cristex.io/component") != "reactive-resume-dev-argocd-registration" or meta.get("labels", {}).get("app.kubernetes.io/managed-by") != "ansible":
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: registration ownership labels drifted"}
        token = os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_ARGOCD_REGISTRATION_TOKEN", "")
        attestation = os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_ARGOCD_REGISTRATION_ATTESTATION_FILE", "")
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except (OSError, ValueError):
            state, content = None, ""
        binding = task_vars.get("reactive_resume_dev_argocd_registration_internal_preflight_binding", {})
        valid_binding = (
            isinstance(binding, dict)
            and set(binding) == {
                "attestation_sha256", "manifest_names", "prestate_names", "handoff_names",
                "object_count", "handoff_object_count", "namespace_contract", "repository_contract",
                "dependency_count", "dependency_names", "workload_dependencies_ready",
                "exact_application_source_contract", "revision", "no_dual_reconciliation", "no_delete_path",
            }
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding.get("manifest_names") == sorted(identity[3] for identity in EXPECTED)
            and binding.get("prestate_names") == sorted(identity[3] for identity in EXPECTED)
            and binding.get("handoff_names") == sorted(identity[3] for identity in EXPECTED_HANDOFF)
            and binding.get("object_count") in (5, "5")
            and binding.get("handoff_object_count") in (8, "8")
            and _strict_true(binding.get("namespace_contract"))
            and _strict_true(binding.get("repository_contract"))
            and binding.get("dependency_count") in (6, "6")
            and binding.get("dependency_names") == sorted((
                "cristexhub-ghcr-pull", "reactive-resume-dev-migration", "reactive-resume-dev-object-storage-ca",
                "reactive-resume-dev-postgresql-ca", "reactive-resume-dev-runtime", "reactive-resume-dev-tls",
            ))
            and _strict_true(binding.get("workload_dependencies_ready"))
            and _strict_true(binding.get("exact_application_source_contract"))
            and binding.get("revision") == EXPECTED_REVISION
            and _strict_true(binding.get("no_dual_reconciliation"))
            and _strict_true(binding.get("no_delete_path"))
        )
        valid = (
            valid_binding
            and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_ARGOCD_REGISTRATION_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and state is not None and stat.S_ISREG(state.st_mode) and not stat.S_ISLNK(state.st_mode)
            and stat.S_IMODE(state.st_mode) == 0o600 and state.st_uid == os.getuid()
            and content == f"{token}:entrypoint"
            and _strict_true(task_vars.get("reactive_resume_dev_argocd_registration_approved"))
            and task_vars.get("reactive_resume_dev_argocd_registration_state") == "present"
        )
        if not valid:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: registration requires the guarded attestation and complete handoff binding"}
        self._task.action = "kubernetes.core.k8s"
        return super().run(tmp=tmp, task_vars=task_vars)
