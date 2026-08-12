from __future__ import annotations

import hashlib
import re
import tarfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = (
    ROOT
    / "ansible/files/vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz"
)
POLICY = (
    ROOT
    / "ansible/files/policies/infisical-operator-privileged-prerequisites.yml"
)
RUNBOOK = ROOT / "runbooks/infisical-operator-privileged-prerequisites-design.md"
KUBERNETES = ROOT / "kubernetes"

ARCHIVE_SHA256 = "7f8846c4f6b1cdca2cea23cf00a29d12a38f42eb8da8e125dc196a1e5683aea8"
EXPECTED_CRDS = {
    "secrets-operator/templates/clustergenerator-crd.yaml": (
        "clustergenerators.secrets.infisical.com",
        "ClusterGenerator",
        "Cluster",
        "v1alpha1",
    ),
    "secrets-operator/templates/infisicalauth-crd.yaml": (
        "infisicalauths.secrets.infisical.com",
        "InfisicalAuth",
        "Namespaced",
        "v1beta1",
    ),
    "secrets-operator/templates/infisicalconnection-crd.yaml": (
        "infisicalconnections.secrets.infisical.com",
        "InfisicalConnection",
        "Namespaced",
        "v1beta1",
    ),
    "secrets-operator/templates/infisicaldynamicsecret-crd.yaml": (
        "infisicaldynamicsecrets.secrets.infisical.com",
        "InfisicalDynamicSecret",
        "Namespaced",
        "v1alpha1",
    ),
    "secrets-operator/templates/infisicalpushsecret-crd.yaml": (
        "infisicalpushsecrets.secrets.infisical.com",
        "InfisicalPushSecret",
        "Namespaced",
        "v1alpha1",
    ),
    "secrets-operator/templates/infisicalsecret-crd.yaml": (
        "infisicalsecrets.secrets.infisical.com",
        "InfisicalSecret",
        "Namespaced",
        "v1alpha1",
    ),
    "secrets-operator/templates/infisicalstaticsecret-crd.yaml": (
        "infisicalstaticsecrets.secrets.infisical.com",
        "InfisicalStaticSecret",
        "Namespaced",
        "v1beta1",
    ),
}


