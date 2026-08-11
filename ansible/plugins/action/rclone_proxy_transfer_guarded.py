from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible.plugins.action import ActionBase

_NAME = "infisical-proxy-secret-zero-20260810T095421Z.tar.gz.age"
_DIGEST = "3562c730814440dc836c3f38d34efc41f0ca6f180635135ba92314990b121d28"
_TIMESTAMP = "20260810T095421Z"
_REMOTE = f"drive:cristexweb-recovery/infisical-proxy/{_TIMESTAMP}"
_EXPECTED_TASK_SOURCE = str(
    Path(__file__).resolve().parents[2] / "roles/rclone_proxy_transfer/tasks/main.yml"
)


class ActionModule(ActionBase):
    """Guard the two immutable uploads, two readbacks, fetch, and ciphertext cleanup."""

    TRANSFERS_FILES = False

    def _fail(self, msg: str) -> dict[str, Any]:
        return {"changed": False, "failed": True, "msg": msg}

    def _run_action(
        self, name: str, args: dict[str, Any], tmp: str | None, task_vars: dict[str, Any]
    ) -> dict[str, Any]:
        original_action, original_args = self._task.action, self._task.args
        self._task.action, self._task.args = name, args
        try:
            plugin_args = {
                "task": self._task,
                "connection": self._connection,
                "play_context": self._play_context,
                "loader": self._loader,
                "templar": self._templar,
                "shared_loader_obj": self._shared_loader_obj,
            }
            plugin = self._shared_loader_obj.action_loader.get(name, **plugin_args)
            if plugin is None:
                plugin = self._shared_loader_obj.action_loader.get(
                    "ansible.builtin.normal", **plugin_args
                )
            if plugin is None:
                return self._fail(f"unable to load guarded action {name} or normal fallback")
            return plugin.run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action, self._task.args = original_action, original_args

    def run(
        self, tmp: str | None = None, task_vars: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        task_vars = task_vars or {}
        if str(self._task.get_path()).rsplit(":", 1)[0] != _EXPECTED_TASK_SOURCE:
            return self._fail("ENTRYPOINT_GUARD: refusing proxy transfer outside its canonical task source")
        if (
            context.CLIARGS.get("start_at_task")
            or context.CLIARGS.get("step")
            or list(context.CLIARGS.get("tags") or []) not in ([], ["all"])
            or list(context.CLIARGS.get("skip_tags") or [])
        ):
            return self._fail("TASK_SELECTION_GUARD: refusing proxy transfer under task selection")
        token = os.environ.get("CRISTEXWEB_RCLONE_PROXY_TRANSFER_TOKEN", "")
        attestation = os.environ.get("CRISTEXWEB_RCLONE_PROXY_TRANSFER_ATTESTATION_FILE", "")
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except OSError:
            return self._fail("ENTRYPOINT_GUARD: invalid proxy transfer attestation")
        binding = task_vars.get("rclone_proxy_transfer_internal_preflight_binding", {})
        valid = (
            os.environ.get("CRISTEXWEB_RCLONE_PROXY_TRANSFER_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and stat.S_ISREG(state.st_mode)
            and stat.S_IMODE(state.st_mode) == 0o600
            and state.st_uid == os.getuid()
            and content == f"{token}:entrypoint"
            and isinstance(binding, dict)
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding.get("ciphertext_sha256") == _DIGEST
            and binding.get("remote_directory") == _REMOTE
            and binding.get("service_contract") is True
            and task_vars.get("rclone_proxy_transfer_approved") is True
        )
        if not valid:
            return self._fail("ENTRYPOINT_GUARD: refusing proxy transfer without complete guarded preflight")
        if set(self._task.args) != {"operation"}:
            return self._fail("MUTATION_ARGUMENT_GUARD: unexpected proxy transfer arguments")
        operation = self._task.args["operation"]
        operator = binding.get("operator_user")
        home = binding.get("operator_home")
        controller_home = os.environ.get("HOME", "")
        readback_root = os.environ.get("CRISTEXWEB_RCLONE_PROXY_TRANSFER_READBACK", "")
        if (
            not isinstance(operator, str)
            or not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", operator)
            or not isinstance(home, str)
            or home != f"/home/{operator}"
            or not readback_root.startswith("/tmp/cristexweb-infisical-proxy-transfer.")
        ):
            return self._fail("MUTATION_ARGUMENT_GUARD: unsafe operator or controller readback path")
        base = f"{home}/.cristexweb-rclone/infisical-proxy/{_TIMESTAMP}"
        staging, readback = f"{base}/staging", f"{base}/readback"
        config = f"{home}/.config/rclone/rclone.conf"
        source_root = f"{controller_home}/Library/Application Support/CristexWeb/recovery/infisical-proxy"
        checksum_name = f"{_NAME}.sha256"
        if operation == "prepare":
            changed = False
            for path in (f"{home}/.cristexweb-rclone", f"{home}/.cristexweb-rclone/infisical-proxy", base, staging, readback):
                result = self._run_action("ansible.builtin.file", {"path": path, "state": "directory", "owner": operator, "mode": "0700"}, tmp, task_vars)
                if result.get("failed"): return result
                changed = changed or bool(result.get("changed"))
            for name in (_NAME, checksum_name):
                result = self._run_action("ansible.builtin.copy", {"src": f"{source_root}/{name}", "dest": f"{staging}/{name}", "owner": operator, "mode": "0600"}, tmp, task_vars)
                if result.get("failed"): return result
                changed = changed or bool(result.get("changed"))
            return {"changed": changed}
        if operation == "remote-list":
            return self._run_action(
                "ansible.builtin.command",
                {
                    "argv": [
                        "/usr/local/bin/rclone",
                        "listremotes",
                        "--long",
                        "--config",
                        config,
                    ]
                },
                tmp,
                task_vars,
            )
        if operation == "remote-about":
            return self._run_action(
                "ansible.builtin.command",
                {
                    "argv": [
                        "/usr/local/bin/rclone",
                        "about",
                        "drive:",
                        "--json",
                        "--config",
                        config,
                    ]
                },
                tmp,
                task_vars,
            )
        fixed = [
            "/usr/local/bin/rclone",
            "copyto",
            "--immutable",
            "--config",
            config,
        ]
        argv_by_operation = {
            "upload-ciphertext": [*fixed, f"{staging}/{_NAME}", f"{_REMOTE}/{_NAME}"],
            "upload-checksum": [
                *fixed,
                f"{staging}/{checksum_name}",
                f"{_REMOTE}/{checksum_name}",
            ],
            "readback-ciphertext": [
                *fixed,
                f"{_REMOTE}/{_NAME}",
                f"{readback}/{_NAME}",
            ],
            "readback-checksum": [
                *fixed,
                f"{_REMOTE}/{checksum_name}",
                f"{readback}/{checksum_name}",
            ],
        }
        if operation in argv_by_operation:
            result = self._run_action(
                "ansible.builtin.command",
                {"argv": argv_by_operation[operation]},
                tmp,
                task_vars,
            )
            if result.get("failed") or not operation.startswith("readback-"):
                return result
            readback_name = _NAME if operation == "readback-ciphertext" else checksum_name
            protected = self._run_action(
                "ansible.builtin.file",
                {
                    "path": f"{readback}/{readback_name}",
                    "state": "file",
                    "follow": False,
                    "owner": operator,
                    "mode": "0600",
                },
                tmp,
                task_vars,
            )
            if protected.get("failed"):
                return protected
            result["changed"] = bool(result.get("changed")) or bool(
                protected.get("changed")
            )
            return result
        if operation == "fetch":
            changed = False
            for name in (_NAME, checksum_name):
                result = self._run_action("ansible.builtin.fetch", {"src": f"{readback}/{name}", "dest": f"{readback_root}/{name}", "flat": True, "fail_on_missing": True}, tmp, task_vars)
                if result.get("failed"): return result
                changed = changed or bool(result.get("changed"))
            return {"changed": changed}
        if operation == "cleanup":
            if task_vars.get("rclone_proxy_transfer_cleanup_approved") is not True:
                return self._fail("ENTRYPOINT_GUARD: cleanup approval is required")
            return self._run_action("ansible.builtin.file", {"path": base, "state": "absent"}, tmp, task_vars)
        return self._fail("MUTATION_ARGUMENT_GUARD: unknown proxy transfer operation")
