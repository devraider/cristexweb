import hashlib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ansible/files/components/reactive-resume-dev-tls-rbac"


class ReactiveResumeDevTlsRbacContractTests(unittest.TestCase):
    def test_exact_least_privilege_source_closure(self) -> None:
        paths = sorted(SOURCE.glob("*.yaml"))
        self.assertEqual(["role.yaml", "rolebinding.yaml"], [path.name for path in paths])
        objects = [yaml.safe_load(path.read_text()) for path in paths]
        role = next(item for item in objects if item["kind"] == "Role")
        binding = next(item for item in objects if item["kind"] == "RoleBinding")
        self.assertEqual("cristexhub-dev", role["metadata"]["namespace"])
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
        text = "\n".join(path.read_text() for path in paths)
        self.assertNotIn("kind: Secret", text)
        self.assertNotIn("BEGIN ", text)
        ledger = (SOURCE / "MANIFESTS.sha256").read_text().splitlines()
        self.assertEqual(2, len(ledger))
        for path in paths:
            self.assertIn(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}", ledger)


if __name__ == "__main__":
    unittest.main()
