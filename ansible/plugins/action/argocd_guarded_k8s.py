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

_EXPECTED_OBJECT_HASHES = {
    ('argoproj.io/v1alpha1', 'AppProject', 'argocd', 'default'): 'e48d5332aaa18c8528ae19f1b83bf00c86450ab39a66c363e4816403ee6cfd56',
    ('v1', 'ConfigMap', 'argocd', 'argocd-cm'): 'c39ba507f18a496857ff8b4ae8530901fe635949bf49717516f421170892c0ae',
    ('v1', 'ConfigMap', 'argocd', 'argocd-cmd-params-cm'): '985c443cb0a810c3c7441a767c34982338ce236955b3118e3afe87cc527e0621',
    ('v1', 'ConfigMap', 'argocd', 'argocd-gpg-keys-cm'): '6a0e06577b23b81c66c2cb98d403fe38b4a2f4b3259e42e31e2b60a85033fa50',
    ('v1', 'ConfigMap', 'argocd', 'argocd-rbac-cm'): '99e5a36e57c3315f8e1c2ae63035f5c9a08f206ee2e14ef047fd83bed0b404e4',
    ('v1', 'ConfigMap', 'argocd', 'argocd-redis-health-configmap'): 'b0ef48a7933de03be6a72f1c90459772ce166cc38fbb93c2aaee7b820cac3982',
    ('v1', 'ConfigMap', 'argocd', 'argocd-ssh-known-hosts-cm'): 'a4c92ab2a7259deeb80a1be0f070e59706cd974d1860a43289ce8d120244ff67',
    ('v1', 'ConfigMap', 'argocd', 'argocd-tls-certs-cm'): '9c8c5faa26e5d8a681535c73c943e7ea72416d24b4e6e8657ae1661f622361a6',
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition', '', 'applications.argoproj.io'): '6a13379ac5654bff09a1421b5b636e3e94d46be8de080b25f8df01ce4f2b494c',
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition', '', 'applicationsets.argoproj.io'): 'a1da609309fc170160d9a96e8638d4cf449067bb726ee8f1fb2c6ea1617dd298',
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition', '', 'appprojects.argoproj.io'): 'ba1b0feb4767eb38a3fa76506437e34882638662979290de38c39a42edc8b3e0',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'argocd', 'argocd-controller-egress'): 'c7e9c0d012b82e87257fc939dea8592b0f9e9aca049a45ee0ca515d1043d7ef8',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'argocd', 'argocd-default-deny'): 'f36487db6ef710d45665ca69007c57d8527f03587bab7a59b5e7e54700ba8485',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'argocd', 'argocd-redis-ingress'): '6151b363e9961d7a000de7bc73c39a1bb090cbd6685f4b7976a4699bcacdb394',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'argocd', 'argocd-repo-server-egress'): '235cbec91dccb2d532da2d6895d55b580b10c978acf16d78c29c8eaba90342fc',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'argocd', 'argocd-repo-server-ingress'): '799ff3b1fc7f59f9723b67dec829a9a846ebb7dadd2190fd946659ce1af666f4',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'argocd', 'argocd-server-egress'): '8bd7c812fb7d60f1e20941c508ca8ebca9a89e0dfc37ec0c89f04c19f7585adf',
    ('rbac.authorization.k8s.io/v1', 'Role', 'argocd', 'argocd-application-controller'): '0587a7eabd73f3c2b0e0f9a15460cabab61e9c8d3fe707ee87f684fc69f093d0',
    ('rbac.authorization.k8s.io/v1', 'Role', 'argocd', 'argocd-server'): '0639dc10bd1a90ae01063d3848c3cb181bdb657d9a6ce34eadace33ee07ef477',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'argocd', 'argocd-application-controller'): 'bfe5fc197ce3b208c3af80d4579469d660b56eca31bb9352344d26be7dde5254',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'argocd', 'argocd-server'): 'ba5296fb48cba19f8c6c6d8a3b87c5935d83e4cc2d410257138aa10d6044f496',
    ('v1', 'ServiceAccount', 'argocd', 'argocd-application-controller'): 'ff04871bfff1dce61066055d34a0e069654661aef494d23f64297fae926a9640',
    ('v1', 'ServiceAccount', 'argocd', 'argocd-redis'): 'bb42f76a7315e482e2c029c4de5e21340111eefbc0ee29d42cb3ba085b3a9107',
    ('v1', 'ServiceAccount', 'argocd', 'argocd-repo-server'): '1339f4a42652325f4fa74d7e0acc713f999b72bb045161ff10fc40a0c36164e7',
    ('v1', 'ServiceAccount', 'argocd', 'argocd-server'): '1f31e8c44625170dd56992f760045f4f3dff840fc4edf3a620d51ebff6e74956',
    ('apps/v1', 'Deployment', 'argocd', 'argocd-redis'): '605bad4a1e8bf59bc0e1631135666b76203facd0f1243f858de744863a2b89ef',
    ('apps/v1', 'Deployment', 'argocd', 'argocd-repo-server'): 'b246cbea64ddbd8fd0772facb339a691ce7d1109af4042da299f6d484c06dda6',
    ('apps/v1', 'Deployment', 'argocd', 'argocd-server'): '13d426d8c3326f2884fad79a08841231c22937787cf25e7caf46f722b22ee26b',
    ('v1', 'Service', 'argocd', 'argocd-redis'): '55a5a55c920d15e350ca2048a9938fbe4bf9c88070f57034d7d7d88a571ca178',
    ('v1', 'Service', 'argocd', 'argocd-repo-server'): '39e11c23843e0be8a160dc289609dc48d948088783c88e8fb00fc5ff850a9969',
    ('v1', 'Service', 'argocd', 'argocd-server'): 'f973fc68b6b94bf283c1337e42509660d62617f1554cc96698f05ff77ad5debd',
    ('apps/v1', 'StatefulSet', 'argocd', 'argocd-application-controller'): 'd763f786816966eca9a30ef70967896dfb646edf2140ca67ee5440f695c9e994',
}


