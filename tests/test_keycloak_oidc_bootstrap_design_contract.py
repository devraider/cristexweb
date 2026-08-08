from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "runbooks" / "keycloak-oidc-bootstrap-design.md"
KUBERNETES = ROOT / "kubernetes"
OPENTOFU = ROOT / "opentofu"


class KeycloakOidcBootstrapDesignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = RUNBOOK.read_text()

    def test_design_only_target_without_release_or_runtime_selection(self) -> None:
        for required in (
            "**DESIGN ONLY.**",
            "One future self-hosted Keycloak shared by CristexHub, Reactive\nResume, and Argo CD is selected as the identity architecture target",
            "No Keycloak\nrelease, image tag or digest, package, operator, chart, database version, hostname,\nroute, manifest, values file, credential, or deployable source is selected",
            "Keycloak\nruntime remains **NOT RUN**",
            "authorizes no discovery, check, installation, Secret operation, database\nmutation, route, or cluster contact",
            "CANDIDATE — NOT DEPLOYABLE — NOT SELECTED",
        ):
            self.assertIn(required, self.text)

    def test_ansible_bootstrap_lifecycle_and_handoff_have_one_writer(self) -> None:
        for required in (
            "Ansible is selected as the future bounded bootstrap installer",
            "Each component requires a separate exact\nsource closure, dedicated non-passthrough entrypoint, reviewed check/diff, separately\napproved apply, and separately approved idempotence checkpoint",
            "Ansible remains lifecycle owner of foundation CRDs, ClusterRoles,\nClusterRoleBindings, and Keycloak realm, client, group, and group-claim\nreconciliation",
            "only after its exact writer is stopped",
            "Ansible and Argo must never\nreconcile the same object concurrently",
            "old\nwrapper is unchanged and must not be reused or reopened",
        ):
            self.assertIn(required, self.text)

    def test_identity_and_authorization_layers_are_independent(self) -> None:
        for required in (
            "Keycloak | Authenticate people and emit reviewed group claims",
            "Argo CD RBAC | Map exact Keycloak groups to Argo administrator or read-only capabilities",
            "Kubernetes RBAC | Limit Argo ServiceAccounts",
            "Keycloak administrator group never implies Kubernetes administrator access",
            "Direct\nArgo OIDC is the intended design and Dex remains absent",
            "OIDC client secret is an Infisical-owned value",
            "Local Argo authentication is one-time bootstrap",
            "read-only mutation denial, ungrouped denial, invalid and\nexpired token denial, logout behavior, and break-glass recovery all pass",
        ):
            self.assertIn(required, self.text)

    def test_external_development_assets_are_not_deployable_source(self) -> None:
        for required in (
            "existing CristexHub Compose Keycloak, realm export, theme, local issuer, local\nredirects, development users, development passwords, and bootstrap defaults remain\nexternal development-only inputs",
            "must not be copied here",
            "Development startup, an embedded development database, mutable image tags",
            "default administrator\ncredentials are forbidden",
        ):
            self.assertIn(required, self.text)

    def test_production_database_backup_and_restore_gates_fail_closed(self) -> None:
        for required in (
            "selected immutable `linux/amd64` image and production\nstartup, never `start-dev`",
            "dedicated external PostgreSQL database, database principal, and\nPVC",
            "Before\nthe first private bootstrap, the database/storage design, backup tooling and\ndestination, encryption/key custody, integrity procedure, restore procedure, and\nprovisional RPO/RTO must be reviewed and approved",
            "first separately approved\nbootstrap remains non-authoritative: it creates only controlled test identity state",
            "application-consistent `pg_dump` backup rather than live-volume synchronization",
            "timestamped non-destructive off-node copy",
            "integrity verification and retention policy",
            "isolated restore rehearsal covering database, roles, controlled test realm\n  state, and clients",
            "declared and measured RPO/RTO",
            "Before authoritative identity state is accepted or OIDC is enabled",
            "PVC deletion, database recreation, realm re-import, and release downgrade are never\nroutine rollback",
        ):
            self.assertIn(required, self.text)

    def test_stable_issuer_private_admin_and_later_public_auth_are_separate(self) -> None:
        for required in (
            "one stable TLS identity from the first accepted login",
            "Keycloak administration and its management health/metrics surface remain private",
            "No public Keycloak route is\nauthorized now",
            "later public browser-auth route may expose only the reviewed authentication surface",
            "Public authentication never makes the admin console, management\nlistener, database, Argo CD, k3s API, or host publicly reachable",
            "Argo server to selected stable OIDC issuer",
            "PostgreSQL accepts only Keycloak and bounded backup/restore identities",
        ):
            self.assertIn(required, self.text)

    def test_secret_zero_sequence_is_non_circular_and_runtime_gated(self) -> None:
        for required in (
            "Infisical Cloud remains the secret-value owner; only its Kubernetes Operator",
            "Self-hosted Infisical is not selected",
            "successor must pass fresh behavior, scope, disclosure, rotation, and recovery checks",
            "future sequence is fixed but authorizes no step",
            "Infisical materializes the exact precreated Argo Secrets",
            "separately approved private, non-authoritative Ansible bootstrap creates only\n   controlled test identity state",
            "restored in isolation with measured RPO/RTO before authoritative identity state\n   is accepted or OIDC is enabled",
            "namespaced specifications hand off one exact object set at a time",
            "No visual placeholder, ephemeral Keycloak,\ndevelopment database, or temporary public route is acceptable",
        ):
            self.assertIn(required, self.text)

    def test_foundation_namespace_source_exists_without_runtime_or_workload_source(self) -> None:
        self.assertIn("`platform-secrets` and `platform-identity` now have exact present-only\nNamespace source", self.text)
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
        ansible_files = {
            str(path.relative_to(ROOT / "ansible"))
            for path in (ROOT / "ansible").rglob("*")
            if path.is_file()
        }
        self.assertFalse(any("keycloak" in path.lower() for path in ansible_files))
        self.assertFalse(any("argocd" in path.lower() for path in ansible_files))
        self.assertFalse(any("infisical" in path.lower() for path in ansible_files))

    def test_secret_address_command_and_traceability_hygiene(self) -> None:
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

        for relative in (
            "AGENTS.md",
            "README.md",
            "ansible/README.md",
            "architecture-plan.md",
            "specs/k3s-iac-foundation/brief.md",
            "specs/k3s-iac-foundation/manual-qa.md",
            "specs/k3s-iac-foundation/requirements.md",
            "specs/k3s-iac-foundation/status.md",
            "specs/k3s-iac-foundation/tasks.md",
            "specs/k3s-iac-foundation/testcases.md",
        ):
            self.assertIn("keycloak-oidc-bootstrap-design.md", (ROOT / relative).read_text(), relative)


if __name__ == "__main__":
    unittest.main()
