from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shlex
import stat
import sys
from pathlib import Path
from typing import Any

from ansible import context
from ansible.plugins.action import ActionBase

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/rabbitmq_prod_credential_rotation_check/defaults/main.yml"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml"
_POLICY_SOURCE = _REPOSITORY_ROOT / "ansible/files/policies/cristexhub-prod-rabbitmq-credential-rotation.yml"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation"
_ACTION_SOURCE = Path(__file__).resolve()
_STRATEGY_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py"
_INVENTORY_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/inventory.local.yml"
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_PYTHON_SOURCE = _REPOSITORY_ROOT / ".venv/bin/python"
_PYTHON_REAL_SOURCE = Path("/usr/bin/python3.13")
_EXPECTED_PYTHON_SHA256 = "17b78e0a93175e86f9ac03141924fd7a7f0c0c52e66b34bfa0de20ffef989df1"
_REQUIREMENTS_SOURCE = _REPOSITORY_ROOT / "ansible/requirements.yml"
_COLLECTION_ROOT = _REPOSITORY_ROOT / "ansible/.ansible/collections/ansible_collections/kubernetes/core"
_COLLECTION_MANIFEST_SOURCE = _COLLECTION_ROOT / "MANIFEST.json"
_COLLECTION_FILES_SOURCE = _COLLECTION_ROOT / "FILES.json"
_OPERATOR = "paul"
_METADATA_SOURCE = _REPOSITORY_ROOT / "ansible/library/rabbitmq_prod_credential_metadata.py"
_BROKER_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/rabbitmq/runtime/statefulset-rabbitmq.yaml"
_RABBITMQ_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/rabbitmq/runtime/configmap-rabbitmq.yaml"
_ENGINE_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-rabbitmq-secrets/source/rabbitmq-infisical-secrets.yaml"
_RUNTIME_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-cristexhub-prod-runtime/source/cristexhub-prod-runtime-static-secret.yaml"
_CLOSURE_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/rabbitmq-prod-credential-rotation/SOURCE-CLOSURE.sha256"
# Integrity DAG anchors.  The closure and its executable anchors are committed
# consistency checks for the canonical source tree, not independent provenance.
# They reject isolated drift; a coordinated rewrite by the already-trusted
# controller UID remains outside the documented integrity boundary.  Only the
# plugin's own pin and the closure digest are normalized by
# _canonical_action_hash().
_ROLES_PATH = _REPOSITORY_ROOT / "ansible/roles"
_LIBRARY_PATH = _REPOSITORY_ROOT / "ansible/library"
_ACTION_CANONICAL_SHA256 = "e61361012b302cd6633d8626e6d4d189b42208aa77b852a60d2b5e1559369a1e"
_TASK_SHA256 = "f9c9dc6c6e055153bec878fb48974faa24e38ca7b1106dca6f4571b628cda619"
_DEFAULTS_SHA256 = "3e5d9d043eccd416d0696da9dd4441f1ec78cac092dd1f1752d4b69725c121ac"
_PLAYBOOK_SHA256 = "afba74ac3b512de525f322dcf7e89e3faed012f277c79912f439ddb9b2cf9b60"
_POLICY_SHA256 = "b4cd58058ccbbd236b44511b63637bda5fb61a6ca2df56f4f78e24f2da8a409f"
_METADATA_SHA256 = "586841d6c3f677e5bd7d68c5968f92f3abe508ddb026227c312db14582bdd6be"
_BROKER_SOURCE_SHA256 = "5ea7cfa66e72615e5ff50657e934740907a90d4219c221323e3b91af3efe6242"
_RABBITMQ_CONFIG_SOURCE_SHA256 = "663c006190e6e5e03e7c22d198cb41245d2ab3b7dab406acb4fdefe00a10a2d5"
_ENGINE_SOURCE_SHA256 = "b5eeaa0abc5b9ee91d392d6ac064862026b64f0d4c74f6431fe5dca517c506d0"
_RUNTIME_SOURCE_SHA256 = "3204aab3fc0f5b55f9af3623fb658d5ffd8289437d5d0ea91ab0480dc4126ee0"
_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_INVENTORY_SHA256 = "652a8455f8a050005ab783d20d4e60a0cd034d8a6439f1cffe551a91102773b0"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_REQUIREMENTS_SHA256 = "f82d9e5ba1b64324710eb66c956d0447c46d3958722f635a4502bcb6c3efc75f"
_COLLECTION_MANIFEST_SHA256 = "dc32e90ca987d6199e9091f749ecb40fd3380b40aabb7c18961ec75582cfc6df"
_COLLECTION_FILES_SHA256 = "9d30dde4e4d6d04ec2e9b00a2d787114f13577fd2c456d25726865e3db39fa69"
_CLOSURE_MANIFEST_SHA256 = "210e49f8ba6a74072517d7f00e6b21e5f37d6d0345da405b380386741aa8adbf"
_RUNTIME_PROVENANCE = (
    ("CONTROLLER_SHA256", _CONTROLLER_SOURCE, _CONTROLLER_SHA256),
    ("PYTHON_SHA256", _PYTHON_REAL_SOURCE, _EXPECTED_PYTHON_SHA256),
    ("ANSIBLE_CONFIG_SHA256", _ANSIBLE_CONFIG_SOURCE, _CONFIG_SHA256),
    ("INVENTORY_SHA256", _INVENTORY_SOURCE, _INVENTORY_SHA256),
    ("REQUIREMENTS_SHA256", _REQUIREMENTS_SOURCE, _REQUIREMENTS_SHA256),
    ("COLLECTION_MANIFEST_SHA256", _COLLECTION_MANIFEST_SOURCE, _COLLECTION_MANIFEST_SHA256),
    ("COLLECTION_FILES_SHA256", _COLLECTION_FILES_SOURCE, _COLLECTION_FILES_SHA256),
)
_ARGUMENT_KEYS = {"namespace", "pod", "container", "command", "kubeconfig", "query"}
_EXPECTED_QUERIES = {
    "readiness": ["rabbitmq-diagnostics", "-q", "check_running"],
    "users": ["rabbitmqctl", "list_users", "--formatter=json"],
    "prod_permissions": [
        "rabbitmqctl",
        "list_permissions",
        "--formatter=json",
        "--vhost",
        "/cristexhub-prod",
    ],
    "all_permissions": ["rabbitmqctl", "list_permissions", "--formatter=json"],
    "vhosts": ["rabbitmqctl", "list_vhosts", "--formatter=json"],
}
_SECRET_KEYS = {"password", "password_hash", "passwordHash", "secret", "token", "clientSecret"}
_EXPECTED_PERMISSIONS = {
    "configure": "^(default|high_priority|low_priority)$",
    "write": "^default$",
    "read": "^(default|high_priority|low_priority)$",
}


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _runtime_provenance_valid() -> bool:
    """Require every wrapper-exported runtime digest to match its source file.

    The strategy validates the same values before scheduling the role, but the
    action must repeat this check because an alternate action-loader path can
    reach this plugin without executing the strategy guard first.
    """
    prefix = "CRISTEXWEB_RABBITMQ_PROD_ROTATION_"
    try:
        for suffix, path, expected in _RUNTIME_PROVENANCE:
            state = path.stat(follow_symlinks=False)
            if not stat.S_ISREG(state.st_mode) or path.is_symlink():
                return False
            actual = _sha256(path)
            if actual != expected or os.environ.get(prefix + suffix) != actual:
                return False
        return True
    except (OSError, RuntimeError, TypeError):
        return False


