from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import ActionModule as KubernetesActionModule

_EXPECTED_OBJECT_HASHES = {
    ('v1', 'ConfigMap', 'shared-services', 'oidc-connect-proxy-config'): '9030f5a145cb1a0597c09e646e6063af1a22881285e269c83f2907188afbddf3',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'cristexhub-dev', 'cristexhub-backend-allow-oidc-proxy'): 'f186bef8bc022dc08012e42418d227fc228282246a47246f3a05399fe452fb03',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'cristexhub-dev', 'oauth2-proxy-allow-oidc-proxy'): '6a15389649dfa29a25802071c7630b5576f8ff36b55075d00e64b3a0aa8afc15',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'oidc-connect-proxy-allow-auth-egress'): '6b03dd1081d31d8c128c64231eee309b3570938a3b9f9767a93da9f64ed3641f',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'oidc-connect-proxy-allow-clients'): '2cf2e9d86eb7c97e0fd56c0fef0ac05c8ac19838401909c41695c96e7d048ec0',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'oidc-connect-proxy-allow-dns'): '1c6e1b62e40ad388f5033ceb00e9f80ab62c4cbe87f7bcc23ff6ecbfe51e704b',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'oidc-connect-proxy-default-deny'): '21a51a152e008488dbb90fac6c550833f63e74d47153b93abea66f9f348dc25f',
    ('v1', 'ServiceAccount', 'shared-services', 'oidc-connect-proxy'): 'eb8a14e1f526d468fcd756b510af7d15f0600573dd0bd788aff99bbda16d6087',
    ('apps/v1', 'Deployment', 'shared-services', 'oidc-connect-proxy'): '2a195e654488af090290a2d9b70d9c4201556ef4da3abbc88acb67d5c6643750',
    ('v1', 'Service', 'shared-services', 'oidc-connect-proxy'): '4ead3c00dd5ba42d341878904d36fd1d67ce25eb4dc2a3121a259b67a510d4e6',
}
_EXPECTED_ARGUMENT_KEYS = {'state', 'definition', 'kubeconfig', 'wait', 'wait_timeout'}
_EXPECTED_TASK_SOURCES = {
    '/Users/paul/Projects/cristexweb/ansible/roles/oidc_connect_proxy_bootstrap/tasks/main.yml',
    '/home/paul/projects/cristexweb/ansible/roles/oidc_connect_proxy_bootstrap/tasks/main.yml',
}


def _canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class ActionModule(KubernetesActionModule):
    def run(self, tmp=None, task_vars=None):
        task_vars = task_vars or {}
        source = str(self._task.get_path()).rsplit(':', 1)[0]
        if source not in _EXPECTED_TASK_SOURCES:
            return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD'}
        if context.CLIARGS.get('start_at_task') or context.CLIARGS.get('step') or context.CLIARGS.get('skip_tags'):
            return {'changed': False, 'failed': True, 'msg': 'TASK_SELECTION_GUARD'}
        args = self._task.args
        definition = args.get('definition')
        token = os.environ.get('CRISTEXWEB_OIDC_CONNECT_PROXY_BOOTSTRAP_TOKEN', '')
        path = os.environ.get('CRISTEXWEB_OIDC_CONNECT_PROXY_BOOTSTRAP_ATTESTATION_FILE', '')
        binding = task_vars.get('oidc_connect_proxy_bootstrap_internal_preflight_binding', {})
        try:
            state = os.stat(path, follow_symlinks=False)
            content = Path(path).read_text().strip()
        except (OSError, ValueError):
            state, content = None, ''
        valid = (
            os.environ.get('CRISTEXWEB_OIDC_CONNECT_PROXY_BOOTSTRAP_ENTRYPOINT') == 'v1'
            and re.fullmatch(r'[0-9a-f]{64}', token)
            and state
            and stat.S_ISREG(state.st_mode)
            and stat.S_IMODE(state.st_mode) == 0o600
            and state.st_uid == os.getuid()
            and content == f'{token}:entrypoint'
        )
        valid = valid and (
            isinstance(binding, dict)
            and binding.get('attestation_sha256') == hashlib.sha256(token.encode()).hexdigest()
            and int(binding.get('object_count', -1)) == 10
            and int(binding.get('prestate_count', -1)) == 10
            and binding.get('identity_set_sha256') == 'c748d703754d4a434775ca966a51130151ffcf019b26f7389953c2d4378bfa85'
            and binding.get('namespace_contract') is True
            and binding.get('no_delete_path') is True
        )
        if not valid or task_vars.get('oidc_connect_proxy_bootstrap_approved') is not True or task_vars.get('oidc_connect_proxy_bootstrap_state') != 'present':
            return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD'}
        if not isinstance(definition, dict) or set(args) != _EXPECTED_ARGUMENT_KEYS or args.get('state') != 'present' or args.get('kubeconfig') != '/etc/rancher/k3s/k3s.yaml' or args.get('wait') is not False or args.get('wait_timeout') != 60:
            return {'changed': False, 'failed': True, 'msg': 'MUTATION_ARGUMENT_GUARD'}
        metadata = definition.get('metadata') or {}
        identity = (definition.get('apiVersion'), definition.get('kind'), metadata.get('namespace', ''), metadata.get('name'))
        if definition.get('kind') in {'Secret', 'PersistentVolumeClaim', 'Ingress', 'ServiceMonitor'} or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition):
            return {'changed': False, 'failed': True, 'msg': 'MUTATION_ARGUMENT_GUARD'}
        original = self._task.action
        self._task.action = 'kubernetes.core.k8s'
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original
