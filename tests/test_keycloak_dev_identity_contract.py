from __future__ import annotations

import hashlib
import json
import re
import stat
import unittest
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/keycloak-dev-identity"
DEFAULTS = ROOT / "ansible/roles/keycloak_dev_identity_bootstrap/defaults/main.yml"
TASKS = ROOT / "ansible/roles/keycloak_dev_identity_bootstrap/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/keycloak_dev_identity_guarded.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-keycloak-dev-identity"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_keycloak_dev_identity.yml"
RUNBOOK = ROOT / "runbooks/keycloak-dev-realm-migration.md"
POLICY = ROOT / "ansible/files/policies/hosted-identity-authorization.yml"


class KeycloakDevIdentityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.leaves = sorted(path for path in COMPONENT.rglob("*.yaml"))
        cls.documents = [yaml.safe_load(path.read_text()) for path in cls.leaves]
        cls.by_kind = {document["kind"]: document for document in cls.documents}
        cls.defaults = yaml.safe_load(DEFAULTS.read_text())
        cls.plugin_text = PLUGIN.read_text()
        cls.tasks_text = TASKS.read_text()
        cls.wrapper_text = WRAPPER.read_text()
        cls.runbook_text = RUNBOOK.read_text()
        cls.policy = yaml.safe_load(POLICY.read_text())

    def test_exact_value_free_source_closure_and_hash_ledger(self) -> None:
        self.assertEqual(4, len(self.leaves))
        self.assertEqual(
            {
                "KeycloakRealmContract",
                "KeycloakClientContract",
                "KeycloakStaticGroupContract",
                "KeycloakProtocolMapperContract",
            },
            set(self.by_kind),
        )
        self.assertEqual(
            {
                "cristexhub-dev",
                "cristexhub-dev-clients",
                "cristexhub-dev-static-groups",
                "cristexhub-dev-claims",
            },
            {document["metadata"]["name"] for document in self.documents},
        )
        expected_hashes = {
            entry["path"].split("}}/", 1)[-1]: entry["sha256"]
            for entry in self.defaults["keycloak_dev_identity_bootstrap_expected_hashes"]
        }
        for path in self.leaves:
            self.assertEqual(0o644, stat.S_IMODE(path.stat().st_mode), path)
            relative = str(path.relative_to(ROOT / "ansible"))
            # Defaults contain a component-root expression; compare by leaf path.
            suffix = str(path.relative_to(COMPONENT))
            matching = next(
                entry
                for entry in self.defaults["keycloak_dev_identity_bootstrap_expected_hashes"]
                if suffix in entry["path"]
            )
            self.assertEqual(
                matching["sha256"], hashlib.sha256(path.read_bytes()).hexdigest(), relative
            )
        ledger = (COMPONENT / "MANIFESTS.sha256").read_text()
        self.assertNotIn("REPLACE_", DEFAULTS.read_text())
        self.assertEqual(4, len([line for line in ledger.splitlines() if line.strip()]))

    def test_realm_client_groups_and_mappers_are_dev_only(self) -> None:
        realm = self.by_kind["KeycloakRealmContract"]["spec"]
        self.assertEqual("cristexhub-dev", realm["realm"])
        self.assertEqual(
            "https://auth.cristex-soft.com/realms/cristexhub-dev", realm["issuer"]
        )
        self.assertEqual("cristexhub", realm["legacyRealm"]["name"])
        self.assertEqual("forbidden", realm["legacyRealm"]["mutation"])
        clients = self.by_kind["KeycloakClientContract"]["spec"]["clients"]
        self.assertEqual(
            ["cristexhub-dev", "cristexhub-admin-svc-dev"],
            [client["clientId"] for client in clients],
        )
        browser, service = clients
        self.assertEqual(
            ["https://dev-hub.cristex-soft.com/oauth2/callback"], browser["redirectUris"]
        )
        self.assertEqual(["https://dev-hub.cristex-soft.com"], browser["webOrigins"])
        self.assertEqual("S256", browser["attributes"]["pkce.code.challenge.method"])
        self.assertFalse(service["bearerOnly"])
        self.assertFalse(service["standardFlowEnabled"])
        self.assertTrue(service["serviceAccountsEnabled"])
        self.assertEqual(
            ["cristexhub-dev-super-admin"],
            [group["name"] for group in self.by_kind["KeycloakStaticGroupContract"]["spec"]["groups"]],
        )
        self.assertEqual(
            ["groups", "organization", "cristexhub-dev-audience"],
            [mapper["name"] for mapper in self.by_kind["KeycloakProtocolMapperContract"]["spec"]["mappers"]],
        )
        source = json.dumps(self.documents, sort_keys=True)
        self.assertNotRegex(source, r'(?i)"(?:password|secret|token|clientSecret|privateKey)"\s*:')
        self.assertNotIn("cristexhub-prod", [client["clientId"] for client in clients])
        self.assertNotIn("cristexhub-prod", [group["name"] for group in self.by_kind["KeycloakStaticGroupContract"]["spec"]["groups"]])
        self.assertNotIn("argocd-admin", [group["name"] for group in self.by_kind["KeycloakStaticGroupContract"]["spec"]["groups"]])

    def test_guard_is_check_only_and_read_only(self) -> None:
        self.assertIn('module_name="ansible.builtin.uri"', self.plugin_text)
        self.assertIn('"method": "GET"', self.plugin_text)
        self.assertNotIn('"method": "POST"', self.plugin_text)
        self.assertNotIn('"method": "PUT"', self.plugin_text)
        self.assertNotIn('"method": "PATCH"', self.plugin_text)
        self.assertNotIn('"method": "DELETE"', self.plugin_text)
        self.assertIn('not task_vars.get("ansible_check_mode")', self.plugin_text)
        self.assertIn("_LEGACY_REALM", self.plugin_text)
        self.assertIn("_FORBIDDEN_IDENTITIES", self.plugin_text)
        self.assertIn("_EXPECTED_DEFINITION_HASHES", self.plugin_text)
        self.assertIn("no_delete_path", self.tasks_text)
        self.assertIn("check_only", self.tasks_text)
        self.assertNotIn("ansible.builtin.command", self.tasks_text)
        self.assertNotIn("ansible.builtin.shell", self.tasks_text)

    def test_wrapper_is_non_passthrough_and_does_not_carry_secret_values(self) -> None:
        self.assertRegex(self.wrapper_text, r"usage=.*bootstrap-keycloak-dev-identity check")
        self.assertIn("[ \"$1\" = check ]", self.wrapper_text)
        self.assertIn("--check", self.wrapper_text)
        self.assertIn("--diff", self.wrapper_text)
        self.assertIn("CRISTEXWEB_KEYCLOAK_DEV_IDENTITY_ADMIN_TOKEN_FILE", self.wrapper_text)
        self.assertIn("CRISTEXWEB_KEYCLOAK_DEV_IDENTITY_ENTRYPOINT=v1", self.wrapper_text)
        self.assertNotIn('mode=$1', self.wrapper_text)
        self.assertNotRegex(self.wrapper_text, r"\b(?:password|secret|token)=\$")
        self.assertIn("role: keycloak_dev_identity_bootstrap", PLAYBOOK.read_text())
        self.assertIn("hosts: crtxweb", PLAYBOOK.read_text())

    def test_policy_and_runbook_preserve_legacy_prod_and_block_activation(self) -> None:
        transition = self.policy["realm_transition"]
        self.assertEqual("cristexhub", transition["legacy_prod"]["name"])
        self.assertEqual("forbidden", transition["legacy_prod"]["mutation"])
        self.assertEqual("cristexhub-dev", transition["successor_dev"]["name"])
        self.assertEqual("present-update-only", transition["successor_dev"]["mutation"])
        self.assertEqual("forbidden", transition["successor_dev"]["deletion"])
        self.assertEqual("blocked", transition["successor_dev"]["runtime_activation"])
        for required in (
            "SOURCE-ONLY / CHECK-ONLY / NOT RUN",
            "existing `cristexhub` realm and\nissuer remain the retained PROD-compatibility identity:",
            "The wrapper rejects `apply`",
            "four hash-bound, value-free source leaves",
            "reports absent or differing DEV state as predicted change without issuing a\n   write request.",
            "identity-preservation-review",
            "Cross-environment negative tests must prove PROD tokens cannot authenticate to DEV",
        ):
            self.assertIn(required, self.runbook_text)


if __name__ == "__main__":
    unittest.main()
