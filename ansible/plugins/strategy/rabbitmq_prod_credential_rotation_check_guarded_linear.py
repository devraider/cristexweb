from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

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
_PYTHON_SOURCE = _REPOSITORY_ROOT / ".venv/bin/python"
_PYTHON_REAL_SOURCE = Path("/usr/bin/python3.13")
_PYTHON_LINK_TARGET = "/usr/bin/python3"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation"
_ACTION_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py"
_STRATEGY_SOURCE = Path(__file__).resolve()
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/rabbitmq_prod_credential_rotation_check/defaults/main.yml"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml"
_POLICY_SOURCE = _REPOSITORY_ROOT / "ansible/files/policies/cristexhub-prod-rabbitmq-credential-rotation.yml"
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
# strategy self-pin and closure digest are normalized by _canonical_hash().
_ROLE_PATH = _REPOSITORY_ROOT / "ansible/roles/rabbitmq_prod_credential_rotation_check"
_ROLES_PATH = _REPOSITORY_ROOT / "ansible/roles"
_LIBRARY_PATH = _REPOSITORY_ROOT / "ansible/library"
_REQUIREMENTS_SOURCE = _REPOSITORY_ROOT / "ansible/requirements.yml"
_COLLECTION_ROOT = _REPOSITORY_ROOT / "ansible/.ansible/collections/ansible_collections/kubernetes/core"
_COLLECTION_MANIFEST_SOURCE = _COLLECTION_ROOT / "MANIFEST.json"
_COLLECTION_FILES_SOURCE = _COLLECTION_ROOT / "FILES.json"
_ENV_PREFIX = "CRISTEXWEB_RABBITMQ_PROD_ROTATION_"
_OPERATOR = "paul"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_EXPECTED_PYTHON_SHA256 = "17b78e0a93175e86f9ac03141924fd7a7f0c0c52e66b34bfa0de20ffef989df1"
_EXPECTED_REQUIREMENTS_SHA256 = "f82d9e5ba1b64324710eb66c956d0447c46d3958722f635a4502bcb6c3efc75f"
_EXPECTED_COLLECTION_MANIFEST_SHA256 = "dc32e90ca987d6199e9091f749ecb40fd3380b40aabb7c18961ec75582cfc6df"
_EXPECTED_COLLECTION_FILES_SHA256 = "9d30dde4e4d6d04ec2e9b00a2d787114f13577fd2c456d25726865e3db39fa69"
_STRATEGY_CANONICAL_SHA256 = "596543a6154f9f293d4429a392ff99451529be2f781333a3a07f4a378bf04323"
_CLOSURE_MANIFEST_SHA256 = "a544d2cff1dfd84e595b2a5e56f63911dbfb3cea76a8c4e6358e751ceacf4350"
_TASK_SHA256 = "ce574a70263b4ddce8c9dd27f07b75c3d401b880c3ac9c02ca3348fb79cc8a71"
_DEFAULTS_SHA256 = "3e5d9d043eccd416d0696da9dd4441f1ec78cac092dd1f1752d4b69725c121ac"
_PLAYBOOK_SHA256 = "afba74ac3b512de525f322dcf7e89e3faed012f277c79912f439ddb9b2cf9b60"
_POLICY_SHA256 = "b4cd58058ccbbd236b44511b63637bda5fb61a6ca2df56f4f78e24f2da8a409f"
_METADATA_SHA256 = "586841d6c3f677e5bd7d68c5968f92f3abe508ddb026227c312db14582bdd6be"
_BROKER_SOURCE_SHA256 = "5ea7cfa66e72615e5ff50657e934740907a90d4219c221323e3b91af3efe6242"
_RABBITMQ_CONFIG_SOURCE_SHA256 = "663c006190e6e5e03e7c22d198cb41245d2ab3b7dab406acb4fdefe00a10a2d5"
_ENGINE_SOURCE_SHA256 = "b5eeaa0abc5b9ee91d392d6ac064862026b64f0d4c74f6431fe5dca517c506d0"
_RUNTIME_SOURCE_SHA256 = "3204aab3fc0f5b55f9af3623fb658d5ffd8289437d5d0ea91ab0480dc4126ee0"

