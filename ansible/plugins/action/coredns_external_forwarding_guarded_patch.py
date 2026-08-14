from __future__ import annotations

import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s_json_patch import ActionModule as PatchActionModule

TASK_SUFFIX = "/ansible/roles/coredns_external_forwarding/tasks/main.yml"
EXPECTED_KEYS = {"api_version", "kind", "name", "namespace", "kubeconfig", "patch"}
OLD = "    forward . /etc/resolv.conf"
NEW = "    forward . 1.1.1.1 1.0.0.1"


class ActionModule(PatchActionModule):
    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        task_vars = task_vars or {}
        source = str(Path(re.sub(r":\d+(?::\d+)?$", "", str(self._task.get_path()))).resolve())
        args = self._task.args
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        expected_patch = [{"op": "test", "path": "/data/Corefile", "value": task_vars.get("coredns_external_forwarding_old_corefile")}, {"op": "replace", "path": "/data/Corefile", "value": task_vars.get("coredns_external_forwarding_new_corefile")}]
        old_corefile = task_vars.get("coredns_external_forwarding_old_corefile")
        new_corefile = task_vars.get("coredns_external_forwarding_new_corefile")
        valid_content = (
            isinstance(old_corefile, str) and isinstance(new_corefile, str)
            and old_corefile.splitlines().count(OLD) == 1
            and old_corefile.splitlines().count(NEW) == 0
            and old_corefile.count(OLD) == 1 and old_corefile.count(NEW) == 0
            and new_corefile == old_corefile.replace(OLD, NEW, 1)
            and new_corefile.splitlines().count(NEW) == 1
        )
        valid_args = (
            set(args) == EXPECTED_KEYS and args.get("api_version") == "v1" and args.get("kind") == "ConfigMap"
            and args.get("namespace") == "kube-system" and args.get("name") == "coredns"
            and args.get("kubeconfig") == "/etc/rancher/k3s/k3s.yaml" and args.get("patch") == expected_patch
            and valid_content
        )
        token = os.environ.get("CRISTEXWEB_COREDNS_FORWARDING_TOKEN", "")
        attestation = os.environ.get("CRISTEXWEB_COREDNS_FORWARDING_ATTESTATION_FILE", "")
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except OSError:
            state, content = None, ""
        repository_root = os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")
        expected_source = str(Path(repository_root).resolve()) + TASK_SUFFIX
        valid_entry = (
            source == expected_source
            and task_vars.get("coredns_external_forwarding_old_directive") == OLD
            and task_vars.get("coredns_external_forwarding_new_directive") == NEW
            and not context.CLIARGS.get("start_at_task") and not context.CLIARGS.get("step")
            and tags in ([], ["all"]) and not skip_tags and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and state is not None and stat.S_ISREG(state.st_mode) and stat.S_IMODE(state.st_mode) == 0o600
            and state.st_uid == os.getuid() and content == f"{token}:coredns-forwarding"
            and task_vars.get("coredns_external_forwarding_approved") is True
        )
        if not valid_args or not valid_entry:
            return {"changed": False, "failed": True, "msg": "COREDNS_FORWARDING_GUARD: refusing noncanonical patch"}
        self._task.action = "kubernetes.core.k8s_json_patch"
        return super().run(tmp=tmp, task_vars=task_vars)
