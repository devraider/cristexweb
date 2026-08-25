from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "ansible/files/backup/mongodb-shared-backup"
RESTORE = ROOT / "ansible/files/backup/restore-mongodb-shared-rehearsal"
SERVICE = ROOT / "ansible/files/backup/cristexweb-mongodb-shared-backup.service"
TIMER = ROOT / "ansible/files/backup/cristexweb-mongodb-shared-backup.timer"
PLAYBOOK = ROOT / "ansible/playbooks/configure_mongodb_shared_backup.yml"
WRAPPER = ROOT / "ansible/bin/configure-mongodb-shared-backup"


class MongoDBSharedBackupContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.backup = BACKUP.read_text()
        cls.restore = RESTORE.read_text()
        cls.service = SERVICE.read_text()
        cls.timer = TIMER.read_text()
        cls.playbook = PLAYBOOK.read_text()
        cls.wrapper = WRAPPER.read_text()
        yaml.safe_load(cls.playbook)

    def test_backup_is_exact_authenticated_tls_oplog_archive(self) -> None:
        for value in (
            "resource=shared-mongodb",
            "pod=shared-mongodb-0",
            "shared-mongodb-auth",
            "mongodb_admin",
            "replicaSet=shared-mongodb",
            "tls=true",
            "--config=/dev/stdin --archive --oplog --quiet",
            "consistency=oplog",
        ):
            self.assertIn(value, self.backup)
        self.assertNotIn("--password=", self.backup)
        self.assertNotIn("AGE-SECRET-KEY-", self.backup)

    def test_encryption_copy_readback_and_cleanup_are_fail_closed(self) -> None:
        for value in (
            "drive:cristexweb-recovery/mongodb/shared-mongodb",
            "/usr/bin/age -r",
            "copyto --immutable",
            "/usr/bin/cmp -s",
            "trap cleanup EXIT HUP INT TERM",
            "-mtime +14",
            "readback=verified",
            "gzip -9 -c \"$run_directory/shared-mongodb.archive\" >\"$run_directory/shared-mongodb.archive.gz\"",
            "source_closure_sha256=",
        ):
            self.assertIn(value, self.backup)
        for forbidden in ("rclone sync", "rclone move", "rclone purge", "rclone delete"):
            self.assertNotIn(forbidden, self.backup)

    def test_restore_is_digest_pinned_emptydir_and_uid_cleaned(self) -> None:
        for value in (
            "8.0.12-ubi8@sha256:5500852ab0693ac56134cecf5ad45d3b81d25e4681f4f960a834e48cd34fe71b",
            "SHARED_DATABASE_BACKUP_AGE_IDENTITY",
            "--env prod",
            "mongodb-restore-rehearsal",
            "automountServiceAccountToken: false",
            "emptyDir: {}",
            "chown 2000:2000 /data/db",
            'add: ["CHOWN", "FOWNER"]',
            "mongorestore --archive=/restore/shared-mongodb.archive --oplogReplay --stopOnError --quiet",
            '"preconditions":{"uid":"%s"}',
            '"propagationPolicy":"Orphan"',
            "current_owner",
            "current_run_id",
            "x['archive_sha256']==os.environ['EXPECTED_SHA']",
            "x['archive_bytes']==int(os.environ['ARCHIVE_BYTES'])",
            "private_residue=none",
        ):
            self.assertIn(value, self.restore)
        self.assertNotIn("PersistentVolumeClaim", self.restore)
        self.assertNotIn("shared-mongodb-auth", self.restore)

    def test_systemd_is_separate_hardened_and_offset(self) -> None:
        for value in (
            "User=paul",
            "SupplementaryGroups=k3s-admin",
            "NoNewPrivileges=true",
            "ProtectSystem=strict",
            "CapabilityBoundingSet=",
            "ReadWritePaths=/var/lib/cristexweb-backup /run/lock /home/paul/.config/rclone",
        ):
            self.assertIn(value, self.service)
        self.assertIn("OnCalendar=*-*-* 03:45:00", self.timer)
        self.assertIn("RandomizedDelaySec=15m", self.timer)
        self.assertIn("Persistent=true", self.timer)
        self.assertNotIn("postgresql-keycloak", self.service + self.timer)
        self.assertIn("/var/lib/cristexweb-backup/mongodb", self.playbook)
        self.assertIn("/var/lib/cristexweb-backup/mongodb/shared-mongodb", self.playbook)
        self.assertNotIn("/var/lib/cristexweb-backup/postgresql/keycloak", self.playbook)
        self.assertIn("/usr/bin/timeout", self.playbook)
        self.assertIn("Roll back timer after failed post-enable validation", self.playbook)

    def test_ansible_modes_keep_timer_gated_and_check_mode_safe(self) -> None:
        for value in (
            "mongodb_shared_backup_mode in ['install', 'test', 'restore', 'enable']",
            "Keep the timer disabled until restore acceptance",
            "mongodb_shared_backup_mode in ['install', 'test', 'restore']",
            "not ansible_check_mode",
            "mongodb_shared_backup_mode == 'enable'",
            "check_mode: false",
            "no_log: true",
            "application_database_count=[0-9]+",
            "mongodb_shared_backup_timer_active.stdout == 'active'",
            "mongodb_shared_backup_timer_enabled.stdout == 'enabled'",
        ):
            self.assertIn(value, self.playbook)

    def test_wrapper_is_non_passthrough_and_exact(self) -> None:
        self.assertIn("check|apply|test|restore|enable-check|enable-apply", self.wrapper)
        self.assertIn("--ask-become-pass", self.wrapper)
        self.assertIn("--limit crtxweb", self.wrapper)
        self.assertIn("CRISTEXWEB_MONGODB_SHARED_BACKUP_ENTRYPOINT=v1", self.wrapper)
        self.assertIn('if [ "$#" -ne 1 ]', self.wrapper)

    def test_no_secret_values_in_source(self) -> None:
        combined = "\n".join((self.backup, self.restore, self.service, self.timer, self.playbook))
        self.assertNotIn("AGE-SECRET-KEY-", combined)
        self.assertNotIn("SHARED_DATABASE_BACKUP_AGE_IDENTITY=", combined)
        self.assertNotIn("MONGODB_ADMIN_PASSWORD", combined)
        self.assertNotIn("shared-database-backup.agekey", combined)


if __name__ == "__main__":
    unittest.main()
