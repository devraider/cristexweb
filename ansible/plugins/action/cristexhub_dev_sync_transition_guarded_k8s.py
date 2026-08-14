from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

import yaml
from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import ActionModule as KubernetesActionModule

EXPECTED = {
    ("argoproj.io/v1alpha1", "AppProject", "argocd", "cristexhub-dev"),
    ("argoproj.io/v1alpha1", "Application", "argocd", "cristexhub-dev"),
}
ARGS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
TASK_SUFFIX = "/ansible/roles/cristexhub_dev_sync_transition/tasks/main.yml"
EXPECTED_HASHES: dict[tuple[str, str, str, str], str] = {}


def canonical(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _source_hashes(repository_root: str) -> dict[tuple[str, str, str, str], str]:
    files = {
        ("argoproj.io/v1alpha1", "AppProject", "argocd", "cristexhub-dev"): "config/appproject-cristexhub-dev-automated.yaml",
        ("argoproj.io/v1alpha1", "Application", "argocd", "cristexhub-dev"): "config/application-cristexhub-dev-automated.yaml",
    }
    result: dict[tuple[str, str, str, str], str] = {}
    for identity, relative in files.items():
        try:
            result[identity] = canonical(yaml.safe_load((Path(repository_root) / "ansible/files/components/cristexhub-dev-sync-transition" / relative).read_text()))
        except (OSError, ValueError, yaml.YAMLError):
            return {}
    return result


class ActionModule(KubernetesActionModule):
    """Permit only the two-object, gate-checked automated-sync transition."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        repository_root = str(Path(os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")).resolve())
        if source != repository_root + TASK_SUFFIX:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical sync transition task source"}
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if context.CLIARGS.get("start_at_task") or context.CLIARGS.get("step") or tags not in ([], ["all"]) or skip_tags:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: task selection controls are forbidden"}
        if not isinstance(definition, dict) or set(args) != ARGS or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml" or args.get("wait") is not False or args.get("wait_timeout") != 60:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing transition arguments"}
        meta = definition.get("metadata") or {}
        identity = (definition.get("apiVersion"), definition.get("kind"), meta.get("namespace", ""), meta.get("name"))
        if identity not in EXPECTED or canonical(definition) != _source_hashes(repository_root).get(identity):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unknown or drifted transition object"}
        if meta.get("labels", {}).get("cristex.io/component") != "cristexhub-dev-sync-transition" or meta.get("labels", {}).get("app.kubernetes.io/managed-by") != "ansible":
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: transition ownership labels drifted"}
        token = os.environ.get("CRISTEXWEB_ARGOCD_SYNC_TRANSITION_TOKEN", "")
        attestation = os.environ.get("CRISTEXWEB_ARGOCD_SYNC_TRANSITION_ATTESTATION_FILE", "")
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except (OSError, ValueError):
            state, content = None, ""
        valid = (
            os.environ.get("CRISTEXWEB_ARGOCD_SYNC_TRANSITION_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and state is not None and stat.S_ISREG(state.st_mode) and not stat.S_ISLNK(state.st_mode)
            and stat.S_IMODE(state.st_mode) == 0o600 and state.st_uid == os.getuid()
            and content == f"{token}:entrypoint"
            and task_vars.get("cristexhub_dev_sync_transition_approved") is True
            and task_vars.get("cristexhub_dev_sync_transition_state") == "present"
        )
        if not valid:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: transition requires the guarded attestation"}
        self._task.action = "kubernetes.core.k8s"
        return super().run(tmp=tmp, task_vars=task_vars)