def _collection_toolchain_valid() -> bool:
    strategy_path = _REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py"
    try:
        spec = importlib.util.spec_from_file_location("_rabbitmq_rotation_strategy_closure", strategy_path)
        if spec is None or spec.loader is None:
            return False
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return bool(module._collection_toolchain_valid())
    except (ImportError, OSError, RuntimeError, AttributeError, TypeError):
        return False


def _canonical_action_hash(path: Path) -> str:
    """Hash an action source while normalizing only its two self-referential pins."""
    try:
        source = path.read_text(encoding="utf-8")
        source, action_count = re.subn(
            r'(?m)^_ACTION_CANONICAL_SHA256 = "[0-9a-f]{64}"$',
            '_ACTION_CANONICAL_SHA256 = "' + ("0" * 64) + '"',
            source,
        )
        source, closure_count = re.subn(
            r'(?m)^_CLOSURE_MANIFEST_SHA256 = "[0-9a-f]{64}"$',
            '_CLOSURE_MANIFEST_SHA256 = "' + ("0" * 64) + '"',
            source,
        )
        return hashlib.sha256(source.encode()).hexdigest() if action_count == closure_count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _canonical_strategy_hash(path: Path) -> str:
    """Hash the strategy source while normalizing only its self and closure pins."""
    try:
        source = path.read_text(encoding="utf-8")
        source, strategy_count = re.subn(
            r'(?m)^_STRATEGY_CANONICAL_SHA256 = "[0-9a-f]{64}"$',
            '_STRATEGY_CANONICAL_SHA256 = "' + ("0" * 64) + '"',
            source,
        )
        source, closure_count = re.subn(
            r'(?m)^_CLOSURE_MANIFEST_SHA256 = "[0-9a-f]{64}"$',
            '_CLOSURE_MANIFEST_SHA256 = "' + ("0" * 64) + '"',
            source,
        )
        return hashlib.sha256(source.encode()).hexdigest() if strategy_count == closure_count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _canonical_wrapper_hash(path: Path) -> str:
    """Hash the wrapper while normalizing only its self and closure pins."""
    try:
        source = path.read_text(encoding="utf-8")
        source, wrapper_count = re.subn(
            r"(?m)^wrapper_canonical_sha256='[0-9a-f]{64}'$",
            "wrapper_canonical_sha256='" + ("0" * 64) + "'",
            source,
        )
        source, closure_count = re.subn(
            r"(?m)^source_closure_sha256_expected='[0-9a-f]{64}'$",
            "source_closure_sha256_expected='" + ("0" * 64) + "'",
            source,
        )
        return hashlib.sha256(source.encode()).hexdigest() if wrapper_count == closure_count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _full_action_hash(path: Path) -> str:
    """Hash the complete action while normalizing only the closure digest."""
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            r'(?m)^_CLOSURE_MANIFEST_SHA256 = "[0-9a-f]{64}"$',
            '_CLOSURE_MANIFEST_SHA256 = "' + ("0" * 64) + '"',
            source,
        )
        return hashlib.sha256(source.encode()).hexdigest() if count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _full_strategy_hash(path: Path) -> str:
    """Hash the complete strategy while normalizing only the closure digest."""
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            r'(?m)^_CLOSURE_MANIFEST_SHA256 = "[0-9a-f]{64}"$',
            '_CLOSURE_MANIFEST_SHA256 = "' + ("0" * 64) + '"',
            source,
        )
        return hashlib.sha256(source.encode()).hexdigest() if count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _full_wrapper_hash(path: Path) -> str:
    """Hash the complete wrapper while normalizing only the closure digest."""
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            r"(?m)^source_closure_sha256_expected='[0-9a-f]{64}'$",
            "source_closure_sha256_expected='" + ("0" * 64) + "'",
            source,
        )
        return hashlib.sha256(source.encode()).hexdigest() if count == 1 else ""
    except (OSError, UnicodeError):
        return ""


