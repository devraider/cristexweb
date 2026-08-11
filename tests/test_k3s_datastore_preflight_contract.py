from __future__ import annotations

import json
import os
import stat
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
ROLE = ANSIBLE / "roles/k3s_datastore_preflight"
WRAPPER = ANSIBLE / "bin/preflight-k3s-datastore"
PLAYBOOK = ANSIBLE / "playbooks/preflight_k3s_datastore.yml"
FIXTURE = ROOT / "tests/validate_k3s_datastore_preflight.yml"
PARSER_FIXTURE = ROOT / "tests/validate_k3s_datastore_preflight_parser.yml"
DIRECT_ROLE_FIXTURE = ROOT / "tests/reject_k3s_datastore_preflight_direct_role.yml"
INTERNAL_FIXTURE = ROOT / "tests/reject_k3s_datastore_preflight_internal_injection.yml"


class K3sDatastorePreflightContractTests(unittest.TestCase):
    def test_layout_wrapper_and_playbook_are_check_only(self) -> None:
        self.assertTrue(WRAPPER.is_file())
        self.assertEqual(0o111, WRAPPER.stat().st_mode & 0o111)
        self.assertTrue(PLAYBOOK.is_file())
        wrapper = WRAPPER.read_text()
        playbook = PLAYBOOK.read_text()
        for required in (
            "usage: ansible/bin/preflight-k3s-datastore check",
            "refusing apply, passthrough arguments",
            "--check",
            "--diff",
            "--limit crtxweb",
            "--become",
            "--ask-become-pass",
            "k3s_datastore_preflight_approved",
            "k3s_datastore_preflight_elevated_requested",
            "k3s_datastore_preflight_elevated_approved",
            "CRISTEXWEB_K3S_DATASTORE_PREFLIGHT_ENTRYPOINT=v1",
            "CRISTEXWEB_K3S_DATASTORE_PREFLIGHT_ATTESTATION_FILE",
            "env -i",
        ):
            self.assertIn(required, wrapper)
        self.assertNotIn("apply", wrapper.split("usage:", 1)[1].split("\n", 1)[0])
        invocation = wrapper.split("set -- \\\n", 1)[1].split("\n\nif [ -n", 1)[0]
        self.assertIn("--become", invocation)
        self.assertIn("--ask-become-pass", invocation)
        self.assertLess(invocation.index("--become"), invocation.index("--ask-become-pass"))
        self.assertNotIn('"ansible_become"', invocation)
        self.assertIn("--start-at-task", wrapper)
        for required in ("hosts: k3s_servers", "become: true", "serial: 1", "any_errors_fatal: true"):
            self.assertIn(required, playbook)

    def test_role_uses_fixed_read_only_commands_and_exact_gates(self) -> None:
        defaults = (ROLE / "defaults/main.yml").read_text()
        tasks = (ROLE / "tasks/main.yml").read_text() + (ROLE / "tasks/parse.yml").read_text()
        for required in (
            "k3s_datastore_preflight_approved: false",
            "k3s_datastore_preflight_elevated_requested: false",
            "k3s_datastore_preflight_elevated_approved: false",
            "k3s_datastore_preflight_output_path",
            "ansible_check_mode",
            "ansible_diff_mode",
            "ansible_limit",
            "ansible_play_hosts_all | length == 1",
            "--version",
            "secrets-encrypt",
            "status",
            "--property=ExecStart",
            "--property=LoadState,ActiveState,SubState",
            "--output=json",
            "check_mode: false",
            "failed_when: false",
            "no_log: true",
            "INTERNAL_VARIABLE_GUARD",
            "ENTRYPOINT_GUARD",
            "Refusing an unknown or malformed preflight stage",
            "k3s_datastore_preflight_remote_path_components",
            "k3s_datastore_preflight_controller_output_path_components",
            "DATASTORE_PATH_GUARD",
            "OUTPUT_PATH_GUARD",
            "internal_output_post_state",
            "stat.nlink == 1",
            "non-private existing preflight artifact destination",
            "config_override_unknown",
            "config_default",
            "k3s_datastore_preflight_config_max_bytes",
            "k3s_datastore_preflight_encryption_output_max_bytes",
            "k3s_datastore_preflight_config_path_components",
            "k3s_datastore_preflight_internal_config_slurp_result",
            "k3s_datastore_preflight_internal_config_post_state",
            "k3s_datastore_preflight_internal_config_content_stable",
            "k3s_datastore_preflight_internal_environment_results",
            "k3s_datastore_preflight_environment_file_paths",
            "k3s_datastore_preflight_internal_environment_file_states",
            "k3s_datastore_preflight_internal_environment_file_post_states",
            "k3s_datastore_preflight_internal_environment_file_key_count_result",
            "k3s_datastore_preflight_internal_environment_file_content_stable",
            "k3s_datastore_preflight_internal_environment_file_relevant_keys_absent",
            "k3s_datastore_preflight_internal_environment_overrides_absent",
            "/etc/systemd/system/k3s.service.env",
            "/usr/bin/grep",
            "--count",
            "EnvironmentFiles",
            "k3s_datastore_preflight_internal_config_key_counts",
            "k3s_datastore_preflight_internal_data_dir_arg_exact_marker",
            "k3s_datastore_preflight_internal_encryption_payload",
            "hashmatch",
            "reencrypt_finished",
            "'initial'",
            "Clear private raw probe facts before report construction",
        ):
            self.assertIn(required, defaults + tasks)
        self.assertNotIn("ansible_become | default", tasks)
        delegated_blocks = tasks.split("delegate_to: localhost")[1:]
        self.assertGreaterEqual(len(delegated_blocks), 8)
        for block in delegated_blocks:
            self.assertIn("become: false", block.split("\n\n", 1)[0])
        environment_count_task = tasks.split("Count only datastore and encryption keys in the exact k3s service EnvironmentFile", 1)[1].split("\n- name:", 1)[0]
        self.assertIn("/usr/bin/grep", environment_count_task)
        self.assertIn("/etc/systemd/system/k3s.service.env", environment_count_task)
        self.assertIn("--count", environment_count_task)
        self.assertIn("no_log: true", environment_count_task)
        self.assertNotIn("ansible.builtin.slurp", environment_count_task)
        for forbidden in (
            "ansible.builtin.shell:",
            "ansible.builtin.raw:",
            "ansible.builtin.script:",
            "ansible.builtin.apt:",
            "ansible.builtin.reboot:",
            "k3s etcd-snapshot",
            "secrets-encrypt prepare",
            "secrets-encrypt rotate",
            "secrets-encrypt reencrypt",
            "state: absent",
            "state: restarted",
        ):
            self.assertNotIn(forbidden, tasks)
        encryption_task = tasks.split("Read the fixed k3s encryption status command", 1)[1].split("\n- name:", 1)[0]
        self.assertIn("- --output\n      - json", encryption_task)
        self.assertNotIn("--output=json", encryption_task)
        self.assertIn("stat.nlink", tasks)
        self.assertIn("stat.inode", tasks)
        self.assertIn("stat.mtime", tasks)
        self.assertIn("stat.ctime", tasks)
        self.assertIn("'/etc/default/k3s (ignore_errors=yes)'", tasks)
        self.assertIn("'/etc/sysconfig/k3s (ignore_errors=yes)'", tasks)
        self.assertIn("'/etc/systemd/system/k3s.service.env (ignore_errors=yes)'", tasks)
        command_blocks = tasks.split("ansible.builtin.command:")[1:]
        self.assertGreaterEqual(len(command_blocks), 5)
        for block in command_blocks:
            self.assertIn("argv:", block)
            self.assertIn("no_log: true", block)
            self.assertIn("check_mode: false", block)
            self.assertIn("failed_when: false", block)

    def test_report_template_has_exact_sanitized_schema(self) -> None:
        template = (ROLE / "templates/report.json.j2").read_text()
        fixture = FIXTURE.read_text()
        expected = (
            "schema_version",
            "evidence_class",
            "invocation",
            "check_mode",
            "diff_mode",
            "one_host_limit",
            "elevated_requested",
            "elevated_approved",
            "k3s",
            "version",
            "executable_status",
            "config_status",
            "exec_start_status",
            "data_dir_source",
            "datastore",
            "type",
            "sqlite_marker_present",
            "etcd_marker_present",
            "external_endpoint_explicit",
            "encryption",
            "command_status",
            "rotation_stage",
            "health",
            "k3s_service",
            "tailscaled_service",
            "node_query",
            "node_count",
            "ready_node_count",
            "node_stage",
            "disclosure_controls",
            "remote_mutation",
            "backup_or_restore",
            "encryption_mutation",
            "secret_values",
            "key_material",
            "token_values",
            "config_content",
            "kubeconfig_content",
            "raw_command_output",
            "node_identifiers",
            "paths_or_urls",
        )
        for key in expected:
            self.assertIn(key, template)
        for forbidden in (
            "stdout",
            "stderr",
            "ExecStart",
            "config_content",
            "kubeconfig_content",
            "nodeInfo",
            "metadata.name",
            "secret_data",
            "token_values",
            "key_material",
            "path=",
            "https://",
            "activekey",
            "hasherror",
            "inactivekeys",
            "EnvironmentFiles",
        ):
            if forbidden in ("config_content", "kubeconfig_content", "token_values", "key_material"):
                continue
            self.assertNotIn(forbidden, template)
        for sensitive in (
            "fixture-token",
            "fixture-key",
            "fixture-config-secret",
            "fixture-kubeconfig-secret",
            "fixture-node-name",
            "fixture-raw-stdout",
            "fixture-raw-stderr",
        ):
            self.assertIn(sensitive, fixture)

    def test_synthetic_fixture_and_ignored_runtime_artifact_boundary(self) -> None:
        self.assertTrue(FIXTURE.is_file())
        ignore = (ROOT / ".gitignore").read_text()
        self.assertIn("k3s-datastore-preflight.local", ignore)
        artifacts = list((ANSIBLE / ".ansible").glob("k3s-datastore-preflight.local.json"))
        for path in artifacts:
            self.assertFalse(path.is_symlink())
            metadata = path.stat()
            self.assertTrue(stat.S_ISREG(metadata.st_mode))
            self.assertEqual(0o600, stat.S_IMODE(metadata.st_mode))
            self.assertEqual(1, metadata.st_nlink)
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "ansible/.ansible/k3s-datastore-preflight.local.json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, tracked.returncode)

    def test_synthetic_report_and_parser_fixtures_execute(self) -> None:
        env = os.environ.copy()
        env["ANSIBLE_CONFIG"] = str(ANSIBLE / "ansible.cfg")
        for fixture in (FIXTURE, PARSER_FIXTURE):
            result = subprocess.run(
                [
                    str(ROOT / ".venv/bin/ansible-playbook"),
                    str(fixture),
                    "-i",
                    "localhost,",
                    "--limit",
                    "localhost",
                ],
                cwd=ANSIBLE,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_direct_role_and_internal_injection_fail_before_host_commands(self) -> None:
        env = os.environ.copy()
        env["ANSIBLE_CONFIG"] = str(ANSIBLE / "ansible.cfg")
        expectations = (
            (DIRECT_ROLE_FIXTURE, "exact crtxweb one-host limit"),
            (INTERNAL_FIXTURE, "INTERNAL_VARIABLE_GUARD"),
        )
        for fixture, expected in expectations:
            result = subprocess.run(
                [
                    str(ROOT / ".venv/bin/ansible-playbook"),
                    str(fixture),
                    "-i",
                    "localhost,",
                    "--limit",
                    "localhost",
                    "--check",
                    "--diff",
                ],
                cwd=ANSIBLE,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stdout + result.stderr
            self.assertNotEqual(0, result.returncode)
            self.assertIn(expected, output)
            self.assertNotIn("Inspect the fixed k3s executable metadata", output)

    def test_wrapper_rejects_passthrough_before_starting_ansible(self) -> None:
        for args in ((), ("apply",), ("check", "--start-at-task"), ("check", "--tags", "all")):
            result = subprocess.run(
                [str(WRAPPER), *args], cwd=ROOT, capture_output=True, text=True, check=False
            )
            self.assertEqual(64, result.returncode, result.stdout + result.stderr)
            self.assertIn("refusing", result.stderr)
            self.assertNotIn("PLAY [", result.stdout + result.stderr)

    def test_report_shape_fixture_is_valid_json_when_rendered_by_contract(self) -> None:
        # Keep the expected schema independently machine-readable for reviewers.
        expected = {
            "schema_version",
            "evidence_class",
            "invocation",
            "k3s",
            "datastore",
            "encryption",
            "health",
            "disclosure_controls",
        }
        self.assertEqual(expected, set(json.loads('{"schema_version":2,"evidence_class":"read-only-k3s-datastore-encryption-preflight","invocation":{},"k3s":{},"datastore":{},"encryption":{},"health":{},"disclosure_controls":{}}')))


if __name__ == "__main__":
    unittest.main()
