from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shlex
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
POLICY = ANSIBLE / "files/policies/cristexhub-prod-rabbitmq-credential-rotation.yml"
DEFAULTS = ANSIBLE / "roles/rabbitmq_prod_credential_rotation_check/defaults/main.yml"
TASKS = ANSIBLE / "roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml"
PLAYBOOK = ANSIBLE / "playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml"
WRAPPER = ANSIBLE / "bin/check-cristexhub-prod-rabbitmq-credential-rotation"
ACTION = ANSIBLE / "plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py"
STRATEGY = ANSIBLE / "plugins/strategy/rabbitmq_prod_credential_rotation_check_guarded_linear.py"
METADATA = ANSIBLE / "library/rabbitmq_prod_credential_metadata.py"
BROKER_SOURCE = ANSIBLE / "files/components/rabbitmq/runtime/statefulset-rabbitmq.yaml"
CONFIG_SOURCE = ANSIBLE / "files/components/rabbitmq/runtime/configmap-rabbitmq.yaml"
ENGINE_SOURCE = ANSIBLE / "files/components/infisical-rabbitmq-secrets/source/rabbitmq-infisical-secrets.yaml"
RUNTIME_SOURCE = ANSIBLE / "files/components/infisical-cristexhub-prod-runtime/source/cristexhub-prod-runtime-static-secret.yaml"


class RabbitMqProdCredentialRotationCheckContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = yaml.safe_load(POLICY.read_text())
        cls.defaults = yaml.safe_load(DEFAULTS.read_text())
        cls.tasks = TASKS.read_text()
        cls.wrapper = WRAPPER.read_text()
        cls.action = ACTION.read_text()
        cls.strategy = STRATEGY.read_text()
        cls.metadata = METADATA.read_text()
        cls.playbook = yaml.safe_load(PLAYBOOK.read_text())

    def test_exact_source_only_policy_and_dual_paths(self) -> None:
        self.assertEqual("cristexhub-prod-rabbitmq-credential-rotation-v1", self.policy["policy_schema"])
        self.assertEqual("source-only-check-only-writer-blocked", self.policy["policy_status"])
        self.assertFalse(self.policy["runtime_mutation_allowed"])
        self.assertEqual("/cristexhub-prod", self.policy["scope"]["vhost"])
        self.assertEqual("cristexhub_prod_user", self.policy["scope"]["predecessor_principal"])
        self.assertEqual("cristexhub_prod_rabbitmq", self.policy["scope"]["successor_principal"])
        self.assertEqual("/shared-services/rabbitmq", self.policy["engine_source"]["path"])
        self.assertEqual("/cristexhub/prod/runtime", self.policy["runtime_source"]["path"])
        self.assertEqual("RABBITMQ_URL", self.policy["runtime_source"]["key"])
        self.assertEqual({"username", "password", "passwordHash"}, set(self.policy["engine_source"]["target_keys"]))
        self.assertEqual(
            {"MONGODB_URL", "RABBITMQ_URL", "REDIS_URL", "REDIS_PASSWORD", "FERNET_KEY",
             "OIDC_CLIENT_SECRET", "OAUTH2_PROXY_COOKIE_SECRET", "PRIVATE_CA_BUNDLE",
             "CODE_RUNNER_AUTH_TOKEN", "BROWSERLESS_TOKEN"},
            set(self.policy["runtime_source"]["target_keys"]),
        )
        self.assertFalse(self.policy["revisions_and_cas"]["writer_available"])
        self.assertFalse(self.policy["revisions_and_cas"]["cas_proven"])
        self.assertTrue(self.policy["revisions_and_cas"]["dual_path_update"])
        self.assertTrue(self.policy["recovery"]["definitions_backup_readback_required"])
        self.assertFalse(self.policy["recovery"]["isolated_definitions_restore_proved"])
        self.assertFalse(self.policy["recovery"]["queued_message_recovery_proved"])

    def test_check_only_role_has_no_writer_or_revocation_path(self) -> None:
        for required in (
            "ansible_check_mode",
            "ansible_diff_mode",
            "SOURCE_ONLY_STOP",
            "not rabbitmq_prod_credential_rotation_check_writer_available",
            "not rabbitmq_prod_credential_rotation_check_cas_available",
            "not rabbitmq_prod_credential_rotation_check_runtime_mutation_allowed",
            "PartialObjectMetadata",
            "resourceVersion",
            "cristexhub_prod_user",
            "cristexhub_prod_rabbitmq",
            "rabbitmqctl",
            "list_users",
            "list_permissions",
            "Operator reconciliation",
            "celery-worker",
        ):
            self.assertIn(required, self.tasks + self.action + self.metadata, required)
        for forbidden in (
            "rabbitmqctl add_user",
            "rabbitmqctl delete_user",
            "rabbitmqctl set_permissions",
            "kubectl apply",
            "kubectl delete",
            "Secret data",
            "secretValue",
        ):
            self.assertNotIn(forbidden, self.tasks)
            self.assertNotIn(forbidden, self.action)
        self.assertEqual("rabbitmq_prod_credential_rotation_check", self.playbook[0]["roles"][0]["role"])
        self.assertEqual("rabbitmq_prod_credential_rotation_check_guarded_linear", self.playbook[0]["strategy"])

    def test_candidate_permissions_are_exact_and_non_wildcarded(self) -> None:
        expected = {
            "configure": "^(default|high_priority|low_priority)$",
            "write": "^default$",
            "read": "^(default|high_priority|low_priority)$",
        }
        self.assertEqual(expected, {key: self.policy["permissions"][key] for key in expected})
        for value in expected.values():
            self.assertNotIn(".*", value)
            self.assertNotIn("[^*]", value)
        self.assertIn("candidate_until_live_probe: true", POLICY.read_text())
        self.assertIn("no_cross_vhost: true", POLICY.read_text())
        self.assertIn("no_user_management: true", POLICY.read_text())

    def test_wrapper_is_check_only_and_hash_bound(self) -> None:
        self.assertIn("usage: ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation check", self.wrapper)
        self.assertIn("--check --diff --limit crtxweb", self.wrapper)
        self.assertNotIn("apply", self.wrapper.split("usage:", 1)[1].split("'", 1)[0])
        self.assertIn("env -i", self.wrapper)
        self.assertIn("umask 077", self.wrapper)
        self.assertIn("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ATTESTATION_FILE", self.wrapper)
        self.assertIn("CRISTEXWEB_RABBITMQ_PROD_ROTATION_MODE=check", self.wrapper)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", self.wrapper)
        self.assertIn("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_STARTTIME", self.wrapper)
        self.assertIn("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_CANONICAL_SHA256", self.wrapper)
        self.assertIn("canonical_action_sha256", self.wrapper)
        self.assertIn("canonical_wrapper_sha256", self.wrapper)
        self.assertIn("controller_user=$(/usr/bin/id -un)", self.wrapper)
        self.assertIn('[ "$controller_user" = paul ]', self.wrapper)
        self.assertIn("HOME=/home/paul", self.wrapper)
        self.assertIn("python_real_source=/usr/bin/python3.13", self.wrapper)
        self.assertIn('regular file:root:root:755', self.wrapper)
        self.assertIn('17b78e0a93175e86f9ac03141924fd7a7f0c0c52e66b34bfa0de20ffef989df1', self.wrapper)
        self.assertIn("collection_files", self.wrapper)
        self.assertIn("ANSIBLE_ROLES_PATH", self.wrapper)
        self.assertIn("ANSIBLE_LIBRARY", self.wrapper)
        self.assertIn("check_cristexhub_prod_rabbitmq_credential_rotation.yml", self.wrapper)
        for digest_name, source_name in (
            ("CONTROLLER_SHA256", "controller"),
            ("PYTHON_SHA256", "python_real_source"),
            ("ANSIBLE_CONFIG_SHA256", "config"),
            ("INVENTORY_SHA256", "inventory"),
            ("REQUIREMENTS_SHA256", "requirements_source"),
            ("COLLECTION_MANIFEST_SHA256", "collection_manifest"),
            ("COLLECTION_FILES_SHA256", "collection_files"),
        ):
            self.assertIn(f"CRISTEXWEB_RABBITMQ_PROD_ROTATION_{digest_name}=", self.wrapper)
            self.assertIn(f'$(sha256 "${source_name}")', self.wrapper)
        self.assertNotIn("--extra-vars '{\"rabbitmq_prod_credential_rotation_check_approved\":false}'", self.wrapper)
        self.assertEqual(0, subprocess.run(["/bin/sh", "-n", str(WRAPPER)], check=False).returncode)
        rejected = subprocess.run([str(WRAPPER), "check", "--start-at-task", "mutation"], check=False, capture_output=True, text=True)
        self.assertEqual(64, rejected.returncode)
        self.assertNotIn("ansible-playbook", rejected.stdout + rejected.stderr)

    def test_python_target_is_root_owned_exact_mode_and_digest_bound(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_strategy_python_target", STRATEGY
        )
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        target = Path("/usr/bin/python3").resolve(strict=True)
        expected_digest = module._sha256(target)
        self.assertTrue(module._regular_file(target, 0o755, 0, 0))
        self.assertFalse(module._regular_file(target, 0o775, 0, 0))
        self.assertFalse(module._regular_file(target, 0o755, 65534, 65534))
        self.assertEqual(expected_digest, module._sha256(target))

    def test_wrapper_exports_check_mode_and_disables_bytecode_for_reruns(self) -> None:
        env_block = self.wrapper.split("/usr/bin/env -i ", 1)[1]
        self.assertIn("CRISTEXWEB_RABBITMQ_PROD_ROTATION_MODE=check \\\n", env_block)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1 \\\n", env_block)

    def test_strategy_binds_ancestor_argv_and_source_closure_consistency(self) -> None:
        for required in (
            "class StrategyModule(LinearStrategyModule)",
            "_wrapper_attestation_valid",
            "_canonical_argv",
            "_source_contract",
            "_collection_toolchain_valid",
            "_PYTHON_REAL_SOURCE",
            "_OPERATOR",
            "_wrapper_canonical_expected",
            "_EXPECTED_COLLECTION_EXECUTED_FILES",
            "_STRATEGY_CANONICAL_SHA256",
            "_ACTION_CANONICAL_SHA256",
            "context.CLIARGS.get(\"start_at_task\") is None",
            "not any(os.environ.get(name) for name in _FORBIDDEN_ENV)",
        ):
            self.assertIn(required, self.strategy, required)
        self.assertEqual(0o644, stat.S_IMODE(STRATEGY.stat().st_mode))
        self.assertIn("strategy: rabbitmq_prod_credential_rotation_check_guarded_linear", PLAYBOOK.read_text())

    def test_action_rejects_unknown_users_and_foreign_permission_rows(self) -> None:
        spec = importlib.util.spec_from_file_location("rabbitmq_prod_credential_rotation_action", ACTION)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        users = [
            {"user": "admin-generated", "tags": "administrator"},
            {"user": "cristexhub_dev_rabbitmq", "tags": ""},
            {"user": "cristexhub_prod_user", "tags": ""},
        ]
        self.assertTrue(module._validate_output("users", json.dumps(users)))
        self.assertFalse(module._validate_output("users", json.dumps(users + [{"user": "foreign", "tags": ""}])))
        self.assertFalse(module._validate_output("users", json.dumps([
            {"user": "admin-generated", "tags": "administrator"},
            {"user": "cristexhub_dev_rabbitmq", "tags": ""},
            {"user": "cristexhub_prod_user", "tags": ""},
            {"user": "guest", "tags": ""},
        ])))
        permissions = [
            {"user": "cristexhub_dev_rabbitmq", "vhost": "/cristexhub-dev", "configure": "^(default|high_priority|low_priority)$", "write": "^default$", "read": "^(default|high_priority|low_priority)$"},
            {"user": "cristexhub_prod_user", "vhost": "/cristexhub-prod", "configure": "^(default|high_priority|low_priority)$", "write": "^default$", "read": "^(default|high_priority|low_priority)$"},
        ]
        self.assertTrue(module._validate_output("all_permissions", json.dumps(permissions)))
        self.assertFalse(module._validate_output("all_permissions", json.dumps(permissions + [{**permissions[0], "user": "foreign"}])))
        self.assertFalse(module._validate_output("prod_permissions", json.dumps([{**permissions[1], "vhost": "/foreign"}])))

    def test_action_binds_ancestor_argv_and_strips_results(self) -> None:
        for required in (
            "_ancestor",
            "_proc_cmdline",
            "_canonical_wrapper_argument(_proc_cmdline(pid)[1], pid)",
            "sys.argv == _expected_argv()",
            "_runtime_provenance_valid()",
            "kubernetes.core.k8s_exec",
            "result.pop(key, None)",
            "metadata_only",
            "no_secret_payloads",
            "no_apply_path",
        ):
            self.assertIn(required, self.action, required)
        self.assertNotIn("kubernetes.core.k8s", self.action.replace("kubernetes.core.k8s_exec", ""))
        self.assertIn("_SECRET_KEYS", self.action)
        self.assertIn("password_hash", self.action)

    def test_partial_metadata_module_rejects_secret_payloads(self) -> None:
        self.assertIn("PartialObjectMetadata", self.metadata)
        self.assertIn("set(payload) != _TOP_LEVEL", self.metadata)
        self.assertIn("payload.get(\"kind\") != \"PartialObjectMetadata\"", self.metadata)
        self.assertIn("metadata.get(\"name\") != name", self.metadata)
        self.assertIn("metadata.get(\"namespace\") != namespace", self.metadata)
        self.assertIn("creationTimestamp", self.metadata)
        self.assertIn("annotations", self.metadata)
        self.assertIn("deletionTimestamp", self.metadata)
        self.assertIn("terminating Secret refused", self.metadata)
        self.assertIn("ownerReferences", self.metadata)
        self.assertIn("_CANONICAL_LABELS", self.metadata)
        self.assertIn("_CANONICAL_ANNOTATION", self.metadata)
        self.assertIn("noncanonical Secret labels", self.metadata)
        self.assertIn("noncanonical Secret annotations", self.metadata)
        self.assertIn("module.exit_json(changed=False, items=items, metadata_only=True)", self.metadata)
        self.assertNotIn('"data"', self.metadata)
        self.assertNotIn('"stringData"', self.metadata)

    def test_partial_metadata_adversarial_shapes_and_identity_are_rejected(self) -> None:
        spec = importlib.util.spec_from_file_location("rabbitmq_prod_credential_metadata", METADATA)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)

        class Client:
            def __init__(self, payload):
                self.payload = payload

            def call_api(self, *args, **kwargs):
                return self.payload

        base = {
            "apiVersion": "meta.k8s.io/v1",
            "kind": "PartialObjectMetadata",
            "metadata": {
                "name": "shared-rabbitmq-cristexhub-prod",
                "namespace": "shared-services",
                "uid": "uid-1",
                "resourceVersion": "123",
                "creationTimestamp": "2026-08-26T00:00:00Z",
                "annotations": {"secrets.infisical.com/version": "7"},
                "labels": {
                    "app.kubernetes.io/managed-by": "infisical",
                    "app.kubernetes.io/part-of": "shared-rabbitmq",
                    "cristex.io/value-owner": "infisical-cloud",
                },
                "managedFields": [],
                "ownerReferences": [],
                "finalizers": [],
                "clusterName": "",

            },
        }
        result = module._metadata(Client(base), "shared-services", "shared-rabbitmq-cristexhub-prod")
        self.assertEqual("shared-rabbitmq-cristexhub-prod", result["metadata"]["name"])
        self.assertEqual("shared-services", result["metadata"]["namespace"])
        self.assertEqual("7", result["metadata"]["annotations"]["secrets.infisical.com/version"])
        self.assertEqual([], result["metadata"]["ownerReferences"])
        self.assertEqual([], result["metadata"]["managedFields"])
        self.assertEqual([], result["metadata"]["finalizers"])
        self.assertEqual("", result["metadata"]["clusterName"])
        for payload in (
            {**base, "data": {}},
            {**base, "stringData": {}},
            {**base, "metadata": {**base["metadata"], "name": "other"}},
            {**base, "metadata": {**base["metadata"], "namespace": "other"}},
            {**base, "metadata": {**base["metadata"], "deletionTimestamp": "2026-08-26T00:00:01Z"}},
            {**base, "metadata": {**base["metadata"], "annotations": {"bad": "1"}}},
            {**base, "metadata": {**base["metadata"], "annotations": {"secrets.infisical.com/version": ""}}},
            {**base, "metadata": {**base["metadata"], "annotations": {"secrets.infisical.com/version": "7", "extra": "x"}}},
            {**base, "metadata": {**base["metadata"], "labels": {**base["metadata"]["labels"], "extra": "x"}}},
            {**base, "metadata": {**base["metadata"], "labels": {**base["metadata"]["labels"], "app.kubernetes.io/part-of": "wrong"}}},
            {**base, "metadata": {**base["metadata"], "ownerReferences": [{"uid": "owner"}]}},
            {**base, "metadata": {**base["metadata"], "ownerReferences": {}}},
            {**base, "metadata": {**base["metadata"], "uid": ""}},
            {**base, "metadata": {**base["metadata"], "resourceVersion": ""}},
        ):
            with self.assertRaises(ValueError):
                module._metadata(Client(payload), "shared-services", "shared-rabbitmq-cristexhub-prod")

        for namespace, name, part_of in (
            ("cristexhub-prod", "cristexhub-prod-runtime", "cristexhub"),
            ("cristexhub-prod", "cristexhub-prod-ghcr-pull", "cristexhub"),
        ):
            payload = {
                **base,
                "metadata": {
                    **base["metadata"],
                    "namespace": namespace,
                    "name": name,
                    "labels": {
                        "app.kubernetes.io/managed-by": "infisical",
                        "app.kubernetes.io/part-of": part_of,
                        "cristex.io/value-owner": "infisical-cloud",
                    },
                },
            }
            result = module._metadata(Client(payload), namespace, name)
            self.assertEqual(part_of, result["metadata"]["labels"]["app.kubernetes.io/part-of"])

        class RecordingClient(Client):
            def call_api(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs
                return self.payload

        recorder = RecordingClient(base)
        module._metadata(recorder, "shared-services", "shared-rabbitmq-cristexhub-prod")
        self.assertEqual("/api/v1/namespaces/{namespace}/secrets/{name}", recorder.args[0])
        self.assertEqual({"namespace": "shared-services", "name": "shared-rabbitmq-cristexhub-prod"}, recorder.kwargs["path_params"])
        self.assertEqual({"Accept": module._PARTIAL_METADATA_ACCEPT}, recorder.kwargs["header_params"])
        self.assertEqual([], recorder.kwargs["query_params"])

    def test_tasks_parse_and_bind_query_set_without_nested_jinja(self) -> None:
        parsed = yaml.safe_load(self.tasks)
        self.assertIsInstance(parsed, list)
        self.assertEqual(29, len(parsed))
        for task in parsed:
            self.assertIsInstance(task, dict)
            if "ansible.builtin.assert" in task:
                self.assertIn("fail_msg", task["ansible.builtin.assert"])
                self.assertNotIn("fail_msg", task)
        self.assertIn("queries:", self.tasks)
        self.assertIn('binding.get("queries") == sorted(_EXPECTED_QUERIES)', self.action)
        self.assertIn("args.get(\"query\") in binding.get(\"queries\", [])", self.action)
        self.assertIn("item.metadata.labels['app.kubernetes.io/part-of']", self.tasks)
        self.assertIn("item.metadata.annotations.keys()", self.tasks)
        self.assertIn("item.metadata.ownerReferences", self.tasks)
        self.assertIn("CRISTEXWEB_RABBITMQ_PROD_ROTATION_WRAPPER_STARTTIME", self.tasks)
        self.assertIn("item.metadata.deletionTimestamp", self.tasks)
        self.assertIn("Require live Infisical source declarations to match canonical manifests", self.tasks)
        self.assertIn("spec.infisicalAuthRef ==", self.tasks)
        self.assertIn("metadata.annotations | default({})) ==", self.tasks)
        self.assertIn("metadata.ownerReferences | default([])) ==", self.tasks)
        self.assertIn("spec.infisicalAuthRef ==", self.tasks)
        registered_names = [
            task["register"]
            for task in yaml.safe_load(self.tasks)
            if isinstance(task, dict) and "register" in task
        ]
        for name in registered_names:
            self.assertNotRegex(
                self.tasks,
                rf"{re.escape(name)}\.(?:items|keys|values|get|update)\b",
                name,
            )
        for field in ("metadata.uid", "metadata.resourceVersion", "metadata.ownerReferences", "spec.template.metadata.labels", "image", "volumeMounts", "startupProbe", "readinessProbe", "livenessProbe"):
            self.assertIn(field, self.tasks, field)
        self.assertIn("spec.targets ==", self.tasks)
        self.assertIn("spec.sources ==", self.tasks)
        self.assertIn("_RABBITMQ_CONFIG_SOURCE", self.action)
        self.assertIn("_ANSIBLE_CONFIG_SOURCE", self.action)
        self.assertIn("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_CANONICAL_SHA256", self.action)
        self.assertIn("CRISTEXWEB_RABBITMQ_PROD_ROTATION_ACTION_CANONICAL_SHA256", self.wrapper)
        self.assertNotIn("== '{{ .RABBITMQ_URL.Value }}'", self.tasks)
        self.assertIn("'{' ~ '{ .RABBITMQ_URL.Value }' ~ '}'", self.tasks)

    def test_live_broker_shape_rejects_extra_components_and_metadata_drift(self) -> None:
        broker = yaml.safe_load(BROKER_SOURCE.read_text())
        template = broker["spec"]["template"]
        pod_spec = template["spec"]
        self.assertEqual(1, len(pod_spec["containers"]))
        self.assertEqual(1, len(pod_spec["initContainers"]))
        self.assertEqual({}, broker["metadata"].get("annotations", {}))
        self.assertEqual([], broker["metadata"].get("ownerReferences", []))
        self.assertEqual({}, template["metadata"].get("annotations", {}))
        required_guards = (
            "metadata.annotations | default({})) ==",
            "metadata.ownerReferences | default([])) ==",
            "metadata.deletionTimestamp | default(none) is none",
            "spec.template.spec.containers | length ==",
            "spec.template.spec.containers | map(attribute='name') | list | sort ==",
            "spec.template.spec.initContainers | length ==",
            "spec.template.spec.initContainers | map(attribute='name') | list | sort ==",
            "internal_live_pod.metadata.annotations | default({})) ==",
            "internal_live_pod.metadata.deletionTimestamp | default(none) is none",
            "internal_live_pod.spec.containers | length ==",
            "internal_live_pod.spec.containers | map(attribute='name') | list | sort ==",
            "internal_live_pod.spec.initContainers | length ==",
            "internal_live_pod.spec.initContainers | map(attribute='name') | list | sort ==",
            "generated_pvc_volume.keys() | list | sort ==",
            "generated_pvc_volume.persistentVolumeClaim.claimName ==",
            "generated_pvc_volume.persistentVolumeClaim.readOnly is not defined",
            "rejectattr('name', 'equalto', 'rabbitmq-data') | list) ==",
            "internal_live_pod_init_container.image ==",
            "internal_live_pod_init_container.args ==",
            "spec.infisicalAuthRef ==",
        )
        for guard in required_guards:
            self.assertIn(guard, self.tasks, guard)
        self.assertIn("difference(", self.tasks)
        self.assertIn("controller-revision-hash", self.tasks)
        self.assertIn("statefulset.kubernetes.io/pod-name", self.tasks)

    def test_generated_pvc_volume_rejects_readonly_wrong_keys_and_extra_volumes(self) -> None:
        """Exercise generated StatefulSet volume projection with Ansible 2.19."""
        controller = ROOT / ".venv/bin/ansible-playbook"
        if not controller.is_file():
            controller = Path("/home/paul/projects/cristexweb/.venv/bin/ansible-playbook")
        if not controller.is_file():
            self.skipTest("canonical Ansible controller is unavailable on this host")

        task = next(
            item
            for item in yaml.safe_load(self.tasks)
            if item.get("name") == "Require exact StatefulSet-generated RabbitMQ PVC volume"
        )
        source = yaml.safe_load(BROKER_SOURCE.read_text())
        source_volumes = source["spec"]["template"]["spec"]["volumes"]
        generated = {
            "name": "rabbitmq-data",
            "persistentVolumeClaim": {"claimName": "rabbitmq-data-shared-rabbitmq-0"},
        }

        def run_case(root: Path, name: str, volumes: list[dict]) -> subprocess.CompletedProcess[str]:
            variables = {
                "rabbitmq_prod_credential_rotation_check_internal_live_pod": {"spec": {"volumes": volumes}},
                "rabbitmq_prod_credential_rotation_check_internal_source_statefulset": source,
                "rabbitmq_prod_credential_rotation_check_internal_generated_pvc_volume": next(
                    item for item in volumes if item.get("name") == "rabbitmq-data"
                ),
            }
            variables_path = root / f"{name}.json"
            variables_path.write_text(json.dumps(variables), encoding="utf-8")
            return subprocess.run(
                [
                    str(controller),
                    "-i",
                    str(root / "inventory"),
                    str(root / "playbook.yml"),
                    "--check",
                    "--diff",
                    "--extra-vars",
                    "@" + str(variables_path),
                ],
                cwd=root,
                env={
                    "HOME": "/tmp",
                    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                    "ANSIBLE_CONFIG": str(root / "ansible.cfg"),
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
                capture_output=True,
                text=True,
                check=False,
            )

        with tempfile.TemporaryDirectory(prefix="rabbitmq-generated-pvc-", dir="/dev/shm") as directory:
            root = Path(directory)
            role_tasks = root / "roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml"
            role_tasks.parent.mkdir(parents=True)
            role_tasks.write_text("---\n" + yaml.safe_dump([task], sort_keys=False), encoding="utf-8")
            (root / "inventory").write_text("localhost ansible_connection=local\n", encoding="utf-8")
            (root / "ansible.cfg").write_text(
                "[defaults]\n"
                f"roles_path = {root / 'roles'}\n"
                "retry_files_enabled = False\n",
                encoding="utf-8",
            )
            (root / "playbook.yml").write_text(
                "---\n- name: Evaluate generated PVC projection\n"
                "  hosts: localhost\n  gather_facts: false\n"
                "  roles:\n    - rabbitmq_prod_credential_rotation_check\n",
                encoding="utf-8",
            )

            valid = run_case(root, "valid-absent", [generated, *source_volumes])
            self.assertEqual(0, valid.returncode, valid.stdout + valid.stderr)

            generated_false = json.loads(json.dumps(generated))
            generated_false["persistentVolumeClaim"]["readOnly"] = False
            valid_false = run_case(root, "valid-false", [generated_false, *source_volumes])
            self.assertEqual(0, valid_false.returncode, valid_false.stdout + valid_false.stderr)

            generated_true = json.loads(json.dumps(generated))
            generated_true["persistentVolumeClaim"]["readOnly"] = True
            rejected_readonly = run_case(root, "rejected-readonly", [generated_true, *source_volumes])
            self.assertNotEqual(0, rejected_readonly.returncode, rejected_readonly.stdout + rejected_readonly.stderr)
            self.assertIn("RABBITMQ_BROKER_VOLUME_GUARD", rejected_readonly.stdout + rejected_readonly.stderr)

            generated_extra = json.loads(json.dumps(generated))
            generated_extra["persistentVolumeClaim"]["unexpected"] = "drift"
            rejected_key = run_case(root, "rejected-key", [generated_extra, *source_volumes])
            self.assertNotEqual(0, rejected_key.returncode, rejected_key.stdout + rejected_key.stderr)
            self.assertIn("RABBITMQ_BROKER_VOLUME_GUARD", rejected_key.stdout + rejected_key.stderr)

            rejected_volume = run_case(
                root,
                "rejected-volume",
                [generated, {"name": "unreviewed-volume", "emptyDir": {}}, *source_volumes],
            )
            self.assertNotEqual(0, rejected_volume.returncode, rejected_volume.stdout + rejected_volume.stderr)
            self.assertIn("RABBITMQ_BROKER_VOLUME_GUARD", rejected_volume.stdout + rejected_volume.stderr)

    def test_source_manifests_have_fixed_hashes_and_exact_mappings(self) -> None:
        expected = {
            BROKER_SOURCE: "5ea7cfa66e72615e5ff50657e934740907a90d4219c221323e3b91af3efe6242",
            CONFIG_SOURCE: "663c006190e6e5e03e7c22d198cb41245d2ab3b7dab406acb4fdefe00a10a2d5",
            ENGINE_SOURCE: "b5eeaa0abc5b9ee91d392d6ac064862026b64f0d4c74f6431fe5dca517c506d0",
            RUNTIME_SOURCE: "3204aab3fc0f5b55f9af3623fb658d5ffd8289437d5d0ea91ab0480dc4126ee0",
        }
        for path, digest in expected.items():
            self.assertEqual(0o644, stat.S_IMODE(path.stat().st_mode), path)
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest(), path)
            self.assertIn(digest, self.action)
            self.assertIn(digest, self.wrapper)
        broker = yaml.safe_load(BROKER_SOURCE.read_text())
        config = yaml.safe_load(CONFIG_SOURCE.read_text())
        engine = yaml.safe_load(ENGINE_SOURCE.read_text())
        runtime = yaml.safe_load(RUNTIME_SOURCE.read_text())
        self.assertEqual("shared-rabbitmq-config", next(v["configMap"]["name"] for v in broker["spec"]["template"]["spec"]["volumes"] if v["name"] == "config"))
        self.assertEqual("shared-rabbitmq-cristexhub-prod", next(v["secret"]["secretName"] for v in broker["spec"]["template"]["spec"]["volumes"] if v["name"] == "prod-secret"))
        self.assertEqual({"enabled_plugins", "rabbitmq.conf"}, set(config["data"]))
        self.assertIn("management.load_definitions = /etc/rabbitmq/definitions/definitions.json", config["data"]["rabbitmq.conf"])
        targets = {item["name"]: item for item in engine["spec"]["targets"]}
        self.assertEqual({"username", "password", "passwordHash"}, set(targets["shared-rabbitmq-cristexhub-prod"]["template"]["data"]))
        self.assertEqual("{{ .RABBITMQ_CRISTEXHUB_PROD_USERNAME.Value }}", targets["shared-rabbitmq-cristexhub-prod"]["template"]["data"]["username"])
        runtime_target = {item["name"]: item for item in runtime["spec"]["targets"]}["cristexhub-prod-runtime"]
        self.assertEqual("{{ .RABBITMQ_URL.Value }}", runtime_target["template"]["data"]["RABBITMQ_URL"])

    def test_source_contract_task_evaluates_with_ansible_219(self) -> None:
        """Evaluate the actual source-contract role task without Kubernetes access."""
        controller = ROOT / ".venv/bin/ansible-playbook"
        if not controller.is_file():
            controller = Path("/home/paul/projects/cristexweb/.venv/bin/ansible-playbook")
        if not controller.is_file():
            self.skipTest("canonical Ansible controller is unavailable on this host")

        source_paths = {
            "broker": BROKER_SOURCE,
            "engine": ENGINE_SOURCE,
            "runtime": RUNTIME_SOURCE,
            "config": CONFIG_SOURCE,
            "policy": POLICY,
        }

        def protect_template_values(value):
            if isinstance(value, dict):
                return {key: protect_template_values(item) for key, item in value.items()}
            if isinstance(value, list):
                return [protect_template_values(item) for item in value]
            if isinstance(value, str) and "{{" in value:
                return "{% raw %}" + value + "{% endraw %}"
            return value

        source_objects = {
            name: protect_template_values(yaml.safe_load(path.read_text()))
            for name, path in source_paths.items()
        }
        task = next(
            item
            for item in yaml.safe_load(TASKS.read_text())
            if item.get("name")
            == "Require exact value-free source scope and dual-path key contracts"
        )
        with tempfile.TemporaryDirectory(prefix="rabbitmq-source-contract-", dir="/dev/shm") as directory:
            root = Path(directory)
            role_tasks = root / "roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml"
            role_tasks.parent.mkdir(parents=True)
            role_tasks.write_text("---\n" + yaml.safe_dump([task], sort_keys=False), encoding="utf-8")
            (root / "source-objects.json").write_text(
                json.dumps(
                    {"rabbitmq_prod_credential_rotation_check_internal_source_objects": source_objects}
                ),
                encoding="utf-8",
            )
            (root / "inventory").write_text("localhost ansible_connection=local\n", encoding="utf-8")
            (root / "ansible.cfg").write_text(
                "[defaults]\n"
                f"roles_path = {root / 'roles'}\n"
                "retry_files_enabled = False\n",
                encoding="utf-8",
            )
            playbook = root / "playbook.yml"
            playbook.write_text(
                "---\n"
                "- name: Evaluate RabbitMQ source contract\n"
                "  hosts: localhost\n"
                "  gather_facts: false\n"
                "  roles:\n"
                "    - rabbitmq_prod_credential_rotation_check\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    str(controller),
                    "-i",
                    str(root / "inventory"),
                    str(playbook),
                    "--check",
                    "--diff",
                    "--extra-vars",
                    "@" + str(root / "source-objects.json"),
                ],
                cwd=root,
                env={
                    "HOME": "/tmp",
                    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                    "ANSIBLE_CONFIG": str(root / "ansible.cfg"),
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertNotIn("No filter named 'search'", result.stdout + result.stderr)

    def test_infisical_static_secret_metadata_reason_codes_are_sanitized(self) -> None:
        """Check source/runtime CR metadata without requiring an operator annotation."""
        controller = ROOT / ".venv/bin/ansible-playbook"
        if not controller.is_file():
            controller = Path("/home/paul/projects/cristexweb/.venv/bin/ansible-playbook")
        if not controller.is_file():
            self.skipTest("canonical Ansible controller is unavailable on this host")

        parsed = yaml.safe_load(self.tasks)
        selected = [
            item
            for item in parsed
            if item.get("name") in {
                "Classify source/runtime Infisical StaticSecret metadata without values",
                "Emit sanitized source/runtime Infisical metadata reason codes",
                "Require exact source/runtime source revisions and no malformed CR lifecycle",
            }
        ]
        self.assertEqual(3, len(selected))
        self.assertIn("INFISICAL_STATIC_SECRET_METADATA_GUARD", self.tasks)
        self.assertIn("observedGeneration", self.tasks)
        self.assertIn("generation", self.tasks)
        self.assertIn("deletionTimestamp", self.tasks)
        self.assertIn("secrets.infisical.com/version belongs to the generated Secret target", self.tasks)

        good = {
            "item": {"namespace": "cristexhub-prod", "name": "cristexhub-prod-runtime"},
            "resources": [{
                "apiVersion": "secrets.infisical.com/v1beta1",
                "kind": "InfisicalStaticSecret",
                "metadata": {
                    "name": "cristexhub-prod-runtime",
                    "namespace": "cristexhub-prod",
                    "uid": "b9344d38-2930-460e-b443-81f8a109b1fb",
                    "resourceVersion": "2782385",
                    "generation": 1,
                },
                "status": {"conditions": [{"status": "True", "observedGeneration": 1}]},
                "spec": {"sources": [{
                    "projectId": "619656da-14f3-4872-857b-be103cdc5326",
                    "environmentSlug": "prod",
                }]},
            }],
        }

        def run_case(root: Path, result: dict) -> subprocess.CompletedProcess[str]:
            (root / "result.json").write_text(
                json.dumps({"rabbitmq_prod_credential_rotation_check_internal_infisical_sources": {"results": [result]}}),
                encoding="utf-8",
            )
            return subprocess.run(
                [
                    str(controller), "-i", str(root / "inventory"), str(root / "playbook.yml"),
                    "--check", "--diff", "--extra-vars", "@" + str(root / "result.json"),
                ],
                cwd=root,
                env={
                    "HOME": "/tmp", "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                    "ANSIBLE_CONFIG": str(root / "ansible.cfg"),
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
                capture_output=True,
                text=True,
                check=False,
            )

        with tempfile.TemporaryDirectory(prefix="rabbitmq-infisical-metadata-", dir="/dev/shm") as directory:
            root = Path(directory)
            role_tasks = root / "roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml"
            role_tasks.parent.mkdir(parents=True)
            role_tasks.write_text("---\n" + yaml.safe_dump(selected, sort_keys=False), encoding="utf-8")
            (root / "inventory").write_text("localhost ansible_connection=local\n", encoding="utf-8")
            (root / "ansible.cfg").write_text(
                "[defaults]\n" + f"roles_path = {root / 'roles'}\nretry_files_enabled = False\n",
                encoding="utf-8",
            )
            (root / "playbook.yml").write_text(
                "---\n- name: Evaluate CR metadata\n  hosts: localhost\n  gather_facts: false\n"
                "  roles:\n    - rabbitmq_prod_credential_rotation_check\n",
                encoding="utf-8",
            )
            accepted = run_case(root, good)
            self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)
            self.assertIn("cristexhub-prod-runtime: READY", accepted.stdout + accepted.stderr)
            self.assertNotIn("secrets.infisical.com/version", accepted.stdout + accepted.stderr)

            absent = dict(good, resources=[])
            rejected_absent = run_case(root, absent)
            self.assertNotEqual(0, rejected_absent.returncode, rejected_absent.stdout + rejected_absent.stderr)
            self.assertIn("cristexhub-prod-runtime: ABSENT", rejected_absent.stdout + rejected_absent.stderr)

            stale = json.loads(json.dumps(good))
            stale["resources"][0]["status"]["conditions"][0]["observedGeneration"] = 0
            rejected_stale = run_case(root, stale)
            self.assertNotEqual(0, rejected_stale.returncode, rejected_stale.stdout + rejected_stale.stderr)
            self.assertIn("cristexhub-prod-runtime: OBSERVED_GENERATION_STALE", rejected_stale.stdout + rejected_stale.stderr)

    def test_secret_metadata_registered_result_uses_bracket_items_on_ansible_219(self) -> None:
        """Evaluate the metadata assertion with a real Ansible 2.19 result-shaped mapping."""
        controller = ROOT / ".venv/bin/ansible-playbook"
        if not controller.is_file():
            controller = Path("/home/paul/projects/cristexweb/.venv/bin/ansible-playbook")
        if not controller.is_file():
            self.skipTest("canonical Ansible controller is unavailable on this host")

        self.assertIn("rabbitmq_prod_credential_rotation_check_internal_secret_metadata['items']", self.tasks)
        self.assertNotIn("rabbitmq_prod_credential_rotation_check_internal_secret_metadata.items", self.tasks)
        task = next(
            item
            for item in yaml.safe_load(self.tasks)
            if item.get("name") == "Require only metadata for exact Infisical-owned target Secrets"
        )

        def secret_metadata(name: str, namespace: str, part_of: str, uid: str, resource_version: str) -> dict:
            return {
                "metadata": {
                    "name": name,
                    "namespace": namespace,
                    "uid": uid,
                    "resourceVersion": resource_version,
                    "labels": {
                        "app.kubernetes.io/managed-by": "infisical",
                        "app.kubernetes.io/part-of": part_of,
                        "cristex.io/value-owner": "infisical-cloud",
                    },
                    "annotations": {"secrets.infisical.com/version": "7"},
                    "ownerReferences": [],
                }
            }

        metadata_result = {
            "metadata_only": True,
            "items": [
                secret_metadata("shared-rabbitmq-cristexhub-prod", "shared-services", "shared-rabbitmq", "uid-1", "101"),
                secret_metadata("cristexhub-prod-runtime", "cristexhub-prod", "cristexhub", "uid-2", "102"),
                secret_metadata("cristexhub-prod-ghcr-pull", "cristexhub-prod", "cristexhub", "uid-3", "103"),
            ],
        }
        with tempfile.TemporaryDirectory(prefix="rabbitmq-secret-metadata-", dir="/dev/shm") as directory:
            root = Path(directory)
            role_tasks = root / "roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml"
            role_tasks.parent.mkdir(parents=True)
            role_tasks.write_text("---\n" + yaml.safe_dump([task], sort_keys=False), encoding="utf-8")
            (root / "result.json").write_text(
                json.dumps({"rabbitmq_prod_credential_rotation_check_internal_secret_metadata": metadata_result}),
                encoding="utf-8",
            )
            (root / "inventory").write_text("localhost ansible_connection=local\n", encoding="utf-8")
            (root / "ansible.cfg").write_text(
                "[defaults]\n"
                f"roles_path = {root / 'roles'}\n"
                "retry_files_enabled = False\n",
                encoding="utf-8",
            )
            playbook = root / "playbook.yml"
            playbook.write_text(
                "---\n"
                "- name: Evaluate metadata-only Secret result\n"
                "  hosts: localhost\n"
                "  gather_facts: false\n"
                "  roles:\n"
                "    - rabbitmq_prod_credential_rotation_check\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    str(controller),
                    "-i",
                    str(root / "inventory"),
                    str(playbook),
                    "--check",
                    "--diff",
                    "--extra-vars",
                    "@" + str(root / "result.json"),
                ],
                cwd=root,
                env={
                    "HOME": "/tmp",
                    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                    "ANSIBLE_CONFIG": str(root / "ansible.cfg"),
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stdout + result.stderr
            self.assertEqual(0, result.returncode, output)
            self.assertNotIn("Type 'method' is unsupported", output)
            self.assertNotIn("must resolve to a 'list'", output)

    def test_wrapper_and_action_pins_match_current_canonical_sources(self) -> None:
        zero = "0" * 64
        action_source, action_count = re.subn(
            r'(?m)^_ACTION_CANONICAL_SHA256 = "[0-9a-f]{64}"$',
            '_ACTION_CANONICAL_SHA256 = "' + zero + '"',
            ACTION.read_text(),
        )
        action_canonical_source = action_source
        action_source, action_closure_count = re.subn(
            r'(?m)^_CLOSURE_MANIFEST_SHA256 = "[0-9a-f]{64}"$',
            '_CLOSURE_MANIFEST_SHA256 = "' + zero + '"',
            action_source,
        )
        strategy_source, strategy_count = re.subn(
            r'(?m)^_STRATEGY_CANONICAL_SHA256 = "[0-9a-f]{64}"$',
            '_STRATEGY_CANONICAL_SHA256 = "' + zero + '"',
            STRATEGY.read_text(),
        )
        strategy_canonical_source = strategy_source
        strategy_source, strategy_closure_count = re.subn(
            r'(?m)^_CLOSURE_MANIFEST_SHA256 = "[0-9a-f]{64}"$',
            '_CLOSURE_MANIFEST_SHA256 = "' + zero + '"',
            strategy_source,
        )
        wrapper_source, wrapper_count = re.subn(
            r"(?m)^wrapper_canonical_sha256='[0-9a-f]{64}'$",
            "wrapper_canonical_sha256='" + zero + "'",
            WRAPPER.read_text(),
        )
        wrapper_source, wrapper_closure_count = re.subn(
            r"(?m)^source_closure_sha256_expected='[0-9a-f]{64}'$",
            "source_closure_sha256_expected='" + zero + "'",
            wrapper_source,
        )
        self.assertEqual((1, 1, 1, 1, 1, 1), (action_count, action_closure_count, strategy_count, strategy_closure_count, wrapper_count, wrapper_closure_count))
        self.assertIn("SOURCE-CLOSURE.sha256", self.wrapper)
        self.assertIn("full_action_sha256", self.wrapper)
        self.assertIn("full_strategy_sha256", self.wrapper)
        self.assertNotRegex(
            self.wrapper,
            r"canonical_(?:action|strategy)_sha256.*0000000000000000000000000000000000000000000000000000000000000000",
        )
        self.assertIn("_CLOSURE_MANIFEST_SHA256", self.action)
        self.assertIn("_CLOSURE_MANIFEST_SHA256", self.strategy)
        self.assertIn("_source_closure_valid", self.action)
        self.assertIn("_source_closure_valid", self.strategy)
        action_canonical_source, action_closure_count = re.subn(
            r'(?m)^_CLOSURE_MANIFEST_SHA256 = "[0-9a-f]{64}"$',
            '_CLOSURE_MANIFEST_SHA256 = "' + zero + '"',
            action_canonical_source,
        )
        strategy_canonical_source, strategy_closure_count = re.subn(
            r'(?m)^_CLOSURE_MANIFEST_SHA256 = "[0-9a-f]{64}"$',
            '_CLOSURE_MANIFEST_SHA256 = "' + zero + '"',
            strategy_canonical_source,
        )
        self.assertEqual(
            hashlib.sha256(action_canonical_source.encode()).hexdigest(),
            re.search(r'(?m)^_ACTION_CANONICAL_SHA256 = "([0-9a-f]{64})"$', ACTION.read_text()).group(1),
        )
        self.assertEqual(
            hashlib.sha256(strategy_canonical_source.encode()).hexdigest(),
            re.search(r'(?m)^_STRATEGY_CANONICAL_SHA256 = "([0-9a-f]{64})"$', STRATEGY.read_text()).group(1),
        )
        self.assertEqual((1, 1), (action_closure_count, strategy_closure_count))
        self.assertEqual(
            hashlib.sha256(wrapper_source.encode()).hexdigest(),
            re.search(r"(?m)^wrapper_canonical_sha256='([0-9a-f]{64})'$", WRAPPER.read_text()).group(1),
        )
    def test_canonical_wrapper_invocation_reaches_role_strategy_with_ansible_219_tuple(self) -> None:
        """Exercise the exact wrapper argv without crossing the Kubernetes API boundary."""
        spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_strategy_role_reach", STRATEGY
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_argv = module.sys.argv
        original_cliargs = module.context.CLIARGS
        canonical_argv = [
            str(module._CONTROLLER),
            "-i",
            ".ansible/inventory.local.yml",
            "playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml",
            "--check",
            "--diff",
            "--limit",
            "crtxweb",
            "--extra-vars",
            '{"rabbitmq_prod_credential_rotation_check_approved":true}',
        ]
        module.sys.argv = canonical_argv
        module.context.CLIARGS = {
            "inventory": (str(module._INVENTORY_SOURCE),),
            "check": True,
            "diff": True,
            "subset": "crtxweb",
            "start_at_task": None,
            "step": False,
            "tags": ("all",),
            "skip_tags": (),
        }
        strategy = object.__new__(module.StrategyModule)
        try:
            self.assertTrue(module._canonical_argv())
            with mock.patch.object(module, "_wrapper_attestation_valid", return_value=True), \
                mock.patch.object(module, "_runtime_contract", return_value=True), \
                mock.patch.object(module, "_source_contract", return_value=True), \
                mock.patch.object(module.LinearStrategyModule, "run", return_value="role-scheduled") as base_run:
                self.assertEqual("role-scheduled", strategy.run(None, None))
                base_run.assert_called_once_with(None, None)
        finally:
            module.sys.argv = original_argv
            module.context.CLIARGS = original_cliargs

    def test_action_accepts_ansible_219_absolute_inventory_tuple(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_action_inventory_tuple", ACTION
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_argv = module.sys.argv
        original_cliargs = module.context.CLIARGS
        module.sys.argv = module._expected_argv()
        module.context.CLIARGS = {
            "inventory": (str(module._INVENTORY_SOURCE),),
            "check": True,
            "diff": True,
            "subset": "crtxweb",
            "start_at_task": None,
            "step": False,
            "tags": ("all",),
            "skip_tags": (),
        }
        try:
            with mock.patch.object(module, "_toolchain_valid", return_value=True), mock.patch.object(
                module, "_runtime_provenance_valid", return_value=True
            ), mock.patch.object(module, "_source_closure_valid", return_value=True), mock.patch.object(
                module, "_canonical_action_hash", return_value=module._ACTION_CANONICAL_SHA256
            ), mock.patch.object(module, "_canonical_strategy_hash", return_value="strategy-canonical"), mock.patch.object(
                module, "_canonical_wrapper_hash", return_value="wrapper-canonical"
            ), mock.patch.object(module, "_action_canonical_expected", return_value=module._ACTION_CANONICAL_SHA256), mock.patch.object(
                module, "_strategy_canonical_expected", return_value="strategy-canonical"
            ), mock.patch.object(
                module, "_wrapper_canonical_expected", return_value="wrapper-canonical"
            ), mock.patch.object(module, "_action_full_expected", return_value="action-full"), mock.patch.object(
                module, "_strategy_full_expected", return_value="strategy-full"
            ), mock.patch.object(module, "_full_action_hash", return_value="action-full"), mock.patch.object(
                module, "_full_strategy_hash", return_value="strategy-full"
            ), mock.patch.object(
                module, "_sha256", side_effect=lambda path: "action-full" if path == module._ACTION_SOURCE else "strategy-full"
            ), mock.patch.dict(
                module.os.environ,
                {
                    "ANSIBLE_CONFIG": str(module._ANSIBLE_CONFIG_SOURCE),
                    "ANSIBLE_LIBRARY": str(module._LIBRARY_PATH),
                    "ANSIBLE_ROLES_PATH": str(module._ROLES_PATH),
                    "CRISTEXWEB_RABBITMQ_PROD_ROTATION_ENTRYPOINT": "v1",
                    "CRISTEXWEB_RABBITMQ_PROD_ROTATION_MODE": "check",
                    "CRISTEXWEB_RABBITMQ_PROD_ROTATION_SOURCE_CLOSURE_PATH": str(module._CLOSURE_SOURCE),
                    "CRISTEXWEB_RABBITMQ_PROD_ROTATION_SOURCE_CLOSURE_SHA256": module._CLOSURE_MANIFEST_SHA256,
                },
                clear=True,
            ):
                self.assertTrue(module._selected())
        finally:
            module.sys.argv = original_argv
            module.context.CLIARGS = original_cliargs

    def test_action_rejects_each_tampered_runtime_digest_at_direct_startup(self) -> None:
        """The action's own preflight rejects every mutable digest export."""
        spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_action_runtime_digests_direct", ACTION
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        digest_sources = (
            "CONTROLLER_SHA256",
            "PYTHON_SHA256",
            "ANSIBLE_CONFIG_SHA256",
            "INVENTORY_SHA256",
            "REQUIREMENTS_SHA256",
            "COLLECTION_MANIFEST_SHA256",
            "COLLECTION_FILES_SHA256",
        )
        self.assertEqual(digest_sources, tuple(item[0] for item in module._RUNTIME_PROVENANCE))
        with tempfile.TemporaryDirectory() as directory:
            entries = []
            environment = {}
            for index, suffix in enumerate(digest_sources):
                path = Path(directory) / f"source-{index}"
                path.write_bytes(f"source-{index}\n".encode())
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                entries.append((suffix, path, digest))
                environment[f"CRISTEXWEB_RABBITMQ_PROD_ROTATION_{suffix}"] = digest
            with mock.patch.object(module, "_RUNTIME_PROVENANCE", tuple(entries)), mock.patch.dict(
                module.os.environ, environment, clear=True
            ):
                self.assertTrue(module._runtime_provenance_valid())
                for suffix in digest_sources:
                    with self.subTest(suffix=suffix):
                        tampered = dict(environment)
                        tampered[f"CRISTEXWEB_RABBITMQ_PROD_ROTATION_{suffix}"] = "0" * 64
                        with mock.patch.dict(module.os.environ, tampered, clear=True):
                            self.assertFalse(module._runtime_provenance_valid())

    def test_action_rejects_each_tampered_runtime_digest_at_alternate_startup(self) -> None:
        """The action selection guard repeats provenance checks on loader entry."""
        spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_action_runtime_digests_alternate", ACTION
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_argv = module.sys.argv
        original_cliargs = module.context.CLIARGS
        digest_sources = tuple(item[0] for item in module._RUNTIME_PROVENANCE)
        with tempfile.TemporaryDirectory() as directory:
            entries = []
            environment = {
                "ANSIBLE_CONFIG": str(module._ANSIBLE_CONFIG_SOURCE),
                "ANSIBLE_LIBRARY": str(module._LIBRARY_PATH),
                "ANSIBLE_ROLES_PATH": str(module._ROLES_PATH),
            }
            for index, suffix in enumerate(digest_sources):
                path = Path(directory) / f"source-{index}"
                path.write_bytes(f"source-{index}\n".encode())
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                entries.append((suffix, path, digest))
                environment[f"CRISTEXWEB_RABBITMQ_PROD_ROTATION_{suffix}"] = digest
            module.sys.argv = module._expected_argv()
            module.context.CLIARGS = {
                "inventory": (str(module._INVENTORY_SOURCE),),
                "check": True,
                "diff": True,
                "subset": "crtxweb",
                "start_at_task": None,
                "step": False,
                "tags": ("all",),
                "skip_tags": (),
            }
            try:
                environment.update({
                    "CRISTEXWEB_RABBITMQ_PROD_ROTATION_ENTRYPOINT": "v1",
                    "CRISTEXWEB_RABBITMQ_PROD_ROTATION_MODE": "check",
                    "CRISTEXWEB_RABBITMQ_PROD_ROTATION_SOURCE_CLOSURE_PATH": str(module._CLOSURE_SOURCE),
                    "CRISTEXWEB_RABBITMQ_PROD_ROTATION_SOURCE_CLOSURE_SHA256": module._CLOSURE_MANIFEST_SHA256,
                })
                with mock.patch.object(module, "_RUNTIME_PROVENANCE", tuple(entries)), mock.patch.object(module, "_toolchain_valid", return_value=True
                ), mock.patch.object(module, "_source_closure_valid", return_value=True), mock.patch.object(
                    module, "_canonical_action_hash", return_value=module._ACTION_CANONICAL_SHA256
                ), mock.patch.object(module, "_canonical_strategy_hash", return_value="strategy-canonical"), mock.patch.object(
                    module, "_canonical_wrapper_hash", return_value="wrapper-canonical"
                ), mock.patch.object(module, "_action_canonical_expected", return_value=module._ACTION_CANONICAL_SHA256), mock.patch.object(
                    module, "_strategy_canonical_expected", return_value="strategy-canonical"
                ), mock.patch.object(
                    module, "_wrapper_canonical_expected", return_value="wrapper-canonical"
                ), mock.patch.object(module, "_action_full_expected", return_value="action-full"), mock.patch.object(
                    module, "_strategy_full_expected", return_value="strategy-full"
                ), mock.patch.object(module, "_full_action_hash", return_value="action-full"), mock.patch.object(
                    module, "_full_strategy_hash", return_value="strategy-full"
                ), mock.patch.object(module, "_sha256", side_effect=lambda path: "action-full" if path == module._ACTION_SOURCE else "strategy-full" if path == module._STRATEGY_SOURCE else hashlib.sha256(path.read_bytes()).hexdigest()), mock.patch.dict(module.os.environ, environment, clear=True):
                    self.assertTrue(module._selected())
                    for suffix in digest_sources:
                        with self.subTest(suffix=suffix):
                            tampered = dict(environment)
                            tampered[f"CRISTEXWEB_RABBITMQ_PROD_ROTATION_{suffix}"] = "f" * 64
                            with mock.patch.dict(module.os.environ, tampered, clear=True):
                                self.assertFalse(module._selected())
            finally:
                module.sys.argv = original_argv
                module.context.CLIARGS = original_cliargs

    def test_real_ansible_219_startup_reaches_strategy_with_tuple_inventory(self) -> None:
        """Run ansible-playbook startup without scheduling a task or querying an API."""
        controller = Path("/home/paul/projects/cristexweb/.venv/bin/ansible-playbook")
        if not controller.is_file():
            self.skipTest("canonical controller is unavailable on this host")
        with tempfile.TemporaryDirectory(prefix="rabbitmq-strategy-startup-", dir="/dev/shm") as temporary:
            root = Path(temporary)
            project = root / "ansible"
            (project / ".ansible").mkdir(parents=True)
            (project / "plugins").mkdir()
            (project / "playbooks").mkdir()
            (project / "roles").mkdir()
            (project / "library").mkdir()
            (project / ".ansible/inventory.local.yml").write_text(
                "---\nall:\n  hosts:\n    crtxweb:\n      ansible_connection: local\n",
                encoding="utf-8",
            )
            (project / "ansible.cfg").write_text(
                "[defaults]\n"
                f"strategy_plugins = {project / 'plugins'}\n"
                f"roles_path = {project / 'roles'}\n"
                f"library = {project / 'library'}\n",
                encoding="utf-8",
            )
            (project / "playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml").write_text(
                "---\n"
                "- name: startup probe\n"
                "  hosts: crtxweb\n"
                "  gather_facts: false\n"
                "  strategy: rabbitmq_prod_credential_rotation_check_guarded_linear\n"
                "  tasks:\n"
                "    - name: must not run\n"
                "      ansible.builtin.debug:\n"
                "        msg: startup-probe-task\n",
                encoding="utf-8",
            )
            strategy_source = str(STRATEGY).replace("\\", "\\\\").replace('"', '\\"')
            plugin_source = f'''from pathlib import Path\nimport importlib.util\nfrom ansible import context\n\nsource = Path("{strategy_source}")\nspec = importlib.util.spec_from_file_location("rabbitmq_startup_probe_source", source)\nmodule = importlib.util.module_from_spec(spec)\nassert spec.loader is not None\nspec.loader.exec_module(module)\nmodule._CONTROLLER = Path("{controller}")\nmodule._INVENTORY_SOURCE = Path(__file__).resolve().parents[1] / ".ansible/inventory.local.yml"\nmodule._wrapper_attestation_valid = lambda: True\nmodule._runtime_contract = lambda: True\nmodule._source_contract = lambda: True\n\nclass StrategyModule(module.StrategyModule):\n    def run(self, iterator, play_context):\n        original = module.LinearStrategyModule.run\n        module.LinearStrategyModule.run = lambda self, *args: "startup-ok"\n        try:\n            result = super().run(iterator, play_context)\n        finally:\n            module.LinearStrategyModule.run = original\n        inventory = context.CLIARGS.get("inventory")\n        tags = context.CLIARGS.get("tags")\n        skip_tags = context.CLIARGS.get("skip_tags")\n        print(\n            "STARTUP_PROBE:strategy=started "\n            f"inventory_type={{type(inventory).__name__}} "\n            f"tags_type={{type(tags).__name__}} "\n            f"skip_tags_type={{type(skip_tags).__name__}} "\n            f"check_type={{type(context.CLIARGS.get('check')).__name__}} "\n            f"diff_type={{type(context.CLIARGS.get('diff')).__name__}}",\n            flush=True,\n        )\n        raise RuntimeError("startup-probe-stop")\n'''
            (project / "plugins/rabbitmq_prod_credential_rotation_check_guarded_linear.py").write_text(
                plugin_source,
                encoding="utf-8",
            )
            command = [
                str(controller),
                "-i",
                ".ansible/inventory.local.yml",
                "playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml",
                "--check",
                "--diff",
                "--limit",
                "crtxweb",
                "--extra-vars",
                '{"rabbitmq_prod_credential_rotation_check_approved":true}',
            ]
            environment = {
                "HOME": "/home/paul",
                "USER": "paul",
                "LOGNAME": "paul",
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "ANSIBLE_CONFIG": str(project / "ansible.cfg"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "CRISTEXWEB_RABBITMQ_PROD_ROTATION_ENTRYPOINT": "v1",
                "CRISTEXWEB_RABBITMQ_PROD_ROTATION_MODE": "check",
            }
            result = subprocess.run(
                command,
                cwd=project,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            output = result.stdout + result.stderr
            self.assertIn("STARTUP_PROBE:strategy=started", output)
            self.assertIn("inventory_type=tuple", output)
            self.assertIn("tags_type=tuple", output)
            self.assertIn("skip_tags_type=tuple", output)
            self.assertIn("check_type=bool", output)
            self.assertIn("diff_type=bool", output)
            self.assertNotIn("TASK_SELECTION_GUARD", output)
            self.assertNotIn("startup-probe-task", output)

    def test_relative_wrapper_argument_survives_wrapper_cwd_change_in_real_process(self) -> None:
        """Exercise the real /proc argv/cwd path used by the wrapper attestation."""
        with tempfile.TemporaryDirectory(prefix="rabbitmq-wrapper-attestation-", dir="/dev/shm") as temporary:
            root = Path(temporary)
            (root / "bin").mkdir()
            (root / "ansible").mkdir()
            wrapper = root / "bin/wrapper"
            probe = root / "probe.py"
            strategy_source = str(STRATEGY).replace("\\", "\\\\").replace('"', '\\"')
            wrapper_source = str(wrapper).replace("\\", "\\\\").replace('"', '\\"')
            repository_root = str(root).replace("\\", "\\\\").replace('"', '\\"')
            probe.write_text(
                f'''import importlib.util
import os
from pathlib import Path

spec = importlib.util.spec_from_file_location("rabbitmq_attestation_probe", "{strategy_source}")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
module._REPOSITORY_ROOT = Path("{repository_root}")
module._WRAPPER_SOURCE = Path("{wrapper_source}")
pid = int(os.environ["RABBITMQ_PROBE_WRAPPER_PID"])
print("WRAPPER_ARGUMENT_PROBE=" + str(module._canonical_wrapper_argument("bin/wrapper", pid)).lower(), flush=True)
''',
                encoding="utf-8",
            )
            wrapper.write_text(
                f'''#!/bin/sh
set -eu
pid=$$
export RABBITMQ_PROBE_WRAPPER_PID="$pid"
cd "{str(root / "ansible")}"
/home/paul/projects/cristexweb/.venv/bin/python "{str(probe)}"
''',
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            result = subprocess.run(
                ["bin/wrapper"],
                cwd=root,
                env={
                    "HOME": "/home/paul",
                    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("WRAPPER_ARGUMENT_PROBE=true", result.stdout)

    def test_strategy_reports_sanitized_reason_codes(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_strategy_reason_codes", STRATEGY
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_argv = module.sys.argv
        original_cliargs = module.context.CLIARGS
        module.sys.argv = [str(module._CONTROLLER), "--start-at-task", "forbidden"]
        module.context.CLIARGS = {
            "inventory": (str(module._INVENTORY_SOURCE),),
            "check": True,
            "diff": True,
            "subset": "crtxweb",
            "start_at_task": "forbidden",
            "step": False,
            "tags": ("all",),
            "skip_tags": (),
        }
        try:
            reasons = module._selection_guard_reasons()
            self.assertIn("selection-argv", reasons)
            self.assertIn("start-at-task", reasons)
            self.assertIn("canonical-argv", reasons)
            self.assertTrue(all(re.fullmatch(r"[a-z0-9-]+", reason) for reason in reasons))
            self.assertNotIn("forbidden", ",".join(reasons))
            strategy = object.__new__(module.StrategyModule)
            with self.assertRaises(Exception) as raised:
                strategy.run(None, None)
            message = str(raised.exception)
            self.assertIn("TASK_SELECTION_GUARD", message)
            self.assertNotIn("forbidden", message)
            self.assertRegex(message, r"\[[a-z0-9,-]+\]")
        finally:
            module.sys.argv = original_argv
            module.context.CLIARGS = original_cliargs

    def test_action_reports_sanitized_reason_codes(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_action_reason_codes", ACTION
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_argv = module.sys.argv
        original_cliargs = module.context.CLIARGS
        module.sys.argv = ["/tmp/not-ansible-playbook"]
        module.context.CLIARGS = {"inventory": (str(module._INVENTORY_SOURCE),)}
        try:
            reasons = module._selection_guard_reasons()
            self.assertIn("argv", reasons)
            self.assertIn("check-mode", reasons)
            self.assertTrue(all(re.fullmatch(r"[a-z0-9-]+", reason) for reason in reasons))
            self.assertNotIn("not-ansible-playbook", ",".join(reasons))
        finally:
            module.sys.argv = original_argv
            module.context.CLIARGS = original_cliargs

    def test_strategy_rejects_every_task_selection_override_before_role(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_strategy_selection_guard", STRATEGY
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_argv = module.sys.argv
        original_cliargs = module.context.CLIARGS
        canonical_argv = [
            str(module._CONTROLLER),
            "-i",
            ".ansible/inventory.local.yml",
            "playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml",
            "--check",
            "--diff",
            "--limit",
            "crtxweb",
            "--extra-vars",
            '{"rabbitmq_prod_credential_rotation_check_approved":true}',
        ]
        baseline = {
            "inventory": (str(module._INVENTORY_SOURCE),),
            "check": True,
            "diff": True,
            "subset": "crtxweb",
            "start_at_task": None,
            "step": False,
            "tags": ("all",),
            "skip_tags": (),
        }
        module.sys.argv = canonical_argv
        module.context.CLIARGS = baseline.copy()
        strategy = object.__new__(module.StrategyModule)
        try:
            with mock.patch.object(module, "_wrapper_attestation_valid", return_value=True), \
                mock.patch.object(module, "_runtime_contract", return_value=True), \
                mock.patch.object(module, "_source_contract", return_value=True), \
                mock.patch.object(module.LinearStrategyModule, "run", return_value="unexpected") as base_run:
                for field, value in (
                    ("start_at_task", "Require broker"),
                    ("step", True),
                    ("tags", ("queries",)),
                    ("skip_tags", ("always",)),
                ):
                    with self.subTest(field=field):
                        candidate = baseline.copy()
                        candidate[field] = value
                        module.context.CLIARGS = candidate
                        with self.assertRaises(Exception) as raised:
                            strategy.run(None, None)
                        self.assertIn("TASK_SELECTION_GUARD", str(raised.exception))
                        base_run.assert_not_called()
                        module.context.CLIARGS = baseline.copy()

                for selection in (
                    ["--start-at-task", "Require broker"],
                    ["--tags", "queries"],
                    ["--skip-tags", "always"],
                    ["-t", "queries"],
                ):
                    with self.subTest(selection=selection):
                        module.sys.argv = canonical_argv + selection
                        with self.assertRaises(Exception) as raised:
                            strategy.run(None, None)
                        self.assertIn("TASK_SELECTION_GUARD", str(raised.exception))
                        base_run.assert_not_called()
                        module.sys.argv = canonical_argv
        finally:
            module.sys.argv = original_argv
            module.context.CLIARGS = original_cliargs

    def test_canonical_wrapper_hash_matches_strategy_before_api_queries(self) -> None:
        strategy_spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_strategy_canonical", STRATEGY
        )
        self.assertIsNotNone(strategy_spec)
        self.assertIsNotNone(strategy_spec.loader)
        strategy_module = importlib.util.module_from_spec(strategy_spec)
        strategy_spec.loader.exec_module(strategy_module)

        action_spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_action_canonical", ACTION
        )
        self.assertIsNotNone(action_spec)
        self.assertIsNotNone(action_spec.loader)
        action_module = importlib.util.module_from_spec(action_spec)
        action_spec.loader.exec_module(action_module)

        expected = strategy_module._wrapper_canonical_expected()
        self.assertEqual(expected, strategy_module._wrapper_canonical_expected())
        self.assertEqual(expected, strategy_module._canonical_wrapper_hash(WRAPPER))
        self.assertEqual(expected, action_module._canonical_wrapper_hash(WRAPPER))
        self.assertEqual(
            strategy_module._strategy_canonical_expected(),
            strategy_module._canonical_hash(STRATEGY, "_STRATEGY_CANONICAL_SHA256"),
        )
        self.assertIn(hashlib.sha256(TASKS.read_bytes()).hexdigest(), self.wrapper)
        self.assertIn("_canonical_wrapper_hash(_WRAPPER_SOURCE)", self.strategy)
        self.assertNotIn(
            '_canonical_hash(_WRAPPER_SOURCE, "wrapper_canonical_sha256")',
            self.strategy,
        )

    def test_shell_and_python_canonicalizers_have_identical_pre_api_outputs(self) -> None:
        strategy_spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_strategy_shell_parity", STRATEGY
        )
        self.assertIsNotNone(strategy_spec)
        self.assertIsNotNone(strategy_spec.loader)
        strategy_module = importlib.util.module_from_spec(strategy_spec)
        strategy_spec.loader.exec_module(strategy_module)

        action_spec = importlib.util.spec_from_file_location(
            "rabbitmq_prod_credential_rotation_action_shell_parity", ACTION
        )
        self.assertIsNotNone(action_spec)
        self.assertIsNotNone(action_spec.loader)
        action_module = importlib.util.module_from_spec(action_spec)
        action_spec.loader.exec_module(action_module)

        wrapper_source = WRAPPER.read_text()
        functions_start = wrapper_source.index("sha256() {")
        functions_end = wrapper_source.index('[ "$(sha256 "$config")"', functions_start)
        shell_functions = wrapper_source[functions_start:functions_end]
        shell_script = "\n".join(
            (
                "set -eu",
                f"script_path={shlex.quote(str(WRAPPER))}",
                f"action={shlex.quote(str(ACTION))}",
                f"strategy={shlex.quote(str(STRATEGY))}",
                shell_functions,
                'printf \'A=%s\\nS=%s\\nW=%s\\n\' "$(canonical_action_sha256 "$action")" "$(canonical_strategy_sha256)" "$(canonical_wrapper_sha256)"',
            )
        )
        result = subprocess.run(
            ["/bin/sh", "-c", shell_script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        shell_values = dict(line.split("=", 1) for line in result.stdout.splitlines())
        self.assertEqual(
            action_module._canonical_action_hash(ACTION),
            shell_values["A"],
        )
        self.assertEqual(
            strategy_module._canonical_hash(STRATEGY, "_STRATEGY_CANONICAL_SHA256"),
            shell_values["S"],
        )
        self.assertEqual(
            strategy_module._canonical_wrapper_hash(WRAPPER),
            shell_values["W"],
        )
        self.assertEqual(
            strategy_module._wrapper_canonical_expected(),
            shell_values["W"],
        )

    def test_independent_action_and_strategy_mutations_fail_consistency_anchors(self) -> None:
        action_spec = importlib.util.spec_from_file_location("rabbitmq_action_mutation", ACTION)
        strategy_spec = importlib.util.spec_from_file_location("rabbitmq_strategy_mutation", STRATEGY)
        self.assertIsNotNone(action_spec)
        self.assertIsNotNone(strategy_spec)
        action_module = importlib.util.module_from_spec(action_spec)
        strategy_module = importlib.util.module_from_spec(strategy_spec)
        self.assertIsNotNone(action_spec.loader)
        self.assertIsNotNone(strategy_spec.loader)
        action_spec.loader.exec_module(action_module)
        strategy_spec.loader.exec_module(strategy_module)
        for path, hasher, expected, marker in (
            (ACTION, action_module._canonical_action_hash, action_module._ACTION_CANONICAL_SHA256, "return False  # mutation"),
            (STRATEGY, lambda candidate: strategy_module._canonical_hash(candidate, "_STRATEGY_CANONICAL_SHA256"), strategy_module._STRATEGY_CANONICAL_SHA256, "return False  # mutation"),
        ):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                source = path.read_text()
                mutated = Path(directory) / path.name
                mutated.write_text(source + "\n" + marker + "\n")
                self.assertNotEqual(expected, hasher(mutated))

    def test_coordinated_same_uid_rewrite_is_outside_integrity_claim(self) -> None:
        """Document the trusted-controller boundary instead of testing impossible provenance."""
        normalized = " ".join(Path(ROOT / "runbooks/cristexhub-prod-rabbitmq-credential-rotation.md").read_text().split())
        for required in (
            "consistency and drift checks, not independent cryptographic provenance",
            "malicious process already running as the trusted controller UID",
            "coordinate edits to the complete checkout",
            "outside the claimed integrity boundary",
        ):
            self.assertIn(required, normalized)
        self.assertIn("isolated action, strategy, wrapper, manifest, or runtime-toolchain drift", normalized)

    def test_isolated_wrapper_and_manifest_drift_fail_consistency_anchors(self) -> None:
        strategy_spec = importlib.util.spec_from_file_location(
            "rabbitmq_strategy_isolated_wrapper_manifest", STRATEGY
        )
        self.assertIsNotNone(strategy_spec.loader)
        strategy_module = importlib.util.module_from_spec(strategy_spec)
        strategy_spec.loader.exec_module(strategy_module)
        with tempfile.TemporaryDirectory() as directory:
            wrapper_candidate = Path(directory) / "wrapper"
            wrapper_candidate.write_text(WRAPPER.read_text() + "\n# isolated wrapper drift\n")
            self.assertNotEqual(
                strategy_module._wrapper_canonical_expected(),
                strategy_module._canonical_wrapper_hash(wrapper_candidate),
            )
            closure_candidate = Path(directory) / "SOURCE-CLOSURE.sha256"
            closure_candidate.write_text(strategy_module._CLOSURE_SOURCE.read_text() + "\n")
            self.assertNotEqual(
                strategy_module._CLOSURE_MANIFEST_SHA256,
                hashlib.sha256(closure_candidate.read_bytes()).hexdigest(),
            )

    def test_source_closure_exposes_cross_file_consistency_anchors(self) -> None:
        action_spec = importlib.util.spec_from_file_location("rabbitmq_action_closure_anchors", ACTION)
        strategy_spec = importlib.util.spec_from_file_location("rabbitmq_strategy_closure_anchors", STRATEGY)
        self.assertIsNotNone(action_spec.loader)
        self.assertIsNotNone(strategy_spec.loader)
        action_module = importlib.util.module_from_spec(action_spec)
        strategy_module = importlib.util.module_from_spec(strategy_spec)
        action_spec.loader.exec_module(action_module)
        strategy_spec.loader.exec_module(strategy_module)
        self.assertEqual(action_module._ACTION_CANONICAL_SHA256, action_module._action_canonical_expected())
        self.assertEqual(strategy_module._STRATEGY_CANONICAL_SHA256, strategy_module._strategy_canonical_expected())
        self.assertEqual(action_module._action_full_expected(), strategy_module._action_full_expected())
        self.assertEqual(action_module._strategy_full_expected(), strategy_module._strategy_full_expected())
        self.assertTrue(action_module._source_closure_valid())
        self.assertTrue(strategy_module._source_closure_valid())

    def test_action_selection_rejects_wrong_environment_mode_and_strategy_argv0(self) -> None:
        action_spec = importlib.util.spec_from_file_location("rabbitmq_action_mode", ACTION)
        strategy_spec = importlib.util.spec_from_file_location("rabbitmq_strategy_argv0", STRATEGY)
        action_module = importlib.util.module_from_spec(action_spec)
        strategy_module = importlib.util.module_from_spec(strategy_spec)
        self.assertIsNotNone(action_spec.loader)
        self.assertIsNotNone(strategy_spec.loader)
        action_spec.loader.exec_module(action_module)
        strategy_spec.loader.exec_module(strategy_module)
        original_argv = strategy_module.sys.argv
        try:
            strategy_module.sys.argv = ["/tmp/not-ansible-playbook"] + strategy_module.sys.argv[1:]
            self.assertFalse(strategy_module._canonical_argv())
        finally:
            strategy_module.sys.argv = original_argv
        self.assertIn('CRISTEXWEB_RABBITMQ_PROD_ROTATION_MODE', self.action)

    def test_source_modes_and_hashes_are_explicit(self) -> None:
        expected_modes = {
            WRAPPER: 0o755,
            TASKS: 0o644,
            DEFAULTS: 0o644,
            PLAYBOOK: 0o644,
            POLICY: 0o644,
            ACTION: 0o644,
            METADATA: 0o755,
            STRATEGY: 0o644,
        }
        for path, mode in expected_modes.items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(mode, stat.S_IMODE(path.stat().st_mode), path)
        metadata_hash = hashlib.sha256(METADATA.read_bytes()).hexdigest()
        self.assertIn(metadata_hash, self.action)
        self.assertIn(metadata_hash, self.wrapper)
        for item in self.defaults["rabbitmq_prod_credential_rotation_check_source_files"]:
            path = ROOT / item["path"]
            self.assertEqual(item["sha256"], hashlib.sha256(path.read_bytes()).hexdigest(), path)
        self.assertEqual(
            hashlib.sha256(POLICY.read_bytes()).hexdigest(),
            self.defaults["rabbitmq_prod_credential_rotation_check_source_policy_sha256"],
        )

    def test_no_values_or_plaintext_credentials_are_in_lane(self) -> None:
        combined = "\n".join(path.read_text() for path in (POLICY, DEFAULTS, TASKS, ACTION, METADATA, WRAPPER))
        self.assertNotRegex(combined, r"(?i)(?:amqps?|rabbitmq)://[^\s/]+:[^\s@]+@")
        self.assertNotRegex(combined, r"(?i)password\s*[:=]\s*[^'\"$<{\n][^\n]*")
        self.assertNotIn("AGE-SECRET-KEY-", combined)
        self.assertNotIn("eyJ", combined)
        self.assertNotIn("kubectl get secret", combined)


if __name__ == "__main__":
    unittest.main()
