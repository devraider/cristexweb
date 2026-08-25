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
        self.assertEqual(5, len(objs))
        self.assertEqual({'AppProject','Application','Role','RoleBinding','Secret'}, {o['kind'] for o in objs})
        cluster = next(o for o in objs if o['kind'] == 'Secret')
        self.assertEqual('argocd-cluster-cristexhub-dev', cluster['metadata']['name'])
        self.assertEqual({'name':'cristexhub-dev-local','server':'https://kubernetes.default.svc','namespaces':'cristexhub-dev','clusterResources':'false','config':'{}'}, cluster['stringData'])
        self.assertNotIn('token', str(cluster).lower())
        self.assertNotIn('password', str(cluster).lower())

    def test_immutable_source_and_manual_sync(self):
        source = APP['spec']['source']
        self.assertEqual('ssh://git@ssh.github.com:443/devraider/cristexhub.git', source['repoURL'])
        self.assertRegex(source['targetRevision'], r'^[0-9a-f]{40}$')
        self.assertEqual('57fffab4585fed12161144de7114c8ad05f3ba94', source['targetRevision'])
        self.assertEqual('infra/kubernetes/cristexhub-dev', source['path'])
        self.assertEqual({'name':'cristexhub-dev-local','server':'','namespace':'cristexhub-dev'}, APP['spec']['destination'])
        self.assertNotIn('automated', APP['spec']['syncPolicy'])
        self.assertIn('CreateNamespace=false', APP['spec']['syncPolicy']['syncOptions'])
        self.assertIn('Prune=false', APP['spec']['syncPolicy']['syncOptions'])
        self.assertNotIn('resources-finalizer.argocd.argoproj.io', APP['metadata'].get('finalizers', []))

    def test_project_is_least_privilege(self):
        self.assertEqual([], PROJECT['spec']['clusterResourceWhitelist'])
        self.assertEqual([
            {'name':'cristexhub-dev-local','namespace':'cristexhub-dev'},
            {'name':'reactive-resume-dev-local','namespace':'cristexhub-dev'},
        ], PROJECT['spec']['destinations'])
        kinds = {x['kind'] for x in PROJECT['spec']['namespaceResourceWhitelist']}
        self.assertNotIn('Secret', kinds)
        self.assertIn('Ingress', kinds)
        self.assertEqual([], PROJECT['spec'].get('namespaceResourceBlacklist', []))
        self.assertEqual([{'kind':'deny','schedule':'* * * * *','duration':'24h','applications':['cristexhub-dev'],'manualSync':False}], PROJECT['spec']['syncWindows'])

    def test_rbac_has_only_namespaced_writes(self):
        role = yaml.safe_load((COMP / 'rbac/role-argocd-application-controller-cristexhub-dev.yaml').read_text())
        self.assertEqual('cristexhub-dev', role['metadata']['namespace'])
        self.assertNotIn('*', str(role))
        binding = yaml.safe_load((COMP / 'rbac/rolebinding-argocd-application-controller-cristexhub-dev.yaml').read_text())
        self.assertEqual([{'kind':'ServiceAccount','name':'argocd-application-controller','namespace':'argocd'}], binding['subjects'])
        self.assertEqual('Role', binding['roleRef']['kind'])
        self.assertFalse(any(p.name.startswith('clusterrole') for p in (COMP / 'rbac').glob('*.yaml')))

    def test_hash_ledger_and_guarded_prerequisites(self):
        defaults = DEFAULTS.read_text()
        self.assertIn('cristexhub_dev_registration_expected_hashes:', defaults)
        tasks = (ROOT / 'ansible/roles/cristexhub_dev_registration/tasks/main.yml').read_text()
        self.assertIn('argocd-repository-cristexhub', tasks)
        self.assertIn("data.type | b64decode == 'git'", tasks)
        self.assertIn("data.url | b64decode == 'ssh://git@ssh.github.com:443/devraider/cristexhub.git'", tasks)
        self.assertIn('metadata.ownerReferences', tasks)
        self.assertIn('syncPolicy.automated is not defined', tasks)
        self.assertIn('Reconcile registration source without synchronization', tasks)
        self.assertNotIn('automated', APP['spec']['syncPolicy'])
        self.assertIn('57fffab4585fed12161144de7114c8ad05f3ba94', defaults)
