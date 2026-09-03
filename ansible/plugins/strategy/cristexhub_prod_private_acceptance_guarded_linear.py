from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

from ansible import context
from ansible.errors import AnsibleError
from ansible.plugins.strategy.linear import StrategyModule as LinearStrategyModule


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/check_cristexhub_prod_private_acceptance.yml"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/check-cristexhub-prod-private-acceptance"
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_private_acceptance/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_private_acceptance/defaults/main.yml"
_ACTION_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/action/cristexhub_prod_private_acceptance_process_guarded.py"
_INVENTORY_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/inventory.local.yml"
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_STRATEGY_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/strategy/cristexhub_prod_private_acceptance_guarded_linear.py"

# This pin is canonicalized by zeroing it before hashing. The wrapper and action
# hold independent raw and canonical pins, so this strategy cannot self-authorize
# a modified source before task iteration.
_STRATEGY_CANONICAL_SHA256 = "e1a2e9732aa96ae62646f2c0264bce3d6cb8be211dddf49e700b9726f15835ab"
_INVENTORY_SHA256 = "652a8455f8a050005ab783d20d4e60a0cd034d8a6439f1cffe551a91102773b0"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_EXPECTED_SOURCE_MODES = {
    _PLAYBOOK_SOURCE: 0o644,
    _WRAPPER_SOURCE: 0o755,
    _TASK_SOURCE: 0o644,
    _DEFAULTS_SOURCE: 0o644,
    _ACTION_SOURCE: 0o644,
    _INVENTORY_SOURCE: 0o600,
    _ANSIBLE_CONFIG_SOURCE: 0o644,
    _STRATEGY_SOURCE: 0o644,
}
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


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _canonical_file_hash(path: Path, symbol: str) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            rf"(?m)^({re.escape(symbol)}\s*=\s*[\"'])([0-9a-f]{{64}})([\"']\s*)$",
            rf"\g<1>{'0' * 64}\g<3>",
            source,
        )
        return hashlib.sha256(source.encode("utf-8")).hexdigest() if count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _regular_file(path: Path, mode: int) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
    except OSError:
        return False
    return (
        stat.S_ISREG(state.st_mode)
        and not path.is_symlink()
        and stat.S_IMODE(state.st_mode) == mode
        and state.st_uid == os.getuid()
        and state.st_gid == os.getgid()
    )


def _inventory_contract() -> bool:
    try:
        content = _INVENTORY_SOURCE.read_bytes()
    except OSError:
        return False
    return (
        _regular_file(_INVENTORY_SOURCE, 0o600)
        and hashlib.sha256(content).hexdigest() == _INVENTORY_SHA256
        and content == (
            b"---\nall:\n  children:\n    k3s_servers:\n      hosts:\n"
            b"        crtxweb:\n          ansible_connection: local\n"
            b"          ansible_python_interpreter: /usr/bin/python3\n"
            b"          ansible_user: paul\n"
        )
    )


def _source_contract() -> bool:
    if not all(_regular_file(path, mode) for path, mode in _EXPECTED_SOURCE_MODES.items()):
        return False
    supplied = {
        "PLAYBOOK_SHA256": _sha256(_PLAYBOOK_SOURCE),
        "WRAPPER_SHA256": _sha256(_WRAPPER_SOURCE),
        "TASK_SHA256": _sha256(_TASK_SOURCE),
        "DEFAULTS_SHA256": _sha256(_DEFAULTS_SOURCE),
        "ACTION_SHA256": _sha256(_ACTION_SOURCE),
        "INVENTORY_SHA256": _sha256(_INVENTORY_SOURCE),
        "ANSIBLE_CONFIG_SHA256": _sha256(_ANSIBLE_CONFIG_SOURCE),
        "CONTROLLER_SHA256": _sha256(_CONTROLLER_SOURCE),
        "STRATEGY_SHA256": _sha256(_STRATEGY_SOURCE),
    }
    prefix = "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_"
    if any(os.environ.get(prefix + key, "") != value for key, value in supplied.items()):
        return False
    if (
        _canonical_file_hash(_STRATEGY_SOURCE, "_STRATEGY_CANONICAL_SHA256")
        != _STRATEGY_CANONICAL_SHA256
        or os.environ.get(prefix + "STRATEGY_CANONICAL_SHA256") != _STRATEGY_CANONICAL_SHA256
        or _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected")
        != os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256")
    ):
        return False
    return (
        _inventory_contract()
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG_SOURCE)
        and _regular_file(_CONTROLLER_SOURCE, 0o775)
        and _sha256(_CONTROLLER_SOURCE) == _CONTROLLER_SHA256
        and not any(name in os.environ for name in _FORBIDDEN_ENV)
    )


def _canonical_argv() -> bool:
    argv = sys.argv[1:]
    expected = [
        "-i",
        str(_INVENTORY_SOURCE),
        str(_PLAYBOOK_SOURCE),
        "--check",
        "--diff",
        "--limit",
        "crtxweb",
        "--extra-vars",
        '{"cristexhub_prod_private_acceptance_approved":true}',
    ]
    return argv == expected


def _selection_contract() -> bool:
    inventory = context.CLIARGS.get("inventory") or []
    inventory = [inventory] if isinstance(inventory, str) else list(inventory)
    tags = list(context.CLIARGS.get("tags") or [])
    skip_tags = list(context.CLIARGS.get("skip_tags") or [])
    return (
        _canonical_argv()
        and context.CLIARGS.get("start_at_task") is None
        and context.CLIARGS.get("step") in (None, False)
        and tags in ([], ["all"])
        and not skip_tags
        and context.CLIARGS.get("subset") == "crtxweb"
        and context.CLIARGS.get("check") is True
        and context.CLIARGS.get("diff") is True
        and inventory == [str(_INVENTORY_SOURCE)]
    )


class StrategyModule(LinearStrategyModule):
    """Reject bypass controls and source drift before Ansible can iterate tasks."""

    def run(self, iterator, play_context):  # type: ignore[no-untyped-def]
        if not _selection_contract() or not _source_contract():
            raise AnsibleError(
                "ENTRYPOINT_GUARD: private PROD acceptance requires the canonical wrapper, "
                "source closure, and unmodified task selection"
            )
        os.environ["CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_STRATEGY_ATTESTED"] = "v1"
        return super().run(iterator, play_context)
