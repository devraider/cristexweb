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
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/check-cristexhub-prod-ghcr-pull-rotation"
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_ghcr_pull_rotation_preflight/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_ghcr_pull_rotation_preflight/defaults/main.yml"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/check_cristexhub_prod_ghcr_pull_rotation.yml"
_METADATA_SOURCE = _REPOSITORY_ROOT / "ansible/library/cristexhub_prod_ghcr_pull_secret_metadata.py"
_POLICY_SOURCE = _REPOSITORY_ROOT / "ansible/files/policies/cristexhub-prod-ghcr-pull-rotation.yml"
_STRATEGY_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/strategy/cristexhub_prod_ghcr_pull_rotation_guarded_linear.py"
_INVENTORY_SOURCE = _REPOSITORY_ROOT / "ansible/inventory/hosts.yml"
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_REQUIREMENTS_SOURCE = _REPOSITORY_ROOT / "ansible/requirements.yml"
_COLLECTION_MANIFEST_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/collections/ansible_collections/kubernetes/core/MANIFEST.json"
_COLLECTION_FILES_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/collections/ansible_collections/kubernetes/core/FILES.json"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"

_TASK_SHA256 = "f2fa470f4343a40d159d2aab4853a794fe75aacb0db22e1fe03ad4f9c2f6eb31"
_DEFAULTS_SHA256 = "073fb314b6197e9e283912d5ae0183299e526d4d53706104ec45f05812adf33f"
_PLAYBOOK_SHA256 = "1aa2553934d39f23f425921f9ed7d78addb9079a2beea9a7a1e0819de4e8b061"
_METADATA_SHA256 = "be834fae4afd0001f15f807f6e52f511dd040a843747bf03c2b5ddc3efd0068e"
_POLICY_SHA256 = "6cfd66000b544ff848c2f81542d2c65d7f53bb615d95b3227b4adcc93f82407d"
_INVENTORY_SHA256 = "843dd43cdce256061d8e6b58b563acd00c3a1d7a1357e5f59ea30040af244752"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_REQUIREMENTS_SHA256 = "f82d9e5ba1b64324710eb66c956d0447c46d3958722f635a4502bcb6c3efc75f"
_COLLECTION_MANIFEST_SHA256 = "dc32e90ca987d6199e9091f749ecb40fd3380b40aabb7c18961ec75582cfc6df"
_COLLECTION_FILES_SHA256 = "9d30dde4e4d6d04ec2e9b00a2d787114f13577fd2c456d25726865e3db39fa69"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_STRATEGY_CANONICAL_SHA256 = "3e25c672daa083f3a805101f05e667f4cddc31eb28744ccdd1f36b70c6124465"

_EXPECTED_ENV_PREFIX = "CRISTEXWEB_CRISTEXHUB_PROD_GHCR_PULL_ROTATION_PREFLIGHT_"
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
        return hashlib.sha256(source.encode("utf-8")).hexdigest() if count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _regular(path: Path, mode: int, owner: int | None = None) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
    except OSError:
        return False
    return (
        stat.S_ISREG(state.st_mode)
        and not path.is_symlink()
        and stat.S_IMODE(state.st_mode) == mode
        and (owner is None or (state.st_uid == owner and state.st_gid == os.getgid()))
    )


def _inventory_contract() -> bool:
    try:
        content = _INVENTORY_SOURCE.read_bytes()
    except OSError:
        return False
    return (
        _regular(_INVENTORY_SOURCE, 0o644, os.getuid())
        and hashlib.sha256(content).hexdigest() == _INVENTORY_SHA256
        and content
        == b"---\nall:\n  children:\n    k3s_servers:\n      hosts:\n        crtxweb:\n"
    )