class InfisicalPrivilegedPrerequisitesDesignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_text = POLICY.read_text()
        cls.policy = yaml.safe_load(cls.policy_text)
        cls.runbook = RUNBOOK.read_text()
        with tarfile.open(ARCHIVE, "r:gz") as bundle:
            cls.members = {
                member.name: bundle.extractfile(member).read().decode()
                for member in bundle.getmembers()
                if member.isfile()
            }

    @staticmethod
    def parse_crd_template(text: str) -> dict:
        sanitized = "\n".join(
            line for line in text.splitlines() if "{{" not in line and "}}" not in line
        )
        document = yaml.safe_load(sanitized)
        if not isinstance(document, dict):
            raise AssertionError("CRD template did not produce one object")
        return document

    def test_archive_binding_and_exact_crd_inventory(self) -> None:
        self.assertEqual(
            ARCHIVE_SHA256, hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
        )
        self.assertEqual(23, len(self.members))
        actual_templates = {
            name for name in self.members if name.endswith("-crd.yaml")
        }
        self.assertEqual(set(EXPECTED_CRDS), actual_templates)

        observed: list[dict[str, str]] = []
        for template_path, expected in EXPECTED_CRDS.items():
            document = self.parse_crd_template(self.members[template_path])
            definition_name, resource_kind, resource_scope, version = expected
            self.assertEqual("apiextensions.k8s.io/v1", document["apiVersion"])
            self.assertEqual("CustomResourceDefinition", document["kind"])
            self.assertEqual(definition_name, document["metadata"]["name"])
            self.assertEqual("secrets.infisical.com", document["spec"]["group"])
            self.assertEqual(resource_kind, document["spec"]["names"]["kind"])
            self.assertEqual(resource_scope, document["spec"]["scope"])
            versions = document["spec"]["versions"]
            self.assertEqual(1, len(versions))
            self.assertEqual(version, versions[0]["name"])
            self.assertIs(True, versions[0]["served"])
            self.assertIs(True, versions[0]["storage"])
            observed.append(
                {
                    "definition_name": definition_name,
                    "resource_kind": resource_kind,
                    "resource_scope": resource_scope,
                    "served_storage_version": version,
                    "template_path": template_path,
                }
            )

        self.assertEqual(
            sorted(observed, key=lambda item: item["template_path"]),
            sorted(
                self.policy["crd_inventory"]["resources"],
                key=lambda item: item["template_path"],
            ),
        )
        self.assertEqual(1, sum(item[2] == "Cluster" for item in EXPECTED_CRDS.values()))
        self.assertEqual(
            6, sum(item[2] == "Namespaced" for item in EXPECTED_CRDS.values())
        )

    def test_raw_chart_rbac_seams_remain_unapproved(self) -> None:
        manager = self.members["secrets-operator/templates/manager-rbac.yaml"]
        metrics_auth = self.members[
            "secrets-operator/templates/metrics-auth-rbac.yaml"
        ]
        metrics_reader = self.members[
            "secrets-operator/templates/metrics-reader-rbac.yaml"
        ]
        user_rbac = self.members["secrets-operator/templates/user-rbac.yaml"]
        deployment = self.members["secrets-operator/templates/deployment.yaml"]

        self.assertIn(
            '$namespaces := (include "secrets-operator.scopedNamespaces" . | fromJson).list',
            manager,
        )
        self.assertIn("$isScopedMode := and $namespaces .Values.scopedRBAC", manager)
        self.assertIn("kind: Role", manager)
        self.assertIn("kind: ClusterRole", manager)
        self.assertIn("- tokenreviews", manager)
        self.assertIn("- clustergenerators", manager)
        self.assertIn("{{- range $ns := $namespaces }}", manager)
        cluster_generator = next(
            resource
            for resource in self.policy["crd_inventory"]["resources"]
            if resource["resource_kind"] == "ClusterGenerator"
        )
        self.assertEqual("Cluster", cluster_generator["resource_scope"])
        self.assertIn(".Values.scopedNamespace", metrics_auth)
        self.assertNotIn(".Values.scopedNamespaces", metrics_auth)
        self.assertIn("kind: Role", metrics_auth)
        self.assertIn("- tokenreviews", metrics_auth)
        self.assertIn("- subjectaccessreviews", metrics_auth)
        self.assertIn(".Values.scopedNamespace", metrics_reader)
        self.assertNotIn(".Values.scopedNamespaces", metrics_reader)
        self.assertIn("{{- if .Values.enableUserRBAC }}", user_rbac)
        self.assertIn("kind: ClusterRole", user_rbac)
        aggregate_labels = [
            "rbac.authorization.k8s.io/aggregate-to-admin",
            "rbac.authorization.k8s.io/aggregate-to-edit",
            "rbac.authorization.k8s.io/aggregate-to-view",
            "rbac.authorization.k8s.io/aggregate-to-cluster-reader",
        ]
        for label in aggregate_labels:
            self.assertIn(label, user_rbac)
        self.assertIn("- --namespaces={{ join \",\" $namespaces }}", deployment)

        observations = self.policy["observed_upstream_rbac"]
        self.assertFalse(observations["approved_for_promotion"])
        self.assertTrue(observations["manager_scope_helper_supports_plural_namespaces"])
        self.assertEqual(
            [
                "authentication.k8s.io/tokenreviews",
                "secrets.infisical.com/clustergenerators",
            ],
            observations["scoped_manager_contains_ineffective_cluster_permissions"],
        )
        self.assertTrue(
            observations["plural_scope_metrics_templates_use_deprecated_singular_condition"]
        )
        self.assertTrue(
            observations[
                "deprecated_singular_metrics_mode_emits_ineffective_namespaced_review_role"
            ]
        )
        self.assertEqual(aggregate_labels, observations["aggregate_role_labels_observed"])
        self.assertFalse(observations["final_permissions_selected"])

    def test_policy_is_inert_and_all_promotion_gates_remain_closed(self) -> None:
        self.assertEqual(
            "design-only-not-deployable-runtime-blocked",
            self.policy["policy_status"],
        )
        self.assertEqual(
            "inert-inventory-and-promotion-contract", self.policy["capability"]
        )
        self.assertTrue(self.policy["source"]["observation_only"])
        self.assertEqual(7, self.policy["crd_inventory"]["template_count"])
        self.assertEqual(
            ARCHIVE_SHA256, self.policy["source"]["chart_archive_sha256"]
        )
        self.assertFalse(self.policy["ownership"]["dual_reconciliation_allowed"])
        self.assertEqual(
            "universal-auth", self.policy["authentication_direction"]["mechanism"]
        )
        gates = self.policy["promotion_gates"]
        self.assertTrue(gates["initial_watch_namespaces_selected"])
        self.assertTrue(gates["foundation_namespace_runtime_proved"])
        self.assertTrue(
            all(
                value is False
                for key, value in gates.items()
                if key
                not in {
                    "initial_watch_namespaces_selected",
                    "foundation_namespace_runtime_proved",
                }
            )
        )
        self.assertTrue(
            {
                "custom-resource-definition-source",
                "cluster-rbac-source",
                "helm-values",
                "rendered-kubernetes-source",
                "ansible-wrapper-playbook-or-role",
                "controller-or-secret-source",
                "network-provider-or-runtime-operation",
            }.issubset(self.policy["prohibited_by_this_increment"])
        )
        self.assertTrue(
            {"apiVersion", "kind", "metadata", "spec"}.isdisjoint(self.policy)
        )

    def test_separate_promoted_source_preserves_namespace_closure(self) -> None:
        self.assertEqual(
            {
                "platform/namespaces/argocd.yaml",
                "platform/namespaces/platform-edge.yaml",
                "platform/namespaces/shared-services.yaml",
                "applications/namespaces/cristexhub-dev.yaml",
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
            )
            for path in root.rglob("*")
            if path.is_file()
        ]
        self.assertEqual(
            {
                "bootstrap-infisical-operator",
                "bootstrap-infisical-proxy-secrets",
                "bootstrap_infisical_operator.yml",
                "bootstrap_infisical_proxy_secrets.yml",
                "transfer-infisical-proxy-recovery",
                "transfer_infisical_proxy_recovery.yml",
                "bootstrap-infisical-argocd-secrets",
                "bootstrap_infisical_argocd_secrets.yml",
                "bootstrap-infisical-database-secrets",
                "bootstrap_infisical_database_secrets.yml",
                "seed-infisical-universal-auth",
                "seed_infisical_universal_auth.yml",
                "upload-infisical-bootstrap-values",
                "bootstrap-infisical-cloudflared-secrets",
                "bootstrap_infisical_cloudflared_secrets.yml",
                "main.yml",
            },
            {path.name for path in operational if "infisical" in str(path).lower()},
        )
        component_root = ROOT / "ansible/files/components/infisical-operator"
        self.assertTrue(component_root.is_dir())
        self.assertEqual(40, len(list(component_root.rglob("*.yaml"))))

    def test_runbook_and_references_preserve_design_only_boundary(self) -> None:
        normalized = " ".join(self.runbook.split())
        for required in (
            "DESIGN ONLY — NOT DEPLOYABLE — NOT RUN/BLOCKED",
            "raw chart templates, not a rendered object closure",
            "None of these observed permissions is approved by being listed here",
            "Universal Auth remains the selected direction, not an implemented bootstrap",
            "Dual reconciliation is forbidden",
            "There is no runtime rollback because no cluster object or external resource was created",
        ):
            self.assertIn(required, normalized)
        self.assertNotIn("```", self.runbook)
        for relative in (
            "AGENTS.md",
            "README.md",
            "ansible/README.md",
            "architecture-plan.md",
            "specs/k3s-iac-foundation/brief.md",
            "specs/k3s-iac-foundation/manual-qa.md",
            "specs/k3s-iac-foundation/requirements.md",
            "specs/k3s-iac-foundation/tasks.md",
            "specs/k3s-iac-foundation/status.md",
            "specs/k3s-iac-foundation/testcases.md",
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
            "tofu apply",
            "ssh ",
        ):
            self.assertNotIn(forbidden, self.runbook.lower())


if __name__ == "__main__":
    unittest.main()
