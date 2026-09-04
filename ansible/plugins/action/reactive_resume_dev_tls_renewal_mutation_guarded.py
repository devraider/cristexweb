from __future__ import annotations

import hashlib
import json
import grp
import os
import pwd
import re
import stat
import sys
from pathlib import Path
from typing import Any

from ansible import context
from ansible.plugins.action import ActionBase


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_EXPECTED_ACTION = "reactive_resume_dev_tls_renewal_mutation_guarded"
_EXPECTED_TASK_NAME = "Bind exact TLS renewal mutation privilege context"
_EXPECTED_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/reactive_resume_dev_tls_renewal/tasks/main.yml"
_ACTION_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/configure-reactive-resume-dev-tls-renewal"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_INVENTORY_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/inventory.local.yml"
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/configure_reactive_resume_dev_tls_renewal.yml"
_STRATEGY_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/strategy/reactive_resume_dev_tls_renewal_guarded_linear.py"
_ENV_PREFIX = "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_"
_INTERNAL_PREFIX = "reactive_resume_dev_tls_renewal_internal_"
# The strategy-attestation digest is a fixed, reviewed marker. Other source
# digests are derived from the files below at action time, avoiding a second
# cross-file hash cycle in this loader-side guard.
_STRATEGY_ATTESTATION_SHA256 = "aa8ef9124552f3d1a1f65d7fdbeb2ec37bc28f84f1a77e8fffdf3f636a9c6dbb"
_CANONICAL_BECOME_METHOD = "sudo"
_CANONICAL_BECOME_USER = "root"
_CANONICAL_BECOME_EXE = "sudo"
_CANONICAL_BECOME_FLAGS = "-H -S -n"
_TASK_PATH_SUFFIX = re.compile(r":(?P<line>[1-9][0-9]*)(?::(?P<column>[1-9][0-9]*))?\Z")

_SOURCE_OWNERSHIP = (
    (_REPOSITORY_ROOT / "ansible/bin/configure-reactive-resume-dev-tls-renewal", 0o755),
    (_REPOSITORY_ROOT / "ansible/playbooks/configure_reactive_resume_dev_tls_renewal.yml", 0o644),
    (_REPOSITORY_ROOT / "ansible/roles/reactive_resume_dev_tls_renewal/tasks/main.yml", 0o644),
    (_REPOSITORY_ROOT / "ansible/roles/reactive_resume_dev_tls_renewal/defaults/main.yml", 0o644),
    (_REPOSITORY_ROOT / "ansible/plugins/strategy/reactive_resume_dev_tls_renewal_guarded_linear.py", 0o644),
    (_REPOSITORY_ROOT / "ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py", 0o644),
    (_REPOSITORY_ROOT / "ansible/library/reactive_resume_dev_tls_renewal_mutation_guarded.py", 0o644),
    (_REPOSITORY_ROOT / "ansible/ansible.cfg", 0o644),
    (_REPOSITORY_ROOT / "ansible/files/components/reactive-resume-dev-tls/MANIFESTS.sha256", 0o644),
    (_REPOSITORY_ROOT / "ansible/files/components/reactive-resume-dev-tls/renewal/validate-reactive-resume-dev-tls-material", 0o755),
    (_REPOSITORY_ROOT / "ansible/files/components/reactive-resume-dev-tls/renewal/reactive-resume-dev-tls-renew", 0o755),
    (_REPOSITORY_ROOT / "ansible/files/components/reactive-resume-dev-tls/renewal/cristexweb-reactive-resume-dev-tls-renew.service", 0o644),
    (_REPOSITORY_ROOT / "ansible/files/components/reactive-resume-dev-tls/renewal/cristexweb-reactive-resume-dev-tls-renew.timer", 0o644),
)

