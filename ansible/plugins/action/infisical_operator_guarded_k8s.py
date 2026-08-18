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
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-auth-boundary'): 'a0d80a5bad4c3c52fdf95dfae20b912db7e3488f4a1be90f409f00895938b6d5',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-auth-boundary'): '4b3259c79f08a96154a47254fa02b6bcfafae2904c9c263637914be64c07f6d5',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-connection-boundary'): '56280a16a89f4b512b3f92a91d2fa7f4402399bdff69cfb0c340839f08ce85c5',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-connection-boundary'): '664ad0d3d245dcd6497485455edf2912da4fa4d2aa6b7243146361fc5020e48e',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-dynamic-secret-boundary'): '2537e670376a526f41f43347a2ae5037052929a8ba981ee4f91aef57820a0994',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-dynamic-secret-boundary'): '8f6f65cfda5305036e5dcd5399104c6cbae79e1f55ca0d8c12febf01cf499a81',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-push-secret-boundary'): 'abb1279c9b9bd85b8ba01ee2bd7e86fb49901c708762e20d05a946860463e90f',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-push-secret-boundary'): 'ee2b3b536eadedd89433cdbe00585a214bedd0720e8d81942b3a996e3182a328',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-secret-boundary'): '57f31bf17d21b487d9e1b671dc7b1362aaa87f026ba89f000c6ff81f74a9ccae',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-secret-boundary'): '6adf6fb2459c26df41b00c7aba6450c27e489fa686d738bfb29ebd4eefd548f3',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'infisical-static-secret-boundary'): '832215eddbb15d770c1796439a2b44cfb9089950a68c91629f2d780b08d82ad6',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'infisical-static-secret-boundary'): 'ab9edcd92db178c3d34a754f510a11eabb92940a36d12cb2dde40e7f7a5c3b70',
    ('apps/v1', 'Deployment', 'shared-services', 'infisical-operator-controller'): '1c9ca4a23ef5b5a6fb5862a1efcf581b8ce4e4405947ae0e234e570e9587a987',
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition', '', 'infisicalauths.secrets.infisical.com'): '7f42a95da11f97758214bb8d6d1a177a848d02d42e9c6154fb8f84724c234326',
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition', '', 'infisicalconnections.secrets.infisical.com'): '41e6e2c61260de61229d997f67426c26fcddcb4e584cef45485646111ca69181',
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition', '', 'infisicaldynamicsecrets.secrets.infisical.com'): 'b95d44aef7023641d00a552e3dbc9b14667de82983d8911a2fd73bcf25ab5f91',
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition', '', 'infisicalpushsecrets.secrets.infisical.com'): '0c54458642f347452e3c1e307e896d2ea5c1a22c5f1768b332afc99621b7b70e',
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition', '', 'infisicalsecrets.secrets.infisical.com'): 'c6c6ec44ebc89ec80d231892300bc43bc2bd2fe185b6e835c8a3c9db0b0b68c5',
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition', '', 'infisicalstaticsecrets.secrets.infisical.com'): '057ab7cb5b343dac044d627350c396056798bb2f4bb7096b87bbc7544eee45ad',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'infisical-operator-allow-api'): '4cb16e5388015ea9aae12787fc52558e9ef17e79640b8434f7ec6bd91c60ace4',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'infisical-operator-allow-dns'): '704e12ee3f8194423adb402329348ed0d97a368c7a46625ccd8458da99df139b',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'infisical-operator-allow-proxy'): '084c4f4e3958d10974120001b27db3d3b6f76649bc7937d085443948b568fe0f',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'infisical-operator-default-deny'): '61e257689c071585b4de18a8ae75566890376411ce3748f4834adc42c4e93af3',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'infisical-proxy-allow-dns'): 'e27f0a87f41eca215d7bae816cc862915d4f12226a23332687408ada90d68a0b',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'infisical-proxy-allow-external-https'): '9dc44e4314ca42eb1d563535730ae20c811e9ae7ff99c8a5f875a9447f472e23',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'infisical-proxy-allow-operator'): 'cbb771d5776b96882f18204d1b75b37cc01be3ba650ed88f4e69bde5756c7ee0',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'infisical-proxy-default-deny'): '5e0ea313a3c00a2aaa59a9e19617d275d085f6c891370818091e72ac907b78a3',
    ('v1', 'ConfigMap', 'shared-services', 'infisical-egress-proxy'): '316ae27fb54908a227f27dbd1c515aaa326d65d835789e4e7beb5044f9f55e56',
    ('apps/v1', 'Deployment', 'shared-services', 'infisical-egress-proxy'): '544f46636ad0e24c1ff8c0d79276a5f8f73a3b8cb4c9aaa509ce56976fa3544f',
    ('v1', 'Service', 'shared-services', 'infisical-egress-proxy'): 'bab34babc51d833e660dca64ddfd72850932f5c5c00fcb7294cbbce8b9f6de6e',
    ('v1', 'ServiceAccount', 'shared-services', 'infisical-operator-controller'): 'bf36af4af47dc8c8b8df12c4b41855b036882180098131352634fc387920b792',
    ('rbac.authorization.k8s.io/v1', 'Role', 'shared-services', 'infisical-operator-leader-election'): 'd5218ad9fc5e308d583f0d7aee1281bfd494ff59dc53d73b2ea5ea112f88c007',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'shared-services', 'infisical-operator-leader-election'): 'dd46e7a333843000d89acfadddb4721fbbc76fb013d96f519b080e442786bfed',
    ('rbac.authorization.k8s.io/v1', 'Role', 'argocd', 'infisical-operator-manager'): '3cfdec9ae3381288a8ee1f38c3ee767e0927b7b52e1a422093c4336b566c2cf6',
    ('rbac.authorization.k8s.io/v1', 'Role', 'cristexhub-dev', 'infisical-operator-manager'): 'fc7b9bec413011bebc7cb594c1dd879a45bd583f9f6b3ce79da796d405687d2f',
    ('rbac.authorization.k8s.io/v1', 'Role', 'cristexhub-prod', 'infisical-operator-manager'): '1fa476d9b1604e1a8cced0fb0ced6f6d877bdbeeb94a6689f087d6ac3f5e8602',
    ('rbac.authorization.k8s.io/v1', 'Role', 'platform-edge', 'infisical-operator-manager'): '0994ab8bd09c31eab914af4b40554bdeae334c73fa6b1060ad55aab4946c0bfe',
    ('rbac.authorization.k8s.io/v1', 'Role', 'shared-services', 'infisical-operator-manager'): '93d4c93736c897f417d4b4852c60321869ce66a87a1460133a017adff0dd2c2f',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'argocd', 'infisical-operator-manager'): '2c345c7df6437be34e1c720181b77541e3b81f657bcf42ab36c8c53884d1cf87',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'cristexhub-dev', 'infisical-operator-manager'): '8da014ed8d1b35011c4fc0a0ef32a8a640d04827be6b339b912dc3b4ab7d08c6',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'cristexhub-prod', 'infisical-operator-manager'): '5f5e3995330df72407911522a41cb0718932c552f08fd0cebe16e82fb95ad34e',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'platform-edge', 'infisical-operator-manager'): '46de61159cb67208490028dd9666c4db663e8082227bab14003e8afaa4e34fda',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'shared-services', 'infisical-operator-manager'): '9d6333a5979cdf887d1f13e1663c60b007d5b141d7da0ad74512d60eca61a26c',
    ('v1', 'ServiceAccount', 'shared-services', 'infisical-egress-proxy'): 'f55214941e54d1215e8c9c8b9e383bc48248b753f707c3dd9436464fb4629ed4',
}
_EXPECTED_OBJECT_IDENTITIES = (
    "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicalauths.secrets.infisical.com",
    "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicalconnections.secrets.infisical.com",
    "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicaldynamicsecrets.secrets.infisical.com",
    "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicalpushsecrets.secrets.infisical.com",
    "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicalsecrets.secrets.infisical.com",
    "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicalstaticsecrets.secrets.infisical.com",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-auth-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-auth-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-connection-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-connection-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-dynamic-secret-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-dynamic-secret-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-push-secret-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-push-secret-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-secret-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-secret-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-static-secret-boundary",
    "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-static-secret-boundary",
    "apps/v1|Deployment|shared-services|infisical-operator-controller",
    "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-operator-allow-api",
    "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-operator-allow-dns",
    "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-operator-allow-proxy",
    "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-operator-default-deny",
    "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-proxy-allow-dns",
    "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-proxy-allow-external-https",
    "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-proxy-allow-operator",
    "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-proxy-default-deny",
    "v1|ConfigMap|shared-services|infisical-egress-proxy",
    "apps/v1|Deployment|shared-services|infisical-egress-proxy",
    "v1|Service|shared-services|infisical-egress-proxy",
    "v1|ServiceAccount|shared-services|infisical-operator-controller",
    "rbac.authorization.k8s.io/v1|Role|shared-services|infisical-operator-leader-election",
    "rbac.authorization.k8s.io/v1|RoleBinding|shared-services|infisical-operator-leader-election",
    "rbac.authorization.k8s.io/v1|Role|argocd|infisical-operator-manager",
    "rbac.authorization.k8s.io/v1|Role|cristexhub-dev|infisical-operator-manager",
    "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|infisical-operator-manager",
    "rbac.authorization.k8s.io/v1|Role|shared-services|infisical-operator-manager",
    "rbac.authorization.k8s.io/v1|Role|platform-edge|infisical-operator-manager",
    "rbac.authorization.k8s.io/v1|RoleBinding|platform-edge|infisical-operator-manager",
    "rbac.authorization.k8s.io/v1|RoleBinding|argocd|infisical-operator-manager",
    "rbac.authorization.k8s.io/v1|RoleBinding|cristexhub-dev|infisical-operator-manager",
    "rbac.authorization.k8s.io/v1|RoleBinding|cristexhub-prod|infisical-operator-manager",
    "rbac.authorization.k8s.io/v1|RoleBinding|shared-services|infisical-operator-manager",
    "v1|ServiceAccount|shared-services|infisical-egress-proxy",
)
_EXPECTED_ARGUMENT_KEYS = {"state", "definition", "kubeconfig", "wait", "wait_timeout"}
_EXPECTED_TASK_SOURCES = {
    "/Users/paul/Projects/cristexweb/ansible/roles/infisical_operator_bootstrap/tasks/main.yml",
    "/home/paul/projects/cristexweb/ansible/roles/infisical_operator_bootstrap/tasks/main.yml",
}


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _exact_count(value: Any, expected: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value == expected


class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only Infisical idle closure."""

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
                    "ENTRYPOINT_GUARD: refusing Infisical mutation outside the "
                    "canonical guarded role task source"
                ),
            }
        args = self._task.args
        definition = args.get("definition")
        task_vars = task_vars or {}
        token = os.environ.get("CRISTEXWEB_INFISICAL_BOOTSTRAP_TOKEN", "")
        attestation_path = os.environ.get(
            "CRISTEXWEB_INFISICAL_BOOTSTRAP_ATTESTATION_FILE", ""
        )
        binding = task_vars.get(
            "infisical_operator_bootstrap_internal_preflight_binding", {}
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
            and _exact_count(binding.get("object_count"), 44)
            and _exact_count(binding.get("crd_count"), 6)
            and _exact_count(binding.get("prestate_count"), 44)
            and _exact_count(binding.get("proxy_secret_count"), 3)
            and _exact_count(binding.get("namespace_count"), 5)
            and binding.get("namespace_contract") is True
            and _exact_count(binding.get("prod_denied_kind_count"), 3)
            and binding.get("prod_denied_kinds_absent") is True
            and binding.get("identity_keys") == list(_EXPECTED_OBJECT_IDENTITIES)
            and binding.get("api_service_contract") is True
            and binding.get("service_contract") is True
        )
        valid_attestation = (
            os.environ.get("CRISTEXWEB_INFISICAL_BOOTSTRAP_ENTRYPOINT") == "v1"
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
            or task_vars.get("infisical_operator_bootstrap_approved") is not True
            or task_vars.get("infisical_operator_bootstrap_state") != "present"
        ):
            return {
                "changed": False,
                "failed": True,
                "msg": (
                    "ENTRYPOINT_GUARD: refusing Infisical mutation without the "
                    "validated wrapper attestation and complete preflight binding"
                ),
            }
        definition = args.get("definition")
        if set(args) != _EXPECTED_ARGUMENT_KEYS or args.get("state") != "present" or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml" or args.get("wait") is not False or args.get("wait_timeout") != 60 or not isinstance(definition, dict):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing arguments outside the exact present-only Infisical closure"}
        metadata = definition.get("metadata") or {}
        identity = (definition.get("apiVersion"), definition.get("kind"), metadata.get("namespace", ""), metadata.get("name"))
        if definition.get("kind") == "Secret" or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing an unknown, changed, or Secret Infisical object"}
        if start_at_task or step or tags not in ([], ["all"]) or skip_tags:
            return {"changed": False, "failed": True, "msg": "TASK_SELECTION_GUARD: refusing Infisical mutation under task selection"}
        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
