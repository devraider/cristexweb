from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class OpenTofuStateBackupContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backup = (ROOT / "ansible/files/backup/opentofu-state-backup").read_text()
        cls.restore = (ROOT / "ansible/files/backup/restore-opentofu-state-rehearsal").read_text()
        cls.service = (ROOT / "ansible/files/backup/cristexweb-opentofu-state-backup.service").read_text()
        cls.timer = (ROOT / "ansible/files/backup/cristexweb-opentofu-state-backup.timer").read_text()
        cls.play = (ROOT / "ansible/playbooks/configure_opentofu_state_backup.yml").read_text()
        cls.wrapper = (ROOT / "ansible/bin/configure-opentofu-state-backup").read_text()
        yaml.safe_load(cls.play)

    def test_manifest_source_closure_is_expanded_and_schema_bound(self):
        self.assertIn('"source_closure_sha256":"%s"', self.backup)
        self.assertNotIn('"source_closure_sha256":"$source_closure_sha256"', self.backup)
        self.assertIn('"run_id":"%s"', self.backup)
        self.assertIn('"address_scope":"%s"', self.backup)
        for required in (
            "object_pairs_hook=reject_duplicate_keys",
            "'run_id', 'created_at_utc'",
            "'address_scope', 'source_closure_sha256'",
            "x['run_id'] == os.environ['TIMESTAMP']",
            "manifest_scope == label",
        ):
            self.assertIn(required, self.restore)
        self.assertIn("x['source_closure_sha256'] == os.environ['EXPECTED_SOURCE_CLOSURE_SHA256']", self.restore)
        self.assertIn("len(actual) == len(set(actual))", self.restore)
        self.assertIn("state address closure mismatch", self.restore)

    def test_encrypted_immutable_readback_contract(self):
        for text in (
            self.backup,
            self.restore,
        ):
            self.assertIn("foundation.tfstate", text)
            self.assertIn("drive:cristexweb-recovery/opentofu/foundation", text)
            self.assertIn("SHARED_DATABASE_BACKUP_AGE_IDENTITY", text) if text is self.restore else None
        for value in (
            "state_file=/var/lib/opentofu/cristexweb/foundation.tfstate",
            "copyto --immutable",
            "/usr/bin/age -r",
            "foundation.tfstate.age.sha256",
            "/usr/bin/cmp -s",
            'state_path":"/var/lib/opentofu/cristexweb/foundation.tfstate',
            'source_closure_sha256":"%s"',
            "source_closure_sha256=c9a04e04303b30148f410dd57c8c5c8cf69d0cbf58b88cbc70023c824e214fae",
            "private_residue=none",
        ):
            self.assertIn(value, self.backup)
        for value in ("rclone sync", "rclone delete", "AGE-SECRET-KEY-", "password="):
            self.assertNotIn(value, self.backup)

    def test_restore_isolated_and_non_mutating(self):
        for value in (
            "SHARED_DATABASE_BACKUP_AGE_IDENTITY",
            "age -d -i",
            "tofu state list",
            "target=isolated-tmpfs",
            "non_mutating=true",
            "address_scope=exact-five",
            "address_scope=exact-six",
            "schema=1 run_id=",
            "source_run_id=",
            "source_closure_sha256=",
            "non_mutating=true",
            "restore_status=success schema=1 run_id=%s source_run_id=%s",
            "checksum=verified",
            "address_scope=%s source_closure_sha256=%s",
        ):
            self.assertIn(value, self.restore)
        self.assertNotIn("tofu apply", self.restore)
        self.assertNotIn("state push", self.restore)

    def test_timer_disabled_until_acceptance(self):
        for value in ("User=paul", "ProtectSystem=strict", "PrivateTmp=true", "CapabilityBoundingSet="):
            self.assertIn(value, self.service)
        for value in ("OnCalendar=*-*-* 02:45:00", "RandomizedDelaySec=15m", "Persistent=true"):
            self.assertIn(value, self.timer)
        for value in (
            "opentofu_state_backup_mode in ['install', 'test', 'restore', 'enable']",
            "Keep timer disabled until restore acceptance",
            "opentofu_state_backup_mode == 'restore'",
            "opentofu_state_backup_mode == 'enable'",
            "fresh matching backup and restore acceptance evidence",
            "exact full current-source-bound acceptance schema",
            "opentofu_state_backup_restore_receipt_pattern",
            "checksum=verified",
            "readback=verified",
            "opentofu_state_backup_acceptance_restore_source_run_id",
            "opentofu_state_backup_acceptance_restore_source_timestamp",
            "opentofu_state_backup_acceptance_restore_scope",
            "opentofu_state_backup_acceptance_restore_run_id != opentofu_state_backup_acceptance_backup_run_id",
            "/usr/bin/timeout",
            "Roll back timer after failed post-enable validation",
        ):
            self.assertIn(value, self.play)
        self.assertIn("check|apply|test|restore|enable-check|enable-apply", self.wrapper)
        self.assertIn("CRISTEXWEB_OPENTOFU_STATE_BACKUP_ENTRYPOINT=v1", self.wrapper)


if __name__ == "__main__":
    unittest.main()
