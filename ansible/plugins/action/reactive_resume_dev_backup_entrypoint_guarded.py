from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

from ansible import context
from ansible.plugins.action import ActionBase


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_EXPECTED_TASK_SOURCE = str(
    _REPOSITORY_ROOT / "ansible/playbooks/configure_reactive_resume_dev_backup.yml"
)
_EXPECTED_TASK_NAME = "Mark the complete guarded backup preflight"
_EXPECTED_TASK_ACTION = "reactive_resume_dev_backup_entrypoint_guarded"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/configure_reactive_resume_dev_backup.yml"
_PLAYBOOK_CANONICAL_SHA256 = "c7b3a8fabad47f2efa9e0069d4259b92bbaa756c711fb41c4ebd9dde38bbefc2"
_EXPECTED_SOURCE_REGISTER = "reactive_resume_dev_backup_source_states"
_SELF_SOURCE_SHA256 = "__SELF_SOURCE_SHA256__"
_WRAPPER_SOURCE_SHA256 = "__WRAPPER_SOURCE_SHA256__"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_INVENTORY_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/inventory.local.yml"
_INVENTORY_SHA256 = "652a8455f8a050005ab783d20d4e60a0cd034d8a6439f1cffe551a91102773b0"
_INVENTORY_BYTES = (
    b"---\nall:\n  children:\n    k3s_servers:\n      hosts:\n"
    b"        crtxweb:\n          ansible_connection: local\n"
    b"          ansible_python_interpreter: /usr/bin/python3\n"
    b"          ansible_user: paul\n"
)
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_STRATEGY_SHA256 = "852257239327e457e910980417e478ee28654d330df2ebeff88374ddb21c3e3c"
_COLLECTION_MANIFEST_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/collections/ansible_collections/kubernetes/core/MANIFEST.json"
_COLLECTION_MANIFEST_SHA256 = "dc32e90ca987d6199e9091f749ecb40fd3380b40aabb7c18961ec75582cfc6df"
_EXPECTED_SOURCE_RESULTS = (
    {
        "path": "ansible/bin/configure-reactive-resume-dev-backup",
        "mode": "0755",
        "sha256": _WRAPPER_SOURCE_SHA256,
    },
    {
        "path": ".venv/bin/ansible-playbook",
        "mode": "0755",
        "sha256": _CONTROLLER_SHA256,
    },
    {
        "path": "ansible/.ansible/inventory.local.yml",
        "mode": "0600",
        "sha256": _INVENTORY_SHA256,
    },
    {
        "path": "ansible/.ansible/collections/ansible_collections/kubernetes/core/MANIFEST.json",
        "mode": "0644",
        "sha256": _COLLECTION_MANIFEST_SHA256,
    },
    {
        "path": "ansible/ansible.cfg",
        "mode": "0644",
        "sha256": "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9",
    },
    {
        "path": "ansible/plugins/strategy/reactive_resume_dev_backup_guarded_linear.py",
        "mode": "0644",
        "sha256": _STRATEGY_SHA256,
    },
    {
        "path": "ansible/plugins/action/reactive_resume_dev_backup_entrypoint_guarded.py",
        "mode": "0644",
        "sha256": _SELF_SOURCE_SHA256,
    },
    {
        "path": "ansible/files/backup/reactive-resume-dev-backup",
        "mode": "0755",
        "sha256": "2a170cb9a26c1110398f7ed0f4ce605a6dd120de3787de0c83708f4cffa0111e",
    },
    {
        "path": "ansible/files/backup/restore-reactive-resume-dev-backup-rehearsal",
        "mode": "0755",
        "sha256": "dc205d8fc6b56d6b98a66358a1c69f68f5fb070e11061815217015d571dfc696",
    },
    {
        "path": "ansible/files/backup/cristexweb-reactive-resume-dev-backup.service",
        "mode": "0644",
        "sha256": "cd1a1cf09646d6675ebdefba085735755c00e229f1a21ae1d2a5ab2c196dbae2",
    },
    {
        "path": "ansible/files/backup/cristexweb-reactive-resume-dev-backup.timer",
        "mode": "0644",
        "sha256": "c0b4d246b523e46a375e55eb0aa4bb70d344b9a7a1c4a5f5e1c05e37ac315461",
    },
    {
        "path": "ansible/files/backup/reactive-resume-dev-backup-networkpolicy.yaml",
        "mode": "0644",
        "sha256": "4bfdf41939c1a6f3312c3f703c235efe14959fb1062c5573f16e8d337e1d1ec6",
    },
)
_SOURCE_CONTRACT_SHA256 = "45a6c12164e0d57c834b21792af85809c5a821396dcdd7ef91121c4b5cc27306"
_EXPECTED_BINDING = {
    "schema": 1,
    "task_source": "ansible/playbooks/configure_reactive_resume_dev_backup.yml",
    "task_name": _EXPECTED_TASK_NAME,
    "task_action": _EXPECTED_TASK_ACTION,
    "source_register": _EXPECTED_SOURCE_REGISTER,
    "source_result_count": len(_EXPECTED_SOURCE_RESULTS),
    "source_contract_sha256": _SOURCE_CONTRACT_SHA256,
    "controller_path": "/home/paul/projects/cristexweb/.venv/bin/ansible-playbook",
    "controller_sha256": _CONTROLLER_SHA256,
    "inventory_path": "/home/paul/projects/cristexweb/ansible/.ansible/inventory.local.yml",
    "inventory_sha256": _INVENTORY_SHA256,
    "ansible_config_sha256": _ANSIBLE_CONFIG_SHA256,
    "strategy_sha256": _STRATEGY_SHA256,
    "collection_manifest_sha256": _COLLECTION_MANIFEST_SHA256,
    "no_apply_path": True,
}


