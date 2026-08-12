from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/infisical-operator"
CHART = ROOT / "ansible/files/vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz"
WRAPPER = ROOT / "ansible/bin/bootstrap-infisical-operator"
PROXY_SECRET_WRAPPER = ROOT / "ansible/bin/bootstrap-infisical-proxy-secrets"
PROXY_SECRET_PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_infisical_proxy_secrets.yml"
PROXY_SECRET_PLUGIN = ROOT / "ansible/plugins/action/infisical_proxy_secret_zero_guarded_k8s.py"
PROXY_SECRET_TASKS = ROOT / "ansible/roles/infisical_proxy_secret_zero/tasks/main.yml"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_infisical_operator.yml"
TASKS = ROOT / "ansible/roles/infisical_operator_bootstrap/tasks/main.yml"
DEFAULTS = ROOT / "ansible/roles/infisical_operator_bootstrap/defaults/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/infisical_operator_guarded_k8s.py"
ACTION_ONLY_FIXTURE = ROOT / "tests/reject_infisical_operator_action_only.yml"
PROXY_ACTION_ONLY_FIXTURE = ROOT / "tests/reject_infisical_proxy_secret_action_only.yml"
WATCHED = {"shared-services", "argocd", "cristexhub-dev"}


class InfisicalOperatorBootstrapContractTests(unittest.TestCase):
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
        cls.wrapper = WRAPPER.read_text()
        cls.tasks = yaml.safe_load(TASKS.read_text())
        cls.plugin = PLUGIN.read_text()

    def task(self, name: str) -> dict:
        return next(item for item in self.tasks if item.get("name") == name)

    def test_exact_value_free_object_closure(self) -> None:
        self.assertEqual(40, len(self.paths))
        self.assertEqual(40, len(self.by_identity))
        kinds: dict[str, int] = {}
        for obj in self.objects:
            kinds[obj["kind"]] = kinds.get(obj["kind"], 0) + 1
            self.assertEqual("ansible", obj["metadata"]["labels"]["app.kubernetes.io/managed-by"])
            self.assertEqual("infisical-operator", obj["metadata"]["labels"]["cristex.io/component"])
        self.assertEqual(
            {
                "CustomResourceDefinition": 6,
                "ValidatingAdmissionPolicy": 6,
                "ValidatingAdmissionPolicyBinding": 6,
                "ServiceAccount": 2,
                "Role": 4,
                "RoleBinding": 4,
                "ConfigMap": 1,
                "Service": 1,
                "Deployment": 2,
                "NetworkPolicy": 8,
            },
            kinds,
        )
        self.assertNotIn("Secret", kinds)
        self.assertNotIn("ClusterRole", kinds)
        self.assertNotIn("ClusterRoleBinding", kinds)
        self.assertFalse(any("clustergenerator" in identity[3] for identity in self.by_identity))

    def test_six_crds_are_exactly_hash_mapped_to_the_chart(self) -> None:
        expected = {
            "infisicalsecrets.secrets.infisical.com",
            "infisicalpushsecrets.secrets.infisical.com",
            "infisicaldynamicsecrets.secrets.infisical.com",
            "infisicalconnections.secrets.infisical.com",
            "infisicalauths.secrets.infisical.com",
            "infisicalstaticsecrets.secrets.infisical.com",
        }
        crds = [obj for obj in self.objects if obj["kind"] == "CustomResourceDefinition"]
        self.assertEqual(expected, {obj["metadata"]["name"] for obj in crds})
        self.assertTrue(all(obj["spec"]["scope"] == "Namespaced" for obj in crds))
        mapping = yaml.safe_load((COMPONENT / "CRD-SOURCE-MAPPING.yml").read_text())
        self.assertFalse(mapping["cluster_generator_promoted"])
        self.assertEqual(expected, {item["crd"] for item in mapping["mappings"]})
        with tarfile.open(CHART, "r:gz") as archive:
            for item in mapping["mappings"]:
                raw = archive.extractfile(item["source_member"]).read()
                promoted = ROOT / item["promoted_file"]
                self.assertEqual(item["source_template_sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(item["promoted_sha256"], hashlib.sha256(promoted.read_bytes()).hexdigest())

    def test_manifest_checksum_ledger_is_complete(self) -> None:
        actual = {
            str(path.relative_to(COMPONENT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.paths
        }
        recorded = {}
        for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines():
            digest, relative = line.split("  ", 1)
            recorded[relative] = digest
        self.assertEqual(actual, recorded)

    def test_runtime_hash_lookup_uses_exact_relative_keys(self) -> None:
        defaults = yaml.safe_load(DEFAULTS.read_text())
        expected_hashes = defaults["infisical_operator_bootstrap_expected_hashes"]
        actual = {
            str(path.relative_to(COMPONENT)):
                hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.paths
        }
        self.assertEqual(actual, expected_hashes)
        tasks_source = TASKS.read_text()
        self.assertIn(
            "'/ansible/files/components/infisical-operator/',\n"
            "            ''",
            tasks_source,
        )
        self.assertNotIn(
            "infisical_operator_bootstrap_expected_hashes[item.item]",
            tasks_source,
        )

    def test_admission_is_fail_closed_same_namespace_and_generator_free(self) -> None:
        policies = [obj for obj in self.objects if obj["kind"] == "ValidatingAdmissionPolicy"]
        bindings = [obj for obj in self.objects if obj["kind"] == "ValidatingAdmissionPolicyBinding"]
        self.assertEqual(6, len(policies))
        self.assertEqual(6, len(bindings))
        resources = set()
        combined = ""
        for policy in policies:
            self.assertEqual("Fail", policy["spec"]["failurePolicy"])
            rule = policy["spec"]["matchConstraints"]["resourceRules"][0]
            self.assertEqual(["CREATE", "UPDATE"], rule["operations"])
            self.assertEqual("Namespaced", rule["scope"])
            self.assertEqual(["secrets.infisical.com"], rule["apiGroups"])
            self.assertEqual(1, len(rule["resources"]))
            resources.add(rule["resources"][0])
            combined += json.dumps(policy["spec"]["validations"])
        self.assertEqual(
            {
                "infisicalauths",
                "infisicalconnections",
                "infisicalstaticsecrets",
                "infisicalsecrets",
                "infisicaldynamicsecrets",
                "infisicalpushsecrets",
            },
            resources,
        )
        for required in (
            "request.namespace",
            "https://app.infisical.com/api",
            "universal",
            "secretNamespace == request.namespace",
            "namespace == request.namespace",
            "generators.size() == 0",
        ):
            self.assertIn(required, combined)
        secret_policy = next(
            policy
            for policy in policies
            if policy["metadata"]["name"] == "infisical-secret-boundary"
        )
        secret_validations = " ".join(
            validation["expression"]
            for validation in secret_policy["spec"]["validations"]
        )
        self.assertIn("!has(object.spec.authentication.serviceAccount)", secret_validations)
        self.assertIn("!has(object.spec.authentication.serviceToken)", secret_validations)
        for binding in bindings:
            self.assertEqual(["Deny"], binding["spec"]["validationActions"])
            self.assertNotIn("matchResources", binding["spec"])

    def test_namespaced_rbac_is_exact_and_omits_cluster_privileges(self) -> None:
        roles = [obj for obj in self.objects if obj["kind"] == "Role"]
        manager = [obj for obj in roles if obj["metadata"]["name"] == "infisical-operator-manager"]
        self.assertEqual(WATCHED, {obj["metadata"]["namespace"] for obj in manager})
        forbidden_resources = {
            "clustergenerators",
            "tokenreviews",
            "subjectaccessreviews",
            "serviceaccounts/token",
            "deployments",
            "statefulsets",
        }
        for role in roles:
            for rule in role["rules"]:
                self.assertNotIn("*", rule.get("apiGroups", []))
                self.assertNotIn("*", rule.get("resources", []))
                self.assertNotIn("*", rule.get("verbs", []))
                self.assertTrue(forbidden_resources.isdisjoint(rule.get("resources", [])))
        for role in manager:
            secret_rule = next(
                rule for rule in role["rules"] if rule["resources"] == ["secrets"]
            )
            configmap_rule = next(
                rule for rule in role["rules"] if rule["resources"] == ["configmaps"]
            )
            self.assertEqual(["get", "list", "watch"], secret_rule["verbs"])
            self.assertEqual(["get", "list", "watch"], configmap_rule["verbs"])

    def test_controller_is_digest_pinned_scoped_metrics_off_and_proxy_only(self) -> None:
        controller = self.by_identity[("apps/v1", "Deployment", "shared-services", "infisical-operator-controller")]
        pod = controller["spec"]["template"]["spec"]
        container = pod["containers"][0]
        self.assertEqual(
            "docker.io/infisical/kubernetes-operator@sha256:5f1767f440407d8f10fb8bd7e051e26ecf18f16731a64273c20fe206947510ae",
            container["image"],
        )
        self.assertEqual(
            [
                "--metrics-bind-address=0",
                "--leader-elect",
                "--health-probe-bind-address=:8081",
                "--namespaces=shared-services,argocd,cristexhub-dev",
            ],
            container["args"],
        )
        env = {item["name"]: item.get("value", item.get("valueFrom")) for item in container["env"]}
        self.assertEqual("kubernetes.default.svc", env["KUBERNETES_SERVICE_HOST"])
        self.assertEqual("443", env["KUBERNETES_SERVICE_PORT"])
        self.assertEqual(".svc,.cluster.local,kubernetes.default.svc,localhost,127.0.0.1", env["NO_PROXY"])
        self.assertEqual("/etc/infisical-proxy-ca/ca.crt", env["SSL_CERT_FILE"])
        self.assertNotIn("SSL_CERT_DIR", env)
        self.assertEqual("infisical-egress-proxy-tls", pod["volumes"][0]["secret"]["secretName"])
        self.assertEqual(
            {"secretKeyRef": {"name": "infisical-egress-proxy-client", "key": "proxy-url"}},
            env["HTTPS_PROXY"],
        )
        self.assertTrue(pod["securityContext"]["runAsNonRoot"])
        self.assertTrue(container["securityContext"]["readOnlyRootFilesystem"])
        self.assertEqual(["ALL"], container["securityContext"]["capabilities"]["drop"])
        self.assertFalse(any(obj["kind"] == "Service" and "operator-controller" in obj["metadata"]["name"] for obj in self.objects))

    def test_proxy_is_tls_authenticated_connect_only_and_hardened(self) -> None:
        proxy = self.by_identity[("apps/v1", "Deployment", "shared-services", "infisical-egress-proxy")]
        container = proxy["spec"]["template"]["spec"]["containers"][0]
        self.assertEqual(
            "docker.io/ubuntu/squid@sha256:94f844158e12b52f51b4ae996515e37e8fb3e8d85e1c86caba1a297376e4ec4f",
            container["image"],
        )
        self.assertTrue(container["securityContext"]["readOnlyRootFilesystem"])
        config = self.by_identity[("v1", "ConfigMap", "shared-services", "infisical-egress-proxy")]["data"]["squid.conf"]
        for required in (
            "https_port 3129",
            "basic_ncsa_auth",
            "proxy_auth REQUIRED",
            "method CONNECT",
            "dstdomain app.infisical.com",
            "port 443",
            "http_access deny forbidden_dst",
            "http_access deny all",
            "cache deny all",
        ):
            self.assertIn(required, config)
        for forbidden in ("ssl_bump", "intercept", "tproxy", "password="):
            self.assertNotIn(forbidden, config.lower())

    def test_network_policy_has_no_direct_operator_internet(self) -> None:
        operator_policies = [
            obj for obj in self.objects
            if obj["kind"] == "NetworkPolicy"
            and obj["spec"]["podSelector"]["matchLabels"].get("app.kubernetes.io/name") == "infisical-operator-controller"
        ]
        self.assertEqual(4, len(operator_policies))
        api = next(obj for obj in operator_policies if obj["metadata"]["name"] == "infisical-operator-allow-api")
        self.assertEqual("10.43.0.1/32", api["spec"]["egress"][0]["to"][0]["ipBlock"]["cidr"])
        serialized = json.dumps(operator_policies)
        self.assertNotIn('"cidr": "0.0.0.0/0"', serialized)
        external = self.by_identity[("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "infisical-proxy-allow-external-https")]
        block = external["spec"]["egress"][0]["to"][0]["ipBlock"]
        self.assertEqual("0.0.0.0/0", block["cidr"])
        for private in ("10.0.0.0/8", "100.64.0.0/10", "169.254.0.0/16", "172.16.0.0/12", "192.168.0.0/16"):
            self.assertIn(private, block["except"])

    def test_wrapper_role_and_action_guard_are_non_passthrough(self) -> None:
        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            WRAPPER.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        for required in (
            "check|apply",
            "/usr/bin/env -i",
            "LC_ALL=C.UTF-8",
            "--diff",
            "--limit crtxweb",
            "CRISTEXWEB_INFISICAL_BOOTSTRAP_TOKEN",
            "openssl rand -hex 32",
        ):
            self.assertIn(required, self.wrapper)
        self.assertNotIn("--ask-become-pass", self.wrapper)
        self.assertIn(
            "extra_vars='{\"infisical_operator_bootstrap_approved\":true}'",
            self.wrapper,
        )
        extra_vars_match = re.search(r"^extra_vars='([^']+)'$", self.wrapper, re.MULTILINE)
        self.assertIsNotNone(extra_vars_match)
        self.assertIs(
            json.loads(extra_vars_match.group(1))["infisical_operator_bootstrap_approved"],
            True,
        )
        self.assertNotIn(
            "--extra-vars infisical_operator_bootstrap_approved=true",
            self.wrapper,
        )
        self.assertIn("become: false", PLAYBOOK.read_text())
        first = self.tasks[0]
        self.assertEqual("Reject externally supplied Infisical bootstrap internal variables", first["name"])
        self.assertIn("INTERNAL_VARIABLE_GUARD", first["ansible.builtin.assert"]["fail_msg"])
        self.assertIn("TASK_SELECTION_GUARD", self.plugin)
        self.assertIn("MUTATION_ARGUMENT_GUARD", self.plugin)
        self.assertIn("ENTRYPOINT_GUARD", self.plugin)
        self.assertIn('definition.get("kind") == "Secret"', self.plugin)
        self.assertEqual(40, len(re.findall(r"^    \(.+\): '[0-9a-f]{64}',?$", self.plugin, re.MULTILINE)))
        for args in (("other",), ("check", "--start-at-task")):
            result = subprocess.run([str(WRAPPER), *args], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(0, result.returncode)

    def test_action_only_invocation_is_rejected_before_kubernetes_access(self) -> None:
        env = os.environ.copy()
        token = "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            attestation = Path(directory) / "attestation"
            attestation.write_text(f"{token}:entrypoint\n")
            attestation.chmod(0o600)
            env.update(
                {
                    "CRISTEXWEB_INFISICAL_BOOTSTRAP_ENTRYPOINT": "v1",
                    "CRISTEXWEB_INFISICAL_BOOTSTRAP_TOKEN": token,
                    "CRISTEXWEB_INFISICAL_BOOTSTRAP_ATTESTATION_FILE": str(attestation),
                }
            )
            result = subprocess.run(
                [
                    str(ROOT / ".venv/bin/ansible-playbook"),
                    "-i",
                    "localhost,",
                    str(ACTION_ONLY_FIXTURE),
                    "--limit",
                    "localhost",
                ],
                cwd=ROOT / "ansible",
                env=env,
                text=True,
                capture_output=True,
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("ENTRYPOINT_GUARD", result.stdout + result.stderr)
        self.assertIn("canonical guarded role task source", result.stdout + result.stderr)
        self.assertNotIn("Failed to connect", result.stdout + result.stderr)

    def test_proxy_secret_action_only_is_rejected_before_kubernetes_access(self) -> None:
        env = os.environ.copy()
        token = "b" * 64
        with tempfile.TemporaryDirectory() as directory:
            attestation = Path(directory) / "attestation"
            attestation.write_text(f"{token}:entrypoint\n")
            attestation.chmod(0o600)
            env.update(
                {
                    "CRISTEXWEB_INFISICAL_PROXY_SECRET_ZERO_ENTRYPOINT": "v1",
                    "CRISTEXWEB_INFISICAL_PROXY_SECRET_ZERO_TOKEN": token,
                    "CRISTEXWEB_INFISICAL_PROXY_SECRET_ZERO_ATTESTATION_FILE": str(
                        attestation
                    ),
                }
            )
            result = subprocess.run(
                [
                    str(ROOT / ".venv/bin/ansible-playbook"),
                    "-i",
                    "localhost,",
                    str(PROXY_ACTION_ONLY_FIXTURE),
                    "--limit",
                    "localhost",
                ],
                cwd=ROOT / "ansible",
                env=env,
                text=True,
                capture_output=True,
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("ENTRYPOINT_GUARD", result.stdout + result.stderr)
        self.assertIn("canonical guarded role task source", result.stdout + result.stderr)
        self.assertNotIn("Failed to connect", result.stdout + result.stderr)

    def test_proxy_secret_zero_writer_is_guarded_and_recoverable(self) -> None:
        wrapper = PROXY_SECRET_WRAPPER.read_text()
        plugin = PROXY_SECRET_PLUGIN.read_text()
        tasks = PROXY_SECRET_TASKS.read_text()
        self.assertEqual(
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            PROXY_SECRET_WRAPPER.stat().st_mode
            & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
        )
        for required in (
            "age-keygen",
            "age -r",
            "drive-verified",
            "refusing Secret mutation before guarded host Drive transfer verification",
            "refusing a drive-verified marker not bound to the exact pending artifact",
            "security add-generic-password",
            "pending_marker",
            "completed_marker",
            "refusing mismatched age identity custody copies",
            "refusing recovery state without either age identity copy",
            "item.resources[0].data == item.item.data",
            "infisical_proxy_secret_zero_guarded_k8s",
            "--limit crtxweb",
        ):
            self.assertIn(required, wrapper + plugin + tasks)
        self.assertNotIn("--ask-become-pass", wrapper)
        self.assertNotIn("add-generic-password -U", wrapper)
        self.assertLess(
            wrapper.index("security find-generic-password"),
            wrapper.index("age-keygen -o"),
        )
        self.assertLess(wrapper.index("trap cleanup"), wrapper.index("openssl req -x509"))
        self.assertLess(wrapper.index("drive_verified_marker"), wrapper.index("secret-vars.yml"))
        self.assertNotIn("rclone", wrapper)
        self.assertNotIn("remote-copy", wrapper)
        self.assertIn("become: false", PROXY_SECRET_PLAYBOOK.read_text())
        for required in (
            "ENTRYPOINT_GUARD",
            "TASK_SELECTION_GUARD",
            "MUTATION_ARGUMENT_GUARD",
            '"infisical-egress-proxy-tls"',
            '"infisical-egress-proxy-auth"',
            '"infisical-egress-proxy-client"',
            "map(attribute='metadata.name') | list | unique | length == 3",
            "Refuse foreign proxy Secrets before first bootstrap or resume",
        ):
            self.assertIn(required, plugin + tasks)
        for args in ((), ("check",), ("apply", "--tags")):
            result = subprocess.run(
                [str(PROXY_SECRET_WRAPPER), *args],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(0, result.returncode)

    def test_role_requires_proxy_secret_metadata_before_mutation(self) -> None:
        secret_query_index = next(i for i, task in enumerate(self.tasks) if task["name"] == "Query exact proxy bootstrap Secret metadata")
        crd_apply_index = next(i for i, task in enumerate(self.tasks) if task["name"] == "Reconcile only the six approved Infisical CRDs")
        self.assertLess(secret_query_index, crd_apply_index)
        secret_assert = self.task("Require precreated exact proxy bootstrap Secret keys")
        self.assertTrue(secret_assert.get("no_log"))
        self.assertIn("Values must be created", secret_assert["ansible.builtin.assert"]["fail_msg"])
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(
            {
                "infisical-egress-proxy-tls": ["ca.crt", "tls.crt", "tls.key"],
                "infisical-egress-proxy-auth": ["users"],
                "infisical-egress-proxy-client": ["proxy-url"],
            },
            defaults["infisical_operator_bootstrap_proxy_secret_contract"],
        )

    def test_kubernetes_namespace_source_closure_is_unchanged(self) -> None:
        kubernetes = ROOT / "kubernetes"
        self.assertEqual(
            {
                "platform/namespaces/argocd.yaml",
                "platform/namespaces/platform-edge.yaml",
                "platform/namespaces/shared-services.yaml",
                "applications/namespaces/cristexhub-dev.yaml",
            },
            {str(path.relative_to(kubernetes)) for path in kubernetes.rglob("*") if path.is_file()},
        )

    def test_source_contains_no_secret_value_material(self) -> None:
        text = "\n".join(path.read_text() for path in COMPONENT.rglob("*") if path.is_file())
        for forbidden in (
            "BEGIN PRIVATE KEY",
            "clientSecret:",
            "clientId:",
            "stringData:",
            "data:\n  proxy-url:",
            "kind: Secret",
            "cristexhub-prod",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
