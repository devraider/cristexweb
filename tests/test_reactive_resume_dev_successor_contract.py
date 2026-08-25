from __future__ import annotations

import ast
import hashlib
import importlib.util
import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/reactive-resume-dev-successor"
CLOSURE = COMPONENT / "SOURCE-CLOSURE.sha256"
SOURCE = COMPONENT / "source"
POLICY = ROOT / "ansible/files/policies/reactive-resume-dev-postgresql-successor.yml"
DEFAULTS = ROOT / "ansible/roles/reactive_resume_dev_successor/defaults/main.yml"
TASKS = ROOT / "ansible/roles/reactive_resume_dev_successor/tasks/main.yml"
PLAYBOOK = ROOT / "ansible/playbooks/check_reactive_resume_dev_successor.yml"
WRAPPER = ROOT / "ansible/bin/check-reactive-resume-dev-successor"
CHECKER = ROOT / "ansible/files/database-provisioning/reactive-resume-dev-successor-check.sh"
GUARD = ROOT / "ansible/plugins/action/reactive_resume_dev_successor_guarded.py"
METADATA = ROOT / "ansible/library/reactive_resume_dev_secret_metadata.py"

RUNTIME_KEYS = {
    "APP_URL", "AUTH_SECRET", "DATABASE_URL", "OAUTH_CLIENT_ID",
    "OAUTH_CLIENT_SECRET", "OAUTH_DISCOVERY_URL", "OAUTH_ISSUER",
    "OAUTH_PROVIDER_NAME", "OAUTH_SCOPES", "S3_ACCESS_KEY_ID", "S3_BUCKET",
    "S3_ENDPOINT", "S3_FORCE_PATH_STYLE", "S3_REGION", "S3_SECRET_ACCESS_KEY",
}
MIGRATION_KEYS = {"DATABASE_URL", "MIGRATION_DATABASE_URL"}


def docs(path: Path) -> list[dict]:
    return [item for item in yaml.safe_load_all(path.read_text()) if item]


def canonical_digest(path: Path) -> str:
    source = path.read_text()
    for symbol in ("_ACTION_CANONICAL_HASH", "_CLOSURE_MANIFEST_HASH"):
        source, count = re.subn(
            rf'(?m)^({re.escape(symbol)}\s*=\s*")[0-9a-f]{{64}}("\s*)$',
            rf'\g<1>{"0" * 64}\g<2>',
            source,
        )
        if count != 1:
            raise AssertionError(f"canonical pin {symbol} count={count}")
    return hashlib.sha256(source.encode()).hexdigest()


def canonical_wrapper_digest(path: Path) -> str:
    source = path.read_text()
    source, count = re.subn(
        r"(?m)^closure_manifest_expected='[0-9a-f]{64}'$",
        "closure_manifest_expected='" + ("0" * 64) + "'",
        source,
    )
    if count != 1:
        raise AssertionError(f"canonical wrapper pin count={count}")
    return hashlib.sha256(source.encode()).hexdigest()


class ReactiveResumeDevSuccessorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = yaml.safe_load(POLICY.read_text())
        cls.defaults = yaml.safe_load(DEFAULTS.read_text())
        cls.tasks = TASKS.read_text()
        cls.checker = CHECKER.read_text()
        cls.wrapper = WRAPPER.read_text()
        cls.guard = GUARD.read_text()
        cls.source_docs = [doc for path in sorted(SOURCE.glob("*.yaml")) for doc in docs(path)]

    def test_scope_is_read_only_and_provenance_pending(self) -> None:
        self.assertEqual("cristex-reactive-resume-dev-successor-v2", self.policy["policy_schema"])
        self.assertEqual("source-only-read-only-catalog-check-provenance-pending", self.policy["policy_status"])
        self.assertFalse(self.policy["runtime_mutation_allowed"])
        self.assertTrue(self.policy["source"]["check_mode_only"])
        self.assertTrue(self.policy["source"]["no_apply_path"])
        self.assertTrue(self.policy["source"]["no_cnpg_database_or_role_source"])
        self.assertTrue(self.policy["source"]["no_competing_ca_static_secret_source"])
        self.assertEqual("observed-sql-created-no-cnpg-crs", self.policy["scope"]["database_provenance"])
        self.assertEqual("absent-until-exact-provenance", self.policy["acceptance_gates"]["successor_cnpg_crs"])

    def test_only_safe_value_free_source_objects_are_present(self) -> None:
        self.assertEqual(
            {"admission-rbac.yaml", "migration-static-secret.yaml", "runtime-static-secret.yaml"},
            {path.name for path in SOURCE.glob("*.yaml")},
        )
        self.assertFalse((SOURCE / "successor-database.yaml").exists())
        self.assertFalse((SOURCE / "postgresql-ca-static-secret.yaml").exists())
        self.assertEqual(2, sum(item["kind"] == "InfisicalStaticSecret" for item in self.source_docs))
        self.assertFalse(any(item.get("kind") in {"Database", "DatabaseRole"} for item in self.source_docs))
        self.assertNotIn("reactive-resume-dev-postgresql-ca", "\n".join(path.read_text() for path in SOURCE.glob("*.yaml")))

    def test_static_secret_contracts_have_exact_paths_and_keys(self) -> None:
        runtime = next(item for item in self.source_docs if item["metadata"]["name"] == "reactive-resume-dev-runtime")
        migration = next(item for item in self.source_docs if item["metadata"]["name"] == "reactive-resume-dev-migration")
        self.assertEqual("/reactive-resume/dev/runtime", runtime["spec"]["sources"][0]["secretPath"])
        self.assertEqual("/reactive-resume/dev/migration", migration["spec"]["sources"][0]["secretPath"])
        self.assertEqual(RUNTIME_KEYS, set(runtime["spec"]["targets"][0]["template"]["data"]))
        self.assertEqual(MIGRATION_KEYS, set(migration["spec"]["targets"][0]["template"]["data"]))
        for item in (runtime, migration):
            target = item["spec"]["targets"][0]
            self.assertEqual("cristexhub-dev", target["namespace"])
            self.assertEqual("Secret", target["kind"])
            self.assertEqual("Opaque", target["secretType"])
            self.assertEqual("Orphan", target["creationPolicy"])

    def test_ca_ownership_is_external_existing_lane(self) -> None:
        ca = yaml.safe_load((ROOT / "ansible/files/components/infisical-reactive-resume-dev-ca/source/reactive-resume-dev-ca-static-secret.yaml").read_text())
        self.assertEqual("reactive-resume-dev-ca", ca["metadata"]["name"])
        self.assertEqual("/reactive-resume/dev/object-storage-tls", ca["spec"]["sources"][0]["secretPath"])
        self.assertIn("reactive-resume-dev-postgresql-ca", [item["name"] for item in ca["spec"]["targets"]])
        self.assertNotIn("postgresql-ca-static-secret.yaml", "\n".join(self.defaults["reactive_resume_dev_successor_source_paths"]))
        self.assertIn("reactive-resume-dev-ca", self.tasks)

    def test_catalog_checker_uses_local_socket_and_full_acl_projection(self) -> None:
        for required in (
            "-U postgres", "-d \"$database_name\"", "PGHOST=\"$pg_socket\"", "env -i", "pg_roles", "rolinherit=false",
            "pg_auth_members", "pg_database", "has_database_privilege",
            "has_schema_privilege", "has_table_privilege", "has_sequence_privilege",
            "has_function_privilege", "pg_default_acl", "defaclobjtype",
            "foreign_database_connect", "runtime_create_database",
            "migration_create_role", "crs_not_required=true",
        ):
            self.assertIn(required, self.checker, required)
        self.assertIn("(g.rolname='$migration_role' AND a.privilege_type <> 'CONNECT')", self.checker)
        self.assertNotIn("(g.rolname='$migration_role' AND a.privilege_type NOT IN ('CONNECT','CREATE','TEMPORARY'))", self.checker)
        for forbidden in ("/etc/postgresql/admin", "/tls/ca.crt", "PGPASSFILE", "PGPASSWORD", "PGSERVICE", "CREATE ROLE", "ALTER ROLE", "GRANT ", "REVOKE ", "DROP "):
            self.assertNotIn(forbidden, self.checker, forbidden)
        self.assertEqual(0, subprocess.run(["/bin/sh", "-n", str(CHECKER)], check=False).returncode)

    def test_sequence_acl_policy_and_checker_match_runtime_boundary(self) -> None:
        self.assertEqual(["USAGE", "SELECT"], self.policy["acl"]["runtime_sequences"])
        self.assertEqual(["runtime=rU"], self.policy["acl"]["default_privileges"]["sequences"])
        self.assertNotIn("runtime=rwU", yaml.safe_dump(self.policy))
        self.assertIn('expected_default_sequence_acl="{${runtime_role}=rU/${migration_role}}"', self.checker)
        self.assertNotIn("runtime_role}=rwU", self.checker)
        self.assertIn("has_sequence_privilege('$runtime_role',c.oid,'USAGE')", self.checker)
        self.assertIn("has_sequence_privilege('$runtime_role',c.oid,'SELECT')", self.checker)
        self.assertIn("has_sequence_privilege('$runtime_role',c.oid,'UPDATE')", self.checker)
        self.assertIn("x.privilege_type NOT IN ('USAGE','SELECT')", self.checker)
        self.assertIn("x.privilege_type NOT IN ('USAGE','SELECT','UPDATE')", self.checker)

    def test_admission_is_namespace_scoped_and_exactly_validated(self) -> None:
        policy = next(item for item in self.source_docs if item["kind"] == "ValidatingAdmissionPolicy")
        self.assertEqual(
            [{"name": "exact-namespace", "expression": "request.namespace == 'cristexhub-dev'"}],
            policy["spec"]["matchConditions"],
        )
        match_constraints = policy["spec"]["matchConstraints"]
        effective_match_constraints = {
            **match_constraints,
            "namespaceSelector": match_constraints.get("namespaceSelector", {}),
            "objectSelector": match_constraints.get("objectSelector", {}),
        }
        self.assertEqual(
            ["matchPolicy", "namespaceSelector", "objectSelector", "resourceRules"],
            sorted(effective_match_constraints),
        )
        self.assertEqual({}, effective_match_constraints["namespaceSelector"])
        self.assertEqual({}, effective_match_constraints["objectSelector"])
        self.assertEqual(
            [{"apiGroups": [""], "apiVersions": ["v1"], "operations": ["CREATE", "UPDATE"],
              "resources": ["secrets"], "scope": "Namespaced"}],
            effective_match_constraints["resourceRules"],
        )
        self.assertNotIn("namespaceSelector", match_constraints)
        self.assertNotIn("objectSelector", match_constraints)
        expression = policy["spec"]["validations"][0]["expression"]
        for required in (
            "object.metadata.name in ['reactive-resume-dev-runtime', 'reactive-resume-dev-migration']",
            "object.metadata.namespace == 'cristexhub-dev'",
            "object.metadata.labels.size() == 3",
            "object.metadata.ownerReferences",
            "object.metadata.finalizers",
            "object.stringData",
            "object.data.size() == 15",
            "object.data.size() == 2",
        ):
            self.assertIn(required, expression, required)
        self.assertEqual(
            self.defaults["reactive_resume_dev_successor_admission_expression_sha256"],
            hashlib.sha256(expression.encode()).hexdigest(),
        )
        self.assertIn("object.metadata.name in", self.tasks)
        self.assertIn("targets[0].namespace == reactive_resume_dev_successor_application_namespace", self.tasks)
        self.assertIn("metadata.ownerReferences", self.tasks)
        self.assertIn("metadata.finalizers", self.tasks)
        self.assertIn("matchConditions[0].expression", self.tasks)
        self.assertIn("admission_expression_sha256", self.tasks)
        for required in (
            "Normalize Kubernetes-defaulted admission match constraints",
            "reactive_resume_dev_successor_effective_match_constraints",
            "namespaceSelector",
            "objectSelector",
            "['matchPolicy', 'namespaceSelector', 'objectSelector', 'resourceRules']",
            "['apiGroups', 'apiVersions', 'operations', 'resources', 'scope']",
            "resourceRules[0] ==",
        ):
            self.assertIn(required, self.tasks)
        self.assertNotIn("spec.matchConstraints | length) == 2", self.tasks)
        self.assertIn("status.observedGeneration", self.tasks)
        self.assertIn("status.typeChecking", self.tasks)
        self.assertIn("expressionWarnings", self.tasks)
        self.assertIn("expressionErrors", self.tasks)

    def test_exact_static_secret_auth_and_writer_rbac_contracts(self) -> None:
        for item in self.source_docs:
            if item["kind"] == "InfisicalStaticSecret":
                self.assertEqual(
                    {"name": "cristexhub-dev-infisical-auth", "namespace": "cristexhub-dev"},
                    item["spec"]["infisicalAuthRef"],
                )
                self.assertEqual({"refreshInterval": "1h", "instantUpdates": False}, item["spec"]["syncOptions"])
                target = item["spec"]["targets"][0]
                self.assertEqual({"annotations": {}, "labels": {
                    "app.kubernetes.io/managed-by": "infisical",
                    "app.kubernetes.io/part-of": "reactive-resume",
                    "cristex.io/value-owner": "infisical-cloud",
                }}, target["metadata"])
                self.assertEqual("v1", target["template"]["engineVersion"])
        role = next(item for item in self.source_docs if item["kind"] == "Role")
        binding = next(item for item in self.source_docs if item["kind"] == "RoleBinding")
        self.assertEqual("infisical-reactive-resume-dev-successor-secret-writer", role["metadata"]["name"])
        self.assertEqual("infisical-reactive-resume-dev-successor-secret-writer", binding["roleRef"]["name"])
        self.assertEqual("infisical-operator-controller", binding["subjects"][0]["name"])
        self.assertEqual("shared-services", binding["subjects"][0]["namespace"])
        admission = [item for item in self.source_docs if item["kind"] == "ValidatingAdmissionPolicy"]
        self.assertEqual(1, len(admission))
        self.assertEqual("Fail", admission[0]["spec"]["failurePolicy"])
        self.assertIn("infisical-operator-controller", admission[0]["spec"]["validations"][0]["expression"])
        self.assertIn("'verbs': ['create']", self.tasks)
        for required in ("status.observedGeneration", "status.typeChecking", "expressionWarnings", "expressionErrors"):
            self.assertIn(required, self.tasks)
        self.assertLess(
            self.tasks.index("status.observedGeneration"),
            self.tasks.index("Query the exact dedicated successor Secret writer Role"),
        )

    def test_role_and_wrapper_are_check_only(self) -> None:
        self.assertIn("ansible_check_mode", self.tasks)
        self.assertIn("kubernetes.core.k8s_info", self.tasks)
        self.assertIn("kubernetes.core.k8s_exec", self.guard)
        self.assertIn("no competing successor CNPG CR ownership", self.tasks)
        self.assertNotIn("state: present", self.tasks)
        self.assertNotIn("kubernetes.core.k8s:", self.tasks)
        self.assertNotIn("ansible.builtin.command:", self.tasks)
        self.assertEqual(0o755, stat.S_IMODE(WRAPPER.stat().st_mode))
        self.assertIn("usage: ansible/bin/check-reactive-resume-dev-successor check", self.wrapper)
        self.assertIn("--check --diff --limit crtxweb", self.wrapper)
        self.assertNotIn("apply'", self.wrapper)
        self.assertEqual(0, subprocess.run(["/bin/sh", "-n", str(WRAPPER)], check=False).returncode)

    def test_metadata_module_uses_pinned_debian_interpreter(self) -> None:
        text = METADATA.read_text()
        self.assertEqual("#!/usr/bin/python3", text.splitlines()[0])
        self.assertNotIn("/usr/bin/env python3", text.splitlines()[0])

    def test_metadata_module_cannot_return_secret_payload(self) -> None:
        text = METADATA.read_text()
        self.assertIn("PartialObjectMetadata", text)
        self.assertIn('"Accept"', text)
        self.assertNotIn("read_namespaced_secret", text)
        self.assertNotIn("binaryData", text)
        self.assertNotIn(".data", text)

    def test_wrapper_verifies_complete_closure_before_controller(self) -> None:
        controller = self.wrapper.index('controller="$repository_root/.venv/bin/ansible-playbook"')
        required = (
            "checker_source",
            "manifest_source",
            "task_source",
            "defaults_source",
            "playbook_source",
            "policy_source",
            "config_source",
            "library_source",
            "action_source",
            "verify_source ansible/files/database-provisioning/reactive-resume-dev-successor-check.sh",
            "verify_source ansible/files/components/reactive-resume-dev-successor/MANIFESTS.sha256",
            "verify_source ansible/roles/reactive_resume_dev_successor/tasks/main.yml",
            "verify_source ansible/roles/reactive_resume_dev_successor/defaults/main.yml",
            "verify_source ansible/playbooks/check_reactive_resume_dev_successor.yml",
            "verify_source ansible/files/policies/reactive-resume-dev-postgresql-successor.yml",
            "verify_source ansible/ansible.cfg",
            "verify_source ansible/library/reactive_resume_dev_secret_metadata.py",
            "canonical_action_file",
            "canonical_wrapper_file",
        )
        for value in required:
            self.assertIn(value, self.wrapper, value)
            self.assertLess(self.wrapper.index(value), controller, value)
        self.assertLess(controller, self.wrapper.index("/usr/bin/env -i"))

    def test_direct_role_invocation_requires_wrapper_boundary(self) -> None:
        self.assertLess(
            self.tasks.index("Reject externally supplied successor internals"),
            self.tasks.index("Require the source-only DEV successor wrapper contract"),
        )
        self.assertIn("exact check-only wrapper", self.tasks)
        self.assertIn("source-only, read-only", (ROOT / "runbooks/reactive-resume-dev-successor.md").read_text())
        self.assertIn("malicious process already running as the trusted controller UID", (ROOT / "runbooks/reactive-resume-dev-successor.md").read_text())

    def test_manifest_and_checker_hash_are_current(self) -> None:
        ledger = {}
        for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines():
            digest, path = line.split("  ", 1)
            ledger[path] = digest
        self.assertEqual(
            {str(path.relative_to(COMPONENT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(SOURCE.glob("*.yaml"))},
            ledger,
        )
        self.assertIn(hashlib.sha256(CHECKER.read_bytes()).hexdigest(), DEFAULTS.read_text())
        self.assertIn("MANIFESTS.sha256", DEFAULTS.read_text())
        self.assertIn("source_manifest_sha256", DEFAULTS.read_text())
        self.assertIn("reactive_resume_dev_successor", PLAYBOOK.read_text())
        closure = {
            path: digest
            for digest, path in (line.split("  ", 1) for line in CLOSURE.read_text().splitlines())
        }
        self.assertEqual(
            {
                "ansible/files/database-provisioning/reactive-resume-dev-successor-check.sh": hashlib.sha256(CHECKER.read_bytes()).hexdigest(),
                "ansible/files/components/reactive-resume-dev-successor/MANIFESTS.sha256": hashlib.sha256((COMPONENT / "MANIFESTS.sha256").read_bytes()).hexdigest(),
                "ansible/roles/reactive_resume_dev_successor/tasks/main.yml": hashlib.sha256(TASKS.read_bytes()).hexdigest(),
                "ansible/roles/reactive_resume_dev_successor/defaults/main.yml": hashlib.sha256(DEFAULTS.read_bytes()).hexdigest(),
                "ansible/playbooks/check_reactive_resume_dev_successor.yml": hashlib.sha256(PLAYBOOK.read_bytes()).hexdigest(),
                "ansible/files/policies/reactive-resume-dev-postgresql-successor.yml": hashlib.sha256(POLICY.read_bytes()).hexdigest(),
                "ansible/ansible.cfg": hashlib.sha256((ROOT / "ansible/ansible.cfg").read_bytes()).hexdigest(),
                "ansible/library/reactive_resume_dev_secret_metadata.py": hashlib.sha256(METADATA.read_bytes()).hexdigest(),
                "ansible/bin/check-reactive-resume-dev-successor": canonical_wrapper_digest(WRAPPER),
                "ansible/plugins/action/reactive_resume_dev_successor_guarded.py": canonical_digest(GUARD),
            },
            closure,
        )
        for required in (
            "SOURCE-CLOSURE.sha256",
            "closure_manifest_expected",
            "canonical_wrapper_file",
            "canonical_action_file",
            "ansible/bin/check-reactive-resume-dev-successor",
            "ansible/ansible.cfg",
            "ansible/library/reactive_resume_dev_secret_metadata.py",
            "ansible/files/database-provisioning/reactive-resume-dev-successor-check.sh",
            "ansible/files/components/reactive-resume-dev-successor/MANIFESTS.sha256",
            "ansible/roles/reactive_resume_dev_successor/tasks/main.yml",
            "ansible/roles/reactive_resume_dev_successor/defaults/main.yml",
            "ansible/playbooks/check_reactive_resume_dev_successor.yml",
            "ansible/files/policies/reactive-resume-dev-postgresql-successor.yml",
        ):
            self.assertIn(required, self.wrapper)
        self.assertIn("_POLICY_HASH", self.guard)
        self.assertEqual(0, subprocess.run(["python3", "-m", "py_compile", str(METADATA), str(GUARD)], check=False).returncode)

    def test_wrapper_alteration_with_updated_pin_changes_bound_action_digest(self) -> None:
        altered_wrapper = WRAPPER.read_text() + "\n# simulated wrapper logic alteration\n"
        with tempfile.TemporaryDirectory() as directory:
            wrapper_path = Path(directory) / WRAPPER.name
            wrapper_path.write_text(altered_wrapper)
            altered_wrapper_digest = canonical_wrapper_digest(wrapper_path)
            self.assertNotEqual(altered_wrapper_digest, canonical_wrapper_digest(WRAPPER))
            altered_action = GUARD.read_text().replace(
                re.search(r'(?m)^_WRAPPER_CANONICAL_HASH = "[0-9a-f]{64}"$', GUARD.read_text()).group(0),
                f'_WRAPPER_CANONICAL_HASH = "{altered_wrapper_digest}"',
                1,
            )
            action_path = Path(directory) / GUARD.name
            action_path.write_text(altered_action)
            closure = {
                path: digest
                for digest, path in (line.split("  ", 1) for line in CLOSURE.read_text().splitlines())
            }
            self.assertNotEqual(canonical_digest(action_path), closure["ansible/plugins/action/reactive_resume_dev_successor_guarded.py"])

    def test_action_guard_hash_constants_match_every_current_source(self) -> None:
        tree = ast.parse(self.guard)
        constants = {}
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                "_SCRIPT_HASH", "_MANIFEST_HASH", "_TASK_HASH", "_DEFAULTS_HASH",
                "_PLAYBOOK_HASH", "_POLICY_HASH", "_MANIFEST_ENTRIES",
                "_ACTION_CANONICAL_HASH", "_WRAPPER_CANONICAL_HASH", "_CLOSURE_MANIFEST_HASH", "_CLOSURE_ENTRIES",
            }:
                constants[target.id] = ast.literal_eval(node.value)
        paths = {
            "_SCRIPT_HASH": CHECKER,
            "_MANIFEST_HASH": COMPONENT / "MANIFESTS.sha256",
            "_TASK_HASH": TASKS,
            "_DEFAULTS_HASH": DEFAULTS,
            "_PLAYBOOK_HASH": PLAYBOOK,
            "_POLICY_HASH": POLICY,
            "_CLOSURE_MANIFEST_HASH": CLOSURE,
        }
        for symbol, path in paths.items():
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                constants[symbol],
                symbol,
            )
        self.assertEqual(
            {
                str(path.relative_to(COMPONENT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(SOURCE.glob("*.yaml"))
            },
            constants["_MANIFEST_ENTRIES"],
        )
        self.assertEqual(canonical_digest(GUARD), constants["_ACTION_CANONICAL_HASH"])
        self.assertEqual(canonical_wrapper_digest(WRAPPER), constants["_WRAPPER_CANONICAL_HASH"])
        self.assertEqual(
            {
                "ansible/files/database-provisioning/reactive-resume-dev-successor-check.sh": hashlib.sha256(CHECKER.read_bytes()).hexdigest(),
                "ansible/files/components/reactive-resume-dev-successor/MANIFESTS.sha256": hashlib.sha256((COMPONENT / "MANIFESTS.sha256").read_bytes()).hexdigest(),
                "ansible/roles/reactive_resume_dev_successor/tasks/main.yml": hashlib.sha256(TASKS.read_bytes()).hexdigest(),
                "ansible/roles/reactive_resume_dev_successor/defaults/main.yml": hashlib.sha256(DEFAULTS.read_bytes()).hexdigest(),
                "ansible/playbooks/check_reactive_resume_dev_successor.yml": hashlib.sha256(PLAYBOOK.read_bytes()).hexdigest(),
                "ansible/files/policies/reactive-resume-dev-postgresql-successor.yml": hashlib.sha256(POLICY.read_bytes()).hexdigest(),
                "ansible/ansible.cfg": hashlib.sha256((ROOT / "ansible/ansible.cfg").read_bytes()).hexdigest(),
                "ansible/library/reactive_resume_dev_secret_metadata.py": hashlib.sha256(METADATA.read_bytes()).hexdigest(),
                "ansible/bin/check-reactive-resume-dev-successor": canonical_wrapper_digest(WRAPPER),
            },
            constants["_CLOSURE_ENTRIES"],
        )

    def test_selection_guard_rejects_empty_step_state(self) -> None:
        spec = importlib.util.spec_from_file_location("reactive_resume_dev_successor_selection_test", GUARD)
        self.assertIsNotNone(spec and spec.loader)
        guarded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guarded)
        cliargs = {
            "tags": [],
            "start_at_task": None,
            "step": "",
            "skip_tags": [],
            "subset": "crtxweb",
            "diff": True,
            "check": True,
            "inventory": ["/synthetic/.ansible/inventory.local.yml"],
        }
        with patch.object(guarded.context, "CLIARGS", guarded.context.CLIARGS.__class__(cliargs)):
            self.assertFalse(guarded._selected())

    def test_action_guard_reaches_read_only_exec_boundary_with_synthetic_attestation(self) -> None:
        spec = importlib.util.spec_from_file_location("reactive_resume_dev_successor_guarded_test", GUARD)
        self.assertIsNotNone(spec and spec.loader)
        guarded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guarded)

        token = "a" * 64
        pod_name = "shared-postgresql-primary"
        command = ["/bin/sh", "-ec", CHECKER.read_text()]
        args = {
            "namespace": "shared-services",
            "pod": pod_name,
            "container": "postgres",
            "command": command,
            "kubeconfig": "/etc/rancher/k3s/k3s.yaml",
            "script_name": CHECKER.name,
            "script_sha256": hashlib.sha256(CHECKER.read_bytes()).hexdigest(),
        }
        binding = {
            "attestation_sha256": hashlib.sha256(token.encode()).hexdigest(),
            "environment": "dev",
            "database": "reactive_resume_dev_successor",
            "runtime_role": "reactive_resume_dev_runtime",
            "migration_role": "reactive_resume_dev_migrator",
            "namespace": "shared-services",
            "pod_name": pod_name,
            "metadata_only": True,
            "no_apply_path": True,
        }

        class SyntheticTask:
            def __init__(self, task_args):
                self.args = task_args

            def get_path(self):
                return str(guarded._TASK_SOURCE)

        action = object.__new__(guarded.ActionModule)
        action._task = SyntheticTask(args)
        with tempfile.TemporaryDirectory() as directory:
            attestation = Path(directory) / "attestation"
            raw_wrapper_hash = hashlib.sha256(WRAPPER.read_bytes()).hexdigest()
            attestation.write_text(f"{token}:entrypoint:{os.getpid()}:{raw_wrapper_hash}\n")
            attestation.chmod(0o600)
            cliargs = {
                "tags": [],
                "start_at_task": None,
                "step": None,
                "skip_tags": [],
                "subset": "crtxweb",
                "diff": True,
                "check": True,
                "inventory": ["/synthetic/.ansible/inventory.local.yml"],
            }
            environment = {
                "CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_ENTRYPOINT": "v1",
                "CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_TOKEN": token,
                "CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_ATTESTATION_FILE": str(attestation),
                "CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_WRAPPER_PID": str(os.getpid()),
                "CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_WRAPPER_PATH": str(guarded._WRAPPER_SOURCE),
                "CRISTEXWEB_REACTIVE_RESUME_DEV_SUCCESSOR_WRAPPER_SHA256": raw_wrapper_hash,
            }
            with patch.object(guarded.context, "CLIARGS", guarded.context.CLIARGS.__class__(cliargs)), patch.dict(os.environ, environment, clear=False), patch.object(guarded.ActionModule.__mro__[1], "run", return_value={}), patch.object(guarded.ActionModule, "_execute_module", return_value={"rc": 0}) as execute:
                result = action.run(task_vars={
                    "reactive_resume_dev_successor_approved": True,
                    "reactive_resume_dev_successor_internal_binding": binding,
                })
        self.assertFalse(result["failed"], result)
        self.assertFalse(result["changed"])
        execute.assert_called_once()
        self.assertEqual("kubernetes.core.k8s_exec", execute.call_args.kwargs["module_name"])


if __name__ == "__main__":
    unittest.main()
