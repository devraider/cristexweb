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
            "successor with no administrator tag",
            "predecessor remains untouched until all successor",
            "restart behavior is unproven",
            "Do not assume the overlap survives",
            "Old-user revocation",
            "authorization denial",
            "does **not** prove authentication revocation",
            "fail authentication",
        ):
            self.assertIn(phrase, self.normalized)

    def test_celery_permission_contract_is_unproven_until_live_probe(self) -> None:
        for phrase in (
            "Candidate permission contract — not yet proven",
            "Exact Celery exchange, queue, reply, event, and pidbox resource names",
            "UNPROVEN",
            "live positive/negative probe",
            "permission acceptance is **NOT RUN / BLOCKED**",
            "candidate table becomes a contract only after that live probe",
        ):
            self.assertIn(phrase, self.normalized)
        self.assertIn("candidate value", self.runbook)
        self.assertNotIn("Both the successor during overlap and the predecessor", self.runbook)

    def test_writer_cas_and_partial_state_are_explicitly_unavailable(self) -> None:
        for phrase in (
            "ABSENT / NOT IMPLEMENTED",
            "no dedicated rotation identity",
            "no proven concurrency/CAS protocol",
            "writer and CAS unavailable",
            "expected revision/conditional write",
            "does not establish atomicity or CAS",
            "Cross-system rotation is **NOT ATOMIC**",
            "partial or mixed state",
            "ambiguous response is `UNKNOWN-STOP`",
            "no predecessor URL/password is read, reconstructed, or presumed",
            "rollback unavailable and stop",
        ):
            self.assertIn(phrase, self.normalized)

    def test_backup_restore_and_message_recovery_are_blocked(self) -> None:
        for phrase in (
            "definitions backup/readback and isolated definitions restore are currently",
            "isolated_rabbitmq_definitions_restore_proved: false",
            "rabbitmq_message_reconciliation_proved: false",
            "No queued-message recovery",
            "hard preconditions",
        ):
            self.assertIn(phrase, self.normalized)
        self.assertIn("A fresh encrypted RabbitMQ definitions/policies backup", self.normalized)

    def test_exact_permissions_are_not_wildcarded(self) -> None:
        for value in EXACT_PERMISSIONS.values():
            self.assertIn(value, self.runbook)
            self.assertNotIn(".*", value)
            self.assertNotIn("[^*]", value)
        self.assertIn("No wildcard or broader pattern is allowed", self.normalized)
        self.assertIn("candidate table becomes a contract", self.normalized)

    def test_application_cutover_is_infisical_owned_and_bounded(self) -> None:
        for phrase in (
            "Operator remains the Kubernetes Secret value owner",
            "never write",
            "derived `RABBITMQ_URL`",
            "protected PROD backend and Celery",
            "predecessor active during this overlap window",
            "preservation of unrelated keys",
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

    def test_check_only_lane_is_separate_and_runtime_mutation_free(self) -> None:
        for relative in (
            "ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation",
            "ansible/playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml",
            "ansible/roles/rabbitmq_prod_credential_rotation_check/defaults/main.yml",
            "ansible/roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml",
            "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py",
            "ansible/library/rabbitmq_prod_credential_metadata.py",
            "ansible/files/policies/cristexhub-prod-rabbitmq-credential-rotation.yml",
        ):
            self.assertTrue((ROOT / relative).exists(), relative)
        for forbidden in (
            "kubectl apply",
            "kubectl delete",
            "rabbitmqctl add_user",
            "rabbitmqctl delete_user",
            "rabbitmqctl set_permissions",
            "rabbitmqctl delete_user",
        ):
            for path in (
                ROOT / "ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation",
                ROOT / "ansible/playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml",
                ROOT / "ansible/roles/rabbitmq_prod_credential_rotation_check",
                ROOT / "ansible/plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py",
            ):
                if path.is_file():
                    self.assertNotIn(forbidden, path.read_text())
                else:
                    self.assertFalse(any(forbidden in child.read_text() for child in path.rglob("*" ) if child.is_file()))
        self.assertIn("SOURCE_ONLY_STOP", self.runbook.upper().replace("-", "_"))
        self.assertIn("metadata-only", self.normalized)
        self.assertIn("source-only design / not run / blocked", self.normalized.lower())


if __name__ == "__main__":
    unittest.main()
