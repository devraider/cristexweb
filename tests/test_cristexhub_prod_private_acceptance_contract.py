from __future__ import annotations

import re
import stat
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
DEFAULTS = ANSIBLE / "roles/cristexhub_prod_private_acceptance/defaults/main.yml"
TASKS = ANSIBLE / "roles/cristexhub_prod_private_acceptance/tasks/main.yml"
PLAYBOOK = ANSIBLE / "playbooks/check_cristexhub_prod_private_acceptance.yml"
WRAPPER = ANSIBLE / "bin/check-cristexhub-prod-private-acceptance"
RUNBOOK = ROOT / "runbooks/cristexhub-prod-private-acceptance.md"
POLICY = ANSIBLE / "files/policies/cristexhub-prod-credential-rotation-gates.yml"


class CristexHubProdPrivateAcceptanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.defaults_text = DEFAULTS.read_text()
        cls.tasks_text = TASKS.read_text()
        cls.playbook_text = PLAYBOOK.read_text()
        cls.wrapper_text = WRAPPER.read_text()
        cls.runbook_text = RUNBOOK.read_text()
        cls.policy_text = POLICY.read_text()
        cls.defaults = yaml.safe_load(cls.defaults_text)
        cls.policy = yaml.safe_load(cls.policy_text)

    def test_exact_check_only_source_closure(self) -> None:
        self.assertEqual(0o755, stat.S_IMODE(WRAPPER.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE(DEFAULTS.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE(TASKS.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE(PLAYBOOK.stat().st_mode))
        self.assertEqual("cristexhub-prod", self.defaults["cristexhub_prod_private_acceptance_namespace"])
        self.assertEqual(
            ["backend", "celery-worker", "frontend", "oauth2-proxy", "redis"],
            self.defaults["cristexhub_prod_private_acceptance_deployments"],
        )
        self.assertEqual(
            "https://kubernetes.default.svc",
            self.defaults["cristexhub_prod_private_acceptance_server"],
        )
        self.assertEqual(
            "751885a42798d282e168131db147f13694a0a621",
            self.defaults["cristexhub_prod_private_acceptance_revision"],
        )
        self.assertEqual(
            {
                "backend": "1",
                "celery-worker": "1",
                "frontend": "1",
                "oauth2-proxy": "1",
                "redis": "1",
            },
            self.defaults["cristexhub_prod_private_acceptance_expected_deployment_revisions"],
        )
        self.assertEqual(
            [
                "CreateNamespace=false",
                "Prune=false",
                "ServerSideApply=false",
                "Replace=false",
                "FailOnSharedResource=true",
            ],
            self.defaults["cristexhub_prod_private_acceptance_expected_application_sync_options"],
        )
        self.assertIn("role: cristexhub_prod_private_acceptance", self.playbook_text)

    def test_no_secret_reads_or_mutation_modules(self) -> None:
        combined = f"{self.tasks_text}\n{self.playbook_text}\n{self.wrapper_text}"
        self.assertNotIn("kind: Secret", combined)
        self.assertNotIn("kind: secret", combined.lower())
        self.assertNotIn("secret.data", combined)
        self.assertNotIn("kubectl", combined)
        for forbidden in (
            "ansible.builtin.k8s:",
            "ansible.builtin.command:",
            "ansible.builtin.shell:",
            "ansible.builtin.raw:",
            "ansible.builtin.script:",
            "ansible.builtin.package:",
            "ansible.builtin.service:",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertNotIn("state: present", self.tasks_text)
        self.assertNotIn("state: absent", self.tasks_text)
        self.assertNotIn("apply", self.wrapper_text.lower())
        self.assertNotIn("tofu", combined.lower())
        self.assertNotIn("infisical", combined.lower())
        self.assertIn("return_content: false", self.tasks_text)
        self.assertIn("return_content: true", self.tasks_text)
        self.assertIn("no_log: true", self.tasks_text)

    def test_check_only_guards_and_attestation_are_bound(self) -> None:
        for required in (
            "ansible_check_mode",
            "ansible_diff_mode",
            "ansible_play_hosts_all | length == 1",
            "ansible_limit",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_ENTRYPOINT",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_TOKEN",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_ATTESTATION_FILE",
            "INTERNAL_VARIABLE_GUARD",
            "check_mode: false",
            "delegate_to: localhost",
            "follow_redirects: none",
            "validate_certs: true",
            "status.sync.comparedTo ==",
            "status.operationState.syncResult.source",
        ):
            self.assertIn(required, self.tasks_text)
        for required in (
            "usage: ansible/bin/check-cristexhub-prod-private-acceptance check",
            'if [ "$#" -ne 1 ] || [ "$1" != check ]; then',
            "--check",
            "--diff",
            "--limit crtxweb",
            "env -i",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_ENTRYPOINT=v1",
            "wrapper_canonical_sha256_expected",
            "refusing traced shell execution",
            "ANSIBLE_CONFIG=",
        ):
            self.assertIn(required, self.wrapper_text)
        self.assertIn('set -- \\\n  "$controller"', self.wrapper_text)
        self.assertNotIn("--start-at-task", self.wrapper_text)
        self.assertNotIn("--tags", self.wrapper_text)
        self.assertNotIn("--skip-tags", self.wrapper_text)

    def test_exact_argocd_and_workload_contract_is_documented(self) -> None:
        normalized = " ".join(self.runbook_text.split())
        for required in (
            "SOURCE-ONLY / CHECK-ONLY / NOT RUN",
            "Namespace `cristexhub-prod`",
            "Application/cristexhub-prod",
            "AppProject/cristexhub-prod",
            "https://kubernetes.default.svc",
            "selfHeal=true",
            "prune=false",
            "allowEmpty=false",
            "exactly five PROD Deployments",
            "backend",
            "celery-worker",
            "frontend",
            "oauth2-proxy",
            "redis",
            "does not create, update, delete, restart, sync, scale",
            "does not read ordinary Secret JSON",
            "records response content",
            "MongoDB NetworkPolicy",
            "exact two change protected PROD OpenTofu plan",
            "public-cutover authorization",
        ):
            self.assertIn(required, normalized)
        self.assertIn("cristexhub-prod-private-acceptance", self.tasks_text)
        self.assertIn("preflight-pass-not-final-acceptance", self.tasks_text)

    def test_argocd_and_workload_identity_is_complete(self) -> None:
        for required in (
            "Require direct-server pinned PROD Argo health and exact sync policy",
            "status.sync.comparedTo ==",
            "status.operationState.syncResult.source ==",
            "operationState.operation.sync.syncOptions ==",
            "Require the exact deny-by-default PROD AppProject boundary and exclusions",
            "clusterResourceBlacklist | default([]) == []",
            "namespaceResourceBlacklist | default([]) == []",
            "roles | default([]) == []",
            "syncWindows | default([]) == []",
            "signatureKeys | default([]) == []",
            "sourceNamespaces | default([]) == []",
            "'Secret'} not in",
            "'ServiceAccount'} not in",
            "'Namespace'} not in",
            "Require exactly one fresh Ready replica for every PROD Deployment",
            "deployment.kubernetes.io/revision",
            "status.observedGeneration | int == item.resources[0].metadata.generation | int",
            "NewReplicaSetAvailable",
            "Bind exact PROD Deployment revision and selector identities",
            "Query the exact current ReplicaSet for each PROD Deployment",
            "Require each PROD ReplicaSet to be the fresh Deployment controller result",
            "metadata.ownerReferences",
            "Bind exact PROD ReplicaSet controller identities",
            "Require each PROD Pod to be owned by the expected current ReplicaSet",
            "pod-template-hash",
            "ContainersReady",
            "status.containerStatuses",
        ):
            self.assertIn(required, self.tasks_text)
        self.assertEqual(7, self.tasks_text.count("kubernetes.core.k8s_info:"))
        self.assertGreaterEqual(self.tasks_text.count("kubeconfig: \"{{ cristexhub_prod_private_acceptance_kubeconfig }}\""), 7)

    def test_credential_policy_freezes_four_scopes_without_values(self) -> None:
        self.assertEqual("source-only-rotation-blocked", self.policy["policy_status"])
        self.assertEqual(
            {"mongodb", "rabbitmq", "ghcr", "deepseek"},
            set(self.policy["rotations"]),
        )
        common = self.policy["common_contract"]
        self.assertFalse(common["values_in_source"])
        self.assertFalse(common["values_in_argv"])
        self.assertFalse(common["values_in_environment"])
        self.assertFalse(common["values_in_logs"])
        self.assertTrue(common["predecessor_recovery_required"])
        self.assertTrue(common["expected_revision_or_conditional_write_required"])
        self.assertEqual("UNKNOWN-STOP", common["ambiguous_write_result"])
        self.assertEqual(
            "/shared-services/mongodb",
            self.policy["rotations"]["mongodb"]["source"]["path"],
        )
        self.assertEqual(
            "/shared-services/rabbitmq",
            self.policy["rotations"]["rabbitmq"]["source"]["path"],
        )
        self.assertEqual(
            "cristexhub-prod-ghcr-pull",
            self.policy["rotations"]["ghcr"]["target"]["name"],
        )
        self.assertEqual(
            "unresolved-external-application-secret",
            self.policy["rotations"]["deepseek"]["source"]["path"],
        )
        combined = self.policy_text + self.runbook_text
        self.assertNotRegex(combined, r"-----BEGIN [^-]+ PRIVATE KEY-----")
        self.assertNotRegex(combined, r"(?:amqps?|https?)://[^\s`]+:[^\s@`]+@")
        self.assertIn("source-only-rotation-blocked", self.runbook_text)

    def test_policy_and_runbook_do_not_add_rotation_executables(self) -> None:
        for relative in (
            "ansible/bin/rotate-mongodb-cristexhub-prod",
            "ansible/bin/rotate-rabbitmq-cristexhub-prod",
            "ansible/bin/rotate-cristexhub-prod-ghcr",
            "ansible/bin/rotate-deepseek-cristexhub-prod",
            "ansible/plugins/action/mongodb_prod_credential_rotation_guarded_k8s.py",
            "ansible/plugins/action/rabbitmq_prod_credential_rotation_guarded_k8s.py",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)
        for required in (
            "writer_source: absent",
            "infrastructure_secret_source: absent",
            "no_public_route_mutation",
            "No result from this preflight authorizes",
        ):
            self.assertIn(required.lower(), (self.policy_text + self.runbook_text).lower())

    def test_wrapper_shell_syntax(self) -> None:
        result = subprocess.run(
            ["/bin/sh", "-n", str(WRAPPER)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
