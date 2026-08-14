from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import (
    ActionModule as KubernetesActionModule,
)

_EXPECTED_OBJECT_HASHES: dict[tuple[str, str, str, str], str] = {('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cristexhub-dev-runtime-alternate-target-boundary'): 'b76c62c997183176fafc3524e3e898c2e230d19b941517dfddbcc415ff681fcd', ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cristexhub-dev-runtime-alternate-target-boundary'): '35322c054efb137bf371efa7e601141d65928258dfc6384495da7f9c00464e0c', ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cristexhub-dev-runtime-secret-write-boundary'): 'f4350e8ac3cbe2c94a4e80413bd82582cb563409273e496685ae145e4cff3d49', ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cristexhub-dev-runtime-secret-write-boundary'): '270c99d67a18ba9df56bfb4eb0086befc31b4d4172ec55f9844e8e3e9d05d87f', ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cristexhub-dev-runtime-source-boundary'): '5c0bcd5caf98d43b08d7e4da068187b8564c1518e2346ea8abffccdd56309b52', ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cristexhub-dev-runtime-source-boundary'): 'fec85c253bbae0d908fba8bd0091692a88100fddbc80cf69ec97e270268e3712', ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-cristexhub-dev-runtime-static-secret-boundary'): '22140582b7cee0e14432c75260ae8cc1edfcadcfee06f790fd92ce3060ec5684', ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-cristexhub-dev-runtime-static-secret-boundary'): '3f1f38f75e147d705091073bc0f75dcc23610af950b9d9be5b01fc10411c4136', ('rbac.authorization.k8s.io/v1', 'Role', 'cristexhub-dev', 'infisical-cristexhub-dev-runtime-secret-writer'): '65c97911f0dc219df9a826f59e2578a79c849c6d4bd3fd16ec51e8530b5c991c', ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'cristexhub-dev', 'infisical-cristexhub-dev-runtime-secret-writer'): 'dcbe84bb0be45d8ecf146cd072474730e05f9641685dd96cbe9428e400decff4', ('secrets.infisical.com/v1beta1', 'InfisicalAuth', 'cristexhub-dev', 'cristexhub-dev-infisical-auth'): '1354d0c7e51fe243f333bdcacc3fb87073aa70c75a2cc99513b30f6fb5350dfa', ('secrets.infisical.com/v1beta1', 'InfisicalStaticSecret', 'cristexhub-dev', 'cristexhub-dev-runtime'): '63010973e4425f7757be9fab9a60894d24bf045f14d0f39f0a5a364b1f4ca965', ('secrets.infisical.com/v1beta1', 'InfisicalConnection', 'cristexhub-dev', 'infisical-cloud'): '71a21173e618795af3d0bb0da397f13564f3217cb621bcc9ec2e0e18d88b30af'}
_EXPECTED_IDENTITY_SET_SHA256 = "8b743f04a3fc8caae30f5825ee0c20bf29b35fccbd1cb62b9a756329bfeaeef3"
_EXPECTED_ARGUMENT_KEYS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
_EXPECTED_TASK_SOURCES = {
    "/Users/paul/Projects/cristexweb/ansible/roles/infisical_cristexhub_dev_runtime_bootstrap/tasks/main.yml",
    "/home/paul/projects/cristexweb/ansible/roles/infisical_cristexhub_dev_runtime_bootstrap/tasks/main.yml",
}


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _integer(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only CristexHub DEV runtime Secret seam."""

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start_at_task = context.CLIARGS.get("start_at_task")
        step = bool(context.CLIARGS.get("step"))
        tags = list(context.CLIARGS.get("tags") or [])
        skip_tags = list(context.CLIARGS.get("skip_tags") or [])
        task_source = str(self._task.get_path()).rsplit(":", 1)[0]
        if task_source not in _EXPECTED_TASK_SOURCES:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing CristexHub DEV runtime Secret seam "
                    "mutation outside the canonical guarded role task source"
                ),
            }

        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        token = os.environ.get(
            "CRISTEXWEB_CRISTEXHUB_DEV_RUNTIME_TOKEN", ""
        )
        attestation_path = os.environ.get(
            "CRISTEXWEB_CRISTEXHUB_DEV_RUNTIME_ATTESTATION_FILE", ""
        )
        binding = task_vars.get(
            "cristexhub_dev_runtime_bootstrap_internal_preflight_binding", {}
        )
        try:
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation_content = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation_state = None
            attestation_content = ""

        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256")
            == hashlib.sha256(token.encode()).hexdigest()
            and _integer(binding.get("object_count")) == 13
            and _integer(binding.get("prestate_count")) == 13
            and binding.get("identity_set_sha256") == _EXPECTED_IDENTITY_SET_SHA256
        )
        valid_attestation = (
            os.environ.get("CRISTEXWEB_CRISTEXHUB_DEV_RUNTIME_ENTRYPOINT")
            == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and attestation_state is not None
            and stat.S_ISREG(attestation_state.st_mode)
            and not stat.S_ISLNK(attestation_state.st_mode)
            and stat.S_IMODE(attestation_state.st_mode) == 0o600
            and attestation_state.st_uid == os.getuid()
            and attestation_content == f"{token}:entrypoint"
        )
        if (
            not valid_attestation
            or not valid_binding
            or task_vars.get("cristexhub_dev_runtime_bootstrap_approved") is not True
            or task_vars.get("cristexhub_dev_runtime_bootstrap_state") != "present"
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing CristexHub DEV runtime Secret seam "
                    "mutation without the validated wrapper attestation and "
                    "complete preflight binding"
                ),
            }

        if not isinstance(definition, dict):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing arguments outside the "
                    "exact present-only CristexHub DEV runtime Secret seam"
                ),
            }
        metadata = definition.get("metadata") or {}
        identity = (
            definition.get("apiVersion"),
            definition.get("kind"),
            metadata.get("namespace", ""),
            metadata.get("name"),
        )
        if (
            set(args) != _EXPECTED_ARGUMENT_KEYS
            or args.get("state") != "present"
            or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml"
            or args.get("wait") is not False
            or args.get("wait_timeout") != 60
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing arguments outside the "
                    "exact present-only CristexHub DEV runtime Secret seam"
                ),
            }
        if (
            definition.get("kind") == "Secret"
            or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition)
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "MUTATION_ARGUMENT_GUARD: refusing an unknown, changed, or "
                    "Secret CristexHub DEV runtime Secret seam object"
                ),
            }
        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "TASK_SELECTION_GUARD: refusing CristexHub DEV runtime Secret seam "
                    "mutation under task selection"
                ),
            }

        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
