from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
BACKUP = ANSIBLE / "files/backup/opentofu-github-state-backup"
RESTORE = ANSIBLE / "files/backup/restore-opentofu-github-state-rehearsal"
ABSENCE = ANSIBLE / "files/backup/opentofu-github-state-absence-attestation"
ABSENCE_RESTORE = ANSIBLE / "files/backup/restore-opentofu-github-state-absence-rehearsal"
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
        cls.absence = ABSENCE.read_text()
        cls.absence_restore = ABSENCE_RESTORE.read_text()
        cls.service = SERVICE.read_text()
        cls.timer = TIMER.read_text()
        cls.wrapper = WRAPPER.read_text()
        cls.playbook = PLAYBOOK.read_text()
        cls.runbook = RUNBOOK.read_text()
        yaml.safe_load(cls.playbook)

    def test_source_closure_is_separate_and_complete(self):
        for path in (BACKUP, RESTORE, ABSENCE, ABSENCE_RESTORE, SERVICE, TIMER, WRAPPER, PLAYBOOK, RUNBOOK):
            self.assertTrue(path.is_file(), path)
        for text in (self.backup, self.restore, self.absence, self.absence_restore, self.service, self.timer, self.wrapper, self.playbook):
            self.assertNotIn("foundation.tfstate", text)
            self.assertNotIn("cristexweb-opentofu-state-backup", text)
        self.assertIn("github.tfstate", self.backup)
        self.assertIn("github.tfstate", self.restore)
        self.assertIn("github-absence", self.absence)
        self.assertIn("github-absence", self.absence_restore)

    def test_state_backup_has_exact_scope_and_immutable_readback(self):
        for value in (
            "state_parent=/var/lib/opentofu/cristexweb",
            "state_file=\"$state_parent/github.tfstate\"",
            "archive_root=/var/lib/cristexweb-backup/opentofu/github",
            "remote_root=drive:cristexweb-recovery/opentofu/github",
            "copyto --immutable",
            "/usr/bin/cmp -s",
            "address_scope=exact-three",
            "listremotes --long",
            "drive: drive",
            "github_actions_repository_permissions.reactive_resume_mirror",
            "github_repository.reactive_resume_mirror",
            "github_repository_vulnerability_alerts.reactive_resume_mirror",
            "manifest.json",
        ):
            self.assertIn(value, self.backup)
        self.assertNotIn("rclone sync", self.backup)
        self.assertNotIn("rclone delete", self.backup)
        self.assertNotIn("assert ", self.backup)
        self.assertEqual(3, self.backup.count("copyto --immutable"))

    def test_state_restore_filters_complete_timestamped_archives_and_scope(self):
        for value in (
            "lsf --dirs-only",
            "sort -r",
            "^20[0-9]{6}T[0-9]{6}Z$",
            "lsf --files-only",
            "nested_dirs",
            "github.tfstate.age\ngithub.tfstate.age.sha256\nmanifest.json",
            "address_scope=exact-three",
            "TOFU_DISABLE_CHECKPOINT=1",
            "target=isolated-tmpfs",
            "non_mutating=true",
        ):
            self.assertIn(value, self.restore)
        for forbidden in ("tofu apply", "state push", "tofu import", "rclone delete", "assert "):
            self.assertNotIn(forbidden, self.restore)

    def test_first_genesis_absence_uses_dedicated_three_leaf_expiring_archive(self):
        for value in (
            '"state_present":false',
            "archive_root=/var/lib/cristexweb-backup/opentofu/github-absence",
            "remote_root=drive:cristexweb-recovery/opentofu/github-absence",
            "expires_at_utc",
            "now_epoch + 900",
            "absence-attestation.json.age",
            "absence-attestation.json.age.sha256",
            "manifest.json",
            "copyto --immutable",
            "state_absent=verified",
            "encrypted=true",
            "/usr/bin/cmp -s",
        ):
            self.assertIn(value, self.absence)
        self.assertIn("github-absence", self.absence_restore)
        self.assertIn("nested_dirs", self.absence_restore)
        self.assertIn("state_write=false", self.absence_restore)
        self.assertIn("non_mutating=true", self.absence_restore)
        for text in (self.absence, self.absence_restore):
            self.assertNotIn("tofu ", text)
            self.assertNotIn("state push", text)
            self.assertNotIn("assert ", text)
        self.assertEqual(3, self.absence.count("copyto --immutable"))

    def test_playbook_has_attestation_and_exact_remote_type_without_timer_mutation(self):
        for value in (
            "Reject externally supplied recovery internals",
            "CRISTEXWEB_OPENTOFU_GITHUB_STATE_BACKUP_TOKEN",
            "CRISTEXWEB_OPENTOFU_GITHUB_STATE_BACKUP_ATTESTATION_FILE",
            "CRISTEXWEB_OPENTOFU_GITHUB_STATE_BACKUP_APPROVAL",
            "ansible_diff_mode",
            "inventory_hostname == 'crtxweb'",
            "Require exact parent and state symlink closure",
            "remote_src: true",
            "listremotes, --long",
            "drive: drive",
            "attest",
            "restore-absence",
            "absence-attestation",
            "exact-three",
        ):
            self.assertIn(value, self.playbook)
        self.assertNotIn("opentofu_github_state_backup_approved", self.playbook)
        self.assertNotIn("opentofu_github_state_backup_mode == 'enable'", self.playbook)
        self.assertIn("Keep the unaccepted recovery timer disabled", self.playbook)
        self.assertIn("enabled: false", self.playbook)
        self.assertIn("state: stopped", self.playbook)

    def test_wrapper_is_non_passthrough_and_mode_bounded(self):
        for value in (
            "check|apply|test|restore|attest|restore-absence",
            "CRISTEXWEB_OPENTOFU_GITHUB_STATE_BACKUP_ENTRYPOINT=v1",
            "CRISTEXWEB_OPENTOFU_GITHUB_STATE_BACKUP_APPROVAL=v1",
            "CRISTEXWEB_OPENTOFU_GITHUB_STATE_BACKUP_TOKEN=",
            "CRISTEXWEB_OPENTOFU_GITHUB_STATE_BACKUP_ATTESTATION_FILE=",
            "--diff",
            "--limit crtxweb",
            "--extra-vars",
            "exec /usr/bin/env -i HOME=/home/paul USER=paul",
        ):
            self.assertIn(value, self.wrapper)
        self.assertNotIn("enable-check", self.wrapper)
        self.assertNotIn("enable-apply", self.wrapper)
        self.assertNotIn('exec "$@"', self.wrapper)

    def test_shell_sources_are_parseable(self):
        for path in (BACKUP, RESTORE, ABSENCE, ABSENCE_RESTORE, WRAPPER):
            result = subprocess.run(["/bin/dash", "-n", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_units_remain_source_only_without_scheduler_state_mutation(self):
        for value in ("User=paul", "ProtectSystem=strict", "PrivateTmp=true", "CapabilityBoundingSet="):
            self.assertIn(value, self.service)
        for value in ("OnCalendar=*-*-* 03:15:00", "RandomizedDelaySec=15m", "Persistent=true"):
            self.assertIn(value, self.timer)
        self.assertIn("source-only", self.runbook)
        self.assertIn("timer", self.runbook)
        self.assertIn("receipt", self.runbook)


if __name__ == "__main__":
    unittest.main()
