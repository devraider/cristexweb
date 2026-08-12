from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
KUBERNETES = ROOT / "kubernetes"
POLICY = ANSIBLE / "files/policies/shared-rabbitmq-architecture.yml"
RUNBOOK = ROOT / "runbooks/shared-rabbitmq-architecture.md"
BACKUP_POLICY = "ansible/files/policies/shared-stateful-backup-architecture.yml"


class SharedRabbitMqArchitectureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_text = POLICY.read_text()
        cls.policy = yaml.safe_load(cls.policy_text)
        cls.runbook_text = RUNBOOK.read_text()

    def test_exact_engine_placement_and_consumer_closure(self) -> None:
        self.assertEqual("cristex-shared-rabbitmq-v1", self.policy["policy_schema"])
        self.assertEqual(
            "source-selected-runtime-blocked", self.policy["policy_status"]
        )
        self.assertEqual("shared-services", self.policy["namespace"])
        engine = self.policy["engine"]
        self.assertEqual(1, engine["instance_count"])
        self.assertEqual("one-shared-engine", engine["model"])
        self.assertEqual("shared-services", engine["namespace"])
        self.assertEqual(
            {"cristexhub-dev", "cristexhub-prod"}, set(engine["consumers"])
        )

    def test_consumers_have_dedicated_value_free_isolation_scopes(self) -> None:
        for consumer in self.policy["engine"]["consumers"].values():
            self.assertTrue(consumer["vhost"].startswith("/cristexhub-"))
            self.assertTrue(consumer["principal"].startswith("cristexhub_"))
            self.assertEqual("infisical-cloud", consumer["credential_value_owner"])
            self.assertEqual("dedicated-vhost-only", consumer["permissions_scope"])
            self.assertEqual("dedicated", consumer["limits_scope"])
            self.assertEqual("dedicated", consumer["recovery_scope"])

    def test_future_consumers_require_reviewed_exact_admission(self) -> None:
        admission = self.policy["future_consumer_admission"]
        self.assertEqual("reviewed-exact-policy-change", admission["mode"])
        self.assertFalse(admission["wildcard_or_dynamic_consumers_allowed"])
        self.assertEqual(
            {
                "exact-consumer-identifier",
                "dedicated-vhost",
                "dedicated-principal-and-infisical-credential",
                "dedicated-permissions-and-limits",
                "capacity-review",
                "negative-cross-vhost-tests",
                "backup-and-recovery-disposition",
                "policy-test-and-runbook-update",
            },
            set(admission["required_evidence"]),
        )

    def test_authorization_and_management_are_deny_first(self) -> None:
        authorization = self.policy["authorization"]
        self.assertEqual("deny", authorization["cross_vhost_access_default"])
        self.assertEqual("deny", authorization["workload_user_administration"])
        self.assertEqual("deny", authorization["workload_vhost_administration"])
        self.assertEqual("deny", authorization["workload_policy_administration"])
        self.assertEqual("disabled", authorization["default_guest_access"])
        self.assertEqual("private-only", authorization["management_access"])
        self.assertEqual(
            {
                "dev-user-to-prod-vhost",
                "prod-user-to-dev-vhost",
                "workload-user-administration",
                "workload-vhost-administration",
                "workload-policy-administration",
                "public-management-access",
            },
            set(authorization["required_negative_tests"]),
        )

    def test_backup_and_message_recovery_boundaries_are_explicit(self) -> None:
        backup = self.policy["backup_and_restore"]
        self.assertEqual(BACKUP_POLICY, backup["policy_path"])
        self.assertEqual("definitions-and-policies", backup["definitions_scope"])
        self.assertEqual(
            "non-authoritative-reconcilable-direction",
            backup["queued_message_disposition"],
        )
        self.assertTrue(backup["application_reconciliation_proof_required"])
        self.assertFalse(backup["definitions_restore_proved"])
        self.assertFalse(backup["message_reconciliation_proved"])

    def test_source_storage_network_and_runtime_gates_remain_blocked(self) -> None:
        source = self.policy["engine"]["source"]
        self.assertEqual("official-docker-image", source["selection"])
        self.assertEqual("docker.io/library/rabbitmq", source["repository"])
        self.assertEqual("4.3.4-management", source["version"])
        self.assertEqual("sha256:cd4fd60136781671d125ed68ac4b67900c0726b55e2e8b98719daa616a63240b", source["linux_amd64_digest"])
        self.assertTrue(source["trust_accepted"])
        self.assertEqual("direct-single-node-statefulset", self.policy["engine"]["topology"])
        self.assertEqual("local-path", self.policy["storage"]["storage_class"])
        self.assertEqual("20Gi", self.policy["storage"]["capacity"])
        self.assertEqual("cluster-internal-only", self.policy["exposure"]["future_scope"])
        self.assertEqual("shared-rabbitmq-amqps", self.policy["exposure"]["service_identity"])
        self.assertEqual(5671, self.policy["exposure"]["amqp_port"])
        self.assertEqual(15671, self.policy["exposure"]["management_port"])
        self.assertTrue(self.policy["promotion_gates"]["immutable_source_selected"])
        self.assertFalse(self.policy["promotion_gates"]["runtime_approved"])
        self.assertFalse(self.policy["executable_source_allowed"])

    def test_runbook_preserves_private_policy_only_boundaries(self) -> None:
        normalized = " ".join(self.runbook_text.split())
        for required in (
            "SOURCE SELECTED — RUNTIME BLOCKED",
            "one shared RabbitMQ engine",
            "dedicated vhost",
            "future consumer",
            "reviewed exact policy change",
            "definitions recovery is not queued-message recovery",
            "private authenticated operator access",
            "No StatefulSet, Deployment, Service, PVC, Secret, Job, CronJob, or NetworkPolicy",
        ):
            self.assertIn(required, normalized)

    def test_policy_is_value_free_and_adds_no_executable_source(self) -> None:
        combined = f"{self.policy_text}\n{self.runbook_text}"
        for pattern in (
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"\b(?:amqps?|https?)://[^\s]+:[^\s]+@",
            r"\b(?:10|127|192\.168)\.(?:\d{1,3}\.){2}\d{1,3}\b",
            r"/Users/[^/\s]+/",
        ):
            self.assertNotRegex(combined, pattern)
        self.assertNotRegex(
            combined,
            r"(?im)^\s*(?:password|token|secret|api_key|credentials?)\s*:\s*\S+",
        )
        self.assertEqual(
            {
                "platform/namespaces/argocd.yaml",
                "platform/namespaces/platform-edge.yaml",
                "platform/namespaces/shared-services.yaml",
                "applications/namespaces/cristexhub-dev.yaml",
            },
            {
                str(path.relative_to(KUBERNETES))
                for path in KUBERNETES.rglob("*")
                if path.is_file()
            },
        )
        operational = [
            path
            for root in (ANSIBLE / "bin", ANSIBLE / "playbooks", ANSIBLE / "roles")
            for path in root.rglob("*")
            if path.is_file()
        ]
        allowed = {
            "ansible/bin/configure-rabbitmq-definitions-backup",
            "ansible/playbooks/configure_rabbitmq_definitions_backup.yml",
        }
        actual = {
            str(path.relative_to(ROOT))
            for path in operational
            if "rabbit" in path.name.lower()
        }
        self.assertEqual(allowed, actual)


if __name__ == "__main__":
    unittest.main()
