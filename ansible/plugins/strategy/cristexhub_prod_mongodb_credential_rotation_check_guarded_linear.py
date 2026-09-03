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
_PLAYBOOK = _REPOSITORY_ROOT / "ansible/playbooks/check_cristexhub_prod_mongodb_credential_rotation.yml"
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_mongodb_credential_rotation_check/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_mongodb_credential_rotation_check/defaults/main.yml"
_ROLE_PATH = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_mongodb_credential_rotation_check"
_ROLES_PATH = _REPOSITORY_ROOT / "ansible/roles"
_LIBRARY_PATH = _REPOSITORY_ROOT / "ansible/library"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/check-cristexhub-prod-mongodb-credential-rotation"
_POLICY_SOURCE = _REPOSITORY_ROOT / "ansible/files/policies/cristexhub-prod-mongodb-credential-rotation.yml"
_METADATA_SOURCE = _REPOSITORY_ROOT / "ansible/library/cristexhub_prod_mongodb_credential_rotation_metadata.py"
_SELECTOR_SOURCE = _REPOSITORY_ROOT / "ansible/library/cristexhub_prod_mongodb_networkpolicy_selector.py"
_STRATEGY_SOURCE = Path(__file__).resolve()
_ENGINE_CONNECTION_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-database-secrets/source/infisical-cloud-connection.yaml"
_ENGINE_AUTH_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-database-secrets/source/shared-mongodb-infisical-auth.yaml"
_ENGINE_MANIFEST_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-database-secrets/source/shared-mongodb-infisical-secrets.yaml"
_RUNTIME_CONNECTION_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-cristexhub-prod-runtime/source/infisical-cloud-connection.yaml"
_RUNTIME_AUTH_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-cristexhub-prod-runtime/source/cristexhub-prod-infisical-auth.yaml"
_RUNTIME_MANIFEST_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-cristexhub-prod-runtime/source/cristexhub-prod-runtime-static-secret.yaml"
_NETWORKPOLICY_DEFAULT_DENY_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/shared-mongodb-networkpolicy/network/shared-mongodb-networkpolicy-default-deny.yaml"
_NETWORKPOLICY_ALLOW_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/shared-mongodb-networkpolicy/network/shared-mongodb-networkpolicy-allow.yaml"
_REQUIREMENTS_SOURCE = _REPOSITORY_ROOT / "ansible/requirements.yml"
_COLLECTION_ROOT = _REPOSITORY_ROOT / "ansible/.ansible/collections/ansible_collections/kubernetes/core"
_COLLECTION_MANIFEST_SOURCE = _COLLECTION_ROOT / "MANIFEST.json"
_COLLECTION_FILES_SOURCE = _COLLECTION_ROOT / "FILES.json"

