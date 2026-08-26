from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from ansible import context
from ansible.errors import AnsibleError
from ansible.plugins.strategy.linear import StrategyModule as LinearStrategyModule


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_INVENTORY_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/inventory.local.yml"
_INVENTORY_SHA256 = "652a8455f8a050005ab783d20d4e60a0cd034d8a6439f1cffe551a91102773b0"
_INVENTORY_BYTES = (
    b"---\nall:\n  children:\n    k3s_servers:\n      hosts:\n"
    b"        crtxweb:\n          ansible_connection: local\n"
    b"          ansible_python_interpreter: /usr/bin/python3\n"
    b"          ansible_user: paul\n"
)
_ANSIBLE_CONFIG = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_CONTROLLER = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_FORBIDDEN_ENV = (
    "ANSIBLE_INVENTORY",
    "ANSIBLE_PLAYBOOK_DIR",
    "ANSIBLE_STRATEGY",
    "ANSIBLE_ACTION_PLUGINS",
    "ANSIBLE_STRATEGY_PLUGINS",
    "ANSIBLE_LIBRARY",
    "ANSIBLE_COLLECTIONS_PATH",
    "ANSIBLE_STDOUT_CALLBACK",
    "ANSIBLE_CALLBACK_PLUGINS",
    "ANSIBLE_LOAD_CALLBACK_PLUGINS",
    "ANSIBLE_VAULT_PASSWORD_FILE",
    "ANSIBLE_PRIVATE_KEY_FILE",
    "ANSIBLE_REMOTE_USER",
    "ANSIBLE_BECOME_EXE",
    "ANSIBLE_BECOME_METHOD",
    "ANSIBLE_BECOME_USER",
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTHONOPTIMIZE",
    "PYTHONINSPECT",
    "PYTHONBREAKPOINT",
    "VIRTUAL_ENV",
)


def _inventory_contract() -> bool:
    try:
        state = _INVENTORY_SOURCE.stat(follow_symlinks=False)
        content = _INVENTORY_SOURCE.read_bytes()
    except OSError:
        return False
    return (
        state.st_uid == os.getuid()
        and state.st_gid == os.getgid()
        and (state.st_mode & 0o777) == 0o600
        and not _INVENTORY_SOURCE.is_symlink()
        and hashlib.sha256(content).hexdigest() == _INVENTORY_SHA256
        and content == _INVENTORY_BYTES
    )


def _canonical_argv() -> bool:
    argv = sys.argv[1:]
    if not argv or argv[0] != "-i" or len(argv) < 8:
        return False
    if argv[1] != str(_INVENTORY_SOURCE) or argv[2] != str(_REPOSITORY_ROOT / "ansible/playbooks/configure_reactive_resume_dev_backup.yml"):
        return False
    expected = ["--diff", "--limit", "crtxweb", "--ask-become-pass", "--extra-vars"]
    if argv[3:8] != expected:
        return False
    try:
        payload = json.loads(argv[8])
    except (IndexError, TypeError, ValueError):
        return False
    if set(payload) != {
        "reactive_resume_dev_backup_approved",
        "reactive_resume_dev_backup_mode",
        "reactive_resume_dev_backup_repository_root",
    }:
        return False
    if payload != {
        "reactive_resume_dev_backup_approved": True,
        "reactive_resume_dev_backup_mode": payload["reactive_resume_dev_backup_mode"],
        "reactive_resume_dev_backup_repository_root": str(_REPOSITORY_ROOT),
    } or payload["reactive_resume_dev_backup_mode"] not in {"install", "test", "restore", "enable"}:
        return False
    return len(argv) == 9 or (len(argv) == 10 and argv[9] == "--check")


def _runtime_contract() -> bool:
    try:
        state = _CONTROLLER.stat(follow_symlinks=False)
        with _CONTROLLER.open("r", encoding="utf-8") as source:
            first_line = source.readline().rstrip("\n")
        digest = hashlib.sha256(_CONTROLLER.read_bytes()).hexdigest()
    except (OSError, UnicodeError):
        return False
    return (
        state.st_uid == os.getuid()
        and state.st_gid == os.getgid()
        and (state.st_mode & 0o777) == 0o755
        and not _CONTROLLER.is_symlink()
        and digest == _CONTROLLER_SHA256
        and first_line == f"#!{_REPOSITORY_ROOT}/.venv/bin/python"
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG)
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_CONTROLLER_PATH") == str(_CONTROLLER)
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_CONTROLLER_SHA256") == _CONTROLLER_SHA256
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ANSIBLE_CONFIG_SHA256") == _ANSIBLE_CONFIG_SHA256
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_STRATEGY_SHA256")
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_COLLECTION_MANIFEST_SHA256")
        and not any(name in os.environ for name in _FORBIDDEN_ENV)
    )


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
        inventory = context.CLIARGS.get("inventory") or []
        if isinstance(inventory, str):
            inventory = [inventory]
        if (
            context.CLIARGS.get("start_at_task") is not None
            or context.CLIARGS.get("step")
            or selection_argv
            or tags not in ([], ["all"])
            or skip_tags
            or context.CLIARGS.get("subset") != "crtxweb"
            or context.CLIARGS.get("diff") is not True
            or inventory != [str(_INVENTORY_SOURCE)]
            or not _inventory_contract()
            or not _runtime_contract()
            or not _canonical_argv()
        ):
            raise AnsibleError(
                "TASK_SELECTION_GUARD: backup requires the complete guarded wrapper invocation"
            )
        return super().run(iterator, play_context)
