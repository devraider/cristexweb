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
_PLAYBOOK = _REPOSITORY_ROOT / "ansible/playbooks/check_cristexhub_prod_mongodb_credential_rotation.yml"
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_mongodb_credential_rotation_check/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_mongodb_credential_rotation_check/defaults/main.yml"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/check-cristexhub-prod-mongodb-credential-rotation"
_STRATEGY_SOURCE = Path(__file__).resolve()
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
# The strategy is loaded before any role task.  Its own marker is normalized
# solely to make this source pin non-circular; the wrapper has the same pin.
_STRATEGY_CANONICAL_SHA256 = "e1a593bbf25c726f5820b395b3e29674bd1849d36880eb45f737711ee6532e29"
_TASK_SHA256 = "eb726cae0983e50d6cb0c1f8b764dea6a52a55c9680c42219a862cc45efae014"
_DEFAULTS_SHA256 = "ead3ec7189b16a6d66e54e263a904619b5b9e46dacf8b40a6174792c4f381703"
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
    except (OSError, UnicodeError):
        return ""


def _canonical_hash(path: Path, symbol: str) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            rf"(?m)^({re.escape(symbol)}\s*=\s*[\"'])([0-9a-f]{{64}})([\"']\s*)$",
            rf"\g<1>{'0' * 64}\g<3>",
            source,
        )
        if count != 1:
            return ""
        return hashlib.sha256(source.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _regular_file(path: Path, mode: int, owner: int | None = None) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
    except OSError:
        return False
    return (
        stat.S_ISREG(state.st_mode)
        and not path.is_symlink()
        and stat.S_IMODE(state.st_mode) == mode
        and (owner is None or state.st_uid == owner)
    )


def _inventory_contract() -> bool:
    if not _regular_file(_INVENTORY_SOURCE, 0o600, os.getuid()):
        return False
    try:
        content = _INVENTORY_SOURCE.read_bytes()
    except OSError:
        return False
    return hashlib.sha256(content).hexdigest() == _INVENTORY_SHA256 and content == _INVENTORY_BYTES


def _canonical_argv() -> bool:
    argv = sys.argv[1:]
    if len(argv) != 9:
        return False
    if argv[:3] != ["-i", str(_INVENTORY_SOURCE), str(_PLAYBOOK)]:
        return False
    if argv[3:8] != ["--check", "--diff", "--limit", "crtxweb", "--extra-vars"]:
        return False
    try:
        payload = json.loads(argv[8])
    except (IndexError, TypeError, ValueError):
        return False
    return payload == {"cristexhub_prod_mongodb_credential_rotation_check_approved": True}


def _runtime_contract() -> bool:
    try:
        config_state = _ANSIBLE_CONFIG.stat(follow_symlinks=False)
        controller_state = _CONTROLLER.stat(follow_symlinks=False)
    except OSError:
        return False
    expected = {
        "CRISTEXWEB_PROD_MONGODB_ROTATION_WRAPPER_PATH": str(_WRAPPER_SOURCE),
        "CRISTEXWEB_PROD_MONGODB_ROTATION_WRAPPER_CANONICAL_SHA256": _canonical_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected"),
        "CRISTEXWEB_PROD_MONGODB_ROTATION_STRATEGY_SHA256": _sha256(_STRATEGY_SOURCE),
        "CRISTEXWEB_PROD_MONGODB_ROTATION_CONTROLLER_SHA256": _CONTROLLER_SHA256,
        "CRISTEXWEB_PROD_MONGODB_ROTATION_ANSIBLE_CONFIG_SHA256": _ANSIBLE_CONFIG_SHA256,
    }
    return (
        _regular_file(_ANSIBLE_CONFIG, 0o644, os.getuid())
        and _regular_file(_CONTROLLER, 0o775, os.getuid())
        and hashlib.sha256(_ANSIBLE_CONFIG.read_bytes()).hexdigest() == _ANSIBLE_CONFIG_SHA256
        and hashlib.sha256(_CONTROLLER.read_bytes()).hexdigest() == _CONTROLLER_SHA256
        and config_state.st_gid == os.getgid()
        and controller_state.st_gid == os.getgid()
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG)
        and os.environ.get("CRISTEXWEB_PROD_MONGODB_ROTATION_ENTRYPOINT") == "v1"
        and os.environ.get("CRISTEXWEB_PROD_MONGODB_ROTATION_MODE") == "check"
        and os.environ.get("CRISTEXWEB_PROD_MONGODB_ROTATION_TOKEN", "")
        and all(os.environ.get(key) == value for key, value in expected.items())
        and not any(name in os.environ for name in _FORBIDDEN_ENV)
    )


def _source_contract() -> bool:
    return (
        _regular_file(_STRATEGY_SOURCE, 0o644, os.getuid())
        and _canonical_hash(_STRATEGY_SOURCE, "_STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256
        and os.environ.get("CRISTEXWEB_PROD_MONGODB_ROTATION_STRATEGY_SHA256") == _sha256(_STRATEGY_SOURCE)
        and _regular_file(_TASK_SOURCE, 0o644, os.getuid())
        and _sha256(_TASK_SOURCE) == _TASK_SHA256
        and _regular_file(_DEFAULTS_SOURCE, 0o644, os.getuid())
        and _sha256(_DEFAULTS_SOURCE) == _DEFAULTS_SHA256
        and os.environ.get("CRISTEXWEB_PROD_MONGODB_ROTATION_TASK_SHA256") == _TASK_SHA256
        and os.environ.get("CRISTEXWEB_PROD_MONGODB_ROTATION_DEFAULTS_SHA256") == _DEFAULTS_SHA256
        and os.environ.get("CRISTEXWEB_PROD_MONGODB_ROTATION_PLAYBOOK_SHA256") == _sha256(_PLAYBOOK)
        and os.environ.get("CRISTEXWEB_PROD_MONGODB_ROTATION_STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256
    )


def _no_vars_plugins() -> bool:
    for name in ("host_vars", "group_vars"):
        if (_INVENTORY_SOURCE.parent / name).exists():
            return False
    return True


class StrategyModule(LinearStrategyModule):
    """Reject direct playbooks and task-selection controls before role tasks load."""

    def run(self, iterator, play_context):  # type: ignore[no-untyped-def]
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        inventory = context.CLIARGS.get("inventory") or []
        if isinstance(inventory, str):
            inventory = [inventory]
        selection_argv = any(
            argument in {"--start-at-task", "--step", "--tags", "--skip-tags", "-t"}
            or argument.startswith(("--start-at-task=", "--tags=", "--skip-tags=", "-t="))
            for argument in sys.argv[1:]
        )
        if (
            selection_argv
            or context.CLIARGS.get("start_at_task") is not None
            or context.CLIARGS.get("step")
            or tags not in ([], ["all"])
            or skip_tags
            or context.CLIARGS.get("subset") != "crtxweb"
            or context.CLIARGS.get("check") is not True
            or context.CLIARGS.get("diff") is not True
            or inventory != [str(_INVENTORY_SOURCE)]
            or not _inventory_contract()
            or not _canonical_argv()
            or not _runtime_contract()
            or not _source_contract()
            or not _no_vars_plugins()
        ):
            raise AnsibleError(
                "TASK_SELECTION_GUARD: MongoDB rotation requires the complete canonical wrapper invocation"
            )
        return super().run(iterator, play_context)
