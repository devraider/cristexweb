from __future__ import annotations

import hashlib
import json
import re
import stat
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/keycloak-reactive-resume-dev-client"
SOURCE = COMPONENT / "source/reactive-resume-dev-client.yaml"
PLUGIN = ROOT / "ansible/plugins/action/keycloak_reactive_resume_dev_client_guarded.py"
TASKS = ROOT / "ansible/roles/keycloak_reactive_resume_dev_client_bootstrap/tasks/main.yml"
DEFAULTS = ROOT / "ansible/roles/keycloak_reactive_resume_dev_client_bootstrap/defaults/main.yml"
WRAPPER = ROOT / "ansible/bin/bootstrap-keycloak-reactive-resume-dev-client"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_keycloak_reactive_resume_dev_client.yml"
RUNBOOK = ROOT / "runbooks/reactive-resume-dev-shared-realm-client.md"
POLICY = ROOT / "ansible/files/policies/hosted-identity-authorization.yml"
ARCH = ROOT / "ansible/files/policies/reactive-resume-architecture.yml"


class KeycloakReactiveResumeDevClientContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_text = SOURCE.read_text()
        cls.source = yaml.safe_load(cls.source_text)
        cls.plugin_text = PLUGIN.read_text()
        cls.tasks_text = TASKS.read_text()
        cls.defaults_text = DEFAULTS.read_text()
        cls.wrapper_text = WRAPPER.read_text()
        cls.runbook_text = RUNBOOK.read_text()
        cls.policy = yaml.safe_load(POLICY.read_text())
        cls.arch = yaml.safe_load(ARCH.read_text())

    def test_exact_value_free_additive_client_contract(self) -> None:
        self.assertEqual("KeycloakClientContract", self.source["kind"])
        self.assertEqual("cristexhub", self.source["spec"]["realm"])
        self.assertTrue(self.source["spec"]["additive"])
        self.assertTrue(self.source["spec"]["preserve_existing_clients"])
        self.assertTrue(self.source["spec"]["preserve_existing_users"])
        self.assertEqual("forbidden", self.source["spec"]["client_deletion"])
        client = self.source["spec"]["clients"][0]
        self.assertEqual("reactive-resume-dev", client["clientId"])
        self.assertEqual(
            ["https://resume-dev.cristex-soft.com/api/auth/oauth2/callback/custom"],
            client["redirectUris"],
        )
        self.assertEqual(["https://resume-dev.cristex-soft.com"], client["webOrigins"])
        self.assertEqual("S256", client["attributes"]["pkce.code.challenge.method"])
        self.assertEqual("https://resume-dev.cristex-soft.com/", client["attributes"]["post.logout.redirect.uris"])
        self.assertNotIn("*", client["attributes"]["post.logout.redirect.uris"])
        self.assertEqual(
            {
                "owner": "infisical-cloud",
                "path": "prod:/reactive-resume/dev/runtime",
                "key": "OAUTH_CLIENT_SECRET",
                "materialization": "materialized-private-runtime",
            },
            client["credentialContract"],
        )
        rollback = self.source["spec"]["rollback"]["oldClient"]
        self.assertEqual("cristexhub-dev", rollback["realm"])
        self.assertEqual("disabled-rollback-only", rollback["status"])
        self.assertEqual("forbidden", rollback["deletion"])
        self.assertNotRegex(self.source_text, r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY")
        self.assertNotRegex(self.source_text, r"(?im)^\s*(?:secret|password|token|clientSecret)\s*:")

    def test_hash_ledger_and_modes(self) -> None:
        self.assertEqual(0o644, stat.S_IMODE(SOURCE.stat().st_mode))
        digest, path = (COMPONENT / "MANIFESTS.sha256").read_text().strip().split("  ", 1)
        self.assertEqual("source/reactive-resume-dev-client.yaml", path)
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), digest)
        self.assertIn(hashlib.sha256(json.dumps(self.source, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), self.plugin_text)

    def test_guard_is_check_only_and_exactly_scoped(self) -> None:
        for value in (
            "shared cristexhub Reactive Resume client source validated offline",
            "EXPECTED_DEFINITION_SHA256",
            "EXPECTED_IDENTITY_SET_SHA256",
            "preserve_existing_clients",
            "preserve_existing_users",
            "runtime_api_access",
            "no_delete_path",
            "ansible_check_mode",
            "post.logout.redirect.uris",
            "OAUTH_CLIENT_SECRET",
        ):
            self.assertIn(value, self.plugin_text + self.tasks_text)
        for forbidden in ("ansible.builtin.uri", "ansible.builtin.command", "ansible.builtin.shell", "requests.", "urllib.request", "POST", "PUT", "PATCH", "DELETE"):
            self.assertNotIn(forbidden, self.plugin_text)
        self.assertNotIn("state: absent", self.tasks_text)
        self.assertNotIn("clientSecret:", self.source_text)

    def test_wrapper_playbook_and_runbook_are_non_passthrough(self) -> None:
        self.assertEqual(0o755, stat.S_IMODE(WRAPPER.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE(PLAYBOOK.stat().st_mode))
        self.assertEqual(0, subprocess.run(["/bin/sh", "-n", str(WRAPPER)]).returncode)
        for value in ("check", "--check", "--diff", "--limit crtxweb", "ENTRYPOINT=v1", "env -i", "ADMIN_TOKEN_FILE", "API_BASE_URL"):
            self.assertIn(value, self.wrapper_text)
        self.assertNotIn('exec "$@"', self.wrapper_text)
        for value in ("source-only", "cristexhub", "reactive-resume-dev", "exact callback", "post-logout", "never a wildcard", "disabled", "must never be deleted"):
            self.assertIn(value.lower(), self.runbook_text.lower())

    def test_policies_are_reconciled_to_exact_contract(self) -> None:
        rr = next(item for item in self.policy["clients"]["browser"] if item["id"] == "reactive-resume-dev")
        self.assertEqual("cristexhub", rr["realm"])
        self.assertEqual(["https://resume-dev.cristex-soft.com/"], rr["post_logout_redirect_uris"])
        self.assertEqual("disabled-rollback-only", rr["old_successor_client"]["status"])
        self.assertEqual("forbidden", rr["old_successor_client"]["deletion"])
        self.assertNotIn("*", json.dumps(rr))
        identity = self.arch["identity"]
        self.assertEqual(["https://resume-dev.cristex-soft.com/"], identity["selected_post_logout_redirects"])
        self.assertIn("keycloak-reactive-resume-dev-client", identity["clients"]["dev"]["source_contract"])
        self.assertNotIn("*", json.dumps(identity["clients"]["dev"]))
        self.assertIn("post-logout redirect", self.runbook_text)


if __name__ == "__main__":
    unittest.main()
