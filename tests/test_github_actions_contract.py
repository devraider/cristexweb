from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
WORKFLOW = WORKFLOWS / "ci.yml"
CHECKOUT = "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"
SETUP_PYTHON = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"


class GitHubActionsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text()
        cls.workflow = yaml.safe_load(cls.text)

    def test_exact_ci_only_workflow_closure(self) -> None:
        self.assertEqual(
            {"ci.yml"},
            {path.name for path in WORKFLOWS.iterdir() if path.is_file()},
        )
        self.assertEqual(
            {"name", "on", "permissions", "concurrency", "jobs"},
            set(self.workflow),
        )
        self.assertEqual("Infrastructure CI", self.workflow["name"])
        self.assertEqual({"validate"}, set(self.workflow["jobs"]))
        self.assertEqual({"contents": "read"}, self.workflow["permissions"])

    def test_triggers_runner_concurrency_and_timeout_are_exact(self) -> None:
        self.assertEqual(
            {
                "push": {"branches": ["develop", "main"]},
                "pull_request": {"branches": ["develop", "main"]},
            },
            self.workflow["on"],
        )
        self.assertEqual(
            {
                "group": "infrastructure-ci-${{ github.workflow }}-${{ github.ref }}",
                "cancel-in-progress": True,
            },
            self.workflow["concurrency"],
        )
        job = self.workflow["jobs"]["validate"]
        self.assertEqual({"runs-on", "timeout-minutes", "steps"}, set(job))
        self.assertEqual("ubuntu-24.04", job["runs-on"])
        self.assertEqual(30, job["timeout-minutes"])

    def test_checkout_python_and_controller_install_steps_are_exact(self) -> None:
        steps = self.workflow["jobs"]["validate"]["steps"]
        self.assertEqual(
            [
                {
                    "name": "Checkout",
                    "uses": CHECKOUT,
                    "with": {"persist-credentials": False},
                },
                {
                    "name": "Set up Python",
                    "uses": SETUP_PYTHON,
                    "with": {"python-version": "3.13.7"},
                },
                {
                    "name": "Install locked controller dependencies",
                    "run": (
                        "python -m pip install uv==0.7.2\n"
                        "uv sync --frozen --all-groups\n"
                    ),
                },
            ],
            steps[:3],
        )

    def test_validation_steps_and_commands_are_exact(self) -> None:
        steps = self.workflow["jobs"]["validate"]["steps"]
        self.assertEqual(7, len(steps))
        self.assertEqual(
            [
                {
                    "name": "Install pinned Ansible collection",
                    "run": (
                        "uv run ansible-galaxy collection install \\\n"
                        "  -r ansible/requirements.yml \\\n"
                        "  -p ansible/.ansible/collections\n"
                    ),
                },
                {
                    "name": "Run offline contract tests",
                    "run": (
                        "uv run python -m unittest discover -s tests -v\n"
                        "uv run python -m compileall -q tests\n"
                    ),
                },
                {
                    "name": "Validate Ansible source",
                    "run": (
                        "cd ansible\n"
                        "for playbook in playbooks/*.yml; do\n"
                        "  uv run ansible-playbook \"$playbook\" --syntax-check\n"
                        "done\n"
                        "uv run ansible-lint . ../tests/validate_storage_report.yml\n"
                    ),
                },
                {
                    "name": "Verify vendored evidence hashes",
                    "run": (
                        "(cd ansible/files/vendor/argocd/10.3.0 && "
                        "shasum -a 256 -c SHA256SUMS)\n"
                        "(cd ansible/files/vendor/infisical-operator/0.11.7 && "
                        "shasum -a 256 -c SHA256SUMS)\n"
                    ),
                },
            ],
            steps[3:],
        )
        uses = [step["uses"] for step in steps if "uses" in step]
        self.assertEqual([CHECKOUT, SETUP_PYTHON], uses)
        self.assertTrue(all(re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", item) for item in uses))

    def test_workflow_has_no_deploy_secret_or_external_mutation_path(self) -> None:
        lowered = self.text.lower()
        for forbidden in (
            "packages: write",
            "id-token: write",
            "secrets.",
            "pull_request_target",
            "workflow_dispatch",
            "kubectl",
            "helm",
            "argocd ",
            "ssh ",
            "--ask-become-pass",
            "inventory.local",
            "bootstrap-foundation-namespaces",
            "bootstrap-platform-namespaces",
            "tofu init",
            "tofu plan",
            "tofu apply",
            "tofu destroy",
            "docker login",
            "docker push",
            "ghcr.io",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertNotRegex(lowered, re.compile(r"\b(?:apply|destroy|deploy)\b"))


if __name__ == "__main__":
    unittest.main()
