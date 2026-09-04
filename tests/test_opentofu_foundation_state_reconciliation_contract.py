from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOFU = ROOT / "opentofu"
BIN = TOFU / "bin"
RECONCILE = BIN / "reconcile-foundation-state"
SCOPE = BIN / "validate-foundation-state-scope"
MANIFEST = BIN / "SOURCE.sha256"
RUNBOOK = ROOT / "runbooks/opentofu-foundation-state-reconciliation.md"
PRE = [
    "cloudflare_dns_record.argocd_tailscale",
    "cloudflare_dns_record.cristexhub_dev",
    "cloudflare_dns_record.keycloak",
    "cloudflare_zero_trust_tunnel_cloudflared.keycloak",
    "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak",
]
POST = PRE + ["cloudflare_dns_record.reactive_resume_dev_tailscale"]
CONFIG = POST + ["cloudflare_dns_record.cristexhub_prod"]
PROVIDER = "registry.opentofu.org/cloudflare/cloudflare"
TUNNEL_ID = "f9442440-96df-4cf1-855b-7257868ed9bc"
ACCOUNT_ID = "8b0f511214c7a4a52ddfb62ca92c5e80"
ZONE_ID = "3cbee16e56d7656440f93e685807e779"
DNS_IDS = {
    "cloudflare_dns_record.argocd_tailscale": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1",
    "cloudflare_dns_record.cristexhub_dev": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb2",
    "cloudflare_dns_record.keycloak": "ccccccccccccccccccccccccccccccc3",
    "cloudflare_dns_record.reactive_resume_dev_tailscale": "ddddddddddddddddddddddddddddddd4",
}
OUTPUTS = {
    "dns_record_name": "auth.cristex-soft.com",
    "public_hostname": "auth.cristex-soft.com",
    "token_handoff": "MANUAL_INFISICAL_HANDOFF_REQUIRED",
    "tunnel_id": TUNNEL_ID,
    "tunnel_name": "cristexhub-keycloak",
}


