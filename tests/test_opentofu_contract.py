from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOFU = ROOT / "opentofu"
ANSIBLE = ROOT / "ansible"


class OpenTofuContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tf_files = sorted(TOFU.glob("*.tf"))
        cls.hcl = "\n".join(path.read_text() for path in cls.tf_files)
        cls.readme = (TOFU / "README.md").read_text()
        cls.brief = (ROOT / "specs/k3s-iac-foundation/brief.md").read_text()
        cls.playbook = (ANSIBLE / "playbooks/install_opentofu.yml").read_text()
        cls.defaults = (ANSIBLE / "roles/opentofu_install/defaults/main.yml").read_text()
        cls.tasks = (ANSIBLE / "roles/opentofu_install/tasks/main.yml").read_text()
        cls.operational = f"{cls.playbook}\n{cls.defaults}\n{cls.tasks}"
        cls.task_blocks = {
            match.group(1): match.group(0)
            for match in re.finditer(
                r"(?ms)^- name: ([^\n]+)\n.*?(?=^- name: |\Z)", cls.tasks
            )
        }

    def task(self, name: str) -> str:
        self.assertIn(name, self.task_blocks)
        return self.task_blocks[name]

    def test_scaffold_is_cloudflare_only_and_resource_free(self) -> None:
        self.assertEqual(
            {"README.md", "backend.tf", "providers.tf", "versions.tf"},
            {path.name for path in TOFU.iterdir() if path.is_file()},
        )
        for required in (
            'required_version = "= 1.12.5"',
            'source  = "cloudflare/cloudflare"',
            'version = "= 5.23.0"',
            'provider "cloudflare" {}',
            'backend "local"',
            'path = "/var/lib/opentofu/cristexweb/foundation.tfstate"',
        ):
            self.assertIn(required, self.hcl)
        for forbidden in (
            'resource "',
            'data "',
            'module "',
            'variable "',
            'output "',
            'import {',
            'moved {',
            "hashicorp/kubernetes",
            "hashicorp/helm",
            "integrations/github",
            "kubernetes_",
            "helm_",
            "kubectl_",
        ):
            self.assertNotIn(forbidden, self.hcl)

    def test_installer_is_exactly_pinned_gated_and_provenanced(self) -> None:
        for required in (
            "hosts: k3s_servers",
            "gather_facts: true",
            "become: true",
            "any_errors_fatal: true",
            "serial: 1",
            "opentofu_install_approved: false",
            "opentofu_install_rollback_approved: false",
            "opentofu_install_state in ['present', 'absent']",
            "ansible_diff_mode",
            "ansible_limit",
            "ansible_play_hosts_all | length == 1",
            "ansible_facts.distribution_major_version == '13'",
            "ansible_facts.architecture == 'x86_64'",
            "opentofu_install_operator_user is match",
            "tofu_1.12.5_SHA256SUMS",
            "tofu_1.12.5_SHA256SUMS.gpgsig",
            "120345f8a2493375aebbca072106de425b2eb227837f8064440b8d911e36f987",
            "E3E6E43D84CB852EADB0051D0C0AF313E5FD9F80",
            "a6894d45ae7a17ce83189cce8fe04b5a65f68cefceb62455b5a6a89fa53ab38f",
            "36dae7ca1e4f1552a6faef27179dc16ef403203e956f31416c17b3d87a38c3f4",
            "opentofu_install_controller_runtime_root == playbook_dir ~ '/../.ansible'",
            "opentofu_install_controller_cache_root == playbook_dir ~ '/../.ansible/cache'",
            "opentofu_install_controller_cache_directory == playbook_dir ~ '/../.ansible/cache/opentofu'",
            "opentofu_install_controller_archive_path == playbook_dir ~ '/../.ansible/cache/opentofu/tofu_1.12.5_linux_amd64.tar.gz'",
            "opentofu_install_archive_path == '/var/cache/opentofu/tofu_1.12.5_linux_amd64.tar.gz'",
            "opentofu_install_version_binary == '/opt/opentofu/1.12.5/tofu'",
            "opentofu_install_selector_path == '/usr/local/bin/tofu'",
            "opentofu_install_state_directory == '/var/lib/opentofu/cristexweb'",
        ):
            self.assertIn(required, self.operational)
        self.assertNotIn("name: paul", self.operational)
        self.assertNotIn("/home/paul", self.operational)

        approval = self.task("Require the OpenTofu installation approval contract")
        for required in (
            "opentofu_install_state != 'present' or (opentofu_install_approved | bool)",
            "opentofu_install_state != 'absent' or (opentofu_install_rollback_approved | bool)",
            "ansible_diff_mode",
            "ansible_play_hosts_all | length == 1",
            "opentofu_install_checksums_sha256 == '120345f8a2493375aebbca072106de425b2eb227837f8064440b8d911e36f987'",
            "opentofu_install_release_signer_fingerprint == 'E3E6E43D84CB852EADB0051D0C0AF313E5FD9F80'",
            "opentofu_install_controller_user == lookup('ansible.builtin.env', 'USER')",
        ):
            self.assertIn(required, approval)

        aliases = self.task("Reject numeric aliases of the selected operator account")
        self.assertIn("ansible_facts.getent_passwd | dict2items", aliases)
        self.assertIn("item.key == opentofu_install_operator_user", aliases)
        self.assertIn("item.value[1] | string", aliases)
        self.assertIn("opentofu_install_operator_passwd[1] | string", aliases)
        self.assertIn("no_log: true", aliases)

    def test_installer_mutations_are_bounded_and_mode_drift_fails_closed(self) -> None:
        parents_assert = self.task("Refuse unsafe existing OpenTofu parent paths")
        self.assertIn("item.stat.mode == item.item.mode", parents_assert)
        parent_create = self.task("Create root-owned OpenTofu parent directories")
        for required in (
            'path: /opt/opentofu\n      mode: "0755"',
            'path: /var/cache/opentofu\n      mode: "0700"',
            'path: "{{ opentofu_install_state_root }}"\n      mode: "0711"',
            "state: directory",
            "owner: root",
            "group: root",
            "when: opentofu_install_state == 'present'",
        ):
            self.assertIn(required, parent_create)

        state_create = self.task("Create the protected empty project state directory")
        for required in (
            'path: "{{ opentofu_install_state_directory }}"',
            "state: directory",
            'owner: "{{ opentofu_install_operator_user }}"',
            "group: root",
            'mode: "0700"',
            "- opentofu_install_state == 'present'",
            "- not ansible_check_mode",
        ):
            self.assertIn(required, state_create)

        archive_assert = self.task("Refuse an unsafe or modified cached release archive")
        self.assertIn("opentofu_install_archive_state.stat.mode == '0600'", archive_assert)
        self.assertIn("when: opentofu_install_state == 'present'", archive_assert)

        version_stat = self.task(
            "Inspect the versioned OpenTofu directory for installation"
        )
        self.assertIn('path: "{{ opentofu_install_version_dir }}"', version_stat)
        self.assertIn("follow: false", version_stat)
        self.assertIn("when: opentofu_install_state == 'present'", version_stat)
        version_assert = self.task("Refuse an unsafe existing version directory")
        for required in (
            "not (opentofu_install_version_directory_state.stat.exists | default(false))",
            "opentofu_install_version_directory_state.stat.isdir",
            "not (opentofu_install_version_directory_state.stat.islnk",
            "opentofu_install_version_directory_state.stat.pw_name == 'root'",
            "opentofu_install_version_directory_state.stat.gr_name == 'root'",
            "opentofu_install_version_directory_state.stat.mode == '0755'",
            "when: opentofu_install_state == 'present'",
        ):
            self.assertIn(required, version_assert)
        payload_stat = self.task(
            "Inspect the payload in an existing safe version directory"
        )
        self.assertIn("follow: false", payload_stat)
        self.assertIn("- opentofu_install_state == 'present'", payload_stat)
        self.assertIn(
            "- opentofu_install_version_directory_state.stat.exists | default(false)",
            payload_stat,
        )
        payload_assert = self.task(
            "Refuse an empty or modified existing version directory"
        )
        for required in (
            "opentofu_install_version_binary_state.stat.isreg",
            "not (opentofu_install_version_binary_state.stat.islnk",
            "opentofu_install_version_binary_state.stat.pw_name == 'root'",
            "opentofu_install_version_binary_state.stat.gr_name == 'root'",
            "opentofu_install_version_binary_state.stat.mode == '0755'",
            "opentofu_install_version_binary_state.stat.checksum == opentofu_install_binary_sha256",
            "- opentofu_install_state == 'present'",
            "- opentofu_install_version_directory_state.stat.exists | default(false)",
        ):
            self.assertIn(required, payload_assert)

        version_create = self.task("Create the immutable version directory")
        extraction = self.task("Expand the verified release archive")
        for block in (version_create, extraction):
            self.assertIn("- opentofu_install_state == 'present'", block)
            self.assertIn(
                "- not (opentofu_install_version_directory_state.stat.exists | default(false))",
                block,
            )
            self.assertIn("- not ansible_check_mode", block)
        self.assertIn('path: "{{ opentofu_install_version_dir }}"', version_create)
        self.assertIn("state: directory", version_create)
        self.assertIn('mode: "0755"', version_create)
        self.assertIn('dest: "{{ opentofu_install_version_dir }}"', extraction)
        self.assertIn('src: "{{ opentofu_install_archive_path }}"', extraction)

        selector_create = self.task("Select the reviewed OpenTofu version")
        for required in (
            'src: "{{ opentofu_install_version_binary }}"',
            'dest: "{{ opentofu_install_selector_path }}"',
            "state: link",
            "force: false",
            "- opentofu_install_state == 'present'",
            "- not ansible_check_mode",
        ):
            self.assertIn(required, selector_create)

    def test_controller_mediated_archive_transfer_is_bounded(self) -> None:
        controller_paths = self.task("Inspect controller OpenTofu cache paths for transfer")
        for required in (
            'path: "{{ opentofu_install_controller_runtime_root }}"',
            'mode: "0755"',
            "required: true",
            'path: "{{ opentofu_install_controller_cache_root }}"',
            'path: "{{ opentofu_install_controller_cache_directory }}"',
            'mode: "0700"',
            "follow: false",
            "delegate_to: localhost",
            "become: false",
            "- not (opentofu_install_archive_state.stat.exists | default(false))",
        ):
            self.assertIn(required, controller_paths)

        controller_paths_assert = self.task(
            "Refuse unsafe controller OpenTofu cache paths"
        )
        for required in (
            "not item.item.required or (item.stat.exists | default(false))",
            "item.stat.isdir",
            "not (item.stat.islnk",
            "item.stat.pw_name == opentofu_install_controller_user",
            "item.stat.mode == item.item.mode",
        ):
            self.assertIn(required, controller_paths_assert)

        controller_archive_stat = self.task(
            "Inspect the controller-cached OpenTofu release archive"
        )
        for required in (
            'path: "{{ opentofu_install_controller_archive_path }}"',
            "follow: false",
            "checksum_algorithm: sha256",
            "delegate_to: localhost",
            "become: false",
        ):
            self.assertIn(required, controller_archive_stat)
        controller_archive_assert = self.task(
            "Refuse an unsafe or modified controller-cached release archive"
        )
        for required in (
            "opentofu_install_controller_archive_state.stat.isreg",
            "not (opentofu_install_controller_archive_state.stat.islnk",
            "opentofu_install_controller_archive_state.stat.pw_name == opentofu_install_controller_user",
            "opentofu_install_controller_archive_state.stat.mode == '0600'",
            "opentofu_install_controller_archive_state.stat.checksum == opentofu_install_archive_sha256",
        ):
            self.assertIn(required, controller_archive_assert)

        cache_create = self.task("Prepare private controller OpenTofu cache directories")
        for required in (
            "ansible.builtin.file:",
            'owner: "{{ opentofu_install_controller_user }}"',
            'mode: "0700"',
            "delegate_to: localhost",
            "become: false",
        ):
            self.assertIn(required, cache_create)

        get_url_tasks = [
            block for block in self.task_blocks.values() if "ansible.builtin.get_url:" in block
        ]
        self.assertEqual(1, len(get_url_tasks))
        controller_download = self.task(
            "Retrieve the exact release archive into the controller cache"
        )
        self.assertEqual(controller_download, get_url_tasks[0])
        for required in (
            'url: "{{ opentofu_install_archive_url }}"',
            'dest: "{{ opentofu_install_controller_archive_path }}"',
            'checksum: "sha256:{{ opentofu_install_archive_sha256 }}"',
            'owner: "{{ opentofu_install_controller_user }}"',
            'mode: "0600"',
            "validate_certs: true",
            "delegate_to: localhost",
            "become: false",
            "- not (opentofu_install_archive_state.stat.exists | default(false))",
            "- not (opentofu_install_controller_archive_state.stat.exists | default(false))",
            "- not ansible_check_mode",
        ):
            self.assertIn(required, controller_download)

        transfer = self.task("Transfer the verified controller archive to the host cache")
        for required in (
            "ansible.builtin.copy:",
            'src: "{{ opentofu_install_controller_archive_path }}"',
            'dest: "{{ opentofu_install_archive_path }}"',
            "owner: root",
            "group: root",
            'mode: "0600"',
            "- not (opentofu_install_archive_state.stat.exists | default(false))",
            "- not ansible_check_mode",
        ):
            self.assertIn(required, transfer)
        self.assertNotIn("delegate_to:", transfer)
        self.assertEqual(1, self.tasks.count("ansible.builtin.copy:"))

        transfer_assert = self.task("Require the exact transferred host release archive")
        self.assertIn(
            "opentofu_install_transferred_archive_state.stat.checksum == opentofu_install_archive_sha256",
            transfer_assert,
        )
        for prediction_name in (
            "Predict controller release archive retrieval in check mode",
            "Predict verified archive transfer to the host in check mode",
        ):
            prediction = self.task(prediction_name)
            self.assertIn("changed_when: true", prediction)
            self.assertIn("- ansible_check_mode", prediction)

    def test_rollback_removes_only_selector_and_never_reads_state_content(self) -> None:
        rollback = self.task("Remove only the exact managed OpenTofu selector")
        for required in (
            'path: "{{ opentofu_install_selector_path }}"',
            "state: absent",
            "- opentofu_install_state == 'absent'",
            "- opentofu_install_selector_state.stat.exists | default(false)",
        ):
            self.assertIn(required, rollback)
        selector_assert = self.task("Refuse an unknown OpenTofu selector")
        for required in (
            "opentofu_install_selector_state.stat.islnk",
            "opentofu_install_selector_state.stat.lnk_source == opentofu_install_version_binary",
            "opentofu_install_selector_state.stat.pw_name == 'root'",
            "opentofu_install_selector_state.stat.gr_name == 'root'",
        ):
            self.assertIn(required, selector_assert)

        absent_tasks = [
            name for name, block in self.task_blocks.items() if "state: absent" in block
        ]
        self.assertEqual(["Remove only the exact managed OpenTofu selector"], absent_tasks)
        for name, block in self.task_blocks.items():
            if name == "Remove only the exact managed OpenTofu selector":
                continue
            self.assertNotIn("state: absent", block)
        for forbidden_module in (
            "ansible.builtin.slurp:",
            "ansible.builtin.fetch:",
            "ansible.builtin.find:",
            "ansible.builtin.synchronize:",
        ):
            self.assertNotIn(forbidden_module, self.tasks)

        for task_name in (
            "Inspect the cached OpenTofu release archive for installation",
            "Refuse an unsafe or modified cached release archive",
            "Inspect the versioned OpenTofu directory for installation",
            "Refuse an unsafe existing version directory",
        ):
            self.assertIn(
                "when: opentofu_install_state == 'present'", self.task(task_name)
            )
        for task_name in (
            "Inspect the payload in an existing safe version directory",
            "Refuse an empty or modified existing version directory",
        ):
            self.assertIn(
                "- opentofu_install_state == 'present'", self.task(task_name)
            )

    def test_version_command_is_non_root_and_provider_operations_remain_blocked(self) -> None:
        for forbidden in (
            "ansible.builtin.shell:",
            "ansible.builtin.raw:",
            "ansible.builtin.script:",
            "ansible.builtin.apt:",
            "ansible.builtin.package:",
            "kubernetes.core",
            "/etc/rancher/k3s",
            "/var/lib/rancher/k3s",
            "/var/lib/kubelet",
            "state: restarted",
            "state: stopped",
            "ansible.builtin.cron:",
            "ansible.builtin.systemd_service:",
        ):
            self.assertNotIn(forbidden, self.operational)
        self.assertEqual(1, self.operational.count("ansible.builtin.command:"))
        command_task = self.task("Verify the selected OpenTofu executable version")
        for required in (
            "ansible.builtin.command:",
            "- /usr/local/bin/tofu",
            "- version",
            "- -json",
            "become: true",
            'become_user: "{{ opentofu_install_operator_user }}"',
            "changed_when: false",
            "- opentofu_install_state == 'present'",
            "- not ansible_check_mode",
        ):
            self.assertIn(required, command_task)
        for forbidden_command in (
            "- init",
            "- validate",
            "- plan",
            "- apply",
            "- import",
            "- state",
            "- destroy",
        ):
            self.assertNotIn(forbidden_command, command_task)

        for required in (
            "zero-resource",
            "single-node failure domain",
            "encrypted timestamped off-node copies",
            "Google Drive",
            "UNKNOWN — STOP",
            "no apply is permitted",
        ):
            self.assertIn(required, self.readme)
        for required in (
            "The approved\nhost check passed",
            "the first live run created only the exact managed parent and\nempty protected state directories",
            "reviewed controller-transfer recovery then passed check, live installation, and a\n`changed=0` rerun",
            "Provider initialization, state, plan, and apply also remain unrun",
        ):
            self.assertIn(required, self.brief)
        for obsolete in (
            "host check/live run",
            "controller-transfer retry and idempotence remain unrun",
        ):
            self.assertNotIn(obsolete, self.brief)
        self.assertFalse((TOFU / ".terraform.lock.hcl").exists())
        self.assertEqual([], list(TOFU.rglob("*.tfstate")))
        self.assertEqual([], list(TOFU.rglob("*.tfplan")))

    def test_ignore_policy_covers_local_runtime_artifacts(self) -> None:
        ignore = (ROOT / ".gitignore").read_text()
        for required in (
            ".ansible/",
            "**/.terraform/*",
            "*.tfstate",
            "*.tfstate.*",
            "*.tfplan",
            "*.plan",
        ):
            self.assertIn(required, ignore)
        self.assertNotIn(
            ".terraform.lock.hcl",
            "\n".join(
                line
                for line in ignore.splitlines()
                if not line.lstrip().startswith("#")
            ),
        )


if __name__ == "__main__":
    unittest.main()
