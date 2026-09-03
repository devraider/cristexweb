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
_STRATEGY = Path(__file__).resolve()
_CONTROLLER = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_PLAYBOOK = _REPOSITORY_ROOT / "ansible/playbooks/configure_reactive_resume_dev_tls_renewal.yml"
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


def _file_contract(path: Path, mode: int, digest: str) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
        digest_actual = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeError):
        return False
    return (
        path.is_file()
        and not path.is_symlink()
        and state.st_uid == os.getuid()
        and state.st_gid == os.getgid()
        and (state.st_mode & 0o777) == mode
        and digest_actual == digest
    )


def _runtime_contract() -> bool:
    try:
        strategy_sha256 = hashlib.sha256(_STRATEGY.read_bytes()).hexdigest()
        controller_first_line = _CONTROLLER.read_text(encoding="utf-8").splitlines()[0]
    except (IndexError, OSError, UnicodeError):
        return False
    return (
        _file_contract(_CONTROLLER, 0o755, _CONTROLLER_SHA256)
        and controller_first_line == f"#!{_REPOSITORY_ROOT}/.venv/bin/python"
        and _file_contract(_ANSIBLE_CONFIG, 0o644, _ANSIBLE_CONFIG_SHA256)
        and _file_contract(_STRATEGY, 0o644, strategy_sha256)
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG)
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_CONTROLLER_SHA256")
        == _CONTROLLER_SHA256
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_ANSIBLE_CONFIG_SHA256")
        == _ANSIBLE_CONFIG_SHA256
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_SHA256")
        == strategy_sha256
        and not any(name in os.environ for name in _FORBIDDEN_ENV)
    )


def _canonical_argv() -> bool:
    """Require the wrapper's exact ansible-playbook argv before task iteration."""
    argv = sys.argv
    if not argv or argv[0] != str(_CONTROLLER):
        return False
    args = argv[1:]
    expected = [
        "-i",
        str(_INVENTORY_SOURCE),
        str(_PLAYBOOK),
        "--diff",
        "--limit",
        "crtxweb",
        "--ask-become-pass",
        "--extra-vars",
    ]
    if len(args) < len(expected) + 1 or args[: len(expected)] != expected:
        return False
    try:
        payload = json.loads(args[len(expected)])
    except (IndexError, TypeError, ValueError):
        return False
    if set(payload) != {
        "reactive_resume_dev_tls_renewal_approved",
        "reactive_resume_dev_tls_renewal_mode",
        "reactive_resume_dev_tls_renewal_repository_root",
    }:
        return False
    if payload.get("reactive_resume_dev_tls_renewal_approved") is not True:
        return False
    if payload.get("reactive_resume_dev_tls_renewal_mode") not in {"install", "enable"}:
        return False
    if payload.get("reactive_resume_dev_tls_renewal_repository_root") != str(_REPOSITORY_ROOT):
        return False
    return len(args) == len(expected) + 1 or (
        len(args) == len(expected) + 2 and args[-1] == "--check"
    )


def _selection_guard() -> bool:
    tags = list(context.CLIARGS.get("tags") or [])
    skip_tags = list(context.CLIARGS.get("skip_tags") or [])
    selection_options = (
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
                for option in selection_options
            )
        )
        for argument in sys.argv[1:]
    )
    inventory = context.CLIARGS.get("inventory") or []
    if isinstance(inventory, str):
        inventory = [inventory]
    return not (
        context.CLIARGS.get("start_at_task") is not None
        or context.CLIARGS.get("step")
        or selection_argv
        or tags not in ([], ["all"])
        or skip_tags
        or context.CLIARGS.get("subset") != "crtxweb"
        or context.CLIARGS.get("diff") is not True
        or inventory != [str(_INVENTORY_SOURCE)]
    )


class StrategyModule(LinearStrategyModule):
    """Reject task selection and wrapper/toolchain drift before task iteration."""

    def run(self, iterator, play_context):  # type: ignore[no-untyped-def]
        if not _selection_guard():
            raise AnsibleError(
                "TASK_SELECTION_GUARD: TLS renewal requires the complete guarded play"
            )
        if not (_inventory_contract() and _runtime_contract() and _canonical_argv()):
            raise AnsibleError(
                "ENTRYPOINT_GUARD: TLS renewal requires the complete guarded wrapper invocation"
            )
        return super().run(iterator, play_context)
