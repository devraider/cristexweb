from __future__ import annotations

import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tools import collect_inventory as inventory


class AllowlistTests(unittest.TestCase):
    def test_allowlist_is_immutable_unique_and_argv_based(self) -> None:
        self.assertIsInstance(inventory.CHECKS, tuple)
        ids = [check.check_id for check in inventory.CHECKS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 20)
        for check in inventory.CHECKS:
            self.assertIsInstance(check, tuple)
            self.assertIsInstance(check.argv, tuple)
            self.assertTrue(check.argv)
            self.assertNotIn("sudo", check.argv)
            self.assertFalse(any(token in {"sh", "bash", "zsh", "-c"} for token in check.argv))
            self.assertFalse(any(any(character in token for character in ";|`$\n") for token in check.argv))

    def test_allowlist_excludes_secret_and_arbitrary_file_targets(self) -> None:
        flattened = [argument.casefold() for check in inventory.CHECKS for argument in check.argv]
        joined = " ".join(flattened)
        for forbidden in (
            "secret",
            "kubeconfig",
            "token",
            "config view",
            "/proc/",
            "/home/",
            "/root/",
            "environ",
            "get all",
        ):
            self.assertNotIn(forbidden, joined)
        cat_targets = [check.argv[1:] for check in inventory.CHECKS if check.argv[0] == "cat"]
        self.assertEqual(cat_targets, [("/etc/os-release",)])
        find_targets = [check.argv[1] for check in inventory.CHECKS if check.argv[0] == "find"]
        self.assertEqual(find_targets, ["/var/lib/rancher/k3s/server/db"])

    def test_kubectl_checks_disable_disk_discovery_cache(self) -> None:
        kubectl_checks = [check for check in inventory.CHECKS if check.argv[:2] == ("k3s", "kubectl")]
        self.assertTrue(kubectl_checks)
        expected_prefix = ("k3s", "kubectl", "--cache-dir=")
        self.assertEqual(inventory.KUBECTL_PREFIX, expected_prefix)
        for check in kubectl_checks:
            self.assertEqual(check.argv[:3], expected_prefix)
            self.assertEqual(check.argv.count("--cache-dir="), 1)

    def test_findmnt_omits_mount_options(self) -> None:
        check = next(check for check in inventory.CHECKS if check.check_id == "filesystems")
        self.assertNotIn("OPTIONS", " ".join(check.argv))

    def test_allowlist_covers_requested_inventory_areas(self) -> None:
        ids = {check.check_id for check in inventory.CHECKS}
        expected = {
            "os_release",
            "kernel",
            "cpu",
            "memory",
            "block_devices",
            "filesystems",
            "network_links",
            "network_addresses",
            "routes",
            "listening_tcp_ports",
            "k3s_service",
            "tailscaled_service",
            "k3s_version",
            "kubectl_nodes",
            "kubectl_namespaces",
            "kubectl_pods",
            "kubectl_services",
            "kubectl_ingress_classes",
            "kubectl_storage_classes",
            "kubectl_network_policies",
            "kubectl_kube_system_components",
            "kubectl_dns_resources",
            "kubectl_traefik_resources",
            "kubectl_helm_charts",
            "kubectl_workload_controllers",
            "kubectl_persistent_volumes",
            "kubectl_persistent_volume_claims",
            "datastore_directory",
            "etcd_snapshots",
            "nftables",
            "ufw",
        }
        self.assertTrue(expected.issubset(ids))


class SanitizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sanitizer = inventory.Sanitizer("node-one.example", "localuser")

    def test_sanitizes_network_and_identity_categories(self) -> None:
        uuid = "123e4567-e89b-42d3-a456-426614174000"
        text = (
            "node-one.example localuser person@example.com "
            "192.0.2.44 2001:db8::1 fe80::1%eth0 ::ffff:192.0.2.45 aa:bb:cc:dd:ee:ff " + uuid
        )
        sanitized = self.sanitizer.sanitize(text)
        for sensitive in (
            "node-one.example",
            "localuser",
            "person@example.com",
            "192.0.2.44",
            "2001:db8::1",
            "fe80::1",
            "::ffff:192.0.2.45",
            "aa:bb:cc:dd:ee:ff",
            uuid,
        ):
            self.assertNotIn(sensitive, sanitized)
        for marker in ("<local-hostname>", "<local-user>", "<email>", "<ipv4>", "<ipv6>", "<mac>", "<uuid>"):
            self.assertIn(marker, sanitized)

    def test_sanitizes_extended_ids_and_allowlist_output_forms(self) -> None:
        values = (
            "00000000-0000-0000-0000-000000000000",
            "01890f47-7c2f-7cc6-9d45-123456789abc",
            "ABCD-1234",
            "0123456789ABCDEF",
            "uHNBbu-UZOt-8xOd-GFOb-0UN3-6Qb7-7LJ0OH",
            "aabb.ccdd.eeff",
            "192.000.002.001",
            "person@localhost",
        )
        sanitized = self.sanitizer.sanitize(" ".join(values))
        for value in values:
            self.assertNotIn(value, sanitized)
        for marker in ("<uuid>", "<filesystem-id>", "<lvm-id>", "<mac>", "<ipv4>", "<email>"):
            self.assertIn(marker, sanitized)

    def test_sanitizes_credentials_and_bearer_values(self) -> None:
        text = " ".join(
            (
                "password" + "=" + "example-value",
                "token" + ":" + "abc123",
                "client_" + "secret" + "=" + "'quoted value'",
                "pass" + "=" + "short-value",
                "credentials" + ":" + "bundle-value",
                "etcd-s3-secret-key" + "=" + "object-store-value",
                "service-api-key" + "=" + "hyphen-value",
                "Authorization: Bearer " + "abc.def.ghi",
            )
        )
        sanitized = self.sanitizer.sanitize(text)
        for sensitive in (
            "example-value",
            "abc123",
            "quoted value",
            "short-value",
            "bundle-value",
            "object-store-value",
            "hyphen-value",
            "abc.def.ghi",
        ):
            self.assertNotIn(sensitive, sanitized)
        self.assertIn("password=<redacted>", sanitized)
        self.assertIn("Bearer <redacted>", sanitized)

    def test_sanitizes_trailing_dot_and_derived_hostnames_without_ordinary_words(self) -> None:
        sanitizer = inventory.Sanitizer("node-one.example.", "root", "invoker")
        sanitized = sanitizer.sanitize("node-one.example. node-one-vg node-one_data root invoker anode-one status")
        self.assertEqual(
            sanitized,
            "<local-hostname>. <local-hostname>-vg <local-hostname>_data <local-user> <sudo-user> anode-one status",
        )


class RunCheckTests(unittest.TestCase):
    @staticmethod
    def check(*argv: str) -> inventory.Check:
        return inventory.Check("test", "test command", tuple(argv))

    def test_success_and_sanitized_output(self) -> None:
        result = inventory.run_check(
            self.check(sys.executable, "-c", "print('192.0.2.9')"),
            sanitizer=inventory.Sanitizer(),
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"], "<ipv4>\n")

    def test_nonzero_is_recorded(self) -> None:
        result = inventory.run_check(
            self.check(sys.executable, "-c", "import sys; print('bad', file=sys.stderr); sys.exit(7)")
        )
        self.assertEqual(result["status"], "nonzero")
        self.assertEqual(result["returncode"], 7)
        self.assertEqual(result["stderr"], "bad\n")

    def test_not_found_is_recorded(self) -> None:
        result = inventory.run_check(self.check("definitely-not-a-real-inventory-command"))
        self.assertEqual(result["status"], "not-found")
        self.assertIsNone(result["returncode"])
        self.assertTrue(result["error"])

    def test_timeout_is_recorded(self) -> None:
        result = inventory.run_check(
            self.check(sys.executable, "-c", "import time; time.sleep(5)"),
            timeout_seconds=0.05,
        )
        self.assertEqual(result["status"], "timeout")
        self.assertNotEqual(result["returncode"], 0)
        self.assertIn("exceeded", result["error"])

    def test_timeout_covers_detached_descendant_holding_pipes(self) -> None:
        code = (
            "import subprocess,sys; "
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'], start_new_session=True); "
            "print(child.pid, flush=True)"
        )
        started = time.monotonic()
        result = inventory.run_check(
            self.check(sys.executable, "-c", code),
            timeout_seconds=0.15,
        )
        elapsed = time.monotonic() - started
        descendant_pid = int(result["stdout"].strip())
        try:
            self.assertEqual(result["status"], "timeout")
            self.assertLess(elapsed, 0.75)
        finally:
            try:
                os.kill(descendant_pid, inventory.signal.SIGKILL)
            except ProcessLookupError:
                pass

    def test_stdout_and_stderr_are_bounded(self) -> None:
        code = "import sys; print('x'*100); print('y'*100, file=sys.stderr)"
        result = inventory.run_check(
            self.check(sys.executable, "-c", code),
            max_output_bytes=16,
        )
        self.assertEqual(len(result["stdout"].encode()), 16)
        self.assertEqual(len(result["stderr"].encode()), 16)
        self.assertTrue(result["stdout_truncated"])
        self.assertTrue(result["stderr_truncated"])

    def test_result_shape_is_same_for_success_and_not_found(self) -> None:
        success = inventory.run_check(self.check(sys.executable, "-c", "pass"))
        missing = inventory.run_check(self.check("definitely-not-a-real-inventory-command"))
        self.assertEqual(set(success), set(missing))

    def test_popen_uses_no_shell_and_fixed_environment(self) -> None:
        process = mock.Mock()
        process.stdout = io.BytesIO(b"ok")
        process.stderr = io.BytesIO(b"")
        process.returncode = 0
        process.wait.return_value = 0
        with mock.patch.object(inventory.subprocess, "Popen", return_value=process) as popen:
            result = inventory.run_check(self.check("uname", "-a"))
        self.assertEqual(result["status"], "ok")
        kwargs = popen.call_args.kwargs
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["env"], dict(inventory.FIXED_ENV))
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(kwargs["bufsize"], 0)
        self.assertIs(kwargs["start_new_session"], True)


