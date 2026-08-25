from __future__ import annotations

import hashlib
import re
import stat
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ansible/files/components/reactive-resume-dev-argocd"
RUNBOOK = ROOT / "runbooks/reactive-resume-dev-argocd.md"
REGISTRATION = ROOT / "ansible/files/components/reactive-resume-dev-argocd-registration/config/application-reactive-resume-dev.yaml"

EXPECTED_FILES = {
    "deployment.yaml",
    "ingress-private.yaml",
    "migration-job.yaml",
    "networkpolicy-default-deny.yaml",
    "networkpolicy-egress.yaml",
    "networkpolicy-route-allow-traefik.yaml",
    "service.yaml",
    "serviceaccount.yaml",
}
RUNTIME_DIGEST = "sha256:720ff5a60a7f6b91a75535e230dbb664207fdf1bc5cb8732d584bae7ebdac13c"
MIGRATION_DIGEST = "sha256:a4f0157e023c10c1c6ff163d34bf25c3343647247eddb1d4f9bfa9b46e1a3093"


def load_objects() -> list[dict]:
    return [yaml.safe_load(path.read_text()) for path in sorted(SOURCE.glob("*.yaml"))]


class ReactiveResumeDevArgoSourceContractTests(unittest.TestCase):
    def test_exact_value_free_runtime_closure(self) -> None:
        paths = {path.name for path in SOURCE.glob("*.yaml")}
        self.assertEqual(EXPECTED_FILES, paths)
        objects = load_objects()
        self.assertEqual(8, len(objects))
        self.assertEqual(
            {
                "Deployment",
                "Ingress",
                "Job",
                "NetworkPolicy",
                "Service",
                "ServiceAccount",
            },
            {obj["kind"] for obj in objects},
        )
        self.assertTrue(all(obj["metadata"]["namespace"] == "cristexhub-dev" for obj in objects))
        self.assertTrue(
            all(obj["metadata"]["labels"]["cristex.io/desired-owner"] == "argocd" for obj in objects)
        )
        text = "\n".join(path.read_text() for path in SOURCE.glob("*.yaml"))
        for forbidden in (
            "kind: Secret",
            "kind: PersistentVolumeClaim",
            "kind: Namespace",
            "stringData:",
            "job/reactive-resume-dev-migration",
            "reactive-resume-prod",
            "cristexhub-prod",
        ):
            self.assertNotIn(forbidden, text)
        self.assertNotRegex(text, r"image:\s+[^\s@]+\s*$", re.MULTILINE)
        self.assertNotRegex(text, r"(?m)^\s{2,}data:\s*$")
        self.assertIn(RUNTIME_DIGEST, text)
        self.assertIn(MIGRATION_DIGEST, text)

    def test_runtime_and_migration_contracts_are_exact(self) -> None:
        objects = {obj["kind"]: obj for obj in load_objects() if obj["kind"] in {"Deployment", "Job", "Service", "ServiceAccount"}}
        deployment = objects["Deployment"]
        self.assertEqual("reactive-resume-dev", deployment["metadata"]["name"])
        self.assertEqual(1, deployment["spec"]["replicas"])
        self.assertEqual(
            RUNTIME_DIGEST,
            deployment["spec"]["template"]["spec"]["containers"][0]["image"].split("@", 1)[1],
        )
        self.assertEqual("reactive-resume-dev", objects["ServiceAccount"]["metadata"]["name"])
        self.assertFalse(objects["ServiceAccount"].get("automountServiceAccountToken", True))
        service = objects["Service"]
        self.assertEqual("ClusterIP", service["spec"]["type"])
        self.assertEqual([{"name": "http", "port": 3000, "protocol": "TCP", "targetPort": "http"}], service["spec"]["ports"])
        job = objects["Job"]
        self.assertEqual("reactive-resume-dev-migrate", job["metadata"]["name"])
        self.assertEqual(
            MIGRATION_DIGEST,
            job["spec"]["template"]["spec"]["containers"][0]["image"].split("@", 1)[1],
        )
        self.assertEqual(["node"], job["spec"]["template"]["spec"]["containers"][0]["command"])
        self.assertEqual(["apps/server/dist/migrate.mjs"], job["spec"]["template"]["spec"]["containers"][0]["args"])
        self.assertEqual("Never", job["spec"]["template"]["spec"]["restartPolicy"])

    def test_route_and_network_boundaries_are_private(self) -> None:
        objects = load_objects()
        ingress = next(obj for obj in objects if obj["kind"] == "Ingress")
        self.assertEqual("traefik", ingress["spec"]["ingressClassName"])
        self.assertEqual("resume-dev.cristex-soft.com", ingress["spec"]["rules"][0]["host"])
        self.assertEqual("resume-dev.cristex-soft.com", ingress["spec"]["tls"][0]["hosts"][0])
        self.assertEqual("reactive-resume-dev-tls", ingress["spec"]["tls"][0]["secretName"])
        self.assertEqual(3000, ingress["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]["port"]["number"])
        policies = [obj for obj in objects if obj["kind"] == "NetworkPolicy"]
        self.assertEqual(
            {"reactive-resume-dev-default-deny", "reactive-resume-dev-egress", "reactive-resume-dev-route-allow-traefik"},
            {obj["metadata"]["name"] for obj in policies},
        )
        deny = next(obj for obj in policies if obj["metadata"]["name"].endswith("default-deny"))
        self.assertEqual({"Ingress", "Egress"}, set(deny["spec"]["policyTypes"]))
        route = next(obj for obj in policies if obj["metadata"]["name"].endswith("allow-traefik"))
        self.assertEqual([{"protocol": "TCP", "port": 3000}], route["spec"]["ingress"][0]["ports"])
        self.assertEqual("kube-system", route["spec"]["ingress"][0]["from"][0]["namespaceSelector"]["matchLabels"]["kubernetes.io/metadata.name"])
        self.assertEqual("traefik", route["spec"]["ingress"][0]["from"][0]["podSelector"]["matchLabels"]["app.kubernetes.io/name"])

    def test_registration_points_at_canonical_path(self) -> None:
        registration = yaml.safe_load(REGISTRATION.read_text())
        self.assertEqual("ansible/files/components/reactive-resume-dev-argocd", registration["spec"]["source"]["path"])
        self.assertRegex(registration["spec"]["source"]["targetRevision"], r"^[0-9a-f]{40}$")
        self.assertFalse(registration["spec"]["syncPolicy"]["automated"]["prune"])
        self.assertFalse(registration["spec"]["syncPolicy"]["automated"]["allowEmpty"])
        self.assertTrue(registration["spec"]["syncPolicy"]["automated"]["selfHeal"])

    def test_hash_ledger_modes_and_runbook_drift_guard(self) -> None:
        ledger = SOURCE / "MANIFESTS.sha256"
        self.assertEqual(0o644, stat.S_IMODE(ledger.stat().st_mode))
        entries = {}
        for line in ledger.read_text().splitlines():
            digest, relative = line.split(maxsplit=1)
            entries[relative] = digest
        self.assertEqual(EXPECTED_FILES, set(entries))
        for relative, digest in entries.items():
            self.assertEqual(digest, hashlib.sha256((SOURCE / relative).read_bytes()).hexdigest())
        for path in SOURCE.glob("*.yaml"):
            self.assertEqual(0o644, stat.S_IMODE(path.stat().st_mode))
        runbook = RUNBOOK.read_text()
        self.assertIn("ansible/files/components/reactive-resume-dev-argocd/", runbook)
        self.assertIn("reactive-resume-dev-migrate", runbook)
        self.assertIn("`job/reactive-resume-dev-migration`", runbook)
        self.assertNotIn("job/reactive-resume-dev-migration` (the canonical", runbook)


if __name__ == "__main__":
    unittest.main()
