from __future__ import annotations

import ast
import hashlib
import json
import re
import stat
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/infisical-argocd-secrets"
DEFAULTS = ROOT / "ansible/roles/infisical_argocd_secrets_bootstrap/defaults/main.yml"
TASKS = ROOT / "ansible/roles/infisical_argocd_secrets_bootstrap/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/infisical_argocd_secrets_guarded_k8s.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-infisical-argocd-secrets"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_infisical_argocd_secrets.yml"
ACTION_ONLY = ROOT / "tests/reject_infisical_argocd_secrets_action_only.yml"
INTERNAL_FIXTURE = ROOT / "tests/reject_infisical_argocd_secrets_internal_injection.yml"
TASK_START = ROOT / "tests/reject_infisical_argocd_secrets_task_start.sh"

LABELS = {
    "app.kubernetes.io/part-of": "cristex-platform",
    "app.kubernetes.io/managed-by": "ansible",
    "cristex.io/component": "infisical-argocd-secrets",
}
TARGET_LABELS = {
    "app.kubernetes.io/managed-by": "infisical",
    "app.kubernetes.io/part-of": "argocd",
    "cristex.io/value-owner": "infisical-cloud",
}
TARGETS = {
    "argocd-secret": {
        "type": "Opaque",
        "keys": {"admin.password", "admin.passwordMtime", "server.secretkey"},
    },
    "argocd-redis": {"type": "Opaque", "keys": {"auth"}},
    "argocd-server-tls": {
        "type": "kubernetes.io/tls",
        "keys": {"ca.crt", "tls.crt", "tls.key"},
    },
    "argocd-repository-cristexhub": {
        "type": "Opaque",
        "keys": {"sshPrivateKey", "type", "url"},
    },
    "argocd-repository-cristexweb": {
        "type": "Opaque",
        "keys": {"sshPrivateKey", "type", "url"},
    },
}
TEMPLATES = {
    "argocd-secret": {
        "admin.password": "{{ .ARGOCD_ADMIN_PASSWORD_BCRYPT.Value }}",
        "admin.passwordMtime": "{{ .ARGOCD_ADMIN_PASSWORD_MTIME.Value }}",
        "server.secretkey": "{{ .ARGOCD_SERVER_SECRETKEY.Value }}",
    },
    "argocd-redis": {"auth": "{{ .ARGOCD_REDIS_AUTH.Value }}"},
    "argocd-server-tls": {
        "ca.crt": "{{ .ARGOCD_TLS_CA_CRT.Value }}",
        "tls.crt": "{{ .ARGOCD_TLS_CRT.Value }}",
        "tls.key": "{{ .ARGOCD_TLS_KEY.Value }}",
    },
    "argocd-repository-cristexhub": {
        "type": "git",
        "url": "ssh://git@ssh.github.com:443/devraider/cristexhub.git",
        "sshPrivateKey": "{{ .ARGOCD_CRISTEXHUB_REPOSITORY_SSH_PRIVATE_KEY.Value }}",
    },
    "argocd-repository-cristexweb": {
        "type": "git",
        "url": "ssh://git@ssh.github.com:443/devraider/cristexweb.git",
        "sshPrivateKey": "{{ .ARGOCD_CRISTEXWEB_REPOSITORY_SSH_PRIVATE_KEY.Value }}",
    },
}


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class InfisicalArgoCdSecretSeamContractTests(unittest.TestCase):
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

    def test_exact_value_free_13_object_closure_and_hashes(self) -> None:
        self.assertEqual(13, len(self.paths))
        self.assertEqual(13, len(self.by_identity))
        self.assertEqual(13, sum(1 for obj in self.objects if obj["kind"]))
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
                hashlib.sha256(path.read_bytes()).hexdigest(), ledger[str(path.relative_to(COMPONENT))]
            )
        defaults = yaml.safe_load(DEFAULTS.read_text())
        configured_hashes = {
            entry["path"].split("/ansible/files/components/infisical-argocd-secrets/", 1)[1]:
            entry["sha256"]
            for entry in defaults["infisical_argocd_secrets_bootstrap_expected_hashes"]
        }
        self.assertEqual(ledger, configured_hashes)

        literal = PLUGIN.read_text().split("_EXPECTED_OBJECT_HASHES: dict", 1)[1]
        literal = literal.split(" = ", 1)[1].split("\n_EXPECTED_IDENTITY_SET_SHA256", 1)[0]
        plugin_hashes = ast.literal_eval(literal)
        expected = {identity: canonical_hash(obj) for identity, obj in self.by_identity.items()}
        self.assertEqual(expected, plugin_hashes)
        identity_keys = sorted("|".join(identity) for identity in self.by_identity)
        expected_identity_digest = hashlib.sha256("\n".join(identity_keys).encode()).hexdigest()
        self.assertIn(expected_identity_digest, PLUGIN.read_text())

    def test_source_closure_uses_one_same_namespace_ua_and_fixed_identifiers(self) -> None:
        connection = self.by_identity[
            ("secrets.infisical.com/v1beta1", "InfisicalConnection", "argocd", "infisical-cloud")
        ]
        self.assertEqual({"address": "https://app.infisical.com"}, connection["spec"])
        auth = self.by_identity[
            ("secrets.infisical.com/v1beta1", "InfisicalAuth", "argocd", "argocd-infisical-auth")
        ]
        self.assertEqual("universal", auth["spec"]["method"])
        self.assertEqual("infisical-cloud", auth["spec"]["infisicalConnectionRef"]["name"])
        self.assertEqual("argocd", auth["spec"]["infisicalConnectionRef"]["namespace"])
        self.assertEqual(
            {"name": "argocd-infisical-universal-auth", "namespace": "argocd", "key": "clientId"},
            auth["spec"]["universal"]["clientIdRef"],
        )
        self.assertEqual(
            {"name": "argocd-infisical-universal-auth", "namespace": "argocd", "key": "clientSecret"},
            auth["spec"]["universal"]["clientSecretRef"],
        )
        static = self.by_identity[
            (
                "secrets.infisical.com/v1beta1",
                "InfisicalStaticSecret",
                "argocd",
                "argocd-infisical-secrets",
            )
        ]
        self.assertEqual(
            {"name": "argocd-infisical-auth", "namespace": "argocd"},
            static["spec"]["infisicalAuthRef"],
        )
        self.assertEqual(
            [{
                "projectId": "619656da-14f3-4872-857b-be103cdc5326",
                "environmentSlug": "prod",
                "secretPath": "/argocd",
                "recursive": False,
                "tagSlugs": [],
            }],
            static["spec"]["sources"],
        )
        self.assertEqual({"refreshInterval": "5m", "instantUpdates": False}, static["spec"]["syncOptions"])
        source = static["spec"]["sources"][0]
        self.assertFalse(source.get("recursive"))
        self.assertEqual([], source.get("tagSlugs"))
        self.assertNotIn("projectSlug", source)

    def test_source_fields_match_the_promoted_v0117_crds(self) -> None:
        crds = {
            path.stem.removesuffix(".yaml"): yaml.safe_load(path.read_text())
            for path in (ROOT / "ansible/files/components/infisical-operator/crds").glob("*.yaml")
        }
        connection_schema = crds["infisicalconnections"]["spec"]["versions"][0]["schema"]["openAPIV3Schema"]
        auth_schema = crds["infisicalauths"]["spec"]["versions"][0]["schema"]["openAPIV3Schema"]
        static_schema = crds["infisicalstaticsecrets"]["spec"]["versions"][0]["schema"]["openAPIV3Schema"]
        self.assertEqual("v1beta1", crds["infisicalconnections"]["spec"]["versions"][0]["name"])
        self.assertEqual("v1beta1", crds["infisicalauths"]["spec"]["versions"][0]["name"])
        self.assertEqual("v1beta1", crds["infisicalstaticsecrets"]["spec"]["versions"][0]["name"])
        for name in ("infisicalconnections", "infisicalauths", "infisicalstaticsecrets"):
            self.assertEqual(
                "v0.11.7",
                crds[name]["metadata"]["labels"]["cristex.io/source-version"],
            )
        connection_spec = connection_schema["properties"]["spec"]
        self.assertIn("address", connection_spec["properties"])
        auth_spec = auth_schema["properties"]["spec"]
        self.assertEqual({"infisicalConnectionRef", "method"}, set(auth_spec["required"]))
        self.assertEqual(
            {"name", "namespace"},
            set(auth_spec["properties"]["infisicalConnectionRef"]["properties"]),
        )
        universal = auth_spec["properties"]["universal"]["properties"]
        for reference in ("clientIdRef", "clientSecretRef"):
            self.assertEqual({"key", "name", "namespace"}, set(universal[reference]["properties"]))
        static_spec = static_schema["properties"]["spec"]
        self.assertEqual(
            {"infisicalAuthRef", "sources", "syncOptions", "targets"},
            set(static_spec["required"]),
        )
        source_properties = static_spec["properties"]["sources"]["items"]["properties"]
        self.assertTrue({"projectId", "environmentSlug", "secretPath"} <= set(source_properties))
        target_properties = static_spec["properties"]["targets"]["items"]["properties"]
        self.assertEqual({"Owner", "Orphan"}, set(target_properties["creationPolicy"]["enum"]))
        self.assertEqual({"Secret", "ConfigMap"}, set(target_properties["kind"]["enum"]))
        self.assertEqual(["v1"], target_properties["template"]["properties"]["engineVersion"]["enum"])
        for source in self.objects:
            if source["kind"] in {"InfisicalConnection", "InfisicalAuth", "InfisicalStaticSecret"}:
                self.assertEqual("secrets.infisical.com/v1beta1", source["apiVersion"])

    def test_targets_have_exact_types_labels_keys_orphan_policy_and_templates(self) -> None:
        static = self.by_identity[
            (
                "secrets.infisical.com/v1beta1",
                "InfisicalStaticSecret",
                "argocd",
                "argocd-infisical-secrets",
            )
        ]
        targets = {target["name"]: target for target in static["spec"]["targets"]}
        self.assertEqual(set(TARGETS), set(targets))
        for name, contract in TARGETS.items():
            target = targets[name]
            self.assertEqual("argocd", target["namespace"])
            self.assertEqual("Secret", target["kind"])
            self.assertEqual(contract["type"], target["secretType"])
            self.assertEqual("Orphan", target["creationPolicy"])
            labels = dict(TARGET_LABELS)
            if name in {"argocd-repository-cristexhub", "argocd-repository-cristexweb"}:
                labels["argocd.argoproj.io/secret-type"] = "repository"
            self.assertEqual(labels, target["metadata"]["labels"])
            self.assertEqual({}, target["metadata"]["annotations"])
            self.assertEqual("v1", target["template"]["engineVersion"])
            self.assertEqual(TEMPLATES[name], target["template"]["data"])
            self.assertEqual(contract["keys"], set(target["template"]["data"]))

    def test_admission_is_fail_closed_and_exact(self) -> None:
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
        secret = policy_by_name["infisical-argocd-secret-write-boundary"]
        secret_rule = secret["spec"]["matchConstraints"]["resourceRules"][0]
        self.assertEqual(["secrets"], secret_rule["resources"])
        self.assertEqual("Fail", secret["spec"]["failurePolicy"])
        secret_conditions = secret["spec"]["matchConditions"]
        self.assertEqual(2, len(secret_conditions))
        self.assertIn("request.namespace == 'argocd'", secret_conditions[0]["expression"])
        self.assertIn("request.userInfo.username ==", secret_conditions[1]["expression"])
        self.assertIn("object.metadata.name in", secret_conditions[1]["expression"])
        secret_expression = secret["spec"]["validations"][0]["expression"]
        self.assertIn("request.userInfo.username ==", secret_expression)
        self.assertNotIn("request.userInfo.username !=", secret_expression)
        for required in (
            "system:serviceaccount:shared-services:infisical-operator-controller",
            "argocd-secret",
            "argocd-redis",
            "argocd-server-tls",
            "argocd-repository-cristexweb",
            "object.type == 'Opaque'",
            "object.type == 'kubernetes.io/tls'",
            "object.data['admin.password'] != null",
            "object.data['tls.key'] != null",
            "object.data['type'] == 'Z2l0'",
            "object.data['url'] == 'c3NoOi8vZ2l0QHNzaC5naXRodWIuY29tOjQ0My9kZXZyYWlkZXIvY3Jpc3RleGh1Yi5naXQ='",
            "object.data['url'] == 'c3NoOi8vZ2l0QHNzaC5naXRodWIuY29tOjQ0My9kZXZyYWlkZXIvY3Jpc3RleHdlYi5naXQ='",
            "object.binaryData.size() == 0",
            "request.namespace == 'argocd'",
        ):
            self.assertIn(required, secret_expression)
        alternate = policy_by_name["infisical-argocd-alternate-target-boundary"]
        self.assertEqual(
            {"infisicalsecrets", "infisicalpushsecrets", "infisicaldynamicsecrets"},
            set(alternate["spec"]["matchConstraints"]["resourceRules"][0]["resources"]),
        )
        self.assertIn("request.namespace != 'argocd'", alternate["spec"]["validations"][0]["expression"])
        static = policy_by_name["infisical-argocd-static-secret-boundary"]
        self.assertEqual(1, len(static["spec"]["matchConditions"]))
        static_match = static["spec"]["matchConditions"][0]["expression"]
        self.assertIn("request.namespace == 'argocd'", static_match)
        self.assertIn("object.metadata.name == 'argocd-infisical-secrets'", static_match)
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
            "argocd-infisical-secrets",
            "argocd-infisical-auth",
            "619656da-14f3-4872-857b-be103cdc5326",
            "prod",
            "argocd-secret",
            "argocd-redis",
            "argocd-server-tls",
            "argocd-repository-cristexhub",
            "argocd-repository-cristexweb",
            "!has(object.spec.sources[0].projectSlug)",
            "has(object.spec.sources[0].recursive)",
            "object.spec.sources[0].recursive == false",
            "has(object.spec.sources[0].tagSlugs)",
            "object.spec.sources[0].tagSlugs.size() == 0",
            "object.spec.syncOptions.refreshInterval == '5m'",
            "has(object.spec.syncOptions.instantUpdates)",
            "object.spec.syncOptions.instantUpdates == false",
            "object.spec.targets.size() == 5",
            "creationPolicy == 'Orphan'",
        ):
            self.assertIn(required, static_expression)
        self.assertIn("t.template.data['type'] == 'git'", static_expression)
        self.assertIn("t.template.data['url'] == 'ssh://git@ssh.github.com:443/devraider/cristexhub.git'", static_expression)
        self.assertIn("t.template.data['url'] == 'ssh://git@ssh.github.com:443/devraider/cristexweb.git'", static_expression)
        self.assertIn("t.template.data['sshPrivateKey']", static_expression)
        self.assertNotIn("request.namespace !=", static_expression)
        self.assertNotIn("shared-postgresql-admin", secret_expression)
        self.assertNotIn("shared-postgresql-tls", secret_expression)
        self.assertNotIn("shared-mongodb-auth", secret_expression)
        self.assertNotIn("shared-mongodb-tls", secret_expression)

        source = policy_by_name["infisical-argocd-source-boundary"]
        source_rule = source["spec"]["matchConstraints"]["resourceRules"][0]
        self.assertEqual(
            {"infisicalconnections", "infisicalauths"},
            set(source_rule["resources"]),
        )
        source_match = source["spec"]["matchConditions"][0]["expression"]
        source_expression = source["spec"]["validations"][0]["expression"]
        for required in (
            "request.namespace == 'argocd'",
            "system:serviceaccount:shared-services:infisical-operator-controller",
            "infisical-cloud",
            "argocd-infisical-auth",
        ):
            self.assertIn(required, source_match + source_expression)
        for required in (
            "request.userInfo.username == 'system:admin'",
            "oldObject != null",
            "oldObject.spec == object.spec",
            "https://app.infisical.com",
            "argocd-infisical-universal-auth",
            "clientId",
            "clientSecret",
        ):
            self.assertIn(required, source_expression)

    def test_additive_rbac_is_exact_without_patch_delete_or_workload_update(self) -> None:
        role = self.by_identity[
            (
                "rbac.authorization.k8s.io/v1",
                "Role",
                "argocd",
                "infisical-argocd-secret-writer",
            )
        ]
        secret_rules = [rule for rule in role["rules"] if rule["resources"] == ["secrets"]]
        self.assertEqual(
            {"get", "list", "watch"},
            set(next(rule for rule in secret_rules if "resourceNames" not in rule)["verbs"]),
        )
        update = next(rule for rule in secret_rules if "resourceNames" in rule)
        self.assertEqual(
            {"argocd-secret", "argocd-redis", "argocd-server-tls", "argocd-repository-cristexhub", "argocd-repository-cristexweb"},
            set(update["resourceNames"]),
        )
        self.assertEqual(["update"], update["verbs"])
        create = [rule for rule in secret_rules if "resourceNames" not in rule and rule["verbs"] == ["create"]]
        self.assertEqual(1, len(create))
        workload = next(rule for rule in role["rules"] if rule["apiGroups"] == ["apps"])
        self.assertEqual({"deployments", "daemonsets", "statefulsets"}, set(workload["resources"]))
        self.assertEqual({"list", "watch"}, set(workload["verbs"]))
        serialized = json.dumps(role)
        self.assertNotIn('"patch"', serialized)
        self.assertNotIn('"delete"', serialized)
        self.assertNotIn('"update"', json.dumps(workload))
        binding = self.by_identity[
            (
                "rbac.authorization.k8s.io/v1",
                "RoleBinding",
                "argocd",
                "infisical-argocd-secret-writer",
            )
        ]
        self.assertEqual("infisical-argocd-secret-writer", binding["roleRef"]["name"])
        self.assertEqual(
            {"name": "infisical-operator-controller", "namespace": "shared-services", "kind": "ServiceAccount"},
            binding["subjects"][0],
        )

    def test_guarded_preflight_order_and_v0117_readiness_waits(self) -> None:
        task_names = [task["name"] for task in self.tasks]
        preflight = task_names.index("Bind the protected Infisical Argo CD Secret seam preflight")
        admission = task_names.index("Reconcile exact Infisical Argo CD Secret seam admission policies first")
        bindings = task_names.index("Reconcile exact Infisical Argo CD Secret seam admission bindings")
        policy_wait = task_names.index("Wait for exact Infisical Argo CD VAPs to be established and type-checked")
        binding_wait = task_names.index("Wait for exact Infisical Argo CD VAP bindings to become effective")
        target_recheck = task_names.index("Refuse Argo CD target races before granting writer RBAC")
        alternate_recheck = task_names.index("Refuse alternate target races after admission")
        static_recheck = task_names.index("Refuse InfisicalStaticSecret identity races after admission")
        rbac = task_names.index("Reconcile exact Infisical Argo CD Secret seam RBAC after admission")
        source = task_names.index("Reconcile Infisical Connection then Auth then StaticSecret source closure")
        wait = task_names.index("Wait for the Infisical Connection, Auth, and StaticSecret to become ready")
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
        wait_task = self.tasks[wait]
        self.assertEqual("not ansible_check_mode", wait_task["when"])
        wait_expression = " ".join(wait_task["until"])
        self.assertIn("secrets.infisical.com/IsReady", wait_expression)
        self.assertIn("secrets.infisical.com/LastReconcileStatus", wait_expression)
        self.assertIn("secrets.infisical.com/LastSuccessfulReconcileAt", wait_expression)
        self.assertIn("secrets.infisical.com/IsReady", wait_expression)
        self.assertIn("observedGeneration", wait_expression)
        static_branch = TASKS.read_text().split("item.kind == 'InfisicalStaticSecret'", 1)[1].split("retries:", 1)[0]
        self.assertNotIn("secrets.infisical.com/IsReady", static_branch)
        self.assertIn("Wait for exact Infisical Argo CD VAPs to be established and type-checked", task_names)
        self.assertIn("Wait for exact Infisical Argo CD VAP bindings to become effective", task_names)
        self.assertIn("infisical_argocd_secrets_bootstrap_internal_credential", TASKS.read_text())
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
        self.assertIn("Refuse existing alternate target-producing Infisical CRs", task_names)
        self.assertIn("Refuse any noncanonical or drifted existing InfisicalStaticSecret", task_names)
        self.assertIn("internal_alternate_target_crs", TASKS.read_text())
        self.assertIn("internal_static_secret_inventory", TASKS.read_text())
        self.assertIn("immutable", TASKS.read_text())
        self.assertLess(
            task_names.index("Require the exact same-Namespace Universal Auth credential metadata"),
            preflight,
        )
        self.assertLess(
            task_names.index("Reject foreign or wrong-type Argo CD target Secrets before mutation"),
            preflight,
        )
        self.assertLess(
            task_names.index("Refuse existing alternate target-producing Infisical CRs"),
            preflight,
        )
        self.assertLess(
            task_names.index("Refuse any noncanonical or drifted existing InfisicalStaticSecret"),
            preflight,
        )
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(
            [
                "infisicalconnections.secrets.infisical.com",
                "infisicalauths.secrets.infisical.com",
                "infisicalstaticsecrets.secrets.infisical.com",
                "infisicalsecrets.secrets.infisical.com",
                "infisicalpushsecrets.secrets.infisical.com",
                "infisicaldynamicsecrets.secrets.infisical.com",
            ],
            defaults["infisical_argocd_secrets_bootstrap_crd_names"],
        )
        self.assertEqual(
            {
                "app.kubernetes.io/managed-by": "ansible",
                "app.kubernetes.io/part-of": "infisical-operator",
                "cristex.io/component": "infisical-runtime-auth",
                "cristex.io/value-owner": "infisical-cloud",
            },
            defaults["infisical_argocd_secrets_bootstrap_credential_contract"]["labels"],
        )
        credential_task = self.tasks[
            task_names.index("Require the exact same-Namespace Universal Auth credential metadata")
        ]
        credential_contract = " ".join(credential_task["ansible.builtin.assert"]["that"])
        for required in ("immutable", "ownerReferences", "binaryData", ".labels"):
            self.assertIn(required, credential_contract)

    def test_preflight_refuses_alternate_targets_and_immutable_secrets(self) -> None:
        task_text = TASKS.read_text()
        self.assertIn("Query existing alternate target-producing Infisical CRs in argocd", task_text)
        self.assertIn("item.resources | length == 0", task_text)
        self.assertIn("not (item.resources[0].immutable | default(false) | bool)", task_text)
        self.assertIn("Query every existing InfisicalStaticSecret in argocd", task_text)
        self.assertIn("internal_static_secret_inventory.resources[0].spec ==", task_text)
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(
            ["InfisicalSecret", "InfisicalPushSecret", "InfisicalDynamicSecret"],
            [entry["kind"] for entry in defaults["infisical_argocd_secrets_bootstrap_alternate_target_crs"]],
        )

    def test_guarded_wrapper_role_and_fixtures_are_non_passthrough(self) -> None:
        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            WRAPPER.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            TASK_START.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        wrapper = WRAPPER.read_text()
        tasks = TASKS.read_text()
        plugin = PLUGIN.read_text()
        for required in (
            "check|apply",
            "/usr/bin/env -i",
            "--diff",
            "--limit crtxweb",
            "CRISTEXWEB_INFISICAL_ARGOCD_SECRETS_BOOTSTRAP_ATTESTATION_FILE",
            "infisical_argocd_secrets_guarded_k8s",
            "TypeChecking",
            "validationActions",
            "crd_count",
            "static_secret_inventory_count",
        ):
            self.assertIn(required, wrapper + tasks)
        self.assertNotIn("--ask-become-pass", wrapper)
        self.assertNotIn("--tags", wrapper)
        self.assertIn("become: false", PLAYBOOK.read_text())
        self.assertIn("INTERNAL_VARIABLE_GUARD", tasks)
        for internal in (
            "internal_alternate_target_crs",
            "internal_admission_policy_state",
            "internal_admission_binding_state",
        ):
            self.assertIn(internal, tasks)
        self.assertIn("TASK_SELECTION_GUARD", plugin)
        self.assertIn("MUTATION_ARGUMENT_GUARD", plugin)
        self.assertIn("definition.get(\"kind\") == \"Secret\"", plugin)
        for fixture in (ACTION_ONLY, INTERNAL_FIXTURE, TASK_START):
            self.assertTrue(fixture.exists())
        for arguments in ((), ("check", "--tags"), ("other",)):
            result = subprocess.run(
                [str(WRAPPER), *arguments],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)

    def test_source_contains_no_secret_values_and_idle_closure_remains_44_objects(self) -> None:
        text = "\n".join(path.read_text() for path in COMPONENT.rglob("*") if path.is_file())
        for forbidden in ("BEGIN PRIVATE KEY", "clientSecret:", "stringData:", "data:\n  auth:"):
            self.assertNotIn(forbidden, text)
        self.assertFalse(any(obj["kind"] == "Secret" for obj in self.objects))
        idle = ROOT / "ansible/files/components/infisical-operator"
        self.assertEqual(44, len(list(idle.rglob("*.yaml"))))
        self.assertIn("runtime remains **NOT RUN/BLOCKED**", (ROOT / "runbooks/infisical-argocd-secret-materialization.md").read_text())


if __name__ == "__main__":
    unittest.main()
