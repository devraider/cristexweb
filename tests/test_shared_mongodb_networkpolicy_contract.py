from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
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
        self.assertEqual(3, len(ingress['from']))
        namespace_names = []
        for source in ingress['from'][:2]:
            namespace_names.append(source['namespaceSelector']['matchLabels']['kubernetes.io/metadata.name'])
            self.assertEqual({'app.kubernetes.io/part-of': 'cristexhub'}, source['podSelector']['matchLabels'])
            self.assertEqual(
                [{
                    'key': 'app.kubernetes.io/name',
                    'operator': 'In',
                    'values': ['backend', 'celery-worker'],
                }],
                source['podSelector']['matchExpressions'],
            )
        self.assertEqual(['cristexhub-dev', 'cristexhub-prod'], namespace_names)
        self.assertEqual(selector, ingress['from'][2]['podSelector']['matchLabels'])
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
            self.assertIn('SOURCE_ONLY_GUARD', result['msg'])
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

    def test_guarded_entrypoint_is_check_only_and_dedicated(self) -> None:
        wrapper = WRAPPER.read_text()
        self.assertIn("usage: ansible/bin/bootstrap-shared-mongodb-networkpolicy check", wrapper)
        self.assertIn('--check', wrapper)
        self.assertNotIn('mongodb_bootstrap', wrapper)
        self.assertNotIn('bootstrap-mongodb', wrapper)
        self.assertNotIn('apply ]', wrapper)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap_approved', wrapper)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap', TASKS.read_text())
        self.assertIn('shared_mongodb_networkpolicy_guarded_k8s:', TASKS.read_text())
        self.assertIn('source-only', TASKS.read_text())
        self.assertIn("if not context.CLIARGS.get('check')", PLUGIN.read_text())
        self.assertIn('SOURCE_ONLY_GUARD', PLUGIN.read_text())
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
        self.assertIn("_safe_int(binding.get('prestate_count')) in (0, 2)", PLUGIN.read_text())
        self.assertIn("binding.get('pod_owner_uid') == binding.get('statefulset_uid')", PLUGIN.read_text())
        self.assertIn('k8s-app=kube-dns', TASKS.read_text())
        self.assertIn('root:k3s-admin', TASKS.read_text())
        self.assertIn("spec.hostNetwork | default(false) | bool == false", TASKS.read_text())
        self.assertIn('shared_mongodb_networkpolicy_bootstrap_internal_all_networkpolicies', TASKS.read_text())
        runbook = (ROOT / 'runbooks/shared-mongodb-networkpolicy-bootstrap.md').read_text()
        self.assertIn('ok=34 changed=1 unreachable=0 failed=0 skipped=0', runbook)
        self.assertIn('check mode made no Kubernetes change', runbook)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap', PLAYBOOK.read_text())

    def test_no_secret_workload_or_operator_exception_source(self) -> None:
        source = '\n'.join(path.read_text() for path in COMPONENT.rglob('*') if path.is_file())
        for forbidden in ('kind: Secret', 'kind: Deployment', 'kind: StatefulSet', 'kind: Service', 'mongodb-system'):
            self.assertNotIn(forbidden, source)
        self.assertNotIn('cristex.io/database-client', source)
        self.assertNotIn('mongodb_bootstrap', TASKS.read_text() + DEFAULTS.read_text() + PLUGIN.read_text())

    def test_wrapper_shell_syntax(self) -> None:
        result = subprocess.run(['sh', '-n', str(WRAPPER)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
