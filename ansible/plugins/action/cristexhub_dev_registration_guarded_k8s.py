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
    ("rbac.authorization.k8s.io/v1", "ClusterRole", "", "argocd-application-controller-cristexhub-dev-read"),
    ("rbac.authorization.k8s.io/v1", "ClusterRoleBinding", "", "argocd-application-controller-cristexhub-dev-read"),
}
ARGS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
TASK_SUFFIX = "/ansible/roles/cristexhub_dev_registration/tasks/main.yml"
EXPECTED_HASHES: dict[tuple[str, str, str, str], str] = {('argoproj.io/v1alpha1', 'AppProject', 'argocd', 'cristexhub-dev'): 'dfcd394cf080d8bf6828ab4fc2e8efb51cd6bb1d640666a6544a2dba659aabe6',
 ('argoproj.io/v1alpha1', 'Application', 'argocd', 'cristexhub-dev'): 'f98759d1f8d7742c888dcf7f8bbbe14e9e1c97071afbb6c240f4c5d123eaab3e',
 ('rbac.authorization.k8s.io/v1', 'ClusterRole', '', 'argocd-application-controller-cristexhub-dev-read'): 'f183ca0f2ddb7159c72448080134be7ab5f27ed5604221451147c990f6a4c627',
 ('rbac.authorization.k8s.io/v1', 'ClusterRoleBinding', '', 'argocd-application-controller-cristexhub-dev-read'): '34702eba77569edf99d133359a6e216a09f4a1016852b6d83953fa54ead49bc1',
 ('rbac.authorization.k8s.io/v1', 'Role', 'cristexhub-dev', 'argocd-application-controller-cristexhub-dev'): '43547fcbb3c42e6c222461581d6a33ce0f88490464b919d5869ed7c8424bcf26',
 ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'cristexhub-dev', 'argocd-application-controller-cristexhub-dev'): '653a3f04f29b3962bc30f7fb02f4db90faea5eb7fec50df8792fabe8b55d1d71'}


def canonical(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ActionModule(KubernetesActionModule):
    """Permit only the four-object, check-only CristexHub DEV registration."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        source = str(self._task.get_path()).rsplit(":", 1)[0]
        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        if not source.endswith(TASK_SUFFIX):
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
