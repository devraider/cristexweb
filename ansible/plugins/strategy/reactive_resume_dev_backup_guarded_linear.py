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
        long_selection_options = (
            "--start-at-task",
            "--step",
            "--tags",
            "--skip-tags",
        )
        selection_argv = any(
            argument == "-t"
            or argument.startswith("-t=")
            or (argument.startswith("-t") and len(argument) > 2)
            or (
                argument.startswith("--")
                and any(
                    option.startswith(argument.split("=", 1)[0])
                    for option in long_selection_options
                )
            )
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