class CollectionTests(unittest.TestCase):
    def test_report_schema_and_result_keys_are_deterministic(self) -> None:
        def runner(check: inventory.Check, **_: object) -> dict[str, object]:
            result = inventory._result_template(check)
            result.update({"status": "ok", "returncode": 0})
            return result

        now = datetime(2026, 8, 3, 12, 30, tzinfo=timezone.utc)
        with mock.patch.object(inventory.os, "geteuid", return_value=1000), mock.patch.dict(
            inventory.os.environ, {}, clear=True
        ):
            report = inventory.collect_inventory(
                runner=runner,
                now=now,
                hostname="test-host",
                username="tester",
            )
        self.assertEqual(
            set(report),
            {"schema_version", "collector_version", "collected_at_utc", "privilege", "sanitization_warning", "results"},
        )
        self.assertEqual(report["collected_at_utc"], "2026-08-03T12:30:00Z")
        self.assertEqual(list(report["results"]), [check.check_id for check in inventory.CHECKS])
        self.assertTrue(report["sanitization_warning"].startswith("WARNING"))
        self.assertFalse(report["privilege"]["is_root"])

    def test_validated_sudo_uid_username_is_sanitized(self) -> None:
        def runner(check: inventory.Check, **_: object) -> dict[str, object]:
            result = inventory._result_template(check)
            result["stdout"] = "invoking-user"
            return result

        passwd_entry = mock.Mock(pw_name="invoking-user")
        with mock.patch.object(inventory.pwd, "getpwuid", return_value=passwd_entry) as getpwuid:
            report = inventory.collect_inventory(
                runner=runner,
                hostname="host",
                username="root",
                environ={"SUDO_UID": "1001", "SUDO_GID": "1002"},
                effective_uid=0,
            )
        getpwuid.assert_called_once_with(1001)
        self.assertNotIn("invoking-user", json.dumps(report))
        self.assertIn("<sudo-user>", json.dumps(report))
        self.assertTrue(report["privilege"]["invoked_via_sudo"])

    def test_all_textual_runner_fields_are_sanitized(self) -> None:
        def runner(check: inventory.Check, **_: object) -> dict[str, object]:
            result = inventory._result_template(check)
            result["stdout"] = "test-host tester@example.com 192.0.2.7"
            result["error"] = "Bearer " + "sample-value"
            return result

        report = inventory.collect_inventory(
            runner=runner,
            hostname="test-host",
            username="tester",
        )
        serialized = json.dumps(report)
        for sensitive in ("test-host", "tester@example.com", "192.0.2.7", "sample-value"):
            self.assertNotIn(sensitive, serialized)


