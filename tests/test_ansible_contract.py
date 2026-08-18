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
        allowed_action_plugins = {
            Path("ansible/plugins/action/argocd_guarded_k8s.py"),
            Path("ansible/plugins/action/argocd_secret_contract.py"),
            Path("ansible/plugins/action/cristexhub_dev_namespace_guarded_k8s.py"),
            Path("ansible/plugins/action/cristexhub_prod_namespace_guarded_k8s.py"),
            Path("ansible/plugins/action/infisical_operator_guarded_k8s.py"),
            Path("ansible/plugins/action/infisical_proxy_secret_zero_guarded_k8s.py"),
            Path("ansible/plugins/action/infisical_argocd_secrets_guarded_k8s.py"),
            Path("ansible/plugins/action/infisical_universal_auth_seed_guarded_k8s.py"),
            Path("ansible/plugins/action/rclone_install_guarded.py"),
            Path("ansible/plugins/action/rclone_proxy_transfer_guarded.py"),
            Path("ansible/plugins/action/mongodb_guarded_k8s.py"),
            Path("ansible/plugins/action/postgresql_guarded_k8s.py"),
            Path("ansible/plugins/action/keycloak_guarded_k8s.py"),
            Path("ansible/plugins/action/rabbitmq_guarded_k8s.py"),
            Path("ansible/plugins/action/stateful_database_secret_contract.py"),
            Path("ansible/plugins/action/infisical_database_secrets_guarded_k8s.py"),
            Path("ansible/plugins/action/database_provisioning_guarded_exec.py"),
            Path("ansible/plugins/action/database_provisioning_guarded_k8s.py"),
            Path("ansible/plugins/action/cloudflared_guarded_k8s.py"),
            Path("ansible/plugins/action/infisical_cloudflared_secrets_guarded_k8s.py"),
            Path("ansible/plugins/action/keycloak_route_guarded_k8s.py"),
            Path("ansible/plugins/action/oidc_connect_proxy_guarded_k8s.py"),
            Path("ansible/plugins/action/argocd_route_guarded_k8s.py"),
            Path("ansible/plugins/action/coredns_external_forwarding_guarded_patch.py"),
            Path("ansible/plugins/action/cristexhub_dev_registration_guarded_k8s.py"),
            Path("ansible/plugins/action/cristexhub_dev_sync_transition_guarded_k8s.py"),
            Path("ansible/plugins/action/infisical_cristexhub_dev_runtime_guarded_k8s.py"),
            Path("ansible/plugins/action/infisical_cristexhub_prod_runtime_guarded_k8s.py"),
        }
        self.assertEqual(28, len(allowed_action_plugins))
        self.assertTrue(
            all(path.parts[0] == "tests" or path in allowed_action_plugins for path in source_python),
            source_python,
        )
        for relative in (
            "AGENTS.md",
            "README.md",
            "specs/k3s-iac-foundation/brief.md",
            "specs/k3s-iac-foundation/status.md",
        ):
            normalized = " ".join((ROOT / relative).read_text().split())
            self.assertIn("exact-scope Ansible action plugins", normalized, relative)

    def test_minimal_ansible_layout_exists(self) -> None:
        required = [
            ".ansible-lint",
            ".ansible-lint-ignore",
            "ansible.cfg",
            "requirements.yml",
            "README.md",
            "files/policies/hosted-identity-authorization.yml",
            "files/policies/reactive-resume-architecture.yml",
            "files/policies/shared-database-architecture.yml",
            "files/policies/shared-rabbitmq-architecture.yml",
            "files/policies/shared-stateful-backup-architecture.yml",
            "files/policies/cloudflare-edge-architecture.yml",
            "files/vendor/argocd/10.3.0/SHA256SUMS",
            "files/vendor/argocd/10.3.0/argo-cd-10.3.0.tgz",
            "files/vendor/argocd/10.3.0/argo-cd-10.3.0.tgz.prov",
            "files/vendor/argocd/10.3.0/pgp_keys.asc",
            "files/vendor/infisical-operator/0.11.7/SHA256SUMS",
            "files/vendor/infisical-operator/0.11.7/cloudsmith-signing-key.asc",
            "files/vendor/infisical-operator/0.11.7/kubernetes-operator-64d2d81.tar.gz",
            "files/vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz",
            "files/vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz.prov",
            "inventory/hosts.yml",
            "playbooks/discover.yml",
            "playbooks/preflight_k3s_datastore.yml",
            "playbooks/bootstrap_dependencies.yml",
            "playbooks/install_backup_dependencies.yml",
            "playbooks/bootstrap_cloudnative_pg.yml",
            "playbooks/bootstrap_cloudnative_pg_cluster.yml",
            "playbooks/configure_postgresql_keycloak_backup.yml",
            "playbooks/configure_mongodb_shared_backup.yml",
            "playbooks/configure_k3s_admin_access.yml",
            "playbooks/configure_k3s_kubectl_client.yml",
            "playbooks/verify_k3s_reboot_recovery.yml",
            "playbooks/probe_k3s_network_policy.yml",
            "playbooks/install_opentofu.yml",
            "playbooks/bootstrap_platform_namespaces.yml",
            "playbooks/bootstrap_foundation_namespaces.yml",
            "playbooks/bootstrap_cristexhub_dev_namespace.yml",
            "playbooks/bootstrap_infisical_operator.yml",
            "playbooks/bootstrap_infisical_proxy_secrets.yml",
            "playbooks/bootstrap_infisical_argocd_secrets.yml",
            "playbooks/bootstrap_infisical_database_secrets.yml",
            "playbooks/seed_infisical_universal_auth.yml",
            "bin/seed-infisical-universal-auth",
            "bin/upload-infisical-bootstrap-values",
            "bin/materialize-infisical-cristexhub-dev-runtime",
            "bin/bootstrap-argocd",
            "playbooks/bootstrap_argocd.yml",
            "bin/bootstrap-mongodb",
            "playbooks/bootstrap_mongodb.yml",
            "bin/bootstrap-postgresql",
            "playbooks/bootstrap_postgresql.yml",
            "bin/bootstrap-keycloak",
            "playbooks/bootstrap_keycloak.yml",
            "plugins/action/keycloak_guarded_k8s.py",
            "roles/keycloak_bootstrap/defaults/main.yml",
            "roles/keycloak_bootstrap/tasks/main.yml",
            "bin/bootstrap-cloudnative-pg",
            "bin/bootstrap-cloudnative-pg-cluster",
            "bin/install-backup-dependencies",
            "bin/configure-postgresql-keycloak-backup",
            "bin/configure-mongodb-shared-backup",
            "bin/bootstrap-rabbitmq",
            "playbooks/bootstrap_rabbitmq.yml",
            "plugins/action/rabbitmq_guarded_k8s.py",
            "roles/rabbitmq_bootstrap/defaults/main.yml",
            "roles/rabbitmq_bootstrap/tasks/main.yml",
            "bin/configure-rabbitmq-definitions-backup",
            "bin/configure-opentofu-state-backup",
            "bin/bootstrap-cloudflared",
            "bin/bootstrap-infisical-cloudflared-secrets",
            "playbooks/bootstrap_cloudflared.yml",
            "playbooks/bootstrap_infisical_cloudflared_secrets.yml",
            "plugins/action/cloudflared_guarded_k8s.py",
            "plugins/action/infisical_cloudflared_secrets_guarded_k8s.py",
            "roles/cloudflared_bootstrap/defaults/main.yml",
            "roles/cloudflared_bootstrap/tasks/main.yml",
            "roles/infisical_cloudflared_secrets_bootstrap/defaults/main.yml",
            "roles/infisical_cloudflared_secrets_bootstrap/tasks/main.yml",
            "bin/bootstrap-keycloak-route",
            "playbooks/bootstrap_keycloak_route.yml",
            "bin/bootstrap-argocd-route",
            "bin/bootstrap-cristexhub-dev-registration",
            "bin/bootstrap-cristexhub-dev-sync-transition",
            "bin/bootstrap-infisical-cristexhub-dev-runtime",
            "bin/bootstrap-infisical-cristexhub-prod-runtime",
            "bin/bootstrap-oidc-connect-proxy",
            "bin/configure-coredns-external-forwarding",
            "bin/validate-argocd-ui-tls-material",
            "playbooks/bootstrap_argocd_route.yml",
            "playbooks/bootstrap_cristexhub_dev_registration.yml",
            "playbooks/bootstrap_cristexhub_dev_sync_transition.yml",
            "playbooks/bootstrap_infisical_cristexhub_dev_runtime.yml",
            "playbooks/bootstrap_infisical_cristexhub_prod_runtime.yml",
            "playbooks/bootstrap_oidc_connect_proxy.yml",
            "playbooks/configure_coredns_external_forwarding.yml",
            "files/policies/argocd-ui-tls-lifecycle.yml",
            "files/policies/cristexhub-dev-runtime-materialization.yml",
            "files/policies/cristexhub-prod-runtime-materialization.yml",
            "plugins/action/keycloak_route_guarded_k8s.py",
            "plugins/action/argocd_route_guarded_k8s.py",
            "plugins/action/coredns_external_forwarding_guarded_patch.py",
            "plugins/action/cristexhub_dev_registration_guarded_k8s.py",
            "plugins/action/cristexhub_dev_sync_transition_guarded_k8s.py",
            "plugins/action/infisical_cristexhub_dev_runtime_guarded_k8s.py",
            "plugins/action/infisical_cristexhub_prod_runtime_guarded_k8s.py",
            "plugins/action/oidc_connect_proxy_guarded_k8s.py",
            "roles/argocd_route_bootstrap/defaults/main.yml",
            "roles/argocd_route_bootstrap/tasks/main.yml",
            "roles/coredns_external_forwarding/defaults/main.yml",
            "roles/coredns_external_forwarding/tasks/main.yml",
            "roles/cristexhub_dev_registration/defaults/main.yml",
            "roles/cristexhub_dev_registration/tasks/main.yml",
            "roles/cristexhub_dev_sync_transition/defaults/main.yml",
            "roles/cristexhub_dev_sync_transition/tasks/main.yml",
            "roles/infisical_cristexhub_dev_runtime_bootstrap/defaults/main.yml",
            "roles/infisical_cristexhub_dev_runtime_bootstrap/tasks/main.yml",
            "roles/infisical_cristexhub_prod_runtime_bootstrap/defaults/main.yml",
            "roles/infisical_cristexhub_prod_runtime_bootstrap/tasks/main.yml",
            "roles/oidc_connect_proxy_bootstrap/defaults/main.yml",
            "roles/oidc_connect_proxy_bootstrap/tasks/main.yml",
            "roles/keycloak_route_bootstrap/defaults/main.yml",
            "roles/keycloak_route_bootstrap/tasks/main.yml",
            "playbooks/configure_rabbitmq_definitions_backup.yml",
            "files/backup/rabbitmq-shared-definitions-backup",
            "files/backup/restore-rabbitmq-definitions-rehearsal",
            "files/backup/cristexweb-rabbitmq-definitions-backup.service",
            "files/backup/cristexweb-rabbitmq-definitions-backup.timer",
            "files/backup/cristexweb-opentofu-state-backup.service",
            "files/backup/cristexweb-opentofu-state-backup.timer",
            "files/backup/opentofu-state-backup",
            "files/backup/restore-opentofu-state-rehearsal",
            "bin/configure-opentofu-state-backup",
            "playbooks/configure_opentofu_state_backup.yml",
            "bin/provision-shared-postgresql",
            "bin/provision-shared-mongodb",
            "playbooks/provision_shared_postgresql.yml",
            "playbooks/provision_shared_mongodb.yml",
            "roles/shared_postgresql_provisioning/defaults/main.yml",
            "roles/shared_postgresql_provisioning/tasks/main.yml",
            "roles/shared_mongodb_provisioning/defaults/main.yml",
            "roles/shared_mongodb_provisioning/tasks/main.yml",
            "files/database-provisioning/postgresql-check.sh",
            "files/database-provisioning/postgresql-apply.sh",
            "files/database-provisioning/mongodb-check.sh",
            "files/database-provisioning/mongodb-apply.sh",
            "files/backup/postgresql-keycloak-backup",
            "files/backup/restore-postgresql-keycloak-rehearsal",
            "files/backup/cristexweb-postgresql-keycloak-backup.service",
            "files/backup/cristexweb-postgresql-keycloak-backup.timer",
            "files/backup/mongodb-shared-backup",
            "files/backup/restore-mongodb-shared-rehearsal",
            "files/backup/cristexweb-mongodb-shared-backup.service",
            "files/backup/cristexweb-mongodb-shared-backup.timer",
            "plugins/action/database_provisioning_guarded_exec.py",
            "plugins/action/database_provisioning_guarded_k8s.py",
            "plugins/action/argocd_guarded_k8s.py",
            "plugins/action/mongodb_guarded_k8s.py",
            "plugins/action/postgresql_guarded_k8s.py",
            "plugins/action/stateful_database_secret_contract.py",
            "plugins/action/argocd_secret_contract.py",
            "plugins/action/cristexhub_dev_namespace_guarded_k8s.py",
            "plugins/action/cristexhub_prod_namespace_guarded_k8s.py",
            "plugins/action/infisical_operator_guarded_k8s.py",
            "plugins/action/infisical_proxy_secret_zero_guarded_k8s.py",
            "plugins/action/infisical_argocd_secrets_guarded_k8s.py",
            "plugins/action/infisical_database_secrets_guarded_k8s.py",
            "plugins/action/infisical_universal_auth_seed_guarded_k8s.py",
            "bin/bootstrap-platform-namespaces",
            "bin/bootstrap-foundation-namespaces",
            "bin/bootstrap-cristexhub-dev-namespace",
            "bin/bootstrap-cristexhub-prod-namespace",
            "bin/bootstrap-infisical-operator",
            "bin/bootstrap-infisical-proxy-secrets",
            "bin/bootstrap-infisical-argocd-secrets",
            "bin/bootstrap-infisical-database-secrets",
            "bin/install-rclone",
            "bin/transfer-infisical-proxy-recovery",
            "bin/preflight-k3s-datastore",
            "playbooks/install_rclone.yml",
            "playbooks/bootstrap_cristexhub_prod_namespace.yml",
            "playbooks/transfer_infisical_proxy_recovery.yml",
            "plugins/action/rclone_install_guarded.py",
            "plugins/action/rclone_proxy_transfer_guarded.py",
            "roles/rclone_install/defaults/main.yml",
            "roles/rclone_install/tasks/main.yml",
            "roles/rclone_proxy_transfer/defaults/main.yml",
            "roles/rclone_proxy_transfer/tasks/main.yml",
            "files/policies/infisical-operator-privileged-prerequisites.yml",
            "files/policies/infisical-operator-implementation-profile.yml",
            "files/policies/infisical-secret-zero-lane.yml",
            "roles/opentofu_install/defaults/main.yml",
            "roles/opentofu_install/tasks/main.yml",
            "roles/platform_namespace_bootstrap/defaults/main.yml",
            "roles/platform_namespace_bootstrap/tasks/main.yml",
            "roles/foundation_namespace_bootstrap/defaults/main.yml",
            "roles/foundation_namespace_bootstrap/tasks/main.yml",
            "roles/cristexhub_dev_namespace_bootstrap/defaults/main.yml",
            "roles/cristexhub_dev_namespace_bootstrap/tasks/main.yml",
            "roles/cristexhub_prod_namespace_bootstrap/defaults/main.yml",
            "roles/cristexhub_prod_namespace_bootstrap/tasks/main.yml",
            "roles/infisical_operator_bootstrap/defaults/main.yml",
            "roles/infisical_operator_bootstrap/tasks/main.yml",
            "roles/infisical_argocd_secrets_bootstrap/defaults/main.yml",
            "roles/infisical_argocd_secrets_bootstrap/tasks/main.yml",
            "roles/infisical_database_secrets_bootstrap/defaults/main.yml",
            "roles/infisical_database_secrets_bootstrap/tasks/main.yml",
            "roles/infisical_universal_auth_seed/defaults/main.yml",
            "roles/infisical_universal_auth_seed/tasks/main.yml",
            "roles/infisical_proxy_secret_zero/defaults/main.yml",
            "roles/infisical_proxy_secret_zero/tasks/main.yml",
            "roles/argocd_bootstrap/defaults/main.yml",
            "roles/argocd_bootstrap/tasks/main.yml",
            "roles/mongodb_bootstrap/defaults/main.yml",
            "roles/mongodb_bootstrap/tasks/main.yml",
            "roles/postgresql_bootstrap/defaults/main.yml",
            "roles/postgresql_bootstrap/tasks/main.yml",
            "roles/network_policy_probe/defaults/main.yml",
            "roles/network_policy_probe/tasks/cleanup.yml",
            "roles/network_policy_probe/tasks/delete_object.yml",
            "roles/network_policy_probe/tasks/discover_owned.yml",
            "roles/network_policy_probe/tasks/main.yml",
            "roles/network_policy_probe/tasks/plan.yml",
            "roles/network_policy_probe/tasks/preflight.yml",
            "roles/network_policy_probe/tasks/probe_pod.yml",
            "roles/network_policy_probe/tasks/register_object.yml",
            "roles/network_policy_probe/tasks/run.yml",
            "roles/network_policy_probe/tasks/validate_cleanup.yml",
            "roles/network_policy_probe/tasks/verify_server.yml",
            "roles/network_policy_probe/tasks/write_ledger.yml",
            "roles/read_only_discovery/defaults/main.yml",
            "roles/k3s_datastore_preflight/defaults/main.yml",
            "roles/k3s_datastore_preflight/tasks/main.yml",
            "roles/k3s_datastore_preflight/tasks/parse.yml",
            "roles/k3s_datastore_preflight/templates/report.json.j2",
            "roles/read_only_discovery/tasks/main.yml",
            "roles/read_only_discovery/tasks/host.yml",
            "roles/read_only_discovery/tasks/kubernetes.yml",
            "roles/read_only_discovery/tasks/report.yml",
            "roles/read_only_discovery/templates/report.json.j2",
        ]
        for component in (
            "infisical-operator",
            "argocd",
            "infisical-argocd-secrets",
            "infisical-database-secrets",
            "mongodb",
            "mongodb-operator",
            "postgresql",
            "cloudnative-pg",
            "keycloak",
            "infisical-keycloak-secrets",
            "rabbitmq",
            "infisical-rabbitmq-secrets",
            "cloudflared",
            "infisical-cloudflared-secrets",
            "keycloak-route",
            "oidc-connect-proxy",
            "argocd-route",
            "cristexhub-dev-registration",
            "cristexhub-dev-sync-transition",
            "infisical-cristexhub-dev-runtime",
            "infisical-cristexhub-prod-runtime",
        ):
            required.extend(
                str(path.relative_to(ANSIBLE))
                for path in sorted((ANSIBLE / "files/components" / component).rglob("*"))
                if path.is_file()
            )
        self.assertEqual([], [path for path in required if not (ANSIBLE / path).is_file()])
        actual = {
            str(path.relative_to(ANSIBLE))
            for path in ANSIBLE.rglob("*")
            if path.is_file()
            and ".ansible" not in path.parts
            and "__pycache__" not in path.parts
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
        self.assertIn("action_plugins = plugins/action", config)

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
            "Inspect kubeconfig access as the approved user",
            "become_user: \"{{ k3s_admin_user }}\"",
            "k3s_admin_user_kubeconfig.stat.readable | default(false)",
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
        self.assertLess(
            playbook.index("Configure the kubeconfig group"),
            playbook.index("Inspect kubeconfig access as the approved user"),
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

    def test_k3s_kubectl_client_defaults_are_user_scoped_and_approved(self) -> None:
        playbook = (ANSIBLE / "playbooks/configure_k3s_kubectl_client.yml").read_text()
        for required in (
            "k3s_kubectl_client_approved: false",
            "k3s_kubectl_client_approved | bool",
            "ansible_limit",
            "ansible_play_hosts_all",
            "ansible_diff_mode",
            "k3s_admin_user is defined",
            "k3s_admin_group: k3s-admin",
            "k3s_kubectl_client_state in ['present', 'absent']",
            "(k3s_client_passwd[1] | int) != 0",
            "k3s_client_passwd[5] in ['/bin/bash', '/usr/bin/bash']",
            "difference([k3s_admin_user])",
            "Reject numeric aliases of the dedicated group",
            "item.value[1] | string",
            "Reject unexpected primary members of the dedicated group",
            "item.value[2] | string",
            "not (k3s_client_home_state.stat.islnk | default(false))",
            ".bash_profile",
            ".bash_login",
            ".profile",
            ".bashrc",
            "ansible.builtin.blockinfile:",
            'export K3S_CONFIG_FILE="${K3S_CONFIG_FILE:-/dev/null}"',
            'export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"',
            "Add the selected user's k3s kubectl client defaults",
            "Remove k3s kubectl client defaults from every supported profile",
            "item.stat.exists | default(false)",
            "become_user: \"{{ k3s_admin_user }}\"",
            "diff: false",
            "no_log: true",
        ):
            self.assertIn(required, playbook)
        self.assertLess(
            playbook.index("Reject numeric aliases of the dedicated group"),
            playbook.index("Record the approved user home"),
        )
        self.assertLess(
            playbook.index("Reject unexpected primary members of the dedicated group"),
            playbook.index("Record the approved user home"),
        )
        self.assertLess(
            playbook.index("Require a safe existing user home"),
            playbook.index("Add the selected user's k3s kubectl client defaults"),
        )
        self.assertIn(
            '- "{{ k3s_client_home }}/.bash_profile"\n'
            '        - "{{ k3s_client_home }}/.bash_login"\n'
            '        - "{{ k3s_client_home }}/.profile"\n'
            '        - "{{ k3s_client_home }}/.bashrc"',
            playbook,
        )
        self.assertNotIn('path: "{{ k3s_client_home }}/{{ item }}"', playbook)
        present_task = re.search(
            r"- name: Add the selected user's k3s kubectl client defaults.*?(?=\n    - name: Remove)",
            playbook,
            re.DOTALL,
        )
        self.assertIsNotNone(present_task)
        self.assertIn('path: "{{ item.item }}"', present_task.group())
        self.assertIn("loop: \"{{ k3s_client_profile_states.results }}\"", present_task.group())
        self.assertIn("item.item in [k3s_client_login_profile, k3s_client_home ~ '/.bashrc']", present_task.group())
        absent_task = playbook[playbook.index("- name: Remove k3s kubectl client defaults") :]
        self.assertIn('path: "{{ item.item }}"', absent_task)
        self.assertIn("loop: \"{{ k3s_client_profile_states.results }}\"", absent_task)
        self.assertIn("state: absent", absent_task)
        self.assertIn("item.stat.exists | default(false)", absent_task)
        self.assertNotIn("k3s_client_login_profile", absent_task)
        self.assertEqual(2, playbook.count("ansible.builtin.blockinfile:"))
        for forbidden in (
            "name: paul",
            "/home/paul",
            "/etc/rancher/k3s/config.yaml",
            "ansible.builtin.shell:",
            "ansible.builtin.command:",
            "ansible.builtin.script:",
            "ansible.builtin.service:",
            "state: restarted",
        ):
            self.assertNotIn(forbidden, playbook)

    def test_k3s_reboot_recovery_is_bounded_and_approved(self) -> None:
        playbook = (ANSIBLE / "playbooks/verify_k3s_reboot_recovery.yml").read_text()
        for required in (
            "k3s_reboot_recovery_approved: false",
            "k3s_reboot_recovery_approved | bool",
            "k3s_recovery_access_confirmed: false",
            "k3s_recovery_access_confirmed | bool",
            "ansible_limit",
            "ansible_play_hosts_all",
            "ansible_diff_mode",
            "k3s_admin_user is defined",
            "k3s_admin_group: k3s-admin",
            "k3s_kubeconfig_path == '/etc/rancher/k3s/k3s.yaml'",
            "difference([k3s_admin_user])",
            "Reject numeric aliases of the dedicated administrator group",
            "Reject unexpected primary administrator group members",
            "ansible.builtin.service_facts:",
            "'k3s.service' in ansible_facts.services",
            "'tailscaled.service' in ansible_facts.services",
            "config.yaml.pre-admin-access",
            "k3s_recovery_user_access_before.stat.readable | default(false)",
            "kind: Node",
            "ansible.builtin.slurp:",
            "/proc/sys/kernel/random/boot_id",
            "ansible.builtin.reboot:",
            "reboot_timeout: 600",
            "post_reboot_delay: 15",
            "k3s_recovery_reboot.rebooted | default(false)",
            "k3s_recovery_user_access_after.stat.readable | default(false)",
            "when: not ansible_check_mode",
            "no_log: true",
        ):
            self.assertIn(required, playbook)
        self.assertEqual(1, playbook.count("ansible.builtin.reboot:"))
        self.assertEqual(2, playbook.count("kind: Node"))
        self.assertLess(
            playbook.index("Require one Ready node before reboot"),
            playbook.index("Perform the approved single reboot"),
        )
        self.assertLess(
            playbook.index("Perform the approved single reboot"),
            playbook.index("Require a completed reboot and a new boot identifier"),
        )
        self.assertLess(
            playbook.index("Require a completed reboot and a new boot identifier"),
            playbook.index("Require the complete post-reboot recovery contract"),
        )
        for forbidden in (
            "name: paul",
            "/home/paul",
            "ansible.builtin.shell:",
            "ansible.builtin.command:",
            "ansible.builtin.raw:",
            "ansible.builtin.script:",
            "ansible.builtin.apt:",
            "ansible.builtin.package:",
            "ansible.builtin.user:",
            "ansible.builtin.group:",
            "ansible.builtin.file:",
            "ansible.builtin.copy:",
            "ansible.builtin.lineinfile:",
            "ansible.builtin.blockinfile:",
            "kind: Secret",
            "kind: ConfigMap",
        ):
            self.assertNotIn(forbidden, playbook)

    def test_inventory_contains_only_the_neutral_ssh_alias(self) -> None:
        text = (ANSIBLE / "inventory/hosts.yml").read_text()
        self.assertIn("crtxweb:", text)
        for forbidden in ("ansible_host", "ansible_user", "ansible_password", "ansible_become", "private_key"):
            self.assertNotIn(forbidden, text)
        self.assertNotRegex(text, r"\b(?:10|127|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.")


class NetworkPolicyProbeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.role = ANSIBLE / "roles/network_policy_probe"
        cls.playbook = (ANSIBLE / "playbooks/probe_k3s_network_policy.yml").read_text()
        cls.defaults = (cls.role / "defaults/main.yml").read_text()
        cls.tasks = {
            path.name: path.read_text()
            for path in sorted((cls.role / "tasks").glob("*.yml"))
        }
        cls.main = cls.tasks["main.yml"]
        cls.preflight = cls.tasks["preflight.yml"]
        cls.run_tasks = cls.tasks["run.yml"]
        cls.cleanup_tasks = cls.tasks["cleanup.yml"]
        cls.delete_tasks = cls.tasks["delete_object.yml"]
        cls.pod_tasks = cls.tasks["probe_pod.yml"]
        cls.operational = "\n".join(
            [cls.playbook, cls.defaults, *cls.tasks.values()]
        )

    def test_plan_run_and_cleanup_truth_table_fails_closed(self) -> None:
        for required in (
            "hosts: k3s_servers",
            "serial: 1",
            "any_errors_fatal: true",
            "become: false",
            "network_policy_probe_action in ['plan', 'run', 'cleanup']",
            "network_policy_probe_action != 'plan' or ansible_check_mode",
            "network_policy_probe_action == 'plan' or ansible_check_mode",
            "network_policy_probe_action == 'run'",
            "network_policy_probe_action == 'cleanup'",
            "not ansible_check_mode",
            "ansible_diff_mode",
            "ansible_limit",
            "ansible_play_hosts_all | length",
        ):
            self.assertIn(required, self.operational)
        self.assertRegex(
            self.defaults,
            re.compile(r'^network_policy_probe_image: ""$', re.MULTILINE),
        )
        self.assertRegex(
            self.defaults,
            re.compile(r'^network_policy_probe_delete_approved: false$', re.MULTILINE),
        )

    def test_runtime_requires_verified_digest_and_separate_approvals(self) -> None:
        for required in (
            "@sha256:[0-9a-f]{64}",
            "network_policy_probe_image_architecture == network_policy_probe_required_architecture",
            "network_policy_probe_image_verification_reference",
            "network_policy_probe_ownership_exception_approved | bool",
            "network_policy_probe_create_approved | bool",
            "network_policy_probe_delete_approved | bool",
            "network_policy_probe_run_id is",
            "[a-z0-9-]{18,30}[a-z0-9]",
            "network_policy_probe_managed_by == 'cristexweb-network-policy-probe'",
            "network_policy_probe_run_label == 'cristexweb.io/network-probe-run'",
            "network_policy_probe_allowed_cleanup_kinds == [",
            "Reject externally supplied internal probe variables",
            "vars.keys()",
        ):
            self.assertIn(required, self.preflight)
        cleanup_gate = self.preflight[
            self.preflight.index("Require exact cleanup identities") :
            self.preflight.index("Validate every exact cleanup identity")
        ]
        self.assertNotIn("network_policy_probe_image", cleanup_gate)
        self.assertIn("equalto', 'Namespace'", cleanup_gate)
        self.assertIn("It does not require", cleanup_gate)

    def test_generated_identity_uid_cleanup_and_ledger_are_bounded(self) -> None:
        self.assertGreaterEqual(self.operational.count("generate_name:"), 5)
        for required in (
            "delete_options:",
            "preconditions:",
            'uid: "{{ network_policy_probe_delete_object.uid }}"',
            "propagationPolicy: Orphan",
            "kind: EndpointSlice",
            "kubernetes.io/service-name",
            "Register the generated client Pod before observing its result",
            "network_policy_probe_discovered_objects | reverse | list",
            "Require zero authored residue",
            'mode: "0600"',
            "not (network_policy_probe_ledger_state.stat.islnk",
            "network_policy_probe_ledger_state.stat.isreg",
            "network_policy_probe_ledger_state.stat.mode",
            "network_policy_probe_ledger_state.stat.pw_name",
            "lookup('ansible.builtin.env', 'USER')",
            "cleanup_required",
            "Discover exact objects carrying both immutable ownership labels",
            "difference(network_policy_probe_discovered_objects)",
        ):
            self.assertIn(required, self.operational)
        self.assertIn(
            "network-policy-probe.local*.json",
            (ROOT / ".gitignore").read_text(),
        )
        self.assertIn("'k3s_network_probe_action': 'cleanup'", self.operational)
        self.assertIn("Revalidate the immutable exact-delete boundary", self.delete_tasks)
        self.assertNotIn("delete_all:", self.operational)
        self.assertNotIn("propagationPolicy: Foreground", self.operational)
        self.assertNotIn("kind: Namespace\n    state: absent", self.operational)
        self.assertNotIn("kind: Namespace\n    state: present", self.operational)
        self.assertIn("namespace_created_or_deleted: false", self.operational)
        service_block = self.run_tasks[
            self.run_tasks.index("Create the generated-name ClusterIP service") :
            self.run_tasks.index("Register the generated service")
        ]
        self.assertNotIn("selector:", service_block)
        self.assertLess(
            self.run_tasks.index("Register the explicit EndpointSlice"),
            self.run_tasks.index("Prove allowed-role baseline connectivity"),
        )

    def test_functional_phases_use_standalone_pods_without_remote_exec(self) -> None:
        for phase in (
            "baseline-allowed",
            "baseline-denied",
            "deny-allowed",
            "deny-denied",
            "selective-allowed",
            "selective-denied",
            "rollback-allowed",
            "rollback-denied",
        ):
            self.assertIn(f"network_policy_probe_pod_phase: {phase}", self.run_tasks)
        self.assertEqual(5, self.run_tasks.count("network_policy_probe_expected_pod_phase: Succeeded"))
        self.assertEqual(3, self.run_tasks.count("network_policy_probe_expected_pod_phase: Failed"))
        for required in (
            "activeDeadlineSeconds: 20",
            "automountServiceAccountToken: false",
            "runAsNonRoot: true",
            "allowPrivilegeEscalation: false",
            "readOnlyRootFilesystem: true",
            "type: ClusterIP",
            "ingress: []",
            "network_policy_probe_probe_succeeded",
            "state.terminated.exitCode == 1",
            "state.terminated.reason == 'Error'",
            "'DeadlineExceeded'",
            "result.spec.clusterIP",
            "restartCount == 0",
            "Verify stable server control after default-deny evidence",
            "Verify stable server control after selective-deny evidence",
            "always:",
        ):
            self.assertIn(required, self.operational)
        self.assertNotIn("cristexweb.io/network-probe-phase", self.pod_tasks)
        self.assertLess(
            self.pod_tasks.index("Register the generated client Pod"),
            self.pod_tasks.index("Wait for the expected terminal Pod phase"),
        )
        self.assertLess(
            self.pod_tasks.index("Require an expected wget connectivity rejection"),
            self.pod_tasks.index("Record the sanitized phase result"),
        )
        for forbidden in (
            "kubernetes.core.k8s_exec:",
            "ansible.builtin.shell:",
            "ansible.builtin.command:",
            "ansible.builtin.raw:",
            "ansible.builtin.script:",
            "NodePort",
            "LoadBalancer",
            "hostPort",
            "kubectl",
            "kind: Job",
        ):
            self.assertNotIn(forbidden, self.operational)

    def test_preflight_is_address_safe_and_never_manages_a_namespace(self) -> None:
        self.assertIn("kind: Node", self.preflight)
        self.assertIn("kind: NetworkPolicy", self.preflight)
        self.assertIn("kind: Namespace", self.preflight)
        self.assertIn("network_policy_probe_namespace == 'default'", self.preflight)
        self.assertIn("network_policy_probe_namespace_raw.resources | length == 1", self.preflight)
        self.assertIn("no_log: true", self.preflight)
        node_query = self.preflight[
            self.preflight.index("Query the single node") :
            self.preflight.index("Require exactly one Ready")
        ]
        self.assertIn("when: network_policy_probe_action in ['plan', 'run']", node_query)
        self.assertNotIn("kind: Node", self.tasks["cleanup.yml"])
        self.assertNotIn("kind: Node", self.tasks["validate_cleanup.yml"])
        for forbidden in (
            "kind: Secret",
            "kind: PersistentVolumeClaim",
            "kind: Ingress",
        ):
            self.assertNotIn(forbidden, self.operational)


class AnsibleSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.task_text = "\n".join(path.read_text() for path in sorted((ANSIBLE / "roles/read_only_discovery/tasks").glob("*.yml")))
        cls.all_ansible_text = "\n".join(
            path.read_text()
            for path in sorted(ANSIBLE.rglob("*"))
            if path.is_file()
            and ".ansible" not in path.parts
            and "__pycache__" not in path.parts
            and not path.name.endswith((".tgz", ".tar.gz"))
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
        self.assertTrue(
            {
                "Node",
                "Namespace",
                "NetworkPolicy",
                "StorageClass",
                "PersistentVolume",
                "PersistentVolumeClaim",
                "IngressClass",
            }.issubset(kinds)
        )
        self.assertTrue(kinds.isdisjoint({"Secret", "ConfigMap", "Event", "Events", "all"}))
        self.assertNotIn("kind: all", kubernetes_tasks.lower())
        self.assertNotIn("read_only_discovery_kubernetes_queries", self.all_ansible_text)
        self.assertIn("kubernetes.core.k8s_info:", kubernetes_tasks)
        self.assertIn("kubeconfig: /etc/rancher/k3s/k3s.yaml", kubernetes_tasks)

    def test_storage_queries_are_exact_and_pvc_scopes_are_bounded(self) -> None:
        kubernetes_tasks = (ANSIBLE / "roles/read_only_discovery/tasks/kubernetes.yml").read_text()
        pvc_blocks = re.findall(
            r"    - id: (?P<id>[a-z_]+_persistent_volume_claims)\n"
            r"      api_version: v1\n"
            r"      kind: PersistentVolumeClaim\n"
            r"      namespace: (?P<namespace>[a-z0-9-]+)",
            kubernetes_tasks,
        )
        self.assertEqual(
            [
                ("default_persistent_volume_claims", "default"),
                ("kube_system_persistent_volume_claims", "kube-system"),
                ("shared_services_persistent_volume_claims", "shared-services"),
                ("dev_persistent_volume_claims", "cristexhub-dev"),
                ("prod_persistent_volume_claims", "cristexhub-prod"),
            ],
            pvc_blocks,
        )
        self.assertEqual(5, kubernetes_tasks.count("kind: PersistentVolumeClaim"))
        self.assertIn("- id: persistent_volumes\n      api_version: v1\n      kind: PersistentVolume", kubernetes_tasks)
        self.assertNotRegex(kubernetes_tasks, r"kind: PersistentVolumeClaim\n\s+- id:")

    def test_storage_report_is_curated_and_omits_identifying_raw_fields(self) -> None:
        template = (ANSIBLE / "roles/read_only_discovery/templates/report.json.j2").read_text()
        self.assertEqual(1, template.count('"schema_version": 3'))
        self.assertNotIn('"schema_version": 2', template)
        for required in (
            '"block_devices"',
            '"size_bytes"',
            '"rotational"',
            '"removable"',
            '"partition_count"',
            '"direct_mount_observed_for_device_or_partition"',
            '"filesystem_types_observed_while_mounted"',
            '"partitions"',
        ):
            self.assertIn(required, template)
        for forbidden in ("serial", "uuid", "address", "mount_point", "mount_source", "contents"):
            self.assertNotIn(forbidden, template.lower())
        self.assertIn("selectattr('device', 'in', device_sources)", template)
        self.assertIn("selectattr('device', 'equalto', partition_source)", template)
        self.assertNotIn("(?:p?[0-9]+)?", template)
        self.assertTrue((ROOT / "tests/validate_storage_report.yml").is_file())
        for forbidden_module in (
            "ansible.posix.mount",
            "community.general.filesystem",
            "community.general.parted",
            "community.general.lvol",
            "ansible.builtin.file",
            "ansible.builtin.copy",
            "ansible.builtin.replace",
            "ansible.builtin.lineinfile",
            "ansible.builtin.blockinfile",
            "ansible.builtin.apt",
            "ansible.builtin.package",
            "ansible.builtin.shell",
            "ansible.builtin.command",
            "ansible.builtin.raw",
            "ansible.builtin.script",
        ):
            self.assertNotRegex(self.task_text, rf"{re.escape(forbidden_module)}\s*:")

    def test_node_version_projection_is_exact_and_bounded(self) -> None:
        template = (ANSIBLE / "roles/read_only_discovery/templates/report.json.j2").read_text()
        node_branch_start = template.index("{% if query_result.item.id == 'nodes' %}")
        node_branch_end = template.index(
            "{% elif query_result.item.id == 'storage_classes' %}", node_branch_start
        )
        node_branch = template[node_branch_start:node_branch_end]
        expected_node_branch = """{% if query_result.item.id == 'nodes' %}
          {
            "name": {{ resource.get('metadata', {}).get('name', 'unknown') | to_json }},
            "namespace": {{ resource.get('metadata', {}).get('namespace', 'cluster-scoped') | to_json }},
            "kubelet_version": {{ resource.get('status', {}).get('nodeInfo', {}).get('kubeletVersion', 'unknown') | to_json }}
          }{% if not loop.last %},{% endif %}
"""
        self.assertEqual(expected_node_branch, node_branch)
        self.assertEqual(1, template.count("query_result.item.id == 'nodes'"))
        self.assertEqual(
            1,
            template.count(
                "resource.get('status', {}).get('nodeInfo', {}).get("
                "'kubeletVersion', 'unknown')"
            ),
        )
        for forbidden in (
            "resource |",
            "resource.status",
            "resource.get('status', {}) |",
            "kernelVersion",
            "containerRuntimeVersion",
            "machineID",
            "systemUUID",
            "bootID",
            "metadata.labels",
            "metadata.annotations",
            "status.addresses",
        ):
            self.assertNotIn(forbidden, node_branch)
        self.assertNotIn('"kubelet_version"', template[:node_branch_start])
        self.assertNotIn('"kubelet_version"', template[node_branch_end:])

        fixture = (ROOT / "tests/validate_storage_report.yml").read_text()
        for required in (
            "synthetic-node-without-status",
            "synthetic-node-without-node-info",
            "kernelVersion: synthetic-kernel",
            "containerRuntimeVersion: synthetic-runtime",
            "machineID: synthetic-machine-id",
            "systemUUID: synthetic-system-uuid",
            "bootID: synthetic-boot-id",
            "addresses:",
            "labels:",
            "annotations:",
            "'kubelet_version': 'unknown'",
        ):
            self.assertIn(required, fixture)

    def test_storageclass_and_volume_projection_is_exact_and_path_safe(self) -> None:
        template = (ANSIBLE / "roles/read_only_discovery/templates/report.json.j2").read_text()
        for required in (
            '"provisioner"',
            '"reclaim_policy"',
            '"volume_binding_mode"',
            '"allow_volume_expansion"',
            '"storage_class_name"',
            '"phase"',
            '"capacity_storage"',
            '"requested_storage"',
            '"access_modes"',
            '"volume_mode"',
            '"bound_volume_present"',
            '"host_path_backend"',
            '"local_volume_backend"',
            '"under_k3s_default_storage_root"',
            '"node_affinity_required"',
        ):
            self.assertIn(required, template)
        for forbidden in (
            '"volume_name"',
            "metadata.uid",
            "metadata.annotations",
            "claimRef.uid",
            "hostPath.path | to_json",
            "local.path | to_json",
        ):
            self.assertNotIn(forbidden, template)

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

    def test_operational_discovery_examples_require_local_inventory(self) -> None:
        required = (
            "uv run ansible-playbook -i .ansible/inventory.local.yml "
            "playbooks/discover.yml --check --diff --limit crtxweb"
        )
        for relative in (
            "README.md",
            "ansible/README.md",
            "specs/k3s-iac-foundation/testcases.md",
        ):
            normalized = " ".join((ROOT / relative).read_text().replace("\\\n", " ").split())
            self.assertIn(required, normalized, relative)
            self.assertNotIn(
                "uv run ansible-playbook playbooks/discover.yml --check --diff --limit crtxweb",
                normalized,
                relative,
            )
        config = (ANSIBLE / "ansible.cfg").read_text()
        self.assertIn("inventory = inventory/hosts.yml", config)
        inventory = (ANSIBLE / "inventory/hosts.yml").read_text()
        self.assertNotIn("ansible_host", inventory)
        self.assertNotIn("ansible_user", inventory)

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
