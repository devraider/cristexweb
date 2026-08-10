from __future__ import annotations

import stat
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
KUBERNETES = ROOT / "kubernetes"
ROLE = ANSIBLE / "roles/cristexhub_dev_namespace_bootstrap"
ENTRYPOINT = ANSIBLE / "bin/bootstrap-cristexhub-dev-namespace"
PLAYBOOK = ANSIBLE / "playbooks/bootstrap_cristexhub_dev_namespace.yml"
ACTION_PLUGIN = ANSIBLE / "plugins/action/cristexhub_dev_namespace_guarded_k8s.py"
MANIFEST = KUBERNETES / "applications/namespaces/cristexhub-dev.yaml"
RUNBOOK = ROOT / "runbooks/cristexhub-dev-namespace-bootstrap.md"
TASK_START_FIXTURE = ROOT / "tests/reject_cristexhub_dev_namespace_task_start.sh"
CLEAN_CONTROLLER_FIXTURE = ROOT / "tests/validate_cristexhub_dev_namespace_clean_controller.sh"
INTERNAL_INJECTION_FIXTURE = ROOT / "tests/reject_cristexhub_dev_namespace_internal_injection.yml"


class CristexhubDevNamespaceBootstrapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.playbook = PLAYBOOK.read_text()
        cls.defaults = (ROLE / "defaults/main.yml").read_text()
        cls.tasks = (ROLE / "tasks/main.yml").read_text()
        cls.entrypoint = ENTRYPOINT.read_text()
        cls.action_plugin = ACTION_PLUGIN.read_text()
        cls.manifest = MANIFEST.read_text()
        cls.runbook = RUNBOOK.read_text()
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

    def test_exact_dev_only_manifest_is_approved_and_value_free(self) -> None:
        self.assertEqual(
            """---
apiVersion: v1
kind: Namespace
metadata:
  name: cristexhub-dev
  labels:
    app.kubernetes.io/part-of: cristexhub
    cristex.io/environment: dev
    cristex.io/bootstrap-writer: ansible
    cristex.io/desired-owner: argocd
""",
            self.manifest,
        )
        self.assertFalse(
            (KUBERNETES / "applications/namespaces/cristexhub-prod.yaml").exists()
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

    def test_exact_playbook_role_and_dedicated_source_closure(self) -> None:
        self.assertEqual(
            """---
- name: Bootstrap the approved CristexHub DEV Namespace
  hosts: k3s_servers
  gather_facts: false
  become: true
  any_errors_fatal: true
  serial: 1

  roles:
    - role: cristexhub_dev_namespace_bootstrap
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
        for forbidden in (
            "foundation_namespace_bootstrap",
            "platform_namespace_bootstrap",
            "shared-services",
            "cristexhub-prod",
        ):
            self.assertNotIn(forbidden, self.operational)

    def test_role_is_exact_present_only_and_fail_closed(self) -> None:
        self.assertTrue(
            self.tasks.startswith(
                "---\n- name: Reject externally supplied CristexHub DEV Namespace internal variables"
            )
        )
        for required in (
            "cristexhub_dev_namespace_bootstrap_approved: false",
            "cristexhub_dev_namespace_bootstrap_state: present",
            "kubernetes/applications/namespaces/cristexhub-dev.yaml",
            "['cristexhub-dev']",
            "item.metadata.name == 'cristexhub-dev'",
            "item.metadata.labels['app.kubernetes.io/part-of'] == 'cristexhub'",
            "item.metadata.labels['cristex.io/environment'] == 'dev'",
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
        ):
            self.assertIn(required, self.defaults + self.tasks)
        self.assertEqual(
            1, self.tasks.count("cristexhub_dev_namespace_guarded_k8s:")
        )
        self.assertNotIn("kubernetes.core.k8s:", self.tasks)
        self.assertEqual(2, self.tasks.count("kubernetes.core.k8s_info:"))
        for required in (
            'context.CLIARGS.get("start_at_task")',
            'context.CLIARGS.get("step")',
            'context.CLIARGS.get("tags")',
            'context.CLIARGS.get("skip_tags")',
            "TASK_SELECTION_GUARD",
            "MUTATION_ARGUMENT_GUARD",
            'self._task.action = "kubernetes.core.k8s"',
            '"state": "present"',
            '"name": "cristexhub-dev"',
            '"cristex.io/environment": "dev"',
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
            "usage: ansible/bin/bootstrap-cristexhub-dev-namespace check|apply",
            'if [ "$#" -ne 1 ]',
            ".venv/bin/ansible-playbook",
            "playbooks/bootstrap_cristexhub_dev_namespace.yml",
            "/usr/bin/env -i",
            "LC_ALL=C.UTF-8",
            "CRISTEXWEB_CRISTEXHUB_DEV_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1",
            "CRISTEXWEB_CRISTEXHUB_DEV_NAMESPACE_BOOTSTRAP_TOKEN=$attestation_token",
            "CRISTEXWEB_CRISTEXHUB_DEV_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE=$attestation_file",
            "/usr/bin/openssl rand -hex 32",
            "cristexhub_dev_namespace_bootstrap_approved=true",
            "--diff",
            "--limit crtxweb",
            "--ask-become-pass",
            'set -- "$@" --check',
        ):
            self.assertIn(required, self.entrypoint)
        for arguments in (("check", "--start-at-task", "anything"), ("apply", "--step")):
            result = subprocess.run(
                [str(ENTRYPOINT), *arguments],
                cwd=ROOT,
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(64, result.returncode, (arguments, result.stdout, result.stderr))
            self.assertNotIn("PLAY [", result.stdout + result.stderr)

    def test_negative_fixtures_and_clean_controller_are_exact(self) -> None:
        for path in (TASK_START_FIXTURE, CLEAN_CONTROLLER_FIXTURE):
            self.assertEqual(
                stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                path.stat().st_mode
                & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
            )
        task_start = TASK_START_FIXTURE.read_text()
        clean = CLEAN_CONTROLLER_FIXTURE.read_text()
        injection = INTERNAL_INJECTION_FIXTURE.read_text()
        for required in (
            "CRISTEXWEB_CRISTEXHUB_DEV_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1",
            "CRISTEXWEB_CRISTEXHUB_DEV_NAMESPACE_BOOTSTRAP_TOKEN",
            "CRISTEXWEB_CRISTEXHUB_DEV_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE",
            "--start-at-task",
            "cristexhub_dev_namespace_bootstrap_internal_preflight_binding",
            "TASK_SELECTION_GUARD",
            "status -ne 0",
        ):
            self.assertIn(required, task_start)
        self.assertIn(
            "bootstrap_cristexhub_dev_namespace.yml --syntax-check", clean
        )
        self.assertIn("name: cristexhub_dev_namespace_bootstrap", injection)
        self.assertIn("INTERNAL_VARIABLE_GUARD", injection)
        self.assertNotIn("kubernetes.core", injection)

    def test_runbook_and_specs_keep_runtime_and_prod_blocked(self) -> None:
        normalized = " ".join(self.runbook.split())
        for required in (
            "SOURCE READY — RUNTIME NOT RUN",
            "cristexhub-dev",
            "`cristexhub-prod` remains absent",
            "separate check, first apply, and idempotence approvals",
            "No Secret, workload, Service, PVC, policy, route, or PROD object",
        ):
            self.assertIn(required, normalized)
        for relative in (
            "AGENTS.md",
            "README.md",
            "ansible/README.md",
            "architecture-plan.md",
            "specs/k3s-iac-foundation/brief.md",
            "specs/k3s-iac-foundation/requirements.md",
            "specs/k3s-iac-foundation/tasks.md",
            "specs/k3s-iac-foundation/testcases.md",
            "specs/k3s-iac-foundation/status.md",
        ):
            self.assertIn(
                "cristexhub-dev-namespace-bootstrap.md",
                (ROOT / relative).read_text(),
                relative,
            )


if __name__ == "__main__":
    unittest.main()
