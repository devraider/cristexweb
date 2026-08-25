from __future__ import annotations

import sys

from ansible import context
from ansible.errors import AnsibleError
from ansible.plugins.strategy.linear import StrategyModule as LinearStrategyModule


class StrategyModule(LinearStrategyModule):
    """Reject task-selection controls before the play iterator can skip guards."""

    def run(self, iterator, play_context):  # type: ignore[no-untyped-def]
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        selection_argv = any(
            argument in {"--start-at-task", "--step", "--tags", "--skip-tags"}
            or argument.startswith(("--start-at-task=", "--tags=", "--skip-tags="))
            for argument in sys.argv[1:]
        )
        if (
            context.CLIARGS.get("start_at_task") is not None
            or context.CLIARGS.get("step")
            or selection_argv
            or tags not in ([], ["all"])
            or skip_tags
        ):
            raise AnsibleError(
                "TASK_SELECTION_GUARD: backup requires the complete guarded play"
            )
        return super().run(iterator, play_context)
