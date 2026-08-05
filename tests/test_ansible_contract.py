from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"


class AnsibleLayoutTests(unittest.TestCase):
    def test_operational_python_collector_is_removed(self) -> None:
        self.assertFalse((ROOT / "tools" / "collect_inventory.py").exists())
        self.assertFalse((ROOT / "tools" / "__init__.py").exists())
        self.assertFalse((ROOT / "tests" / "test_collect_inventory.py").exists())
        source_python = [
            path.relative_to(ROOT)
            for path in ROOT.rglob("*.py")
            if ".git" not in path.parts
            and ".pi-subagents" not in path.parts
            and ".venv" not in path.parts
            and ".ansible" not in path.parts
            and "__pycache__" not in path.parts
        ]
        self.assertTrue(source_python)
        self.assertTrue(all(path.parts[0] == "tests" for path in source_python), source_python)

    def test_minimal_ansible_layout_exists(self) -> None:
        required = [
            "ansible.cfg",
            "requirements.yml",
            "README.md",
            "inventory/hosts.yml",
            "playbooks/discover.yml",
            "playbooks/bootstrap_dependencies.yml",
            "playbooks/configure_k3s_admin_access.yml",
            "roles/read_only_discovery/defaults/main.yml",
            "roles/read_only_discovery/tasks/main.yml",
            "roles/read_only_discovery/tasks/host.yml",
            "roles/read_only_discovery/tasks/kubernetes.yml",
            "roles/read_only_discovery/tasks/report.yml",
            "roles/read_only_discovery/templates/report.json.j2",
        ]
        self.assertEqual([], [path for path in required if not (ANSIBLE / path).is_file()])
        actual = {
            str(path.relative_to(ANSIBLE))
            for path in ANSIBLE.rglob("*")
            if path.is_file() and ".ansible" not in path.parts
        }
        self.assertEqual(set(required), actual)

    def test_uv_controller_environment_is_pinned_and_ignored(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())
        self.assertIn("ansible-core==2.19.0", project["project"]["dependencies"])
        self.assertIn("ansible-lint==26.6.0", project["dependency-groups"]["dev"])
        self.assertTrue((ROOT / "uv.lock").is_file())
        ignore_rules = (ROOT / ".gitignore").read_text()
        self.assertIn(".venv/", ignore_rules)
        self.assertIn(".ansible/", ignore_rules)
        config = (ANSIBLE / "ansible.cfg").read_text()
        self.assertIn("collections_path = .ansible/collections", config)

    def test_dependency_bootstrap_is_bounded_and_approved(self) -> None:
        playbook = (ANSIBLE / "playbooks/bootstrap_dependencies.yml").read_text()
        for required in (
            "hosts: k3s_servers",
            "become: true",
            "ansible_dependency_bootstrap_approved: false",
            "ansible_dependency_bootstrap_approved | bool",
            "ansible_limit",
            "ansible_play_hosts_all",
            "ansible.builtin.apt:",
            "- python3-jsonpatch",
            "- python3-kubernetes",
            "state: present",
            "update_cache: false",
        ):
            self.assertIn(required, playbook)
        self.assertEqual(1, playbook.count("ansible.builtin.apt:"))
        package_block = re.search(
            r"ansible\.builtin\.apt:\n\s+name:\n(?P<items>(?:\s+- [a-z0-9-]+\n)+)\s+state: present",
            playbook,
        )
        self.assertIsNotNone(package_block)
        packages = re.findall(r"^\s+- ([a-z0-9-]+)$", package_block.group("items"), re.MULTILINE)
        self.assertEqual(["python3-jsonpatch", "python3-kubernetes"], packages)
        for forbidden in (
            "ansible.builtin.shell:",
            "ansible.builtin.command:",
            "state: latest",
            "upgrade:",
            "update_cache: true",
        ):
            self.assertNotIn(forbidden, playbook)

    def test_k3s_admin_access_is_group_scoped_and_approved(self) -> None:
        playbook = (ANSIBLE / "playbooks/configure_k3s_admin_access.yml").read_text()
        for required in (
            "k3s_admin_access_approved: false",
            "k3s_admin_access_approved | bool",
            "ansible_limit",
            "ansible_play_hosts_all",
            "k3s_admin_user is defined",
            "(ansible_facts.getent_passwd[k3s_admin_user][1] | int) != 0",
            "k3s_admin_group: k3s-admin",
            "k3s_admin_group == 'k3s-admin'",
            "k3s_admin_existing_members | difference([k3s_admin_user])",
            "Reject unexpected primary members of the dedicated group",
            "item.value[2] | string",
            "Reject an unsafe existing dedicated group GID",
            "Reject pre-existing numeric aliases of the dedicated group",
            "Refresh group metadata before granting access",
            "Verify the dedicated group numeric identity before granting access",
            "Verify no numeric group aliases before granting access",
            "Verify no unexpected primary members before granting access",
            "item.value[1] | string",
            "ansible.builtin.group:",
            "ansible.builtin.user:",
            "append: true",
            "create_home: false",
            "not ansible_check_mode or (k3s_admin_group_preexists | bool)",
            "Refresh dedicated group membership before configuring access",
            "Verify exclusive dedicated group membership before configuring access",
            "Predict membership change when the group is new",
            "config.yaml.pre-admin-access",
            "Refuse an unsafe existing k3s configuration path",
            "Refuse an unsafe existing rollback destination",
            "islnk",
            "remote_src: true",
            "force: false",
            "write-kubeconfig-group",
            "write-kubeconfig-mode",
            "'0640'",
            "ansible.builtin.service:",
            "state: restarted",
            "k3s_admin_kubeconfig.stat.mode == '0640'",
            "retries: 15",
            "delay: 2",
        ):
            self.assertIn(required, playbook)
        self.assertEqual(2, playbook.count("ansible.builtin.lineinfile:"))
        self.assertEqual(2, playbook.count("ansible.builtin.copy:"))
        self.assertLess(
            playbook.index("Create the restricted k3s administrator group"),
            playbook.index("Refresh group metadata before granting access"),
        )
        self.assertLess(
            playbook.index("Refresh group metadata before granting access"),
            playbook.index("Verify the dedicated group numeric identity before granting access"),
        )
        self.assertLess(
            playbook.index("Verify the dedicated group numeric identity before granting access"),
            playbook.index("Verify no numeric group aliases before granting access"),
        )
        self.assertLess(
            playbook.index("Verify no numeric group aliases before granting access"),
            playbook.index("Verify no unexpected primary members before granting access"),
        )
        self.assertLess(
            playbook.index("Verify no unexpected primary members before granting access"),
            playbook.index("Add the approved user to the k3s administrator group"),
        )
        self.assertLess(
            playbook.index("Add the approved user to the k3s administrator group"),
            playbook.index("Refresh dedicated group membership before configuring access"),
        )
        self.assertLess(
            playbook.index("Refresh dedicated group membership before configuring access"),
            playbook.index("Verify exclusive dedicated group membership before configuring access"),
        )
        self.assertLess(
            playbook.index("Verify exclusive dedicated group membership before configuring access"),
            playbook.index("Configure the kubeconfig group"),
        )
        line_tasks = re.findall(
            r"- name: Configure the kubeconfig .*?(?=\n    - name:)",
            playbook,
            re.DOTALL,
        )
        self.assertEqual(2, len(line_tasks))
        for task in line_tasks:
            self.assertIn("path: /etc/rancher/k3s/config.yaml", task)
            self.assertIn("diff: false", task)
            self.assertIn("no_log: true", task)
            self.assertIn("notify: Restart k3s", task)
        for forbidden in (
            'write-kubeconfig-mode: "0644"',
            "name: paul",
            "ansible.builtin.shell:",
            "ansible.builtin.command:",
            "k3s_admin_group: root",
            "k3s_admin_group: sudo",
        ):
            self.assertNotIn(forbidden, playbook)

    def test_inventory_contains_only_the_neutral_ssh_alias(self) -> None:
        text = (ANSIBLE / "inventory/hosts.yml").read_text()
        self.assertIn("crtxweb:", text)
        for forbidden in ("ansible_host", "ansible_user", "ansible_password", "ansible_become", "private_key"):
            self.assertNotIn(forbidden, text)
        self.assertNotRegex(text, r"\b(?:10|127|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.")


class AnsibleSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.task_text = "\n".join(path.read_text() for path in sorted((ANSIBLE / "roles/read_only_discovery/tasks").glob("*.yml")))
        cls.all_ansible_text = "\n".join(
            path.read_text()
            for path in sorted(ANSIBLE.rglob("*"))
            if path.is_file() and ".ansible" not in path.parts
        )

    def test_no_arbitrary_execution_module_is_used(self) -> None:
        for module in ("shell", "command", "raw", "script"):
            self.assertNotRegex(self.task_text, rf"ansible\.builtin\.{module}\s*:")

    def test_raw_discovery_results_are_no_log(self) -> None:
        raw_registers = re.findall(r"register:\s*(read_only_discovery_[a-z0-9_]+_raw)", self.task_text)
        self.assertGreaterEqual(len(raw_registers), 5)
        for register in raw_registers:
            task_start = self.task_text.rfind("\n- name:", 0, self.task_text.find(f"register: {register}"))
            task_end = self.task_text.find("\n- name:", self.task_text.find(f"register: {register}"))
            task = self.task_text[task_start : task_end if task_end >= 0 else None]
            self.assertIn("no_log: true", task, register)

    def test_kubernetes_queries_are_exact_and_exclude_sensitive_kinds(self) -> None:
        kubernetes_tasks = (ANSIBLE / "roles/read_only_discovery/tasks/kubernetes.yml").read_text()
        kinds = set(re.findall(r"^\s+kind:\s*([A-Za-z]+)\s*$", kubernetes_tasks, re.MULTILINE))
        self.assertTrue({"Node", "Namespace", "NetworkPolicy", "StorageClass", "IngressClass"}.issubset(kinds))
        self.assertTrue(kinds.isdisjoint({"Secret", "ConfigMap", "Event", "Events", "all"}))
        self.assertNotIn("kind: all", kubernetes_tasks.lower())
        self.assertNotIn("read_only_discovery_kubernetes_queries", self.all_ansible_text)
        self.assertIn("kubernetes.core.k8s_info:", kubernetes_tasks)
        self.assertIn("kubeconfig: /etc/rancher/k3s/k3s.yaml", kubernetes_tasks)

    def test_mandatory_gates_and_default_non_elevation_are_present(self) -> None:
        main = (ANSIBLE / "roles/read_only_discovery/tasks/main.yml").read_text()
        defaults = (ANSIBLE / "roles/read_only_discovery/defaults/main.yml").read_text()
        play = (ANSIBLE / "playbooks/discover.yml").read_text()
        for gate in ("ansible_check_mode", "ansible_diff_mode", "ansible_limit", "ansible_play_hosts_all"):
            self.assertIn(gate, main)
        self.assertIn("read_only_discovery_enable_elevated: false", defaults)
        self.assertIn("read_only_discovery_elevated_approved: false", defaults)
        self.assertIn("become: false", play)
        elevated = (ANSIBLE / "roles/read_only_discovery/tasks/kubernetes.yml").read_text()
        self.assertEqual(2, elevated.count("become: true"))

    def test_fact_cache_is_memory_only_and_no_install_task_exists(self) -> None:
        config = (ANSIBLE / "ansible.cfg").read_text()
        self.assertIn("fact_caching = memory", config)
        self.assertIn("become = False", config)
        for module in ("package", "apt", "pip"):
            self.assertNotRegex(self.task_text, rf"ansible\.builtin\.{module}\s*:")

    def test_report_is_local_private_curated_and_symlink_checked(self) -> None:
        report_tasks = (ANSIBLE / "roles/read_only_discovery/tasks/report.yml").read_text()
        template = (ANSIBLE / "roles/read_only_discovery/templates/report.json.j2").read_text()
        defaults = (ANSIBLE / "roles/read_only_discovery/defaults/main.yml").read_text()
        ignore_rules = (ROOT / ".gitignore").read_text()
        self.assertIn("delegate_to: localhost", report_tasks)
        self.assertIn('mode: "0600"', report_tasks)
        self.assertIn("diff: false", report_tasks)
        self.assertIn("check_mode: false", report_tasks)
        self.assertIn("islnk", report_tasks)
        self.assertIn("read_only_discovery_output_path ==", report_tasks)
        self.assertIn("inventory.local.ansible.json", defaults)
        self.assertIn("inventory.local*.json", ignore_rules)
        self.assertIn("HUMAN REVIEW REQUIRED", template)
        for forbidden in (
            "address",
            "macaddress",
            "uuid",
            "annotations",
            "labels",
            "env",
            "envFrom",
            "secret_data",
            "valuesContent",
            "stdout",
            "stderr",
            "raw_spec",
            "client_certificate_data",
            "client_key_data",
            "certificate_authority_data",
            "token",
        ):
            self.assertNotIn(forbidden, template)

    def test_collection_version_is_pinned(self) -> None:
        requirements = (ANSIBLE / "requirements.yml").read_text()
        self.assertRegex(requirements, r"name:\s*kubernetes\.core\s+version:\s*\"\d+\.\d+\.\d+\"")


if __name__ == "__main__":
    unittest.main()
