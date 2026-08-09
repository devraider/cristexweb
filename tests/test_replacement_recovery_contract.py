from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOKS = ROOT / "runbooks"


class ReplacementRecoveryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runbook_path = RUNBOOKS / "replacement-host-recovery.md"
        cls.register_path = RUNBOOKS / "recovery-artifact-register.md"
        cls.runbook = cls.runbook_path.read_text()
        cls.register = cls.register_path.read_text()
        cls.combined = f"{cls.runbook}\n{cls.register}"

    def test_secret_free_recovery_documents_exist_without_executable_automation(self) -> None:
        self.assertTrue(self.runbook_path.is_file())
        self.assertTrue(self.register_path.is_file())
        self.assertEqual(
            {
                "argocd-candidate-provenance.md",
                "argocd-hardened-design.md",
                "argocd-release-selection.md",
                "cloudflared-candidate-provenance.md",
                "foundation-namespace-bootstrap.md",
                "infisical-operator-candidate-provenance.md",
                "infisical-operator-privileged-prerequisites-design.md",
                "infisical-operator-release-selection.md",
                "keycloak-oidc-bootstrap-design.md",
                "keycloak-release-selection.md",
                "reactive-resume-hosted-architecture.md",
                "shared-database-architecture.md",
                "recovery-artifact-register.md",
                "replacement-host-recovery.md",
            },
            {path.name for path in RUNBOOKS.iterdir() if path.is_file()},
        )
        self.assertNotIn("```", self.combined)
        ignore = (ROOT / ".gitignore").read_text()
        self.assertIn("recovery-artifact-register.local.*", ignore)
        self.assertIn("replacement-recovery.local.*", ignore)
        self.assertIn("replacement-host-recovery.local.*", ignore)
        for forbidden in (
            "ansible-playbook ",
            "kubectl ",
            "k3s etcd-snapshot",
            "systemctl ",
            "tofu apply",
            "tofu destroy",
            "helm install",
            "rclone sync",
        ):
            self.assertNotIn(forbidden, self.combined.lower())
        self.assertIn(
            "contains no executable k3s, datastore, token, disk,\nbackup, provider, or Kubernetes recovery command",
            self.runbook,
        )

    def test_reboot_and_replacement_boundaries_are_truthful(self) -> None:
        for required in (
            "same trusted installation, datastore, token,\n   storage, and cluster identity remain intact",
            "successful\nSSH/Tailscale return, running services, Ready node, and kubeconfig access do **not**\nprove recovery",
            "Do not relabel a replacement as\na reboot to bypass these gates",
            "No replacement recovery has been run or proven",
            "Replacement recovery remains **NOT RUN/BLOCKED**",
        ):
            self.assertIn(required, self.runbook)

    def test_old_host_fencing_and_identity_decision_fail_closed(self) -> None:
        for required in (
            "Gate 1 — isolate the old host and prevent split brain",
            "cannot concurrently mount, write, or attach",
            "cannot automatically rejoin",
            "Split-brain stop gate",
            "Do not start\nk3s on the replacement",
            "Gate 2 — choose the recovery identity model",
            "Preserve the existing cluster identity",
            "Create a new cluster identity",
            "There is no automatic default and no hybrid path",
            "Never import an old datastore into a separately\ninitialized fresh cluster",
        ):
            self.assertIn(required, self.runbook)

    def test_unknown_recovery_prerequisites_are_explicit_blockers(self) -> None:
        required_unknown_rows = (
            "Event classification",
            "Old-host fencing evidence reference",
            "Storage exclusivity evidence reference",
            "Recovery identity model",
            "Declared RPO",
            "Declared RTO",
            "k3s datastore",
            "Exact k3s version/configuration",
            "k3s server token",
            "Host/storage design",
            "OpenTofu state",
            "Infisical bootstrap material",
            "Application encryption keys",
            "PostgreSQL backups",
            "MongoDB backups",
            "RPO/RTO acceptance",
        )
        for row in required_unknown_rows:
            self.assertRegex(
                self.register,
                rf"(?m)^\| {re.escape(row)} \|.*UNKNOWN — STOP.*\|$",
            )
        self.assertIn(
            "A file existing only on the failed node is not a recovery artifact",
            self.runbook,
        )
        self.assertIn("off-node", self.runbook.lower())
        self.assertIn("off-node", self.register.lower())
        for required in (
            "Protected host-local single-writer owner",
            "timestamped off-node Google Drive copy",
            "isolated restore result",
        ):
            self.assertIn(required, self.register)
        self.assertRegex(
            self.register,
            r"(?m)^\| cloudflared component artifact \|.*cloudflared-candidate-provenance\.md.*CANDIDATE EVIDENCE ONLY — STOP \|$",
        )
        self.assertRegex(
            self.register,
            r"(?m)^\| Infisical Operator component artifact \|.*infisical-operator-candidate-provenance\.md.*CANDIDATE EVIDENCE ONLY — STOP \|$",
        )
        self.assertRegex(
            self.register,
            r"(?m)^\| Infisical bootstrap material \|.*UNKNOWN — STOP \|$",
        )
        self.assertRegex(
            self.register,
            r"(?m)^\| Replacement execution plan \(Gate 4\) \|.*NOT AUTHORED — GATE 3 BLOCKED \|$",
        )
        self.assertRegex(
            self.register,
            r"(?m)^\| Isolated restore rehearsal \(Gate 5\) \|.*NOT RUN — GATE 4 BLOCKED \|$",
        )
        self.assertLess(
            self.runbook.index("## Gate 3"),
            self.runbook.index("## Gate 4"),
        )
        self.assertLess(
            self.runbook.index("## Gate 4"),
            self.runbook.index("## Gate 5"),
        )

    def test_register_forbids_secret_values_and_contains_no_secret_shaped_data(self) -> None:
        for required in (
            "Never enter a secret value, kubeconfig, private key, recovery code, token",
            "off-node locator\nor record ID only",
            "not the value or a retrieval command",
            "Record only a\n  custodian-approved off-node reference",
        ):
            self.assertIn(required, self.combined)
        forbidden_patterns = (
            r"\bK10[a-zA-Z0-9]{20,}\b",
            r"\bghp_[A-Za-z0-9]+\b",
            r"\bgithub_pat_[A-Za-z0-9_]+\b",
            r"(?im)^\s*(?:certificate-authority-data|client-certificate-data|client-key-data|token):\s*\S+",
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
            r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
            r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
        )
        for pattern in forbidden_patterns:
            self.assertNotRegex(self.combined, pattern)
        private_addresses = (
            ".".join(("10", "1", "2", "3")),
            ".".join(("127", "0", "0", "1")),
            ".".join(("172", "16", "1", "2")),
            ".".join(("172", "31", "255", "254")),
            ".".join(("192", "168", "1", "1")),
        )
        for private_address in private_addresses:
            self.assertTrue(
                any(re.search(pattern, private_address) for pattern in forbidden_patterns),
                private_address,
            )


if __name__ == "__main__":
    unittest.main()
