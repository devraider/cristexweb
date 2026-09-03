from __future__ import annotations

import hashlib
import importlib.util
import os
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
PROCESS_GUARD = ANSIBLE / "plugins/action/cristexhub_prod_private_acceptance_process_guarded.py"
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
        cls.process_guard_text = PROCESS_GUARD.read_text()
        cls.runbook_text = RUNBOOK.read_text()
        cls.policy_text = POLICY.read_text()
        cls.defaults = yaml.safe_load(cls.defaults_text)
        cls.policy = yaml.safe_load(cls.policy_text)

    def test_exact_check_only_source_closure(self) -> None:
        self.assertEqual(0o755, stat.S_IMODE(WRAPPER.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE(DEFAULTS.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE(TASKS.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE(PLAYBOOK.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE(PROCESS_GUARD.stat().st_mode))
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
            "100.122.139.32",
            self.defaults["cristexhub_prod_private_acceptance_private_origin_ip"],
        )
        self.assertEqual(
            "http://100.122.139.32/",
            self.defaults["cristexhub_prod_private_acceptance_private_origin_url"],
        )
        self.assertEqual(
            "hub.cristex-soft.com",
            self.defaults["cristexhub_prod_private_acceptance_private_origin_host"],
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
        combined = f"{self.tasks_text}\n{self.playbook_text}\n{self.wrapper_text}\n{self.process_guard_text}"
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
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_WRAPPER_PID",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_WRAPPER_STARTTIME",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_SOURCE_CLOSURE_SHA256",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_ACTION_SHA256",
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
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_ENTRYPOINT=v2",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_ACTION_SHA256=",
            "wrapper_canonical_sha256_expected",
            "refusing traced shell execution",
            "ANSIBLE_CONFIG=",
            "WRAPPER_PATH=",
            "WRAPPER_PID=",
            "WRAPPER_STARTTIME=",
            "SOURCE_CLOSURE_SHA256=",
            "task_sha256_expected=",
            "refusing private PROD acceptance wrapper source drift",
        ):
            self.assertIn(required, self.wrapper_text)
        self.assertIn('set -- \\\n  "$controller"', self.wrapper_text)
        self.assertIn(":entrypoint:%s:%s:%s", self.wrapper_text)
        self.assertIn("Require source leaves and hashes bound to the canonical wrapper", self.tasks_text)
        for required in (
            "_ancestor",
            "_proc_parent",
            "_proc_starttime",
            "_proc_cmdline",
            "sys.argv == _expected_argv()",
            "_proc_cmdline(pid) == [\"/bin/dash\", str(_WRAPPER_SOURCE), \"check\"]",
            "and _ancestor(pid)",
            "and _proc_starttime(pid) == starttime",
        ):
            self.assertIn(required, self.process_guard_text)
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
            "current ReplicaSet",
            "100.122.139.32",
            "Host: hub.cristex-soft.com",
            "does not test or require the unapplied Cloudflare route",
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
            "replicaset_name",
            "pod-template-hash={{ item.pod_template_hash }}",
            "metadata.ownerReferences",
            "Bind exact PROD ReplicaSet controller identities",
            "Require each PROD Pod to be owned by the expected current ReplicaSet",
            "pod-template-hash",
            "ContainersReady",
            "status.containerStatuses",
        ):
            self.assertIn(required, self.tasks_text)
        self.assertEqual(8, self.tasks_text.count("kubernetes.core.k8s_info:"))
        self.assertGreaterEqual(self.tasks_text.count("kubeconfig: \"{{ cristexhub_prod_private_acceptance_kubeconfig }}\""), 8)
        self.assertIn("Query the complete PROD Deployment inventory", self.tasks_text)
        self.assertIn("Require exactly the approved PROD Deployment inventory", self.tasks_text)
        self.assertNotIn("url: https://hub.cristex-soft.com/", self.tasks_text)

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

    def test_adversarial_direct_invocation_and_public_dns_bypass_are_rejected(self) -> None:
        direct = subprocess.run(
            [str(WRAPPER)],
            check=False,
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin"},
        )
        self.assertEqual(64, direct.returncode)
        self.assertNotIn("ansible-playbook", direct.stdout + direct.stderr)
        self.assertNotIn("url: https://hub.cristex-soft.com/", self.tasks_text)
        self.assertIn("private_origin_url", self.tasks_text)
        self.assertIn("Host:", self.tasks_text)
        self.assertIn("WRAPPER_STARTTIME", self.tasks_text)
        self.assertIn("cristexhub_prod_private_acceptance_process_guarded", self.tasks_text)
        self.assertIn("exact private PROD acceptance process ancestry", self.tasks_text)
        self.assertIn("original_script_path", self.wrapper_text)
        self.assertIn('exec /bin/dash "$script_path" check', self.wrapper_text)
        self.assertIn("_proc_starttime", self.process_guard_text)

    def test_adversarial_extra_wrapper_arguments_are_rejected(self) -> None:
        result = subprocess.run(
            [str(WRAPPER), "check", "extra"],
            check=False,
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin"},
        )
        self.assertEqual(64, result.returncode)
        self.assertNotIn("ansible-playbook", result.stdout + result.stderr)

    def test_process_ancestry_helper_rejects_unrelated_process(self) -> None:
        spec = importlib.util.spec_from_file_location("private_acceptance_process_guard", PROCESS_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(module._ancestor(os.getpid()))
        unrelated = subprocess.Popen(["/bin/sleep", "2"])
        try:
            self.assertFalse(module._ancestor(unrelated.pid))
        finally:
            unrelated.terminate()
            unrelated.wait(timeout=5)
        self.assertTrue(module._proc_starttime(os.getpid()))
        self.assertEqual([], module._proc_cmdline(0))

    def test_process_guard_source_pins_match_current_bytes(self) -> None:
        def canonical(path: Path, symbol: str) -> str:
            source = path.read_text()
            source, count = re.subn(
                rf"(?m)^({re.escape(symbol)}\s*=\s*['\"])[0-9a-f]{{64}}(['\"]\s*)$",
                rf"\g<1>{'0' * 64}\g<2>",
                source,
            )
            self.assertEqual(1, count)
            return hashlib.sha256(source.encode()).hexdigest()

        self.assertEqual(
            canonical(WRAPPER, "wrapper_canonical_sha256_expected"),
            re.search(r"(?m)^wrapper_canonical_sha256_expected='([0-9a-f]{64})'$", self.wrapper_text).group(1),
        )
        self.assertEqual(
            canonical(PROCESS_GUARD, "_ACTION_CANONICAL_SHA256"),
            re.search(r'(?m)^_ACTION_CANONICAL_SHA256 = "([0-9a-f]{64})"$', self.process_guard_text).group(1),
        )
        wrapper_hashes = {
            name: value
            for name, value in re.findall(r"(?m)^([a-z_]+_sha256_expected)='([0-9a-f]{64})'$", self.wrapper_text)
        }
        for name, path in (
            ("task_sha256_expected", TASKS),
            ("defaults_sha256_expected", DEFAULTS),
            ("playbook_sha256_expected", PLAYBOOK),
            ("action_sha256_expected", PROCESS_GUARD),
        ):
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), wrapper_hashes[name])

    def test_process_guard_rejects_extra_ansible_argv(self) -> None:
        spec = importlib.util.spec_from_file_location("private_acceptance_process_guard_argv", PROCESS_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_argv = module.sys.argv
        original_cliargs = module.context.CLIARGS
        module.context.CLIARGS = {
            "start_at_task": None,
            "step": False,
            "tags": [],
            "skip_tags": [],
            "subset": "crtxweb",
            "check": True,
            "diff": True,
            "inventory": [str(module._INVENTORY_SOURCE)],
        }
        try:
            module.sys.argv = module._expected_argv()
            self.assertTrue(module._selection_is_canonical())
            module.sys.argv = module._expected_argv() + ["--forks", "1"]
            self.assertFalse(module._selection_is_canonical())
        finally:
            module.sys.argv = original_argv
            module.context.CLIARGS = original_cliargs

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
