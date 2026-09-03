from __future__ import annotations

import hashlib
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

from ansible import context
from ansible.plugins.action import ActionBase

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_private_acceptance/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_private_acceptance/defaults/main.yml"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/check_cristexhub_prod_private_acceptance.yml"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/check-cristexhub-prod-private-acceptance"
_INVENTORY_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/inventory.local.yml"
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_ACTION_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/action/cristexhub_prod_private_acceptance_process_guarded.py"
_STRATEGY_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/strategy/cristexhub_prod_private_acceptance_guarded_linear.py"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_PYTHON_SOURCE = Path("/usr/bin/python3")
_EXPECTED_OPERATOR = "paul"
_EXPECTED_KUBECONFIG = Path("/etc/rancher/k3s/k3s.yaml")
_PYTHON_OWNER_UID = 0
_PYTHON_OWNER_GID = 0
_PYTHON_LINK_MODE = 0o777
_PYTHON_TARGET_MODE = 0o755
_PYTHON_COMPONENT_MODE = 0o755
_PYTHON_MAX_LINK_DEPTH = 8

# These values are source pins, not task inputs. They are refreshed whenever one
# of the leaves changes; the action's own pin is canonicalized by zeroing it.
_ACTION_CANONICAL_SHA256 = "409c328166c245e671c7e82605c6a7aa6d59b92bd6e0e5ccc1ed43164156e5ce"
_STRATEGY_CANONICAL_SHA256 = "e1a2e9732aa96ae62646f2c0264bce3d6cb8be211dddf49e700b9726f15835ab"


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeError):
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


def _secure_python_directory(path: Path) -> bool:
    """Require every interpreter path directory to be root-owned and private."""
    if not path.is_absolute():
        return False
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        try:
            state = current.lstat()
        except OSError:
            return False
        if (
            not stat.S_ISDIR(state.st_mode)
            or stat.S_ISLNK(state.st_mode)
            or state.st_uid != _PYTHON_OWNER_UID
            or state.st_gid != _PYTHON_OWNER_GID
            or stat.S_IMODE(state.st_mode) != _PYTHON_COMPONENT_MODE
        ):
            return False
    return True


def _python_target() -> Path | None:
    """Resolve the fixed system Python link without trusting writable components."""
    current = _PYTHON_SOURCE
    seen: set[tuple[int, int]] = set()
    for depth in range(_PYTHON_MAX_LINK_DEPTH):
        if not current.is_absolute() or not _secure_python_directory(current.parent):
            return None
        try:
            state = current.lstat()
        except OSError:
            return None
        identity = (state.st_dev, state.st_ino)
        if identity in seen:
            return None
        seen.add(identity)
        if stat.S_ISLNK(state.st_mode):
            if (
                depth == 0
                and current != _PYTHON_SOURCE
                or state.st_uid != _PYTHON_OWNER_UID
                or state.st_gid != _PYTHON_OWNER_GID
                or stat.S_IMODE(state.st_mode) != _PYTHON_LINK_MODE
                or state.st_nlink != 1
            ):
                return None
            try:
                link_target = os.readlink(current)
            except OSError:
                return None
            if not link_target:
                return None
            current = Path(link_target) if os.path.isabs(link_target) else current.parent / link_target
            current = Path(os.path.normpath(str(current)))
            continue
        if (
            depth == 0
            or not stat.S_ISREG(state.st_mode)
            or state.st_uid != _PYTHON_OWNER_UID
            or state.st_gid != _PYTHON_OWNER_GID
            or stat.S_IMODE(state.st_mode) != _PYTHON_TARGET_MODE
            or state.st_nlink != 1
        ):
            return None
        return current
    return None


def _python_runtime_contract() -> bool:
    target = _python_target()
    if target is None:
        return False
    supplied = os.environ.get("CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_PYTHON_SHA256", "")
    return (
        re.fullmatch(r"[0-9a-f]{64}", supplied) is not None
        and _sha256(target) == supplied
    )


def _proc_starttime(pid: int) -> str:
    try:
        # The command name is parenthesized and may itself contain spaces or
        # parentheses.  Everything after the final ") " starts at field 3.
        tail = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").rsplit(") ", 1)[1].split()
        return tail[19]
    except (OSError, UnicodeError, IndexError):
        return ""


def _proc_parent(pid: int) -> int:
    try:
        status = Path(f"/proc/{pid}/status").read_text(encoding="ascii")
        line = next(line for line in status.splitlines() if line.startswith("PPid:"))
        return int(line.split()[1])
    except (OSError, UnicodeError, StopIteration, ValueError, IndexError):
        return 0