_CLOSURE_ENTRIES = (
    ("canonical", "ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation", _WRAPPER_SOURCE, 0o755),
    ("canonical", "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py", Path(__file__), 0o644),
    ("canonical", "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py", _REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py", 0o644),
    ("full", "ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation", _WRAPPER_SOURCE, 0o755),
    ("full", "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py", Path(__file__), 0o644),
    ("full", "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py", _REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py", 0o644),
    ("sha256", "ansible/ansible.cfg", _ANSIBLE_CONFIG_SOURCE, 0o644),
    ("sha256", "ansible/roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml", _TASK_SOURCE, 0o644),
    ("sha256", "ansible/roles/rabbitmq_prod_credential_rotation_check/defaults/main.yml", _DEFAULTS_SOURCE, 0o644),
    ("sha256", "ansible/playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml", _PLAYBOOK_SOURCE, 0o644),
    ("sha256", "ansible/files/policies/cristexhub-prod-rabbitmq-credential-rotation.yml", _POLICY_SOURCE, 0o644),
    ("sha256", "ansible/library/rabbitmq_prod_credential_metadata.py", _METADATA_SOURCE, 0o755),
    ("sha256", "ansible/files/components/rabbitmq/runtime/statefulset-rabbitmq.yaml", _BROKER_SOURCE, 0o644),
    ("sha256", "ansible/files/components/rabbitmq/runtime/configmap-rabbitmq.yaml", _RABBITMQ_CONFIG_SOURCE, 0o644),
    ("sha256", "ansible/files/components/infisical-rabbitmq-secrets/source/rabbitmq-infisical-secrets.yaml", _ENGINE_SOURCE, 0o644),
    ("sha256", "ansible/files/components/infisical-cristexhub-prod-runtime/source/cristexhub-prod-runtime-static-secret.yaml", _RUNTIME_SOURCE, 0o644),
)


def _closure_lines() -> list[str]:
    lines: list[str] = []
    for kind, relative, path, _mode in _CLOSURE_ENTRIES:
        digest = (
            _canonical_wrapper_hash(path)
            if kind == "canonical" and path == _WRAPPER_SOURCE
            else _canonical_action_hash(path)
            if kind == "canonical" and path == Path(__file__)
            else _canonical_strategy_hash(path)
            if kind == "canonical"
            else _full_wrapper_hash(path)
            if kind == "full" and path == _WRAPPER_SOURCE
            else _full_action_hash(path)
            if kind == "full" and path == Path(__file__)
            else _full_strategy_hash(path)
            if kind == "full"
            else _sha256(path)
        )
        lines.append(f"{kind} {digest}  {relative}")
    return lines


def _closure_anchor(kind: str, relative: str) -> str:
    """Read one committed consistency anchor from the source closure."""
    try:
        lines = _CLOSURE_SOURCE.read_text(encoding="utf-8").splitlines()
        matches = [line.split()[1] for line in lines if len(line.split()) == 3 and line.split()[0] == kind and line.split()[2] == relative]
        return matches[0] if len(matches) == 1 and re.fullmatch(r"[0-9a-f]{64}", matches[0]) else ""
    except (OSError, UnicodeError):
        return ""


def _wrapper_canonical_expected() -> str:
    return _closure_anchor(
        "canonical", "ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation"
    )


def _action_canonical_expected() -> str:
    return _closure_anchor(
        "canonical", "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py"
    )


def _strategy_canonical_expected() -> str:
    return _closure_anchor(
        "canonical", "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py"
    )


def _action_full_expected() -> str:
    return _closure_anchor(
        "full", "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py"
    )


def _strategy_full_expected() -> str:
    return _closure_anchor(
        "full", "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py"
    )


def _source_closure_valid() -> bool:
    """Require the committed source closure before any alternate action startup."""
    try:
        state = _CLOSURE_SOURCE.stat(follow_symlinks=False)
        if (
            not stat.S_ISREG(state.st_mode)
            or _CLOSURE_SOURCE.is_symlink()
            or stat.S_IMODE(state.st_mode) != 0o644
            or state.st_uid != os.getuid()
            or _sha256(_CLOSURE_SOURCE) != _CLOSURE_MANIFEST_SHA256
        ):
            return False
        if _CLOSURE_SOURCE.read_text(encoding="utf-8").splitlines() != _closure_lines():
            return False
        for kind, relative, path, mode in _CLOSURE_ENTRIES:
            leaf = path.stat(follow_symlinks=False)
            if (
                not stat.S_ISREG(leaf.st_mode)
                or path.is_symlink()
                or stat.S_IMODE(leaf.st_mode) != mode
                or leaf.st_uid != os.getuid()
                or leaf.st_gid != os.getgid()
            ):
                return False
            actual = (
                _canonical_wrapper_hash(path)
                if kind == "canonical" and path == _WRAPPER_SOURCE
                else _canonical_action_hash(path)
                if kind == "canonical" and path == Path(__file__)
                else _canonical_strategy_hash(path)
                if kind == "canonical"
                else _full_wrapper_hash(path)
                if kind == "full" and path == _WRAPPER_SOURCE
                else _full_action_hash(path)
                if kind == "full" and path == Path(__file__)
                else _full_strategy_hash(path)
                if kind == "full"
                else _sha256(path)
            )
            expected = next(
                line.split()[1]
                for line in _CLOSURE_SOURCE.read_text(encoding="utf-8").splitlines()
                if len(line.split()) == 3 and line.split()[0] == kind and line.split()[2] == relative
            )
            if not actual or actual != expected:
                return False
        return (
            _canonical_action_hash(Path(__file__)) == _ACTION_CANONICAL_SHA256
            and _ACTION_CANONICAL_SHA256 == _action_canonical_expected()
            and _canonical_strategy_hash(_REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py") == _strategy_canonical_expected()
            and _canonical_wrapper_hash(_WRAPPER_SOURCE) == _wrapper_canonical_expected()
            and _full_action_hash(_ACTION_SOURCE) == _action_full_expected()
            and _full_strategy_hash(_REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py") == _strategy_full_expected()
        )
    except (OSError, UnicodeError, RuntimeError):
        return False


def _ancestor(pid: int) -> bool:
    current = os.getpid()
    seen: set[int] = set()
    while current > 1 and current not in seen:
        if current == pid:
            return True
        seen.add(current)
        try:
            status = Path(f"/proc/{current}/status").read_text(encoding="utf-8")
            current = int(next(line for line in status.splitlines() if line.startswith("PPid:")).split()[1])
        except (OSError, StopIteration, ValueError):
            return False
    return False


def _proc_starttime(pid: int) -> str:
    try:
        tail = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").rsplit(") ", 1)[1].split()
        return tail[19]
    except (OSError, UnicodeError, IndexError):
        return ""


def _proc_executable(pid: int) -> Path | None:
    try:
        return Path(os.readlink(f"/proc/{pid}/exe")).resolve(strict=True)
    except (OSError, RuntimeError):
        return None


def _canonical_shell(pid: int, command: list[str]) -> bool:
    if not command or command[0] not in {"/bin/sh", "/bin/dash"}:
        return False
    try:
        dash = Path("/usr/bin/dash").resolve(strict=True)
        return Path(command[0]).resolve(strict=True) == dash and _proc_executable(pid) == dash
    except (OSError, RuntimeError):
        return False


def _proc_cmdline(pid: int) -> list[str]:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        if not raw.endswith(b"\0"):
            return []
        return [part.decode("utf-8", "strict") for part in raw[:-1].split(b"\0")]
    except (OSError, UnicodeError):
        return []


def _canonical_wrapper_argument(argument: str, pid: int) -> bool:
    try:
        requested = Path(argument)
        if requested.is_absolute():
            return requested.resolve(strict=True) == _WRAPPER_SOURCE
        cwd = Path(os.readlink(f"/proc/{pid}/cwd"))
        # The wrapper changes cwd to ansible before launching Ansible.  Evaluate
        # each relative-path base independently so a nonexistent cwd candidate
        # cannot prevent the repository-root candidate from being checked.
        for base in (cwd, _REPOSITORY_ROOT):
            try:
                if (base / requested).resolve(strict=True) == _WRAPPER_SOURCE:
                    return True
            except (OSError, RuntimeError):
                continue
        return False
    except (OSError, RuntimeError):
        return False


def _expected_argv() -> list[str]:
    return [
        str(_CONTROLLER_SOURCE),
        "-i",
        ".ansible/inventory.local.yml",
        "playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml",
        "--check",
        "--diff",
        "--limit",
        "crtxweb",
        "--extra-vars",
        '{"rabbitmq_prod_credential_rotation_check_approved":true}',
    ]


def _toolchain_valid() -> bool:
    try:
        inventory_state = _INVENTORY_SOURCE.stat(follow_symlinks=False)
        config_state = _ANSIBLE_CONFIG_SOURCE.stat(follow_symlinks=False)
        controller_state = _CONTROLLER_SOURCE.stat(follow_symlinks=False)
        python_link = _PYTHON_SOURCE.stat(follow_symlinks=False)
        python_target = _PYTHON_SOURCE.resolve(strict=True).stat(follow_symlinks=False)
        return (
            stat.S_ISREG(inventory_state.st_mode)
            and not _INVENTORY_SOURCE.is_symlink()
            and stat.S_IMODE(inventory_state.st_mode) == 0o600
            and inventory_state.st_uid == os.getuid()
            and _sha256(_INVENTORY_SOURCE) == _INVENTORY_SHA256
            and stat.S_ISREG(config_state.st_mode)
            and not _ANSIBLE_CONFIG_SOURCE.is_symlink()
            and stat.S_IMODE(config_state.st_mode) == 0o644
            and config_state.st_uid == os.getuid()
            and _sha256(_ANSIBLE_CONFIG_SOURCE) == _CONFIG_SHA256
            and stat.S_ISREG(controller_state.st_mode)
            and not _CONTROLLER_SOURCE.is_symlink()
            and stat.S_IMODE(controller_state.st_mode) == 0o755
            and controller_state.st_uid == os.getuid()
            and _sha256(_CONTROLLER_SOURCE) == _CONTROLLER_SHA256
            and stat.S_ISLNK(python_link.st_mode)
            and python_link.st_uid == os.getuid()
            and python_link.st_gid == os.getgid()
            and os.readlink(_PYTHON_SOURCE) == "/usr/bin/python3"
            and _PYTHON_SOURCE.resolve(strict=True) == _PYTHON_REAL_SOURCE
            and stat.S_ISREG(python_target.st_mode)
            and python_target.st_uid == 0
            and stat.S_IMODE(python_target.st_mode) == 0o755
            and _sha256(_PYTHON_REAL_SOURCE) == _EXPECTED_PYTHON_SHA256
            and os.getuid() == controller_state.st_uid
            and os.environ.get("HOME") == "/home/paul"
            and os.environ.get("USER") == _OPERATOR
            and os.environ.get("LOGNAME") == _OPERATOR
            and _collection_toolchain_valid()
        )
    except OSError:
        return False


def _selection_guard_reasons() -> tuple[str, ...]:
    """Return stable selection reason codes without exposing runtime values."""
    reasons: list[str] = []

    def check(code: str, predicate: Any) -> None:
        try:
            if not bool(predicate()):
                reasons.append(code)
        except Exception:
            reasons.append(code)

    try:
        inventory = context.CLIARGS.get("inventory") or []
        if isinstance(inventory, str):
            inventory = [inventory]
        elif isinstance(inventory, tuple):
            inventory = list(inventory)
    except Exception:
        return ("cliargs-shape",)
    check("argv", lambda: sys.argv == _expected_argv())
    check(
        "entrypoint",
        lambda: os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ENTRYPOINT") == "v1",
    )
    check(
        "mode",
        lambda: os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_MODE") == "check",
    )
    check(
        "closure-path",
        lambda: os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_SOURCE_CLOSURE_PATH")
        == str(_CLOSURE_SOURCE),
    )
    check(
        "closure-digest",
        lambda: os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_SOURCE_CLOSURE_SHA256")
        == _CLOSURE_MANIFEST_SHA256,
    )
    check("toolchain", _toolchain_valid)
    check("runtime-provenance", _runtime_provenance_valid)
    check("source-closure", _source_closure_valid)
    check(
        "action-canonical",
        lambda: _canonical_action_hash(Path(__file__))
        == _ACTION_CANONICAL_SHA256
        == _action_canonical_expected(),
    )
    check(
        "strategy-canonical",
        lambda: _canonical_strategy_hash(
            _REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py"
        )
        == _strategy_canonical_expected(),
    )
    check("wrapper-canonical", lambda: _canonical_wrapper_hash(_WRAPPER_SOURCE) == _wrapper_canonical_expected())
    check("action-full", lambda: _full_action_hash(_ACTION_SOURCE) == _action_full_expected())
    check(
        "strategy-full",
        lambda: _full_strategy_hash(
            _REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py"
        )
        == _strategy_full_expected(),
    )
    check("check-mode", lambda: context.CLIARGS.get("check") is True)
    check("diff-mode", lambda: context.CLIARGS.get("diff") is True)
    check("subset", lambda: context.CLIARGS.get("subset") == "crtxweb")
    check("start-at-task", lambda: context.CLIARGS.get("start_at_task") is None)
    check("step", lambda: context.CLIARGS.get("step") in (None, False))
    check("skip-tags", lambda: not context.CLIARGS.get("skip_tags"))
    check("tags", lambda: list(context.CLIARGS.get("tags") or []) in ([], ["all"]))
    check("inventory", lambda: inventory == [str(_INVENTORY_SOURCE)])
    check("ansible-config", lambda: os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG_SOURCE))
    check("ansible-library", lambda: os.environ.get("ANSIBLE_LIBRARY") == str(_LIBRARY_PATH))
    check("ansible-roles", lambda: os.environ.get("ANSIBLE_ROLES_PATH") == str(_ROLES_PATH))
    check(
        "inherited-selection",
        lambda: not any(
            os.environ.get(name)
            for name in (
                "ANSIBLE_ACTION_PLUGINS",
                "ANSIBLE_COLLECTIONS_PATH",
                "ANSIBLE_START_AT_TASK",
                "ANSIBLE_SKIP_TAGS",
                "ANSIBLE_TAGS",
                "ANSIBLE_STEP",
            )
        ),
    )
    return tuple(dict.fromkeys(reasons))


def _selected() -> bool:
    """Return whether the wrapper argv and CRISTEXWEB_RABBITMQ_PROD_ROTATION_MODE are canonical."""
    return not _selection_guard_reasons()


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key) in _SECRET_KEYS or _contains_secret_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_secret_key(child) for child in value)
    return False


