from pathlib import Path
import hashlib
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / 'ansible/files/components/cristexhub-dev-registration'
DEFAULTS = ROOT / 'ansible/roles/cristexhub_dev_registration/defaults/main.yml'
APP = yaml.safe_load((COMP / 'config/application-cristexhub-dev.yaml').read_text())
PROJECT = yaml.safe_load((COMP / 'config/appproject-cristexhub-dev.yaml').read_text())

class RegistrationContractTests(unittest.TestCase):
    def test_exact_value_free_registration_objects(self):
        objs = [yaml.safe_load(p.read_text()) for p in sorted(COMP.rglob('*.yaml'))]
        self.assertEqual(4, len(objs))
        self.assertEqual({'AppProject','Application','Role','RoleBinding'}, {o['kind'] for o in objs})
        self.assertFalse(any(o['kind'] == 'Secret' for o in objs))

    def test_immutable_source_and_manual_sync(self):
        source = APP['spec']['source']
        self.assertEqual('https://github.com/devraider/cristexhub.git', source['repoURL'])
        self.assertRegex(source['targetRevision'], r'^[0-9a-f]{40}$')
        self.assertEqual('147bbbf7042e4bbca4bdd026494a855437238654', source['targetRevision'])
        self.assertEqual('infra/kubernetes/cristexhub-dev', source['path'])
        self.assertEqual('cristexhub-dev', APP['spec']['destination']['namespace'])
        self.assertNotIn('automated', APP['spec']['syncPolicy'])
        self.assertIn('CreateNamespace=false', APP['spec']['syncPolicy']['syncOptions'])
        self.assertIn('Prune=false', APP['spec']['syncPolicy']['syncOptions'])
        self.assertNotIn('resources-finalizer.argocd.argoproj.io', APP['metadata'].get('finalizers', []))

    def test_project_is_least_privilege(self):
        self.assertEqual([], PROJECT['spec']['clusterResourceWhitelist'])
        self.assertEqual([{'server':'https://kubernetes.default.svc','namespace':'cristexhub-dev'}], PROJECT['spec']['destinations'])
        kinds = {x['kind'] for x in PROJECT['spec']['namespaceResourceWhitelist']}
        self.assertNotIn('Secret', kinds)
        self.assertNotIn('Ingress', kinds)
        self.assertEqual([], PROJECT['spec'].get('namespaceResourceBlacklist', []))

    def test_rbac_is_namespaced_and_exact_subject(self):
        role = yaml.safe_load((COMP / 'rbac/role-argocd-application-controller-cristexhub-dev.yaml').read_text())
        self.assertEqual('cristexhub-dev', role['metadata']['namespace'])
        self.assertNotIn('*', str(role))
        binding = yaml.safe_load((COMP / 'rbac/rolebinding-argocd-application-controller-cristexhub-dev.yaml').read_text())
        self.assertEqual([{'kind':'ServiceAccount','name':'argocd-application-controller','namespace':'argocd'}], binding['subjects'])
        self.assertEqual('Role', binding['roleRef']['kind'])

    def test_hash_ledger_and_apply_blocker(self):
        defaults = DEFAULTS.read_text()
        self.assertIn('cristexhub_dev_registration_expected_hashes:', defaults)
        tasks = (ROOT / 'ansible/roles/cristexhub_dev_registration/tasks/main.yml').read_text()
        self.assertIn('APPLY_BLOCKED:', tasks)
        self.assertIn('when: not ansible_check_mode', tasks)
        self.assertIn('147bbbf7042e4bbca4bdd026494a855437238654', defaults)
