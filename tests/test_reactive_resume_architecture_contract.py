from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ansible/files/policies/reactive-resume-architecture.yml"
DATABASE_POLICY = ROOT / "ansible/files/policies/shared-database-architecture.yml"
IDENTITY_POLICY = ROOT / "ansible/files/policies/hosted-identity-authorization.yml"
CNPG_CLUSTER = ROOT / "ansible/files/components/cloudnative-pg/cluster/shared-postgresql.yaml"
RUNBOOK = ROOT / "runbooks/reactive-resume-hosted-architecture.md"
KUBERNETES = ROOT / "kubernetes"


class ReactiveResumeArchitectureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_text = POLICY.read_text()
        cls.policy = yaml.safe_load(cls.policy_text)
        cls.database_policy = yaml.safe_load(DATABASE_POLICY.read_text())
        cls.identity_policy = yaml.safe_load(IDENTITY_POLICY.read_text())
        cls.runbook_text = RUNBOOK.read_text()

    def test_scope_is_source_only_and_prod_is_template(self) -> None:
        self.assertEqual("cristex-reactive-resume-v4", self.policy["policy_schema"])
        self.assertEqual("source-policy-only-runtime-blocked", self.policy["policy_status"])
        self.assertEqual("included-private-dev", self.policy["mvp_scope"])
        self.assertEqual(
            "blocked-pending-dedicated-dev-lanes-and-private-acceptance",
            self.policy["environments"]["dev"]["activation"],
        )
        self.assertEqual(
            "promotion-blocked-template-only",
            self.policy["environments"]["prod"]["activation"],
        )
        self.assertFalse(self.policy["executable_source_allowed"])
        closure = self.policy["source_closure"]
        self.assertEqual("value-free-policy-only-incomplete-blocked", closure["status"])
        self.assertFalse(closure["dev_contract_complete"])
        self.assertTrue(closure["prod_promotion_template_only"])
        self.assertTrue(closure["no_runtime_objects_added"])
        self.assertTrue(closure["no_secret_values_added"])
        self.assertTrue(closure["no_selected_image_digest_claimed"])
        self.assertTrue(closure["candidate_digest_is_not_selection"])
        self.assertEqual("absent-blocker", closure["executable_workload_source"])
        dev_objects = closure["dev"]["object_contract"]
        self.assertTrue(dev_objects["no_runtime_source"])
        self.assertEqual(
            "absent-until-image-and-config-review",
            dev_objects["exact_objects"]["deployment"],
        )
        self.assertEqual(
            "absent-until-image-and-config-review", dev_objects["exact_objects"]["service"]
        )

    def test_image_and_runtime_contact_remain_blocked(self) -> None:
        source = self.policy["image_source"]
        self.assertEqual("unselected", source["selection"])
        self.assertIsNone(source["repository"])
        self.assertIsNone(source["version"])
        self.assertIsNone(source["linux_amd64_digest"])
        self.assertFalse(source["trust_accepted"])
        self.assertEqual("unaccepted-blocker", source["sbom_and_vulnerability_review"])
        self.assertEqual("unaccepted-blocker", source["off_node_oci_recovery"])
        self.assertEqual("unaccepted-blocker", source["target_pull_and_admission"])
        self.assertFalse(source["candidate_record_is_deployable"])
        self.assertFalse(source["candidate_record_is_selection"])
        self.assertEqual(
            "blocked-tag-image-revision-mismatch", source["upstream_release_contract"]
        )
        self.assertEqual(
            "reviewed-tag-source-not-image-runtime-contract",
            source["environment_variable_allowlist"],
        )
        self.assertEqual(
            "reviewed-tag-source-not-image-runtime-contract",
            source["health_and_readiness_endpoint"],
        )
        self.assertEqual("reviewed-tag-source-blocked", source["migration_command_and_locking"])
        self.assertEqual(
            "reviewed-tag-source-none-client-side-pdf",
            source["printer_or_browser_dependency"],
        )
        self.assertEqual(
            {
                "host": "forbidden",
                "registry": "forbidden",
                "kubernetes_api": "forbidden",
                "infisical_api": "forbidden",
                "database": "forbidden",
                "provider": "forbidden",
            },
            self.policy["source_closure"]["runtime_mutation"],
        )
        self.assertEqual(
            {
                "github_source_and_release_metadata": "performed",
                "docker_hub_oci_metadata_and_attestations": "performed",
                "ghcr_oci_metadata_and_attestations": "performed-no-equivalence-or-selection-claim",
                "kubernetes_absence_inventory": "performed",
            },
            self.policy["source_closure"]["read_only_research_contact"],
        )

    def test_candidate_image_provenance_is_exact_and_non_deployable(self) -> None:
        candidate = self.policy["image_candidate_provenance"]
        self.assertEqual("candidate-only-not-deployable", candidate["status"])
        self.assertEqual("2026-08-21", candidate["observed_at_utc"])
        self.assertEqual(
            "https://github.com/amruthpillai/reactive-resume",
            candidate["upstream_repository"],
        )
        self.assertEqual("annotated", candidate["upstream_tag_type"])
        self.assertEqual("docker.io", candidate["registry"])
        self.assertEqual(
            "docker.io/amruthpillai/reactive-resume", candidate["registry_repository"]
        )
        self.assertTrue(candidate["ghcr_is_not_this_record"])
        self.assertEqual("v5.2.7", candidate["upstream_tag"])
        self.assertEqual(
            "5392728f22580ac107cad25a5ccfcde962133535",
            candidate["upstream_tag_commit"],
        )
        self.assertEqual(
            "sha256:656a7ce0409ea1b8fcdb4985320d8b687b94da1201d10af13fd1e2c7c74f6083",
            candidate["index_digest"],
        )
        self.assertEqual(
            "sha256:befa93b3af3e8fe91a4dd02401fc7996c4aa2f19641463e3b2aaa77089caff5a",
            candidate["linux_amd64_digest"],
        )
        self.assertEqual(
            "sha256:7f2c997d1f48b152e649c2561e0e23e2d5bc7d9e7e7dbf3e6cac7dd1a6f002f7",
            candidate["config_digest"],
        )
        self.assertEqual(
            "3221afda9ddfb03d6cce87927b0ce47338b4cfa8",
            candidate["config_revision"],
        )
        self.assertFalse(candidate["tag_commit_matches_config_revision"])
        self.assertTrue(candidate["tag_source_reviewed"])
        self.assertFalse(candidate["candidate_image_source_reviewed"])
        self.assertEqual("16-commits-150-changed-files", candidate["mismatch_distance"])
        self.assertEqual("2026-08-20T08:45:26.993Z", candidate["image_created_utc"])
        self.assertEqual("node", candidate["non_root_user"])
        self.assertEqual("3000/tcp", candidate["exposed_port"])
        self.assertEqual("node-apps-server-dist-index-mjs", candidate["command"])
        self.assertEqual("/api/health", candidate["health_endpoint"])
        self.assertEqual("observed", candidate["index_signature"])
        self.assertEqual("not-observed-blocker", candidate["linux_amd64_child_signature"])
        self.assertEqual("observed-not-accepted", candidate["spdx_sbom_attestation"])
        self.assertEqual("observed-not-accepted", candidate["slsa_provenance_attestation"])
        self.assertEqual("absent-blocker", candidate["vulnerability_disposition"])
        self.assertEqual("forbidden", candidate["registry_equivalence_claim"])
        self.assertTrue(candidate["index_to_linux_amd64_binding_verified"])
        self.assertTrue(candidate["linux_amd64_to_config_binding_verified"])
        self.assertEqual("forbidden", candidate["promotion"])
        runtime = self.policy["reviewed_v5_runtime_contract"]
        self.assertEqual("source-tag-evidence-only-not-runtime-contract", runtime["status"])
        self.assertEqual("v5.2.7", runtime["source_tag"])
        self.assertEqual(43, len(runtime["environment_allowlist"]))
        self.assertEqual(43, len(set(runtime["environment_allowlist"])))
        self.assertEqual(
            ["APP_URL", "DATABASE_URL", "AUTH_SECRET"],
            runtime["required_core_environment"],
        )
        self.assertEqual(3000, runtime["production_port"])
        self.assertEqual("/api/health", runtime["health_endpoint"])
        self.assertEqual(200, runtime["health_success_status"])
        self.assertEqual(503, runtime["health_dependency_failure_status"])
        self.assertEqual(["postgresql", "storage"], runtime["health_dependencies"])
        self.assertTrue(runtime["startup_migrations_before_bind"])

    def test_infisical_lane_is_dedicated_dev_only_and_broad_reuse_is_forbidden(self) -> None:
        secrets = self.policy["secrets"]
        broad = secrets["current_broad_lanes"]
        for key, value in broad.items():
            self.assertIn("forbidden", value, key)
        dev = secrets["dedicated_dev_only"]
        self.assertEqual("absent-blocker", dev["status"])
        self.assertEqual("absent", dev["source"])
        self.assertEqual("cristexhub-dev", dev["target_namespace"])
        self.assertEqual("reactive-resume-runtime", dev["target_name"])
        self.assertEqual("unselected-blocker", dev["infisical_path"])
        self.assertEqual(
            "blocked-pending-source-patch-and-feature-selection", dev["exact_keys"]
        )
        self.assertEqual("absent-blocker", dev["dedicated_machine_identity"])
        self.assertEqual("absent-blocker", dev["dedicated_writer"])
        self.assertEqual("forbidden-until-dedicated-lane", dev["materialization"])
        vap = secrets["vap_rbac"]
        self.assertEqual("absent-blocker", vap["status"])
        self.assertEqual("absent", vap["dev_vap_source"])
        self.assertEqual("required", vap["dev_vap_exact_target_only"])
        self.assertEqual(
            "preserve-allow-outside-deny-inside-guard",
            vap["existing_namespace_inequality_validation"],
        )
        self.assertEqual("blocker", vap["existing_matchcondition_skip_behavior"])
        self.assertEqual("unobserved-blocker", vap["existing_typecheck_status"])
        self.assertEqual("required", vap["future_zero_typecheck_warnings"])
        for key in (
            "alternate_target_in_target_namespace",
            "foreign_target_name",
            "foreign_target_namespace",
            "target_foreign_name",
            "target_foreign_namespace",
            "pushsecret_and_dynamicsecret_foreign_targets",
        ):
            if key in vap:
                self.assertEqual("deny", vap[key], key)
        self.assertEqual("absent", vap["dev_writer_role_source"])
        self.assertEqual("forbidden", vap["broad_secret_create"])
        self.assertEqual("forbidden", vap["broad_secret_get_list_watch"])
        self.assertEqual("forbidden", vap["shared_manager_role_reuse"])
        prod = secrets["dedicated_prod_template_only"]
        self.assertEqual("reservation-only", prod["status"])
        self.assertEqual("forbidden-before-dev-soak", prod["materialization"])

    def test_database_uses_one_dev_only_canonical_lane_and_strict_owner(self) -> None:
        db = self.policy["database"]
        self.assertEqual("postgresql", db["engine"])
        lane = db["canonical_lane"]
        self.assertEqual("unresolved-dual-owner-blocker", lane["status"])
        self.assertEqual(
            "cloudnative-pg-database-and-role-crs-via-ansible",
            lane["lifecycle_owner_candidate"],
        )
        self.assertEqual("required-before-source", lane["final_owner_selection"])
        self.assertEqual(["reactive-resume-dev"], lane["allowed_consumers"])
        self.assertEqual("exact-consumer-and-secret-binding", lane["dev_only_selector"])
        self.assertEqual("forbidden", lane["prod_consumer_in_dev_run"])
        self.assertEqual("forbidden", lane["all_consumer_apply_in_dev_run"])
        self.assertTrue(lane["check_apply_idempotence_required"])
        self.assertEqual("forbidden", lane["broad_shared_postgresql_wrapper_reuse"])
        self.assertEqual("forbidden", lane["helper_role_or_database_lifecycle"])
        self.assertEqual("forbidden", lane["simultaneous_cnpg_and_helper_lifecycle"])
        broad = db["current_broad_lanes"]
        self.assertIn("forbidden", broad["shared_postgresql_wrapper_all_consumer_scopes"])
        self.assertIn("forbidden", broad["cloudnative_pg_rr_database_objects"])
        self.assertEqual("forbidden", broad["implicit_prod_scope_creation"])
        capacity = db["capacity_and_failure_domain"]
        self.assertEqual("acknowledged", capacity["shared_single_engine_failure_domain"])
        for key in (
            "connection_headroom",
            "storage_headroom",
            "migration_headroom",
            "backup_staging_headroom",
            "restore_headroom",
        ):
            self.assertEqual("unselected-blocker", capacity[key], key)
        self.assertEqual("required-before-dev-apply", capacity["contention_review"])
        owner = db["owner_role_contract"]
        self.assertEqual("absent-blocker", owner["status"])
        self.assertEqual("reactive_resume_dev_owner", owner["role"])
        self.assertEqual("reactive_resume_dev", owner["database"])
        for key in (
            "superuser",
            "createdb",
            "createrole",
            "inherit",
            "replication",
            "bypassrls",
        ):
            self.assertFalse(owner[key], key)
        self.assertEqual("revoke", owner["public_connect"])
        self.assertEqual("revoke", owner["public_temporary"])
        self.assertEqual("revoke", owner["public_schema_create"])
        self.assertEqual([], owner["role_memberships"])
        self.assertEqual("required-empty", owner["pg_auth_members_projection"])
        self.assertEqual("deny", owner["set_role_to_foreign_roles"])
        self.assertEqual("deny", owner["cross_database_access"])
        self.assertEqual(
            "exact-allowlisted-owner-and-runtime-privileges", owner["acl_projection"]
        )
        self.assertGreaterEqual(len(owner["negative_tests"]), 8)

    def test_database_and_identity_reservations_match_canonical_policies(self) -> None:
        consumers = self.database_policy["engines"]["postgresql"]["consumers"]
        for environment, consumer_name in (
            ("dev", "reactive-resume-dev"),
            ("prod", "reactive-resume-prod"),
        ):
            expected = consumers[consumer_name]
            scoped = self.policy["source_closure"][environment]["database_scope"]
            self.assertEqual(expected["logical_database"], scoped["logical_database"])
            self.assertEqual(expected["principal_name"], scoped["owner_role"])
            self.assertEqual(expected["credential_secret"], scoped["credential_secret"])
            self.assertEqual("inactive", expected["activation"])
        clients = {
            item["id"]: item for item in self.identity_policy["clients"]["browser"]
        }
        dev_identity = self.policy["source_closure"]["dev"]["identity_scope"]
        prod_identity = self.policy["source_closure"]["prod"]["identity_scope"]
        for scoped in (dev_identity, prod_identity):
            canonical = clients[scoped["client_id"]]
            self.assertEqual(canonical["realm"], scoped["realm"])
            self.assertEqual(canonical["issuer"], scoped["issuer"])
            self.assertFalse(canonical["callback_selected"])

    def test_current_broad_cnpg_reactive_resume_roles_match_recorded_blocker(self) -> None:
        objects = list(yaml.safe_load_all(CNPG_CLUSTER.read_text()))
        roles = {
            item["spec"]["name"]: item
            for item in objects
            if item and item.get("kind") == "DatabaseRole"
        }
        for role_name in ("reactive_resume_dev_owner", "reactive_resume_prod_owner"):
            self.assertTrue(roles[role_name]["spec"]["inherit"], role_name)
        migration = self.policy["migration"]
        self.assertEqual("blocker", migration["cnpg_source_contract_drift"])
        self.assertEqual(
            "ansible/files/components/cloudnative-pg/cluster/shared-postgresql.yaml",
            migration["current_cnpg_source_path"],
        )
        self.assertIn(
            "forbidden",
            self.policy["database"]["current_broad_lanes"]["cloudnative_pg_rr_database_objects"],
        )

    def test_database_and_network_identity_are_unresolved_blockers(self) -> None:
        tls = self.policy["database"]["tls_and_network"]
        self.assertEqual("absent-blocker", tls["status"])
        self.assertEqual("unresolved-blocker", tls["service_identity"])
        self.assertEqual("unresolved-blocker", tls["tls_secret_identity"])
        self.assertEqual("required-before-selection", tls["cnpg_server_tls_secret"])
        self.assertEqual("required-before-selection", tls["cnpg_compatible_network_policy"])
        self.assertEqual("absent-blocker", tls["network_policy_source"])
        self.assertEqual("required", tls["default_deny"])
        self.assertEqual("exact-service-and-port-only", tls["allowed_destinations"])
        self.assertEqual("forbidden", tls["broad_namespace_or_selector_allow"])
        self.assertEqual("forbidden", tls["direct_database_origin"])

    def test_oidc_realm_callbacks_claims_and_negative_tests_are_unresolved(self) -> None:
        identity = self.policy["identity"]
        self.assertEqual(
            "blocked-successor-realm-not-live-and-upstream-oidc-hardening-unaccepted",
            identity["status"],
        )
        self.assertEqual("cristexhub-dev", identity["realm"])
        self.assertEqual(
            "https://auth.cristex-soft.com/realms/cristexhub-dev", identity["issuer"]
        )
        self.assertEqual("cristexhub", identity["candidate_realms"]["retained_prod_compatible"])
        self.assertEqual("cristexhub-dev", identity["candidate_realms"]["successor_dev_source"])
        self.assertEqual(
            "source-only-successor-client-runtime-unobserved-blocker",
            identity["clients"]["dev"]["status"],
        )
        self.assertEqual(
            "unobserved-blocker",
            self.policy["source_closure"]["dev"]["identity_scope"]["realm_runtime_state"],
        )
        for key in (
            "exact_callbacks_selected",
            "exact_web_origins_selected",
            "exact_post_logout_selected",
            "pkce_s256_selected",
            "scopes_selected",
            "audience_selected",
            "claims_selected",
            "group_authorization_selected",
            "logout_and_account_linking_selected",
        ):
            self.assertFalse(identity[key], key)
        self.assertEqual("unaccepted-blocker", identity["discovery_and_jwks_validation"])
        self.assertEqual("unaccepted-blocker", identity["positive_negative_oidc_tests"])
        hardening = identity["upstream_v5_hardening"]
        self.assertEqual("v5.2.7-source-tag-only", hardening["reviewed_release"])
        self.assertTrue(hardening["callback_verified_for_reviewed_source_tag"])
        self.assertFalse(hardening["callback_verified_for_selected_release"])
        self.assertEqual(
            "reviewed-db-backed-signed-cookie-one-time-ten-minute",
            hardening["state_csrf_protection"],
        )
        self.assertEqual("absent-blocker", hardening["pkce"])
        self.assertEqual("absent-blocker", hardening["oidc_nonce"])
        self.assertEqual(
            "absent-blocker",
            hardening["id_token_signature_jwks_issuer_audience_expiry_validation"],
        )
        self.assertFalse(hardening["password_login_disabled"])
        self.assertFalse(hardening["username_password_direct_endpoint_disabled"])
        self.assertFalse(hardening["trustworthy_email_verified_mapping"])
        self.assertEqual("hardcoded-true-blocker", hardening["new_oauth_user_email_verified_behavior"])
        self.assertFalse(hardening["custom_provider_linking_requires_verified_trusted_email"])
        self.assertFalse(hardening["stable_provider_account_id_uses_oidc_sub"])
        self.assertEqual("absent-blocker", hardening["rp_initiated_logout"])
        self.assertEqual(
            "absent-blocker",
            hardening["oauth_access_refresh_and_id_token_application_encryption"],
        )
        self.assertEqual(
            "required-per-environment", hardening["token_encryption_key_custody_patch"]
        )
        self.assertEqual(
            "privacy-blocker", hardening["smtp_absent_reset_and_verification_logging"]
        )
        self.assertEqual("insufficient", hardening["configuration_only_remediation"])
        self.assertEqual("forbidden", hardening["groups_as_authorization_boundary"])
        self.assertTrue(identity["contract_required_before_client_mutation"])
        self.assertFalse(identity["local_development_inputs_allowed"])
        self.assertEqual("forbidden", identity["cross_environment_issuer_or_client_reuse"])
        self.assertEqual("unselected-blocker", identity["authorization"]["exact_client_role_set"])
        self.assertEqual("unselected-blocker", identity["authorization"]["exact_field_projection"])
        self.assertEqual("forbidden-until-reviewed", identity["authorization"]["view_clients_role"])
        self.assertEqual(
            "forbidden-until-reviewed",
            identity["authorization"]["group_view_and_membership_roles"],
        )

    def test_object_storage_is_authoritative_and_redis_ai_is_blocked(self) -> None:
        storage = self.policy["object_storage"]
        self.assertEqual("blocked-authoritative-state-unselected", storage["status"])
        self.assertTrue(storage["required_for_runtime"])
        self.assertEqual("durable-application-state", storage["authority"])
        for key in (
            "backend_selection",
            "provider",
            "dev_bucket_or_prefix",
            "prod_bucket_or_prefix",
        ):
            self.assertEqual("unselected-blocker", storage[key], key)
        for key in (
            "environment_scopes_separate",
            "private_access_only",
            "encryption_at_rest",
            "versioning_or_immutable_manifest",
            "url_continuity",
            "database_reference_consistency",
            "encrypted_off_node_backup",
            "isolated_object_restore",
            "object_manifest_checksum_readback",
        ):
            self.assertTrue(storage[key], key)
        self.assertEqual(
            [
                "profile-pictures-under-uploads-user-pictures",
                "application-resume-and-cover-letter-pdfs-under-pictures-prefix",
                "private-agent-attachments-under-uploads-user-agent",
            ],
            storage["reviewed_v5_persisted_objects"],
        )
        self.assertEqual(["screenshots", "pdfs"], storage["reviewed_v5_delete_only_prefixes"])
        self.assertEqual("unreviewed-blocker", storage["legacy_delete_only_object_exposure"])
        self.assertEqual(["resume-export-pdfs"], storage["reviewed_v5_streamed_not_persisted"])
        self.assertEqual("blocker", storage["public_read_acl_or_unauthenticated_upload_serving"])
        self.assertEqual("public-read-blocker", storage["reviewed_v5_normal_s3_acl"])
        self.assertEqual("unauthenticated-blocker", storage["reviewed_v5_upload_read_route"])
        self.assertEqual("public-immutable-blocker", storage["reviewed_v5_upload_cache_control"])
        self.assertEqual("absent-blocker", storage["reviewed_v5_generic_upload_mime_allowlist"])
        self.assertEqual("required", storage["required_mime_byte_validation_and_safe_disposition"])
        self.assertEqual("deny", storage["svg_html_and_active_content_upload"])
        self.assertEqual("required", storage["response_nosniff"])
        self.assertEqual("silent-local-storage-blocker", storage["partial_s3_configuration_fallback"])
        self.assertEqual("required", storage["s3_configuration_all_or_none"])
        self.assertEqual("root-fixed-key-put-delete-insufficient", storage["s3_health_behavior"])
        self.assertEqual("required", storage["object_ownership_and_public_access_block"])
        self.assertEqual("deny", storage["anonymous_get_list_head_put_delete"])
        self.assertEqual("deny", storage["cross_environment_prefix_access"])
        self.assertTrue(storage["private_bucket_policy_and_readback"])
        self.assertEqual("required", storage["source_patch_for_authenticated_private_reads"])
        self.assertEqual("forbidden", storage["local_ephemeral_storage_only"])
        redis_ai = self.policy["redis_ai"]
        self.assertEqual(
            "reviewed-v5-agent-disabled-pending-separate-selection", redis_ai["status"]
        )
        self.assertEqual("present", redis_ai["reviewed_v5_server_agent_evidence"])
        self.assertEqual("conditional-agent-workspace", redis_ai["reviewed_v5_redis_requirement"])
        self.assertEqual(
            "conditional-agent-and-saved-ai-providers",
            redis_ai["reviewed_v5_encryption_secret_requirement"],
        )
        self.assertFalse(redis_ai["agent_enabled"])
        self.assertFalse(redis_ai["redis_selected"])
        self.assertEqual(
            "not-applicable-while-agent-disabled-required-if-selected",
            redis_ai["redis_recovery"],
        )
        self.assertEqual("absent-in-v5-health-endpoint", redis_ai["redis_health_coverage"])
        self.assertEqual("forbidden", redis_ai["redis_backup_as_authoritative_state"])

    def test_application_keys_migrations_and_recovery_are_blocked(self) -> None:
        keys = self.policy["application_keys"]
        self.assertEqual("blocked-source-patch-feature-and-recovery-unselected", keys["status"])
        self.assertEqual(
            "reviewed-candidate-not-materialization-contract", keys["exact_key_names"]
        )
        self.assertEqual(["AUTH_SECRET"], keys["candidate_required_names"])
        self.assertEqual(
            ["OAUTH_CLIENT_SECRET", "ENCRYPTION_SECRET"],
            keys["candidate_conditional_names"],
        )
        self.assertEqual(
            "custom-oauth-provider-selected",
            keys["conditional_requirements"]["OAUTH_CLIENT_SECRET"],
        )
        self.assertEqual(32, keys["encryption_secret_minimum_length"])
        self.assertEqual(
            ["saved-ai-provider-credentials", "agent-workspace"],
            keys["encryption_secret_conditions"],
        )
        self.assertEqual([], keys["unverified_or_absent_upstream_keys"])
        for key in ("dev_path", "prod_path"):
            self.assertEqual("unselected-blocker", keys[key])
        for key in (
            "values_in_source",
            "values_in_argv",
            "values_in_environment_examples",
            "values_in_evidence",
        ):
            self.assertFalse(keys[key], key)
        for key in (
            "independent_custody",
            "retrieval_and_decryption_rehearsal",
            "rotation_and_revocation_plan",
            "encryption_key_loss_recovery",
        ):
            self.assertTrue(keys[key], key)
        migration = self.policy["migration"]
        self.assertEqual(
            "blocked-upstream-startup-migration-privilege-and-concurrency",
            migration["status"],
        )
        self.assertEqual(
            "always-before-listen-same-database-url",
            migration["upstream_startup_migration_behavior"],
        )
        self.assertEqual("rethrow-and-process-exit-one", migration["migration_failure_propagation"])
        self.assertEqual(
            "pending-sql-and-ledger-single-begin-commit", migration["transaction_scope"]
        )
        self.assertEqual(
            "outside-pending-transaction",
            migration["migration_schema_and_ledger_bootstrap_transaction"],
        )
        self.assertEqual("absent-blocker", migration["distributed_or_advisory_lock"])
        self.assertEqual("absent-name-only-selection", migration["checksum_comparison"])
        self.assertEqual("absent-blocker", migration["migration_only_mode"])
        self.assertEqual("absent-blocker", migration["startup_migration_disable_flag"])
        self.assertTrue(migration["destructive_or_broad_ddl_observed"])
        self.assertFalse(migration["runtime_role_without_ddl_compatible_with_upstream"])
        self.assertEqual(
            "true-conflicts-with-required-noinherit",
            migration["current_cnpg_dev_owner_inherit_setting"],
        )
        self.assertEqual(
            "true-conflicts-with-required-noinherit",
            migration["current_cnpg_prod_owner_inherit_setting"],
        )
        self.assertEqual("blocker", migration["cnpg_source_contract_drift"])
        self.assertEqual("absent-blocker", migration["dedicated_migration_actor"])
        self.assertTrue(migration["migration_lock"])
        self.assertTrue(migration["pre_migration_backup"])
        self.assertTrue(migration["expand_contract_or_forward_compatible"])
        self.assertEqual("forbidden-as-routine", migration["rollback_by_database_restore_only"])

    def test_backup_restore_and_rpo_rto_are_explicitly_unaccepted(self) -> None:
        recovery = self.policy["backup_restore"]
        self.assertEqual("blocked-no-reactive-resume-scope", recovery["status"])
        for key in (
            "postgresql_scope",
            "object_storage_scope",
            "application_key_scope",
        ):
            self.assertEqual("absent-blocker", recovery[key], key)
        self.assertEqual(
            "not-applicable-while-agent-disabled-required-if-selected",
            recovery["redis_scope"]
        )
        for key in (
            "database_and_object_consistency",
            "encrypted_off_node_copy",
            "integrity_readback",
            "isolated_restore",
            "login_and_upload_restore_tests",
            "clean_host_restore",
        ):
            self.assertTrue(recovery[key], key)
        self.assertFalse(recovery["measured_rpo_rto"])
        self.assertEqual("24h-target-not-accepted", recovery["rpo"])
        self.assertEqual("4h-target-not-accepted", recovery["rto"])

    def test_exposure_and_promotion_order_are_fail_closed(self) -> None:
        forbidden = set(self.policy["exposure"]["forbidden"])
        self.assertTrue(
            {
                "Ingress",
                "NodePort",
                "LoadBalancer",
                "CloudflareTunnel",
                "Tunnel",
                "CloudflareDNS",
                "public-route",
                "public-administration",
                "direct-origin",
            }.issubset(forbidden)
        )
        self.assertEqual("forbidden-until-separate-public-cutover", self.policy["exposure"]["traefik_ingress"])
        self.assertEqual("forbidden-until-separate-public-cutover", self.policy["exposure"]["cloudflare_route"])
        self.assertEqual("forbidden", self.policy["exposure"]["dns_mutation"])
        gates = self.policy["promotion_gates"]
        self.assertTrue(all(value is False for value in gates.values()))
        order = self.policy["promotion_order"]
        self.assertEqual("required", order["dev_private_validation_before_prod"])
        self.assertEqual("required", order["dev_soak_before_prod"])
        self.assertEqual("forbidden", order["simultaneous_dev_prod_activation"])
        self.assertEqual("forbidden", order["prod_runtime_objects_from_reservation"])
        self.assertEqual("required", order["public_route_last"])

    def test_prod_is_reservation_only_and_has_no_runtime_source(self) -> None:
        review = self.policy["source_closure_review"]
        self.assertEqual(
            "observed-absent-2026-08-21-read-only-inventory",
            review["current_runtime_state"],
        )
        self.assertFalse(review["runtime_observation_is_reconciliation"])
        self.assertTrue(review["no_selected_image_digest_claimed"])
        self.assertTrue(review["candidate_digest_is_not_selection"])
        prod = self.policy["source_closure"]["prod"]
        self.assertEqual("cristexhub-prod", prod["namespace"])
        self.assertTrue(prod["source_template"])
        self.assertEqual("absent-promotion-template-only", prod["manifest_source"])
        self.assertTrue(prod["no_prod_runtime_from_this_contract"])
        self.assertEqual("absent", prod["object_contract"]["runtime_objects"])
        self.assertEqual("forbidden", prod["object_contract"]["generated_manifests"])
        self.assertEqual("blocked-promotion-only", prod["database_scope"]["materialization"])
        self.assertEqual("forbidden-in-this-increment", prod["runtime_secret_contract"]["materialization"])

    def test_runbook_records_all_blockers_without_claiming_completion(self) -> None:
        normalized = " ".join(self.runbook_text.split())
        for required in (
            "SOURCE POLICY ONLY — RUNTIME BLOCKED / DEV CONTRACT INCOMPLETE",
            "executable_source_allowed` remains `false`",
            "candidate-only, **not selected and not deployable**",
            "docker.io/amruthpillai/reactive-resume",
            self.policy["image_candidate_provenance"]["index_digest"],
            self.policy["image_candidate_provenance"]["linux_amd64_digest"],
            self.policy["image_candidate_provenance"]["config_digest"],
            self.policy["image_candidate_provenance"]["upstream_tag_commit"],
            self.policy["image_candidate_provenance"]["config_revision"],
            "16 commits and 150 files beyond the release tag",
            "Configuration alone cannot remediate this",
            "single-run locked migration Job",
            "Dedicated Infisical lane",
            "Dedicated PostgreSQL lane",
            "CNPG/TLS/NetworkPolicy",
            "OIDC",
            "Object storage",
            "Redis and AI",
            "Application keys",
            "Migrations and recovery",
            "No blocker above is satisfied by a policy reservation",
            "Reactive Resume PROD is represented only as a promotion template",
            "private DEV validation and an explicit DEV soak",
            "Ingress, Traefik public routes, NodePort, LoadBalancer, Cloudflare Tunnel",
            "No Deployment, StatefulSet, Service, PVC, Secret, Infisical CR",
        ):
            self.assertIn(required, normalized)
        self.assertNotIn("source-only DEV closure is complete", normalized)

    def test_no_executable_source_or_secret_value_is_added(self) -> None:
        self.assertEqual(
            {
                "platform/namespaces/argocd.yaml",
                "platform/namespaces/platform-edge.yaml",
                "platform/namespaces/shared-services.yaml",
                "applications/namespaces/cristexhub-dev.yaml",
                "applications/namespaces/cristexhub-prod.yaml",
            },
            {
                str(path.relative_to(KUBERNETES))
                for path in KUBERNETES.rglob("*")
                if path.is_file()
            },
        )
        combined = f"{self.policy_text}\n{self.runbook_text}"
        self.assertNotRegex(
            combined,
            r"(?im)^\s*(?:password|token|client_secret|api_key|credentials?)\s*:\s*\S+",
        )
        executable_roots = (
            ROOT / "kubernetes",
            ROOT / "ansible/files/components",
            ROOT / "ansible/playbooks",
            ROOT / "ansible/roles",
            ROOT / "ansible/bin",
        )
        for root in executable_roots:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                text = path.read_text(errors="ignore")
                self.assertNotRegex(
                    text,
                    r"(?im)^\s*image:\s*\S*(?:amruthpillai/)?reactive[-_/]?resume\S*\s*$",
                    str(path),
                )
                self.assertNotIn("reactive-resume", path.name.lower(), str(path))
                self.assertNotIn("reactive_resume", path.name.lower(), str(path))
        self.assertNotIn("/Users/", combined)
        self.assertNotIn("/home/paul/", combined)


if __name__ == "__main__":
    unittest.main()
