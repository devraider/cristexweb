from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "runbooks" / "argocd-hardened-design.md"
KUBERNETES = ROOT / "kubernetes"
OPENTOFU = ROOT / "opentofu"


class ArgoCdHardenedDesignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = RUNBOOK.read_text()

    def table(self, heading: str) -> dict[str, tuple[str, ...]]:
        section = self.text.split(heading, 1)[1]
        next_heading = section.find("\n## ")
        if next_heading >= 0:
            section = section[:next_heading]
        rows: dict[str, tuple[str, ...]] = {}
        for line in section.splitlines():
            if not line.startswith("|"):
                continue
            cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
            if cells[0] in {"Flow", "Project", "Material", "ID"}:
                continue
            if all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            self.assertNotIn(cells[0], rows)
            rows[cells[0]] = cells[1:]
        return rows

    def test_status_and_source_only_boundary(self) -> None:
        self.assertTrue(RUNBOOK.is_file())
        for required in (
            "**DESIGN ONLY.**",
            "Chart `10.3.0` and Argo CD `v3.5.0` remain **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED**",
            "Argo CD runtime remains **NOT RUN**",
            "does not select a\nrelease, authorize bootstrap, contact the cluster",
            "does not select a\nrelease, authorize bootstrap, contact the cluster, or add a chart, values file,\nrendered YAML, manifest, Secret, Application, AppProject, NetworkPolicy, RBAC object",
            "Ansible is\nselected as the future bounded bootstrap installer and lifecycle owner of privileged\nCRDs and cluster RBAC",
            "There is no runtime\nrollback because no runtime action occurred",
        ):
            self.assertIn(required, self.text)

    def test_private_admin_and_exposure_closure(self) -> None:
        for required in (
            "Every Argo Service remains `ClusterIP`",
            "no Ingress, Gateway API\nroute, Traefik route, NodePort, LoadBalancer, `externalIPs`, host port, Cloudflare\nroute, or public DNS route",
            "authorized operator device -> Tailscale -> authenticated k3s API -> loopback-only Kubernetes port-forward -> argocd-server",
            "bind only to the operator's loopback interface",
            "No executable invocation or address is\ncommitted here",
            "Server TLS remains\nenabled",
            "Dex and notifications remain absent",
            "Metrics Services and ServiceMonitors remain\nabsent",
        ):
            self.assertIn(required, self.text)

    def test_ansible_bootstrap_and_direct_oidc_boundary(self) -> None:
        for required in (
            "Ansible is\nselected as the future bounded bootstrap installer",
            "lifecycle owner of privileged\nCRDs and cluster RBAC",
            "Direct OIDC to the future selected shared Keycloak is the intended design",
            "stable issuer,\ncallback, TLS, NetworkPolicy, Secret, and positive/negative authorization evidence",
            "Direct Keycloak OIDC client",
            "Infisical-owned client secret after OIDC positive/negative and recovery proof",
        ):
            self.assertIn(required, self.text)

    def test_applicationset_is_retained_and_quiescent(self) -> None:
        for required in (
            "controller is retained with `allowAnyNamespace=false`",
            "SCM providers and\ncredentialed generators remain disabled",
            "no Application create, update, or delete permission",
            "no Secret read permission",
            "still starts its webhook listener",
            "`ClusterIP` Service on TCP `7000`",
            "Webhook exposure and use are disabled, but the listener is not absent",
            "no ApplicationSet-to-Redis flow exists",
        ):
            self.assertIn(required, self.text)
        for forbidden in (
            "ApplicationSet is absent",
            "ApplicationSet is disabled",
            "webhook listener is disabled",
            "applicationSet.enabled: false",
        ):
            self.assertNotIn(forbidden, self.text)

    def test_supplemental_default_deny_flow_matrix_is_complete(self) -> None:
        self.assertIn("Every chart-generated component NetworkPolicy must be disabled", self.text)
        self.assertIn("namespace-wide default-deny selects every `argocd` pod for both ingress and\n  egress", self.text)
        self.assertEqual(
            {
                "server to repo-server": ("TCP `8081`", "Reviewed repository and render requests"),
                "application-controller to repo-server": ("TCP `8081`", "Manifest generation"),
                "ApplicationSet to repo-server": ("TCP `8081`", "Approved non-SCM generator support"),
                "server to Redis": ("TCP `6379`", "Session and cache traffic"),
                "application-controller to Redis": ("TCP `6379`", "Controller cache traffic"),
                "repo-server to Redis": ("TCP `6379`", "Repository cache traffic"),
                "server to API class": ("TCP `443` and conservative translated TCP `6443`", "Argo control-plane access"),
                "application-controller to API class": ("TCP `443` and conservative translated TCP `6443`", "Watches and reconciliation"),
                "ApplicationSet to API class": ("TCP `443` and conservative translated TCP `6443`", "Bounded Argo-resource reconciliation"),
                "repo-server to approved HTTPS": ("broad TCP `443`", "Exact private repository and reviewed HTTPS dependencies"),
                "server to selected OIDC issuer": ("conditional future TCP `443`", "Direct OIDC discovery, code exchange, and key retrieval only after identity approval"),
                "DNS clients to CoreDNS": ("UDP/TCP `53`", "Name resolution for controller, server, repo-server, and ApplicationSet"),
                "loopback port-forward to server": ("node-origin stream to TCP `8080`", "Private UI, API, and gRPC administration"),
            },
            self.table("### Component flow closure"),
        )
        for required in (
            "permit arbitrary destinations on those ports",
            "explicit port\nisolation, not GitHub isolation, Kubernetes-Service isolation, FQDN isolation, TLS\nidentity isolation, or endpoint isolation",
            "Redis receives no DNS allowance and no egress",
            "Whether kube-router enforces policy before\nor after Kubernetes Service DNAT",
            "observes API traffic on Service port\n`443`, translated port `6443`, or both—remains unproven",
            "separately approved live\npositive/negative acceptance must prove that behavior; failure is a stop condition",
            "`redisSecretInit.enabled=false`",
            "`argocd-redis` must be precreated",
            "retained initializer in a future render is a stop condition",
        ):
            self.assertIn(required, self.text)

    def test_rbac_and_appproject_phases_fail_closed(self) -> None:
        for required in (
            "AppProject policy and Kubernetes RBAC are independent enforcement layers",
            "Kubernetes\nRBAC must be equal to or narrower",
            "Ansible is selected for a future bounded privileged installation phase",
            "Ansible remains lifecycle owner of Argo CRDs,\nClusterRoles, and ClusterRoleBindings",
            "server does not receive the chart's broad ClusterRole",
            "Repo-server has a dedicated ServiceAccount, no API token, no Role, and no\n  RoleBinding",
            "Initial runtime rules omit `delete`, `deletecollection`, `escalate`, `bind`",
            "No runtime identity may create future\nNamespaces",
            "built-in `default` AppProject becomes effective deny-all",
            "One shared controller identity remains a common DEV/PROD compromise domain",
        ):
            self.assertIn(required, self.text)
        projects = self.table("### Project model")
        self.assertEqual(
            {
                "`namespace-adoption`",
                "`argocd-system`",
                "`platform-edge`",
                "`shared-services`",
                "`cristexhub-dev`",
                "`cristexhub-prod`",
            },
            set(projects),
        )

    def test_private_git_secret_custody_and_recovery(self) -> None:
        for required in (
            "one private GitHub App scoped to exactly one future\nselected private repository",
            "repository `Contents: read-only`",
            "no write,\nadministration, webhook, organization, Actions, or unrelated permission",
            "canonical HTTPS repository URL with normal TLS verification",
            "one direct,\nproject-scoped `repository` Secret",
            "no broad `repo-creds` prefix template",
            "Secret object, private key, IDs, and every credential value\nare absent from this increment",
            "value-free custody ledger",
            "`argocd-initial-admin-secret` must remain absent",
            "Infisical receives only the\nsuccessor",
            "fresh repository read",
            "separately\napproved revocation",
            "Independent encrypted off-node custody",
        ):
            self.assertIn(required, self.text)
        self.assertEqual(
            {
                "`argocd-secret` and signing key",
                "One-time local administrator state",
                "`argocd-redis`",
                "`argocd-server-tls`",
                "Direct repository credential",
                "Direct Keycloak OIDC client",
                "Infisical authentication",
            },
            set(self.table("## Private Git and value-free secret custody")),
        )

    def test_two_application_namespace_adoption(self) -> None:
        for required in (
            "two future adoption Applications: one renders only\n`platform-edge`, and one renders only `argocd`",
            "separate reviewed source entry points are required in a\nlater deployable-source change",
            "registered without sync",
            "Automated sync, prune, self-heal,\nApplication finalizers, `CreateNamespace`, managed namespace metadata, `Replace`,\n`Force`, cascading deletion, and shared-resource acceptance remain disabled",
            "No\nserver-side-apply choice is made",
            "First-sync apply mode remains unresolved",
            "Adoption order is `platform-edge` first",
            "unchanged UID",
            "Only successful sync evidence may establish Argo ownership",
        ):
            self.assertIn(required, self.text)

    def test_stop_rollback_and_exact_open_decisions(self) -> None:
        for required in (
            "Future work stops on secret disclosure, public Argo reachability",
            "any chart-generated permissive NetworkPolicy",
            "Routine rollback never deletes or recreates a Namespace",
            "performs a release-wide\nuninstall",
            "revokes a\nworking predecessor before successor acceptance",
            "This source-only increment has only Git revert as rollback",
        ):
            self.assertIn(required, self.text)
        self.assertEqual(
            {
                "D1": ("Exact Ansible bootstrap closure and credentials", "Installer and privileged lifecycle owner are selected, but exact source, objects, credential lifetime, escalation controls, and separate approvals remain undefined"),
                "D2": ("Foundation Namespace runtime checkpoints", "Exact `platform-secrets` and `platform-identity` source and a distinct present-only wrapper exist, but check, first apply, and idempotence remain separately approved and NOT RUN; the earlier exception remains closed"),
                "D3": ("Exact resource, GVR, and discovery inventory", "Runtime Roles and Projects cannot be authored safely before every required kind and discovery path is enumerated"),
                "D4": ("Infisical authentication and independent recovery", "Authentication method, scope, custodians, RPO/RTO, and isolated recovery remain unselected"),
                "D5": ("Live Namespace-adoption apply mode", "Managed-field, tracking, last-applied, and diff evidence is unavailable until a separately approved read-only checkpoint"),
                "D6": ("Stable Keycloak issuer and Argo OIDC/RBAC", "Release, private callback, TLS, client secret, group mappings, negative authorization, logout, and recovery evidence remain absent"),
            },
            self.table("## Open architecture decisions"),
        )

    def test_secret_address_command_and_source_hygiene(self) -> None:
        self.assertNotIn("```", self.text)
        self.assertNotIn(".pi-subagents", self.text)
        forbidden_patterns = (
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"\bghp_[A-Za-z0-9]+\b",
            r"\bgithub_pat_[A-Za-z0-9_]+\b",
            r"(?im)^\s*(?:certificate-authority-data|client-certificate-data|client-key-data|token):\s*\S+",
            r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
            r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
            r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
            r"/Users/[^/\s]+/",
        )
        for pattern in forbidden_patterns:
            self.assertNotRegex(self.text, pattern)
        for forbidden in (
            "kubectl ",
            "helm install",
            "helm upgrade",
            "helm uninstall",
            "argocd app ",
            "tofu apply",
            "ansible-playbook ",
            "--address",
        ):
            self.assertNotIn(forbidden, self.text.lower())

        self.assertEqual(
            {
                "platform/namespaces/argocd.yaml",
                "platform/namespaces/platform-edge.yaml",
                "platform/namespaces/platform-secrets.yaml",
                "platform/namespaces/platform-identity.yaml",
            },
            {
                str(path.relative_to(KUBERNETES))
                for path in KUBERNETES.rglob("*")
                if path.is_file()
            },
        )
        self.assertFalse(any(path.name in {"Chart.yaml", "values.yaml"} for path in KUBERNETES.rglob("*")))
        self.assertEqual(
            {"README.md", "backend.tf", "providers.tf", "versions.tf"},
            {path.name for path in OPENTOFU.iterdir() if path.is_file()},
        )
        combined_tofu = "\n".join(path.read_text() for path in OPENTOFU.glob("*.tf"))
        self.assertNotRegex(combined_tofu, r"(?m)^\s*(?:resource|data|module|import|variable|output)\s+")
        self.assertFalse((ROOT / ".github/workflows").exists())
        self.assertFalse(any("argocd" in str(path.relative_to(ROOT / "ansible")) for path in (ROOT / "ansible").rglob("*") if path.is_file()))

    def test_design_traceability_links(self) -> None:
        for relative in (
            "README.md",
            "architecture-plan.md",
            "specs/k3s-iac-foundation/brief.md",
            "specs/k3s-iac-foundation/manual-qa.md",
            "specs/k3s-iac-foundation/requirements.md",
            "specs/k3s-iac-foundation/status.md",
            "specs/k3s-iac-foundation/tasks.md",
            "specs/k3s-iac-foundation/testcases.md",
        ):
            self.assertIn("argocd-hardened-design.md", (ROOT / relative).read_text(), relative)


if __name__ == "__main__":
    unittest.main()
