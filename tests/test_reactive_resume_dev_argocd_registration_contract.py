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
        self.assertEqual('dd7d4cedd902e68266d9713d1dbb8e90f0b529b1', app['spec']['source']['targetRevision'])
        self.assertEqual('ansible/files/components/reactive-resume-dev-argocd', app['spec']['source']['path'])
        self.assertEqual({'prune': False, 'selfHeal': True, 'allowEmpty': False}, app['spec']['syncPolicy']['automated'])
        self.assertIn('CreateNamespace=false', app['spec']['syncPolicy']['syncOptions'])
        self.assertIn('Prune=false', app['spec']['syncPolicy']['syncOptions'])
        self.assertNotIn('resources-finalizer.argocd.argoproj.io', app['metadata'].get('finalizers', []))

    def test_project_and_rbac_are_least_privilege(self):
        project = next(x for x in docs(REG) if x['kind'] == 'AppProject')
        self.assertEqual([], project['spec']['clusterResourceWhitelist'])
        self.assertEqual([{'name': 'reactive-resume-dev-local', 'namespace': 'cristexhub-dev'}], project['spec']['destinations'])
        self.assertEqual({'Deployment', 'Service', 'ServiceAccount', 'Ingress', 'NetworkPolicy'}, {x['kind'] for x in project['spec']['namespaceResourceWhitelist']})
        self.assertEqual([{'kind': 'deny', 'schedule': '* * * * *', 'duration': '24h', 'applications': ['reactive-resume-dev'], 'manualSync': False}], project['spec']['syncWindows'])
        role = next(x for x in docs(REG) if x['kind'] == 'Role')
        self.assertNotIn('jobs', str(role))
        self.assertNotIn('delete', str(role))
        self.assertNotIn('*', str(role))
        binding = next(x for x in docs(REG) if x['kind'] == 'RoleBinding')
        self.assertEqual('argocd-application-controller-reactive-resume-dev', binding['roleRef']['name'])

    def test_dependency_contracts_are_exact_and_payload_suppressed(self):
        defaults = yaml.safe_load(DEFAULTS.read_text())
        contracts = defaults['reactive_resume_dev_argocd_registration_dependency_contracts']
        self.assertEqual(6, len(contracts))
        self.assertEqual(
            ['reactive-resume-dev-runtime', 'reactive-resume-dev-migration',
             'reactive-resume-dev-postgresql-ca', 'reactive-resume-dev-object-storage-ca',
             'cristexhub-ghcr-pull', 'reactive-resume-dev-tls'],
            [item['name'] for item in contracts],
        )
        self.assertEqual(
            ['Opaque', 'Opaque', None, 'Opaque', 'kubernetes.io/dockerconfigjson', 'kubernetes.io/tls'],
            [item.get('type') for item in contracts],
        )
        for item in contracts:
            self.assertEqual('cristexhub-dev', item['namespace'])
            self.assertEqual('secrets.infisical.com/version', item['annotation_key'])
            self.assertIn('data', item['hidden_fields'])
            self.assertIn('binaryData', item['hidden_fields'])
            self.assertEqual(
                {'app.kubernetes.io/managed-by': 'infisical',
                 'app.kubernetes.io/part-of': 'cristexhub' if item['name'] == 'cristexhub-ghcr-pull' else 'reactive-resume',
                 'cristex.io/value-owner': 'infisical-cloud'},
                item['labels'],
            )

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
        self.assertIn('dependency_contracts:', defaults)
        self.assertIn('reactive-resume-dev-runtime', defaults)
        self.assertIn('reactive-resume-dev-migration', defaults)
        self.assertIn('reactive-resume-dev-postgresql-ca', defaults)
        self.assertIn('reactive-resume-dev-object-storage-ca', defaults)
        self.assertIn('cristexhub-ghcr-pull', defaults)
        self.assertIn('reactive-resume-dev-tls', defaults)
        self.assertIn('hidden_fields:', tasks)
        self.assertIn('Require exact RR Secret, CA, pull, and TLS dependency metadata', tasks)
        self.assertIn('Require ready existing Reactive Resume DEV workload dependencies', tasks)
        self.assertIn('exact_application_source_contract', tasks)
        self.assertIn('item.resources[0].spec.source == item.item.spec.source', tasks)
        self.assertIn('item.resources[0].spec.destination == item.item.spec.destination', tasks)
        self.assertIn('item.resources[0].spec.syncPolicy == item.item.spec.syncPolicy', tasks)
        self.assertIn('no_dual_reconciliation: true', tasks)
        self.assertIn('reactive_resume_dev_argocd_registration_desired_state_paths', tasks)
        self.assertIn('reactive_resume_dev_argocd_registration_destination_policy_paths', tasks)
        self.assertIn('item.rc == 0', tasks)
        self.assertIn('every live workload object equals', tasks)
        self.assertIn('cross-Namespace destination NetworkPolicy', tasks)
        self.assertIn('managedFields', tasks)
        self.assertIn('argocd.argoproj.io/tracking-id', tasks)
        self.assertIn('EXPECTED_HANDOFF', plugin)
        self.assertIn('dependency_names', plugin)
        self.assertIn('no_delete_path', plugin)
        self.assertIn('task selection controls are forbidden', plugin)
        self.assertIn('check|apply', wrapper)
        self.assertIn('--diff', wrapper)
        self.assertIn('env -i', wrapper)
        self.assertIn('CRISTEXWEB_REACTIVE_RESUME_DEV_ARGOCD_REGISTRATION_ENTRYPOINT=v1', wrapper)
        self.assertNotIn('exec "$@"', wrapper)
        self.assertIn('no dual reconciliation', runbook)
        self.assertIn('SOURCE IMPLEMENTED / GUARDED CHECK BLOCKED ON REPOSITORY CREDENTIAL', runbook)
        self.assertIn('latest guarded `check` reached the', runbook)
        self.assertIn('live dependency preflight', runbook)
        self.assertIn('argocd-repository-cristexweb', runbook)
        self.assertIn('No registration apply, Argo sync, adoption, workload restart, or', runbook)
        self.assertIn('other mutation occurred', runbook)
        self.assertIn('migration Job is excluded from the automated Argo desired-state', runbook)
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
