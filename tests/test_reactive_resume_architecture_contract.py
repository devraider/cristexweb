from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ansible/files/policies/reactive-resume-architecture.yml"
DATABASE_POLICY = ROOT / "ansible/files/policies/shared-database-architecture.yml"
IDENTITY_POLICY = ROOT / "ansible/files/policies/hosted-identity-authorization.yml"
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
        self.assertEqual("cristex-reactive-resume-v3", self.policy["policy_schema"])
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
        self.assertTrue(closure["no_image_digest_claimed"])

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
        for key in (
            "upstream_release_contract",
            "environment_variable_allowlist",
            "health_and_readiness_endpoint",
            "migration_command_and_locking",
            "printer_or_browser_dependency",
        ):
            self.assertEqual("unselected-blocker", source[key], key)
        self.assertEqual(
            {
                "host": "forbidden",
                "registry": "forbidden",
                "kubernetes_api": "forbidden",
                "infisical_api": "forbidden",
                "database": "forbidden",
                "provider": "forbidden",
            },
            self.policy["source_closure"]["runtime_contact"],
        )

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
        self.assertEqual("unselected-until-upstream-config-review", dev["exact_keys"])
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
        self.assertFalse(hardening["callback_verified_for_selected_release"])
        self.assertFalse(hardening["password_login_disabled"])
        self.assertFalse(hardening["trustworthy_email_verified_mapping"])
        self.assertEqual(
            "unaccepted-blocker", hardening["id_token_signature_issuer_nonce_validation"]
        )
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
        self.assertEqual(["pictures", "screenshots", "pdfs"], storage["reviewed_v5_candidate_objects"])
        self.assertEqual("blocker", storage["public_read_acl_or_unauthenticated_upload_serving"])
        self.assertTrue(storage["private_bucket_policy_and_readback"])
        self.assertEqual("forbidden", storage["local_ephemeral_storage_only"])
        redis_ai = self.policy["redis_ai"]
        self.assertEqual(
            "no-server-side-agent-or-redis-contract-selected", redis_ai["status"]
        )
        self.assertEqual("absent", redis_ai["reviewed_v5_server_agent_evidence"])
        self.assertEqual("absent", redis_ai["reviewed_v5_redis_requirement"])
        self.assertEqual(
            "forbidden-until-pinned-and-reviewed", redis_ai["future_release_ai_or_redis"]
        )
        self.assertEqual("forbidden", redis_ai["redis_backup_as_authoritative_state"])

    def test_application_keys_migrations_and_recovery_are_blocked(self) -> None:
        keys = self.policy["application_keys"]
        self.assertEqual("blocked-key-inventory-and-recovery-unselected", keys["status"])
        self.assertEqual(
            "unselected-until-pinned-upstream-release", keys["exact_key_names"]
        )
        self.assertEqual(
            ["AUTH_SECRET", "OAUTH_CLIENT_SECRET"], keys["candidate_required_names"]
        )
        self.assertEqual([], keys["candidate_conditional_names"])
        self.assertEqual(["ENCRYPTION_SECRET"], keys["unverified_or_absent_upstream_keys"])
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
            "blocked-upstream-startup-migration-not-fail-closed", migration["status"]
        )
        self.assertEqual("present-and-unaccepted", migration["upstream_startup_migration_behavior"])
        self.assertEqual("absent-blocker", migration["migration_failure_propagation"])
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
            "not-applicable-reviewed-v5-unless-future-release", recovery["redis_scope"]
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
        self.assertNotRegex(combined, re.compile(r"@sha256:[0-9a-f]{64}"))
        self.assertNotIn("/Users/", combined)
        self.assertNotIn("/home/paul/", combined)


if __name__ == "__main__":
    unittest.main()
