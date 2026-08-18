from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ansible/files/policies/shared-stateful-backup-architecture.yml"
RUNBOOK = ROOT / "runbooks/shared-stateful-backup-architecture.md"


class SharedStatefulBackupArchitectureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_text = POLICY.read_text()
        cls.policy = yaml.safe_load(cls.policy_text)
        cls.runbook_text = RUNBOOK.read_text()

    def test_policy_scope_and_status_are_exact(self) -> None:
        self.assertEqual(
            "cristex-shared-stateful-backup-v1", self.policy["policy_schema"]
        )
        self.assertEqual(
            "postgresql-keycloak-scheduler-active", self.policy["policy_status"]
        )
        self.assertEqual(
            {"postgresql", "mongodb", "rabbitmq"}, set(self.policy["services"])
        )
        self.assertEqual(
            "infisical-cloud", self.policy["service_credential_value_owner"]
        )

    def test_easy_operator_access_is_private_and_authenticated(self) -> None:
        access = self.policy["operator_access"]
        self.assertEqual("private-authenticated-only", access["scope"])
        self.assertEqual("metadata-only", access["catalog"])
        self.assertEqual(
            "service/consumer-or-purpose/timestamp", access["archive_layout"]
        )
        self.assertTrue(access["list_retrieve_verify_workflow_required"])
        self.assertTrue(access["redacted_status_required"])
        self.assertFalse(access["public_endpoint_allowed"])
        self.assertFalse(access["anonymous_share_allowed"])
        self.assertFalse(access["live_data_mount_allowed"])

    def test_copy_integrity_and_encryption_contract_is_fail_closed(self) -> None:
        archive = self.policy["archive_contract"]
        self.assertEqual("timestamped-immutable-copy", archive["copy_semantics"])
        self.assertEqual("copy-not-sync", archive["transfer_semantics"])
        self.assertTrue(archive["compression_required"])
        self.assertTrue(archive["encryption_required"])
        self.assertTrue(archive["independent_key_custody_required"])
        self.assertTrue(archive["checksum_manifest_required"])
        self.assertTrue(archive["integrity_verification_required"])
        self.assertTrue(archive["isolated_restore_required"])
        self.assertTrue(archive["separate_consumer_paths_required"])
        self.assertFalse(archive["destructive_mirror_allowed"])

    def test_google_drive_host_transfer_is_exactly_selected(self) -> None:
        destination = self.policy["destination"]
        self.assertEqual("google-drive", destination["direction"])
        self.assertEqual("approved-google-drive-host-transfer", destination["selection_status"])
        self.assertEqual("pinned-host-rclone-copy", destination["tool_direction"])
        self.assertEqual("1.71.1", str(destination["rclone_version"]))
        self.assertEqual(
            "417e3da236f3a12d292da4e7287d67b1df558b8c2b280d092e563958ed724be7",
            destination["linux_amd64_archive_sha256"],
        )
        self.assertEqual(
            "5409cb410e49903af3517654ccc65c89d89f9dc12d7a97b0e13e09a9be6dc74a",
            destination["linux_amd64_binary_sha256"],
        )
        self.assertEqual("rclone-1.71.1-and-age-1.2.1-installed", destination["host_install_status"])
        self.assertEqual("drive", destination["remote_identity"])
        self.assertEqual("cristexweb-recovery", destination["root_folder_identity"])
        self.assertEqual(
            "host-operator-secret-zero", destination["oauth_credential_owner"]
        )
        self.assertEqual(
            "interactive-host-authorization", destination["oauth_credential_source"]
        )
        self.assertFalse(destination["infisical_as_sole_oauth_source_allowed"])
        self.assertFalse(destination["credential_in_git_allowed"])
        self.assertFalse(destination["rclone_sync_allowed"])

    def test_service_recovery_semantics_are_distinct(self) -> None:
        services = self.policy["services"]
        self.assertEqual(
            "application-consistent-logical-dumps",
            services["postgresql"]["backup_method_direction"],
        )
        self.assertEqual(
            "application-consistent-logical-dumps",
            services["mongodb"]["backup_method_direction"],
        )
        rabbitmq = services["rabbitmq"]
        self.assertEqual("definitions-and-policies", rabbitmq["definitions_scope"])
        self.assertEqual(
            "non-authoritative-reconcilable-direction",
            rabbitmq["queued_message_disposition"],
        )
        self.assertTrue(rabbitmq["application_reconciliation_proof_required"])
        self.assertFalse(rabbitmq["definitions_only_claims_message_recovery"])

    def test_future_consumers_require_separate_paths_and_restore_evidence(self) -> None:
        admission = self.policy["future_consumer_admission"]
        self.assertEqual("reviewed-exact-policy-change", admission["mode"])
        self.assertFalse(admission["wildcard_or_dynamic_paths_allowed"])
        self.assertEqual(
            {
                "exact-service-and-consumer-or-purpose",
                "dedicated-archive-path",
                "retention-and-capacity-review",
                "integrity-check",
                "isolated-restore-plan",
                "rpo-rto-disposition",
                "policy-test-and-runbook-update",
            },
            set(admission["required_evidence"]),
        )

    def test_approved_schedule_profile_and_runtime_gates_are_exact(self) -> None:
        schedule = self.policy["schedule_and_retention"]
        self.assertEqual("daily", schedule["schedule"])
        self.assertEqual("14d", schedule["local_retention"])
        self.assertEqual("14d", schedule["off_node_retention"])
        self.assertEqual("24h", schedule["rpo"])
        self.assertEqual("4h", schedule["rto"])
        self.assertEqual("14d", self.policy["local_staging"]["retention"])
        self.assertEqual("/var/lib/cristexweb-backup", self.policy["local_staging"]["path"])
        gates = self.policy["promotion_gates"]
        for completed in (
            "backup_tool_host_install_completed",
            "destination_identity_accepted",
            "staging_capacity_and_path_accepted",
            "schedules_and_retention_accepted",
            "encryption_key_recovery_proved",
            "integrity_verification_proved",
            "isolated_postgresql_restore_proved",
            "isolated_mongodb_restore_proved",
            "operator_retrieval_workflow_proved",
            "runtime_approved",
        ):
            self.assertTrue(gates[completed])
        for pending in set(gates) - {
            "backup_tool_host_install_completed",
            "destination_identity_accepted",
            "staging_capacity_and_path_accepted",
            "schedules_and_retention_accepted",
            "encryption_key_recovery_proved",
            "integrity_verification_proved",
            "isolated_postgresql_restore_proved",
            "isolated_mongodb_restore_proved",
            "operator_retrieval_workflow_proved",
            "runtime_approved",
        }:
            self.assertFalse(gates[pending])
        self.assertTrue(self.policy["executable_source_allowed"])

    def test_runbook_and_policy_are_value_free_and_private(self) -> None:
        normalized = " ".join(self.runbook_text.split())
        for required in (
            "POSTGRESQL KEYCLOAK SCHEDULER ACTIVE",
            "Easy access means private authenticated operator retrieval",
            "metadata-only catalog",
            "pinned host `rclone 1.71.1`",
            "rclone copy",
            "never `rclone sync`",
            "definitions recovery is not queued-message recovery",
            "isolated restore",
            "No CronJob, Job, PVC, Kubernetes Secret, Service, or public download endpoint",
        ):
            self.assertIn(required, normalized)
        combined = f"{self.policy_text}\n{self.runbook_text}"
        self.assertNotIn("containerized-rclone", combined)
        self.assertNotIn("containerized `rclone", combined)
        self.assertIn("host-operator-secret-zero", combined)
        for pattern in (
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"\b(?:https?|s3)://[^\s]+:[^\s]+@",
            r"\b(?:10|127|192\.168)\.(?:\d{1,3}\.){2}\d{1,3}\b",
            r"/Users/[^/\s]+/",
        ):
            self.assertNotRegex(combined, pattern)
        self.assertNotRegex(
            combined,
            r"(?im)^\s*(?:password|token|secret|api_key|credentials?)\s*:\s*\S+",
        )


if __name__ == "__main__":
    unittest.main()
