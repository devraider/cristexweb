from __future__ import annotations

import base64
import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import (
    ActionModule as KubernetesActionModule,
)

_EXPECTED_TASK_SOURCE = (
    "/Users/paul/Projects/cristexweb/ansible/roles/"
    "infisical_universal_auth_seed/tasks/main.yml"
)
_EXPECTED = {
    ("argocd", "argocd-infisical-universal-auth"),
    ("shared-services", "shared-postgresql-infisical-universal-auth"),
    ("shared-services", "shared-mongodb-infisical-universal-auth"),
}
_EXPECTED_LABELS = {
    "app.kubernetes.io/managed-by": "ansible",
    "app.kubernetes.io/part-of": "infisical-operator",
    "cristex.io/component": "infisical-runtime-auth",
    "cristex.io/value-owner": "infisical-cloud",
}
_TOKEN = re.compile(r"^[0-9a-f]{64}$")


def _decoded_data(data: Any) -> dict[str, bytes]:
    if not isinstance(data, dict):
        raise ValueError("Secret data is not a map")
    result: dict[str, bytes] = {}
    for key, value in data.items():
        if not isinstance(value, str):
            raise ValueError("Secret data is not encoded text")
        decoded = base64.b64decode(value, validate=True)
        if not decoded or any(byte < 0x20 or byte == 0x7f for byte in decoded):
            raise ValueError("Secret data contains an empty or control value")
        result[key] = decoded
    return result


class ActionModule(KubernetesActionModule):
    """Permit only the three exact, same-Namespace Universal Auth Secrets."""

    TRANSFERS_FILES = False

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task_vars = task_vars or {}
        task_source = str(self._task.get_path()).rsplit(":", 1)[0]
        if task_source != _EXPECTED_TASK_SOURCE:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing Universal Auth credential mutation "
                    "outside the canonical guarded role task source"
                ),
            }

        token = os.environ.get("CRISTEXWEB_INFISICAL_UNIVERSAL_AUTH_SEED_TOKEN", "")
        attestation_path = os.environ.get(
            "CRISTEXWEB_INFISICAL_UNIVERSAL_AUTH_SEED_ATTESTATION_FILE", ""
        )
        try:
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation_content = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation_state = None
            attestation_content = ""
        valid_attestation = (
            os.environ.get("CRISTEXWEB_INFISICAL_UNIVERSAL_AUTH_SEED_ENTRYPOINT")
            == "v1"
            and _TOKEN.fullmatch(token) is not None
            and attestation_state is not None
            and stat.S_ISREG(attestation_state.st_mode)
            and not stat.S_ISLNK(attestation_state.st_mode)
            and stat.S_IMODE(attestation_state.st_mode) == 0o600
            and attestation_state.st_uid == os.getuid()
            and attestation_content == f"{token}:entrypoint"
            and task_vars.get("infisical_universal_auth_seed_approved") is True
        )
        if not valid_attestation:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing Universal Auth credential mutation "
                    "without the private single-run attestation"
                ),
            }

        start_at_task = context.CLIARGS.get("start_at_task")
        step = bool(context.CLIARGS.get("step"))
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {
                "changed": False,
                "failed": True,
                "msg": "TASK_SELECTION_GUARD: refusing Universal Auth seed under task selection",
            }

        args = self._task.args
        definition = args.get("definition")
        if (
            set(args) != {"state", "definition", "kubeconfig"}
            or args.get("state") != "present"
            or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml"
            or not isinstance(definition, dict)
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": "MUTATION_ARGUMENT_GUARD: refusing Universal Auth seed argument drift",
            }

        metadata = definition.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        identity = (metadata.get("namespace"), metadata.get("name"))
        try:
            decoded = _decoded_data(definition.get("data"))
        except (TypeError, ValueError):
            decoded = {}
        valid = (
            definition.get("apiVersion") == "v1"
            and definition.get("kind") == "Secret"
            and set(definition) == {"apiVersion", "kind", "metadata", "type", "data"}
            and set(metadata) == {"name", "namespace", "labels"}
            and identity in _EXPECTED
            and definition.get("type") == "Opaque"
            and set(decoded) == {"clientId", "clientSecret"}
            and metadata.get("labels") == _EXPECTED_LABELS
        )
        if not valid:
            return {
                "changed": False,
                "failed": True,
                "msg": "MUTATION_ARGUMENT_GUARD: refusing unknown or malformed Universal Auth Secret",
            }

        return_value = super().run
        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return return_value(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
