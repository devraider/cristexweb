from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/infisical-database-secrets"
DEFAULTS = ROOT / "ansible/roles/infisical_database_secrets_bootstrap/defaults/main.yml"
TASKS = ROOT / "ansible/roles/infisical_database_secrets_bootstrap/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/infisical_database_secrets_guarded_k8s.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-infisical-database-secrets"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_infisical_database_secrets.yml"
ACTION_ONLY = ROOT / "tests/reject_infisical_database_secrets_action_only.yml"
INTERNAL_FIXTURE = ROOT / "tests/reject_infisical_database_secrets_internal_injection.yml"
TASK_SELECTION = ROOT / "tests/reject_infisical_database_secrets_task_selection.sh"
LABELS = {
    "app.kubernetes.io/part-of": "cristex-platform",
    "app.kubernetes.io/managed-by": "ansible",
    "cristex.io/component": "infisical-database-secrets",
}
TARGET_LABELS = {
    "app.kubernetes.io/managed-by": "infisical",
    "app.kubernetes.io/part-of": "shared-databases",
    "cristex.io/value-owner": "infisical-cloud",
}
CONTRACT_PLUGIN = ROOT / "ansible/plugins/action/stateful_database_secret_contract.py"
CONTRACT_SPEC = importlib.util.spec_from_file_location(
    "database_secret_contract_for_seam", CONTRACT_PLUGIN
)
assert CONTRACT_SPEC and CONTRACT_SPEC.loader
CONTRACT_MODULE = importlib.util.module_from_spec(CONTRACT_SPEC)
sys.modules[CONTRACT_SPEC.name] = CONTRACT_MODULE
CONTRACT_SPEC.loader.exec_module(CONTRACT_MODULE)
TARGETS = {
    name: {"type": secret_type, "keys": keys}
    for engine_contract in CONTRACT_MODULE._EXPECTED_SECRET_CONTRACTS.values()
    for name, (secret_type, keys) in engine_contract.items()
}
TARGETS.update(
    {
        name: {"type": "Opaque", "keys": {"username", "password"}}
        for name in (
            "shared-postgresql-cristexhub-dev",
            "shared-postgresql-cristexhub-prod",
            "shared-postgresql-reactive-resume-dev",
            "shared-postgresql-reactive-resume-prod",
            "shared-postgresql-keycloak",
            "shared-mongodb-cristexhub-dev",
            "shared-mongodb-cristexhub-prod",
        )
    }
)
TEMPLATES = {
    "shared-postgresql-admin": {
        "username": "{{ .POSTGRESQL_ADMIN_USERNAME.Value }}",
        "password": "{{ .POSTGRESQL_ADMIN_PASSWORD.Value }}",
    },
    "shared-postgresql-tls": {
        "ca.crt": "{{ .POSTGRESQL_TLS_CA_CRT.Value }}",
        "tls.crt": "{{ .POSTGRESQL_TLS_CRT.Value }}",
        "tls.key": "{{ .POSTGRESQL_TLS_KEY.Value }}",
    },
    "shared-mongodb-auth": {
        "username": "{{ .MONGODB_ADMIN_USERNAME.Value }}",
        "password": "{{ .MONGODB_ADMIN_PASSWORD.Value }}",
    },
    "shared-mongodb-tls": {
        "ca.crt": "{{ .MONGODB_TLS_CA_CRT.Value }}",
        "tls.pem": "{{ .MONGODB_TLS_PEM.Value }}",
    },
    "shared-postgresql-cristexhub-dev": {
        "username": "{{ .POSTGRESQL_CRISTEXHUB_DEV_USERNAME.Value }}",
        "password": "{{ .POSTGRESQL_CRISTEXHUB_DEV_PASSWORD.Value }}",
    },
    "shared-postgresql-cristexhub-prod": {
        "username": "{{ .POSTGRESQL_CRISTEXHUB_PROD_USERNAME.Value }}",
        "password": "{{ .POSTGRESQL_CRISTEXHUB_PROD_PASSWORD.Value }}",
    },
    "shared-postgresql-reactive-resume-dev": {
        "username": "{{ .POSTGRESQL_REACTIVE_RESUME_DEV_USERNAME.Value }}",
        "password": "{{ .POSTGRESQL_REACTIVE_RESUME_DEV_PASSWORD.Value }}",
    },
    "shared-postgresql-reactive-resume-prod": {
        "username": "{{ .POSTGRESQL_REACTIVE_RESUME_PROD_USERNAME.Value }}",
        "password": "{{ .POSTGRESQL_REACTIVE_RESUME_PROD_PASSWORD.Value }}",
    },
    "shared-postgresql-keycloak": {
        "username": "{{ .POSTGRESQL_KEYCLOAK_USERNAME.Value }}",
        "password": "{{ .POSTGRESQL_KEYCLOAK_PASSWORD.Value }}",
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


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class InfisicalDatabaseSecretSeamContractTests(unittest.TestCase):
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
        cls.tasks = yaml.safe_load(TASKS.read_text())

    def test_exact_value_free_15_object_closure_and_hashes(self) -> None:
        self.assertEqual(15, len(self.paths))
        self.assertEqual(15, len(self.by_identity))
        self.assertFalse(any(obj["kind"] in {"Secret", "ConfigMap"} for obj in self.objects))
        for obj in self.objects:
            self.assertEqual(LABELS, obj["metadata"]["labels"])

        ledger = {}
        for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines():
            digest, relative = line.split("  ", 1)
            ledger[relative] = digest
        self.assertEqual({str(path.relative_to(COMPONENT)) for path in self.paths}, set(ledger))
        for path in self.paths:
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                ledger[str(path.relative_to(COMPONENT))],
            )
        defaults = yaml.safe_load(DEFAULTS.read_text())
        configured = {
            entry["path"].split("/ansible/files/components/infisical-database-secrets/", 1)[1]: entry["sha256"]
            for entry in defaults["infisical_database_secrets_bootstrap_expected_hashes"]
        }
        self.assertEqual(ledger, configured)

        literal = PLUGIN.read_text().split("_EXPECTED_OBJECT_HASHES: dict", 1)[1]
        literal = literal.split(" = ", 1)[1].split("\n_EXPECTED_IDENTITY_SET_SHA256", 1)[0]
        plugin_hashes = ast.literal_eval(literal)
        expected = {identity: canonical_hash(obj) for identity, obj in self.by_identity.items()}
        self.assertEqual(expected, plugin_hashes)
        identity_keys = sorted("|".join(identity) for identity in self.by_identity)
        self.assertIn(
            hashlib.sha256("\n".join(identity_keys).encode()).hexdigest(),
            PLUGIN.read_text(),
        )

    def test_fixed_project_environment_paths_auths_and_targets(self) -> None:
        connection = self.by_identity[
            ("secrets.infisical.com/v1beta1", "InfisicalConnection", "shared-services", "infisical-cloud")
        ]
        self.assertEqual({"address": "https://app.infisical.com/api"}, connection["spec"])
        expected_auths = {
            "shared-postgresql-infisical-auth": "shared-postgresql-infisical-universal-auth",
            "shared-mongodb-infisical-auth": "shared-mongodb-infisical-universal-auth",
        }
        for name, credential in expected_auths.items():
            auth = self.by_identity[("secrets.infisical.com/v1beta1", "InfisicalAuth", "shared-services", name)]
            self.assertEqual("universal", auth["spec"]["method"])
            self.assertEqual(
                {"name": "infisical-cloud", "namespace": "shared-services"},
                auth["spec"]["infisicalConnectionRef"],
            )
            self.assertEqual(
                {"name": credential, "namespace": "shared-services", "key": "clientId"},
                auth["spec"]["universal"]["clientIdRef"],
            )
            self.assertEqual(
                {"name": credential, "namespace": "shared-services", "key": "clientSecret"},
                auth["spec"]["universal"]["clientSecretRef"],
            )

        for name, path in {
            "shared-postgresql-infisical-secrets": "/shared-services/postgresql",
            "shared-mongodb-infisical-secrets": "/shared-services/mongodb",
        }.items():
            static = self.by_identity[
                ("secrets.infisical.com/v1beta1", "InfisicalStaticSecret", "shared-services", name)
            ]
            self.assertEqual("cristexweb-infrastructure", static["spec"]["sources"][0]["projectSlug"])
            self.assertEqual("bootstrap", static["spec"]["sources"][0]["environmentSlug"])
            self.assertEqual(path, static["spec"]["sources"][0]["secretPath"])
            self.assertFalse(static["spec"]["sources"][0]["recursive"])
            self.assertEqual([], static["spec"]["sources"][0]["tagSlugs"])
            self.assertNotIn("projectId", static["spec"]["sources"][0])
            self.assertEqual({"refreshInterval": "1h", "instantUpdates": False}, static["spec"]["syncOptions"])
            for target in static["spec"]["targets"]:
                self.assertEqual("shared-services", target["namespace"])
                self.assertEqual("Secret", target["kind"])
                self.assertEqual("Orphan", target["creationPolicy"])
                self.assertEqual(TARGET_LABELS, target["metadata"]["labels"])
                self.assertEqual({}, target["metadata"]["annotations"])
                self.assertEqual("v1", target["template"]["engineVersion"])
                self.assertEqual(TEMPLATES[target["name"]], target["template"]["data"])

    def test_source_fields_match_promoted_v0117_crds_and_vap_resources(self) -> None:
        crds = {
            path.stem.removesuffix(".yaml"): yaml.safe_load(path.read_text())
            for path in (ROOT / "ansible/files/components/infisical-operator/crds").glob("*.yaml")
        }
        for name in (
            "infisicalconnections",
            "infisicalauths",
            "infisicalstaticsecrets",
        ):
            self.assertEqual("v0.11.7", crds[name]["metadata"]["labels"]["cristex.io/source-version"])
            self.assertEqual("v1beta1", crds[name]["spec"]["versions"][0]["name"])
        auth_schema = crds["infisicalauths"]["spec"]["versions"][0]["schema"]["openAPIV3Schema"]
        static_schema = crds["infisicalstaticsecrets"]["spec"]["versions"][0]["schema"]["openAPIV3Schema"]
        self.assertEqual(
            {"infisicalConnectionRef", "method"},
            set(auth_schema["properties"]["spec"]["required"]),
        )
        self.assertEqual(
            {"infisicalAuthRef", "sources", "syncOptions", "targets"},
            set(static_schema["properties"]["spec"]["required"]),
        )
        target_properties = static_schema["properties"]["spec"]["properties"]["targets"]["items"]["properties"]
        self.assertEqual({"Owner", "Orphan"}, set(target_properties["creationPolicy"]["enum"]))
        self.assertEqual({"Secret", "ConfigMap"}, set(target_properties["kind"]["enum"]))
        for source in self.objects:
            if source["kind"] in {"InfisicalConnection", "InfisicalAuth", "InfisicalStaticSecret"}:
                self.assertEqual("secrets.infisical.com/v1beta1", source["apiVersion"])

        policies = {
            obj["metadata"]["name"]: obj
            for obj in self.objects
            if obj["kind"] == "ValidatingAdmissionPolicy"
        }
        secret_rule = policies["infisical-database-secret-write-boundary"]["spec"]["matchConstraints"]["resourceRules"][0]
        self.assertEqual([""], secret_rule["apiGroups"])
        self.assertEqual(["v1"], secret_rule["apiVersions"])
        self.assertEqual(["secrets"], secret_rule["resources"])
        static_rule = policies["infisical-database-static-secret-boundary"]["spec"]["matchConstraints"]["resourceRules"][0]
        self.assertEqual(["secrets.infisical.com"], static_rule["apiGroups"])
        self.assertEqual(["v1beta1"], static_rule["apiVersions"])
        self.assertEqual(["infisicalstaticsecrets"], static_rule["resources"])
        alternate_rule = policies["infisical-database-alternate-target-boundary"]["spec"]["matchConstraints"]["resourceRules"][0]
        self.assertEqual(["secrets.infisical.com"], alternate_rule["apiGroups"])
        self.assertEqual(["v1alpha1"], alternate_rule["apiVersions"])
        source_rule = policies["infisical-database-source-boundary"]["spec"]["matchConstraints"]["resourceRules"][0]
        self.assertEqual(["secrets.infisical.com"], source_rule["apiGroups"])
        self.assertEqual(["v1beta1"], source_rule["apiVersions"])
        self.assertEqual(
            {"infisicalconnections", "infisicalauths"},
            set(source_rule["resources"]),
        )

    def test_targets_align_with_stateful_database_secret_contract(self) -> None:
        targets = {}
        for obj in self.objects:
            if obj["kind"] == "InfisicalStaticSecret":
                targets.update({target["name"]: target for target in obj["spec"]["targets"]})
        self.assertEqual(set(TARGETS), set(targets))
        for name, contract in TARGETS.items():
            self.assertEqual(contract["type"], targets[name]["secretType"])
            self.assertEqual(contract["keys"], set(targets[name]["template"]["data"]))
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(
            {name: {"type": value["type"], "keys": sorted(value["keys"])} for name, value in TARGETS.items()},
            {name: {"type": value["type"], "keys": sorted(value["keys"])} for name, value in defaults["infisical_database_secrets_bootstrap_target_contract"].items()},
        )
        self.assertEqual(11, defaults["infisical_database_secrets_bootstrap_target_count"])
        expected_credential_labels = {
            "app.kubernetes.io/managed-by": "ansible",
            "app.kubernetes.io/part-of": "infisical-operator",
            "cristex.io/component": "infisical-runtime-auth",
            "cristex.io/value-owner": "infisical-cloud",
        }
        for credential in defaults["infisical_database_secrets_bootstrap_credential_contracts"]:
            self.assertEqual(expected_credential_labels, credential["labels"])

    def test_admission_is_fail_closed_and_cross_policy_scoped(self) -> None:
        policies = [obj for obj in self.objects if obj["kind"] == "ValidatingAdmissionPolicy"]
        bindings = [obj for obj in self.objects if obj["kind"] == "ValidatingAdmissionPolicyBinding"]
        self.assertEqual(4, len(policies))
        self.assertEqual(4, len(bindings))
        policy_by_name = {obj["metadata"]["name"]: obj for obj in policies}
        binding_by_name = {obj["metadata"]["name"]: obj for obj in bindings}
        self.assertEqual(set(policy_by_name), set(binding_by_name))
        for policy in policies:
            self.assertEqual("Fail", policy["spec"]["failurePolicy"])
            rule = policy["spec"]["matchConstraints"]["resourceRules"][0]
            self.assertEqual(["CREATE", "UPDATE"], rule["operations"])
            self.assertEqual("Namespaced", rule["scope"])
        for binding in bindings:
            self.assertEqual(["Deny"], binding["spec"]["validationActions"])
            self.assertEqual(binding["metadata"]["name"], binding["spec"]["policyName"])

        secret = policy_by_name["infisical-database-secret-write-boundary"]
        conditions = secret["spec"]["matchConditions"]
        self.assertEqual(2, len(conditions))
        self.assertIn("request.namespace == 'shared-services'", conditions[0]["expression"])
        self.assertIn("request.userInfo.username ==", conditions[1]["expression"])
        self.assertIn("object.metadata.name in", conditions[1]["expression"])
        expression = secret["spec"]["validations"][0]["expression"]
        self.assertIn("request.userInfo.username ==", expression)
        self.assertNotIn("request.userInfo.username !=", expression)
        for required in (
            "shared-postgresql-admin",
            "shared-postgresql-tls",
            "shared-mongodb-auth",
            "shared-mongodb-tls",
            "shared-postgresql-cristexhub-dev",
            "shared-postgresql-cristexhub-prod",
            "shared-postgresql-reactive-resume-dev",
            "shared-postgresql-reactive-resume-prod",
            "shared-postgresql-keycloak",
            "shared-mongodb-cristexhub-dev",
            "shared-mongodb-cristexhub-prod",
            "object.type == 'Opaque'",
            "object.type == 'kubernetes.io/tls'",
            "object.data['tls.pem'] != null",
            "object.binaryData.size() == 0",
        ):
            self.assertIn(required, expression)
        self.assertNotIn("argocd", expression)
        self.assertNotIn("argocd", secret["spec"]["matchConditions"][0]["expression"])

        alternate = policy_by_name["infisical-database-alternate-target-boundary"]
        self.assertEqual(
            {"infisicalsecrets", "infisicalpushsecrets", "infisicaldynamicsecrets"},
            set(alternate["spec"]["matchConstraints"]["resourceRules"][0]["resources"]),
        )
        self.assertIn("request.namespace != 'shared-services'", alternate["spec"]["validations"][0]["expression"])
        static = policy_by_name["infisical-database-static-secret-boundary"]
        self.assertEqual(1, len(static["spec"]["matchConditions"]))
        static_match = static["spec"]["matchConditions"][0]["expression"]
        self.assertIn("request.namespace == 'shared-services'", static_match)
        self.assertIn("shared-postgresql-infisical-secrets", static_match)
        self.assertIn("shared-mongodb-infisical-secrets", static_match)
        self.assertIn(
            "system:serviceaccount:shared-services:infisical-operator-controller",
            static_match,
        )
        static_expression = static["spec"]["validations"][0]["expression"]
        for required in (
            "request.userInfo.username == 'system:admin'",
            "system:serviceaccount:shared-services:infisical-operator-controller",
            "oldObject != null",
            "oldObject.spec == object.spec",
            "shared-postgresql-infisical-secrets",
            "shared-mongodb-infisical-secrets",
            "/shared-services/postgresql",
            "/shared-services/mongodb",
            "!has(object.spec.sources[0].projectId)",
            "object.spec.sources[0].recursive == false",
            "object.spec.sources[0].tagSlugs.size() == 0",
            "object.spec.targets.size() == 7",
            "object.spec.targets.size() == 4",
            "creationPolicy == 'Orphan'",
        ):
            self.assertIn(required, static_expression)
        self.assertNotIn("template.data", static_expression)
        self.assertNotIn("request.namespace !=", static_expression)

        source = policy_by_name["infisical-database-source-boundary"]
        source_match = source["spec"]["matchConditions"][0]["expression"]
        source_expression = source["spec"]["validations"][0]["expression"]
        for required in (
            "request.namespace == 'shared-services'",
            "system:serviceaccount:shared-services:infisical-operator-controller",
            "infisical-cloud",
            "shared-postgresql-infisical-auth",
            "shared-mongodb-infisical-auth",
        ):
            self.assertIn(required, source_match + source_expression)
        for required in (
            "request.userInfo.username == 'system:admin'",
            "oldObject != null",
            "oldObject.spec == object.spec",
            "https://app.infisical.com/api",
            "shared-postgresql-infisical-universal-auth",
            "shared-mongodb-infisical-universal-auth",
            "clientId",
            "clientSecret",
        ):
            self.assertIn(required, source_expression)

    def test_rbac_has_only_additive_secret_writer_and_no_workload_write_delete(self) -> None:
        role = self.by_identity[
            ("rbac.authorization.k8s.io/v1", "Role", "shared-services", "infisical-database-secret-writer")
        ]
        secret_rules = [rule for rule in role["rules"] if rule["resources"] == ["secrets"]]
        update = next(rule for rule in secret_rules if "resourceNames" in rule)
        self.assertEqual(set(TARGETS), set(update["resourceNames"]))
        self.assertEqual(["update"], update["verbs"])
        self.assertEqual(1, len([rule for rule in secret_rules if rule.get("verbs") == ["create"]]))
        workload = next(rule for rule in role["rules"] if rule["apiGroups"] == ["apps"])
        self.assertEqual({"deployments", "daemonsets", "statefulsets"}, set(workload["resources"]))
        self.assertEqual({"list", "watch"}, set(workload["verbs"]))
        serialized = json.dumps(role)
        self.assertNotIn('"patch"', serialized)
        self.assertNotIn('"delete"', serialized)
        self.assertNotIn('"update"', json.dumps(workload))
        binding = self.by_identity[
            ("rbac.authorization.k8s.io/v1", "RoleBinding", "shared-services", "infisical-database-secret-writer")
        ]
        self.assertEqual("infisical-database-secret-writer", binding["roleRef"]["name"])
        self.assertEqual(
            {"name": "infisical-operator-controller", "namespace": "shared-services", "kind": "ServiceAccount"},
            binding["subjects"][0],
        )

    def test_guarded_preflight_order_readiness_and_fixtures(self) -> None:
        task_names = [task["name"] for task in self.tasks]
        preflight = task_names.index("Bind the protected Infisical database Secret seam preflight")
        admission = task_names.index("Reconcile exact Infisical database Secret seam admission policies first")
        policy_wait = task_names.index("Wait for exact Infisical database VAPs to be established and type-checked")
        bindings = task_names.index("Reconcile exact Infisical database Secret seam admission bindings")
        binding_wait = task_names.index("Wait for exact Infisical database VAP bindings to become effective")
        target_recheck = task_names.index("Refuse database target races before granting writer RBAC")
        alternate_recheck = task_names.index("Refuse alternate target races after admission")
        static_recheck = task_names.index("Refuse InfisicalStaticSecret identity races after admission")
        rbac = task_names.index("Reconcile exact Infisical database Secret seam RBAC after admission")
        source = task_names.index("Reconcile Infisical Connection then Auth then StaticSecret database source closure")
        wait = task_names.index("Wait for the Infisical database Connection, Auths, and StaticSecrets to become ready")
        self.assertLess(preflight, admission)
        self.assertLess(admission, policy_wait)
        self.assertLess(policy_wait, bindings)
        self.assertLess(bindings, binding_wait)
        self.assertLess(binding_wait, target_recheck)
        self.assertLess(target_recheck, alternate_recheck)
        self.assertLess(alternate_recheck, static_recheck)
        self.assertLess(static_recheck, rbac)
        self.assertLess(rbac, source)
        self.assertLess(source, wait)
        wait_expression = " ".join(self.tasks[wait]["until"])
        for condition in ("secrets.infisical.com/IsReady", "secrets.infisical.com/LastReconcileStatus", "secrets.infisical.com/LastSuccessfulReconcileAt", "observedGeneration"):
            self.assertIn(condition, wait_expression)
        self.assertIn("internal_static_secret_inventory", TASKS.read_text())
        self.assertIn("internal_target_inventory", TASKS.read_text())
        self.assertIn("unreviewed Infisical-owned database target", TASKS.read_text())
        self.assertIn("target_count", TASKS.read_text())
        self.assertIn("internal_alternate_target_crs", TASKS.read_text())
        self.assertIn("Require the ready and admitted Infisical Operator checkpoint", task_names)
        self.assertLess(
            task_names.index("Require the ready and admitted Infisical Operator checkpoint"),
            preflight,
        )
        for required in (
            "resourceVersion",
            "spec.matchResources",
            "item.resources[0].rules == item.item.rules",
            "item.resources[0].subjects == item.item.subjects",
        ):
            self.assertIn(required, TASKS.read_text())
        self.assertIn("not (item.resources[0].immutable | default(false) | bool)", TASKS.read_text())
        credential_task = self.tasks[
            task_names.index("Require the exact same-Namespace Universal Auth credential metadata")
        ]
        credential_contract = " ".join(credential_task["ansible.builtin.assert"]["that"])
        for required in ("immutable", "ownerReferences", "binaryData", "item.item.labels"):
            self.assertIn(required, credential_contract)
        self.assertIn("become: false", PLAYBOOK.read_text())
        self.assertEqual(
            [
                "infisicalconnections.secrets.infisical.com",
                "infisicalauths.secrets.infisical.com",
                "infisicalstaticsecrets.secrets.infisical.com",
                "infisicalsecrets.secrets.infisical.com",
                "infisicalpushsecrets.secrets.infisical.com",
                "infisicaldynamicsecrets.secrets.infisical.com",
            ],
            yaml.safe_load(DEFAULTS.read_text())["infisical_database_secrets_bootstrap_crd_names"],
        )
        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            WRAPPER.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            TASK_SELECTION.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        wrapper = WRAPPER.read_text()
        for required in (
            "check|apply",
            "/usr/bin/env -i",
            "--diff",
            "--limit crtxweb",
            "CRISTEXWEB_INFISICAL_DATABASE_SECRETS_BOOTSTRAP_ATTESTATION_FILE",
            "infisical_database_secrets_guarded_k8s",
            "TypeChecking",
            "validationActions",
            "crd_count",
            "static_secret_inventory_count",
        ):
            self.assertIn(required, wrapper + TASKS.read_text())
        self.assertNotIn("--ask-become-pass", wrapper)
        self.assertNotIn("--tags", wrapper)
        for fixture in (ACTION_ONLY, INTERNAL_FIXTURE, TASK_SELECTION):
            self.assertTrue(fixture.exists())
        for arguments in ((), ("check", "--tags"), ("other",)):
            result = subprocess.run(
                [str(WRAPPER), *arguments], cwd=ROOT, capture_output=True, text=True, check=False
            )
            self.assertNotEqual(0, result.returncode)

    def test_negative_fixtures_fail_before_kubernetes_access(self) -> None:
        env = os.environ.copy()
        env["ANSIBLE_CONFIG"] = str(ROOT / "ansible/ansible.cfg")
        token = "d" * 64
        with tempfile.TemporaryDirectory() as directory:
            attestation = Path(directory) / "attestation"
            attestation.write_text(f"{token}:entrypoint\n")
            attestation.chmod(0o600)
            env.update(
                {
                    "CRISTEXWEB_INFISICAL_DATABASE_SECRETS_BOOTSTRAP_ENTRYPOINT": "v1",
                    "CRISTEXWEB_INFISICAL_DATABASE_SECRETS_BOOTSTRAP_TOKEN": token,
                    "CRISTEXWEB_INFISICAL_DATABASE_SECRETS_BOOTSTRAP_ATTESTATION_FILE": str(attestation),
                }
            )
            action_only = subprocess.run(
                [
                    str(ROOT / ".venv/bin/ansible-playbook"),
                    "-i",
                    "localhost,",
                    str(ACTION_ONLY),
                    "--limit",
                    "localhost",
                ],
                cwd=ROOT / "ansible",
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(0, action_only.returncode)
        self.assertIn("ENTRYPOINT_GUARD", action_only.stdout + action_only.stderr)
        self.assertNotIn("Failed to connect", action_only.stdout + action_only.stderr)

        internal = subprocess.run(
            [
                str(ROOT / ".venv/bin/ansible-playbook"),
                "-i",
                "localhost,",
                str(INTERNAL_FIXTURE),
                "--limit",
                "localhost",
            ],
            cwd=ROOT / "ansible",
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, internal.returncode, internal.stdout + internal.stderr)
        self.assertIn("INTERNAL_VARIABLE_GUARD", internal.stdout + internal.stderr)
        self.assertNotIn("Failed to connect", internal.stdout + internal.stderr)

        task_selection = subprocess.run(
            [str(TASK_SELECTION)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            0,
            task_selection.returncode,
            task_selection.stdout + task_selection.stderr,
        )
        self.assertIn("PASS:", task_selection.stdout)

    def test_source_contains_no_values_and_runtime_remains_blocked(self) -> None:
        text = "\n".join(path.read_text() for path in COMPONENT.rglob("*") if path.is_file())
        for forbidden in ("BEGIN PRIVATE KEY", "clientSecret:", "stringData:", "data:\n  auth:"):
            self.assertNotIn(forbidden, text)
        self.assertFalse(any(obj["kind"] == "Secret" for obj in self.objects))
        self.assertIn("runtime remains **NOT RUN/BLOCKED**", (ROOT / "runbooks/infisical-database-secret-materialization.md").read_text())


if __name__ == "__main__":
    unittest.main()