class AtomicOutputTests(unittest.TestCase):
    def sample_report(self) -> dict[str, object]:
        return {"schema_version": inventory.SCHEMA_VERSION, "results": {}}

    def test_atomic_output_is_valid_json_mode_0600_and_leaves_no_temp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            inventory.write_report_atomic(output, self.sample_report(), environ={}, effective_uid=1000)
            self.assertEqual(json.loads(output.read_text()), self.sample_report())
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual([path.name for path in Path(directory).iterdir()], ["report.json"])

    def test_existing_regular_output_is_replaced_securely(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            output.write_text("old")
            os.chmod(output, 0o644)
            inventory.write_report_atomic(output, self.sample_report(), environ={}, effective_uid=1000)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(json.loads(output.read_text()), self.sample_report())

    def test_symlink_destination_is_rejected_without_changing_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.json"
            target.write_text("unchanged")
            output = Path(directory) / "report.json"
            output.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symlink"):
                inventory.write_report_atomic(output, self.sample_report())
            self.assertEqual(target.read_text(), "unchanged")

    def test_sudo_ownership_helper_uses_fchown_for_valid_invoker(self) -> None:
        with mock.patch.object(inventory.os, "fchown") as fchown:
            inventory.handoff_sudo_ownership(
                17,
                environ={"SUDO_UID": "1001", "SUDO_GID": "1002"},
                effective_uid=0,
            )
        fchown.assert_called_once_with(17, 1001, 1002)

    def test_sudo_ownership_helper_rejects_malformed_identity(self) -> None:
        with self.assertRaisesRegex(ValueError, "SUDO_UID"):
            inventory.handoff_sudo_ownership(
                17,
                environ={"SUDO_UID": "not-a-number", "SUDO_GID": "1002"},
                effective_uid=0,
            )

    def test_sudo_ownership_helper_rejects_unicode_decimal_and_huge_ids(self) -> None:
        invalid_environments = (
            {"SUDO_UID": "١٠٠١", "SUDO_GID": "1002"},
            {"SUDO_UID": str(inventory.LINUX_ID_MAX + 1), "SUDO_GID": "1002"},
            {"SUDO_UID": "9" * 5000, "SUDO_GID": "1002"},
        )
        for environment in invalid_environments:
            with self.subTest(environment=environment):
                with self.assertRaises(ValueError):
                    inventory.handoff_sudo_ownership(
                        17,
                        environ=environment,
                        effective_uid=0,
                    )

    def test_sudo_ownership_helper_accepts_linux_id_boundary(self) -> None:
        with mock.patch.object(inventory.os, "fchown") as fchown:
            inventory.handoff_sudo_ownership(
                17,
                environ={"SUDO_UID": str(inventory.LINUX_ID_MAX), "SUDO_GID": "00001002"},
                effective_uid=0,
            )
        fchown.assert_called_once_with(17, inventory.LINUX_ID_MAX, 1002)

    def test_non_root_environment_cannot_trigger_chown(self) -> None:
        with mock.patch.object(inventory.os, "fchown") as fchown:
            inventory.handoff_sudo_ownership(
                17,
                environ={"SUDO_UID": "1001", "SUDO_GID": "1002"},
                effective_uid=1000,
            )
        fchown.assert_not_called()


class CliTests(unittest.TestCase):
    def test_list_checks_prints_json_without_collection(self) -> None:
        stdout = io.StringIO()
        with mock.patch.object(inventory, "collect_inventory") as collect, redirect_stdout(stdout):
            exit_code = inventory.main(["--list-checks"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(json.loads(stdout.getvalue())), len(inventory.CHECKS))
        collect.assert_not_called()

    def test_collection_writes_requested_report_and_ignores_check_statuses(self) -> None:
        report = {"results": {"example": {"status": "nonzero"}}}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with mock.patch.object(inventory, "collect_inventory", return_value=report), mock.patch.object(
                inventory, "write_report_atomic"
            ) as write:
                exit_code = inventory.main(["--local", "--sanitized-output", str(output)])
        self.assertEqual(exit_code, 0)
        write.assert_called_once_with(output, report)

    def test_malformed_sudo_identity_is_a_clean_collector_error(self) -> None:
        stderr = io.StringIO()
        environment = {"SUDO_UID": str(inventory.LINUX_ID_MAX + 1), "SUDO_GID": "1002"}
        with mock.patch.object(inventory.os, "geteuid", return_value=0), mock.patch.dict(
            inventory.os.environ, environment, clear=True
        ), redirect_stderr(stderr):
            exit_code = inventory.main(["--local", "--sanitized-output", "report.json"])
        self.assertEqual(exit_code, 1)
        self.assertIn("collector error: SUDO_UID exceeds the Linux ID range", stderr.getvalue())
        self.assertFalse(Path("report.json").exists())

    def test_output_failure_returns_nonzero(self) -> None:
        stderr = io.StringIO()
        with mock.patch.object(inventory, "collect_inventory", return_value={}), mock.patch.object(
            inventory, "write_report_atomic", side_effect=OSError("cannot write")
        ), redirect_stderr(stderr):
            exit_code = inventory.main(["--local", "--sanitized-output", "report.json"])
        self.assertEqual(exit_code, 1)
        self.assertIn("collector error", stderr.getvalue())

    def test_arbitrary_or_incomplete_arguments_are_rejected(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                inventory.main(["uname", "-a"])
            with self.assertRaises(SystemExit):
                inventory.main(["--local"])
            with self.assertRaises(SystemExit):
                inventory.main(["--list-checks", "--local"])


if __name__ == "__main__":
    unittest.main()