def _canonical_playbook_sha256() -> str:
    try:
        text = _PLAYBOOK_SOURCE.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""
    text, self_count = re.subn(
        r"(?m)^(    reactive_resume_dev_backup_playbook_sha256: )[0-9a-f]{64}$",
        lambda match: match.group(1) + ("0" * 64),
        text,
    )
    text, wrapper_variable_count = re.subn(
        r"(?m)^(    reactive_resume_dev_backup_wrapper_sha256: )[0-9a-f]{64}$",
        lambda match: match.group(1) + ("0" * 64),
        text,
    )
    text, immutable_hash_count = re.subn(
        r"(?m)^(\s+- reactive_resume_dev_backup_(?:wrapper|playbook)_sha256 == ')[0-9a-f]{64}(')$",
        lambda match: match.group(1) + ("0" * 64) + match.group(2),
        text,
    )
    dynamic_count = 0
    for source_path in (
        "ansible/bin/configure-reactive-resume-dev-backup",
        "ansible/plugins/action/reactive_resume_dev_backup_entrypoint_guarded.py",
    ):
        pattern = (
            r"(- path: "
            + re.escape(source_path)
            + r"\n\s+mode: '[0-9]{4}'\n\s+sha256: )[0-9a-f]{64}"
        )
        text, count = re.subn(
            pattern,
            lambda match: match.group(1) + ("0" * 64),
            text,
        )
        dynamic_count += count
    if self_count != 1 or wrapper_variable_count != 1 or immutable_hash_count != 2 or dynamic_count != 2:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _controller_contract() -> bool:
    try:
        state = _CONTROLLER_SOURCE.stat(follow_symlinks=False)
        with _CONTROLLER_SOURCE.open("r", encoding="utf-8") as source:
            first_line = source.readline().rstrip("\n")
    except (OSError, UnicodeError):
        return False
    return (
        stat.S_ISREG(state.st_mode)
        and not stat.S_ISLNK(state.st_mode)
        and state.st_uid == os.getuid()
        and state.st_gid == os.getgid()
        and stat.S_IMODE(state.st_mode) == 0o755
        and hashlib.sha256(_CONTROLLER_SOURCE.read_bytes()).hexdigest() == _CONTROLLER_SHA256
        and first_line == f"#!{_REPOSITORY_ROOT}/.venv/bin/python"
    )


