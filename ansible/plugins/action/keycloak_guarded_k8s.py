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
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'keycloak-allow-dns'): '46d30870622a3e117fb1f96917a6bd7eebdb78ca304f73462f90263e8918ace6',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'keycloak-allow-postgresql'): '7063ee97ed33e6aff5c81b00c8f91da5cfbd2b56e129277763493b5c94f0e4d4',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'keycloak-default-deny'): '0f8bea5dee6a64cd3e2bc79277c78bfa79fd589e4d794a333b7e112aabb7b729',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'keycloak-private-ingress'): 'cd1a018187695a7a34807d12a604bf1fd4ab40d660057cca6a8b8559bc8889f2',
    ('v1', 'ServiceAccount', 'shared-services', 'keycloak'): 'ed90a0cbed8a407b9ac89912267befc31e4d3c7f1a5b05ece8a676f05036353e',
    ('v1', 'ConfigMap', 'shared-services', 'keycloak-realm-cristexhub'): '5268883af726ec0f6f22f638155e16533235c2b5c548c43d4c8aa2ea086b75ec',
    ('apps/v1', 'Deployment', 'shared-services', 'keycloak'): '7c2cdce2b6b0f6b45d1ccad138ed9c8f3f403b040139d4c7adbb13524b8147b7',
    ('v1', 'Service', 'shared-services', 'keycloak'): 'a6d6285f1f0c315f2d2fd8d3adb7adad02925cd1ed2d176f9ca403a3750bcf2f',
}
_EXPECTED_ARGUMENT_KEYS = {'state', 'definition', 'kubeconfig', 'wait', 'wait_timeout'}
_EXPECTED_TASK_SOURCES = {
    '/Users/paul/Projects/cristexweb/ansible/roles/keycloak_bootstrap/tasks/main.yml',
    '/home/paul/projects/cristexweb/ansible/roles/keycloak_bootstrap/tasks/main.yml',
}

def _canonical_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only private Keycloak closure."""
    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        task_vars = task_vars or {}
        source = str(self._task.get_path()).rsplit(':', 1)[0]
        if source not in _EXPECTED_TASK_SOURCES:
            return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD: refusing Keycloak mutation outside the canonical role'}
        if context.CLIARGS.get('start_at_task') or context.CLIARGS.get('step') or list(context.CLIARGS.get('tags') or []) not in ([], ['all']) or context.CLIARGS.get('skip_tags'):
            return {'changed': False, 'failed': True, 'msg': 'TASK_SELECTION_GUARD: refusing Keycloak task selection'}
        args = self._task.args
        definition = args.get('definition')
        token = os.environ.get('CRISTEXWEB_KEYCLOAK_BOOTSTRAP_TOKEN', '')
        path = os.environ.get('CRISTEXWEB_KEYCLOAK_BOOTSTRAP_ATTESTATION_FILE', '')
        binding = task_vars.get('keycloak_bootstrap_internal_preflight_binding', {})
        try:
            st = os.stat(path, follow_symlinks=False)
            content = Path(path).read_text().strip()
        except (OSError, ValueError):
            st, content = None, ''
        valid_attestation = (os.environ.get('CRISTEXWEB_KEYCLOAK_BOOTSTRAP_ENTRYPOINT') == 'v1' and re.fullmatch(r'[0-9a-f]{64}', token) is not None and st is not None and stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode) and stat.S_IMODE(st.st_mode) == 0o600 and st.st_uid == os.getuid() and content == f'{token}:entrypoint')
        valid_binding = (isinstance(binding, dict) and binding.get('attestation_sha256') == hashlib.sha256(token.encode()).hexdigest() and int(binding.get('object_count', -1)) == 8 and binding.get('identity_set_sha256') == 'f44c9e2b7bfff7d7b3365a1f82b3910fe4741969b428fcebd94cff80e53ed912' and int(binding.get('prestate_count', -1)) == 8 and int(binding.get('secret_count', -1)) == 3 and binding.get('namespace_contract') is True and binding.get('service_contract') is True and binding.get('no_delete_path') is True)
        if not valid_attestation or not valid_binding or task_vars.get('keycloak_bootstrap_approved') is not True or task_vars.get('keycloak_bootstrap_state') != 'present':
            return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD: refusing Keycloak mutation without attestation and preflight binding'}
        if not isinstance(definition, dict) or set(args) != _EXPECTED_ARGUMENT_KEYS or args.get('state') != 'present' or args.get('kubeconfig') != '/etc/rancher/k3s/k3s.yaml' or args.get('wait') is not False or args.get('wait_timeout') != 60:
            return {'changed': False, 'failed': True, 'msg': 'MUTATION_ARGUMENT_GUARD: refusing Keycloak arguments'}
        metadata = definition.get('metadata') or {}
        identity = (definition.get('apiVersion'), definition.get('kind'), metadata.get('namespace', ''), metadata.get('name'))
        if definition.get('kind') in {'Secret', 'PersistentVolumeClaim', 'Ingress', 'ServiceMonitor'} or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition):
            return {'changed': False, 'failed': True, 'msg': 'MUTATION_ARGUMENT_GUARD: refusing unknown, changed, or forbidden Keycloak object'}
        original = self._task.action
        self._task.action = 'kubernetes.core.k8s'
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original
