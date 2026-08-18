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

_EXPECTED_OBJECT_HASHES = {
    ("v1", "ConfigMap", "shared-services", "shared-postgresql-pg-hba"): "d2bac23760974c866422638a4d0a5eb43e9caf0b58cfbd8399ed8bc30e73c91f",
    ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "shared-postgresql-default-deny"): "4b6a28a3073740296a651d339facb282213caeb75a1d3ba202661ceea05b9a95",
    ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "shared-postgresql-ingress"): "01d160abe56c40676728862453a155b97b26957f41ec41789cab71d3556ae9e4",
    ("v1", "ServiceAccount", "shared-services", "shared-postgresql"): "be24efea11ad657555d504a7d5591e5d77259c21bf4779839b0bc42fbb887d03",
    ("v1", "Service", "shared-services", "shared-postgresql"): "677078b36159313e0effe92897bcc21fd17b1917841e26ba0e820f37f58d3677",
    ("apps/v1", "StatefulSet", "shared-services", "shared-postgresql"): "5bb45cf3ed5db37ca01bd53444ee93ea7a0aefe7be43a151b1572e882dfd1b2f",
}
_EXPECTED_ARGUMENT_KEYS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
_EXPECTED_TASK_SOURCES = {
    "/Users/paul/Projects/cristexweb/ansible/roles/postgresql_bootstrap/tasks/main.yml",
    "/home/paul/projects/cristexweb/ansible/roles/postgresql_bootstrap/tasks/main.yml",
}
_EXPECTED_IDENTITY_SET_SHA256 = (
    "29c7c24d94405550370d3528c12df31e6beeea06dda23edfba417d3e15a8baf4"
)


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _integer(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only PostgreSQL source closure."""

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start_at_task = context.CLIARGS.get("start_at_task")
        step = bool(context.CLIARGS.get("step"))
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {
                "changed": False,
                "failed": True,
                "msg": "TASK_SELECTION_GUARD: refusing PostgreSQL mutation under task selection",
            }

        task_source = str(self._task.get_path()).rsplit(":", 1)[0]
        if task_source not in _EXPECTED_TASK_SOURCES:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing PostgreSQL mutation outside the "
                    "canonical guarded role task source"
                ),
            }

        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        token = os.environ.get("CRISTEXWEB_POSTGRESQL_BOOTSTRAP_TOKEN", "")
        attestation_path = os.environ.get(
            "CRISTEXWEB_POSTGRESQL_BOOTSTRAP_ATTESTATION_FILE", ""
        )
        binding = task_vars.get(
            "postgresql_bootstrap_internal_preflight_binding", {}
        )
        try:
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation_content = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation_state = None
            attestation_content = ""
        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and _integer(binding.get("object_count")) == 6
            and binding.get("identity_set_sha256") == _EXPECTED_IDENTITY_SET_SHA256
            and _integer(binding.get("prestate_count")) == 6
            and _integer(binding.get("secret_count")) == 2
            and _integer(binding.get("pvc_prestate_count")) in (0, 1)
            and binding.get("namespace_contract") is True
            and binding.get("storage_contract") is True
            and binding.get("service_contract") is True
            and binding.get("no_delete_path") is True
        )
        valid_attestation = (
            os.environ.get("CRISTEXWEB_POSTGRESQL_BOOTSTRAP_ENTRYPOINT") == "v1"
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
            or task_vars.get("postgresql_bootstrap_approved") is not True
            or task_vars.get("postgresql_bootstrap_state") != "present"
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing PostgreSQL mutation without the "
                    "validated wrapper attestation and complete preflight binding"
                ),
            }
        if (
            set(args) != _EXPECTED_ARGUMENT_KEYS
            or args.get("state") != "present"
            or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml"
            or args.get("wait") is not False
            or args.get("wait_timeout") != 60
            or not isinstance(definition, dict)
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing arguments outside the "
                    "exact present-only PostgreSQL closure"
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
            definition.get("kind") in {"Secret", "PersistentVolumeClaim"}
            or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition)
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing an unknown, changed, or "
                    "Secret PostgreSQL object"
                ),
            }
        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
