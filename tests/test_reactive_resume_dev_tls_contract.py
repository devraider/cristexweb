import hashlib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/reactive-resume-dev-tls"
MANIFEST = COMPONENT / "source/reactive-resume-dev-tls.yaml"


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

    def test_manifest_hash_is_exact(self) -> None:
        expected = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
        self.assertIn(
            f"{expected}  source/reactive-resume-dev-tls.yaml",
            (COMPONENT / "MANIFESTS.sha256").read_text().splitlines(),
        )


if __name__ == "__main__":
    unittest.main()
