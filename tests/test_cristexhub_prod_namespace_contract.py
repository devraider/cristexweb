from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
KUBERNETES = ROOT / "kubernetes"
ROLE = ANSIBLE / "roles/cristexhub_prod_namespace_bootstrap"
ENTRYPOINT = ANSIBLE / "bin/bootstrap-cristexhub-prod-namespace"
PLAYBOOK = ANSIBLE / "playbooks/bootstrap_cristexhub_prod_namespace.yml"
ACTION_PLUGIN = ANSIBLE / "plugins/action/cristexhub_prod_namespace_guarded_k8s.py"
MANIFEST = KUBERNETES / "applications/namespaces/cristexhub-prod.yaml"
RUNBOOK = ROOT / "runbooks/cristexhub-prod-namespace-bootstrap.md"
TESTCASES = ROOT / "specs/k3s-iac-foundation/testcases.md"
TASK_START_FIXTURE = ROOT / "tests/reject_cristexhub_prod_namespace_task_start.sh"
CLEAN_CONTROLLER_FIXTURE = ROOT / "tests/validate_cristexhub_prod_namespace_clean_controller.sh"
INTERNAL_INJECTION_FIXTURE = ROOT / "tests/reject_cristexhub_prod_namespace_internal_injection.yml"
ACTION_ONLY_FIXTURE = ROOT / "tests/reject_cristexhub_prod_namespace_action_only.yml"
_EXPECTED_MANIFEST_SHA256 = "f029bb06bb698c6ddc3e083985f754bd326de8b18804523d1300eae54e8260d0"


class CristexhubProdNamespaceBootstrapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.playbook = PLAYBOOK.read_text()
        cls.defaults = (ROLE / "defaults/main.yml").read_text()
        cls.tasks = (ROLE / "tasks/main.yml").read_text()
        cls.entrypoint = ENTRYPOINT.read_text()
        cls.action_plugin = ACTION_PLUGIN.read_text()
        cls.manifest = MANIFEST.read_text()
        cls.runbook = RUNBOOK.read_text()
        cls.testcases = TESTCASES.read_text()
        cls.operational = "\n".join(
            (
                cls.playbook,
                cls.defaults,
                cls.tasks,
                cls.entrypoint,
                cls.action_plugin,
                cls.manifest,
            )
        )

    def test_exact_prod_manifest_is_present_only_and_value_free(self) -> None:
        self.assertEqual(
            """---
apiVersion: v1
kind: Namespace
metadata:
  name: cristexhub-prod
  labels:
    app.kubernetes.io/part-of: cristexhub
    cristex.io/environment: prod
    cristex.io/bootstrap-writer: ansible
    cristex.io/desired-owner: argocd
""",
            self.manifest,
        )
        self.assertTrue(MANIFEST.is_file())
        self.assertTrue(
            (KUBERNETES / "applications/namespaces/cristexhub-dev.yaml").is_file()
        )
        for forbidden in (
            "kind: Secret",
            "kind: ServiceAccount",
            "kind: ResourceQuota",
            "kind: LimitRange",
            "kind: NetworkPolicy",
            "kind: Deployment",
            "kind: Service",
            "kind: PersistentVolumeClaim",
            "kind: Ingress",
            "pod-security.kubernetes.io",
        ):
            self.assertNotIn(forbidden, self.manifest)

    def test_manifest_hash_is_a_non_overridable_literal(self) -> None:
        self.assertEqual(
            _EXPECTED_MANIFEST_SHA256,
            hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        )
        self.assertNotIn("cristexhub_prod_namespace_bootstrap_expected_hashes", self.defaults)
        self.assertIn(
            f"item.stat.checksum == '{_EXPECTED_MANIFEST_SHA256}'",
            self.tasks,
        )
        self.assertIn(
            f"['{_EXPECTED_MANIFEST_SHA256}']",
            self.tasks,
        )
        self.assertIn(
            f'_EXPECTED_MANIFEST_SHA256 = "{_EXPECTED_MANIFEST_SHA256}"',
            self.action_plugin,
        )
        for required in (
            "get_checksum: true",
            "checksum_algorithm: sha256",
            "item.stat.checksum ==",
            "manifest_sha256:",
            "manifest_sha256 ==",
        ):
            self.assertIn(required, self.tasks)

    def test_exact_playbook_role_and_source_closure(self) -> None:
        self.assertEqual(
            """---
- name: Bootstrap the approved CristexHub PROD Namespace
  hosts: k3s_servers
  gather_facts: false
  become: true
  any_errors_fatal: true
  serial: 1

  roles:
    - role: cristexhub_prod_namespace_bootstrap
""",
            self.playbook,
        )
        self.assertEqual(
            {"defaults/main.yml", "tasks/main.yml"},
            {
                str(path.relative_to(ROLE))
                for path in ROLE.rglob("*")
                if path.is_file()
            },
        )
        expected_source_names = {
            "ansible/bin/bootstrap-cristexhub-prod-namespace",
            "ansible/playbooks/bootstrap_cristexhub_prod_namespace.yml",
            "ansible/plugins/action/cristexhub_prod_namespace_guarded_k8s.py",
            "ansible/roles/cristexhub_prod_namespace_bootstrap/defaults/main.yml",
            "ansible/roles/cristexhub_prod_namespace_bootstrap/tasks/main.yml",
            "kubernetes/applications/namespaces/cristexhub-prod.yaml",
        }
        for relative in expected_source_names:
            self.assertTrue((ROOT / relative).is_file(), relative)
        for forbidden in (
            "foundation_namespace_bootstrap",
            "platform_namespace_bootstrap",
            "shared-services",
            "cristexhub-dev",
            "state: absent",
            "force: true",
            "delete_all:",
        ):
            self.assertNotIn(forbidden, self.operational)

    def test_role_is_exact_present_only_and_fail_closed(self) -> None:
        self.assertTrue(
            self.tasks.startswith(
                "---\n- name: Reject externally supplied CristexHub PROD Namespace internal variables"
            )
        )
        for required in (
            "cristexhub_prod_namespace_bootstrap_approved: false",
            "cristexhub_prod_namespace_bootstrap_state: present",
            "kubernetes/applications/namespaces/cristexhub-prod.yaml",
            "['cristexhub-prod']",
            "item.metadata.name == 'cristexhub-prod'",
            "item.metadata.labels['app.kubernetes.io/part-of'] == 'cristexhub'",
            "item.metadata.labels['cristex.io/environment'] == 'prod'",
            "item.metadata.labels['cristex.io/bootstrap-writer'] == 'ansible'",
            "item.metadata.labels['cristex.io/desired-owner'] == 'argocd'",
            "item.metadata.labels | length == 4",
            "state: present",
            "wait: true",
            "ansible_diff_mode",
            "(ansible_limit | default('')) == 'crtxweb'",
            "ansible_play_hosts_all | length == 1",
            "status.phase == 'Active'",
            "when: not ansible_check_mode",
            "k3s.service",
            "tailscaled.service",
            "refusing silent adoption",
            "(item.resources[0].metadata.labels | default({})) ==",
            "no_delete_path: true",
        ):
            self.assertIn(required, self.defaults + self.tasks)
        self.assertEqual(
            1, self.tasks.count("cristexhub_prod_namespace_guarded_k8s:")
        )
        self.assertNotIn("kubernetes.core.k8s:", self.tasks)
        self.assertEqual(2, self.tasks.count("kubernetes.core.k8s_info:"))
        for required in (
            'context.CLIARGS.get("start_at_task")',
            'context.CLIARGS.get("step")',
            'context.CLIARGS.get("tags")',
            'context.CLIARGS.get("skip_tags")',
            "_EXPECTED_TASK_SOURCE",
            "canonical guarded role task source",
            "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE",
            "valid_attestation",
            "valid_binding",
            "cristexhub_prod_namespace_bootstrap_approved",
            "cristexhub_prod_namespace_bootstrap_state",
            "TASK_SELECTION_GUARD",
            "MUTATION_ARGUMENT_GUARD",
            'self._task.action = "kubernetes.core.k8s"',
            '"state": "present"',
            '"name": "cristexhub-prod"',
            '"cristex.io/environment": "prod"',
            "no_delete_path",
        ):
            self.assertIn(required, self.action_plugin)
        for forbidden in (
            "state: absent",
            "force: true",
            "delete_all:",
            "kind: Secret",
            "kind: ServiceAccount",
            "kind: ResourceQuota",
            "kind: LimitRange",
            "kind: NetworkPolicy",
            "kind: Deployment",
            "kind: Service",
            "kind: PersistentVolumeClaim",
            "kind: Ingress",
            "ansible.builtin.shell:",
            "ansible.builtin.command:",
            "ansible.builtin.include_tasks:",
            "ansible.builtin.import_tasks:",
        ):
            self.assertNotIn(forbidden, self.tasks)

    def test_wrapper_is_non_passthrough_and_uses_private_attestation(self) -> None:
        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            ENTRYPOINT.stat().st_mode
            & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        for required in (
            "usage: ansible/bin/bootstrap-cristexhub-prod-namespace check|apply",
            'if [ "$#" -ne 1 ]',
            '.venv/bin/ansible-playbook',
            "playbooks/bootstrap_cristexhub_prod_namespace.yml",
            "/usr/bin/env -i",
            "LC_ALL=C.UTF-8",
            "CRISTEXWEB_REPOSITORY_ROOT=$repository_root",
            "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1",
            "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_TOKEN=$attestation_token",
            "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE=$attestation_file",
            "/usr/bin/openssl rand -hex 32",
            "{\"cristexhub_prod_namespace_bootstrap_approved\":true}",
            "--diff",
            "--limit crtxweb",
            "--ask-become-pass",
            'set -- "$@" --check',
            "trap cleanup EXIT HUP INT TERM",
        ):
            self.assertIn(required, self.entrypoint)
        self.assertNotIn("uv run", self.entrypoint)
        execution_lines = "\n".join(
            line
            for line in self.entrypoint.splitlines()
            if "refusing passthrough" not in line
        )
        self.assertNotIn("--start-at-task", execution_lines)
        self.assertNotIn("--step", execution_lines)

    def test_offline_negative_fixtures_and_clean_controller_are_exact(self) -> None:
        for path in (TASK_START_FIXTURE, CLEAN_CONTROLLER_FIXTURE):
            self.assertEqual(
                stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                path.stat().st_mode
                & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
            )
        self.assertTrue(ACTION_ONLY_FIXTURE.is_file())
        task_start = TASK_START_FIXTURE.read_text()
        clean = CLEAN_CONTROLLER_FIXTURE.read_text()
        injection = INTERNAL_INJECTION_FIXTURE.read_text()
        action_only = ACTION_ONLY_FIXTURE.read_text()
        for required in (
            "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1",
            "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_TOKEN",
            "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE",
            "--start-at-task",
            "cristexhub_prod_namespace_bootstrap_internal_preflight_binding",
            "TASK_SELECTION_GUARD",
            "status -ne 0",
        ):
            self.assertIn(required, task_start)
        self.assertIn(
            "bootstrap_cristexhub_prod_namespace.yml --syntax-check", clean
        )
        self.assertIn("name: cristexhub_prod_namespace_bootstrap", injection)
        self.assertIn("INTERNAL_VARIABLE_GUARD", injection)
        self.assertNotIn("kubernetes.core", injection)
        self.assertIn("canonical guarded role task source", self.action_plugin)
        self.assertIn("manifest_sha256", action_only)
        self.assertIn("cristexhub_prod_namespace_bootstrap_approved: true", action_only)
        self.assertNotIn("kubernetes.core", injection)

        controller = ROOT / ".venv/bin/ansible-playbook"
        if not controller.is_file():
            self.skipTest("offline controller environment is not installed")

        token = "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            attestation_file = Path(directory) / "attestation"
            attestation_file.write_text(f"{token}:entrypoint\n")
            attestation_file.chmod(0o600)
            env = os.environ.copy()
            env.update(
                {
                    "ANSIBLE_CONFIG": str(ROOT / "ansible/ansible.cfg"),
                    "CRISTEXWEB_REPOSITORY_ROOT": str(ROOT),
                    "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_ENTRYPOINT": "v1",
                    "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_TOKEN": token,
                    "CRISTEXWEB_CRISTEXHUB_PROD_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE": str(attestation_file),
                }
            )
            action_result = subprocess.run(
                [
                    str(controller),
                    "-i",
                    "localhost,",
                    str(ACTION_ONLY_FIXTURE),
                ],
                cwd=ROOT / "ansible",
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(0, action_result.returncode)
        action_output = action_result.stdout + action_result.stderr
        self.assertIn("ENTRYPOINT_GUARD", action_output)
        self.assertIn("canonical guarded role task source", action_output)
        self.assertNotIn("Failed to connect", action_output)

        injection_env = os.environ.copy()
        injection_env.update(
            {
                "ANSIBLE_CONFIG": str(ROOT / "ansible/ansible.cfg"),
                "ANSIBLE_ROLES_PATH": str(ROOT / "ansible/roles"),
            }
        )
        injection_result = subprocess.run(
            [
                str(controller),
                "-i",
                "localhost,",
                str(INTERNAL_INJECTION_FIXTURE),
                "--extra-vars",
                '{"cristexhub_prod_namespace_bootstrap_internal_preflight_binding":{}}',
            ],
            cwd=ROOT / "ansible",
            env=injection_env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, injection_result.returncode)
        injection_output = injection_result.stdout + injection_result.stderr
        self.assertIn("INTERNAL_VARIABLE_GUARD", injection_output)
        self.assertNotIn("Failed to connect", injection_output)

    def test_runbook_and_testcase_keep_all_runtime_blocked(self) -> None:
        normalized = " ".join(self.runbook.split())
        for required in (
            "SOURCE-ONLY — NOT RUN / BLOCKED",
            "cristexhub-prod",
            "cristex.io/environment: prod",
            "check and apply remain NOT RUN/BLOCKED",
            "separate human approval",
            "refuses foreign existing",
            "no deletion path",
            "No Secret, workload, Service, PVC, policy, route, or PROD workload",
        ):
            self.assertIn(required, normalized)
        self.assertIn("KIF-NS-07", self.testcases)
        testcase = self.testcases.split("| KIF-NS-07", 1)[1].split("\n", 1)[0]
        self.assertIn("PASS SOURCE-ONLY / CHECK-APPLY NOT RUN-BLOCKED", testcase)
        self.assertIn("cristexhub-prod", testcase)
        self.assertIn("exact four PROD labels", testcase)
        self.assertIn("offline", testcase.lower())
        self.assertNotIn("first apply passed", testcase)
        self.assertNotIn("idempotence passed", testcase)


if __name__ == "__main__":
    unittest.main()
