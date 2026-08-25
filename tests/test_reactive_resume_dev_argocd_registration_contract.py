from pathlib import Path
import hashlib
import stat
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / 'ansible/files/components/reactive-resume-dev-argocd-registration'
SOURCE = ROOT / 'ansible/files/policies/reactive-resume-dev-argocd-handoff'
DEFAULTS = ROOT / 'ansible/roles/reactive_resume_dev_argocd_registration/defaults/main.yml'
TASKS = ROOT / 'ansible/roles/reactive_resume_dev_argocd_registration/tasks/main.yml'
PLUGIN = ROOT / 'ansible/plugins/action/reactive_resume_dev_argocd_registration_guarded_k8s.py'
WRAPPER = ROOT / 'ansible/bin/bootstrap-reactive-resume-dev-argocd-registration'
PLAYBOOK = ROOT / 'ansible/playbooks/bootstrap_reactive_resume_dev_argocd_registration.yml'
RUNBOOK = ROOT / 'runbooks/reactive-resume-dev-argocd-registration.md'


def docs(path: Path):
    return [yaml.safe_load(p.read_text()) for p in sorted(path.rglob('*.yaml'))]


class ReactiveResumeDevArgoRegistrationContractTests(unittest.TestCase):
    def test_exact_registration_closure(self):
        objects = docs(REG)
        self.assertEqual(5, len(objects))
        self.assertEqual({'Application', 'AppProject', 'Role', 'RoleBinding', 'Secret'}, {x['kind'] for x in objects})
        self.assertNotIn('Secret', str([x for x in objects if x['kind'] != 'Secret']))
        app = next(x for x in objects if x['kind'] == 'Application')
        self.assertEqual('reactive-resume-dev', app['metadata']['name'])
        self.assertEqual('ssh://git@ssh.github.com:443/devraider/cristexweb.git', app['spec']['source']['repoURL'])
        self.assertEqual('2be0d834a5a07b28961613a564dcf5a87f020c97', app['spec']['source']['targetRevision'])
        self.assertEqual('ansible/files/components/reactive-resume-dev-argocd', app['spec']['source']['path'])
        self.assertEqual({'prune': False, 'selfHeal': True, 'allowEmpty': False}, app['spec']['syncPolicy']['automated'])
        self.assertIn('CreateNamespace=false', app['spec']['syncPolicy']['syncOptions'])
        self.assertIn('Prune=false', app['spec']['syncPolicy']['syncOptions'])
        self.assertNotIn('resources-finalizer.argocd.argoproj.io', app['metadata'].get('finalizers', []))

    def test_project_and_rbac_are_least_privilege(self):
        project = next(x for x in docs(REG) if x['kind'] == 'AppProject')
        self.assertEqual([], project['spec']['clusterResourceWhitelist'])
        self.assertEqual([{'name': 'reactive-resume-dev-local', 'namespace': 'cristexhub-dev'}], project['spec']['destinations'])
        self.assertEqual({'Deployment', 'Job', 'Service', 'ServiceAccount', 'Ingress', 'NetworkPolicy'}, {x['kind'] for x in project['spec']['namespaceResourceWhitelist']})
        self.assertEqual([{'kind': 'deny', 'schedule': '* * * * *', 'duration': '24h', 'applications': ['reactive-resume-dev'], 'manualSync': False}], project['spec']['syncWindows'])
        role = next(x for x in docs(REG) if x['kind'] == 'Role')
        self.assertNotIn('delete', str(role))
        self.assertNotIn('*', str(role))
        binding = next(x for x in docs(REG) if x['kind'] == 'RoleBinding')
        self.assertEqual('argocd-application-controller-reactive-resume-dev', binding['roleRef']['name'])

    def test_handoff_source_is_exact_dev_and_value_free(self):
        objects = docs(SOURCE)
        self.assertEqual(8, len(objects))
        self.assertEqual({'Deployment', 'Ingress', 'Job', 'NetworkPolicy', 'Service', 'ServiceAccount'}, {x['kind'] for x in objects})
        self.assertTrue(all(x['metadata']['namespace'] == 'cristexhub-dev' for x in objects))
        self.assertTrue(all(x['metadata']['labels']['app.kubernetes.io/managed-by'] == 'ansible' for x in objects))
        self.assertTrue(all(x['metadata']['labels'].get('cristex.io/bootstrap-writer') == 'ansible' or x['metadata']['labels'].get('app.kubernetes.io/bootstrap-writer') == 'ansible' for x in objects))
        self.assertTrue(all(x['metadata']['labels']['cristex.io/desired-owner'] == 'argocd' for x in objects))
        text = '\n'.join(p.read_text() for p in SOURCE.glob('*.yaml'))
        for forbidden in ('kind: Secret', 'kind: Namespace', 'kind: PersistentVolumeClaim', 'cristexhub-prod', 'reactive-resume-prod', 'stringData:', 'password:'):
            self.assertNotIn(forbidden, text)
        self.assertIn('reactive-resume-dev-private', text)
        self.assertIn('reactive-resume-dev-migrate', text)

    def test_hash_bound_guarded_entrypoint_and_runbook(self):
        defaults = DEFAULTS.read_text()
        tasks = TASKS.read_text()
        plugin = PLUGIN.read_text()
        wrapper = WRAPPER.read_text()
        runbook = RUNBOOK.read_text()
        self.assertIn('handoff_expected_hashes:', defaults)
        self.assertIn('no_dual_reconciliation: true', tasks)
        self.assertIn('managedFields', tasks)
        self.assertIn('argocd.argoproj.io/tracking-id', tasks)
        self.assertIn('EXPECTED_HANDOFF', plugin)
        self.assertIn('no_delete_path', plugin)
        self.assertIn('task selection controls are forbidden', plugin)
        self.assertIn('check|apply', wrapper)
        self.assertIn('--diff', wrapper)
        self.assertIn('env -i', wrapper)
        self.assertIn('CRISTEXWEB_REACTIVE_RESUME_DEV_ARGOCD_REGISTRATION_ENTRYPOINT=v1', wrapper)
        self.assertNotIn('exec "$@"', wrapper)
        self.assertIn('no dual reconciliation', runbook)
        self.assertIn('prune=false', runbook)
        self.assertIn('allowEmpty=false', runbook)
        self.assertIn('CreateNamespace=false', runbook)
        self.assertNotIn('cristexhub-prod', app_text := next(x for x in docs(REG) if x['kind'] == 'Application')['spec']['destination']['namespace'])
        self.assertEqual(0o755, stat.S_IMODE(WRAPPER.stat().st_mode))
        self.assertEqual('reactive_resume_dev_argocd_registration', PLAYBOOK.read_text().split('role: ')[1].split('\n')[0])
        for p in SOURCE.glob('*.yaml'):
            self.assertEqual(0o644, stat.S_IMODE(p.stat().st_mode))

    def test_source_hashes_are_recorded(self):
        defaults = DEFAULTS.read_text()
        for p in REG.rglob('*.yaml'):
            self.assertIn(hashlib.sha256(p.read_bytes()).hexdigest(), defaults)
        for p in SOURCE.glob('*.yaml'):
            self.assertIn(hashlib.sha256(p.read_bytes()).hexdigest(), defaults)


if __name__ == '__main__':
    unittest.main()