def _ancestor(pid: int) -> bool:
    current = os.getpid()
    seen: set[int] = set()
    while current > 1 and current not in seen:
        if current == pid:
            return True
        seen.add(current)
        current = _proc_parent(current)
    return False


def _proc_cmdline(pid: int) -> list[str]:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        if not raw.endswith(b"\0"):
            return []
        return [item.decode("utf-8", "strict") for item in raw[:-1].split(b"\0")]
    except (OSError, UnicodeError):
        return []


def _expected_argv() -> list[str]:
    return [
        str(_CONTROLLER_SOURCE),
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


def _selection_is_canonical() -> bool:
    inventory = context.CLIARGS.get("inventory") or []
    inventory = [inventory] if isinstance(inventory, str) else list(inventory)
    return (
        sys.argv == _expected_argv()
        and context.CLIARGS.get("start_at_task") is None
        and context.CLIARGS.get("step") in (None, False)
        and list(context.CLIARGS.get("tags") or []) in ([], ["all"])
        and not list(context.CLIARGS.get("skip_tags") or [])
        and context.CLIARGS.get("subset") == "crtxweb"
        and bool(context.CLIARGS.get("check"))
        and bool(context.CLIARGS.get("diff"))
        and inventory == [str(_INVENTORY_SOURCE)]
        and not any(
            os.environ.get(name)
            for name in (
                "ANSIBLE_LIBRARY",
                "ANSIBLE_ACTION_PLUGINS",
                "ANSIBLE_ROLES_PATH",
                "ANSIBLE_COLLECTIONS_PATH",
                "ANSIBLE_STRATEGY_PLUGINS",
            )
        )
    )


def _source_closure_valid() -> bool:
    prefix = "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_"
    expected = (
        (_TASK_SOURCE, "TASK_SHA256", 0o644),
        (_DEFAULTS_SOURCE, "DEFAULTS_SHA256", 0o644),
        (_PLAYBOOK_SOURCE, "PLAYBOOK_SHA256", 0o644),
        (_INVENTORY_SOURCE, "INVENTORY_SHA256", 0o600),
        (_ANSIBLE_CONFIG_SOURCE, "ANSIBLE_CONFIG_SHA256", 0o644),
        (_ACTION_SOURCE, "ACTION_SHA256", 0o644),
        (_STRATEGY_SOURCE, "STRATEGY_SHA256", 0o644),
        (_WRAPPER_SOURCE, "WRAPPER_SHA256", 0o755),
    )
    for path, suffix, mode in expected:
        try:
            state = path.stat(follow_symlinks=False)
            digest = _sha256(path)
            supplied = os.environ.get(prefix + suffix, "")
            if (
                not path.is_file()
                or path.is_symlink()
                or stat.S_IMODE(state.st_mode) != mode
                or state.st_uid != os.getuid()
                or not re.fullmatch(r"[0-9a-f]{64}", supplied)
                or digest != supplied
            ):
                return False
        except OSError:
            return False
    try:
        controller = _CONTROLLER_SOURCE.stat(follow_symlinks=False)
        return (
            stat.S_ISREG(controller.st_mode)
            and not _CONTROLLER_SOURCE.is_symlink()
            and stat.S_IMODE(controller.st_mode) == 0o775
            and controller.st_uid == os.getuid()
            and _sha256(_CONTROLLER_SOURCE) == os.environ.get(prefix + "CONTROLLER_SHA256")
            and _python_runtime_contract()
            and _canonical_file_hash(_ACTION_SOURCE, "_ACTION_CANONICAL_SHA256") == _ACTION_CANONICAL_SHA256
            and _canonical_file_hash(_STRATEGY_SOURCE, "_STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256
            and os.environ.get(prefix + "STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256
            and os.environ.get(prefix + "STRATEGY_ATTESTED") == "v1"
            and _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected")
            == os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256")
        )
    except OSError:
        return False


def _wrapper_binding_valid(task_vars: dict[str, Any]) -> bool:
    prefix = "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_"
    attestation_path = os.environ.get(prefix + "ATTESTATION_FILE", "")
    pid_text = os.environ.get(prefix + "WRAPPER_PID", "")
    starttime = os.environ.get(prefix + "WRAPPER_STARTTIME", "")
    wrapper_path = os.environ.get(prefix + "WRAPPER_PATH", "")
    wrapper_sha = os.environ.get(prefix + "WRAPPER_SHA256", "")
    token = os.environ.get(prefix + "TOKEN", "")
    try:
        pid = int(pid_text)
        state = os.stat(attestation_path, follow_symlinks=False)
        content = Path(attestation_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return False
    source_closure = ":".join(
        os.environ.get(prefix + name, "")
        for name in (
            "TASK_SHA256",
            "DEFAULTS_SHA256",
            "PLAYBOOK_SHA256",
            "ACTION_SHA256",
            "INVENTORY_SHA256",
            "ANSIBLE_CONFIG_SHA256",
            "CONTROLLER_SHA256",
            "PYTHON_SHA256",
            "STRATEGY_SHA256",
        )
    )
    expected_closure = hashlib.sha256(source_closure.encode("utf-8")).hexdigest()
    return (
        os.environ.get(prefix + "ENTRYPOINT") == "v2"
        and re.fullmatch(r"[0-9a-f]{64}", token) is not None
        and pid > 1
        and _ancestor(pid)
        and _proc_starttime(pid) == starttime
        and state.st_uid == os.getuid()
        and stat.S_ISREG(state.st_mode)
        and not stat.S_ISLNK(state.st_mode)
        and stat.S_IMODE(state.st_mode) == 0o600
        and state.st_nlink == 1
        and Path(wrapper_path) == _WRAPPER_SOURCE
        and wrapper_sha == _sha256(_WRAPPER_SOURCE)
        and _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected")
        == os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256")
        and _proc_cmdline(pid) == ["/bin/dash", str(_WRAPPER_SOURCE), "check"]
        and content == f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\n"
        and os.environ.get(prefix + "OPERATOR") == _EXPECTED_OPERATOR
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG_SOURCE)
        and os.environ.get(prefix + "CONTROLLER") == str(_CONTROLLER_SOURCE)
        and os.environ.get(prefix + "PYTHON") == str(_PYTHON_SOURCE)
        and os.environ.get(prefix + "KUBECONFIG") == str(_EXPECTED_KUBECONFIG)
        and os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256")
        == _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected")
        and os.environ.get(prefix + "TASK_SHA256") == _sha256(_TASK_SOURCE)
        and os.environ.get(prefix + "DEFAULTS_SHA256") == _sha256(_DEFAULTS_SOURCE)
        and os.environ.get(prefix + "PLAYBOOK_SHA256") == _sha256(_PLAYBOOK_SOURCE)
        and os.environ.get(prefix + "ACTION_SHA256") == _sha256(_ACTION_SOURCE)
        and os.environ.get(prefix + "STRATEGY_SHA256") == _sha256(_STRATEGY_SOURCE)
        and os.environ.get(prefix + "STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256
        and os.environ.get(prefix + "STRATEGY_ATTESTED") == "v1"
        and os.environ.get(prefix + "INVENTORY_SHA256") == _sha256(_INVENTORY_SOURCE)
        and os.environ.get(prefix + "ANSIBLE_CONFIG_SHA256") == _sha256(_ANSIBLE_CONFIG_SOURCE)
        and os.environ.get(prefix + "CONTROLLER_SHA256") == _sha256(_CONTROLLER_SOURCE)
        and os.environ.get(prefix + "PYTHON_SHA256") == (_sha256(_python_target()) if _python_target() else "")
        and os.environ.get(prefix + "SOURCE_CLOSURE_SHA256") == expected_closure
        and task_vars.get("cristexhub_prod_private_acceptance_approved") is True
        and bool(context.CLIARGS.get("check"))
        and bool(context.CLIARGS.get("diff"))
    )


class ActionModule(ActionBase):
    """Validate private PROD acceptance provenance before any read-only task."""

    TRANSFERS_FILES = False

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        result = super().run(tmp=tmp, task_vars=task_vars)
        task_vars = task_vars or {}
        if any(
            key.startswith("cristexhub_prod_private_acceptance_internal_")
            for key in task_vars
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": "ENTRYPOINT_GUARD: externally supplied private PROD acceptance internals",
            }
        if self._task.args != {"state": "check"}:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: invalid process guard arguments"}
        if not _selection_is_canonical():
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: non-canonical private PROD acceptance argv or task selection"}
        if not _source_closure_valid() or not _wrapper_binding_valid(task_vars):
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: private PROD acceptance requires the canonical wrapper ancestor"}
        result.update(changed=False, failed=False, process_guarded=True)
        return result
