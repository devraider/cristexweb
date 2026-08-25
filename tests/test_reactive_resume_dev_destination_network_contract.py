from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RR = ROOT / "ansible/files/components/reactive-resume-dev-argocd"
KEYCLOAK = ROOT / "ansible/files/components/keycloak/network/keycloak-allow-reactive-resume-dev.yaml"
OIDC = ROOT / "ansible/files/components/oidc-connect-proxy/network/oidc-connect-proxy-allow-reactive-resume-dev.yaml"
POSTGRES = ROOT / "ansible/files/components/postgresql/network/postgresql-ingress.yaml"
STORAGE = ROOT / "ansible/files/components/reactive-resume-dev-networkpolicy/network/reactive-resume-object-storage-allow-dev.yaml"


def load(path: Path):
    return yaml.safe_load(path.read_text())


class ReactiveResumeDevDestinationNetworkContractTests(unittest.TestCase):
    def test_rr_workload_labels_ca_bundle_and_exact_egress(self):
        deployment = load(RR / "deployment.yaml")
        labels = deployment["spec"]["template"]["metadata"]["labels"]
        self.assertEqual("shared-postgresql", labels["cristex.io/database-client"])
        self.assertEqual("/etc/reactive-resume/ca-bundle/ca.crt", next(x["value"] for x in deployment["spec"]["template"]["spec"]["containers"][0]["env"] if x["name"] == "NODE_EXTRA_CA_CERTS"))
        self.assertEqual("merge-ca-bundle", deployment["spec"]["template"]["spec"]["initContainers"][0]["name"])
        self.assertFalse((RR / "migration-job.yaml").exists())
        policy = load(RR / "networkpolicy-egress.yaml")
        pod = policy["spec"]["podSelector"]
        self.assertEqual("shared-postgresql", pod["matchLabels"]["cristex.io/database-client"])
        rules = policy["spec"]["egress"]
        self.assertIn({"cnpg.io/cluster": "shared-postgresql", "cnpg.io/instanceRole": "primary"}, [r["to"][0]["podSelector"]["matchLabels"] for r in rules])
        self.assertIn({"app.kubernetes.io/name": "reactive-resume-object-storage", "app.kubernetes.io/part-of": "reactive-resume"}, [r["to"][0]["podSelector"]["matchLabels"] for r in rules])
        self.assertIn(8443, [p["port"] for r in rules for p in r["ports"]])
        self.assertIn(3128, [p["port"] for r in rules for p in r["ports"]])

    def test_bounded_destination_ingress_sources(self):
        for path, name, port in ((KEYCLOAK, "keycloak-allow-reactive-resume-dev", 8443), (OIDC, "oidc-connect-proxy-allow-reactive-resume-dev", 3128), (STORAGE, "reactive-resume-object-storage-allow-dev", 8333)):
            obj = load(path)
            self.assertEqual(name, obj["metadata"]["name"])
            self.assertEqual("shared-services", obj["metadata"]["namespace"])
            source = obj["spec"]["ingress"][0]["from"][0]
            self.assertEqual("cristexhub-dev", source["namespaceSelector"]["matchLabels"]["kubernetes.io/metadata.name"])
            self.assertEqual({"app.kubernetes.io/name": "reactive-resume-dev", "app.kubernetes.io/part-of": "cristexhub"}, source["podSelector"]["matchLabels"])
            self.assertEqual(port, obj["spec"]["ingress"][0]["ports"][0]["port"])

    def test_postgresql_destination_matches_cnpg_primary_and_rr_label(self):
        obj = load(POSTGRES)
        self.assertEqual({"cnpg.io/cluster": "shared-postgresql", "cnpg.io/instanceRole": "primary"}, obj["spec"]["podSelector"]["matchLabels"])
        peers = obj["spec"]["ingress"][0]["from"]
        rr = next(peer for peer in peers if peer.get("namespaceSelector", {}).get("matchLabels", {}).get("kubernetes.io/metadata.name") == "cristexhub-dev" and peer.get("podSelector", {}).get("matchLabels", {}).get("app.kubernetes.io/name") == "reactive-resume-dev")
        self.assertEqual("shared-postgresql", rr["podSelector"]["matchLabels"]["cristex.io/database-client"])
        self.assertEqual(5432, obj["spec"]["ingress"][0]["ports"][0]["port"])

    def test_ledgers_and_value_free_sources(self):
        for path in (KEYCLOAK, OIDC, POSTGRES, STORAGE):
            self.assertNotIn("BEGIN PRIVATE", path.read_text())
        ledger = ROOT / "ansible/files/components/reactive-resume-dev-networkpolicy/MANIFESTS.sha256"
        digest, rel = ledger.read_text().strip().split("  ", 1)
        self.assertEqual("network/reactive-resume-object-storage-allow-dev.yaml", rel)
        self.assertEqual(hashlib.sha256(STORAGE.read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
