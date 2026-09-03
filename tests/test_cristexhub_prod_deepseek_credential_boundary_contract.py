from __future__ import annotations

import re
import stat
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ansible/files/policies/cristexhub-prod-deepseek-credential-boundary.yml"
RUNBOOK = ROOT / "runbooks/cristexhub-prod-deepseek-credential-boundary.md"
MAIN_POLICY = ROOT / "ansible/files/policies/cristexhub-prod-credential-rotation-gates.yml"
MAIN_RUNBOOK = ROOT / "runbooks/cristexhub-prod-credential-rotation-gates.md"
OIDC_PROXY_SOURCE = ROOT / "ansible/files/components/oidc-connect-proxy/config/configmap-oidc-connect-proxy.yaml"


class CristexHubProdDeepSeekCredentialBoundaryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_text = POLICY.read_text()
        cls.runbook = RUNBOOK.read_text()
        cls.main_policy_text = MAIN_POLICY.read_text()
        cls.main_runbook = MAIN_RUNBOOK.read_text()
        cls.policy = yaml.safe_load(cls.policy_text)
        cls.main_policy = yaml.safe_load(cls.main_policy_text)
        cls.normalized = " ".join(cls.runbook.split())

    def test_value_free_source_boundary_and_exact_transport_scope(self) -> None:
        self.assertEqual(0o644, stat.S_IMODE(POLICY.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE(RUNBOOK.stat().st_mode))
        self.assertEqual(
            "cristexhub-prod-deepseek-credential-boundary-v1",
            self.policy["policy_schema"],
        )
        self.assertEqual("source-only-external-owner-unverified", self.policy["policy_status"])
        scope = self.policy["scope"]
        self.assertEqual("deepseek", scope["provider"])
        self.assertEqual("api.deepseek.com", scope["api_host"])
        self.assertEqual(443, scope["api_port"])
        self.assertEqual("transport-only", scope["transport"]["proof"])
        self.assertTrue(scope["transport"]["unauthenticated_status_is_not_credential_acceptance"])
        self.assertEqual("NOT-RUN-BLOCKED", scope["current_status"])
        self.assertIn("api.deepseek.com:443", self.normalized)
        self.assertIn("unauthenticated `/models` response is transport smoke only", self.normalized)
        self.assertIn("api.deepseek.com", OIDC_PROXY_SOURCE.read_text())

    def test_main_rotation_contract_points_to_this_boundary(self) -> None:
        deepseek = self.main_policy["rotations"]["deepseek"]
        self.assertEqual(
            "ansible/files/policies/cristexhub-prod-deepseek-credential-boundary.yml",
            deepseek["boundary_policy"],
        )
        self.assertEqual(
            "external-application-owner-and-deepseek-account-owner",
            deepseek["owner_action"],
        )
        self.assertEqual("protected-metadata-only", deepseek["exact_target_discovery"])
        self.assertEqual("forbidden-unless-ownership-is-proven", deepseek["provider_revocation"])
        self.assertIn("separate [DeepSeek credential boundary]", self.main_runbook)

    def test_external_owner_and_provider_account_actions_are_explicit(self) -> None:
        application = self.policy["external_owner_actions"]["application_owner"]
        self.assertEqual("cristexhub-application", self.policy["application_target"]["owner"])
        self.assertEqual("devraider/cristexhub", self.policy["application_target"]["repository"])
        self.assertEqual("exact-application-secret-source-and-consumer", application["authority"])
        self.assertIn("identify_exact_secret_manager_path_and_key_by_metadata_only", application["required_actions"])
        provider = self.policy["external_owner_actions"]["deepseek_account_owner"]
        self.assertEqual("provider-account-and-api-key-lifecycle", provider["authority"])
        self.assertIn("prove_account_ownership_through_protected_provider_metadata", provider["required_actions"])
        self.assertIn("revoke_the_exposed_predecessor", provider["required_actions"])
        self.assertIn("issue_the_provider_successor", provider["required_actions"])
        self.assertIn("provider-console-or-official-provider-api-owned-by-account-holder", provider["provider_channel"])
        self.assertIn("DeepSeek account owner owns provider API-key lifecycle", self.normalized)

    def test_exact_application_and_infisical_discovery_is_metadata_only(self) -> None:
        target = self.policy["application_target"]["runtime_secret_target"]
        self.assertEqual("absent-from-infrastructure-source", target["status"])
        self.assertEqual("none-in-this-repository", target["name"])
        self.assertEqual("unresolved-until-protected-discovery", target["key"])
        self.assertTrue(target["direct_kubernetes_secret_write"] == "forbidden")
        discovery = self.policy["infisical_target_discovery"]
        self.assertEqual("unresolved", discovery["status"])
        self.assertTrue(discovery["exact_target_required"])
        context = discovery["known_project_context"]
        self.assertEqual("cristexweb-infrastructure", context["project_slug"])
        self.assertEqual("619656da-14f3-4872-857b-be103cdc5326", context["project_id"])
        self.assertEqual("prod", context["environment_slug"])
        self.assertTrue(context["context_is_not_target_proof"])
        for field in (
            "project_id",
            "environment_slug",
            "secret_path",
            "secret_key_name",
            "source_revision",
            "target_secret_name",
            "target_secret_type",
            "target_owner_labels",
            "consumer_environment_variable_name",
        ):
            self.assertEqual("metadata-only", discovery["accepted_only_after_application_owner_proof"][field])
        for forbidden in (
            "plaintext_secret_value",
            "decoded_secret_value",
            "base64_secret_data",
            "authorization_header",
            "provider_token",
            "connection_string_with_credentials",
        ):
            self.assertIn(forbidden, discovery["forbidden_discovery_fields"])
        for phrase in (
            "one complete source path/key",
            "ordinary kubernetes secret json",
            "do not add `DEEPSEEK_API_KEY`",
            "do not infer that the key is under `/cristexhub/prod/runtime`",
        ):
            self.assertIn(phrase.lower(), self.normalized.lower())

    def test_infrastructure_provider_revocation_is_forbidden_without_ownership_proof(self) -> None:
        infra = self.policy["external_owner_actions"]["infrastructure_repository"]
        self.assertEqual("forbidden-unless-ownership-is-proven", infra["provider_revocation"])
        self.assertEqual("absent", infra["current_provider_authority"])
        self.assertEqual("absent", infra["provider_credentials"])
        self.assertTrue(infra["provider_api_calls"] == "forbidden")
        self.assertTrue(infra["no_exception_implementation_in_this_repository"])
        required = set(infra["exception_requires_all"])
        self.assertIn("explicit_human_ownership_transfer_to_this_infrastructure_owner", required)
        self.assertIn("protected_provider_account_ownership_receipt", required)
        self.assertIn("dedicated_source_hash_bound_guarded_lane", required)
        self.assertIn("separate_provider_revocation_approval", required)
        for phrase in (
            "Provider revocation from here is **forbidden unless ownership is proven**",
            "No such exception implementation exists here",
            "A check result from this source can never itself authorize provider revocation",
        ):
            self.assertIn(phrase, self.normalized)

    def test_check_only_evidence_and_stop_states_are_closed(self) -> None:
        evidence = self.policy["check_only_evidence"]
        self.assertEqual("NOT-RUN-BLOCKED", evidence["status"])
        self.assertEqual("source-only-check-only", evidence["mode"])
        self.assertEqual("forbidden", evidence["runtime_or_provider_action"])
        self.assertTrue(evidence["no_value_output"])
        self.assertTrue(evidence["no_value_persistence"])
        for key in (
            "owner_identity_proved",
            "provider_account_ownership_proved",
            "exact_application_target_proved",
            "exact_infisical_target_proved",
            "predecessor_identity_proved",
            "successor_issued",
            "successor_reconciled_to_private_consumer",
            "predecessor_revoked",
            "fresh_authentication_failure_proved",
            "plaintext_residue_absent",
        ):
            self.assertFalse(evidence["required_boolean_results"][key])
        for forbidden in (
            "secret_value",
            "secret_data",
            "token",
            "password",
            "authorization_header",
            "request_or_response_body",
            "cookie",
            "connection_string",
        ):
            self.assertIn(forbidden, evidence["receipt_fields_forbidden"])
        for state in (
            "OWNER-UNKNOWN-STOP",
            "PROVIDER-ACCOUNT-UNKNOWN-STOP",
            "APPLICATION-TARGET-UNKNOWN-STOP",
            "INFISICAL-TARGET-UNKNOWN-STOP",
            "PREDECESSOR-UNKNOWN-STOP",
            "SUCCESSOR-UNKNOWN-STOP",
            "CUSTODY-UNKNOWN-STOP",
            "REVISION-UNKNOWN-STOP",
            "PROVIDER-REVOCATION-UNKNOWN-STOP",
            "AUTHENTICATION-ACCEPTANCE-UNKNOWN-STOP",
            "AMBIGUOUS-WRITE-UNKNOWN-STOP",
            "PLAINTEXT-RESIDUE-STOP",
            "PUBLIC-CUTOVER-STOP",
        ):
            self.assertIn(state, self.policy["stop_states"])
            self.assertIn(f"`{state}`", self.runbook)

    def test_safe_order_and_public_gate_are_explicit(self) -> None:
        order = self.policy["state_machine"]["required_order"]
        self.assertEqual("protected_owner_and_account_discovery", order[0])
        self.assertEqual("provider_predecessor_revocation_by_account_owner", order[-3])
        self.assertEqual("sanitized_receipt_and_plaintext_cleanup", order[-1])
        self.assertEqual("stop-state", self.policy["state_machine"]["any_unknown_or_ambiguous_result"])
        public = self.policy["public_cutover"]
        self.assertEqual("forbidden", public["status"])
        self.assertTrue(public["no_public_route_mutation"])
        self.assertTrue(public["no_cloudflare_provider_operation"])
        self.assertTrue(public["no_infrastructure_provider_revocation"])
        for gate in (
            "deepseek_owner_and_account_ownership_proved",
            "exact_application_target_proved",
            "exact_infisical_target_proved_or_external_path_proved",
            "provider_predecessor_revoked",
            "provider_successor_reconciled",
            "private_authenticated_successor_probe_passed",
            "fresh_predecessor_authentication_failure_proved",
        ):
            self.assertIn(gate, public["forbidden_until"])
        for phrase in (
            "Required external actions",
            "Check-only evidence contract",
            "Mandatory order and stop states",
            "PROD public-cutover gate",
            "Nothing in this document authorizes a provider call",
        ):
            self.assertIn(phrase, self.runbook)

    def test_no_values_or_executable_provider_lane(self) -> None:
        combined = f"{self.policy_text}\n{self.runbook}"
        self.assertNotRegex(
            combined,
            r"(?i)(?<![A-Za-z0-9_])(?:api[_ -]?key|secret|token|password)\s*[:=]\s*"
            r"(?!(?:absent|unknown|unresolved|forbidden|metadata-only|false|true|none-in-this-repository)\b)"
            r"[^`\s{][^\n]*",
        )
        self.assertNotRegex(combined, r"(?i)sk-[a-z0-9_-]{12,}")
        self.assertNotRegex(combined, r"-----BEGIN [^-]+ PRIVATE KEY-----")
        self.assertNotIn("kubectl", combined.lower())
        self.assertNotIn("ansible-playbook", combined.lower())
        self.assertNotIn("curl ", combined.lower())
        self.assertNotRegex(combined, r"(?im)^\s*tofu\s")
        self.assertNotIn("provider API call implementation", combined)
        self.assertNotIn("InfisicalStaticSecret", combined)
        self.assertNotIn("DEEPSEEK_API_KEY", self.policy_text)
        for relative in (
            "ansible/bin/rotate-deepseek-cristexhub-prod",
            "ansible/plugins/action/deepseek_credential_rotation_guarded.py",
            "ansible/roles/deepseek_credential_rotation",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)


if __name__ == "__main__":
    unittest.main()