def _inventory_contract() -> bool:
    try:
        state = _INVENTORY_SOURCE.stat(follow_symlinks=False)
        return (
            stat.S_ISREG(state.st_mode)
            and not stat.S_ISLNK(state.st_mode)
            and state.st_uid == os.getuid()
            and state.st_gid == os.getgid()
            and stat.S_IMODE(state.st_mode) == 0o600
            and hashlib.sha256(_INVENTORY_SOURCE.read_bytes()).hexdigest() == _INVENTORY_SHA256
            and _INVENTORY_SOURCE.read_bytes() == _INVENTORY_BYTES
        )
    except OSError:
        return False


def _runtime_binding_contract() -> bool:
    return (
        os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_CONTROLLER_PATH")
        == str(_CONTROLLER_SOURCE)
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_CONTROLLER_SHA256")
        == _CONTROLLER_SHA256
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_INVENTORY_PATH")
        == str(_INVENTORY_SOURCE)
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_INVENTORY_SHA256")
        == _INVENTORY_SHA256
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ANSIBLE_CONFIG_SHA256")
        == _ANSIBLE_CONFIG_SHA256
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_STRATEGY_SHA256")
        == _STRATEGY_SHA256
        and os.environ.get("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_COLLECTION_MANIFEST_SHA256")
        == _COLLECTION_MANIFEST_SHA256
        and os.environ.get("ANSIBLE_CONFIG") == str(_REPOSITORY_ROOT / "ansible/ansible.cfg")
        and not any(
            key.startswith("ANSIBLE_") and key != "ANSIBLE_CONFIG"
            for key in os.environ
        )
        and not any(
            key in os.environ
            for key in (
                "PYTHONHOME",
                "PYTHONPATH",
                "PYTHONOPTIMIZE",
                "PYTHONINSPECT",
                "PYTHONBREAKPOINT",
                "VIRTUAL_ENV",
            )
        )
    )


def _task_source(task: Any) -> str:
    try:
        raw_path = str(task.get_path())
    except (AttributeError, OSError, TypeError):
        return ""
    return str(Path(re.sub(r":\d+(?::\d+)?$", "", raw_path)).resolve())


def _resolved_source_item(expected: dict[str, str]) -> dict[str, str] | None:
    resolved = dict(expected)
    if resolved["sha256"] in {_SELF_SOURCE_SHA256, _WRAPPER_SOURCE_SHA256}:
        try:
            resolved["sha256"] = hashlib.sha256(
                (_REPOSITORY_ROOT / resolved["path"]).read_bytes()
            ).hexdigest()
        except OSError:
            return None
    return resolved


def _canonical_source_file_matches(expected: dict[str, str]) -> bool:
    try:
        path = _REPOSITORY_ROOT / expected["path"]
        state = path.stat(follow_symlinks=False)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return False
    return (
        stat.S_ISREG(state.st_mode)
        and not stat.S_ISLNK(state.st_mode)
        and state.st_uid == os.getuid()
        and state.st_gid == os.getgid()
        and stat.S_IMODE(state.st_mode) == int(expected["mode"], 8)
        and digest == expected["sha256"]
    )


def _valid_source_result(result: Any, expected: dict[str, str]) -> bool:
    if not isinstance(result, dict):
        return False
    expected_item = _resolved_source_item(expected)
    if expected_item is None:
        return False
    if result.get("changed") is not False or result.get("failed", False) is not False:
        return False
    if result.get("unreachable", False) is not False or result.get("skipped", False) is not False:
        return False
    if result.get("ansible_loop_var") != "item" or result.get("item") != expected_item:
        return False
    stat_result = result.get("stat")
    return (
        isinstance(stat_result, dict)
        and stat_result.get("exists") is True
        and stat_result.get("isreg") is True
        and stat_result.get("islnk") is False
        and stat_result.get("pw_name") == "paul"
        and stat_result.get("gr_name") == "paul"
        and stat_result.get("mode") == expected_item["mode"]
        and stat_result.get("checksum") == expected_item["sha256"]
    )