# Every host-mutating task in the role is dispatched through this action.  A
# task-selection control therefore reaches this guard even when Ansible's
# default linear strategy (rather than the guarded strategy) is in use.
_MUTATION_TASKS = {
    "Install exact renewal dependencies": (
        "ansible.builtin.apt",
        frozenset({"name", "state", "update_cache"}),
    ),
    "Create protected renewal directories during install mode": (
        "ansible.builtin.file",
        frozenset({"path", "state", "owner", "group", "mode"}),
    ),
    "Install the value-free TLS validator during install mode": (
        "ansible.builtin.copy",
        frozenset({"src", "dest", "owner", "group", "mode"}),
    ),
    "Install the guarded renewal executable during install mode": (
        "ansible.builtin.copy",
        frozenset({"src", "dest", "owner", "group", "mode"}),
    ),
    "Install the renewal service unit during install mode": (
        "ansible.builtin.copy",
        frozenset({"src", "dest", "owner", "group", "mode"}),
    ),
    "Install the renewal timer unit during install mode": (
        "ansible.builtin.copy",
        frozenset({"src", "dest", "owner", "group", "mode"}),
    ),
    "Reload systemd after install-mode renewal unit changes": (
        "ansible.builtin.systemd_service",
        frozenset({"daemon_reload"}),
    ),
    "Keep renewal timer disabled during install mode": (
        "ansible.builtin.systemd_service",
        frozenset({"name", "enabled", "state"}),
    ),
    "Enable and start the guarded renewal timer": (
        "ansible.builtin.systemd_service",
        frozenset({"name", "enabled", "state"}),
    ),
}


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _source_ownership_contract() -> bool:
    """Require every reviewed source leaf to be paul:paul and exact mode."""
    try:
        owner_uid = pwd.getpwnam("paul").pw_uid
        group_gid = grp.getgrnam("paul").gr_gid
    except KeyError:
        return False
    for path, mode in _SOURCE_OWNERSHIP:
        try:
            state = path.stat(follow_symlinks=False)
        except OSError:
            return False
        if (
            not stat.S_ISREG(state.st_mode)
            or path.is_symlink()
            or state.st_uid != owner_uid
            or state.st_gid != group_gid
            or stat.S_IMODE(state.st_mode) != mode
        ):
            return False
    return True


def _canonical_file_hash(path: Path) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            r"(?m)^wrapper_canonical_sha256_expected='[0-9a-f]{64}'$",
            "wrapper_canonical_sha256_expected='" + ("0" * 64) + "'",
            source,
        )
        if count != 1:
            return ""
        return hashlib.sha256(source.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _normalized_yaml_hash(path: Path, *, task: bool = False) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        if task:
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


def _strategy_hash(path: Path, *, normalized: bool) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        markers = (
            ("_STRATEGY_CANONICAL_SHA256", "__STRATEGY_CANONICAL_HASH__" if normalized else "__PIN__"),
            ("_STRATEGY_NORMALIZED_SHA256", "__STRATEGY_NORMALIZED_HASH__" if normalized else "__PIN__"),
            ("_WRAPPER_CANONICAL_SHA256", "__WRAPPER_CANONICAL_HASH__" if normalized else "__PIN__"),
        )
        for symbol, marker in markers:
            source, count = re.subn(
                rf"(?m)^({re.escape(symbol)}\s*=\s*[\"\'])[0-9a-f]{{64}}([\"\']\s*)$",
                rf"\g<1>{marker}\g<2>",
                source,
            )
            if count != 1:
                return ""
        return hashlib.sha256(source.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError):
        return ""


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


def _normalize_inventory_sources(value: object) -> list[str] | None:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)) and all(isinstance(source, str) for source in value):
        return list(value)
    return None


def _canonical_argv() -> tuple[bool, str]:
    argv = sys.argv
    expected = [
        str(_CONTROLLER_SOURCE),
        "-i",
        str(_INVENTORY_SOURCE),
        str(_PLAYBOOK_SOURCE),
        "--diff",
        "--limit",
        "crtxweb",
        "--ask-become-pass",
        "--extra-vars",
    ]
    if len(argv) not in (len(expected) + 1, len(expected) + 2) or argv[: len(expected)] != expected:
        return False, ""
    if len(argv) == len(expected) + 2 and argv[-1] != "--check":
        return False, ""
    try:
        payload = json.loads(argv[len(expected)])
    except (IndexError, TypeError, ValueError):
        return False, ""
    if not isinstance(payload, dict) or set(payload) != {
        "reactive_resume_dev_tls_renewal_approved",
        "reactive_resume_dev_tls_renewal_mode",
        "reactive_resume_dev_tls_renewal_repository_root",
    }:
        return False, ""
    if payload.get("reactive_resume_dev_tls_renewal_approved") is not True:
        return False, ""
    if payload.get("reactive_resume_dev_tls_renewal_mode") not in {"install", "enable"}:
        return False, ""
    if payload.get("reactive_resume_dev_tls_renewal_repository_root") != str(_REPOSITORY_ROOT):
        return False, ""
    mode = str(payload["reactive_resume_dev_tls_renewal_mode"])
    check = len(argv) == len(expected) + 2
    return True, ("enable-check" if mode == "enable" and check else
                  "enable-apply" if mode == "enable" else
                  "check" if check else "apply")


