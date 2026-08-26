from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / 'ansible/files/components/shared-mongodb-networkpolicy'
NETWORK = COMPONENT / 'network'
DEFAULTS = ROOT / 'ansible/roles/shared_mongodb_networkpolicy_bootstrap/defaults/main.yml'
TASKS = ROOT / 'ansible/roles/shared_mongodb_networkpolicy_bootstrap/tasks/main.yml'
PLUGIN = ROOT / 'ansible/plugins/action/shared_mongodb_networkpolicy_guarded_k8s.py'
WRAPPER = ROOT / 'ansible/bin/bootstrap-shared-mongodb-networkpolicy'
PLAYBOOK = ROOT / 'ansible/playbooks/bootstrap_shared_mongodb_networkpolicy.yml'
PLUGIN_MODULE = None


class SharedMongoDbNetworkPolicyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = sorted(NETWORK.glob('*.yaml'))
        cls.objects = [yaml.safe_load(path.read_text()) for path in cls.paths]
        cls.by_name = {obj['metadata']['name']: obj for obj in cls.objects}
        package_names = [
            'ansible_collections',
            'ansible_collections.kubernetes',
            'ansible_collections.kubernetes.core',
            'ansible_collections.kubernetes.core.plugins',
            'ansible_collections.kubernetes.core.plugins.action',
        ]
        fake_modules: dict[str, ModuleType] = {}
        for name in package_names:
            package = ModuleType(name)
            package.__path__ = []
            fake_modules[name] = package
        k8s_module = ModuleType('ansible_collections.kubernetes.core.plugins.action.k8s')
        k8s_module.ActionModule = type('KubernetesActionModule', (), {})
        fake_modules[k8s_module.__name__] = k8s_module
        spec = importlib.util.spec_from_file_location(
            'shared_mongodb_networkpolicy_guarded_k8s_contract', PLUGIN
        )
        assert spec is not None and spec.loader is not None
        cls.plugin = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, fake_modules):
            spec.loader.exec_module(cls.plugin)

    def test_exact_two_object_hash_bound_inventory(self) -> None:
        self.assertEqual(
            {
                'shared-mongodb-networkpolicy-allow',
                'shared-mongodb-networkpolicy-default-deny',
            },
            set(self.by_name),
        )
        ledger = {}
        for line in (COMPONENT / 'MANIFESTS.sha256').read_text().splitlines():
            digest, relative = line.split('  ', 1)
            ledger[relative] = digest
        self.assertEqual({str(path.relative_to(COMPONENT)) for path in self.paths}, set(ledger))
        for path in self.paths:
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                ledger[str(path.relative_to(COMPONENT))],
            )
        plugin = PLUGIN.read_text()
        literal = plugin.split('_EXPECTED_OBJECT_HASHES = ', 1)[1].split(
            '\n_EXPECTED_ARGUMENT_KEYS', 1
        )[0]
        plugin_hashes = ast.literal_eval(literal)
        expected = {}
        for obj in self.objects:
            identity = (
                obj['apiVersion'],
                obj['kind'],
                obj['metadata']['namespace'],
                obj['metadata']['name'],
            )
            expected[identity] = hashlib.sha256(
                json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()
            ).hexdigest()
        self.assertEqual(expected, plugin_hashes)
        self.assertIn('11352b9439d10f2ffdfad385ee31f524885fead8d74d38937101614f742ab575', plugin)
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(
            '/etc/rancher/k3s/k3s.yaml',
            defaults['shared_mongodb_networkpolicy_bootstrap_kubeconfig'],
        )
        self.assertEqual(2, defaults['shared_mongodb_networkpolicy_bootstrap_object_count'])
        self.assertIn('shared-mongodb-networkpolicy-default-deny.yaml', defaults['shared_mongodb_networkpolicy_bootstrap_manifest_paths'][0])
        self.assertIn('shared-mongodb-networkpolicy-allow.yaml', defaults['shared_mongodb_networkpolicy_bootstrap_manifest_paths'][1])
        self.assertEqual(
            sorted(self.by_name),
            sorted(defaults['shared_mongodb_networkpolicy_bootstrap_target_names']),
        )
        configured_hashes = {
            entry['path'].split('}}/', 1)[1]: entry['sha256']
            for entry in defaults['shared_mongodb_networkpolicy_bootstrap_expected_hashes']
        }
        self.assertEqual(set(ledger), set(configured_hashes))
        self.assertEqual(ledger, configured_hashes)
        identity_keys = sorted(
            '|'.join((obj['apiVersion'], obj['kind'], obj['metadata']['namespace'], obj['metadata']['name']))
            for obj in self.objects
        )
        self.assertEqual(
            '11352b9439d10f2ffdfad385ee31f524885fead8d74d38937101614f742ab575',
            hashlib.sha256('\n'.join(identity_keys).encode()).hexdigest(),
        )

    def test_live_operator_selector_and_exact_default_deny(self) -> None:
        selector = {
            'app': 'shared-mongodb-svc',
            'app.kubernetes.io/part-of': 'shared-databases',
            'cristex.io/component': 'mongodb',
        }
        deny = self.by_name['shared-mongodb-networkpolicy-default-deny']
        self.assertEqual('shared-services', deny['metadata']['namespace'])
        self.assertEqual(selector, deny['spec']['podSelector']['matchLabels'])
        self.assertEqual(['Ingress', 'Egress'], deny['spec']['policyTypes'])
        self.assertNotIn('ingress', deny['spec'])
        self.assertNotIn('egress', deny['spec'])

    def test_allow_policy_has_only_requested_ingress_and_egress(self) -> None:
        allow = self.by_name['shared-mongodb-networkpolicy-allow']['spec']
        selector = {
            'app': 'shared-mongodb-svc',
            'app.kubernetes.io/part-of': 'shared-databases',
            'cristex.io/component': 'mongodb',
        }
        self.assertEqual(selector, allow['podSelector']['matchLabels'])
        self.assertEqual(['Ingress', 'Egress'], allow['policyTypes'])
        self.assertEqual(1, len(allow['ingress']))
        ingress = allow['ingress'][0]
        self.assertEqual([{'protocol': 'TCP', 'port': 27017}], ingress['ports'])
        self.assertEqual(5, len(ingress['from']))
        self.assertEqual(
            [
                ('cristexhub-dev', 'backend'),
                ('cristexhub-dev', 'celery-worker'),
                ('cristexhub-prod', 'backend'),
                ('cristexhub-prod', 'celery-worker'),
            ],
            [
                (
                    source['namespaceSelector']['matchLabels']['kubernetes.io/metadata.name'],
                    source['podSelector']['matchLabels']['app.kubernetes.io/name'],
                )
                for source in ingress['from'][:4]
            ],
        )
        for source in ingress['from'][:4]:
            self.assertEqual(
                {'app.kubernetes.io/part-of': 'cristexhub'},
                {
                    key: value
                    for key, value in source['podSelector']['matchLabels'].items()
                    if key == 'app.kubernetes.io/part-of'
                },
            )
            self.assertNotIn('matchExpressions', source['podSelector'])
        self.assertEqual(selector, ingress['from'][4]['podSelector']['matchLabels'])
        self.assertNotIn('mongodb-system', json.dumps(allow))
        self.assertEqual(2, len(allow['egress']))
        same_set, dns = allow['egress']
        self.assertEqual(selector, same_set['to'][0]['podSelector']['matchLabels'])
        self.assertEqual([{'protocol': 'TCP', 'port': 27017}], same_set['ports'])
        self.assertEqual(
            {'kubernetes.io/metadata.name': 'kube-system'},
            dns['to'][0]['namespaceSelector']['matchLabels'],
        )
        self.assertEqual({'k8s-app': 'kube-dns'}, dns['to'][0]['podSelector']['matchLabels'])
        self.assertEqual({('TCP', 53), ('UDP', 53)}, {(x['protocol'], x['port']) for x in dns['ports']})

    def test_existing_target_uses_uid_resource_version_and_payload_cas(self) -> None:
        definition = copy.deepcopy(self.by_name['shared-mongodb-networkpolicy-default-deny'])
        prestate = {
            'name': definition['metadata']['name'],
            'uid': 'uid-default-deny',
            'resource_version': '17',
        }
        patch = self.plugin._networkpolicy_cas_patch(definition, prestate)
        self.assertEqual(
            [
                ('test', '/metadata/uid', 'uid-default-deny'),
                ('test', '/metadata/resourceVersion', '17'),
                ('test', '/metadata/labels', definition['metadata']['labels']),
                ('test', '/spec', definition['spec']),
            ],
            [(item['op'], item['path'], item['value']) for item in patch],
        )
        with self.assertRaises(ValueError):
            self.plugin._networkpolicy_cas_patch(definition, {
                'name': definition['metadata']['name'],
                'uid': 'uid-default-deny',
                'resource_version': 'stale',
            })

    def test_preflight_rejects_annotations_and_foreign_managed_field_ownership(self) -> None:
        definitions = copy.deepcopy(self.objects)
        pod = {
            'metadata': {'name': 'shared-mongodb-0', 'labels': self.plugin._MONGODB_POD_LABELS}
        }
        live = copy.deepcopy(definitions)
        for index, policy in enumerate(live):
            policy['metadata'].update({'uid': f'uid-{index}', 'resourceVersion': str(index + 1)})
        ledger = [
            {
                'name': policy['metadata']['name'],
                'uid': policy['metadata']['uid'],
                'resource_version': policy['metadata']['resourceVersion'],
            }
            for policy in live
        ]
        live[0]['metadata']['annotations'] = {'foreign.example/claim': 'x'}
        self.assertIn(
            'target NetworkPolicy drift',
            self.plugin._networkpolicy_preflight_error(live, definitions, pod, ledger),
        )
        live[0]['metadata'].pop('annotations')
        live[0]['metadata']['managedFields'] = [
            {'manager': 'argocd-application-controller', 'operation': 'Apply'}
        ]
        self.assertIn(
            'target NetworkPolicy drift',
            self.plugin._networkpolicy_preflight_error(live, definitions, pod, ledger),
        )
        live[0]['metadata']['managedFields'] = [
            {'manager': 'ansible', 'operation': 'Apply'}
        ]
        self.assertIsNone(
            self.plugin._networkpolicy_preflight_error(live, definitions, pod, ledger)
        )

    def test_portable_lock_requires_atomic_directory_owner_and_live_pid(self) -> None:
        with TemporaryDirectory() as directory:
            lock = Path(directory) / 'lock'
            lock.mkdir(mode=0o700)
            token = 'a' * 64
            (lock / 'owner').write_text(f'{token}:{os.getpid()}\n')
            (lock / 'owner').chmod(0o600)
            with mock.patch.object(self.plugin, '_EXPECTED_LOCK_FILE', str(lock)), mock.patch.dict(
                os.environ,
                {
                    'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_LOCK_FILE': str(lock),
                    'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_TOKEN': token,
                    'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_PID': str(os.getpid()),
                },
                clear=False,
            ):
                self.assertTrue(self.plugin._cooperative_lock_valid())
                (lock / 'owner').write_text(f'{token}:99999999\n')
                self.assertFalse(self.plugin._cooperative_lock_valid())

    def test_absent_target_uses_create_only_module_not_merge_update(self) -> None:
        plugin = PLUGIN.read_text()
        module = ROOT / 'ansible/library/shared_mongodb_networkpolicy_create.py'
        module_text = module.read_text()
        self.assertIn("module_name='shared_mongodb_networkpolicy_create'", plugin)
        self.assertIn('CREATE_ONLY_CONFLICT', module_text)
        self.assertIn('resource.create(', module_text)
        self.assertNotIn("self._task.action = 'kubernetes.core.k8s'", plugin)
        self.assertNotIn('state: absent', module_text)

    def test_selector_overlap_negative_cases_are_fail_closed(self) -> None:
        labels = {
            **self.plugin._MONGODB_POD_LABELS,
            'controller-revision-hash': 'example',
            'statefulset.kubernetes.io/pod-name': 'shared-mongodb-0',
        }
        overlap = self.plugin._selector_can_match_labels
        self.assertTrue(overlap({}, labels))
        self.assertTrue(overlap({'matchExpressions': [{'key': 'app', 'operator': 'Exists'}]}, labels))
        self.assertTrue(overlap({'matchExpressions': [{'key': 'future', 'operator': 'NotIn', 'values': ['x']}]}, labels))
        self.assertTrue(overlap({'matchExpressions': [{'key': 'future', 'operator': 'DoesNotExist'}]}, labels))
        self.assertFalse(overlap({'matchLabels': {'app': 'other'}}, labels))
        self.assertFalse(overlap({'matchExpressions': [{'key': 'app', 'operator': 'In', 'values': ['other']}]}, labels))
        self.assertFalse(overlap({'matchExpressions': [{'key': 'unknown', 'operator': 'Exists'}]}, labels))
        self.assertFalse(overlap({'matchExpressions': [{'key': 'app', 'operator': 'DoesNotExist'}]}, labels))

    def test_action_guard_rejects_apply_and_task_selection_before_kubernetes(self) -> None:
        context = self.plugin.context
        original = context.CLIARGS
        action = object.__new__(self.plugin.ActionModule)
        action._task = SimpleNamespace(args={}, get_path=lambda: '/not-canonical:1')
        try:
            context.CLIARGS = {
                'check': False,
                'start_at_task': None,
                'step': False,
                'tags': [],
                'skip_tags': [],
            }
            result = action.run(task_vars={})
            self.assertTrue(result['failed'])
            self.assertIn('MODE_GUARD', result['msg'])
            context.CLIARGS = {
                'check': False,
                'start_at_task': 'forged',
                'step': False,
                'tags': [],
                'skip_tags': [],
            }
            result = action.run(task_vars={})
            self.assertTrue(result['failed'])
            self.assertIn('TASK_SELECTION_GUARD', result['msg'])
        finally:
            context.CLIARGS = original

    def test_action_preflight_rejects_foreign_overlap_and_target_drift(self) -> None:
        definitions = copy.deepcopy(self.objects)
        pod = {
            'metadata': {'name': 'shared-mongodb-0', 'labels': self.plugin._MONGODB_POD_LABELS}
        }
        foreign_empty = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'NetworkPolicy',
            'metadata': {'namespace': 'shared-services', 'name': 'foreign-empty'},
            'spec': {'podSelector': {}},
        }
        self.assertIn(
            'foreign NetworkPolicy selector overlaps',
            self.plugin._networkpolicy_preflight_error([foreign_empty], definitions, pod),
        )
        drifted = copy.deepcopy(definitions)
        drifted[0]['spec']['policyTypes'] = ['Ingress']
        drifted[0]['metadata']['name'] = definitions[0]['metadata']['name']
        self.assertIn(
            'target NetworkPolicy drift',
            self.plugin._networkpolicy_preflight_error(drifted, definitions, pod),
        )
        live = copy.deepcopy(definitions)
        for index, policy in enumerate(live):
            policy['metadata']['uid'] = f'uid-{index}'
            policy['metadata']['resourceVersion'] = str(index + 1)
        ledger = [
            {
                'name': policy['metadata']['name'],
                'uid': policy['metadata']['uid'],
                'resource_version': policy['metadata']['resourceVersion'],
            }
            for policy in live
        ]
        self.assertIsNone(self.plugin._networkpolicy_preflight_error(live, definitions, pod, ledger))
        for field, value in (
            ('deletionTimestamp', '2026-08-25T00:00:00Z'),
            ('deletionGracePeriodSeconds', 30),
            ('deletionGracePeriod', 30),
            ('finalizers', []),
            ('ownerReferences', []),
        ):
            terminating = copy.deepcopy(live)
            terminating[0]['metadata'][field] = value
            self.assertIn(
                'target NetworkPolicy drift',
                self.plugin._networkpolicy_preflight_error(terminating, definitions, pod, ledger),
            )
        replacement = copy.deepcopy(live)
        replacement[0]['metadata']['uid'] = 'replacement-uid'
        self.assertIn(
            'target NetworkPolicy replacement',
            self.plugin._networkpolicy_preflight_error(replacement, definitions, pod, ledger),
        )

    def test_guarded_entrypoint_has_separate_check_and_apply_modes(self) -> None:
        wrapper = WRAPPER.read_text()
        self.assertIn("usage: ansible/bin/bootstrap-shared-mongodb-networkpolicy check|apply", wrapper)
        self.assertIn('--check', wrapper)
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_APPLY_APPROVED', wrapper)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap_mode', wrapper)
        self.assertNotIn('mongodb_bootstrap', wrapper)
        self.assertNotIn('bootstrap-mongodb', wrapper)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap_approved', wrapper)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap_mode in [\'check\', \'apply\']', TASKS.read_text())
        self.assertIn('shared_mongodb_networkpolicy_bootstrap', TASKS.read_text())
        self.assertIn('shared_mongodb_networkpolicy_guarded_k8s:', TASKS.read_text())
        self.assertIn('source-only', TASKS.read_text())
        self.assertIn("mode not in {'check', 'apply'}", PLUGIN.read_text())
        self.assertIn('APPROVAL_GUARD', PLUGIN.read_text())
        self.assertIn('MUTATION_ARGUMENT_GUARD', PLUGIN.read_text())
        self.assertIn('TASK_SELECTION_GUARD', PLUGIN.read_text())
        self.assertIn('Enumerate every shared-services NetworkPolicy', TASKS.read_text())
        self.assertIn("status.phase == 'Running'", TASKS.read_text())
        self.assertIn("status.currentMongoDBMembers | int == 1", TASKS.read_text())
        self.assertIn("name == 'shared-mongodb-0'", TASKS.read_text())
        self.assertIn('Query the exact live MongoDB StatefulSet', TASKS.read_text())
        self.assertIn("status.readyReplicas | int == 1", TASKS.read_text())
        self.assertIn("ownerReferences[0].uid ==", TASKS.read_text())
        self.assertIn("shared_mongodb_networkpolicy_bootstrap_internal_statefulset.resources[0].metadata.uid", TASKS.read_text())
        self.assertIn("map(attribute='resources') | map('length') | sum", TASKS.read_text())
        self.assertIn("_safe_int(binding.get('prestate_count'))", PLUGIN.read_text())
        self.assertIn("initial_prestate_count", PLUGIN.read_text())
        self.assertIn("transition_phase", PLUGIN.read_text())
        self.assertIn("_networkpolicy_cas_patch", PLUGIN.read_text())
        self.assertIn("kubernetes.core.k8s_json_patch", PLUGIN.read_text())
        self.assertIn("'path': '/metadata/resourceVersion'", PLUGIN.read_text())
        self.assertIn('validation_only', PLUGIN.read_text())
        self.assertIn('Enumerate every NetworkPolicy after the complete closure mutation', TASKS.read_text())
        self.assertIn('Reconcile the exact default-deny policy before any allow policy', TASKS.read_text())
        self.assertIn("lock_file='/tmp/cristexweb-shared-mongodb-networkpolicy.lock'", WRAPPER.read_text())
        self.assertIn('/bin/mkdir "$lock_file"', WRAPPER.read_text())
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_LOCK_FILE=$lock_file', WRAPPER.read_text())
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_PID=$wrapper_pid', WRAPPER.read_text())
        self.assertIn('_cooperative_lock_valid', PLUGIN.read_text())
        self.assertIn('_source_closure_valid', PLUGIN.read_text())
        self.assertIn('_runtime_binding_valid', PLUGIN.read_text())
        self.assertIn('managedFields', TASKS.read_text())
        self.assertIn('difference([\'ansible\'])', TASKS.read_text())
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_DEFAULTS_SHA256', TASKS.read_text())
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_CONTROLLER_SHA256', TASKS.read_text())
        self.assertIn('shared_mongodb_networkpolicy_create.py', WRAPPER.read_text())
        self.assertIn('resource.create(', (ROOT / 'ansible/library/shared_mongodb_networkpolicy_create.py').read_text())
        self.assertNotIn('/usr/bin/flock', WRAPPER.read_text())
        self.assertIn("binding.get('pod_owner_uid') == binding.get('statefulset_uid')", PLUGIN.read_text())
        self.assertIn('k8s-app=kube-dns', TASKS.read_text())
        self.assertIn('root:k3s-admin', TASKS.read_text())
        self.assertIn("spec.hostNetwork | default(false) | bool == false", TASKS.read_text())
        self.assertIn('shared_mongodb_networkpolicy_bootstrap_internal_all_networkpolicies', TASKS.read_text())
        self.assertIn("'deletionTimestamp' not in item.resources[0].metadata", TASKS.read_text())
        self.assertIn("'ownerReferences' not in item.resources[0].metadata", TASKS.read_text())
        self.assertIn('networkpolicy_prestate', PLUGIN.read_text())
        runbook = (ROOT / 'runbooks/shared-mongodb-networkpolicy-bootstrap.md').read_text()
        self.assertIn('cooperative lock', runbook.lower())
        self.assertIn('historical and predates the', runbook)
        self.assertIn('lifecycle/pre-state hardening', runbook)
        self.assertIn('fresh check is required', runbook)
        self.assertIn('Apply remains a', runbook)
        self.assertIn('no Kubernetes mutation', runbook)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap', PLAYBOOK.read_text())

    def test_no_secret_workload_or_operator_exception_source(self) -> None:
        source = '\n'.join(path.read_text() for path in COMPONENT.rglob('*') if path.is_file())
        for forbidden in ('kind: Secret', 'kind: Deployment', 'kind: StatefulSet', 'kind: Service', 'mongodb-system'):
            self.assertNotIn(forbidden, source)
        self.assertNotIn('cristex.io/database-client', source)
        self.assertNotIn('mongodb_bootstrap', TASKS.read_text() + DEFAULTS.read_text() + PLUGIN.read_text())

    def test_wrapper_shell_syntax_and_apply_approval_gate(self) -> None:
        result = subprocess.run(['sh', '-n', str(WRAPPER)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        result = subprocess.run([str(WRAPPER), 'apply'], env={}, capture_output=True, text=True)
        self.assertEqual(77, result.returncode, result.stdout + result.stderr)
        self.assertIn('APPLY_APPROVED=v1', result.stderr)


if __name__ == '__main__':
    unittest.main()
