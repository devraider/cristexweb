from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ansible/files/policies/reactive-resume-postgresql-exposure-rotation.yml"
CORE_POLICY = ROOT / "ansible/files/policies/reactive-resume-architecture.yml"
RUNBOOK = ROOT / "runbooks/reactive-resume-postgresql-exposure-rotation.md"
CNPG_SOURCE = ROOT / "ansible/files/components/cloudnative-pg/cluster/shared-postgresql.yaml"

EXPECTED_SOURCE_KEYS = {
    "POSTGRESQL_ADMIN_USERNAME",
    "POSTGRESQL_ADMIN_PASSWORD",
    "POSTGRESQL_TLS_CA_CRT",
    "POSTGRESQL_TLS_CRT",
    "POSTGRESQL_TLS_KEY",
    "POSTGRESQL_CRISTEXHUB_DEV_USERNAME",
    "POSTGRESQL_CRISTEXHUB_DEV_PASSWORD",
    "POSTGRESQL_CRISTEXHUB_PROD_USERNAME",
    "POSTGRESQL_CRISTEXHUB_PROD_PASSWORD",
    "POSTGRESQL_REACTIVE_RESUME_DEV_USERNAME",
    "POSTGRESQL_REACTIVE_RESUME_DEV_PASSWORD",
    "POSTGRESQL_REACTIVE_RESUME_PROD_USERNAME",
    "POSTGRESQL_REACTIVE_RESUME_PROD_PASSWORD",
    "POSTGRESQL_KEYCLOAK_USERNAME",
    "POSTGRESQL_KEYCLOAK_PASSWORD",
}

EXPECTED_CONSUMERS = {
    "dev": {
        "logical_database": "reactive_resume_dev",
        "database_role": "reactive_resume_dev_owner",
        "database_role_resource": "reactive-resume-dev-owner",
        "credential_secret": "shared-postgresql-reactive-resume-dev",
        "source_username_key": "POSTGRESQL_REACTIVE_RESUME_DEV_USERNAME",
        "source_password_key": "POSTGRESQL_REACTIVE_RESUME_DEV_PASSWORD",
    },
    "prod": {
        "logical_database": "reactive_resume_prod",
        "database_role": "reactive_resume_prod_owner",
        "database_role_resource": "reactive-resume-prod-owner",
        "credential_secret": "shared-postgresql-reactive-resume-prod",
        "source_username_key": "POSTGRESQL_REACTIVE_RESUME_PROD_USERNAME",
        "source_password_key": "POSTGRESQL_REACTIVE_RESUME_PROD_PASSWORD",
    },
}

FORBIDDEN_LANE_PATHS = {
    "ansible/bin/upload-infisical-bootstrap-values",
    "ansible/bin/provision-shared-postgresql",
    "ansible/playbooks/bootstrap_cloudnative_pg_cluster.yml",
    "ansible/files/components/infisical-database-secrets/source/shared-postgresql-infisical-secrets.yaml",
    "ansible/files/components/cloudnative-pg/cluster/shared-postgresql.yaml",
    "ansible/plugins/action/database_provisioning_guarded_exec.py",
    "ansible/plugins/action/database_provisioning_guarded_k8s.py",
}


class ReactiveResumePostgresqlExposureRotationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_text = POLICY.read_text()
        cls.policy = yaml.safe_load(cls.policy_text)
        cls.core_policy = yaml.safe_load(CORE_POLICY.read_text())
        cls.runbook_text = RUNBOOK.read_text()

    def test_scope_is_exact_two_consumer_same_principal_password_rotation(self) -> None:
        self.assertEqual(
            "cristex-reactive-resume-postgresql-exposure-rotation-v1",
            self.policy["policy_schema"],
        )
        self.assertEqual("source-only-design-not-run-blocked", self.policy["policy_status"])
        self.assertFalse(self.policy["executable_source_allowed"])
        self.assertFalse(self.policy["apply_capable"])
        self.assertFalse(self.policy["runtime_mutation_allowed"])
        self.assertEqual("cristexweb-infrastructure", self.policy["scope"]["project_slug"])
        self.assertEqual("619656da-14f3-4872-857b-be103cdc5326", self.policy["scope"]["project_id"])
        self.assertEqual("prod", self.policy["scope"]["environment_slug"])
        self.assertEqual("/shared-services/postgresql", self.policy["scope"]["secret_path"])
        self.assertEqual(15, self.policy["scope"]["source_key_count"])
        self.assertEqual(EXPECTED_SOURCE_KEYS, set(self.policy["scope"]["exact_source_keys"]))
        self.assertEqual(15, len(self.policy["scope"]["exact_source_keys"]))
        self.assertEqual("forbidden", self.policy["scope"]["extra_source_keys"])
        self.assertEqual("forbidden", self.policy["scope"]["missing_source_keys"])
        self.assertEqual("one-environment-per-approved-invocation", self.policy["scope"]["rotation_concurrency"])
        self.assertEqual("forbidden", self.policy["scope"]["simultaneous_dev_prod_rotation"])

        for environment, expected in EXPECTED_CONSUMERS.items():
            consumer = self.policy["consumers"][environment]
            for key, value in expected.items():
                self.assertEqual(value, consumer[key], f"{environment}.{key}")
            self.assertEqual("shared-services", consumer["target_namespace"])
            self.assertEqual("Opaque", consumer["target_type"])
            self.assertEqual(["username", "password"], consumer["target_keys"])
            self.assertEqual("Orphan", consumer["target_creation_policy"])
            self.assertEqual("same-principal-new-password", consumer["password_successor_semantics"])
            self.assertTrue(consumer["database_role_name_is_immutable"])
            self.assertEqual("forbidden", consumer["username_change"])
            self.assertEqual("forbidden", consumer["new_role_or_user"])
            self.assertEqual("forbidden", consumer["role_delete_recreate"])
            self.assertEqual("forbidden", consumer["database_delete_recreate"])
            self.assertEqual("password-key-only", consumer["source_key_update_scope"])
            self.assertEqual(14, consumer["unrelated_source_keys_preserved"])
            self.assertEqual("required-after-successor-acceptance", consumer["predecessor_revocation"])

        self.assertEqual(
            "ansible/files/policies/reactive-resume-postgresql-exposure-rotation.yml",
            self.core_policy["postgresql_exposure_rotation_contract"],
        )

    def test_no_output_contract_forbids_values_and_allows_only_metadata(self) -> None:
        contract = self.policy["no_output_contract"]
        for key in (
            "source_preflight_metadata_only",
            "protected_predecessor_custody",
            "plaintext_residue_after_completion",
        ):
            self.assertTrue(contract[key], key)
        self.assertEqual("protected-cleanup-first-mode-0600-only", contract["successor_generation"])
        self.assertEqual("64-lowercase-hex", contract["successor_format"])
        for key in (
            "values_allowed_in_source",
            "values_allowed_in_argv",
            "values_allowed_in_environment",
            "values_allowed_in_logs",
            "values_allowed_in_evidence",
        ):
            self.assertFalse(self.policy[key], key)
        for prohibited in (
            "password",
            "username_value",
            "secret_data",
            "secret_data_base64",
            "connection_url",
            "token",
            "request_body",
            "response_body",
            "hash",
            "sql_output",
        ):
            self.assertIn(prohibited, contract["prohibited_receipt_fields"])
        self.assertIn("environment", contract["allowed_receipt_fields"])
        self.assertIn("target_resource_version", contract["allowed_receipt_fields"])
        self.assertIn("boolean_results", contract["allowed_receipt_fields"])

    def test_infisical_cas_and_stop_state_machine_are_fail_closed(self) -> None:
        cas = self.policy["cas_contract"]
        self.assertEqual("blocked-official-infisical-api-has-no-documented-cas", cas["status"])
        decision = cas["official_infisical_cas_decision"]
        self.assertEqual("reviewed-no-documented-cas", decision["status"])
        self.assertFalse(decision["accepted"])
        self.assertEqual("official-api-review-2026-08-21", decision["decision_record"])
        self.assertEqual("PATCH-/api/v3/secrets/raw/{secretName}", decision["provider_endpoint"])
        self.assertEqual("universal-auth-bearer-token", decision["provider_authentication"])
        self.assertEqual("absent-from-official-contract", decision["conditional_header_or_equivalent"])
        self.assertEqual("not-documented", decision["bulk_atomicity"])
        self.assertEqual("not-documented", decision["stale_write_conflict_status"])
        self.assertFalse(decision["secret_history_or_rollback_is_cas"])
        self.assertEqual("required", cas["expected_revision_or_etag"])
        self.assertEqual("required", cas["if_match_or_equivalent"])
        self.assertEqual("exactly-one-scoped-password-key-per-invocation", cas["update_scope"])
        self.assertTrue(cas["preserve_fixed_username"])
        self.assertTrue(cas["preserve_unrelated_source_keys"])
        self.assertEqual("required", cas["post_write_revision_metadata"])
        self.assertEqual("CAS-CONFLICT-STOP", cas["conflict_result"])
        self.assertEqual("CAS-UNKNOWN-STOP", cas["timeout_result"])
        self.assertEqual("CAS-UNKNOWN-STOP", cas["malformed_or_missing_authoritative_revision"])
        self.assertEqual("PARTIAL-STOP", cas["partial_or_ambiguous_write"])
        self.assertEqual("forbidden", cas["blind_retry"])
        self.assertEqual("forbidden", cas["source_batch_uploader_reuse"])
        self.assertEqual("never-output", cas["provider_response_values"])

    def test_materialization_and_cnpg_type_decisions_block_apply(self) -> None:
        materialization = self.policy["materialization_contract"]
        self.assertEqual("blocked-operator-sync-and-cnpg-type-decision", materialization["status"])
        self.assertTrue(materialization["operator_is_secret_value_owner"])
        self.assertEqual("forbidden", materialization["direct_kubernetes_secret_patch"])
        self.assertEqual("forbidden", materialization["direct_kubernetes_secret_apply"])
        self.assertEqual("shared-postgresql-infisical-secrets", materialization["static_secret_identity"])
        self.assertEqual("1h", materialization["refresh_interval_source"])
        self.assertFalse(materialization["instant_updates_source"])
        self.assertEqual("at-least-two-refresh-intervals", materialization["bounded_sync_wait"])
        self.assertTrue(materialization["protected_successor_equality_check"])

        cnpg = self.policy["cnpg_contract"]
        self.assertEqual(
            "blocked-current-target-type-incompatible-with-official-contract", cnpg["status"]
        )
        decision = cnpg["official_cnpg_secret_type_decision"]
        self.assertEqual("reviewed-basic-auth-required", decision["status"])
        self.assertTrue(decision["accepted"])
        self.assertEqual("v1.30.0", decision["pinned_crd_version"])
        self.assertEqual("kubernetes.io/basic-auth", decision["documented_password_secret_type"])
        self.assertEqual(["username", "password"], decision["documented_keys"])
        self.assertEqual("Opaque", decision["current_target_type"])
        self.assertFalse(decision["current_target_compatible"])
        self.assertEqual("official-cnpg-1.30-review-2026-08-21", decision["decision_record"])
        self.assertEqual(
            "blocked-until-infisical-concurrency-and-cnpg-basic-auth-remediation",
            cnpg["apply_gate"],
        )
        self.assertEqual(
            [
                "vendor-confirmed-infisical-cas-or-accepted-external-serialization",
                "cnpg-basic-auth-target-contract-remediation",
                "dedicated-no-output-writer-source-review",
                "exact-predecessor-custody-review",
                "exact-successor-authentication-and-negative-tests",
                "separate-acl-and-networkpolicy-acceptance",
            ],
            self.policy["apply_gate"]["unblock_requires"],
        )
        self.assertTrue(cnpg["database_role_spec_name_mutable"] is False)
        self.assertTrue(cnpg["role_password_update_without_role_recreation"])
        self.assertEqual("forbidden", cnpg["role_or_database_delete"])
        self.assertEqual("required-before-revocation", cnpg["authenticated_successor_probe"])
        self.assertTrue(cnpg["authorization_denial_is_not_authentication_revocation"])

    def test_predecessor_revocation_and_rollback_are_ordered_and_fail_closed(self) -> None:
        revocation = self.policy["predecessor_revocation"]
        self.assertEqual("blocked-until-successor-acceptance", revocation["status"])
        self.assertTrue(revocation["successor_acceptance_before_revocation"])
        self.assertTrue(revocation["predecessor_authentication_must_fail"])
        self.assertTrue(revocation["predecessor_authorization_denial_is_insufficient"])
        self.assertEqual("sanitized-boolean-only", revocation["revocation_source_receipt"])
        rollback = self.policy["rollback"]
        self.assertEqual("source-only-design", rollback["status"])
        self.assertTrue(rollback["after_cas_only_exact_revision"])
        self.assertEqual("forbidden", rollback["restore_predecessor_on_revision_mismatch"])
        self.assertEqual("CAS-UNKNOWN-STOP-and-preserve-encrypted-custody", rollback["ambiguous_write"])
        self.assertEqual("forbidden", rollback["direct_secret_patch_rollback"])
        self.assertEqual("forbidden", rollback["role_database_pvc_delete"])
        self.assertEqual("forbidden", rollback["blind_restore"])

    def test_broad_lanes_and_runtime_mutations_are_explicitly_forbidden(self) -> None:
        prohibition = self.policy["broad_lane_prohibition"]
        self.assertEqual("hard-block", prohibition["status"])
        self.assertEqual(FORBIDDEN_LANE_PATHS, set(prohibition["forbidden_paths"]))
        for value in prohibition["forbidden_reuse"]:
            self.assertIn(value, {"broad-15-key-postgresql-uploader", "all-consumer-static-secret", "all-consumer-cloudnative-pg-lifecycle", "shared-database-provisioning-wrapper", "direct-kubernetes-secret-write", "direct-sql-alter-role"})
        for mutation in (
            "database_cr",
            "databaserole_cr",
            "role_or_user_create",
            "role_or_user_delete",
            "database_delete",
            "pvc_delete",
            "networkpolicy_change",
            "workload_rollout",
            "argo_sync",
            "route_change",
        ):
            self.assertIn(mutation, prohibition["forbidden_mutations"])
        self.assertEqual("absent-by-design", prohibition["dedicated_rotation_source"])
        self.assertEqual("absent-by-design", prohibition["apply_wrapper"])
        self.assertEqual("forbidden", prohibition["runtime_contact"])
        source = self.policy["source_closure"]
        self.assertEqual([], source["manifest_files"])
        self.assertEqual([], source["executable_files"])
        for key in ("runtime_objects_added", "secret_values_added", "provider_calls", "kubernetes_calls", "database_calls", "infisical_calls"):
            self.assertFalse(source[key], key)
        self.assertTrue(source["no_runtime_mutation"])
        self.assertFalse(any((ROOT / "ansible/bin").glob("*reactive*resume*rotation*")))
        self.assertFalse(any((ROOT / "ansible/playbooks").glob("*reactive*resume*rotation*")))

    def test_cnpg_source_drift_is_recorded_without_mutation(self) -> None:
        objects = list(yaml.safe_load_all(CNPG_SOURCE.read_text()))
        roles = {
            item["spec"]["name"]: item
            for item in objects
            if item and item.get("kind") == "DatabaseRole"
        }
        self.assertTrue(roles["reactive_resume_dev_owner"]["spec"]["inherit"])
        self.assertTrue(roles["reactive_resume_prod_owner"]["spec"]["inherit"])
        self.assertEqual("separate-blocked-lane", self.policy["cnpg_contract"]["runtime_role_acl_remediation"])

    def test_runbook_and_source_boundaries_are_complete(self) -> None:
        normalized = " ".join(self.runbook_text.split())
        for phrase in (
            "SOURCE-ONLY DESIGN / NOT RUN / BLOCKED",
            "exactly the two Reactive Resume PostgreSQL credentials",
            "one environment may be handled by one separately approved invocation",
            "same-principal-new-password",
            "CAS-CONFLICT-STOP",
            "CAS-UNKNOWN-STOP",
            "PARTIAL-STOP",
            "published contract contains **NO DOCUMENTED CAS**",
            "requires a same-Namespace `kubernetes.io/basic-auth` Secret",
            "kubernetes.io/basic-auth",
            "Opaque",
            "blocked-until-infisical-concurrency-and-cnpg-basic-auth-remediation",
            "The 15-key bootstrap uploader is not a CAS writer and is forbidden",
            "no executable files",
            "No password, username value, Secret data",
            "predecessor authentication attempt fails",
        ):
            self.assertIn(phrase, normalized)
        self.assertNotIn("apply-capable rotation lane is ready", normalized)
        self.assertNotRegex(self.policy_text + self.runbook_text, r"(?i)(postgres(?:ql)?://[^\s/]+:[^\s@]+@)")
        self.assertNotRegex(self.policy_text + self.runbook_text, r"(?im)^\s*(?:PGPASSWORD|password_value|secret_value)\s*[:=]\s*[^<\s]")

    def test_no_rotation_wrapper_or_runtime_source_was_added(self) -> None:
        expected_files = {
            "ansible/files/policies/reactive-resume-postgresql-exposure-rotation.yml",
            "runbooks/reactive-resume-postgresql-exposure-rotation.md",
            "tests/test_reactive_resume_postgresql_exposure_rotation_contract.py",
        }
        self.assertTrue(all((ROOT / path).is_file() for path in expected_files))
        for directory in (ROOT / "ansible/files/components", ROOT / "ansible/plugins/action"):
            for path in directory.rglob("*"):
                if not path.is_file():
                    continue
                self.assertNotIn("reactive-resume-postgresql-exposure-rotation", path.name)
        self.assertFalse(any((ROOT / "ansible/bin").glob("*postgresql*exposure*rotation*")))
        self.assertFalse(any((ROOT / "ansible/playbooks").glob("*postgresql*exposure*rotation*")))


if __name__ == "__main__":
    unittest.main()
