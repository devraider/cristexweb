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
    (
        'networking.k8s.io/v1',
        'NetworkPolicy',
        'shared-services',
        'shared-mongodb-networkpolicy-allow',
    ): 'ab2df6d138e231c0b35181927e4f1c9daa0076fee5f55d5fa0198db712f91382',
    (
        'networking.k8s.io/v1',
        'NetworkPolicy',
        'shared-services',
        'shared-mongodb-networkpolicy-default-deny',
    ): '85647c86943781233258c7c7e386255dd375d6b4b437dab29032bde1653872bd',
}
_EXPECTED_ARGUMENT_KEYS = {'state', 'definition', 'kubeconfig', 'wait', 'wait_timeout'}
_EXPECTED_TASK_SOURCES = {
    '/Users/paul/Projects/cristexweb/ansible/roles/shared_mongodb_networkpolicy_bootstrap/tasks/main.yml',
    '/home/paul/projects/cristexweb/ansible/roles/shared_mongodb_networkpolicy_bootstrap/tasks/main.yml',
}
_EXPECTED_IDENTITY_SET_SHA256 = '11352b9439d10f2ffdfad385ee31f524885fead8d74d38937101614f742ab575'


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(payload).hexdigest()


class ActionModule(KubernetesActionModule):
    """Validate, but never apply, the exact live MongoDB policy closure."""

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start_at_task = context.CLIARGS.get('start_at_task')
        step = bool(context.CLIARGS.get('step'))
        tags = list(context.CLIARGS.get('tags') or [])
        skip_tags = list(context.CLIARGS.get('skip_tags') or [])
        if start_at_task or step or tags not in ([], ['all']) or skip_tags:
            return {
                'changed': False,
                'failed': True,
                'msg': 'TASK_SELECTION_GUARD: refusing shared MongoDB NetworkPolicy check under task selection',
            }
        if not context.CLIARGS.get('check'):
            return {
                'changed': False,
                'failed': True,
                'msg': 'SOURCE_ONLY_GUARD: shared MongoDB NetworkPolicy closure has no apply path',
            }
        task_source = str(self._task.get_path()).rsplit(':', 1)[0]
        if task_source not in _EXPECTED_TASK_SOURCES:
            return {
                'changed': False,
                'failed': True,
                'msg': 'ENTRYPOINT_GUARD: refusing source outside canonical shared MongoDB NetworkPolicy role',
            }
        args = self._task.args
        task_vars = task_vars or {}
        token = os.environ.get('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_TOKEN', '')
        attestation_path = os.environ.get(
            'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_ATTESTATION_FILE', ''
        )
        binding = task_vars.get(
            'shared_mongodb_networkpolicy_bootstrap_internal_preflight_binding', {}
        )
        try:
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation_content = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation_state = None
            attestation_content = ''
        valid_binding = (
            isinstance(binding, dict)
            and binding.get('attestation_sha256') == hashlib.sha256(token.encode()).hexdigest()
            and int(binding.get('object_count', -1)) == 2
            and binding.get('identity_set_sha256') == _EXPECTED_IDENTITY_SET_SHA256
            and int(binding.get('prestate_count', -1)) == 2
            and int(binding.get('mongodb_count', -1)) == 1
            and int(binding.get('pod_count', -1)) >= 1
            and binding.get('namespace_contract') is True
            and binding.get('no_delete_path') is True
        )
        valid_attestation = (
            os.environ.get('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_ENTRYPOINT') == 'v1'
            and re.fullmatch(r'[0-9a-f]{64}', token) is not None
            and attestation_state is not None
            and stat.S_ISREG(attestation_state.st_mode)
            and not stat.S_ISLNK(attestation_state.st_mode)
            and stat.S_IMODE(attestation_state.st_mode) == 0o600
            and attestation_state.st_uid == os.getuid()
            and attestation_content == f'{token}:entrypoint'
        )
        if (
            not valid_attestation
            or not valid_binding
            or task_vars.get('shared_mongodb_networkpolicy_bootstrap_approved') is not True
            or task_vars.get('shared_mongodb_networkpolicy_bootstrap_state') != 'present'
        ):
            return {
                'changed': False,
                'failed': True,
                'msg': 'ENTRYPOINT_GUARD: refusing without validated source-only attestation and preflight binding',
            }
        definition = args.get('definition')
        if (
            not isinstance(definition, dict)
            or set(args) != _EXPECTED_ARGUMENT_KEYS
            or args.get('state') != 'present'
            or args.get('kubeconfig') != '/etc/rancher/k3s/k3s.yaml'
            or args.get('wait') is not False
            or args.get('wait_timeout') != 60
        ):
            return {
                'changed': False,
                'failed': True,
                'msg': 'MUTATION_ARGUMENT_GUARD: refusing arguments outside exact source-only policy check',
            }
        metadata = definition.get('metadata') or {}
        identity = (
            definition.get('apiVersion'),
            definition.get('kind'),
            metadata.get('namespace', ''),
            metadata.get('name'),
        )
        if (
            definition.get('kind') != 'NetworkPolicy'
            or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition)
        ):
            return {
                'changed': False,
                'failed': True,
                'msg': 'MUTATION_ARGUMENT_GUARD: refusing unknown or changed NetworkPolicy',
            }
        original_action = self._task.action
        self._task.action = 'kubernetes.core.k8s'
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
