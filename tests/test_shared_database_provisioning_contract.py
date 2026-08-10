from __future__ import annotations

import hashlib
import re
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ansible/files/policies/shared-database-architecture.yml"
PG_DEFAULTS = ROOT / "ansible/roles/shared_postgresql_provisioning/defaults/main.yml"
MONGO_DEFAULTS = ROOT / "ansible/roles/shared_mongodb_provisioning/defaults/main.yml"
PG_TASKS = ROOT / "ansible/roles/shared_postgresql_provisioning/tasks/main.yml"
MONGO_TASKS = ROOT / "ansible/roles/shared_mongodb_provisioning/tasks/main.yml"
EXEC_GUARD = ROOT / "ansible/plugins/action/database_provisioning_guarded_exec.py"
K8S_GUARD = ROOT / "ansible/plugins/action/database_provisioning_guarded_k8s.py"
RUNBOOK = ROOT / "runbooks/shared-database-provisioning.md"

EXPECTED_PG = {
    "cristexhub_dev": ("cristexhub_dev_owner", "shared-postgresql-cristexhub-dev"),
    "cristexhub_prod": ("cristexhub_prod_owner", "shared-postgresql-cristexhub-prod"),
    "reactive_resume_dev": (
        "reactive_resume_dev_owner",
        "shared-postgresql-reactive-resume-dev",
    ),
    "reactive_resume_prod": (
        "reactive_resume_prod_owner",
        "shared-postgresql-reactive-resume-prod",
    ),
    "keycloak": ("keycloak_owner", "shared-postgresql-keycloak"),
}
EXPECTED_MONGO = {
    "cristexhub_dev": ("cristexhub_dev_user", "shared-mongodb-cristexhub-dev"),
    "cristexhub_prod": ("cristexhub_prod_user", "shared-mongodb-cristexhub-prod"),
}


class SharedDatabaseProvisioningContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = yaml.safe_load(POLICY.read_text())
        cls.pg_defaults = yaml.safe_load(PG_DEFAULTS.read_text())
        cls.mongo_defaults = yaml.safe_load(MONGO_DEFAULTS.read_text())
        cls.pg_tasks = PG_TASKS.read_text()
        cls.mongo_tasks = MONGO_TASKS.read_text()
        cls.exec_guard = EXEC_GUARD.read_text()
        cls.k8s_guard = K8S_GUARD.read_text()
        cls.runbook = RUNBOOK.read_text()

    def test_exact_empty_reservation_map_and_inactive_promotion(self) -> None:
        pg = self.policy["engines"]["postgresql"]
        mongo = self.policy["engines"]["mongodb"]
        self.assertEqual(
            {
                database: (value["principal_name"], value["credential_secret"])
                for value in pg["consumers"].values()
                for database in [value["logical_database"]]
            },
            EXPECTED_PG,
        )
        self.assertEqual(
            {
                database: (value["principal_name"], value["credential_secret"])
                for value in mongo["consumers"].values()
                for database in [value["logical_database"]]
            },
            EXPECTED_MONGO,
        )
        self.assertTrue(all(v["bootstrap_state"] == "empty-reservation" for v in pg["consumers"].values()))
        self.assertTrue(all(v["bootstrap_state"] == "empty-reservation" for v in mongo["consumers"].values()))
        self.assertTrue(all(v["activation"] == "inactive" for v in pg["consumers"].values()))
        self.assertTrue(all(v["activation"] == "inactive" for v in mongo["consumers"].values()))
        provisioning = self.policy["provisioning"]
        self.assertEqual("cristexweb-infrastructure", provisioning["infisical_source"]["project_slug"])
        self.assertEqual("bootstrap", provisioning["infisical_source"]["environment_slug"])
        self.assertEqual(
            {"postgresql": "/shared-services/postgresql", "mongodb": "/shared-services/mongodb"},
            provisioning["infisical_source"]["paths"],
        )
        self.assertTrue(provisioning["require_exact_infisical_consumer_secrets"])
        self.assertFalse(provisioning["generate_consumer_credentials"])
        self.assertFalse(provisioning["implicit_password_rotation"])
        self.assertEqual("forbidden", provisioning["database_delete_path"])
        self.assertEqual("forbidden", provisioning["role_or_user_delete_path"])
        self.assertEqual("forbidden", provisioning["pvc_delete_path"])
        self.assertFalse(self.policy["promotion_gates"]["logical_provisioning_runtime_approved"])
        self.assertFalse(self.policy["promotion_gates"]["production_logical_scopes_active"])
        self.assertFalse(mongo["logical_provisioning"]["authoritative_data"])

    def test_defaults_repeat_exact_map_and_secret_contract(self) -> None:
        self.assertEqual(
            EXPECTED_PG,
            {
                item["database"]: (item["role"], item["secret"])
                for item in self.pg_defaults["shared_postgresql_provisioning_scopes"]
            },
        )
        self.assertEqual(
            EXPECTED_MONGO,
            {
                item["database"]: (item["user"], item["secret"])
                for item in self.mongo_defaults["shared_mongodb_provisioning_scopes"]
            },
        )
        for defaults in (self.pg_defaults, self.mongo_defaults):
            contract_key = (
                "shared_postgresql_provisioning_secret_contract"
                if defaults is self.pg_defaults
                else "shared_mongodb_provisioning_secret_contract"
            )
            self.assertEqual(
                {"password", "username"},
                set(defaults[contract_key]["keys"]),
            )
            self.assertEqual("infisical", defaults[contract_key]["labels"]["app.kubernetes.io/managed-by"])
            self.assertEqual("infisical-cloud", defaults[contract_key]["labels"]["cristex.io/value-owner"])

    def test_scripts_are_hash_bound_and_no_secret_argv_or_destructive_reset(self) -> None:
        scripts = sorted((ROOT / "ansible/files/database-provisioning").glob("*.sh"))
        self.assertEqual(4, len(scripts))
        all_scripts = "\n".join(path.read_text() for path in scripts)
        for path in scripts:
            result = subprocess.run(["/bin/bash", "-n", str(path)], check=False)
            self.assertEqual(0, result.returncode, str(path))
        for forbidden in (
            "--password",
            "postgresql://",
            "mongodb://",
            "PGPASSWORD",
            "ROLE_PASSWORD",
            "process.env.MONGO_ROOT_PASSWORD",
            "process.env.MONGO_SCOPE_PASSWORD",
            "DROP ",
            "DROP\n",
            "DROP DATABASE",
            "DROP USER",
            "DROP ROLE",
            "DROP OWNED",
            "REASSIGN OWNED",
            "ALTER SYSTEM",
        ):
            self.assertNotIn(forbidden, all_scripts)
        self.assertIn("CREATE DATABASE", all_scripts)
        self.assertIn("CREATE ROLE", all_scripts)
        self.assertNotIn("BEGIN; CREATE DATABASE", all_scripts)
        self.assertNotIn("BEGIN; CREATE ROLE", all_scripts)
        self.assertIn("ROLE_ONLY", all_scripts)
        self.assertIn("user_relation_count", all_scripts)
        self.assertIn("non_system_schema_count", all_scripts)
        self.assertIn("has_database_privilege", all_scripts)
        self.assertIn("has_schema_privilege", all_scripts)
        self.assertIn("readWrite", all_scripts)
        self.assertIn("readAnyDatabase", all_scripts)
        self.assertIn("connectionStatus", all_scripts)
        self.assertIn("PGPASSFILE", all_scripts)
        self.assertIn("readFileSync", all_scripts)
        self.assertIn("/run/database-credentials/", all_scripts)
        self.assertNotRegex(all_scripts, r"--(?:password|pass)\s+\$|--(?:password|pass)=")
        self.assertNotRegex(all_scripts, r"(?:password|client_secret|private_key)\s*:\s*[^$\s]")
        expected_hashes = {
            **self.pg_defaults["shared_postgresql_provisioning_script_hashes"],
            **self.mongo_defaults["shared_mongodb_provisioning_script_hashes"],
        }
        for name, digest in expected_hashes.items():
            self.assertEqual(digest, hashlib.sha256((ROOT / "ansible/files/database-provisioning" / name).read_bytes()).hexdigest())

    def test_helpers_are_temporary_tokenless_and_uid_bound(self) -> None:
        combined_tasks = self.pg_tasks + "\n" + self.mongo_tasks
        for text in (combined_tasks, self.k8s_guard, self.runbook):
            self.assertIn("UID", text)
            self.assertIn("Orphan", text)
            self.assertIn("database-logical-provisioning", text)
        self.assertIn("UID", self.exec_guard)
        self.assertIn("Orphan", self.exec_guard)
        self.assertIn("is not True", self.exec_guard)
        for tasks in (self.pg_tasks, self.mongo_tasks):
            self.assertIn("automountServiceAccountToken: false", tasks)
            self.assertIn("readOnlyRootFilesystem: true", tasks)
            self.assertIn("runAsUser: 999", tasks)
            self.assertIn("emptyDir:", tasks)
            self.assertIn("always:", tasks)
            self.assertIn("preconditions:", tasks)
            self.assertIn("identity before cleanup", tasks)
            self.assertIn("interruption-safe cleanup", tasks)
            self.assertIn("zero", tasks.lower())
            self.assertNotIn("kubernetes.core.k8s:\n", tasks)
            self.assertNotIn("ansible.builtin.command", tasks)
            self.assertNotIn("ansible.builtin.shell", tasks)
        self.assertIn("state: absent", self.pg_tasks)
        self.assertIn("state: absent", self.mongo_tasks)
        for tasks in (self.pg_tasks, self.mongo_tasks):
            self.assertIn("- Egress", tasks)
            self.assertIn("kubernetes.io/metadata.name: kube-system", tasks)
            self.assertIn("k8s-app: kube-dns", tasks)
        self.assertIn("expected_egress", self.k8s_guard)
        self.assertIn("Do not delete a database", self.runbook)
        self.assertIn("shared_postgresql_provisioning_scopes ==", self.pg_tasks)
        self.assertIn("shared_mongodb_provisioning_scopes ==", self.mongo_tasks)

    def test_guards_refuse_task_selection_and_foreign_objects(self) -> None:
        for text in (self.exec_guard, self.k8s_guard):
            for required in ("TASK_SELECTION_GUARD", "ENTRYPOINT_GUARD", "MUTATION_ARGUMENT_GUARD", "SECRET_ARGV_GUARD", "kubernetes.core.k8s"):
                self.assertIn(required, text)
        self.assertIn("state == \"absent\"", self.k8s_guard)
        self.assertIn("delete_options", self.k8s_guard)
        self.assertIn("preconditions", self.k8s_guard)
        self.assertIn('container.get("env") not in (None, [])', self.k8s_guard)
        self.assertIn("expected_secret_volumes", self.k8s_guard)
        self.assertIn("persistentVolumeClaim", self.k8s_guard)
        self.assertNotIn("secretKeyRef", self.pg_tasks + self.mongo_tasks)
        for wrapper in (ROOT / "ansible/bin/provision-shared-postgresql", ROOT / "ansible/bin/provision-shared-mongodb"):
            text = wrapper.read_text()
            self.assertIn("check|apply", text)
            self.assertIn("/usr/bin/env -i", text)
            self.assertIn("--diff", text)
            self.assertIn("--limit crtxweb", text)
            self.assertIn("CRISTEXWEB_SHARED_DATABASE_PROVISIONING_ATTESTATION_FILE", text)
            self.assertNotIn("--tags", text)
            self.assertNotIn("--skip-tags", text)
            self.assertNotIn("--start-at-task", text)
            self.assertNotIn("--ask-become-pass", text)

    def test_runbook_and_tasks_keep_promotion_blocked(self) -> None:
        normalized = " ".join(self.runbook.split())
        for required in (
            "five PostgreSQL and two MongoDB",
            "empty bootstrap reservations",
            "precreated Infisical-owned",
            "PROD remains inactive",
            "standalone and non-authoritative",
            "backup, isolated restore, RPO/RTO",
            "database/user rollback operation",
        ):
            self.assertIn(required, normalized)
        for tasks in (self.pg_tasks, self.mongo_tasks):
            self.assertIn("credential", tasks)
            self.assertIn("no_delete_path", tasks)
            self.assertIn("precreated", tasks)


if __name__ == "__main__":
    unittest.main()