def _json_rows(stdout: str, field: str) -> list[dict[str, Any]] | None:
    try:
        payload = json.loads(stdout)
    except (TypeError, ValueError):
        return None
    if _contains_secret_key(payload):
        return None
    rows = payload.get(field) if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        return None
    return rows


def _username(row: dict[str, Any]) -> str:
    return str(row.get("user", row.get("username", row.get("name", ""))))


def _vhost_name(row: dict[str, Any]) -> str:
    return str(row.get("vhost", row.get("name", "")))


def _validate_output(query: str, stdout: str) -> bool:
    if query == "readiness":
        return stdout.strip() in {"", "ok", "running", "RabbitMQ is running"}
    field = {"users": "users", "prod_permissions": "permissions", "all_permissions": "permissions", "vhosts": "vhosts"}.get(query)
    if field is None:
        return False
    rows = _json_rows(stdout, field)
    if rows is None:
        return False
    if query == "users":
        names = [_username(row) for row in rows]
        expected_workloads = {"cristexhub_dev_rabbitmq", "cristexhub_prod_user"}
        if len(rows) != 3 or len(set(names)) != 3 or not expected_workloads.issubset(names):
            return False
        if any(not name or name == "guest" for name in names):
            return False
        administrators = [row for row in rows if str(row.get("tags", "")) == "administrator"]
        workload_rows = [row for row in rows if _username(row) in expected_workloads]
        return (
            len(administrators) == 1
            and len(workload_rows) == 2
            and all(row.get("tags", "") == "" for row in workload_rows)
            and all(set(row).issubset({"user", "username", "name", "tags"}) for row in rows)
        )
    if query in {"prod_permissions", "all_permissions"}:
        expected_prod = {"user": "cristexhub_prod_user", "vhost": "/cristexhub-prod", **_EXPECTED_PERMISSIONS}
        expected_dev = {"user": "cristexhub_dev_rabbitmq", "vhost": "/cristexhub-dev", **_EXPECTED_PERMISSIONS}
        expected_rows = [expected_prod] if query == "prod_permissions" else [expected_dev, expected_prod]
        if any(set(row) != {"user", "vhost", "configure", "write", "read"} for row in rows):
            return False
        if any(any(not isinstance(row.get(key), str) for key in ("user", "vhost", "configure", "write", "read")) for row in rows):
            return False
        return sorted(rows, key=lambda row: (row["user"], row["vhost"])) == sorted(
            expected_rows, key=lambda row: (row["user"], row["vhost"])
        )
    if query == "vhosts":
        return len(rows) == 2 and {_vhost_name(row) for row in rows} == {"/cristexhub-dev", "/cristexhub-prod"}
    return False


