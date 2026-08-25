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
        self.assertEqual("reactive-resume-dev-tls", p["kubernetes"]["target_secret"])
        self.assertTrue(p["safety"]["no_value_output"])

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
            "cleanup()",
            "chmod 0600 \"$credentials\"",
            "values_output=false",
            "private_residue=none",
        ):
            self.assertIn(required, text)
        for forbidden in ("kubectl", "tls.crt:", "tls.key:", "printf '%s' \"$token\""):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("CLOUDFLARE_DNS_API_TOKEN=", text)

    def test_validator_and_systemd_units_are_hardened(self) -> None:
        self.assertEqual(0o755, stat.S_IMODE(RENEW.stat().st_mode))
        self.assertEqual(0o755, stat.S_IMODE(VALIDATOR.stat().st_mode))
        service = SERVICE.read_text()
        for required in (
            "User=paul",
            "UMask=0077",
            "NoNewPrivileges=true",
            "PrivateTmp=true",
            "ProtectSystem=strict",
            "ProtectHome=read-only",
            "ReadWritePaths=/var/lib/cristexweb/reactive-resume-dev-tls /run/lock",
            "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
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
            "'certbot' in ansible_facts.packages",
            "'python3-certbot-dns-cloudflare' in ansible_facts.packages",
            "mode == '0600'",
            "Keep renewal timer disabled during install mode",
            "Enable and start the guarded renewal timer",
            "not ansible_check_mode",
        ):
            self.assertIn(required, text)
        self.assertIn("role: reactive_resume_dev_tls_renewal", PLAYBOOK.read_text())

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
            "Direct `kubectl` Secret writes are forbidden",
        ):
            self.assertIn(required, runbook)
        self.assertNotIn("*.cristex-soft.com", runbook)


if __name__ == "__main__":
    unittest.main()
