from __future__ import annotations

import hashlib
import re
import tarfile
import unittest
from pathlib import Path, PurePosixPath

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARCHIVE = (
    ROOT
    / "ansible/files/vendor/infisical-operator/0.11.7/"
    "kubernetes-operator-64d2d81.tar.gz"
)
POLICY = ROOT / "ansible/files/policies/infisical-operator-implementation-profile.yml"
RUNBOOK = ROOT / "runbooks/infisical-operator-implementation-profile.md"
KUBERNETES = ROOT / "kubernetes"
SOURCE_SHA256 = "a08141c750404c653d23b35ecb29ab33e788845c3f666f0984fa156b9c468415"
SOURCE_COMMIT = "64d2d81da3707d81dc271410da6fd88254b6c9b3"
SOURCE_ROOT = f"kubernetes-operator-{SOURCE_COMMIT}"


class InfisicalOperatorImplementationProfileContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_text = POLICY.read_text()
        cls.policy = yaml.safe_load(cls.policy_text)
        cls.runbook = RUNBOOK.read_text()
        with tarfile.open(SOURCE_ARCHIVE, "r:gz") as bundle:
            cls.members = bundle.getmembers()
            cls.files = {
                member.name: bundle.extractfile(member).read().decode()
                for member in cls.members
                if member.isfile()
            }

    def source(self, relative: str) -> str:
        return self.files[f"{SOURCE_ROOT}/{relative}"]

    def test_hash_bound_official_source_archive_is_safe_and_exact(self) -> None:
        self.assertEqual(
            SOURCE_SHA256, hashlib.sha256(SOURCE_ARCHIVE.read_bytes()).hexdigest()
        )
        self.assertEqual(307, len(self.members))
        for embedded in (
            f"{SOURCE_ROOT}/kubectl-install/install-secrets-operator.yaml",
            f"{SOURCE_ROOT}/helm-charts/secrets-operator/templates/deployment.yaml",
            f"{SOURCE_ROOT}/config/manager/manager.yaml",
            f"{SOURCE_ROOT}/Dockerfile",
            f"{SOURCE_ROOT}/.github/workflows/release_docker_k8_operator.yaml",
        ):
            self.assertIn(embedded, self.files)
        for member in self.members:
            path = PurePosixPath(member.name)
            self.assertFalse(path.is_absolute(), member.name)
            self.assertNotIn("..", path.parts, member.name)
            self.assertTrue(member.isfile() or member.isdir(), (member.name, member.type))
            self.assertEqual(SOURCE_ROOT, path.parts[0])
        sums = (
            ROOT
            / "ansible/files/vendor/infisical-operator/0.11.7/SHA256SUMS"
        ).read_text()
        self.assertIn(
            f"{SOURCE_SHA256}  kubernetes-operator-64d2d81.tar.gz", sums
        )
        release_selection = " ".join(
            (
                ROOT / "runbooks/infisical-operator-release-selection.md"
            ).read_text().split()
        )
        for required in (
            "kubernetes-operator-64d2d81.tar.gz",
            SOURCE_COMMIT,
            SOURCE_SHA256,
            "quarantined evidence only",
            "not an operational input or promoted object closure",
        ):
            self.assertIn(required, release_selection)

    def test_commit_source_proves_scope_controller_and_auth_behavior(self) -> None:
        main = self.source("cmd/main.go")
        for required in (
            'flag.StringVar(&namespaces, "namespaces", ""',
            'flag.StringVar(&metricsAddr, "metrics-bind-address", "0"',
            "cache.Options{",
            "DefaultNamespaces: defaultNamespaces",
            "InfisicalSecretReconciler",
            "InfisicalPushSecretReconciler",
            "InfisicalDynamicSecretReconciler",
            "InfisicalConnectionReconciler",
            "InfisicalAuthReconciler",
            "InfisicalStaticSecretReconciler",
        ):
            self.assertIn(required, main)
        self.assertNotIn("ClusterGeneratorReconciler", main)

        push = self.source("internal/services/infisicalpushsecret/reconciler.go")
        self.assertIn("v1alpha1.ClusterGenerator{}", push)
        self.assertIn(
            "r.Client.Get(ctx, types.NamespacedName{Name: generatorRef.Name}, clusterGenerator)",
            push,
        )

        universal = self.source("internal/auth/universal.go")
        self.assertIn("UniversalAuthLogin", universal)
        self.assertIn("ClientIdRef", universal)
        self.assertIn("ClientSecretRef", universal)
        for forbidden in ("TokenReview", "ServiceAccount", "CreateToken"):
            self.assertNotIn(forbidden, universal)

    def test_selected_profile_is_exact_separated_and_fail_closed(self) -> None:
        self.assertEqual(
            "deployable-idle-source-selected-runtime-blocked",
            self.policy["policy_status"],
        )
        self.assertEqual(SOURCE_COMMIT, self.policy["source"]["commit"])
        self.assertEqual(SOURCE_SHA256, self.policy["source"]["archive_sha256"])
        self.assertTrue(self.policy["source"]["controller_source_audit_complete"])
        self.assertTrue(
            self.policy["source"]["evidence_archive_contains_upstream_deployable_material"]
        )
        self.assertFalse(
            self.policy["source"]["evidence_archive_operational_input_allowed"]
        )

        runtime = self.policy["runtime_profile"]
        self.assertEqual("shared-services", runtime["controller_namespace"])
        self.assertEqual(
            ["shared-services", "argocd", "cristexhub-dev", "cristexhub-prod", "platform-edge"],
            runtime["watched_namespaces"],
        )
        self.assertEqual("0", runtime["metrics_bind_address"])
        self.assertEqual(1, runtime["replicas"])
        self.assertEqual(
            "docker.io/infisical/kubernetes-operator:v0.11.7@"
            "sha256:5f1767f440407d8f10fb8bd7e051e26ecf18f16731a64273c20fe206947510ae",
            runtime["image"],
        )
        self.assertTrue(runtime["prod_watched"])
        self.assertFalse(runtime["cluster_generator_controller_registered"])
        self.assertFalse(runtime["cluster_generator_eager_watch_registered"])
        self.assertTrue(runtime["cluster_generator_access_on_demand_only"])
        self.assertTrue(runtime["cluster_generator_lazy_informer_possible_if_referenced"])
        self.assertFalse(runtime["cluster_generator_references_supported"])

        rbac = self.policy["rbac_profile"]
        self.assertFalse(rbac["manager_cluster_role_allowed"])
        self.assertEqual(
            ["shared-services", "argocd", "cristexhub-dev", "cristexhub-prod", "platform-edge"],
            rbac["namespaced_roles_required"],
        )
        self.assertFalse(rbac["cluster_generator_permissions_allowed"])
        self.assertFalse(rbac["token_review_allowed"])
        self.assertFalse(rbac["service_account_token_creation_allowed"])
        self.assertEqual(
            [
                "infisicalsecrets",
                "infisicalpushsecrets",
                "infisicaldynamicsecrets",
                "infisicalconnections",
                "infisicalauths",
                "infisicalstaticsecrets",
            ],
            rbac["startup_namespaced_cr_watch_resources"],
        )

        scopes = self.policy["secret_scope_profile"]
        self.assertEqual(
            ["shared-services", "argocd", "cristexhub-dev", "cristexhub-prod", "platform-edge"],
            [scope["namespace"] for scope in scopes],
        )
        self.assertEqual(5, len({scope["logical_identity"] for scope in scopes}))
        self.assertTrue(all(scope["credentials_shared"] is False for scope in scopes))
        self.assertTrue(all(scope["wildcard_access_allowed"] is False for scope in scopes))

        boundary = self.policy["reference_boundary"]
        self.assertTrue(boundary["same_namespace_auth_reference_required"])
        self.assertTrue(boundary["same_namespace_connection_reference_required"])
        self.assertTrue(boundary["same_namespace_credential_reference_required"])
        self.assertTrue(boundary["same_namespace_source_and_target_required"])
        self.assertFalse(boundary["cross_namespace_references_allowed"])
        self.assertTrue(boundary["enforcement_source_selected"])
        self.assertFalse(boundary["negative_cross_namespace_tests_proved"])

    def test_proxy_secret_zero_and_smoke_profiles_are_selected_but_not_deployable(self) -> None:
        egress = self.policy["egress_profile"]
        self.assertEqual("separate-authenticated-squid-proxy", egress["architecture"])
        self.assertEqual("app.infisical.com", egress["allowed_hostname"])
        self.assertEqual(443, egress["allowed_port"])
        self.assertTrue(egress["proxy_image_selected"])
        self.assertTrue(egress["proxy_config_selected"])
        self.assertFalse(egress["broad_direct_443_allowed"])

        secret_zero = self.policy["secret_zero_profile"]
        self.assertEqual("interactive-no-log", secret_zero["bootstrap_input"])
        self.assertEqual("age-encrypted-google-drive-copy", secret_zero["off_node_copy"])
        self.assertTrue(secret_zero["age_key_custody_separate"])
        self.assertFalse(secret_zero["credential_values_allowed_in_git"])

        smoke = self.policy["smoke_profile"]
        self.assertEqual("cristexhub-dev", smoke["namespace"])
        self.assertEqual("ConfigMap", smoke["target_kind"])
        self.assertEqual("read-only", smoke["identity_access"])
        self.assertFalse(smoke["sensitive_value_allowed"])
        self.assertFalse(smoke["runtime_allowed"])

        gates = self.policy["promotion_gates"]
        self.assertEqual(
            {
                "foundation_namespaces_proved",
                "source_controller_audit_complete",
                "technical_profile_selected",
                "proxy_image_and_config_selected",
                "same_namespace_reference_enforcement_source_selected",
                "deployable_kubernetes_source_allowed",
                "operational_ansible_source_allowed",
            },
            {key for key, value in gates.items() if value is True},
        )
        self.assertTrue(
            all(
                value is False
                for key, value in gates.items()
                if key
                not in {
                    "foundation_namespaces_proved",
                    "source_controller_audit_complete",
                    "technical_profile_selected",
                    "proxy_image_and_config_selected",
                    "same_namespace_reference_enforcement_source_selected",
                    "deployable_kubernetes_source_allowed",
                    "operational_ansible_source_allowed",
                }
            )
        )

    def test_deployable_source_preserves_namespace_and_runtime_boundaries(self) -> None:
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
        operational = [
            path
            for root in (
                ROOT / "ansible/bin",
                ROOT / "ansible/playbooks",
                ROOT / "ansible/roles",
                ROOT / "ansible/plugins/action",
            )
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        ]
        self.assertEqual(
            {
                "bootstrap-infisical-operator",
                "bootstrap-infisical-proxy-secrets",
                "bootstrap_infisical_operator.yml",
                "bootstrap_infisical_proxy_secrets.yml",
                "transfer-infisical-proxy-recovery",
                "transfer_infisical_proxy_recovery.yml",
                "main.yml",
                "infisical_operator_guarded_k8s.py",
                "infisical_proxy_secret_zero_guarded_k8s.py",
                "infisical_argocd_secrets_guarded_k8s.py",
                "bootstrap-infisical-argocd-secrets",
                "bootstrap_infisical_argocd_secrets.yml",
                "bootstrap-infisical-database-secrets",
                "bootstrap_infisical_database_secrets.yml",
                "infisical_database_secrets_guarded_k8s.py",
                "seed-infisical-universal-auth",
                "seed_infisical_universal_auth.yml",
                "upload-infisical-bootstrap-values",
                "materialize-infisical-cristexhub-dev-runtime",
                "bootstrap-infisical-cristexhub-dev-runtime",
                "bootstrap_infisical_cristexhub_dev_runtime.yml",
                "infisical_cristexhub_dev_runtime_guarded_k8s.py",
                "bootstrap-infisical-cristexhub-prod-runtime",
                "bootstrap_infisical_cristexhub_prod_runtime.yml",
                "infisical_cristexhub_prod_runtime_guarded_k8s.py",
                "infisical_universal_auth_seed_guarded_k8s.py",
                "bootstrap-infisical-cloudflared-secrets",
                "bootstrap_infisical_cloudflared_secrets.yml",
                "infisical_cloudflared_secrets_guarded_k8s.py",
            },
            {path.name for path in operational if "infisical" in str(path).lower()},
        )
        component_root = ROOT / "ansible/files/components/infisical-operator"
        self.assertTrue(component_root.is_dir())
        self.assertEqual(44, len(list(component_root.rglob("*.yaml"))))

        normalized = " ".join(self.runbook.split())
        for required in (
            "44-OBJECT IDLE CLOSURE APPLIED/IDEMPOTENT — CREDENTIAL-BEARING PROD PHASES BLOCKED",
            "shared-services`, `argocd`, `cristexhub-dev`, `cristexhub-prod`, and `platform-edge`",
            "separate identity and credential scope",
            "ClusterGenerator has no reconciler or eager watch",
            "cache-backed lazy informer",
            "generator references are unsupported",
            "metrics-bind-address=0",
            "separate authenticated Squid proxy",
            "age-encrypted off-node copy",
            "non-sensitive ConfigMap",
            "44 hash-bound objects",
        ):
            self.assertIn(required, normalized)
        for relative in (
            "AGENTS.md",
            "README.md",
            "ansible/README.md",
            "architecture-plan.md",
            "specs/k3s-iac-foundation/brief.md",
            "specs/k3s-iac-foundation/requirements.md",
            "specs/k3s-iac-foundation/tasks.md",
            "specs/k3s-iac-foundation/testcases.md",
            "specs/k3s-iac-foundation/status.md",
        ):
            self.assertIn(RUNBOOK.name, (ROOT / relative).read_text(), relative)

    def test_value_and_evidence_hygiene(self) -> None:
        combined = self.policy_text + "\n" + self.runbook
        for pattern in (
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"\bghp_[A-Za-z0-9]+\b",
            r"\bgithub_pat_[A-Za-z0-9_]+\b",
            r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
            r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
            r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
            r"/Users/[^/\s]+/",
            r"(?im)^\s*(?:password|token|client_secret|api_key|credentials?)\s*:\s*\S+",
        ):
            self.assertNotRegex(combined, pattern)
        for forbidden in (
            "ansible-playbook ",
            "helm install",
            "helm upgrade",
            "kubectl apply",
            "ssh ",
        ):
            self.assertNotIn(forbidden, self.runbook.lower())


if __name__ == "__main__":
    unittest.main()
