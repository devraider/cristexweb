import hashlib
import stat
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ansible/files/policies/reactive-resume-dev-tls-renewal.yml"
COMPONENT = ROOT / "ansible/files/components/reactive-resume-dev-tls"
RENEW = COMPONENT / "renewal/reactive-resume-dev-tls-renew"
VALIDATOR = COMPONENT / "renewal/validate-reactive-resume-dev-tls-material"
SERVICE = COMPONENT / "renewal/cristexweb-reactive-resume-dev-tls-renew.service"
TIMER = COMPONENT / "renewal/cristexweb-reactive-resume-dev-tls-renew.timer"
WRAPPER = ROOT / "ansible/bin/configure-reactive-resume-dev-tls-renewal"
PLAYBOOK = ROOT / "ansible/playbooks/configure_reactive_resume_dev_tls_renewal.yml"
ROLE = ROOT / "ansible/roles/reactive_resume_dev_tls_renewal/tasks/main.yml"
DEFAULTS = ROOT / "ansible/roles/reactive_resume_dev_tls_renewal/defaults/main.yml"
RUNBOOK = ROOT / "runbooks/reactive-resume-dev-tls-renewal.md"


class ReactiveResumeDevTlsRenewalContractTests(unittest.TestCase):
    def test_exact_policy_and_custody(self) -> None:
        p = yaml.safe_load(POLICY.read_text())
        self.assertEqual("resume-dev.cristex-soft.com", p["hostname"])
        self.assertEqual(["resume-dev.cristex-soft.com"], p["certificate"]["exact_san_set"])
        self.assertEqual(
            "_acme-challenge.resume-dev.cristex-soft.com",
            p["certificate"]["exact_challenge_name"],
        )
        self.assertEqual("~/.config/cristexweb/cloudflare-argo-dns-token", p["cloudflare"]["token_file"])
        self.assertEqual("paul:paul:0600", p["cloudflare"]["token_file_contract"])
        self.assertEqual("/reactive-resume/dev/tls", p["infisical"]["path"])
        self.assertEqual({"TLS_CRT", "TLS_KEY"}, set(p["infisical"]["keys"]))
        self.assertEqual("unavailable", p["infisical"]["rollback_cas"])
        self.assertIn("fail_closed_without_rollback", p["infisical"]["mismatch_recovery"])
        self.assertIn("no_automatic_rollback_without_infisical_cas", p["safety"]["rollback"])
        self.assertEqual("reactive-resume-dev-tls", p["kubernetes"]["target_secret"])
        self.assertTrue(p["safety"]["no_value_output"])
        self.assertTrue(p["certificate"]["endpoint_preflight"]["exact_hostname_check"])
        self.assertTrue(p["certificate"]["endpoint_preflight"]["exact_san_set_check"])
        self.assertTrue(p["certificate"]["endpoint_preflight"]["system_trust_store_check"])
        self.assertEqual("https://api.cloudflare.com/client/v4/user/tokens/verify", p["cloudflare"]["token_validation"]["verify_endpoint"])
        self.assertEqual("cristex-soft.com", p["cloudflare"]["token_validation"]["exact_zone_name"])
        self.assertEqual("yaml_key_set_and_byte_equality_verified", p["infisical"]["readback"])
        self.assertEqual("persistent_lineage_keep_until_expiring_without_renew_by_default", p["safety"]["certbot_issuance"])
        self.assertEqual("4.0.0-2+deb13u1", p["safety"]["dependency_provenance"]["certbot_package"])
        self.assertEqual("4.0.0-1", p["safety"]["dependency_provenance"]["dns_cloudflare_package"])
        self.assertEqual("0.43.121", p["safety"]["dependency_provenance"]["infisical_cli"])

    def test_controller_is_guarded_and_value_free(self) -> None:
        text = RENEW.read_text()
        for required in (
            "cloudflare_token_file=/home/paul/.config/cristexweb/cloudflare-argo-dns-token",
            "challenge_name=_acme-challenge.resume-dev.cristex-soft.com",
            "infisical_path=/reactive-resume/dev/tls",
            "--dns-cloudflare",
            "--dns-cloudflare-credentials",
            "--domains \"$hostname\"",
            "--keep-until-expiring",
            "-verify_return_error",
            "-verify_hostname \"$hostname\"",
            "-CAfile \"$system_ca\"",
            "current_san=",
            "token-verify.json",
            "type=TXT&name=$challenge_name",
            "challenge_record_preexisting",
            "scope-probe.json",
            "cloudflare_dns_write_scope",
            "cleanup_challenge_records",
            "record_owned_challenge_ids",
            "challenge_cleanup_armed=1",
            "upload_readback=verified",
            "infisical_prewrite",
            "infisical_concurrent_change",
            "Infisical's documented CLI exposes no CAS/If-Match operation",
            "rollback_owned_infisical_state",
            "wait_for_runtime_convergence",
            "infisical_sync_interval_seconds=3600",
            "convergence_grace_seconds=900",
            "convergence_timeout_seconds=$((infisical_sync_interval_seconds + convergence_grace_seconds))",
            "convergence_command_timeout_seconds=30",
            "convergence_attempts=$(( (convergence_timeout_seconds + convergence_interval_seconds - 1) / convergence_interval_seconds ))",
            "convergence_deadline",
            "run_convergence_command",
            "wait_for_convergence_interval",
            "no_cas_fail_closed",
            "verify_infisical_key_set",
            "infisical-rollback-current-keys",
            "LastReconcileStatus",
            "convergence=verified",
            "kubeconfig=/etc/rancher/k3s/k3s.yaml",
            "PATH=/home/paul/.nvm/versions/node/v24.19.0/bin",
            "infisical_keys_expected",
            '"$infisical" export --env "$environment"',
            "--format yaml --silent",
            "infisical_readback_mismatch",
            "chmod 0600 \"$credentials\"",
            "values_output=false",
            "private_residue=none",
            "infisical_rotation_armed=1",
            "stage=infisical_rollback",
            "infisical-rollback-readback.yaml",
            "remaining_threshold_seconds",
        ):
            self.assertIn(required, text)
        for forbidden in (
            "tls.crt:",
            "tls.key:",
            "printf '%s' \"$token\"",
            "--renew-by-default",
            "INFISICAL_TOKEN=",
            "INFISICAL_SERVICE_TOKEN=",
        ):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("CLOUDFLARE_DNS_API_TOKEN=", text)
        self.assertNotIn('secrets set --env "$environment" --projectId "$project_id" \\\n    --path "$infisical_path" --file "$infisical_before"', text)
        self.assertNotIn('sleep "$convergence_interval_seconds"', text)
        self.assertIn('/usr/bin/timeout "$command_timeout" "$@"', text)

    def test_validator_and_systemd_units_are_hardened(self) -> None:
        self.assertEqual(0o755, stat.S_IMODE(RENEW.stat().st_mode))
        self.assertEqual(0o755, stat.S_IMODE(VALIDATOR.stat().st_mode))
        validator = VALIDATOR.read_text()
        self.assertIn("-checkend 2592000", validator)
        self.assertIn("exact single-host SAN set", validator)
        service = SERVICE.read_text()
        for required in (
            "User=paul",
            "Group=paul",
            "Environment=HOME=/home/paul",
            "Environment=PATH=/home/paul/.nvm/versions/node/v24.19.0/bin:/usr/local/bin:/usr/bin:/bin",
            "SupplementaryGroups=k3s-admin",
            "UMask=0077",
            "NoNewPrivileges=true",
            "PrivateTmp=true",
            "ProtectSystem=strict",
            "ProtectHome=read-only",
            "ReadWritePaths=/var/lib/cristexweb/reactive-resume-dev-tls /run/lock",
            "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
            "TimeoutStartSec=2h",
        ):
            self.assertIn(required, service)
        timer = TIMER.read_text()
        for required in ("OnCalendar=*-*-* 03:45:00", "RandomizedDelaySec=15m", "Persistent=true"):
            self.assertIn(required, timer)
        wrapper = WRAPPER.read_text()
        for required in ("check|apply|enable-check|enable-apply", "refusing passthrough", "--check", "ENTRYPOINT=v1"):
            self.assertIn(required, wrapper)

    def test_role_is_separate_install_and_enable_boundary(self) -> None:
        text = ROLE.read_text()
        for required in (
            "reactive_resume_dev_tls_renewal_mode in ['install', 'enable']",
            "Install exact renewal dependencies",
            'certbot={{ reactive_resume_dev_tls_renewal_certbot_package_version }}',
            'python3-certbot-dns-cloudflare={{ reactive_resume_dev_tls_renewal_dns_cloudflare_package_version }}',
            "'certbot' in ansible_facts.packages",
            "'python3-certbot-dns-cloudflare' in ansible_facts.packages",
            "reactive_resume_dev_tls_renewal_certbot_package_version",
            "reactive_resume_dev_tls_renewal_dns_cloudflare_package_version",
            "reactive_resume_dev_tls_renewal_infisical_cli_version",
            "reactive_resume_dev_tls_renewal_infisical_cli_sha256",
            "checksum_algorithm: sha256",
            "stat.mode == '0755'",
            "Verify pinned Certbot CLI provenance",
            "Verify pinned Infisical CLI provenance",
            "mode == '0600'",
            "Keep renewal timer disabled during install mode",
            "Enable and start the guarded renewal timer",
            "not ansible_check_mode",
            "Inspect the hash-bound renewal source closure on the controller",
            "reactive_resume_dev_tls_renewal_manifest_sha256",
            "reactive_resume_dev_tls_renewal_source_hashes",
            "reactive_resume_dev_tls_renewal_execution_source_hashes",
            "item.stat.mode == item.item.mode",
            "item.stat.pw_name == 'paul'",
            "normalized execution closure sources",
            "normalized_digest_name",
            "reactive_resume_dev_tls_renewal_defaults_self_hash",
            "regex_replace(",

        ):
            self.assertIn(required, text)
        self.assertIn("role: reactive_resume_dev_tls_renewal", PLAYBOOK.read_text())
        defaults = DEFAULTS.read_text()
        self.assertIn(
            f"reactive_resume_dev_tls_renewal_manifest_sha256: "
            f"{hashlib.sha256((COMPONENT / 'MANIFESTS.sha256').read_bytes()).hexdigest()}",
            defaults,
        )
        self.assertIn("reactive_resume_dev_tls_renewal_defaults_self_hash:", defaults)
        self.assertIn("normalized_digest_name: reactive_resume_dev_tls_renewal_defaults_self_hash", defaults)
        self.assertIn("v24.19.0/lib/node_modules/@infisical/cli/bin/infisical", defaults)
        self.assertIn("reactive_resume_dev_tls_renewal_infisical_cli", defaults)
        self.assertIn("reactive_resume_dev_tls_renewal_manifest_path", defaults)
        self.assertIn("reactive_resume_dev_tls_renewal_source_hashes", defaults)
        self.assertIn("4.0.0-2+deb13u1", defaults)
        self.assertIn("4.0.0-1", defaults)
        self.assertIn("0.43.121", defaults)
        self.assertIn("21e24f040a09196fb1214873ef964ac74655b172575a78fd95e6c9f2ab1c8940", defaults)

    def test_manifest_hashes_and_runbook(self) -> None:
        manifest = (COMPONENT / "MANIFESTS.sha256").read_text().splitlines()
        files = [COMPONENT / line.split("  ", 1)[1] for line in manifest]
        self.assertEqual(5, len(files))
        for line, path in zip(manifest, files):
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), line.split()[0])
        runbook = RUNBOOK.read_text()
        for required in (
            "DNS-01",
            "_acme-challenge.resume-dev.cristex-soft.com",
            "prod:/reactive-resume/dev/tls",
            "exact SAN",
            "enable-apply",
            "python3-certbot-dns-cloudflare",
            "v24.19.0/lib/node_modules/@infisical/cli/bin/infisical",
            "Direct `kubectl` Secret writes are forbidden",
            "system trust store",
            "--renew-by-default",
            "exact two-key",
            "byte readback",
            "pinned Debian packages",
            "explicitly lists the exact name",
            "DNS write/delete scope probe",
            "Infisical has no CAS/If-Match",
            "pre-write export",
            "unattended rollback",
            "unavoidable race",
            "no_cas_fail_closed",
            "exact two-key set",
            "all exact-name record IDs",
            "runtime convergence",
            "refreshInterval: 1h",
            "instantUpdates: false",
            "15-minute safety margin",
            "canonical wrapper, playbook, role task file, and role defaults",
        ):
            self.assertIn(required, runbook)
        self.assertNotIn("*.cristex-soft.com", runbook)


if __name__ == "__main__":
    unittest.main()
