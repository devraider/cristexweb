from pathlib import Path
import hashlib
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / 'ansible/files/components/argocd-route'

class ArgoCdPrivateUiRouteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.objects = [yaml.safe_load(p.read_text()) for p in COMPONENT.rglob('*.yaml')]

    def test_exact_tls_terminated_route(self):
        ingress = next(o for o in self.objects if o['kind'] == 'Ingress')
        self.assertEqual('argo.cristex-soft.com', ingress['spec']['rules'][0]['host'])
        self.assertEqual('argocd-ui-tls', ingress['spec']['tls'][0]['secretName'])
        self.assertEqual(80, ingress['spec']['rules'][0]['http']['paths'][0]['backend']['service']['port']['number'])
        self.assertEqual('true', ingress['metadata']['annotations']['traefik.ingress.kubernetes.io/router.tls'])

    def test_route_has_no_secret_values_and_exact_network_policy(self):
        text = '\n'.join(p.read_text() for p in COMPONENT.rglob('*.yaml'))
        self.assertNotIn('tls.key:', text)
        policy = next(o for o in self.objects if o['kind'] == 'NetworkPolicy')
        self.assertEqual(['Ingress'], policy['spec']['policyTypes'])
        self.assertEqual(8080, policy['spec']['ingress'][0]['ports'][0]['port'])
        self.assertEqual('kube-system', policy['spec']['ingress'][0]['from'][0]['namespaceSelector']['matchLabels']['kubernetes.io/metadata.name'])

    def test_manifest_hash_ledger(self):
        ledger = {r: d for d, r in (line.split('  ', 1) for line in (COMPONENT / 'MANIFESTS.sha256').read_text().splitlines())}
        self.assertEqual(set(ledger), {str(p.relative_to(COMPONENT)) for p in COMPONENT.rglob('*.yaml')})
        for path in COMPONENT.rglob('*.yaml'):
            self.assertEqual(ledger[str(path.relative_to(COMPONENT))], hashlib.sha256(path.read_bytes()).hexdigest())

if __name__ == '__main__':
    unittest.main()
