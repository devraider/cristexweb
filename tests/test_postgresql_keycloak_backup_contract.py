from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ansible/files/backup/postgresql-keycloak-backup"
SERVICE = ROOT / "ansible/files/backup/cristexweb-postgresql-keycloak-backup.service"
TIMER = ROOT / "ansible/files/backup/cristexweb-postgresql-keycloak-backup.timer"
RESTORE = ROOT / "ansible/files/backup/restore-postgresql-keycloak-rehearsal"
PLAYBOOK = ROOT / "ansible/playbooks/configure_postgresql_keycloak_backup.yml"
WRAPPER = ROOT / "ansible/bin/configure-postgresql-keycloak-backup"


class PostgreSQLKeycloakBackupContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = SCRIPT.read_text()
        self.service = SERVICE.read_text()
        self.timer = TIMER.read_text()
        self.restore = RESTORE.read_text()
        self.playbook = yaml.safe_load(PLAYBOOK.read_text())[0]
        self.wrapper = WRAPPER.read_text()

    def test_exact_database_encryption_and_immutable_remote(self) -> None:
        for value in (
            "namespace=shared-services",
            "cluster=shared-postgresql",
            "database=keycloak",
            "remote_root=drive:cristexweb-recovery/postgresql/keycloak",
            "--format=custom",
            "/usr/bin/age -r",
            "copyto --immutable",
            "readback=verified",
            "gzip -9 -c \"$run_directory/keycloak.dump\" >\"$run_directory/keycloak.dump.gz\"",
            "source_closure_sha256=",
        ):
            self.assertIn(value, self.script)
        self.assertNotRegex(self.script, r"rclone[^\n]*(sync|move|purge|delete)")
        self.assertNotIn("AGE-SECRET-KEY-", self.script)
        self.assertNotIn("password", self.script.lower())

    def test_plaintext_cleanup_and_exact_local_retention(self) -> None:
        self.assertIn("trap cleanup_plaintext EXIT HUP INT TERM", self.script)
        self.assertIn("/usr/bin/rm -f -- \"$run_directory/keycloak.dump\"", self.script)
        self.assertIn("-mtime +14", self.script)
        self.assertIn("-mindepth 1 -maxdepth 1 -type d", self.script)
        self.assertIn("-name '20[0-9]", self.script)

    def test_service_runs_unprivileged_and_is_hardened(self) -> None:
        for value in (
            "User=paul",
            "Group=paul",
            "SupplementaryGroups=k3s-admin",
            "NoNewPrivileges=true",
            "ProtectSystem=strict",
            "ProtectHome=read-only",
            "ReadWritePaths=/var/lib/cristexweb-backup /run/lock",
            "TimeoutStartSec=30min",
        ):
            self.assertIn(value, self.service)

    def test_timer_is_daily_persistent_and_bounded(self) -> None:
        self.assertIn("OnCalendar=*-*-* 03:15:00", self.timer)
        self.assertIn("RandomizedDelaySec=15m", self.timer)
        self.assertIn("Persistent=true", self.timer)
        self.assertIn("WantedBy=timers.target", self.timer)

    def test_timer_enablement_follows_test_and_restore_gate(self) -> None:
        text = PLAYBOOK.read_text()
        self.assertIn("Keep the timer disabled until restore acceptance", text)
        self.assertIn("postgresql_keycloak_backup_mode in ['install', 'test', 'restore']", text)
        self.assertIn("Enable the accepted daily timer", text)
        self.assertIn("postgresql_keycloak_backup_mode == 'enable'", text)
        self.assertIn(
            "ansible_check_mode or postgresql_keycloak_backup_mode != 'enable'",
            text,
        )
        self.assertIn("Inspect final timer active state", text)
        self.assertIn("Inspect final timer enabled state", text)
        self.assertIn("postgresql_keycloak_backup_timer_active.stdout == 'active'", text)
        self.assertIn("postgresql_keycloak_backup_timer_enabled.stdout == 'enabled'", text)
        self.assertIn("not ansible_check_mode", text)
        self.assertIn("/usr/bin/timeout", text)
        self.assertIn("Roll back timer after failed post-enable validation", text)
        self.assertRegex(
            text,
            r"Verify the sole configured rclone remote[\s\S]*?check_mode: false[\s\S]*?no_log: true",
        )

    def test_restore_is_exact_isolated_and_uid_cleaned(self) -> None:
        for value in (
            "drive:cristexweb-recovery/postgresql/keycloak",
            "SHARED_DATABASE_BACKUP_AGE_IDENTITY",
            "--env prod",
            "listen_addresses=",
            "emptyDir: {}",
            "automountServiceAccountToken: false",
            "initContainers:",
            'add: ["CHOWN", "FOWNER"]',
            "chown 999:999 /var/lib/postgresql/data",
            "pg_restore --exit-on-error --no-owner --no-privileges",
            '"preconditions":{"uid":"%s"}',
            "propagationPolicy",
            "private_residue=none",
            "K3S_CONFIG_FILE=/dev/null",
            "/usr/bin/tr '[:upper:]' '[:lower:]'",
        ):
            self.assertIn(value, self.restore)
        self.assertNotIn("shared-postgresql-keycloak", self.restore)
        self.assertNotIn("PersistentVolumeClaim", self.restore)
        self.assertNotIn("AGE-SECRET-KEY-", self.restore)

    def test_wrapper_is_non_passthrough_and_requires_sudo(self) -> None:
        self.assertIn("check|apply|test|restore|enable-check|enable-apply", self.wrapper)
        self.assertIn("--ask-become-pass", self.wrapper)
        self.assertIn("--limit crtxweb", self.wrapper)
        self.assertIn("CRISTEXWEB_POSTGRESQL_KEYCLOAK_BACKUP_ENTRYPOINT=v1", self.wrapper)
        self.assertIn('if [ "$#" -ne 1 ]', self.wrapper)
        self.assertIn("refusing passthrough arguments or task selection", self.wrapper)

    def test_no_secret_values_or_unsafe_environment_in_source(self) -> None:
        combined = "\n".join((self.script, self.restore, self.service, self.timer, PLAYBOOK.read_text()))
        self.assertNotRegex(combined, r"(?i)(password|clientsecret|token)\s*[:=]\s*(?!false\b)[^\s{]" )
        self.assertNotIn("shared-database-backup.agekey", combined)
        self.assertNotIn("SHARED_DATABASE_BACKUP_AGE_IDENTITY=", combined)


if __name__ == "__main__":
    unittest.main()
