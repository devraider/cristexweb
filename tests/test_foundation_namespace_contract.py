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
ROLE = ANSIBLE / "roles/foundation_namespace_bootstrap"
ENTRYPOINT = ANSIBLE / "bin/bootstrap-foundation-namespaces"
TASK_START_FIXTURE = ROOT / "tests/reject_foundation_namespace_task_start.sh"
CLEAN_CONTROLLER_FIXTURE = ROOT / "tests/validate_foundation_namespace_clean_controller.sh"


class FoundationNamespaceBootstrapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.playbook_path = ANSIBLE / "playbooks/bootstrap_foundation_namespaces.yml"
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

    def test_current_docs_record_first_apply_without_inferring_components(self) -> None:
        expected_fragments = {
            ROOT / "README.md": "completed exact `shared-services` Namespace check/first-apply/idempotence evidence",
            ANSIBLE / "README.md": "check, separately approved first apply, and separately approved idempotence all passed",
            ROOT / "architecture-plan.md": "wrapper check, separately approved first apply, and separately approved idempotence passed",
            ROOT / "runbooks/keycloak-oidc-bootstrap-design.md": "check and separately approved first apply/idempotence passed",
            ROOT / "runbooks/shared-rabbitmq-architecture.md": "approved first apply/idempotence passed",
            ROOT / "specs/k3s-iac-foundation/requirements.md": "check, separately approved first apply, and separately approved idempotence passed",
        }
        for path, fragment in expected_fragments.items():
            text = path.read_text()
            normalized = " ".join(text.split())
            self.assertIn(fragment, normalized, path)
            self.assertIn("idempotence", normalized, path)
            self.assertIn("changed=0", normalized, path)
        joined = "\n".join(path.read_text() for path in expected_fragments)
        for stale in (
            "none of its runtime checkpoints has run",
            "wrapper check, first apply, and idempotence apply are\n  all **NOT RUN**",
            "Its check, first apply, and idempotence checkpoints remain\n**NOT RUN**",
            "`shared-services` check/apply/idempotence remains a\nseparate NOT RUN approval sequence",
            "deployable-but-not-run exact present-only bootstrap for `shared-services`",
            "present-only bootstrap is implemented but not run for\n`shared-services`",
            "foundation Namespace source/exception is\nimplemented but not run",
            "foundation Namespace\nsource is implemented, while its runtime checkpoints",
            "deployable-but-not-run\n[foundation Namespace bootstrap]",
            "Idempotence is **NOT RUN**",
            "idempotence remains separately approved and **NOT RUN**",
            "pending idempotence gate",
        ):
            self.assertNotIn(stale, joined)

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
            "applications/namespaces/cristexhub-dev.yaml": """---
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
                "foundation-namespace-bootstrap.md",
                (ROOT / relative).read_text(),
                relative,
            )

    def test_exact_playbook_and_role_file_closure(self) -> None:
        self.assertEqual(
            """---
