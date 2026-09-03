from __future__ import annotations

import copy
import hashlib
import importlib.util
import re
import stat
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "ansible/bin/check-cristexhub-prod-mongodb-credential-rotation"
PLAYBOOK = ROOT / "ansible/playbooks/check_cristexhub_prod_mongodb_credential_rotation.yml"
ROLE = ROOT / "ansible/roles/cristexhub_prod_mongodb_credential_rotation_check"
TASKS = ROLE / "tasks/main.yml"
DEFAULTS = ROLE / "defaults/main.yml"
POLICY = ROOT / "ansible/files/policies/cristexhub-prod-mongodb-credential-rotation.yml"
METADATA = ROOT / "ansible/library/cristexhub_prod_mongodb_credential_rotation_metadata.py"
ENGINE_SOURCE = ROOT / "ansible/files/components/infisical-database-secrets/source/shared-mongodb-infisical-secrets.yaml"
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
        ):
            self.assertIn(required, self.wrapper)
        self.assertNotIn("--extra-vars.*apply", self.wrapper)
        self.assertNotIn("ansible-playbook.*--diff'", self.wrapper)
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

    def test_source_manifest_hashes_are_wrapper_bound(self) -> None:
        source_pairs = (
            (ENGINE_SOURCE, "engine_source_manifest_sha256_expected"),
            (RUNTIME_SOURCE, "runtime_source_manifest_sha256_expected"),
            (NETWORKPOLICY_DEFAULT_DENY, "networkpolicy_default_deny_sha256_expected"),
            (NETWORKPOLICY_ALLOW, "networkpolicy_allow_sha256_expected"),
        )
        for path, variable in source_pairs:
            match = re.search(rf"(?m)^{re.escape(variable)}='([0-9a-f]{{64}})'$", self.wrapper)
            self.assertIsNotNone(match, variable)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), match.group(1))
        for path in (ENGINE_SOURCE, RUNTIME_SOURCE, NETWORKPOLICY_DEFAULT_DENY, NETWORKPOLICY_ALLOW):
            self.assertIn(str(path.relative_to(ROOT)), self.tasks)

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
        self.assertIsNone(module._metadata({**payload, "metadata": {**payload["metadata"], "deletionTimestamp": 7}}))
        self.assertIn("deletionTimestamp is none", self.tasks)

    def test_metadata_module_negotiates_partial_object_only(self) -> None:
        for phrase in (
            "PartialObjectMetadata",
            "application/json;as=PartialObjectMetadata;g=meta.k8s.io;v=v1",
            "set(payload) != _ALLOWED_TOP_LEVEL_KEYS",
            "module.exit_json(",
            "resource_kind=resource_kind,",
            "Never return managedFields",
            '"data" in payload',
        ):
            self.assertIn(phrase, self.metadata)
        self.assertNotIn("stringData", self.metadata)
        self.assertNotIn("module.exit_json(changed=False, data=", self.metadata)

    def test_metadata_targets_and_revision_channels_are_exact(self) -> None:
        resources = self.defaults["cristexhub_prod_mongodb_credential_rotation_check_metadata_resources"]
        by_id = {resource["id"]: resource for resource in resources}
        self.assertEqual(
            {"engine_source", "runtime_source", "engine_target", "runtime_target"},
            set(by_id),
        )
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
            for path in (WRAPPER, PLAYBOOK, TASKS, DEFAULTS, POLICY, METADATA, RUNBOOK)
        )
        for forbidden in (
            "kubectl apply", "kubectl delete", "kubectl patch", "rabbitmqctl",
            "mongosh", "ansible.builtin.k8s:", "stringData:", "Secret.data",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertIn("resource_kind: \"{{ item.kind }}\"", self.tasks)
        self.assertIn("metadata_only=True", self.metadata)
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
