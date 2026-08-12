from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "ansible/files/components/infisical-keycloak-secrets"


class InfisicalKeycloakSecretsContractTests(unittest.TestCase):
    def test_manifest_ledger_matches_all_component_leaves(self) -> None:
        ledger = COMPONENT / "MANIFESTS.sha256"
        entries = {}
        for line in ledger.read_text().splitlines():
            digest, relative = line.split("  ", 1)
            entries[relative] = digest
        leaves = sorted(
            path.relative_to(COMPONENT).as_posix()
            for path in COMPONENT.rglob("*.yaml")
        )
        self.assertEqual(sorted(entries), leaves)
        for relative, expected in entries.items():
            actual = hashlib.sha256((COMPONENT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)

    def test_exact_value_free_source_and_target_contract(self) -> None:
        source = yaml.safe_load(
            (COMPONENT / "source/keycloak-infisical-secrets.yaml").read_text()
        )
        self.assertEqual(source["metadata"]["namespace"], "shared-services")
        self.assertEqual(source["spec"]["sources"], [{
            "projectId": "619656da-14f3-4872-857b-be103cdc5326",
            "environmentSlug": "prod",
            "secretPath": "/shared-services/keycloak",
            "recursive": False,
            "tagSlugs": [],
        }])
        targets = source["spec"]["targets"]
        self.assertEqual(len(targets), 1)
        target = targets[0]
        self.assertEqual(target["name"], "keycloak-bootstrap-admin")
        self.assertEqual(target["secretType"], "Opaque")
        self.assertEqual(target["creationPolicy"], "Orphan")
        self.assertEqual(sorted(target["template"]["data"]), ["password", "username"])
        self.assertNotRegex(
            (COMPONENT / "source/keycloak-infisical-secrets.yaml").read_text(),
            r"(?:password|username):\s*[^'{\s][^\n]*",
        )

    def test_exact_admission_and_rbac_closure(self) -> None:
        policies = [
            yaml.safe_load(path.read_text())
            for path in (COMPONENT / "admission").glob("*.yaml")
            if "binding" not in path.name
        ]
        bindings = [
            yaml.safe_load(path.read_text())
            for path in (COMPONENT / "admission").glob("*-binding.yaml")
        ]
        self.assertEqual(len(policies), 4)
        self.assertEqual(len(bindings), 4)
        self.assertEqual(
            {policy["kind"] for policy in policies},
            {"ValidatingAdmissionPolicy"},
        )
        self.assertEqual(
            {tuple(binding["spec"]["validationActions"]) for binding in bindings},
            {("Deny",)},
        )
        self.assertEqual(
            {policy["spec"]["failurePolicy"] for policy in policies},
            {"Fail"},
        )
        role = yaml.safe_load(
            (COMPONENT / "rbac/keycloak-secret-writer-role.yaml").read_text()
        )
        secret_rules = [rule for rule in role["rules"] if "secrets" in rule["resources"]]
        self.assertIn("keycloak-bootstrap-admin", secret_rules[1]["resourceNames"])
        self.assertNotIn("delete", {verb for rule in secret_rules for verb in rule["verbs"]})
        binding = yaml.safe_load(
            (COMPONENT / "rbac/keycloak-secret-writer-rolebinding.yaml").read_text()
        )
        self.assertEqual(binding["roleRef"]["name"], "infisical-keycloak-secret-writer")


if __name__ == "__main__":
    unittest.main()
