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
_INVENTORY_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/inventory.local.yml"
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_PYTHON_SOURCE = _REPOSITORY_ROOT / ".venv/bin/python"
_PYTHON_REAL_SOURCE = Path("/usr/bin/python3.13")
_EXPECTED_PYTHON_SHA256 = "17b78e0a93175e86f9ac03141924fd7a7f0c0c52e66b34bfa0de20ffef989df1"
_OPERATOR = "paul"
_METADATA_SOURCE = _REPOSITORY_ROOT / "ansible/library/rabbitmq_prod_credential_metadata.py"
_BROKER_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/rabbitmq/runtime/statefulset-rabbitmq.yaml"
_RABBITMQ_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/rabbitmq/runtime/configmap-rabbitmq.yaml"
_ENGINE_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-rabbitmq-secrets/source/rabbitmq-infisical-secrets.yaml"
_RUNTIME_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-cristexhub-prod-runtime/source/cristexhub-prod-runtime-static-secret.yaml"
# Integrity DAG: the wrapper's own canonical startup value is the root.  The
# fixed wrapper pin is intentionally included in this action's canonical hash;
# the action self-pin is the only field normalized here.  No action↔wrapper
# runtime pin is normalized, so a coordinated wrapper/action edit is rejected.
_ROLES_PATH = _REPOSITORY_ROOT / "ansible/roles"
_LIBRARY_PATH = _REPOSITORY_ROOT / "ansible/library"
_ACTION_CANONICAL_SHA256 = "c38744ce0768c8ce40955866b9df138a93a3bc32845ff0085406654fdfbd6aa4"
_TASK_SHA256 = "78104b5277c14ac6071c21250769d74184b12128c7c74591f50b01556fbb0250"
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
_WRAPPER_CANONICAL_SHA256 = "ca2c1488e08ab46a0f096c84f1284dc812fdb4d8dce6ea235aae3edd14e47951"
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
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            r'(?m)^_ACTION_CANONICAL_SHA256 = "[0-9a-f]{64}"$',
            '_ACTION_CANONICAL_SHA256 = "' + ("0" * 64) + '"',
            source,
        )
        return hashlib.sha256(source.encode()).hexdigest() if count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _canonical_wrapper_hash(path: Path) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            r"(?m)^wrapper_canonical_sha256='[0-9a-f]{64}'$",
            "wrapper_canonical_sha256='" + ("0" * 64) + "'",
            source,
        )


        return hashlib.sha256(source.encode()).hexdigest() if count == 1 else ""
    except (OSError, UnicodeError):
        return ""


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
        return any(
            (base / requested).resolve(strict=True) == _WRAPPER_SOURCE
            for base in (cwd, _REPOSITORY_ROOT)
        )
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


def _selected() -> bool:
    inventory = context.CLIARGS.get("inventory") or []
    if isinstance(inventory, str):
        inventory = [inventory]
    elif isinstance(inventory, tuple):
        inventory = list(inventory)
    return (
        sys.argv == _expected_argv()
        and _toolchain_valid()
        and bool(context.CLIARGS.get("check"))
        and bool(context.CLIARGS.get("diff"))
        and context.CLIARGS.get("subset") == "crtxweb"
        and context.CLIARGS.get("start_at_task") is None
        and context.CLIARGS.get("step") in (None, False)
        and not context.CLIARGS.get("skip_tags")
        and list(context.CLIARGS.get("tags") or []) in ([], ["all"])
        and inventory == [".ansible/inventory.local.yml"]
        and os.environ.get("ANSIBLE_LIBRARY") == str(_LIBRARY_PATH)
        and os.environ.get("ANSIBLE_ROLES_PATH") == str(_ROLES_PATH)
        and not any(
            os.environ.get(name)
            for name in (
                "ANSIBLE_ACTION_PLUGINS",
                "ANSIBLE_COLLECTIONS_PATH",
                "ANSIBLE_START_AT_TASK",
                "ANSIBLE_SKIP_TAGS",
                "ANSIBLE_TAGS",
                "ANSIBLE_STEP",
            )
        )
    )


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
        if not _selected():
            return _reject("TASK_SELECTION_GUARD: use the exact check-only RabbitMQ rotation wrapper")
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
            "CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_CANONICAL_SHA256": _canonical_action_hash(Path(__file__)),
            "CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_CANONICAL_SHA256": _WRAPPER_CANONICAL_SHA256,
        }
        valid_sources = (
            _sha256(_TASK_SOURCE) == _TASK_SHA256
            and _sha256(_DEFAULTS_SOURCE) == _DEFAULTS_SHA256
            and _sha256(_PLAYBOOK_SOURCE) == _PLAYBOOK_SHA256
            and _sha256(_POLICY_SOURCE) == _POLICY_SHA256
            and _sha256(_METADATA_SOURCE) == _METADATA_SHA256
            and _sha256(_BROKER_SOURCE) == _BROKER_SOURCE_SHA256
            and _sha256(_RABBITMQ_CONFIG_SOURCE) == _RABBITMQ_CONFIG_SOURCE_SHA256
            and _sha256(_ENGINE_SOURCE) == _ENGINE_SOURCE_SHA256
            and _sha256(_RUNTIME_SOURCE) == _RUNTIME_SOURCE_SHA256
            and _sha256(Path(__file__)) == os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_SHA256")
            and _canonical_action_hash(Path(__file__)) == os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_CANONICAL_SHA256") == expected_env["CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_CANONICAL_SHA256"]
            and _canonical_wrapper_hash(_WRAPPER_SOURCE) == _WRAPPER_CANONICAL_SHA256
            and expected_env["CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_CANONICAL_SHA256"] == os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_CANONICAL_SHA256")
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
