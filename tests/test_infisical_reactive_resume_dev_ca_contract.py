from __future__ import annotations

import ast
import copy
import hashlib
import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "ansible/files/components/infisical-reactive-resume-dev-ca"
DEFAULTS = ROOT / "ansible/roles/infisical_reactive_resume_dev_ca_bootstrap/defaults/main.yml"
TASKS = ROOT / "ansible/roles/infisical_reactive_resume_dev_ca_bootstrap/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/infisical_reactive_resume_dev_ca_guarded_k8s.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-infisical-reactive-resume-dev-ca"


class CaClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = sorted(COMP.rglob("*.yaml"))
        cls.objects = [yaml.safe_load(path.read_text()) for path in cls.paths]
        cls.static_secret = next(
            obj for obj in cls.objects if obj["kind"] == "InfisicalStaticSecret"
        )
        cls.source_policy = next(
            obj
            for obj in cls.objects
            if obj["kind"] == "ValidatingAdmissionPolicy"
            and obj["metadata"]["name"] == "reactive-resume-dev-ca-source-boundary"
        )
        cls.target_policy = next(
            obj
            for obj in cls.objects
            if obj["kind"] == "ValidatingAdmissionPolicy"
            and obj["metadata"]["name"] == "reactive-resume-dev-ca-target-boundary"
        )
        cls.tasks_text = TASKS.read_text()

    def test_exact_value_free_closure(self):
        self.assertEqual(7, len(self.objects))
        self.assertEqual(
            {
                "ValidatingAdmissionPolicy": 2,
                "ValidatingAdmissionPolicyBinding": 2,
                "Role": 1,
                "RoleBinding": 1,
                "InfisicalStaticSecret": 1,
            },
            {
                kind: sum(obj["kind"] == kind for obj in self.objects)
                for kind in {obj["kind"] for obj in self.objects}
            },
        )
        self.assertFalse(any(obj["kind"] == "Secret" for obj in self.objects))

    def test_exact_sources_targets_and_sync_options(self):
        spec = self.static_secret["spec"]
        self.assertEqual(
            {
                "name": "cristexhub-dev-infisical-auth",
                "namespace": "cristexhub-dev",
            },
            spec["infisicalAuthRef"],
        )
        self.assertEqual({"refreshInterval": "1h", "instantUpdates": False}, spec["syncOptions"])
        self.assertEqual(
            [
                {
                    "projectId": "619656da-14f3-4872-857b-be103cdc5326",
                    "environmentSlug": "prod",
                    "secretPath": "/reactive-resume/dev/object-storage-tls",
                    "recursive": False,
                    "tagSlugs": [],
                }
            ],
            spec["sources"],
        )
        self.assertEqual(
            [
                {
                    "name": "reactive-resume-dev-postgresql-ca",
                    "namespace": "cristexhub-dev",
                    "kind": "ConfigMap",
                    "creationPolicy": "Orphan",
                    "metadata": {
                        "annotations": {},
                        "labels": {
                            "app.kubernetes.io/managed-by": "infisical",
                            "app.kubernetes.io/part-of": "reactive-resume",
                            "cristex.io/value-owner": "infisical-cloud",
                        },
                    },
                    "template": {
                        "engineVersion": "v1",
                        "data": {"ca.crt": "{{ .POSTGRESQL_CA_CRT.Value }}"},
                    },
                },
                {
                    "name": "reactive-resume-dev-object-storage-ca",
                    "namespace": "cristexhub-dev",
                    "kind": "Secret",
                    "secretType": "Opaque",
                    "creationPolicy": "Orphan",
                    "metadata": {
                        "annotations": {},
                        "labels": {
                            "app.kubernetes.io/managed-by": "infisical",
                            "app.kubernetes.io/part-of": "reactive-resume",
                            "cristex.io/value-owner": "infisical-cloud",
                        },
                    },
                    "template": {
                        "engineVersion": "v1",
                        "data": {"ca.crt": "{{ .STORAGE_TLS_CA_CRT.Value }}"},
                    },
                },
            ],
            spec["targets"],
        )

    def test_exact_operator_writer_and_guard(self):
        role_binding = next(obj for obj in self.objects if obj["kind"] == "RoleBinding")
        self.assertEqual(
            {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "Role",
                "name": "reactive-resume-dev-ca-secret-writer",
            },
            role_binding["roleRef"],
        )
        self.assertEqual(
            [
                {
                    "kind": "ServiceAccount",
                    "name": "infisical-operator-controller",
                    "namespace": "shared-services",
                }
            ],
            role_binding["subjects"],
        )
        role = next(obj for obj in self.objects if obj["kind"] == "Role")
        self.assertEqual(4, len(role["rules"]))
        self.assertIn("check|apply", WRAPPER.read_text())
        self.assertIn("CRISTEXWEB_INFISICAL_REACTIVE_RESUME_DEV_CA_TOKEN", WRAPPER.read_text())
        self.assertIn("precreated DEV Infisical Auth", self.tasks_text)

    def test_prestate_requires_exact_role_and_rolebinding_specs(self):
        self.assertIn("item.resources[0].rules == item.item.rules", self.tasks_text)
        self.assertIn("item.resources[0].spec == item.item.spec", self.tasks_text)
        self.assertNotIn("item.resources[0].get('rules') == item.item.get('rules')", self.tasks_text)
        self.assertNotIn("item.resources[0].get('spec') == item.item.get('spec') or", self.tasks_text)

    def test_predecessor_source_contract_is_exact(self):
        # The only accepted predecessor has both historical sources and all
        # source fields fixed.  Mutating any source field must fail equality.
        predecessor = copy.deepcopy(self.static_secret["spec"])
        predecessor["sources"] = [
            {
                "projectId": "619656da-14f3-4872-857b-be103cdc5326",
                "environmentSlug": "prod",
                "secretPath": "/shared-services/postgresql",
                "recursive": False,
                "tagSlugs": [],
            },
            copy.deepcopy(self.static_secret["spec"]["sources"][0]),
        ]
        predecessor["targets"][0]["template"]["data"] = {
            "ca.crt": "{{ .POSTGRESQL_TLS_CA_CRT.Value }}"
        }
        predecessor["targets"][1]["template"]["data"] = {"ca.crt": "{{ .CA_CRT.Value }}"}
        expected_sources = copy.deepcopy(predecessor["sources"])
        for index, field, value in (
            (0, "projectId", "other-project"),
            (0, "environmentSlug", "dev"),
            (0, "secretPath", "/wrong"),
            (0, "recursive", True),
            (0, "tagSlugs", ["unexpected"]),
            (1, "projectId", "other-project"),
            (1, "environmentSlug", "dev"),
            (1, "secretPath", "/wrong"),
            (1, "recursive", True),
            (1, "tagSlugs", ["unexpected"]),
        ):
            mutated = copy.deepcopy(expected_sources)
            mutated[index][field] = value
            self.assertNotEqual(expected_sources, mutated, (index, field))
        for required in (
            "sources[0].projectId == '619656da-14f3-4872-857b-be103cdc5326'",
            "sources[0].environmentSlug == 'prod'",
            "sources[0].secretPath == '/shared-services/postgresql'",
            "sources[0].recursive == false",
            "sources[0].tagSlugs | length == 0",
            "sources[1].projectId == '619656da-14f3-4872-857b-be103cdc5326'",
            "sources[1].environmentSlug == 'prod'",
            "sources[1].secretPath == '/reactive-resume/dev/object-storage-tls'",
            "sources[1].recursive == false",
            "sources[1].tagSlugs | length == 0",
        ):
            self.assertIn(required, self.tasks_text)

    def test_vap_source_and_target_closures_are_full(self):
        source_expression = self.source_policy["spec"]["validations"][0]["expression"]
        target_expression = self.target_policy["spec"]["validations"][0]["expression"]
        for required in (
            "object.spec.size() == 4",
            "object.spec.syncOptions.size() == 2",
            "object.spec.syncOptions.refreshInterval == '1h'",
            "object.spec.syncOptions.instantUpdates == false",
            "object.spec.sources[0].size() == 5",
            "object.spec.targets[0].namespace == 'cristexhub-dev'",
            "object.spec.targets[0].creationPolicy == 'Orphan'",
            "object.spec.targets[0].metadata.annotations.size() == 0",
            "object.spec.targets[0].template.engineVersion == 'v1'",
            "object.spec.targets[1].secretType == 'Opaque'",
            "object.spec.targets[1].template.data['ca.crt'] == '{{ .STORAGE_TLS_CA_CRT.Value }}'",
        ):
            self.assertIn(required, source_expression)
        for required in (
            "object.metadata.namespace == 'cristexhub-dev'",
            "object.metadata.finalizers.size() == 0",
            "object.data.size() == 1",
            "object.data['ca.crt'].startsWith('-----BEGIN CERTIFICATE-----')",
            "object.data['ca.crt'].startsWith('LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0t')",
        ):
            self.assertIn(required, target_expression)

    def test_negative_vap_and_predecessor_mutations_are_represented(self):
        source_expression = self.source_policy["spec"]["validations"][0]["expression"]
        target_expression = self.target_policy["spec"]["validations"][0]["expression"]
        for forbidden in (
            "object.spec.sources[0].secretPath == '/shared-services/postgresql'",
            "object.spec.targets[0].kind == 'Secret'",
            "object.spec.syncOptions.instantUpdates == true",
        ):
            self.assertNotIn(forbidden, source_expression)
        for forbidden in (
            "object.data.size() > 0",
            "object.metadata.name == 'unrestricted-ca'",
        ):
            self.assertNotIn(forbidden, target_expression)
        self.assertIn("item.resources[0].spec.sources | length == 2", self.tasks_text)
        self.assertIn("item.resources[0].spec.targets[0].template.data['ca.crt'] | b64encode", self.tasks_text)

    def test_hash_ledgers_and_action_map(self):
        ledger = {
            line.split("  ", 1)[1]: line.split()[0]
            for line in (COMP / "MANIFESTS.sha256").read_text().splitlines()
        }
        self.assertEqual(set(ledger), {str(path.relative_to(COMP)) for path in self.paths})
        self.assertTrue(
            all(hashlib.sha256((COMP / relative).read_bytes()).hexdigest() == digest for relative, digest in ledger.items())
        )
        defaults = yaml.safe_load(DEFAULTS.read_text())
        configured = {
            item["path"].rsplit("}}/", 1)[1]: item["sha256"]
            for item in defaults["infisical_reactive_resume_dev_ca_bootstrap_expected_hashes"]
        }
        self.assertEqual(ledger, configured)
        literal = PLUGIN.read_text().split("EXPECTED: dict", 1)[1].split(" = {", 1)[1].split("\n}", 1)[0]
        actual = ast.literal_eval("{" + literal + "}")
        expected = {
            (
                obj["apiVersion"],
                obj["kind"],
                obj["metadata"].get("namespace", ""),
                obj["metadata"]["name"],
            ): hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            for obj in self.objects
        }
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
