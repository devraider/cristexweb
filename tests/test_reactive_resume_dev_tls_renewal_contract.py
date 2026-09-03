import hashlib
import importlib.util
import json
import re
import stat
import unittest
from pathlib import Path
from unittest import mock

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
STRATEGY = ROOT / "ansible/plugins/strategy/reactive_resume_dev_tls_renewal_guarded_linear.py"


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
        self.assertIn("delete_only_process_owned_ids", p["cloudflare"]["token_validation"]["dns_write_scope"])
        self.assertEqual("never_delete_unobserved_exact_name_records_fail_closed", p["cloudflare"]["token_validation"]["concurrent_record_policy"])
        self.assertEqual("exact_leaf_sha256_fingerprint_san_and_expiry", p["safety"]["served_certificate_convergence"])
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
            "certificate_fingerprint()",
            "certificate_san_set()",
            "certificate_expiry()",
            "validate_existing_certificate_pair()",
            "expected_certificate_fingerprint",
            "expected_certificate_san_set",
            "expected_certificate_expiry",
            "token-verify.json",
            "type=TXT&name=$challenge_name",
            "challenge_record_preexisting",
            "scope-probe.json",
            "cloudflare_dns_write_scope",
            "cleanup_challenge_records",
            "owned_challenge_ids",
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
        self.assertNotIn('record_owned_challenge_ids "$records"', text)
        self.assertNotIn('public_key_revision "$served_cert"', text)
        self.assertIn('validate_existing_certificate_pair "$infisical_before_cert" "$infisical_before_key"', text)
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
        service = (COMPONENT / "renewal/cristexweb-reactive-resume-dev-tls-renew.service").read_text()
        self.assertIn("Requires=k3s.service", service)
        self.assertIn("After=network-online.target k3s.service", service)
        renewal = (COMPONENT / "renewal/reactive-resume-dev-tls-renew").read_text()
        self.assertEqual(2, renewal.count("--connect-timeout 15 --max-time 60"))
        wrapper = WRAPPER.read_text()
        for required in (
            "check|apply|enable-check|enable-apply",
            "refusing passthrough",
            "--check",
            "ENTRYPOINT=v2",
            "wrapper_pid",
            "wrapper_starttime",
            "WRAPPER_PATH",
            "refusing traced shell execution",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_TOKEN",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_ATTESTATION_FILE",
            "wrapper_canonical_sha256_expected",
            "normalized_defaults_sha256",
        ):
            self.assertIn(required, wrapper)

    def test_strategy_rejects_selection_controls_before_task_iteration(self) -> None:
        self.assertEqual(0o644, stat.S_IMODE(STRATEGY.stat().st_mode))
        spec = importlib.util.spec_from_file_location("rr_tls_strategy", STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        strategy = module.StrategyModule.__new__(module.StrategyModule)
        with mock.patch.object(module.context, "CLIARGS", {"start_at_task": "mutation"}):
            with self.assertRaisesRegex(Exception, "TASK_SELECTION_GUARD"):
                strategy.run(None, None)
        empty_selection = {"start_at_task": "", "step": False, "tags": [], "skip_tags": []}
        with mock.patch.object(module.context, "CLIARGS", empty_selection):
            for argv in (
                ["ansible-playbook", "--start-at-task="],
                ["ansible-playbook", "--step="],
                ["ansible-playbook", "-t", "all"],
                ["ansible-playbook", "-t=all"],
                ["ansible-playbook", "-tall"],
                ["ansible-playbook", "--ta", "all"],
                ["ansible-playbook", "--tag=all"],
            ):
                with self.subTest(argv=argv):
                    with mock.patch.object(module.sys, "argv", argv):
                        with self.assertRaisesRegex(Exception, "TASK_SELECTION_GUARD"):
                            strategy.run(None, None)

    def test_strategy_binds_exact_wrapper_argv_and_runtime_inputs(self) -> None:
        spec = importlib.util.spec_from_file_location("rr_tls_strategy_argv", STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        payload = {
            "reactive_resume_dev_tls_renewal_approved": True,
            "reactive_resume_dev_tls_renewal_mode": "install",
            "reactive_resume_dev_tls_renewal_repository_root": str(module._REPOSITORY_ROOT),
        }
        argv = [
            str(module._CONTROLLER),
            "-i",
            str(module._INVENTORY_SOURCE),
            str(module._PLAYBOOK),
            "--diff",
            "--limit",
            "crtxweb",
            "--ask-become-pass",
            "--extra-vars",
            json.dumps(payload, separators=(",", ":")),
            "--check",
        ]
        with mock.patch.object(module.sys, "argv", argv):
            self.assertTrue(module._canonical_argv())
            tampered = list(argv)
            tampered[9] = json.dumps({**payload, "unexpected": True}, separators=(",", ":"))
            with mock.patch.object(module.sys, "argv", tampered):
                self.assertFalse(module._canonical_argv())
        cliargs = {
            "start_at_task": None,
            "step": False,
            "tags": [],
            "skip_tags": [],
            "subset": "crtxweb",
            "diff": True,
            "inventory": [str(module._INVENTORY_SOURCE)],
        }
        strategy = module.StrategyModule.__new__(module.StrategyModule)
        with (
            mock.patch.object(module.context, "CLIARGS", cliargs),
            mock.patch.object(module, "_runtime_contract", return_value=True),
            mock.patch.object(module, "_wrapper_binding_valid", return_value=True),
            mock.patch.object(module.LinearStrategyModule, "run", return_value="ok"),
            mock.patch.object(module.sys, "argv", argv),
        ):
            self.assertEqual("ok", strategy.run(None, None))

    def test_wrapper_binding_requires_ancestor_exact_argv_and_attestation(self) -> None:
        spec = importlib.util.spec_from_file_location("rr_tls_strategy_binding", STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        payload = {
            "reactive_resume_dev_tls_renewal_approved": True,
            "reactive_resume_dev_tls_renewal_mode": "install",
            "reactive_resume_dev_tls_renewal_repository_root": str(module._REPOSITORY_ROOT),
        }
        argv = [
            str(module._CONTROLLER),
            "-i",
            str(module._INVENTORY_SOURCE),
            str(module._PLAYBOOK),
            "--diff",
            "--limit",
            "crtxweb",
            "--ask-become-pass",
            "--extra-vars",
            json.dumps(payload, separators=(",", ":")),
            "--check",
        ]
        wrapper_sha = hashlib.sha256(WRAPPER.read_bytes()).hexdigest()
        wrapper_canonical_sha = module._canonical_file_hash(WRAPPER, "wrapper_canonical_sha256_expected")
        starttime = "123456"
        pid = "4242"
        token = "a" * 64
        with self.subTest("valid ancestor"):
            attestation = self._write_tls_attestation(
                f"{token}:{pid}:{starttime}:{WRAPPER}:{wrapper_sha}:check\n"
            )
            env = {
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_ENTRYPOINT": "v2",
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_TOKEN": token,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_ATTESTATION_FILE": str(attestation),
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_WRAPPER_PID": pid,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_WRAPPER_STARTTIME": starttime,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_WRAPPER_PATH": str(WRAPPER),
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_WRAPPER_SHA256": wrapper_sha,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_WRAPPER_CANONICAL_SHA256": wrapper_canonical_sha,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_CONTROLLER": str(module._CONTROLLER),
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_PYTHON": "/usr/bin/python3",
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_ANSIBLE_CONFIG": str(module._ANSIBLE_CONFIG),
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_TASK_SHA256": module._TASK_SHA256,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_PLAYBOOK_SHA256": module._PLAYBOOK_SHA256,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_SHA256": hashlib.sha256(STRATEGY.read_bytes()).hexdigest(),
            }
            with (
                mock.patch.dict(module.os.environ, env, clear=False),
                mock.patch.object(module.sys, "argv", argv),
                mock.patch.object(module, "_is_ancestor", return_value=True),
                mock.patch.object(module, "_proc_starttime", return_value=starttime),
                mock.patch.object(module, "_proc_cmdline", return_value=["/bin/dash", str(WRAPPER), "check"]),
                mock.patch.object(module.context, "CLIARGS", {"check": True}),
            ):
                self.assertTrue(module._wrapper_binding_valid())
            attestation.unlink()
        with self.subTest("forged direct process"):
            attestation = self._write_tls_attestation(
                f"{token}:{pid}:{starttime}:{WRAPPER}:{wrapper_sha}:check\n"
            )
            with (
                mock.patch.dict(module.os.environ, env, clear=False),
                mock.patch.object(module.sys, "argv", argv),
                mock.patch.object(module, "_is_ancestor", return_value=False),
                mock.patch.object(module, "_proc_starttime", return_value=starttime),
                mock.patch.object(module, "_proc_cmdline", return_value=["/bin/dash", str(WRAPPER), "check"]),
                mock.patch.object(module.context, "CLIARGS", {"check": True}),
            ):
                self.assertFalse(module._wrapper_binding_valid())
            attestation.unlink()

    @staticmethod
    def _write_tls_attestation(content: str) -> Path:
        import tempfile

        handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False)
        handle.write(content)
        handle.close()
        path = Path(handle.name)
        path.chmod(0o600)
        return path

    def test_hash_helpers_are_environment_isolated(self) -> None:
        wrapper = WRAPPER.read_text()
        self.assertIn("clean_python()", wrapper)
        self.assertIn("/usr/bin/env -i", wrapper)
        self.assertIn("PYTHONNOUSERSITE=1", wrapper)
        self.assertIn("PYTHONHASHSEED=0", wrapper)
        self.assertIn('"$python_tool" -I "$@"', wrapper)
        self.assertIn('clean_python - "$1" wrapper_canonical_sha256_expected', wrapper)
        self.assertIn('python_target=/usr/bin/python3.13', wrapper)
        self.assertEqual(2, wrapper.count("clean_python - \"$1\" <<'PY'"))

    def test_operational_defaults_are_immutable_and_nonempty(self) -> None:
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual("/var/lib/cristexweb/reactive-resume-dev-tls", defaults["reactive_resume_dev_tls_renewal_state_root"])
        self.assertEqual("/usr/local/libexec/cristexweb", defaults["reactive_resume_dev_tls_renewal_libexec_root"])
        self.assertEqual("/usr/bin/certbot", defaults["reactive_resume_dev_tls_renewal_certbot_path"])
        self.assertEqual("4.0.0-2+deb13u1", defaults["reactive_resume_dev_tls_renewal_certbot_package_version"])
        self.assertEqual("4.0.0-1", defaults["reactive_resume_dev_tls_renewal_dns_cloudflare_package_version"])
        self.assertEqual(
            "21e24f040a09196fb1214873ef964ac74655b172575a78fd95e6c9f2ab1c8940",
            defaults["reactive_resume_dev_tls_renewal_infisical_cli_sha256"],
        )
        self.assertEqual(4, len(defaults["reactive_resume_dev_tls_renewal_installed_file_contract"]))
        role = ROLE.read_text()
        self.assertIn("Require immutable TLS renewal operational defaults", role)
        for required in (
            "reactive_resume_dev_tls_renewal_state_root == '/var/lib/cristexweb/reactive-resume-dev-tls'",
            "reactive_resume_dev_tls_renewal_libexec_root == '/usr/local/libexec/cristexweb'",
            "reactive_resume_dev_tls_renewal_certbot_path == '/usr/bin/certbot'",
            "reactive_resume_dev_tls_renewal_installed_file_contract == [",
        ):
            self.assertIn(required, role)

    def test_playbook_and_role_pin_first_task_and_execution_inputs(self) -> None:
        playbook = PLAYBOOK.read_text()
        role = ROLE.read_text()
        self.assertIn("strategy: reactive_resume_dev_tls_renewal_guarded_linear", playbook)
        self.assertIn("Require strategy provenance attestation before any TLS task", role)
        self.assertIn("STRATEGY_ATTESTED", role)
        self.assertIn("Require the immutable TLS renewal source paths and manifest contract", role)
        self.assertIn("Reject externally supplied source marker variables", role)
        self.assertIn("Require the fixed wrapper-bound controller inputs", role)
        self.assertIn("CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_CONTROLLER_SHA256", role)
        self.assertIn("CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_INVENTORY_SHA256", role)
        self.assertIn("CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_ANSIBLE_CONFIG_SHA256", role)
        self.assertIn("reactive_resume_dev_tls_renewal_task_self_hash", role)
        self.assertIn("reactive_resume_dev_tls_renewal_defaults_raw_hash", role)
        self.assertIn("reactive_resume_dev_tls_renewal_guarded_linear.py", role)
        defaults = yaml.safe_load(DEFAULTS.read_text())
        execution = defaults["reactive_resume_dev_tls_renewal_execution_source_hashes"]
        self.assertEqual(hashlib.sha256(STRATEGY.read_bytes()).hexdigest(), execution[4]["sha256"])
        self.assertEqual(
            hashlib.sha256((ROOT / "ansible/ansible.cfg").read_bytes()).hexdigest(),
            execution[5]["sha256"],
        )
        wrapper = WRAPPER.read_text()
        self.assertIn('"$playbook"', wrapper)
        self.assertIn('exec /bin/dash "$script_path" "$@"', wrapper)
        self.assertIn('CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_WRAPPER_PID', wrapper)
        self.assertIn('CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_WRAPPER_STARTTIME', wrapper)
        self.assertIn('CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_WRAPPER_CANONICAL_SHA256', wrapper)
        self.assertIn('"/bin/dash", str(_WRAPPER_SOURCE), invocation', STRATEGY.read_text())
        self.assertIn('_STRATEGY_CANONICAL_SHA256', STRATEGY.read_text())
        self.assertNotIn('strategy_sha256 = hashlib.sha256(_STRATEGY.read_bytes())', STRATEGY.read_text())
        for digest_name in (
            "CONTROLLER_SHA256",
            "INVENTORY_SHA256",
            "ANSIBLE_CONFIG_SHA256",
            "STRATEGY_SHA256",
        ):
            self.assertIn(
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_" + digest_name,
                wrapper,
            )
        self.assertNotIn("--start-at-task", wrapper)

    def test_strategy_hashes_and_interpreter_are_fixed_before_task_iteration(self) -> None:
        spec = importlib.util.spec_from_file_location("rr_tls_strategy_hashes", STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(module._python_contract())
        self.assertEqual(module._TASK_SHA256, module._normalized_yaml_hash(module._TASK_SOURCE, task=True))
        self.assertEqual(module._DEFAULTS_SHA256, module._normalized_yaml_hash(module._DEFAULTS_SOURCE))
        self.assertTrue(module._source_closure_contract())
        with __import__('tempfile').TemporaryDirectory() as directory:
            altered = Path(directory) / 'tasks.yml'
            altered.write_text(module._TASK_SOURCE.read_text() + '\n# altered\n', encoding='utf-8')
            self.assertNotEqual(module._TASK_SHA256, module._normalized_yaml_hash(altered, task=True))

    def test_role_mutations_require_strategy_attestation(self) -> None:
        tasks = yaml.safe_load(ROLE.read_text())
        mutation_names = {
            'Install exact renewal dependencies',
            'Create protected renewal directories during install mode',
            'Install the value-free TLS validator during install mode',
            'Install the guarded renewal executable during install mode',
            'Install the renewal service unit during install mode',
            'Install the renewal timer unit during install mode',
            'Reload systemd after install-mode renewal unit changes',
            'Keep renewal timer disabled during install mode',
            'Enable and start the guarded renewal timer',
        }
        for task in tasks:
            if task.get('name') in mutation_names:
                when = task.get('when', [])
                when = when if isinstance(when, list) else [when]
                self.assertTrue(any('STRATEGY_ATTESTED' in str(condition) for condition in when), task['name'])

    def test_role_is_separate_install_and_enable_boundary(self) -> None:
        text = ROLE.read_text()
        tasks = yaml.safe_load(text)
        task_names = [task.get('name', '') for task in tasks]
        source_index = task_names.index('Inspect the hash-bound renewal source closure on the controller')
        apt_index = task_names.index('Install exact renewal dependencies')
        self.assertLess(source_index, apt_index)
        install_condition = "reactive_resume_dev_tls_renewal_mode == 'install'"
        for name in (
            'Create protected renewal directories during install mode',
            'Install the value-free TLS validator during install mode',
            'Install the guarded renewal executable during install mode',
            'Install the renewal service unit during install mode',
            'Install the renewal timer unit during install mode',
            'Reload systemd after install-mode renewal unit changes',
            'Keep renewal timer disabled during install mode',
        ):
            task = next(task for task in tasks if task.get('name') == name)
            when = task.get('when', [])
            when = when if isinstance(when, list) else [when]
            self.assertIn(install_condition, when)
        installed = next(task for task in tasks if task.get('name') == 'Inspect exact installed TLS renewal files for enable mode')
        self.assertEqual("reactive_resume_dev_tls_renewal_mode == 'enable'", installed['when'])
        enable = next(task for task in tasks if task.get('name') == 'Enable and start the guarded renewal timer')
        self.assertIn("reactive_resume_dev_tls_renewal_mode == 'enable'", enable['when'])
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
            "Require the single-use TLS renewal wrapper attestation",
            "Require the exact single-use TLS renewal wrapper attestation",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_MANIFEST_SHA256",
            "item.stat.mode == item.item.mode",
            "item.stat.pw_name == 'paul'",
            "normalized execution closure sources",
            "Require wrapper-bound renewal source digests",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_TASK_SHA256",
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
        for name in (
            'Inspect the pinned user-owned Infisical CLI as paul',
            'Verify pinned Infisical CLI provenance as paul',
        ):
            task = next(task for task in yaml.safe_load(text) if task.get('name') == name)
            self.assertFalse(task.get('become', True))
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
        wrapper = WRAPPER.read_text()
        wrapper_expected = re.search(
            r"(?m)^wrapper_canonical_sha256_expected='([0-9a-f]{64})'$", wrapper
        )
        self.assertIsNotNone(wrapper_expected)
        wrapper_normalized = re.sub(
            r"(?m)^wrapper_canonical_sha256_expected='[0-9a-f]{64}'$",
            "wrapper_canonical_sha256_expected='" + ("0" * 64) + "'",
            wrapper,
        )
        self.assertEqual(hashlib.sha256(wrapper_normalized.encode()).hexdigest(), wrapper_expected.group(1))
        defaults = DEFAULTS.read_text()
        defaults_normalized = re.sub(
            r"(?m)^reactive_resume_dev_tls_renewal_defaults_self_hash: [0-9a-f]{64}$",
            "reactive_resume_dev_tls_renewal_defaults_self_hash: __SELF_HASH__",
            defaults,
        )
        defaults_normalized = re.sub(
            r"(?m)^(    normalized_digest_name: reactive_resume_dev_tls_renewal_defaults_self_hash\n    sha256: )[0-9a-f]{64}$",
            r"\1__SELF_HASH__",
            defaults_normalized,
        )
        defaults_expected = re.search(
            r"(?m)^reactive_resume_dev_tls_renewal_defaults_self_hash: ([0-9a-f]{64})$",
            defaults,
        )
        self.assertIsNotNone(defaults_expected)
        defaults_normalized, strategy_count = re.subn(
            r"(?m)^(  - path: >-\n      .*reactive_resume_dev_tls_renewal_guarded_linear\.py\n    mode: '0644'\n    sha256: )[0-9a-f]{64}$",
            r"\1__STRATEGY_SHA256__",
            defaults_normalized,
        )
        self.assertEqual(1, strategy_count)
        self.assertEqual(hashlib.sha256(defaults_normalized.encode()).hexdigest(), defaults_expected.group(1))
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
            "complete controller-local source/hash preflight runs before any package or",
            "enable-check` and `enable-apply`\nnever install or repair",
            "already-installed exact file hashes",
            "exact two-key set",
            "process-owned ledger",
            "unknown record added concurrently remains untouched",
            "runtime convergence",
            "SHA-256 DER fingerprint",
            "refreshInterval: 1h",
            "instantUpdates: false",
            "15-minute safety margin",
            "single-use,",
            "direct playbook invocation",
            "externally supplied hash variables",
            "canonical wrapper, playbook, role task file, and role defaults",
        ):
            self.assertIn(required, runbook)
        self.assertNotIn("*.cristex-soft.com", runbook)


if __name__ == "__main__":
    unittest.main()
