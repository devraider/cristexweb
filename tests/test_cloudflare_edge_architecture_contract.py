from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ansible/files/policies/cloudflare-edge-architecture.yml"
RUNBOOK = ROOT / "runbooks/cloudflared-candidate-provenance.md"


class CloudflareEdgeArchitectureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = yaml.safe_load(POLICY.read_text())
        cls.runbook = RUNBOOK.read_text()
        cls.normalized = " ".join(cls.runbook.split())

    def test_exact_phased_private_origin_path(self) -> None:
        path = self.policy["traffic_path"]
        self.assertEqual(
            "Cloudflare -> cloudflared/platform-edge -> Traefik/kube-system -> Keycloak/shared-services",
            path["flow"],
        )
        self.assertEqual("platform-edge", path["connector_namespace"])
        self.assertEqual("kube-system", path["ingress_controller_namespace"])
        self.assertEqual("shared-services", path["private_origin_namespace"])
        self.assertEqual("keycloak", path["private_origin_service"])
        self.assertTrue(path["direct_origin_wan_exposure"] == "forbidden")
        self.assertTrue(path["origin_network_scope"] == "cluster-internal-only")
        self.assertEqual("http://traefik.kube-system.svc.cluster.local:80", self.policy["route"]["target"])

    def test_explicit_approval_boundaries_and_blocked_runtime(self) -> None:
        approvals = self.policy["approvals"]
        self.assertTrue(approvals["no_phase_implies_another"])
        self.assertEqual("not-run-blocked", approvals["runtime_status"])
        for phase in (
            "cloudflare_account_and_zone_read",
            "opentofu_provider_state_recovery",
            "tunnel_creation_and_token_materialization",
            "private_connector_reconciliation",
            "traefik_route_reconciliation",
            "dns_hostname_publication",
            "public_validation",
            "production_cutover",
        ):
            self.assertEqual("separate", approvals["phases"][phase])
        self.assertTrue(self.policy["executable_source_allowed"])
        self.assertEqual("selected-source-runtime-blocked", self.policy["runtime_source_status"])
        self.assertIn("Each phase requires its own review and approval", self.normalized)
        self.assertIn("No runtime phase is currently approved or run", self.normalized)
        self.assertIn("source closures exist", self.normalized)

    def test_secret_and_surface_boundaries(self) -> None:
        token = self.policy["cloudflared"]
        self.assertEqual("prod:/platform-edge/cloudflared", token["token_path"])
        self.assertEqual("CLOUDFLARE_TUNNEL_TOKEN", token["token_key"])
        for field in (
            "token_in_git",
            "token_in_opentofu_state",
            "token_in_argv",
            "token_in_environment_examples",
            "token_in_logs_or_evidence",
        ):
            self.assertFalse(token[field])
        self.assertTrue(token["health_endpoint_not_sufficient"])
        self.assertTrue(token["public_service_or_ingress"] == "forbidden")
        self.assertEqual("exact-reviewed-hostname-route", self.policy["route"]["mode"])
        self.assertTrue(self.policy["route"]["admin_management_negative_test_required"])
        self.assertTrue(self.policy["route"]["direct_origin_negative_test_required"])
        self.assertTrue(self.policy["network_policy"]["default"] == "deny")
        for forbidden in (
            "public-keycloak-admin",
            "public-keycloak-management",
            "public-argocd",
            "public-databases",
            "direct-origin-wan",
        ):
            self.assertIn(forbidden, self.policy["network_policy"]["denied"])

    def test_rollback_and_no_runtime_source(self) -> None:
        rollback = self.policy["rollback"]
        self.assertEqual("git-revert-and-disable-exact-route", rollback["preferred"])
        self.assertIn("route-disabled", rollback["evidence_required"])
        self.assertIn("private-keycloak-still-healthy", rollback["evidence_required"])
        self.assertIn("no-token-residue", rollback["evidence_required"])
        self.assertIn("Routine rollback must not use blind destroy", self.normalized)
        self.assertNotIn("CLOUDFLARE_TUNNEL_TOKEN=", self.runbook)
        self.assertNotIn("cloudflared tunnel run", self.runbook.lower())


if __name__ == "__main__":
    unittest.main()
