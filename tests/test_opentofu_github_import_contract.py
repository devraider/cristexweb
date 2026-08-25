from __future__ import annotations

import json
import os
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
        self.assertEqual(0, subprocess.run(["/bin/dash", "-n", str(IMPORT)]).returncode)
        check = CHECK.read_text()
        self.assertIn('API_ROOT = "https://api.github.com"', check)
        self.assertIn('repository = get_json(f"/repos/{OWNER}/{REPOSITORY}")', check)
        self.assertIn('repository.get("private") is not True', check)
        self.assertIn('repository.get("visibility") != "private"', check)
        for method in ("POST", "PUT", "PATCH", "DELETE", "subprocess", "curl"):
            self.assertNotIn(method, check)

    def test_import_is_fixed_and_non_destructive(self) -> None:
        source = IMPORT.read_text()
        for value in (
            "check|import",
            "/home/paul/projects/cristexweb/opentofu/github",
            "/var/lib/opentofu/cristexweb/github.tfstate",
            "GitHub token (input hidden)",
            "read -r -s github_token",
            "GITHUB_TOKEN=",
            "check-repository-present",
            "restore-absence",
            "tofu",
            "github_repository.reactive_resume_mirror",
            "devraider/cristex-reactive-resume",
            "github_repository_vulnerability_alerts.reactive_resume_mirror",
            "github_actions_repository_permissions.reactive_resume_mirror",
            "validate-import-plan",
            "restore",
            "token_output=false",
        ):
            self.assertIn(value, source, value)
        for forbidden in (
            "tofu apply",
            "tofu destroy",
            "tofu state rm",
            "tofu state push",
            "github_repository_file",
            "github_repository_webhook",
            "github_actions_secret",
            "printf '%s' \"$github_token\"",
        ):
            self.assertNotIn(forbidden, source, forbidden)

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
        ):
            self.assertIn(value, text, value)
        self.assertIn("tofu apply", text)
        self.assertIn("tofu state push", text)


if __name__ == "__main__":
    unittest.main()