_ENV_PREFIX = "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
# This marker is the only normalized value; it prevents a circular strategy pin.
_STRATEGY_CANONICAL_SHA256 = "23b70ae8fb3f76cc373b2c7202e9071d273e314f2ea9b0c3330094fa2a951eb3"
_EXPECTED_REQUIREMENTS_SHA256 = "f82d9e5ba1b64324710eb66c956d0447c46d3958722f635a4502bcb6c3efc75f"
_EXPECTED_COLLECTION_MANIFEST_SHA256 = "dc32e90ca987d6199e9091f749ecb40fd3380b40aabb7c18961ec75582cfc6df"
_EXPECTED_COLLECTION_FILES_SHA256 = "9d30dde4e4d6d04ec2e9b00a2d787114f13577fd2c456d25726865e3db39fa69"
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
_EXPECTED_HASHES = {
    "TASK_SHA256": "cf81db862c6f79b9f56bbd0595793073ebb581850c3678eb240713f13d22ffbb",
    "DEFAULTS_SHA256": "ead3ec7189b16a6d66e54e263a904619b5b9e46dacf8b40a6174792c4f381703",
    "PLAYBOOK_SHA256": "c3986c36bea429483e3ca73be76a860db9f31fabe784253d9b3c0d4c3940bde9",
    "POLICY_SHA256": "16db815caf6989944632345aac46c6b45ee6d18d4bda7800d3d485d1d68217a2",
    "METADATA_MODULE_SHA256": "571837ae852d0098347747307dd5101c724413d9ee27e01bca50fa25157960d2",
    "NETWORKPOLICY_SELECTOR_MODULE_SHA256": "b3405007cd0c5c382d57bb184ab52715ea371ed9c3bd7421106860b95130c68a",
    "ENGINE_CONNECTION_SOURCE_SHA256": "701558f35f7473e2476f48ddf1298d0d3fe1e9c69fdd5e4e621ef196972b5a0f",
    "ENGINE_AUTH_SOURCE_SHA256": "7449e49d5a73da51f3915eb9e84d63800330e4d2c1142ff9539676f069660dcf",
    "ENGINE_SOURCE_MANIFEST_SHA256": "dba0e83942063c389aadb8b11a7ac24acdbadb214bb825e3dfcc7330b619dad0",
    "RUNTIME_CONNECTION_SOURCE_SHA256": "46c7e32727604975952b8f4eff6764dd341d222d8ac4d47015cdd07b12198a73",
    "RUNTIME_AUTH_SOURCE_SHA256": "e8173010a1f55b87024c367ac89177c34f4bc4993174960803c838046d766148",
    "RUNTIME_SOURCE_MANIFEST_SHA256": "3204aab3fc0f5b55f9af3623fb658d5ffd8289437d5d0ea91ab0480dc4126ee0",
    "NETWORKPOLICY_DEFAULT_DENY_SHA256": "531923114cb79b0c73adc64014422a0b8ded8d39550ffe0d5adb1e7c361843fc",
    "NETWORKPOLICY_ALLOW_SHA256": "b3f492e663a99f2264fa64bbf3accdb12a42767f67b5e2819c4fb24246cd3bfd"
}
_FORBIDDEN_ENV = (
    "ANSIBLE_INVENTORY",
    "ANSIBLE_PLAYBOOK_DIR",
    "ANSIBLE_STRATEGY",
    "ANSIBLE_ACTION_PLUGINS",
    "ANSIBLE_STRATEGY_PLUGINS",
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


def _regular_file(path: Path, mode: int, owner: int | None = None) -> bool:
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
        cwd = Path(os.readlink(f"/proc/{pid}/cwd"))
        return (cwd / argument).resolve() == _WRAPPER_SOURCE
    except (OSError, RuntimeError):
        return False


def _wrapper_binding_valid() -> bool:
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
        and os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256") ==
        _canonical_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected")
    )


def _runtime_contract() -> bool:
    prefix = _ENV_PREFIX
    if not _inventory_contract() or not _directory(_ROLES_PATH, os.getuid()) or not _directory(_ROLE_PATH, os.getuid()):
        return False
    if not _regular_file(_ANSIBLE_CONFIG, 0o644, os.getuid()) or not _regular_file(_CONTROLLER, 0o775, os.getuid()):
        return False
    if _sha256(_ANSIBLE_CONFIG) != _ANSIBLE_CONFIG_SHA256 or _sha256(_CONTROLLER) != _CONTROLLER_SHA256:
        return False
    expected_paths = {
        "WRAPPER_PATH": str(_WRAPPER_SOURCE),
        "ANSIBLE_CONFIG_PATH": str(_ANSIBLE_CONFIG),
        "INVENTORY_PATH": str(_INVENTORY_SOURCE),
        "CONTROLLER_PATH": str(_CONTROLLER),
        "ROLES_PATH": str(_ROLES_PATH),
        "LIBRARY_PATH": str(_LIBRARY_PATH),
        "REQUIREMENTS_PATH": str(_REQUIREMENTS_SOURCE),
        "COLLECTION_ROOT": str(_COLLECTION_ROOT),
        "COLLECTION_MANIFEST_PATH": str(_COLLECTION_MANIFEST_SOURCE),
        "COLLECTION_FILES_PATH": str(_COLLECTION_FILES_SOURCE),
    }
    if any(os.environ.get(prefix + key) != value for key, value in expected_paths.items()):
        return False
    if os.environ.get("ANSIBLE_CONFIG") != str(_ANSIBLE_CONFIG):
        return False
    if os.environ.get("ANSIBLE_ROLES_PATH") != str(_ROLES_PATH):
        return False
    if os.environ.get("ANSIBLE_LIBRARY") != str(_LIBRARY_PATH):
        return False
    if os.environ.get(prefix + "ENTRYPOINT") != "v1" or os.environ.get(prefix + "MODE") != "check":
        return False
    if not os.environ.get(prefix + "TOKEN"):
        return False
    for suffix, value in (
        ("CONTROLLER_SHA256", _CONTROLLER_SHA256),
        ("ANSIBLE_CONFIG_SHA256", _ANSIBLE_CONFIG_SHA256),
        ("INVENTORY_SHA256", _INVENTORY_SHA256),
        ("REQUIREMENTS_SHA256", _EXPECTED_REQUIREMENTS_SHA256),
        ("COLLECTION_MANIFEST_SHA256", _EXPECTED_COLLECTION_MANIFEST_SHA256),
        ("COLLECTION_FILES_SHA256", _EXPECTED_COLLECTION_FILES_SHA256),
    ):
        if os.environ.get(prefix + suffix) != value:
            return False
    return _collection_toolchain_valid() and not any(name in os.environ for name in _FORBIDDEN_ENV)


