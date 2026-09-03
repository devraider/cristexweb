from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath

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
_VENV_PYTHON_SOURCE = _REPOSITORY_ROOT / ".venv/bin/python"
_VENV_PYTHON_TARGET = Path("/usr/bin/python3.13")
_REQUIREMENTS_SOURCE = _REPOSITORY_ROOT / "ansible/requirements.yml"
_COLLECTION_ROOT = _REPOSITORY_ROOT / "ansible/.ansible/collections/ansible_collections/kubernetes/core"
_COLLECTION_MANIFEST_SOURCE = _COLLECTION_ROOT / "MANIFEST.json"
_COLLECTION_FILES_SOURCE = _COLLECTION_ROOT / "FILES.json"
_STRATEGY_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/strategy/cristexhub_prod_private_acceptance_guarded_linear.py"

# This pin is canonicalized by zeroing it before hashing. The wrapper and action
# hold independent raw and canonical pins, so this strategy cannot self-authorize
# a modified source before task iteration.
_STRATEGY_CANONICAL_SHA256 = "2f551dbe46871cd8db35e4105b6745d04ac5ae7193ee142f848a4e4ecfae7325"
_WRAPPER_CANONICAL_SHA256 = "50c41be6a5a0d78ce0ee8b040fa96c1c8add60f023b1d1af36e3d3da23f72eea"
_EXPECTED_PYTHON_SHA256 = "17b78e0a93175e86f9ac03141924fd7a7f0c0c52e66b34bfa0de20ffef989df1"
_EXPECTED_REQUIREMENTS_SHA256 = "f82d9e5ba1b64324710eb66c956d0447c46d3958722f635a4502bcb6c3efc75f"
_EXPECTED_COLLECTION_MANIFEST_SHA256 = "dc32e90ca987d6199e9091f749ecb40fd3380b40aabb7c18961ec75582cfc6df"
_EXPECTED_COLLECTION_FILES_SHA256 = "9d30dde4e4d6d04ec2e9b00a2d787114f13577fd2c456d25726865e3db39fa69"
_EXPECTED_COLLECTION_ACTION_SYMLINKS = {
    "helm.py", "helm_info.py", "helm_plugin.py", "helm_plugin_info.py",
    "helm_repository.py", "k8s.py", "k8s_cluster_info.py", "k8s_cp.py",
    "k8s_drain.py", "k8s_exec.py", "k8s_json_patch.py", "k8s_log.py",
    "k8s_rollback.py", "k8s_scale.py", "k8s_service.py",
}
_EXPECTED_COLLECTION_ACTION_TARGET = "k8s_info.py"
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


_WRAPPER_CANONICAL_FIELDS = (
    "wrapper_canonical_sha256_expected", "task_sha256_expected",
    "defaults_sha256_expected", "playbook_sha256_expected",
    "action_sha256_expected", "strategy_sha256_expected",
    "strategy_canonical_sha256_expected", "inventory_sha256_expected",
    "ansible_config_sha256_expected", "controller_sha256_expected",
    "python_sha256_expected", "venv_python_sha256_expected",
)


def _wrapper_canonical_hash(path: Path) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        pattern = r"(?m)^(" + "|".join(_WRAPPER_CANONICAL_FIELDS) + r")='[0-9a-f]{64}'$"
        source, count = re.subn(pattern, r"\g<1>='" + ("0" * 64) + "'", source)
        return hashlib.sha256(source.encode("utf-8")).hexdigest() if count == len(_WRAPPER_CANONICAL_FIELDS) else ""
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


def _venv_python_contract() -> bool:
    try:
        link = _VENV_PYTHON_SOURCE.lstat()
        target = _VENV_PYTHON_TARGET.lstat()
        return (
            stat.S_ISLNK(link.st_mode)
            and link.st_uid == os.getuid()
            and link.st_gid == os.getgid()
            and stat.S_IMODE(link.st_mode) == 0o777
            and os.readlink(_VENV_PYTHON_SOURCE) == "/usr/bin/python3"
            and _VENV_PYTHON_SOURCE.resolve() == _VENV_PYTHON_TARGET
            and stat.S_ISREG(target.st_mode)
            and target.st_uid == 0
            and target.st_gid == 0
            and stat.S_IMODE(target.st_mode) == 0o755
            and _sha256(_VENV_PYTHON_TARGET) == _EXPECTED_PYTHON_SHA256
            and os.environ.get(
                "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_VENV_PYTHON_TARGET", ""
            ) == str(_VENV_PYTHON_TARGET)
            and os.environ.get(
                "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_VENV_PYTHON_SHA256", ""
            ) == _EXPECTED_PYTHON_SHA256
        )
    except (OSError, RuntimeError):
        return False


