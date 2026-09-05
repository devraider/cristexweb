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
    "infisical-tls-writer-binding.yaml",
    "infisical-tls-writer-rbac.yaml",
    "networkpolicy-allow-backend.yaml",
    "networkpolicy-default-deny.yaml",
    "networkpolicy-egress.yaml",
    "networkpolicy-route-allow-traefik.yaml",
    "service.yaml",
    "serviceaccount.yaml",
}
HANDOFF = ROOT / "ansible/files/policies/reactive-resume-dev-argocd-handoff"
RUNTIME_DIGEST = "sha256:720ff5a60a7f6b91a75535e230dbb664207fdf1bc5cb8732d584bae7ebdac13c"
MIGRATION_DIGEST = "sha256:a4f0157e023c10c1c6ff163d34bf25c3343647247eddb1d4f9bfa9b46e1a3093"
MIGRATION_SOURCE_SHA256 = "b262ddb6834eb9d14d0eb279bb1a1c8686df83fedea56dc51d01fddc2281a3ac"
PINNED_REVISION = "f5d15f011865a93c16278ed7b89cf32c02c52fa8"
PINNED_FILES = EXPECTED_FILES


def load_objects() -> list[dict]:
    return [yaml.safe_load(path.read_text()) for path in sorted(SOURCE.glob("*.yaml"))]


