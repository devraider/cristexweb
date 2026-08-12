from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import ActionModule as KubernetesActionModule

_EXPECTED_OBJECT_HASHES = {
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'shared-rabbitmq-allow-client'): '1ddaf2b106b73264dddf113932136c7cb108112074c0dff4efb3619838c95602',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'shared-rabbitmq-allow-dns'): '8da7b3b828919de699caa2cf08f433e2819e5007b35fe4b21ed43eb34f578a9a',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'shared-rabbitmq-allow-management'): '800a4aff94fb5e62bd85fe3307ec144b995ce1217bba4d1ed6c7375aef69c543',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'shared-rabbitmq-default-deny'): '68f1bf1fc49db500ae169d7d64d0fc4e39dec60707865c4dfa6df1c76e86fee2',
    ('v1', 'ServiceAccount', 'shared-services', 'shared-rabbitmq'): '2c042d1bec06a4e04beaad4cc157e29db16bad77e66c9e544d37ee3e26b03d63',
    ('v1', 'ConfigMap', 'shared-services', 'shared-rabbitmq-config'): '2e173ef84ea82b15a00660c4ffb77989bf2da186e60656186b1f0f2439823041',
    ('v1', 'Service', 'shared-services', 'shared-rabbitmq-headless'): '57f28c3f60ea236890de9669e79c0652a38eb7690bc3f6f3b11af07460216dc2',
    ('v1', 'Service', 'shared-services', 'shared-rabbitmq-management'): 'd9ff999c6bb9d11edca3e19fe393a90efc110a5b9f4fdb2948b6299674b84372',
    ('v1', 'Service', 'shared-services', 'shared-rabbitmq'): '6a4c9eb21301940011bcd646d0f71dcf022b6b8db3be8c9ee7c0a50d79ae5964',
    ('apps/v1', 'StatefulSet', 'shared-services', 'shared-rabbitmq'): '2e2c8849755d0aedb466d12f01119eb2dbf8b50a21cc563bbdcbe0761ad2ed00',
}
_EXPECTED_ARGUMENT_KEYS = {'state', 'definition', 'kubeconfig', 'wait', 'wait_timeout'}
_EXPECTED_TASK_SOURCES = {
    '/Users/paul/Projects/cristexweb/ansible/roles/rabbitmq_bootstrap/tasks/main.yml',
    '/home/paul/projects/cristexweb/ansible/roles/rabbitmq_bootstrap/tasks/main.yml',
}

def _canonical_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only private RabbitMQ closure."""
    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        task_vars = task_vars or {}
        source = str(self._task.get_path()).rsplit(':', 1)[0]
        if source not in _EXPECTED_TASK_SOURCES:
            return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD: refusing RabbitMQ mutation outside the canonical role'}
        if context.CLIARGS.get('start_at_task') or context.CLIARGS.get('step') or list(context.CLIARGS.get('tags') or []) not in ([], ['all']) or context.CLIARGS.get('skip_tags'):
            return {'changed': False, 'failed': True, 'msg': 'TASK_SELECTION_GUARD: refusing RabbitMQ task selection'}
        args = self._task.args
        definition = args.get('definition')
        token = os.environ.get('CRISTEXWEB_RABBITMQ_BOOTSTRAP_TOKEN', '')
        path = os.environ.get('CRISTEXWEB_RABBITMQ_BOOTSTRAP_ATTESTATION_FILE', '')
        binding = task_vars.get('rabbitmq_bootstrap_internal_preflight_binding', {})
        try:
            st = os.stat(path, follow_symlinks=False)
            content = Path(path).read_text().strip()
        except (OSError, ValueError):
            st, content = None, ''
        valid_attestation = (os.environ.get('CRISTEXWEB_RABBITMQ_BOOTSTRAP_ENTRYPOINT') == 'v1' and re.fullmatch(r'[0-9a-f]{64}', token) is not None and st is not None and stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode) and stat.S_IMODE(st.st_mode) == 0o600 and st.st_uid == os.getuid() and content == f'{token}:entrypoint')
        valid_binding = (isinstance(binding, dict) and binding.get('attestation_sha256') == hashlib.sha256(token.encode()).hexdigest() and int(binding.get('object_count', -1)) == 10 and binding.get('identity_set_sha256') == '29a53fb0f3a280db0bdd5c0e59b69b56a4cf031c2e1a9da5f92170fae1e0bb5e' and int(binding.get('prestate_count', -1)) == 10 and int(binding.get('secret_count', -1)) == 4 and binding.get('namespace_contract') is True and binding.get('service_contract') is True and binding.get('no_delete_path') is True)
        if not valid_attestation or not valid_binding or task_vars.get('rabbitmq_bootstrap_approved') is not True or task_vars.get('rabbitmq_bootstrap_state') != 'present':
            return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD: refusing RabbitMQ mutation without attestation and preflight binding'}
        if not isinstance(definition, dict) or set(args) != _EXPECTED_ARGUMENT_KEYS or args.get('state') != 'present' or args.get('kubeconfig') != '/etc/rancher/k3s/k3s.yaml' or args.get('wait') is not False or args.get('wait_timeout') != 60:
            return {'changed': False, 'failed': True, 'msg': 'MUTATION_ARGUMENT_GUARD: refusing RabbitMQ arguments'}
        metadata = definition.get('metadata') or {}
        identity = (definition.get('apiVersion'), definition.get('kind'), metadata.get('namespace', ''), metadata.get('name'))
        if definition.get('kind') in {'Secret', 'PersistentVolumeClaim', 'Ingress', 'ServiceMonitor'} or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition):
            return {'changed': False, 'failed': True, 'msg': f'MUTATION_ARGUMENT_GUARD: refusing unknown, changed, or forbidden RabbitMQ object identity={identity!r} actual_hash={_canonical_hash(definition)}'}
        original = self._task.action
        self._task.action = 'kubernetes.core.k8s'
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original
