from __future__ import annotations

import ast
import base64
import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/argocd"
DEFAULTS = ROOT / "ansible/roles/argocd_bootstrap/defaults/main.yml"
TASKS = ROOT / "ansible/roles/argocd_bootstrap/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/argocd_guarded_k8s.py"
RUNBOOK = ROOT / "runbooks/argocd-hardened-design.md"
ARGO_IMAGE = "quay.io/argoproj/argocd@sha256:521d6b62ecd0434c9cc6e9242a74f0e1137bb8fc0026b2c483ea88f3f17e725d"
REDIS_IMAGE = "docker.io/library/redis@sha256:c64af41b8fc06a2d9b8fde812dd781aa157bed6fcf8ae1656ad4e79f3f9fc9b1"


class ArgoCdHardenedDesignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = sorted(
            path
            for directory in ("crds", "config", "runtime", "rbac", "network")
            for path in (COMPONENT / directory).glob("*.yaml")
        )
        cls.objects = [yaml.safe_load(path.read_text()) for path in cls.paths]
        cls.by_identity = {
            (obj["apiVersion"], obj["kind"], obj["metadata"].get("namespace", ""), obj["metadata"]["name"]): obj
            for obj in cls.objects
        }

    def test_exact_object_inventory_and_hash_ledger(self) -> None:
        self.assertEqual(32, len(self.paths))
        self.assertEqual(32, len(self.by_identity))
        ledger = {}
        for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines():
            digest, relative = line.split("  ", 1)
            ledger[relative] = digest
        self.assertEqual({str(p.relative_to(COMPONENT)) for p in self.paths}, set(ledger))
        for path in self.paths:
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), ledger[str(path.relative_to(COMPONENT))])
        plugin_text = PLUGIN.read_text()
        literal = plugin_text.split("_EXPECTED_OBJECT_HASHES = ", 1)[1].split("\n_EXPECTED_ARGUMENT_KEYS", 1)[0]
        plugin_hashes = ast.literal_eval(literal)
        expected = {}
        for identity, obj in self.by_identity.items():
            payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
            expected[identity] = hashlib.sha256(payload).hexdigest()
        self.assertEqual(expected, plugin_hashes)
        defaults = yaml.safe_load(DEFAULTS.read_text())
        expected_paths = {str(path.relative_to(COMPONENT)) for path in self.paths}
        configured_paths = {
            path.split("/ansible/files/components/argocd/", 1)[1]
            for path in defaults["argocd_bootstrap_manifest_paths"]
        }
        self.assertEqual(32, defaults["argocd_bootstrap_object_count"])
        self.assertEqual(expected_paths, configured_paths)
        configured_hashes = {
            entry["path"].split("/ansible/files/components/argocd/", 1)[1]: entry["sha256"]
            for entry in defaults["argocd_bootstrap_expected_hashes"]
        }
        self.assertEqual(ledger, configured_hashes)
        identity_keys = sorted("|".join(identity) for identity in self.by_identity)
        identity_digest = hashlib.sha256("\n".join(identity_keys).encode()).hexdigest()
        self.assertEqual("bb81e0babfa314a91e52479e71d778b79c81df77bf5b74a9f2cb1bf08d692b81", identity_digest)
        self.assertIn(identity_digest, plugin_text)

    def test_exact_minimal_kind_closure(self) -> None:
        counts = {}
        for obj in self.objects:
            counts[obj["kind"]] = counts.get(obj["kind"], 0) + 1
        self.assertEqual({"CustomResourceDefinition": 3, "AppProject": 1, "ConfigMap": 7, "ServiceAccount": 4, "Role": 2, "RoleBinding": 2, "NetworkPolicy": 6, "Service": 3, "Deployment": 3, "StatefulSet": 1}, counts)
        forbidden = {"Secret", "Application", "ApplicationSet", "ClusterRole", "ClusterRoleBinding", "Ingress", "Job", "PersistentVolumeClaim", "ServiceMonitor"}
        self.assertFalse(forbidden & set(counts))
        self.assertFalse(any("applicationset-controller" in obj["metadata"]["name"] for obj in self.objects))

    def test_three_chart_crds_and_vendored_source_mapping(self) -> None:
        crds = {obj["metadata"]["name"] for obj in self.objects if obj["kind"] == "CustomResourceDefinition"}
        self.assertEqual({"applications.argoproj.io", "applicationsets.argoproj.io", "appprojects.argoproj.io"}, crds)
        mapping = yaml.safe_load((COMPONENT / "SOURCE-MAPPING.yml").read_text())
        self.assertEqual("10.3.0", mapping["chart"]["version"])
        self.assertEqual("v3.5.0", mapping["chart"]["applicationVersion"])
        self.assertFalse(mapping["chart"]["runtimeUsesHelm"])
        self.assertEqual(crds, {entry["name"] for entry in mapping["promotedCrds"]})
        identities = {"|".join(identity) for identity in self.by_identity}
        promoted = set(mapping["chartRenderedIdentitiesPromoted"])
        custom = set(mapping["customHardenedIdentities"])
        omitted = set(mapping["intentionallyOmittedRenderedIdentities"])
        self.assertEqual(24, len(promoted))
        self.assertEqual(8, len(custom))
        self.assertEqual(11, len(omitted))
        self.assertFalse(promoted & custom)
        self.assertFalse((promoted | custom) & omitted)
        self.assertEqual(identities, promoted | custom)
        self.assertEqual(35, len(promoted | omitted))
        vendor = ROOT / "ansible/files/vendor/argocd/10.3.0/argo-cd-10.3.0.tgz"
        self.assertEqual("d08882d22d0c76e3174e005cc09abe300c70ba556aec76725a4410d172b9c1f3", hashlib.sha256(vendor.read_bytes()).hexdigest())
        comparator = (ROOT / "tests/validate_argocd_chart_render.sh").read_text()
        for required in ("v3.19.0", "argo-cd-10.3.0.tgz", "CHART-RENDER-EVIDENCE-VALUES.yaml", "SOURCE-MAPPING.yml", "len(render) == len(rendered) == 35"):
            self.assertIn(required, comparator)
        for forbidden in ("curl ", "wget ", "helm repo", "helm pull"):
            self.assertNotIn(forbidden, comparator)

    def test_default_project_is_precreated_deny_all(self) -> None:
        project = self.by_identity[("argoproj.io/v1alpha1", "AppProject", "argocd", "default")]
        spec = project["spec"]
        self.assertEqual([], spec["sourceRepos"])
        self.assertEqual([], spec["destinations"])
        self.assertEqual([], spec["clusterResourceWhitelist"])
        self.assertEqual([], spec["namespaceResourceWhitelist"])
        self.assertEqual([{"group": "*", "kind": "*"}], spec["clusterResourceBlacklist"])
        self.assertEqual([{"group": "*", "kind": "*"}], spec["namespaceResourceBlacklist"])
        params = self.by_identity[("v1", "ConfigMap", "argocd", "argocd-cmd-params-cm")]
        self.assertNotIn("application.namespaces", params["data"])
        server_role = self.by_identity[("rbac.authorization.k8s.io/v1", "Role", "argocd", "argocd-server")]
        project_rules = [rule for rule in server_role["rules"] if "appprojects" in rule["resources"]]
        self.assertEqual(1, len(project_rules))
        self.assertFalse({"create", "update", "patch", "delete"} & set(project_rules[0]["verbs"]))
        tasks_text = TASKS.read_text()
        plugin_text = PLUGIN.read_text()
        for required in (
            "Query AppProject API prerequisite pre-state",
            "item.kind != 'AppProject' or not ansible_check_mode",
            "type: Established",
            "deferred_custom_resource_count",
        ):
            self.assertIn(required, tasks_text)
        self.assertIn("_EXPECTED_CRD_WAIT_CONDITION", plugin_text)
        self.assertIn('args.get("wait") is True', plugin_text)

    def test_images_resources_and_container_hardening(self) -> None:
        workloads = [o for o in self.objects if o["kind"] in {"Deployment", "StatefulSet"}]
        self.assertEqual(4, len(workloads))
        images = []
        for workload in workloads:
            pod = workload["spec"]["template"]["spec"]
            self.assertTrue(pod["securityContext"]["runAsNonRoot"])
            self.assertEqual("RuntimeDefault", pod["securityContext"]["seccompProfile"]["type"])
            for container in pod.get("initContainers", []) + pod["containers"]:
                images.append(container["image"])
                security = container["securityContext"]
                self.assertFalse(security["allowPrivilegeEscalation"])
                self.assertEqual(["ALL"], security["capabilities"]["drop"])
                self.assertTrue(security["readOnlyRootFilesystem"])
                self.assertIn("requests", container["resources"])
                self.assertIn("limits", container["resources"])
        self.assertEqual({ARGO_IMAGE, REDIS_IMAGE}, set(images))

    def test_tokenless_repo_and_redis_and_exact_secret_references(self) -> None:
        for name in ("argocd-repo-server", "argocd-redis"):
            workload = next(o for o in self.objects if o["metadata"]["name"] == name and o["kind"] == "Deployment")
            self.assertFalse(workload["spec"]["template"]["spec"]["automountServiceAccountToken"])
        redis = next(o for o in self.objects if o["kind"] == "Deployment" and o["metadata"]["name"] == "argocd-redis")
        self.assertEqual("argocd-redis", redis["spec"]["template"]["spec"]["serviceAccountName"])
        refs = []
        for workload in [o for o in self.objects if o["kind"] in {"Deployment", "StatefulSet"}]:
            for container in workload["spec"]["template"]["spec"]["containers"]:
                for env in container.get("env", []):
                    ref = env.get("valueFrom", {}).get("secretKeyRef")
                    if ref:
                        refs.append((ref["name"], ref["key"]))
        self.assertEqual({("argocd-redis", "auth")}, set(refs))
        self.assertNotIn("kind: Secret", "\n".join(p.read_text() for p in self.paths))

    def test_services_are_private_clusterip_only(self) -> None:
        services = [o for o in self.objects if o["kind"] == "Service"]
        self.assertEqual({"argocd-server", "argocd-repo-server", "argocd-redis"}, {o["metadata"]["name"] for o in services})
        for service in services:
            self.assertEqual("ClusterIP", service["spec"]["type"])
            for forbidden in ("externalIPs", "externalName", "loadBalancerIP"):
                self.assertNotIn(forbidden, service["spec"])
            self.assertFalse(any(port.get("nodePort") for port in service["spec"]["ports"]))

    def test_server_tls_secret_is_api_loaded_and_ca_configmap_is_distinct(self) -> None:
        self.assertEqual(32, len(self.paths))
        server = self.by_identity[("apps/v1", "Deployment", "argocd", "argocd-server")]
        server_text = json.dumps(server, sort_keys=True)
        self.assertNotIn("argocd-server-tls", server_text)
        pod_spec = server["spec"]["template"]["spec"]
        tls_mounts = [
            mount
            for container in pod_spec["containers"]
            for mount in container.get("volumeMounts", [])
            if mount["name"] == "tls-certs"
        ]
        self.assertEqual([{"mountPath": "/app/config/tls", "name": "tls-certs"}], tls_mounts)
        tls_volumes = [volume for volume in pod_spec["volumes"] if volume["name"] == "tls-certs"]
        self.assertEqual(1, len(tls_volumes))
        self.assertEqual({"name": "argocd-tls-certs-cm"}, tls_volumes[0]["configMap"])
        self.assertNotIn("secret", tls_volumes[0])

        server_role = self.by_identity[("rbac.authorization.k8s.io/v1", "Role", "argocd", "argocd-server")]
        secret_rules = [rule for rule in server_role["rules"] if "secrets" in rule["resources"]]
        self.assertEqual(1, len(secret_rules))
        self.assertEqual({"get", "list", "watch"}, set(secret_rules[0]["verbs"]))

        runbook = RUNBOOK.read_text()
        for required in (
            "API-based dynamic Secret consumption",
            "externalServerTLSSecretName",
            "GetSecretByName",
            "loadTLSCertificate",
            "resourceVersion",
            "repository trust CA",
            "https://github.com/argoproj/argo-cd/blob/v3.5.0/util/settings/settings.go",
            "https://github.com/argoproj/argo-cd/blob/v3.5.0/util/settings/settings_test.go",
        ):
            self.assertIn(required, runbook)

    def test_default_deny_and_exact_component_flows(self) -> None:
        policies = {o["metadata"]["name"]: o for o in self.objects if o["kind"] == "NetworkPolicy"}
        self.assertEqual({"argocd-default-deny", "argocd-controller-egress", "argocd-server-egress", "argocd-repo-server-egress", "argocd-repo-server-ingress", "argocd-redis-ingress"}, set(policies))
        self.assertEqual({}, policies["argocd-default-deny"]["spec"]["podSelector"])
        self.assertEqual(["Ingress", "Egress"], policies["argocd-default-deny"]["spec"]["policyTypes"])
        self.assertNotIn("egress", policies["argocd-redis-ingress"]["spec"])
        combined = json.dumps(policies)
        for port in (53, 443, 6443, 8081, 6379):
            self.assertIn(f'"port": {port}', combined)
        for metrics in (8082, 8083, 8084):
            self.assertNotIn(f'"port": {metrics}', combined)

    def test_namespaced_rbac_has_no_broad_or_destructive_privilege(self) -> None:
        roles = [o for o in self.objects if o["kind"] == "Role"]
        self.assertEqual(2, len(roles))
        forbidden_verbs = {"*", "delete", "deletecollection", "escalate", "bind", "impersonate"}
        forbidden_resources = {"namespaces", "customresourcedefinitions", "clusterroles", "clusterrolebindings", "serviceaccounts/token"}
        for role in roles:
            for rule in role["rules"]:
                self.assertFalse(forbidden_verbs & set(rule["verbs"]))
                self.assertFalse(forbidden_resources & set(rule["resources"]))
                self.assertNotIn("*", rule.get("apiGroups", []))
                self.assertNotIn("*", rule["resources"])

    def test_bootstrap_preflight_secret_and_foreign_object_guards(self) -> None:
        text = TASKS.read_text() + DEFAULTS.read_text()
        for required in ("argocd-secret", "admin.password", "admin.passwordMtime", "server.secretkey", "argocd-redis", "argocd-server-tls", "argocd-initial-admin-secret", "app.kubernetes.io/managed-by') == 'infisical'", "app.kubernetes.io/part-of') == 'argocd'", "cristex.io/value-owner') == 'infisical-cloud'", "Refusing silent adoption of a foreign Argo CD object", "root:k3s-admin mode-0640", "identity_set_sha256"):
            self.assertIn(required, text)
        self.assertIn("state: present", text)
        self.assertNotIn("state: absent", text)

    def test_secret_value_contract_is_cryptographically_enforced(self) -> None:
        plugin_path = ROOT / "ansible/plugins/action/argocd_secret_contract.py"
        module_spec = importlib.util.spec_from_file_location("argocd_secret_contract", plugin_path)
        self.assertIsNotNone(module_spec)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        now = datetime(2026, 8, 10, tzinfo=timezone.utc)
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "CristexWeb Argo CA")])
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(ca_name)
            .issuer_name(ca_name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=365))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .sign(ca_key, hashes.SHA256())
        )
        leaf_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        leaf_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "argocd-server.argocd.svc")])
        leaf_cert = (
            x509.CertificateBuilder()
            .subject_name(leaf_name)
            .issuer_name(ca_name)
            .public_key(leaf_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=30))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName("argocd-server.argocd.svc"), x509.DNSName("localhost")]), critical=False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(ca_key, hashes.SHA256())
        )

        def encoded(value: bytes) -> str:
            return base64.b64encode(value).decode()

        results = [
            {"resources": [{"metadata": {"name": "argocd-secret"}, "data": {
                "admin.password": encoded(("$2b$12$" + "A" * 53).encode()),
                "admin.passwordMtime": encoded(b"2026-08-09T00:00:00Z"),
                "server.secretkey": encoded(b"s" * 32),
            }}]},
            {"resources": [{"metadata": {"name": "argocd-redis"}, "data": {"auth": encoded(b"r" * 32)}}]},
            {"resources": [{"metadata": {"name": "argocd-server-tls"}, "data": {
                "ca.crt": encoded(ca_cert.public_bytes(serialization.Encoding.PEM)),
                "tls.crt": encoded(leaf_cert.public_bytes(serialization.Encoding.PEM)),
                "tls.key": encoded(leaf_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())),
            }}]},
        ]
        module.validate_secret_results(results, now=now)
        invalid_cost = copy.deepcopy(results)
        invalid_cost[0]["resources"][0]["data"]["admin.password"] = encoded(("$2b$31$" + "A" * 53).encode())
        with self.assertRaises(ValueError):
            module.validate_secret_results(invalid_cost, now=now)
        noncanonical_time = copy.deepcopy(results)
        noncanonical_time[0]["resources"][0]["data"]["admin.passwordMtime"] = encoded(b"2026-08-09T0:0:0Z")
        with self.assertRaises(ValueError):
            module.validate_secret_results(noncanonical_time, now=now)
        invalid_time = copy.deepcopy(results)
        invalid_time[0]["resources"][0]["data"]["admin.passwordMtime"] = encoded(b"2026-99-99Tgarbage")
        with self.assertRaises(ValueError):
            module.validate_secret_results(invalid_time, now=now)
        wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        invalid_key = copy.deepcopy(results)
        invalid_key[2]["resources"][0]["data"]["tls.key"] = encoded(wrong_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        with self.assertRaises(ValueError):
            module.validate_secret_results(invalid_key, now=now)

        def signed_leaf(dns_names: list[str], *, is_ca: bool) -> x509.Certificate:
            return (
                x509.CertificateBuilder()
                .subject_name(leaf_name)
                .issuer_name(ca_name)
                .public_key(leaf_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(days=1))
                .not_valid_after(now + timedelta(days=30))
                .add_extension(
                    x509.SubjectAlternativeName(
                        [x509.DNSName(name) for name in dns_names]
                    ),
                    critical=False,
                )
                .add_extension(
                    x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
                    critical=False,
                )
                .add_extension(
                    x509.BasicConstraints(ca=is_ca, path_length=0 if is_ca else None),
                    critical=True,
                )
                .sign(ca_key, hashes.SHA256())
            )

        for invalid_leaf in (
            signed_leaf(
                ["argocd-server.argocd.svc", "localhost", "attacker.invalid"],
                is_ca=False,
            ),
            signed_leaf(
                ["argocd-server.argocd.svc", "localhost"],
                is_ca=True,
            ),
        ):
            invalid_tls = copy.deepcopy(results)
            invalid_tls[2]["resources"][0]["data"]["tls.crt"] = encoded(
                invalid_leaf.public_bytes(serialization.Encoding.PEM)
            )
            with self.assertRaises(ValueError):
                module.validate_secret_results(invalid_tls, now=now)

    def test_wrapper_and_action_are_non_passthrough_and_hash_bound(self) -> None:
        wrapper = (ROOT / "ansible/bin/bootstrap-argocd").read_text()
        plugin = PLUGIN.read_text()
        for required in ("check|apply", "/usr/bin/env -i", "--diff", "--limit crtxweb", "CRISTEXWEB_ARGOCD_BOOTSTRAP_ATTESTATION_FILE"):
            self.assertIn(required, wrapper)
        approval = re.search(r"--extra-vars '(\{[^']+\})'", wrapper)
        self.assertIsNotNone(approval)
        approval_json = approval.group(1)
        self.assertIs(json.loads(approval_json)["argocd_bootstrap_approved"], True)
        with tempfile.TemporaryDirectory() as directory:
            playbook = Path(directory) / "approval.yml"
            playbook.write_text(
                "---\n- hosts: localhost\n  gather_facts: false\n  tasks:\n"
                "    - ansible.builtin.assert:\n        that:\n"
                "          - argocd_bootstrap_approved is sameas true\n"
            )
            result = subprocess.run(
                [str(ROOT / ".venv/bin/ansible-playbook"), "-i", "localhost,", "-c", "local", str(playbook), "--extra-vars", approval_json],
                cwd=ROOT / "ansible",
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for forbidden in ("--tags", "--skip-tags", "--start-at-task", "--step", "--ask-become-pass"):
            self.assertNotIn(forbidden, wrapper)
        for required in ("_EXPECTED_OBJECT_HASHES", "_EXPECTED_TASK_SOURCE", "TASK_SELECTION_GUARD", "MUTATION_ARGUMENT_GUARD", "definition.get(\"kind\") == \"Secret\"", "prestate_count", "secret_count"):
            self.assertIn(required, plugin)

    def test_shell_guards_and_default_role_smoke_are_automated(self) -> None:
        for relative in (
            "tests/validate_argocd_clean_controller.sh",
            "tests/validate_argocd_role_defaults.sh",
            "tests/reject_argocd_task_start.sh",
        ):
            result = subprocess.run(
                [str(ROOT / relative)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        internal = subprocess.run(
            [
                str(ROOT / ".venv/bin/ansible-playbook"),
                "-i",
                "localhost,",
                str(ROOT / "tests/reject_argocd_internal_injection.yml"),
                "--extra-vars",
                '{"argocd_bootstrap_internal_manifests":[]}',
            ],
            cwd=ROOT / "ansible",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, internal.returncode, internal.stdout + internal.stderr)

    def test_valid_attestation_action_only_fails_before_kubernetes(self) -> None:
        token = "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            attestation = Path(directory) / "attestation"
            attestation.write_text(f"{token}:entrypoint\n")
            os.chmod(attestation, 0o600)
            env = os.environ.copy()
            env.update({"ANSIBLE_CONFIG": str(ROOT / "ansible/ansible.cfg"), "CRISTEXWEB_ARGOCD_BOOTSTRAP_ENTRYPOINT": "v1", "CRISTEXWEB_ARGOCD_BOOTSTRAP_TOKEN": token, "CRISTEXWEB_ARGOCD_BOOTSTRAP_ATTESTATION_FILE": str(attestation)})
            result = subprocess.run([str(ROOT / ".venv/bin/ansible-playbook"), "-i", "localhost,", str(ROOT / "tests/reject_argocd_action_only.yml")], cwd=ROOT / "ansible", env=env, capture_output=True, text=True, check=False)
        self.assertNotEqual(0, result.returncode)
        output = result.stdout + result.stderr
        self.assertIn("ENTRYPOINT_GUARD", output)
        self.assertIn("canonical guarded role task source", output)
        self.assertNotIn("Failed to connect", output)

    def test_documentation_records_deployable_source_and_runtime_block(self) -> None:
        text = " ".join(RUNBOOK.read_text().split())
        for required in ("GUARDED PRIVATE BOOTSTRAP SOURCE READY", "ApplicationSet runtime is absent", "exact 32-object closure", "Chart `10.3.0`", "Argo CD `v3.5.0`", "runtime remains **NOT RUN/BLOCKED**", "https://github.com/devraider/cristexweb.git", "develop", "port-only", "Infisical-owned"):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
