from __future__ import annotations

import hashlib
import os
import re
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from ansible import context
from ansible.plugins.action import ActionBase

_VERSION = "1.71.1"
_ARCHIVE_NAME = "rclone-v1.71.1-linux-amd64.zip"
_ARCHIVE_SHA256 = "417e3da236f3a12d292da4e7287d67b1df558b8c2b280d092e563958ed724be7"
_BINARY_SHA256 = "5409cb410e49903af3517654ccc65c89d89f9dc12d7a97b0e13e09a9be6dc74a"
_MEMBERS = {
    "rclone-v1.71.1-linux-amd64/rclone",
    "rclone-v1.71.1-linux-amd64/rclone.1",
    "rclone-v1.71.1-linux-amd64/README.txt",
    "rclone-v1.71.1-linux-amd64/README.html",
    "rclone-v1.71.1-linux-amd64/git-log.txt",
}
_EXPECTED_TASK_SOURCE = str(
    Path(__file__).resolve().parents[2] / "roles/rclone_install/tasks/main.yml"
)


def _write_binary_cache(binary_cache: Path, payload: bytes) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=binary_cache.parent,
            prefix=".rclone.pending.",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.chmod(temporary_path, 0o600, follow_symlinks=False)
        os.replace(temporary_path, binary_cache)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


