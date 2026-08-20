from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/infisical-cristexhub-prod-runtime"
DEFAULTS = ROOT / "ansible/roles/infisical_cristexhub_prod_runtime_bootstrap/defaults/main.yml"
TASKS = ROOT / "ansible/roles/infisical_cristexhub_prod_runtime_bootstrap/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/infisical_cristexhub_prod_runtime_guarded_k8s.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-infisical-cristexhub-prod-runtime"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_infisical_cristexhub_prod_runtime.yml"
POLICY = ROOT / "ansible/files/policies/cristexhub-prod-runtime-materialization.yml"
HOSTED_POLICY = ROOT / "ansible/files/policies/hosted-identity-authorization.yml"
ACTION_ONLY = ROOT / "tests/reject_infisical_cristexhub_prod_runtime_action_only.yml"

NAMESPACE = "cristexhub-prod"
COMPONENT_NAME = "infisical-cristexhub-prod-runtime"
PROJECT_ID = "619656da-14f3-4872-857b-be103cdc5326"
RUNTIME_NAME = "cristexhub-prod-runtime"
PULL_NAME = "cristexhub-prod-ghcr-pull"
AUTH_NAME = "cristexhub-prod-infisical-auth"
UNIVERSAL_AUTH_NAME = "cristexhub-prod-infisical-universal-auth"
RUNTIME_KEYS = [
    "MONGODB_URL",
    "RABBITMQ_URL",
    "REDIS_URL",
    "REDIS_PASSWORD",
    "FERNET_KEY",
    "OIDC_CLIENT_SECRET",
    "OAUTH2_PROXY_COOKIE_SECRET",
    "PRIVATE_CA_BUNDLE",
    "CODE_RUNNER_AUTH_TOKEN",
]


class InfisicalCristexhubProdRuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = sorted(COMPONENT.rglob("*.yaml"))
        cls.objects = [yaml.safe_load(path.read_text()) for path in cls.paths]
        cls.by_identity = {
            (
                obj["apiVersion"],
                obj["kind"],
                obj["metadata"].get("namespace", ""),
                obj["metadata"]["name"],
            ): obj
            for obj in cls.objects
        }
        cls.text = "\n".join(path.read_text() for path in cls.paths)
        cls.policy = yaml.safe_load(POLICY.read_text())
        cls.hosted_policy = yaml.safe_load(HOSTED_POLICY.read_text())

    def test_exact_value_free_object_closure(self) -> None:
        self.assertEqual(13, len(self.objects))
        self.assertEqual(13, len(self.by_identity))
        self.assertFalse(any(obj["kind"] == "Secret" for obj in self.objects))
        self.assertEqual(
            {
                "ValidatingAdmissionPolicy": 4,
                "ValidatingAdmissionPolicyBinding": 4,
                "Role": 1,
                "RoleBinding": 1,
                "InfisicalConnection": 1,
                "InfisicalAuth": 1,
                "InfisicalStaticSecret": 1,
            },
            {
                kind: sum(obj["kind"] == kind for obj in self.objects)
                for kind in {obj["kind"] for obj in self.objects}
            },
        )
        for obj in self.objects:
            self.assertEqual(NAMESPACE, obj["metadata"].get("namespace", NAMESPACE))
            self.assertEqual("ansible", obj["metadata"]["labels"]["app.kubernetes.io/managed-by"])
            self.assertEqual(COMPONENT_NAME, obj["metadata"]["labels"]["cristex.io/component"])

    def test_exact_prod_source_identity_and_targets(self) -> None:
        static = next(obj for obj in self.objects if obj["kind"] == "InfisicalStaticSecret")
        self.assertEqual(NAMESPACE, static["metadata"]["namespace"])
        self.assertEqual(AUTH_NAME, static["spec"]["infisicalAuthRef"]["name"])
        self.assertEqual(NAMESPACE, static["spec"]["infisicalAuthRef"]["namespace"])
        self.assertEqual(
            {
                "projectId": PROJECT_ID,
                "environmentSlug": "prod",
                "secretPath": "/cristexhub/prod/runtime",
                "recursive": False,
                "tagSlugs": [],
            },
            static["spec"]["sources"][0],
        )
        self.assertEqual("1h", static["spec"]["syncOptions"]["refreshInterval"])
        self.assertFalse(static["spec"]["syncOptions"]["instantUpdates"])
        targets = static["spec"]["targets"]
        self.assertEqual([RUNTIME_NAME, PULL_NAME], [target["name"] for target in targets])
        self.assertEqual(set(RUNTIME_KEYS), set(targets[0]["template"]["data"]))
        self.assertEqual(
            "{{ .OIDC_CLIENT_SECRET.Value }}",
            targets[0]["template"]["data"]["OIDC_CLIENT_SECRET"],
        )
        self.assertEqual("Opaque", targets[0]["secretType"])
        self.assertEqual("kubernetes.io/dockerconfigjson", targets[1]["secretType"])
        self.assertEqual({".dockerconfigjson"}, set(targets[1]["template"]["data"]))
        self.assertEqual("{{ .DOCKER_CONFIG_JSON.Value }}", targets[1]["template"]["data"][".dockerconfigjson"])
        for target in targets:
            self.assertEqual(NAMESPACE, target["namespace"])
            self.assertEqual("Secret", target["kind"])
            self.assertEqual("Orphan", target["creationPolicy"])
            self.assertEqual(
                {
                    "app.kubernetes.io/managed-by": "infisical",
                    "app.kubernetes.io/part-of": "cristexhub",
                    "cristex.io/value-owner": "infisical-cloud",
                },
                target["metadata"]["labels"],
            )

        auth = next(obj for obj in self.objects if obj["kind"] == "InfisicalAuth")
        self.assertEqual(AUTH_NAME, auth["metadata"]["name"])
        self.assertEqual("universal", auth["spec"]["method"])
        self.assertEqual(UNIVERSAL_AUTH_NAME, auth["spec"]["universal"]["clientIdRef"]["name"])
        self.assertEqual(UNIVERSAL_AUTH_NAME, auth["spec"]["universal"]["clientSecretRef"]["name"])
        self.assertEqual(NAMESPACE, auth["spec"]["universal"]["clientIdRef"]["namespace"])
        self.assertEqual(NAMESPACE, auth["spec"]["universal"]["clientSecretRef"]["namespace"])
        connection = next(obj for obj in self.objects if obj["kind"] == "InfisicalConnection")
        self.assertEqual(NAMESPACE, connection["metadata"]["namespace"])
        self.assertEqual({"address": "https://app.infisical.com"}, connection["spec"])

    def test_prod_oidc_source_contract_matches_hosted_identity_policy(self) -> None:
        source = self.policy["oidc_client_secret_source"]
        self.assertEqual(
            {
                "owner": "infisical-cloud",
                "project_id": PROJECT_ID,
                "environment_slug": "prod",
                "path": "/cristexhub/prod/runtime",
                "key": "OIDC_CLIENT_SECRET",
                "target_key": "OIDC_CLIENT_SECRET",
                "values": "absent",
            },
            source,
        )
        prod = {
            entry["id"]: entry for entry in self.hosted_policy["clients"]["browser"]
        }["cristexhub-prod"]
        self.assertEqual(
            f'{source["environment_slug"]}:{source["path"]}',
            prod["client_secret_path"],
        )
        self.assertEqual(source["owner"], prod["client_secret_owner"])
        self.assertEqual(source["key"], prod["client_secret_key"])
        self.assertEqual(source["project_id"], self.policy["project"]["id"])
        self.assertEqual(source["environment_slug"], self.policy["project"]["environment"])
        self.assertEqual(source["path"], self.policy["project"]["source_path"])
        self.assertEqual(source["path"], self.policy["sources"]["infisical"]["path"])
        static = next(obj for obj in self.objects if obj["kind"] == "InfisicalStaticSecret")
        self.assertEqual(
            {
                "projectId": source["project_id"],
                "environmentSlug": source["environment_slug"],
                "secretPath": source["path"],
                "recursive": False,
                "tagSlugs": [],
            },
            static["spec"]["sources"][0],
        )
        self.assertIn("_EXPECTED_OIDC_CLIENT_SECRET_SOURCE", PLUGIN.read_text())
        self.assertIn("_EXPECTED_OIDC_CLIENT_SECRET_TEMPLATE", PLUGIN.read_text())
        self.assertIn(
            "prod:/cristexhub/prod/runtime#OIDC_CLIENT_SECRET",
            (COMPONENT / "source/cristexhub-prod-runtime-static-secret.yaml").read_text(),
        )
        runtime_data = static["spec"]["targets"][0]["template"]["data"]
        self.assertEqual(source["target_key"], "OIDC_CLIENT_SECRET")
        self.assertEqual(
            "{{ .OIDC_CLIENT_SECRET.Value }}",
            runtime_data[source["target_key"]],
        )
        self.assertIn(source["target_key"], self.policy["target_keys"])

    def test_fail_closed_vaps_are_prod_scoped_and_exact(self) -> None:
        policies = [obj for obj in self.objects if obj["kind"] == "ValidatingAdmissionPolicy"]
        bindings = [obj for obj in self.objects if obj["kind"] == "ValidatingAdmissionPolicyBinding"]
        self.assertEqual(4, len(policies))
        self.assertEqual(4, len(bindings))
        self.assertTrue(all(policy["spec"]["failurePolicy"] == "Fail" for policy in policies))
        self.assertTrue(all(binding["spec"]["validationActions"] == ["Deny"] for binding in bindings))
        for policy in policies:
            conditions = policy["spec"].get("matchConditions", [])
            self.assertTrue(any("cristexhub-prod" in condition["expression"] for condition in conditions))
            self.assertNotIn("cristexhub-dev", json.dumps(policy))
        static = next(policy for policy in policies if "static-secret" in policy["metadata"]["name"])
        static_expression = json.dumps(static["spec"]["validations"])
        for required in (NAMESPACE, RUNTIME_NAME, PULL_NAME, "/cristexhub/prod/runtime", "CODE_RUNNER_AUTH_TOKEN", ".dockerconfigjson"):
            self.assertIn(required, static_expression)
        source = next(policy for policy in policies if "source-boundary" in policy["metadata"]["name"])
        source_expression = json.dumps(source["spec"]["validations"])
        for required in (AUTH_NAME, UNIVERSAL_AUTH_NAME, "clientId", "clientSecret"):
            self.assertIn(required, source_expression)
        secret_write = next(
            policy for policy in policies
            if "secret-write-boundary" in policy["metadata"]["name"]
        )
        secret_write_expression = json.dumps(secret_write["spec"]["validations"])
        self.assertIn("secrets.infisical.com/version", secret_write_expression)
        self.assertIn("annotations.size() == 1", secret_write_expression)
        self.assertIn("metadata.finalizers", secret_write_expression)
        self.assertNotIn("binaryData", secret_write_expression)
        self.assertNotIn("!= null", secret_write_expression)
        self.assertIn(".size() > 0", secret_write_expression)
        self.assertIn("dyn(object).spec", source_expression)
        static_policy = next(policy for policy in policies if "static-secret-boundary" in policy["metadata"]["name"])
        self.assertIn("dyn(object.spec.targets[0].template).data", json.dumps(static_policy["spec"]["validations"]))
        alternate = next(policy for policy in policies if "alternate-target" in policy["metadata"]["name"])
        self.assertEqual("Namespaced", alternate["spec"]["matchConstraints"]["resourceRules"][0]["scope"])
        self.assertEqual(NAMESPACE, alternate["spec"]["matchConditions"][0]["expression"].split("== ", 1)[1].strip("'"))

    def test_secret_writer_rbac_is_least_privilege(self) -> None:
        role = next(obj for obj in self.objects if obj["kind"] == "Role")
        self.assertEqual(NAMESPACE, role["metadata"]["namespace"])
        update_rule = next(rule for rule in role["rules"] if "resourceNames" in rule)
        self.assertEqual([RUNTIME_NAME, PULL_NAME], update_rule["resourceNames"])
        self.assertEqual(["update"], update_rule["verbs"])
        verbs = {verb for rule in role["rules"] for verb in rule["verbs"]}
        self.assertNotIn("delete", verbs)
        self.assertNotIn("patch", verbs)
        self.assertNotIn("impersonate", verbs)
        binding = next(obj for obj in self.objects if obj["kind"] == "RoleBinding")
        self.assertEqual(
            [{"kind": "ServiceAccount", "name": "infisical-operator-controller", "namespace": "shared-services"}],
            binding["subjects"],
        )
        self.assertEqual(role["metadata"]["name"], binding["roleRef"]["name"])

    def test_manifest_ledger_defaults_and_action_hashes_are_current(self) -> None:
        ledger = {
            relative: digest
            for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines()
            if line.strip()
            for digest, relative in [line.split("  ", 1)]
        }
        actual = {
            path.relative_to(COMPONENT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.paths
        }
        self.assertEqual(actual, ledger)
        defaults = yaml.safe_load(DEFAULTS.read_text())
        configured = {
            item["path"].split("/ansible/files/components/infisical-cristexhub-prod-runtime/", 1)[1]: item["sha256"]
            for item in defaults["cristexhub_prod_runtime_bootstrap_expected_hashes"]
        }
        self.assertEqual(actual, configured)
        literal = PLUGIN.read_text().split("_EXPECTED_OBJECT_HASHES: dict", 1)[1].split(" = ", 1)[1].split("\n_EXPECTED_IDENTITY_SET_SHA256", 1)[0]
        action_hashes = ast.literal_eval(literal)
        expected_action_hashes = {
            (
                obj["apiVersion"],
                obj["kind"],
                obj["metadata"].get("namespace", ""),
                obj["metadata"]["name"],
            ): hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            for obj in self.objects
        }
        self.assertEqual(expected_action_hashes, action_hashes)
        identity = "\n".join(sorted("|".join(key) for key in expected_action_hashes))
        expected_identity_hash = hashlib.sha256(identity.encode()).hexdigest()
        self.assertIn(f'_EXPECTED_IDENTITY_SET_SHA256 = "{expected_identity_hash}"', PLUGIN.read_text())
        self.assertIn(f"identity_set_sha256: {expected_identity_hash}", TASKS.read_text())

    def test_guarded_role_wrapper_and_policy_are_blocked_without_values(self) -> None:
        tasks = TASKS.read_text()
        for required in (
            "ansible_diff_mode",
            "status.phase == 'Active'",
            "cristexhub-prod-infisical-universal-auth",
            "BLOCKED:",
            "No mutation was attempted",
            "metadata.ownerReferences",
            "Infisical Operator PROD checkpoint is separately approved",
            "watch/RBAC/admission",
            "infisical-static-secret-boundary",
            "--namespaces=shared-services,argocd,cristexhub-dev,cristexhub-prod,platform-edge",
            "expected_hashes | length == 13",
        ):
            self.assertIn(required, tasks)
        self.assertIn("become: false", PLAYBOOK.read_text())
        wrapper = WRAPPER.read_text()
        for required in (
            "check|apply",
            "--diff",
            "--limit crtxweb",
            "CRISTEXWEB_CRISTEXHUB_PROD_RUNTIME_TOKEN",
            "env -i",
        ):
            self.assertIn(required, wrapper)
        action_only = subprocess.run(
            [
                str(ROOT / ".venv/bin/ansible-playbook"),
                "-i",
                "localhost,",
                "-c",
                "local",
                str(ACTION_ONLY),
            ],
            cwd=ROOT / "ansible",
            env={
                **os.environ,
                "ANSIBLE_CONFIG": str(ROOT / "ansible/ansible.cfg"),
                "CRISTEXWEB_REPOSITORY_ROOT": str(ROOT),
            },
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(0, action_only.returncode)
        self.assertIn(
            "outside the canonical guarded role task source",
            action_only.stdout + action_only.stderr,
        )
        self.assertNotIn("Failed to connect", action_only.stdout + action_only.stderr)

        self.assertNotIn("clientSecret:", self.text)
        self.assertFalse(any(obj["kind"] == "Secret" for obj in self.objects))
        self.assertNotIn("cristexhub-dev", self.text)
        self.assertEqual(stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH, WRAPPER.stat().st_mode & 0o111)
        bad = subprocess.run([str(WRAPPER), "other"], cwd=ROOT, text=True, capture_output=True)
        self.assertNotEqual(0, bad.returncode)
        self.assertNotIn("Failed to connect", bad.stdout + bad.stderr)

        policy = yaml.safe_load(POLICY.read_text())
        self.assertEqual("prod", policy["project"]["environment"])
        self.assertEqual("/cristexhub/prod/runtime", policy["project"]["target_path"])
        self.assertEqual(NAMESPACE, policy["project"]["target_namespace"])
        self.assertEqual(RUNTIME_KEYS, policy["target_keys"])
        self.assertEqual(UNIVERSAL_AUTH_NAME, policy["authorization"]["universal_auth_secret"]["name"])
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(
            {"name": RUNTIME_NAME, "namespace": NAMESPACE, "type": "Opaque", "keys": RUNTIME_KEYS},
            defaults["cristexhub_prod_runtime_bootstrap_target_contract"]["runtime"],
        )
        self.assertEqual(
            {"name": PULL_NAME, "namespace": NAMESPACE, "type": "kubernetes.io/dockerconfigjson", "keys": [".dockerconfigjson"]},
            defaults["cristexhub_prod_runtime_bootstrap_target_contract"]["ghcr_pull"],
        )
        self.assertEqual("APPLIED/IDEMPOTENT", policy["workflow"]["runtime_execution"])
        self.assertTrue(policy["authorization"]["no_plaintext_output"])

    def test_runtime_runbook_records_materialization_and_remaining_rotation_gate(self) -> None:
        runbook = ROOT / "runbooks/infisical-cristexhub-prod-runtime-materialization.md"
        text = runbook.read_text()
        for required in (
            "APPLIED / MATERIALIZED / IDEMPOTENT",
            "cristexhub-prod",
            "cristexhub-prod-infisical-universal-auth",
            "/cristexhub/prod/runtime",
            "cristexhub-prod-ghcr-pull",
            "ok=62 changed=0 failed=0 skipped=3",
            "Synced/Healthy",
            "still require separately verified rotation",
        ):
            self.assertIn(required, text)

    def test_operator_prod_watch_source_remains_value_free_after_runtime_activation(self) -> None:
        component = ROOT / "ansible/files/components/infisical-operator"
        deployment = (component / "controller/deployment.yaml").read_text()
        self.assertIn(
            "--namespaces=shared-services,argocd,cristexhub-dev,cristexhub-prod,platform-edge",
            deployment,
        )
        self.assertTrue((component / "rbac/manager-role-cristexhub-prod.yaml").exists())
        self.assertTrue((component / "rbac/manager-rolebinding-cristexhub-prod.yaml").exists())
        generic_prod_allowlist = {
            "infisical-auth-boundary.yaml",
            "infisical-connection-boundary.yaml",
            "infisical-static-secret-boundary.yaml",
        }
        for policy in (component / "admission").glob("*.yaml"):
            if policy.name.endswith("-binding.yaml"):
                continue
            text = policy.read_text()
            if policy.name in generic_prod_allowlist:
                self.assertIn("cristexhub-prod", text, policy)
            else:
                self.assertNotIn("cristexhub-prod", text, policy)
        source = "\n".join(path.read_text() for path in component.rglob("*.yaml"))
        self.assertNotIn("kind: Secret", source)
        for path in component.rglob("*.yaml"):
            obj = yaml.safe_load(path.read_text())
            if obj.get("metadata", {}).get("namespace") == "cristexhub-prod":
                self.assertIn(obj["kind"], {"Role", "RoleBinding"}, path)
        runbook = (ROOT / "runbooks/infisical-cristexhub-prod-runtime-materialization.md").read_text()
        self.assertIn("now watches `cristexhub-prod`", runbook)
        self.assertIn("watch/RBAC expansion is applied/idempotent", runbook)
        self.assertIn("seam created the exact Connection, Auth", runbook)
        self.assertIn("created no Namespace, PVC, database engine", runbook)
        self.assertIn("separately approved runtime", runbook)
        tasks = TASKS.read_text()
        parsed_tasks = yaml.safe_load(tasks)
        credential_task = next(
            task for task in parsed_tasks
            if task.get("name") == "Refuse absent runtime Universal Auth prerequisite before any mutation"
        )
        self.assertTrue(credential_task.get("no_log"))
        self.assertIn("kubernetes.core.k8s_info", credential_task)
        credential_assertion = next(
            task for task in parsed_tasks
            if task.get("name") == "Stop until runtime Universal Auth is separately materialized"
        )
        self.assertTrue(credential_assertion.get("no_log"))
        checkpoint = tasks.index("Stop until the Infisical Operator PROD checkpoint")
        credential = tasks.index("Refuse absent runtime Universal Auth prerequisite")
        prestate = tasks.index("Query exact runtime seam object pre-state")
        admission = tasks.index("Reconcile exact runtime seam admission policies first")
        bindings = tasks.index("Reconcile exact runtime seam admission bindings second")
        race = tasks.index("Refuse Infisical CR or Secret UID/resourceVersion races")
        rbac = tasks.index("Reconcile exact runtime seam RBAC after admission and race checks")
        connection_apply = tasks.index("Reconcile canonical PROD Infisical Connection first")
        auth_preapply = tasks.index("Recheck canonical PROD Infisical Auth immediately before apply")
        auth_apply = tasks.index("Reconcile canonical PROD Infisical Auth second")
        static_preapply = tasks.index("Recheck canonical PROD StaticSecret immediately before apply")
        source_apply = tasks.index("Reconcile canonical PROD Infisical StaticSecret last")
        source_ready = tasks.index("Wait for PROD Connection Auth and StaticSecret reconciliation readiness")
        target_poststate = tasks.index("Require exact generated PROD runtime target Secret post-state")
        self.assertLess(checkpoint, credential)
        self.assertLess(checkpoint, prestate)
        self.assertLess(prestate, admission)
        self.assertLess(admission, bindings)
        admission_recheck = tasks.index("Requery exact runtime admission policies immediately before PROD RBAC")
        nonadmission_recheck = tasks.index("Recheck exact runtime RBAC and source objects before granting PROD RBAC")
        credential_recheck = tasks.index("Recheck Universal Auth credential after granting PROD RBAC")
        source_recheck = tasks.index("Recheck exact runtime source objects after granting PROD RBAC")
        self.assertLess(bindings, race)
        self.assertLess(race, nonadmission_recheck)
        self.assertLess(nonadmission_recheck, admission_recheck)
        self.assertLess(admission_recheck, rbac)
        self.assertLess(rbac, credential_recheck)
        self.assertLess(credential_recheck, source_recheck)
        self.assertLess(source_recheck, connection_apply)
        self.assertLess(connection_apply, auth_preapply)
        self.assertLess(auth_preapply, auth_apply)
        self.assertLess(auth_apply, static_preapply)
        self.assertLess(static_preapply, source_apply)
        self.assertLess(source_apply, source_ready)
        self.assertLess(source_ready, target_poststate)
        for required in (
            "status.observedGeneration == item.resources[0].metadata.generation",
            "status.typeChecking.expressionWarnings",
            "Requery exact runtime admission policies immediately before PROD RBAC",
            "Require exact ready and effective runtime admission closure before PROD RBAC",
            "Recheck exact runtime RBAC and source objects before granting PROD RBAC",
            "Refuse runtime RBAC or source object UID resourceVersion races",
            "Recheck exact runtime source objects after granting PROD RBAC",
            "Recheck Universal Auth credential immediately before Infisical Auth",
            "Recheck Universal Auth credential immediately before StaticSecret",
            "Recheck canonical PROD Infisical Auth immediately before apply",
            "Recheck canonical PROD StaticSecret immediately before apply",
            "Requery exact Operator PROD prerequisites immediately before writer RBAC",
            "metadata.finalizers",
            "cristexhub_prod_runtime_bootstrap_kubeconfig == '/etc/rancher/k3s/k3s.yaml'",
            "kubectl.kubernetes.io/restartedAt",
            "cristex.io/identity-access-generation",
            "cristex.io/proxy-config-sha256",
        ):
            self.assertIn(required, tasks)

        generic_policy_query = next(
            item for item in parsed_tasks
            if item.get("name") == "Query generic Infisical admission prerequisites"
        )
        self.assertEqual(
            ["infisical-auth-boundary", "infisical-connection-boundary", "infisical-static-secret-boundary"],
            generic_policy_query["loop"],
        )
        partition = next(
            item for item in parsed_tasks
            if item.get("name") == "Require exact 13-object value-free closure"
        )
        self.assertIn("cristexhub_prod_runtime_identity_keys[8:]", " ".join(partition["ansible.builtin.assert"]["that"]))

        for task_name in (
            "Query every Secret in the PROD Namespace before mutation",
            "Reject drifted existing PROD target Secret contracts",
            "Recheck all PROD Secrets before granting PROD RBAC",
            "Require exact generated PROD runtime target Secret post-state",
        ):
            task = next(item for item in parsed_tasks if item.get("name") == task_name)
            self.assertTrue(task.get("no_log"), task_name)

        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(
            [
                {"kind": "InfisicalSecret", "api_version": "secrets.infisical.com/v1alpha1"},
                {"kind": "InfisicalPushSecret", "api_version": "secrets.infisical.com/v1alpha1"},
                {"kind": "InfisicalDynamicSecret", "api_version": "secrets.infisical.com/v1alpha1"},
                {"kind": "InfisicalConnection", "api_version": "secrets.infisical.com/v1beta1"},
                {"kind": "InfisicalAuth", "api_version": "secrets.infisical.com/v1beta1"},
                {"kind": "InfisicalStaticSecret", "api_version": "secrets.infisical.com/v1beta1"},
            ],
            defaults["cristexhub_prod_runtime_bootstrap_expected_cr_kinds"],
        )
        plugin = PLUGIN.read_text()
        self.assertIn("_strict_integer", plugin)
        self.assertNotIn("def _integer", plugin)
        plugin_tree = ast.parse(plugin)
        strict_integer_node = next(
            node for node in plugin_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_strict_integer"
        )
        strict_integer_module = ast.Module(
            body=[ast.ImportFrom(module="typing", names=[ast.alias(name="Any")], level=0), strict_integer_node],
            type_ignores=[],
        )
        namespace: dict[str, object] = {}
        exec(compile(ast.fix_missing_locations(strict_integer_module), str(PLUGIN), "exec"), namespace)
        strict_integer = namespace["_strict_integer"]
        self.assertTrue(strict_integer(3, 3))
        for forged_count in (True, False, "3", 3.0, None):
            self.assertFalse(strict_integer(forged_count, 3), forged_count)
        self.assertFalse(strict_integer(2, 3))
        self.assertIn('binding.get("identity_keys_sha256")', plugin)
        self.assertGreaterEqual(plugin.count("_strict_integer(binding.get("), 7)
        self.assertIn("_EXPECTED_TASK_SUFFIX", plugin)
        self.assertIn('os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")', plugin)
        wrapper_text = WRAPPER.read_text()
        self.assertIn('CRISTEXWEB_REPOSITORY_ROOT="$repository_root"', wrapper_text)
        self.assertIn("status --porcelain --untracked-files=all", wrapper_text)
        self.assertIn("devraider/cristexweb.git", wrapper_text)
        self.assertIn("rev-parse --show-toplevel", wrapper_text)
        self.assertIn("GIT_CONFIG_NOSYSTEM=1", wrapper_text)
        self.assertIn("GIT_CONFIG_GLOBAL=/dev/null", wrapper_text)
        self.assertIn("GIT_OPTIONAL_LOCKS=0", wrapper_text)
        self.assertIn("core.fsmonitor=false", wrapper_text)
        self.assertIn("core.hooksPath=/dev/null", wrapper_text)
        self.assertIn('[ ! -L "$controller" ]', wrapper_text)
        self.assertNotIn("_EXPECTED_TASK_SOURCES", plugin)


if __name__ == "__main__":
    unittest.main()
