from __future__ import annotations
import ast, hashlib, json, unittest
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
COMP=ROOT/'ansible/files/components/infisical-reactive-resume-dev-ca'
DEFAULTS=ROOT/'ansible/roles/infisical_reactive_resume_dev_ca_bootstrap/defaults/main.yml'
TASKS=ROOT/'ansible/roles/infisical_reactive_resume_dev_ca_bootstrap/tasks/main.yml'
PLUGIN=ROOT/'ansible/plugins/action/infisical_reactive_resume_dev_ca_guarded_k8s.py'
WRAPPER=ROOT/'ansible/bin/bootstrap-infisical-reactive-resume-dev-ca'
class CaClosureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.paths=sorted(COMP.rglob('*.yaml')); cls.objects=[yaml.safe_load(p.read_text()) for p in cls.paths]
 def test_exact_value_free_closure(self):
  self.assertEqual(7,len(self.objects)); self.assertEqual({'ValidatingAdmissionPolicy':2,'ValidatingAdmissionPolicyBinding':2,'Role':1,'RoleBinding':1,'InfisicalStaticSecret':1},{k:sum(x['kind']==k for x in self.objects) for k in {x['kind'] for x in self.objects}}); self.assertFalse(any(x['kind']=='Secret' for x in self.objects))
 def test_exact_sources_and_targets(self):
  s=next(x for x in self.objects if x['kind']=='InfisicalStaticSecret'); self.assertEqual('cristexhub-dev',s['metadata']['namespace']); self.assertEqual('cristexhub-dev-infisical-auth',s['spec']['infisicalAuthRef']['name']); self.assertEqual(['/shared-services/postgresql','/reactive-resume/dev/object-storage-tls'],[x['secretPath'] for x in s['spec']['sources']]); self.assertEqual(['{{ .POSTGRESQL_TLS_CA_CRT.Value }}','{{ .CA_CRT.Value }}'],[s['spec']['targets'][0]['template']['data']['ca.crt'],s['spec']['targets'][1]['template']['data']['ca.crt']])
  self.assertEqual([('reactive-resume-dev-postgresql-ca','ConfigMap'),('reactive-resume-dev-object-storage-ca','Secret')],[(x['name'],x['kind']) for x in s['spec']['targets']])
 def test_exact_operator_writer_and_guard(self):
  rb=next(x for x in self.objects if x['kind']=='RoleBinding'); self.assertEqual('shared-services',rb['subjects'][0]['namespace']); self.assertEqual('infisical-operator-controller',rb['subjects'][0]['name']); role=next(x for x in self.objects if x['kind']=='Role'); self.assertEqual({'secrets','configmaps'},set(role['rules'][0]['resources'])); self.assertIn('check|apply',WRAPPER.read_text()); self.assertIn('CRISTEXWEB_INFISICAL_REACTIVE_RESUME_DEV_CA_TOKEN',WRAPPER.read_text()); self.assertIn('precreated DEV Infisical Auth',TASKS.read_text())
 def test_hash_ledgers_and_action_map(self):
  ledger={line.split('  ',1)[1]:line.split()[0] for line in (COMP/'MANIFESTS.sha256').read_text().splitlines()}; self.assertEqual(set(ledger),{str(p.relative_to(COMP)) for p in self.paths}); self.assertTrue(all(hashlib.sha256((COMP/r).read_bytes()).hexdigest()==h for r,h in ledger.items())); d=yaml.safe_load(DEFAULTS.read_text()); configured={x['path'].split('/ansible/files/components/infisical-reactive-resume-dev-ca/',1)[1]:x['sha256'] for x in d['infisical_reactive_resume_dev_ca_bootstrap_expected_hashes']}; self.assertEqual(ledger,configured); literal=PLUGIN.read_text().split('EXPECTED: dict',1)[1].split(' = {',1)[1].split('\n}',1)[0]; actual=ast.literal_eval('{'+literal+'}'); expected={(x['apiVersion'],x['kind'],x['metadata'].get('namespace',''),x['metadata']['name']):hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest() for x in self.objects}; self.assertEqual(expected,actual)
if __name__=='__main__': unittest.main()