_EXPECTED_ARGUMENT_KEYS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
_EXPECTED_TASK_SOURCES = {
    "/Users/paul/Projects/cristexweb/ansible/roles/argocd_bootstrap/tasks/main.yml",
    "/home/paul/projects/cristexweb/ansible/roles/argocd_bootstrap/tasks/main.yml",
}
_EXPECTED_CRD_ARGUMENT_KEYS = _EXPECTED_ARGUMENT_KEYS | {"wait_condition"}
_EXPECTED_CRD_WAIT_CONDITION = {"type": "Established", "status": "True"}


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only Argo CD idle closure."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
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
                    "ENTRYPOINT_GUARD: refusing Argo CD mutation outside the "
                    "canonical guarded role task source"
                ),
            }
        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        token = os.environ.get("CRISTEXWEB_ARGOCD_BOOTSTRAP_TOKEN", "")
        attestation_path = os.environ.get(
            "CRISTEXWEB_ARGOCD_BOOTSTRAP_ATTESTATION_FILE", ""
        )
        binding = task_vars.get(
            "argocd_bootstrap_internal_preflight_binding", {}
        )
        try:
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation_content = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation_state = None
            attestation_content = ""
        expected_attestation_sha256 = hashlib.sha256(token.encode()).hexdigest()
        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256") == expected_attestation_sha256
            and int(binding.get("object_count", -1)) == 32
            and binding.get("identity_set_sha256") == (
                # Canonical identity digest: bb81e0babfa314a91e52479e71d778b79c81df77bf5b74a9f2cb1bf08d692b81
                # Jinja runtime joins the protected list with literal ``\\n``.
                "53672a1267926abdbe773a90cfaa84cf958b343fde292c1c2d2e199f2c16778c"
            )
            and int(binding.get("crd_count", -1)) == 3
            and int(binding.get("prestate_count", -1)) == 32
            and int(binding.get("deferred_custom_resource_count", -1)) in (0, 1)
            and (
                int(binding.get("deferred_custom_resource_count", -1)) == 0
                or self._play_context.check_mode
            )
            and int(binding.get("secret_count", -1)) == 3
            and binding.get("namespace_contract") is True
            and binding.get("service_contract") is True
        )
        valid_attestation = (
            os.environ.get("CRISTEXWEB_ARGOCD_BOOTSTRAP_ENTRYPOINT") == "v1"
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
            or task_vars.get("argocd_bootstrap_approved") is not True
            or task_vars.get("argocd_bootstrap_state") != "present"
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing Argo CD mutation without the "
                    "validated wrapper attestation and complete preflight binding"
                ),
            }
        definition = args.get("definition")
        if not isinstance(definition, dict):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing arguments outside the exact present-only Argo CD closure"}
        metadata = definition.get("metadata") or {}
        identity = (definition.get("apiVersion"), definition.get("kind"), metadata.get("namespace", ""), metadata.get("name"))
        is_crd = definition.get("kind") == "CustomResourceDefinition"
        expected_argument_keys = _EXPECTED_CRD_ARGUMENT_KEYS if is_crd else _EXPECTED_ARGUMENT_KEYS
        valid_wait = (
            args.get("wait") is True
            and args.get("wait_condition") == _EXPECTED_CRD_WAIT_CONDITION
            if is_crd
            else args.get("wait") is False
        )
        if set(args) != expected_argument_keys or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml" or not valid_wait or args.get("wait_timeout") != 60:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing arguments outside the exact present-only Argo CD closure"}
        if definition.get("kind") == "Secret" or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing an unknown, changed, or Secret Argo CD object"}
        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {"changed": False, "failed": True, "msg": "TASK_SELECTION_GUARD: refusing Argo CD mutation under task selection"}
        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