class ReactiveResumeDevArgoSourceContractTests(unittest.TestCase):
    def test_exact_value_free_runtime_closure(self) -> None:
        paths = {path.name for path in SOURCE.glob("*.yaml")}
        self.assertEqual(EXPECTED_FILES, paths)
        objects = load_objects()
        self.assertEqual(10, len(objects))
        self.assertEqual(
            {
                "Deployment",
                "Ingress",
                "NetworkPolicy",
                "Role",
                "RoleBinding",
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
            "kind: Job",
            "reactive-resume-prod",
            "cristexhub-prod",
        ):
            self.assertNotIn(forbidden, text)
        self.assertNotRegex(text, r"image:\s+[^\s@]+\s*$", re.MULTILINE)
        self.assertNotRegex(text, r"(?m)^\s{2,}data:\s*$")
        self.assertIn(RUNTIME_DIGEST, text)
        self.assertNotIn(MIGRATION_DIGEST, text)

    def test_runtime_contract_is_exact_and_migration_is_not_automated(self) -> None:
        objects = {obj["kind"]: obj for obj in load_objects() if obj["kind"] in {"Deployment", "Service", "ServiceAccount"}}
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
        handoff = [yaml.safe_load(path.read_text()) for path in sorted(HANDOFF.glob("*.yaml"))]
        migration = next(obj for obj in handoff if obj["kind"] == "Job")
        self.assertEqual("reactive-resume-dev-migrate", migration["metadata"]["name"])
        self.assertEqual("Job", migration["kind"])
        self.assertEqual("ansible", migration["metadata"]["labels"]["app.kubernetes.io/managed-by"])
        self.assertEqual("argocd", migration["metadata"]["labels"]["cristex.io/desired-owner"])
        self.assertEqual("ghcr.io/devraider/cristex-reactive-resume@sha256:a4f0157e023c10c1c6ff163d34bf25c3343647247eddb1d4f9bfa9b46e1a3093", migration["spec"]["template"]["spec"]["containers"][0]["image"])
        self.assertEqual(
            {"DATABASE_URL", "MIGRATION_DATABASE_URL"},
            {env["name"] for env in migration["spec"]["template"]["spec"]["containers"][0]["env"] if "valueFrom" in env},
        )
        secret_refs = [env["valueFrom"]["secretKeyRef"] for env in migration["spec"]["template"]["spec"]["containers"][0]["env"] if "valueFrom" in env]
        self.assertTrue(all(ref["name"] == "reactive-resume-dev-migration" and ref["optional"] is False for ref in secret_refs))
        self.assertEqual("reactive-resume-dev-postgresql-ca", migration["spec"]["template"]["spec"]["volumes"][0]["configMap"]["name"])
        self.assertNotIn("migration-job.yaml", {path.name for path in SOURCE.glob("*.yaml")})

    def test_infisical_tls_writer_rbac_is_exact(self) -> None:
        objects = load_objects()
        role = next(obj for obj in objects if obj["kind"] == "Role")
        binding = next(obj for obj in objects if obj["kind"] == "RoleBinding")
        self.assertEqual(
            [{
                "apiGroups": [""],
                "resources": ["secrets"],
                "resourceNames": ["reactive-resume-dev-tls"],
                "verbs": ["get", "update", "patch"],
            }],
            role["rules"],
        )
        self.assertEqual("reactive-resume-dev-tls-infisical-writer", binding["roleRef"]["name"])
        self.assertEqual(
            [{"kind": "ServiceAccount", "name": "infisical-operator-controller", "namespace": "shared-services"}],
            binding["subjects"],
        )

    def test_route_and_network_boundaries_are_private(self) -> None:
        objects = load_objects()
        ingress = next(obj for obj in objects if obj["kind"] == "Ingress")
        self.assertEqual("traefik", ingress["spec"]["ingressClassName"])
        self.assertEqual("dev-resume.cristex-soft.com", ingress["spec"]["rules"][0]["host"])
        self.assertEqual("dev-resume.cristex-soft.com", ingress["spec"]["tls"][0]["hosts"][0])
        self.assertEqual("reactive-resume-dev-tls", ingress["spec"]["tls"][0]["secretName"])
        self.assertEqual(3000, ingress["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]["port"]["number"])
        policies = [obj for obj in objects if obj["kind"] == "NetworkPolicy"]
        self.assertEqual(
            {"reactive-resume-dev-allow-backend", "reactive-resume-dev-default-deny", "reactive-resume-dev-egress", "reactive-resume-dev-route-allow-traefik"},
            {obj["metadata"]["name"] for obj in policies},
        )
        deny = next(obj for obj in policies if obj["metadata"]["name"].endswith("default-deny"))
        self.assertEqual({"Ingress", "Egress"}, set(deny["spec"]["policyTypes"]))
        route = next(obj for obj in policies if obj["metadata"]["name"].endswith("allow-traefik"))
        self.assertEqual([{"protocol": "TCP", "port": 3000}], route["spec"]["ingress"][0]["ports"])
        self.assertEqual("kube-system", route["spec"]["ingress"][0]["from"][0]["namespaceSelector"]["matchLabels"]["kubernetes.io/metadata.name"])
        self.assertEqual("traefik", route["spec"]["ingress"][0]["from"][0]["podSelector"]["matchLabels"]["app.kubernetes.io/name"])

    def test_registration_points_at_pinned_ten_object_revision(self) -> None:
        registration = yaml.safe_load(REGISTRATION.read_text())
        self.assertEqual("ansible/files/components/reactive-resume-dev-argocd", registration["spec"]["source"]["path"])
        self.assertEqual(PINNED_REVISION, registration["spec"]["source"]["targetRevision"])
        self.assertEqual(10, len(PINNED_FILES))
        self.assertIn("networkpolicy-allow-backend.yaml", PINNED_FILES)
        self.assertFalse(registration["spec"]["syncPolicy"]["automated"]["prune"])
        self.assertFalse(registration["spec"]["syncPolicy"]["automated"]["allowEmpty"])
        self.assertTrue(registration["spec"]["syncPolicy"]["automated"]["selfHeal"])

    def test_head_ten_manifest_is_claimed_live_and_argo_managed(self) -> None:
        runbook = RUNBOOK.read_text()
        normalized = " ".join(runbook.split())
        self.assertIn("source contains exactly ten value-free Kubernetes objects", normalized)
        self.assertIn("networkpolicy-allow-backend.yaml", normalized)
        self.assertIn("claimed live and Argo-managed", runbook)

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
        self.assertIn(MIGRATION_DIGEST, runbook)
        self.assertIn(MIGRATION_SOURCE_SHA256, runbook)
        self.assertIn("excluded from the automated Argo desired-state", runbook)
        self.assertIn("one-shot", runbook)
        self.assertIn("migration-job.yaml", runbook)
        self.assertNotIn("`job/reactive-resume-dev-migration`", runbook)


if __name__ == "__main__":
    unittest.main()