def _write_identity(path: Path, *, record_ids: dict[str, str] | None = None) -> Path:
    identity_path = path.with_name(path.name + ".identity.json")
    identity_path.write_text(
        json.dumps(
            {
                "schema": 1,
                "scope": "cloudflare-foundation-import-reactive-resume-dev-tailscale",
                "account_id": ACCOUNT_ID,
                "zone_id": ZONE_ID,
                "tunnel_id": TUNNEL_ID,
                "tunnel_account_tag": ACCOUNT_ID,
                "dns_record_ids": record_ids or DNS_IDS,
            },
            separators=(",", ":"),
        )
    )
    identity_path.chmod(0o600)
    return identity_path


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the validator with sanitized provenance and identity sidecars."""
    command = list(args)
    if len(command) == 2 and command[0] == "plan":
        plan_path = Path(command[1])
        receipt = plan_path.with_name(plan_path.name + ".provenance.json")
        try:
            info = plan_path.stat(follow_symlinks=False)
            is_regular = stat.S_ISREG(info.st_mode)
        except OSError:
            is_regular = False
        if is_regular and stat.S_IMODE(info.st_mode) == 0o600:
            digest = hashlib.sha256(plan_path.read_bytes()).hexdigest()
        else:
            # Plan input is validated before provenance; this placeholder keeps
            # FIFO/symlink tests on the intended input-boundary path.
            digest = "0" * 64
        receipt.write_text(
            json.dumps(
                {
                    "artifact": "refresh-only-plan-json",
                    "artifact_sha256": digest,
                    "tofu_path": "/opt/opentofu/1.12.5/tofu",
                    "tofu_sha256": "36dae7ca1e4f1552a6faef27179dc16ef403203e956f31416c17b3d87a38c3f4",
                    "tofu_version": "1.12.5",
                    "provider": "cloudflare",
                    "provider_version": "5.23.0",
                    "source": "pinned-cli-show-json",
                },
                separators=(",", ":"),
            )
        )
        receipt.chmod(0o600)
        command.append(str(receipt))
        command.append(str(_write_identity(plan_path)))
    elif len(command) == 3 and command[:2] == ["state", "post"]:
        state_path = Path(command[2])
        identity_path = _write_identity(state_path)
        command = ["state", "post", str(identity_path), str(state_path)]
    return subprocess.run(
        ["/usr/bin/python3", str(SCOPE), *command],
        check=False,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )


def state_document(addresses: list[str]) -> dict[str, Any]:
    resources = []
    for address in addresses:
        resource_type, name = address.split(".", 1)
        values: dict[str, Any] = {}
        sensitive_values: dict[str, Any] = {}
        if address == "cloudflare_zero_trust_tunnel_cloudflared.keycloak":
            values = {
                "id": TUNNEL_ID,
                "account_id": ACCOUNT_ID,
                "account_tag": ACCOUNT_ID,
                "tunnel_secret": None,
            }
            sensitive_values = {"connections": [], "tunnel_secret": True}
        if address == "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak":
            values = {
                "account_id": ACCOUNT_ID,
                "tunnel_id": TUNNEL_ID,
                "config": {
                    "origin_request": None,
                    "ingress": [
                        {
                            "hostname": "auth.cristex-soft.com",
                            "origin_request": None,
                            "path": None,
                            "service": "http://traefik.kube-system.svc.cluster.local:80",
                        },
                        {
                            "hostname": "dev-hub.cristex-soft.com",
                            "origin_request": None,
                            "path": None,
                            "service": "http://traefik.kube-system.svc.cluster.local:80",
                        },
                        {
                            "hostname": None,
                            "origin_request": None,
                            "path": None,
                            "service": "http_status:404",
                        },
                    ],
                },
            }
            sensitive_values = {"config": {"ingress": [{}, {}, {}]}}
        if address == "cloudflare_dns_record.argocd_tailscale":
            values = {"id": DNS_IDS[address], "zone_id": ZONE_ID}
            sensitive_values = {"tags": []}
        if address in {
            "cloudflare_dns_record.cristexhub_dev",
            "cloudflare_dns_record.keycloak",
        }:
            values = {
                "id": DNS_IDS[address],
                "zone_id": ZONE_ID,
                "type": "CNAME",
            }
            sensitive_values = {"settings": {}, "tags": []}
        if address == "cloudflare_dns_record.reactive_resume_dev_tailscale":
            sensitive_values = {"tags": []}
            values = {
                "id": DNS_IDS[address],
                "zone_id": ZONE_ID,
                "name": "resume-dev.cristex-soft.com",
                "type": "A",
                "content": "100.122.139.32",
                "ttl": 300,
                "proxied": False,
                "comment": "Managed by OpenTofu; private Reactive Resume DEV endpoint on Tailscale",
            }
        resources.append(
            {
                "address": address,
                "mode": "managed",
                "type": resource_type,
                "name": name,
                "provider_name": PROVIDER,
                "schema_version": 0,
                "values": values,
                "sensitive_values": sensitive_values,
            }
        )
    return {
        "format_version": "1.0",
        "terraform_version": "1.12.5",
        "checks": [],
        "values": {
            "outputs": {
                name: {"value": value, "type": "string", "sensitive": False}
                for name, value in OUTPUTS.items()
            },
            "root_module": {"resources": resources},
        },
    }


def plan_document() -> dict[str, Any]:
    return json.loads(
        (ROOT / "tests/fixtures/opentofu-1.12.5-refresh-only-noop.json").read_text()
    )


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, separators=(",", ":")))
    path.chmod(0o600)


class OpenTofuFoundationStateReconciliationContractTests(unittest.TestCase):
    def test_manifest_is_exactly_ten_files_and_hash_bound(self) -> None:
        lines = MANIFEST.read_text().splitlines()
        self.assertEqual(12, len(lines))
        paths: list[str] = []
        for line in lines:
            digest, path = line.split("  ", 1)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            self.assertFalse(Path(path).is_absolute())
            self.assertNotIn("..", Path(path).parts)
            file_path = TOFU / path
            self.assertTrue(file_path.is_file(), path)
            self.assertFalse(file_path.is_symlink(), path)
            expected_mode = (
                0o755
                if path.startswith("bin/") and path != "bin/SOURCE.sha256"
                else 0o644
            )
            self.assertEqual(
                expected_mode, stat.S_IMODE(file_path.stat().st_mode), path
            )
            if path in {"bin/reconcile-foundation-state", "bin/plan-foundation-prod-route"}:
                text = file_path.read_text()
                text = re.sub(
                    r"source_manifest_expected_sha256='[0-9a-f]{64}'",
                    "source_manifest_expected_sha256='__SOURCE_MANIFEST_SHA256__'",
                    text,
                )
                if path == "bin/reconcile-foundation-state":
                    text = re.sub(
                        r"source_reconcile_expected_canonical_sha256='[0-9a-f]{64}'",
                        "source_reconcile_expected_canonical_sha256='__SOURCE_RECONCILE_SHA256__'",
                        text,
                    )
                else:
                    text = re.sub(
                        r"source_prod_expected_canonical_sha256='[0-9a-f]{64}'",
                        "source_prod_expected_canonical_sha256='__SOURCE_PROD_SHA256__'",
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
                    "bin/plan-foundation-prod-route",
                    "bin/reconcile-foundation-state",
                    "bin/validate-foundation-prod-plan",
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
        reconcile_text = RECONCILE.read_text()
        manifest_pin = re.search(
            r"source_manifest_expected_sha256='([0-9a-f]{64})'", reconcile_text
        )
        canonical_pin = re.search(
            r"source_reconcile_expected_canonical_sha256='([0-9a-f]{64})'",
            reconcile_text,
        )
        self.assertIsNotNone(manifest_pin)
        self.assertIsNotNone(canonical_pin)
        self.assertEqual(
            manifest_pin.group(1), hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
        )
        canonical = re.sub(
            r"^source_manifest_expected_sha256='[0-9a-f]{64}'$",
            "source_manifest_expected_sha256='__SOURCE_MANIFEST_SHA256__'",
            reconcile_text,
            flags=re.MULTILINE,
        )
        canonical = re.sub(
            r"^source_reconcile_expected_canonical_sha256='[0-9a-f]{64}'$",
            "source_reconcile_expected_canonical_sha256='__SOURCE_RECONCILE_SHA256__'",
            canonical,
            flags=re.MULTILINE,
        )
        self.assertEqual(
            canonical_pin.group(1), hashlib.sha256(canonical.encode()).hexdigest()
        )

    def test_validator_manifest_and_embedded_pins_are_independently_equal(self) -> None:
        manifest = {
            path: digest
            for digest, path in (
                line.split("  ", 1) for line in MANIFEST.read_text().splitlines()
            )
        }
        expected = {
            "validate-foundation-prod-plan": "bin/validate-foundation-prod-plan",
            "validate-foundation-state-scope": "bin/validate-foundation-state-scope",
        }
        actual = {
            name: hashlib.sha256((BIN / name).read_bytes()).hexdigest()
            for name in expected
        }
        for name, path in expected.items():
            self.assertEqual(actual[name], manifest[path], path)

        plan_text = (BIN / "plan-foundation-prod-route").read_text()
        reconcile_text = RECONCILE.read_text()
        plan_prod_pin = re.search(
            r"^validator_sha256='([0-9a-f]{64})'$", plan_text, re.MULTILINE
        )
        plan_scope_pin = re.search(
            r"^state_scope_validator_sha256='([0-9a-f]{64})'$",
            plan_text,
            re.MULTILINE,
        )
        reconcile_scope_pin = re.search(
            r"^validator_sha256='([0-9a-f]{64})'$",
            reconcile_text,
            re.MULTILINE,
        )
        self.assertIsNotNone(plan_prod_pin)
        self.assertIsNotNone(plan_scope_pin)
        self.assertIsNotNone(reconcile_scope_pin)
        self.assertEqual(plan_prod_pin.group(1), actual["validate-foundation-prod-plan"])
        self.assertEqual(plan_scope_pin.group(1), actual["validate-foundation-state-scope"])
        self.assertEqual(
            reconcile_scope_pin.group(1), actual["validate-foundation-state-scope"]
        )

    def test_backup_gate_hashes_match_current_source_files(self) -> None:
        text = RECONCILE.read_text()
        source_checks = {
            "backup_wrapper": ROOT / "ansible/bin/configure-opentofu-state-backup",
            "backup_playbook": ROOT
            / "ansible/playbooks/configure_opentofu_state_backup.yml",
            "backup_source/opentofu-state-backup": ROOT
            / "ansible/files/backup/opentofu-state-backup",
            "backup_source/restore-opentofu-state-rehearsal": ROOT
            / "ansible/files/backup/restore-opentofu-state-rehearsal",
            "backup_source/cristexweb-opentofu-state-backup.service": ROOT
            / "ansible/files/backup/cristexweb-opentofu-state-backup.service",
            "backup_source/cristexweb-opentofu-state-backup.timer": ROOT
            / "ansible/files/backup/cristexweb-opentofu-state-backup.timer",
        }
        for shell_path, source_path in source_checks.items():
            pattern = rf'sha256sum "\${re.escape(shell_path)}".*?= \'([0-9a-f]{{64}})\''
            match = re.search(pattern, text)
            self.assertIsNotNone(match, shell_path)
            self.assertEqual(
                hashlib.sha256(source_path.read_bytes()).hexdigest(),
                match.group(1),
                shell_path,
            )

    def test_entrypoint_has_clean_pinned_boundary_and_split_proofs(self) -> None:
        text = RECONCILE.read_text()
        for required in (
            "usage: opentofu/bin/reconcile-foundation-state check|import",
            'readlink -f "/proc/$$/exe")" = /usr/bin/dash',
            "Refusing traced shell execution",
            "TF_CLI_ARGS_*",
            "TF_VAR_*",
            "TF_PLUGIN_CACHE_DIR|",
            "TF_*|",
            "TOFU_*|",
            "OPENTOFU_*|",
            "LD_*|",
            "DYLD_*|",
            "os.O_NONBLOCK",
            "CLOUDFLARE_API_TOKEN",
            "/var/lib/opentofu/cristexweb/foundation.tfstate",
            "/opt/opentofu/1.12.5/tofu",
            "36dae7ca1e4f1552a6faef27179dc16ef403203e956f31416c17b3d87a38c3f4",
            "state_parent_links",
            "-ge 2",
            "state_identity",
            "protected_tunnel_id=f9442440-96df-4cf1-855b-7257868ed9bc",
            "validate-foundation-state-scope",
            'show -json -no-color "$state_file"',
            "validate_state_json",
            "validate_plan_contract",
            "plan -refresh-only -input=false -lock=true",
            "TOFU_DISABLE_CHECKPOINT=1",
            "TF_CLI_CONFIG_FILE=/dev/null",
            "TF_WORKSPACE=default",
            'TF_DATA_DIR="$work/tofu-data"',
            "PYTHONNOUSERSITE=1",
            "PYTHONDONTWRITEBYTECODE=1",
            "O_NOFOLLOW",
            "anonymous pipe",
            "expected_pre_addresses=5",
            "expected_post_addresses=6",
            "IMPORT EXISTING reactive_resume_dev_tailscale DNS",
            "run_backup_gate test",
            "run_backup_gate restore",
            "prod_plan=separate",
        ):
            self.assertIn(required, text)
        for forbidden in (
            "tofu apply",
            "tofu destroy",
            "state rm",
            "state push",
            "--auto-approve",
            "-target=",
            "state show -state=",
        ):
            self.assertNotIn(forbidden, text)

    def test_exact_address_list_and_descriptor_input_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for phase, addresses, count in (("pre", PRE, 5), ("post", POST, 6)):
                path = root / phase
                path.write_text("\n".join(addresses) + "\n")
                path.chmod(0o600)
                accepted = run_validator(phase, str(path))
                self.assertEqual(
                    0, accepted.returncode, accepted.stdout + accepted.stderr
                )
                self.assertIn(f"addresses={count}", accepted.stdout)
            duplicate = root / "duplicate"
            duplicate.write_text("\n".join(PRE + [PRE[0]]) + "\n")
            duplicate.chmod(0o600)
            refused = run_validator("pre", str(duplicate))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("state_address_duplicates_or_empty", refused.stdout)
            link = root / "link"
            link.symlink_to(root / "pre")
            refused = run_validator("pre", str(link))
            self.assertNotEqual(0, refused.returncode)
            hard = root / "hard"
            os.link(root / "pre", hard)
            refused = run_validator("pre", str(hard))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("input_permissions", refused.stdout)

    def test_state_json_requires_exact_closure_import_and_safe_nested_markers(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for phase, addresses, count in (("pre", PRE, 5), ("post", POST, 6)):
                path = root / f"{phase}.json"
                write_json(path, state_document(addresses))
                accepted = run_validator("state", phase, str(path))
                self.assertEqual(
                    0, accepted.returncode, accepted.stdout + accepted.stderr
                )
                self.assertIn(f"phase={phase}-json addresses={count}", accepted.stdout)
            bad = state_document(POST)
            bad.pop("checks")
            path = root / "missing-checks.json"
            write_json(path, bad)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("state_json_top_level", refused.stdout)
            bad = state_document(POST)
            bad["checks"] = [{"status": "pass"}]
            path = root / "bad.json"
            write_json(path, bad)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("state_checks", refused.stdout)
            bad = state_document(POST)
            bad["values"]["outputs"]["tunnel_id"]["value"] = "0" * 32
            write_json(path, bad)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("state_tunnel_uuid", refused.stdout)
            bad = state_document(POST)
            bad["values"]["root_module"]["resources"][0]["sensitive_values"] = {
                "evil": True
            }
            write_json(path, bad)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("sensitive_values_nonempty", refused.stdout)
            bad = state_document(POST)
            tunnel = next(
                r
                for r in bad["values"]["root_module"]["resources"]
                if r["address"] == "cloudflare_zero_trust_tunnel_cloudflared.keycloak"
            )
            tunnel["values"]["tunnel_secret"] = "PLAINTEXT"
            write_json(path, bad)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("tunnel_secret_plaintext", refused.stdout)
            variants = (
                ("apiToken", None),
                ("api-key", None),
                ("clientSecret", None),
            )
            for key, value in variants:
                bad = state_document(POST)
                bad["values"]["root_module"]["resources"][0]["values"][key] = value
                write_json(path, bad)
                refused = run_validator("state", "post", str(path))
                self.assertNotEqual(0, refused.returncode)
                self.assertIn(f"{key}_field", refused.stdout)
            bad = state_document(POST)
            bad["values"]["root_module"]["resources"][0]["values"]["metadata"] = {
                "nested-token": None
            }
            write_json(path, bad)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("nested-token_field", refused.stdout)
            bad = state_document(POST)
            tunnel = next(
                r
                for r in bad["values"]["root_module"]["resources"]
                if r["address"] == "cloudflare_zero_trust_tunnel_cloudflared.keycloak"
            )
            tunnel["values"]["nested"] = {"tunnel_secret": None}
            write_json(path, bad)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("tunnel_secret_field", refused.stdout)
            bad = state_document(POST)
            bad["values"]["root_module"]["resources"][0]["values"]["nested_resource"] = {
                "address": "cloudflare_zero_trust_tunnel_cloudflared.keycloak",
                "values": {"tunnel_secret": None},
                "sensitive_values": {"tunnel_secret": True},
            }
            write_json(path, bad)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            # The nested object is not one of the canonical direct resource
            # projections, so its tunnel-secret field is rejected before any
            # sensitive-values exception could apply.
            self.assertIn("tunnel_secret_field", refused.stdout)

    def test_plan_requires_exact_real_refresh_envelope_and_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "plan.json"
            plan = plan_document()
            write_json(path, plan)
            accepted = run_validator("plan", str(path))
            self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)
            self.assertIn("configuration=7 variables=5", accepted.stdout)
            # The fixture is a sanitized OpenTofu 1.12.5 plan projection, not a
            # hand-evaluated substitute: references and provider metadata must
            # retain the representation emitted by ``tofu show -json``.
            configuration = plan["configuration"]
            self.assertEqual(
                "5.23.0",
                configuration["provider_config"]["cloudflare"]["version_constraint"],
            )
            self.assertEqual(
                {"resources", "outputs", "variables"},
                set(configuration["root_module"]),
            )
            tunnel_config = next(
                resource
                for resource in configuration["root_module"]["resources"]
                if resource["address"]
                == "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak"
            )
            self.assertEqual(
                [
                    "var.public_hostname",
                    "var.traefik_origin_service",
                    "var.traefik_origin_service",
                    "var.traefik_origin_service",
                ],
                tunnel_config["expressions"]["config"]["references"],
            )
            self.assertEqual(
                ["var.public_hostname"],
                configuration["root_module"]["outputs"]["public_hostname"][
                    "expression"
                ]["references"],
            )
            mutations = [
                (
                    "missing variables",
                    lambda p: p.pop("variables"),
                    "plan_required_fields",
                ),
                (
                    "missing configuration",
                    lambda p: p.pop("configuration"),
                    "plan_required_fields",
                ),
                (
                    "nonempty root",
                    lambda p: p["planned_values"]["root_module"].update(resources=[]),
                    "plan_planned_values_root_module",
                ),
                (
                    "foreign resource",
                    lambda p: p["configuration"]["root_module"][
                        "resources"
                    ].__setitem__(
                        0,
                        {
                            **p["configuration"]["root_module"]["resources"][0],
                            "address": "foreign.x",
                        },
                    ),
                    "config_resource_identity",
                ),
                (
                    "extra variable",
                    lambda p: p["variables"].update(evil={"value": "x"}),
                    "plan_variables_closure",
                ),
                (
                    "resource drift",
                    lambda p: p.update(resource_drift=[{"address": "foreign.x"}]),
                    "plan_resource_drift",
                ),
                (
                    "checks",
                    lambda p: p.update(checks=[{"status": "pass"}]),
                    "plan_checks",
                ),
                (
                    "sensitive output",
                    lambda p: p["output_changes"]["tunnel_name"].update(
                        after_sensitive=True
                    ),
                    "plan_output_after_sensitive",
                ),
                (
                    "unbound tunnel output change",
                    lambda p: p["output_changes"]["tunnel_id"].update(
                        before="87654321-4321-4321-4321-987654321abc",
                        after="87654321-4321-4321-4321-987654321abc",
                    ),
                    "plan_output_surface_binding",
                ),
            ]
            for _, mutate, reason in mutations:
                candidate = plan_document()
                mutate(candidate)
                write_json(path, candidate)
                refused = run_validator("plan", str(path))
                self.assertNotEqual(0, refused.returncode, reason)
                self.assertIn(reason, refused.stdout, refused.stdout)

    def test_descriptor_input_survives_path_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "state.json"
            write_json(original, state_document(POST))
            identity_path = _write_identity(original)
            identity_fd = os.open(identity_path, os.O_RDONLY)
            fd = os.open(original, os.O_RDONLY)
            os.unlink(original)
            original.write_text("{}")
            original.chmod(0o600)
            try:
                result = subprocess.run(
                    [
                        "/usr/bin/python3",
                        str(SCOPE),
                        "state",
                        "post",
                        f"fd:{identity_fd}",
                        f"fd:{fd}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    pass_fds=(identity_fd, fd),
                    env={
                        "PATH": "/usr/bin:/bin",
                        "PYTHONNOUSERSITE": "1",
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                )
            finally:
                os.close(identity_fd)
                os.close(fd)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("phase=post-json addresses=6", result.stdout)

    def test_capture_and_validator_boundaries_are_revalidated_after_production(self) -> None:
        source = RECONCILE.read_text()
        for helper, failure_stage in (
            ("run_capture", "stage=tofu_command"),
            ("run_capture_with_token", "stage=provider_command"),
            ("run_plan_capture_with_token", "stage=provider_plan_or_show"),
        ):
            start = source.index(f"{helper}() {{")
            next_start = source.find("\n}", start) + 2
            body = source[start:next_start]
            self.assertIn(failure_stage, body)
            self.assertIn(
                "revalidate_source_closure\n    revalidate_state_metadata\n    revalidate_state_content\n}",
                body,
            )
        self.assertIn("immutable_validator_runner_code", source)
        self.assertIn("os.memfd_create", source)
        self.assertIn("F_SEAL_WRITE", source)
        self.assertIn("validator_sha256", source)
        self.assertNotIn('/usr/bin/python3 "$validator"', source)
        self.assertNotIn("/usr/bin/python3 /proc/self/fd/5", source)
        self.assertNotIn('exec 6<&- 2>/dev/null', source)
        self.assertNotIn('exec 7<&- 2>/dev/null', source)
        # Each validator branch re-attests the source immediately before and
        # after invoking Python; this is separate from the post-capture check.
        self.assertGreaterEqual(
            source.count("revalidate_source_closure\n        revalidate_state_metadata"),
            3,
        )

    def test_validator_descriptor_rejects_path_swap_without_executing_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            validator = root / "validator.py"
            replacement = root / "replacement.py"
            output = root / "output.txt"
            validator.write_text("print('trusted')\n")
            replacement.write_text("print('evil')\n")
            harness = root / "pin-validator.sh"
            harness.write_text(
                """#!/bin/sh
