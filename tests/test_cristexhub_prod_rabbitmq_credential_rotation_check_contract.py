from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import stat
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
POLICY = ANSIBLE / "files/policies/cristexhub-prod-rabbitmq-credential-rotation.yml"
DEFAULTS = ANSIBLE / "roles/rabbitmq_prod_credential_rotation_check/defaults/main.yml"
TASKS = ANSIBLE / "roles/rabbitmq_prod_credential_rotation_check/tasks/main.yml"
PLAYBOOK = ANSIBLE / "playbooks/check_cristexhub_prod_rabbitmq_credential_rotation.yml"
WRAPPER = ANSIBLE / "bin/check-cristexhub-prod-rabbitmq-credential-rotation"
ACTION = ANSIBLE / "plugins/action/rabbitmq_prod_credential_rotation_check_guarded_k8s.py"
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
        self.assertIn("canonical_action_sha256", self.wrapper)
        self.assertIn("canonical_wrapper_sha256", self.wrapper)
        self.assertIn("check_cristexhub_prod_rabbitmq_credential_rotation.yml", self.wrapper)
        self.assertNotIn("--extra-vars '{\"rabbitmq_prod_credential_rotation_check_approved\":false}'", self.wrapper)
        self.assertEqual(0, subprocess.run(["/bin/sh", "-n", str(WRAPPER)], check=False).returncode)

    def test_action_binds_ancestor_argv_and_strips_results(self) -> None:
        for required in (
            "_ancestor",
            "_proc_cmdline",
            "Path(_proc_cmdline(pid)[1]).resolve() == _WRAPPER_SOURCE",
            "sys.argv == _expected_argv()",
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
                "labels": {"app.kubernetes.io/managed-by": "infisical"},
                "managedFields": [],
            },
        }
        result = module._metadata(Client(base), "shared-services", "shared-rabbitmq-cristexhub-prod")
        self.assertEqual("shared-rabbitmq-cristexhub-prod", result["metadata"]["name"])
        self.assertEqual("shared-services", result["metadata"]["namespace"])
        self.assertEqual("7", result["metadata"]["annotations"]["secrets.infisical.com/version"])
        for payload in (
            {**base, "data": {}},
            {**base, "metadata": {**base["metadata"], "name": "other"}},
            {**base, "metadata": {**base["metadata"], "namespace": "other"}},
            {**base, "metadata": {**base["metadata"], "deletionTimestamp": "2026-08-26T00:00:01Z"}},
            {**base, "metadata": {**base["metadata"], "annotations": {"bad": 1}}},
        ):
            with self.assertRaises(ValueError):
                module._metadata(Client(payload), "shared-services", "shared-rabbitmq-cristexhub-prod")

    def test_tasks_parse_and_bind_query_set_without_nested_jinja(self) -> None:
        parsed = yaml.safe_load(self.tasks)
        self.assertIsInstance(parsed, list)
        self.assertEqual(24, len(parsed))
        for task in parsed:
            self.assertIsInstance(task, dict)
            if "ansible.builtin.assert" in task:
                self.assertIn("fail_msg", task["ansible.builtin.assert"])
                self.assertNotIn("fail_msg", task)
        self.assertIn("queries:", self.tasks)
        self.assertIn('binding.get("queries") == sorted(_EXPECTED_QUERIES)', self.action)
        self.assertIn("args.get(\"query\") in binding.get(\"queries\", [])", self.action)
        self.assertIn("_RABBITMQ_CONFIG_SOURCE", self.action)
        self.assertIn("_ANSIBLE_CONFIG_SOURCE", self.action)
        self.assertNotIn("== '{{ .RABBITMQ_URL.Value }}'", self.tasks)
        self.assertIn("'{' ~ '{ .RABBITMQ_URL.Value }' ~ '}'", self.tasks)

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

    def test_source_modes_and_hashes_are_explicit(self) -> None:
        expected_modes = {
            WRAPPER: 0o755,
            TASKS: 0o644,
            DEFAULTS: 0o644,
            PLAYBOOK: 0o644,
            POLICY: 0o644,
            ACTION: 0o644,
            METADATA: 0o755,
        }
        for path, mode in expected_modes.items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(mode, stat.S_IMODE(path.stat().st_mode), path)
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
