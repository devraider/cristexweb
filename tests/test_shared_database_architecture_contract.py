from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
KUBERNETES = ROOT / "kubernetes"
POLICY = ANSIBLE / "files/policies/shared-database-architecture.yml"
RUNBOOK = ROOT / "runbooks/shared-database-architecture.md"


class SharedDatabaseArchitectureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_text = POLICY.read_text()
        cls.policy = yaml.safe_load(cls.policy_text)
        cls.runbook_text = RUNBOOK.read_text()

    def test_exact_shared_engine_and_consumer_closure(self) -> None:
        self.assertEqual(
            "cristex-shared-databases-v1", self.policy["policy_schema"]
        )
        self.assertEqual(
            "source-policy-only-runtime-blocked", self.policy["policy_status"]
        )
        self.assertEqual("shared-services", self.policy["namespace"])
        self.assertEqual({"postgresql", "mongodb"}, set(self.policy["engines"]))

        postgresql = self.policy["engines"]["postgresql"]
        self.assertEqual(1, postgresql["instance_count"])
        self.assertEqual("shared-services", postgresql["namespace"])
        self.assertEqual(
            {"cristexhub-dev", "cristexhub-prod", "keycloak"},
            set(postgresql["consumers"]),
        )
        self.assertTrue(postgresql["no_consumer_specific_engine_or_pvc"])

        mongodb = self.policy["engines"]["mongodb"]
        self.assertEqual(1, mongodb["instance_count"])
        self.assertEqual("shared-services", mongodb["namespace"])
        self.assertEqual(
            {"cristexhub-dev", "cristexhub-prod"}, set(mongodb["consumers"])
        )
        self.assertNotIn("keycloak", mongodb["consumers"])
        self.assertTrue(mongodb["no_consumer_specific_engine_or_pvc"])

    def test_every_consumer_has_dedicated_value_free_scopes(self) -> None:
        for engine_name, engine in self.policy["engines"].items():
            for consumer in engine["consumers"].values():
                self.assertEqual("dedicated-logical-database", consumer["database"])
                expected_principal = (
                    "dedicated-owner-role"
                    if engine_name == "postgresql"
                    else "dedicated-database-user"
                )
                self.assertEqual(expected_principal, consumer["principal"])
                self.assertEqual("infisical-cloud", consumer["credential_value_owner"])
                self.assertEqual("dedicated-logical-database", consumer["backup_scope"])
                self.assertEqual("dedicated", consumer["migration_scope"])

        self.assertEqual(
            "dedicated-owner-role",
            self.policy["engines"]["postgresql"]["consumers"]["keycloak"][
                "principal"
            ],
        )

    def test_postgresql_authorization_is_deny_first(self) -> None:
        authorization = self.policy["engines"]["postgresql"]["authorization"]
        self.assertEqual("deny", authorization["cross_database_access_default"])
        self.assertEqual("revoke", authorization["public_connect"])
        self.assertEqual("revoke", authorization["public_schema_create"])
        self.assertEqual("deny", authorization["workload_create_database"])
        self.assertEqual("deny", authorization["workload_create_role"])
        self.assertEqual(
            {
                "dev-role-to-prod-database",
                "prod-role-to-dev-database",
                "application-roles-to-keycloak-database",
                "keycloak-role-to-application-databases",
                "workload-role-create-database",
                "workload-role-create-role",
            },
            set(authorization["required_negative_tests"]),
        )

    def test_mongodb_authorization_rejects_broad_roles(self) -> None:
        authorization = self.policy["engines"]["mongodb"]["authorization"]
        self.assertEqual("deny", authorization["cross_database_access_default"])
        self.assertEqual("deny", authorization["workload_user_administration"])
        self.assertEqual("deny", authorization["workload_role_administration"])
        self.assertEqual("deny", authorization["writes_outside_authorized_database"])
        self.assertEqual(
            {
                "readAnyDatabase",
                "readWriteAnyDatabase",
                "dbAdminAnyDatabase",
                "userAdminAnyDatabase",
                "root",
            },
            set(authorization["forbidden_builtin_roles"]),
        )
        self.assertEqual(
            {
                "dev-user-to-prod-database",
                "prod-user-to-dev-database",
                "workload-user-administration",
                "workload-role-administration",
            },
            set(authorization["required_negative_tests"]),
        )

    def test_source_storage_recovery_and_runtime_gates_remain_blocked(self) -> None:
        postgresql_source = self.policy["engines"]["postgresql"]["source"]
        self.assertEqual("selected-offline-only", postgresql_source["selection"])
        self.assertEqual(
            "ansible/files/policies/hosted-identity-authorization.yml#images.postgresql",
            postgresql_source["reference"],
        )
        self.assertFalse(postgresql_source["trust_accepted"])

        mongodb_source = self.policy["engines"]["mongodb"]["source"]
        self.assertEqual("unselected", mongodb_source["selection"])
        self.assertIsNone(mongodb_source["repository"])
        self.assertIsNone(mongodb_source["version"])
        self.assertIsNone(mongodb_source["linux_amd64_digest"])
        self.assertFalse(mongodb_source["trust_accepted"])

        self.assertEqual("unselected", self.policy["storage"]["storage_class"])
        self.assertEqual("unselected", self.policy["storage"]["pvc_topology"])
        self.assertEqual("unselected", self.policy["storage"]["capacities"])
        self.assertEqual("unselected", self.policy["provisioning"]["owner"])
        self.assertEqual("unselected", self.policy["backup_and_restore"]["tooling"])
        self.assertEqual("unselected", self.policy["backup_and_restore"]["rpo"])
        self.assertEqual("unselected", self.policy["backup_and_restore"]["rto"])
        self.assertTrue(
            all(value is False for value in self.policy["promotion_gates"].values())
        )
        self.assertFalse(self.policy["executable_source_allowed"])

    def test_private_only_exposure_and_admin_separation_are_exact(self) -> None:
        exposure = self.policy["exposure"]
        self.assertEqual("cluster-internal-only", exposure["future_scope"])
        self.assertEqual(
            {"Ingress", "NodePort", "LoadBalancer", "CloudflareTunnel", "public-route"},
            set(exposure["forbidden"]),
        )
        self.assertFalse(
            self.policy["provisioning"]["administrator_credential_available_to_workloads"]
        )
        self.assertEqual(
            "infisical-cloud",
            self.policy["provisioning"]["administrator_credential_value_owner"],
        )

    def test_runbook_preserves_policy_only_and_shared_failure_boundaries(self) -> None:
        normalized = " ".join(self.runbook_text.split())
        for required in (
            "POLICY ONLY — RUNTIME BLOCKED",
            "one PostgreSQL engine and one MongoDB engine",
            "shared failure and contention domains",
            "NetworkPolicy cannot enforce logical-database isolation",
            "MongoDB topology remains unselected",
            "No StatefulSet, Deployment, Service, PVC, Secret, Job, CronJob, or NetworkPolicy",
            "No host, registry, Kubernetes API, provider, Infisical, Helm, or runtime operation",
        ):
            self.assertIn(required, normalized)

    def test_no_executable_database_source_or_kubernetes_widening(self) -> None:
        self.assertEqual(
            {
                "platform/namespaces/argocd.yaml",
                "platform/namespaces/platform-edge.yaml",
                "platform/namespaces/shared-services.yaml",
            },
            {
                str(path.relative_to(KUBERNETES))
                for path in KUBERNETES.rglob("*")
                if path.is_file()
            },
        )
        operational = [
            path
            for root in (ANSIBLE / "bin", ANSIBLE / "playbooks", ANSIBLE / "roles")
            for path in root.rglob("*")
            if path.is_file()
        ]
        self.assertFalse(
            any(
                component in path.name.lower()
                for path in operational
                for component in ("postgres", "postgresql", "mongo", "mongodb", "database")
            )
        )

    def test_policy_is_value_free(self) -> None:
        combined = f"{self.policy_text}\n{self.runbook_text}"
        for pattern in (
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"\bghp_[A-Za-z0-9]+\b",
            r"\bgithub_pat_[A-Za-z0-9_]+\b",
            r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
            r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
            r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
            r"/Users/[^/\s]+/",
        ):
            self.assertNotRegex(combined, pattern)
        self.assertNotRegex(
            combined,
            r"(?im)^\s*(?:password|token|client_secret|api_key|credentials?)\s*:\s*\S+",
        )
        self.assertNotRegex(self.policy_text, re.compile(r"@sha256:[0-9a-f]{64}"))


if __name__ == "__main__":
    unittest.main()
