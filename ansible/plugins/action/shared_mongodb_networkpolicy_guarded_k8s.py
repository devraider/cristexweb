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
    ): 'c7b4348046fb6afd97b1ce7fdf2aacc5b649a83af6c45158f3f864f82dc3d1b8',
    (
        'networking.k8s.io/v1',
        'NetworkPolicy',
        'shared-services',
        'shared-mongodb-networkpolicy-default-deny',
    ): '85647c86943781233258c7c7e386255dd375d6b4b437dab29032bde1653872bd',
}
_EXPECTED_ARGUMENT_KEYS = {
    'state', 'definition', 'kubeconfig', 'wait', 'wait_timeout',
    'prestate_binding', 'validation_only',
}
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_TASK_SOURCE = _REPOSITORY_ROOT / 'ansible/roles/shared_mongodb_networkpolicy_bootstrap/tasks/main.yml'
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / 'ansible/roles/shared_mongodb_networkpolicy_bootstrap/defaults/main.yml'
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / 'ansible/playbooks/bootstrap_shared_mongodb_networkpolicy.yml'
_WRAPPER_SOURCE = _REPOSITORY_ROOT / 'ansible/bin/bootstrap-shared-mongodb-networkpolicy'
_ACTION_SOURCE = _REPOSITORY_ROOT / 'ansible/plugins/action/shared_mongodb_networkpolicy_guarded_k8s.py'
_CREATE_MODULE_SOURCE = _REPOSITORY_ROOT / 'ansible/library/shared_mongodb_networkpolicy_create.py'
_INVENTORY_SOURCE = _REPOSITORY_ROOT / 'ansible/.ansible/inventory.local.yml'
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / 'ansible/ansible.cfg'
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / '.venv/bin/ansible-playbook'
_EXPECTED_TASK_SOURCES = {str(_TASK_SOURCE)}
_EXPECTED_IDENTITY_SET_SHA256 = '11352b9439d10f2ffdfad385ee31f524885fead8d74d38937101614f742ab575'
_EXPECTED_LOCK_FILE = '/tmp/cristexweb-shared-mongodb-networkpolicy.lock'
_EXPECTED_TASK_SHA256 = '96e67586550ee4850f1275988265d5f4ea507566a7da417fb83f26ff5d5ed0cb'
_EXPECTED_DEFAULTS_SHA256 = '2daa92a2dccecf493c88741777c40198b0ad8721677d6d12b2d29806ea1b8202'
_EXPECTED_PLAYBOOK_SHA256 = '7521e6d1e0fc705b70d1d9ba08ee9330a8de00abf846f3598ee51047748be3c9'
_EXPECTED_ACTION_CANONICAL_SHA256 = '61321b0be7c73db6400e405daf6ffe3859f3957593398c0453fbc355af3a515a'
_EXPECTED_CREATE_MODULE_SHA256 = '7fed1d8a3655dad7dad7fdab1e204d9c4907abd144b2c1f2ce0e5caee88e177f'
_EXPECTED_INVENTORY_SHA256 = '652a8455f8a050005ab783d20d4e60a0cd034d8a6439f1cffe551a91102773b0'
_EXPECTED_ANSIBLE_CONFIG_SHA256 = '4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9'
_EXPECTED_CONTROLLER_SHA256 = 'baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd'
_EXPECTED_CONTROLLER_MODE = 0o775
_ALLOWED_MANAGED_FIELD_MANAGERS = {'ansible'}
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


def _managed_fields_are_owned(metadata: dict[str, Any]) -> bool:
    fields = metadata.get('managedFields', [])
    if fields in (None, []):
        return fields in (None, [])
    if not isinstance(fields, list):
        return False
    return all(
        isinstance(entry, dict)
        and isinstance(entry.get('manager'), str)
        and entry.get('manager') in _ALLOWED_MANAGED_FIELD_MANAGERS
        and entry.get('operation') in {'Apply', 'Update'}
        and entry.get('subresource') in (None, '')
        for entry in fields
    )


