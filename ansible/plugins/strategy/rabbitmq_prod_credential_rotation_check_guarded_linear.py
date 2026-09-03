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
_INVENTORY_SHA256 = "652a8455f8a050005ab783d20d4e60a0cd034d8a6439f1cffe551a91102773b0"
_INVENTORY_BYTES = (
    b"---\nall:\n  children:\n    k3s_servers:\n      hosts:\n"
    b"        crtxweb:\n          ansible_connection: local\n"
    b"          ansible_python_interpreter: /usr/bin/python3\n"
    b"          ansible_user: paul\n"
)
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation"
_ACTION_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py"
_STRATEGY_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py"
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/rabbitmq_prod_credential_rotation_check/defaults/main.yml"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml"
_POLICY_SOURCE = _REPOSITORY_ROOT / "ansible/files/policies/cristexhub-prod-rabbitmq-credential-rotation.yml"
_METADATA_SOURCE = _REPOSITORY_ROOT / "ansible/library/rabbitmq_prod_credential_metadata.py"
_BROKER_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/rabbitmq/runtime/statefulset-rabbitmq.yaml"
_RABBITMQ_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/rabbitmq/runtime/configmap-rabbitmq.yaml"
_ENGINE_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-rabbitmq-secrets/source/rabbitmq-infisical-secrets.yaml"
_RUNTIME_SOURCE = _REPOSITORY_ROOT / "ansible/files/components/infisical-cristexhub-prod-runtime/source/cristexhub-prod-runtime-static-secret.yaml"
_TASK_SHA256 = "345b29854485d139febfbd9010e2da1e3b9e4aadf2ad6c3265be83085bbe5cd1"
_DEFAULTS_SHA256 = "3e5d9d043eccd416d0696da9dd4441f1ec78cac092dd1f1752d4b69725c121ac"
_PLAYBOOK_SHA256 = "afba74ac3b512de525f322dcf7e89e3faed012f277c79912f439ddb9b2cf9b60"
_POLICY_SHA256 = "b4cd58058ccbbd236b44511b63637bda5fb61a6ca2df56f4f78e24f2da8a409f"
_METADATA_SHA256 = "586841d6c3f677e5bd7d68c5968f92f3abe508ddb026227c312db14582bdd6be"
_BROKER_SOURCE_SHA256 = "5ea7cfa66e72615e5ff50657e934740907a90d4219c221323e3b91af3efe6242"
_RABBITMQ_CONFIG_SOURCE_SHA256 = "663c006190e6e5e03e7c22d198cb41245d2ab3b7dab406acb4fdefe00a10a2d5"
_ENGINE_SOURCE_SHA256 = "b5eeaa0abc5b9ee91d392d6ac064862026b64f0d4c74f6431fe5dca517c506d0"
_RUNTIME_SOURCE_SHA256 = "3204aab3fc0f5b55f9af3623fb658d5ffd8289437d5d0ea91ab0480dc4126ee0"
_ACTION_CANONICAL_SHA256 = "9291babe5fea873ddf77dc15ec147fbf1a2c1e6467d72e6598234f8c4634b6aa"
_STRATEGY_CANONICAL_SHA256 = "613fc18fb26bb9c916e97d4d5da3b7bc35515b10c16e616da6c4846a56ebc513"

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


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _canonical_hash(path: Path) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            r'(?m)^_STRATEGY_CANONICAL_SHA256 = "[0-9a-f]{64}"$',
            '_STRATEGY_CANONICAL_SHA256 = "' + ("0" * 64) + '"',
            source,
        )
        return hashlib.sha256(source.encode()).hexdigest() if count == 1 else ""
    except (OSError, UnicodeError):
        return ""


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
        and content == _INVENTORY_BYTES
        and hashlib.sha256(content).hexdigest() == _INVENTORY_SHA256
    )


def _source_contract() -> bool:
    expected = {
        _ANSIBLE_CONFIG_SOURCE: _ANSIBLE_CONFIG_SHA256,
        _CONTROLLER_SOURCE: _CONTROLLER_SHA256,
        _TASK_SOURCE: _TASK_SHA256,
        _DEFAULTS_SOURCE: _DEFAULTS_SHA256,
        _PLAYBOOK_SOURCE: _PLAYBOOK_SHA256,
        _POLICY_SOURCE: _POLICY_SHA256,
        _METADATA_SOURCE: _METADATA_SHA256,
        _BROKER_SOURCE: _BROKER_SOURCE_SHA256,
        _RABBITMQ_CONFIG_SOURCE: _RABBITMQ_CONFIG_SOURCE_SHA256,
        _ENGINE_SOURCE: _ENGINE_SOURCE_SHA256,
        _RUNTIME_SOURCE: _RUNTIME_SOURCE_SHA256,
    }
    try:
        for path, digest in expected.items():
            state = path.stat(follow_symlinks=False)
            if not stat.S_ISREG(state.st_mode) or path.is_symlink() or state.st_uid != os.getuid():
                return False
            expected_mode = 0o775 if path == _CONTROLLER_SOURCE else 0o644
            if stat.S_IMODE(state.st_mode) != expected_mode or _sha256(path) != digest:
                return False
        return True
    except OSError:
        return False


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
        try:
            lines = Path(f"/proc/{current}/status").read_text(encoding="utf-8").splitlines()
            current = int(next(line for line in lines if line.startswith("PPid:")).split()[1])
        except (OSError, StopIteration, ValueError):
            return False
    return False