_FORBIDDEN_ENV = (
    "ANSIBLE_INVENTORY",
    "ANSIBLE_PLAYBOOK_DIR",
    "ANSIBLE_STRATEGY",
    "ANSIBLE_ACTION_PLUGINS",
    "ANSIBLE_STRATEGY_PLUGINS",
    "ANSIBLE_STDOUT_CALLBACK",
    "ANSIBLE_CALLBACK_PLUGINS",
    "ANSIBLE_LOAD_CALLBACK_PLUGINS",
    "ANSIBLE_VAULT_PASSWORD_FILE",
    "ANSIBLE_PRIVATE_KEY_FILE",
    "ANSIBLE_REMOTE_USER",
    "ANSIBLE_BECOME_EXE",
    "ANSIBLE_BECOME_METHOD",
    "ANSIBLE_BECOME_USER",
    "ANSIBLE_COLLECTIONS_PATH",
    "ANSIBLE_START_AT_TASK",
    "ANSIBLE_SKIP_TAGS",
    "ANSIBLE_TAGS",
    "ANSIBLE_STEP",
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTHONOPTIMIZE",
    "PYTHONINSPECT",
    "PYTHONBREAKPOINT",
    "VIRTUAL_ENV",
)

_EXPECTED_COLLECTION_ACTION_SYMLINKS = {
    "helm.py", "helm_info.py", "helm_plugin.py", "helm_plugin_info.py",
    "helm_repository.py", "k8s.py", "k8s_cluster_info.py", "k8s_cp.py",
    "k8s_drain.py", "k8s_exec.py", "k8s_json_patch.py", "k8s_log.py",
    "k8s_rollback.py", "k8s_scale.py", "k8s_service.py",
}
_EXPECTED_COLLECTION_EXECUTED_FILES = {
    "plugins/action/k8s.py",
    "plugins/action/k8s_info.py",
    "plugins/action/k8s_json_patch.py",
    "plugins/modules/k8s_info.py",
    "plugins/modules/k8s.py",
    "plugins/modules/k8s_json_patch.py",
    "plugins/module_utils/k8s/client.py",
    "plugins/module_utils/k8s/core.py",
    "plugins/module_utils/k8s/exceptions.py",
    "plugins/module_utils/k8s/resource.py",
    "plugins/module_utils/k8s/runner.py",
    "plugins/module_utils/k8s/service.py",
    "plugins/module_utils/k8s/waiter.py",
    "plugins/module_utils/ansiblemodule.py",
    "plugins/module_utils/apply.py",
    "plugins/module_utils/args_common.py",
    "plugins/module_utils/common.py",
    "plugins/module_utils/copy.py",
    "plugins/module_utils/exceptions.py",
    "plugins/module_utils/hashes.py",
    "plugins/module_utils/k8sdynamicclient.py",
    "plugins/module_utils/selector.py",
    "plugins/module_utils/version.py",
}
def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _canonical_hash(path: Path, symbol: str) -> str:
    """Hash a strategy source while normalizing only self/closure pins."""
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            rf'(?m)^{re.escape(symbol)} = "[0-9a-f]{{64}}"$',
            f'{symbol} = "' + ("0" * 64) + '"',
            source,
        )
        source, closure_count = re.subn(
            r'(?m)^_CLOSURE_MANIFEST_SHA256 = "[0-9a-f]{64}"$',
            '_CLOSURE_MANIFEST_SHA256 = "' + ("0" * 64) + '"',
            source,
        )
        return hashlib.sha256(source.encode("utf-8")).hexdigest() if count == closure_count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _canonical_action_hash(path: Path) -> str:
    """Hash the action source while normalizing only its self/closure pins."""
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
        return hashlib.sha256(source.encode("utf-8")).hexdigest() if action_count == closure_count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _closure_anchor(kind: str, relative: str) -> str:
    """Read one committed consistency anchor from the source closure."""
    try:
        lines = _CLOSURE_SOURCE.read_text(encoding="utf-8").splitlines()
        matches = [
            line.split()[1]
            for line in lines
            if len(line.split()) == 3 and line.split()[0] == kind and line.split()[2] == relative
        ]
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


def _action_full_expected() -> str:
    return _closure_anchor(
        "full", "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py"
    )


def _strategy_full_expected() -> str:
    return _closure_anchor(
        "full", "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py"
    )


def _strategy_canonical_expected() -> str:
    return _closure_anchor(
        "canonical", "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py"
    )


