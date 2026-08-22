from pathlib import Path
import hashlib, json, unittest, yaml
ROOT=Path(__file__).resolve().parents[1]
COMP=ROOT/'ansible/files/components/infisical-cristexhub-dev-runtime'
DEFAULTS=ROOT/'ansible/roles/infisical_cristexhub_dev_runtime_bootstrap/defaults/main.yml'
TASKS=ROOT/'ansible/roles/infisical_cristexhub_dev_runtime_bootstrap/tasks/main.yml'
PLUGIN=ROOT/'ansible/plugins/action/infisical_cristexhub_dev_runtime_guarded_k8s.py'
WRAPPER=ROOT/'ansible/bin/bootstrap-infisical-cristexhub-dev-runtime'
POLICY=ROOT/'ansible/files/policies/cristexhub-dev-runtime-materialization.yml'
COMPOSER=ROOT/'ansible/bin/materialize-infisical-cristexhub-dev-runtime'
class RuntimeSeamTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.paths=sorted(COMP.glob('admission/*.yaml'))+sorted(COMP.glob('rbac/*.yaml'))+sorted(COMP.glob('source/*.yaml'))
  cls.objects=[yaml.safe_load(p.read_text()) for p in cls.paths]
 def test_exact_13_object_value_free_closure(self):
  self.assertEqual(13,len(self.objects)); self.assertFalse(any(x['kind']=='Secret' for x in self.objects))
  self.assertEqual({'ValidatingAdmissionPolicy':4,'ValidatingAdmissionPolicyBinding':4,'Role':1,'RoleBinding':1,'InfisicalConnection':1,'InfisicalAuth':1,'InfisicalStaticSecret':1},{k:sum(x['kind']==k for x in self.objects) for k in {x['kind'] for x in self.objects}})
 def test_fixed_source_target_and_keys(self):
  s=next(x for x in self.objects if x['kind']=='InfisicalStaticSecret'); self.assertEqual('cristexhub-dev',s['metadata']['namespace']); self.assertEqual('/cristexhub/dev/runtime',s['spec']['sources'][0]['secretPath']); self.assertEqual('prod',s['spec']['sources'][0]['environmentSlug']); self.assertEqual('619656da-14f3-4872-857b-be103cdc5326',s['spec']['sources'][0]['projectId']); self.assertEqual({'MONGODB_URL','RABBITMQ_URL','REDIS_URL','REDIS_PASSWORD','FERNET_KEY','OIDC_CLIENT_SECRET','OAUTH2_PROXY_COOKIE_SECRET','PRIVATE_CA_BUNDLE','CODE_RUNNER_AUTH_TOKEN','BROWSERLESS_TOKEN'},set(s['spec']['targets'][0]['template']['data']))
  self.assertEqual('cristexhub-ghcr-pull', s['spec']['targets'][1]['name']); self.assertEqual('kubernetes.io/dockerconfigjson', s['spec']['targets'][1]['secretType']); self.assertEqual({'.dockerconfigjson'}, set(s['spec']['targets'][1]['template']['data']))
  self.assertEqual({'address': 'https://app.infisical.com'}, next(x for x in self.objects if x['kind']=='InfisicalConnection')['spec'])
  auth=next(x for x in self.objects if x['kind']=='InfisicalAuth'); self.assertEqual('universal',auth['spec']['method']); self.assertEqual('cristexhub-dev',auth['spec']['infisicalConnectionRef']['namespace'])
 def test_hardened_guards_are_present(self):
  t=TASKS.read_text(); self.assertIn('expected_hashes | length == 13',t); self.assertIn('prestate_count',t); self.assertIn("status.phase == 'Active'",t); self.assertIn("system:serviceaccount:shared-services:infisical-operator-controller",'\n'.join(p.read_text() for p in self.paths)); self.assertIn("template.data.exists(k, k == 'MONGODB_URL')",'\n'.join(p.read_text() for p in self.paths))
  self.assertIn("cristexhub_dev_runtime_credential.resources[0].type ==", t); self.assertIn('metadata.ownerReferences', t)
 def test_rolebinding_targets_actual_operator_service_account(self):
  binding=next(x for x in self.objects if x['kind']=='RoleBinding' and x['apiVersion'].startswith('rbac.authorization.k8s.io/'))
  self.assertEqual('Role', binding['roleRef']['kind'])
  self.assertEqual('infisical-cristexhub-dev-runtime-secret-writer', binding['roleRef']['name'])
  self.assertEqual([{'kind':'ServiceAccount','name':'infisical-operator-controller','namespace':'shared-services'}],binding['subjects'])
 def test_manifest_ledgers_and_action_hashes_are_current(self):
  ledger={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (COMP/'MANIFESTS.sha256').read_text().splitlines()}
  self.assertEqual({str(p.relative_to(COMP)) for p in self.paths},set(ledger))
  for p in self.paths: self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),ledger[str(p.relative_to(COMP))])
  defaults=yaml.safe_load(DEFAULTS.read_text()); configured={x['path'].split('/ansible/files/components/infisical-cristexhub-dev-runtime/',1)[1]:x['sha256'] for x in defaults['cristexhub_dev_runtime_bootstrap_expected_hashes']}; self.assertEqual(ledger,configured)
  literal=PLUGIN.read_text().split('_EXPECTED_OBJECT_HASHES: dict',1)[1].split(' = ',1)[1].split('\n_EXPECTED_IDENTITY_SET_SHA256',1)[0]
  actual=__import__('ast').literal_eval(literal); expected={(x['apiVersion'],x['kind'],x['metadata'].get('namespace',''),x['metadata']['name']):hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest() for x in self.objects}; self.assertEqual(expected,actual)
 def test_absent_credential_is_explicit_gate(self):
  t=TASKS.read_text(); self.assertIn('cristexhub-dev-infisical-universal-auth',t); self.assertIn('BLOCKED:',t); self.assertIn('No mutation was attempted',t)
 def test_guarded_entrypoint_and_no_values(self):
  self.assertIn('check|apply',WRAPPER.read_text()); self.assertNotIn('clientSecret:', '\n'.join(p.read_text() for p in self.paths)); self.assertIn('_EXPECTED_OBJECT_HASHES',PLUGIN.read_text())
 def test_composition_policy_binds_existing_contracts_and_tls(self):
  policy=yaml.safe_load(POLICY.read_text())
  self.assertEqual(policy['target_keys'], ['MONGODB_URL','RABBITMQ_URL','REDIS_URL','REDIS_PASSWORD','FERNET_KEY','OIDC_CLIENT_SECRET','OAUTH2_PROXY_COOKIE_SECRET','PRIVATE_CA_BUNDLE','CODE_RUNNER_AUTH_TOKEN','BROWSERLESS_TOKEN'])
  self.assertEqual(policy['sources']['mongodb']['path'], '/shared-services/mongodb')
  self.assertEqual(policy['sources']['rabbitmq']['path'], '/shared-services/rabbitmq')
  self.assertEqual(policy['sources']['keycloak']['path'], '/shared-services/keycloak')
  self.assertEqual(policy['sources']['mongodb']['tls_ca_file'], '/etc/cristexhub/tls/ca-bundle.pem')
  self.assertEqual(policy['sources']['rabbitmq']['tls_ca_file'], '/etc/cristexhub/tls/ca-bundle.pem')
  self.assertEqual(policy['authorization']['universal_auth_secret']['keys'], ['clientId','clientSecret'])
  self.assertTrue(policy['workflow']['atomic_remote_upload'])
  self.assertTrue(policy['authorization']['no_plaintext_output'])
 def test_composition_entrypoint_is_guarded_and_value_safe(self):
  t=COMPOSER.read_text()
  self.assertIn("[ \"$1\" = apply ]",t)
  self.assertIn('v3/secrets/raw/',t)
  self.assertIn('/shared-services/mongodb',t); self.assertIn('/shared-services/rabbitmq',t); self.assertIn('/shared-services/keycloak',t)
  self.assertIn('PRIVATE_CA_BUNDLE',t); self.assertIn('atomic',POLICY.read_text())
  self.assertIn('PRIVATE KEY',t); self.assertIn('UNKNOWN — STOP',t)
  self.assertNotIn('set +x',t)
if __name__=='__main__': unittest.main()
