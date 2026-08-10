from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import (
    ActionModule as KubernetesActionModule,
)

_EXPECTED_OBJECT_HASHES: dict[tuple[str, str, str, str], str] = {
    ("admissionregistration.k8s.io/v1", "ValidatingAdmissionPolicy", "", "infisical-argocd-alternate-target-boundary"): 'e83729093168045791912a4802ab4d930250241dfd6186181eb89d51ca8955d8',
    ("admissionregistration.k8s.io/v1", "ValidatingAdmissionPolicy", "", "infisical-argocd-secret-write-boundary"): '723f7958ae2bb48f8ec54d8272592f0b1963be05b25485b7442e1309bab87471',
    ("admissionregistration.k8s.io/v1", "ValidatingAdmissionPolicy", "", "infisical-argocd-static-secret-boundary"): 'f24ea8526f398a25bfb7ac8867ecfa7a7358643f8d5a5a2b0d1d30b91c21038b',
    ("admissionregistration.k8s.io/v1", "ValidatingAdmissionPolicyBinding", "", "infisical-argocd-alternate-target-boundary"): '9fe628a53a33301c095b1a6ac3c6007fde1377ced3e1e5800960f79133952477',
    ("admissionregistration.k8s.io/v1", "ValidatingAdmissionPolicyBinding", "", "infisical-argocd-secret-write-boundary"): '07ebbfc58d15281eed817e054f7d6483bbed21a99b0d10deb9322cf0e3fbc631',
    ("admissionregistration.k8s.io/v1", "ValidatingAdmissionPolicyBinding", "", "infisical-argocd-static-secret-boundary"): '11bf7f48ae4e746136a8d64fe6c1b8b090738424c06eaafaf00d0f79fd32826c',
    ("rbac.authorization.k8s.io/v1", "Role", "argocd", "infisical-argocd-secret-writer"): '625fab82d18ec8fe8ec3b50d509d3f9415cb36e13ac52d736ce2d3877ffee3bd',
    ("rbac.authorization.k8s.io/v1", "RoleBinding", "argocd", "infisical-argocd-secret-writer"): '355d7899cdcbc9a86c7bc21741d46f99d3c0d4905978ec44964b24c6ac69713b',
    ("secrets.infisical.com/v1beta1", "InfisicalAuth", "argocd", "argocd-infisical-auth"): '88518d0fcc938aea1109edba6ac793c7a8b35d65c98160556b360f450c605c26',
    ("secrets.infisical.com/v1beta1", "InfisicalConnection", "argocd", "infisical-cloud"): 'e8539e82bbb91f590d829610c3e4c78b640cf8571a8d58f1b7e957e7123fa41c',
    ("secrets.infisical.com/v1beta1", "InfisicalStaticSecret", "argocd", "argocd-infisical-secrets"): 'bfded8e5ce5c15a5fef44c81b6326e087b23c266049627e0345e4035836b109c'
}
_EXPECTED_IDENTITY_SET_SHA256 = "bbfddcc3da0de1de6da0632fb51fb7a364960f7080e3eeca4094a267b27e1698"
_EXPECTED_ARGUMENT_KEYS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
_EXPECTED_TASK_SOURCE = (
    "/Users/paul/Projects/cristexweb/ansible/roles/"
    "infisical_argocd_secrets_bootstrap/tasks/main.yml"
)


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only Infisical Argo CD Secret seam."""

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start_at_task = context.CLIARGS.get("start_at_task")
        step = bool(context.CLIARGS.get("step"))
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        task_source = str(self._task.get_path()).rsplit(":", 1)[0]
        if task_source != _EXPECTED_TASK_SOURCE:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing Infisical Argo CD Secret seam "
                    "mutation outside the canonical guarded role task source"
                ),
            }

        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        token = os.environ.get(
            "CRISTEXWEB_INFISICAL_ARGOCD_SECRETS_BOOTSTRAP_TOKEN", ""
        )
        attestation_path = os.environ.get(
            "CRISTEXWEB_INFISICAL_ARGOCD_SECRETS_BOOTSTRAP_ATTESTATION_FILE", ""
        )
        binding = task_vars.get(
            "infisical_argocd_secrets_bootstrap_internal_preflight_binding", {}
        )
        try:
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation_content = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation_state = None
            attestation_content = ""

        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256")
            == hashlib.sha256(token.encode()).hexdigest()
            and int(binding.get("object_count", -1)) == 11
            and binding.get("identity_set_sha256") == _EXPECTED_IDENTITY_SET_SHA256
            and int(binding.get("prestate_count", -1)) == 11
            and int(binding.get("admission_count", -1)) == 6
            and int(binding.get("rbac_count", -1)) == 2
            and int(binding.get("source_count", -1)) == 3
            and int(binding.get("alternate_target_count", -1)) == 3
            and int(binding.get("static_secret_inventory_count", -1)) in (0, 1)
            and int(binding.get("crd_count", -1)) == 6
            and binding.get("credential_contract") is True
            and binding.get("target_contract") is True
            and binding.get("namespace_contract") is True
        )
        valid_attestation = (
            os.environ.get("CRISTEXWEB_INFISICAL_ARGOCD_SECRETS_BOOTSTRAP_ENTRYPOINT")
            == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and attestation_state is not None
            and stat.S_ISREG(attestation_state.st_mode)
            and not stat.S_ISLNK(attestation_state.st_mode)
            and stat.S_IMODE(attestation_state.st_mode) == 0o600
            and attestation_state.st_uid == os.getuid()
            and attestation_content == f"{token}:entrypoint"
        )
        if (
            not valid_attestation
            or not valid_binding
            or task_vars.get("infisical_argocd_secrets_bootstrap_approved") is not True
            or task_vars.get("infisical_argocd_secrets_bootstrap_state") != "present"
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing Infisical Argo CD Secret seam "
                    "mutation without the validated wrapper attestation and "
                    "complete preflight binding"
                ),
            }

        if not isinstance(definition, dict):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing arguments outside the "
                    "exact present-only Infisical Argo CD Secret seam"
                ),
            }
        metadata = definition.get("metadata") or {}
        identity = (
            definition.get("apiVersion"),
            definition.get("kind"),
            metadata.get("namespace", ""),
            metadata.get("name"),
        )
        if (
            set(args) != _EXPECTED_ARGUMENT_KEYS
            or args.get("state") != "present"
            or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml"
            or args.get("wait") is not False
            or args.get("wait_timeout") != 60
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing arguments outside the "
                    "exact present-only Infisical Argo CD Secret seam"
                ),
            }
        if definition.get("kind") == "Secret" or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing an unknown, changed, or "
                    "Secret Infisical Argo CD Secret seam object"
                ),
            }
        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "TASK_SELECTION_GUARD: refusing Infisical Argo CD Secret seam "
                    "mutation under task selection"
                ),
            }

        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
