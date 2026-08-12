from pathlib import Path
import unittest, yaml
ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / 'ansible/files/components/keycloak-route'
class KeycloakRouteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.objects=[]
        for p in sorted(COMP.rglob('*.yaml')):
            cls.objects.append(yaml.safe_load(p.read_text()))
    def test_exact_route(self):
        ingress = next(x for x in self.objects if x['kind']=='Ingress')
        self.assertEqual('shared-services', ingress['metadata']['namespace'])
        self.assertEqual('traefik', ingress['spec']['ingressClassName'])
        self.assertEqual([{'host':'auth.cristex-soft.com','http':{'paths':[{'path':'/','pathType':'Prefix','backend':{'service':{'name':'keycloak','port':{'number':8080}}}}]}}], ingress['spec']['rules'])
    def test_network_policy_only_allows_traefik_keycloak_port(self):
        policy = next(x for x in self.objects if x['kind']=='NetworkPolicy')
        self.assertEqual(['Ingress'], policy['spec']['policyTypes'])
        self.assertEqual(8080, policy['spec']['ingress'][0]['ports'][0]['port'])
        self.assertEqual({'app.kubernetes.io/name':'traefik'}, policy['spec']['ingress'][0]['from'][0]['podSelector']['matchLabels'])
    def test_no_secret_or_management_route(self):
        self.assertFalse(any(x['kind']=='Secret' for x in self.objects))
        text='\n'.join(p.read_text() for p in COMP.rglob('*.yaml'))
        self.assertNotIn('9000', text); self.assertNotIn('management', text.lower()); self.assertNotIn('cloudflared', text.lower())
if __name__ == '__main__': unittest.main()
