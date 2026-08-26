from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOFU = ROOT / "opentofu"
BIN = TOFU / "bin"
RECONCILE = BIN / "reconcile-foundation-state"
SCOPE = BIN / "validate-foundation-state-scope"
MANIFEST = BIN / "SOURCE.sha256"
RUNBOOK = ROOT / "runbooks/opentofu-foundation-state-reconciliation.md"
EXPECTED_PRE = {
    "cloudflare_dns_record.argocd_tailscale",
    "cloudflare_dns_record.cristexhub_dev",
    "cloudflare_dns_record.keycloak",
    "cloudflare_zero_trust_tunnel_cloudflared.keycloak",
    "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak",
}
EXPECTED_POST = EXPECTED_PRE | {"cloudflare_dns_record.reactive_resume_dev_tailscale"}


class OpenTofuFoundationStateReconciliationContractTests(unittest.TestCase):
    def test_manifest_is_complete_hashed_and_mode_bound(self) -> None:
        lines = MANIFEST.read_text().splitlines()
        self.assertEqual(10, len(lines))
        paths: list[str] = []
        for line in lines:
            digest, path = line.split("  ", 1)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            self.assertNotIn("..", Path(path).parts)
            self.assertNotIn("/", path[0])
            file_path = TOFU / path
            self.assertTrue(file_path.is_file(), path)
            self.assertFalse(file_path.is_symlink(), path)
            expected_mode = 0o755 if path.startswith("bin/") else 0o644
            self.assertEqual(expected_mode, stat.S_IMODE(file_path.stat().st_mode), path)
            if path == "bin/reconcile-foundation-state":
                text = file_path.read_text()
                text = re.sub(
                    r"source_manifest_expected_sha256='[0-9a-f]{64}'",
                    "source_manifest_expected_sha256='__SOURCE_MANIFEST_SHA256__'",
                    text,
                )
                text = re.sub(
                    r"source_reconcile_expected_canonical_sha256='[0-9a-f]{64}'",
                    "source_reconcile_expected_canonical_sha256='__SOURCE_RECONCILE_SHA256__'",
                    text,
                )
                actual = hashlib.sha256(text.encode()).hexdigest()
            else:
                actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
            self.assertEqual(digest, actual, path)
            paths.append(path)
        self.assertEqual(
            sorted(
                {
                    ".terraform.lock.hcl",
                    "README.md",
                    "backend.tf",
                    "bin/reconcile-foundation-state",
                    "bin/validate-foundation-state-scope",
                    "cloudflare.tf",
                    "outputs.tf",
                    "providers.tf",
                    "variables.tf",
                    "versions.tf",
                }
            ),
            sorted(paths),
        )

    def test_entrypoint_is_direct_dash_and_exactly_scoped(self) -> None:
        text = RECONCILE.read_text()
        for required in (
            "usage: opentofu/bin/reconcile-foundation-state check|import",
            'readlink -f "/proc/$$/exe")" = /usr/bin/dash',
            "Refusing traced shell execution",
            "TF_CLI_ARGS_*",
            "TF_VAR_*",
            "CLOUDFLARE_API_TOKEN",
            "/var/lib/opentofu/cristexweb/foundation.tfstate",
            "/opt/opentofu/1.12.5/tofu",
            "cloudflare_dns_record.reactive_resume_dev_tailscale",
            "validate-foundation-state-scope",
            "state show -state=\"$state_file\" cloudflare_dns_record.reactive_resume_dev_tailscale",
            "expected_pre_addresses=5",
            "expected_post_addresses=6",
            "configure-opentofu-state-backup",
            'run_backup_gate test',
            'run_backup_gate restore',
            "IMPORT EXISTING reactive_resume_dev_tailscale DNS",
            "TF_CLI_CONFIG_FILE=/dev/null",
            "TF_WORKSPACE=default",
            "TOFU_DISABLE_CHECKPOINT=1",
            "CLOUDFLARE_API_TOKEN",
            "anonymous pipe",
            "prod_plan=separate",
            "token_output=false",
            "root_expected_files",
            "root_actual_files",
            "-printf '%y %f\\n'",
            "d bin",
            "d github",
            "d .terraform",
            "Refusing extra or non-regular OpenTofu root .tf, .tf.json, auto-var, override, or directory entry.",
        ):
            self.assertIn(required, text)
        for forbidden in (
            "tofu apply",
            "tofu destroy",
            "state rm",
            "state push",
            "--auto-approve",
            "-target=",
        ):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("$1", text.split("usage=", 1)[-1].split("case", 1)[0])

    def test_scope_validator_accepts_only_pre_and_post_closures(self) -> None:
        self.assertEqual(0o755, stat.S_IMODE(SCOPE.stat().st_mode))
        pre = sorted(EXPECTED_PRE)
        post = sorted(EXPECTED_POST)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pre_path = root / "pre"
            post_path = root / "post"
            pre_path.write_text("\n".join(pre) + "\n")
            post_path.write_text("\n".join(post) + "\n")
            pre_path.chmod(0o600)
            post_path.chmod(0o600)
            for phase, path, expected in (("pre", pre_path, 5), ("post", post_path, 6)):
                result = subprocess.run(
                    ["/usr/bin/python3", str(SCOPE), phase, str(path)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn(f"state_scope=accepted phase={phase} addresses={expected}", result.stdout)
            (root / "foreign").write_text("\n".join(pre + ["cloudflare_dns_record.cristexhub_prod"]) + "\n")
            (root / "foreign").chmod(0o600)
            result = subprocess.run(
                ["/usr/bin/python3", str(SCOPE), "post", str(root / "foreign")],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("state_scope=refused reason=state_address_closure", result.stdout)
            resource_path = root / "resource"
            resource_path.write_text(
                'resource "cloudflare_dns_record" "reactive_resume_dev_tailscale" {\n'
                '  name = "resume-dev.cristex-soft.com"\n'
                '  type = "A"\n'
                '  content = "100.122.139.32"\n'
                '  proxied = false\n'
                '  ttl = 300\n}\n'
            )
            resource_path.chmod(0o600)
            result = subprocess.run(
                ["/usr/bin/python3", str(SCOPE), "resource", "reactive_resume_dev_tailscale", str(resource_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("state_scope=accepted phase=resource", result.stdout)

    def test_source_only_docs_and_boundaries(self) -> None:
        docs = RUNBOOK.read_text()
        for required in (
            "source-only",
            "direct, non-passthrough `/usr/bin/dash`",
            "exact six-address closure",
            "immutable encrypted readback",
            "isolated non-mutating restore",
            "IMPORT EXISTING reactive_resume_dev_tailscale DNS",
            "anonymous pipe",
            "mode-`0600`",
            "PROD plan",
            "No provider command, state import, state write, backup, restore, or PROD plan",
            "source_closure_sha256",
            "address_scope=exact-five",
            "address_scope=exact-six",
        ):
            self.assertIn(required, docs)
        readme = (TOFU / "README.md").read_text()
        self.assertIn("source defines seven resource addresses", readme)
        self.assertIn("reactive_resume_dev_tailscale", readme)
        self.assertIn("exact six-address state closure", readme)

    def test_shell_and_python_syntax(self) -> None:
        shell = subprocess.run(["/bin/sh", "-n", str(RECONCILE)], check=False, capture_output=True, text=True)
        self.assertEqual(0, shell.returncode, shell.stderr)
        python = subprocess.run(["/usr/bin/python3", "-m", "py_compile", str(SCOPE)], check=False, capture_output=True, text=True)
        self.assertEqual(0, python.returncode, python.stderr)


if __name__ == "__main__":
    unittest.main()
