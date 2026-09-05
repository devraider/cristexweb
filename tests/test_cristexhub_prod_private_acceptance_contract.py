from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
DEFAULTS = ANSIBLE / "roles/cristexhub_prod_private_acceptance/defaults/main.yml"
TASKS = ANSIBLE / "roles/cristexhub_prod_private_acceptance/tasks/main.yml"
PLAYBOOK = ANSIBLE / "playbooks/check_cristexhub_prod_private_acceptance.yml"
PROCESS_GUARD = ANSIBLE / "plugins/action/cristexhub_prod_private_acceptance_process_guarded.py"
STRATEGY = ANSIBLE / "plugins/strategy/cristexhub_prod_private_acceptance_guarded_linear.py"
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
        cls.strategy_text = STRATEGY.read_text()
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
        self.assertEqual(0o644, stat.S_IMODE(STRATEGY.stat().st_mode))
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
        combined = f"{self.tasks_text}\n{self.playbook_text}\n{self.wrapper_text}\n{self.process_guard_text}\n{self.strategy_text}"
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
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_VENV_PYTHON_TARGET",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_VENV_PYTHON_SHA256",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_ACTION_SHA256",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_STRATEGY_SHA256",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_STRATEGY_CANONICAL_SHA256",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_STRATEGY_ATTESTED",
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
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_STRATEGY_SHA256=",
            "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_STRATEGY_CANONICAL_SHA256=",
            "strategy_sha256_expected=",
            "strategy_canonical_sha256_expected=",
            "/usr/bin/python3 -I -",
            "wrapper_canonical_sha256_expected",
            "venv_python_sha256_expected=",
            "readlink -f",
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
        self.assertIn('"$playbook_source"', self.wrapper_text)
        self.assertIn("strategy: cristexhub_prod_private_acceptance_guarded_linear", self.playbook_text)
        for required in (
            "class StrategyModule(LinearStrategyModule)",
            "_canonical_argv",
            "_selection_contract",
            "_source_contract",
            "start_at_task",
            "skip_tags",
            "_STRATEGY_CANONICAL_SHA256",
            "_WRAPPER_CANONICAL_SHA256",
            "_collection_tree_contract",
            "STRATEGY_ATTESTED",
        ):
            self.assertIn(required, self.strategy_text)
        self.assertIn(":entrypoint:%s:%s:%s", self.wrapper_text)
        self.assertIn("Require source leaves and hashes bound to the canonical wrapper", self.tasks_text)
        for required in (
            "_ancestor",
            "_proc_parent",
            "_proc_starttime",
            "_proc_cmdline",
            "sys.argv == _expected_argv()",
            "_proc_cmdline(pid) == [\"/bin/dash\", str(_WRAPPER_SOURCE), \"check\"]",
            "STRATEGY_ATTESTED",
            "and _ancestor(pid)",
            "and _proc_starttime(pid) == starttime",
        ):
            self.assertIn(required, self.process_guard_text)
        self.assertNotIn("--start-at-task", self.wrapper_text)
        self.assertNotIn("--tags", self.wrapper_text)
        self.assertNotIn("--skip-tags", self.wrapper_text)

    def test_canonical_wrapper_invocation_matches_ansible_219_cli_shapes(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "private_acceptance_canonical_invocation", STRATEGY
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_argv = module.sys.argv
        original_cliargs = module.context.CLIARGS
        expected = [
            str(module._CONTROLLER_SOURCE),
            "-i",
            str(module._INVENTORY_SOURCE),
            str(module._PLAYBOOK_SOURCE),
            "--check",
            "--diff",
            "--limit",
            "crtxweb",
            "--extra-vars",
            '{"cristexhub_prod_private_acceptance_approved":true}',
        ]
        module.sys.argv = expected
        module.context.CLIARGS = {
            "start_at_task": None,
            "step": False,
            "tags": [],
            "skip_tags": [],
            "subset": "crtxweb",
            "check": True,
            "diff": True,
            # ansible-core 2.19 exposes inventory CLIARGS as a tuple.
            "inventory": (str(module._INVENTORY_SOURCE),),
        }
        try:
            self.assertEqual(
                [
                    str(module._CONTROLLER_SOURCE),
                    "-i",
                    str(module._INVENTORY_SOURCE),
                    str(module._PLAYBOOK_SOURCE),
                    "--check",
                    "--diff",
                    "--limit",
                    "crtxweb",
                    "--extra-vars",
                    '{"cristexhub_prod_private_acceptance_approved":true}',
                ],
                expected,
            )
            self.assertTrue(module._canonical_argv())
            self.assertTrue(module._selection_contract())
            self.assertIn("_regular_file(_CONTROLLER_SOURCE, 0o755)", self.strategy_text)
            self.assertIn("stat.S_IMODE(controller.st_mode) == 0o755", self.process_guard_text)
        finally:
            module.sys.argv = original_argv
            module.context.CLIARGS = original_cliargs

    def test_guarded_strategy_rejects_task_selection_and_alternate_argv(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "private_acceptance_guarded_strategy", STRATEGY
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_argv = module.sys.argv
        original_cliargs = module.context.CLIARGS
        expected = [str(module._CONTROLLER_SOURCE)] + [
            "-i",
            str(module._INVENTORY_SOURCE),
            str(module._PLAYBOOK_SOURCE),
            "--check",
            "--diff",
            "--limit",
            "crtxweb",
            "--extra-vars",
            '{"cristexhub_prod_private_acceptance_approved":true}',
        ]
        module.sys.argv = expected
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
            self.assertTrue(module._canonical_argv())
            self.assertTrue(module._selection_contract())
            for field, value in (
                ("start_at_task", "Query the exact PROD AppProject"),
                ("tags", ["queries"]),
                ("skip_tags", ["always"]),
            ):
                with self.subTest(field=field):
                    module.context.CLIARGS[field] = value
                    self.assertFalse(module._selection_contract())
                    module.context.CLIARGS[field] = {
                        "start_at_task": None,
                        "step": False,
                        "tags": [],
                        "skip_tags": [],
                        "subset": "crtxweb",
                        "check": True,
                        "diff": True,
                        "inventory": [str(module._INVENTORY_SOURCE)],
                    }[field]
            module.sys.argv = expected[:2] + [str(module._REPOSITORY_ROOT / "alternate.yml")] + expected[3:]
            self.assertFalse(module._canonical_argv())
        finally:
            module.sys.argv = original_argv
            module.context.CLIARGS = original_cliargs

    def test_every_post_guard_task_requires_process_guard_completion(self) -> None:
        task_names = self.tasks_text.count("- name: ")
        guarded_tasks = self.tasks_text.count(
            "cristexhub_prod_private_acceptance_internal_process_guard.process_guarded"
        )
        self.assertGreaterEqual(task_names, 36)
        self.assertEqual(task_names - 1, guarded_tasks)
        self.assertIn("tags: [always]", self.tasks_text)
        self.assertIn("cannot report success when", self.tasks_text)

    def test_exact_argocd_and_workload_contract_is_documented(self) -> None:
        normalized = " ".join(self.runbook_text.split())
        for required in (
            "LIVE READ-ONLY PREFLIGHT PASSED / FINAL ACCEPTANCE BLOCKED",
            "SOURCE-ONLY / CHECK-ONLY / NOT RUN",
            "Current parent live read-only evidence",
            "ok=37 changed=0 unreachable=0 failed=0 skipped=0",
            "preflight-pass-not-final-acceptance",
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
        testcases = (ROOT / "specs/k3s-iac-foundation/testcases.md").read_text()
        normalized_testcases = " ".join(testcases.split())
        for required in (
            "CristexHub PROD private acceptance preflight — CURRENT CHECK PASSED / FINAL ACCEPTANCE BLOCKED",
            "actual parent live read-only private acceptance preflight passed on 2026-08-26",
            "ok=37 changed=0 unreachable=0 failed=0 skipped=0",
            "preflight-pass-not-final-acceptance",
            "Final acceptance remains blocked by the independent NetworkPolicy enforcement",
        ):
            self.assertIn(required, normalized_testcases)

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

    def _wrapper_binding_fixture(self):
        spec = importlib.util.spec_from_file_location(
            "private_acceptance_operator_binding_guard", PROCESS_GUARD
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        prefix = "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_"
        token = "a" * 64
        wrapper_sha = module._sha256(module._WRAPPER_SOURCE)
        wrapper_canonical = module._wrapper_canonical_hash(module._WRAPPER_SOURCE)
        python_target = module._python_target()
        self.assertIsNotNone(python_target)
        module._VENV_PYTHON_TARGET = python_target
        module._EXPECTED_PYTHON_SHA256 = module._sha256(python_target)
        hash_values = {
            "TASK_SHA256": module._sha256(module._TASK_SOURCE),
            "DEFAULTS_SHA256": module._sha256(module._DEFAULTS_SOURCE),
            "PLAYBOOK_SHA256": module._sha256(module._PLAYBOOK_SOURCE),
            "ACTION_SHA256": module._sha256(module._ACTION_SOURCE),
            "STRATEGY_SHA256": module._sha256(module._STRATEGY_SOURCE),
            "INVENTORY_SHA256": module._sha256(module._INVENTORY_SOURCE),
            "ANSIBLE_CONFIG_SHA256": module._sha256(module._ANSIBLE_CONFIG_SOURCE),
            "CONTROLLER_SHA256": module._sha256(module._CONTROLLER_SOURCE),
            "PYTHON_SHA256": module._sha256(python_target),
            "VENV_PYTHON_SHA256": module._sha256(module._VENV_PYTHON_TARGET),
        }
        source_closure = ":".join(
            hash_values[name]
            for name in (
                "TASK_SHA256",
                "DEFAULTS_SHA256",
                "PLAYBOOK_SHA256",
                "ACTION_SHA256",
                "INVENTORY_SHA256",
                "ANSIBLE_CONFIG_SHA256",
                "CONTROLLER_SHA256",
                "PYTHON_SHA256",
                "VENV_PYTHON_SHA256",
                "STRATEGY_SHA256",
            )
        )
        attestation_fd, attestation_name = tempfile.mkstemp(prefix="cristexweb-operator-")
        os.close(attestation_fd)
        attestation_path = Path(attestation_name)
        attestation_path.chmod(0o600)
        pid = str(os.getpid())
        starttime = "123456"
        attestation_path.write_text(
            f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\n",
            encoding="utf-8",
        )
        environment = {
            prefix + "ENTRYPOINT": "v2",
            prefix + "TOKEN": token,
            prefix + "ATTESTATION_FILE": str(attestation_path),
            prefix + "WRAPPER_PID": pid,
            prefix + "WRAPPER_STARTTIME": starttime,
            prefix + "WRAPPER_PATH": str(module._WRAPPER_SOURCE),
            prefix + "WRAPPER_SHA256": wrapper_sha,
            prefix + "WRAPPER_CANONICAL_SHA256": wrapper_canonical,
            prefix + "STRATEGY_CANONICAL_SHA256": module._canonical_file_hash(
                module._STRATEGY_SOURCE, "_STRATEGY_CANONICAL_SHA256"
            ),
            prefix + "STRATEGY_ATTESTED": "v1",
            prefix + "SOURCE_CLOSURE_SHA256": hashlib.sha256(source_closure.encode()).hexdigest(),
            prefix + "CONTROLLER": str(module._CONTROLLER_SOURCE),
            prefix + "PYTHON": str(module._PYTHON_SOURCE),
            prefix + "VENV_PYTHON_TARGET": str(module._VENV_PYTHON_TARGET),
            prefix + "VENV_PYTHON_SHA256": module._EXPECTED_PYTHON_SHA256,
            prefix + "KUBECONFIG": str(module._EXPECTED_KUBECONFIG),
            "ANSIBLE_CONFIG": str(module._ANSIBLE_CONFIG_SOURCE),
            prefix + "OPERATOR": module._EXPECTED_OPERATOR,
        }
        environment.update({prefix + key: value for key, value in hash_values.items()})
        return module, environment, attestation_path

    def test_wrapper_binding_rejects_missing_or_forged_operator(self) -> None:
        module, environment, attestation_path = self._wrapper_binding_fixture()
        prefix = "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_"
        python_target = module._python_target()
        self.assertIsNotNone(python_target)
        try:
            with mock.patch.object(module, "_ancestor", return_value=True), mock.patch.object(
                module, "_proc_starttime", return_value="123456"
            ), mock.patch.object(
                module,
                "_proc_cmdline",
                return_value=["/bin/dash", str(module._WRAPPER_SOURCE), "check"],
            ), mock.patch.object(
                module, "_python_runtime_contract", return_value=True
            ), mock.patch.object(
                module, "_python_target", return_value=python_target
            ), mock.patch.object(
                module.context, "CLIARGS", {"check": True, "diff": True}
            ), mock.patch.dict(os.environ, environment, clear=False):
                self.assertTrue(
                    module._wrapper_binding_valid(
                        {"cristexhub_prod_private_acceptance_approved": True}
                    )
                )
                for operator in (None, "mallory", "paul:mallory"):
                    with self.subTest(operator=operator):
                        if operator is None:
                            os.environ.pop(prefix + "OPERATOR", None)
                        else:
                            os.environ[prefix + "OPERATOR"] = operator
                        self.assertFalse(
                            module._wrapper_binding_valid(
                                {"cristexhub_prod_private_acceptance_approved": True}
                            )
                        )
                        os.environ[prefix + "OPERATOR"] = module._EXPECTED_OPERATOR
        finally:
            attestation_path.unlink(missing_ok=True)

    def test_wrapper_binds_inventory_resolved_operator_without_override(self) -> None:
        self.assertIn("ansible_user:", self.wrapper_text)
        self.assertIn("inventory_operator", self.wrapper_text)
        self.assertIn(
            'CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_OPERATOR="$inventory_operator"',
            self.wrapper_text,
        )
        self.assertIn('[ "$inventory_operator" = paul ]', self.wrapper_text)
        self.assertIn('[ "$controller_user" = "$inventory_operator" ]', self.wrapper_text)
        self.assertIn(
            'os.environ.get(prefix + "OPERATOR") == _EXPECTED_OPERATOR',
            self.process_guard_text,
        )

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

    def test_python_source_contract_follows_canonical_system_symlink(self) -> None:
        spec = importlib.util.spec_from_file_location("private_acceptance_python_contract", PROCESS_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(module._PYTHON_SOURCE.is_symlink())
        target = module._PYTHON_SOURCE.resolve(strict=True)
        self.assertTrue(target.is_file())
        self.assertEqual(0, target.stat().st_uid)
        name = "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_PYTHON_SHA256"
        venv_target_name = "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_VENV_PYTHON_TARGET"
        venv_hash_name = "CRISTEXWEB_CRISTEXHUB_PROD_PRIVATE_ACCEPTANCE_VENV_PYTHON_SHA256"
        original = {key: os.environ.get(key) for key in (name, venv_target_name, venv_hash_name)}
        os.environ[name] = hashlib.sha256(target.read_bytes()).hexdigest()
        module._EXPECTED_PYTHON_SHA256 = os.environ[name]
        with tempfile.TemporaryDirectory() as directory:
            venv_python = Path(directory) / "python"
            venv_python.symlink_to("/usr/bin/python3")
            module._VENV_PYTHON_SOURCE = venv_python
            module._VENV_PYTHON_TARGET = target
            os.environ[venv_target_name] = str(target)
            os.environ[venv_hash_name] = os.environ[name]
            try:
                self.assertEqual(target, module._python_target())
                self.assertTrue(module._python_runtime_contract())
            finally:
                for key, value in original.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_python_source_contract_rejects_writable_or_non_linked_chains(self) -> None:
        spec = importlib.util.spec_from_file_location("private_acceptance_python_unsafe_contract", PROCESS_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.subTest("writable-parent-chain"):
            unsafe = Path("/tmp") / f"cristexweb-python-{os.getpid()}"
            target = unsafe.with_name(unsafe.name + ".target")
            try:
                target.write_bytes(b"#!/usr/bin/python3\\n")
                target.chmod(0o755)
                unsafe.symlink_to(target)
                module._PYTHON_SOURCE = unsafe
                self.assertIsNone(module._python_target())
            finally:
                unsafe.unlink(missing_ok=True)
                target.unlink(missing_ok=True)
        with self.subTest("regular-source-is-not-followed"):
            module._PYTHON_SOURCE = Path("/usr/bin/python3.13")
            self.assertIsNone(module._python_target())

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

        process_spec = importlib.util.spec_from_file_location("private_acceptance_wrapper_canonical", PROCESS_GUARD)
        self.assertIsNotNone(process_spec)
        self.assertIsNotNone(process_spec.loader)
        process_module = importlib.util.module_from_spec(process_spec)
        process_spec.loader.exec_module(process_module)
        self.assertEqual(
            process_module._wrapper_canonical_hash(WRAPPER),
            process_module._WRAPPER_CANONICAL_SHA256,
        )
        self.assertEqual(
            process_module._WRAPPER_CANONICAL_SHA256,
            re.search(r"(?m)^wrapper_canonical_sha256_expected='([0-9a-f]{64})'$", self.wrapper_text).group(1),
        )
        self.assertEqual(
            canonical(PROCESS_GUARD, "_ACTION_CANONICAL_SHA256"),
            re.search(r'(?m)^_ACTION_CANONICAL_SHA256 = "([0-9a-f]{64})"$', self.process_guard_text).group(1),
        )
        self.assertEqual(
            canonical(STRATEGY, "_STRATEGY_CANONICAL_SHA256"),
            re.search(r'(?m)^_STRATEGY_CANONICAL_SHA256 = "([0-9a-f]{64})"$', self.strategy_text).group(1),
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
            ("strategy_sha256_expected", STRATEGY),
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

    def test_collection_tree_contract_rejects_leaf_mutation_and_extra_artifact(self) -> None:
        spec = importlib.util.spec_from_file_location("private_acceptance_collection_contract", PROCESS_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "core"
            root.mkdir()
            root.chmod(0o755)
            for relative in ("plugins/action", "plugins/modules", "plugins/module_utils"):
                path = root / relative
                path.mkdir(parents=True)
                path.chmod(0o755)
            (root / "plugins").chmod(0o755)
            files = {
                "plugins/action/k8s_info.py": b"action\n",
                "plugins/modules/k8s_info.py": b"module\n",
                "plugins/module_utils/__init__.py": b"",
            }
            for relative, content in files.items():
                path = root / relative
                path.write_bytes(content)
                path.chmod(0o644)
            entries = [{"name": ".", "ftype": "dir", "chksum_type": None, "chksum_sha256": None, "format": 1}]
            for relative in ("plugins", "plugins/action", "plugins/modules", "plugins/module_utils"):
                entries.append({"name": relative, "ftype": "dir", "chksum_type": None, "chksum_sha256": None, "format": 1})
            for relative, content in files.items():
                entries.append({
                    "name": relative,
                    "ftype": "file",
                    "chksum_type": "sha256",
                    "chksum_sha256": hashlib.sha256(content).hexdigest(),
                    "format": 1,
                })
            files_manifest = root / "FILES.json"
            files_manifest.write_text(json.dumps({"files": entries}, sort_keys=True), encoding="utf-8")
            files_manifest.chmod(0o644)
            manifest = root / "MANIFEST.json"
            manifest.write_text(json.dumps({"collection_info": {"namespace": "kubernetes", "name": "core", "version": "6.1.0"}}, sort_keys=True), encoding="utf-8")
            manifest.chmod(0o644)
            requirements = Path(directory) / "requirements.yml"
            requirements.write_text("---\\ncollections: []\\n", encoding="utf-8")
            requirements.chmod(0o644)
            with mock.patch.object(module, "_COLLECTION_ROOT", root), mock.patch.object(module, "_COLLECTION_FILES_SOURCE", files_manifest), mock.patch.object(module, "_COLLECTION_MANIFEST_SOURCE", manifest), mock.patch.object(module, "_REQUIREMENTS_SOURCE", requirements), mock.patch.object(module, "_EXPECTED_COLLECTION_FILES_SHA256", hashlib.sha256(files_manifest.read_bytes()).hexdigest()), mock.patch.object(module, "_EXPECTED_COLLECTION_MANIFEST_SHA256", hashlib.sha256(manifest.read_bytes()).hexdigest()), mock.patch.object(module, "_EXPECTED_REQUIREMENTS_SHA256", hashlib.sha256(requirements.read_bytes()).hexdigest()), mock.patch.object(module, "_EXPECTED_COLLECTION_ACTION_SYMLINKS", set()):
                self.assertTrue(module._collection_tree_contract())
                (root / "plugins/modules/k8s_info.py").write_bytes(b"tampered\\n")
                self.assertFalse(module._collection_tree_contract())
                (root / "plugins/modules/k8s_info.py").write_bytes(files["plugins/modules/k8s_info.py"])
                (root / "plugins/action/extra.py").write_bytes(b"extra\\n")
                self.assertFalse(module._collection_tree_contract())

    def test_two_consecutive_disposable_collection_imports_do_not_create_bytecode(self) -> None:
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", self.wrapper_text)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module = root / "ansible_collections/kubernetes/core/plugins/action/k8s_info.py"
            module.parent.mkdir(parents=True)
            for parent in (
                root / "ansible_collections",
                root / "ansible_collections/kubernetes",
                root / "ansible_collections/kubernetes/core",
                root / "ansible_collections/kubernetes/core/plugins",
                root / "ansible_collections/kubernetes/core/plugins/action",
            ):
                (parent / "__init__.py").write_text("", encoding="utf-8")
            module.write_text("def run():\n    return 'ok'\n", encoding="utf-8")
            runner = (
                "import importlib, pathlib, sys; "
                "sys.path.insert(0, sys.argv[1]); "
                "assert importlib.import_module("
                "'ansible_collections.kubernetes.core.plugins.action.k8s_info').run() == 'ok'; "
                "assert not list(pathlib.Path(sys.argv[1]).rglob('__pycache__'))"
            )
            environment = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, "-S", "-c", runner, str(root)],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=environment,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual([], list(root.rglob("__pycache__")))

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