def _source_contract() -> bool:
    expected = (
        (_WRAPPER_SOURCE, "WRAPPER_SHA256", 0o755, None),
        (_TASK_SOURCE, "TASK_SHA256", 0o644, os.getuid()),
        (_DEFAULTS_SOURCE, "DEFAULTS_SHA256", 0o644, os.getuid()),
        (_PLAYBOOK_SOURCE, "PLAYBOOK_SHA256", 0o644, os.getuid()),
        (_METADATA_SOURCE, "METADATA_MODULE_SHA256", 0o644, os.getuid()),
        (_POLICY_SOURCE, "POLICY_SHA256", 0o644, os.getuid()),
        (_STRATEGY_SOURCE, "STRATEGY_SHA256", 0o644, os.getuid()),
        (_ANSIBLE_CONFIG_SOURCE, "ANSIBLE_CONFIG_SHA256", 0o644, os.getuid()),
        (_REQUIREMENTS_SOURCE, "REQUIREMENTS_SHA256", 0o644, os.getuid()),
        (_COLLECTION_MANIFEST_SOURCE, "COLLECTION_MANIFEST_SHA256", 0o644, os.getuid()),
        (_COLLECTION_FILES_SOURCE, "COLLECTION_FILES_SHA256", 0o644, os.getuid()),
        (_INVENTORY_SOURCE, "INVENTORY_SHA256", 0o644, os.getuid()),
        (_CONTROLLER_SOURCE, "CONTROLLER_SHA256", 0o755, os.getuid()),
    )
    fixed = {
        "TASK_SHA256": _TASK_SHA256,
        "DEFAULTS_SHA256": _DEFAULTS_SHA256,
        "PLAYBOOK_SHA256": _PLAYBOOK_SHA256,
        "METADATA_MODULE_SHA256": _METADATA_SHA256,
        "POLICY_SHA256": _POLICY_SHA256,
        "ANSIBLE_CONFIG_SHA256": _ANSIBLE_CONFIG_SHA256,
        "REQUIREMENTS_SHA256": _REQUIREMENTS_SHA256,
        "COLLECTION_MANIFEST_SHA256": _COLLECTION_MANIFEST_SHA256,
        "COLLECTION_FILES_SHA256": _COLLECTION_FILES_SHA256,
        "INVENTORY_SHA256": _INVENTORY_SHA256,
        "CONTROLLER_SHA256": _CONTROLLER_SHA256,
    }
    if not _inventory_contract() or _canonical_hash(_STRATEGY_SOURCE, "_STRATEGY_CANONICAL_SHA256") != _STRATEGY_CANONICAL_SHA256:
        return False
    if os.environ.get(_EXPECTED_ENV_PREFIX + "STRATEGY_CANONICAL_SHA256") != _STRATEGY_CANONICAL_SHA256:
        return False
    for path, suffix, mode, owner in expected:
        if not _regular(path, mode, owner):
            return False
        digest = _sha256(path)
        supplied = os.environ.get(_EXPECTED_ENV_PREFIX + suffix, "")
        if suffix in {"WRAPPER_SHA256", "STRATEGY_SHA256"}:
            if digest != supplied:
                return False
        elif digest != fixed[suffix] or digest != supplied:
            return False
    return True


def _proc_parent(pid: int) -> int:
    try:
        text = Path(f"/proc/{pid}/status").read_text(encoding="ascii")
        return int(next(line for line in text.splitlines() if line.startswith("PPid:")).split()[1])
    except (OSError, UnicodeError, StopIteration, ValueError, IndexError):
        return 0


def _proc_starttime(pid: int) -> str:
    try:
        tail = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").rsplit(") ", 1)[1].split()
        return tail[19]
    except (OSError, UnicodeError, IndexError):
        return ""


def _proc_cmdline(pid: int) -> list[str]:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        if not raw.endswith(b"\0"):
            return []
        return [part.decode("utf-8", "strict") for part in raw[:-1].split(b"\0")]
    except (OSError, UnicodeError):
        return []


def _is_ancestor(pid: int) -> bool:
    current = os.getpid()
    seen: set[int] = set()
    while current > 1 and current not in seen:
        if current == pid:
            return True
        seen.add(current)
        current = _proc_parent(current)
    return False


def _canonical_wrapper_argument(argument: str, pid: int) -> bool:
    try:
        cwd = Path(os.readlink(f"/proc/{pid}/cwd"))
        return (cwd / argument).resolve() == _WRAPPER_SOURCE
    except OSError:
        return False


