import json
from pathlib import Path
import re
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
            "x['run_id'] == expected_timestamp",
            "if manifest_scope != label",
            "parse_constant=reject_json_constant",
            "raise SystemExit('manifest_contract:invalid_json')",
            "type(x['schema']) is int",
            "type(x.get('version')) is not int",
            "type(x.get('serial')) is not int",
            "type(x['archive_bytes']) is int",
        ):
            self.assertIn(required, self.restore)
        self.assertIn("x['source_closure_sha256'] == expected_source", self.restore)
        for text in (self.backup, self.restore):
            self.assertNotRegex(text, r"(?m)^\s*assert\b")
            for python_override in ("PYTHONOPTIMIZE", "PYTHONPATH", "PYTHONHOME"):
                self.assertIn(python_override, text)
        self.assertIn("seen = {}", self.restore)
        self.assertIn("if address in seen:", self.restore)
        self.assertIn("state address closure mismatch", self.restore)
        for text in (self.backup, self.restore):
            self.assertIn("run_rclone() {", text)
            self.assertIn("/usr/bin/env -i", text)
            self.assertIn("HOME=/home/paul", text)
            self.assertIn("XDG_CONFIG_HOME=/home/paul/.config", text)
        self.assertIn("run_infisical() {", self.restore)
        self.assertNotIn("/home/paul/.nvm/versions/node/v24.19.0/bin/infisical secrets", self.restore)

    def test_restore_catalog_selection_is_exact_and_fail_closed(self):
        self.assertIn("select_latest_complete_catalog()", self.restore)
        self.assertIn("uniq -d", self.restore)
        self.assertIn("[ ! -s \"$nested\" ] || continue", self.restore)
        self.assertIn("if ! run_rclone lsf --dirs-only \"$remote_root\" >\"$catalog\"; then", self.restore)
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
export FAKE_RCLONE={shlex.quote(str(fake))}
run_rclone() {{ "$FAKE_RCLONE" --config "$rclone_config" "$@"; }}
{selector}if select_latest_complete_catalog; then
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

    def test_state_list_uses_pinned_clean_environment_and_exact_paths(self):
        for required in (
            "Environment=TF_CLI_CONFIG_FILE=/dev/null",
            "Environment=TF_WORKSPACE=default",
            "Environment=TOFU_DISABLE_CHECKPOINT=1",
        ):
            self.assertIn(required, self.service)
        for text in (self.backup, self.restore):
            for required in (
                "/usr/bin/env -i",
                "TF_CLI_CONFIG_FILE=/dev/null",
                "TF_DATA_DIR=",
                "TF_WORKSPACE=default",
                "TOFU_DISABLE_CHECKPOINT=1",
                "TF_CLI_ARGS_*",
                "TF_VAR_*",
                "TF_REGISTRY_*",
                "CLOUDFLARE_*",
                "AWS_*",
                "RCLONE_*",
                "INFISICAL_*",
                "PYTHON*",
                "PYTHONNOUSERSITE=1",
                "PYTHONDONTWRITEBYTECODE=1",
                "inherited_environment_override",
                "tofu_target=/opt/opentofu/1.12.5/tofu",
                "-no-color",
            ):
                self.assertIn(required, text)
        self.assertIn("state_file=/var/lib/opentofu/cristexweb/foundation.tfstate", self.backup)
        self.assertIn("state_parent=/var/lib/opentofu/cristexweb", self.backup)
        self.assertIn("-state=\"$state_file\"", self.backup)
        self.assertIn("TF_WORKSPACE=default", self.restore)
        self.assertIn("run_tofu_state_list \"$work/foundation.tfstate\" \"$work/resources\"", self.restore)
        for text in (self.backup, self.restore):
            self.assertNotIn("TOFU_DISABLE_CHECKPOINT=1 /usr/local/bin/tofu state list", text)
            self.assertNotIn("actual_set = set(actual)", text)
            self.assertNotIn("actual = {", text)
            self.assertIn("if address in seen:", text)
            self.assertIn("len(actual) == len(addresses)", text)

    @staticmethod
    def _embedded_scope_parser(text, marker):
        start = text.index(marker) + len(marker)
        end = text.index("\nPY\n", start)
        return text[start:end]

    def test_state_list_rejects_inherited_cli_and_provider_overrides(self):
        for text, stop_marker in (
            (self.backup, "tofu=/usr/local/bin/tofu"),
            (self.restore, "project_id=619656da-14f3-4872-857b-be103cdc5326"),
        ):
            start = text.index("umask 077")
            prefix = text[start:text.index(stop_marker, start)]
            for variable in (
                "TF_CLI_ARGS_plan",
                "TF_VAR_cloudflare_zone_id",
                "CLOUDFLARE_API_TOKEN",
                "RCLONE_CONFIG",
                "RCLONE_CONFIG_DRIVE_TYPE",
                "RCLONE_REMOTE",
                "INFISICAL_TOKEN",
                "INFISICAL_DOMAIN",
                "INFISICAL_API_URL",
                "PYTHONOPTIMIZE",
                "PYTHONPATH",
                "PYTHONHOME",
                "PYTHONEXECUTABLE",
            ):
                result = subprocess.run(
                    ["/bin/sh", "-c", prefix],
                    env={"PATH": "/usr/local/bin:/usr/bin:/bin", variable: "sentinel-value"},
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(65, result.returncode, result.stdout + result.stderr)
                self.assertIn("inherited_environment_override", result.stdout)
                self.assertIn(variable, result.stdout)
                self.assertNotIn("sentinel-value", result.stdout)
                self.assertNotIn("sentinel-value", result.stderr)
            safe = subprocess.run(
                ["/bin/sh", "-c", prefix],
                env={
                    "PATH": "/usr/local/bin:/usr/bin:/bin",
                    "TF_CLI_CONFIG_FILE": "/dev/null",
                    "TF_WORKSPACE": "default",
                    "TOFU_DISABLE_CHECKPOINT": "1",
                },
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, safe.returncode, safe.stdout + safe.stderr)

    def test_optimized_manifest_parser_rejects_forged_source_closure(self):
        marker = "import json, os, re\n"
        start = self.restore.index(marker)
        end = self.restore.index("\nPY\n", start)
        parser = self.restore[start:end]
        source_match = re.search(r"source_closure_sha256=([0-9a-f]{64})", self.restore)
        self.assertIsNotNone(source_match)
        expected_source = source_match.group(1)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "manifest.json"
            forged_source = "0" * 64
            self.assertNotEqual(forged_source, expected_source)
            archive_sha = "a" * 64
            manifest.write_text(
                "{"
                '"schema":1,"service":"opentofu","state":"foundation.tfstate",'
                '"run_id":"20240101T000000Z","created_at_utc":"20240101T000000Z",'
                '"archive":"foundation.tfstate.age","archive_bytes":123,'
                f'"archive_sha256":"{archive_sha}","encryption":"age-x25519",'
                '"backend":"local","state_path":"/var/lib/opentofu/cristexweb/foundation.tfstate",'
                '"address_scope":"exact-five",'
                f'"source_closure_sha256":"{forged_source}"'
                "}\n"
            )
            result = subprocess.run(
                ["/usr/bin/python3", "-"],
                input=parser,
                text=True,
                check=False,
                capture_output=True,
                env={
                    "PATH": "/usr/bin:/bin",
                    "PYTHONOPTIMIZE": "1",
                    "FILE": str(manifest),
                    "TIMESTAMP": "20240101T000000Z",
                    "EXPECTED_SHA": "a" * 64,
                    "ARCHIVE_BYTES": "123",
                    "EXPECTED_SOURCE_CLOSURE_SHA256": expected_source,
                },
            )
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("manifest_contract:source_closure", result.stderr)

    def test_state_list_parser_preserves_list_cardinality_and_rejects_duplicates(self):
        expected = [
            "cloudflare_dns_record.argocd_tailscale",
            "cloudflare_dns_record.cristexhub_dev",
            "cloudflare_dns_record.keycloak",
            "cloudflare_zero_trust_tunnel_cloudflared.keycloak",
            "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak",
        ]
        for text, marker, restore in (
            (self.backup, '/usr/bin/python3 - "$state_scope_file" <<\'PY\'\n', False),
            (self.restore, '/usr/bin/python3 - "$work/resources" "$work/manifest.json" <<\'PY\'\n', True),
        ):
            parser = self._embedded_scope_parser(text, marker)
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state_list = root / "resources"
                state_list.write_text("\n".join(reversed(expected)) + "\n")
                state_list.chmod(0o600)
                argv = ["/usr/bin/python3", "-", str(state_list)]
                if restore:
                    manifest = root / "manifest.json"
                    manifest.write_text('{"address_scope":"exact-five"}\n')
                    manifest.chmod(0o600)
                    argv.append(str(manifest))
                accepted = subprocess.run(argv, input=parser, text=True, check=False, capture_output=True)
                self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)
                self.assertIn("exact-five", accepted.stdout)

                duplicate = root / "duplicate"
                duplicate.write_text("\n".join(expected[:-1] + [expected[0]]) + "\n")
                duplicate.chmod(0o600)
                duplicate_argv = ["/usr/bin/python3", "-", str(duplicate)]
                if restore:
                    duplicate_argv.append(str(manifest))
                refused = subprocess.run(duplicate_argv, input=parser, text=True, check=False, capture_output=True)
                self.assertNotEqual(0, refused.returncode)
                self.assertIn("state address closure mismatch", refused.stderr)

                blank = root / "blank"
                blank.write_text("\n".join(expected) + "\n\n")
                blank.chmod(0o600)
                blank_argv = ["/usr/bin/python3", "-", str(blank)]
                if restore:
                    blank_argv.append(str(manifest))
                refused_blank = subprocess.run(blank_argv, input=parser, text=True, check=False, capture_output=True)
                self.assertNotEqual(0, refused_blank.returncode)

    def test_optimized_manifest_and_state_parsers_reject_boolean_integers(self):
        manifest_marker = "import json, os, re\n"
        manifest_start = self.restore.index(manifest_marker)
        manifest_end = self.restore.index("\nPY\n", manifest_start)
        manifest_parser = self.restore[manifest_start:manifest_end]
        source_match = re.search(r"source_closure_sha256=([0-9a-f]{64})", self.restore)
        self.assertIsNotNone(source_match)
        expected_source = source_match.group(1)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "manifest.json"
            base_manifest = {
                "schema": 1,
                "service": "opentofu",
                "state": "foundation.tfstate",
                "run_id": "20240101T000000Z",
                "created_at_utc": "20240101T000000Z",
                "archive": "foundation.tfstate.age",
                "archive_bytes": 123,
                "archive_sha256": "a" * 64,
                "encryption": "age-x25519",
                "backend": "local",
                "state_path": "/var/lib/opentofu/cristexweb/foundation.tfstate",
                "address_scope": "exact-five",
                "source_closure_sha256": expected_source,
            }
            for schema in (True, False):
                candidate = dict(base_manifest)
                candidate["schema"] = schema
                manifest.write_text(json.dumps(candidate) + "\n")
                result = subprocess.run(
                    ["/usr/bin/python3", "-"],
                    input=manifest_parser,
                    text=True,
                    check=False,
                    capture_output=True,
                    env={
                        "PATH": "/usr/bin:/bin",
                        "PYTHONOPTIMIZE": "1",
                        "FILE": str(manifest),
                        "TIMESTAMP": "20240101T000000Z",
                        "EXPECTED_SHA": "a" * 64,
                        "ARCHIVE_BYTES": "123",
                        "EXPECTED_SOURCE_CLOSURE_SHA256": expected_source,
                    },
                )
                self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn("manifest_contract:identity", result.stderr)

            candidate = dict(base_manifest)
            candidate["archive_bytes"] = True
            manifest.write_text(json.dumps(candidate) + "\n")
            result = subprocess.run(
                ["/usr/bin/python3", "-"],
                input=manifest_parser,
                text=True,
                check=False,
                capture_output=True,
                env={
                    "PATH": "/usr/bin:/bin",
                    "PYTHONOPTIMIZE": "1",
                    "FILE": str(manifest),
                    "TIMESTAMP": "20240101T000000Z",
                    "EXPECTED_SHA": "a" * 64,
                    "ARCHIVE_BYTES": "123",
                    "EXPECTED_SOURCE_CLOSURE_SHA256": expected_source,
                },
            )
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("manifest_contract:archive_bytes", result.stderr)

            state_marker = "import json, os\n"
            state_start = self.restore.index(state_marker)
            state_end = self.restore.index("\nPY\n", state_start)
            state_parser = self.restore[state_start:state_end]
            state = {"version": 3, "lineage": "lineage", "serial": 1}
            for version in (True, False):
                candidate = dict(state)
                candidate["version"] = version
                state_file = root / "foundation.tfstate"
                state_file.write_text(json.dumps(candidate) + "\n")
                result = subprocess.run(
                    ["/usr/bin/python3", "-"],
                    input=state_parser,
                    text=True,
                    check=False,
                    capture_output=True,
                    env={"PATH": "/usr/bin:/bin", "PYTHONOPTIMIZE": "1", "STATE": str(state_file)},
                )
                self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn("state_contract:version", result.stderr)

            candidate = dict(state)
            candidate["serial"] = True
            state_file.write_text(json.dumps(candidate) + "\n")
            result = subprocess.run(
                ["/usr/bin/python3", "-"],
                input=state_parser,
                text=True,
                check=False,
                capture_output=True,
                env={"PATH": "/usr/bin:/bin", "PYTHONOPTIMIZE": "1", "STATE": str(state_file)},
            )
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("state_contract:serial", result.stderr)

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
