from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
BACKUP = ANSIBLE / "files/backup/opentofu-github-state-backup"
RESTORE = ANSIBLE / "files/backup/restore-opentofu-github-state-rehearsal"
SERVICE = ANSIBLE / "files/backup/cristexweb-opentofu-github-state-backup.service"
TIMER = ANSIBLE / "files/backup/cristexweb-opentofu-github-state-backup.timer"
WRAPPER = ANSIBLE / "bin/configure-opentofu-github-state-backup"
PLAYBOOK = ANSIBLE / "playbooks/configure_opentofu_github_state_backup.yml"
RUNBOOK = ROOT / "runbooks/opentofu-github-state-backup.md"


class OpenTofuGithubStateBackupContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backup = BACKUP.read_text()
        cls.restore = RESTORE.read_text()
        cls.service = SERVICE.read_text()
        cls.timer = TIMER.read_text()
        cls.wrapper = WRAPPER.read_text()
        cls.playbook = PLAYBOOK.read_text()
        cls.runbook = RUNBOOK.read_text()
        yaml.safe_load(cls.playbook)

    def test_source_closure_is_separate_from_foundation_lane(self):
        self.assertTrue(BACKUP.is_file())
        self.assertTrue(RESTORE.is_file())
        self.assertTrue(SERVICE.is_file())
        self.assertTrue(TIMER.is_file())
        self.assertTrue(WRAPPER.is_file())
        self.assertTrue(PLAYBOOK.is_file())
        for text in (
            self.backup,
            self.restore,
            self.service,
            self.timer,
            self.wrapper,
            self.playbook,
        ):
            self.assertNotIn("foundation.tfstate", text)
            self.assertNotIn("opentofu-state-backup", text)
            self.assertNotIn("restore-opentofu-state-rehearsal", text)
            self.assertNotIn("cristexweb-opentofu-state-backup", text)
        self.assertIn("github.tfstate", self.backup)
        self.assertIn("github.tfstate", self.restore)
        self.assertIn("cristexweb-opentofu-github-state-backup", self.service)
        self.assertIn("cristexweb-opentofu-github-state-backup", self.timer)
        self.assertIn("configure_opentofu_github_state_backup.yml", self.wrapper)

    def test_backup_encrypts_immutable_three_leaf_archive_and_reads_back(self):
        for value in (
            "state_file=/var/lib/opentofu/cristexweb/github.tfstate",
            "archive_root=/var/lib/cristexweb-backup/opentofu/github",
            "remote_root=drive:cristexweb-recovery/opentofu/github",
            "lock_file=/run/lock/cristexweb-opentofu-github-state-backup.lock",
            "/usr/bin/age -r",
            "TOFU_DISABLE_CHECKPOINT=1 /usr/local/bin/tofu state list",
            "github.tfstate.age.sha256",
            "copyto --immutable",
            "/usr/bin/cmp -s",
            'state_path":"/var/lib/opentofu/cristexweb/github.tfstate',
            '"service":"opentofu-github"',
            "backup_status=success service=opentofu-github",
        ):
            self.assertIn(value, self.backup)
        for forbidden in (
            "rclone sync",
            "rclone delete",
            "AGE-SECRET-KEY-",
            "password=",
            "foundation",
        ):
            self.assertNotIn(forbidden, self.backup)
        self.assertEqual(1, self.backup.count("copyto --immutable"))
        self.assertEqual(2, self.backup.count("for leaf in github.tfstate.age"))

    def test_restore_is_checksum_checked_isolated_and_non_mutating(self):
        for value in (
            "remote_root=drive:cristexweb-recovery/opentofu/github",
            "/dev/shm/cristexweb-opentofu-github-restore.XXXXXX",
            "SHARED_DATABASE_BACKUP_AGE_IDENTITY",
            "age -d -i",
            "github.tfstate.age.sha256",
            "tofu state list",
            "TOFU_DISABLE_CHECKPOINT=1",
            "target=isolated-tmpfs",
            "non_mutating=true",
            "x['service']=='opentofu-github'",
            "/usr/bin/rm -f -- \"$work/identity\"",
        ):
            self.assertIn(value, self.restore)
        for forbidden in (
            "tofu apply",
            "state push",
            "tofu import",
            "rclone delete",
            "foundation",
        ):
            self.assertNotIn(forbidden, self.restore)

    def test_systemd_units_have_unique_hardened_scope(self):
        for value in (
            "User=paul",
            "Group=paul",
            "ProtectSystem=strict",
            "PrivateTmp=true",
            "PrivateDevices=true",
            "CapabilityBoundingSet=",
            "SyslogIdentifier=cristexweb-opentofu-github-state-backup",
            "BACKUP_SERVICE=opentofu-github",
            "ReadWritePaths=/var/lib/cristexweb-backup/opentofu/github",
        ):
            self.assertIn(value, self.service)
        self.assertNotIn("ReadWritePaths=/var/lib/cristexweb-backup /", self.service)
        for value in (
            "OnCalendar=*-*-* 03:15:00",
            "RandomizedDelaySec=15m",
            "Persistent=true",
            "Unit=cristexweb-opentofu-github-state-backup.service",
        ):
            self.assertIn(value, self.timer)
        self.assertNotIn("02:45:00", self.timer)

    def test_playbook_has_fixed_target_and_no_foundation_timer_path(self):
        for value in (
            "opentofu_github_state_backup_approved: false",
            "opentofu_github_state_backup_mode: install",
            "CRISTEXWEB_OPENTOFU_GITHUB_STATE_BACKUP_ENTRYPOINT",
            "/var/lib/opentofu/cristexweb/github.tfstate",
            "/var/lib/cristexweb-backup/opentofu/github",
            "cristexweb-opentofu-github-state-backup.timer",
            "restore-opentofu-github-state-rehearsal",
            "opentofu_github_state_restore_result",
            "opentofu_github_state_backup_mode in ['install', 'test', 'restore', 'enable']",
        ):
            self.assertIn(value, self.playbook)
        for forbidden in (
            "opentofu_github_state_backup_repository_root",
            "foundation.tfstate",
            "cristexweb-opentofu-state-backup",
            "name: cristexweb-opentofu-state-backup.timer",
        ):
            self.assertNotIn(forbidden, self.playbook)
        self.assertEqual(2, self.playbook.count("cristexweb-opentofu-github-state-backup.service"))
        self.assertEqual(3, self.playbook.count("cristexweb-opentofu-github-state-backup.timer"))

    def test_wrapper_is_non_passthrough_and_mode_bounded(self):
        for value in (
            "check|apply|test|restore|enable-check|enable-apply",
            "root=$(CDPATH= cd -- \"$dir/../..\" && pwd -P)",
            "[ \"$root\" = /home/paul/projects/cristexweb ]",
            "controller=\"$root/.venv/bin/ansible-playbook\"",
            "-i .ansible/inventory.local.yml",
            "--limit crtxweb",
            "--ask-become-pass",
            "--extra-vars",
            "CRISTEXWEB_OPENTOFU_GITHUB_STATE_BACKUP_ENTRYPOINT=v1",
        ):
            self.assertIn(value, self.wrapper)
        self.assertNotIn("foundation", self.wrapper)
        self.assertNotIn("--start-at-task", self.wrapper)
        self.assertNotIn("--step", self.wrapper)
        self.assertIn('exec /usr/bin/env -i HOME=/home/paul USER=paul', self.wrapper)
        self.assertNotIn('exec "$@"', self.wrapper)

    def test_runbook_records_source_only_fixed_boundary(self):
        normalized = " ".join(self.runbook.split())
        for value in (
            "source-only",
            "/var/lib/opentofu/cristexweb/github.tfstate",
            "/var/lib/cristexweb-backup/opentofu/github",
            "drive:cristexweb-recovery/opentofu/github",
            "cristexweb-opentofu-github-state-backup.{service,timer}",
            "SHARED_DATABASE_BACKUP_AGE_IDENTITY",
            "no state path, archive path, remote, lock, unit, identity, or retention parameters",
            "byte-for-byte",
            "isolated restore",
            "non_mutating=true",
            "foundation",
            "No task in this playbook",
        ):
            self.assertIn(value, normalized)
        self.assertNotRegex(normalized, re.compile(r"(?i)(AGE-SECRET-KEY-|ghp_[a-z0-9]{20,}|github_pat_[a-z0-9_]{20,})"))


if __name__ == "__main__":
    unittest.main()
