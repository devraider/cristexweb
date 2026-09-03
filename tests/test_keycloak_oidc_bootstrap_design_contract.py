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

    def test_source_policy_selection_retains_prod_and_adds_dev_source_only_lane(self) -> None:
        for required in (
            "**SOURCE POLICY SELECTED — EXISTING PRIVATE WORKLOAD; DEV SUCCESSOR SOURCE-ONLY.**",
            "shared self-hosted Keycloak workload is an existing private runtime checkpoint",
            "retained PROD-compatibility realm\n`cristexhub`, and issuer `https://auth.cristex-soft.com/realms/cristexhub` remain\ncanonical",
            "Reactive Resume DEV is an explicit\nshared-realm exception",
            "shared login theme and SSO are the same as CristexHub",
            "https://resume-dev.cristex-soft.com",
            "`/api/auth/oauth2/callback/custom`",
            "PKCE `S256`",
            "source-only DEV successor\ncontract now defines realm `cristexhub-dev` and issuer",
            "authorizes only offline source validation",
            "performs no\nAdmin API request and authorizes no apply, Secret operation, database mutation",
            "next transition source\nclosure defines a blocked strict-TLS controller-local Kubernetes API port-forward",
            "four separated Infisical value paths with CAS semantics still unverified",
        ):
            self.assertIn(required, self.text)

    def test_ansible_bootstrap_lifecycle_and_handoff_have_one_writer(self) -> None:
        for required in (
            "Ansible is selected as the future bounded bootstrap installer",
            "Each component requires a separate exact\nsource closure, dedicated non-passthrough entrypoint, reviewed check/diff, separately\napproved apply, and separately approved idempotence checkpoint",
            "Ansible remains lifecycle owner of foundation CRDs, ClusterRoles,\nClusterRoleBindings, and Keycloak realm, client, group, and group-claim\nreconciliation",
            "only after its exact writer is stopped",
            "Ansible and Argo must never\nreconcile the same object concurrently",
            "old\nhistorical wrapper is unchanged and must not be reused or reopened",
        ):
            self.assertIn(required, self.text)

    def test_identity_and_authorization_layers_are_independent(self) -> None:
        for required in (
            "Keycloak | Authenticate people and emit reviewed group claims",
            "Argo CD RBAC | Map exact Keycloak groups to Argo administrator or read-only capabilities",
            "Kubernetes RBAC | Limit Argo ServiceAccounts",
            "Keycloak administrator group never implies Kubernetes administrator access",
            "Direct\nArgo OIDC is the selected direction and Dex remains absent",
            "OIDC client secret is an Infisical-owned value",
            "Local Argo authentication is one-time bootstrap",
            "read-only mutation denial, ungrouped denial, invalid and\nexpired token denial, logout behavior, and break-glass recovery all pass",
        ):
            self.assertIn(required, self.text)

    def test_cristexhub_prod_browser_contract_is_exact_and_value_free(self) -> None:
        for required in (
            "Legacy DEV and private PROD\nconsumers are live on the retained realm; the DEV successor remains unactivated",
            "The `cristexhub-prod` client is confidential, uses\nPKCE `S256`",
            "https://hub.cristex-soft.com/oauth2/callback",
            "https://hub.cristex-soft.com",
            "https://hub.cristex-soft.com/",
            "prod:/cristexhub/prod/runtime",
            "OIDC_CLIENT_SECRET",
            "same source/key projected by the PROD runtime\nStaticSecret",
            "cristexhub-prod-<organization-alias>-<role>",
            "cristexhub-prod-super-admin",
            "Missing, unverified,\nambiguous, unmatched, or cross-environment group claims fail closed",
            "The two administrative service clients remain\n`browser_flow_allowed: false`",
            "existing reviewed browser-auth route and DEV application route are live",
        ):
            self.assertIn(required, self.text)
        self.assertNotIn("client_secret:", self.text)
        self.assertNotIn("client secret:", self.text.lower())

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
            "live Keycloak `26.7.1` workload uses the immutable CristexHub-derived digest",
            "official\nlinux/amd64 digest\n`sha256:7523ccfbd950f59783504cdf5a0138dae48746dfe36075bbfccdb5a9ee245ee2`\nremains upstream selection evidence",
            "a dedicated logical database and dedicated owner role on the one general shared\nPostgreSQL instance",
            "Keycloak remains a separate deployment from PostgreSQL",
            "No\nseparate Keycloak PostgreSQL deployment or PVC is selected",
            "the shared engine and\nPVC remain a shared failure domain",
            "Keycloak role cannot access application databases, and application roles cannot\naccess the Keycloak database",
            "Encrypted\napplication-consistent backup, immutable off-node readback, and isolated restore\nhave runtime evidence",
            "realm/client/admin behavioral recovery, role/ownership\nrestoration, measured RPO/RTO, and full production recovery acceptance remain open",
            "application-consistent `pg_dump` backup rather than live-volume synchronization",
            "timestamped non-destructive off-node copy",
            "integrity verification and retention policy",
            "isolated restore rehearsal covering database, roles, controlled test realm\n  state, and clients",
            "declared and measured RPO/RTO",
            "Before any identity migration or authoritative recovery claim",
            "PVC deletion, database recreation, realm\nre-import, and release downgrade are never routine rollback",
        ):
            self.assertIn(required, self.text)

    def test_stable_issuer_private_admin_and_later_public_auth_are_separate(self) -> None:
        for required in (
            "one stable TLS identity from\nthe first accepted login",
            "Keycloak administration and its management health/metrics surface remain private",
            "existing reviewed browser-auth route and DEV application route are live",
            "`hub.cristex-soft.com` PROD application route remains unapplied",
            "Public authentication never makes the admin console, management\nlistener, database, Argo CD, k3s API, or host publicly reachable",
            "Argo server to selected stable OIDC issuer",
            "The Keycloak database accepts only the dedicated Keycloak role and bounded\nbackup/restore identities; application database roles are denied",
        ):
            self.assertIn(required, self.text)

    def test_secret_zero_sequence_is_non_circular_and_runtime_gated(self) -> None:
        for required in (
            "Infisical Cloud remains the secret-value owner; only its Kubernetes Operator",
            "Self-hosted Infisical is not selected",
            "successor must pass fresh behavior, scope, disclosure, rotation, and recovery checks",
            "remaining sequence is fixed but this design authorizes no additional step",
            "completed foundation checkpoint: the bounded Ansible exception created only the\n   separately approved `shared-services` Namespace",
            "Infisical materializes the exact precreated Argo Secrets",
            "separately approved private, non-authoritative Ansible bootstrap creates only\n   controlled test identity state",
            "restored in isolation with measured RPO/RTO before authoritative identity state\n   is accepted or OIDC is enabled",
            "namespaced specifications hand off one exact object set at a time",
            "No visual placeholder, ephemeral Keycloak,\ndevelopment database, or temporary public route is acceptable",
        ):
            self.assertIn(required, self.text)

    def test_foundation_namespace_exists_without_component_or_workload_source(self) -> None:
        normalized = " ".join(self.text.split())
        self.assertIn("`shared-services` now exists through its distinct bounded Ansible wrapper", normalized)
        self.assertIn("check and separately approved first apply/idempotence passed", normalized)
        self.assertIn("final run at `changed=0`", normalized)
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
        self.assertFalse(any(path.name in {"Chart.yaml", "values.yaml"} for path in KUBERNETES.rglob("*")))
        self.assertEqual(
            {
                ".terraform.lock.hcl", "README.md", "backend.tf", "cloudflare.tf", "outputs.tf",
                "providers.tf", "variables.tf", "versions.tf",
            },
            {path.name for path in OPENTOFU.iterdir() if path.is_file()},
        )
        combined_tofu = "\n".join(path.read_text() for path in OPENTOFU.glob("*.tf"))
        self.assertNotRegex(combined_tofu, r"(?m)^\s*(?:data|module|import)\s+")
        self.assertEqual(
            {"ci.yml"},
            {
                path.name
                for path in (ROOT / ".github/workflows").iterdir()
                if path.is_file()
            },
        )
        operational = [
            path
            for root in (ROOT / "ansible/bin", ROOT / "ansible/playbooks", ROOT / "ansible/roles")
            for path in root.rglob("*")
            if path.is_file()
        ]
        self.assertEqual(
            {
                "ansible/bin/bootstrap-keycloak",
                "ansible/bin/bootstrap-keycloak-route",
                "ansible/playbooks/bootstrap_keycloak.yml",
                "ansible/roles/keycloak_bootstrap/defaults/main.yml",
                "ansible/roles/keycloak_bootstrap/tasks/main.yml",
                "ansible/playbooks/bootstrap_keycloak_route.yml",
                "ansible/roles/keycloak_route_bootstrap/defaults/main.yml",
                "ansible/roles/keycloak_route_bootstrap/tasks/main.yml",
                "ansible/bin/bootstrap-keycloak-dev-identity",
                "ansible/playbooks/bootstrap_keycloak_dev_identity.yml",
                "ansible/roles/keycloak_dev_identity_bootstrap/defaults/main.yml",
                "ansible/roles/keycloak_dev_identity_bootstrap/tasks/main.yml",
                "ansible/bin/bootstrap-keycloak-dev-identity-transition",
                "ansible/playbooks/bootstrap_keycloak_dev_identity_transition.yml",
                "ansible/roles/keycloak_dev_identity_transition_bootstrap/defaults/main.yml",
                "ansible/roles/keycloak_dev_identity_transition_bootstrap/tasks/main.yml",
                "ansible/bin/bootstrap-keycloak-reactive-resume-dev-client",
                "ansible/playbooks/bootstrap_keycloak_reactive_resume_dev_client.yml",
                "ansible/roles/keycloak_reactive_resume_dev_client_bootstrap/defaults/main.yml",
                "ansible/roles/keycloak_reactive_resume_dev_client_bootstrap/tasks/main.yml",
            },
            {
                str(path.relative_to(ROOT))
                for path in operational
                if "keycloak" in str(path).lower() and "backup" not in path.name.lower()
            },
        )
        self.assertEqual(
            {
                "ansible/bin/bootstrap-postgresql",
                "ansible/bin/configure-postgresql-keycloak-backup",
                "ansible/bin/provision-shared-postgresql",
                "ansible/playbooks/bootstrap_postgresql.yml",
                "ansible/playbooks/configure_postgresql_keycloak_backup.yml",
                "ansible/playbooks/provision_shared_postgresql.yml",
                "ansible/roles/postgresql_bootstrap/defaults/main.yml",
                "ansible/roles/postgresql_bootstrap/tasks/main.yml",
                "ansible/roles/shared_postgresql_provisioning/defaults/main.yml",
                "ansible/roles/shared_postgresql_provisioning/tasks/main.yml",
            },
            {
                str(path.relative_to(ROOT))
                for path in operational
                if "postgresql" in str(path).lower()
            },
        )
        expected_public_inputs = {
            "policies/hosted-identity-authorization.yml",
            "policies/reactive-resume-architecture.yml",
            "policies/reactive-resume-postgresql-exposure-rotation.yml",
            "policies/shared-database-architecture.yml",
            "policies/shared-rabbitmq-architecture.yml",
            "policies/shared-stateful-backup-architecture.yml",
            "policies/cloudflare-edge-architecture.yml",
            "policies/infisical-operator-privileged-prerequisites.yml",
            "policies/infisical-operator-implementation-profile.yml",
            "policies/infisical-secret-zero-lane.yml",
            "policies/cristexhub-dev-runtime-materialization.yml",
            "policies/cristexhub-prod-runtime-materialization.yml",
            "policies/argocd-ui-tls-lifecycle.yml",
            "policies/reactive-resume-dev-tls-renewal.yml",
            "policies/reactive-resume-dev-postgresql-successor.yml",
            "vendor/argocd/10.3.0/SHA256SUMS",
            "vendor/argocd/10.3.0/argo-cd-10.3.0.tgz",
            "vendor/argocd/10.3.0/argo-cd-10.3.0.tgz.prov",
            "vendor/argocd/10.3.0/pgp_keys.asc",
            "vendor/infisical-operator/0.11.7/SHA256SUMS",
            "vendor/infisical-operator/0.11.7/cloudsmith-signing-key.asc",
            "vendor/infisical-operator/0.11.7/kubernetes-operator-64d2d81.tar.gz",
            "vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz",
            "vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz.prov",
        }
        for component in (
            "infisical-operator",
            "argocd",
            "argocd-route",
            "reactive-resume-dev-route",
            "reactive-resume-dev-tls",
            "reactive-resume-dev-argocd-registration",
            "reactive-resume-dev-argocd",
            "keycloak-reactive-resume-dev-client",
            "reactive-resume-dev-networkpolicy",
            "reactive-resume-object-storage-history",
            "infisical-reactive-resume-dev-ca",
            "cristexhub-dev-registration",
            "cristexhub-prod-registration",
            "cristexhub-dev-sync-transition",
            "infisical-cristexhub-dev-runtime",
            "infisical-cristexhub-prod-runtime",
            "oidc-connect-proxy",
            "infisical-argocd-secrets",
            "infisical-database-secrets",
            "infisical-keycloak-secrets",
            "infisical-rabbitmq-secrets",
            "cloudflared",
            "infisical-cloudflared-secrets",
            "keycloak-route",
            "keycloak-dev-identity",
            "keycloak-dev-identity-transition",
            "rabbitmq",
            "mongodb",
            "mongodb-operator",
            "postgresql",
            "cloudnative-pg",
            "keycloak",
            "shared-mongodb-networkpolicy",
            "reactive-resume-dev-successor",
        ):
            expected_public_inputs.update(
                str(path.relative_to(ROOT / "ansible/files"))
                for path in (ROOT / "ansible/files/components" / component).rglob("*")
                if path.is_file()
            )
        expected_public_inputs.update(
            str(path.relative_to(ROOT / "ansible/files"))
            for path in (ROOT / "ansible/files/policies/reactive-resume-dev-argocd-handoff").rglob("*")
            if path.is_file()
        )
        expected_public_inputs.add("policies/cristexhub-prod-credential-rotation-gates.yml")
        expected_public_inputs.add("policies/cristexhub-prod-mongodb-credential-rotation.yml")
        expected_public_inputs.add("policies/cristexhub-prod-rabbitmq-credential-rotation.yml")
        expected_public_inputs.add("policies/cristexhub-prod-deepseek-credential-boundary.yml")
        expected_public_inputs.add("policies/cristexhub-prod-ghcr-pull-rotation.yml")
        expected_public_inputs.add("components/cristexhub-prod-ghcr-pull-rotation/SOURCE-CLOSURE.sha256")
        for source_directory in ("database-provisioning", "backup"):
            expected_public_inputs.update(
                str(path.relative_to(ROOT / "ansible/files"))
                for path in (ROOT / "ansible/files" / source_directory).rglob("*")
                if path.is_file()
            )
        self.assertEqual(
            expected_public_inputs,
            {
                str(path.relative_to(ROOT / "ansible/files"))
                for path in (ROOT / "ansible/files").rglob("*")
                if path.is_file()
            },
        )

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
