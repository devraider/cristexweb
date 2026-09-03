from pathlib import Path
import shlex
import subprocess
import tempfile
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

    def test_restore_catalog_selection_is_exact_and_fail_closed(self):
        self.assertIn("select_latest_complete_catalog()", self.restore)
        self.assertIn("uniq -d", self.restore)
        self.assertIn("[ ! -s \"$nested\" ] || continue", self.restore)
        self.assertIn("if ! /usr/local/bin/rclone --config \"$rclone_config\" lsf --dirs-only \"$remote_root\" >\"$catalog\"; then", self.restore)
        self.assertNotIn("tail -1", self.restore)
        self.assertNotIn("| /usr/bin/sort", self.restore)
        for line in self.restore.splitlines():
            if "rclone" in line:
                self.assertNotIn("|", line, line)

        selector_start = self.restore.index("select_latest_complete_catalog() {")
        selector_end = self.restore.index("if ! select_latest_complete_catalog;", selector_start)
        selector = self.restore[selector_start:selector_end]

        def run_selector(root_entries, files_by_timestamp, nested_by_timestamp=None, error_path=""):
            nested_by_timestamp = nested_by_timestamp or {}
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                work = root / "work"
                work.mkdir()
                root_listing = root / "root-listing"
                root_listing.write_text(root_entries)
                nested_dir = root / "nested"
                nested_dir.mkdir()
                files_dir = root / "files"
                files_dir.mkdir()
                for timestamp, entries in nested_by_timestamp.items():
                    (nested_dir / timestamp).write_text(entries)
                for timestamp, entries in files_by_timestamp.items():
                    (files_dir / timestamp).write_text(entries)
                fake = root / "rclone"
                fake.write_text(
                    """#!/bin/sh
set -eu
[ "$1" = --config ] && [ "$3" = lsf ] || exit 99
mode="$4"
path="$5"
[ "${FAKE_ERROR_PATH:-}" != "$mode|$path" ] || exit 23
if [ "$mode" = --dirs-only ] && [ "$path" = drive:root ]; then
  cat "$FAKE_ROOT_FILE"
  exit 0
fi
if [ "$mode" = --dirs-only ]; then
  candidate="${path#drive:root/}"
  file="$FAKE_NESTED_DIR/$candidate"
  [ ! -f "$file" ] || cat "$file"
  exit 0
fi
if [ "$mode" = --files-only ]; then
  candidate="${path#drive:root/}"
  file="$FAKE_FILES_DIR/$candidate"
  if [ -f "$file" ]; then
    cat "$file"
  fi
  exit 0
fi
exit 99
"""
                )
                fake.chmod(0o755)
                harness = f"""#!/bin/sh
set -eu
work={shlex.quote(str(root / 'work'))}
remote_root=drive:root
rclone_config=config
archive_leaf=foundation.tfstate.age
checksum_leaf=foundation.tfstate.age.sha256
manifest_leaf=manifest.json
export FAKE_ROOT_FILE={shlex.quote(str(root / 'root-listing'))}
export FAKE_NESTED_DIR={shlex.quote(str(nested_dir))}
export FAKE_FILES_DIR={shlex.quote(str(files_dir))}
export FAKE_ERROR_PATH={shlex.quote(error_path)}
{selector.replace('/usr/local/bin/rclone', shlex.quote(str(fake)))}if select_latest_complete_catalog; then
  printf 'selected=%s\\n' "$latest"
else
  printf 'selection=failed\\n'
  exit 1
fi
"""
                harness_path = root / "selector"
                harness_path.write_text(harness)
                harness_path.chmod(0o755)
                return subprocess.run([str(harness_path)], check=False, capture_output=True, text=True)

        exact = "foundation.tfstate.age\nfoundation.tfstate.age.sha256\nmanifest.json\n"
        result = run_selector(
            "20240101T000000Z/\n20240201T000000Z/\n20240301T000000Z/\n",
            {
                "20240101T000000Z": exact,
                "20240201T000000Z": exact,
                "20240301T000000Z": exact + "extra.txt\n",
            },
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("selected=20240201T000000Z", result.stdout)

        result = run_selector(
            "20240101T000000Z/\n20240201T000000Z/\n",
            {"20240101T000000Z": exact, "20240201T000000Z": exact + "manifest.json\n"},
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("selected=20240101T000000Z", result.stdout)

        result = run_selector("20240101T000000Z/\n20240101T000000Z/\n", {"20240101T000000Z": exact})
        self.assertNotEqual(0, result.returncode)

        result = run_selector(
            "20240101T000000Z/\n20240201T000000Z/\n",
            {"20240101T000000Z": exact, "20240201T000000Z": exact},
            {"20240201T000000Z": "nested/\n"},
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("selected=20240101T000000Z", result.stdout)

        result = run_selector("", {}, error_path="--dirs-only|drive:root")
        self.assertNotEqual(0, result.returncode)

        result = run_selector(
            "20240101T000000Z/\n",
            {"20240101T000000Z": exact},
            error_path="--files-only|drive:root/20240101T000000Z",
        )
        self.assertNotEqual(0, result.returncode)

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