def _target_policy_matches_source(current: dict[str, Any], source: dict[str, Any]) -> bool:
    """Require a live, nonterminating object rather than a replacement candidate."""
    current_metadata = current.get('metadata') or {}
    source_metadata = source.get('metadata') or {}
    forbidden_lifecycle_fields = {
        'deletionTimestamp',
        'deletionGracePeriodSeconds',
        'deletionGracePeriod',
        'finalizers',
        'ownerReferences',
    }
    # Kubernetes omits these fields for an ordinary object.  Their presence is
    # deliberately rejected, including empty lists/nulls, so a terminating or
    # controller-replaced target cannot satisfy the source-only closure.
    if forbidden_lifecycle_fields.intersection(current_metadata):
        return False
    return (
        current.get('apiVersion') == source.get('apiVersion')
        and current.get('kind') == source.get('kind')
        and current_metadata.get('namespace') == source_metadata.get('namespace')
        and current_metadata.get('name') == source_metadata.get('name')
        and isinstance(current_metadata.get('uid'), str)
        and bool(current_metadata.get('uid'))
        and isinstance(current_metadata.get('resourceVersion'), str)
        and bool(current_metadata.get('resourceVersion'))
        and current_metadata.get('labels', {}) == source_metadata.get('labels', {})
        and (current_metadata.get('annotations') or {}) == (source_metadata.get('annotations') or {})
        and _managed_fields_are_owned(current_metadata)
        and current.get('spec') == source.get('spec')
    )


def _safe_int(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() == 'true')


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return ''


def _canonical_file_hash(path: Path, symbol: str) -> str:
    try:
        source = path.read_text(encoding='utf-8')
        source, count = re.subn(
            rf'(?m)^({re.escape(symbol)}\s*=\s*[\"\'])([0-9a-f]{{64}})([\"\']\s*)$',
            rf'\g<1>{"0" * 64}\g<3>',
            source,
        )
        return hashlib.sha256(source.encode()).hexdigest() if count == 1 else ''
    except (OSError, UnicodeError, ValueError):
        return ''


def _regular_file(path: Path, mode: int, owner: int | None = None) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
        return (
            stat.S_ISREG(state.st_mode)
            and not path.is_symlink()
            and stat.S_IMODE(state.st_mode) == mode
            and (owner is None or state.st_uid == owner)
        )
    except OSError:
        return False


def _source_closure_valid() -> bool:
    expected = (
        (_TASK_SOURCE, _EXPECTED_TASK_SHA256, 0o644),
        (_DEFAULTS_SOURCE, _EXPECTED_DEFAULTS_SHA256, 0o644),
        (_PLAYBOOK_SOURCE, _EXPECTED_PLAYBOOK_SHA256, 0o644),
        (_INVENTORY_SOURCE, _EXPECTED_INVENTORY_SHA256, 0o600),
        (_ANSIBLE_CONFIG_SOURCE, _EXPECTED_ANSIBLE_CONFIG_SHA256, 0o644),
    )
    for path, digest, mode in expected:
        if not _regular_file(path, mode, os.getuid()) or _sha256(path) != digest:
            return False
    if not _regular_file(_WRAPPER_SOURCE, 0o755, os.getuid()):
        return False
    wrapper_canonical = _canonical_file_hash(_WRAPPER_SOURCE, 'wrapper_canonical_sha256_expected')
    if not wrapper_canonical or os.environ.get('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_CANONICAL_SHA256') != wrapper_canonical:
        return False
    if not _regular_file(_ACTION_SOURCE, 0o644, os.getuid()):
        return False
    if _canonical_file_hash(_ACTION_SOURCE, '_EXPECTED_ACTION_CANONICAL_SHA256') != _EXPECTED_ACTION_CANONICAL_SHA256:
        return False
    if not _regular_file(_CREATE_MODULE_SOURCE, 0o755, os.getuid()):
        return False
    if _sha256(_CREATE_MODULE_SOURCE) != _EXPECTED_CREATE_MODULE_SHA256:
        return False
    try:
        state = _CONTROLLER_SOURCE.stat(follow_symlinks=False)
        return (
            stat.S_ISREG(state.st_mode)
            and not _CONTROLLER_SOURCE.is_symlink()
            and stat.S_IMODE(state.st_mode) == _EXPECTED_CONTROLLER_MODE
            and state.st_uid == os.getuid()
            and _sha256(_CONTROLLER_SOURCE) == _EXPECTED_CONTROLLER_SHA256
        )
    except OSError:
        return False