def _wrapper_attestation_valid() -> bool:
    token = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_TOKEN", "")
    path = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ATTESTATION_FILE", "")
    wrapper_pid = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_PID", "")
    wrapper_path = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_PATH", "")
    wrapper_sha = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_SHA256", "")
    try:
        pid = int(wrapper_pid)
        state = os.stat(path, follow_symlinks=False)
        attestation = Path(path).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError, ValueError):
        return False
    argv = _proc_cmdline(pid)
    return (
        os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ENTRYPOINT") == "v1"
        and len(token) == 64
        and all(char in "0123456789abcdef" for char in token)
        and pid > 1
        and _is_ancestor(pid)
        and len(argv) == 3
        and argv[0] == "/bin/sh"
        and Path(argv[1]).resolve() == _WRAPPER_SOURCE
        and argv[2] == "check"
        and stat.S_ISREG(state.st_mode)
        and not stat.S_ISLNK(state.st_mode)
        and stat.S_IMODE(state.st_mode) == 0o600
        and state.st_uid == os.getuid()
        and Path(wrapper_path) == _WRAPPER_SOURCE
        and wrapper_sha == _sha256(_WRAPPER_SOURCE)
        and attestation == f"{token}:entrypoint:{pid}:{wrapper_sha}"
    )


def _canonical_argv() -> bool:
    return sys.argv == [
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


def _cli_contract() -> bool:
    inventory = context.CLIARGS.get("inventory") or []
    if isinstance(inventory, str):
        inventory = [inventory]
    tags = list(context.CLIARGS.get("tags") or [])
    skip_tags = list(context.CLIARGS.get("skip_tags") or [])
    selection_argv = any(
        argument in {"--start-at-task", "--step", "--tags", "--skip-tags", "-t"}
        or argument.startswith(("--start-at-task=", "--tags=", "--skip-tags=", "-t="))
        for argument in sys.argv[1:]
    )
    return (
        _canonical_argv()
        and context.CLIARGS.get("check") is True
        and context.CLIARGS.get("diff") is True
        and context.CLIARGS.get("subset") == "crtxweb"
        and context.CLIARGS.get("start_at_task") is None
        and context.CLIARGS.get("step") in (None, False)
        and not skip_tags
        and tags in ([], ["all"])
        and inventory == [".ansible/inventory.local.yml"]
        and not selection_argv
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG_SOURCE)
        and not any(os.environ.get(name) for name in _FORBIDDEN_ENV)
    )


def _env_contract() -> bool:
    action_sha = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_SHA256", "")
    strategy_sha = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_STRATEGY_SHA256", "")
    wrapper_canonical = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_CANONICAL_SHA256", "")
    strategy_canonical = os.environ.get("CRISTEXWEB_RABBITMQ_PROD_ROTATION_STRATEGY_CANONICAL_SHA256", "")
    return (
        _wrapper_attestation_valid()
        and action_sha == _ACTION_CANONICAL_SHA256
        and _canonical_action_hash(_ACTION_SOURCE) == _ACTION_CANONICAL_SHA256
        and strategy_canonical == _STRATEGY_CANONICAL_SHA256
        and _canonical_hash(_STRATEGY_SOURCE) == _STRATEGY_CANONICAL_SHA256
        and strategy_sha == _sha256(_STRATEGY_SOURCE)
        and len(wrapper_canonical) == 64
        and all(char in "0123456789abcdef" for char in wrapper_canonical)
    )


class StrategyModule(LinearStrategyModule):
    """Reject selection bypass and provenance drift before role tasks iterate."""

    def run(self, iterator, play_context):  # type: ignore[no-untyped-def]
        if not (_inventory_contract() and _source_contract() and _cli_contract() and _env_contract()):
            raise AnsibleError(
                "ENTRYPOINT_GUARD: use the exact check-only RabbitMQ rotation wrapper"
            )
        return super().run(iterator, play_context)
