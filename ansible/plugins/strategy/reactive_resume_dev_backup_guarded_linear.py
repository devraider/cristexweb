from __future__ import annotations

from ansible import context
from ansible.errors import AnsibleError
from ansible.plugins.strategy.linear import StrategyModule as LinearStrategyModule


class StrategyModule(LinearStrategyModule):
    """Reject task-selection controls before the play iterator can skip guards."""

    def run(self, iterator, play_context):  # type: ignore[no-untyped-def]
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if (
            context.CLIARGS.get("start_at_task")
            or context.CLIARGS.get("step")
            or tags not in ([], ["all"])
            or skip_tags
        ):
            raise AnsibleError(
                "TASK_SELECTION_GUARD: backup requires the complete guarded play"
            )
        return super().run(iterator, play_context)
