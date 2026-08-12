from __future__ import annotations

import stat
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ansible/files/policies/infisical-secret-zero-lane.yml"
SEED_WRAPPER = ROOT / "ansible/bin/seed-infisical-universal-auth"
UPLOAD_WRAPPER = ROOT / "ansible/bin/upload-infisical-bootstrap-values"
SEED_PLAYBOOK = ROOT / "ansible/playbooks/seed_infisical_universal_auth.yml"
SEED_DEFAULTS = ROOT / "ansible/roles/infisical_universal_auth_seed/defaults/main.yml"
SEED_TASKS = ROOT / "ansible/roles/infisical_universal_auth_seed/tasks/main.yml"
SEED_PLUGIN = ROOT / "ansible/plugins/action/infisical_universal_auth_seed_guarded_k8s.py"
RUNBOOK = ROOT / "runbooks/infisical-universal-auth-value-lane.md"

EXPECTED_LABELS = {
    "app.kubernetes.io/managed-by": "ansible",
    "app.kubernetes.io/part-of": "infisical-operator",
    "cristex.io/component": "infisical-runtime-auth",
    "cristex.io/value-owner": "infisical-cloud",
}
EXPECTED_CREDENTIALS = {
    ("argocd", "argocd-infisical-universal-auth"),
    ("shared-services", "shared-postgresql-infisical-universal-auth"),
    ("shared-services", "shared-mongodb-infisical-universal-auth"),
}
EXPECTED_PATHS = {
    "/argocd": {
        "ARGOCD_ADMIN_PASSWORD_BCRYPT",
        "ARGOCD_ADMIN_PASSWORD_MTIME",
        "ARGOCD_SERVER_SECRETKEY",
        "ARGOCD_REDIS_AUTH",
        "ARGOCD_TLS_CA_CRT",
        "ARGOCD_TLS_CRT",
        "ARGOCD_TLS_KEY",
    },
    "/shared-services/postgresql": {
        "POSTGRESQL_ADMIN_USERNAME",
        "POSTGRESQL_ADMIN_PASSWORD",
        "POSTGRESQL_TLS_CA_CRT",
        "POSTGRESQL_TLS_CRT",
        "POSTGRESQL_TLS_KEY",
        "POSTGRESQL_CRISTEXHUB_DEV_USERNAME",
        "POSTGRESQL_CRISTEXHUB_DEV_PASSWORD",
        "POSTGRESQL_CRISTEXHUB_PROD_USERNAME",
        "POSTGRESQL_CRISTEXHUB_PROD_PASSWORD",
        "POSTGRESQL_REACTIVE_RESUME_DEV_USERNAME",
        "POSTGRESQL_REACTIVE_RESUME_DEV_PASSWORD",
        "POSTGRESQL_REACTIVE_RESUME_PROD_USERNAME",
        "POSTGRESQL_REACTIVE_RESUME_PROD_PASSWORD",
        "POSTGRESQL_KEYCLOAK_USERNAME",
        "POSTGRESQL_KEYCLOAK_PASSWORD",
    },
    "/shared-services/mongodb": {
        "MONGODB_ADMIN_USERNAME",
        "MONGODB_ADMIN_PASSWORD",
        "MONGODB_TLS_CA_CRT",
        "MONGODB_TLS_PEM",
        "MONGODB_CRISTEXHUB_DEV_USERNAME",
        "MONGODB_CRISTEXHUB_DEV_PASSWORD",
        "MONGODB_CRISTEXHUB_PROD_USERNAME",
        "MONGODB_CRISTEXHUB_PROD_PASSWORD",
    },
}


class InfisicalSecretZeroLaneContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = yaml.safe_load(POLICY.read_text())
        cls.defaults = yaml.safe_load(SEED_DEFAULTS.read_text())
        cls.tasks = yaml.safe_load(SEED_TASKS.read_text())
        cls.seed_source = SEED_WRAPPER.read_text()
        cls.upload_source = UPLOAD_WRAPPER.read_text()
        cls.plugin_source = SEED_PLUGIN.read_text()

    def test_policy_freezes_project_paths_credentials_and_keys(self) -> None:
        self.assertEqual("cristexweb-infrastructure", self.policy["project_slug"])
        self.assertEqual("prod", self.policy["environment_slug"])
        self.assertEqual("cristexweb-infrastructure", self.policy["infisical_project_slug"])
        self.assertEqual("prod", self.policy["infisical_environment_slug"])
        self.assertTrue(self.policy["scope_separation"]["infisical_environment_is_prod"])
        self.assertEqual("not-authorized", self.policy["scope_separation"]["kubernetes_cristexhub_prod_activation"])
        self.assertEqual("absent", self.policy["scope_separation"]["kubernetes_prod_namespace_or_path"])
        self.assertEqual(
            {
                "argocd": "/argocd",
                "shared-postgresql": "/shared-services/postgresql",
                "shared-mongodb": "/shared-services/mongodb",
            },
            self.policy["paths"],
        )
        credentials = self.policy["credential_secrets"]
        self.assertEqual(EXPECTED_LABELS, credentials["labels"])
        self.assertEqual(
            EXPECTED_CREDENTIALS,
            {(item["namespace"], item["name"]) for item in credentials["contracts"]},
        )
        for contract in credentials["contracts"]:
            self.assertEqual("Opaque", contract["type"])
            self.assertEqual(["clientId", "clientSecret"], contract["keys"])
            self.assertEqual(EXPECTED_LABELS, contract["labels"])
        paths = {item["path"]: set(item["keys"]) for item in self.policy["value_paths"]}
        self.assertEqual(EXPECTED_PATHS, paths)
        consumer_credentials = self.policy["consumer_credentials"]
        self.assertEqual(5, len(consumer_credentials["postgresql"]))
        self.assertEqual(2, len(consumer_credentials["mongodb"]))
        self.assertEqual(
            {item["secret"] for items in consumer_credentials.values() for item in items},
            {
                "shared-postgresql-cristexhub-dev",
                "shared-postgresql-cristexhub-prod",
                "shared-postgresql-reactive-resume-dev",
                "shared-postgresql-reactive-resume-prod",
                "shared-postgresql-keycloak",
                "shared-mongodb-cristexhub-dev",
                "shared-mongodb-cristexhub-prod",
            },
        )
        self.assertTrue(
            all(
                item["activation"] == "inactive"
                for items in consumer_credentials.values()
                for item in items
            )
        )
        self.assertEqual(
            {
                "owner": "protected-controller-value-lane",
                "logical_consumer_credentials": "generated-and-uploaded",
                "provisioning_roles": "forbidden",
                "username_contract": "frozen-principal",
                "random_password_contract": "64-lowercase-hex",
                "upload_response_contract": "exact-key-closure-and-revision-marker",
            },
            self.policy["value_generation"],
        )
        self.assertTrue(self.policy["identities"]["provisioning"] == "out-of-band")
        self.assertFalse(self.policy["identities"]["create_or_delete_allowed"])
        slots = [
            (component["runtime"]["identity_slot"], component["writer"]["identity_slot"])
            for component in self.policy["identities"]["components"].values()
        ]
        self.assertEqual(3, len(set(slots)))
        self.assertTrue(all(runtime != writer for runtime, writer in slots))
        self.assertTrue(self.policy["scope_separation"]["runtime_credentials_are_not_writer_credentials"])
        self.assertTrue(self.policy["scope_separation"]["components_have_distinct_credentials"])
        self.assertEqual(12, self.policy["value_paths"][0]["bcrypt"]["cost"])

    def test_policy_aligns_with_db_and_argocd_seam_contracts(self) -> None:
        db_defaults = ROOT / "ansible/roles/infisical_argocd_secrets_bootstrap/defaults/main.yml"
        argo_defaults = yaml.safe_load(db_defaults.read_text())
        self.assertEqual(
            {"name": "argocd-infisical-universal-auth", "namespace": "argocd"},
            {
                "name": argo_defaults["infisical_argocd_secrets_bootstrap_credential_contract"]["name"],
                "namespace": argo_defaults["infisical_argocd_secrets_bootstrap_credential_contract"]["namespace"],
            },
        )
        db_source_root = ROOT / "ansible/files/components"
        # The database seam may be supplied by the integration stash.  When present,
        # assert the exact identities and paths rather than inventing another closure.
        db_component = db_source_root / "infisical-database-secrets/source"
        if db_component.exists():
            source_text = "\n".join(path.read_text() for path in db_component.glob("*.yaml"))
            for required in (
                "shared-postgresql-infisical-universal-auth",
                "/shared-services/postgresql",
                "619656da-14f3-4872-857b-be103cdc5326",
                "prod",
            ):
                self.assertIn(required, source_text)
        database_policy = yaml.safe_load(
            (ROOT / "ansible/files/policies/shared-database-architecture.yml").read_text()
        )
        for engine_name in ("postgresql", "mongodb"):
            consumers = database_policy["engines"][engine_name]["consumers"]
            lane_consumers = self.policy["consumer_credentials"][engine_name]
            self.assertEqual(set(consumers), {item["consumer"] for item in lane_consumers})
            for item in lane_consumers:
                consumer = consumers[item["consumer"]]
                self.assertEqual(item["secret"], consumer["credential_secret"])
                self.assertEqual(item["username"], consumer["principal_name"])
                self.assertEqual("inactive", item["activation"])

    def test_seed_role_and_plugin_are_apply_only_and_no_log(self) -> None:
        self.assertIn("not ansible_check_mode", SEED_TASKS.read_text())
        self.assertIn("not ansible_diff_mode", SEED_TASKS.read_text())
        self.assertGreaterEqual(SEED_TASKS.read_text().count("no_log: true"), 12)
        self.assertIn("INTERNAL_VARIABLE_GUARD", SEED_TASKS.read_text())
        for required in (
            "TASK_SELECTION_GUARD",
            "MUTATION_ARGUMENT_GUARD",
            "CRISTEXWEB_INFISICAL_UNIVERSAL_AUTH_SEED_ENTRYPOINT",
            "argocd-infisical-universal-auth",
            "shared-postgresql-infisical-universal-auth",
            "shared-mongodb-infisical-universal-auth",
            "binaryData",
            "ownerReferences",
            "immutable",
            "k3s-datastore-preflight.local.json",
            "k3s-secret-encryption-recovery.local.json",
            "encryption.status == 'enabled'",
            "encryption.rotation_stage == 'finished'",
            "backup_verified == true",
            "key_recovery_verified == true",
            "isolated_restore_verified == true",
            "datastore_preflight_sha256",
            "k3s_version",
            "attested_at_utc",
            "expires_at_utc",
            "total_seconds() <= 86400",
            "invocation.check_mode == true",
            "health.node_stage == 'ready'",
            "datastore_evidence.schema_version == 2",
            "k3s.executable_status == 'safe'",
            "data_dir_source in ['default_no_config', 'config_default', 'explicit_arg']",
            "disclosure_controls.remote_mutation == false",
            "disclosure_controls.raw_command_output == false",
        ):
            self.assertIn(required, self.plugin_source + SEED_TASKS.read_text())
        self.assertIn("become: false", SEED_PLAYBOOK.read_text())
        self.assertNotIn("--diff", self.seed_source)
        self.assertNotIn("--check", self.seed_source)
        self.assertIn("--extra-vars \"@$vars_file\"", self.seed_source)
        self.assertIn("find-generic-password", self.seed_source)
        self.assertIn("chmod 600", self.seed_source)
        self.assertIn("/usr/bin/env -i", self.seed_source)
        self.assertIn("do not start an Infisical-compatible endpoint", RUNBOOK.read_text())

    def test_upload_is_file_input_only_and_has_protected_api_cleanup(self) -> None:
        for required in (
            "apply-only",
            "read_protected_json",
            "api-endpoint",
            "--slurpfile",
            "--rawfile",
            "--data-binary",
            "--config",
            "v1/auth/universal-auth/login",
            "v3/secrets/batch",
            "pending_marker",
            "completed_marker",
            "refusing implicit Infisical value rotation",
            "age-keygen",
            "shasum -a 256",
            "rm -rf -- \"$temporary_directory\"",
            "htpasswd_tool",
            "-C 12",
            "refusing random credential outside exact 64-hex contract",
            "openssl_tool",
            "checkend 86400",
            "subjectAltName",
            "DNS SAN count",
            "keyCertSign",
            "expected_archive_members",
            "exact member closure",
            "refusing non-regular Infisical pending archive members",
            "(. | keys | sort)",
            "metadata_keys \"$component\" \"$path\" \"$expected_keys\" done",
            "env -i PATH=/usr/bin:/bin LC_ALL=C.UTF-8",
            "-q --config",
            ".revision == (.revision | floor)",
        ):
            self.assertIn(required, self.upload_source)
        self.assertNotIn(".secretsVersion", self.upload_source)
        self.assertNotIn(".secretVersion", self.upload_source)
        self.assertNotIn("// .token", self.upload_source)
        self.assertNotIn("--rotate", self.upload_source)
        self.assertNotIn("--dry-run", self.upload_source)
        self.assertNotIn("echo \"$", self.upload_source)
        self.assertNotIn("CRISTEXWEB_INFISICAL_FAKE_ENDPOINT", self.upload_source)
        self.assertIn("[ \"$api_base\" = 'https://app.infisical.com/api' ]", self.upload_source)
        for required_prod_binding in (
            "environment=prod",
            '"environmentSlug":"prod"',
            'environmentSlug == "prod"',
            "environmentSlug=prod",
            "--arg environment prod",
        ):
            self.assertIn(required_prod_binding, self.upload_source)
        for superseded_bootstrap_binding in (
            "environment=bootstrap",
            '"environmentSlug":"bootstrap"',
            'environmentSlug == "bootstrap"',
            "environmentSlug=bootstrap",
            "--arg environment bootstrap",
        ):
            self.assertNotIn(superseded_bootstrap_binding, self.upload_source)
        for secret_name in (
            "clientId",
            "clientSecret",
            "ARGOCD_ADMIN_PASSWORD_BCRYPT",
            "POSTGRESQL_TLS_KEY",
            "POSTGRESQL_CRISTEXHUB_DEV_USERNAME",
            "POSTGRESQL_CRISTEXHUB_DEV_PASSWORD",
            "POSTGRESQL_CRISTEXHUB_PROD_USERNAME",
            "POSTGRESQL_CRISTEXHUB_PROD_PASSWORD",
            "POSTGRESQL_REACTIVE_RESUME_DEV_USERNAME",
            "POSTGRESQL_REACTIVE_RESUME_DEV_PASSWORD",
            "POSTGRESQL_REACTIVE_RESUME_PROD_USERNAME",
            "POSTGRESQL_REACTIVE_RESUME_PROD_PASSWORD",
            "POSTGRESQL_KEYCLOAK_USERNAME",
            "POSTGRESQL_KEYCLOAK_PASSWORD",
            "MONGODB_TLS_PEM",
            "MONGODB_CRISTEXHUB_DEV_USERNAME",
            "MONGODB_CRISTEXHUB_DEV_PASSWORD",
            "MONGODB_CRISTEXHUB_PROD_USERNAME",
            "MONGODB_CRISTEXHUB_PROD_PASSWORD",
        ):
            self.assertIn(secret_name, self.upload_source)

    def test_source_route_contract_is_exact_and_nontransactional_state_is_blocked(self) -> None:
        # This source-level contract checks the fixed paths and key sets. No endpoint is
        # started and no network request is made by this test.
        routes = ["/v1/auth/universal-auth/login", "/v3/secrets/batch"]
        self.assertTrue(all(route in self.upload_source for route in routes))
        self.assertIn("metadata_keys", self.upload_source)
        self.assertIn("UNKNOWN — STOP", self.upload_source)
        self.assertIn("ambiguous-post Infisical remote state", self.upload_source)
        self.assertIn("set_progress_done", self.upload_source)
        self.assertIn('--argjson expected "$expected_keys"', self.upload_source)
        self.assertIn("($actual | unique | sort) == ($expected | unique | sort)", self.upload_source)
        self.assertIn("refusing an unverified Infisical value upload response", self.upload_source)
        self.assertEqual(
            {
                "argocd": 7,
                "postgresql": 15,
                "mongodb": 8,
            },
            {
                "argocd": len(EXPECTED_PATHS["/argocd"]),
                "postgresql": len(EXPECTED_PATHS["/shared-services/postgresql"]),
                "mongodb": len(EXPECTED_PATHS["/shared-services/mongodb"]),
            },
        )

    def test_wrappers_and_negative_fixtures_are_executable_and_reject_passthrough(self) -> None:
        for path in (
            SEED_WRAPPER,
            UPLOAD_WRAPPER,
            ROOT / "tests/reject_infisical_universal_auth_seed_task_start.sh",
            ROOT / "tests/reject_infisical_values_upload_passthrough.sh",
        ):
            self.assertTrue(path.exists())
            self.assertTrue(path.stat().st_mode & stat.S_IXUSR)
            self.assertEqual(0, subprocess.run(["sh", "-n", str(path)], check=False).returncode)
        for wrapper in (SEED_WRAPPER, UPLOAD_WRAPPER):
            for args in ((), ("check",), ("apply", "--rotate")):
                result = subprocess.run([str(wrapper), *args], capture_output=True, text=True, check=False)
                self.assertNotEqual(0, result.returncode)
        for fixture in (
            ROOT / "tests/reject_infisical_universal_auth_seed_action_only.yml",
            ROOT / "tests/reject_infisical_universal_auth_seed_internal_injection.yml",
        ):
            self.assertTrue(fixture.exists())

    def test_source_contains_no_values_or_private_material(self) -> None:
        text = "\n".join(
            path.read_text()
            for path in (POLICY, RUNBOOK, SEED_WRAPPER, UPLOAD_WRAPPER, SEED_DEFAULTS, SEED_TASKS)
        )
        for forbidden in (
            "BEGIN PRIVATE KEY",
            "BEGIN RSA PRIVATE KEY",
            "clientSecret: real",
            "clientSecret: committed",
            "stringData:",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("NOT RUN/BLOCKED", RUNBOOK.read_text())


if __name__ == "__main__":
    unittest.main()
