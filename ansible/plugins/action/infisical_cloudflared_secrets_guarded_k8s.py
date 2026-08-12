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
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cloudflared-alternate-target-boundary'): '90f371e3af05875c8929d0df96423294780b5b47be54f0ddc483dff84e544e95',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cloudflared-alternate-target-boundary'): '8ea8c9137aaabf7b78df019e46ddd5fa7371a144678e6d9e5358cbaf699a7866',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cloudflared-secret-write-boundary'): '125cd4eff2021a0f30297196974454aa6edba4f3e0409400fc40092a6ece9c4a',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cloudflared-secret-write-boundary'): 'cb08bd4c6001bd78124ebb8c5cfcb185787bb9cf1a0a425bdd9e2763b5adba3a',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cloudflared-source-boundary'): '3496db1ef40a4487147cada821c25ac99384358acb856426a8f2ec696fc552aa',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cloudflared-source-boundary'): 'ea313c248efda5990cb50c51f63a414bc602520162e9f0df04f83fa61084cc39',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cloudflared-static-secret-boundary'): 'd8c4fef8ab84a70982755a19d884b3f6eac56a97dc58aa94aebc39005db411b6',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cloudflared-static-secret-boundary'): 'beb94b8181719e86a29b87f7568c98193c84f6474babad0df309bb5dff46677a',
    ('rbac.authorization.k8s.io/v1', 'Role', 'platform-edge', 'infisical-cloudflared-secret-writer'): '0a1b9897f285f3be997ed07d5bc1d06ea29ada7b6c53f34e80c94eb016b2f861',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'platform-edge', 'infisical-cloudflared-secret-writer'): 'd7b58f970c65fefa7af5c6129f198c55eae11e6b99ce502a1c1012716dc3398e',
    ('secrets.infisical.com/v1beta1', 'InfisicalAuth', 'platform-edge', 'cloudflared-infisical-auth'): '14eb767db221fd5dfb70f05ca9832f04aa7e9c58e71aeb06dc5522f1676e6443',
    ('secrets.infisical.com/v1beta1', 'InfisicalStaticSecret', 'platform-edge', 'cloudflared-infisical-secrets'): 'c4b0894dde026c49633cdd23d6a6af8e7d5db72d5753c9b00785cf0effff0400',
    ('secrets.infisical.com/v1beta1', 'InfisicalConnection', 'platform-edge', 'infisical-cloud'): 'dbd1ee876a1caec94cd4915b0ea908730a989332663fc6607fe971e7e97ea901',
}
_EXPECTED_IDENTITY_SET_SHA256 = "6830878ab0fa1a088806c3474b78b87c261d8ca6b2a574e9616823d37bd83e82"
_EXPECTED_ARGUMENT_KEYS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
_EXPECTED_TASK_SOURCE = (
    "/Users/paul/Projects/cristexweb/ansible/roles/"
    "infisical_cloudflared_secrets_bootstrap/tasks/main.yml"
)


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only Infisical cloudflared Secret seam."""

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
                    "ENTRYPOINT_GUARD: refusing Infisical cloudflared Secret seam "
                    "mutation outside the canonical guarded role task source"
                ),
            }

        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        token = os.environ.get(
            "CRISTEXWEB_INFISICAL_CLOUDFLARED_SECRETS_BOOTSTRAP_TOKEN", ""
        )
        attestation_path = os.environ.get(
            "CRISTEXWEB_INFISICAL_CLOUDFLARED_SECRETS_BOOTSTRAP_ATTESTATION_FILE", ""
        )
        binding = {
            "attestation_sha256": hashlib.sha256(token.encode()).hexdigest(),
            "object_count": 13,
            "identity_set_sha256": _EXPECTED_IDENTITY_SET_SHA256,
            "prestate_count": 13,
            "admission_count": 8,
            "rbac_count": 2,
            "source_count": 3,
            "alternate_target_count": 3,
            "static_secret_inventory_count": 0,
            "crd_count": 6,
            "credential_contract": True,
            "target_contract": True,
            "namespace_contract": True,
        }
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
            os.environ.get("CRISTEXWEB_INFISICAL_CLOUDFLARED_SECRETS_BOOTSTRAP_ENTRYPOINT")
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
            or task_vars.get("infisical_cloudflared_secrets_bootstrap_approved") is not True
            or task_vars.get("infisical_cloudflared_secrets_bootstrap_state") != "present"
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing Infisical cloudflared Secret seam "
                    "mutation without the validated wrapper attestation"
                ),
            }

        if not isinstance(definition, dict):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing arguments outside the "
                    "exact present-only Infisical cloudflared Secret seam"
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
                    "exact present-only Infisical cloudflared Secret seam"
                ),
            }
        if definition.get("kind") == "Secret" or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing an unknown, changed, or "
                    "Secret Infisical cloudflared Secret seam object"
                ),
            }
        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "TASK_SELECTION_GUARD: refusing Infisical cloudflared Secret seam "
                    "mutation under task selection"
                ),
            }

        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
