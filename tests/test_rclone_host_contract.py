from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
INSTALL_ROLE = ANSIBLE / "roles/rclone_install"
TRANSFER_ROLE = ANSIBLE / "roles/rclone_proxy_transfer"
INSTALL_WRAPPER = ANSIBLE / "bin/install-rclone"
TRANSFER_WRAPPER = ANSIBLE / "bin/transfer-infisical-proxy-recovery"
SECRET_WRAPPER = ANSIBLE / "bin/bootstrap-infisical-proxy-secrets"


class RcloneHostContractTests(unittest.TestCase):
    def test_install_is_exactly_pinned_and_selector_only_rollback(self) -> None:
        combined = "\n".join(
            path.read_text()
            for path in (
                ANSIBLE / "playbooks/install_rclone.yml",
                INSTALL_ROLE / "defaults/main.yml",
                INSTALL_ROLE / "tasks/main.yml",
                ANSIBLE / "plugins/action/rclone_install_guarded.py",
                INSTALL_WRAPPER,
            )
        )
        for required in (
            "rclone-v1.71.1-linux-amd64.zip",
            "e7179eb69f2fda1b0a3c933d50a3e34e0f5f7e0fa0145c3e75110298b374d407",
            "417e3da236f3a12d292da4e7287d67b1df558b8c2b280d092e563958ed724be7",
            "5409cb410e49903af3517654ccc65c89d89f9dc12d7a97b0e13e09a9be6dc74a",
            "/opt/rclone/1.71.1/rclone",
            "/usr/local/bin/rclone",
            "/var/cache/rclone",
            "Debian",
            "x86_64",
            "controller-download",
            "host-archive-transfer",
            "ARCHIVE_LAYOUT_GUARD",
            "TASK_SELECTION_GUARD",
            "INTERNAL_VARIABLE_GUARD",
            "rollback-check|rollback-apply",
            "--ask-become-pass",
            'extra_vars="{\\"rclone_install_approved\\":true',
            '--extra-vars "$extra_vars"',
        ):
            self.assertIn(required, combined)
        plugin_path = ANSIBLE / "plugins/action/rclone_install_guarded.py"
        plugin = plugin_path.read_text()
        self.assertIn("tempfile.NamedTemporaryFile", plugin)
        self.assertIn('prefix=".rclone.pending."', plugin)
        self.assertNotIn('with_suffix(".pending")', plugin)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.write_bytes(b"sentinel")
            cache = root / "cache"
            cache.mkdir()
            (cache / "rclone.pending").symlink_to(outside)
            module_spec = importlib.util.spec_from_file_location(
                "rclone_install_guarded_contract", plugin_path
            )
            self.assertIsNotNone(module_spec)
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            module._write_binary_cache(cache / "rclone", b"payload")
            self.assertEqual(b"sentinel", outside.read_bytes())
            self.assertEqual(b"payload", (cache / "rclone").read_bytes())
            self.assertTrue((cache / "rclone.pending").is_symlink())
            self.assertFalse(list(cache.glob(".rclone.pending.*")))
        for member in ("rclone", "rclone.1", "README.txt", "README.html", "git-log.txt"):
            self.assertIn(f'rclone-v1.71.1-linux-amd64/{member}', plugin)
        tasks = (INSTALL_ROLE / "tasks/main.yml").read_text()
        self.assertEqual(1, tasks.count("operation: selector-absent"))
        self.assertNotIn("state: absent", tasks)
        self.assertNotIn("name: paul", combined)
        self.assertNotIn("/home/paul", combined)

    def test_transfer_is_host_only_fixed_argv_and_ciphertext_only(self) -> None:
        tasks = (TRANSFER_ROLE / "tasks/main.yml").read_text()
        plugin = (ANSIBLE / "plugins/action/rclone_proxy_transfer_guarded.py").read_text()
        wrapper = TRANSFER_WRAPPER.read_text()
        defaults = (TRANSFER_ROLE / "defaults/main.yml").read_text()
        combined = f"{defaults}\n{tasks}\n{plugin}\n{wrapper}"
        for required in (
            "3562c730814440dc836c3f38d34efc41f0ca6f180635135ba92314990b121d28",
            "infisical-proxy-secret-zero-20260810T095421Z.tar.gz.age",
            "drive:cristexweb-recovery/infisical-proxy/20260810T095421Z",
            '"copyto",',
            '"--immutable",',
            '"--local-umask",',
            '"--config",',
            ".config/rclone/rclone.conf",
            "rclone_proxy_transfer_operator_user == ansible_user",
            "become: false",
            "operation: remote-list",
            "operation: remote-about",
            "listremotes",
            '"--long",',
            "drive: drive",
            '"about",',
            "operation: cleanup",
            'extra_vars="{\\"rclone_proxy_transfer_approved\\":true',
            '--extra-vars "$extra_vars"',
            "Refuse transfer collision or unexpected residue",
            "drive-verified",
            "filename=%s",
            "sha256=%s",
            "remote=%s",
        ):
            self.assertIn(required, combined)
        for operation in (
            '"upload-ciphertext"',
            '"upload-checksum"',
            '"readback-ciphertext"',
            '"readback-checksum"',
        ):
            self.assertEqual(1, plugin.count(operation))
        for forbidden in (" sync", '"sync"', '"move"', '"purge"', '"delete"', "age -d", "AGE-SECRET-KEY"):
            self.assertNotIn(forbidden, tasks + plugin)
        self.assertNotIn("name: paul", tasks + plugin)
        self.assertNotIn("/home/paul", tasks + plugin)
        self.assertNotIn("lookup('ansible.builtin.file', rclone_proxy_transfer_internal_config", tasks)
        role_tasks = yaml.safe_load(tasks)
        config_stat = next(
            task
            for task in role_tasks
            if task["name"] == "Inspect OAuth config path metadata without reading config content"
        )
        self.assertFalse(config_stat["ansible.builtin.stat"]["get_checksum"])
        self.assertTrue(
            any("rclone.conf" in str(path) for path in config_stat["loop"])
        )
        binary_stat = next(
            task
            for task in role_tasks
            if task["name"] == "Inspect exact rclone selector and binary digest"
        )
        self.assertTrue(binary_stat["ansible.builtin.stat"]["get_checksum"])
        self.assertFalse(any("rclone.conf" in str(path) for path in binary_stat["loop"]))
        remote_about = next(
            task
            for task in role_tasks
            if task["name"] == "Verify host Google Drive OAuth with a read-only request"
        )
        self.assertNotIn("check_mode", remote_about)
        self.assertIn("not ansible_check_mode", remote_about["when"])

    def test_controller_secret_writer_has_no_rclone_and_requires_bound_marker(self) -> None:
        writer = SECRET_WRAPPER.read_text()
        self.assertNotIn("/usr/local/bin/rclone", writer)
        self.assertNotIn("rclone copyto", writer)
        self.assertNotIn("remote-copy", writer)
        for required in (
            "drive-verified",
            "filename=%s",
            "sha256=%s",
            "remote=drive:cristexweb-recovery/infisical-proxy/%s/",
            "refusing Secret mutation before guarded host Drive transfer verification",
            "refusing a drive-verified marker not bound to the exact pending artifact",
        ):
            self.assertIn(required, writer)
        self.assertLess(writer.index("drive_verified_marker"), writer.index("secret-vars.yml"))

    def test_wrappers_reject_passthrough_without_starting_ansible(self) -> None:
        for wrapper, modes in (
            (INSTALL_WRAPPER, ("check", "apply", "rollback-check", "rollback-apply")),
            (TRANSFER_WRAPPER, ("check", "apply", "cleanup-check", "cleanup-apply")),
        ):
            self.assertEqual(0o111, wrapper.stat().st_mode & 0o111)
            for mode in modes:
                result = subprocess.run([str(wrapper), mode, "--start-at-task"], cwd=ROOT, text=True, capture_output=True)
                self.assertEqual(64, result.returncode)
                self.assertIn("refusing passthrough arguments", result.stderr)
                self.assertNotIn("PLAY [", result.stdout + result.stderr)

    def test_direct_action_only_and_internal_injection_negatives(self) -> None:
        env = os.environ.copy()
        for fixture in ("reject_rclone_install_direct.yml", "reject_rclone_transfer_direct.yml"):
            result = subprocess.run(
                [str(ROOT / ".venv/bin/ansible-playbook"), "-i", "localhost,", str(ROOT / "tests" / fixture)],
                cwd=ANSIBLE,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("approval contract", result.stdout + result.stderr)
        for fixture in ("reject_rclone_install_action_only.yml", "reject_rclone_transfer_action_only.yml"):
            result = subprocess.run(
                [str(ROOT / ".venv/bin/ansible-playbook"), "-i", "localhost,", str(ROOT / "tests" / fixture)],
                cwd=ANSIBLE,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("ENTRYPOINT_GUARD", result.stdout + result.stderr)
        injections = (
            ("reject_rclone_install_internal_injection.yml", "rclone_install_internal_preflight_binding"),
            ("reject_rclone_transfer_internal_injection.yml", "rclone_proxy_transfer_internal_preflight_binding"),
        )
        for fixture, variable in injections:
            result = subprocess.run(
                [str(ROOT / ".venv/bin/ansible-playbook"), "-i", "localhost,", str(ROOT / "tests" / fixture), "--extra-vars", f"{variable}=forged"],
                cwd=ANSIBLE,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("rescued=1", result.stdout + result.stderr)

    def test_shell_cleanup_is_installed_before_plaintext_and_task_start_fixture_exists(self) -> None:
        transfer = TRANSFER_WRAPPER.read_text()
        self.assertLess(transfer.index("trap cleanup"), transfer.index("age -d"))
        self.assertIn("/bin/rm -rf -- \"$temporary_directory\"", transfer)
        self.assertIn("ca.srl", transfer)
        self.assertIn("/usr/bin/grep -v '^$'", transfer)
        self.assertIn("$1 !~ /^[-d]/", transfer)
        fixture = ROOT / "tests/reject_rclone_task_start.sh"
        self.assertEqual(0o111, fixture.stat().st_mode & 0o111)
        self.assertIn("--start-at-task", fixture.read_text())
        result = subprocess.run(
            [str(fixture)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("forged preflight bindings are rejected", result.stdout)
        manual_qa = (ROOT / "specs/k3s-iac-foundation/manual-qa.md").read_text()
        self.assertIn("the other fifteen cases remain", manual_qa)
        self.assertEqual(1, manual_qa.count("| MQA-17 |"))
        self.assertIn("## MQA-17 — Host rclone", manual_qa)


if __name__ == "__main__":
    unittest.main()
