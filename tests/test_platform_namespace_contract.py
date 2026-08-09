from __future__ import annotations

import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
KUBERNETES = ROOT / "kubernetes"
ROLE = ANSIBLE / "roles/platform_namespace_bootstrap"
ENTRYPOINT = ANSIBLE / "bin/bootstrap-platform-namespaces"
TASK_START_FIXTURE = ROOT / "tests/reject_platform_namespace_task_start.sh"
CLEAN_CONTROLLER_FIXTURE = ROOT / "tests/validate_platform_namespace_clean_controller.sh"


class PlatformNamespaceBootstrapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.playbook_path = ANSIBLE / "playbooks/bootstrap_platform_namespaces.yml"
        cls.playbook = cls.playbook_path.read_text()
        cls.defaults = (ROLE / "defaults/main.yml").read_text()
        cls.tasks = (ROLE / "tasks/main.yml").read_text()
        cls.operational = f"{cls.playbook}\n{cls.defaults}\n{cls.tasks}"
        cls.task_blocks: dict[str, str] = {}
        current_name: str | None = None
        current_lines: list[str] = []
        for line in cls.tasks.splitlines(keepends=True):
            if line.startswith("- name: "):
                if current_name is not None:
                    cls.task_blocks[current_name] = "".join(current_lines)
                current_name = line.removeprefix("- name: ").strip()
                current_lines = [line]
            elif current_name is not None:
                current_lines.append(line)
        if current_name is not None:
            cls.task_blocks[current_name] = "".join(current_lines)

    def task(self, name: str) -> str:
        self.assertIn(name, self.task_blocks)
        return self.task_blocks[name]

    def test_exact_namespace_source_set_and_truthful_content(self) -> None:
        expected = {
            "platform/namespaces/argocd.yaml": """---
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
  labels:
    app.kubernetes.io/part-of: cristex-platform
    cristex.io/bootstrap-writer: ansible
    cristex.io/desired-owner: argocd
""",
            "platform/namespaces/platform-edge.yaml": """---
apiVersion: v1
kind: Namespace
metadata:
  name: platform-edge
  labels:
    app.kubernetes.io/part-of: cristex-platform
    cristex.io/bootstrap-writer: ansible
    cristex.io/desired-owner: argocd
""",
            "platform/namespaces/shared-services.yaml": """---
apiVersion: v1
kind: Namespace
metadata:
  name: shared-services
  labels:
    app.kubernetes.io/part-of: cristex-platform
    cristex.io/bootstrap-writer: ansible
    cristex.io/desired-owner: argocd
""",
        }
        actual_files = {
            str(path.relative_to(KUBERNETES)): path.read_text()
            for path in KUBERNETES.rglob("*")
            if path.is_file()
        }
        self.assertEqual(expected, actual_files)
        combined = "\n".join(actual_files.values())
        for forbidden in (
            "app.kubernetes.io/managed-by",
            "kind: Secret",
            "kind: ConfigMap",
            "kind: Pod",
            "kind: Deployment",
            "kind: Service",
            "kind: Ingress",
            "kind: NetworkPolicy",
            "pod-security.kubernetes.io",
        ):
            self.assertNotIn(forbidden, combined)

    def test_exact_playbook_and_role_file_closure(self) -> None:
        self.assertEqual(
            """---
- name: Bootstrap the approved persistent platform Namespaces
  hosts: k3s_servers
  gather_facts: false
  become: true
  any_errors_fatal: true
  serial: 1

  roles:
    - role: platform_namespace_bootstrap
""",
            self.playbook,
        )
        role_files = {
            str(path.relative_to(ROLE))
            for path in ROLE.rglob("*")
            if path.is_file()
        }
        self.assertEqual({"defaults/main.yml", "tasks/main.yml"}, role_files)
        self.assertNotIn("pre_tasks:", self.playbook)
        self.assertNotIn("post_tasks:", self.playbook)
        self.assertEqual(1, self.playbook.count("- role:"))
        for path in [self.playbook_path, *(ROLE / "tasks").rglob("*.yml")]:
            text = path.read_text()
            for forbidden in (
                "ansible.builtin.include_tasks:",
                "ansible.builtin.import_tasks:",
                "ansible.builtin.include_role:",
                "ansible.builtin.import_role:",
                "include_tasks:",
                "import_tasks:",
                "include_role:",
                "import_role:",
            ):
                self.assertNotIn(forbidden, text, (path, forbidden))

    def test_non_passthrough_entrypoint_rejects_task_skipping_controls(self) -> None:
        self.assertEqual(
            {
                ENTRYPOINT,
                ANSIBLE / "bin/bootstrap-foundation-namespaces",
            },
            {path for path in (ANSIBLE / "bin").rglob("*") if path.is_file()},
        )
        entrypoint = ENTRYPOINT.read_text()
        task_start_fixture = TASK_START_FIXTURE.read_text()
        clean_controller_fixture = CLEAN_CONTROLLER_FIXTURE.read_text()
        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            CLEAN_CONTROLLER_FIXTURE.stat().st_mode
            & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        for required in (
            "/usr/bin/env -i",
            "LC_ALL=C.UTF-8",
            ".venv/bin/ansible-playbook",
            "bootstrap_platform_namespaces.yml --syntax-check",
            "wrapper-equivalent clean controller environment",
        ):
            self.assertIn(required, clean_controller_fixture)
        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            TASK_START_FIXTURE.stat().st_mode
            & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        for required in (
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1",
            "--start-at-task",
            "Create or reconcile only the approved platform Namespaces",
            "item=(argocd|platform-edge)",
            "status -ne 0",
            "cannot mutate without the private single-run wrapper attestation",
        ):
            self.assertIn(required, task_start_fixture)
        self.assertNotIn("CRISTEXWEB_NAMESPACE_BOOTSTRAP_TOKEN", task_start_fixture)
        self.assertNotIn("CRISTEXWEB_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE", task_start_fixture)

        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            ENTRYPOINT.stat().st_mode
            & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        for required in (
            'if [ "$#" -ne 1 ]',
            'controller="$repository_root/.venv/bin/ansible-playbook"',
            "/usr/bin/env -i",
            "LC_ALL=C.UTF-8",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_TOKEN=$attestation_token",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE=$attestation_file",
            "/usr/bin/mktemp",
            "/usr/bin/openssl rand -hex 32",
            "trap cleanup EXIT HUP INT TERM",
            'ANSIBLE_CONFIG=$PWD/ansible.cfg',
            "--diff",
            "--limit crtxweb",
            "platform_namespace_bootstrap_approved=true",
            "--ask-become-pass",
            'set -- "$@" --check',
            'run_controller "$@"',
        ):
            self.assertIn(required, entrypoint)
        self.assertIn("set -- \\\n  \"$controller\"", entrypoint)
        self.assertNotIn("uv run", entrypoint)
        self.assertNotIn("UV_", entrypoint)
        self.assertNotIn("VIRTUAL_ENV", entrypoint)
        self.assertNotIn("PYTHONPATH", entrypoint)
        self.assertNotIn("--start-at-task", "\n".join(
            line for line in entrypoint.splitlines() if "refusing passthrough" not in line
        ))
        self.assertNotIn("--step", "\n".join(
            line for line in entrypoint.splitlines() if "refusing passthrough" not in line
        ))

        for arguments in (
            ("check", "--start-at-task", "Create or reconcile only the approved platform Namespaces"),
            ("apply", "--step"),
        ):
            result = subprocess.run(
                [str(ENTRYPOINT), *arguments],
                cwd=ROOT,
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(64, result.returncode, (arguments, result.stdout, result.stderr))
            self.assertIn("refusing passthrough arguments", result.stderr)
            self.assertNotIn("PLAY [", result.stdout + result.stderr)

    def test_internal_variable_guard_is_the_unique_first_task(self) -> None:
        guard_name = "Reject externally supplied platform Namespace internal variables"
        self.assertEqual(guard_name, next(iter(self.task_blocks)))
        guard = self.task(guard_name)
        protected = (
            "platform_namespace_bootstrap_internal_attestation_state",
            "platform_namespace_bootstrap_internal_controller_path_states",
            "platform_namespace_bootstrap_internal_manifest_path_states",
            "platform_namespace_bootstrap_internal_manifests",
            "platform_namespace_bootstrap_internal_service_facts_before",
            "platform_namespace_bootstrap_internal_kubeconfig_state",
            "platform_namespace_bootstrap_internal_prestate",
            "platform_namespace_bootstrap_internal_poststate",
            "platform_namespace_bootstrap_internal_service_facts_after",
        )
        self.assertIn("item not in vars", guard)
        self.assertIn("INTERNAL_VARIABLE_GUARD", guard)
        for name in protected:
            self.assertIn(name, guard)
        later_tasks = self.tasks[self.tasks.index("- name: Require the platform") :]
        for name in protected:
            self.assertIn(name, later_tasks)

        fixture = (ROOT / "tests/reject_platform_namespace_internal_injection.yml").read_text()
        self.assertIn("hosts: localhost", fixture)
        self.assertIn("connection: local", fixture)
        self.assertIn("name: platform_namespace_bootstrap", fixture)
        self.assertIn(guard_name, fixture)
        self.assertIn("INTERNAL_VARIABLE_GUARD", fixture)
        self.assertNotIn("kubernetes.core", fixture)

    def test_public_inputs_are_pinned_and_manifests_load_controller_side(self) -> None:
        approval = self.task("Require the platform Namespace bootstrap approval contract")
        for required in (
            "platform_namespace_bootstrap_approved | bool",
            "platform_namespace_bootstrap_state == 'present'",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_ENTRYPOINT",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_TOKEN",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE",
            "ansible_diff_mode",
            "(ansible_limit | default('')) == 'crtxweb'",
            "ansible_play_hosts_all | length == 1",
            "platform_namespace_bootstrap_kubeconfig == '/etc/rancher/k3s/k3s.yaml'",
            "platform_namespace_bootstrap_controller_user == lookup('ansible.builtin.env', 'USER')",
            "platform_namespace_bootstrap_repository_root ==",
            "platform_namespace_bootstrap_controller_path_components ==",
            "platform_namespace_bootstrap_manifest_paths ==",
            "kubernetes/platform/namespaces/argocd.yaml",
            "kubernetes/platform/namespaces/platform-edge.yaml",
        ):
            self.assertIn(required, self.operational + approval)

        attestation_stat = self.task(
            "Inspect the ephemeral Namespace bootstrap entrypoint attestation"
        )
        for required in (
            "ansible.builtin.stat:",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE",
            "follow: false",
            "register: platform_namespace_bootstrap_internal_attestation_state",
            "delegate_to: localhost",
            "become: false",
            "no_log: true",
        ):
            self.assertIn(required, attestation_stat)
        attestation_assert = self.task(
            "Require the private single-run Namespace bootstrap attestation"
        )
        for required in (
            "platform_namespace_bootstrap_internal_attestation_state",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_TOKEN",
            "':entrypoint'",
            "pw_name ==",
            "mode == '0600'",
            "delegate_to: localhost",
            "no_log: true",
        ):
            self.assertIn(required, attestation_assert)

        load = self.task("Load the exact committed Namespace manifests on the controller")
        for required in (
            "lookup('ansible.builtin.file', item) | from_yaml",
            "platform_namespace_bootstrap_manifest_paths",
            "platform_namespace_bootstrap_internal_manifests",
            "delegate_to: localhost",
            "become: false",
            "changed_when: false",
        ):
            self.assertIn(required, load)
        contract = self.task("Require the exact bounded Namespace manifest contract")
        for required in (
            "['argocd', 'platform-edge']",
            "item.keys() | list | sort == ['apiVersion', 'kind', 'metadata']",
            "item.apiVersion == 'v1'",
            "item.kind == 'Namespace'",
            "item.metadata.keys() | list | sort == ['labels', 'name']",
            "app.kubernetes.io/part-of",
            "cristex.io/bootstrap-writer",
            "cristex.io/desired-owner",
            "item.metadata.labels | length == 3",
        ):
            self.assertIn(required, contract)
        self.assertNotIn("app.kubernetes.io/managed-by", self.operational)

    def test_controller_ancestors_and_manifest_leaves_fail_closed(self) -> None:
        ancestor_stat = self.task(
            "Inspect every controller repository path component without following links"
        )
        ancestor_assert = self.task(
            "Refuse unsafe or noncanonical controller repository path components"
        )
        leaf_stat = self.task(
            "Inspect the exact committed Namespace manifest leaves without following links"
        )
        leaf_assert = self.task(
            "Refuse unsafe or noncanonical committed Namespace manifest leaves"
        )
        for block in (ancestor_stat, leaf_stat):
            for required in (
                "ansible.builtin.stat:",
                "follow: false",
                "get_checksum: false",
                "delegate_to: localhost",
                "become: false",
            ):
                self.assertIn(required, block)
        for required in (
            "item.stat.isdir",
            "not (item.stat.islnk",
            "item.stat.pw_name == platform_namespace_bootstrap_controller_user",
            "item.stat.gr_name ==",
            "item.stat.mode == '0755'",
            "item.item | ansible.builtin.realpath",
        ):
            self.assertIn(required, ancestor_assert)
        for required in (
            "item.stat.isreg",
            "not (item.stat.islnk",
            "item.stat.pw_name == platform_namespace_bootstrap_controller_user",
            "item.stat.gr_name ==",
            "item.stat.mode == '0644'",
            "item.item | ansible.builtin.realpath",
            "item.item | ansible.builtin.dirname",
            "platform_namespace_bootstrap_repository_root | ansible.builtin.realpath",
            ".startswith(",
        ):
            self.assertIn(required, leaf_assert)

    def test_synthetic_ancestor_symlink_is_noncanonical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sandbox = Path(temporary_directory)
            repository = sandbox / "repository"
            outside = sandbox / "outside"
            repository.mkdir()
            outside_namespace_dir = outside / "platform/namespaces"
            outside_namespace_dir.mkdir(parents=True)
            outside_manifest = outside_namespace_dir / "argocd.yaml"
            outside_manifest.write_text("kind: Namespace\n")
            (repository / "kubernetes").symlink_to(outside, target_is_directory=True)
            expected_manifest = repository / "kubernetes/platform/namespaces/argocd.yaml"

            components = (
                repository,
                repository / "kubernetes",
                repository / "kubernetes/platform",
                repository / "kubernetes/platform/namespaces",
            )
            self.assertTrue(components[1].is_symlink())
            self.assertNotEqual(expected_manifest.absolute(), expected_manifest.resolve())
            self.assertEqual(outside_manifest.resolve(), expected_manifest.resolve())
            self.assertTrue(any(component.is_symlink() for component in components))

    def test_kubeconfig_services_and_foreign_preflight_use_protected_results(self) -> None:
        before_capture = self.task("Capture service facts before Namespace bootstrap")
        after_capture = self.task("Capture service facts after Namespace bootstrap")
        self.assertIn(
            "register: platform_namespace_bootstrap_internal_service_facts_before",
            before_capture,
        )
        self.assertIn(
            "register: platform_namespace_bootstrap_internal_service_facts_after",
            after_capture,
        )
        before_assert = self.task(
            "Require k3s and Tailscale to be running before Namespace bootstrap"
        )
        after_assert = self.task("Require k3s and Tailscale to remain running")
        for block, protected in (
            (before_assert, "platform_namespace_bootstrap_internal_service_facts_before"),
            (after_assert, "platform_namespace_bootstrap_internal_service_facts_after"),
        ):
            self.assertIn(f"{protected}.ansible_facts.services.get(", block)
            self.assertIn("k3s.service", block)
            self.assertIn("tailscaled.service", block)

        kubeconfig = self.task("Require the protected group-scoped kubeconfig contract")
        self.assertIn("platform_namespace_bootstrap_internal_kubeconfig_state", kubeconfig)
        self.assertIn("pw_name == 'root'", kubeconfig)
        self.assertIn("gr_name ==", kubeconfig)
        self.assertIn("'k3s-admin'", kubeconfig)
        self.assertIn("mode == '0640'", kubeconfig)
        prestate = self.task("Query only the exact platform Namespace pre-state")
        self.assertIn("register: platform_namespace_bootstrap_internal_prestate", prestate)
        refusal = self.task("Refuse a foreign existing platform Namespace")
        self.assertIn("platform_namespace_bootstrap_internal_prestate.results", refusal)
        for required in (
            "item.resources | length in [0, 1]",
            "item.resources | length == 0 or",
            "app.kubernetes.io/part-of",
            "cristex.io/bootstrap-writer",
            "cristex.io/desired-owner",
            "refusing silent adoption",
        ):
            self.assertIn(required, refusal)

    def test_apply_is_present_only_and_live_poststate_is_exact(self) -> None:
        apply = self.task("Create or reconcile only the approved platform Namespaces")
        for required in (
            "kubernetes.core.k8s:",
            "state: present",
            'definition: "{{ item }}"',
            "kubeconfig: /etc/rancher/k3s/k3s.yaml",
            "wait: true",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_ENTRYPOINT",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_TOKEN",
            "CRISTEXWEB_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE",
            "':entrypoint'",
            "platform_namespace_bootstrap_approved | bool",
            "platform_namespace_bootstrap_state == 'present'",
            "ansible_diff_mode",
            "(ansible_limit | default('')) == 'crtxweb'",
            "ansible_play_hosts_all | length == 1",
            "item.keys() | list | sort == ['apiVersion', 'kind', 'metadata']",
            "item.apiVersion == 'v1'",
            "item.kind == 'Namespace'",
            "item.metadata.keys() | list | sort == ['labels', 'name']",
            "item.metadata.name in ['argocd', 'platform-edge']",
            "item.metadata.labels | length == 3",
            "kubernetes/platform/namespaces/argocd.yaml",
            "kubernetes/platform/namespaces/platform-edge.yaml",
        ):
            self.assertIn(required, apply)
        self.assertEqual(3, apply.count("lookup('ansible.builtin.file'"))
        self.assertNotIn("platform_namespace_bootstrap_internal_manifests", apply)
        for forbidden in ("state: absent", "force: true", "delete_all:"):
            self.assertNotIn(forbidden, self.tasks)
        self.assertNotIn("no_log: true", apply)
        self.assertNotIn("diff: false", apply)
        postquery = self.task(
            "Requery only the exact platform Namespaces after live bootstrap"
        )
        self.assertIn("register: platform_namespace_bootstrap_internal_poststate", postquery)
        self.assertIn("when: not ansible_check_mode", postquery)
        verify = self.task(
            "Verify exact Namespace identity and pending Argo CD desired ownership"
        )
        for required in (
            "platform_namespace_bootstrap_internal_poststate.results",
            "item.resources | length == 1",
            "item.resources[0].metadata.name == item.item.metadata.name",
            "app.kubernetes.io/part-of",
            "cristex.io/bootstrap-writer",
            "cristex.io/desired-owner",
            "status.phase == 'Active'",
            "when: not ansible_check_mode",
        ):
            self.assertIn(required, verify)

    def test_every_executable_role_file_has_no_scope_escape(self) -> None:
        executable_files = list((ROLE / "tasks").rglob("*.yml"))
        self.assertEqual([ROLE / "tasks/main.yml"], executable_files)
        for path in executable_files:
            text = path.read_text()
            self.assertEqual(1, text.count("kubernetes.core.k8s:"))
            self.assertEqual(2, text.count("kubernetes.core.k8s_info:"))
            for forbidden in (
                "ansible.builtin.shell:",
                "ansible.builtin.command:",
                "ansible.builtin.raw:",
                "ansible.builtin.script:",
                "ansible.builtin.include_tasks:",
                "ansible.builtin.import_tasks:",
                "ansible.builtin.include_role:",
                "ansible.builtin.import_role:",
                "kind: Secret",
                "kind: ConfigMap",
                "kind: Deployment",
                "kind: Service",
                "kind: Ingress",
                "kind: PersistentVolumeClaim",
                "kind: all",
                "state: restarted",
                "state: stopped",
                "propagation_policy:",
            ):
                self.assertNotIn(forbidden, text, (path, forbidden))
            self.assertEqual(2, text.count("kind: Namespace"))

    def test_namespace_bootstrap_is_a_pre_stage_4_bounded_exception(self) -> None:
        architecture = (ROOT / "architecture-plan.md").read_text()
        exception_heading = (
            "### Pre-Stage-4 — bounded platform Namespace bootstrap exception"
        )
        stage_heading = "### Stage 4 — minimal GitOps and secrets bootstrap"
        self.assertLess(
            architecture.index(exception_heading),
            architecture.index(stage_heading),
        )
        exception = architecture.split(exception_heading, 1)[1].split(
            stage_heading, 1
        )[0]
        for required in (
            "`ansible/bin/bootstrap-platform-namespaces check`",
            "`argocd` and `platform-edge` Namespace manifests",
            "`state:\n  present`",
            "No deletion or other persistent\n  Kubernetes kind is authorized",
            "separately approved wrapper apply passed",
            "during the separately approved second wrapper checkpoint",
            "`ok=21 changed=0 unreachable=0 failed=0 skipped=0`",
            "the exact check, first apply, and idempotence checkpoints are complete",
            "Ansible remains the bootstrap writer",
            "a label alone is not a handoff",
            "this exception does not waive the Stage 4 entry gates",
            "does not\n  authorize Argo CD, Infisical, cloudflared, or any other "
            "persistent Kubernetes\n  object",
        ):
            self.assertIn(required, exception)

        stage = architecture.split(stage_heading, 1)[1].split(
            "### Stage 5 — isolation and shared data", 1
        )[0]
        for required in (
            "pinned component versions",
            "human-reviewed target kubelet-version evidence",
            "verified Kubernetes compatibility",
            "an approved secret-zero procedure",
            "only after every Stage 4 entry gate passes",
        ):
            self.assertIn(required, stage)
        self.assertNotIn(
            "first create or reconcile only the committed `argocd` and `platform-edge`",
            stage,
        )

        tasks = (
            ROOT / "specs" / "k3s-iac-foundation" / "tasks.md"
        ).read_text()
        tasks_exception_heading = (
            "## Pre-Stage-4 — bounded platform Namespace bootstrap exception"
        )
        tasks_stage_heading = "## Stage 4 — GitOps and secret bootstrap"
        self.assertLess(
            tasks.index(tasks_exception_heading),
            tasks.index(tasks_stage_heading),
        )
        tasks_exception = tasks.split(tasks_exception_heading, 1)[1].split(
            tasks_stage_heading, 1
        )[0]
        normalized_exception = " ".join(tasks_exception.split())
        for required in (
            "Commit exact `argocd` and `platform-edge` Namespace source",
            "`state: present`, no-delete Ansible bootstrap exception",
            "separate human approval for only `ansible/bin/bootstrap-platform-namespaces check`",
            "inspect its complete result",
            "predicted exactly `argocd` and `platform-edge`, and made no mutation",
            "separate human approval for the first "
            "`ansible/bin/bootstrap-platform-namespaces apply`",
            "reconciled exactly the two reviewed Namespaces",
            "separate human approval for a second "
            "`ansible/bin/bootstrap-platform-namespaces apply`",
            "require `changed=0`",
            "initial invocation stopped before service preflight and Kubernetes reconciliation",
            "the retry passed at `ok=21 changed=0 unreachable=0 failed=0 skipped=0`",
            "Check mode, first apply, and idempotence passed",
            "bounded exception is complete and closed",
            "authorize no further bootstrap run and waive no Stage 4 entry gate",
        ):
            self.assertIn(required, normalized_exception)

        tasks_stage = tasks.split(tasks_stage_heading, 1)[1].split(
            "## Stage 5 — namespaces, policy, and shared data", 1
        )[0]
        normalized_tasks_stage = " ".join(tasks_stage.split())
        for required in (
            "Record public Argo CD chart",
            "Record official cloudflared release/source/image",
            "Select Infisical Operator `v0.11.7` only as an offline source baseline",
        ):
            self.assertIn(required, normalized_tasks_stage)
        for stale in (
            "Commit exact `argocd` and `platform-edge` Namespace source",
            "`ansible/bin/bootstrap-platform-namespaces check`",
            "`ansible/bin/bootstrap-platform-namespaces apply`",
        ):
            self.assertNotIn(stale, normalized_tasks_stage)

        authority = " ".join((ROOT / "AGENTS.md").read_text().split())
        for required in (
            "This root `AGENTS.md` is authoritative for the entire repository",
            "One additional bounded bootstrap exception may create or reconcile only "
            "the committed `argocd` and `platform-edge` Namespaces with `state: present`",
            "refuses foreign existing namespaces and has no deletion path",
            "Its only authorized entrypoint is the committed non-passthrough wrapper",
            "direct playbook invocation and task-skipping/selection controls are forbidden",
            "a label alone is not a handoff",
            "That completed exception authorizes no other persistent Kubernetes object",
            "Ansible is selected as the bounded bootstrap installer for future exact "
            "foundational Namespaces",
            "Each component requires its own exact source closure and separate "
            "check/apply/idempotence approvals",
            "Dual reconciliation is forbidden",
        ):
            self.assertIn(required, authority)

    def test_wrapper_check_evidence_is_preserved_after_first_apply(self) -> None:
        recap = "ok=19 changed=1 unreachable=0 failed=0 skipped=2"
        for relative in (
            "README.md",
            "ansible/README.md",
            "architecture-plan.md",
            "specs/k3s-iac-foundation/brief.md",
            "specs/k3s-iac-foundation/status.md",
            "specs/k3s-iac-foundation/tasks.md",
            "specs/k3s-iac-foundation/testcases.md",
        ):
            self.assertIn(recap, (ROOT / relative).read_text(), relative)

        testcases = (ROOT / "specs/k3s-iac-foundation/testcases.md").read_text()
        for required in (
            "Labels: app.kubernetes.io/part-of=cristex-platform; cristex.io/bootstrap-writer=ansible; cristex.io/desired-owner=argocd",
            "Prediction: changed item=argocd; changed item=platform-edge",
            "Live post-state query and identity verification: skipped by design in check mode",
            "Namespace or other Kubernetes-object mutation: none",
            "At this historical checkpoint the check did not approve the first apply;\nboth applies were **NOT RUN**",
            "later separately approved first-apply and\nidempotence evidence below supersedes both historical execution boundaries",
        ):
            self.assertIn(required, testcases)

    def test_idempotence_evidence_passes_after_pre_reconciliation_failure(self) -> None:
        first_apply_recap = "ok=21 changed=1 unreachable=0 failed=0 skipped=0"
        failed_recap = "ok=10 changed=0 unreachable=0 failed=1 skipped=0"
        idempotence_recap = "ok=21 changed=0 unreachable=0 failed=0 skipped=0"
        evidence_paths = (
            "README.md",
            "ansible/README.md",
            "architecture-plan.md",
            "specs/k3s-iac-foundation/brief.md",
            "specs/k3s-iac-foundation/status.md",
            "specs/k3s-iac-foundation/tasks.md",
            "specs/k3s-iac-foundation/testcases.md",
        )
        for relative in evidence_paths:
            evidence = (ROOT / relative).read_text()
            self.assertIn(first_apply_recap, evidence, relative)
            self.assertIn(failed_recap, evidence, relative)
            self.assertIn(idempotence_recap, evidence, relative)

        testcases = (ROOT / "specs/k3s-iac-foundation/testcases.md").read_text()
        authoritative_paths = (
            "AGENTS.md",
            "README.md",
            "ansible/README.md",
            "architecture-plan.md",
            "specs/k3s-iac-foundation/brief.md",
            "specs/k3s-iac-foundation/manual-qa.md",
            "specs/k3s-iac-foundation/requirements.md",
            "specs/k3s-iac-foundation/status.md",
            "specs/k3s-iac-foundation/tasks.md",
            "specs/k3s-iac-foundation/testcases.md",
        )
        for relative in authoritative_paths:
            self.assertNotRegex((ROOT / relative).read_text(), r"/Users/[^/\s]+/")
        self.assertRegex(
            testcases,
            r"(?m)^\| KIF-NS-02 .* \| PASS — .*first apply passed at ok=21/changed=1/unreachable=0/failed=0/skipped=0.*initial invocation.*ok=10/changed=0/unreachable=0/failed=1/skipped=0.*retry passed at ok=21/changed=0/unreachable=0/failed=0/skipped=0",
        )
        for required in (
            "Failure boundary: before service preflight and Kubernetes reconciliation",
            "Namespace or other Kubernetes-object mutation: none",
            "Idempotence proof from this attempt: none",
            "Reconciliation: ok item=argocd; ok item=platform-edge",
            "Post-state requery: ok for both exact items",
            "Exact identity, all three labels, and status.phase=Active assertions: ok for both exact items under no_log",
            "k3s and tailscaled service assertions before/after: PASS",
            "Changed/skipped/failed/unreachable tasks: none",
            "Other persistent kind authorized or changed: none",
            "The supplied verbose output included controller-local identity and stat/path\nmetadata. Those values, the password, inventory, kubeconfig, host/address data, and\nraw output are deliberately not copied into Git",
            "The exact check,\nfirst apply, and idempotence checkpoints are complete",
        ):
            self.assertIn(required, testcases)

        tasks = (ROOT / "specs/k3s-iac-foundation/tasks.md").read_text()
        normalized_tasks = " ".join(tasks.split())
        self.assertIn(
            "- [x] After accepting the check result, obtain separate human approval "
            "for the first `ansible/bin/bootstrap-platform-namespaces apply`",
            normalized_tasks,
        )
        self.assertIn(
            "- [x] Verify exact identity, labels, Active phase, and k3s/Tailscale service health",
            normalized_tasks,
        )
        self.assertIn(
            "- [x] Obtain separate human approval for a second "
            "`ansible/bin/bootstrap-platform-namespaces apply` and require `changed=0`",
            normalized_tasks,
        )
        self.assertIn("bounded exception is complete and closed", normalized_tasks)
        self.assertIn("authorize no further bootstrap run", normalized_tasks)

        authority = (ROOT / "AGENTS.md").read_text()
        self.assertIn("separately approved first apply created exactly those two Namespaces", authority)
        self.assertIn("retry passed at `changed=0`", authority)
        normalized_authority = re.sub(
            r"[*_`\s]+",
            " ",
            "\n".join((ROOT / path).read_text() for path in authoritative_paths),
        )
        self.assertNotRegex(
            normalized_authority,
            r"(?i)(?:second )?idempotence apply remains (?:not run|unrun|pending)",
        )

    def test_authoritative_ownership_wording_has_no_stale_absolute_claims(self) -> None:
        authoritative = "\n".join(
            path.read_text()
            for path in (
                ROOT / "README.md",
                ANSIBLE / "README.md",
                ROOT / "architecture-plan.md",
                ROOT / "specs/k3s-iac-foundation/status.md",
            )
        )
        for stale in (
            "Argo CD remains the sole owner of persistent Kubernetes desired state",
            "Argo CD remains the persistent Kubernetes-object owner",
            "Argo CD for all in-cluster desired state",
            "Argo CD is the intended persistent Kubernetes reconciler",
            "Exact committed Namespace source now defines only `argocd` and `platform-edge`",
        ):
            self.assertNotIn(stale, authoritative)
        for required in (
            "Ansible as bootstrap writer",
            "future desired owner",
            "label alone is not a handoff",
            "Argo CD is the intended namespaced\nreconciler only for exact object sets",
            "Ansible retains privileged lifecycle ownership",
        ):
            self.assertIn(required, authoritative)

    def test_shared_services_source_change_is_offline_only(self) -> None:
        kubernetes_tasks = (
            ANSIBLE / "roles/read_only_discovery/tasks/kubernetes.yml"
        ).read_text()
        self.assertIn("shared_services_persistent_volume_claims", kubernetes_tasks)
        self.assertIn("namespace: shared-services", kubernetes_tasks)
        self.assertNotIn("shared_data_persistent_volume_claims", kubernetes_tasks)
        self.assertNotIn("namespace: shared-data", kubernetes_tasks)
        self.assertEqual(5, kubernetes_tasks.count("kind: PersistentVolumeClaim"))


if __name__ == "__main__":
    unittest.main()
