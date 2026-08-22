from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GITHUB_ROOT = ROOT / "opentofu/github"


class OpenTofuGithubRootContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.files = {
            path.name: path.read_text()
            for path in GITHUB_ROOT.iterdir()
            if path.is_file()
        }
        cls.hcl = "\n".join(
            cls.files[name]
            for name in ("backend.tf", "github.tf", "providers.tf", "versions.tf")
        )
        cls.readme = cls.files["README.md"]

    def test_root_is_separate_and_exactly_closed(self) -> None:
        self.assertEqual(
            {
                "README.md",
                "backend.tf",
                "github.tf",
                "providers.tf",
                "versions.tf",
                ".terraform.lock.hcl",
            },
            set(self.files),
        )
        self.assertEqual(
            {
                ("github_repository", "reactive_resume_mirror"),
                ("github_repository_vulnerability_alerts", "reactive_resume_mirror"),
                ("github_actions_repository_permissions", "reactive_resume_mirror"),
            },
            set(
                re.findall(
                    r'(?m)^resource "([^"]+)" "([^"]+)"\s*\{',
                    self.hcl,
                )
            ),
        )
        self.assertNotIn("opentofu/cloudflare.tf", self.readme)
        self.assertNotIn("foundation.tfstate", self.hcl)
        self.assertIn(
            'path = "/var/lib/opentofu/cristexweb/github.tfstate"',
            self.hcl,
        )

    def test_provider_and_lock_are_pinned_without_provider_secret_configuration(self) -> None:
        for required in (
            'required_version = "= 1.12.5"',
            'source  = "integrations/github"',
            'version = "= 6.13.0"',
            'provider "github"',
            'owner = "devraider"',
            'provider "registry.opentofu.org/integrations/github"',
            'version     = "6.13.0"',
            'constraints = "6.13.0"',
        ):
            self.assertIn(required, self.hcl + self.files[".terraform.lock.hcl"])
        for forbidden in (
            "token =",
            "github_token",
            "GITHUB_TOKEN =",
            "secret",
            "password",
            "client_secret",
            "sensitive",
            "output ",
            "data ",
            "local-exec",
        ):
            self.assertNotIn(forbidden, self.hcl.lower(), forbidden)

    def test_repository_is_private_empty_and_non_destructive(self) -> None:
        repository = self.hcl
        for required in (
            'resource "github_repository" "reactive_resume_mirror"',
            'name         = "cristex-reactive-resume"',
            'visibility   = "private"',
            "auto_init    = false",
            "prevent_destroy = true",
            "has_issues   = false",
            "has_projects = false",
            "has_wiki     = false",
            'resource "github_repository_vulnerability_alerts" "reactive_resume_mirror"',
            "enabled    = true",
            'resource "github_actions_repository_permissions" "reactive_resume_mirror"',
            "enabled    = false",
        ):
            self.assertIn(required, repository)
        for forbidden in (
            "source =",
            "fork =",
            "template =",
            "github_repository_file",
            "has_downloads",
            "vulnerability_alerts =",
            "github_repository_webhook",
            "github_deploy_key",
            "github_actions_secret",
            'allowed_actions = "selected"',
            "allowed_actions_config",
            "github_owned_allowed",
            "patterns_allowed",
            "verified_allowed",
            "github_actions_organization_permissions",
            "github_actions_environment_secret",
            "github_package",
            "github_repository_ruleset",
            "github_branch_protection",
            "github_repository_collaborators",
            "github_team_repository",
            "github_app_installation",
            "webhook",
            "deploy_key",
            "actions_secret",
            "package",
            "cloudflare_",
            "kubernetes_",
            "helm_",
        ):
            self.assertNotIn(forbidden, repository.lower(), forbidden)

    def test_inventory_and_plan_guards_are_fixed_and_executable(self) -> None:
        inventory = GITHUB_ROOT / "bin/check-repository-absence"
        validator = GITHUB_ROOT / "bin/validate-create-plan"
        for path in (inventory, validator):
            self.assertTrue(path.is_file())
            self.assertEqual(0o755, path.stat().st_mode & 0o777)
        inventory_source = inventory.read_text()
        for required in (
            'OWNER = "devraider"',
            'REPOSITORY = "cristex-reactive-resume"',
            'method="GET"',
            'os.environ.get("GITHUB_TOKEN", "")',
            "error.code == 404",
        ):
            self.assertIn(required, inventory_source)
        for forbidden in ("POST", "PATCH", "PUT", "DELETE", "subprocess", "curl"):
            self.assertNotIn(forbidden, inventory_source)

        plan = {
            "output_changes": {},
            "resource_drift": [],
            "resource_changes": [
                {
                    "address": "github_repository.reactive_resume_mirror",
                    "mode": "managed",
                    "type": "github_repository",
                    "provider_name": "registry.opentofu.org/integrations/github",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "name": "cristex-reactive-resume",
                            "visibility": "private",
                            "auto_init": False,
                            "has_issues": False,
                            "has_projects": False,
                            "has_wiki": False,
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
                        "actions": ["create"],
                        "before": None,
                        "after": {"enabled": True},
                        "after_sensitive": {},
                    },
                },
                {
                    "address": "github_actions_repository_permissions.reactive_resume_mirror",
                    "mode": "managed",
                    "type": "github_actions_repository_permissions",
                    "provider_name": "registry.opentofu.org/integrations/github",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {"enabled": False},
                        "after_sensitive": {},
                    },
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.json"
            plan_path.write_text(json.dumps(plan))
            os.chmod(plan_path, 0o600)
            accepted = subprocess.run(
                [str(validator), str(plan_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)
            plan["resource_changes"][0]["change"]["actions"] = ["delete", "create"]
            plan_path.write_text(json.dumps(plan))
            refused = subprocess.run(
                [str(validator), str(plan_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("reason=non_create_action", refused.stdout)

    def test_docs_preserve_owner_and_mutation_boundaries(self) -> None:
        normalized = " ".join(self.readme.split())
        for required in (
            "separate, source-only OpenTofu root",
            "devraider/cristex-reactive-resume",
            "private",
            "auto_init = false",
            "prevent_destroy = true",
            "Actions disabled before any upstream ref is pushed",
            "vulnerability alerts enabled through the non-deprecated dedicated resource",
            "metadata-only container",
            "source files",
            "webhooks",
            "deploy keys",
            "Actions secrets",
            "package resources",
            "github.tfstate",
            "encrypted backup/readback",
            "Controller-only provider/backend initialization",
            "No `tofu plan`, `tofu apply`, import, state mutation",
            "no token variable",
            "source push",
            "GHCR package",
            "Kubernetes object",
            "PostgreSQL role/Secret",
            "no-op plan",
        ):
            self.assertIn(required, normalized)
        self.assertNotRegex(normalized, re.compile(r"(?i)(ghp_[a-z0-9]{20,}|github_pat_[a-z0-9_]{20,})"))


if __name__ == "__main__":
    unittest.main()
