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

_SCRIPT_HASHES = {
    "postgresql-check.sh": "edd5c0b8aee1636b76cae4f2f6ff7e94b54bdb5e62a08e9ea5438eabb224b514",
    "postgresql-apply.sh": "08a98b5796c2be31d63c6b47e391aaed741bb6620023cc22e3af6abe514cbc4a",
    "mongodb-check.sh": "4e9c27b502e1ab5e49472d53642b8469d33ccd9bbe021e9e59ddf6ea607d39f6",
    "mongodb-apply.sh": "571301f932cd2a36d40813313c9da077380114452542cd622e0d6d379a4990f6",
}
# The canonical checkout is the only permitted operational task source.
_TASK_SOURCES = {
    "/Users/paul/Projects/cristexweb/ansible/roles/shared_postgresql_provisioning/tasks/main.yml",
    "/Users/paul/Projects/cristexweb/ansible/roles/shared_mongodb_provisioning/tasks/main.yml",
}
_ARGUMENT_KEYS = {
    "namespace",
    "pod",
    "container",
    "command",
    "kubeconfig",
    "script_name",
    "script_sha256",
}
_FORBIDDEN_ARGUMENT_PATTERNS = (
    re.compile(r"--(?:password|pass|secret|token)(?:[= ]|$)", re.IGNORECASE),
    re.compile(r"(?:postgres(?:ql)?|mongodb)://[^\s/]+:[^\s@]+@", re.IGNORECASE),
    re.compile(r"(?:client_secret|private_key|api_key)\s*=\s*[^$\s]", re.IGNORECASE),
)


def _script_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "ansible" / "files" / "database-provisioning" / name


def _valid_selection() -> bool:
    start_at_task = context.CLIARGS.get("start_at_task")
    step = bool(context.CLIARGS.get("step"))
    tags = list(context.CLIARGS.get("tags") or [])
    skip_tags = list(context.CLIARGS.get("skip_tags") or [])
    return not start_at_task and not step and tags in ([], ["all"]) and not skip_tags


class ActionModule(ActionBase):
    """Execute only a hash-bound, value-free, UID-bound database-logical-provisioning script through k8s_exec;
    helper cleanup uses an Orphan propagation boundary.
    """

    TRANSFERS_FILES = False

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = super().run(tmp=tmp, task_vars=task_vars)
        args = self._task.args
        task_source = str(self._task.get_path()).rsplit(":", 1)[0]
        task_vars = task_vars or {}
        if task_source not in _TASK_SOURCES:
            return {
                "changed": False,
                "failed": True,
                "msg": "ENTRYPOINT_GUARD: refusing database execution outside the canonical role source",
            }
        if not _valid_selection():
            return {
                "changed": False,
                "failed": True,
                "msg": "TASK_SELECTION_GUARD: refusing database execution under task selection",
            }
        entrypoint = os.environ.get("CRISTEXWEB_SHARED_DATABASE_PROVISIONING_ENTRYPOINT")
        token = os.environ.get("CRISTEXWEB_SHARED_DATABASE_PROVISIONING_TOKEN", "")
        attestation_path = os.environ.get(
            "CRISTEXWEB_SHARED_DATABASE_PROVISIONING_ATTESTATION_FILE", ""
        )
        binding = task_vars.get(
            "shared_postgresql_provisioning_internal_preflight_binding",
            task_vars.get(
                "shared_mongodb_provisioning_internal_preflight_binding",
                task_vars.get("shared_database_provisioning_internal_preflight_binding", {}),
            ),
        )
        try:
            attestation = os.stat(attestation_path, follow_symlinks=False)
            contents = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation = None
            contents = ""
        valid_attestation = (
            entrypoint == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and attestation is not None
            and stat.S_ISREG(attestation.st_mode)
            and not stat.S_ISLNK(attestation.st_mode)
            and stat.S_IMODE(attestation.st_mode) == 0o600
            and attestation.st_uid == os.getuid()
            and contents == f"{token}:entrypoint"
        )
        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding.get("namespace_contract") is True
            and binding.get("ready_pod_contract") is True
            and binding.get("secret_contract") is True
            and binding.get("no_delete_path") is True
        )
        if not valid_attestation or not valid_binding or task_vars.get(
            "shared_postgresql_provisioning_approved",
            task_vars.get("shared_mongodb_provisioning_approved"),
        ) is not True:
            return {
                "changed": False,
                "failed": True,
                "msg": "ENTRYPOINT_GUARD: refusing database execution without the validated wrapper and preflight",
            }
        if set(args) != _ARGUMENT_KEYS:
            return {
                "changed": False,
                "failed": True,
                "msg": "MUTATION_ARGUMENT_GUARD: refusing unmodeled database execution arguments",
            }
        script_name = args.get("script_name")
        command = args.get("command")
        if script_name not in _SCRIPT_HASHES or not isinstance(command, list):
            return {
                "changed": False,
                "failed": True,
                "msg": "MUTATION_ARGUMENT_GUARD: refusing an unknown database script",
            }
        if args.get("script_sha256") != _SCRIPT_HASHES[script_name]:
            return {
                "changed": False,
                "failed": True,
                "msg": "SOURCE_HASH_GUARD: refusing database script hash drift",
            }
        path = _script_path(script_name)
        try:
            source = path.read_text()
        except OSError:
            source = ""
        if not source or hashlib.sha256(source.encode()).hexdigest() != _SCRIPT_HASHES[script_name]:
            return {
                "changed": False,
                "failed": True,
                "msg": "SOURCE_HASH_GUARD: canonical database script is absent or changed",
            }
        expected_shell = "/bin/bash" if script_name.startswith("mongodb-") else "/bin/sh"
        if command != [expected_shell, "-ec", source]:
            return {
                "changed": False,
                "failed": True,
                "msg": "MUTATION_ARGUMENT_GUARD: refusing inline database script drift",
            }
        command_text = " ".join(str(value) for value in command)
        if any(pattern.search(command_text) for pattern in _FORBIDDEN_ARGUMENT_PATTERNS):
            return {
                "changed": False,
                "failed": True,
                "msg": "SECRET_ARGV_GUARD: refusing credential-bearing database arguments",
            }
        if (
            args.get("namespace") != "shared-services"
            or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml"
            or not re.fullmatch(r"shared-(?:postgresql|mongodb)-0", str(args.get("pod")))
            or args.get("container") not in {"postgresql", "mongodb", "provision"}
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": "MUTATION_ARGUMENT_GUARD: refusing database execution identity drift",
            }
        module_args = {
            "namespace": args["namespace"],
            "pod": args["pod"],
            "container": args["container"],
            "command": " ".join(shlex.quote(str(value)) for value in command),
            "kubeconfig": args["kubeconfig"],
        }
        executed = self._execute_module(
            module_name="kubernetes.core.k8s_exec",
            module_args=module_args,
            task_vars=task_vars,
            tmp=tmp,
        )
        failed = bool(executed.get("failed")) or int(executed.get("rc", 0) or 0) != 0
        result.update(
            changed=False,
            failed=failed,
            msg=(
                "Database provisioning script completed"
                if not failed
                else "Database provisioning script failed"
            ),
        )
        for key in ("stdout", "stderr", "rc", "result"):
            result.pop(key, None)
        return result
