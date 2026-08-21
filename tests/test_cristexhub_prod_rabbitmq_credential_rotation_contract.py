from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "runbooks/cristexhub-prod-rabbitmq-credential-rotation.md"
SOURCE = ROOT / "ansible/files/components/infisical-rabbitmq-secrets/source/rabbitmq-infisical-secrets.yaml"

EXACT_PERMISSIONS = {
    "configure": "^(default|high_priority|low_priority)$",
    "write": "^default$",
    "read": "^(default|high_priority|low_priority)$",
}


class CristexHubProdRabbitMqCredentialRotationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runbook = RUNBOOK.read_text()
        cls.normalized = " ".join(cls.runbook.split())
        cls.source = yaml.safe_load(SOURCE.read_text())

    def test_design_scope_and_execution_state_are_exact(self) -> None:
        for phrase in (
            "SOURCE-ONLY DESIGN / NOT RUN / BLOCKED",
            "broker Namespace: `shared-services`",
            "vhost: `/cristexhub-prod`",
            "environment `prod`, path `/shared-services/rabbitmq`",
            "shared-rabbitmq-cristexhub-prod",
            "`/cristexhub/prod/runtime`, key `RABBITMQ_URL`",
            "cristexhub-prod/backend",
            "cristexhub-prod/celery-worker",
            "UNKNOWN-STOP",
            "runtime mutation",
        ):
            self.assertIn(phrase, self.normalized)

    def test_successor_overlap_and_revocation_contract(self) -> None:
        for phrase in (
            "canonical successor identity is the exact",
            "cristexhub_prod_rabbitmq",
            "must be absent before the rotation begins",
            "successor during overlap",
            "predecessor remains untouched until all successor",
            "Retain the predecessor with its exact permission",
            "Old-user revocation",
            "remove the predecessor's vhost permissions",
            "authentication fails",
        ):
            self.assertIn(phrase, self.normalized)

    def test_exact_permissions_are_not_wildcarded(self) -> None:
        for value in EXACT_PERMISSIONS.values():
            self.assertIn(value, self.runbook)
            self.assertNotIn(".*", value)
            self.assertNotIn("[^*]", value)
        self.assertIn("No wildcard or broader pattern is allowed", self.normalized)
        self.assertIn("exact permission contract", self.normalized)

    def test_application_cutover_is_infisical_owned_and_bounded(self) -> None:
        for phrase in (
            "Operator remains the Kubernetes Secret value owner",
            "never write",
            "derived `RABBITMQ_URL`",
            "protected PROD backend and Celery",
            "predecessor active during this overlap window",
            "Preserve every unrelated runtime key",
        ):
            self.assertIn(phrase, self.normalized)

    def test_source_target_contract_is_existing_and_value_free(self) -> None:
        self.assertEqual("/shared-services/rabbitmq", self.source["spec"]["sources"][0]["secretPath"])
        targets = {item["name"]: item for item in self.source["spec"]["targets"]}
        target = targets["shared-rabbitmq-cristexhub-prod"]
        self.assertEqual("Opaque", target["secretType"])
        self.assertEqual(
            {"username", "password", "passwordHash"},
            set(target["template"]["data"]),
        )
        self.assertNotRegex(self.runbook, r"(?i)(?:password|secret|token)\s*[:=]\s*[^`\s{][^\n]*")
        self.assertNotRegex(self.runbook, r"(?:amqps?|rabbitmq)://[^\s/]+:[^\s@]+@")
        self.assertNotIn("BEGIN", self.runbook)
        self.assertNotIn("eyJ", self.runbook)

    def test_no_executable_rotation_lane_or_runtime_mutation_was_added(self) -> None:
        # The requested change is a design contract only. These are deliberately
        # absent; implementation requires a later, separately approved closure.
        for relative in (
            "ansible/bin/rotate-rabbitmq-cristexhub-prod",
            "ansible/roles/rabbitmq_prod_credential_rotation",
            "ansible/plugins/action/rabbitmq_prod_credential_rotation_guarded_k8s.py",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)
        for forbidden in (
            "kubectl apply",
            "kubectl delete",
            "rabbitmqctl add_user",
            "rabbitmqctl delete_user",
            "rabbitmqctl set_permissions",
            "ansible-playbook",
        ):
            self.assertNotIn(forbidden, self.runbook)
        for phrase in (
            "adds no executable",
            "performs no runtime mutation",
            "this runbook adds",
            "source-only design / not run / blocked",
        ):
            self.assertIn(phrase.lower(), self.normalized.lower())


if __name__ == "__main__":
    unittest.main()
