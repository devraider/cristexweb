import hashlib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/reactive-resume-dev-tls"
MANIFEST = COMPONENT / "source/reactive-resume-dev-tls.yaml"
RBAC_PATHS = [
    COMPONENT / "rbac/infisical-writer-role.yaml",
    COMPONENT / "rbac/infisical-writer-rolebinding.yaml",
]


class ReactiveResumeDevTlsContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = MANIFEST.read_text()
        self.docs = list(yaml.safe_load_all(self.text))

    def test_exact_value_free_infisical_tls_closure(self) -> None:
        self.assertEqual(
            [
                "ValidatingAdmissionPolicy",
                "ValidatingAdmissionPolicyBinding",
                "ValidatingAdmissionPolicy",
                "ValidatingAdmissionPolicyBinding",
                "InfisicalStaticSecret",
            ],
            [doc["kind"] for doc in self.docs],
        )
        self.assertIn("/reactive-resume/dev/tls", self.text)
        self.assertIn("kubernetes.io/tls", self.text)
        self.assertIn("reactive-resume-dev-tls", self.text)
        self.assertIn("{{ .TLS_CRT.Value }}", self.text)
        self.assertIn("{{ .TLS_KEY.Value }}", self.text)
        for forbidden in ("BEGIN CERTIFICATE", "BEGIN PRIVATE KEY", "stringData:"):
            self.assertNotIn(forbidden, self.text)

    def test_infisical_tls_writer_rbac_is_exact(self) -> None:
        objects = [yaml.safe_load(path.read_text()) for path in RBAC_PATHS]
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

    def test_manifest_hashes_are_exact(self) -> None:
        manifest_ledger = (COMPONENT / "MANIFESTS.sha256").read_text().splitlines()
        expected = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
        self.assertIn(f"{expected}  source/reactive-resume-dev-tls.yaml", manifest_ledger)
        rbac_ledger = (COMPONENT / "RBAC.sha256").read_text().splitlines()
        for path in RBAC_PATHS:
            relative = path.relative_to(COMPONENT)
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertIn(f"{expected}  {relative}", rbac_ledger)


if __name__ == "__main__":
    unittest.main()
