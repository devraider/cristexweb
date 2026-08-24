from pathlib import Path
import hashlib
import json
import stat
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / 'ansible/files/components/cristexhub-dev-sync-transition'
APP = yaml.safe_load((COMP / 'config/application-cristexhub-dev-automated.yaml').read_text())
PROJECT = yaml.safe_load((COMP / 'config/appproject-cristexhub-dev-automated.yaml').read_text())
ACTIVE = yaml.safe_load((ROOT / 'ansible/files/components/cristexhub-dev-registration/config/application-cristexhub-dev.yaml').read_text())


class AutomatedSyncTransitionContractTests(unittest.TestCase):
    def test_candidate_enables_only_safe_automated_sync(self):
        self.assertEqual('cristexhub-dev', APP['metadata']['name'])
        self.assertEqual('cristexhub-dev-sync-transition', APP['metadata']['labels']['cristex.io/component'])
        automated = APP['spec']['syncPolicy']['automated']
        self.assertEqual({'prune': False, 'selfHeal': True, 'allowEmpty': False}, automated)
        self.assertIn('Prune=false', APP['spec']['syncPolicy']['syncOptions'])
        self.assertIn('CreateNamespace=false', APP['spec']['syncPolicy']['syncOptions'])
        self.assertEqual([], PROJECT['spec']['syncWindows'])
        self.assertEqual([], PROJECT['spec']['clusterResourceWhitelist'])
        self.assertNotIn('Secret', {x['kind'] for x in PROJECT['spec']['namespaceResourceWhitelist']})

    def test_active_registration_remains_manual_and_unchanged(self):
        self.assertNotIn('automated', ACTIVE['spec']['syncPolicy'])
        self.assertIn('Prune=false', ACTIVE['spec']['syncPolicy']['syncOptions'])
        self.assertEqual('cristexhub-dev-registration', ACTIVE['metadata']['labels']['cristex.io/component'])
        self.assertNotEqual(ACTIVE['metadata']['labels']['cristex.io/component'], APP['metadata']['labels']['cristex.io/component'])

    def test_gate_contract_is_value_free_and_exact(self):
        defaults = (ROOT / 'ansible/roles/cristexhub_dev_sync_transition/defaults/main.yml').read_text()
        tasks = (ROOT / 'ansible/roles/cristexhub_dev_sync_transition/tasks/main.yml').read_text()
        self.assertIn('cristexhub_dev_sync_transition_runtime_secret_keys:', defaults)
        parsed_defaults = yaml.safe_load(defaults)
        self.assertIn('BROWSERLESS_TOKEN', parsed_defaults['cristexhub_dev_sync_transition_runtime_secret_keys'])
        self.assertEqual('43582cc3b79f961148760b3d23bbadea913d9acf', parsed_defaults['cristexhub_dev_sync_transition_revision'])
        self.assertFalse(parsed_defaults['cristexhub_dev_sync_transition_image_provenance_verified'])
        for gate in ('image', 'runtime Secret', 'namespace-scoped Argo cache', 'OIDC proxy', 'dependency'):
            self.assertIn(gate, tasks)
        self.assertIn('all automated-sync promotion gates', tasks)
        self.assertIn('oidc-connect-proxy', defaults)
        self.assertIn('PRIVATE_CA_BUNDLE', defaults)
        self.assertNotIn('clientSecret:', str(APP))
        self.assertNotIn('password:', str(APP))

    def test_source_hashes_and_guarded_entrypoint(self):
        for path in sorted((COMP / 'config').glob('*.yaml')):
            self.assertEqual(0o644, stat.S_IMODE(path.stat().st_mode))
        defaults = (ROOT / 'ansible/roles/cristexhub_dev_sync_transition/defaults/main.yml').read_text()
        for path in sorted((COMP / 'config').glob('*.yaml')):
            self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(), defaults)
        entrypoint = ROOT / 'ansible/bin/bootstrap-cristexhub-dev-sync-transition'
        self.assertTrue(entrypoint.stat().st_mode & stat.S_IXUSR)
        text = entrypoint.read_text()
        self.assertIn('check|apply', text)
        self.assertIn('--diff', text)
        self.assertIn('env -i', text)
        self.assertIn('CRISTEXWEB_ARGOCD_SYNC_TRANSITION_ENTRYPOINT=v1', text)

    def test_guard_rejects_task_selection_and_has_exact_objects(self):
        plugin = (ROOT / 'ansible/plugins/action/cristexhub_dev_sync_transition_guarded_k8s.py').read_text()
        tasks = (ROOT / 'ansible/roles/cristexhub_dev_sync_transition/tasks/main.yml').read_text()
        self.assertIn('task selection controls are forbidden', plugin)
        self.assertIn('MUTATION_ARGUMENT_GUARD', plugin)
        self.assertIn('wait_timeout', plugin)
        self.assertIn('manifest_paths | length == 2', tasks)
        self.assertIn('kubeconfig == \'/etc/rancher/k3s/k3s.yaml\'', tasks)


if __name__ == '__main__':
    unittest.main()