def _source_contract() -> bool:
    prefix = _ENV_PREFIX
    sources = (
        ("TASK_SHA256", _TASK_SOURCE, 0o644, os.getuid()),
        ("DEFAULTS_SHA256", _DEFAULTS_SOURCE, 0o644, os.getuid()),
        ("PLAYBOOK_SHA256", _PLAYBOOK, 0o644, os.getuid()),
        ("POLICY_SHA256", _POLICY_SOURCE, 0o644, os.getuid()),
        ("METADATA_MODULE_SHA256", _METADATA_SOURCE, 0o755, os.getuid()),
        ("NETWORKPOLICY_SELECTOR_MODULE_SHA256", _SELECTOR_SOURCE, 0o755, os.getuid()),
        ("STRATEGY_SHA256", _STRATEGY_SOURCE, 0o644, os.getuid()),
        ("ENGINE_CONNECTION_SOURCE_SHA256", _ENGINE_CONNECTION_SOURCE, 0o644, os.getuid()),
        ("ENGINE_AUTH_SOURCE_SHA256", _ENGINE_AUTH_SOURCE, 0o644, os.getuid()),
        ("ENGINE_SOURCE_MANIFEST_SHA256", _ENGINE_MANIFEST_SOURCE, 0o644, os.getuid()),
        ("RUNTIME_CONNECTION_SOURCE_SHA256", _RUNTIME_CONNECTION_SOURCE, 0o644, os.getuid()),
        ("RUNTIME_AUTH_SOURCE_SHA256", _RUNTIME_AUTH_SOURCE, 0o644, os.getuid()),
        ("RUNTIME_SOURCE_MANIFEST_SHA256", _RUNTIME_MANIFEST_SOURCE, 0o644, os.getuid()),
        ("NETWORKPOLICY_DEFAULT_DENY_SHA256", _NETWORKPOLICY_DEFAULT_DENY_SOURCE, 0o644, os.getuid()),
        ("NETWORKPOLICY_ALLOW_SHA256", _NETWORKPOLICY_ALLOW_SOURCE, 0o644, os.getuid()),
    )
    for suffix, path, mode, owner in sources:
        if not _regular_file(path, mode, owner):
            return False
        digest = _sha256(path)
        expected = digest if suffix == "STRATEGY_SHA256" else _EXPECTED_HASHES[suffix]
        if digest != expected or os.environ.get(prefix + suffix) != digest:
            return False
    if _canonical_hash(_STRATEGY_SOURCE, "_STRATEGY_CANONICAL_SHA256") != _STRATEGY_CANONICAL_SHA256:
        return False
    if os.environ.get(prefix + "STRATEGY_CANONICAL_SHA256") != _STRATEGY_CANONICAL_SHA256:
        return False
    if os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256") != _canonical_hash(
        _WRAPPER_SOURCE, "wrapper_canonical_sha256_expected"
    ):
        return False
    return _collection_toolchain_valid()


def _no_vars_plugins() -> bool:
    bases = (_INVENTORY_SOURCE.parent, _PLAYBOOK.parent, _ANSIBLE_CONFIG.parent, _REPOSITORY_ROOT)
    for base in bases:
        for name in ("host_vars", "group_vars"):
            if (base / name).exists():
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
        elif isinstance(inventory, tuple):
            inventory = list(inventory)
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
            or not _canonical_argv()
            or not _wrapper_binding_valid()
            or not _runtime_contract()
            or not _source_contract()
            or not _no_vars_plugins()
        ):
            raise AnsibleError(
                "TASK_SELECTION_GUARD: MongoDB rotation requires the complete canonical wrapper invocation"
            )
        return super().run(iterator, play_context)
