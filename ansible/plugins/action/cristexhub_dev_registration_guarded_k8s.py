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
    ("argoproj.io/v1alpha1", "AppProject", "argocd", "cristexhub-dev"),
    ("argoproj.io/v1alpha1", "Application", "argocd", "cristexhub-dev"),
    ("rbac.authorization.k8s.io/v1", "Role", "cristexhub-dev", "argocd-application-controller-cristexhub-dev"),
    ("rbac.authorization.k8s.io/v1", "RoleBinding", "cristexhub-dev", "argocd-application-controller-cristexhub-dev"),
    ("v1", "Secret", "argocd", "argocd-cluster-cristexhub-dev"),
}
ARGS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
TASK_SUFFIX = "/ansible/roles/cristexhub_dev_registration/tasks/main.yml"
EXPECTED_HASHES: dict[tuple[str, str, str, str], str] = {('argoproj.io/v1alpha1', 'AppProject', 'argocd', 'cristexhub-dev'): '0da42198c4e7e8f2ddb0d5066ad25de624af99d67a50569a0e155b0b769f0576',
 ('argoproj.io/v1alpha1', 'Application', 'argocd', 'cristexhub-dev'): 'be0425a38e3f07613d6d1cff29c9c88c1b849c1a5a874c6f57431d4caf2b96a8',
 ('rbac.authorization.k8s.io/v1', 'Role', 'cristexhub-dev', 'argocd-application-controller-cristexhub-dev'): '964edcc8a93400aa28f5dbda167e0e1a928362c2cf1b5140aa25cc26005f484d',
 ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'cristexhub-dev', 'argocd-application-controller-cristexhub-dev'): '653a3f04f29b3962bc30f7fb02f4db90faea5eb7fec50df8792fabe8b55d1d71',
 ('v1', 'Secret', 'argocd', 'argocd-cluster-cristexhub-dev'): '3ed366a3df3e87f8d79c60a2122e63b29b4246f61f350eb5bc8fe6c2e8034793'}

def canonical(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ActionModule(KubernetesActionModule):
    """Permit only the six-object, guarded CristexHub DEV registration."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        repository_root = str(Path(os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")).resolve())
        if source != repository_root + TASK_SUFFIX:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical registration task source"}
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if context.CLIARGS.get("start_at_task") or context.CLIARGS.get("step") or tags not in ([], ["all"]) or skip_tags:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: task selection controls are forbidden"}
        if not isinstance(definition, dict) or set(args) != ARGS or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml" or args.get("wait") is not False or args.get("wait_timeout") != 60:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing registration arguments"}
        meta = definition.get("metadata") or {}
        identity = (definition.get("apiVersion"), definition.get("kind"), meta.get("namespace", ""), meta.get("name"))
        if identity not in EXPECTED or canonical(definition) != EXPECTED_HASHES.get(identity):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unknown or drifted registration object"}
        if meta.get("labels", {}).get("cristex.io/component") != "cristexhub-dev-registration" or meta.get("labels", {}).get("app.kubernetes.io/managed-by") != "ansible":
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: ownership labels drifted"}
        token = os.environ.get("CRISTEXWEB_CRISTEXHUB_DEV_REGISTRATION_TOKEN", "")
        attestation = os.environ.get("CRISTEXWEB_CRISTEXHUB_DEV_REGISTRATION_ATTESTATION_FILE", "")
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except (OSError, ValueError):
            state, content = None, ""
        valid = (
            os.environ.get("CRISTEXWEB_CRISTEXHUB_DEV_REGISTRATION_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and state is not None and stat.S_ISREG(state.st_mode) and not stat.S_ISLNK(state.st_mode)
            and stat.S_IMODE(state.st_mode) == 0o600 and state.st_uid == os.getuid()
            and content == f"{token}:entrypoint"
            and task_vars.get("cristexhub_dev_registration_approved") is True
            and task_vars.get("cristexhub_dev_registration_state") == "present"
        )
        if not valid:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: registration requires the guarded attestation"}
        self._task.action = "kubernetes.core.k8s"
        return super().run(tmp=tmp, task_vars=task_vars)
