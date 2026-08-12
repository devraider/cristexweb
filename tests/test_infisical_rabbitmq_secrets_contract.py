from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "ansible/files/components/infisical-rabbitmq-secrets"
TARGETS = {
    "rabbitmq-admin": ("Opaque", {"username", "password", "passwordHash"}),
    "rabbitmq-tls": ("kubernetes.io/tls", {"ca.crt", "tls.crt", "tls.key"}),
    "rabbitmq-cristexhub-dev": ("Opaque", {"username", "password", "passwordHash"}),
    "rabbitmq-cristexhub-prod": ("Opaque", {"username", "password", "passwordHash"}),
}


class InfisicalRabbitMqSecretsContractTests(unittest.TestCase):
    def test_manifest_ledger_matches_all_component_leaves(self) -> None:
        entries = {}
        for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines():
            digest, relative = line.split("  ", 1)
            entries[relative] = digest
        leaves = sorted(p.relative_to(COMPONENT).as_posix() for p in COMPONENT.rglob("*.yaml"))
        self.assertEqual(leaves, sorted(entries))
        for relative, expected in entries.items():
            self.assertEqual(expected, hashlib.sha256((COMPONENT / relative).read_bytes()).hexdigest(), relative)

    def test_exact_source_and_four_secret_targets(self) -> None:
        source_path = COMPONENT / "source/rabbitmq-infisical-secrets.yaml"
        source = yaml.safe_load(source_path.read_text())
        self.assertEqual(source["metadata"]["namespace"], "shared-services")
        self.assertEqual(source["spec"]["sources"], [{
            "projectId": "619656da-14f3-4872-857b-be103cdc5326",
            "environmentSlug": "prod",
            "secretPath": "/shared-services/rabbitmq",
            "recursive": False,
            "tagSlugs": [],
        }])
        targets = {target["name"]: target for target in source["spec"]["targets"]}
        self.assertEqual(set(TARGETS), set(targets))
        for name, (secret_type, keys) in TARGETS.items():
            target = targets[name]
            self.assertEqual(secret_type, target["secretType"])
            self.assertEqual("Orphan", target["creationPolicy"])
            self.assertEqual(keys, set(target["template"]["data"]))
            self.assertEqual("shared-rabbitmq", target["metadata"]["labels"]["app.kubernetes.io/part-of"])
        self.assertNotRegex(source_path.read_text(), r"(?:password|username|tls\.key):\s*[^'{\s][^\n]*")

    def test_admission_and_rbac_are_exact_and_deny_first(self) -> None:
        policies = [yaml.safe_load(p.read_text()) for p in (COMPONENT / "admission").glob("*.yaml") if "binding" not in p.name]
        bindings = [yaml.safe_load(p.read_text()) for p in (COMPONENT / "admission").glob("*-binding.yaml")]
        self.assertEqual(4, len(policies)); self.assertEqual(4, len(bindings))
        self.assertTrue(all(p["spec"]["failurePolicy"] == "Fail" for p in policies))
        self.assertTrue(all(tuple(b["spec"]["validationActions"]) == ("Deny",) for b in bindings))
        role = yaml.safe_load((COMPONENT / "rbac/rabbitmq-secret-writer-role.yaml").read_text())
        rules = [r for r in role["rules"] if "secrets" in r["resources"]]
        self.assertEqual(set(TARGETS), set(rules[1]["resourceNames"]))
        self.assertNotIn("delete", {verb for r in rules for verb in r["verbs"]})
        self.assertNotIn("patch", {verb for r in rules for verb in r["verbs"]})


if __name__ == "__main__":
    unittest.main()
