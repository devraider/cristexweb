import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
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
        self.assertEqual("dev-resume.cristex-soft.com", p["hostname"])
        self.assertEqual(["dev-resume.cristex-soft.com"], p["certificate"]["exact_san_set"])
        self.assertEqual(
            "_acme-challenge.dev-resume.cristex-soft.com",
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
            "challenge_name=_acme-challenge.dev-resume.cristex-soft.com",
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
            # ansible-core 2.19 exposes this as a tuple at runtime.
            "inventory": (str(module._INVENTORY_SOURCE),),
        }
        strategy = module.StrategyModule.__new__(module.StrategyModule)
        play = type(
            "Play",
            (),
            {
                "become": True,
                "become_method": "ansible.builtin.sudo",
                "become_user": "root",
                "become_exe": "sudo",
                "become_flags": "-H -S -n",
            },
        )()
        iterator = type("Iterator", (), {"_play": play})()
        with (
            mock.patch.object(module.context, "CLIARGS", cliargs),
            mock.patch.object(module, "_runtime_contract", return_value=True),
            mock.patch.object(module, "_wrapper_binding_valid", return_value=True),
            mock.patch.object(module, "_effective_play_definition_contract", return_value=True) as definition,
            mock.patch.object(module.LinearStrategyModule, "run", return_value="ok"),
            mock.patch.object(module.sys, "argv", argv),
        ):
            # The initial strategy PlayContext may carry no privilege fields in
            # ansible-core 2.19; the parsed iterator Play is authoritative.
            self.assertEqual("ok", strategy.run(iterator, None))
            definition.assert_called_once_with(None, None, play)

    def test_play_definition_binds_privilege_without_initial_play_context(self) -> None:
        module = self._strategy_module()

        class Host:
            name = "crtxweb"

        class Inventory:
            _sources = [str(module._INVENTORY_SOURCE)]

            def get_host(self, name):
                self_name = name
                if self_name != "crtxweb":
                    return None
                return Host()

        class VariableManager:
            def get_vars(self, *, play, host):
                return {
                    "ansible_connection": "local",
                    "ansible_host": None,
                    "ansible_user": "paul",
                    "ansible_python_interpreter": "/usr/bin/python3",
                }

        play = type(
            "Play",
            (),
            {
                "become": True,
                "become_method": "ansible.builtin.sudo",
                "become_user": "root",
                "become_exe": "sudo",
                "become_flags": "-H -S -n",
            },
        )()
        self.assertTrue(module._effective_play_definition_contract(VariableManager(), Inventory(), play))
        play.become_flags = "--evil"
        self.assertFalse(module._effective_play_definition_contract(VariableManager(), Inventory(), play))
        play.become_flags = "-H -S -n"
        play.become_exe = "/tmp/evil"
        self.assertFalse(module._effective_play_definition_contract(VariableManager(), Inventory(), play))
        play.become_exe = "sudo"
        play.become = None
        self.assertFalse(module._effective_play_definition_contract(VariableManager(), Inventory(), play))

    def test_effective_host_vars_use_ansible_219_variable_manager_lifecycle(self) -> None:
        spec = importlib.util.spec_from_file_location("rr_tls_strategy_lifecycle", STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class Host:
            name = "crtxweb"

        test_case = self

        class Inventory:
            _sources = [str(module._INVENTORY_SOURCE)]

            def get_host(self, name):
                test_case.assertEqual("crtxweb", name)
                return Host()

        class Play:
            remote_user = None
            become = True
            become_method = "sudo"
            become_user = None

        class VariableManager:
            def get_vars(self, *, play, host):
                test_case.assertIsInstance(play, Play)
                test_case.assertIsInstance(host, Host)
                return {
                    "ansible_connection": "local",
                    "ansible_host": None,
                    "ansible_user": "paul",
                    "ansible_python_interpreter": "/usr/bin/python3",
                    "ansible_playbook_python": str(module._REPOSITORY_ROOT / ".venv/bin/python"),
                    "ansible_inventory_sources": (str(module._INVENTORY_SOURCE),),
                }

        self.assertTrue(module._effective_host_vars_contract(VariableManager(), Inventory(), Play()))

        class ForgedVariableManager(VariableManager):
            def get_vars(self, *, play, host):
                values = super().get_vars(play=play, host=host)
                values["ansible_inventory_sources"] = ("/tmp/forged-inventory.yml",)
                return values

        self.assertFalse(module._effective_host_vars_contract(ForgedVariableManager(), Inventory(), Play()))

        class ForgedInventory(Inventory):
            _sources = ["/tmp/forged-inventory.yml"]

        self.assertFalse(module._effective_host_vars_contract(VariableManager(), ForgedInventory(), Play()))

    def test_real_ansible_219_variable_manager_and_inventory_lifecycle(self) -> None:
        from ansible.inventory.manager import InventoryManager
        from ansible.parsing.dataloader import DataLoader
        from ansible.playbook.play import Play
        from ansible.vars.manager import VariableManager

        module = self._strategy_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory_path = root / "inventory.local.yml"
            inventory_path.write_bytes(module._INVENTORY_BYTES)
            loader = DataLoader()
            inventory = InventoryManager(loader=loader, sources=[str(inventory_path)])
            variable_manager = VariableManager(loader=loader, inventory=inventory)
            play = Play().load(
                {
                    "name": "real lifecycle",
                    "hosts": "crtxweb",
                    "connection": "local",
                    "become": True,
                    "gather_facts": False,
                    "tasks": [],
                },
                variable_manager=variable_manager,
                loader=loader,
            )
            with mock.patch.object(module, "_INVENTORY_SOURCE", inventory_path):
                self.assertTrue(module._effective_host_vars_contract(variable_manager, inventory, play))
                self.assertEqual([str(inventory_path)], module._normalize_inventory_sources((str(inventory_path),)))
                self.assertEqual([str(inventory_path)], module._normalize_inventory_sources([str(inventory_path)]))
                self.assertEqual([str(inventory_path)], module._normalize_inventory_sources(str(inventory_path)))
                self.assertIsNone(module._normalize_inventory_sources((str(inventory_path), 7)))

    def test_real_role_lifecycle_rejects_direct_default_strategy_before_mutation(self) -> None:
        """Run the checked-in first action through ansible-core's real loader.

        This intentionally omits the guarded wrapper and strategy.  A direct
        role/playbook invocation must fail in the action plugin before the
        following sentinel task can run; this is not a mocked action call.
        """
        controller = Path("/home/paul/projects/cristexweb/.venv/bin/ansible-playbook")
        canonical_root = ROOT
        inventory_source = canonical_root / "ansible/.ansible/inventory.local.yml"
        if not controller.is_file() or not inventory_source.is_file():
            self.skipTest("canonical controller/inventory unavailable in offline worktree")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / "mutation-sentinel"
            playbook = root / "direct-role.yml"
            playbook.write_text(
                yaml.safe_dump(
                    [
                        {
                            "name": "reject direct TLS role",
                            "hosts": "crtxweb",
                            "gather_facts": False,
                            "connection": "local",
                            "become": True,
                            "become_method": "ansible.builtin.sudo",
                            "become_user": "root",
                            "become_exe": "sudo",
                            "become_flags": "-H -S -n",
                            "vars": {
                                "reactive_resume_dev_tls_renewal_approved": True,
                                "reactive_resume_dev_tls_renewal_mode": "install",
                                "reactive_resume_dev_tls_renewal_repository_root": str(canonical_root),
                            },
                            "tasks": [
                                {"ansible.builtin.include_role": {"name": "reactive_resume_dev_tls_renewal"}},
                                {"name": "must never run", "ansible.builtin.file": {"path": str(sentinel), "state": "touch"}},
                            ],
                        }
                    ],
                    sort_keys=False,
                    width=100000,
                ),
                encoding="utf-8",
            )
            env = {
                "HOME": "/home/paul",
                "USER": "paul",
                "LOGNAME": "paul",
                "PATH": str(controller.parent) + ":/usr/bin:/bin",
                "ANSIBLE_CONFIG": str(canonical_root / "ansible/ansible.cfg"),
                "ANSIBLE_ROLES_PATH": str(canonical_root / "ansible/roles"),
                "ANSIBLE_ACTION_PLUGINS": str(canonical_root / "ansible/plugins/action"),
                "ANSIBLE_LIBRARY": str(canonical_root / "ansible/library"),
                "ANSIBLE_NOCOLOR": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            result = subprocess.run(
                [str(controller), "-i", str(inventory_source), str(playbook), "--check"],
                cwd=canonical_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("ENTRYPOINT_GUARD", result.stdout + result.stderr)
            self.assertFalse(sentinel.exists())

    def test_real_default_linear_start_at_task_cannot_reach_any_mutation(self) -> None:
        """Selection must be rejected by each mutation action, not just the strategy.

        The invocation deliberately uses Ansible's default linear strategy,
        supplies the internal marker and strategy environment marker an
        attacker might forge, and starts directly at each mutating task.  A
        native module must never be reached in any of these cases.
        """
        controller = Path("/home/paul/projects/cristexweb/.venv/bin/ansible-playbook")
        inventory_source = ROOT / "ansible/.ansible/inventory.local.yml"
        if not controller.is_file() or not inventory_source.is_file():
            self.skipTest("canonical controller/inventory unavailable in offline worktree")
        mutation_names = (
            "Install exact renewal dependencies",
            "Create protected renewal directories during install mode",
            "Install the value-free TLS validator during install mode",
            "Install the guarded renewal executable during install mode",
            "Install the renewal service unit during install mode",
            "Install the renewal timer unit during install mode",
            "Reload systemd after install-mode renewal unit changes",
            "Keep renewal timer disabled during install mode",
            "Enable and start the guarded renewal timer",
        )
        for mutation_name in mutation_names:
            for check in (True, False):
                with self.subTest(task=mutation_name, check=check):
                    with tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        sentinel = root / "mutation-sentinel"
                        playbook = root / "direct-selected-role.yml"
                        playbook.write_text(
                            yaml.safe_dump(
                                [
                                    {
                                        "name": "reject selected TLS mutation",
                                        "hosts": "crtxweb",
                                        "gather_facts": False,
                                        "connection": "local",
                                        "become": True,
                                        "become_method": "ansible.builtin.sudo",
                                        "become_user": "root",
                                        "become_exe": "sudo",
                                        "become_flags": "-H -S -n",
                                        "vars": {
                                            "reactive_resume_dev_tls_renewal_approved": True,
                                            "reactive_resume_dev_tls_renewal_mode": "install",
                                            "reactive_resume_dev_tls_renewal_repository_root": str(ROOT),
                                            # Deliberately forged values; neither may
                                            # substitute for the wrapper/action.
                                            "reactive_resume_dev_tls_renewal_internal_mutation_privilege_attested": True,
                                        },
                                        "roles": ["reactive_resume_dev_tls_renewal"],
                                        "tasks": [
                                            {"name": "must never run", "ansible.builtin.file": {"path": str(sentinel), "state": "touch"}},
                                        ],
                                    }
                                ],
                                sort_keys=False,
                                width=100000,
                            ),
                            encoding="utf-8",
                        )
                        env = {
                            "HOME": "/home/paul",
                            "USER": "paul",
                            "LOGNAME": "paul",
                            "PATH": str(controller.parent) + ":/usr/bin:/bin",
                            "ANSIBLE_CONFIG": str(ROOT / "ansible/ansible.cfg"),
                            "ANSIBLE_ROLES_PATH": str(ROOT / "ansible/roles"),
                            "ANSIBLE_ACTION_PLUGINS": str(ROOT / "ansible/plugins/action"),
                            "ANSIBLE_LIBRARY": str(ROOT / "ansible/library"),
                            "ANSIBLE_NOCOLOR": "1",
                            "PYTHONDONTWRITEBYTECODE": "1",
                            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_ATTESTED": "v1",
                        }
                        command = [
                            str(controller),
                            "-i",
                            str(inventory_source),
                            str(playbook),
                        ]
                        if check:
                            command.append("--check")
                        command.extend(("--start-at-task", mutation_name))
                        result = subprocess.run(
                            command,
                            cwd=ROOT,
                            env=env,
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                        self.assertFalse(sentinel.exists(), result.stdout + result.stderr)
                        self.assertNotIn("changed=1", result.stdout + result.stderr)

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
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_NORMALIZED_SHA256": module._STRATEGY_NORMALIZED_SHA256,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_CANONICAL_SHA256": module._STRATEGY_CANONICAL_SHA256,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_WRAPPER_CANONICAL_SHA256": module._WRAPPER_CANONICAL_SHA256,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_ATTESTATION_SHA256": module._STRATEGY_ATTESTATION_SHA256,
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

    def test_mutation_action_binds_real_play_context_and_rejects_forged_privilege(self) -> None:
        action_path = ROOT / "ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py"
        spec = importlib.util.spec_from_file_location("rr_tls_mutation_action", action_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        task = type(
            "Task",
            (),
            {
                "action": "reactive_resume_dev_tls_renewal_mutation_guarded",
                "name": "Bind exact TLS renewal mutation privilege context",
                "args": {},
                "get_path": lambda self: f"{ROLE}:1",
            },
        )()
        action = module.ActionModule.__new__(module.ActionModule)
        action._task = task
        action._play_context = type(
            "PlayContext",
            (),
            {
                "become": True,
                "become_method": "sudo",
                "become_user": "root",
                "become_exe": "sudo",
                "become_flags": "-H -S -n",
            },
        )()
        env = {
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_ATTESTED": "v1",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME": "true",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_METHOD": "sudo",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_USER": "root",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_EXE": "sudo",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_FLAGS": "-H -S -n",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_MUTATION_ACTION_PATH": str(module._ACTION_SOURCE),
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_MUTATION_ACTION_SHA256": module._sha256(module._ACTION_SOURCE),
        }
        with (
            mock.patch.dict(module.os.environ, env, clear=True),
            mock.patch.object(module.ActionBase, "run", return_value={}),
                    mock.patch.object(module, "_wrapper_binding_valid", return_value=True),
            mock.patch.object(
                module.context,
                "CLIARGS",
                {
                    "start_at_task": None,
                    "step": False,
                    "tags": [],
                    "skip_tags": [],
                    "subset": "crtxweb",
                    "diff": True,
                    "inventory": [str(module._INVENTORY_SOURCE)],
                    "check": False,
                },
            ),
        ):
            result = action.run(task_vars={})
        self.assertFalse(result["changed"])
        self.assertEqual(
            {
                "schema": 1,
                "become": True,
                "become_method": "sudo",
                "become_user": "root",
                "become_exe": "sudo",
                "become_flags": "-H -S -n",
                "action": "reactive_resume_dev_tls_renewal_mutation_guarded",
            },
            result["ansible_facts"]["reactive_resume_dev_tls_renewal_internal_mutation_privilege_attestation"],
        )
        action._play_context.become_user = None
        with (
            mock.patch.dict(module.os.environ, env, clear=True),
            mock.patch.object(module.ActionBase, "run", return_value={}),
                    mock.patch.object(module, "_wrapper_binding_valid", return_value=True),
            mock.patch.object(module.context, "CLIARGS", {"start_at_task": None, "step": False, "tags": [], "skip_tags": []}),
        ):
            rejected = action.run(task_vars={})
        self.assertTrue(rejected["failed"])
        action._play_context.become_user = "root"
        with (
            mock.patch.dict(module.os.environ, {key: value for key, value in env.items()
                                                 if not key.endswith("MUTATION_ACTION_SHA256")}, clear=True),
            mock.patch.object(module.ActionBase, "run", return_value={}),
                    mock.patch.object(module, "_wrapper_binding_valid", return_value=True),
            mock.patch.object(module.context, "CLIARGS", {"start_at_task": None, "step": False, "tags": [], "skip_tags": []}),
        ):
            missing_source_pin = action.run(task_vars={})
        self.assertTrue(missing_source_pin["failed"])
        action._play_context.become_method = "ansible.builtin.sudo"
        action._play_context.become_exe = "sudo"
        action._play_context.become_flags = "-H -S -n"
        with (
            mock.patch.dict(module.os.environ, env, clear=True),
            mock.patch.object(module.ActionBase, "run", return_value={}),
                    mock.patch.object(module, "_wrapper_binding_valid", return_value=True),
            mock.patch.object(
                module.context,
                "CLIARGS",
                {
                    "start_at_task": None,
                    "step": False,
                    "tags": [],
                    "skip_tags": [],
                    "subset": "crtxweb",
                    "diff": True,
                    "inventory": [str(module._INVENTORY_SOURCE)],
                    "check": False,
                },
            ),
        ):
            fqcn_method = action.run(task_vars={})
        self.assertFalse(fqcn_method.get("failed", False))
        for field, value in (("become_exe", "/tmp/evil"), ("become_flags", "--evil")):
            with self.subTest(field=field):
                setattr(action._play_context, field, value)
                with (
                    mock.patch.dict(module.os.environ, env, clear=True),
                    mock.patch.object(module.ActionBase, "run", return_value={}),
                    mock.patch.object(module, "_wrapper_binding_valid", return_value=True),
                    mock.patch.object(module.context, "CLIARGS", {"start_at_task": None, "step": False, "tags": [], "skip_tags": []}),
                ):
                    rejected = action.run(task_vars={})
                self.assertTrue(rejected["failed"])
                setattr(action._play_context, field, "sudo" if field == "become_exe" else "-H -S -n")

    def test_first_task_rejects_externally_supplied_internal_state(self) -> None:
        action_path = ROOT / "ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py"
        spec = importlib.util.spec_from_file_location("rr_tls_internal_injection", action_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        task = type(
            "Task",
            (),
            {
                "action": "reactive_resume_dev_tls_renewal_mutation_guarded",
                "name": "Bind exact TLS renewal mutation privilege context",
                "args": {},
                "get_path": lambda self: f"{ROLE}:1",
            },
        )()
        action = module.ActionModule.__new__(module.ActionModule)
        action._task = task
        action._play_context = type(
            "PlayContext",
            (),
            {
                "become": True,
                "become_method": "sudo",
                "become_user": "root",
                "become_exe": "sudo",
                "become_flags": "-H -S -n",
            },
        )()
        env = {
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_ATTESTED": "v1",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME": "true",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_METHOD": "sudo",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_USER": "root",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_EXE": "sudo",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_FLAGS": "-H -S -n",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_MUTATION_ACTION_PATH": str(module._ACTION_SOURCE),
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_MUTATION_ACTION_SHA256": module._sha256(module._ACTION_SOURCE),
        }
        cliargs = {
            "start_at_task": None,
            "step": False,
            "tags": [],
            "skip_tags": [],
            "subset": "crtxweb",
            "diff": True,
            "inventory": [str(module._INVENTORY_SOURCE)],
            "check": False,
        }
        with (
            mock.patch.dict(module.os.environ, env, clear=True),
            mock.patch.object(module.ActionBase, "run", return_value={}),
            mock.patch.object(module, "_wrapper_binding_valid", return_value=True),
            mock.patch.object(module.context, "CLIARGS", cliargs),
            mock.patch.object(module.sys, "argv", ["ansible-playbook"]),
        ):
            result = action.run(
                task_vars={
                    "reactive_resume_dev_tls_renewal_internal_forged": True,
                }
            )
        self.assertTrue(result["failed"])
        self.assertIn("ENTRYPOINT_GUARD", result["msg"])
        self.assertNotIn("ansible_facts", result)

    def test_first_task_same_name_and_source_with_wrong_action_cannot_mint_attestation(self) -> None:
        action_path = ROOT / "ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py"
        spec = importlib.util.spec_from_file_location("rr_tls_wrong_action", action_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        task = type(
            "Task",
            (),
            {
                # Same reviewed name and canonical source are insufficient: the
                # first task must also be the custom action itself.
                "action": "ansible.builtin.file",
                "name": "Bind exact TLS renewal mutation privilege context",
                "args": {},
                "get_path": lambda self: f"{ROLE}:1",
            },
        )()
        action = module.ActionModule.__new__(module.ActionModule)
        action._task = task
        action._play_context = type(
            "PlayContext",
            (),
            {
                "become": True,
                "become_method": "sudo",
                "become_user": "root",
                "become_exe": "sudo",
                "become_flags": "-H -S -n",
            },
        )()
        env = {
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_ATTESTED": "v1",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME": "true",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_METHOD": "sudo",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_USER": "root",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_EXE": "sudo",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_EFFECTIVE_BECOME_FLAGS": "-H -S -n",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_MUTATION_ACTION_PATH": str(module._ACTION_SOURCE),
            "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_MUTATION_ACTION_SHA256": module._sha256(module._ACTION_SOURCE),
        }
        with (
            mock.patch.dict(module.os.environ, env, clear=True),
            mock.patch.object(module.ActionBase, "run", return_value={}),
            mock.patch.object(module, "_wrapper_binding_valid", return_value=True),
            mock.patch.object(module.context, "CLIARGS", {"start_at_task": None, "step": False, "tags": [], "skip_tags": []}),
        ):
            result = action.run(task_vars={})
        self.assertTrue(result["failed"])
        self.assertNotIn("ansible_facts", result)

    def test_mutation_action_strips_only_canonical_task_path_suffix(self) -> None:
        """Model ansible-core Task.get_path() without widening source identity."""
        action_path = ROOT / "ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py"
        spec = importlib.util.spec_from_file_location("rr_tls_task_source", action_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        from ansible.playbook.task import Task

        task = Task()
        task._origin = type("Origin", (), {"path": str(ROLE), "line_num": 17})()
        self.assertEqual(f"{ROLE}:17", task.get_path())
        self.assertEqual(str(ROLE), module._task_source(task))

        class ColumnTask:
            def __init__(self, path: str) -> None:
                self.path = path

            def get_path(self) -> str:
                return self.path

        for valid in (f"{ROLE}:1", f"{ROLE}:17:3"):
            with self.subTest(path=valid):
                self.assertEqual(str(ROLE), module._task_source(ColumnTask(valid)))
        for invalid in (
            f"{ROLE}:0",
            f"{ROLE}:17:0",
            f"{ROLE}:17:",
            f"{ROLE}:17:3:4",
            f"{ROLE}:line",
            f"{ROLE}:17x",
            f"{ROLE}.alternate:17",
            f"{ROLE}/../main.yml:17",
            f"{ROLE}:17\\n",
            str(ROLE),
            "relative/main.yml:17",
            "",
        ):
            with self.subTest(path=invalid):
                self.assertEqual("", module._task_source(ColumnTask(invalid)))

    def test_custom_action_registration_has_fail_closed_lint_shim(self) -> None:
        action = ROOT / "ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py"
        shim = ROOT / "ansible/library/reactive_resume_dev_tls_renewal_mutation_guarded.py"
        self.assertTrue(action.is_file())
        self.assertTrue(shim.is_file())
        self.assertEqual(0o644, stat.S_IMODE(shim.stat().st_mode))
        shim_text = shim.read_text(encoding="utf-8")
        self.assertIn("AnsibleModule", shim_text)
        self.assertIn("supports_check_mode=True", shim_text)
        self.assertIn("module.fail_json", shim_text)
        self.assertNotIn("subprocess", shim_text)
        self.assertNotIn("os.system", shim_text)
        self.assertIn("library = library", (ROOT / "ansible/ansible.cfg").read_text(encoding="utf-8"))
        defaults = yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))
        entries = defaults["reactive_resume_dev_tls_renewal_execution_source_hashes"]
        shim_entry = next(
            entry
            for entry in entries
            if "/library/reactive_resume_dev_tls_renewal_mutation_guarded.py" in entry["path"]
        )
        self.assertEqual(hashlib.sha256(shim.read_bytes()).hexdigest(), shim_entry["sha256"])

    def test_every_host_mutation_requires_action_privilege_marker(self) -> None:
        role = ROLE.read_text(encoding="utf-8")
        mutation_names = (
            "Install exact renewal dependencies",
            "Create protected renewal directories during install mode",
            "Install the value-free TLS validator during install mode",
            "Install the guarded renewal executable during install mode",
            "Install the renewal service unit during install mode",
            "Install the renewal timer unit during install mode",
            "Reload systemd after install-mode renewal unit changes",
            "Keep renewal timer disabled during install mode",
            "Enable and start the guarded renewal timer",
        )
        for name in mutation_names:
            section = role.split(f"- name: {name}", 1)[1]
            section = section.split("\n- name:", 1)[0]
            self.assertIn("reactive_resume_dev_tls_renewal_internal_mutation_privilege_attested", section, name)

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
        self.assertEqual(4, wrapper.count("clean_python - \"$1\" <<'PY'"))

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

    def test_role_uses_strategy_bound_effective_context_and_exact_normalized_entries(self) -> None:
        role = ROLE.read_text(encoding="utf-8")
        strategy = STRATEGY.read_text(encoding="utf-8")
        self.assertNotIn("ansible_become", role)
        self.assertNotIn("default('sudo')", strategy)
        self.assertNotIn("default('root')", strategy)
        for marker, value in (
            ("EFFECTIVE_BECOME", "'true'"),
            ("EFFECTIVE_BECOME_METHOD", "'sudo'"),
            ("EFFECTIVE_BECOME_USER", "'root'"),
            ("EFFECTIVE_BECOME_EXE", "'sudo'"),
            ("EFFECTIVE_BECOME_FLAGS", "'-H -S -n'"),
        ):
            self.assertIn(
                "CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_" + marker + "') == " + value,
                role,
            )
            if marker in {"EFFECTIVE_BECOME_EXE", "EFFECTIVE_BECOME_FLAGS"}:
                self.assertIn(
                    f'os.environ[_WRAPPER_ENV_PREFIX + "{marker}"] = _CANONICAL_BECOME_{"EXE" if marker.endswith("EXE") else "FLAGS"}',
                    strategy,
                )
            else:
                self.assertIn(
                    'os.environ[_WRAPPER_ENV_PREFIX + "' + marker + '"] = "' + value.strip("'") + '"',
                    strategy,
                )
        defaults = yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))
        execution = defaults["reactive_resume_dev_tls_renewal_execution_source_hashes"]
        normalized = [entry for entry in execution if "normalized_digest_name" in entry]
        self.assertEqual(
            [
                "reactive_resume_dev_tls_renewal_task_self_hash",
                "reactive_resume_dev_tls_renewal_defaults_self_hash",
            ],
            [entry["normalized_digest_name"] for entry in normalized],
        )
        self.assertEqual(2, len(normalized))
        self.assertEqual([], [entry for entry in defaults["reactive_resume_dev_tls_renewal_source_hashes"] if "normalized_digest_name" in entry])

    def test_role_strategy_hash_pin_matches_canonical_execution_closure(self) -> None:
        """The role's lifecycle pin must match both source and defaults closure."""
        role = ROLE.read_text(encoding="utf-8")
        strategy_digest = hashlib.sha256(STRATEGY.read_bytes()).hexdigest()
        match = re.search(
            r"CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_STRATEGY_SHA256'\)\s*==\s*'([0-9a-f]{64})'",
            role,
        )
        self.assertIsNotNone(match)
        self.assertEqual(strategy_digest, match.group(1))
        defaults = yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))
        execution = defaults["reactive_resume_dev_tls_renewal_execution_source_hashes"]
        self.assertEqual(strategy_digest, execution[4]["sha256"])

    def test_playbook_and_role_pin_first_task_and_execution_inputs(self) -> None:
        playbook = PLAYBOOK.read_text()
        role = ROLE.read_text()
        self.assertIn("strategy: reactive_resume_dev_tls_renewal_guarded_linear", playbook)
        self.assertIn("become_method: ansible.builtin.sudo", playbook)
        self.assertIn("become_user: root", playbook)
        self.assertIn("become_exe: sudo", playbook)
        self.assertIn("become_flags: '-H -S -n'", playbook)
        self.assertIn("Require strategy provenance attestation before any TLS task", role)
        self.assertIn("STRATEGY_ATTESTED", role)
        self.assertIn("EFFECTIVE_BECOME", role)
        self.assertIn("ansible_inventory_sources | list", role)
        self.assertIn("normalized_digest_name', 'defined'", role)
        self.assertIn("Require the immutable TLS renewal source paths and manifest contract", role)
        self.assertIn("Reject externally supplied source marker variables", role)
        self.assertIn("Require the fixed wrapper-bound controller inputs", role)
        self.assertIn("CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_CONTROLLER_SHA256", role)
        self.assertIn("CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_INVENTORY_SHA256", role)
        self.assertIn("CRISTEXWEB_REACTIVE_RESUME_DEV_TLS_RENEWAL_ANSIBLE_CONFIG_SHA256", role)
        self.assertIn("reactive_resume_dev_tls_renewal_task_self_hash", role)
        self.assertIn("reactive_resume_dev_tls_renewal_defaults_raw_hash", role)
        self.assertIn("reactive_resume_dev_tls_renewal_guarded_linear.py", role)
        self.assertIn("reactive_resume_dev_tls_renewal_mutation_guarded.py", role)
        defaults = yaml.safe_load(DEFAULTS.read_text())
        execution = defaults["reactive_resume_dev_tls_renewal_execution_source_hashes"]
        self.assertEqual(hashlib.sha256(STRATEGY.read_bytes()).hexdigest(), execution[4]["sha256"])
        self.assertEqual(
            hashlib.sha256((ROOT / "ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py").read_bytes()).hexdigest(),
            execution[5]["sha256"],
        )
        self.assertEqual(
            hashlib.sha256((ROOT / "ansible/library/reactive_resume_dev_tls_renewal_mutation_guarded.py").read_bytes()).hexdigest(),
            execution[6]["sha256"],
        )
        self.assertEqual(
            hashlib.sha256((ROOT / "ansible/ansible.cfg").read_bytes()).hexdigest(),
            execution[7]["sha256"],
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
        self.assertIn("InventoryManager._sources", STRATEGY.read_text())
        self.assertIn("become_exe: sudo", PLAYBOOK.read_text())
        self.assertIn("become_flags: '-H -S -n'", PLAYBOOK.read_text())
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

    def test_custom_strategy_and_mutation_action_dry_lifecycle_for_check_and_enable_apply(self) -> None:
        """Exercise both guarded plugins with a real Play definition and task context.

        The dry harness patches only LinearStrategy's queue boundary and
        ActionBase's remote executor.  The repository strategy and mutation
        action still run their real guards; no host, API, or provider is
        contacted.  This models ansible-core 2.19's unset initial strategy
        privilege context and the effective per-task context used by actions.
        """
        strategy = self._strategy_module()
        action_path = ROOT / "ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py"
        action_spec = importlib.util.spec_from_file_location("rr_tls_mutation_lifecycle", action_path)
        self.assertIsNotNone(action_spec)
        self.assertIsNotNone(action_spec.loader)
        action_module = importlib.util.module_from_spec(action_spec)
        action_spec.loader.exec_module(action_module)

        class Host:
            name = "crtxweb"

        class Inventory:
            _sources = [str(strategy._INVENTORY_SOURCE)]

            def get_host(self, name):
                return Host() if name == "crtxweb" else None

        class VariableManager:
            def get_vars(self, *, play, host):
                return {
                    "ansible_connection": "local",
                    "ansible_host": None,
                    "ansible_user": "paul",
                    "ansible_python_interpreter": "/usr/bin/python3",
                }

        play = type(
            "Play",
            (),
            {
                "become": True,
                "become_method": "ansible.builtin.sudo",
                "become_user": "root",
                "become_exe": "sudo",
                "become_flags": "-H -S -n",
            },
        )()
        effective_context = type(
            "EffectiveTaskContext",
            (),
            {
                "become": True,
                "become_method": "ansible.builtin.sudo",
                "become_user": "root",
                "become_exe": "sudo",
                "become_flags": "-H -S -n",
            },
        )()
        task = type(
            "Task",
            (),
            {
                "action": "reactive_resume_dev_tls_renewal_mutation_guarded",
                "name": "Bind exact TLS renewal mutation privilege context",
                "args": {},
                "get_path": lambda self: f"{ROLE}:1",
            },
        )()

        for mode, check in (("install", True), ("enable", False)):
            with self.subTest(mode=mode):
                payload = {
                    "reactive_resume_dev_tls_renewal_approved": True,
                    "reactive_resume_dev_tls_renewal_mode": mode,
                    "reactive_resume_dev_tls_renewal_repository_root": str(strategy._REPOSITORY_ROOT),
                }
                argv = [
                    str(strategy._CONTROLLER),
                    "-i",
                    str(strategy._INVENTORY_SOURCE),
                    str(strategy._PLAYBOOK),
                    "--diff",
                    "--limit",
                    "crtxweb",
                    "--ask-become-pass",
                    "--extra-vars",
                    json.dumps(payload, separators=(",", ":")),
                ]
                if check:
                    argv.append("--check")
                cliargs = {
                    "start_at_task": None,
                    "step": False,
                    "tags": [],
                    "skip_tags": [],
                    "subset": "crtxweb",
                    "diff": True,
                    "check": check,
                    "inventory": (str(strategy._INVENTORY_SOURCE),),
                }
                strategy_instance = strategy.StrategyModule.__new__(strategy.StrategyModule)
                strategy_instance._variable_manager = VariableManager()
                strategy_instance._inventory = Inventory()
                iterator = type("Iterator", (), {"_play": play})()

                def dry_queue(_self, _iterator, _initial_context):
                    action = action_module.ActionModule.__new__(action_module.ActionModule)
                    action._task = task
                    action._play_context = effective_context
                    with (
                        mock.patch.object(action_module.ActionBase, "run", return_value={}),
                        mock.patch.object(action_module, "_wrapper_binding_valid", return_value=True),
                    ):
                        return action.run(task_vars={})

                with (
                    mock.patch.object(strategy.context, "CLIARGS", cliargs),
                    mock.patch.object(strategy.sys, "argv", argv),
                    mock.patch.object(strategy, "_runtime_contract", return_value=True),
                    mock.patch.object(strategy, "_wrapper_binding_valid", return_value=True),
                    mock.patch.dict(strategy.os.environ, {}, clear=True),
                    mock.patch.object(strategy.LinearStrategyModule, "run", new=dry_queue),
                ):
                    result = strategy_instance.run(iterator, None)
                self.assertFalse(result.get("failed", False))
                self.assertFalse(result["changed"])
                self.assertEqual(
                    "reactive_resume_dev_tls_renewal_mutation_guarded",
                    result["ansible_facts"][
                        "reactive_resume_dev_tls_renewal_internal_mutation_privilege_attestation"
                    ]["action"],
                )

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

    def test_named_hash_normalization_preserves_unrelated_digest_integrity(self) -> None:
        module = self._strategy_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_copy = root / "tasks.yml"
            task_source = ROLE.read_text()
            task_copy.write_text(
                task_source.replace(
                    "'baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd'",
                    "'" + ("0" * 64) + "'",
                    1,
                ),
                encoding="utf-8",
            )
            self.assertNotEqual(
                module._TASK_SHA256,
                module._normalized_yaml_hash(task_copy, task=True),
            )
            strategy_source = STRATEGY.read_text()
            strategy_copy = root / "strategy-attestation.yml"
            strategy_copy.write_text(
                strategy_source.replace(
                    f'_STRATEGY_ATTESTATION_SHA256 = "{module._STRATEGY_ATTESTATION_SHA256}"',
                    f'_STRATEGY_ATTESTATION_SHA256 = "{"0" * 64}"',
                    1,
                ),
                encoding="utf-8",
            )
            self.assertNotEqual(
                module._STRATEGY_NORMALIZED_SHA256,
                module._normalized_strategy_hash(strategy_copy),
            )
            self.assertNotEqual(
                module._STRATEGY_CANONICAL_SHA256,
                module._canonical_strategy_hash(strategy_copy),
            )
            defaults_source = DEFAULTS.read_text()
            for label, needle in (
                (
                    "Infisical CLI digest",
                    "reactive_resume_dev_tls_renewal_infisical_cli_sha256: "
                    "21e24f040a09196fb1214873ef964ac74655b172575a78fd95e6c9f2ab1c8940",
                ),
                (
                    "installed-file digest",
                    "sha256: 3a62d2326a8dee0e091cb0f4b12b9dbe12a10432d737b98aed5b5a27fd1b43cf",
                ),
                (
                    "manifest digest",
                    "reactive_resume_dev_tls_renewal_manifest_sha256: "
                    "4d68e7c466e1c396454ccd663f5d45d903f41cc0b64b68c8220fa9334378888b",
                ),
            ):
                with self.subTest(label=label):
                    copy = root / (label.replace(" ", "-") + ".yml")
                    self.assertIn(needle, defaults_source)
                    copy.write_text(defaults_source.replace(needle, needle[:-64] + ("0" * 64), 1), encoding="utf-8")
                    self.assertNotEqual(
                        module._DEFAULTS_SHA256,
                        module._normalized_yaml_hash(copy),
                    )

    def test_named_self_fields_have_normalization_parity(self) -> None:
        module = self._strategy_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_source = ROLE.read_text()
            task_copy = root / "task-self.yml"
            task_copy.write_text(
                re.sub(
                    r"(?m)(reactive_resume_dev_tls_renewal_task_self_hash:\s*)'?([0-9a-f]{64})'?",
                    r"\g<1>'" + ("1" * 64) + "'",
                    task_source,
                    count=1,
                ),
                encoding="utf-8",
            )
            task_copy.write_text(
                re.sub(
                    r"(?m)(reactive_resume_dev_tls_renewal_defaults_raw_hash:\s*)'?([0-9a-f]{64})'?",
                    r"\g<1>'" + ("2" * 64) + "'",
                    task_copy.read_text(encoding="utf-8"),
                    count=1,
                ),
                encoding="utf-8",
            )
            self.assertEqual(module._TASK_SHA256, module._normalized_yaml_hash(task_copy, task=True))
            defaults_source = DEFAULTS.read_text()
            defaults_copy = root / "defaults-self.yml"
            current_defaults_hash = re.search(
                r"(?m)^reactive_resume_dev_tls_renewal_defaults_self_hash:\s*([0-9a-f]{64})$",
                defaults_source,
            )
            self.assertIsNotNone(current_defaults_hash)
            defaults_digest = current_defaults_hash.group(1)
            defaults_copy.write_text(
                defaults_source.replace(
                    "reactive_resume_dev_tls_renewal_defaults_self_hash: " + defaults_digest,
                    "reactive_resume_dev_tls_renewal_defaults_self_hash: " + ("3" * 64),
                    1,
                ).replace(
                    "normalized_digest_name: reactive_resume_dev_tls_renewal_defaults_self_hash\n"
                    "    sha256: " + defaults_digest,
                    "normalized_digest_name: reactive_resume_dev_tls_renewal_defaults_self_hash\n"
                    "    sha256: " + ("4" * 64),
                    1,
                ),
                encoding="utf-8",
            )
            self.assertEqual(module._DEFAULTS_SHA256, module._normalized_yaml_hash(defaults_copy))

    def test_cross_file_hash_parity_executes_wrapper_and_strategy_helpers(self) -> None:
        spec = importlib.util.spec_from_file_location("rr_tls_strategy_parity", STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        wrapper_source = WRAPPER.read_text()
        start = wrapper_source.index("clean_python() {")
        end = wrapper_source.index("# Immutable pre-launch pins.")
        helper_script = "python_tool=/usr/bin/python3\n" + wrapper_source[start:end]
        command = helper_script + "\nprintf '%s\\n' " + " ".join(
            (
                f"$(canonical_sha256 {shlex.quote(str(WRAPPER))} wrapper_canonical_sha256_expected)",
                f"$(normalized_strategy_sha256 {shlex.quote(str(STRATEGY))})",
                f"$(canonical_strategy_sha256 {shlex.quote(str(STRATEGY))})",
                f"$(normalized_task_sha256 {shlex.quote(str(ROLE))})",
                f"$(normalized_defaults_sha256 {shlex.quote(str(DEFAULTS))})",
            )
        )
        result = subprocess.run(
            ["/bin/dash", "-c", command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            [
                module._WRAPPER_CANONICAL_SHA256,
                module._STRATEGY_NORMALIZED_SHA256,
                module._STRATEGY_CANONICAL_SHA256,
                module._TASK_SHA256,
                module._DEFAULTS_SHA256,
            ],
            result.stdout.splitlines(),
        )
        wrapper = WRAPPER.read_text()
        defaults = yaml.safe_load(DEFAULTS.read_text())
        execution = defaults["reactive_resume_dev_tls_renewal_execution_source_hashes"]
        self.assertIn(
            f"strategy_canonical_sha256_expected='{module._STRATEGY_CANONICAL_SHA256}'",
            wrapper,
        )
        self.assertIn(
            f"strategy_normalized_sha256_expected='{module._STRATEGY_NORMALIZED_SHA256}'",
            wrapper,
        )
        self.assertIn(
            f"wrapper_canonical_sha256_expected='{module._WRAPPER_CANONICAL_SHA256}'",
            wrapper,
        )
        self.assertEqual(module._sha256(STRATEGY), execution[4]["sha256"])
        self.assertEqual(module._sha256(WRAPPER), execution[0]["sha256"])
        self.assertEqual(
            hashlib.sha256(DEFAULTS.read_bytes()).hexdigest(),
            re.search(
                r"(?m)^\s*reactive_resume_dev_tls_renewal_defaults_raw_hash:\s*'([0-9a-f]{64})'$",
                ROLE.read_text(),
            ).group(1),
        )
        role = ROLE.read_text()
        for digest in (
            module._STRATEGY_CANONICAL_SHA256,
            module._STRATEGY_NORMALIZED_SHA256,
            module._WRAPPER_CANONICAL_SHA256,
            module._TASK_SHA256,
            module._DEFAULTS_SHA256,
        ):
            self.assertIn(digest, role)


    def test_canonical_wrapper_preflight_reaches_controller_without_unbound_sources(self) -> None:
        """Execute the real wrapper preflight in a disposable source tree.

        The copied controller is the pinned local launcher and the copied
        wrapper keeps its complete preflight.  The launcher is expected to
        stop at the strategy/source boundary because this disposable tree is
        not the canonical repository; reaching Ansible proves that all
        mutation action/module variables were defined, validated, hashed, and
        exported before controller execution.  ``--check`` and a closed
        become-password input ensure this test cannot mutate a host.
        """
        canonical_root = Path("/home/paul/projects/cristexweb")
        controller_source = canonical_root / ".venv/bin/ansible-playbook"
        inventory_source = canonical_root / "ansible/.ansible/inventory.local.yml"
        if not controller_source.is_file() or not inventory_source.is_file():
            self.skipTest("canonical controller/inventory unavailable for wrapper lifecycle")

        copied_sources = (
            Path("ansible/ansible.cfg"),
            Path("ansible/playbooks/configure_reactive_resume_dev_tls_renewal.yml"),
            Path("ansible/roles/reactive_resume_dev_tls_renewal/tasks/main.yml"),
            Path("ansible/roles/reactive_resume_dev_tls_renewal/defaults/main.yml"),
            Path("ansible/plugins/strategy/reactive_resume_dev_tls_renewal_guarded_linear.py"),
            Path("ansible/plugins/action/reactive_resume_dev_tls_renewal_mutation_guarded.py"),
            Path("ansible/library/reactive_resume_dev_tls_renewal_mutation_guarded.py"),
            Path("ansible/files/components/reactive-resume-dev-tls/MANIFESTS.sha256"),
            Path("ansible/files/components/reactive-resume-dev-tls/renewal/validate-reactive-resume-dev-tls-material"),
            Path("ansible/files/components/reactive-resume-dev-tls/renewal/reactive-resume-dev-tls-renew"),
            Path("ansible/files/components/reactive-resume-dev-tls/renewal/cristexweb-reactive-resume-dev-tls-renew.service"),
            Path("ansible/files/components/reactive-resume-dev-tls/renewal/cristexweb-reactive-resume-dev-tls-renew.timer"),
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            disposable_root = Path(directory)
            for relative in copied_sources:
                destination = disposable_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            inventory = disposable_root / "ansible/.ansible/inventory.local.yml"
            inventory.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(inventory_source, inventory)
            controller = disposable_root / ".venv/bin/ansible-playbook"
            controller.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(controller_source, controller)
            for relative in copied_sources:
                destination = disposable_root / relative
                os.chmod(destination, 0o755 if relative in {
                    Path("ansible/files/components/reactive-resume-dev-tls/renewal/validate-reactive-resume-dev-tls-material"),
                    Path("ansible/files/components/reactive-resume-dev-tls/renewal/reactive-resume-dev-tls-renew"),
                } else 0o644)
            os.chmod(inventory, 0o600)
            os.chmod(controller, 0o755)

            wrapper = disposable_root / "ansible/bin/configure-reactive-resume-dev-tls-renewal"
            wrapper.parent.mkdir(parents=True, exist_ok=True)
            wrapper_source = (ROOT / "ansible/bin/configure-reactive-resume-dev-tls-renewal").read_text(
                encoding="utf-8"
            ).replace(str(canonical_root), str(disposable_root))
            zero_pin, count = re.subn(
                r"(?m)^wrapper_canonical_sha256_expected='[0-9a-f]{64}'$",
                "wrapper_canonical_sha256_expected='" + ("0" * 64) + "'",
                wrapper_source,
            )
            self.assertEqual(1, count)
            wrapper_pin = hashlib.sha256(zero_pin.encode("utf-8")).hexdigest()
            wrapper_source = zero_pin.replace(
                "wrapper_canonical_sha256_expected='" + ("0" * 64) + "'",
                "wrapper_canonical_sha256_expected='" + wrapper_pin + "'",
                1,
            )
            wrapper.write_text(wrapper_source, encoding="utf-8")
            os.chmod(wrapper, 0o755)
            temporary_files = disposable_root / "tmp"
            temporary_files.mkdir(mode=0o700)

            result = subprocess.run(
                ["/bin/dash", str(wrapper), "check"],
                cwd=disposable_root,
                env={
                    "HOME": str(disposable_root),
                    "USER": "paul",
                    "LOGNAME": "paul",
                    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                    "TMPDIR": str(temporary_files),
                    "LC_ALL": "C.UTF-8",
                },
                input="",
                text=True,
                capture_output=True,
                check=False,
                timeout=60,
            )
            combined = result.stdout + result.stderr
            self.assertIn("PLAY [", combined)
            self.assertNotIn("parameter not set", combined)
            self.assertNotIn("unbound variable", combined)
            self.assertNotIn("undefined variable", combined)
            self.assertFalse(list(temporary_files.iterdir()), combined)

    def test_role_jinja_normalizer_matches_python_and_shell_algorithms(self) -> None:
        role_tasks = yaml.safe_load(ROLE.read_text())
        expression = next(
            task["ansible.builtin.assert"]["that"][1]
            for task in role_tasks
            if task.get("name") == "Require normalized execution closure source hashes"
        )
        ansible_playbook = Path(sys.executable).with_name("ansible-playbook")
        self.assertTrue(ansible_playbook.is_file(), ansible_playbook)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = root / "inventory"
            playbook = root / "playbook.yml"
            inventory.write_text("localhost ansible_connection=local\n", encoding="utf-8")
            checks = []
            for source, expected, variable in (
                (ROLE, self._strategy_module()._TASK_SHA256, "source_task"),
                (DEFAULTS, self._strategy_module()._DEFAULTS_SHA256, "source_defaults"),
            ):
                checks.append(
                    {
                        "name": f"check {variable}",
                        "ansible.builtin.slurp": {"src": str(source)},
                        "register": variable,
                    }
                )
                rendered = expression.replace("item.content", f"{variable}.content").replace(
                    "item.item.sha256", repr(expected)
                )
                checks.extend(
                    [
                        {
                            "name": f"assert {variable}",
                            "ansible.builtin.assert": {"that": [rendered]},
                        }
                    ]
                )
            playbook.write_text(
                yaml.safe_dump(
                    [
                        {
                            "hosts": "localhost",
                            "gather_facts": False,
                            "connection": "local",
                            "tasks": checks,
                        }
                    ],
                    sort_keys=False,
                    width=100000,
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [str(ansible_playbook), "-i", str(inventory), str(playbook), "--check"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env={"PATH": str(ansible_playbook.parent) + ":/usr/bin:/bin", "LC_ALL": "C.UTF-8"},
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    @staticmethod
    def _strategy_module():
        spec = importlib.util.spec_from_file_location("rr_tls_strategy_normalizer", STRATEGY)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_playbook_adjacent_ansible_become_exe_injection_is_rejected(self) -> None:
        spec = importlib.util.spec_from_file_location("rr_tls_strategy_adjacency", STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        wrapper = WRAPPER.read_text()
        for path in (
            "$repository_root/ansible/inventory/group_vars",
            "$repository_root/ansible/inventory/host_vars",
            "$repository_root/ansible/playbooks/group_vars",
            "$repository_root/ansible/playbooks/host_vars",
        ):
            self.assertIn(path, wrapper)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory_directory = root / "ansible/.ansible"
            inventory_directory.mkdir(parents=True)
            playbook_host_vars = root / "ansible/playbooks/host_vars"
            playbook_host_vars.mkdir(parents=True)
            (playbook_host_vars / "crtxweb.yml").write_text(
                "ansible_become_exe: /tmp/evil-become\\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(module, "_REPOSITORY_ROOT", root),
                mock.patch.object(module, "_INVENTORY_DIRECTORY", inventory_directory),
            ):
                self.assertFalse(module._inventory_adjacency_contract())

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
        defaults_expected = re.search(
            r"(?m)^reactive_resume_dev_tls_renewal_defaults_self_hash: ([0-9a-f]{64})$",
            defaults,
        )
        self.assertIsNotNone(defaults_expected)
        self.assertEqual(
            self._strategy_module()._DEFAULTS_SHA256,
            self._strategy_module()._normalized_yaml_hash(DEFAULTS),
        )
        runbook = RUNBOOK.read_text()
        for required in (
            "DNS-01",
            "_acme-challenge.dev-resume.cristex-soft.com",
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
