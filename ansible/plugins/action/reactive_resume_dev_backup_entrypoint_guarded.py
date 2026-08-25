from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """Fail closed on task selection before enabling backup operations."""

    TRANSFERS_FILES = False

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = super().run(tmp, task_vars)
        task_vars = task_vars or {}
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        if (
            context.CLIARGS.get("start_at_task")
            or context.CLIARGS.get("step")
            or tags not in ([], ["all"])
            or skip_tags
        ):
            return {
                **result,
                "changed": False,
                "failed": True,
                "msg": "TASK_SELECTION_GUARD: backup requires the complete guarded play",
            }

        token = os.environ.get(
            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT_TOKEN", ""
        )
        attestation = os.environ.get(
            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT_ATTESTATION_FILE", ""
        )
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            state = None
            content = ""
        source_states = task_vars.get("reactive_resume_dev_backup_source_states", {})
        source_results = source_states.get("results", [])
        valid = (
            len(token) == 64
            and all(char in "0123456789abcdef" for char in token)
            and state is not None
            and stat.S_ISREG(state.st_mode)
            and state.st_uid == os.getuid()
            and stat.S_IMODE(state.st_mode) == 0o600
            and state.st_nlink == 1
            and content == f"{token}:entrypoint\n"
            and len(source_results) == 9
            and all(not item.get("failed", False) for item in source_results)
        )
        if not valid:
            return {
                **result,
                "changed": False,
                "failed": True,
                "msg": "ENTRYPOINT_GUARD: backup preflight or attestation is incomplete",
            }
        result.update(
            changed=False,
            ansible_facts={
                "reactive_resume_dev_backup_internal_preflight_complete": True
            },
        )
        return result