def _full_action_hash(path: Path) -> str:
    """Hash the complete action while normalizing only the closure digest."""
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            r'(?m)^_CLOSURE_MANIFEST_SHA256 = "[0-9a-f]{64}"$',
            '_CLOSURE_MANIFEST_SHA256 = "' + ("0" * 64) + '"',
            source,
        )
        return hashlib.sha256(source.encode("utf-8")).hexdigest() if count == 1 else ""
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
        return hashlib.sha256(source.encode("utf-8")).hexdigest() if count == 1 else ""
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
        return hashlib.sha256(source.encode("utf-8")).hexdigest() if count == 1 else ""
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
        return hashlib.sha256(source.encode("utf-8")).hexdigest() if wrapper_count == closure_count == 1 else ""
    except (OSError, UnicodeError):
        return ""


_CLOSURE_ENTRIES = (
    ("canonical", "ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation", _WRAPPER_SOURCE, 0o755),
    ("canonical", "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py", _ACTION_SOURCE, 0o644),
    ("canonical", "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py", _STRATEGY_SOURCE, 0o644),
    ("full", "ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation", _WRAPPER_SOURCE, 0o755),
    ("full", "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py", _ACTION_SOURCE, 0o644),
    ("full", "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py", _STRATEGY_SOURCE, 0o644),
    ("sha256", "ansible/ansible.cfg", _ANSIBLE_CONFIG, 0o644),
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


def _closure_digest(kind: str, path: Path) -> str:
    if kind == "sha256":
        return _sha256(path)
    if kind == "full":
        if path == _WRAPPER_SOURCE:
            return _full_wrapper_hash(path)
        if path == _ACTION_SOURCE:
            return _full_action_hash(path)
        if path == _STRATEGY_SOURCE:
            return _full_strategy_hash(path)
        return ""
    if path == _WRAPPER_SOURCE:
        return _canonical_wrapper_hash(path)
    if path == _ACTION_SOURCE:
        return _canonical_action_hash(path)
    if path == _STRATEGY_SOURCE:
        return _canonical_hash(path, "_STRATEGY_CANONICAL_SHA256")
    return ""


def _closure_lines() -> list[str]:
    return [f"{kind} {_closure_digest(kind, path)}  {relative}" for kind, relative, path, _mode in _CLOSURE_ENTRIES]


def _source_closure_valid() -> bool:
    """Require the committed source closure before role scheduling or API access."""
    try:
        if not _regular_file(_CLOSURE_SOURCE, 0o644, os.getuid()):
            return False
        if _sha256(_CLOSURE_SOURCE) != _CLOSURE_MANIFEST_SHA256:
            return False
        if _CLOSURE_SOURCE.read_text(encoding="utf-8").splitlines() != _closure_lines():
            return False
        closure_lines = _CLOSURE_SOURCE.read_text(encoding="utf-8").splitlines()
        for kind, relative, path, mode in _CLOSURE_ENTRIES:
            if not _regular_file(path, mode, os.getuid()):
                return False
            actual = _closure_digest(kind, path)
            expected = [
                line.split()[1]
                for line in closure_lines
                if len(line.split()) == 3 and line.split()[0] == kind and line.split()[2] == relative
            ]
            if not actual or expected != [actual]:
                return False
        return (
            _canonical_hash(_STRATEGY_SOURCE, "_STRATEGY_CANONICAL_SHA256")
            == _STRATEGY_CANONICAL_SHA256
            == _strategy_canonical_expected()
        )
    except (OSError, UnicodeError, RuntimeError):
        return False


def _regular_file(
    path: Path,
    mode: int,
    owner: int | None = None,
    group: int | None = None,
) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
    except OSError:
        return False
    expected_group = os.getgid() if owner is not None and group is None else group
    return (
        stat.S_ISREG(state.st_mode)
        and not path.is_symlink()
        and stat.S_IMODE(state.st_mode) == mode
        and (owner is None or state.st_uid == owner)
        and (expected_group is None or state.st_gid == expected_group)
    )


def _directory(path: Path, owner: int | None = None) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
    except OSError:
        return False
    return (
        stat.S_ISDIR(state.st_mode)
        and not path.is_symlink()
        and (owner is None or (state.st_uid == owner and state.st_gid == os.getgid()))
    )


def _collection_toolchain_valid() -> bool:
    """Validate the exact installed kubernetes.core 6.1.0 execution tree."""
    try:
        if not _directory(_COLLECTION_ROOT, os.getuid()):
            return False
        if not _regular_file(_REQUIREMENTS_SOURCE, 0o644, os.getuid()):
            return False
        if _sha256(_REQUIREMENTS_SOURCE) != _EXPECTED_REQUIREMENTS_SHA256:
            return False
        if not _regular_file(_COLLECTION_MANIFEST_SOURCE, 0o644, os.getuid()):
            return False
        if _sha256(_COLLECTION_MANIFEST_SOURCE) != _EXPECTED_COLLECTION_MANIFEST_SHA256:
            return False
        if not _regular_file(_COLLECTION_FILES_SOURCE, 0o644, os.getuid()):
            return False
        if _sha256(_COLLECTION_FILES_SOURCE) != _EXPECTED_COLLECTION_FILES_SHA256:
            return False
        manifest = json.loads(_COLLECTION_MANIFEST_SOURCE.read_text(encoding="utf-8"))
        if manifest.get("collection_info", {}).get("namespace") != "kubernetes":
            return False
        if manifest.get("collection_info", {}).get("name") != "core":
            return False
        if manifest.get("collection_info", {}).get("version") != "6.1.0":
            return False
        files_payload = json.loads(_COLLECTION_FILES_SOURCE.read_text(encoding="utf-8"))
        entries = files_payload.get("files")
        if not isinstance(entries, list):
            return False
        expected: dict[str, str] = {"FILES.json": "file", "MANIFEST.json": "file"}
        digests: dict[str, str] = {}
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
            if relative.is_absolute() or relative.as_posix() != name or any(
                part in {"", ".", ".."} for part in relative.parts
            ):
                return False
            if kind not in {"file", "dir"} or name in expected:
                return False
            expected[name] = kind
            if kind == "file":
                digest = item.get("chksum_sha256")
                if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                    return False
                digests[name] = digest
            elif item.get("chksum_sha256") not in (None, ""):
                return False
        if not _EXPECTED_COLLECTION_EXECUTED_FILES.issubset(expected):
            return False
        actual: dict[str, str] = {}
        symlinks: set[str] = set()
        for entry in _COLLECTION_ROOT.rglob("*"):
            name = entry.relative_to(_COLLECTION_ROOT).as_posix()
            if entry.is_symlink():
                actual[name] = "file"
                symlinks.add(name)
            elif entry.is_dir():
                actual[name] = "dir"
            elif entry.is_file():
                actual[name] = "file"
            else:
                return False
        if actual != expected:
            return False
        expected_symlinks = {
            f"plugins/action/{name}" for name in _EXPECTED_COLLECTION_ACTION_SYMLINKS
        }
        if symlinks != expected_symlinks:
            return False
        if any(
            entry.name == "__pycache__" or entry.suffix.lower() in
            {".pyc", ".pyo", ".so", ".dylib", ".dll", ".pyd"}
            for entry in _COLLECTION_ROOT.rglob("*")
        ):
            return False
        for name, kind in expected.items():
            entry = _COLLECTION_ROOT / name
            state = entry.stat(follow_symlinks=False)
            if kind == "dir":
                if entry.is_symlink() or not stat.S_ISDIR(state.st_mode):
                    return False
                if stat.S_IMODE(state.st_mode) != 0o755 or state.st_uid != os.getuid():
                    return False
                continue
            if entry.is_symlink():
                if name not in expected_symlinks or state.st_uid != os.getuid():
                    return False
                if os.readlink(entry) != "k8s_info.py":
                    return False
            elif (
                not stat.S_ISREG(state.st_mode)
                or state.st_uid != os.getuid()
                or stat.S_IMODE(state.st_mode) not in {0o644, 0o755}
            ):
                return False
            if name in digests and _sha256(entry) != digests[name]:
                return False
        return True
    except (OSError, RuntimeError, UnicodeError, ValueError, TypeError):
        return False


def _inventory_contract() -> bool:
    if not _regular_file(_INVENTORY_SOURCE, 0o600, os.getuid()):
        return False
    try:
        content = _INVENTORY_SOURCE.read_bytes()
    except OSError:
        return False
    return hashlib.sha256(content).hexdigest() == _INVENTORY_SHA256 and content == _INVENTORY_BYTES


def _canonical_argv() -> bool:
    if not sys.argv or sys.argv[0] != str(_CONTROLLER):
        return False
    argv = sys.argv[1:]
    if len(argv) != 9:
        return False
    if argv[:3] != ["-i", ".ansible/inventory.local.yml", "playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml"]:
        return False
    if argv[3:8] != ["--check", "--diff", "--limit", "crtxweb", "--extra-vars"]:
        return False
    try:
        payload = json.loads(argv[8])
    except (IndexError, TypeError, ValueError):
        return False
    return payload == {"rabbitmq_prod_credential_rotation_check_approved": True}

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


def _proc_executable(pid: int) -> Path | None:
    try:
        return Path(os.readlink(f"/proc/{pid}/exe")).resolve(strict=True)
    except (OSError, RuntimeError):
        return None


def _is_ancestor(pid: int) -> bool:
    current = os.getpid()
    seen: set[int] = set()
    while current > 1 and current not in seen:
        if current == pid:
            return True
        seen.add(current)
        current = _proc_parent(current)
    return False


def _canonical_shell(pid: int, command: list[str]) -> bool:
    if not command or command[0] not in {"/bin/sh", "/bin/dash"}:
        return False
    try:
        dash = Path("/usr/bin/dash").resolve(strict=True)
        requested = Path(command[0]).resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    return requested == dash and _proc_executable(pid) == dash


def _canonical_wrapper_argument(argument: str, pid: int) -> bool:
    try:
        requested = Path(argument)
        if requested.is_absolute():
            return requested.resolve(strict=True) == _WRAPPER_SOURCE
        cwd = Path(os.readlink(f"/proc/{pid}/cwd"))
        # A relative wrapper argument may be relative to the wrapper's original
        # cwd or to the repository root after the wrapper has cd'd into ansible.
        # Resolve each candidate independently: a missing first candidate must
        # not abort evaluation of the canonical repository-root candidate.
        for base in (cwd, _REPOSITORY_ROOT):
            try:
                if (base / requested).resolve(strict=True) == _WRAPPER_SOURCE:
                    return True
            except (OSError, RuntimeError):
                continue
        return False
    except (OSError, RuntimeError):
        return False


def _wrapper_attestation_valid() -> bool:
    prefix = _ENV_PREFIX
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
    expected_wrapper = _wrapper_canonical_expected()
    return (
        os.environ.get(prefix + "ENTRYPOINT") == "v1"
        and os.environ.get(prefix + "MODE") == "check"
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
        and _canonical_shell(pid, command)
        and len(command) == 3
        and _canonical_wrapper_argument(command[1], pid)
        and command[2] == "check"
        and content == f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\n"
        and os.environ.get(prefix + "WRAPPER_PATH") == str(_WRAPPER_SOURCE)
        and wrapper_sha == _sha256(_WRAPPER_SOURCE)
        and expected_wrapper != ""
        and os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256") == expected_wrapper
        and _canonical_wrapper_hash(_WRAPPER_SOURCE) == expected_wrapper
    )


_wrapper_binding_valid = _wrapper_attestation_valid


def _python_interpreter_valid() -> bool:
    try:
        link_state = _PYTHON_SOURCE.stat(follow_symlinks=False)
        return (
            stat.S_ISLNK(link_state.st_mode)
            and link_state.st_uid == os.getuid()
            and os.readlink(_PYTHON_SOURCE) == _PYTHON_LINK_TARGET
            and _PYTHON_SOURCE.resolve(strict=True) == _PYTHON_REAL_SOURCE
            and _regular_file(_PYTHON_REAL_SOURCE, 0o755, 0, 0)
            and _sha256(_PYTHON_REAL_SOURCE) == _EXPECTED_PYTHON_SHA256
        )
    except (OSError, RuntimeError):
        return False


def _source_contract() -> bool:
    prefix = _ENV_PREFIX
    if not _source_closure_valid():
        return False
    sources = (
        ("TASK_SHA256", _TASK_SOURCE, _TASK_SHA256, 0o644),
        ("DEFAULTS_SHA256", _DEFAULTS_SOURCE, _DEFAULTS_SHA256, 0o644),
        ("PLAYBOOK_SHA256", _PLAYBOOK_SOURCE, _PLAYBOOK_SHA256, 0o644),
        ("POLICY_SHA256", _POLICY_SOURCE, _POLICY_SHA256, 0o644),
        ("METADATA_SHA256", _METADATA_SOURCE, _METADATA_SHA256, 0o755),
        ("BROKER_SOURCE_SHA256", _BROKER_SOURCE, _BROKER_SOURCE_SHA256, 0o644),
        ("RABBITMQ_CONFIG_SOURCE_SHA256", _RABBITMQ_CONFIG_SOURCE, _RABBITMQ_CONFIG_SOURCE_SHA256, 0o644),
        ("ENGINE_SOURCE_SHA256", _ENGINE_SOURCE, _ENGINE_SOURCE_SHA256, 0o644),
        ("RUNTIME_SOURCE_SHA256", _RUNTIME_SOURCE, _RUNTIME_SOURCE_SHA256, 0o644),
    )
    for suffix, path, expected, mode in sources:
        if not _regular_file(path, mode, os.getuid()):
            return False
        if _sha256(path) != expected or os.environ.get(prefix + suffix) != expected:
            return False
    action_sha = _full_action_hash(_ACTION_SOURCE)
    strategy_sha = _full_strategy_hash(_STRATEGY_SOURCE)
    expected_wrapper = _wrapper_canonical_expected()
    expected_action = _action_canonical_expected()
    return (
        _regular_file(_ACTION_SOURCE, 0o644, os.getuid())
        and action_sha == os.environ.get(prefix + "ACTION_SHA256")
        and action_sha == _action_full_expected()
        and _canonical_action_hash(_ACTION_SOURCE) == expected_action
        and os.environ.get(prefix + "ACTION_CANONICAL_SHA256") == expected_action
        and _regular_file(_STRATEGY_SOURCE, 0o644, os.getuid())
        and strategy_sha == os.environ.get(prefix + "STRATEGY_SHA256")
        and strategy_sha == _strategy_full_expected()
        and _canonical_hash(_STRATEGY_SOURCE, "_STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256 == _strategy_canonical_expected()
        and os.environ.get(prefix + "STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256
        and expected_wrapper != ""
        and _canonical_wrapper_hash(_WRAPPER_SOURCE) == expected_wrapper
        and os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256") == expected_wrapper
        and os.environ.get(prefix + "SOURCE_CLOSURE_PATH") == str(_CLOSURE_SOURCE)
        and os.environ.get(prefix + "SOURCE_CLOSURE_SHA256") == _CLOSURE_MANIFEST_SHA256
    )



def _no_vars_plugins() -> bool:
    bases = (_INVENTORY_SOURCE.parent, _PLAYBOOK_SOURCE.parent, _ANSIBLE_CONFIG.parent, _REPOSITORY_ROOT)
    return all(not (base / name).exists() for base in bases for name in ("host_vars", "group_vars"))


def _forbidden_environment_clean() -> bool:
    return not any(os.environ.get(name) for name in _FORBIDDEN_ENV)


def _runtime_contract() -> bool:
    prefix = _ENV_PREFIX
    if (
        os.environ.get(prefix + "ENTRYPOINT") != "v1"
        or os.environ.get(prefix + "MODE") != "check"
    ):
        return False
    if not _inventory_contract() or not _python_interpreter_valid():
        return False
    if not _regular_file(_ANSIBLE_CONFIG, 0o644, os.getuid()) or not _regular_file(_CONTROLLER, 0o755, os.getuid()):
        return False
    if _sha256(_ANSIBLE_CONFIG) != _ANSIBLE_CONFIG_SHA256 or _sha256(_CONTROLLER) != _CONTROLLER_SHA256:
        return False
    if os.getuid() != os.stat(_CONTROLLER).st_uid or os.environ.get("HOME") != "/home/paul":
        return False
    if os.environ.get("USER") != _OPERATOR or os.environ.get("LOGNAME") != _OPERATOR:
        return False
    expected_paths = {
        "WRAPPER_PATH": str(_WRAPPER_SOURCE),
        "ANSIBLE_CONFIG_PATH": str(_ANSIBLE_CONFIG),
        "INVENTORY_PATH": str(_INVENTORY_SOURCE),
        "CONTROLLER_PATH": str(_CONTROLLER),
        "PYTHON_PATH": str(_PYTHON_SOURCE),
        "ROLES_PATH": str(_ROLES_PATH),
        "LIBRARY_PATH": str(_LIBRARY_PATH),
        "REQUIREMENTS_PATH": str(_REQUIREMENTS_SOURCE),
        "COLLECTION_ROOT": str(_COLLECTION_ROOT),
        "COLLECTION_MANIFEST_PATH": str(_COLLECTION_MANIFEST_SOURCE),
        "COLLECTION_FILES_PATH": str(_COLLECTION_FILES_SOURCE),
        "SOURCE_CLOSURE_PATH": str(_CLOSURE_SOURCE),
    }
    if any(os.environ.get(prefix + key) != value for key, value in expected_paths.items()):
        return False
    if os.environ.get("ANSIBLE_CONFIG") != str(_ANSIBLE_CONFIG):
        return False
    if os.environ.get("ANSIBLE_ROLES_PATH") != str(_ROLES_PATH) or os.environ.get("ANSIBLE_LIBRARY") != str(_LIBRARY_PATH):
        return False
    for suffix, value in (
        ("CONTROLLER_SHA256", _CONTROLLER_SHA256),
        ("PYTHON_SHA256", _EXPECTED_PYTHON_SHA256),
        ("ANSIBLE_CONFIG_SHA256", _ANSIBLE_CONFIG_SHA256),
        ("INVENTORY_SHA256", _INVENTORY_SHA256),
        ("REQUIREMENTS_SHA256", _EXPECTED_REQUIREMENTS_SHA256),
        ("COLLECTION_MANIFEST_SHA256", _EXPECTED_COLLECTION_MANIFEST_SHA256),
        ("COLLECTION_FILES_SHA256", _EXPECTED_COLLECTION_FILES_SHA256),
        ("SOURCE_CLOSURE_SHA256", _CLOSURE_MANIFEST_SHA256),
    ):
        if os.environ.get(prefix + suffix) != value:
            return False
    return _collection_toolchain_valid() and _no_vars_plugins() and _forbidden_environment_clean()

def _start_at_task_allowed() -> bool:
    return context.CLIARGS.get("start_at_task") is None


def _selection_guard_reasons() -> tuple[str, ...]:
    """Return stable reason codes without exposing argv, environment, or values.

    This intentionally reports categories only.  The strategy may inspect
    credential-adjacent runtime state, but a rejected invocation must never
    echo that state into an Ansible error or callback log.
    """
    reasons: list[str] = []

    def check(code: str, predicate: Any) -> None:
        try:
            if not bool(predicate()):
                reasons.append(code)
        except Exception:
            reasons.append(code)

    try:
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        inventory = context.CLIARGS.get("inventory") or []
        if isinstance(inventory, str):
            inventory = [inventory]
        elif isinstance(inventory, tuple):
            inventory = list(inventory)
        selection_argv = any(
            argument in {"--start-at-task", "--step", "--tags", "--skip-tags", "-t"}
            or argument.startswith(("--start-at-task=", "--tags=", "--skip-tags=", "-t="))
            for argument in sys.argv[1:]
        )
    except Exception:
        return ("cliargs-shape",)
    if selection_argv:
        reasons.append("selection-argv")
    check("start-at-task", _start_at_task_allowed)
    check("step", lambda: not context.CLIARGS.get("step"))
    check("tags", lambda: tags in ([], ["all"]))
    check("skip-tags", lambda: not skip_tags)
    check("subset", lambda: context.CLIARGS.get("subset") == "crtxweb")
    check("check-mode", lambda: context.CLIARGS.get("check") is True)
    check("diff-mode", lambda: context.CLIARGS.get("diff") is True)
    check("inventory", lambda: inventory == [str(_INVENTORY_SOURCE)])
    check("canonical-argv", _canonical_argv)
    check("wrapper-attestation", _wrapper_attestation_valid)
    runtime_ok = False
    try:
        runtime_ok = bool(_runtime_contract())
    except Exception:
        runtime_ok = False
    if not runtime_ok:
        reasons.append("runtime-contract")
        # Keep the useful environmental category separate while retaining the
        # generic runtime code for all other clean-environment failures.
        check("collection-toolchain", _collection_toolchain_valid)
    source_ok = False
    try:
        source_ok = bool(_source_contract())
    except Exception:
        source_ok = False
    if not source_ok:
        reasons.append("source-contract")
        check("source-closure", _source_closure_valid)
    return tuple(dict.fromkeys(reasons))


class StrategyModule(LinearStrategyModule):
    """Reject direct playbooks and task-selection controls before role tasks load."""

    def run(self, iterator, play_context):  # type: ignore[no-untyped-def]
        reasons = _selection_guard_reasons()
        if reasons:
            raise AnsibleError(
                "TASK_SELECTION_GUARD: canonical invocation rejected ["
                + ",".join(reasons)
                + "]"
            )
        return super().run(iterator, play_context)
