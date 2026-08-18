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
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-database-alternate-target-boundary'): 'c9a3c52a98e06ec04a38cd132e58eae3b37953dadfc248ae5fa02ef1ac886e69',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-database-alternate-target-boundary'): '16eaade61d5a3cef75d9f79f9785bc41be9eb63d1f69bc528e74af12bb53fcee',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-database-secret-write-boundary'): 'aee4580bba72d6271cbbd4d4f856338fa85ce2df1b0d3f7cbb9e7a752c02dd8d',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-database-secret-write-boundary'): 'a96d8c51fb09fdd25ad1eefcf77c4c70c6945d6a54183ef8bb8843055625ffc8',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-database-source-boundary'): '09ff778eebb18a6e8cd3cac7f8cdcb811c0578a0af56b3387a381b1d2ddfdbf6',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-database-source-boundary'): '858a123d08565695ae07be7f7036be869557175812e7096addf068213c3a2a01',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-database-static-secret-boundary'): '5068c028a8136394dc598506bb8a82ba2bc8bb748e3371d1610d7e986ded7c49',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-database-static-secret-boundary'): 'e90239295218e12faeb711072e8b9088a5065777c1b1ec66a92c98090e345298',
    ('rbac.authorization.k8s.io/v1', 'Role', 'shared-services', 'infisical-database-secret-writer'): '344e4a3b0ea222e1a6f8c35de2db4621dd31861b099eedb11a92f5db42027fab',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'shared-services', 'infisical-database-secret-writer'): 'dcbbc0a696753a3c18340eb05bebb4e71ace0c375e3726f61e163e0a196486f1',
    ('secrets.infisical.com/v1beta1', 'InfisicalConnection', 'shared-services', 'infisical-cloud'): '12a4c1f435d7c82c9a368ed09067dcc87adfd5f53a359486cf6d4313348ae4c5',
    ('secrets.infisical.com/v1beta1', 'InfisicalAuth', 'shared-services', 'shared-mongodb-infisical-auth'): '6246745f80e59d68016a8bb805d4b6512c38aeb0eeacca86e9574d139b568359',
    ('secrets.infisical.com/v1beta1', 'InfisicalStaticSecret', 'shared-services', 'shared-mongodb-infisical-secrets'): '8d5ea212693ecee4208be9b0e51891a3a5385be10bd0ed6850c87d047c8e38b8',
    ('secrets.infisical.com/v1beta1', 'InfisicalAuth', 'shared-services', 'shared-postgresql-infisical-auth'): 'b32652088ec3a205cba528446a1380d39363ee916597408a8e15164e035abee1',
    ('secrets.infisical.com/v1beta1', 'InfisicalStaticSecret', 'shared-services', 'shared-postgresql-infisical-secrets'): 'cfbf3216d827f61565dfd02dea46652150f3010cb5280bfee84be30818b27aa8',
}
_EXPECTED_IDENTITY_SET_SHA256 = "7cb8035f3189e6bd5d4d36186a5666cbf5e62b6c1e8606dc4e6dea9ea9dbad67"
_EXPECTED_ARGUMENT_KEYS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
_EXPECTED_TASK_SOURCES = {
    "/Users/paul/Projects/cristexweb/ansible/roles/infisical_database_secrets_bootstrap/tasks/main.yml",
    "/home/paul/projects/cristexweb/ansible/roles/infisical_database_secrets_bootstrap/tasks/main.yml",
}


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _integer(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only Infisical database Secret seam."""

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
        if task_source not in _EXPECTED_TASK_SOURCES:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing Infisical database Secret seam "
                    "mutation outside the canonical guarded role task source"
                ),
            }

        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        token = os.environ.get(
            "CRISTEXWEB_INFISICAL_DATABASE_SECRETS_BOOTSTRAP_TOKEN", ""
        )
        attestation_path = os.environ.get(
            "CRISTEXWEB_INFISICAL_DATABASE_SECRETS_BOOTSTRAP_ATTESTATION_FILE", ""
        )
        binding = task_vars.get(
            "infisical_database_secrets_bootstrap_internal_preflight_binding", {}
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
            and _integer(binding.get("object_count")) == 15
            and binding.get("identity_set_sha256") == _EXPECTED_IDENTITY_SET_SHA256
            and _integer(binding.get("prestate_count")) == 15
            and _integer(binding.get("admission_count")) == 8
            and _integer(binding.get("rbac_count")) == 2
            and _integer(binding.get("source_count")) == 5
            and _integer(binding.get("alternate_target_count")) == 3
            and _integer(binding.get("target_count")) == 11
            and _integer(binding.get("static_secret_inventory_count")) in (0, 1)
            and _integer(binding.get("crd_count")) == 6
            and binding.get("credential_contract") is True
            and binding.get("target_contract") is True
            and binding.get("namespace_contract") is True
        )
        valid_attestation = (
            os.environ.get("CRISTEXWEB_INFISICAL_DATABASE_SECRETS_BOOTSTRAP_ENTRYPOINT")
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
            or task_vars.get("infisical_database_secrets_bootstrap_approved") is not True
            or task_vars.get("infisical_database_secrets_bootstrap_state") != "present"
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing Infisical database Secret seam "
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
                    "exact present-only Infisical database Secret seam"
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
                    "exact present-only Infisical database Secret seam"
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
                    "Secret Infisical database Secret seam object"
                ),
            }
        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "TASK_SELECTION_GUARD: refusing Infisical database Secret seam "
                    "mutation under task selection"
                ),
            }

        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