def _valid_source_pair(result: Any, expected: dict[str, str]) -> bool:
    expected_item = _resolved_source_item(expected)
    return (
        expected_item is not None
        and _canonical_source_file_matches(expected_item)
        and _valid_source_result(result, expected_item)
    )


def _valid_source_states(source_states: Any) -> bool:
    if not isinstance(source_states, dict):
        return False
    if (
        source_states.get("changed") is not False
        or source_states.get("failed", False) is not False
        or source_states.get("unreachable", False) is not False
        or source_states.get("skipped", False) is not False
    ):
        return False
    results = source_states.get("results")
    return (
        isinstance(results, list)
        and len(results) == len(_EXPECTED_SOURCE_RESULTS)
        and all(
            _valid_source_pair(result, expected)
            for result, expected in zip(results, _EXPECTED_SOURCE_RESULTS)
        )
    )


class ActionModule(ActionBase):
    """Fail closed unless the canonical complete preflight is present.

    The wrapper and controller enforce this boundary for accidental/direct
    invocation; a hostile same-UID process can still forge same-UID inputs.
    """

    TRANSFERS_FILES = False

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = super().run(tmp, task_vars)
        task_vars = task_vars or {}
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        long_selection_options = (
            "--start-at-task",
            "--step",
            "--tags",
            "--skip-tags",
        )
        selection_argv = any(
            argument == "-t"
            or argument.startswith("-t=")
            or (argument.startswith("-t") and len(argument) > 2)
            or (
                argument.startswith("--")
                and any(
                    option.startswith(argument.split("=", 1)[0])
                    for option in long_selection_options
                )
            )
            for argument in sys.argv[1:]
        )
        if (
            context.CLIARGS.get("start_at_task") is not None
            or (
                context.CLIARGS.get("step") is not None
                and context.CLIARGS.get("step") is not False
            )
            or selection_argv
            or tags not in ([], ["all"])
            or skip_tags
        ):
            return {
                **result,
                "changed": False,
                "failed": True,
                "msg": "TASK_SELECTION_GUARD: backup requires the complete guarded play",
            }
        task = self._task
        if (
            getattr(task, "action", None) != _EXPECTED_TASK_ACTION
            or getattr(task, "name", None) != _EXPECTED_TASK_NAME
            or _task_source(task) != _EXPECTED_TASK_SOURCE
            or _canonical_playbook_sha256() != _PLAYBOOK_CANONICAL_SHA256
            or getattr(task, "args", None) != {}
        ):
            return {
                **result,
                "changed": False,
                "failed": True,
                "msg": "ENTRYPOINT_GUARD: backup action is outside the canonical task source",
            }

        token = os.environ.get(
            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT_TOKEN", ""
        )
        attestation = os.environ.get(
            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT_ATTESTATION_FILE", ""
        )
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            state = None
            content = ""
        binding = task_vars.get(
            "reactive_resume_dev_backup_internal_preflight_binding", {}
        )
        valid_binding = (
            isinstance(binding, dict)
            and binding == _EXPECTED_BINDING
        )
        source_states = task_vars.get(_EXPECTED_SOURCE_REGISTER)
        valid = (
            len(token) == 64
            and all(char in "0123456789abcdef" for char in token)
            and state is not None
            and stat.S_ISREG(state.st_mode)
            and state.st_uid == os.getuid()
            and stat.S_IMODE(state.st_mode) == 0o600
            and state.st_nlink == 1
            and content == f"{token}:entrypoint\n"
            and valid_binding
            and _valid_source_states(source_states)
            and _runtime_binding_contract()
            and _controller_contract()
            and _inventory_contract()
        )
        if not valid:
            return {
                **result,
                "changed": False,
                "failed": True,
                "msg": "ENTRYPOINT_GUARD: backup preflight or attestation is incomplete",
            }
        result.update(
            changed=False,
            ansible_facts={
                "reactive_resume_dev_backup_internal_preflight_complete": True
            },
        )
        return result
