from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "runbooks" / "cloudflared-candidate-provenance.md"
KUBERNETES = ROOT / "kubernetes"
OPENTOFU = ROOT / "opentofu"


class CloudflaredCandidateProvenanceContractTests(unittest.TestCase):
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

    def test_exact_release_and_source_provenance_is_recorded(self) -> None:
        self.assertTrue(RUNBOOK.is_file())
        self.assertEqual(
            {
                "Retrieval time": "`2026-08-07T06:13:42Z`",
                "Official latest release": "`2026.7.3`",
                "Release state": "draft `false`; prerelease `false`",
                "Published time": "`2026-07-23T10:19:16Z`",
                "Official release URL": "`https://github.com/cloudflare/cloudflared/releases/tag/2026.7.3`",
                "Annotated tag object": "`92bf87305b06c8614e78f5e6a7c6b2364a236c36`",
                "Resolved source commit": "`3a2b45c2a511fcdd81b68c190938e4ffadbea5dc`",
                "GitHub verification state": "annotated tag unsigned; resolved commit unsigned",
                "Official Darwin arm64 archive": "SHA-256 `90c5a4f914d705fd70c135dba6d80b1791d254b08d6d4136301941f88330dd09`",
                "Controller-side version result": "`cloudflared version 2026.7.3 (built 2026-07-23-10:03 UTC)`",
                "Official linux/amd64 binary asset": "SHA-256 `9d71c677db00134c1bd4144b7783486b654ad281b1ea62b4972098d19f770f17`; not executed",
            },
            self.table("## Release and source provenance evidence"),
        )
        for required in (
            "verified controller-side help binary was the Darwin arm64 asset, not the linux/amd64 runtime binary or container",
            "GitHub reports both the annotated tag and resolved commit as unsigned",
            "publisher identity, release authorization, provenance trust, and source-to-binary reproducibility are **not established**",
        ):
            self.assertIn(required, self.normalized)

    def test_exact_container_provenance_and_trust_boundary_is_recorded(self) -> None:
        self.assertEqual(
            {
                "Candidate image": "`docker.io/cloudflare/cloudflared:2026.7.3`",
                "Observed multi-platform index": "`sha256:e39ee8da81ad5e05d77f38d2f51c60ca51bf2a8450ac3abab50c17fdb91d91bf`",
                "Required linux/amd64 child": "`sha256:b392761b711c0e5649d9b64e1fc9a10ba0563fa3e712ed7c26bde5cc1fbe9059`",
                "linux/amd64 config": "`sha256:41320ce229c5fb52a316a5e3af2e6a1faa32b114aa9e2a5eed0652eff59e8eef`",
                "Config platform": "`linux`; `amd64`",
                "Config user": "`65532:65532`",
                "Config entrypoint": "`cloudflared`; `--no-autoupdate`",
                "Config default command": "`version`",
                "Config source linkage": "`org.opencontainers.image.source=https://github.com/cloudflare/cloudflared`; `CI_GIT_COMMIT=3a2b45c2a511fcdd81b68c190938e4ffadbea5dc`",
            },
            self.table("## Container image provenance evidence"),
        )
        for required in (
            "config source label and CI commit match the unsigned source commit",
            "registry digests establish observed content linkage, not a publisher signature, identity, authorization, or trusted build attestation",
            "tag is mutable",
            "exact selected architecture-specific child digest, not the tag or multi-platform index alone",
        ):
            self.assertIn(required, self.normalized)

    def test_token_health_and_network_evidence_is_exact_and_qualified(self) -> None:
        self.assertEqual(
            {
                "Token-file interface": "release help exposes `--token-file value`; no token or example value was captured",
                "Credential precedence": "`--token` takes precedence over credentials and token-file; token-file takes precedence over credentials",
                "Readiness endpoint": "`/ready` returns HTTP 200 only with more than zero active connections; otherwise HTTP 503",
                "Independent health endpoint": "`/healthcheck` returns `OK` independently of active tunnel connections",
                "Default virtual metrics binding": "all interfaces; semi-deterministic ports `20241` through `20245`, then a random fallback",
                "Metrics server surface": "readiness, health, metrics, debug, quick-tunnel, diagnostics, and configuration handlers share the listener",
                "Required Cloudflare edge egress": "outbound port `7844`: UDP for QUIC and TCP for HTTP/2 to the documented tunnel endpoints",
                "Name resolution": "DNS is required for the documented tunnel endpoints",
            },
            self.table("## Token, health, and network behavior evidence"),
        )
        for required in (
            "choose one fixed reviewed metrics port rather than the default range or random fallback",
            "expose no Service or Ingress for the metrics listener",
            "restrict the metrics, debug, quick-tunnel, diagnostics, and configuration surface",
            "Readiness must use connection-aware `/ready`; `/healthcheck` alone cannot prove that the tunnel can carry traffic",
            "does not copy the published address lists",
            "Kubernetes NetworkPolicy cannot express DNS-name or Cloudflare-managed anycast IP-set destinations",
            "bounded public TCP/UDP `7844` exception",
            "compensated by node/host egress controls",
        ):
            self.assertIn(required, self.normalized)

    def test_blockers_and_exact_source_only_boundary_are_enforced(self) -> None:
        for required in (
            "**SOURCE SELECTED — RUNTIME NOT RUN/BLOCKED.**",
            "The reviewed cloudflared and Infisical token-materialization source closures exist",
            "Human trust, version selection, and soak",
            "publisher signature, SBOM, vulnerability review, and trusted build evidence",
            "independent off-node availability",
            "read-only root filesystem, dropped capabilities, seccomp profile, non-root execution, and exact writable paths",
            "**NOT TESTED** because the local Docker daemon was inactive",
            "Token secret-zero, recovery, and rotation",
            "Infisical ownership of the token-file value",
            "No token may enter Git, OpenTofu state/plan, command arguments, environment examples, or logs",
            "Cloudflare external-resource ownership and state recovery",
            "encrypted timestamped state backup, independent key custody, integrity verification, isolated restore",
            "Argo CD installation and handoff",
            "Future-owner labels alone are not a handoff",
            "Exact component traffic policy",
            "DNS, Traefik, and Cloudflare-edge flows",
            "outbound port `7844` UDP/QUIC and TCP/HTTP/2",
            "no public route or hostname is approved",
            "one replica on one physical node is a shared failure domain",
            "Runtime approvals",
            "deny unrelated namespace, control-plane, metadata, metrics, debug, quick-tunnel, configuration, and public access",
            "does not select a release, authorize a Cloudflare resource, approve a route or hostname, or add an OpenTofu resource, Kubernetes object, chart, values file, credential, or secret value",
            "Reviewed cloudflared and Infisical token-materialization manifests now exist as source",
            "Any future cloudflared namespaced objects belong only in `platform-edge`",
            "Keycloak, PostgreSQL, MongoDB, and the Infisical Operator belong in `shared-services`, not `platform-edge`",
        ):
            self.assertIn(required, self.normalized)

        self.assertEqual(
            {
                "platform/namespaces/argocd.yaml",
                "platform/namespaces/platform-edge.yaml",
                "platform/namespaces/shared-services.yaml",
                "applications/namespaces/cristexhub-dev.yaml",
                "applications/namespaces/cristexhub-prod.yaml",
            },
            {
                str(path.relative_to(KUBERNETES))
                for path in KUBERNETES.rglob("*")
                if path.is_file()
            },
        )
        self.assertFalse(
            any(path.name in {"Chart.yaml", "values.yaml"} for path in KUBERNETES.rglob("*"))
        )
        self.assertEqual(
            {
                ".terraform.lock.hcl", "README.md", "backend.tf", "cloudflare.tf", "outputs.tf",
                "providers.tf", "variables.tf", "versions.tf",
            },
            {path.name for path in OPENTOFU.iterdir() if path.is_file()},
        )
        self.assertEqual(
            'terraform {\n  backend "local" {\n    path = "/var/lib/opentofu/cristexweb/foundation.tfstate"\n  }\n}\n',
            (OPENTOFU / "backend.tf").read_text(),
        )
        self.assertEqual('provider "cloudflare" {}\n', (OPENTOFU / "providers.tf").read_text())
        hcl = "\n".join(path.read_text() for path in OPENTOFU.glob("*.tf"))
        for forbidden_block in ("data", "module", "import"):
            self.assertNotRegex(hcl, rf"(?m)^\s*{forbidden_block}\s+[\"{{]")
        self.assertIn('resource "cloudflare_zero_trust_tunnel_cloudflared"', hcl)
        self.assertNotIn("tunnel_secret", hcl)
        self.assertNotIn("zero_trust_tunnel_cloudflared_token", hcl)

    def test_candidate_record_hygiene_and_documentation_links(self) -> None:
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
            "ansible-playbook ",
            "cloudflared tunnel run",
            "curl ",
            "docker run",
            "helm install",
            "kubectl apply",
            "rclone ",
            "ssh ",
            "tofu apply",
        ):
            self.assertNotIn(forbidden, self.text.lower())

        testcase_text = (
            ROOT / "specs" / "k3s-iac-foundation" / "testcases.md"
        ).read_text()
        cloudflared_validation = testcase_text.split(
            "## cloudflared candidate provenance source-only validation", 1
        )[1].split("\n## ", 1)[0]
        self.assertIn(
            "A later repository commit provides source traceability and is\nnot runtime evidence",
            cloudflared_validation,
        )
        self.assertNotIn("deployment, route, commit, or push", cloudflared_validation)

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
            self.assertIn("cloudflared-candidate-provenance.md", text, relative)


if __name__ == "__main__":
    unittest.main()
