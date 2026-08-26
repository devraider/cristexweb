from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CurrentProdStatusDocsContractTests(unittest.TestCase):
    def test_authoritative_docs_record_current_direct_server_synced_healthy_state(self) -> None:
        docs = {
            "AGENTS.md": (ROOT / "AGENTS.md").read_text(),
            "README.md": (ROOT / "README.md").read_text(),
            "ansible/README.md": (ROOT / "ansible/README.md").read_text(),
            "specs/k3s-iac-foundation/brief.md": (
                ROOT / "specs/k3s-iac-foundation/brief.md"
            ).read_text(),
            "specs/k3s-iac-foundation/status.md": (
                ROOT / "specs/k3s-iac-foundation/status.md"
            ).read_text(),
            "specs/k3s-iac-foundation/testcases.md": (
                ROOT / "specs/k3s-iac-foundation/testcases.md"
            ).read_text(),
            "runbooks/cristexhub-prod-argocd-registration.md": (
                ROOT / "runbooks/cristexhub-prod-argocd-registration.md"
            ).read_text(),
        }
        for path, text in docs.items():
            with self.subTest(path=path):
                self.assertIn("Synced/Healthy", text)
                self.assertIn("751885a42798d282e168131db147f13694a0a621", text)
                self.assertIn("historical", text.lower())
                self.assertIn("public", text.lower())
                self.assertRegex(
                    text,
                    r"(?is)(?:Unknown/Missing).{0,120}historical|historical.{0,120}(?:Unknown/Missing)",
                )
                self.assertNotIn("current snapshot is `Unknown/Missing`", text)
                self.assertNotIn("current Argo status is `Unknown/Missing`", text)
                self.assertNotIn("live Application is currently `Unknown/Missing`", text)

        for path in ("AGENTS.md", "ansible/README.md", "specs/k3s-iac-foundation/status.md"):
            with self.subTest(path=path):
                text = docs[path]
                self.assertIn("direct-server", text)
                self.assertIn("target-cache repair", text.lower())
                self.assertIn("idempotence", text.lower())
                self.assertIn("pending", text.lower())
                self.assertTrue(
                    "not applied" in text.lower() or "unapplied" in text.lower()
                )

    def test_authoritative_docs_record_opentofu_source_and_state_counts(self) -> None:
        docs = {
            "AGENTS.md": (ROOT / "AGENTS.md").read_text(),
            "README.md": (ROOT / "README.md").read_text(),
            "ansible/README.md": (ROOT / "ansible/README.md").read_text(),
            "specs/k3s-iac-foundation/brief.md": (
                ROOT / "specs/k3s-iac-foundation/brief.md"
            ).read_text(),
            "specs/k3s-iac-foundation/status.md": (
                ROOT / "specs/k3s-iac-foundation/status.md"
            ).read_text(),
            "opentofu/README.md": (ROOT / "opentofu/README.md").read_text(),
            "runbooks/cloudflared-candidate-provenance.md": (
                ROOT / "runbooks/cloudflared-candidate-provenance.md"
            ).read_text(),
        }
        for path, text in docs.items():
            with self.subTest(path=path):
                self.assertIn("five imported", text)
                self.assertRegex(text.lower(), r"defines seven|seven resource")
                self.assertIn("pending", text.lower())
                self.assertIn("DEV DNS", text)
                self.assertIn("six", text.lower())
        tofu = docs["opentofu/README.md"]
        self.assertIn("exactly five imported", tofu)
        self.assertIn("defines seven resource addresses", tofu)
        self.assertIn("import prerequisite", tofu)


if __name__ == "__main__":
    unittest.main()
