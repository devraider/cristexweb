import stat
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
ROLE = ANSIBLE / "roles/reactive_resume_dev_soak"
DEFAULTS = ROLE / "defaults/main.yml"
TASKS = ROLE / "tasks/main.yml"
SAMPLE = ROLE / "tasks/sample.yml"
PLAYBOOK = ANSIBLE / "playbooks/soak_reactive_resume_dev.yml"
WRAPPER = ANSIBLE / "bin/soak-reactive-resume-dev"
RUNBOOK = ROOT / "runbooks/reactive-resume-dev-soak.md"


class ReactiveResumeDevSoakContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.defaults = DEFAULTS.read_text()
        self.tasks = TASKS.read_text()
        self.sample = SAMPLE.read_text()
        self.playbook = PLAYBOOK.read_text()
        self.wrapper = WRAPPER.read_text()
        self.runbook = RUNBOOK.read_text()

    def test_fixed_duration_and_shared_realm_contract(self) -> None:
        for value in (
            "reactive_resume_dev_soak_duration_seconds: 900",
            "reactive_resume_dev_soak_interval_seconds: 60",
            "reactive_resume_dev_soak_sample_count: 16",
            "reactive_resume_dev_soak_hostname: resume-dev.cristex-soft.com",
            "reactive_resume_dev_soak_oidc_issuer: https://auth.cristex-soft.com/realms/cristexhub",
            "reactive_resume_dev_soak_prod_namespace: cristexhub-prod",
            "reactive_resume_dev_soak_backup_timer: cristexweb-reactive-resume-dev-backup.timer",
            "reactive_resume_dev_soak_receipt_format: sanitized-v1",
        ):
            self.assertIn(value, self.defaults, value)
        self.assertIn("sample_count == (reactive_resume_dev_soak_duration_seconds // reactive_resume_dev_soak_interval_seconds) + 1", self.tasks)

    def test_read_only_probe_closure_and_prod_fence(self) -> None:
        for value in (
            "ansible_check_mode",
            "ansible_diff_mode",
            "ansible.builtin.command:",
            "/usr/bin/systemctl",
            "is-active",
            "is-enabled",
            "kubernetes.core.k8s_info:",
            "ansible.builtin.uri:",
            "validate_certs: true",
            "reactive_resume_dev_soak_internal_prod_results",
            "prod_activation_absent",
            "values_output: false",
            "from_json",
            "reactive_resume_dev_soak_internal_samples",
        ):
            self.assertIn(value, self.tasks + self.sample, value)
        for forbidden in (
            "ansible.builtin.shell:",
            "ansible.builtin.copy:",
            "ansible.builtin.template:",
            "kubernetes.core.k8s:",
            "kubernetes.core.k8s_delete",
            "ansible.builtin.systemd_service:",
            "stringData:",
        ):
            self.assertNotIn(forbidden, self.tasks + self.sample, forbidden)

    def test_wrapper_is_check_only_and_non_passthrough(self) -> None:
        self.assertEqual(0o755, stat.S_IMODE(WRAPPER.stat().st_mode))
        for value in (
            "usage='usage: ansible/bin/soak-reactive-resume-dev check'",
            "playbooks/soak_reactive_resume_dev.yml",
            "--check",
            "--diff",
            "--limit crtxweb",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_SOAK_ENTRYPOINT=v1",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_SOAK_TOKEN",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_SOAK_ATTESTATION_FILE",
            "/usr/bin/env -i",
            "reactive_resume_dev_soak_approved",
        ):
            self.assertIn(value, self.wrapper, value)
        for forbidden in ("apply", "exec \"$@\"", "kubectl apply", "tofu apply"):
            self.assertNotIn(forbidden, self.wrapper, forbidden)

    def test_source_files_parse_and_runbook_sets_pass_criteria(self) -> None:
        self.assertEqual("soak_reactive_resume_dev.yml", PLAYBOOK.name)
        self.assertEqual("reactive_resume_dev_soak", yaml.safe_load(self.playbook)[0]["roles"][0]["role"])
        yaml.safe_load(self.defaults)
        yaml.safe_load(self.tasks)
        yaml.safe_load(self.sample)
        for value in (
            "source-only, guarded, read-only",
            "16 samples",
            "900 seconds",
            "reactive-resume-dev-backup.timer",
            "cristexhub-prod",
            "values_output=false",
            "no apply, delete, enable, restart",
        ):
            self.assertIn(value, " ".join(self.runbook.split()), value)
        for forbidden in ("BEGIN PRIVATE KEY", "Authorization: Bearer", "client_secret", "password:"):
            self.assertNotIn(forbidden, self.runbook + self.tasks + self.sample)


if __name__ == "__main__":
    unittest.main()