def _runtime_binding_valid() -> bool:
    expected = {
        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_TASK_SHA256': _EXPECTED_TASK_SHA256,
        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_DEFAULTS_SHA256': _EXPECTED_DEFAULTS_SHA256,
        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_PLAYBOOK_SHA256': _EXPECTED_PLAYBOOK_SHA256,
        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_CANONICAL_SHA256': _canonical_file_hash(_WRAPPER_SOURCE, 'wrapper_canonical_sha256_expected'),
        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_ACTION_CANONICAL_SHA256': _EXPECTED_ACTION_CANONICAL_SHA256,
        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_CREATE_MODULE_SHA256': _EXPECTED_CREATE_MODULE_SHA256,
        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_INVENTORY_SHA256': _EXPECTED_INVENTORY_SHA256,
        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_ANSIBLE_CONFIG_SHA256': _EXPECTED_ANSIBLE_CONFIG_SHA256,
        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_CONTROLLER_SHA256': _EXPECTED_CONTROLLER_SHA256,
    }
    expected_mode = 'check' if bool(context.CLIARGS.get('check')) else 'apply'
    return (
        os.environ.get('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_MODE') == expected_mode
        and all(os.environ.get(name) == value for name, value in expected.items())
    )


def _cooperative_lock_valid() -> bool:
    """Require an atomically-created, live wrapper-owned lock directory."""
    if os.environ.get('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_LOCK_FILE') != _EXPECTED_LOCK_FILE:
        return False
    token = os.environ.get('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_TOKEN', '')
    pid_text = os.environ.get('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_PID', '')
    try:
        pid = int(pid_text)
        lock = Path(_EXPECTED_LOCK_FILE)
        owner = lock / 'owner'
        lock_state = lock.stat(follow_symlinks=False)
        owner_state = owner.stat(follow_symlinks=False)
        owner_text = owner.read_text(encoding='utf-8').strip()
        return (
            stat.S_ISDIR(lock_state.st_mode)
            and not lock.is_symlink()
            and stat.S_IMODE(lock_state.st_mode) == 0o700
            and lock_state.st_uid == os.getuid()
            and stat.S_ISREG(owner_state.st_mode)
            and not owner.is_symlink()
            and stat.S_IMODE(owner_state.st_mode) == 0o600
            and owner_state.st_uid == os.getuid()
            and owner_text == f'{token}:{pid}'
            and re.fullmatch(r'[0-9a-f]{64}', token) is not None
            and pid > 1
        ) and _pid_alive(pid)
    except (OSError, ValueError, UnicodeError):
        return False


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def _networkpolicy_cas_patch(
    definition: dict[str, Any], prestate: dict[str, Any]
) -> list[dict[str, Any]]:
    """Build a no-op JSON patch whose tests condition the target mutation.

    The Kubernetes JSON-patch endpoint performs the GET and all RFC 6902 test
    operations as one request.  Testing both identity fields and the complete
    desired payload prevents a stale Ansible snapshot from being silently
    adopted by a later generic reconcile.
    """
    identity = _policy_identity(definition)
    metadata = definition.get('metadata') or {}
    if (
        set(prestate) != {'name', 'uid', 'resource_version'}
        or prestate.get('name') != identity[-1]
        or not isinstance(prestate.get('uid'), str)
        or not prestate.get('uid')
        or not isinstance(prestate.get('resource_version'), str)
        or not re.fullmatch(r'[0-9]+', prestate.get('resource_version', ''))
        or not isinstance(metadata.get('labels'), dict)
        or not isinstance(definition.get('spec'), dict)
    ):
        raise ValueError('invalid existing NetworkPolicy prestate for CAS')
    return [
        {'op': 'test', 'path': '/metadata/uid', 'value': prestate['uid']},
        {
            'op': 'test',
            'path': '/metadata/resourceVersion',
            'value': prestate['resource_version'],
        },
        {'op': 'test', 'path': '/metadata/labels', 'value': metadata['labels']},
        {'op': 'test', 'path': '/spec', 'value': definition['spec']},
    ]


