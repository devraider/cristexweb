from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ansible/files/policies/reactive-resume-architecture.yml"
DATABASE_POLICY = ROOT / "ansible/files/policies/shared-database-architecture.yml"
RUNBOOK = ROOT / "runbooks/reactive-resume-hosted-architecture.md"
KUBERNETES = ROOT / "kubernetes"


class ReactiveResumeArchitectureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_text = POLICY.read_text()
        cls.policy = yaml.safe_load(cls.policy_text)
        cls.database_policy = yaml.safe_load(DATABASE_POLICY.read_text())
        cls.runbook_text = RUNBOOK.read_text()

    def test_private_dev_mvp_and_future_prod_are_separate(self) -> None:
        self.assertEqual(
            "cristex-reactive-resume-v1", self.policy["policy_schema"]
        )
        self.assertEqual(
            "source-policy-only-runtime-blocked", self.policy["policy_status"]
        )
        self.assertEqual("included-private-dev", self.policy["mvp_scope"])
        self.assertEqual(
            {
                "dev": {
                    "namespace": "cristexhub-dev",
                    "identity_client": "reactive-resume-dev",
                    "activation": "blocked",
                },
                "prod": {
                    "namespace": "cristexhub-prod",
                    "identity_client": "reactive-resume-prod",
                    "activation": "blocked",
                },
            },
            self.policy["environments"],
        )

    def test_upstream_image_and_callbacks_remain_unselected(self) -> None:
        source = self.policy["image_source"]
        self.assertEqual("unselected", source["selection"])
        self.assertIsNone(source["repository"])
        self.assertIsNone(source["version"])
        self.assertIsNone(source["linux_amd64_digest"])
        self.assertFalse(source["trust_accepted"])
        identity = self.policy["identity"]
        self.assertEqual(
            "https://auth.cristex-soft.com/realms/cristexhub", identity["issuer"]
        )
        self.assertFalse(identity["exact_callbacks_selected"])
        self.assertFalse(identity["exact_web_origins_selected"])

    def test_database_scopes_are_dedicated_on_the_shared_engine(self) -> None:
        database = self.policy["database"]
        self.assertEqual(
            "ansible/files/policies/shared-database-architecture.yml",
            database["policy_path"],
        )
        self.assertEqual("postgresql", database["engine"])
        self.assertEqual(
            {
                "dev": "reactive-resume-dev",
                "prod": "reactive-resume-prod",
            },
            database["consumer_scopes"],
        )
        consumers = self.database_policy["engines"]["postgresql"]["consumers"]
        self.assertEqual(
            {"reactive-resume-dev", "reactive-resume-prod", "keycloak"},
            set(consumers),
        )
        for scope in ("reactive-resume-dev", "reactive-resume-prod"):
            self.assertEqual("dedicated-logical-database", consumers[scope]["database"])
            self.assertEqual("dedicated-owner-role", consumers[scope]["principal"])
            self.assertEqual(
                "infisical-cloud", consumers[scope]["credential_value_owner"]
            )
            self.assertEqual(
                "dedicated-logical-database", consumers[scope]["backup_scope"]
            )

    def test_secrets_exposure_and_handoff_fail_closed(self) -> None:
        self.assertEqual("infisical-cloud", self.policy["secrets"]["value_owner"])
        self.assertFalse(self.policy["secrets"]["values_allowed_in_source"])
        self.assertEqual("private-only", self.policy["exposure"]["current_scope"])
        self.assertEqual(
            {"public-route", "NodePort", "LoadBalancer", "public-administration"},
            set(self.policy["exposure"]["forbidden"]),
        )
        self.assertTrue(
            all(value is False for value in self.policy["promotion_gates"].values())
        )
        self.assertFalse(self.policy["executable_source_allowed"])

    def test_runbook_preserves_local_asset_and_runtime_boundaries(self) -> None:
        normalized = " ".join(self.runbook_text.split())
        for required in (
            "SOURCE POLICY ONLY — RUNTIME BLOCKED",
            "Reactive Resume is included in the private DEV MVP",
            "local Compose tag, callback, credentials, and development issuer are not hosted inputs",
            "Infisical Cloud owns every runtime value",
            "GitHub Actions does not rebuild the upstream Reactive Resume image",
            "No Deployment, StatefulSet, Service, PVC, Secret, Ingress, route, or Argo Application",
            "No registry, GitHub runner, host, Kubernetes API, Infisical, database, or runtime operation",
        ):
            self.assertIn(required, normalized)

    def test_no_executable_source_or_secret_value_is_added(self) -> None:
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
        combined = f"{self.policy_text}\n{self.runbook_text}"
        self.assertNotRegex(
            combined,
            r"(?im)^\s*(?:password|token|client_secret|api_key|credentials?)\s*:\s*\S+",
        )
        self.assertNotRegex(combined, re.compile(r"@sha256:[0-9a-f]{64}"))
        self.assertNotIn("/Users/", combined)


if __name__ == "__main__":
    unittest.main()