class ActionModule(ActionBase):
    """Guard every rclone installer mutation against task selection and injection."""

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
        source = str(self._task.get_path()).rsplit(":", 1)[0]
        if source != _EXPECTED_TASK_SOURCE:
            return self._fail("ENTRYPOINT_GUARD: refusing rclone install outside its canonical task source")
        if (
            context.CLIARGS.get("start_at_task")
            or context.CLIARGS.get("step")
            or list(context.CLIARGS.get("tags") or []) not in ([], ["all"])
            or list(context.CLIARGS.get("skip_tags") or [])
        ):
            return self._fail("TASK_SELECTION_GUARD: refusing rclone install mutation under task selection")
        token = os.environ.get("CRISTEXWEB_RCLONE_INSTALL_TOKEN", "")
        attestation = os.environ.get("CRISTEXWEB_RCLONE_INSTALL_ATTESTATION_FILE", "")
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except OSError:
            return self._fail("ENTRYPOINT_GUARD: invalid rclone install attestation")
        binding = task_vars.get("rclone_install_internal_preflight_binding", {})
        valid = (
            os.environ.get("CRISTEXWEB_RCLONE_INSTALL_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and stat.S_ISREG(state.st_mode)
            and stat.S_IMODE(state.st_mode) == 0o600
            and state.st_uid == os.getuid()
            and content == f"{token}:entrypoint"
            and isinstance(binding, dict)
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding.get("service_contract") is True
            and binding.get("platform_contract") is True
            and task_vars.get("rclone_install_approved") is True
            and task_vars.get("rclone_install_state") in ("present", "absent")
        )
        if not valid:
            return self._fail("ENTRYPOINT_GUARD: refusing rclone install without complete guarded preflight")
        operation = self._task.args.get("operation")
        if set(self._task.args) != {"operation"}:
            return self._fail("MUTATION_ARGUMENT_GUARD: unexpected rclone install action arguments")
        controller_archive = str(Path(_EXPECTED_TASK_SOURCE).parents[3] / ".ansible/cache/rclone" / _ARCHIVE_NAME)
        if operation == "controller-cache-directories":
            changed = False
            for path, mode in (
                (str(Path(controller_archive).parents[1]), "0700"),
                (str(Path(controller_archive).parent), "0700"),
            ):
                result = self._run_action(
                    "ansible.builtin.file",
                    {"path": path, "state": "directory", "mode": mode},
                    tmp,
                    task_vars,
                )
                if result.get("failed"):
                    return result
                changed = changed or bool(result.get("changed"))
            return {"changed": changed}
        if operation == "host-directories":
            operator = binding.get("operator_user")
            home = binding.get("operator_home")
            operator_gid = binding.get("operator_gid")
            config_root_exists = binding.get("config_root_exists")
            if (
                not isinstance(operator, str)
                or not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", operator)
                or not isinstance(home, str)
                or home != f"/home/{operator}"
                or not isinstance(operator_gid, int)
                or operator_gid <= 0
                or not isinstance(config_root_exists, bool)
            ):
                return self._fail("MUTATION_ARGUMENT_GUARD: unsafe operator identity")
            entries = [
                ("/opt/rclone", "root", "root", "0755"),
                (f"/opt/rclone/{_VERSION}", "root", "root", "0755"),
                ("/var/cache/rclone", "root", "root", "0700"),
            ]
            if not config_root_exists:
                entries.append((f"{home}/.config", operator, str(operator_gid), "0700"))
            entries.append((f"{home}/.config/rclone", operator, str(operator_gid), "0700"))
            changed = False
            for path, owner, group, mode in entries:
                result = self._run_action(
                    "ansible.builtin.file",
                    {"path": path, "state": "directory", "owner": owner, "group": group, "mode": mode},
                    tmp,
                    task_vars,
                )
                if result.get("failed"):
                    return result
                changed = changed or bool(result.get("changed"))
            return {"changed": changed}
        if operation == "controller-download":
            if binding.get("controller_cache_complete") is True:
                return {"changed": False}
            sums_path = str(Path(controller_archive).parent / "SHA256SUMS")
            sums_result = self._run_action(
                "ansible.builtin.get_url",
                {
                    "url": f"https://downloads.rclone.org/v{_VERSION}/SHA256SUMS",
                    "dest": sums_path,
                    "checksum": "sha256:e7179eb69f2fda1b0a3c933d50a3e34e0f5f7e0fa0145c3e75110298b374d407",
                    "mode": "0600",
                    "validate_certs": True,
                },
                tmp,
                task_vars,
            )
            if sums_result.get("failed"):
                return sums_result
            try:
                expected_line = f"{_ARCHIVE_SHA256}  {_ARCHIVE_NAME}"
                if expected_line not in Path(sums_path).read_text().splitlines():
                    return self._fail("ARCHIVE_LAYOUT_GUARD: SHA256SUMS does not bind the exact archive")
            except OSError:
                return self._fail("ARCHIVE_LAYOUT_GUARD: unreadable SHA256SUMS")
            result = self._run_action(
                "ansible.builtin.get_url",
                {
                    "url": f"https://downloads.rclone.org/v{_VERSION}/{_ARCHIVE_NAME}",
                    "dest": controller_archive,
                    "checksum": f"sha256:{_ARCHIVE_SHA256}",
                    "mode": "0600",
                    "validate_certs": True,
                },
                tmp,
                task_vars,
            )
            if result.get("failed"):
                return result
            try:
                with zipfile.ZipFile(controller_archive) as archive:
                    members = {name.rstrip("/") for name in archive.namelist() if not name.endswith("/")}
                    if members != _MEMBERS:
                        return self._fail("ARCHIVE_LAYOUT_GUARD: unexpected rclone archive layout")
                    binary = archive.read("rclone-v1.71.1-linux-amd64/rclone")
                    digest = hashlib.sha256(binary).hexdigest()
                    if digest != _BINARY_SHA256:
                        return self._fail("ARCHIVE_LAYOUT_GUARD: unexpected rclone binary digest")
                    binary_cache = Path(controller_archive).parent / "rclone"
                    binary_changed = (
                        not binary_cache.is_file()
                        or hashlib.sha256(binary_cache.read_bytes()).hexdigest()
                        != _BINARY_SHA256
                    )
                    if binary_changed:
                        _write_binary_cache(binary_cache, binary)
            except (OSError, zipfile.BadZipFile, KeyError):
                return self._fail("ARCHIVE_LAYOUT_GUARD: unreadable rclone archive")
            result["changed"] = bool(
                result.get("changed")
                or sums_result.get("changed")
                or binary_changed
            )
            return result
        if operation == "host-archive-transfer":
            return self._run_action(
                "ansible.builtin.copy",
                {
                    "src": controller_archive,
                    "dest": f"/var/cache/rclone/{_ARCHIVE_NAME}",
                    "owner": "root",
                    "group": "root",
                    "mode": "0600",
                },
                tmp,
                task_vars,
            )
        if operation == "extract":
            return self._run_action(
                "ansible.builtin.copy",
                {
                    "src": str(Path(controller_archive).parent / "rclone"),
                    "dest": f"/opt/rclone/{_VERSION}/rclone",
                    "owner": "root",
                    "group": "root",
                    "mode": "0755",
                },
                tmp,
                task_vars,
            )
        if operation == "version-check":
            operator = binding.get("operator_user")
            if not isinstance(operator, str) or not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", operator):
                return self._fail("MUTATION_ARGUMENT_GUARD: unsafe operator identity")
            return self._run_action(
                "ansible.builtin.command",
                {"argv": ["/usr/local/bin/rclone", "version"]},
                tmp,
                task_vars,
            )
        if operation == "selector-present":
            return self._run_action(
                "ansible.builtin.file",
                {"src": f"/opt/rclone/{_VERSION}/rclone", "dest": "/usr/local/bin/rclone", "state": "link", "owner": "root", "group": "root", "force": False},
                tmp,
                task_vars,
            )
        if operation == "selector-absent":
            if task_vars.get("rclone_install_rollback_approved") is not True:
                return self._fail("ENTRYPOINT_GUARD: rollback approval is required")
            return self._run_action(
                "ansible.builtin.file", {"path": "/usr/local/bin/rclone", "state": "absent"}, tmp, task_vars
            )
        return self._fail("MUTATION_ARGUMENT_GUARD: unknown rclone install operation")