def _networkpolicy_preflight_error(
    policies: list[dict[str, Any]],
    source_definitions: list[dict[str, Any]],
    pod: dict[str, Any],
    expected_target_identities: list[dict[str, str]] | None = None,
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
    ledger_provided = expected_target_identities is not None
    expected_target_identities = expected_target_identities or []
    expected_by_name = {item.get('name'): item for item in expected_target_identities}
    if ledger_provided and any(
        not isinstance(item, dict)
        or set(item) != {'name', 'uid', 'resource_version'}
        or item.get('name') not in {identity[-1] for identity in expected}
        or not item.get('uid')
        or not item.get('resource_version')
        for item in expected_target_identities
    ):
        return 'malformed NetworkPolicy pre-state identity ledger'
    for policy in policies:
        if not isinstance(policy, dict):
            return 'malformed NetworkPolicy inventory'
        identity = _policy_identity(policy)
        if identity in expected:
            if not _target_policy_matches_source(policy, expected[identity]):
                return f'target NetworkPolicy drift: {identity[-1]}'
            metadata = policy.get('metadata') or {}
            if ledger_provided:
                expected_identity = expected_by_name.get(metadata.get('name'))
                if expected_identity is None:
                    return f'target NetworkPolicy replacement: {identity[-1]}'
                if (
                    metadata.get('uid') != expected_identity['uid']
                    or metadata.get('resourceVersion') != expected_identity['resource_version']
                ):
                    return f'target NetworkPolicy replacement: {identity[-1]}'
        elif _selector_can_match_labels((policy.get('spec') or {}).get('podSelector'), labels):
            return f'foreign NetworkPolicy selector overlaps live MongoDB: {identity[-1]}'
    if ledger_provided:
        present_target_names = {
            policy.get('metadata', {}).get('name')
            for policy in policies
            if isinstance(policy, dict) and _policy_identity(policy) in expected
        }
        if present_target_names != set(expected_by_name):
            return 'target NetworkPolicy replacement or disappearance'
    return None


class ActionModule(KubernetesActionModule):
    """Guard the exact MongoDB policy closure in separately gated check/apply modes."""

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
        mode = task_vars.get('shared_mongodb_networkpolicy_bootstrap_mode', '') if task_vars else ''
        if mode not in {'check', 'apply'} or bool(context.CLIARGS.get('check')) != (mode == 'check'):
            return {
                'changed': False,
                'failed': True,
                'msg': 'MODE_GUARD: shared MongoDB NetworkPolicy mode does not match Ansible check mode',
            }
        if mode == 'apply' and os.environ.get('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_APPLY_APPROVED') != 'v1':
            return {
                'changed': False,
                'failed': True,
                'msg': 'APPROVAL_GUARD: shared MongoDB NetworkPolicy apply requires the separately gated wrapper',
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
        if not isinstance(binding, dict):
            binding = {}
        all_networkpolicies = task_vars.get(
            'shared_mongodb_networkpolicy_bootstrap_internal_all_networkpolicies', {}
        )
        source_manifests = task_vars.get(
            'shared_mongodb_networkpolicy_bootstrap_internal_manifests', []
        )
        live_pod_result = task_vars.get(
            'shared_mongodb_networkpolicy_bootstrap_internal_pod', {}
        )
        policy_resources = (
            all_networkpolicies.get('resources', [])
            if isinstance(all_networkpolicies, dict)
            and isinstance(all_networkpolicies.get('resources'), list)
            else []
        )
        try:
            attestation_state = os.stat(attestation_path, follow_symlinks=False)
            attestation_content = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation_state = None
            attestation_content = ''
        policy_prestate = binding.get('networkpolicy_prestate')
        prestate_count = _safe_int(binding.get('prestate_count'))
        initial_prestate_count = _safe_int(binding.get('initial_prestate_count'))
        transition_phase = binding.get('transition_phase')
        valid_binding = (
            isinstance(binding, dict)
            and binding.get('attestation_sha256') == hashlib.sha256(token.encode()).hexdigest()
            and _safe_int(binding.get('object_count')) == 2
            and binding.get('identity_set_sha256') == _EXPECTED_IDENTITY_SET_SHA256
            and transition_phase in {'initial', 'after-default-deny', 'post'}
            and initial_prestate_count in (0, 2)
            and prestate_count == (len(policy_prestate) if isinstance(policy_prestate, list) else -1)
            and prestate_count in ((0, 2) if transition_phase == 'initial' else (0, 1, 2))
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
            and _safe_int(binding.get('networkpolicy_count')) == len(policy_resources)
            and isinstance(binding.get('networkpolicy_names'), list)
            and sorted(binding.get('networkpolicy_names', [])) == sorted(
                item.get('metadata', {}).get('name')
                for item in policy_resources
                if isinstance(item, dict)
            )
            and _safe_int(binding.get('client_environment_count')) == 2
            and _safe_int(binding.get('coredns_count')) >= 1
            and binding.get('kubeconfig_contract') is True
            and binding.get('namespace_contract') is True
            and binding.get('no_delete_path') is True
            and isinstance(binding.get('networkpolicy_prestate'), list)
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
        live_pods = (
            live_pod_result.get('resources', [])
            if isinstance(live_pod_result, dict)
            else []
        )
        policy_inventory_present = isinstance(all_networkpolicies, dict) and isinstance(
            all_networkpolicies.get('resources'), list
        )
        policy_preflight_error = _networkpolicy_preflight_error(
            policy_resources,
            source_manifests,
            live_pods[0] if len(live_pods) == 1 else {},
            binding.get('networkpolicy_prestate', []),
        )
        if (
            not valid_attestation
            or not _cooperative_lock_valid()
            or not _source_closure_valid()
            or not _runtime_binding_valid()
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
            or args.get('validation_only') not in (True, False)
            or not isinstance(args.get('prestate_binding'), dict)
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
        prestate_binding = args['prestate_binding']
        expected_prestate = next(
            (
                item
                for item in (binding.get('networkpolicy_prestate') or [])
                if isinstance(item, dict) and item.get('name') == identity[-1]
            ),
            {},
        )
        if prestate_binding != expected_prestate:
            return {
                'changed': False,
                'failed': True,
                'msg': 'MUTATION_ARGUMENT_GUARD: target NetworkPolicy prestate binding drift',
            }
        if args['validation_only']:
            return {
                'changed': False,
                'identity': '|'.join(str(value) for value in identity),
                'validation_only': True,
            }
        if prestate_binding:
            try:
                patch = _networkpolicy_cas_patch(definition, prestate_binding)
            except (TypeError, ValueError, KeyError):
                return {
                    'changed': False,
                    'failed': True,
                    'msg': 'MUTATION_ARGUMENT_GUARD: exact target NetworkPolicy CAS prestate required',
                }
            if context.CLIARGS.get('check'):
                return {
                    'changed': False,
                    'identity': '|'.join(str(value) for value in identity),
                    'patch_operation_count': len(patch),
                    'cas': True,
                }
            original_action, original_args = self._task.action, self._task.args
            self._task.action = 'kubernetes.core.k8s_json_patch'
            self._task.args = {
                'api_version': definition['apiVersion'],
                'kind': definition['kind'],
                'namespace': metadata['namespace'],
                'name': metadata['name'],
                'kubeconfig': '/etc/rancher/k3s/k3s.yaml',
                'patch': patch,
            }
            try:
                from ansible_collections.kubernetes.core.plugins.action.k8s_json_patch import (
                    ActionModule as PatchActionModule,
                )
                patch_action = PatchActionModule(
                    self._task,
                    self._connection,
                    self._play_context,
                    self._loader,
                    self._templar,
                    getattr(self, '_shared_loader_obj', None),
                )
                result = patch_action.run(tmp=tmp, task_vars=task_vars)
                return {
                    **result,
                    'identity': '|'.join(str(value) for value in identity),
                    'patch_operation_count': len(patch),
                    'cas': True,
                }
            finally:
                self._task.action, self._task.args = original_action, original_args
        # An absent target is create-only.  The focused module performs an
        # atomic server-side POST after its GET and fails on a concurrent 409;
        # it must never fall back to a merge/update operation.
        if context.CLIARGS.get('check'):
            return {
                'changed': True,
                'identity': '|'.join(str(value) for value in identity),
                'create': True,
                'cas': True,
            }
        result = self._execute_module(
            module_name='shared_mongodb_networkpolicy_create',
            module_args={
                'api_version': definition['apiVersion'],
                'kind': definition['kind'],
                'namespace': metadata['namespace'],
                'name': metadata['name'],
                'kubeconfig': '/etc/rancher/k3s/k3s.yaml',
                'definition': definition,
            },
            task_vars=task_vars,
        )
        if result.get('failed') or result.get('method') != 'create':
            return {
                **result,
                'changed': False,
                'identity': '|'.join(str(value) for value in identity),
                'create': True,
                'cas': True,
            }
        created = result.get('resource') or result.get('result') or {}
        created_metadata = created.get('metadata', {}) if isinstance(created, dict) else {}
        if (
            created_metadata.get('name') != metadata.get('name')
            or created_metadata.get('namespace') != metadata.get('namespace')
            or not created_metadata.get('uid')
            or not created_metadata.get('resourceVersion')
        ):
            return {
                'changed': False,
                'failed': True,
                'msg': 'CREATE_ONLY_GUARD: create response did not bind UID/resourceVersion',
            }
        return {
            **result,
            'identity': '|'.join(str(value) for value in identity),
            'create': True,
            'cas': True,
            'created_uid': created_metadata['uid'],
            'created_resource_version': created_metadata['resourceVersion'],
        }
