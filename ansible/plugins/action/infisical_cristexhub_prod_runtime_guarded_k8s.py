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
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cristexhub-prod-runtime-alternate-target-boundary'): 'f9814d97dc32dd6cbeebdbbe00f5529fa88424bb992995da6adb707513042d77',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cristexhub-prod-runtime-secret-write-boundary'): '45a45c9091390e470130a15ec52c984f80965cdb08f57ffdc908f73f2e011c8b',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cristexhub-prod-runtime-source-boundary'): 'cab66e9830b8ff882f6f78f43e6a5108319daee11c1b6f01deb364e6a902b5fd',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cristexhub-prod-runtime-static-secret-boundary'): '0556d4acb1f0a03cbfb5da179559f194c64fc57ab66535f7711708dd182df6c5',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cristexhub-prod-runtime-alternate-target-boundary'): '2e0439d1622eb50e93a9cf3ae0280eef9aa9db7eef3cd62ddd3c788d621e4308',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cristexhub-prod-runtime-secret-write-boundary'): '49db55c48fe2a2db1a02a776e5f77b72c2e512893a7b0655be8277fca5a87c1f',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cristexhub-prod-runtime-source-boundary'): '919d0a5f04773a28fee5beb606254943fec60f5b7e7d4816b8b4ab5a2d6a9397',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cristexhub-prod-runtime-static-secret-boundary'): '66f35a9abcb010e63ef9a2b0e529181501ee3c5093915129e2deb801cea84877',
    ('rbac.authorization.k8s.io/v1', 'Role', 'cristexhub-prod', 'infisical-cristexhub-prod-runtime-secret-writer'): '2935ea4190154f1110de72764e86841d0c5c74632819f533a9b881192fce4bd0',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'cristexhub-prod', 'infisical-cristexhub-prod-runtime-secret-writer'): '5ebfbd5b01b0cbb086044b73d2bf87df09aaf09c299d0ab80968fa4d808aadf5',
    ('secrets.infisical.com/v1beta1', 'InfisicalAuth', 'cristexhub-prod', 'cristexhub-prod-infisical-auth'): '2431da24946ca30fa377c9269b04e1f0bfceaaad6fa1d1c039621166b7699d7a',
    ('secrets.infisical.com/v1beta1', 'InfisicalConnection', 'cristexhub-prod', 'infisical-cloud'): 'a9405cf0d8e1b78fe0433e6acfe6d46f645fea3bad61beeafdd0ba96bb8e17ca',
    ('secrets.infisical.com/v1beta1', 'InfisicalStaticSecret', 'cristexhub-prod', 'cristexhub-prod-runtime'): 'd18b1db7a698f2b1953b0861cf78729c66369043e33e0ae091e7e57ab6991e0c',
}
_EXPECTED_IDENTITY_SET_SHA256 = "d46dde754f05f248bbc19ff28a65ec44ccb1f84c53221c1f7d4e3bb355d6ff20"
_EXPECTED_OIDC_CLIENT_SECRET_SOURCE = {
    "projectId": "619656da-14f3-4872-857b-be103cdc5326",
    "environmentSlug": "prod",
    "secretPath": "/cristexhub/prod/runtime",
    "recursive": False,
    "tagSlugs": [],
}
_EXPECTED_OIDC_CLIENT_SECRET_TEMPLATE = "{{ .OIDC_CLIENT_SECRET.Value }}"
_EXPECTED_ARGUMENT_KEYS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
_EXPECTED_TASK_SUFFIX = "/ansible/roles/infisical_cristexhub_prod_runtime_bootstrap/tasks/main.yml"


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _strict_integer(value: Any, expected: int | None = None) -> bool:
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return expected is None or value == expected


# Canonical identity digest: SHA-256 of sorted API/kind/namespace/name lines.
class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only CristexHub PROD runtime Secret seam."""

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start_at_task = context.CLIARGS.get("start_at_task")
        step = bool(context.CLIARGS.get("step"))
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        task_source = str(
            Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve()
        )
        repository_root = os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")
        if task_source != str(Path(repository_root).resolve()) + _EXPECTED_TASK_SUFFIX:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing CristexHub PROD runtime Secret seam "
                    "mutation outside the canonical guarded role task source"
                ),
            }

        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        token = os.environ.get(
            "CRISTEXWEB_CRISTEXHUB_PROD_RUNTIME_TOKEN", ""
        )
        attestation_path = os.environ.get(
            "CRISTEXWEB_CRISTEXHUB_PROD_RUNTIME_ATTESTATION_FILE", ""
        )
        binding = task_vars.get(
            "cristexhub_prod_runtime_bootstrap_internal_preflight_binding", {}
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
            and _strict_integer(binding.get("object_count"), 13)
            and _strict_integer(binding.get("prestate_count"), 13)
            and _strict_integer(binding.get("operator_prerequisite_count"), 3)
            and _strict_integer(binding.get("generic_policy_count"), 3)
            and _strict_integer(binding.get("generic_binding_count"), 3)
            and _strict_integer(binding.get("cr_inventory_count"), 6)
            and _strict_integer(binding.get("target_secret_inventory_count"))
            and 1 <= binding.get("target_secret_inventory_count", -1) <= 3
            and binding.get("identity_set_sha256") == _EXPECTED_IDENTITY_SET_SHA256
            and binding.get("identity_keys_sha256") == _EXPECTED_IDENTITY_SET_SHA256
        )
        valid_attestation = (
            os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_RUNTIME_ENTRYPOINT")
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
            or task_vars.get("cristexhub_prod_runtime_bootstrap_approved") is not True
            or task_vars.get("cristexhub_prod_runtime_bootstrap_state") != "present"
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing CristexHub PROD runtime Secret seam "
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
                    "exact present-only CristexHub PROD runtime Secret seam"
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
                    "exact present-only CristexHub PROD runtime Secret seam"
                ),
            }
        if (
            definition.get("kind") == "Secret"
            or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition)
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing an unknown, changed, or "
                    "Secret CristexHub PROD runtime Secret seam object"
                ),
            }
        if identity == (
            "secrets.infisical.com/v1beta1",
            "InfisicalStaticSecret",
            "cristexhub-prod",
            "cristexhub-prod-runtime",
        ):
            spec = definition.get("spec") or {}
            sources = spec.get("sources") or []
            targets = spec.get("targets") or []
            runtime_data = (
                (targets[0].get("template") or {}).get("data", {})
                if targets
                else {}
            )
            if (
                sources != [_EXPECTED_OIDC_CLIENT_SECRET_SOURCE]
                or runtime_data.get("OIDC_CLIENT_SECRET")
                != _EXPECTED_OIDC_CLIENT_SECRET_TEMPLATE
            ):
                return {
                    "changed": False,
                    "failed": True,
                    "msg": (
                        "MUTATION_ARGUMENT_GUARD: refusing a PROD OIDC client-secret "
                        "source or target-key mapping outside the canonical runtime contract"
                    ),
                }
        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "TASK_SELECTION_GUARD: refusing CristexHub PROD runtime Secret seam "
                    "mutation under task selection"
                ),
            }

        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