set -eu
validator=$1
replacement=$2
output=$3
exec 5<"$validator"
fd_identity=$(/usr/bin/stat -Lc '%d:%i' /proc/self/fd/5)
/bin/mv -- "$replacement" "$validator"
path_identity=$(/usr/bin/stat -Lc '%d:%i' "$validator")
[ "$fd_identity" = "$path_identity" ] || exit 78
/usr/bin/env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
    /usr/bin/python3 /proc/self/fd/5 >"$output"
"""
            )
            harness.chmod(0o755)
            result = subprocess.run(
                [str(harness), str(validator), str(replacement), str(output)],
                check=False,
                capture_output=True,
                text=True,
                env={
                    "PATH": "/usr/bin:/bin",
                    "PYTHONNOUSERSITE": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )
            self.assertEqual(78, result.returncode)
            self.assertFalse(output.exists())
            self.assertEqual("print('evil')\n", validator.read_text())

    def test_plan_provenance_is_required_and_digest_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_path = root / "plan.json"
            write_json(plan_path, plan_document())
            missing = subprocess.run(
                ["/usr/bin/python3", str(SCOPE), "plan", str(plan_path)],
                check=False,
                capture_output=True,
                text=True,
                env={
                    "PATH": "/usr/bin:/bin",
                    "PYTHONNOUSERSITE": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )
            self.assertNotEqual(0, missing.returncode)
            self.assertIn("usage", missing.stdout)
            receipt = root / "receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "artifact": "refresh-only-plan-json",
                        "artifact_sha256": "0" * 64,
                        "tofu_path": "/opt/opentofu/1.12.5/tofu",
                        "tofu_sha256": "36dae7ca1e4f1552a6faef27179dc16ef403203e956f31416c17b3d87a38c3f4",
                        "tofu_version": "1.12.5",
                        "provider": "cloudflare",
                        "provider_version": "5.23.0",
                        "source": "pinned-cli-show-json",
                    },
                    separators=(",", ":"),
                )
            )
            receipt.chmod(0o600)
            identity_path = _write_identity(plan_path)
            refused = subprocess.run(
                [
                    "/usr/bin/python3",
                    str(SCOPE),
                    "plan",
                    str(plan_path),
                    str(receipt),
                    str(identity_path),
                ],
                check=False,
                capture_output=True,
                text=True,
                env={
                    "PATH": "/usr/bin:/bin",
                    "PYTHONNOUSERSITE": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("plan_provenance_digest_mismatch", refused.stdout)

    def test_reconciler_binds_capture_descriptors_and_denies_plugin_cache(self) -> None:
        text = RECONCILE.read_text()
        for required in (
            "TF_PLUGIN_CACHE_DIR|",
            "os.O_EXCL",
            "os.O_NOFOLLOW",
            "capture_identity",
            "capture inode replacement",
            "fd:8",
            "run_plan_capture_with_token",
            "--SHOW-COMMAND--",
            "plan_provenance",
            "-out=/proc/self/fd/",
        ):
            self.assertIn(required, text)
        self.assertNotIn("new_capture", text)
        self.assertNotIn('>"$work/init.stdout"', text)
        self.assertNotIn('>"$work/import.stdout"', text)

    def test_check_initializes_ephemeral_tofu_data_before_state_validation(self) -> None:
        # Keep a real command-level fixture here rather than relying only on a
        # textual assertion: a fresh TF_DATA_DIR must be initialized before the
        # first state consumer can succeed.  The production wrappers are then
        # checked for that same ordering and exact clean init command.
        for wrapper, state_validation_call in (
            (RECONCILE, "validate_scope pre"),
            (TOFU / "bin/plan-foundation-prod-route", "validate_state_scope pre"),
        ):
            source = wrapper.read_text()
            self.assertEqual(1, source.count("run_quiet_init\n"), wrapper.name)
            self.assertLess(
                source.index("run_quiet_init\n"),
                source.index(state_validation_call),
                wrapper.name,
            )
            quiet_start = source.index("run_quiet_init() {")
            quiet_end = source.index("\n}\nrun_capture", quiet_start) + 2
            quiet_body = source[quiet_start:quiet_end]
            self.assertIn("init -reconfigure -input=false -lockfile=readonly -no-color", quiet_body)
            self.assertIn(">/dev/null 2>/dev/null", quiet_body)
            self.assertNotIn("safe_runner_code", quiet_body)
            self.assertNotIn("preexec_fn=apply_output_limit", quiet_body)
            self.assertIn("TF_DATA_DIR=\"$work/tofu-data\"", quiet_body, wrapper.name)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake_tofu = root / "fake-tofu"
            fake_tofu.write_text(
                "#!/bin/sh\n"
                "set -eu\n"
                "case \" $* \" in\n"
                "  *' init '* )\n"
                "    test -n \"${TF_DATA_DIR-}\"\n"
                "    mkdir -p \"$TF_DATA_DIR\"\n"
                "    : >\"$TF_DATA_DIR/.initialized\"\n"
                "    exit 0\n"
                "    ;;\n"
                "  *' state list '* )\n"
                "    test -f \"$TF_DATA_DIR/.initialized\"\n"
                "    printf '%s\\n' state-validation-reached\n"
                "    exit 0\n"
                "    ;;\n"
                "esac\n"
                "exit 64\n"
            )
            fake_tofu.chmod(0o755)
            harness = root / "check-fixture"
            harness.write_text(
                "#!/bin/sh\n"
                "set -eu\n"
                "work=$(mktemp -d)\n"
                "trap 'rm -rf -- \"$work\"' EXIT\n"
                "env -i HOME=/tmp PATH=/usr/bin:/bin TF_DATA_DIR=\"$work/tofu-data\" "
                "  /bin/sh \"$1\" -chdir=fixture init -reconfigure -input=false "
                "-lockfile=readonly -no-color\n"
                "env -i HOME=/tmp PATH=/usr/bin:/bin TF_DATA_DIR=\"$work/tofu-data\" "
                "  /bin/sh \"$1\" -chdir=fixture state list -state=fixture -no-color\n"
            )
            harness.chmod(0o755)
            result = subprocess.run(
                [str(harness), str(fake_tofu)],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
                env={"PATH": "/usr/bin:/bin"},
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("state-validation-reached", result.stdout)

    def test_quiet_init_allows_large_provider_temp_with_discarded_output(self) -> None:
        # A provider installer can briefly create a package larger than the
        # bounded capture limit. The dedicated init path must therefore avoid
        # the capture runner's RLIMIT_FSIZE while still discarding init output.
        for wrapper in (RECONCILE, TOFU / "bin/plan-foundation-prod-route"):
            source = wrapper.read_text()
            quiet_start = source.index("run_quiet_init() {")
            quiet_end = source.index("\n}\nrun_capture", quiet_start) + 2
            quiet_function = source[quiet_start:quiet_end]
            self.assertNotIn("RLIMIT_FSIZE", quiet_function, wrapper.name)
            self.assertNotIn("safe_runner_code", quiet_function, wrapper.name)
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                fake_tofu = root / "fake-tofu"
                fake_tofu.write_text(
                    "#!/bin/sh\n"
                    "set -eu\n"
                    "mkdir -p \"$TMPDIR\"\n"
                    "/usr/bin/dd if=/dev/zero of=\"$TMPDIR/terraform-provider-large\" "
                    "bs=1048576 count=17 status=none\n"
                    "/usr/bin/dd if=/dev/zero bs=1048576 count=17 status=none\n"
                    "/usr/bin/dd if=/dev/zero bs=1048576 count=17 status=none >&2\n"
                )
                fake_tofu.chmod(0o755)
                harness = root / "quiet-init-fixture"
                harness.write_text(
                    "#!/bin/sh\n"
                    "set -eu\n"
                    "work=$1\n"
                    "tofu=$2\n"
                    "root=$3\n"
                    "revalidate_source_closure() { :; }\n"
                    "revalidate_state_metadata() { :; }\n"
                    "revalidate_state_content() { :; }\n"
                    + quiet_function
                    + "\nrun_quiet_init\n"
                    + "test -s \"$work/tofu-tmp/terraform-provider-large\"\n"
                    + "test \"$(wc -c <\"$work/tofu-tmp/terraform-provider-large\")\" -gt 16777216\n"
                )
                harness.chmod(0o755)
                result = subprocess.run(
                    [str(harness), str(root), str(fake_tofu), str(root)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env={"PATH": "/usr/bin:/bin"},
                )
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual("", result.stdout)
                self.assertEqual("", result.stderr)

    def test_prod_plan_rejects_extra_bin_entries(self) -> None:
        text = (TOFU / "bin/plan-foundation-prod-route").read_text()
        for required in (
            "bin_expected_paths",
            "bin_actual_paths",
            "Refusing extra or non-regular OpenTofu bin entry.",
            "find \"$root/bin\" -mindepth 1 -maxdepth 1",
        ):
            self.assertIn(required, text)

    def test_plan_requires_full_surfaces_and_exact_configuration_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "plan.json"
            mutations = [
                (
                    "missing prior state",
                    lambda p: p.pop("prior_state"),
                    "plan_required_fields",
                ),
                (
                    "missing planned outputs",
                    lambda p: p["planned_values"].pop("outputs"),
                    "plan_planned_values_outputs",
                ),
                (
                    "missing output sensitivity",
                    lambda p: p["planned_values"]["outputs"]["tunnel_name"].pop(
                        "sensitive"
                    ),
                    "plan_planned_values_output_shape",
                ),
                (
                    "widened ingress",
                    lambda p: p["configuration"]["root_module"]["resources"][4][
                        "expressions"
                    ]["config"]["references"].append("var.evil"),
                    "config_resource_expression_semantics",
                ),
                (
                    "evaluated output expression",
                    lambda p: p["configuration"]["root_module"]["outputs"][
                        "public_hostname"
                    ].update(expression={"constant_value": "auth.cristex-soft.com"}),
                    "plan_configuration_output_semantics",
                ),
                (
                    "widened provider",
                    lambda p: p["configuration"]["provider_config"]["cloudflare"].update(
                        version_constraint="evil"
                    ),
                    "plan_provider_config_identity",
                ),
                (
                    "provisioner closure",
                    lambda p: p["configuration"]["root_module"]["resources"][0].update(
                        provisioners=[]
                    ),
                    "config_resource_fields",
                ),
                (
                    "arbitrary token field",
                    lambda p: p["prior_state"]["values"]["root_module"][
                        "resources"
                    ][0]["values"].update(token="must-not-pass"),
                    "token_field",
                ),
                (
                    "wrong pre-existing DNS identity",
                    lambda p: next(
                        resource
                        for resource in p["prior_state"]["values"]["root_module"][
                            "resources"
                        ]
                        if resource["address"] == "cloudflare_dns_record.keycloak"
                    )["values"].update(id="e" * 32),
                    "state_identity_record",
                ),
                (
                    "wrong refresh Tunnel ingress",
                    lambda p: next(
                        resource
                        for resource in p["prior_state"]["values"]["root_module"][
                            "resources"
                        ]
                        if resource["address"]
                        == "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak"
                    )["values"]["config"]["ingress"][0].update(
                        service="http://evil.example:80"
                    ),
                    "state_tunnel_ingress",
                ),
            ]
            for _, mutate, reason in mutations:
                candidate = plan_document()
                mutate(candidate)
                write_json(path, candidate)
                refused = run_validator("plan", str(path))
                self.assertNotEqual(0, refused.returncode, reason)
                self.assertIn(reason, refused.stdout, refused.stdout)

    def test_fifo_input_is_rejected_before_any_blocking_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fifo = Path(temp) / "input"
            os.mkfifo(fifo, 0o600)
            receipt = Path(temp) / "input.provenance.json"
            receipt.write_text("{}")
            receipt.chmod(0o600)
            identity = _write_identity(fifo)
            result = subprocess.run(
                [
                    "/usr/bin/python3",
                    str(SCOPE),
                    "plan",
                    str(fifo),
                    str(receipt),
                    str(identity),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
                env={
                    "PATH": "/usr/bin:/bin",
                    "PYTHONNOUSERSITE": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("input_permissions", result.stdout)

    def test_state_resource_values_are_exact_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            state = state_document(POST)
            argocd = next(
                item
                for item in state["values"]["root_module"]["resources"]
                if item["address"] == "cloudflare_dns_record.argocd_tailscale"
            )
            argocd["values"]["padding"] = "unexpected"
            write_json(path, state)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("state_dns_values", refused.stdout)

            state = state_document(POST)
            resume = next(
                item
                for item in state["values"]["root_module"]["resources"]
                if item["address"] == "cloudflare_dns_record.reactive_resume_dev_tailscale"
            )
            resume["values"]["ttl"] = True
            write_json(path, state)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("state_reactive_resume_value", refused.stdout)

            path.write_bytes(b"{}" + b"x" * (4 * 1024 * 1024))
            path.chmod(0o600)
            refused = run_validator("state", "post", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("input_too_large", refused.stdout)

    def test_plan_rejects_nonfinite_duplicate_and_wrong_marker_types(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "plan.json"
            plan = plan_document()
            path.write_text('{"format_version":NaN}')
            path.chmod(0o600)
            refused = run_validator("plan", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("json", refused.stdout)
            path.write_text('{"format_version":"1.2","format_version":"1.2"}')
            path.chmod(0o600)
            refused = run_validator("plan", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("json", refused.stdout)
            plan["output_changes"]["tunnel_name"]["before_unknown"] = {}
            write_json(path, plan)
            refused = run_validator("plan", str(path))
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("plan_output_before_unknown", refused.stdout)

    def test_state_identity_profile_binds_prompted_account_zone_and_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path = root / "state.json"
            identity_path = root / "identity.json"
            state = state_document(POST)
            imported = next(
                resource
                for resource in state["values"]["root_module"]["resources"]
                if resource["address"] == "cloudflare_dns_record.reactive_resume_dev_tailscale"
            )
            imported["values"].update(id="a" * 32, zone_id=ZONE_ID)
            identity = {
                "schema": 1,
                "scope": "cloudflare-foundation-import-reactive-resume-dev-tailscale",
                "account_id": ACCOUNT_ID,
                "zone_id": ZONE_ID,
                "tunnel_id": TUNNEL_ID,
                "tunnel_account_tag": ACCOUNT_ID,
                "dns_record_ids": {**DNS_IDS, "cloudflare_dns_record.reactive_resume_dev_tailscale": "a" * 32},
            }
            write_json(state_path, state)
            write_json(identity_path, identity)
            identity_fd = os.open(identity_path, os.O_RDONLY)
            state_fd = os.open(state_path, os.O_RDONLY)
            try:
                accepted = subprocess.run(
                    [
                        "/usr/bin/python3",
                        str(SCOPE),
                        "state",
                        "post",
                        f"fd:{identity_fd}",
                        f"fd:{state_fd}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    pass_fds=(identity_fd, state_fd),
                    env={
                        "PATH": "/usr/bin:/bin",
                        "PYTHONNOUSERSITE": "1",
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                )
            finally:
                os.close(identity_fd)
                os.close(state_fd)
            self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)
            identity["dns_record_ids"]["cloudflare_dns_record.reactive_resume_dev_tailscale"] = "b" * 32
            write_json(identity_path, identity)
            identity_fd = os.open(identity_path, os.O_RDONLY)
            state_fd = os.open(state_path, os.O_RDONLY)
            try:
                refused = subprocess.run(
                    [
                        "/usr/bin/python3",
                        str(SCOPE),
                        "state",
                        "post",
                        f"fd:{identity_fd}",
                        f"fd:{state_fd}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    pass_fds=(identity_fd, state_fd),
                    env={
                        "PATH": "/usr/bin:/bin",
                        "PYTHONNOUSERSITE": "1",
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                )
            finally:
                os.close(identity_fd)
                os.close(state_fd)
            self.assertNotEqual(0, refused.returncode)
            self.assertIn("state_identity_record", refused.stdout)

    def test_plan_and_provenance_are_consumed_from_verified_descriptors(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_path = root / "plan.json"
            receipt_path = root / "receipt.json"
            plan_bytes = json.dumps(plan_document(), separators=(",", ":")).encode()
            plan_path.write_bytes(plan_bytes)
            plan_path.chmod(0o600)
            receipt_path.write_text(
                json.dumps(
                    {
                        "artifact": "refresh-only-plan-json",
                        "artifact_sha256": hashlib.sha256(plan_bytes).hexdigest(),
                        "tofu_path": "/opt/opentofu/1.12.5/tofu",
                        "tofu_sha256": "36dae7ca1e4f1552a6faef27179dc16ef403203e956f31416c17b3d87a38c3f4",
                        "tofu_version": "1.12.5",
                        "provider": "cloudflare",
                        "provider_version": "5.23.0",
                        "source": "pinned-cli-show-json",
                    },
                    separators=(",", ":"),
                )
            )
            receipt_path.chmod(0o600)
            identity_path = _write_identity(plan_path)
            plan_fd = os.open(plan_path, os.O_RDONLY)
            receipt_fd = os.open(receipt_path, os.O_RDONLY)
            identity_fd = os.open(identity_path, os.O_RDONLY)
            try:
                result = subprocess.run(
                    [
                        "/usr/bin/python3",
                        str(SCOPE),
                        "plan",
                        f"fd:{plan_fd}",
                        f"fd:{receipt_fd}",
                        f"fd:{identity_fd}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    pass_fds=(plan_fd, receipt_fd, identity_fd),
                    env={
                        "PATH": "/usr/bin:/bin",
                        "PYTHONNOUSERSITE": "1",
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                )
            finally:
                os.close(plan_fd)
                os.close(receipt_fd)
                os.close(identity_fd)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_state_dns_ids_and_tunnel_ingress_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            for mutation, reason in (
                (
                    lambda state: next(
                        resource
                        for resource in state["values"]["root_module"]["resources"]
                        if resource["address"] == "cloudflare_dns_record.argocd_tailscale"
                    )["values"].update(id="e" * 32),
                    "state_identity_record",
                ),
                (
                    lambda state: next(
                        resource
                        for resource in state["values"]["root_module"]["resources"]
                        if resource["address"]
                        == "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak"
                    )["values"]["config"]["ingress"][0].update(
                        hostname="evil.example"
                    ),
                    "state_tunnel_ingress",
                ),
                (
                    lambda state: next(
                        resource
                        for resource in state["values"]["root_module"]["resources"]
                        if resource["address"]
                        == "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak"
                    )["values"]["config"]["ingress"][0].update(
                        service="http://evil.example:80"
                    ),
                    "state_tunnel_ingress",
                ),
                (
                    lambda state: next(
                        resource
                        for resource in state["values"]["root_module"]["resources"]
                        if resource["address"]
                        == "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak"
                    )["values"]["config"]["ingress"][0].update(
                        origin_request={}
                    ),
                    "state_tunnel_ingress",
                ),
            ):
                candidate = state_document(POST)
                mutation(candidate)
                write_json(path, candidate)
                refused = run_validator("state", "post", str(path))
                self.assertNotEqual(0, refused.returncode)
                self.assertIn(reason, refused.stdout)

    def test_state_tunnel_identity_is_fixed_and_cross_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            mutations = []
            state = state_document(POST)
            tunnel = next(
                resource
                for resource in state["values"]["root_module"]["resources"]
                if resource["address"] == "cloudflare_zero_trust_tunnel_cloudflared.keycloak"
            )
            tunnel["values"]["id"] = "00000000-0000-0000-0000-000000000000"
            mutations.append(("tunnel UUID", state))
            state = state_document(POST)
            tunnel = next(
                resource
                for resource in state["values"]["root_module"]["resources"]
                if resource["address"] == "cloudflare_zero_trust_tunnel_cloudflared.keycloak"
            )
            tunnel["values"]["account_tag"] = "f" * 32
            mutations.append(("tunnel account tag", state))
            state = state_document(POST)
            config = next(
                resource
                for resource in state["values"]["root_module"]["resources"]
                if resource["address"] == "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak"
            )
            config["values"]["tunnel_id"] = "00000000-0000-0000-0000-000000000000"
            mutations.append(("tunnel config UUID", state))
            state = state_document(POST)
            state["values"]["outputs"]["tunnel_id"]["value"] = "00000000-0000-0000-0000-000000000000"
            mutations.append(("state output UUID", state))
            for label, candidate in mutations:
                write_json(path, candidate)
                refused = run_validator("state", "post", str(path))
                self.assertNotEqual(0, refused.returncode, label)

    def test_refresh_plan_tunnel_identity_is_cross_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "plan.json"
            for mutation in (
                lambda plan: next(
                    resource
                    for resource in plan["prior_state"]["values"]["root_module"]["resources"]
                    if resource["address"] == "cloudflare_zero_trust_tunnel_cloudflared.keycloak"
                )["values"].update(account_tag="f" * 32),
                lambda plan: next(
                    resource
                    for resource in plan["prior_state"]["values"]["root_module"]["resources"]
                    if resource["address"] == "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak"
                )["values"].update(tunnel_id="00000000-0000-0000-0000-000000000000"),
                lambda plan: plan["output_changes"]["tunnel_id"].update(
                    before="00000000-0000-0000-0000-000000000000",
                    after="00000000-0000-0000-0000-000000000000",
                ),
            ):
                candidate = plan_document()
                mutation(candidate)
                write_json(path, candidate)
                refused = run_validator("plan", str(path))
                self.assertNotEqual(0, refused.returncode)

    def test_verified_validator_runner_rejects_path_swap_in_place_edit_and_hardlink(
        self,
    ) -> None:
        for wrapper in (
            TOFU / "bin/plan-foundation-prod-route",
            RECONCILE,
        ):
            match = re.search(
                r"immutable_validator_runner_code='\n(.*?)\n'\n",
                wrapper.read_text(),
                flags=re.DOTALL,
            )
            self.assertIsNotNone(match, wrapper.name)
            runner = match.group(1)
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                trusted = root / "validator"
                replacement = root / "replacement"
                trusted.write_text("print('trusted')\n")
                replacement.write_text("print('evil')\n")
                trusted.chmod(0o755)
                replacement.chmod(0o755)
                digest = hashlib.sha256(trusted.read_bytes()).hexdigest()
                replacement.replace(trusted)
                swapped = subprocess.run(
                    ["/usr/bin/python3", "-c", runner, str(trusted), digest],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                )
                self.assertNotEqual(0, swapped.returncode)
                self.assertNotIn("evil", swapped.stdout)
                trusted.write_text(
                    "from pathlib import Path\n"
                    "import sys\n"
                    "Path(sys.argv[1]).write_text(\"print('evil')\\n\")\n"
                    "print('trusted')\n"
                )
                trusted.chmod(0o755)
                digest = hashlib.sha256(trusted.read_bytes()).hexdigest()
                mutated = subprocess.run(
                    ["/usr/bin/python3", "-c", runner, str(trusted), digest, str(trusted)],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                )
                self.assertEqual(0, mutated.returncode, mutated.stdout + mutated.stderr)
                self.assertEqual("trusted\n", mutated.stdout)
                self.assertEqual("print('evil')\n", trusted.read_text())
                trusted.write_text("print('trusted')\n")
                trusted.chmod(0o755)
                os.link(trusted, root / "hardlink")
                digest = hashlib.sha256(trusted.read_bytes()).hexdigest()
                hardlinked = subprocess.run(
                    ["/usr/bin/python3", "-c", runner, str(trusted), digest],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                )
                self.assertNotEqual(0, hardlinked.returncode)

    def test_embedded_runners_bound_source_and_capture_sizes(self) -> None:
        """Exercise the producer/source limits without any provider or state."""
        wrappers = (
            TOFU / "bin/plan-foundation-prod-route",
            RECONCILE,
        )
        for wrapper in wrappers:
            source = wrapper.read_text()
            source_match = re.search(
                r"immutable_validator_runner_code='\n(.*?)\n'\n",
                source,
                flags=re.DOTALL,
            )
            self.assertIsNotNone(source_match, wrapper.name)
            source_runner = source_match.group(1)
            source_limit = 256 * 1024
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                oversized = root / "oversized-validator"
                oversized.write_bytes(b"x" * (source_limit + 1))
                oversized.chmod(0o755)
                source_result = subprocess.run(
                    [
                        "/usr/bin/python3",
                        "-c",
                        source_runner,
                        str(oversized),
                        hashlib.sha256(oversized.read_bytes()).hexdigest(),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                )
                self.assertNotEqual(0, source_result.returncode)
                self.assertLessEqual(oversized.stat().st_size, source_limit + 1)

                safe_match = re.search(
                    r"safe_runner_code='\n(.*?)\n'\n",
                    source,
                    flags=re.DOTALL,
                )
                self.assertIsNotNone(safe_match, wrapper.name)
                capture_runner = safe_match.group(1)
                output = root / "stdout"
                error = root / "stderr"
                child = (
                    "import sys; "
                    "sys.stdout.write('x' * (16 * 1024 * 1024 + 1))"
                )
                capture_result = subprocess.run(
                    [
                        "/usr/bin/python3",
                        "-c",
                        capture_runner,
                        str(output),
                        str(error),
                        "/usr/bin/python3",
                        "-c",
                        child,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                )
                self.assertNotEqual(0, capture_result.returncode)
                self.assertLessEqual(output.stat().st_size, 16 * 1024 * 1024)
                self.assertLessEqual(error.stat().st_size, 16 * 1024 * 1024)

                plan_match = re.search(
                    r"safe_plan_runner_code='\n(.*?)\n'\n",
                    source,
                    flags=re.DOTALL,
                )
                self.assertIsNotNone(plan_match, wrapper.name)
                plan_runner = plan_match.group(1)
                plan_file = root / "binary-plan"
                plan_stdout = root / "plan-stdout"
                plan_json = root / "plan-json"
                plan_error = root / "plan-stderr"
                plan_child = (
                    "import sys; "
                    "sys.stdout.write('x' * (16 * 1024 * 1024 + 1))"
                )
                plan_result = subprocess.run(
                    [
                        "/usr/bin/python3",
                        "-c",
                        plan_runner,
                        str(plan_file),
                        str(plan_stdout),
                        str(plan_json),
                        str(plan_error),
                        "/usr/bin/python3",
                        "-c",
                        plan_child,
                        "--SHOW-COMMAND--",
                        "/usr/bin/python3",
                        "-c",
                        "pass",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                )
                self.assertNotEqual(0, plan_result.returncode)
                self.assertLessEqual(plan_stdout.stat().st_size, 16 * 1024 * 1024)
                self.assertLessEqual(plan_error.stat().st_size, 16 * 1024 * 1024)

            self.assertIn("MAX_SOURCE_BYTES = 256 * 1024", source)
            self.assertIn("source_info.st_size > MAX_SOURCE_BYTES", source)
            self.assertIn("MAX_CAPTURE_BYTES = 16 * 1024 * 1024", source)
            self.assertIn("resource.RLIMIT_FSIZE", source)
            self.assertIn("preexec_fn=apply_output_limit", source)
            self.assertIn("binary_plan", source)

    def test_failed_producers_revalidate_before_reporting_failure(self) -> None:
        for wrapper in (
            TOFU / "bin/plan-foundation-prod-route",
            RECONCILE,
        ):
            source = wrapper.read_text()
            expected_stages = (
                "tofu_command",
                "provider_command",
                "provider_plan_or_show",
            )
            self.assertGreaterEqual(source.count("producer_status=$?"), 3)
            for stage in expected_stages:
                self.assertIn(f"stage={stage}", source)
            self.assertIn(
                "revalidate_source_closure\n        revalidate_state_metadata\n        revalidate_state_content\n        printf",
                source,
            )

    def test_output_limit_signal_and_provider_override_guards_are_bound(self) -> None:
        for wrapper in (TOFU / "bin/plan-foundation-prod-route", RECONCILE):
            source = wrapper.read_text()
            self.assertIn("preexec_fn=apply_output_limit", source)
            self.assertIn("RLIMIT_FSIZE", source)
            self.assertIn("LD_*", source)
            self.assertIn("DYLD_*", source)
            self.assertIn("trap 'cleanup; exit 129' HUP", source)
            self.assertIn("trap 'cleanup; exit 130' INT", source)
            self.assertIn("trap 'cleanup; exit 143' TERM", source)
        validator = (BIN / "validate-foundation-prod-plan").read_text()
        self.assertIn(
            '"name", "full_name", "version_constraint"',
            validator,
        )
        self.assertIn("omits provider expressions entirely", validator)
        self.assertIn('set(state) != {"format_version", "terraform_version", "values", "checks"}', SCOPE.read_text())

    def test_signal_traps_cleanup_then_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "cleaned"
            script = (
                "set -eu; "
                f"cleanup() {{ /usr/bin/touch {marker}; }}; "
                "trap 'cleanup' EXIT; "
                "trap 'cleanup; exit 143' TERM; "
                "kill -TERM $$"
            )
            result = subprocess.run(
                ["/bin/dash", "-c", script],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(143, result.returncode)
            self.assertTrue(marker.exists())

    def test_shell_python_syntax_and_docs(self) -> None:
        shell = subprocess.run(
            ["/bin/sh", "-n", str(RECONCILE)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, shell.returncode, shell.stderr)
        python = subprocess.run(
            ["/usr/bin/python3", "-m", "py_compile", str(SCOPE)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, python.returncode, python.stderr)
        docs = RUNBOOK.read_text()
        for required in (
            "source-only",
            "exact five-address",
            "exact six-address",
            "protected state JSON proof",
            "refresh-only plan-envelope proof",
            "resource_changes",
            "planned_values.root_module",
            "five output",
            "exact seven-resource configuration closure",
            "exact five-variable closure",
            "O_NOFOLLOW",
            "immutable encrypted readback",
            "isolated non-mutating restore",
            "RLIMIT_FSIZE",
            "16 MiB",
            "256 KiB",
            "post-producer source/state revalidation",
            "PROD plan",
        ):
            self.assertIn(required, docs)


if __name__ == "__main__":
    unittest.main()
