from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "runbooks" / "infisical-operator-candidate-provenance.md"
KUBERNETES = ROOT / "kubernetes"
OPENTOFU = ROOT / "opentofu"


class InfisicalOperatorCandidateProvenanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = RUNBOOK.read_text()
        cls.normalized = " ".join(cls.text.split())

    def table(self, heading: str) -> dict[str, str]:
        section = self.text.split(heading, 1)[1]
        next_heading = section.find("\n## ")
        if next_heading >= 0:
            section = section[:next_heading]
        rows: dict[str, str] = {}
        for line in section.splitlines():
            if not line.startswith("|"):
                continue
            cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
            if cells[0] == "Item":
                continue
            if all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            self.assertEqual(2, len(cells), line)
            self.assertNotIn(cells[0], rows)
            rows[cells[0]] = cells[1]
        return rows

    def test_latest_release_distribution_gap_is_recorded_without_selection(self) -> None:
        self.assertTrue(RUNBOOK.is_file())
        self.assertEqual(
            {
                "Evidence capture began": "`2026-08-07T07:02:15Z`",
                "Evidence capture finalized": "`2026-08-07T07:29:40Z`",
                "Selected evidence hashes": "`24` verified",
                "Latest GitHub release": "`infisical-k8-operator/v0.11.8`",
                "Release state": "draft `false`; prerelease `false`",
                "Published time": "`2026-08-06T20:12:56Z`",
                "Source commit": "`fc5931fb329feeeeb17b84646772bfcabe1f7dc1`",
                "GitHub commit verification": "`verified: true`; reason `valid`",
                "Source archive": "SHA-256 `9cc6354d5dfe212687988b92dd08d4496797d56f93c3cf150f2d04e7461fd743`",
                "Source chart alignment": "chart `v0.11.8`; app `v0.11.8`; default image tag `v0.11.8`",
                "Public distribution observation": "matching Cloudsmith chart entry/archive and Docker Hub image tag were not observed at retrieval",
            },
            self.table("## Latest v0.11.8 source release and distribution gap"),
        )
        for required in (
            "time-qualified observation, not proof of permanent absence",
            "Mutable indexes and tags must be refreshed before any selection",
            "does not independently establish release authorization or bind the source, chart, container image, and current publisher trust chain",
            "**CANDIDATE — NOT DEPLOYABLE — NOT SELECTED.**",
            "Runtime evidence is **NOT RUN**",
        ):
            self.assertIn(required, self.normalized)

    def test_v0117_version_aligned_candidate_evidence_is_exact(self) -> None:
        self.assertEqual(
            {
                "Candidate status": "last observed version-aligned set; not selected",
                "Release/chart/app/image": "`v0.11.7` / `v0.11.7` / `v0.11.7` / `v0.11.7`",
                "Source commit": "`64d2d81da3707d81dc271410da6fd88254b6c9b3`",
                "GitHub commit verification": "`verified: true`; reason `valid`",
                "Chart archive": "SHA-256 `7f8846c4f6b1cdca2cea23cf00a29d12a38f42eb8da8e125dc196a1e5683aea8`",
                "Chart provenance file": "SHA-256 `a39ae4be9ca25f7dc0b50b6633c92fc320d427fd67364b50e82c0d512db7b933`",
                "Observed OCI index": "`sha256:89e211167a7cb2a271b63684aeceff0b599dc4b9f770e92f6ee0526cb64a4e68`",
                "Required linux/amd64 child": "`sha256:5f1767f440407d8f10fb8bd7e051e26ecf18f16731a64273c20fe206947510ae`",
                "linux/amd64 config": "`sha256:2c7bf8b4e450afba645bc504c5a5fef3ad8e728f6562599c830a0b2dbbf57bf4`",
                "Config user and entrypoint": "`65532:65532`; `/manager`",
            },
            self.table("## Last observed version-aligned v0.11.7 candidate"),
        )
        for required in (
            "Alignment is useful candidate evidence, not human selection, target-cluster compatibility, publisher authorization, image assurance, or deployment approval",
            "reviewed linux/amd64 child digest rather than a tag or index alone",
        ):
            self.assertIn(required, self.normalized)

    def test_chart_and_image_trust_boundaries_are_qualified(self) -> None:
        self.assertEqual(
            {
                "Provenance payload binding": "names the matching chart archive SHA-256 `7f8846c4f6b1cdca2cea23cf00a29d12a38f42eb8da8e125dc196a1e5683aea8`",
                "Provenance issuer fingerprint": "`D5CAFD69577534F2F6698C2BCFEA742D3B8FF4D5`",
                "Captured Cloudsmith public-key fingerprint": "`D5CAFD69577534F2F6698C2BCFEA742D3B8FF4D5`",
                "Cryptographic chart verification": "**NOT RUN**; captured verifier attempt reported `gpg: command not found`",
                "Independent trust result": "Infisical authorization, trust path, revocation status, and current signer authority remain blocked",
            },
            self.table("## Chart provenance and trust qualification"),
        )
        self.assertEqual(
            {
                "amd64 attestation manifest": "`sha256:0e561fbd350b7cf57b58acd27a5ff3a5de0c5a882e973681517dee318d30780a`",
                "SLSA statement layer": "`sha256:416cef4ba2778a2ed020d3f58c138ff4f5d0a79cc98bd553a7514edbbd0ec56c`",
                "Predicate type": "`https://slsa.dev/provenance/v1`",
                "Subject binding": "linux/amd64 child `sha256:5f1767f440407d8f10fb8bd7e051e26ecf18f16731a64273c20fe206947510ae`",
                "Source revision": "`64d2d81da3707d81dc271410da6fd88254b6c9b3`",
                "Builder identity": "empty",
                "Completeness": "BuildKit request and resolved-dependency completeness are false",
                "SBOM observation": "no SBOM was observed in the bounded evidence; this is not proof of absence",
            },
            self.table("## OCI image and attached SLSA content"),
        )
        for required in (
            "do not establish that Infisical authorized that key",
            "chart provenance must not be described as verified",
            "observed registry content",
            "not a verified publisher signature or trusted build attestation",
        ):
            self.assertIn(required, self.normalized)

    def test_namespace_rbac_secret_zero_and_compatibility_blockers_are_explicit(self) -> None:
        self.assertEqual(
            {
                "Kubernetes compatibility declaration": "no `kubeVersion` declaration",
                "Controller replicas": "`1`",
                "CRD behavior": "seven CRD templates; `installCRDs: true`",
                "Default watch scope": "all Namespaces; `scopedNamespaces: []`; `scopedRBAC: false`",
                "Metrics Service": "private `ClusterIP`",
                "Container hardening defaults": "non-root; read-only root filesystem; privilege escalation disabled; all capabilities dropped",
                "Pod hardening defaults": "`runAsNonRoot: true`; `RuntimeDefault` seccomp",
                "Image template behavior": "concatenates repository and tag; digest rendering must be proven before source",
            },
            self.table("## Chart defaults and runtime implications"),
        )
        for required in (
            "Human version, trust, and soak selection",
            "approved schema-v3 discovery now captures target kubelet `v1.36.2+k3s1`",
            "chart, CRD/API, and exact k3s compatibility remain unproven",
            "Target compatibility",
            "approved schema-v3 discovery captured kubelet `v1.36.2+k3s1`",
            "Review every rendered CRD/API version and prove exact chart and k3s compatibility",
            "Chart and image assurance",
            "Dedicated operator Namespace",
            "current Ansible exception can create only `argocd` and `platform-edge`",
            "cannot create an Infisical Namespace",
            "Argo CD must later reconcile the dedicated Namespace",
            "Do not place the operator into `argocd`, `platform-edge`, shared-data, `shared-services`, `cristexhub-dev`, or `cristexhub-prod` by default",
            "Argo installation and ownership handoff",
            "Watch scope and least-privilege RBAC",
            "CRD lifecycle and permissions",
            "Exact component traffic policy",
            "Kubernetes API, DNS, Infisical API, and private metrics flows",
            "Secret-zero, recovery, rotation, and revocation",
            "Argo owns committed CR/reference objects; Infisical owns generated Secret values",
            "No bootstrap credential may enter Git, OpenTofu state/plan, command arguments, environment examples, CI logs, or review artifacts",
            "Environment separation and bootstrap circularity",
            "Single-node availability",
            "Runtime approvals",
            "explicit non-empty target scope or document and separately approve why cluster-wide access is required",
            "reviewed `tag@linux/amd64-digest` reference works before deployable source is added",
        ):
            self.assertIn(required, self.normalized)

    def test_candidate_hygiene_source_closure_and_documentation_links(self) -> None:
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
        for private_address in (
            ".".join(("10", "1", "2", "3")),
            ".".join(("127", "0", "0", "1")),
            ".".join(("172", "16", "1", "2")),
            ".".join(("172", "31", "255", "254")),
            ".".join(("192", "168", "1", "1")),
        ):
            self.assertTrue(
                any(re.search(pattern, private_address) for pattern in forbidden_patterns),
                private_address,
            )
        for forbidden in (
            "ansible-playbook ",
            "curl ",
            "docker run",
            "helm install",
            "helm upgrade",
            "kubectl apply",
            "rclone ",
            "ssh ",
            "tofu apply",
        ):
            self.assertNotIn(forbidden, self.text.lower())

        self.assertEqual(
            {
                "platform/namespaces/argocd.yaml",
                "platform/namespaces/platform-edge.yaml",
            },
            {
                str(path.relative_to(KUBERNETES))
                for path in KUBERNETES.rglob("*")
                if path.is_file()
            },
        )
        self.assertFalse(
            any(
                path.name in {"Chart.yaml", "values.yaml"}
                or "crd" in path.name.lower()
                or "secret" in path.name.lower()
                for path in KUBERNETES.rglob("*")
                if path.is_file()
            )
        )
        self.assertEqual(
            {"README.md", "backend.tf", "providers.tf", "versions.tf"},
            {path.name for path in OPENTOFU.iterdir() if path.is_file()},
        )
        hcl = "\n".join(path.read_text() for path in OPENTOFU.glob("*.tf"))
        for forbidden_block in ("resource", "data", "module", "import", "variable", "output"):
            self.assertNotRegex(hcl, rf"(?m)^\s*{forbidden_block}\s+[\"{{]")

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
            self.assertIn(
                "infisical-operator-candidate-provenance.md",
                (ROOT / relative).read_text(),
                relative,
            )


if __name__ == "__main__":
    unittest.main()