- name: Bootstrap the approved persistent foundation Namespaces
  hosts: k3s_servers
  gather_facts: false
  become: true
  any_errors_fatal: true
  serial: 1

  roles:
    - role: foundation_namespace_bootstrap
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
                ANSIBLE / "bin/bootstrap-platform-namespaces",
                ENTRYPOINT,
                ANSIBLE / "bin/bootstrap-cristexhub-dev-namespace",
                ANSIBLE / "bin/bootstrap-infisical-operator",
                ANSIBLE / "bin/bootstrap-infisical-proxy-secrets",
                ANSIBLE / "bin/bootstrap-infisical-argocd-secrets",
                ANSIBLE / "bin/bootstrap-infisical-database-secrets",
                ANSIBLE / "bin/bootstrap-argocd",
                ANSIBLE / "bin/bootstrap-mongodb",
                ANSIBLE / "bin/bootstrap-postgresql",
                ANSIBLE / "bin/bootstrap-keycloak",
                ANSIBLE / "bin/bootstrap-cloudnative-pg",
                ANSIBLE / "bin/bootstrap-cloudnative-pg-cluster",
                ANSIBLE / "bin/install-backup-dependencies",
                ANSIBLE / "bin/configure-postgresql-keycloak-backup",
                ANSIBLE / "bin/configure-mongodb-shared-backup",
                ANSIBLE / "bin/provision-shared-postgresql",
                ANSIBLE / "bin/provision-shared-mongodb",
                ANSIBLE / "bin/install-rclone",
                ANSIBLE / "bin/transfer-infisical-proxy-recovery",
                ANSIBLE / "bin/preflight-k3s-datastore",
                ANSIBLE / "bin/seed-infisical-universal-auth",
                ANSIBLE / "bin/upload-infisical-bootstrap-values",
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
            "bootstrap_foundation_namespaces.yml --syntax-check",
            "wrapper-equivalent clean controller environment",
        ):
            self.assertIn(required, clean_controller_fixture)
        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            TASK_START_FIXTURE.stat().st_mode
            & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        for required in (
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_TOKEN",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE",
            "/usr/bin/openssl rand -hex 32",
            "--start-at-task",
            "Create or reconcile only the approved foundation Namespaces",
            "item=shared-services",
            "status -ne 0",
            "forged wrapper-format attestation cannot bypass the protected in-run preflight binding",
        ):
            self.assertIn(required, task_start_fixture)

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
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_TOKEN=$attestation_token",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE=$attestation_file",
            "/usr/bin/mktemp",
            "/usr/bin/openssl rand -hex 32",
            "trap cleanup EXIT HUP INT TERM",
            'ANSIBLE_CONFIG=$PWD/ansible.cfg',
            "--diff",
            "--limit crtxweb",
            "foundation_namespace_bootstrap_approved=true",
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
            ("check", "--start-at-task", "Create or reconcile only the approved foundation Namespaces"),
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
        guard_name = "Reject externally supplied foundation Namespace internal variables"
        self.assertEqual(guard_name, next(iter(self.task_blocks)))
        guard = self.task(guard_name)
        protected = (
            "foundation_namespace_bootstrap_internal_attestation_state",
            "foundation_namespace_bootstrap_internal_controller_path_states",
            "foundation_namespace_bootstrap_internal_manifest_path_states",
            "foundation_namespace_bootstrap_internal_manifests",
            "foundation_namespace_bootstrap_internal_service_facts_before",
            "foundation_namespace_bootstrap_internal_kubeconfig_state",
            "foundation_namespace_bootstrap_internal_prestate",
            "foundation_namespace_bootstrap_internal_preflight_binding",
            "foundation_namespace_bootstrap_internal_poststate",
            "foundation_namespace_bootstrap_internal_service_facts_after",
        )
        self.assertIn("item not in vars", guard)
        self.assertIn("INTERNAL_VARIABLE_GUARD", guard)
        for name in protected:
            self.assertIn(name, guard)
        later_tasks = self.tasks[self.tasks.index("- name: Require the foundation") :]
        for name in protected:
            self.assertIn(name, later_tasks)

        fixture = (ROOT / "tests/reject_foundation_namespace_internal_injection.yml").read_text()
        self.assertIn("hosts: localhost", fixture)
        self.assertIn("connection: local", fixture)
        self.assertIn("name: foundation_namespace_bootstrap", fixture)
        self.assertIn(guard_name, fixture)
        self.assertIn("INTERNAL_VARIABLE_GUARD", fixture)
        self.assertNotIn("kubernetes.core", fixture)

    def test_public_inputs_are_pinned_and_manifests_load_controller_side(self) -> None:
        approval = self.task("Require the foundation Namespace bootstrap approval contract")
        for required in (
            "foundation_namespace_bootstrap_approved | bool",
            "foundation_namespace_bootstrap_state == 'present'",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ENTRYPOINT",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_TOKEN",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE",
            "ansible_diff_mode",
            "(ansible_limit | default('')) == 'crtxweb'",
            "ansible_play_hosts_all | length == 1",
            "foundation_namespace_bootstrap_kubeconfig == '/etc/rancher/k3s/k3s.yaml'",
            "foundation_namespace_bootstrap_controller_user == lookup('ansible.builtin.env', 'USER')",
            "foundation_namespace_bootstrap_repository_root ==",
            "foundation_namespace_bootstrap_controller_path_components ==",
            "foundation_namespace_bootstrap_manifest_paths ==",
            "kubernetes/platform/namespaces/shared-services.yaml",
        ):
            self.assertIn(required, self.operational + approval)

        attestation_stat = self.task(
            "Inspect the ephemeral Namespace bootstrap entrypoint attestation"
        )
        for required in (
            "ansible.builtin.stat:",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE",
            "follow: false",
            "register: foundation_namespace_bootstrap_internal_attestation_state",
            "delegate_to: localhost",
            "become: false",
            "no_log: true",
        ):
            self.assertIn(required, attestation_stat)
        attestation_assert = self.task(
            "Require the private single-run Namespace bootstrap attestation"
        )
        for required in (
            "foundation_namespace_bootstrap_internal_attestation_state",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_TOKEN",
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
            "foundation_namespace_bootstrap_manifest_paths",
            "foundation_namespace_bootstrap_internal_manifests",
            "delegate_to: localhost",
            "become: false",
            "changed_when: false",
        ):
            self.assertIn(required, load)
        contract = self.task("Require the exact bounded Namespace manifest contract")
        for required in (
            "['shared-services']",
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
            "item.stat.pw_name == foundation_namespace_bootstrap_controller_user",
            "item.stat.gr_name ==",
            "item.stat.mode == '0755'",
            "item.item | ansible.builtin.realpath",
        ):
            self.assertIn(required, ancestor_assert)
        for required in (
            "item.stat.isreg",
            "not (item.stat.islnk",
            "item.stat.pw_name == foundation_namespace_bootstrap_controller_user",
            "item.stat.gr_name ==",
            "item.stat.mode == '0644'",
            "item.item | ansible.builtin.realpath",
            "item.item | ansible.builtin.dirname",
            "foundation_namespace_bootstrap_repository_root | ansible.builtin.realpath",
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
            outside_manifest = outside_namespace_dir / "shared-services.yaml"
            outside_manifest.write_text("kind: Namespace\n")
            (repository / "kubernetes").symlink_to(outside, target_is_directory=True)
            expected_manifest = repository / "kubernetes/platform/namespaces/shared-services.yaml"

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
            "register: foundation_namespace_bootstrap_internal_service_facts_before",
            before_capture,
        )
        self.assertIn(
            "register: foundation_namespace_bootstrap_internal_service_facts_after",
            after_capture,
        )
        before_assert = self.task(
            "Require k3s and Tailscale to be running before Namespace bootstrap"
        )
        after_assert = self.task("Require k3s and Tailscale to remain running")
        for block, protected in (
            (before_assert, "foundation_namespace_bootstrap_internal_service_facts_before"),
            (after_assert, "foundation_namespace_bootstrap_internal_service_facts_after"),
        ):
            self.assertIn(f"{protected}.ansible_facts.services.get(", block)
            self.assertIn("k3s.service", block)
            self.assertIn("tailscaled.service", block)

        kubeconfig = self.task("Require the protected group-scoped kubeconfig contract")
        self.assertIn("foundation_namespace_bootstrap_internal_kubeconfig_state", kubeconfig)
        self.assertIn("pw_name == 'root'", kubeconfig)
        self.assertIn("gr_name ==", kubeconfig)
        self.assertIn("'k3s-admin'", kubeconfig)
        self.assertIn("mode == '0640'", kubeconfig)
        prestate = self.task("Query only the exact foundation Namespace pre-state")
        self.assertIn("register: foundation_namespace_bootstrap_internal_prestate", prestate)
        refusal = self.task("Refuse a foreign existing foundation Namespace")
        self.assertIn("foundation_namespace_bootstrap_internal_prestate.results", refusal)
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
        binding = self.task("Bind the protected foundation Namespace preflight to this run")
        for required in (
            "ansible.builtin.set_fact:",
            "foundation_namespace_bootstrap_internal_preflight_binding",
            "attestation_sha256",
            "foundation_namespace_bootstrap_internal_manifests",
            "foundation_namespace_bootstrap_internal_prestate.results",
            "foundation_namespace_bootstrap_internal_controller_path_states.results",
            "foundation_namespace_bootstrap_internal_manifest_path_states.results",
            "kubeconfig_contract: true",
            "service_contract: true",
            "changed_when: false",
            "no_log: true",
        ):
            self.assertIn(required, binding)

        apply = self.task("Create or reconcile only the approved foundation Namespaces")
        for required in (
            "kubernetes.core.k8s:",
            "state: present",
            'definition: "{{ item }}"',
            "kubeconfig: /etc/rancher/k3s/k3s.yaml",
            "wait: true",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ENTRYPOINT",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_TOKEN",
            "CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE",
            "':entrypoint'",
            "foundation_namespace_bootstrap_internal_preflight_binding is defined",
            "foundation_namespace_bootstrap_internal_preflight_binding.attestation_sha256",
            "foundation_namespace_bootstrap_internal_preflight_binding.manifest_names",
            "foundation_namespace_bootstrap_internal_preflight_binding.prestate_names",
            "foundation_namespace_bootstrap_internal_preflight_binding.controller_path_count == 4",
            "foundation_namespace_bootstrap_internal_preflight_binding.manifest_path_count == 1",
            "foundation_namespace_bootstrap_approved | bool",
            "foundation_namespace_bootstrap_state == 'present'",
            "ansible_diff_mode",
            "(ansible_limit | default('')) == 'crtxweb'",
            "ansible_play_hosts_all | length == 1",
            "item.keys() | list | sort == ['apiVersion', 'kind', 'metadata']",
            "item.apiVersion == 'v1'",
            "item.kind == 'Namespace'",
            "item.metadata.keys() | list | sort == ['labels', 'name']",
            "item.metadata.name == 'shared-services'",
            "item.metadata.labels | length == 3",
            "kubernetes/platform/namespaces/shared-services.yaml",
        ):
            self.assertIn(required, apply)
        self.assertEqual(2, apply.count("lookup('ansible.builtin.file'"))
        self.assertNotIn("foundation_namespace_bootstrap_internal_manifests", apply)
        for forbidden in ("state: absent", "force: true", "delete_all:"):
            self.assertNotIn(forbidden, self.tasks)
        self.assertNotIn("no_log: true", apply)
        self.assertNotIn("diff: false", apply)
        postquery = self.task(
            "Requery only the exact foundation Namespaces after live bootstrap"
        )
        self.assertIn("register: foundation_namespace_bootstrap_internal_poststate", postquery)
        self.assertIn("when: not ansible_check_mode", postquery)
        verify = self.task(
            "Verify exact Namespace identity and pending Argo CD desired ownership"
        )
        for required in (
            "foundation_namespace_bootstrap_internal_poststate.results",
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



if __name__ == "__main__":
    unittest.main()
