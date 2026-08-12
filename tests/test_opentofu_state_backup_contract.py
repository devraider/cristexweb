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
        ):
            self.assertIn(value, self.play)
        self.assertIn("check|apply|test|restore|enable-check|enable-apply", self.wrapper)
        self.assertIn("CRISTEXWEB_OPENTOFU_STATE_BACKUP_ENTRYPOINT=v1", self.wrapper)


if __name__ == "__main__":
    unittest.main()
