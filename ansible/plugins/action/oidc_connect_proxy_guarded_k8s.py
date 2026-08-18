from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import ActionModule as KubernetesActionModule

_EXPECTED_OBJECT_HASHES = {('apps/v1', 'Deployment', 'shared-services', 'oidc-connect-proxy'): '989f70665225a0ec5aaa71967d9c7fd545f750da9dc7aa725c51f68a029b2607',
 ('networking.k8s.io/v1', 'NetworkPolicy', 'cristexhub-dev', 'cristexhub-backend-allow-oidc-proxy'): 'b71a698a978952c068220db0dfa842409baa4394b77672bd04c532ec81b73f05',
 ('networking.k8s.io/v1', 'NetworkPolicy', 'cristexhub-dev', 'oauth2-proxy-allow-oidc-proxy'): '6a15389649dfa29a25802071c7630b5576f8ff36b55075d00e64b3a0aa8afc15',
 ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'oidc-connect-proxy-allow-auth-egress'): '6b03dd1081d31d8c128c64231eee309b3570938a3b9f9767a93da9f64ed3641f',
 ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'oidc-connect-proxy-allow-clients'): '22c4eb3c57e8f335eba677caaf0f5fe39098c3a2d8b3ab5c989e256300a8f7ab',
 ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'oidc-connect-proxy-allow-dns'): '1c6e1b62e40ad388f5033ceb00e9f80ab62c4cbe87f7bcc23ff6ecbfe51e704b',
 ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'oidc-connect-proxy-default-deny'): '21a51a152e008488dbb90fac6c550833f63e74d47153b93abea66f9f348dc25f',
 ('v1', 'ConfigMap', 'shared-services', 'oidc-connect-proxy-config'): '9f2baecbdca48fa66855df9bca961f9946f4a10b6077bf819231d2ac1651e9b4',
 ('v1', 'Service', 'shared-services', 'oidc-connect-proxy'): '4ead3c00dd5ba42d341878904d36fd1d67ce25eb4dc2a3121a259b67a510d4e6',
 ('v1', 'ServiceAccount', 'shared-services', 'oidc-connect-proxy'): 'eb8a14e1f526d468fcd756b510af7d15f0600573dd0bd788aff99bbda16d6087'}
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
