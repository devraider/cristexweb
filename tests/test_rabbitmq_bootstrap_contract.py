from pathlib import Path
import unittest
import yaml
ROOT=Path(__file__).resolve().parents[1]
COMP=ROOT/'ansible/files/components/rabbitmq'
class RabbitMqBootstrapContractTests(unittest.TestCase):
 def test_exact_present_only_closure(self):
  objs=[]
  for p in sorted(COMP.rglob('*.yaml')):
   objs += [x for x in yaml.safe_load_all(p.read_text()) if isinstance(x,dict)]
  self.assertEqual(10,len(objs)); self.assertEqual(4,sum(x['kind']=='NetworkPolicy' for x in objs)); self.assertEqual(1,sum(x['kind']=='StatefulSet' for x in objs)); self.assertEqual(3,sum(x['kind']=='Service' for x in objs)); self.assertFalse(any(x['kind'] in {'Secret','PersistentVolumeClaim'} for x in objs))
 def test_digest_storage_and_private_ports(self):
  s=yaml.safe_load((COMP/'runtime/statefulset-rabbitmq.yaml').read_text()); c=s['spec']['template']['spec']['containers'][0]; self.assertIn('@sha256:',c['image']); self.assertEqual('20Gi',s['spec']['volumeClaimTemplates'][0]['spec']['resources']['requests']['storage']); self.assertEqual({5671,15671},{p['containerPort'] for p in c['ports']})
 def test_wrapper_guard_exists(self):
  for p in ('ansible/bin/bootstrap-rabbitmq','ansible/playbooks/bootstrap_rabbitmq.yml','ansible/roles/rabbitmq_bootstrap/tasks/main.yml','ansible/plugins/action/rabbitmq_guarded_k8s.py'): self.assertTrue((ROOT/p).is_file(),p)
if __name__=='__main__': unittest.main()
