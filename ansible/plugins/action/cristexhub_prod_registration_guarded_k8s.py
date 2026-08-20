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
    ("argoproj.io/v1alpha1", "AppProject", "argocd", "cristexhub-prod"),
    ("argoproj.io/v1alpha1", "Application", "argocd", "cristexhub-prod"),
    ("rbac.authorization.k8s.io/v1", "Role", "cristexhub-prod", "argocd-application-controller-cristexhub-prod"),
    ("rbac.authorization.k8s.io/v1", "RoleBinding", "cristexhub-prod", "argocd-application-controller-cristexhub-prod"),
    ("v1", "Secret", "argocd", "argocd-cluster-cristexhub-prod"),
}
ARGS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
EXPECTED_REPOSITORY_ROOT = "/home/paul/projects/cristexweb"
TASK_SUFFIX = "/ansible/roles/cristexhub_prod_registration/tasks/main.yml"
EXPECTED_HASHES: dict[tuple[str, str, str, str], str] = {('argoproj.io/v1alpha1', 'AppProject', 'argocd', 'cristexhub-prod'): '4625c40d6030961d799f7b04b386f5a840273bc96b5d7031a507bf48ab57afa2',
 ('argoproj.io/v1alpha1', 'Application', 'argocd', 'cristexhub-prod'): '29a3bd87c83d881e73f6e50739e9b510d89f58d2d851be93276658f1ad35bdf1',
 ('rbac.authorization.k8s.io/v1', 'Role', 'cristexhub-prod', 'argocd-application-controller-cristexhub-prod'): 'c40a189cdf4a3b864fae8bb64f06b0473aae2b47771f1c22ddf4a86f0f669fc4',
 ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'cristexhub-prod', 'argocd-application-controller-cristexhub-prod'): 'd0f0b78eb5960d368631b4d0ed9dd0371bacf19efa0e1c7ba01599d94bb75a83',
 ('v1', 'Secret', 'argocd', 'argocd-cluster-cristexhub-prod'): '3d8901d60df585bf9b5110e99fee323266acb9d8e41dbf55d174d82a1358d538'}

def canonical(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ActionModule(KubernetesActionModule):
    """Permit only the five-object, guarded CristexHub PROD registration."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if context.CLIARGS.get("start_at_task") or context.CLIARGS.get("step") or tags not in ([], ["all"]) or skip_tags:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: task selection controls are forbidden"}
        repository_root = str(Path(os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")).resolve())
        if repository_root != EXPECTED_REPOSITORY_ROOT or source != EXPECTED_REPOSITORY_ROOT + TASK_SUFFIX:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical registration task source"}
        if not isinstance(definition, dict) or set(args) != ARGS or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml" or args.get("wait") is not False or args.get("wait_timeout") != 60:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing registration arguments"}
        meta = definition.get("metadata") or {}
        identity = (definition.get("apiVersion"), definition.get("kind"), meta.get("namespace", ""), meta.get("name"))
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
                "prestate_names",
                "object_count",
                "namespace_contract",
                "repository_contract",
                "revision",
                "no_delete_path",
            }
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding.get("manifest_names") == expected_names
            and binding.get("prestate_names") == expected_names
            and binding.get("object_count") in (5, "5")
            and strict_true(binding.get("namespace_contract"))
            and strict_true(binding.get("repository_contract"))
            and binding.get("revision") == "751885a42798d282e168131db147f13694a0a621"
            and strict_true(binding.get("no_delete_path"))
        )
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
        self._task.action = "kubernetes.core.k8s"
        return super().run(tmp=tmp, task_vars=task_vars)
