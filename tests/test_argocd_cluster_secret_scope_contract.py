from pathlib import Path
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_SECRETS = (
    ROOT / 'ansible/files/components/cristexhub-dev-registration/config/secret-cluster-cristexhub-dev.yaml',
    ROOT / 'ansible/files/components/cristexhub-prod-registration/config/secret-cluster-cristexhub-prod.yaml',
    ROOT / 'ansible/files/components/reactive-resume-dev-argocd-registration/config/secret-cluster-reactive-resume-dev.yaml',
)
EXPECTED_NAMESPACES = 'cristexhub-dev,cristexhub-prod'


class ArgoClusterSecretScopeContractTests(unittest.TestCase):
    def test_all_same_server_registration_secrets_share_exact_bounded_namespace_scope(self) -> None:
        values = []
        for path in REGISTRATION_SECRETS:
            manifest = yaml.safe_load(path.read_text())
            self.assertEqual('Secret', manifest['kind'])
            self.assertEqual('Opaque', manifest['type'])
            self.assertEqual('https://kubernetes.default.svc', manifest['stringData']['server'])
            self.assertEqual('false', manifest['stringData']['clusterResources'])
            namespaces = manifest['stringData']['namespaces']
            self.assertEqual(EXPECTED_NAMESPACES, namespaces, path)
            self.assertEqual(['cristexhub-dev', 'cristexhub-prod'], namespaces.split(','))
            self.assertNotIn(' ', namespaces)
            values.append(namespaces)
        self.assertEqual([EXPECTED_NAMESPACES] * 3, values)

    def test_each_owner_lane_supports_check_apply_and_postvalidates_scope(self) -> None:
        lanes = (
            (ROOT / 'ansible/bin/bootstrap-cristexhub-dev-registration', ROOT / 'ansible/roles/cristexhub_dev_registration/tasks/main.yml'),
            (ROOT / 'ansible/bin/bootstrap-cristexhub-prod-registration', ROOT / 'ansible/roles/cristexhub_prod_registration/tasks/main.yml'),
            (ROOT / 'ansible/bin/bootstrap-reactive-resume-dev-argocd-registration', ROOT / 'ansible/roles/reactive_resume_dev_argocd_registration/tasks/main.yml'),
        )
        for wrapper, tasks in lanes:
            wrapper_text = wrapper.read_text()
            task_text = tasks.read_text()
            self.assertTrue(
                'check|apply' in wrapper_text or
                ('[ "$1" = check ]' in wrapper_text and '[ "$1" = apply ]' in wrapper_text),
                wrapper,
            )
            self.assertIn("state: present", task_text, tasks)
            self.assertIn('b64decode', task_text, tasks)
            self.assertIn('cluster_namespaces', task_text, tasks)
            self.assertIn('when: not ansible_check_mode', task_text, tasks)
        self.assertIn("['cristexhub-prod', cristexhub_prod_registration_cluster_namespaces]", (ROOT / 'ansible/roles/cristexhub_prod_registration/tasks/main.yml').read_text())
        self.assertIn("['cristexhub-dev', reactive_resume_dev_argocd_registration_cluster_namespaces]", (ROOT / 'ansible/roles/reactive_resume_dev_argocd_registration/tasks/main.yml').read_text())
        prod_plugin = (ROOT / 'ansible/plugins/action/cristexhub_prod_registration_guarded_k8s.py').read_text()
        self.assertIn('kubernetes.core.k8s_json_patch', prod_plugin)
        self.assertIn('op": "test"', prod_plugin)
        self.assertIn('/metadata/uid', prod_plugin)
        self.assertIn('/spec', prod_plugin)

    def test_scope_does_not_widen_application_destinations_or_rbac(self) -> None:
        app_specs = (
            ROOT / 'ansible/files/components/cristexhub-dev-registration/config/application-cristexhub-dev.yaml',
            ROOT / 'ansible/files/components/cristexhub-prod-registration/config/application-cristexhub-prod.yaml',
            ROOT / 'ansible/files/components/reactive-resume-dev-argocd-registration/config/application-reactive-resume-dev.yaml',
        )
        expected = (
            ('cristexhub-dev', ''),
            ('cristexhub-prod', ''),
            ('cristexhub-dev', 'https://kubernetes.default.svc'),
        )
        for path, (namespace, server) in zip(app_specs, expected):
            manifest = yaml.safe_load(path.read_text())
            destination = manifest['spec']['destination']
            self.assertEqual(namespace, destination['namespace'], path)
            self.assertEqual(server, destination.get('server', ''))
        for path in (
            ROOT / 'ansible/files/components/cristexhub-dev-registration/rbac/role-argocd-application-controller-cristexhub-dev.yaml',
            ROOT / 'ansible/files/components/cristexhub-prod-registration/rbac/role-argocd-application-controller-cristexhub-prod.yaml',
            ROOT / 'ansible/files/components/reactive-resume-dev-argocd-registration/rbac/role-argocd-application-controller-reactive-resume-dev.yaml',
        ):
            role = yaml.safe_load(path.read_text())
            self.assertNotIn('*', str(role))
            self.assertNotIn('delete', str(role))


if __name__ == '__main__':
    unittest.main()
