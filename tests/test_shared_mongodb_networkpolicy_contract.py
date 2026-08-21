from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / 'ansible/files/components/shared-mongodb-networkpolicy'
NETWORK = COMPONENT / 'network'
DEFAULTS = ROOT / 'ansible/roles/shared_mongodb_networkpolicy_bootstrap/defaults/main.yml'
TASKS = ROOT / 'ansible/roles/shared_mongodb_networkpolicy_bootstrap/tasks/main.yml'
PLUGIN = ROOT / 'ansible/plugins/action/shared_mongodb_networkpolicy_guarded_k8s.py'
WRAPPER = ROOT / 'ansible/bin/bootstrap-shared-mongodb-networkpolicy'
PLAYBOOK = ROOT / 'ansible/playbooks/bootstrap_shared_mongodb_networkpolicy.yml'


class SharedMongoDbNetworkPolicyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = sorted(NETWORK.glob('*.yaml'))
        cls.objects = [yaml.safe_load(path.read_text()) for path in cls.paths]
        cls.by_name = {obj['metadata']['name']: obj for obj in cls.objects}

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
