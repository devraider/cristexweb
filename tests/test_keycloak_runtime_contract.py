from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/keycloak"
EXPECTED_IMAGE = (
    "ghcr.io/devraider/cristexhub/keycloak@sha256:"
    "c1c49aa925127c2a9277f9d0d6fffee888030a4c5710e8478c0a5b26ccbda0ac"
)
EXPECTED_HOSTNAME = "https://auth.cristex-soft.com"
EXPECTED_NAMESPACE = "shared-services"
EXPECTED_SOURCE_OBJECTS = 10


def _yaml_objects() -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for path in sorted(COMPONENT.rglob("*.yaml")):
        with path.open() as stream:
            for document in yaml.safe_load_all(stream):
                if isinstance(document, dict) and document.get("kind"):
                    objects.append(document)
    return objects


@unittest.skipUnless(COMPONENT.is_dir(), "Keycloak runtime source is not present yet")
class KeycloakRuntimeSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.objects = _yaml_objects()
        cls.by_kind = {}
        for obj in cls.objects:
            cls.by_kind.setdefault(obj["kind"], []).append(obj)

    def test_source_is_exactly_the_private_ten_object_closure(self) -> None:
        self.assertEqual(EXPECTED_SOURCE_OBJECTS, len(self.objects))
        self.assertEqual(1, len(self.by_kind.get("ServiceAccount", [])))
        self.assertEqual(1, len(self.by_kind.get("Service", [])))
        self.assertEqual(1, len(self.by_kind.get("Deployment", [])))
        self.assertEqual(6, len(self.by_kind.get("NetworkPolicy", [])))
        self.assertEqual(1, len(self.by_kind.get("ConfigMap", [])))
        self.assertEqual(
            {"ServiceAccount", "Service", "Deployment", "NetworkPolicy", "ConfigMap"},
            set(self.by_kind),
        )
        for obj in self.objects:
            self.assertEqual(EXPECTED_NAMESPACE, obj["metadata"]["namespace"])
            self.assertEqual("ansible", obj["metadata"]["labels"].get("app.kubernetes.io/managed-by"))

    def test_deployment_is_digest_pinned_production_start_and_private(self) -> None:
        deployment = self.by_kind["Deployment"][0]
        self.assertEqual("keycloak", deployment["metadata"]["name"])
        self.assertEqual(1, deployment["spec"]["replicas"])
        pod_spec = deployment["spec"]["template"]["spec"]
        self.assertFalse(pod_spec.get("automountServiceAccountToken", True))
        self.assertEqual([{"name": "keycloak-ghcr-pull"}], pod_spec["imagePullSecrets"])
        container = next(c for c in pod_spec["containers"] if c["name"] == "keycloak")
        self.assertEqual(EXPECTED_IMAGE, container["image"])
        self.assertNotIn("start-dev", " ".join(container.get("command", []) + container.get("args", [])))
        self.assertIn("start", container.get("command", []) + container.get("args", []))
        self.assertIn("--import-realm", container.get("args", []))
        realm = self.by_kind["ConfigMap"][0]
        self.assertEqual("keycloak-realm-cristexhub", realm["metadata"]["name"])
        self.assertTrue(realm["immutable"])
        import json
        realm_json = json.loads(realm["data"]["cristexhub-realm.json"])
        self.assertEqual("cristexhub", realm_json["realm"])
        self.assertTrue(realm_json["organizationsEnabled"])
        self.assertFalse(any(key in realm_json for key in ("users", "clients", "credentials")))
        self.assertEqual("keycloak", deployment["spec"]["selector"]["matchLabels"].get("app.kubernetes.io/name"))
        self.assertEqual(
            EXPECTED_HOSTNAME,
            next(e["value"] for e in container["env"] if e["name"] == "KC_HOSTNAME"),
        )
        self.assertEqual("xforwarded", next(e["value"] for e in container["env"] if e["name"] == "KC_PROXY_HEADERS"))
        env = {item["name"]: item.get("value") for item in container["env"]}
        self.assertEqual(
            "http://oidc-connect-proxy.shared-services.svc.cluster.local:3128",
            env["HTTPS_PROXY"],
        )
        self.assertEqual("localhost,127.0.0.1,.svc,.svc.cluster.local", env["NO_PROXY"])

    def test_postgres_tls_is_verify_full_and_ca_only(self) -> None:
        deployment = self.by_kind["Deployment"][0]
        container = next(c for c in deployment["spec"]["template"]["spec"]["containers"] if c["name"] == "keycloak")
        env = {item["name"]: item for item in container["env"]}
        self.assertEqual("postgres", env["KC_DB"]["value"])
        db_url = env["KC_DB_URL"]["value"]
        self.assertIn("jdbc:postgresql://shared-postgresql-rw.shared-services.svc:5432/keycloak", db_url)
        self.assertIn("sslmode=verify-full", db_url)
        self.assertIn("sslrootcert=/opt/keycloak/conf/postgresql-ca.crt", db_url)
        for key in ("KC_DB_USERNAME", "KC_DB_PASSWORD"):
            self.assertEqual("shared-postgresql-keycloak", env[key]["valueFrom"]["secretKeyRef"]["name"])
        self.assertEqual("username", env["KC_DB_USERNAME"]["valueFrom"]["secretKeyRef"]["key"])
        self.assertEqual("password", env["KC_DB_PASSWORD"]["valueFrom"]["secretKeyRef"]["key"])
        ca_volume = next(v for v in deployment["spec"]["template"]["spec"]["volumes"] if v["name"] == "postgresql-ca")
        self.assertEqual("shared-postgresql-ca", ca_volume["secret"]["secretName"])
        self.assertEqual(["ca.crt"], [item["key"] for item in ca_volume["secret"]["items"]])
        mount = next(m for m in container["volumeMounts"] if m["name"] == "postgresql-ca")
        self.assertTrue(mount["readOnly"])
        self.assertEqual("/opt/keycloak/conf/postgresql-ca.crt", mount["mountPath"])
        source = str(deployment)
        self.assertNotRegex(source, r"(?i)(ca\.key|tls\.key|POSTGRESQL_TLS_KEY)")

    def test_secret_refs_probes_resources_and_security_context_are_explicit(self) -> None:
        deployment = self.by_kind["Deployment"][0]
        pod_spec = deployment["spec"]["template"]["spec"]
        pod_security = pod_spec["securityContext"]
        self.assertTrue(pod_security["runAsNonRoot"])
        self.assertEqual("RuntimeDefault", pod_security["seccompProfile"]["type"])
        container = next(c for c in pod_spec["containers"] if c["name"] == "keycloak")
        security = container["securityContext"]
        self.assertFalse(security["allowPrivilegeEscalation"])
        self.assertEqual(["ALL"], security["capabilities"]["drop"])
        self.assertTrue(container["readinessProbe"]["httpGet"]["path"].endswith("/health/ready"))
        self.assertTrue(container["livenessProbe"]["httpGet"]["path"].endswith("/health/live"))
        self.assertEqual("management", container["readinessProbe"]["httpGet"]["port"])
        self.assertEqual("management", container["livenessProbe"]["httpGet"]["port"])
        self.assertEqual("management", container["startupProbe"]["httpGet"]["port"])
        self.assertIn("/health", container["startupProbe"]["httpGet"]["path"])
        for resource in ("requests", "limits"):
            self.assertTrue(container["resources"].get(resource, {}).get("cpu"))
            self.assertTrue(container["resources"].get(resource, {}).get("memory"))

    def test_service_and_network_policies_remain_private_without_ingress_or_pvc(self) -> None:
        service = self.by_kind["Service"][0]
        self.assertEqual("ClusterIP", service["spec"]["type"])
        self.assertEqual({8080}, {port["port"] for port in service["spec"]["ports"]})
        self.assertEqual("keycloak", service["spec"]["selector"].get("app.kubernetes.io/name"))
        policies = self.by_kind["NetworkPolicy"]
        self.assertTrue(any(not policy["spec"].get("ingress") and not policy["spec"].get("egress") for policy in policies))
        self.assertTrue(any("Ingress" in policy["spec"].get("policyTypes", []) for policy in policies))
        self.assertTrue(any("Egress" in policy["spec"].get("policyTypes", []) for policy in policies))
        self.assertTrue(any("kube-dns" in str(policy) or "k8s-app" in str(policy) for policy in policies))
        self.assertFalse(any(obj["kind"] in {"Ingress", "PersistentVolumeClaim", "Secret"} for obj in self.objects))


class KeycloakGuardConventionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = {
            "wrapper": ROOT / "ansible/bin/bootstrap-keycloak",
            "playbook": ROOT / "ansible/playbooks/bootstrap_keycloak.yml",
            "defaults": ROOT / "ansible/roles/keycloak_bootstrap/defaults/main.yml",
            "tasks": ROOT / "ansible/roles/keycloak_bootstrap/tasks/main.yml",
            "guard": ROOT / "ansible/plugins/action/keycloak_guarded_k8s.py",
        }
        cls.present = any(path.exists() for path in cls.paths.values())

    @unittest.skipUnless(
        (ROOT / "ansible/bin/bootstrap-keycloak").exists(),
        "Keycloak guarded workflow is not present yet",
    )
    def test_wrapper_playbook_role_and_action_guard_are_complete(self) -> None:
        for name, path in self.paths.items():
            self.assertTrue(path.is_file(), name)
        wrapper = self.paths["wrapper"].read_text()
        self.assertRegex(wrapper, r"usage=.*bootstrap-keycloak check\|apply")
        self.assertIn("--diff --limit crtxweb", wrapper)
        self.assertIn("--check", wrapper)
        self.assertIn("CRISTEXWEB_KEYCLOAK_BOOTSTRAP_ENTRYPOINT=v1", wrapper)
        self.assertIn("CRISTEXWEB_KEYCLOAK_BOOTSTRAP_ATTESTATION_FILE", wrapper)
        playbook = self.paths["playbook"].read_text()
        self.assertIn("hosts: crtxweb", playbook)
        self.assertIn("role: keycloak_bootstrap", playbook)
        guard = self.paths["guard"].read_text()
        self.assertIn("CRISTEXWEB_KEYCLOAK_BOOTSTRAP_ENTRYPOINT", guard)
        self.assertIn("TASK_SELECTION_GUARD", guard)
        self.assertIn("kubernetes.core.k8s", guard)
        self.assertIn("definition", guard)
        self.assertNotIn("state': 'absent", guard.lower())
        self.assertNotIn('state": "absent', guard.lower())


if __name__ == "__main__":
    unittest.main()