def _reject(message: str) -> dict[str, Any]:
    return {"changed": False, "failed": True, "msg": message}


class ActionModule(ActionBase):
    """Execute one fixed, value-free RabbitMQ metadata query through k8s_exec."""

    TRANSFERS_FILES = False

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        result = super().run(tmp=tmp, task_vars=task_vars)
        task_vars = task_vars or {}
        args = self._task.args
        if str(self._task.get_path()).rsplit(":", 1)[0] != str(_TASK_SOURCE):
            return _reject("ENTRYPOINT_GUARD: refusing RabbitMQ rotation query outside canonical role")
        selection_reasons = _selection_guard_reasons()
        if selection_reasons:
            return _reject(
                "TASK_SELECTION_GUARD: canonical invocation rejected ["
                + ",".join(selection_reasons)
                + "]"
            )
        if set(args) != _ARGUMENT_KEYS or args.get("query") not in _EXPECTED_QUERIES:
            return _reject("MUTATION_ARGUMENT_GUARD: refusing unmodeled RabbitMQ metadata query")
        token = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_TOKEN", "")
        attestation_path = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ATTESTATION_FILE", "")
        wrapper_pid = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_PID", "")
        wrapper_starttime = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_STARTTIME", "")
        wrapper_path = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_PATH", "")
        try:
            pid = int(wrapper_pid)
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation = Path(attestation_path).read_text(encoding="utf-8").strip()
        except (OSError, ValueError, UnicodeError):
            pid, attestation_state, attestation = 0, None, ""
        wrapper_sha = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_SHA256", "")
        valid_attestation = (
            os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and pid > 1
            and _ancestor(pid)
            and _proc_starttime(pid) == wrapper_starttime
            and len(_proc_cmdline(pid)) == 3
            and _canonical_shell(pid, _proc_cmdline(pid))
            and _canonical_wrapper_argument(_proc_cmdline(pid)[1], pid)
            and _proc_cmdline(pid)[2] == "check"
            and attestation_state is not None
            and stat.S_ISREG(attestation_state.st_mode)
            and not stat.S_ISLNK(attestation_state.st_mode)
            and stat.S_IMODE(attestation_state.st_mode) == 0o600
            and attestation_state.st_uid == os.getuid()
            and Path(wrapper_path) == _WRAPPER_SOURCE
            and wrapper_sha == _sha256(_WRAPPER_SOURCE)
            and attestation == f"{token}:entrypoint:{pid}:{wrapper_starttime}:{wrapper_sha}"
        )
        expected_env = {
            "CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_CANONICAL_SHA256": _action_canonical_expected(),
            "CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_CANONICAL_SHA256": _wrapper_canonical_expected(),
        }
        valid_sources = (
            _source_closure_valid()
            and _runtime_provenance_valid()
            and _canonical_action_hash(Path(__file__)) == _ACTION_CANONICAL_SHA256 == _action_canonical_expected()
            and _canonical_strategy_hash(_REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py") == _strategy_canonical_expected()
            and _canonical_wrapper_hash(_WRAPPER_SOURCE) == _wrapper_canonical_expected()
            and _full_action_hash(_ACTION_SOURCE) == _action_full_expected()
            and _full_strategy_hash(_REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py") == _strategy_full_expected()
            and _sha256(_TASK_SOURCE) == _TASK_SHA256
            and _sha256(_DEFAULTS_SOURCE) == _DEFAULTS_SHA256
            and _sha256(_PLAYBOOK_SOURCE) == _PLAYBOOK_SHA256
            and _sha256(_POLICY_SOURCE) == _POLICY_SHA256
            and _sha256(_METADATA_SOURCE) == _METADATA_SHA256
            and _sha256(_BROKER_SOURCE) == _BROKER_SOURCE_SHA256
            and _sha256(_RABBITMQ_CONFIG_SOURCE) == _RABBITMQ_CONFIG_SOURCE_SHA256
            and _sha256(_ENGINE_SOURCE) == _ENGINE_SOURCE_SHA256
            and _sha256(_RUNTIME_SOURCE) == _RUNTIME_SOURCE_SHA256
            and _full_action_hash(_ACTION_SOURCE) == os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_SHA256")
            and _canonical_action_hash(Path(__file__)) == os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_CANONICAL_SHA256") == expected_env["CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_CANONICAL_SHA256"]
            and _canonical_wrapper_hash(_WRAPPER_SOURCE) == _wrapper_canonical_expected()
            and expected_env["CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_CANONICAL_SHA256"] == os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_CANONICAL_SHA256")
            and _full_action_hash(_ACTION_SOURCE) == _action_full_expected()
            and _full_action_hash(_ACTION_SOURCE) == os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_SHA256")
            and _full_strategy_hash(_REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py") == _strategy_full_expected()
            and _full_strategy_hash(_REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py") == os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_STRATEGY_SHA256")
        )
        binding = task_vars.get("rabbitmq_prod_credential_rotation_check_internal_binding", {})
        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding.get("queries") == sorted(_EXPECTED_QUERIES)
            and args.get("query") in binding.get("queries", [])
            and binding.get("metadata_only") is True
            and binding.get("no_apply_path") is True
            and binding.get("no_secret_payloads") is True
        )
        if not valid_attestation or not valid_sources or not valid_binding:
            return _reject("ENTRYPOINT_GUARD: refusing RabbitMQ rotation query without canonical binding")
        if args.get("namespace") != "shared-services" or args.get("pod") != "shared-rabbitmq-0" or args.get("container") != "rabbitmq" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml":
            return _reject("MUTATION_ARGUMENT_GUARD: refusing RabbitMQ query identity drift")
        command = args.get("command")
        if command != _EXPECTED_QUERIES[args["query"]] or any(re.search(pattern, " ".join(command), re.I) for pattern in (r"password", r"secret", r"token", r"(?:amqps?|rabbitmq)://[^ ]+:[^ ]+@")):
            return _reject("SECRET_ARGV_GUARD: refusing non-canonical RabbitMQ query")
        executed = self._execute_module(
            module_name="kubernetes.core.k8s_exec",
            module_args={
                "namespace": args["namespace"],
                "pod": args["pod"],
                "container": args["container"],
                "command": " ".join(shlex.quote(str(value)) for value in command),
                "kubeconfig": args["kubeconfig"],
            },
            task_vars=task_vars,
            tmp=tmp,
        )
        stdout = executed.get("stdout", "")
        failed = bool(executed.get("failed")) or int(executed.get("rc", 0) or 0) != 0 or not _validate_output(args["query"], stdout)
        result.update(changed=False, failed=failed, msg="RabbitMQ metadata query completed" if not failed else "RabbitMQ metadata query failed")
        for key in ("stdout", "stderr", "rc", "result"):
            result.pop(key, None)
        return result
