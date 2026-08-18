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

_EXPECTED_OBJECT_HASHES: dict[tuple[str, str, str, str], str] = {('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-argocd-alternate-target-boundary'): 'e83729093168045791912a4802ab4d930250241dfd6186181eb89d51ca8955d8',
 ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-argocd-secret-write-boundary'): '939a712ba766b2203d4e8d65abdfe09079975b929fdc138f85c48edd9aa1e99b',
 ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-argocd-source-boundary'): 'a2834bef0fd3efb25b05f604f5136626b0b0e038d8e3716437e7ea78aa335238',
 ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-argocd-static-secret-boundary'): '81ee0012de7bea069cf8282c8b14bd0049275486886072f9be39cf9d3d583f0f',
 ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-argocd-alternate-target-boundary'): '9fe628a53a33301c095b1a6ac3c6007fde1377ced3e1e5800960f79133952477',
 ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-argocd-secret-write-boundary'): '07ebbfc58d15281eed817e054f7d6483bbed21a99b0d10deb9322cf0e3fbc631',
 ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-argocd-source-boundary'): 'b3b105477003f52c56a1dd999adc71891a3a808940e36917359e14fb9cbf661c',
 ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-argocd-static-secret-boundary'): '11bf7f48ae4e746136a8d64fe6c1b8b090738424c06eaafaf00d0f79fd32826c',
 ('rbac.authorization.k8s.io/v1', 'Role', 'argocd', 'infisical-argocd-secret-writer'): '7e6cbef8230081d86760613de0895bae7b139935ee28501639fcd8344300650c',
 ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'argocd', 'infisical-argocd-secret-writer'): '355d7899cdcbc9a86c7bc21741d46f99d3c0d4905978ec44964b24c6ac69713b',
 ('secrets.infisical.com/v1beta1', 'InfisicalAuth', 'argocd', 'argocd-infisical-auth'): '88518d0fcc938aea1109edba6ac793c7a8b35d65c98160556b360f450c605c26',
 ('secrets.infisical.com/v1beta1', 'InfisicalConnection', 'argocd', 'infisical-cloud'): 'd8ea88e0dccaadaea0765b7b488370f5d8adf007892528ff24e68740d667bff3',
 ('secrets.infisical.com/v1beta1', 'InfisicalStaticSecret', 'argocd', 'argocd-infisical-secrets'): '19e1d96a392a53ef6a05f12744d5a6085ffe37d0a80e30327d3f38943b0c0204'}
# Canonical source identity digest: 23623b2be563e41d19483994371f67c3ab9d2f2e94919cbd22588d32883aca33
# Ansible/Jinja joins the protected runtime identity list with literal ``\\n``.
_EXPECTED_IDENTITY_SET_SHA256 = "1bffb930b5aaaa129000320c6124f0fdf87f1774e0391fadd44ffb055fe658c3"
_EXPECTED_ARGUMENT_KEYS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
_EXPECTED_TASK_SUFFIX = "/ansible/roles/infisical_argocd_secrets_bootstrap/tasks/main.yml"


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
        task_vars = task_vars or {}
        task_source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        repository_root = os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")
        if task_source != str(Path(repository_root).resolve()) + _EXPECTED_TASK_SUFFIX:
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
            and int(binding.get("object_count", -1)) == 13
            and binding.get("identity_set_sha256") == _EXPECTED_IDENTITY_SET_SHA256
            and int(binding.get("prestate_count", -1)) == 13
            and int(binding.get("admission_count", -1)) == 8
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
