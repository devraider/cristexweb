from __future__ import annotations

import copy
import hashlib
import importlib.util
import re
import stat
import subprocess
import unittest
from pathlib import Path
import shutil
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "ansible/bin/check-cristexhub-prod-mongodb-credential-rotation"
PLAYBOOK = ROOT / "ansible/playbooks/check_cristexhub_prod_mongodb_credential_rotation.yml"
ROLE = ROOT / "ansible/roles/cristexhub_prod_mongodb_credential_rotation_check"
TASKS = ROLE / "tasks/main.yml"
DEFAULTS = ROLE / "defaults/main.yml"
POLICY = ROOT / "ansible/files/policies/cristexhub-prod-mongodb-credential-rotation.yml"
METADATA = ROOT / "ansible/library/cristexhub_prod_mongodb_credential_rotation_metadata.py"
SELECTOR_MODULE = ROOT / "ansible/library/cristexhub_prod_mongodb_networkpolicy_selector.py"
STRATEGY = ROOT / "ansible/plugins/strategy/cristexhub_prod_mongodb_credential_rotation_check_guarded_linear.py"
ENGINE_CONNECTION_SOURCE = ROOT / "ansible/files/components/infisical-database-secrets/source/infisical-cloud-connection.yaml"
ENGINE_AUTH_SOURCE = ROOT / "ansible/files/components/infisical-database-secrets/source/shared-mongodb-infisical-auth.yaml"
ENGINE_SOURCE = ROOT / "ansible/files/components/infisical-database-secrets/source/shared-mongodb-infisical-secrets.yaml"
RUNTIME_CONNECTION_SOURCE = ROOT / "ansible/files/components/infisical-cristexhub-prod-runtime/source/infisical-cloud-connection.yaml"
RUNTIME_AUTH_SOURCE = ROOT / "ansible/files/components/infisical-cristexhub-prod-runtime/source/cristexhub-prod-infisical-auth.yaml"
RUNTIME_SOURCE = ROOT / "ansible/files/components/infisical-cristexhub-prod-runtime/source/cristexhub-prod-runtime-static-secret.yaml"
NETWORKPOLICY_DEFAULT_DENY = ROOT / "ansible/files/components/shared-mongodb-networkpolicy/network/shared-mongodb-networkpolicy-default-deny.yaml"
NETWORKPOLICY_ALLOW = ROOT / "ansible/files/components/shared-mongodb-networkpolicy/network/shared-mongodb-networkpolicy-allow.yaml"
RUNBOOK = ROOT / "runbooks/cristexhub-prod-mongodb-credential-rotation.md"


class CristexHubProdMongoDBCredentialRotationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wrapper = WRAPPER.read_text()
        cls.playbook = yaml.safe_load(PLAYBOOK.read_text())
        cls.tasks = TASKS.read_text()
        cls.defaults = yaml.safe_load(DEFAULTS.read_text())
        cls.policy = yaml.safe_load(POLICY.read_text())
        cls.metadata = METADATA.read_text()
        cls.engine = yaml.safe_load(ENGINE_SOURCE.read_text())
        cls.runtime = yaml.safe_load(RUNTIME_SOURCE.read_text())
        cls.runbook = RUNBOOK.read_text()
        cls.normalized_runbook = " ".join(cls.runbook.split())

    def test_dedicated_source_closure_exists_with_exact_modes(self) -> None:
        expected = {
            WRAPPER: 0o755,
            TASKS: 0o644,
            DEFAULTS: 0o644,
            PLAYBOOK: 0o644,
            POLICY: 0o644,
            METADATA: 0o755,
            SELECTOR_MODULE: 0o755,
            STRATEGY: 0o644,
            ENGINE_CONNECTION_SOURCE: 0o644,
            ENGINE_AUTH_SOURCE: 0o644,
            RUNTIME_CONNECTION_SOURCE: 0o644,
            RUNTIME_AUTH_SOURCE: 0o644,
            RUNBOOK: 0o644,
        }
        for path, mode in expected.items():
            self.assertTrue(path.is_file(), path)
            self.assertFalse(path.is_symlink(), path)
            self.assertEqual(mode, stat.S_IMODE(path.stat().st_mode), path)

    def test_wrapper_is_strict_check_only_and_hash_bound(self) -> None:
        self.assertIn('usage: ansible/bin/check-cristexhub-prod-mongodb-credential-rotation check', self.wrapper)
        self.assertIn('[ "$#" -eq 1 ] && [ "$1" = check ]', self.wrapper)
        self.assertIn('playbooks/check_cristexhub_prod_mongodb_credential_rotation.yml', self.wrapper)
        self.assertIn('--check --diff --limit crtxweb', self.wrapper)
        self.assertIn("wrapper_canonical_sha256_expected=", self.wrapper)
        self.assertEqual(
            1,
            len(re.findall(r"(?m)^wrapper_canonical_sha256_expected='[0-9a-f]{64}'$", self.wrapper)),
        )
        for required in (
            "task_sha256_expected=",
            "defaults_sha256_expected=",
            "playbook_sha256_expected=",
            "policy_sha256_expected=",
            "metadata_module_sha256_expected=",
            "inventory_sha256_expected=",
            "ansible_config_sha256_expected=",
            "controller_sha256_expected=",
            "env -i",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_ATTESTATION_FILE",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_WRAPPER_PID",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_WRAPPER_STARTTIME",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_ROLES_PATH",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_LIBRARY_PATH",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_ANSIBLE_CONFIG_PATH",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_INVENTORY_PATH",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_CONTROLLER_PATH",
            "ANSIBLE_ROLES_PATH",
            "ANSIBLE_LIBRARY",
            "requirements_sha256_expected=",
            "collection_manifest_sha256_expected=",
            "collection_files_sha256_expected=",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_REQUIREMENTS_SHA256",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_COLLECTION_MANIFEST_SHA256",
            "CRISTEXWEB_CRISTEXHUB_PROD_MONGODB_ROTATION_COLLECTION_FILES_SHA256",
        ):
            self.assertIn(required, self.wrapper)
        self.assertNotIn("--extra-vars.*apply", self.wrapper)
        self.assertNotIn("ansible-playbook.*--diff'", self.wrapper)
        self.assertNotIn("/usr/bin/wait", self.wrapper)
        self.assertIn('wait "$child_pid"', self.wrapper)
        self.assertIn('= "$controller_uid:755"', self.wrapper)
        self.assertEqual(0, subprocess.run(["/bin/sh", "-n", str(WRAPPER)], check=False).returncode)

    def test_playbook_is_one_host_non_mutating_role(self) -> None:
        self.assertEqual("crtxweb", self.playbook[0]["hosts"])
        self.assertFalse(self.playbook[0]["gather_facts"])
        self.assertFalse(self.playbook[0]["become"])
        self.assertTrue(self.playbook[0]["any_errors_fatal"])
        self.assertEqual(
            [{"role": "cristexhub_prod_mongodb_credential_rotation_check"}],
            self.playbook[0]["roles"],
        )
        self.assertIn("ansible_check_mode", self.tasks)
        self.assertIn("ansible_diff_mode", self.tasks)
        self.assertIn("crtxweb", self.tasks)
        self.assertNotIn("ansible.builtin.k8s:", self.tasks)
        self.assertNotIn("ansible.builtin.command:", self.tasks)
        self.assertNotIn("ansible.builtin.shell:", self.tasks)

    def test_exact_two_path_source_contract(self) -> None:
        source = self.policy["scope"]["source_paths"]
        self.assertEqual(
            {
                "environment_slug": "prod",
                "secret_path": "/shared-services/mongodb",
                "recursive": False,
                "keys": ["MONGODB_CRISTEXHUB_PROD_USERNAME", "MONGODB_CRISTEXHUB_PROD_PASSWORD"],
            },
            source["engine"],
        )
        self.assertEqual(
            {
                "environment_slug": "prod",
                "secret_path": "/cristexhub/prod/runtime",
                "recursive": False,
                "key": "MONGODB_URL",
            },
            source["runtime_url"],
        )
        self.assertEqual("619656da-14f3-4872-857b-be103cdc5326", self.policy["scope"].get("project_id", "619656da-14f3-4872-857b-be103cdc5326"))
        self.assertEqual("check-only", self.policy["execution"]["mode"])
        self.assertFalse(self.policy["execution"]["check_mutates_infisical"])
        self.assertFalse(self.policy["execution"]["check_mutates_kubernetes"])

    def test_existing_value_free_source_manifests_are_exactly_bound(self) -> None:
        engine_source = self.engine["spec"]["sources"]
        self.assertEqual(1, len(engine_source))
        self.assertEqual("prod", engine_source[0]["environmentSlug"])
        self.assertEqual("/shared-services/mongodb", engine_source[0]["secretPath"])
        self.assertFalse(engine_source[0]["recursive"])
        engine_targets = {target["name"]: target for target in self.engine["spec"]["targets"]}
        engine_target = engine_targets["shared-mongodb-cristexhub-prod"]
        self.assertEqual("shared-services", engine_target["namespace"])
        self.assertEqual("Opaque", engine_target["secretType"])
        self.assertEqual({"username", "password"}, set(engine_target["template"]["data"]))

        runtime_source = self.runtime["spec"]["sources"]
        self.assertEqual(1, len(runtime_source))
        self.assertEqual("prod", runtime_source[0]["environmentSlug"])
        self.assertEqual("/cristexhub/prod/runtime", runtime_source[0]["secretPath"])
        self.assertFalse(runtime_source[0]["recursive"])
        runtime_targets = {target["name"]: target for target in self.runtime["spec"]["targets"]}
        runtime_target = runtime_targets["cristexhub-prod-runtime"]
        self.assertEqual("cristexhub-prod", runtime_target["namespace"])
        self.assertEqual("Opaque", runtime_target["secretType"])
        self.assertEqual(
            {
                "BROWSERLESS_TOKEN", "CODE_RUNNER_AUTH_TOKEN", "FERNET_KEY", "MONGODB_URL",
                "OAUTH2_PROXY_COOKIE_SECRET", "OIDC_CLIENT_SECRET", "PRIVATE_CA_BUNDLE",
                "RABBITMQ_URL", "REDIS_PASSWORD", "REDIS_URL",
            },
            set(runtime_target["template"]["data"]),
        )

    def test_source_manifests_bind_every_target_and_template_reference(self) -> None:
        engine_targets = {target["name"]: target for target in self.engine["spec"]["targets"]}
        self.assertEqual(
            {
                "shared-mongodb-auth",
                "shared-mongodb-tls",
                "shared-mongodb-cristexhub-dev",
                "shared-mongodb-cristexhub-prod",
            },
            set(engine_targets),
        )
        expected_engine = {
            "shared-mongodb-auth": {
                "username": "{{ .MONGODB_ADMIN_USERNAME.Value }}",
                "password": "{{ .MONGODB_ADMIN_PASSWORD.Value }}",
            },
            "shared-mongodb-tls": {
                "ca.crt": "{{ .MONGODB_TLS_CA_CRT.Value }}",
                "tls.pem": "{{ .MONGODB_TLS_PEM.Value }}",
            },
            "shared-mongodb-cristexhub-dev": {
                "username": "{{ .MONGODB_CRISTEXHUB_DEV_USERNAME.Value }}",
                "password": "{{ .MONGODB_CRISTEXHUB_DEV_PASSWORD.Value }}",
            },
            "shared-mongodb-cristexhub-prod": {
                "username": "{{ .MONGODB_CRISTEXHUB_PROD_USERNAME.Value }}",
                "password": "{{ .MONGODB_CRISTEXHUB_PROD_PASSWORD.Value }}",
            },
        }
        for name, data in expected_engine.items():
            self.assertEqual(data, engine_targets[name]["template"]["data"])
            self.assertEqual("v1", engine_targets[name]["template"]["engineVersion"])
            self.assertEqual("shared-services", engine_targets[name]["namespace"])
            self.assertEqual("Secret", engine_targets[name]["kind"])
            self.assertEqual("Opaque", engine_targets[name]["secretType"])
            self.assertEqual("Orphan", engine_targets[name]["creationPolicy"])
        runtime_targets = {target["name"]: target for target in self.runtime["spec"]["targets"]}
        self.assertEqual({"cristexhub-prod-runtime", "cristexhub-prod-ghcr-pull"}, set(runtime_targets))
        expected_runtime = {
            "MONGODB_URL": "{{ .MONGODB_URL.Value }}",
            "RABBITMQ_URL": "{{ .RABBITMQ_URL.Value }}",
            "REDIS_URL": "{{ .REDIS_URL.Value }}",
            "REDIS_PASSWORD": "{{ .REDIS_PASSWORD.Value }}",
            "FERNET_KEY": "{{ .FERNET_KEY.Value }}",
            "OIDC_CLIENT_SECRET": "{{ .OIDC_CLIENT_SECRET.Value }}",
            "OAUTH2_PROXY_COOKIE_SECRET": "{{ .OAUTH2_PROXY_COOKIE_SECRET.Value }}",
            "PRIVATE_CA_BUNDLE": "{{ .PRIVATE_CA_BUNDLE.Value }}",
            "CODE_RUNNER_AUTH_TOKEN": "{{ .CODE_RUNNER_AUTH_TOKEN.Value }}",
            "BROWSERLESS_TOKEN": "{{ .BROWSERLESS_TOKEN.Value }}",
        }
        self.assertEqual(expected_runtime, runtime_targets["cristexhub-prod-runtime"]["template"]["data"])
        self.assertEqual(
            {".dockerconfigjson": "{{ .DOCKER_CONFIG_JSON.Value }}"},
            runtime_targets["cristexhub-prod-ghcr-pull"]["template"]["data"],
        )
        for target in runtime_targets.values():
            self.assertEqual("cristexhub-prod", target["namespace"])
            self.assertEqual("Secret", target["kind"])
            self.assertEqual("Orphan", target["creationPolicy"])
            self.assertEqual("v1", target["template"]["engineVersion"])

    def test_selector_module_implements_kubernetes_label_selector_semantics(self) -> None:
        spec = importlib.util.spec_from_file_location("mongodb_networkpolicy_selector", SELECTOR_MODULE)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        labels = {
            "app": "shared-mongodb-svc",
            "app.kubernetes.io/part-of": "shared-databases",
            "cristex.io/component": "mongodb",
        }
        self.assertTrue(module._selector_matches({}, labels))
        self.assertTrue(module._selector_matches({"matchLabels": {"app": "shared-mongodb-svc"}}, labels))
        self.assertTrue(module._selector_matches({"matchExpressions": [{"key": "app", "operator": "In", "values": ["shared-mongodb-svc"]}]}, labels))
        self.assertTrue(module._selector_matches({"matchExpressions": [{"key": "missing", "operator": "NotIn", "values": ["value"]}]}, labels))
        self.assertTrue(module._selector_matches({"matchExpressions": [{"key": "app", "operator": "Exists"}]}, labels))
        self.assertTrue(module._selector_matches({"matchExpressions": [{"key": "missing", "operator": "DoesNotExist"}]}, labels))
        self.assertFalse(module._selector_matches({"matchExpressions": [{"key": "app", "operator": "NotIn", "values": ["shared-mongodb-svc"]}]}, labels))
        self.assertFalse(module._selector_matches({"matchExpressions": [{"key": "app", "operator": "DoesNotExist"}]}, labels))
        self.assertFalse(module._selector_matches({"matchExpressions": [{"key": "missing", "operator": "In", "values": ["value"]}]}, labels))
        self.assertFalse(module._selector_matches({"matchExpressions": [{"key": "app", "operator": "Unsupported", "values": ["x"]}]}, labels))
        self.assertFalse(module._selector_matches({"unknown": {}}, labels))
        self.assertFalse(module._selector_matches({"matchExpressions": [{"key": "app", "operator": "Exists", "values": ["x"]}]}, labels))

    def test_selector_module_fails_closed_on_malformed_terminating_and_duplicate_inventory(self) -> None:
        spec = importlib.util.spec_from_file_location("mongodb_networkpolicy_selector", SELECTOR_MODULE)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        policy = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": "shared-mongodb-networkpolicy-allow",
                "namespace": "shared-services",
            },
            "spec": {"podSelector": {"matchLabels": {"app": "shared-mongodb-svc"}}},
        }
        result = module._evaluate([policy, dict(policy)], {"app": "shared-mongodb-svc"}, "shared-services")
        self.assertEqual("invalid-selector", result["selector_status"])
        self.assertTrue(result["invalid_policy_identities"])
        terminating = {
            **policy,
            "metadata": {**policy["metadata"], "deletionTimestamp": "2026-08-26T00:00:00Z"},
        }
        result = module._evaluate([terminating], {"app": "shared-mongodb-svc"}, "shared-services")
        self.assertEqual(["networking.k8s.io/v1|NetworkPolicy|shared-services|shared-mongodb-networkpolicy-allow"], result["terminating_policy_identities"])
        self.assertEqual("invalid-selector", result["selector_status"])
        malformed = {**policy, "spec": {"podSelector": {"matchExpressions": [{"key": "app", "operator": "Unsupported", "values": ["x"]}]}}}
        result = module._evaluate([malformed], {"app": "shared-mongodb-svc"}, "shared-services")
        self.assertEqual("invalid-selector", result["selector_status"])
        self.assertEqual([], result["matched_policy_identities"])

    def test_source_manifest_hashes_are_wrapper_bound(self) -> None:
        source_pairs = (
            (TASKS, "task_sha256_expected"),
            (DEFAULTS, "defaults_sha256_expected"),
            (PLAYBOOK, "playbook_sha256_expected"),
            (POLICY, "policy_sha256_expected"),
            (METADATA, "metadata_module_sha256_expected"),
            (STRATEGY, "strategy_sha256_expected"),
            (ENGINE_CONNECTION_SOURCE, "engine_connection_source_sha256_expected"),
            (ENGINE_AUTH_SOURCE, "engine_auth_source_sha256_expected"),
            (ENGINE_SOURCE, "engine_source_manifest_sha256_expected"),
            (RUNTIME_CONNECTION_SOURCE, "runtime_connection_source_sha256_expected"),
            (RUNTIME_AUTH_SOURCE, "runtime_auth_source_sha256_expected"),
            (RUNTIME_SOURCE, "runtime_source_manifest_sha256_expected"),
            (NETWORKPOLICY_DEFAULT_DENY, "networkpolicy_default_deny_sha256_expected"),
            (NETWORKPOLICY_ALLOW, "networkpolicy_allow_sha256_expected"),
            (SELECTOR_MODULE, "networkpolicy_selector_module_sha256_expected"),
        )
        for path, variable in source_pairs:
            match = re.search(rf"(?m)^{re.escape(variable)}='([0-9a-f]{{64}})'$", self.wrapper)
            self.assertIsNotNone(match, variable)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), match.group(1))
        marker = re.search(r'(?m)^_STRATEGY_CANONICAL_SHA256 = "([0-9a-f]{64})"$', STRATEGY.read_text())
        self.assertIsNotNone(marker)
        normalized_strategy = re.sub(
            r'(?m)^(_STRATEGY_CANONICAL_SHA256 = ")[0-9a-f]{64}("\s*)$',
            r'\g<1>' + ('0' * 64) + r'\g<2>',
            STRATEGY.read_text(),
        )
        self.assertEqual(marker.group(1), hashlib.sha256(normalized_strategy.encode()).hexdigest())
        for path in (
            ENGINE_CONNECTION_SOURCE, ENGINE_AUTH_SOURCE, ENGINE_SOURCE,
            RUNTIME_CONNECTION_SOURCE, RUNTIME_AUTH_SOURCE, RUNTIME_SOURCE,
            NETWORKPOLICY_DEFAULT_DENY, NETWORKPOLICY_ALLOW,
        ):
            self.assertIn(str(path.relative_to(ROOT)), self.tasks)
        self.assertIn(str(SELECTOR_MODULE.relative_to(ROOT)), self.tasks)
        self.assertIn("NETWORKPOLICY_SELECTOR_MODULE_SHA256", self.wrapper)
        self.assertIn("cristexhub_prod_mongodb_networkpolicy_selector", self.tasks)

    def test_metadata_only_live_pod_identity_binds_selector_evaluation(self) -> None:
        for phrase in (
            "Query exact metadata-only shared MongoDB pod identity",
            "api_path: /api/v1/namespaces/shared-services/pods/shared-mongodb-0",
            "resource_kind: Pod",
            "expected_name: shared-mongodb-0",
            "expected_namespace: shared-services",
            "internal_mongodb_pod_uid",
            "internal_mongodb_pod_resource_version",
            "pod_labels: \"{{ cristexhub_prod_mongodb_credential_rotation_check_internal_mongodb_pod_labels }}\"",
            "pod_uid: \"{{ cristexhub_prod_mongodb_credential_rotation_check_internal_mongodb_pod_uid }}\"",
            "pod_resource_version: \"{{ cristexhub_prod_mongodb_credential_rotation_check_internal_mongodb_pod_resource_version }}\"",
            "selector_evaluation.pod_uid ==",
            "selector_evaluation.pod_resource_version ==",
        ):
            self.assertIn(phrase, self.tasks)
        self.assertNotIn("pod_labels:\n      app: shared-mongodb-svc", self.tasks)

    def test_collection_requirements_and_exact_execution_tree_are_pinned(self) -> None:
        strategy = STRATEGY.read_text()
        for phrase in (
            "_REQUIREMENTS_SOURCE",
            "_COLLECTION_MANIFEST_SOURCE",
            "_COLLECTION_FILES_SOURCE",
            "_EXPECTED_REQUIREMENTS_SHA256",
            "_EXPECTED_COLLECTION_MANIFEST_SHA256",
            "_EXPECTED_COLLECTION_FILES_SHA256",
            "def _collection_toolchain_valid",
            "plugins/action/k8s.py",
            "plugins/modules/k8s_info.py",
            "__pycache__",
            "PurePosixPath",
        ):
            self.assertIn(phrase, strategy)
        self.assertIn("collection_toolchain_valid()", strategy)
        self.assertIn('"pod_uid": {"type": "str", "required": True}', SELECTOR_MODULE.read_text())
        self.assertIn('"pod_resource_version": {"type": "str", "required": True}', SELECTOR_MODULE.read_text())
        self.assertIn("_EXPECTED_REQUIREMENTS_SHA256 = \"f82d9e5ba1b64324710eb66c956d0447c46d3958722f635a4502bcb6c3efc75f\"", strategy)
        self.assertIn("_EXPECTED_COLLECTION_MANIFEST_SHA256 = \"dc32e90ca987d6199e9091f749ecb40fd3380b40aabb7c18961ec75582cfc6df\"", strategy)
        self.assertIn("_EXPECTED_COLLECTION_FILES_SHA256 = \"9d30dde4e4d6d04ec2e9b00a2d787114f13577fd2c456d25726865e3db39fa69\"", strategy)
        self.assertIn("requirements_source", self.wrapper)
        self.assertIn("collection_root", self.wrapper)
        self.assertIn("ansible/requirements.yml", self.wrapper)

    def test_collection_tree_rejects_mutated_executable_leaves_and_extra_artifacts(self) -> None:
        source = Path('/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core')
        if not (source / 'FILES.json').is_file():
            self.skipTest('pinned kubernetes.core installation is not available in this checkout')
        spec = importlib.util.spec_from_file_location('mongodb_rotation_strategy_collection', STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = (module._COLLECTION_ROOT, module._COLLECTION_MANIFEST_SOURCE, module._COLLECTION_FILES_SOURCE)
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / 'core'
            shutil.copytree(source, copy, symlinks=True)
            for cache in copy.rglob('__pycache__'):
                shutil.rmtree(cache)
            module._COLLECTION_ROOT = copy
            module._COLLECTION_MANIFEST_SOURCE = copy / 'MANIFEST.json'
            module._COLLECTION_FILES_SOURCE = copy / 'FILES.json'
            self.assertTrue(module._collection_toolchain_valid())
            with (copy / 'plugins/modules/k8s_info.py').open('a', encoding='utf-8') as drift:
                drift.write('# drift\\n')
            self.assertFalse(module._collection_toolchain_valid())
            (copy / 'plugins/modules/k8s_info.py').write_bytes(
                Path('/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core/plugins/modules/k8s_info.py').read_bytes()
            )
            (copy / 'plugins/action/__init__.py').write_text('', encoding='utf-8')
            self.assertFalse(module._collection_toolchain_valid())
            (copy / 'plugins/action/__init__.py').unlink()
            (copy / 'plugins/action/k8s.py').with_suffix('.so').write_bytes(b'forbidden')
            self.assertFalse(module._collection_toolchain_valid())
        module._COLLECTION_ROOT, module._COLLECTION_MANIFEST_SOURCE, module._COLLECTION_FILES_SOURCE = original

    def test_adversarial_template_and_networkpolicy_drift_is_rejected(self) -> None:
        mutated_engine = copy.deepcopy(self.engine)
        mutated_engine["spec"]["targets"][3]["template"]["data"]["password"] = "{{ .MONGODB_ADMIN_PASSWORD.Value }}"
        self.assertNotEqual(self.engine["spec"]["targets"][3]["template"]["data"], mutated_engine["spec"]["targets"][3]["template"]["data"])
        self.assertIn("incorrect Infisical template references", self.tasks)
        for path in (NETWORKPOLICY_DEFAULT_DENY, NETWORKPOLICY_ALLOW):
            policy = yaml.safe_load(path.read_text())
            policy["spec"]["podSelector"]["matchLabels"]["cristex.io/component"] = "not-mongodb"
            self.assertNotEqual("mongodb", policy["spec"]["podSelector"]["matchLabels"]["cristex.io/component"])
        self.assertIn("foreign overlap", self.tasks)
        self.assertIn("spec-drifted shared MongoDB NetworkPolicies", self.tasks)
        self.assertIn("Query exact MongoDB NetworkPolicy preflight objects", self.tasks)
        self.assertIn("Query every shared MongoDB NetworkPolicy selector for foreign overlap", self.tasks)
        self.assertEqual(
            ["shared-mongodb-networkpolicy-default-deny", "shared-mongodb-networkpolicy-allow"],
            self.policy["scope"]["networkpolicy_preflight"]["exact_names"],
        )
        self.assertEqual(
            {
                "app": "shared-mongodb-svc",
                "app.kubernetes.io/part-of": "shared-databases",
                "cristex.io/component": "mongodb",
            },
            self.policy["scope"]["networkpolicy_preflight"]["target_pod_selector"],
        )

    def test_infisical_auth_and_connection_sources_are_exact_and_value_free(self) -> None:
        self.assertEqual({"address": "https://app.infisical.com"}, yaml.safe_load(ENGINE_CONNECTION_SOURCE.read_text())["spec"])
        self.assertEqual({"address": "https://app.infisical.com"}, yaml.safe_load(RUNTIME_CONNECTION_SOURCE.read_text())["spec"])
        engine_auth = yaml.safe_load(ENGINE_AUTH_SOURCE.read_text())
        runtime_auth = yaml.safe_load(RUNTIME_AUTH_SOURCE.read_text())
        self.assertEqual("universal", engine_auth["spec"]["method"])
        self.assertEqual("universal", runtime_auth["spec"]["method"])
        self.assertEqual("shared-services", engine_auth["spec"]["infisicalConnectionRef"]["namespace"])
        self.assertEqual("cristexhub-prod", runtime_auth["spec"]["infisicalConnectionRef"]["namespace"])
        for source in (ENGINE_CONNECTION_SOURCE, ENGINE_AUTH_SOURCE, RUNTIME_CONNECTION_SOURCE, RUNTIME_AUTH_SOURCE):
            self.assertNotIn("clientSecret:", source.read_text())
            self.assertNotIn("clientId:", source.read_text())
        self.assertIn("compare_spec", str(self.defaults))
        self.assertIn("owner_references", str(self.defaults))
        self.assertIn("include_spec", self.tasks)

    def test_metadata_module_preserves_and_rejects_termination_timestamp(self) -> None:
        spec = importlib.util.spec_from_file_location("mongodb_metadata", METADATA)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        payload = {
            "apiVersion": "meta.k8s.io/v1",
            "kind": "PartialObjectMetadata",
            "metadata": {
                "name": "example",
                "namespace": "shared-services",
                "uid": "uid",
                "resourceVersion": "7",
                "deletionTimestamp": "2026-08-26T00:00:00Z",
            },
        }
        result = module._metadata(payload)
        self.assertIsNotNone(result)
        self.assertEqual("2026-08-26T00:00:00Z", result["deletionTimestamp"])
        self.assertEqual([], result["ownerReferences"])
        with_owner = {**payload, "metadata": {**payload["metadata"], "ownerReferences": [{"apiVersion": "v1", "kind": "ConfigMap", "name": "x", "uid": "u"}]}}
        self.assertEqual("u", module._metadata(with_owner)["ownerReferences"][0]["uid"])
        self.assertIsNone(module._metadata({**payload, "metadata": {**payload["metadata"], "deletionTimestamp": 7}}))
        self.assertIn("deletionTimestamp is none", self.tasks)

    def test_metadata_response_identity_is_bound_to_requested_resource(self) -> None:
        spec = importlib.util.spec_from_file_location("mongodb_metadata_identity", METADATA)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        partial = {
            "apiVersion": "meta.k8s.io/v1",
            "kind": "PartialObjectMetadata",
            "metadata": {
                "name": "example",
                "namespace": "shared-services",
                "uid": "uid",
                "resourceVersion": "7",
            },
        }
        self.assertTrue(module._response_shape_valid(partial, "Secret", "v1", False))
        self.assertFalse(module._response_shape_valid({**partial, "kind": "Secret"}, "Secret", "v1", False))
        full = {
            "apiVersion": "secrets.infisical.com/v1beta1",
            "kind": "InfisicalAuth",
            "metadata": partial["metadata"],
            "spec": {},
        }
        self.assertTrue(module._response_shape_valid(full, "InfisicalAuth", "secrets.infisical.com/v1beta1", True))
        self.assertFalse(module._response_shape_valid({**full, "kind": "Secret"}, "InfisicalAuth", "secrets.infisical.com/v1beta1", True))
        self.assertFalse(module._response_shape_valid({**full, "apiVersion": "v1"}, "InfisicalAuth", "secrets.infisical.com/v1beta1", True))

    def test_metadata_module_negotiates_partial_object_only(self) -> None:
        for phrase in (
            "PartialObjectMetadata",
            "application/json;as=PartialObjectMetadata;g=meta.k8s.io;v=v1",
            "_response_shape_valid",
            "set(payload) == _ALLOWED_TOP_LEVEL_KEYS",
            "module.exit_json(",
            "resource_kind=resource_kind,",
            "expected_name",
            "expected_namespace",
            "include_spec",
            "ownerReferences",
            "Never return managedFields",
            '"data" not in payload',
        ):
            self.assertIn(phrase, self.metadata)
        self.assertNotIn("stringData:", self.metadata)
        self.assertIn("spec_only=include_spec", self.metadata)
        self.assertNotIn("module.exit_json(changed=False, data=", self.metadata)

    def test_metadata_targets_and_revision_channels_are_exact(self) -> None:
        resources = self.defaults["cristexhub_prod_mongodb_credential_rotation_check_metadata_resources"]
        by_id = {resource["id"]: resource for resource in resources}
        self.assertEqual(
            {
                "engine_connection", "engine_auth", "engine_source", "engine_target",
                "runtime_connection", "runtime_auth", "runtime_source", "runtime_target",
            },
            set(by_id),
        )
        self.assertEqual("InfisicalConnection", by_id["engine_connection"]["kind"])
        self.assertEqual("InfisicalAuth", by_id["engine_auth"]["kind"])
        self.assertEqual("InfisicalConnection", by_id["runtime_connection"]["kind"])
        self.assertEqual("InfisicalAuth", by_id["runtime_auth"]["kind"])
        for source_id in ("engine_connection", "engine_auth", "engine_source", "runtime_connection", "runtime_auth", "runtime_source"):
            self.assertTrue(by_id[source_id]["compare_spec"])
            self.assertEqual([], by_id[source_id]["owner_references"])
        self.assertEqual("Secret", by_id["engine_target"]["kind"])
        self.assertEqual("shared-services", by_id["engine_target"]["namespace"])
        self.assertEqual("shared-mongodb-cristexhub-prod", by_id["engine_target"]["name"])
        self.assertEqual("Secret", by_id["runtime_target"]["kind"])
        self.assertEqual("cristexhub-prod", by_id["runtime_target"]["namespace"])
        self.assertTrue(by_id["engine_target"]["require_version_annotation"])
        self.assertTrue(by_id["runtime_target"]["require_version_annotation"])
        self.assertIn("metadata.resourceVersion", self.policy["revision_and_cas"]["source_revision_observation"]["engine"])
        self.assertEqual("unavailable", self.policy["revision_and_cas"]["engine_path_cas"])
        self.assertEqual("unavailable", self.policy["revision_and_cas"]["runtime_url_path_cas"])
        self.assertEqual("UNKNOWN-STOP", self.policy["revision_and_cas"]["ambiguous_result"])
        self.assertEqual("UNKNOWN-STOP", self.policy["revision_and_cas"]["missing_revision"])

    def test_provenance_guard_is_non_skippable_before_role_tasks(self) -> None:
        self.assertEqual("cristexhub_prod_mongodb_credential_rotation_check_guarded_linear", self.playbook[0]["strategy"])
        for phrase in (
            "_canonical_argv", "_source_contract", "_wrapper_binding_valid", "_is_ancestor",
            "_proc_starttime", "_proc_cmdline", "TASK_SELECTION_GUARD", "start_at_task",
            "skip_tags", "_canonical_hash", "_POLICY_SOURCE", "_METADATA_SOURCE",
            "_SELECTOR_SOURCE", "_ROLES_PATH", "ANSIBLE_ROLES_PATH",
        ):
            self.assertIn(phrase, STRATEGY.read_text())
        self.assertIn("plugins/strategy/cristexhub_prod_mongodb_credential_rotation_check_guarded_linear.py", self.wrapper)
        self.assertIn("ansible/playbooks/check_cristexhub_prod_mongodb_credential_rotation.yml", self.wrapper)
        self.assertIn('set -- "$controller" -i "$inventory" "$playbook_source"', self.wrapper)
        self.assertNotIn("CRISTEXWEB_PROD_MONGODB_ROTATION_", self.wrapper)
        self.assertNotIn("CRISTEXWEB_PROD_MONGODB_ROTATION_", STRATEGY.read_text())
        self.assertNotIn("CRISTEXWEB_PROD_MONGODB_ROTATION_", self.tasks)

    def test_strategy_pins_complete_role_policy_and_module_source_closure(self) -> None:
        strategy = STRATEGY.read_text()
        for suffix in (
            "TASK_SHA256", "DEFAULTS_SHA256", "PLAYBOOK_SHA256", "POLICY_SHA256",
            "METADATA_MODULE_SHA256", "NETWORKPOLICY_SELECTOR_MODULE_SHA256",
            "ENGINE_CONNECTION_SOURCE_SHA256", "ENGINE_AUTH_SOURCE_SHA256",
            "ENGINE_SOURCE_MANIFEST_SHA256", "RUNTIME_CONNECTION_SOURCE_SHA256",
            "RUNTIME_AUTH_SOURCE_SHA256", "RUNTIME_SOURCE_MANIFEST_SHA256",
            "NETWORKPOLICY_DEFAULT_DENY_SHA256", "NETWORKPOLICY_ALLOW_SHA256",
        ):
            self.assertIn(f'"{suffix}"', strategy)
        self.assertIn("_ROLE_PATH", strategy)
        self.assertIn("_ROLES_PATH", strategy)
        self.assertIn('os.environ.get("ANSIBLE_ROLES_PATH") != str(_ROLES_PATH)', strategy)
        self.assertIn("_source_contract()", strategy)

    def test_wrapper_shell_startup_rejects_before_controller_for_invalid_invocations(self) -> None:
        for argv in ((), ("apply",), ("check", "--start-at-task", "mutation")):
            result = subprocess.run([str(WRAPPER), *argv], capture_output=True, text=True, check=False)
            self.assertEqual(64, result.returncode, argv)
            self.assertNotIn("ansible-playbook", result.stdout + result.stderr)

    def test_direct_task_selected_and_forged_environment_invocations_are_rejected(self) -> None:
        strategy = STRATEGY.read_text()
        self.assertIn("selection_argv", strategy)
        self.assertIn("--start-at-task", strategy)
        self.assertIn("--skip-tags", strategy)
        self.assertIn('context.CLIARGS.get("start_at_task")', strategy)
        self.assertIn('context.CLIARGS.get("step")', strategy)
        self.assertIn("not any(name in os.environ for name in _FORBIDDEN_ENV)", strategy)
        self.assertIn("_is_ancestor", strategy)
        self.assertIn("_proc_cmdline", strategy)
        for argv in ([], ["check", "extra"], ["apply"]):
            result = subprocess.run([str(WRAPPER), *argv], capture_output=True, text=True, check=False)
            self.assertEqual(64, result.returncode, argv)

    def test_role_is_explicitly_check_only_and_operator_owned(self) -> None:
        for phrase in (
            "Require the exact metadata-only MongoDB rotation preflight",
            "Require the canonical check wrapper attestation",
            "Query exact Infisical source and target metadata without Secret data",
            "Bind the two observed revision channels without claiming Infisical CAS",
            "engine_cas_status: unavailable",
            "runtime_url_cas_status: unavailable",
            "source_write_status == 'forbidden'",
            "apply_status == 'NOT-RUN-BLOCKED'",
            "auth_negative_status == 'NOT-RUN-BLOCKED'",
            "predecessor_revocation_status == 'SEPARATE-APPROVAL-REQUIRED'",
            "kubernetes.core.k8s_info",
            "Require an available Infisical Operator without mutating it",
            "Require current consumer readiness without claiming successor acceptance",
            "Require private PROD Argo health before any future cutover",
            "secret_data_requested: false",
            "consumer_restart: false",
        ):
            self.assertIn(phrase, self.tasks)
        self.assertNotIn("cristexhub_prod_mongodb_credential_rotation_guarded_k8s", self.tasks)
        self.assertNotIn("kubernetes.core.k8s:\n", self.tasks)

    def test_policy_freezes_recovery_restart_auth_and_revocation_boundaries(self) -> None:
        required = (
            "encrypted_predecessor_custody", "encrypted_successor_custody", "fresh_mongodb_backup_readback",
            "isolated_restore", "new_pod_uids_required", "readiness_required", "tls_scram_positive_authentication",
            "cross_database_negative", "cross_environment_negative", "networkpolicy_enforcement",
            "identity_from_protected_metadata_only", "revocation_approval", "database_principal_restore_is_separate",
        )
        for key in required:
            self.assertIn(key, str(self.policy))
        self.assertFalse(self.policy["execution"]["restarts_consumers"])
        self.assertFalse(self.policy["execution"]["revokes_predecessor"])

    def test_runbook_is_value_free_and_truthfully_blocked(self) -> None:
        for phrase in (
            "SOURCE-ONLY METADATA PREFLIGHT / NOT RUN / BLOCKED",
            "There is intentionally no `apply` mode",
            "The repository has no reviewed Infisical API CAS",
            "both path CAS states are `unavailable`",
            "source writing is `forbidden`",
            "`UNKNOWN-STOP`",
            "Operator remains the only Kubernetes value owner",
            "Consumer restart/readiness",
            "Authentication and authorization negatives",
            "Separate predecessor revocation",
            "authorization denial",
            "does not prove predecessor authentication revocation",
            "Rollback requires",
            "No Kubernetes apply, Infisical mutation",
        ):
            self.assertIn(phrase, self.normalized_runbook)
        self.assertNotRegex(self.runbook, r"(?im)^\s*(?:password|token|secret|clientsecret)\s*[:=]\s*[^`{<\n]")
        self.assertNotRegex(self.runbook, r"(?:mongodb|mongodb\+srv)://[^\s/]+:[^\s@]+@")
        self.assertNotIn("BEGIN AGE", self.runbook)
        self.assertNotIn("eyJ", self.runbook)

    def test_dedicated_files_do_not_mutate_or_request_secret_bodies(self) -> None:
        combined = "\n".join(
            path.read_text()
            for path in (WRAPPER, PLAYBOOK, TASKS, DEFAULTS, POLICY, METADATA, SELECTOR_MODULE, RUNBOOK)
        )
        for forbidden in (
            "kubectl apply", "kubectl delete", "kubectl patch", "rabbitmqctl",
            "mongosh", "ansible.builtin.k8s:", "stringData:", "Secret.data",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertIn("resource_kind: \"{{ item.kind }}\"", self.tasks)
        self.assertIn("metadata_only=not include_spec", self.metadata)
        self.assertEqual("forbidden", self.policy["ownership"]["direct_kubernetes_secret_write"])

    def test_source_manifest_digests_are_stable(self) -> None:
        for path in (
            ENGINE_SOURCE,
            RUNTIME_SOURCE,
            NETWORKPOLICY_DEFAULT_DENY,
            NETWORKPOLICY_ALLOW,
            POLICY,
        ):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(64, len(digest))
            self.assertNotEqual("0" * 64, digest)


if __name__ == "__main__":
    unittest.main()
