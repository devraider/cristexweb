from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import (
    ActionModule as KubernetesActionModule,
)


_EXPECTED_MANIFEST_SHA256 = "f029bb06bb698c6ddc3e083985f754bd326de8b18804523d1300eae54e8260d0"
_EXPECTED_TASK_SOURCE = str(
    Path(__file__).resolve().parents[2]
    / "roles/cristexhub_prod_namespace_bootstrap/tasks/main.yml"
)
_EXPECTED_DEFINITION = {
    "apiVersion": "v1",
    "kind": "Namespace",
    "metadata": {
        "name": "cristexhub-prod",
        "labels": {
            "app.kubernetes.io/part-of": "cristexhub",
            "cristex.io/environment": "prod",
            "cristex.io/bootstrap-writer": "ansible",
            "cristex.io/desired-owner": "argocd",
        },
    },
}
_EXPECTED_ARGUMENTS = {
    "state": "present",
    "definition": _EXPECTED_DEFINITION,
    "kubeconfig": "/etc/rancher/k3s/k3s.yaml",
    "wait": True,
    "wait_timeout": 30,
}


class ActionModule(KubernetesActionModule):
    """Permit only the exact PROD Namespace mutation from the guarded role."""

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

        # An action plugin can be invoked directly without executing the role's
        # controller-side preflight.  The task path is therefore an independent
        # boundary, not merely a convention documented by the wrapper.
        task_source = str(self._task.get_path()).rsplit(":", 1)[0]
        if task_source != _EXPECTED_TASK_SOURCE:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing CristexHub PROD Namespace mutation "
                    "outside the canonical guarded role task source"
                ),
            }

        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "TASK_SELECTION_GUARD: refusing the CristexHub PROD Namespace "
                    "mutation under --start-at-task, --step, --tags, or --skip-tags"
                ),
            }

        token = os.environ.get(
            "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_TOKEN", ""
        )
        attestation_path = os.environ.get(
            "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE", ""
        )
        try:
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation_content = Path(attestation_path).read_text().strip()
        except (OSError, ValueError, UnicodeError):
            attestation_state = None
            attestation_content = ""

        binding = task_vars.get(
            "cristexhub_prod_namespace_bootstrap_internal_preflight_binding", {}
        )
        expected_attestation_sha256 = hashlib.sha256(token.encode()).hexdigest()
        valid_binding = (
            isinstance(binding, dict)
            and set(binding)
            == {
                "attestation_sha256",
                "manifest_names",
                "prestate_names",
                "controller_path_count",
                "manifest_path_count",
                "manifest_sha256",
                "kubeconfig_contract",
                "service_contract",
                "no_delete_path",
            }
            and binding.get("attestation_sha256") == expected_attestation_sha256
            and binding.get("manifest_names") == ["cristexhub-prod"]
            and binding.get("prestate_names") == ["cristexhub-prod"]
            and binding.get("controller_path_count") in (4, "4")
            and binding.get("manifest_path_count") in (1, "1")
            and binding.get("manifest_sha256") == [_EXPECTED_MANIFEST_SHA256]
            and binding.get("kubeconfig_contract") is True
            and binding.get("service_contract") is True
            and binding.get("no_delete_path") is True
        )
        valid_attestation = (
            os.environ.get(
                "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_ENTRYPOINT"
            )
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
            or task_vars.get("cristexhub_prod_namespace_bootstrap_approved") is not True
            or task_vars.get("cristexhub_prod_namespace_bootstrap_state") != "present"
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing CristexHub PROD Namespace mutation "
                    "without the validated wrapper attestation and complete "
                    "preflight binding"
                ),
            }

        if self._task.args != _EXPECTED_ARGUMENTS:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing arguments outside the exact "
                    "present-only cristexhub-prod Namespace contract"
                ),
            }

        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
