from __future__ import annotations
import hashlib, json, os, re, stat
from pathlib import Path
from typing import Any
from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import ActionModule as KubernetesActionModule

EXPECTED: dict[tuple[str, str, str, str], str] = {
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'reactive-resume-dev-ca-source-boundary'): 'c9e9b65a8a72f754119d023ccade6bd72767fa21694e04e88d49af2f269ebf51',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'reactive-resume-dev-ca-source-boundary'): '0f5041d274aadf2f7af77b0eec7085f11135763c2d29be3378ad63ab5efd4515',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicyBinding', '', 'reactive-resume-dev-ca-target-boundary'): '4cc7112e5f414970aeb8a9ff8b01a0f0d01bcbcf8e2161b11192edea50e7ec0c',
    ('admissionregistration.k8s.io/v1', 'ValidatingAdmissionPolicy', '', 'reactive-resume-dev-ca-target-boundary'): '7e70ada05d26d7c0c7f2be1737dbc5e0ea5945b2b063fbf58a219f520a8f2283',
    ('rbac.authorization.k8s.io/v1', 'Role', 'cristexhub-dev', 'reactive-resume-dev-ca-secret-writer'): 'd5ade307167d4c6bba1335da1687aae77eefcfa5c2a975e959b1776d8c0df4c0',
    ('rbac.authorization.k8s.io/v1', 'RoleBinding', 'cristexhub-dev', 'reactive-resume-dev-ca-secret-writer'): '5d00994be70dc4a3b3d212a33e02d127f167a85fb9998ee9a4319f48297fc346',
    ('secrets.infisical.com/v1beta1', 'InfisicalStaticSecret', 'cristexhub-dev', 'reactive-resume-dev-ca'): 'f3b903f0d0a77e69193692b6a63c42ad1688b8343cdd18f84f1c7b14825ffac2'
}
TASK_SUFFIX = '/ansible/roles/infisical_reactive_resume_dev_ca_bootstrap/tasks/main.yml'
ARGS = {'state', 'definition', 'kubeconfig', 'wait', 'wait_timeout'}

def canonical(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def strict_true(value: Any) -> bool:
    return value is True or (type(value).__name__ == '_AnsibleTaggedBool' and bool(value)) or (type(value).__name__ == '_AnsibleTaggedStr' and value == 'true')

class ActionModule(KubernetesActionModule):
    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        task_vars = task_vars or {}
        root = str(Path(os.environ.get('CRISTEXWEB_REPOSITORY_ROOT', '')).resolve())
        source = str(Path(re.sub(r':\d+(?::\d+)?$', '', str(self._task.get_path()))).resolve())
        token = os.environ.get('CRISTEXWEB_INFISICAL_REACTIVE_RESUME_DEV_CA_TOKEN', '')
        attestation = os.environ.get('CRISTEXWEB_INFISICAL_REACTIVE_RESUME_DEV_CA_ATTESTATION_FILE', '')
        try:
            state = os.stat(attestation, follow_symlinks=False)
            content = Path(attestation).read_text().strip()
        except (OSError, ValueError):
            state, content = None, ''
        binding = task_vars.get('infisical_reactive_resume_dev_ca_bootstrap_internal_preflight_binding', {})
        valid = (
            source == root + TASK_SUFFIX and isinstance(binding, dict) and
            binding.get('attestation_sha256') == hashlib.sha256(token.encode()).hexdigest() and
            str(binding.get('object_count')) == '7' and str(binding.get('prestate_count')) == '7' and
            os.environ.get('CRISTEXWEB_INFISICAL_REACTIVE_RESUME_DEV_CA_ENTRYPOINT') == 'v1' and
            re.fullmatch(r'[0-9a-f]{64}', token) is not None and state is not None and stat.S_ISREG(state.st_mode) and
            not stat.S_ISLNK(state.st_mode) and stat.S_IMODE(state.st_mode) == 0o600 and state.st_uid == os.getuid() and
            content == f'{token}:entrypoint' and strict_true(task_vars.get('infisical_reactive_resume_dev_ca_bootstrap_approved')) and
            task_vars.get('infisical_reactive_resume_dev_ca_bootstrap_state') == 'present' and
            not context.CLIARGS.get('start_at_task') and not context.CLIARGS.get('step') and
            list(context.CLIARGS.get('skip_tags') or []) == [] and list(context.CLIARGS.get('tags') or []) in ([], ['all'])
        )
        args = self._task.args
        definition = args.get('definition')
        identity = ((definition or {}).get('apiVersion'), (definition or {}).get('kind'), ((definition or {}).get('metadata') or {}).get('namespace', ''), ((definition or {}).get('metadata') or {}).get('name'))
        if set(args) != ARGS or args.get('state') != 'present' or args.get('kubeconfig') != '/etc/rancher/k3s/k3s.yaml' or args.get('wait') is not False or args.get('wait_timeout') != 60 or identity not in EXPECTED or canonical(definition) != EXPECTED[identity]:
            valid = False
        if not valid:
            return {'changed': False, 'failed': True, 'msg': 'ENTRYPOINT_GUARD: refusing Reactive Resume DEV CA mutation outside the exact guarded closure'}
        self._task.action = 'kubernetes.core.k8s'
        return super().run(tmp=tmp, task_vars=task_vars)
