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
_INVENTORY_DIRECTORY = _INVENTORY_SOURCE.parent
_INVENTORY_SHA256 = "652a8455f8a050005ab783d20d4e60a0cd034d8a6439f1cffe551a91102773b0"
_INVENTORY_BYTES = (
    b"---\nall:\n  children:\n    k3s_servers:\n      hosts:\n"
    b"        crtxweb:\n          ansible_connection: local\n"
    b"          ansible_python_interpreter: /usr/bin/python3\n"
    b"          ansible_user: paul\n"
)
_ANSIBLE_CONFIG = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_CONTROLLER = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_PLAYBOOK = _REPOSITORY_ROOT / "ansible/playbooks/configure_reactive_resume_dev_tls_renewal.yml"
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/reactive_resume_dev_tls_renewal/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/reactive_resume_dev_tls_renewal/defaults/main.yml"
_MANIFEST_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/reactive-resume-dev-tls/MANIFESTS.sha256"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/configure-reactive-resume-dev-tls-renewal"
_MUTATION_ACTION_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py"
_MUTATION_MODULE_SOURCE = _REPOSITORY_ROOT / "ansible/library/reactive_resume_dev_tls_renewal_mutation_guarded.py"
_STRATEGY = Path(__file__).resolve()
_SOURCE_ROOT = _REPOSITORY_ROOT / "ansible/files/components/reactive-resume-dev-tls"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_PYTHON_SOURCE = Path("/usr/bin/python3")
_PYTHON_TARGET = Path("/usr/bin/python3.13")
_PYTHON_SHA256 = "17b78e0a93175e86f9ac03141924fd7a7f0c0c52e66b34bfa0de20ffef989df1"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
# These are immutable source pins. Self-referential source pins are normalized
# before hashing; all other pins are ordinary SHA-256 digests.
_STRATEGY_CANONICAL_SHA256 = "71b1c74ed437585d82a3b797fb60e25e16a1b8081d5b57a2bb210cf8acf11383"
# This canonical pin normalizes both self-referential provenance markers.
# The wrapper can therefore pin it without creating a cross-file hash cycle.
# This normalized pin removes only the provenance marker values below.
# It is independent of the wrapper's canonical marker and therefore cannot
# participate in a wrapper/strategy self-hash cycle.
_STRATEGY_NORMALIZED_SHA256 = "afd92617706fd7d523eb3ac4408dd6ddd2bcdc739e55db519ebafc0bf71a1daa"
_WRAPPER_CANONICAL_SHA256 = "96ad529555fa7a7a7d8bf8236b26dc81c6ac0d7edfb527dbf30fd8139c2cdc33"
_MUTATION_ACTION_SHA256 = "e0060109acc9fff92bae03c697f08697b81527f4e631cda86e7f33c581090d7d"
_MUTATION_MODULE_SHA256 = "38da36be88a0b530884b804b817ea5eb636f7008ec4272da4f2f0b2c0e58565a"
_PLAYBOOK_SHA256 = "3e73c601399c1189829802c5c3d438107bd1f884ff50b9e76702658bfd07db05"
_TASK_SHA256 = "11aa379f95e3f169ad2127734c58e4a6b03f605478cd8f3314840a755535d5aa"
_DEFAULTS_SHA256 = "d429cd82ed12f0cf8e5c5a56916f82a3efdb47d81706d8f8b2679585c9527b23"
_STRATEGY_ATTESTATION_SHA256 = "aa8ef9124552f3d1a1f65d7fdbeb2ec37bc28f84f1a77e8fffdf3f636a9c6dbb"
_MANIFEST_SHA256 = "4d68e7c466e1c396454ccd663f5d45d903f41cc0b64b68c8220fa9334378888b"
_SOURCE_HASHES = (
    ("renewal/validate-reactive-resume-dev-tls-material", "3a62d2326a8dee0e091cb0f4b12b9dbe12a10432d737b98aed5b5a27fd1b43cf", 0o755),
    ("renewal/cristexweb-reactive-resume-dev-tls-renew.service", "ddadb603a2f580bd14af0461c60cc30163174ecade9328c73b39d7afb1bd6cb3", 0o644),
    ("renewal/reactive-resume-dev-tls-renew", "cdd610d20a972f3a53f11122a038f20c7f8a327280ca5128a3da87845d576341", 0o755),
    ("source/reactive-resume-dev-tls.yaml", "bf9f6104f1e45c6f75bb86344dd151b05a2b4084cd76185a60ed3171f4d33ffe", 0o644),
    ("renewal/cristexweb-reactive-resume-dev-tls-renew.timer", "cd0a8c3b01e623627854ed63da37e0d35d4cc9f7db0b675d93f52325f2fb3a0f", 0o644),
)
_FORBIDDEN_ENV = (
    "ANSIBLE_INVENTORY",
    "ANSIBLE_PLAYBOOK_DIR",
    "ANSIBLE_STRATEGY",
    "ANSIBLE_ACTION_PLUGINS",
    "ANSIBLE_STRATEGY_PLUGINS",
    "ANSIBLE_LIBRARY",
    "ANSIBLE_COLLECTIONS_PATH",
    "ANSIBLE_VARS_PLUGINS",
    "ANSIBLE_VARS_PLUGIN_PATH",
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
_WRAPPER_ENV_PREFIX = "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_"
_CANONICAL_BECOME_METHODS = {"sudo", "ansible.builtin.sudo"}
_CANONICAL_BECOME_USER = "root"
_CANONICAL_BECOME_EXE = "sudo"
_CANONICAL_BECOME_FLAGS = "-H -S -n"


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
        if count != 1:
            return ""
        return hashlib.sha256(source.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _canonical_strategy_hash(path: Path) -> str:
    """Hash strategy source while normalizing every fixed provenance pin."""
    try:
        source = path.read_text(encoding="utf-8")
        for symbol in (
            "_STRATEGY_CANONICAL_SHA256",
            "_STRATEGY_NORMALIZED_SHA256",
            "_WRAPPER_CANONICAL_SHA256",
        ):
            source, count = re.subn(
                rf"(?m)^({re.escape(symbol)}\s*=\s*[\"'])([0-9a-f]{{64}})([\"']\s*)$",
                rf"\g<1>__PIN__\g<3>",
                source,
            )
            if count != 1:
                return ""
        return hashlib.sha256(source.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _normalized_strategy_hash(path: Path) -> str:
    """Hash strategy code while normalizing only fixed provenance markers."""
    try:
        source = path.read_text(encoding="utf-8")
        for symbol, marker in (
            ("_STRATEGY_CANONICAL_SHA256", "__STRATEGY_CANONICAL_HASH__"),
            ("_STRATEGY_NORMALIZED_SHA256", "__STRATEGY_NORMALIZED_HASH__"),
            ("_WRAPPER_CANONICAL_SHA256", "__WRAPPER_CANONICAL_HASH__"),
        ):
            source, count = re.subn(
                rf"(?m)^({re.escape(symbol)}\s*=\s*[\"'])([0-9a-f]{{64}})([\"']\s*)$",
                rf"\g<1>{marker}\g<3>",
                source,
            )
            if count != 1:
                return ""
        return hashlib.sha256(source.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _file_contract(path: Path, mode: int, digest: str) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
        return (
            stat.S_ISREG(state.st_mode)
            and not path.is_symlink()
            and state.st_uid == os.getuid()
            and state.st_gid == os.getgid()
            and stat.S_IMODE(state.st_mode) == mode
            and _sha256(path) == digest
        )
    except OSError:
        return False


def _normalized_yaml_hash(path: Path, task: bool = False) -> str:
    """Hash YAML while normalizing only named self-referential hash fields."""
    try:
        source = path.read_text(encoding="utf-8")
        if task:
            # These six provenance values participate in the task/defaults/
            # strategy/wrapper hash cycle. Keep every unrelated digest (for
            # example controller, Python, manifest, and source pins) covered.
            replacements = (
                (
                    r"(?ms)(lookup\('ansible\.builtin\.env',\s*'CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_CANONICAL_SHA256'\)\s*==\s*')[0-9a-f]{64}(')",
                    r"\1__STRATEGY_CANONICAL_HASH__\2",
                ),
                (
                    r"(?ms)(lookup\('ansible\.builtin\.env',\s*'CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_SHA256'\)\s*==\s*')[0-9a-f]{64}(')",
                    r"\1__STRATEGY_HASH__\2",
                ),
                (
                    r"(?ms)(lookup\('ansible\.builtin\.env',\s*'CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_NORMALIZED_SHA256'\)\s*==\s*')[0-9a-f]{64}(')",
                    r"\1__STRATEGY_NORMALIZED_HASH__\2",
                ),
                (
                    r"(?ms)(lookup\('ansible\.builtin\.env',\s*'CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_WRAPPER_CANONICAL_SHA256'\)\s*==\s*')[0-9a-f]{64}(')",
                    r"\1__WRAPPER_CANONICAL_HASH__\2",
                ),
                (
                    r"(?ms)(lookup\('ansible\.builtin\.env',\s*'CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_TASK_SHA256'\)\s*==\s*')[0-9a-f]{64}(')",
                    r"\1__TASK_HASH__\2",
                ),
                (
                    r"(?ms)(lookup\('ansible\.builtin\.env',\s*'CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_DEFAULTS_SHA256'\)\s*==\s*')[0-9a-f]{64}(')",
                    r"\1__DEFAULTS_HASH__\2",
                ),
                (
                    r"(?m)^    reactive_resume_dev_tls_renewal_task_self_hash:\s*'?[0-9a-f]{64}'?$",
                    "    reactive_resume_dev_tls_renewal_task_self_hash: __TASK_SELF_HASH__",
                ),
                (
                    r"(?m)^    reactive_resume_dev_tls_renewal_defaults_raw_hash:\s*'?[0-9a-f]{64}'?$",
                    "    reactive_resume_dev_tls_renewal_defaults_raw_hash: __DEFAULTS_RAW_HASH__",
                ),
            )
        else:
            # Defaults contain two explicit self references plus the two
            # execution-closure entries whose hashes would otherwise create a
            # cross-file cycle. No arbitrary 64-hex literal is normalized.
            replacements = (
                (
                    r"(?m)^reactive_resume_dev_tls_renewal_defaults_self_hash:\s+[0-9a-f]{64}$",
                    "reactive_resume_dev_tls_renewal_defaults_self_hash: __SELF_HASH__",
                ),
                (
                    r"(?m)^(    normalized_digest_name: reactive_resume_dev_tls_renewal_defaults_self_hash\n    sha256: )[0-9a-f]{64}$",
                    r"\1__SELF_HASH__",
                ),
                (
                    r"(?m)^(  - path: >-\n      .*reactive_resume_dev_tls_renewal_guarded_linear\.py\n    mode: '0644'\n    sha256: )[0-9a-f]{64}$",
                    r"\1__STRATEGY_HASH__",
                ),
                (
                    r"(?m)^(  - path: >-\n      .*ansible/bin/configure-reactive-resume-dev-tls-renewal\n    mode: '0755'\n    sha256: )[0-9a-f]{64}$",
                    r"\1__WRAPPER_HASH__",
                ),
            )
        for pattern, replacement in replacements:
            source, count = re.subn(pattern, replacement, source)
            if count != 1:
                return ""
        return hashlib.sha256(source.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _python_contract() -> bool:
    try:
        link = _PYTHON_SOURCE.lstat()
        target = _PYTHON_SOURCE.resolve(strict=True)
        target_state = _PYTHON_TARGET.stat()
        return (
            stat.S_ISLNK(link.st_mode)
            and link.st_uid == 0
            and link.st_gid == 0
            and target == _PYTHON_TARGET
            and stat.S_ISREG(target_state.st_mode)
            and target_state.st_uid == 0
            and target_state.st_gid == 0
            and stat.S_IMODE(target_state.st_mode) == 0o755
            and _sha256(_PYTHON_TARGET) == _PYTHON_SHA256
        )
    except OSError:
        return False


def _inventory_contract() -> bool:
    try:
        state = _INVENTORY_SOURCE.stat(follow_symlinks=False)
        content = _INVENTORY_SOURCE.read_bytes()
    except OSError:
        return False
    return (
        stat.S_ISREG(state.st_mode)
        and not _INVENTORY_SOURCE.is_symlink()
        and state.st_uid == os.getuid()
        and state.st_gid == os.getgid()
        and stat.S_IMODE(state.st_mode) == 0o600
        and hashlib.sha256(content).hexdigest() == _INVENTORY_SHA256
        and content == _INVENTORY_BYTES
    )


def _inventory_adjacency_contract() -> bool:
    """Reject auto-loaded inventory vars and unpinned vars-plugin trees."""
    candidates = (
        _INVENTORY_DIRECTORY / "group_vars",
        _INVENTORY_DIRECTORY / "host_vars",
        _INVENTORY_DIRECTORY / "vars_plugins",
        _REPOSITORY_ROOT / "ansible/inventory/group_vars",
        _REPOSITORY_ROOT / "ansible/inventory/host_vars",
        _REPOSITORY_ROOT / "ansible/inventory/vars_plugins",
        _REPOSITORY_ROOT / "ansible/playbooks/group_vars",
        _REPOSITORY_ROOT / "ansible/playbooks/host_vars",
        _REPOSITORY_ROOT / "ansible/playbooks/vars_plugins",
        _REPOSITORY_ROOT / "ansible/group_vars",
        _REPOSITORY_ROOT / "ansible/host_vars",
        _REPOSITORY_ROOT / "ansible/vars_plugins",
        _REPOSITORY_ROOT / "group_vars",
        _REPOSITORY_ROOT / "host_vars",
        _REPOSITORY_ROOT / "vars_plugins",
    )
    return all(not path.exists() and not path.is_symlink() for path in candidates)


def _source_closure_contract() -> bool:
    if not _file_contract(_PLAYBOOK, 0o644, _PLAYBOOK_SHA256):
        return False
    if _normalized_yaml_hash(_TASK_SOURCE, task=True) != _TASK_SHA256:
        return False
    if _normalized_yaml_hash(_DEFAULTS_SOURCE) != _DEFAULTS_SHA256:
        return False
    if not _file_contract(_MANIFEST_SOURCE, 0o644, _MANIFEST_SHA256):
        return False
    if _canonical_strategy_hash(_STRATEGY) != _STRATEGY_CANONICAL_SHA256:
        return False
    if _normalized_strategy_hash(_STRATEGY) != _STRATEGY_NORMALIZED_SHA256:
        return False
    if _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected") != _WRAPPER_CANONICAL_SHA256:
        return False
    if not _file_contract(_MUTATION_ACTION_SOURCE, 0o644, _MUTATION_ACTION_SHA256):
        return False
    if _sha256(_MUTATION_ACTION_SOURCE) != _MUTATION_ACTION_SHA256:
        return False
    if not _file_contract(_MUTATION_MODULE_SOURCE, 0o644, _MUTATION_MODULE_SHA256):
        return False
    if _sha256(_MUTATION_MODULE_SOURCE) != _MUTATION_MODULE_SHA256:
        return False
    if not _inventory_adjacency_contract():
        return False
    for relative, digest, mode in _SOURCE_HASHES:
        if not _file_contract(_SOURCE_ROOT / relative, mode, digest):
            return False
    return True


def _runtime_contract() -> bool:
    try:
        controller_first_line = _CONTROLLER.read_text(encoding="utf-8").splitlines()[0]
    except (IndexError, OSError, UnicodeError):
        return False
    return (
        _file_contract(_CONTROLLER, 0o755, _CONTROLLER_SHA256)
        and _python_contract()
        and _file_contract(_ANSIBLE_CONFIG, 0o644, _ANSIBLE_CONFIG_SHA256)
        and _source_closure_contract()
        and _inventory_contract()
        and controller_first_line == f"#!{_REPOSITORY_ROOT}/.venv/bin/python"
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG)
        and os.environ.get(_WRAPPER_ENV_PREFIX + "CONTROLLER_SHA256") == _CONTROLLER_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "PYTHON") == str(_PYTHON_SOURCE)
        and os.environ.get(_WRAPPER_ENV_PREFIX + "PYTHON_SHA256") == _PYTHON_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "ANSIBLE_CONFIG_SHA256") == _ANSIBLE_CONFIG_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "INVENTORY_SHA256") == _INVENTORY_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "PLAYBOOK_PATH") == str(_PLAYBOOK)
        and os.environ.get(_WRAPPER_ENV_PREFIX + "PLAYBOOK_SHA256") == _PLAYBOOK_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "TASK_SHA256") == _TASK_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "DEFAULTS_SHA256") == _DEFAULTS_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "MANIFEST_SHA256") == _MANIFEST_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "STRATEGY_PATH") == str(_STRATEGY)
        and os.environ.get(_WRAPPER_ENV_PREFIX + "STRATEGY_SHA256") == _sha256(_STRATEGY)
        and os.environ.get(_WRAPPER_ENV_PREFIX + "STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "STRATEGY_NORMALIZED_SHA256") == _STRATEGY_NORMALIZED_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "WRAPPER_CANONICAL_SHA256") == _WRAPPER_CANONICAL_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "STRATEGY_ATTESTATION_SHA256") == _STRATEGY_ATTESTATION_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "MUTATION_ACTION_PATH") == str(_MUTATION_ACTION_SOURCE)
        and os.environ.get(_WRAPPER_ENV_PREFIX + "MUTATION_ACTION_SHA256") == _MUTATION_ACTION_SHA256
        and os.environ.get(_WRAPPER_ENV_PREFIX + "MUTATION_MODULE_PATH") == str(_MUTATION_MODULE_SOURCE)
        and os.environ.get(_WRAPPER_ENV_PREFIX + "MUTATION_MODULE_SHA256") == _MUTATION_MODULE_SHA256
        and not any(name in os.environ for name in _FORBIDDEN_ENV)
    )


