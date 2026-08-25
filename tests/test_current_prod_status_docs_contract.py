from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CurrentProdStatusDocsContractTests(unittest.TestCase):
    def test_authoritative_docs_record_current_alias_pending_state(self) -> None:
        docs = {
            "AGENTS.md": (ROOT / "AGENTS.md").read_text(),
            "ansible/README.md": (ROOT / "ansible/README.md").read_text(),
            "specs/k3s-iac-foundation/status.md": (
                ROOT / "specs/k3s-iac-foundation/status.md"
            ).read_text(),
        }
        for path, text in docs.items():
            with self.subTest(path=path):
                self.assertIn("Unknown/Missing", text)
                self.assertIn("cristexhub-prod-local", text)
                self.assertIn("Synced/Healthy", text)
                self.assertIn("historical", text.lower())
                self.assertIn("public", text.lower())

        for path in ("AGENTS.md", "ansible/README.md", "specs/k3s-iac-foundation/status.md"):
            with self.subTest(path=path):
                text = docs[path]
                self.assertIn("409 Conflict", text)
                self.assertIn("resourceVersion", text)
                self.assertIn("source", text.lower())
                self.assertIn("check", text.lower())
                self.assertTrue(
                    "not applied" in text.lower() or "unapplied" in text.lower()
                )

    def test_authoritative_docs_record_opentofu_source_and_state_counts(self) -> None:
        docs = {
            "AGENTS.md": (ROOT / "AGENTS.md").read_text(),
            "README.md": (ROOT / "README.md").read_text(),
            "ansible/README.md": (ROOT / "ansible/README.md").read_text(),
            "specs/k3s-iac-foundation/status.md": (
                ROOT / "specs/k3s-iac-foundation/status.md"
            ).read_text(),
        }
        for path, text in docs.items():
            with self.subTest(path=path):
                self.assertIn("five imported", text)
                self.assertIn("seven", text.lower())
                self.assertIn("pending", text.lower())
        tofu = (ROOT / "opentofu/README.md").read_text()
        self.assertIn("exactly five imported", tofu)
        self.assertIn("defines seven resource addresses", tofu)
        self.assertIn("import prerequisite", tofu)


if __name__ == "__main__":
    unittest.main()
