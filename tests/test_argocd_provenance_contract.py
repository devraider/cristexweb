from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "runbooks" / "argocd-candidate-provenance.md"
KUBERNETES = ROOT / "kubernetes"


class ArgoCdCandidateProvenanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = RUNBOOK.read_text()

    def table(self, heading: str) -> dict[str, tuple[str, ...]]:
        section = self.text.split(heading, 1)[1]
        next_heading = section.find("\n## ")
        if next_heading >= 0:
            section = section[:next_heading]
        rows: dict[str, tuple[str, ...]] = {}
        for line in section.splitlines():
            if not line.startswith("|"):
                continue
            cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
            if cells[0] in {"Item", "Candidate image", "Ignored evidence"}:
                continue
            if all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            self.assertNotIn(cells[0], rows)
            rows[cells[0]] = cells[1:]
        return rows

    def test_exact_upstream_and_image_provenance_is_recorded(self) -> None:
        self.assertTrue(RUNBOOK.is_file())
        self.assertIn("2026-08-07T05:42:22Z", self.text)
        self.assertEqual(
            {
                "Official argo-helm index": (
                    "SHA-256 `d0281dd436a64de6ce419d231bec7beb61ffa890b1e9aac4bec60380d7a4360f`",
                ),
                "Chart/application": ("`argo-cd` chart `10.3.0`; application `v3.5.0`",),
                "Official chart URL": (
                    "`https://github.com/argoproj/argo-helm/releases/download/argo-cd-10.3.0/argo-cd-10.3.0.tgz`",
                ),
                "Chart archive": (
                    "SHA-256 `d08882d22d0c76e3174e005cc09abe300c70ba556aec76725a4410d172b9c1f3`",
                ),
                "Declared Kubernetes range": ("`kubeVersion: >=1.25.0-0`",),
                "Official provenance file": (
                    "SHA-256 `52157f1e9cf2a68cc26e6e456bff03afdfe11a8f1637078a72262e980fb5cd02`",
                ),
                "Official signing-key URL": (
                    "`https://argoproj.github.io/argo-helm/pgp_keys.asc`",
                ),
                "Signing-key fingerprint": ("`2B8F22F57260EFA67BE1C5824B11F800CD9D2252`",),
                "Helm verification result": (
                    "Succeeded as `Argo Helm maintainers`; the verified chart hash matched the archive SHA-256 above",
                ),
                "Verification tool": (
                    "Helm `v3.21.3+g1ad6e68`; archive SHA-256 `19879a848cad832b7a1ac24b767a481d20fb3b95ab53a220849649422ada144e`",
                ),
            },
            self.table("## Upstream chart and verification evidence"),
        )
        self.assertEqual(
            {
                "`quay.io/argoproj/argocd:v3.5.0`": (
                    "`sha256:c298cedbaeb31532ba8d4e9904eba9e4987e067293fbd86400c5194e78f743d5`",
                    "`sha256:521d6b62ecd0434c9cc6e9242a74f0e1137bb8fc0026b2c483ea88f3f17e725d`",
                    "`sha256:79eb3a49a62f9a6ec75db06bee304030272f9a6bd3b86279f88562ddfc3c4695`; `linux`; `amd64`; user `999`",
                ),
                "Candidate Redis override `docker.io/library/redis:8.6.4-alpine`": (
                    "`sha256:2cc044fc5a07c9b701f8f1255a309ae9ad7856e694ac03513bf3648c01e40763`",
                    "`sha256:c64af41b8fc06a2d9b8fde812dd781aa157bed6fcf8ae1656ad4e79f3f9fc9b1`",
                    "`sha256:28a8a19f9dd9e63eb5b00e62e385739e9727aacdf1275a037ab52e517c419ded`; `linux`; `amd64`",
                ),
            },
            self.table("## Image provenance evidence"),
        )
        for required in (
            "valid under the captured key\nfingerprint and binds the captured chart hash",
            "does **not** independently\nestablish the signing key's publisher identity",
            "trust path, or\nrevocation status",
        ):
            self.assertIn(required, self.text)

    def test_target_minor_screen_is_exact_and_narrowly_qualified(self) -> None:
        self.assertEqual(
            {
                "Approved discovery report time": ("`2026-08-07T08:09:31Z`",),
                "Target kubelet": ("`v1.36.2+k3s1`; Kubernetes minor `1.36`",),
                "Compatibility evidence retrieval": ("`2026-08-07T08:13:26Z`",),
                "Official Argo CD v3.5.0 source archive": (
                    "SHA-256 `f63ae068404901496f8501f386386aa89566bce37b18d44b6026d01a23abfc24`",
                ),
                "Official tested-version matrix": (
                    "SHA-256 `5f32e19055811f9fea77e31e4f6f9bd1b5a809d845ffa4832162fc3dea9f65df`; Argo CD `3.5` tested with Kubernetes `v1.36`, `v1.35`, `v1.34`, and `v1.33`",
                ),
                "Official CI workflow": (
                    "SHA-256 `14ba51038ddc46a4e5ad7dbdbb2772662ebce13d116d61d53ba378ff04c742ef`; includes k3s `v1.36.0`",
                ),
                "Official Go module file": (
                    "SHA-256 `c1dd593a09cccaf6e51a6a3cf64b9c2e2af6c4f453c8f8b9ced8f1b41fff3799`; includes `k8s.io/kubernetes v1.36.1`",
                ),
                "Chart semver gate": (
                    "chart `10.3.0` / app `v3.5.0` declares `kubeVersion: >=1.25.0-0`",
                ),
            },
            self.table("## Target-minor compatibility evidence"),
        )
        for required in (
            "target Kubernetes minor `1.36` is in Argo CD `3.5`'s official tested\nmatrix",
            "chart's declared semver gate admits target version\n`v1.36.2+k3s1`",
            "closes only the candidate's target-minor screening",
            "not proof that this\nexact k3s patch/distribution",
            "rendered APIs and CRDs",
            "No chart was installed or rendered against the live API",
            "no Argo CD runtime\nvalidation succeeded or was attempted",
        ):
            self.assertIn(required, self.text)

    def test_ignored_render_is_bound_and_described_without_selection(self) -> None:
        self.assertEqual(
            {
                "Minimal candidate values": (
                    "`fb1564687186fdf9742c56de5534eed6e9c1496a8aa65cf5ade8b875ea0f839a`",
                ),
                "Rendered output": (
                    "`51bb87262f6896d9621a05fb0a340ccf12cac0a45cdfb72516be821892c15480`",
                ),
                "Render summary": (
                    "`26ed8310c453152cdbd78e7914e66a5d8039acf7dbbe74b3cf09d09c5f2c47a0`",
                ),
            },
            self.table("## Ignored candidate render evidence"),
        )
        for required in (
            "**CANDIDATE — NOT DEPLOYABLE — NOT SELECTED.**",
            "Argo CD runtime evidence is **NOT RUN**",
            "candidate render contains 44 documents",
            "3 CustomResourceDefinitions",
            "4 Deployments, including the ApplicationSet controller",
            "1 StatefulSet",
            "1 `redis-secret-init` Job and 1 Secret",
            "4 ClusterIP Services and 4 NetworkPolicies",
            "2 ClusterRoles and 2 ClusterRoleBindings",
            "5 Roles, 5 RoleBindings, and 5 ServiceAccounts",
            "7 ConfigMaps",
            "There are 7 image occurrences",
            "both resource requests\nand limits",
            "has one replica",
            "no\nPVC and no ingress-like object",
            "Dex, notifications, and `redis-ha` were disabled",
            "chart `10.3.0` has no effective `applicationSet.enabled` disable\ngate",
            "candidate render retains the ApplicationSet controller",
        ):
            self.assertIn(required, self.text)
        self.assertNotIn("applicationSet.enabled: false", self.text)
        self.assertNotIn("ApplicationSet was disabled", self.text)

    def test_blockers_and_source_only_boundary_are_truthful(self) -> None:
        for required in (
            "Full target Kubernetes compatibility",
            "captured target minor `1.36` is in\n   Argo CD `3.5`'s official tested matrix",
            "does not prove exact k3s patch/distribution behavior, rendered\n   API/CRD compatibility",
            "Offline render/schema review and separately approved target runtime\n   validation remain blocked",
            "Human trust, selection, and soak",
            "signing-key trust/status",
            "Generated and internal Secret ownership/recovery",
            "`argocd-secret`",
            "initial\n   admin credential",
            "TLS/signing material",
            "`redis-secret-init` Job",
            "Private Git secret-zero and recovery",
            "Image acquisition and component traffic",
            "exact Quay and Docker Hub child digests",
            "component flow matrix for Kubernetes API,\n   DNS, Redis",
            "NetworkPolicies are ingress-only and do not establish egress default-deny",
            "Bootstrap ownership exception",
            "Future-owner\n   labels alone do not establish Argo ownership",
            "Runtime approvals",
            "Argo CD must remain private",
            "does not select a\nrelease, authorize a bootstrap, or add a Helm chart, values file, Kubernetes object,\ncredential, or secret value",
        ):
            self.assertIn(required, self.text)

        expected_kubernetes = {
            "platform/namespaces/argocd.yaml",
            "platform/namespaces/platform-edge.yaml",
        }
        actual_kubernetes = {
            str(path.relative_to(KUBERNETES))
            for path in KUBERNETES.rglob("*")
            if path.is_file()
        }
        self.assertEqual(expected_kubernetes, actual_kubernetes)
        self.assertFalse(any(path.name in {"Chart.yaml", "values.yaml"} for path in KUBERNETES.rglob("*")))

    def test_candidate_record_contains_no_secret_or_private_address_material(self) -> None:
        self.assertNotIn("```", self.text)
        forbidden_patterns = (
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"\bghp_[A-Za-z0-9]+\b",
            r"\bgithub_pat_[A-Za-z0-9_]+\b",
            r"(?im)^\s*(?:certificate-authority-data|client-certificate-data|client-key-data|token):\s*\S+",
            r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
            r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
            r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
        )
        for pattern in forbidden_patterns:
            self.assertNotRegex(self.text, pattern)
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
        for forbidden in (
            "helm install",
            "helm upgrade",
            "kubectl apply",
            "argocd app sync",
            "tofu apply",
            "ansible-playbook ",
        ):
            self.assertNotIn(forbidden, self.text.lower())

        for relative in (
            "README.md",
            "architecture-plan.md",
            "specs/k3s-iac-foundation/brief.md",
            "specs/k3s-iac-foundation/requirements.md",
            "specs/k3s-iac-foundation/tasks.md",
            "specs/k3s-iac-foundation/testcases.md",
            "specs/k3s-iac-foundation/manual-qa.md",
            "specs/k3s-iac-foundation/status.md",
        ):
            text = (ROOT / relative).read_text()
            self.assertIn("argocd-candidate-provenance.md", text, relative)


if __name__ == "__main__":
    unittest.main()
