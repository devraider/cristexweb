from __future__ import annotations
import hashlib, json, os, re, stat
from pathlib import Path
from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import ActionModule as KubernetesActionModule

_EXPECTED_OBJECT_HASHES = {
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'keycloak-route-allow-traefik'): '14d2efe72a3c2092a28aeadb6b89a42c44b376090eda45f5a118c10435c12718',
    ('networking.k8s.io/v1', 'Ingress', 'shared-services', 'keycloak-auth'): '6bc4a462f1ab8b6c50fd726f2eb1377a647b273a0725e6e23b9b7cda37da5286',
}
_EXPECTED_ARGUMENT_KEYS = {'state', 'definition', 'kubeconfig', 'wait', 'wait_timeout'}
_EXPECTED_TASK_SOURCES = {
    '/Users/paul/Projects/cristexweb/ansible/roles/keycloak_route_bootstrap/tasks/main.yml',
    '/home/paul/projects/cristexweb/ansible/roles/keycloak_route_bootstrap/tasks/main.yml',
}
def _canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
class ActionModule(KubernetesActionModule):
    def run(self, tmp=None, task_vars=None):
        task_vars = task_vars or {}
        source = str(self._task.get_path()).rsplit(':', 1)[0]
        if source not in _EXPECTED_TASK_SOURCES or context.CLIARGS.get('start_at_task') or context.CLIARGS.get('step') or context.CLIARGS.get('skip_tags'):
            return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD'}
        args = self._task.args
        definition = args.get('definition')
        token = os.environ.get('CRISTEXWEB_KEYCLOAK_ROUTE_BOOTSTRAP_TOKEN', '')
        path = os.environ.get('CRISTEXWEB_KEYCLOAK_ROUTE_BOOTSTRAP_ATTESTATION_FILE', '')
        binding = task_vars.get('keycloak_route_bootstrap_internal_preflight_binding', {})
        try:
            st = os.stat(path, follow_symlinks=False); content = Path(path).read_text().strip()
        except (OSError, ValueError): st, content = None, ''
        valid = (os.environ.get('CRISTEXWEB_KEYCLOAK_ROUTE_BOOTSTRAP_ENTRYPOINT') == 'v1' and re.fullmatch(r'[0-9a-f]{64}', token) and st and stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode) == 0o600 and st.st_uid == os.getuid() and content == f'{token}:entrypoint')
        valid = valid and isinstance(binding, dict) and binding.get('attestation_sha256') == hashlib.sha256(token.encode()).hexdigest() and int(binding.get('object_count', -1)) == 2 and int(binding.get('prestate_count', -1)) == 2 and binding.get('identity_set_sha256') == '94e2eb0dfa6911ae7df231f0c8edee4e09b9ea34928f84074b1803d3af1552c5' and binding.get('namespace_contract') is True and binding.get('no_delete_path') is True
        if not valid or task_vars.get('keycloak_route_bootstrap_approved') is not True or task_vars.get('keycloak_route_bootstrap_state') != 'present': return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD'}
        if not isinstance(definition, dict) or set(args) != _EXPECTED_ARGUMENT_KEYS or args.get('state') != 'present' or args.get('kubeconfig') != '/etc/rancher/k3s/k3s.yaml' or args.get('wait') is not False or args.get('wait_timeout') != 60: return {'changed': False, 'failed': True, 'msg': 'MUTATION_ARGUMENT_GUARD'}
        metadata = definition.get('metadata') or {}; identity = (definition.get('apiVersion'), definition.get('kind'), metadata.get('namespace', ''), metadata.get('name'))
        if definition.get('kind') in {'Secret', 'PersistentVolumeClaim', 'Service', 'Deployment', 'IngressRoute'} or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition): return {'changed': False, 'failed': True, 'msg': 'MUTATION_ARGUMENT_GUARD'}
        original = self._task.action; self._task.action = 'kubernetes.core.k8s'
        try: return super().run(tmp=tmp, task_vars=task_vars)
        finally: self._task.action = original
