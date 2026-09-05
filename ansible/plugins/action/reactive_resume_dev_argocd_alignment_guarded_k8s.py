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

ARGS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
TASK_SUFFIX = "/ansible/roles/reactive_resume_dev_argocd_alignment/tasks/main.yml"
EXPECTED_IDENTITY_SET_SHA256 = "a1b576db27f865a2988f00420022303943c50ebf2422d172d147f7ddac03e712"
EXPECTED = {
    ("apps/v1", "Deployment", "cristexhub-dev", "reactive-resume-dev"),
    ("networking.k8s.io/v1", "Ingress", "cristexhub-dev", "reactive-resume-dev-private"),
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-allow-backend"),
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-default-deny"),
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-egress"),
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-route-allow-traefik"),
    ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "shared-postgresql-ingress"),
    ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "keycloak-allow-reactive-resume-dev"),
    ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "oidc-connect-proxy-allow-reactive-resume-dev"),
    ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "reactive-resume-object-storage-allow-dev"),
    ("v1", "Service", "cristexhub-dev", "reactive-resume-dev"),
    ("v1", "ServiceAccount", "cristexhub-dev", "reactive-resume-dev"),
}
EXPECTED_HASHES = {
    ("apps/v1", "Deployment", "cristexhub-dev", "reactive-resume-dev"): "82f439133999c5f6bd888cfa0943d1ed5a22e68f5c54a6ca48cf19638d231599",
    ("networking.k8s.io/v1", "Ingress", "cristexhub-dev", "reactive-resume-dev-private"): "694883a0e10310e893cb24f238dfa49af5613cc77624e82072f5e684eb5b6389",
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-allow-backend"): "60025e8937b19bcc418fc92ed2e54c65770c35a0132ba7736cd3d2bb4a0dea89",
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-default-deny"): "1b858a6e58228abc563072b4d1dee78042b05f20aeb9e522a2a37398fcc3ac6b",
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-egress"): "3b26ef586e526506dccd955675ccceb2776e294b8d710facbe3c73236ae7e178",
    ("networking.k8s.io/v1", "NetworkPolicy", "cristexhub-dev", "reactive-resume-dev-route-allow-traefik"): "26c970db8f44cfd3765af69e8b668e258b128c502f436f3d6882f83f300cdbd1",
    ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "shared-postgresql-ingress"): "159f9f00ee9758bf558e3c8da921491247830988f0eaa9fd029884e98cfced1e",
    ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "keycloak-allow-reactive-resume-dev"): "3108c21cd11de7dba7f28957a09f63dbccf90523d28f5aec7a4c4d550699f562",
    ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "oidc-connect-proxy-allow-reactive-resume-dev"): "4279fb9976ce6a7e0d3983fd34291c35bad1c5b46159e4ec86b761f28e5c4e42",
    ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "reactive-resume-object-storage-allow-dev"): "9388927d9484b41d9554baf40cec5c546a7a0a1928ea8308d9680e9ed4a2d545",
    ("v1", "Service", "cristexhub-dev", "reactive-resume-dev"): "808bda3a8337604bccb19d3771cd4f8c484ea73cef413102993061366fd67f10",
    ("v1", "ServiceAccount", "cristexhub-dev", "reactive-resume-dev"): "d72cf9455d8ea2248663870dcbf1f0f971c4c89c8e4ce021efc0f9353aea7689",
}


def canonical(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def strict_true(value: Any) -> bool:
    return value is True or (type(value).__name__ == "_AnsibleTaggedBool" and bool(value)) or (type(value).__name__ == "_AnsibleTaggedStr" and value == "true")


class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only 12-object alignment lane."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        task_vars = task_vars or {}
        source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        repository_root = str(Path(os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")).resolve())
        if source != repository_root + TASK_SUFFIX:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical alignment task source"}
        tags = list(context.CLIARGS.get("tags") or [])
        if context.CLIARGS.get("start_at_task") or context.CLIARGS.get("step") or tags not in ([], ["all"]) or context.CLIARGS.get("skip_tags"):
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: task selection controls are forbidden"}
        args = self._task.args
        definition = args.get("definition")
        if not isinstance(definition, dict) or set(args) != ARGS or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml" or args.get("wait") is not False or args.get("wait_timeout") != 60:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing alignment arguments"}
        metadata = definition.get("metadata") or {}
        identity = (definition.get("apiVersion"), definition.get("kind"), metadata.get("namespace", ""), metadata.get("name"))
        if identity not in EXPECTED or canonical(definition) != EXPECTED_HASHES[identity]:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: unknown or drifted alignment object"}
        labels = metadata.get("labels", {})
        if labels.get("app.kubernetes.io/managed-by") != "ansible" or (labels.get("cristex.io/bootstrap-writer") != "ansible" and labels.get("app.kubernetes.io/bootstrap-writer") != "ansible"):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: alignment ownership labels drifted"}
        token = os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_ARGOCD_ALIGNMENT_TOKEN", "")
        attestation = os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_ARGOCD_ALIGNMENT_ATTESTATION_FILE", "")
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except (OSError, ValueError):
            state, content = None, ""
        binding = task_vars.get("reactive_resume_dev_argocd_alignment_internal_preflight_binding", {})
        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding.get("identity_set_sha256") == EXPECTED_IDENTITY_SET_SHA256
            and int(binding.get("object_count", -1)) == 12
            and int(binding.get("prestate_count", -1)) == 12
            and strict_true(binding.get("no_delete_path"))
            and strict_true(binding.get("no_job"))
            and strict_true(binding.get("no_secret"))
            and binding.get("scope") == "reactive-resume-dev-8-plus-destination-networkpolicies-4"
        )
        valid = (
            valid_binding
            and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_ARGOCD_ALIGNMENT_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and state is not None and stat.S_ISREG(state.st_mode) and not stat.S_ISLNK(state.st_mode)
            and stat.S_IMODE(state.st_mode) == 0o600 and state.st_uid == os.getuid()
            and content == f"{token}:entrypoint"
            and strict_true(task_vars.get("reactive_resume_dev_argocd_alignment_approved"))
            and task_vars.get("reactive_resume_dev_argocd_alignment_state") == "present"
        )
        if not valid:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: alignment requires guarded attestation and complete preflight"}
        self._task.action = "kubernetes.core.k8s"
        return super().run(tmp=tmp, task_vars=task_vars)