def _collection_tree_contract() -> bool:
    """Validate requirements and every installed kubernetes.core tree leaf pre-query."""
    try:
        if not _regular_file(_REQUIREMENTS_SOURCE, 0o644):
            return False
        if _sha256(_REQUIREMENTS_SOURCE) != _EXPECTED_REQUIREMENTS_SHA256:
            return False
        for path, digest in (
            (_COLLECTION_MANIFEST_SOURCE, _EXPECTED_COLLECTION_MANIFEST_SHA256),
            (_COLLECTION_FILES_SOURCE, _EXPECTED_COLLECTION_FILES_SHA256),
        ):
            if not _regular_file(path, 0o644) or _sha256(path) != digest:
                return False
        payload = json.loads(_COLLECTION_FILES_SOURCE.read_text(encoding="utf-8"))
        entries = payload.get("files")
        if not isinstance(entries, list):
            return False
        listed: dict[str, tuple[str, str | None]] = {}
        for item in entries:
            if not isinstance(item, dict):
                return False
            name = item.get("name")
            kind = item.get("ftype")
            if name == ".":
                if kind != "dir":
                    return False
                continue
            if not isinstance(name, str) or not name:
                return False
            relative = PurePosixPath(name)
            if (
                relative.is_absolute()
                or relative.as_posix() != name
                or any(part in {"", ".", ".."} for part in relative.parts)
                or kind not in {"file", "dir"}
                or name in listed
                or item.get("format") != 1
            ):
                return False
            digest = item.get("chksum_sha256")
            if kind == "file":
                if item.get("chksum_type") != "sha256" or not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                    return False
            elif digest not in (None, "") or item.get("chksum_type") not in (None, ""):
                return False
            listed[name] = (kind, digest if kind == "file" else None)
        listed["FILES.json"] = ("file", _EXPECTED_COLLECTION_FILES_SHA256)
        listed["MANIFEST.json"] = ("file", _EXPECTED_COLLECTION_MANIFEST_SHA256)
        actual: dict[str, str] = {}
        for entry in _COLLECTION_ROOT.rglob("*"):
            name = entry.relative_to(_COLLECTION_ROOT).as_posix()
            if entry.is_symlink() or entry.is_file():
                actual[name] = "file"
            elif entry.is_dir():
                actual[name] = "dir"
            else:
                return False
        if actual != {name: kind for name, (kind, _) in listed.items()}:
            return False
        for name, (kind, digest) in listed.items():
            path = _COLLECTION_ROOT / name
            state = path.lstat()
            if state.st_uid != os.getuid() or state.st_gid != os.getgid():
                return False
            if kind == "dir":
                if not stat.S_ISDIR(state.st_mode) or stat.S_IMODE(state.st_mode) != 0o755:
                    return False
                continue
            if path.is_symlink():
                if not name.startswith("plugins/action/") or name.removeprefix("plugins/action/") not in _EXPECTED_COLLECTION_ACTION_SYMLINKS:
                    return False
                if (
                    os.readlink(path) != _EXPECTED_COLLECTION_ACTION_TARGET
                    or path.resolve() != _COLLECTION_ROOT / "plugins/action/k8s_info.py"
                    or stat.S_IMODE(state.st_mode) != 0o777
                ):
                    return False
            elif not stat.S_ISREG(state.st_mode) or stat.S_IMODE(state.st_mode) not in {0o644, 0o755}:
                return False
            if digest is None or _sha256(path) != digest:
                return False
        info = json.loads(_COLLECTION_MANIFEST_SOURCE.read_text(encoding="utf-8")).get("collection_info", {})
        return info.get("namespace") == "kubernetes" and info.get("name") == "core" and info.get("version") == "6.1.0"
    except (OSError, RuntimeError, UnicodeError, ValueError, TypeError):
        return False


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
        "PYTHON_SHA256": _sha256(Path("/usr/bin/python3.13")),
        "VENV_PYTHON_SHA256": _sha256(_VENV_PYTHON_TARGET),
    }
    prefix = "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_"
    if any(os.environ.get(prefix + key, "") != value for key, value in supplied.items()):
        return False
    if (
        _canonical_file_hash(_STRATEGY_SOURCE, "_STRATEGY_CANONICAL_SHA256")
        != _STRATEGY_CANONICAL_SHA256
        or _wrapper_canonical_hash(_WRAPPER_SOURCE) != _WRAPPER_CANONICAL_SHA256
        or os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256") != _WRAPPER_CANONICAL_SHA256
        or os.environ.get(prefix + "STRATEGY_CANONICAL_SHA256") != _STRATEGY_CANONICAL_SHA256
    ):
        return False
    return (
        _inventory_contract()
        and _venv_python_contract()
        and _collection_tree_contract()
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG_SOURCE)
        and _regular_file(_CONTROLLER_SOURCE, 0o755)
        and _sha256(_CONTROLLER_SOURCE) == _CONTROLLER_SHA256
        and _CONTROLLER_SOURCE.read_text(encoding="utf-8").splitlines()[0] == "#!" + str(_VENV_PYTHON_SOURCE)
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
