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
_MONGODB_POD_LABELS = {
    'app': 'shared-mongodb-svc',
    'app.kubernetes.io/part-of': 'shared-databases',
    'cristex.io/component': 'mongodb',
}


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(payload).hexdigest()


def _selector_can_match_labels(selector: dict[str, Any] | None, labels: dict[str, str]) -> bool:
    """Return true when a NetworkPolicy podSelector can select the live pod labels."""
    if selector in (None, {}):
        return True
    if not isinstance(selector, dict):
        return True
    match_labels = selector.get('matchLabels', {})
    expressions = selector.get('matchExpressions', [])
    if not isinstance(match_labels, dict) or not isinstance(expressions, list):
        return True
    for key, expected in match_labels.items():
        if key not in labels or labels[key] != str(expected):
            return False
    for expression in expressions:
        if not isinstance(expression, dict):
            return True
        key = expression.get('key')
        operator = expression.get('operator')
        values = expression.get('values', [])
        present = key in labels
        actual = labels.get(key)
        if operator == 'In':
            if not present or not isinstance(values, list) or actual not in values:
                return False
        elif operator == 'NotIn':
            if present and isinstance(values, list) and actual in values:
                return False
        elif operator == 'Exists':
            if not present:
                return False
        elif operator == 'DoesNotExist':
            if present:
                return False
        else:
            return True
    return True


def _policy_identity(policy: dict[str, Any]) -> tuple[str, str, str, str]:
    metadata = policy.get('metadata') or {}
    return (
        policy.get('apiVersion', ''),
        policy.get('kind', ''),
        metadata.get('namespace', ''),
        metadata.get('name', ''),
    )


def _target_policy_matches_source(current: dict[str, Any], source: dict[str, Any]) -> bool:
    current_metadata = current.get('metadata') or {}
    source_metadata = source.get('metadata') or {}
    return (
        current.get('apiVersion') == source.get('apiVersion')
        and current.get('kind') == source.get('kind')
        and current_metadata.get('namespace') == source_metadata.get('namespace')
        and current_metadata.get('name') == source_metadata.get('name')
        and current_metadata.get('labels', {}) == source_metadata.get('labels', {})
        and current.get('spec') == source.get('spec')
        and not current_metadata.get('ownerReferences')
        and not current_metadata.get('finalizers')
    )


def _safe_int(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() == 'true')


def _networkpolicy_preflight_error(
    policies: list[dict[str, Any]],
    source_definitions: list[dict[str, Any]],
    pod: dict[str, Any],
) -> str | None:
    """Return a fail-closed reason for policy union or target drift."""
    if not isinstance(policies, list) or not isinstance(source_definitions, list):
        return 'missing NetworkPolicy inventory'
    if any(not isinstance(item, dict) for item in source_definitions):
        return 'malformed source NetworkPolicy inventory'
    expected = {_policy_identity(item): item for item in source_definitions}
    if set(expected) != set(_EXPECTED_OBJECT_HASHES):
        return 'source NetworkPolicy identity closure drift'
    labels = (pod.get('metadata') or {}).get('labels') or {}
    if (pod.get('metadata') or {}).get('name') != 'shared-mongodb-0' or any(
        labels.get(key) != value for key, value in _MONGODB_POD_LABELS.items()
    ):
        return 'live MongoDB pod identity or selector drift'
    for policy in policies:
        if not isinstance(policy, dict):
            return 'malformed NetworkPolicy inventory'
        identity = _policy_identity(policy)
        if identity in expected:
            if not _target_policy_matches_source(policy, expected[identity]):
                return f'target NetworkPolicy drift: {identity[-1]}'
        elif _selector_can_match_labels((policy.get('spec') or {}).get('podSelector'), labels):
            return f'foreign NetworkPolicy selector overlaps live MongoDB: {identity[-1]}'
    return None


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
        all_networkpolicies = task_vars.get(
            'shared_mongodb_networkpolicy_bootstrap_internal_all_networkpolicies', {}
        )
        source_manifests = task_vars.get(
            'shared_mongodb_networkpolicy_bootstrap_internal_manifests', []
        )
        live_pod_result = task_vars.get(
            'shared_mongodb_networkpolicy_bootstrap_internal_pod', {}
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
            and _safe_int(binding.get('object_count')) == 2
            and binding.get('identity_set_sha256') == _EXPECTED_IDENTITY_SET_SHA256
            and _safe_int(binding.get('prestate_count')) in (0, 2)
            and _safe_int(binding.get('prestate_count')) != 1
            and _safe_int(binding.get('mongodb_count')) == 1
            and _safe_int(binding.get('statefulset_count')) == 1
            and isinstance(binding.get('statefulset_uid'), str)
            and len(binding.get('statefulset_uid', '')) > 0
            and _safe_int(binding.get('pod_count')) == 1
            and binding.get('pod_name') == 'shared-mongodb-0'
            and binding.get('pod_phase') == 'Running'
            and _as_bool(binding.get('pod_ready'))
            and not _as_bool(binding.get('pod_terminating'))
            and binding.get('pod_owner_api_version') == 'apps/v1'
            and binding.get('pod_owner_kind') == 'StatefulSet'
            and binding.get('pod_owner_name') == 'shared-mongodb'
            and binding.get('pod_owner_uid') == binding.get('statefulset_uid')
            and _as_bool(binding.get('pod_owner_controller'))
            and _safe_int(binding.get('networkpolicy_count')) == len((all_networkpolicies or {}).get('resources', []))
            and isinstance(binding.get('networkpolicy_names'), list)
            and sorted(binding.get('networkpolicy_names', [])) == sorted(
                item.get('metadata', {}).get('name') for item in (all_networkpolicies or {}).get('resources', [])
            )
            and _safe_int(binding.get('client_environment_count')) == 2
            and _safe_int(binding.get('coredns_count')) >= 1
            and binding.get('kubeconfig_contract') is True
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
        live_pods = (live_pod_result or {}).get('resources', [])
        policy_inventory_present = (
            isinstance(all_networkpolicies, dict)
            and isinstance(all_networkpolicies.get('resources'), list)
        )
        policy_preflight_error = _networkpolicy_preflight_error(
            (all_networkpolicies or {}).get('resources', []),
            source_manifests,
            live_pods[0] if len(live_pods) == 1 else {},
        )
        if (
            not valid_attestation
            or not valid_binding
            or not policy_inventory_present
            or policy_preflight_error is not None
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
