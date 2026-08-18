from __future__ import annotations

import base64
import os
import re
import stat
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import (
    ActionModule as KubernetesActionModule,
)

_EXPECTED = {
    "infisical-egress-proxy-tls": ("kubernetes.io/tls", {"ca.crt", "tls.crt", "tls.key"}),
    "infisical-egress-proxy-auth": ("Opaque", {"users"}),
    "infisical-egress-proxy-client": ("Opaque", {"proxy-url"}),
}
_EXPECTED_TASK_SOURCE = (
    "/Users/paul/Projects/cristexweb/ansible/roles/"
    "infisical_proxy_secret_zero/tasks/main.yml"
)
_EXPECTED_LABELS = {
    "app.kubernetes.io/part-of": "cristex-platform",
    "app.kubernetes.io/managed-by": "ansible",
    "cristex.io/component": "infisical-operator",
    "cristex.io/value-owner": "secret-zero",
}


def _decode(value: Any) -> bytes:
    if not isinstance(value, str):
        raise ValueError("Secret data must be encoded text")
    return base64.b64decode(value, validate=True)


class ActionModule(KubernetesActionModule):
    """Permit only the three exact recovered proxy bootstrap Secrets."""

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
                    "ENTRYPOINT_GUARD: refusing proxy Secret mutation outside the "
                    "canonical guarded role task source"
                ),
            }
        token = os.environ.get("CRISTEXWEB_INFISICAL_PROXY_SECRET_ZERO_TOKEN", "")
        attestation_path = os.environ.get(
            "CRISTEXWEB_INFISICAL_PROXY_SECRET_ZERO_ATTESTATION_FILE", ""
        )
        try:
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation_content = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation_state = None
            attestation_content = ""
        valid_attestation = (
            os.environ.get("CRISTEXWEB_INFISICAL_PROXY_SECRET_ZERO_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and attestation_state is not None
            and stat.S_ISREG(attestation_state.st_mode)
            and not stat.S_ISLNK(attestation_state.st_mode)
            and stat.S_IMODE(attestation_state.st_mode) == 0o600
            and attestation_state.st_uid == os.getuid()
            and attestation_content == f"{token}:entrypoint"
            and task_vars.get("infisical_proxy_secret_zero_approved") is True
        )
        if not valid_attestation:
            return {
                "changed": False,
                "failed": True,
                "msg": "ENTRYPOINT_GUARD: refusing proxy Secret mutation outside its writer",
            }
        start_at_task = context.CLIARGS.get("start_at_task")
        step = bool(context.CLIARGS.get("step"))
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {
                "changed": False,
                "failed": True,
                "msg": "TASK_SELECTION_GUARD: refusing proxy Secret mutation under task selection",
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
                "msg": "MUTATION_ARGUMENT_GUARD: refusing proxy Secret argument drift",
            }
        metadata = definition.get("metadata") or {}
        name = metadata.get("name")
        expected = _EXPECTED.get(name)
        data = definition.get("data")
        try:
            decoded = {key: _decode(value) for key, value in data.items()}
        except (AttributeError, ValueError):
            decoded = {}
        valid = (
            definition.get("apiVersion") == "v1"
            and definition.get("kind") == "Secret"
            and set(definition) == {"apiVersion", "kind", "metadata", "type", "data"}
            and set(metadata) == {"name", "namespace", "labels"}
            and metadata.get("namespace") == "shared-services"
            and metadata.get("labels") == _EXPECTED_LABELS
            and expected is not None
            and definition.get("type") == expected[0]
            and isinstance(data, dict)
            and set(data) == expected[1]
            and set(decoded) == expected[1]
        )
        if valid and name == "infisical-egress-proxy-tls":
            valid = (
                decoded["ca.crt"].startswith(b"-----BEGIN CERTIFICATE-----")
                and decoded["tls.crt"].startswith(b"-----BEGIN CERTIFICATE-----")
                and b"PRIVATE KEY-----" in decoded["tls.key"]
            )
        elif valid and name == "infisical-egress-proxy-auth":
            valid = re.fullmatch(
                rb"infisical-operator:\$6\$[^\r\n]{20,}\n", decoded["users"]
            ) is not None
        elif valid and name == "infisical-egress-proxy-client":
            try:
                proxy = urlsplit(decoded["proxy-url"].decode())
                valid = (
                    proxy.scheme == "https"
                    and proxy.hostname == "infisical-egress-proxy.shared-services.svc"
                    and proxy.port == 3129
                    and proxy.username == "infisical-operator"
                    and proxy.password is not None
                    and re.fullmatch(r"[0-9a-f]{64}", proxy.password) is not None
                    and proxy.path == ""
                    and proxy.query == ""
                    and proxy.fragment == ""
                )
            except (UnicodeDecodeError, ValueError):
                valid = False
        if not valid:
            return {
                "changed": False,
                "failed": True,
                "msg": "MUTATION_ARGUMENT_GUARD: refusing unknown or malformed proxy Secret",
            }
        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
