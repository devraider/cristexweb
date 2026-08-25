from __future__ import annotations

import hashlib
import os
import re
import shlex
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible.plugins.action import ActionBase

_SCRIPT_NAME = "reactive-resume-dev-successor-check.sh"
_SCRIPT_HASH = "f1891dc507d411d0c3bc91793c51cb640cc0ca8f71d7cd42f066a30ad7dbab66"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_MANIFEST_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/reactive-resume-dev-successor/MANIFESTS.sha256"
_MANIFEST_HASH = "f02b444f16a5444cc3b4dba56cbcf4e9e94c72f6021e32375a2504afd3d5cce1"
_MANIFEST_ENTRIES = {
    "source/admission-rbac.yaml": "e38c6d6e531e78013c74994006beaa50fea7195774e60e96379811bd47a7cb3f",
    "source/migration-static-secret.yaml": "587404c0f41e7920a6eb742c713e45b867c638e1b4ff1e306145ad7a281bfbdd",
    "source/runtime-static-secret.yaml": "e8b11b97146c98ed4a95e46009385b4883b2f533ffe50ea02b44415bf568177a",
}
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/reactive_resume_dev_successor/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/reactive_resume_dev_successor/defaults/main.yml"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/check_reactive_resume_dev_successor.yml"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/check-reactive-resume-dev-successor"
_POLICY_SOURCE = _REPOSITORY_ROOT / "ansible/files/policies/reactive-resume-dev-postgresql-successor.yml"
_TASK_HASH = "585ab7c7d813fc6dedd2cc6cc3880b7191179057d66aa812617faaf070afb5fa"
_DEFAULTS_HASH = "a31d4646169f72c68c41186b83a2da422fcce1cd270a69e21e4a8471bc170d2b"
_PLAYBOOK_HASH = "98c4ecc22ea6387d5c9f63ec3359573893223d93f562bf0e53de2a5a18d9c089"
_WRAPPER_HASH = "c8a7f69b803d99152d555905d9a32e2e66b479a1d2b145c411400b8bdd0ac3e2"
_POLICY_HASH = "7bcd206f32db6f7a182feb618fd5595726e7cb4c63e1d34fe2641303ee7983a4"
_ACTION_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/action/reactive_resume_dev_successor_guarded.py"
_CLOSURE_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/reactive-resume-dev-successor/SOURCE-CLOSURE.sha256"
_ACTION_CANONICAL_HASH = "2c01d1fe73d115d05dda72fc4219d61a4516df3ab686b707af1cc2c83c32905b"
_CLOSURE_MANIFEST_HASH = "043e29ed210afd1e7381979792a0c11f68bfc3007e415b934906e4e4e21b29f9"
_CLOSURE_ENTRIES = {
    "ansible/ansible.cfg": "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9",
    "ansible/library/reactive_resume_dev_secret_metadata.py": "6762f3b7830a6c01977238fca7c3397b08702c3c9b303712cf050df9c85b02c7",
}
_CLOSURE_ACTION_PATH = "ansible/plugins/action/reactive_resume_dev_successor_guarded.py"
_ARGUMENT_KEYS = {"namespace", "pod", "container", "command", "kubeconfig", "script_name", "script_sha256"}


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _canonical_sha256(path: Path) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        for symbol in ("_ACTION_CANONICAL_HASH", "_CLOSURE_MANIFEST_HASH", "_WRAPPER_HASH"):
            source, count = re.subn(
                rf'(?m)^({re.escape(symbol)}\s*=\s*")[0-9a-f]{{64}}("\s*)$',
                rf'\g<1>{"0" * 64}\g<2>',
                source,
            )
            if count != 1:
                return ""
        return hashlib.sha256(source.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _source_closure() -> bool:
    if not _CLOSURE_SOURCE.is_file() or _CLOSURE_SOURCE.is_symlink():
        return False
    try:
        if stat.S_IMODE(_CLOSURE_SOURCE.stat().st_mode) != 0o644:
            return False
        if _sha256(_CLOSURE_SOURCE) != _CLOSURE_MANIFEST_HASH:
            return False
        lines = _CLOSURE_SOURCE.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return False
    expected_lines = [
        *(f"{digest}  {path}" for path, digest in _CLOSURE_ENTRIES.items()),
        f"{_ACTION_CANONICAL_HASH}  {_CLOSURE_ACTION_PATH}",
    ]
    if lines != expected_lines:
        return False
    for relative, digest in _CLOSURE_ENTRIES.items():
        leaf = _REPOSITORY_ROOT / relative
        if not leaf.is_file() or leaf.is_symlink():
            return False
        try:
            if stat.S_IMODE(leaf.stat().st_mode) != 0o644 or _sha256(leaf) != digest:
                return False
        except OSError:
            return False
    if not _ACTION_SOURCE.is_file() or _ACTION_SOURCE.is_symlink():
        return False
    try:
        return (
            stat.S_IMODE(_ACTION_SOURCE.stat().st_mode) == 0o644
            and _canonical_sha256(_ACTION_SOURCE) == _ACTION_CANONICAL_HASH
        )
    except OSError:
        return False


def _ancestor(pid: int) -> bool:
    current = os.getpid()
    seen: set[int] = set()
    while current > 1 and current not in seen:
        if current == pid:
            return True
        seen.add(current)
        try:
            status = Path(f"/proc/{current}/status").read_text()
            current = int(next(x for x in status.splitlines() if x.startswith("PPid:")).split()[1])
        except (OSError, StopIteration, ValueError):
            return False
    return False


def _selected() -> bool:
    tags = list(context.CLIARGS.get("tags") or [])
    inventory = context.CLIARGS.get("inventory") or []
    if isinstance(inventory, str):
        inventory = [inventory]
    return (
        not context.CLIARGS.get("start_at_task")
        and not context.CLIARGS.get("step")
        and tags in ([], ["all"])
        and not context.CLIARGS.get("skip_tags")
        and context.CLIARGS.get("subset") == "crtxweb"
        and bool(context.CLIARGS.get("diff"))
        and any(str(item).endswith(".ansible/inventory.local.yml") for item in inventory)
    )


def _reject(message: str) -> dict[str, Any]:
    return {"changed": False, "failed": True, "msg": message}


def _manifest_closure() -> bool:
    if not _MANIFEST_SOURCE.is_file() or _MANIFEST_SOURCE.is_symlink():
        return False
    try:
        if stat.S_IMODE(_MANIFEST_SOURCE.stat().st_mode) != 0o644:
            return False
        if _sha256(_MANIFEST_SOURCE) != _MANIFEST_HASH:
            return False
        lines = _MANIFEST_SOURCE.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return False
    expected_lines = [f"{digest}  {path}" for path, digest in _MANIFEST_ENTRIES.items()]
    if lines != expected_lines:
        return False
    for relative, digest in _MANIFEST_ENTRIES.items():
        leaf = _REPOSITORY_ROOT / "ansible/files/components/reactive-resume-dev-successor" / relative
        if not leaf.is_file() or leaf.is_symlink():
            return False
        try:
            if stat.S_IMODE(leaf.stat().st_mode) != 0o644 or _sha256(leaf) != digest:
                return False
        except OSError:
            return False
    return True


class ActionModule(ActionBase):
    """Run only the hash-bound, read-only successor catalog check."""

    TRANSFERS_FILES = False

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        result = super().run(tmp=tmp, task_vars=task_vars)
        args = self._task.args
        task_vars = task_vars or {}
        if str(self._task.get_path()).rsplit(":", 1)[0] != str(_TASK_SOURCE):
            return _reject("ENTRYPOINT_GUARD: refusing successor check outside the canonical role source")
        if not _selected() or not context.CLIARGS.get("check"):
            return _reject("TASK_SELECTION_GUARD: successor check requires the exact check/diff wrapper")
        if set(args) != _ARGUMENT_KEYS:
            return _reject("MUTATION_ARGUMENT_GUARD: refusing unmodeled successor check arguments")

        token = os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_TOKEN", "")
        attestation_path = os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_ATTESTATION_FILE", "")
        wrapper_pid = os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_WRAPPER_PID", "")
        wrapper_path = os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_WRAPPER_PATH", "")
        wrapper_sha = os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_WRAPPER_SHA256", "")
        try:
            pid = int(wrapper_pid)
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            pid, attestation_state, attestation = 0, None, ""
        valid_attestation = (
            os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and pid > 1
            and _ancestor(pid)
            and attestation_state is not None
            and stat.S_ISREG(attestation_state.st_mode)
            and not stat.S_ISLNK(attestation_state.st_mode)
            and stat.S_IMODE(attestation_state.st_mode) == 0o600
            and attestation_state.st_uid == os.getuid()
            and Path(wrapper_path) == _WRAPPER_SOURCE
            and wrapper_sha == _WRAPPER_HASH
            and _sha256(_WRAPPER_SOURCE) == _WRAPPER_HASH
            and attestation == f"{token}:entrypoint:{pid}:{wrapper_sha}"
        )
        binding = task_vars.get("reactive_resume_dev_successor_internal_binding", {})
        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding.get("environment") == "dev"
            and binding.get("database") == "reactive_resume_dev_successor"
            and binding.get("runtime_role") == "reactive_resume_dev_runtime"
            and binding.get("migration_role") == "reactive_resume_dev_migrator"
            and binding.get("namespace") == "shared-services"
            and binding.get("pod_name") == args.get("pod")
            and binding.get("metadata_only") is True
            and binding.get("no_apply_path") is True
        )
        if not valid_attestation or not valid_binding or task_vars.get("reactive_resume_dev_successor_approved") is not True:
            return _reject("ENTRYPOINT_GUARD: refusing successor check without the single-run wrapper binding")

        script = _REPOSITORY_ROOT / "ansible/files/database-provisioning" / _SCRIPT_NAME
        if args.get("script_name") != _SCRIPT_NAME or args.get("script_sha256") != _SCRIPT_HASH:
            return _reject("SOURCE_HASH_GUARD: successor checker identity drift")
        if _sha256(script) != _SCRIPT_HASH:
            return _reject("SOURCE_HASH_GUARD: successor checker source drift")
        if not _source_closure():
            return _reject("SOURCE_HASH_GUARD: successor Ansible source closure drift")
        if not _manifest_closure():
            return _reject("SOURCE_HASH_GUARD: successor MANIFESTS closure drift")
        for path, expected in (
            (_TASK_SOURCE, _TASK_HASH),
            (_DEFAULTS_SOURCE, _DEFAULTS_HASH),
            (_PLAYBOOK_SOURCE, _PLAYBOOK_HASH),
            (_POLICY_SOURCE, _POLICY_HASH),
        ):
            if _sha256(path) != expected:
                return _reject(f"SOURCE_HASH_GUARD: source drift in {path.name}")
        try:
            source = script.read_text()
        except OSError:
            return _reject("SOURCE_HASH_GUARD: successor checker is unreadable")
        command = args.get("command")
        if command != ["/bin/sh", "-ec", source]:
            return _reject("MUTATION_ARGUMENT_GUARD: inline successor checker drift")
        if args.get("namespace") != "shared-services" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml" or args.get("container") != "postgres":
            return _reject("MUTATION_ARGUMENT_GUARD: successor execution identity drift")
        if not re.fullmatch(r"shared-postgresql-[a-z0-9-]+", str(args.get("pod", ""))):
            return _reject("MUTATION_ARGUMENT_GUARD: successor Pod identity drift")
        if any(re.search(pattern, " ".join(str(value) for value in command), re.I) for pattern in (r"postgres(?:ql)?://[^ ]+:[^ ]+@", r"--(?:password|secret|token)(?:=| )")):
            return _reject("SECRET_ARGV_GUARD: credential-bearing successor command")

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
        failed = bool(executed.get("failed")) or int(executed.get("rc", 0) or 0) != 0
        result.update(changed=False, failed=failed, msg="Reactive Resume DEV successor check completed" if not failed else "Reactive Resume DEV successor check failed")
        for key in ("stdout", "stderr", "rc", "result"):
            result.pop(key, None)
        return result
