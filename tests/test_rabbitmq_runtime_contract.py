from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/rabbitmq"
IMAGE = "docker.io/library/rabbitmq@sha256:cd4fd60136781671d125ed68ac4b67900c0726b55e2e8b98719daa616a63240b"


def objects() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path in sorted(COMPONENT.rglob("*.yaml")):
        for item in yaml.safe_load_all(path.read_text()):
            if isinstance(item, dict) and item.get("kind"):
                result.append(item)
    return result


class RabbitMqRuntimeSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.objects = objects()
        cls.by_kind = {}
        for item in cls.objects:
            cls.by_kind.setdefault(item["kind"], []).append(item)

    def test_exact_private_source_closure(self) -> None:
        self.assertEqual(10, len(self.objects))
        self.assertEqual(1, len(self.by_kind["StatefulSet"]))
        self.assertEqual(3, len(self.by_kind["Service"]))
        self.assertEqual(1, len(self.by_kind["ServiceAccount"]))
        self.assertEqual(1, len(self.by_kind["ConfigMap"]))
        self.assertEqual(4, len(self.by_kind["NetworkPolicy"]))
        self.assertNotIn("Ingress", self.by_kind)
        self.assertNotIn("Secret", self.by_kind)
        self.assertNotIn("Job", self.by_kind)
        for item in self.objects:
            self.assertEqual("shared-services", item["metadata"]["namespace"])
            self.assertEqual("ansible", item["metadata"]["labels"]["app.kubernetes.io/managed-by"])

    def test_statefulset_is_pinned_single_node_and_retained(self) -> None:
        sts = self.by_kind["StatefulSet"][0]
        self.assertEqual("shared-rabbitmq", sts["metadata"]["name"])
        self.assertEqual(1, sts["spec"]["replicas"])
        self.assertEqual("shared-rabbitmq-headless", sts["spec"]["serviceName"])
        claim = sts["spec"]["volumeClaimTemplates"][0]
        self.assertEqual("local-path", claim["spec"]["storageClassName"])
        self.assertEqual("20Gi", claim["spec"]["resources"]["requests"]["storage"])
        self.assertEqual("ReadWriteOnce", claim["spec"]["accessModes"][0])
        container = next(x for x in sts["spec"]["template"]["spec"]["containers"] if x["name"] == "rabbitmq")
        self.assertEqual(IMAGE, container["image"])
        pod = sts["spec"]["template"]["spec"]
        self.assertEqual(999, pod["securityContext"]["runAsUser"])
        self.assertEqual(999, pod["securityContext"]["runAsGroup"])
        self.assertEqual(999, pod["securityContext"]["fsGroup"])
        self.assertEqual(1, len(sts["spec"]["template"]["spec"]["initContainers"]))

    def test_tls_services_and_no_public_exposure(self) -> None:
        services = {x["metadata"]["name"]: x for x in self.by_kind["Service"]}
        self.assertEqual("None", services["shared-rabbitmq-headless"]["spec"]["clusterIP"])
        self.assertEqual("ClusterIP", services["shared-rabbitmq"]["spec"]["type"])
        self.assertEqual(5671, services["shared-rabbitmq"]["spec"]["ports"][0]["port"])
        self.assertEqual(15671, services["shared-rabbitmq-management"]["spec"]["ports"][0]["port"])
        self.assertNotIn("nodePort", json.dumps(services))
        cfg = self.by_kind["ConfigMap"][0]["data"]["rabbitmq.conf"]
        self.assertIn("listeners.tcp = none", cfg)
        self.assertIn("listeners.ssl.default = 5671", cfg)
        self.assertIn("management.ssl.port = 15671", cfg)
        self.assertNotIn("management.tcp.port = 15672", cfg)

    def test_definitions_are_vhost_scoped_without_wildcard_permissions(self) -> None:
        sts = self.by_kind["StatefulSet"][0]
        script = sts["spec"]["template"]["spec"]["initContainers"][0]["args"][0]
        for value in ("/cristexhub-dev", "/cristexhub-prod", 'configure":"^(celery|default|high_priority|low_priority|reply[.]celery[.]pidbox|[0-9a-f-]+[.]reply[.]celery[.]pidbox|celeryev|celery[.]pidbox|celery@celery-worker-[0-9a-z-]+[.]celery[.]pidbox)$', "administrator"):
            self.assertIn(value, script)
        self.assertNotIn(".*", script)
        self.assertIn("password_hash", script)
        self.assertNotIn('"password"', script)
        self.assertIn("shared-rabbitmq-admin", json.dumps(sts))
        self.assertIn("shared-rabbitmq-cristexhub-dev", json.dumps(sts))
        self.assertIn("shared-rabbitmq-cristexhub-prod", json.dumps(sts))

    def test_network_policy_is_deny_first_and_private(self) -> None:
        policies = self.by_kind["NetworkPolicy"]
        self.assertTrue(any(set(x["spec"]["policyTypes"]) == {"Ingress", "Egress"} and not x["spec"].get("ingress") and not x["spec"].get("egress") for x in policies))
        combined = json.dumps(policies)
        self.assertIn('"port": 53', combined)
        self.assertIn('"port": 5671', combined)
        self.assertIn('"port": 15671', combined)
        self.assertNotIn("0.0.0.0/0", combined)

    def test_manifest_hash_ledger_matches_sources(self) -> None:
        ledger = (COMPONENT / "MANIFESTS.sha256").read_text().splitlines()
        expected = {}
        for line in ledger:
            digest, name = line.split(maxsplit=1)
            expected[name] = digest
        self.assertEqual(10, len(expected))
        for path in sorted(COMPONENT.rglob("*.yaml")):
            relative = str(path.relative_to(COMPONENT))
            self.assertEqual(expected[relative], hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
