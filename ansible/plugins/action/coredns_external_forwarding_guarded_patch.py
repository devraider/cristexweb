from __future__ import annotations

import hashlib
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
        source = str(self._task.get_path()).rsplit(":", 1)[0]
        args = self._task.args
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        expected_patch = [{"op": "test", "path": "/data/Corefile", "value": task_vars.get("coredns_external_forwarding_old_corefile")}, {"op": "replace", "path": "/data/Corefile", "value": task_vars.get("coredns_external_forwarding_new_corefile")}]
        valid_args = (
            set(args) == EXPECTED_KEYS and args.get("api_version") == "v1" and args.get("kind") == "ConfigMap"
            and args.get("namespace") == "kube-system" and args.get("name") == "coredns"
            and args.get("kubeconfig") == "/etc/rancher/k3s/k3s.yaml" and args.get("patch") == expected_patch
        )
        token = os.environ.get("CRISTEXWEB_COREDNS_FORWARDING_TOKEN", "")
        attestation = os.environ.get("CRISTEXWEB_COREDNS_FORWARDING_ATTESTATION_FILE", "")
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except OSError:
            state, content = None, ""
        valid_entry = (
            source.endswith(TASK_SUFFIX) and not context.CLIARGS.get("start_at_task") and not context.CLIARGS.get("step")
            and tags in ([], ["all"]) and not skip_tags and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and state is not None and stat.S_ISREG(state.st_mode) and stat.S_IMODE(state.st_mode) == 0o600
            and state.st_uid == os.getuid() and content == f"{token}:coredns-forwarding"
            and task_vars.get("coredns_external_forwarding_approved") is True
            and OLD in str(task_vars.get("coredns_external_forwarding_old_corefile", ""))
            and NEW in str(task_vars.get("coredns_external_forwarding_new_corefile", ""))
        )
        if not valid_args or not valid_entry:
            return {"changed": False, "failed": True, "msg": "COREDNS_FORWARDING_GUARD: refusing noncanonical patch"}
        self._task.action = "kubernetes.core.k8s_json_patch"
        return super().run(tmp=tmp, task_vars=task_vars)
