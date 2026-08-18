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
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'shared-mongodb-default-deny'): '9bea1c7f631a0264002e97875df89fedf2977e57a3849f5cf6fb138a1febee46',
    ('networking.k8s.io/v1', 'NetworkPolicy', 'shared-services', 'shared-mongodb-ingress'): '1f7d6382e9a60fd17e82198930da512aaec0f171a051c3663d4b11dfa2bbc9c3',
    ('v1', 'ServiceAccount', 'shared-services', 'shared-mongodb'): '469d30f12c1e5cf2ca33239d913d9b8cc6e4fbd9a84178a1f7e6f99d14ab8022',
    ('v1', 'Service', 'shared-services', 'shared-mongodb'): '207364d704890e330e9acd39f40d876bf91ab9f640c8cffd6464e56363683ca6',
    ('apps/v1', 'StatefulSet', 'shared-services', 'shared-mongodb'): 'ae04c4c70d2f5bfce9b3850f2b17d52e8739e15649b507e1a0950d18b5f38094',
}
_EXPECTED_ARGUMENT_KEYS = {'state', 'definition', 'kubeconfig', 'wait', 'wait_timeout'}
_EXPECTED_TASK_SOURCES = {
    '/Users/paul/Projects/cristexweb/ansible/roles/mongodb_bootstrap/tasks/main.yml',
    '/home/paul/projects/cristexweb/ansible/roles/mongodb_bootstrap/tasks/main.yml',
}
_EXPECTED_IDENTITY_SET_SHA256 = '2dafb88dd68d2031c0e558a9c8b18b2ee5bdd6c6f7116163e222c7dbe71c470e'


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(payload).hexdigest()


class ActionModule(KubernetesActionModule):
    """Permit only the exact present-only standalone MongoDB closure."""

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start_at_task = context.CLIARGS.get('start_at_task')
        step = bool(context.CLIARGS.get('step'))
        tags = list(context.CLIARGS.get('tags') or [])
        skip_tags = list(context.CLIARGS.get('skip_tags') or [])
        task_source = str(self._task.get_path()).rsplit(':', 1)[0]
        if task_source not in _EXPECTED_TASK_SOURCES:
            return {
                'changed': False,
                'failed': True,
                'msg': (
                    'ENTRYPOINT_GUARD: refusing MongoDB mutation outside the '
                    'canonical guarded role task source'
                ),
            }
        args = self._task.args
        task_vars = task_vars or {}
        token = os.environ.get('CRISTEXWEB_MONGODB_BOOTSTRAP_TOKEN', '')
        attestation_path = os.environ.get(
            'CRISTEXWEB_MONGODB_BOOTSTRAP_ATTESTATION_FILE', ''
        )
        binding = task_vars.get('mongodb_bootstrap_internal_preflight_binding', {})
        try:
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation_content = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation_state = None
            attestation_content = ''
        expected_attestation_sha256 = hashlib.sha256(token.encode()).hexdigest()
        valid_binding = (
            isinstance(binding, dict)
            and binding.get('attestation_sha256') == expected_attestation_sha256
            and int(binding.get('object_count', -1)) == 5
            and binding.get('identity_set_sha256') == _EXPECTED_IDENTITY_SET_SHA256
            and int(binding.get('prestate_count', -1)) == 5
            and int(binding.get('secret_count', -1)) == 2
            and int(binding.get('pvc_prestate_count', -1)) in (0, 1)
            and binding.get('namespace_contract') is True
            and binding.get('storage_contract') is True
            and binding.get('service_contract') is True
            and binding.get('no_delete_path') is True
        )
        valid_attestation = (
            os.environ.get('CRISTEXWEB_MONGODB_BOOTSTRAP_ENTRYPOINT') == 'v1'
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
            or task_vars.get('mongodb_bootstrap_approved') is not True
            or task_vars.get('mongodb_bootstrap_state') != 'present'
        ):
            return {
                'changed': False,
                'failed': True,
                'msg': (
                    'ENTRYPOINT_GUARD: refusing MongoDB mutation without the '
                    'validated wrapper attestation and complete preflight binding'
                ),
            }
        definition = args.get('definition')
        if not isinstance(definition, dict):
            return {
                'changed': False,
                'failed': True,
                'msg': (
                    'MUTATION_ARGUMENT_GUARD: refusing arguments outside the '
                    'exact present-only MongoDB closure'
                ),
            }
        metadata = definition.get('metadata') or {}
        identity = (
            definition.get('apiVersion'),
            definition.get('kind'),
            metadata.get('namespace', ''),
            metadata.get('name'),
        )
        if (
            set(args) != _EXPECTED_ARGUMENT_KEYS
            or args.get('state') != 'present'
            or args.get('kubeconfig') != '/etc/rancher/k3s/k3s.yaml'
            or args.get('wait') is not False
            or args.get('wait_timeout') != 60
        ):
            return {
                'changed': False,
                'failed': True,
                'msg': (
                    'MUTATION_ARGUMENT_GUARD: refusing arguments outside the '
                    'exact present-only MongoDB closure'
                ),
            }
        if (
            definition.get('kind') in {'Secret', 'PersistentVolumeClaim'}
            or _EXPECTED_OBJECT_HASHES.get(identity) != _canonical_hash(definition)
        ):
            return {
                'changed': False,
                'failed': True,
                'msg': (
                    'MUTATION_ARGUMENT_GUARD: refusing an unknown, changed, '
                    'Secret, or generated-storage MongoDB object'
                ),
            }
        if start_at_task or step or tags not in ([], ['all']) or skip_tags:
            return {
                'changed': False,
                'failed': True,
                'msg': 'TASK_SELECTION_GUARD: refusing MongoDB mutation under task selection',
            }
        original_action = self._task.action
        self._task.action = 'kubernetes.core.k8s'
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action