def _wrapper_binding_valid() -> bool:
    prefix = _EXPECTED_ENV_PREFIX
    token = os.environ.get(prefix + "TOKEN", "")
    attestation = os.environ.get(prefix + "ATTESTATION_FILE", "")
    pid_text = os.environ.get(prefix + "WRAPPER_PID", "")
    starttime = os.environ.get(prefix + "WRAPPER_STARTTIME", "")
    wrapper_sha = os.environ.get(prefix + "WRAPPER_SHA256", "")
    try:
        pid = int(pid_text)
        state = Path(attestation).stat(follow_symlinks=False)
        content = Path(attestation).read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return False
    command = _proc_cmdline(pid)
    return (
        os.environ.get(prefix + "ENTRYPOINT") == "v1"
        and re.fullmatch(r"[0-9a-f]{64}", token) is not None
        and pid > 1
        and _is_ancestor(pid)
        and _proc_starttime(pid) == starttime
        and stat.S_ISREG(state.st_mode)
        and not stat.S_ISLNK(state.st_mode)
        and stat.S_IMODE(state.st_mode) == 0o600
        and state.st_uid == os.getuid()
        and state.st_gid == os.getgid()
        and state.st_nlink == 1
        and command[:1] == ["/bin/dash"]
        and len(command) == 3
        and _canonical_wrapper_argument(command[1], pid)
        and command[2] == "check"
        and content == f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\n"
        and os.environ.get(prefix + "WRAPPER_PATH") == str(_WRAPPER_SOURCE)
        and wrapper_sha == _sha256(_WRAPPER_SOURCE)
        and os.environ.get(prefix + "ANSIBLE_CONFIG_PATH") == str(_ANSIBLE_CONFIG_SOURCE)
        and os.environ.get(prefix + "INVENTORY_PATH") == str(_INVENTORY_SOURCE)
        and os.environ.get(prefix + "CONTROLLER_PATH") == str(_CONTROLLER_SOURCE)
        and os.environ.get(prefix + "TOOLCHAIN_PATH") == str(_COLLECTION_MANIFEST_SOURCE)
        and os.environ.get(prefix + "STRATEGY_PATH") == str(_STRATEGY_SOURCE)
        and os.environ.get(prefix + "STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG_SOURCE)
        and not any(os.environ.get(name) for name in _FORBIDDEN_ENV)
    )


def _canonical_argv() -> bool:
    expected = [
        "-i",
        str(_INVENTORY_SOURCE),
        str(_PLAYBOOK_SOURCE),
        "--check",
        "--diff",
        "--limit",
        "crtxweb",
        "--connection",
        "local",
        "--extra-vars",
        '{"cristexhub_prod_ghcr_pull_rotation_preflight_approved":true}',
    ]
    return sys.argv[1:] == expected


def _selection_is_canonical() -> bool:
    tags = list(context.CLIARGS.get("tags") or [])
    skip_tags = list(context.CLIARGS.get("skip_tags") or [])
    inventory = context.CLIARGS.get("inventory") or []
    inventory = [inventory] if isinstance(inventory, str) else list(inventory)
    selection_argv = any(
        argument == "-t"
        or (argument.startswith("-t") and len(argument) > 2)
        or argument in {"--tags", "--skip-tags", "--start-at-task", "--step"}
        or argument.startswith(("--tags=", "--skip-tags=", "--start-at-task=", "--step="))
        for argument in sys.argv[1:]
    )
    return (
        not selection_argv
        and context.CLIARGS.get("start_at_task") is None
        and not context.CLIARGS.get("step")
        and tags in ([], ["all"])
        and not skip_tags
        and context.CLIARGS.get("subset") == "crtxweb"
        and context.CLIARGS.get("check") is True
        and context.CLIARGS.get("diff") is True
        and inventory == [str(_INVENTORY_SOURCE)]
    )


class StrategyModule(LinearStrategyModule):
    """Run provenance checks before Ansible can iterate or skip role tasks."""

    def run(self, iterator, play_context):  # type: ignore[no-untyped-def]
        if not _canonical_argv() or not _selection_is_canonical() or not _source_contract() or not _wrapper_binding_valid():
            raise AnsibleError(
                "TASK_SELECTION_GUARD: GHCR rotation requires the complete canonical wrapper provenance"
            )
        os.environ[_EXPECTED_ENV_PREFIX + "STRATEGY_ATTESTED"] = "v1"
        return super().run(iterator, play_context)