def _selection_is_canonical() -> bool:
    """Reject every task-selection control and require the wrapper CLI shape."""
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
    return (
        not selection_argv
        and context.CLIARGS.get("start_at_task") is None
        and not context.CLIARGS.get("step")
        and tags in ([], ["all"])
        and not skip_tags
        and context.CLIARGS.get("subset") == "crtxweb"
        and context.CLIARGS.get("diff") is True
        and inventory == [str(_INVENTORY_SOURCE)]
        and bool(context.CLIARGS.get("check")) == (len(sys.argv) > 10)
    )


def _wrapper_binding_valid() -> bool:
    prefix = _ENV_PREFIX
    ok, invocation = _canonical_argv()
    if not ok or not _selection_is_canonical():
        return False
    token = os.environ.get(prefix + "TOKEN", "")
    pid_text = os.environ.get(prefix + "WRAPPER_PID", "")
    starttime = os.environ.get(prefix + "WRAPPER_STARTTIME", "")
    wrapper_path = os.environ.get(prefix + "WRAPPER_PATH", "")
    attestation_path = os.environ.get(prefix + "ATTESTATION_FILE", "")
    wrapper_sha = os.environ.get(prefix + "WRAPPER_SHA256", "")
    try:
        pid = int(pid_text)
        attestation = os.stat(attestation_path, follow_symlinks=False)
        content = Path(attestation_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return False
    expected_env = {
        "ENTRYPOINT": "v2",
        "CONTROLLER": str(_CONTROLLER_SOURCE),
        "PYTHON": "/usr/bin/python3",
        "ANSIBLE_CONFIG": str(_ANSIBLE_CONFIG_SOURCE),
        "PLAYBOOK_PATH": str(_PLAYBOOK_SOURCE),
        "PLAYBOOK_SHA256": _sha256(_PLAYBOOK_SOURCE),
        "TASK_SHA256": _normalized_yaml_hash(_REPOSITORY_ROOT / "ansible/roles/reactive_resume_dev_tls_renewal/tasks/main.yml", task=True),
        "DEFAULTS_SHA256": _normalized_yaml_hash(_REPOSITORY_ROOT / "ansible/roles/reactive_resume_dev_tls_renewal/defaults/main.yml"),
        "STRATEGY_SHA256": _sha256(_STRATEGY_SOURCE),
        "STRATEGY_NORMALIZED_SHA256": _strategy_hash(_STRATEGY_SOURCE, normalized=True),
        "STRATEGY_CANONICAL_SHA256": _strategy_hash(_STRATEGY_SOURCE, normalized=False),
        "WRAPPER_CANONICAL_SHA256": _canonical_file_hash(_WRAPPER_SOURCE),
        "STRATEGY_ATTESTATION_SHA256": _STRATEGY_ATTESTATION_SHA256,
        "CONTROLLER_SHA256": _sha256(_CONTROLLER_SOURCE),
    }
    expected_cmdline = ["/bin/dash", str(_WRAPPER_SOURCE), invocation]
    return (
        re.fullmatch(r"[0-9a-f]{64}", token) is not None
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
        and _canonical_file_hash(_WRAPPER_SOURCE) == _WRAPPER_CANONICAL_SHA256
        and content == f"{token}:{pid}:{starttime}:{_WRAPPER_SOURCE}:{wrapper_sha}:{invocation}\\n"
        and all(os.environ.get(prefix + key) == value for key, value in expected_env.items())
        and os.environ.get(prefix + "INVENTORY_SHA256") == _sha256(_INVENTORY_SOURCE)
        and os.environ.get(prefix + "ANSIBLE_CONFIG_SHA256") == _sha256(_ANSIBLE_CONFIG_SOURCE)
        and os.environ.get(prefix + "MUTATION_ACTION_PATH") == str(_ACTION_SOURCE)
        and os.environ.get(prefix + "MUTATION_ACTION_SHA256") == _sha256(_ACTION_SOURCE)
        and os.environ.get(prefix + "MUTATION_MODULE_PATH")
        == str(_REPOSITORY_ROOT / "ansible/library/reactive_resume_dev_tls_renewal_mutation_guarded.py")
        and os.environ.get(prefix + "MUTATION_MODULE_SHA256") == _sha256(
            _REPOSITORY_ROOT / "ansible/library/reactive_resume_dev_tls_renewal_mutation_guarded.py"
        )
    )


def _source_contract() -> bool:
    """Bind this plugin to the wrapper's raw source closure before use."""
    try:
        loaded = Path(__file__).resolve(strict=True)
        state = _ACTION_SOURCE.stat(follow_symlinks=False)
    except (OSError, RuntimeError):
        return False
    expected = os.environ.get(_ENV_PREFIX + "MUTATION_ACTION_SHA256", "")
    return (
        loaded == _ACTION_SOURCE
        and stat.S_ISREG(state.st_mode)
        and not _ACTION_SOURCE.is_symlink()
        and state.st_uid == os.getuid()
        and state.st_gid == os.getgid()
        and stat.S_IMODE(state.st_mode) == 0o644
        and re.fullmatch(r"[0-9a-f]{64}", expected) is not None
        and _sha256(_ACTION_SOURCE) == expected
        and os.environ.get(_ENV_PREFIX + "MUTATION_ACTION_PATH") == str(_ACTION_SOURCE)
        and os.environ.get(_ENV_PREFIX + "STRATEGY_ATTESTED") == "v1"
        and _source_ownership_contract()
    )


def _fail(message: str) -> dict[str, Any]:
    return {"changed": False, "failed": True, "msg": message}


def _effective_privilege(play_context: object) -> bool:
    """Require Ansible's resolved per-task sudo context exactly.

    ansible-core 2.19 resolves the pinned sudo declaration to executable
    ``sudo`` and flags ``-H -S -n`` before invoking an action plugin.  Empty or
    alternate values are rejected rather than treated as implicit defaults.
    """
    return (
        type(getattr(play_context, "become", None)) is bool
        and getattr(play_context, "become") is True
        and getattr(play_context, "become_method", None) in {_CANONICAL_BECOME_METHOD, "ansible.builtin.sudo"}
        and getattr(play_context, "become_user", None) == _CANONICAL_BECOME_USER
        and getattr(play_context, "become_exe", None) == _CANONICAL_BECOME_EXE
        and getattr(play_context, "become_flags", None) == _CANONICAL_BECOME_FLAGS
    )




def _task_source(task: object) -> str:
    """Return only the exact role source from Ansible's ``path:line[:column]``.

    ``Task.get_path()`` reports an absolute source path followed by the
    one-based origin line, and some Ansible versions also include a column.
    Keep the path lexical and exact: resolving arbitrary paths would accept a
    symlink or alternate spelling of the reviewed task file.  A malformed
    suffix, relative path, or any other source is rejected before filesystem
    access.
    """
    try:
        raw = task.get_path()
    except (AttributeError, TypeError):
        return ""
    if not isinstance(raw, str) or not raw or any(char in raw for char in "\x00\r\n"):
        return ""
    expected = str(_EXPECTED_TASK_SOURCE)
    if not raw.startswith(expected):
        return ""
    suffix = raw[len(expected) :]
    if _TASK_PATH_SUFFIX.fullmatch(suffix) is None:
        return ""
    return expected


def _common_guard(action: object, task: object, task_vars: dict[str, Any]) -> str | None:
    """Validate wrapper/source/selection/context before any delegated module."""
    if not _selection_is_canonical():
        return "TASK_SELECTION_GUARD: TLS mutation requires the complete guarded play"
    if _task_source(task) != str(_EXPECTED_TASK_SOURCE):
        return "ENTRYPOINT_GUARD: TLS mutation task source is not the reviewed role"
    if getattr(task, "action", None) != _EXPECTED_ACTION:
        return "ENTRYPOINT_GUARD: TLS mutation action identity is not canonical"
    if not _source_contract() or not _wrapper_binding_valid():
        return "ENTRYPOINT_GUARD: TLS mutation requires the complete guarded wrapper invocation"
    if (
        os.environ.get(_ENV_PREFIX + "EFFECTIVE_BECOME") != "true"
        or os.environ.get(_ENV_PREFIX + "EFFECTIVE_BECOME_METHOD") != "sudo"
        or os.environ.get(_ENV_PREFIX + "EFFECTIVE_BECOME_USER") != _CANONICAL_BECOME_USER
        or os.environ.get(_ENV_PREFIX + "EFFECTIVE_BECOME_EXE") != _CANONICAL_BECOME_EXE
        or os.environ.get(_ENV_PREFIX + "EFFECTIVE_BECOME_FLAGS") != _CANONICAL_BECOME_FLAGS
        or not _effective_privilege(getattr(action, "_play_context", None))
    ):
        return "ENTRYPOINT_GUARD: TLS mutation privilege context is not the exact guarded PlayContext"
    if task_vars.get("reactive_resume_dev_tls_renewal_internal_mutation_privilege_attested") is not True:
        return "ENTRYPOINT_GUARD: TLS mutation first-task attestation is absent"
    return None


class ActionModule(ActionBase):
    """Guard the first task and every host-mutating task in the role.

    Native modules are delegated only after the wrapper ancestry, exact source,
    task-selection, and effective sudo checks pass.  This is deliberately
    repeated per mutation so ``--start-at-task`` cannot skip the first guard.
    """

    TRANSFERS_FILES = False

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = super().run(tmp, task_vars)
        task_vars = task_vars or {}
        task = self._task
        task_name = getattr(task, "name", None)
        args = getattr(task, "args", None)
        # The first task is a no-op attestation.  Its exact empty argument set
        # prevents it from being repurposed as a delegated native operation.
        # A direct role invocation must report an entrypoint failure rather than
        # allowing a selection error to obscure the missing wrapper binding.
        if task_name == _EXPECTED_TASK_NAME:
            if not _selection_is_canonical():
                return _fail("ENTRYPOINT_GUARD: TLS mutation requires the complete guarded wrapper invocation")
            if (
                args != {}
                or getattr(task, "action", None) != _EXPECTED_ACTION
                or _task_source(task) != str(_EXPECTED_TASK_SOURCE)
                or any(
                    isinstance(key, str) and key.startswith(_INTERNAL_PREFIX)
                    for key in task_vars
                )
                or not _source_contract()
                or not _wrapper_binding_valid()
                or os.environ.get(_ENV_PREFIX + "EFFECTIVE_BECOME") != "true"
                or os.environ.get(_ENV_PREFIX + "EFFECTIVE_BECOME_METHOD") != "sudo"
                or os.environ.get(_ENV_PREFIX + "EFFECTIVE_BECOME_USER") != _CANONICAL_BECOME_USER
                or os.environ.get(_ENV_PREFIX + "EFFECTIVE_BECOME_EXE") != _CANONICAL_BECOME_EXE
                or os.environ.get(_ENV_PREFIX + "EFFECTIVE_BECOME_FLAGS") != _CANONICAL_BECOME_FLAGS
                or not _effective_privilege(self._play_context)
            ):
                return _fail("ENTRYPOINT_GUARD: TLS mutation privilege context is not the exact guarded PlayContext")
            result.update(
                changed=False,
                ansible_facts={
                    "reactive_resume_dev_tls_renewal_internal_mutation_privilege_attestation": {
                        "schema": 1,
                        "become": True,
                        "become_method": _CANONICAL_BECOME_METHOD,
                        "become_user": _CANONICAL_BECOME_USER,
                        "become_exe": _CANONICAL_BECOME_EXE,
                        "become_flags": _CANONICAL_BECOME_FLAGS,
                        "action": _EXPECTED_ACTION,
                    }
                },
            )
            return result
        if not _selection_is_canonical():
            return _fail("TASK_SELECTION_GUARD: TLS mutation requires the complete guarded play")
        mutation = _MUTATION_TASKS.get(task_name)
        if mutation is None:
            return _fail("ENTRYPOINT_GUARD: unknown TLS mutation task")
        failure = _common_guard(self, task, task_vars)
        if failure is not None:
            return _fail(failure)
        if not isinstance(args, dict) or set(args) != {"module", "module_args"}:
            return _fail("MUTATION_ARGUMENT_GUARD: TLS mutation module arguments are not canonical")
        module_name, allowed_args = mutation
        if args.get("module") != module_name or not isinstance(args.get("module_args"), dict):
            return _fail("MUTATION_ARGUMENT_GUARD: TLS mutation module is not allowlisted")
        module_args = args["module_args"]
        if set(module_args) != set(allowed_args):
            return _fail("MUTATION_ARGUMENT_GUARD: TLS mutation argument keys are not allowlisted")
        try:
            module_args = self._templar.template(module_args, variables=task_vars, fail_on_undefined=True)
        except (AttributeError, TypeError, ValueError):
            return _fail("MUTATION_ARGUMENT_GUARD: TLS mutation arguments could not be resolved")
        if not isinstance(module_args, dict):
            return _fail("MUTATION_ARGUMENT_GUARD: TLS mutation arguments are not a mapping")
        original_action, original_args = self._task.action, self._task.args
        self._task.action, self._task.args = module_name, module_args
        try:
            plugin_args = {
                "task": self._task,
                "connection": self._connection,
                "play_context": self._play_context,
                "loader": self._loader,
                "templar": self._templar,
                "shared_loader_obj": self._shared_loader_obj,
            }
            plugin = self._shared_loader_obj.action_loader.get(module_name, **plugin_args)
            if plugin is None:
                plugin = self._shared_loader_obj.action_loader.get(
                    "ansible.builtin.normal", **plugin_args
                )
            if plugin is None:
                return _fail("ENTRYPOINT_GUARD: unable to load the allowlisted TLS mutation module")
            delegated = plugin.run(tmp=tmp, task_vars=task_vars)
            delegated.setdefault("changed", False)
            return delegated
        finally:
            self._task.action, self._task.args = original_action, original_args
