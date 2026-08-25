from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITHUB = ROOT / "opentofu/github"
CHECK = GITHUB / "bin/check-repository-present"
IMPORT = GITHUB / "bin/import-existing-repository"
VALIDATE = GITHUB / "bin/validate-import-plan"
SOURCE = GITHUB / "SOURCE.sha256"
RUNBOOK = ROOT / "runbooks/opentofu-github-repository-import.md"

ADDRESSES = [
    "github_actions_repository_permissions.reactive_resume_mirror",
    "github_repository.reactive_resume_mirror",
    "github_repository_vulnerability_alerts.reactive_resume_mirror",
]


def plan(actions: list[str] | None = None) -> dict:
    action = [] if actions is None else actions
    return {
        "output_changes": {},
        "resource_drift": [],
        "resource_changes": [
            {
                "address": "github_repository.reactive_resume_mirror",
                "mode": "managed",
                "type": "github_repository",
                "provider_name": "registry.opentofu.org/integrations/github",
                "change": {
                    "actions": action,
                    "before": {"id": "devraider/cristex-reactive-resume"},
                    "after": {
                        "name": "cristex-reactive-resume",
                        "description": "Private standalone Reactive Resume source mirror",
                        "visibility": "private",
                        "auto_init": False,
                        "has_issues": False,
                        "has_projects": False,
                        "has_wiki": False,
                        "fork": False,
                        "has_downloads": False,
                    },
                    "after_sensitive": {},
                },
            },
            {
                "address": "github_repository_vulnerability_alerts.reactive_resume_mirror",
                "mode": "managed",
                "type": "github_repository_vulnerability_alerts",
                "provider_name": "registry.opentofu.org/integrations/github",
                "change": {
                    "actions": action,
                    "before": {"id": "cristex-reactive-resume"},
                    "after": {"repository": "cristex-reactive-resume", "enabled": True},
                    "after_sensitive": {},
                },
            },
            {
                "address": "github_actions_repository_permissions.reactive_resume_mirror",
                "mode": "managed",
                "type": "github_actions_repository_permissions",
                "provider_name": "registry.opentofu.org/integrations/github",
                "change": {
                    "actions": action,
                    "before": {"id": "cristex-reactive-resume"},
                    "after": {"repository": "cristex-reactive-resume", "enabled": False},
                    "after_sensitive": {},
                },
            },
        ],
    }


