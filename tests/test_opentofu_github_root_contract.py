from __future__ import annotations

import re
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
            'name                 = "cristex-reactive-resume"',
            'visibility           = "private"',
            "auto_init            = false",
            "prevent_destroy = true",
            "has_issues           = false",
            "has_projects         = false",
            "has_wiki             = false",
            "has_downloads        = false",
            "vulnerability_alerts = true",
            'resource "github_actions_repository_permissions" "reactive_resume_mirror"',
            "enabled         = false",
            'allowed_actions = "selected"',
            "github_owned_allowed = false",
            "verified_allowed     = false",
            "patterns_allowed     = []",
        ):
            self.assertIn(required, repository)
        for forbidden in (
            "source =",
            "fork =",
            "template =",
            "github_repository_file",
            "github_repository_webhook",
            "github_deploy_key",
            "github_actions_secret",
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

    def test_docs_preserve_owner_and_mutation_boundaries(self) -> None:
        normalized = " ".join(self.readme.split())
        for required in (
            "separate, source-only OpenTofu root",
            "devraider/cristex-reactive-resume",
            "private",
            "auto_init = false",
            "prevent_destroy = true",
            "Actions disabled before any upstream ref is pushed",
            "metadata-only container",
            "source files",
            "webhooks",
            "deploy keys",
            "Actions secrets",
            "package resources",
            "github.tfstate",
            "encrypted backup/readback",
            "No `tofu init`, `tofu plan`, `tofu apply`",
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
