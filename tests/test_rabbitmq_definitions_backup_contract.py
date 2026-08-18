from pathlib import Path
import unittest
import yaml
ROOT=Path(__file__).resolve().parents[1]
class RabbitMqDefinitionsBackupContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.backup=(ROOT/'ansible/files/backup/rabbitmq-shared-definitions-backup').read_text(); cls.restore=(ROOT/'ansible/files/backup/restore-rabbitmq-definitions-rehearsal').read_text(); cls.service=(ROOT/'ansible/files/backup/cristexweb-rabbitmq-definitions-backup.service').read_text(); cls.timer=(ROOT/'ansible/files/backup/cristexweb-rabbitmq-definitions-backup.timer').read_text(); cls.play=(ROOT/'ansible/playbooks/configure_rabbitmq_definitions_backup.yml').read_text(); cls.wrapper=(ROOT/'ansible/bin/configure-rabbitmq-definitions-backup').read_text(); yaml.safe_load(cls.play)
 def test_archive_contract(self):
  for x in ('shared-rabbitmq-management','shared-rabbitmq-admin','shared-rabbitmq-tls','rabbitmq-definitions','drive:cristexweb-recovery/rabbitmq/definitions','copyto --immutable','/usr/bin/age -r','/usr/bin/cmp -s','consistency":"definitions-and-policies','readback=verified'): self.assertIn(x,self.backup)
  for x in ('rclone sync','rclone delete','AGE-SECRET-KEY-','password='): self.assertNotIn(x,self.backup)
 def test_restore_isolated_and_pinned(self):
  for x in ('4.3.4-management@sha256:cd4fd60136781671d125ed68ac4b67900c0726b55e2e8b98719daa616a63240b','SHARED_DATABASE_BACKUP_AGE_IDENTITY','emptyDir: {}','rabbitmqctl import_definitions','automountServiceAccountToken: false','"propagationPolicy":"Orphan"','"preconditions":{"uid":"%s"}','message_recovery=not_claimed'): self.assertIn(x,self.restore)
  self.assertNotIn('PersistentVolumeClaim',self.restore)
 def test_timer_and_hardening(self):
  for x in ('User=paul','SupplementaryGroups=k3s-admin','ProtectSystem=strict','PrivateTmp=true','CapabilityBoundingSet='): self.assertIn(x,self.service)
  for x in ('OnCalendar=*-*-* 04:15:00','RandomizedDelaySec=15m','Persistent=true'): self.assertIn(x,self.timer)
 def test_wrapper_and_modes(self):
  self.assertIn('check|apply|test|restore|enable-check|enable-apply',self.wrapper); self.assertIn('--ask-become-pass',self.wrapper); self.assertIn('CRISTEXWEB_RABBITMQ_DEFINITIONS_BACKUP_ENTRYPOINT=v1',self.wrapper)
  for x in ("rabbitmq_definitions_backup_mode in ['install', 'test', 'restore', 'enable']",'not ansible_check_mode','Keep timer disabled'): self.assertIn(x,self.play)
if __name__=='__main__': unittest.main()