class OpenTofuGithubImportContractTests(unittest.TestCase):
    def test_exact_sources_are_executable_and_value_free(self) -> None:
        for path in (CHECK, IMPORT, VALIDATE):
            self.assertTrue(path.is_file(), path)
            self.assertEqual(0o755, stat.S_IMODE(path.stat().st_mode), path)
        self.assertTrue(SOURCE.is_file())
        self.assertEqual(0o644, stat.S_IMODE(SOURCE.stat().st_mode))
        self.assertEqual(0, subprocess.run(["/bin/dash", "-n", str(IMPORT)]).returncode)
        check = CHECK.read_text()
        self.assertIn('API_ROOT = "https://api.github.com"', check)
        self.assertIn('repository = get_json(f"/repos/{OWNER}/{REPOSITORY}")', check)
        self.assertIn('repository.get("private") is not True', check)
        self.assertIn('repository.get("visibility") != "private"', check)
        for method in ("POST", "PUT", "PATCH", "DELETE", "subprocess", "curl"):
            self.assertNotIn(method, check)

    def test_import_binds_complete_root_source_closure(self) -> None:
        source = IMPORT.read_text()
        closure = SOURCE.read_text().splitlines()
        expected_paths = {
            ".terraform.lock.hcl",
            "README.md",
            "backend.tf",
            "bin/check-repository-absence",
            "bin/check-repository-present",
            "bin/import-existing-repository",
            "bin/validate-create-plan",
            "bin/validate-import-plan",
            "github.tf",
            "providers.tf",
            "versions.tf",
        }
        entries = {relative: digest for digest, relative in (line.split("  ", 1) for line in closure)}
        self.assertEqual(expected_paths, set(entries))
        self.assertEqual(11, len(closure))
        manifest_hash = re.search(r"source_manifest_expected_sha256='([0-9a-f]{64})'", source)
        self_hash = re.search(r"source_import_expected_canonical_sha256='([0-9a-f]{64})'", source)
        self.assertIsNotNone(manifest_hash)
        self.assertIsNotNone(self_hash)
        self.assertEqual(manifest_hash.group(1), hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        canonical = IMPORT.read_text()
        canonical = re.sub(
            r"^source_manifest_expected_sha256='[0-9a-f]{64}'$",
            "source_manifest_expected_sha256='__SOURCE_MANIFEST_SHA256__'",
            canonical,
            flags=re.MULTILINE,
        )
        canonical = re.sub(
            r"^source_import_expected_canonical_sha256='[0-9a-f]{64}'$",
            "source_import_expected_canonical_sha256='__SOURCE_IMPORT_SHA256__'",
            canonical,
            flags=re.MULTILINE,
        )
        self.assertEqual(self_hash.group(1), hashlib.sha256(canonical.encode()).hexdigest())
        for relative, expected in entries.items():
            path = GITHUB / relative
            self.assertTrue(path.is_file(), relative)
            if relative == "bin/import-existing-repository":
                self.assertEqual(expected, hashlib.sha256(canonical.encode()).hexdigest(), relative)
            else:
                self.assertEqual(expected, hashlib.sha256(path.read_bytes()).hexdigest(), relative)
        for value in (
            "SOURCE.sha256",
            "source_manifest_expected_sha256=",
            "source_import_expected_canonical_sha256=",
            "Refusing incomplete or widened GitHub source closure.",
            "Refusing GitHub source drift:",
            "source_actual_paths",
            "source_mode=755",
        ):
            self.assertIn(value, source, value)

    def test_import_is_fixed_and_non_destructive(self) -> None:
        source = IMPORT.read_text()
        for value in (
            "check|import",
            "/home/paul/projects/cristexweb/opentofu/github",
            "/var/lib/opentofu/cristexweb/github.tfstate",
            "GitHub token (input hidden)",
            "/bin/stty -echo",
            "read -r github_token",
            "canonical dash interpreter",
            "LC_ALL=C",
            "export PATH LC_ALL",
            "GITHUB_TOKEN",
            "check-repository-present",
            "restore-absence",
            "tofu",
            "github_repository.reactive_resume_mirror",
            "devraider/cristex-reactive-resume",
            "github_repository_vulnerability_alerts.reactive_resume_mirror",
            "github_actions_repository_permissions.reactive_resume_mirror",
            "validate-import-plan",
            "restore",
            "run_backup_interactive()",
            "sudo_prompt=interactive",
            "token_output=false",
        ):
            self.assertIn(value, source, value)
        for forbidden in (
            "github-import.lock",
            "tofu apply",
            "tofu destroy",
            "tofu state rm",
            "tofu state push",
            "github_repository_file",
            "github_repository_webhook",
            "github_actions_secret",
            "printf '%s' \"$github_token\"",
            'run_quiet "$backup_wrapper"',
        ):
            self.assertNotIn(forbidden, source, forbidden)
        for value in (
            "tofu_target=/opt/opentofu/1.12.5/tofu",
            '[ -L "$tofu" ]',
            'readlink -f -- "$tofu"',
            "stat -c '%U:%G:%a' \"$tofu_target\"",
        ):
            self.assertIn(value, source, value)

    def test_source_closure_is_revalidated_before_each_root_consumer(self) -> None:
        source = IMPORT.read_text()
        self.assertIn("revalidate_source_closure() {", source)
        self.assertIn("not a security boundary against a malicious", source)
        self.assertIn("same operator UID", source)
        self.assertGreaterEqual(source.count("revalidate_source_closure"), 5)
        self.assertIn("run_quiet() {\n    revalidate_source_closure", source)
        self.assertIn("run_quiet_with_token() {\n    revalidate_source_closure", source)
        self.assertIn("run_capture() {\n    revalidate_source_closure", source)
        self.assertIn("revalidate_source_closure\n", source)
        self.assertGreaterEqual(
            source.count('run_quiet_with_token "$github_root/bin/check-repository-present"'),
            4,
        )
        self.assertIn('582ab4adde9e34f06c6ccc9535cb77594c5992ff3a1484d27420385dc5da89b5', source)
        self.assertIn("stat -c '%U:%G:%a' \"$backup_wrapper\"", source)

    def test_backend_environment_lock_and_final_gates_are_bound(self) -> None:
        source = IMPORT.read_text()
        backend = (GITHUB / "backend.tf").read_bytes()
        self.assertEqual(
            "318f268e4f93ae5c7775b798a88db997f4e47d1e32374432cf5c438f63a8e487",
            hashlib.sha256(backend).hexdigest(),
        )
        for value in (
            "backend_expected_sha256=",
            "backend_expected_state_path='/var/lib/opentofu/cristexweb/github.tfstate'",
            "committed backend file is hash-bound",
            "grep -Fxq",
            "exec 9<\"$state_parent\"",
            "check creates or truncates no lock file",
            "/usr/bin/flock -n 9",
            "state_absence_recheck",
            "TF_CLI_ARGS_*",
            "TF_LOG_PATH",
            "TF_CLI_CONFIG_FILE",
            "TF_DATA_DIR",
            "http_proxy",
            "clean_exec_with_token",
            "TF_CLI_CONFIG_FILE=/dev/null",
            "anonymous pipe",
            "post_plan=",
            "second_plan=no-op",
            "postcheck=private-exact",
            "state list -no-color",
        ):
            self.assertIn(value, source, value)
        self.assertIn("run_quiet_with_token \"$github_root/bin/check-repository-present\"", source)
        self.assertIn("run_quiet_with_token \"$tofu\" -chdir=\"$github_root\" plan", source)
        self.assertIn("run_capture \"$post_plan_json\"", source)

    def test_import_plan_validator_accepts_only_noop_exact_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(json.dumps(plan()))
            os.chmod(path, 0o600)
            accepted = subprocess.run([str(VALIDATE), str(path)], capture_output=True, text=True)
            self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)
            self.assertIn("actions=no-op", accepted.stdout)
            payload = plan()
            payload["resource_changes"][0]["change"]["after"].update(
                {"fork": True, "source_owner": "amruthpillai", "source_repo": "reactive-resume"}
            )
            path.write_text(json.dumps(payload))
            fork = subprocess.run([str(VALIDATE), str(path)], capture_output=True, text=True)
            self.assertEqual(0, fork.returncode, fork.stdout + fork.stderr)
            payload = plan(["create"])
            path.write_text(json.dumps(payload))
            refused = subprocess.run([str(VALIDATE), str(path)], capture_output=True, text=True)
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("reason=non_noop_action", refused.stdout)
            payload = plan()
            payload["resource_changes"][0]["change"]["after_sensitive"] = {"token": True}
            path.write_text(json.dumps(payload))
            refused_secret = subprocess.run([str(VALIDATE), str(path)], capture_output=True, text=True)
            self.assertNotEqual(0, refused_secret.returncode)
            self.assertIn("reason=sensitive_values", refused_secret.stdout)

    def test_runbook_records_exact_import_backup_and_restore_gates(self) -> None:
        text = " ".join(RUNBOOK.read_text().split())
        for value in (
            "source-only",
            "devraider/cristex-reactive-resume",
            "/var/lib/opentofu/cristexweb/github.tfstate",
            "github_repository.reactive_resume_mirror",
            "github_repository_vulnerability_alerts.reactive_resume_mirror",
            "github_actions_repository_permissions.reactive_resume_mirror",
            "protected token",
            "immutable",
            "readback",
            "isolated restore",
            "no-op plan",
            "never creates",
            "tofu destroy",
            "state rm",
            "/opt/opentofu/1.12.5/tofu",
            "distribution symlink itself is intentional",
            "--ask-become-pass",
            "controlling terminal",
            "318f268e4f93ae5c7775b798a88db997f4e47d1e32374432cf5c438f63a8e487",
            "anonymous pipe",
            "TF_CLI_ARGS*",
            "first-genesis `flock`",
            "second no-op plan",
            "exact private-repository API postcheck",
            "tofu state list",
        ):
            self.assertIn(value, text, value)
        self.assertIn("tofu apply", text)
        self.assertIn("tofu state push", text)


if __name__ == "__main__":
    unittest.main()
