from __future__ import annotations

from typing import Any

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import (
    ActionModule as KubernetesActionModule,
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
    """Permit only the exact PROD Namespace mutation without task selection."""

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start_at_task = context.CLIARGS.get("start_at_task")
        step = bool(context.CLIARGS.get("step"))
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])

        if self._task.args != _EXPECTED_ARGUMENTS:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing arguments outside the exact "
                    "present-only cristexhub-prod Namespace contract"
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

        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
