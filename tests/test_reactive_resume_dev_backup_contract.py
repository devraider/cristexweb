from __future__ import annotations

import hashlib
import re
import stat
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "ansible/files/backup/reactive-resume-dev-backup"
RESTORE = ROOT / "ansible/files/backup/restore-reactive-resume-dev-backup-rehearsal"
SERVICE = ROOT / "ansible/files/backup/cristexweb-reactive-resume-dev-backup.service"
TIMER = ROOT / "ansible/files/backup/cristexweb-reactive-resume-dev-backup.timer"
NETWORK_POLICY = ROOT / "ansible/files/backup/reactive-resume-dev-backup-networkpolicy.yaml"
PLAYBOOK = ROOT / "ansible/playbooks/configure_reactive_resume_dev_backup.yml"
WRAPPER = ROOT / "ansible/bin/configure-reactive-resume-dev-backup"
RUNBOOK = ROOT / "runbooks/reactive-resume-dev-backup.md"


class ReactiveResumeDevBackupContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.backup = BACKUP.read_text()
        cls.restore = RESTORE.read_text()
        cls.service = SERVICE.read_text()
        cls.timer = TIMER.read_text()
        cls.playbook_text = PLAYBOOK.read_text()
        cls.playbook = yaml.safe_load(cls.playbook_text)[0]
        cls.wrapper = WRAPPER.read_text()
        cls.runbook = RUNBOOK.read_text()

    def test_scripts_are_shell_valid_executable_and_source_only(self) -> None:
        for path in (BACKUP, RESTORE, WRAPPER):
            subprocess.run(["sh", "-n", str(path)], check=True)
            self.assertEqual(0o755, stat.S_IMODE(path.stat().st_mode), path)
        for path in (SERVICE, TIMER, NETWORK_POLICY, PLAYBOOK, RUNBOOK):
            self.assertTrue(path.is_file(), path)
        combined = "\n".join((self.backup, self.restore, self.service, self.timer, NETWORK_POLICY.read_text(), self.playbook_text))
        self.assertNotIn("AGE-SECRET-KEY-", combined)
        self.assertNotRegex(combined, r"(?im)^\s*(?:password|clientsecret|token)\s*[:=]\s*[^$<\n]")

    def test_nonempty_object_and_timing_acceptance_contract(self) -> None:
        for value in (
            "object_storage_empty",
            '[ "$object_count" -gt 0 ] && [ "$total_object_bytes" -gt 0 ]',
            "backup_duration_seconds=",
            '"backup_duration_seconds": int(duration)',
            '"created_at_utc": run_id',
        ):
            self.assertIn(value, self.backup, value)
        for value in (
            "declared_rpo_seconds=86400",
            "declared_rto_seconds=14400",
            "backup_duration_seconds",
            "restore_duration_seconds",
            "rpo_seconds",
            "object_storage_empty",
            "restored_object_empty",
            "rpo_exceeded",
            "rto_exceeded",
            'run["created_at_utc"] == os.environ["RUN_ID"]',
            'run["object_storage"]["object_count"] > 0',
            'run["object_storage"]["total_object_bytes"] > 0',
            'run["database"]["bytes"] == pg["archive_bytes"]',
            'run["object_storage"]["bytes"] == obj["archive_bytes"]',
        ):
            self.assertIn(value, self.restore, value)
        self.assertIn(
            "backup_duration_seconds=[0-9]+ restore_duration_seconds=[0-9]+ rpo_seconds=[0-9]+",
            self.playbook_text,
        )
        self.assertIn("object_count=[1-9][0-9]* object_bytes=[1-9][0-9]*", self.playbook_text)

    def test_combined_run_id_and_exact_sources(self) -> None:
        for value in (
            "database=reactive_resume_dev_successor",
            "object_bucket=reactive-resume-dev",
            "archive_root=/var/lib/cristexweb-backup/reactive-resume/dev",
            "remote_root=drive:cristexweb-recovery/reactive-resume/dev",
            "run_id=$timestamp",
            "pod_run_id=",
            "run-manifest.json",
            "postgresql.manifest.json",
            "object-storage.manifest.json",
            "source_cluster",
        ):
            self.assertIn(value, self.backup, value)
        self.assertIn("run_id=$selected", self.restore)
        self.assertIn("pod_run_id=", self.restore)
        self.assertIn("run[\"run_id\"] == os.environ[\"RUN_ID\"]", self.restore)
        self.assertIn("reactive_resume_dev_successor", self.restore)
        self.assertIn("reactive-resume-dev", self.restore)

    def test_immutable_drive_readback_and_retention(self) -> None:
        for text in (self.backup, self.restore):
            self.assertIn("drive:cristexweb-recovery/reactive-resume/dev", text)
            self.assertIn("copyto --immutable", text) if text is self.backup else None
            self.assertNotRegex(text, r"rclone[^\n]*(?:sync|move|purge|delete)")
        for value in (
            "copyto --immutable",
            "cmp -s",
            "-mtime +14",
            "-mindepth 1 -maxdepth 1 -type d",
            "postgresql.dump.gz.age",
            "object-storage.tar.gz.age",
            "postgresql.dump.gz.age.sha256",
            "object-storage.tar.gz.age.sha256",
        ):
            self.assertIn(value, self.backup, value)
        self.assertIn("sha256sum -c", self.restore)

    def test_postgresql_is_logical_only_and_no_raw_pv_copy(self) -> None:
        for value in (
            "pg_dump",
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "reactive_resume_dev_successor",
            "shared-postgresql",
            "reactive-resume-dev.dump",
        ):
            self.assertIn(value, self.backup, value)
        combined = self.backup + "\n" + self.restore
        for forbidden in ("PersistentVolumeClaim", "rclone sync", "kubectl cp .*data", "shared-postgresql-reactive-resume"):
            self.assertNotIn(forbidden, combined, forbidden)
        self.assertIn("emptyDir", self.restore)
        for stage in (
            "remote_download",
            "postgresql_checksum",
            "object_checksum",
            "manifest_contract",
            "infisical_identity",
            "postgresql_decrypt",
            "object_decrypt",
            "object_archive_list",
            "object_archive_paths",
        ):
            self.assertIn(f"fail {stage}", self.restore)
        self.assertIn('obj["service"] == "seaweedfs"', self.restore)
        self.assertIn("listen_addresses=", self.restore)
        self.assertIn("pg_restore --exit-on-error --no-owner --no-privileges", self.restore)

    def test_object_storage_is_s3_tls_authenticated_and_prefix_bound(self) -> None:
        for value in (
            "reactive-resume-object-storage",
            "reactive-resume-object-storage-tls",
            "reactive-resume-object-storage-auth",
            "RCLONE_CONFIG_S3_ENDPOINT",
            "RCLONE_CA_CERT",
            "tls_contract=",
            "auth_contract=",
            "https://$object_service.$namespace.svc.cluster.local:8333",
            "uploads/user-pictures/",
            "pictures/",
            "uploads/user-agent/",
            "object-storage.tar.gz.age",
            "raw-manifest.json.tmp",
            "mv /work/raw-manifest.json.tmp /work/raw-manifest.json",
            "touch /work/export.ready",
            "test -f /work/export.ready && test -s /work/raw-manifest.json",
            'wait --for=condition=Ready "pod/$helper_pod" --timeout=1800s',
            "failureThreshold: 900",
        ):
            self.assertIn(value, self.backup, value)
        for value in (
            "rclone check --one-way --size-only",
            "reactive-resume-object-storage-tls",
            "reactive-resume-object-storage-auth",
            "target=isolated-emptydir-postgresql-and-seaweedfs",
            "seaweed_image",
            "emptyDir",
        ):
            self.assertIn(value, self.restore, value)
        self.assertNotIn("/data" + " ", self.backup)
        self.assertNotIn("PersistentVolume", self.restore)
        policy = yaml.safe_load(NETWORK_POLICY.read_text())
        self.assertEqual("reactive-resume-object-storage-allow-backup", policy["metadata"]["name"])
        self.assertEqual("shared-services", policy["metadata"]["namespace"])
        self.assertEqual(
            {
                "app.kubernetes.io/name": "reactive-resume-dev-backup",
                "cristex.io/object-storage-client": "backup",
            },
            policy["spec"]["ingress"][0]["from"][0]["podSelector"]["matchLabels"],
        )
        self.assertEqual([{"protocol": "TCP", "port": 8333}], policy["spec"]["ingress"][0]["ports"])
        self.assertIn("reactive-resume-dev-backup-networkpolicy.yaml", self.playbook_text)

    def test_uid_bound_helper_cleanup_and_no_service_account(self) -> None:
        for text in (self.backup, self.restore):
            self.assertIn("automountServiceAccountToken: false", text)
            self.assertIn("cristex.io/run-id", text)
            self.assertIn('propagationPolicy":"Orphan"', text)
            self.assertIn('preconditions":{"uid":"%s"}', text)
            self.assertIn("current_uid", text)
            self.assertIn("wait --for=delete", text)
        self.assertIn('rm -rf -- "$run_directory" "$work"', self.backup)
        self.assertIn("helper_uid=", self.backup)
        self.assertIn("pg_uid=", self.restore)
        self.assertIn("storage_uid=", self.restore)

    def test_age_custody_and_plaintext_cleanup(self) -> None:
        combined = self.backup + "\n" + self.restore
        for value in (
            "/etc/cristexweb-backup/age.recipient",
            "ce615905ec27fa6e085578d96e48dc798677b3f2ade5c417770f22e78248ad28",
            "age -r",
            "SHARED_DATABASE_BACKUP_AGE_IDENTITY",
            "infisical_path=/shared-services/backup-recovery",
            "trap cleanup_plaintext EXIT HUP INT TERM",
            "private_residue=none",
        ):
            self.assertIn(value, combined, value)
        self.assertNotIn("SHARED_DATABASE_BACKUP_AGE_IDENTITY=", combined)
        self.assertNotIn("--password=", combined)

    def test_weekly_systemd_unit_is_hardened_and_persistent(self) -> None:
        for value in (
            "User=paul",
            "Group=paul",
            "SupplementaryGroups=k3s-admin",
            "NoNewPrivileges=true",
            "ProtectSystem=strict",
            "ProtectHome=read-only",
            "PrivateTmp=true",
            "ReadWritePaths=/var/lib/cristexweb-backup /run/lock /home/paul/.config/rclone",
            "TimeoutStartSec=60min",
        ):
            self.assertIn(value, self.service, value)
        for value in (
            "OnCalendar=Sun *-*-* 04:15:00",
            "RandomizedDelaySec=30m",
            "Persistent=true",
            "AccuracySec=1m",
            "WantedBy=timers.target",
            "Unit=cristexweb-reactive-resume-dev-backup.service",
        ):
            self.assertIn(value, self.timer, value)

    def test_playbook_gates_timer_until_restore_and_supports_idempotence(self) -> None:
        for value in (
            "reactive_resume_dev_backup_approved",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT",
            "reactive_resume_dev_backup_mode in ['install', 'test', 'restore', 'enable']",
            "Keep the weekly timer disabled until restore acceptance",
            "Execute the separately approved one-time combined backup test",
            "Execute the separately approved isolated combined restore rehearsal",
            "Enable the accepted weekly timer",
            "reactive_resume_dev_backup_mode == 'enable'",
            "not ansible_check_mode",
            "failed_when: false",
            "Extract only the allowlisted restore failure stage",
            "restore_status=failed stage=([a-z0-9_-]+)",
            "reactive_resume_dev_backup_repository_root == '/home/paul/projects/cristexweb'",
        ):
            self.assertIn(value, self.playbook_text, value)
        self.assertEqual("crtxweb", self.playbook["hosts"])
        self.assertTrue(self.playbook["become"])
        self.assertIn("serial", self.playbook)

    def test_wrapper_is_fixed_non_passthrough_and_restore_scoped(self) -> None:
        for value in (
            "check|apply|test|restore|enable-check|enable-apply",
            "if [ \"$#\" -ne 1 ]",
            "refusing passthrough arguments or task selection",
            "--ask-become-pass",
            "--limit crtxweb",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT=v1",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_RESTORE_TOKEN",
            "/home/paul/projects/cristexweb",
            "/usr/bin/env -i",
        ):
            self.assertIn(value, self.wrapper, value)
        self.assertNotIn('exec "$@"', self.wrapper)

    def test_runbook_records_not_run_scope_and_recovery_contract(self) -> None:
        normalized = " ".join(self.runbook.split())
        for value in (
            "SOURCE-ONLY DESIGN / NOT RUN / RUNTIME UNINSTALLED",
            "reactive_resume_dev_successor",
            "reactive-resume-dev",
            "one UTC `YYYYmmddTHHMMSSZ` run ID",
            "OnCalendar=Sun *-*-* 04:15:00",
            "14 days",
            "rclone copyto --immutable",
            "emptyDir",
            "no raw volume copy",
            "isolated PostgreSQL",
            "isolated SeaweedFS",
            "private_residue=none",
            "PROD has no source",
            "backup_duration_seconds",
            "restore_duration_seconds",
            "rpo_seconds",
            "non-empty backup",
            "RPO `86400` seconds (24 hours)",
            "RTO `14400` seconds (4 hours)",
            "Exact approved acceptance run sequence",
            "journalctl -u cristexweb-reactive-resume-dev-backup.service",
            "--ask-become-pass",
            "controlling terminal",
            "do not pipe or redirect",
        ):
            self.assertIn(value, normalized, value)
        self.assertNotIn("runtime was applied", self.runbook.lower())


if __name__ == "__main__":
    unittest.main()
