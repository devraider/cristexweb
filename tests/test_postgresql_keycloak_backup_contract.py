from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
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
            "backup_status=success schema=1",
        ):
            self.assertIn(value, self.script)
        self.assertNotRegex(self.script, r"rclone[^\n]*(sync|move|purge|delete)")
        self.assertNotIn("AGE-SECRET-KEY-", self.script)
        self.assertNotIn("password", self.script.lower())

    def test_plaintext_cleanup_and_exact_local_retention(self) -> None:
        self.assertIn("trap cleanup_plaintext EXIT HUP INT TERM", self.script)
        self.assertIn("/usr/bin/rm -f -- \"$run_directory/keycloak.dump\" \"$run_directory/keycloak.dump.gz\"", self.script)
        self.assertIn("trap cleanup_plaintext EXIT HUP INT TERM", self.script)
        self.assertIn("/usr/bin/age -d -i \"$work/identity\" \"$work/keycloak.dump.gz.age\" >\"$work/keycloak.dump.gz\"", self.restore)
        self.assertIn("/usr/bin/gzip -d -c \"$work/keycloak.dump.gz\" >\"$work/keycloak.dump\"", self.restore)
        self.assertNotIn('age -d -i \"$work/identity\" \"$work/keycloak.dump.gz.age\" |', self.restore)
        self.assertIn("restore_status=failed stage=keycloak_decrypt", self.restore)
        self.assertIn("restore_status=failed stage=keycloak_decompress", self.restore)
        self.assertIn("restore_status=failed stage=cleanup", self.restore)
        self.assertNotIn("delete_restore_pod >/dev/null 2>&1 || true", self.restore)
        self.assertLess(self.script.index("trap cleanup_plaintext EXIT HUP INT TERM"), self.script.index("gzip -9 -c"))
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

    def test_source_closure_is_expanded_and_restore_requires_exact_digest(self) -> None:
        closure_paths = (
            ROOT / "ansible/files/backup/restore-postgresql-keycloak-rehearsal",
            ROOT / "ansible/files/backup/cristexweb-postgresql-keycloak-backup.service",
            ROOT / "ansible/files/backup/cristexweb-postgresql-keycloak-backup.timer",
        )
        digest = hashlib.sha256()
        for path in closure_paths:
            content = path.read_bytes()
            if path.name == "restore-postgresql-keycloak-rehearsal":
                content, count = re.subn(
                    rb"(?m)^source_closure_sha256=[0-9a-f]{64}$",
                    b"source_closure_sha256=" + b"0" * 64,
                    content,
                )
                self.assertEqual(1, count)
            digest.update(str(path.relative_to(ROOT)).encode())
            digest.update(b"\0")
            digest.update(hashlib.sha256(content).hexdigest().encode())
            digest.update(b"\n")
        closure = digest.hexdigest()
        self.assertIn(f"source_closure_sha256={closure}", self.script)
        self.assertIn(f"source_closure_sha256={closure}", self.restore)
        self.assertIn(f"source_closure_sha256: {closure}", PLAYBOOK.read_text())
        self.assertIn('"source_closure_sha256":"%s"', self.script)
        self.assertNotIn('"source_closure_sha256":"$source_closure_sha256"', self.script)
        self.assertIn("backup_status=failed stage=source_closure_contract", self.script)
        self.assertIn("'source_closure_sha256'", self.restore)
        self.assertIn('EXPECTED_SOURCE_CLOSURE_SHA256="$source_closure_sha256"', self.restore)
        self.assertIn("re.fullmatch(r'[0-9a-f]{64}', x['source_closure_sha256'])", self.restore)
        self.assertIn("x['source_closure_sha256']==os.environ['EXPECTED_SOURCE_CLOSURE_SHA256']", self.restore)
        self.assertIn("restore_status=failed stage=manifest_contract", self.restore)
        self.assertIn(
            "restore_status=success schema=1 source_timestamp=%s source_closure_sha256=%s",
            self.restore,
        )
        self.assertIn("discover_restore_pod", self.restore)
        self.assertIn("pod_uid_discovery", self.restore)
        self.assertNotIn("tail -1", self.restore)
        self.assertIn("lsf --files-only", self.restore)
        self.assertIn('cmp -s \"$sorted\" \"$expected_sorted\"', self.restore)
        self.assertIn("source_timestamp", PLAYBOOK.read_text())
        self.assertIn(
            "acceptance_backup_timestamp == postgresql_keycloak_backup_acceptance_restore_source_timestamp",
            PLAYBOOK.read_text(),
        )
        self.assertIn("acceptance_backup_schema == '1'", PLAYBOOK.read_text())
        self.assertIn("acceptance_restore_schema == '1'", PLAYBOOK.read_text())

    def test_catalog_selection_is_complete_and_fail_closed(self) -> None:
        self.assertIn("lsf --dirs-only", self.restore)
        self.assertIn("lsf --files-only", self.restore)
        self.assertIn("catalog-valid", self.restore)
        self.assertIn("grep -Fxq", self.restore)
        self.assertIn("return 1", self.restore)
        self.assertIn('cmp -s \"$sorted\" \"$expected_sorted\"', self.restore)
        self.assertNotIn("tail -1", self.restore)
        self.assertNotRegex(self.restore, r"rclone[^\n]*\|")

    def test_historical_manifests_fail_closed_before_decryption(self) -> None:
        validator = re.search(
            r"if ! FILE=.*? /usr/bin/python3 - <<'PY'\n(?P<body>.*?)\nPY\nthen",
            self.restore,
            re.DOTALL,
        )
        self.assertIsNotNone(validator)
        source_closure = re.search(
            r"(?m)^source_closure_sha256=([0-9a-f]{64})$", self.restore
        )
        self.assertIsNotNone(source_closure)
        expected = source_closure.group(1)
        base = {
            "schema": 1,
            "service": "postgresql",
            "database": "keycloak",
            "created_at_utc": "20260826T031500Z",
            "archive": "keycloak.dump.gz.age",
            "archive_bytes": 1,
            "archive_sha256": "a" * 64,
            "encryption": "age-x25519",
            "source_cluster": "shared-postgresql",
            "source_closure_sha256": expected,
        }
        cases = []
        missing = dict(base)
        del missing["source_closure_sha256"]
        cases.append(missing)
        literal = dict(base)
        literal["source_closure_sha256"] = "$source_closure_sha256"
        cases.append(literal)
        stale = dict(base)
        stale["source_closure_sha256"] = "0" * 64
        cases.append(stale)
        for manifest in cases:
            with tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, "manifest.json")
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(manifest, handle)
                result = subprocess.run(
                    [sys.executable, "-c", validator.group("body")],
                    env={
                        "FILE": path,
                        "TIMESTAMP": "20260826T031500Z",
                        "EXPECTED_SHA": "a" * 64,
                        "ARCHIVE_BYTES": "1",
                        "EXPECTED_SOURCE_CLOSURE_SHA256": expected,
                    },
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0)
        self.assertIn("restore_status=failed stage=manifest_contract", self.restore)

    def test_restore_cleanup_commands_render_and_fail_closed(self) -> None:
        for jsonpath in (
            r"{.metadata.labels.app\.kubernetes\.io/name}",
            r"{.metadata.labels.cristex\.io/run-id}",
        ):
            self.assertIn(f"jsonpath='{jsonpath}'", self.restore)
        self.assertNotIn(r"app\\.kubernetes", self.restore)
        self.assertNotIn(r"cristex\\.io", self.restore)
        delete_lines = [line for line in self.restore.splitlines() if "DeleteOptions" in line]
        self.assertEqual(1, len(delete_lines))
        format_match = re.search(r"/usr/bin/printf '([^']+)' \"\$uid\"", delete_lines[0])
        self.assertIsNotNone(format_match)
        rendered = subprocess.run(
            ["/usr/bin/printf", format_match.group(1), "uid-123"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(
            {"kind": "DeleteOptions", "apiVersion": "v1", "propagationPolicy": "Orphan", "preconditions": {"uid": "uid-123"}},
            json.loads(rendered),
        )
        self.assertTrue(rendered.endswith("\n"))
        self.assertIn('[ "$discovered_count" -eq 1 ] && [ "$discovered_name" = "$pod" ] || return 1', self.restore)
        self.assertIn("delete_restore_pod || cleanup_status=1", self.restore)
        self.assertNotIn("delete_restore_pod >/dev/null 2>&1 || true", self.restore)

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