def _normalize_inventory_sources(value: object) -> list[str] | None:
    """Normalize ansible-core CLI/source containers without widening them."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)) and all(isinstance(source, str) for source in value):
        return list(value)
    return None


def _effective_host_vars_contract(variable_manager: object, inventory: object, play: object) -> bool:
    """Resolve effective host variables through Ansible's 2.19 lifecycle."""
    try:
        host = inventory.get_host("crtxweb")
        if host is None:
            return False
        values = variable_manager.get_vars(play=play, host=host)
        # InventoryManager._sources is the authoritative parser result in
        # ansible-core 2.19.  Do not let an inventory/host variable named
        # ansible_inventory_sources satisfy this boundary; compare it only as a
        # consistency check when the executor exposes the derived variable.
        inventory_sources = _normalize_inventory_sources(getattr(inventory, "_sources", None))
        if inventory_sources != [str(_INVENTORY_SOURCE)]:
            return False
        derived_sources = values.get("ansible_inventory_sources")
        if derived_sources is not None and _normalize_inventory_sources(derived_sources) != inventory_sources:
            return False
        connection = values.get("ansible_connection")
        remote_addr = values.get("ansible_host")
        if remote_addr is None:
            remote_addr = host.name
        remote_user = values.get("ansible_user")
        if remote_user is None:
            return False
        return (
            connection == "local"
            and remote_addr == "crtxweb"
            and remote_user == "paul"
            and values.get("ansible_python_interpreter") == "/usr/bin/python3"
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return False


def _effective_play_definition_contract(
    variable_manager: object | None,
    inventory: object | None,
    play: object | None,
) -> bool:
    """Bind privilege to the parsed Play definition, not initial PlayContext.

    ansible-core 2.19 invokes a strategy with an initial PlayContext whose
    privilege fields are unset.  The parsed play is authoritative for the
    requested privilege boundary; each mutation action separately verifies the
    task's effective PlayContext before it can run.
    """
    if variable_manager is None or inventory is None or play is None:
        return False
    if (
        type(getattr(play, "become", None)) is not bool
        or getattr(play, "become") is not True
        or getattr(play, "become_method", None) not in {"sudo", "ansible.builtin.sudo"}
        or getattr(play, "become_user", None) != _CANONICAL_BECOME_USER
        or getattr(play, "become_exe", None) != _CANONICAL_BECOME_EXE
        or getattr(play, "become_flags", None) != _CANONICAL_BECOME_FLAGS
    ):
        return False
    return _effective_host_vars_contract(variable_manager, inventory, play)


def _argv_payload() -> tuple[bool, dict[str, object] | None]:
    argv = sys.argv
    expected = [
        str(_CONTROLLER),
        "-i",
        str(_INVENTORY_SOURCE),
        str(_PLAYBOOK),
        "--diff",
        "--limit",
        "crtxweb",
        "--ask-become-pass",
        "--extra-vars",
    ]
    if len(argv) not in (len(expected) + 1, len(expected) + 2) or argv[: len(expected)] != expected:
        return False, None
    if len(argv) == len(expected) + 2 and argv[-1] != "--check":
        return False, None
    try:
        payload = json.loads(argv[len(expected)])
    except (IndexError, TypeError, ValueError):
        return False, None
    if not isinstance(payload, dict) or set(payload) != {
        "reactive_resume_dev_tls_renewal_approved",
        "reactive_resume_dev_tls_renewal_mode",
        "reactive_resume_dev_tls_renewal_repository_root",
    }:
        return False, None
    if payload.get("reactive_resume_dev_tls_renewal_approved") is not True:
        return False, None
    if payload.get("reactive_resume_dev_tls_renewal_mode") not in {"install", "enable"}:
        return False, None
    if payload.get("reactive_resume_dev_tls_renewal_repository_root") != str(_REPOSITORY_ROOT):
        return False, None
    return True, payload


def _canonical_argv() -> bool:
    return _argv_payload()[0]


def _proc_starttime(pid: int) -> str:
    try:
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


def _is_ancestor(pid: int) -> bool:
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
        return [part.decode("utf-8", "strict") for part in raw[:-1].split(b"\0")]
    except (OSError, UnicodeError):
        return []


def _wrapper_binding_valid() -> bool:
    prefix = _WRAPPER_ENV_PREFIX
    ok, payload = _argv_payload()
    if not ok or payload is None:
        return False
    token = os.environ.get(prefix + "TOKEN", "")
    pid_text = os.environ.get(prefix + "WRAPPER_PID", "")
    starttime = os.environ.get(prefix + "WRAPPER_STARTTIME", "")
    wrapper_path = os.environ.get(prefix + "WRAPPER_PATH", "")
    attestation_path = os.environ.get(prefix + "ATTESTATION_FILE", "")
    wrapper_sha = os.environ.get(prefix + "WRAPPER_SHA256", "")
    wrapper_canonical_sha = os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256", "")
    try:
        pid = int(pid_text)
        attestation = os.stat(attestation_path, follow_symlinks=False)
        content = Path(attestation_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return False
    mode = str(payload["reactive_resume_dev_tls_renewal_mode"])
    invocation = "enable-check" if mode == "enable" and len(sys.argv) > 10 else "enable-apply"
    if mode == "install":
        invocation = "check" if len(sys.argv) > 10 else "apply"
    expected_cmdline = ["/bin/dash", str(_WRAPPER_SOURCE), invocation]
    return (
        os.environ.get(prefix + "ENTRYPOINT") == "v2"
        and re.fullmatch(r"[0-9a-f]{64}", token) is not None
        and pid > 1
        and _is_ancestor(pid)
        and _proc_starttime(pid) == starttime
        and _proc_cmdline(pid) == expected_cmdline
        and Path(wrapper_path) == _WRAPPER_SOURCE
        and stat.S_ISREG(attestation.st_mode)
        and not stat.S_ISLNK(attestation.st_mode)
        and attestation.st_uid == os.getuid()
        and attestation.st_gid == os.getgid()
        and stat.S_IMODE(attestation.st_mode) == 0o600
        and attestation.st_nlink == 1
        and wrapper_sha == _sha256(_WRAPPER_SOURCE)
        and wrapper_canonical_sha == _canonical_file_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256_expected")
        and content == f"{token}:{pid}:{starttime}:{_WRAPPER_SOURCE}:{wrapper_sha}:{invocation}\n"
        and os.environ.get(prefix + "CONTROLLER") == str(_CONTROLLER)
        and os.environ.get(prefix + "PYTHON") == "/usr/bin/python3"
        and os.environ.get(prefix + "ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG)
        and os.environ.get(prefix + "TASK_SHA256") == _TASK_SHA256
        and os.environ.get(prefix + "PLAYBOOK_SHA256") == _PLAYBOOK_SHA256
        and os.environ.get(prefix + "STRATEGY_SHA256") == _sha256(_STRATEGY)
        and os.environ.get(prefix + "STRATEGY_NORMALIZED_SHA256") == _STRATEGY_NORMALIZED_SHA256
        and os.environ.get(prefix + "STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256
        and os.environ.get(prefix + "WRAPPER_CANONICAL_SHA256") == _WRAPPER_CANONICAL_SHA256
        and os.environ.get(prefix + "STRATEGY_ATTESTATION_SHA256") == _STRATEGY_ATTESTATION_SHA256
        and bool(context.CLIARGS.get("check")) == (invocation.endswith("-check") or invocation == "check")
    )


def _selection_guard() -> bool:
    tags = list(context.CLIARGS.get("tags") or [])
    skip_tags = list(context.CLIARGS.get("skip_tags") or [])
    selection_options = ("--start-at-task", "--step", "--tags", "--skip-tags")
    selection_argv = any(
        argument == "-t"
        or argument.startswith("-t=")
        or (argument.startswith("-t") and len(argument) > 2)
        or (
            argument.startswith("--")
            and any(option.startswith(argument.split("=", 1)[0]) for option in selection_options)
        )
        for argument in sys.argv[1:]
    )
    inventory = _normalize_inventory_sources(context.CLIARGS.get("inventory") or [])
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
    """Reject selection, source, and wrapper drift before task iteration."""

    def run(self, iterator, play_context):  # type: ignore[no-untyped-def]
        if not _selection_guard():
            raise AnsibleError("TASK_SELECTION_GUARD: TLS renewal requires the complete guarded play")
        if not (
            _canonical_argv()
            and _wrapper_binding_valid()
            and _runtime_contract()
            and _effective_play_definition_contract(
                getattr(self, "_variable_manager", None),
                getattr(self, "_inventory", None),
                getattr(iterator, "_play", None),
            )
        ):
            raise AnsibleError("ENTRYPOINT_GUARD: TLS renewal requires the complete guarded wrapper invocation")
        # ansible-core 2.19 intentionally does not expose become settings as
        # task variables.  Publish only the values already proven through the
        # real VariableManager/InventoryManager/Play lifecycle so the role's
        # first task can bind the same effective context without guessing.
        os.environ[_WRAPPER_ENV_PREFIX + "EFFECTIVE_BECOME"] = "true"
        os.environ[_WRAPPER_ENV_PREFIX + "EFFECTIVE_BECOME_METHOD"] = "sudo"
        os.environ[_WRAPPER_ENV_PREFIX + "EFFECTIVE_BECOME_USER"] = "root"
        os.environ[_WRAPPER_ENV_PREFIX + "EFFECTIVE_BECOME_EXE"] = _CANONICAL_BECOME_EXE
        os.environ[_WRAPPER_ENV_PREFIX + "EFFECTIVE_BECOME_FLAGS"] = _CANONICAL_BECOME_FLAGS
        os.environ[_WRAPPER_ENV_PREFIX + "MUTATION_ACTION_PATH"] = str(_MUTATION_ACTION_SOURCE)
        os.environ[_WRAPPER_ENV_PREFIX + "MUTATION_ACTION_SHA256"] = _MUTATION_ACTION_SHA256
        os.environ[_WRAPPER_ENV_PREFIX + "MUTATION_MODULE_PATH"] = str(_MUTATION_MODULE_SOURCE)
        os.environ[_WRAPPER_ENV_PREFIX + "MUTATION_MODULE_SHA256"] = _MUTATION_MODULE_SHA256
        os.environ[_WRAPPER_ENV_PREFIX + "STRATEGY_ATTESTED"] = "v1"
        os.environ[_WRAPPER_ENV_PREFIX + "STRATEGY_PATH"] = str(_STRATEGY)
        os.environ[_WRAPPER_ENV_PREFIX + "STRATEGY_CANONICAL_SHA256"] = _STRATEGY_CANONICAL_SHA256
        return super().run(iterator, play_context)
