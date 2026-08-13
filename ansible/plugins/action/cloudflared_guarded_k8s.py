from __future__ import annotations

import hashlib, json, os, re, stat
from pathlib import Path
from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import ActionModule as KubernetesActionModule

_EXPECTED_OBJECT_HASHES = {
    ('networking.k8s.io/v1', 'NetworkPolicy', 'platform-edge', 'cloudflared-allow-egress'): '1def16ac9ed1f1acbcbbb2a0304e8f5a498db6e44cecd897d821b1eea620ac3a',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'platform-edge', 'cloudflared-allow-traefik-origin'): 'a0fae89f3799ab5be4623484d132830710fbd51e804ea88cdb83055c3ab7c8ce',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'platform-edge', 'cloudflared-default-deny'): '04d11614782f936cdcd89367d1622f42dd520dc71fc688d76567a808b2202e06',
    ('v1', 'ServiceAccount', 'platform-edge', 'cloudflared'): '34051c2d22c673a246f1ee9459d9f3b8b414c292e9b9527a4f4d55bb85955c8d',
    ('apps/v1', 'Deployment', 'platform-edge', 'cloudflared'): 'fdb6d2047898fed3ee02b60d48029bb0175dd59f6941cb6b09bf8cd862f84dbd',
}
_EXPECTED_ARGUMENT_KEYS = {'state', 'definition', 'kubeconfig', 'wait', 'wait_timeout'}
_EXPECTED_TASK_SOURCES = {'/Users/paul/Projects/cristexweb/ansible/roles/cloudflared_bootstrap/tasks/main.yml', '/home/paul/projects/cristexweb/ansible/roles/cloudflared_bootstrap/tasks/main.yml'}

def _canonical_hash(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

class ActionModule(KubernetesActionModule):
    def run(self, tmp=None, task_vars=None):
        task_vars = task_vars or {}
        source = str(self._task.get_path()).rsplit(':', 1)[0]
        if source not in _EXPECTED_TASK_SOURCES: return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD'}
        if context.CLIARGS.get('start_at_task') or context.CLIARGS.get('step') or context.CLIARGS.get('skip_tags'): return {'changed': False, 'failed': True, 'msg': 'TASK_SELECTION_GUARD'}
        args = self._task.args; definition = args.get('definition'); token=os.environ.get('CRISTEXWEB_CLOUDFLARED_BOOTSTRAP_TOKEN',''); path=os.environ.get('CRISTEXWEB_CLOUDFLARED_BOOTSTRAP_ATTESTATION_FILE',''); binding=task_vars.get('cloudflared_bootstrap_internal_preflight_binding', {})
        try: st=os.stat(path, follow_symlinks=False); content=Path(path).read_text().strip()
        except (OSError, ValueError): st,content=None,''
        valid = os.environ.get('CRISTEXWEB_CLOUDFLARED_BOOTSTRAP_ENTRYPOINT') == 'v1' and re.fullmatch(r'[0-9a-f]{64}', token) and st and stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==0o600 and st.st_uid==os.getuid() and content==f'{token}:entrypoint'
        valid = valid and isinstance(binding,dict) and binding.get('attestation_sha256')==hashlib.sha256(token.encode()).hexdigest() and int(binding.get('object_count',-1))==5 and int(binding.get('prestate_count',-1))==5 and binding.get('identity_set_sha256')=='edc38bcf9d7f0313076c47a3c70c8f2ca878dfed2a2dcf0ea190eca06e8a29db' and int(binding.get('secret_count',-1))==1 and binding.get('namespace_contract') is True and binding.get('no_delete_path') is True
        if not valid or task_vars.get('cloudflared_bootstrap_approved') is not True or task_vars.get('cloudflared_bootstrap_state')!='present': return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD'}
        if not isinstance(definition,dict) or set(args)!=_EXPECTED_ARGUMENT_KEYS or args.get('state')!='present' or args.get('kubeconfig')!='/etc/rancher/k3s/k3s.yaml' or args.get('wait') is not False or args.get('wait_timeout')!=60: return {'changed': False, 'failed': True, 'msg': 'MUTATION_ARGUMENT_GUARD'}
        m=definition.get('metadata') or {}; identity=(definition.get('apiVersion'),definition.get('kind'),m.get('namespace',''),m.get('name'))
        if definition.get('kind') in {'Secret','PersistentVolumeClaim','Ingress','ServiceMonitor'} or _EXPECTED_OBJECT_HASHES.get(identity)!=_canonical_hash(definition): return {'changed':False,'failed':True,'msg':'MUTATION_ARGUMENT_GUARD'}
        original=self._task.action; self._task.action='kubernetes.core.k8s'
        try: return super().run(tmp=tmp, task_vars=task_vars)
        finally: self._task.action=original
