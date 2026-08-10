from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
COMPONENT = ANSIBLE / "files/components/postgresql"
DEFAULTS = ANSIBLE / "roles/postgresql_bootstrap/defaults/main.yml"
TASKS = ANSIBLE / "roles/postgresql_bootstrap/tasks/main.yml"
PLUGIN = ANSIBLE / "plugins/action/postgresql_guarded_k8s.py"
WRAPPER = ANSIBLE / "bin/bootstrap-postgresql"
DIGEST = "docker.io/library/postgres@sha256:dbbeb22a65db2503050cdbbe5e78f017478f10a1002a226463f049dbb017e99b"


class PostgreSQLBootstrapContractTests(unittest.TestCase):
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
        cls.statefulset = cls.by_identity[
            ("apps/v1", "StatefulSet", "shared-services", "shared-postgresql")
        ]

    def test_exact_six_object_hash_bound_closure(self) -> None:
        identities = {
            ("v1", "ConfigMap", "shared-services", "shared-postgresql-pg-hba"),
            ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "shared-postgresql-default-deny"),
            ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "shared-postgresql-ingress"),
            ("v1", "ServiceAccount", "shared-services", "shared-postgresql"),
            ("v1", "Service", "shared-services", "shared-postgresql"),
            ("apps/v1", "StatefulSet", "shared-services", "shared-postgresql"),
        }
        self.assertEqual(identities, set(self.by_identity))
        ledger = {}
        for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines():
            digest, relative = line.split("  ", 1)
            ledger[relative] = digest
        self.assertEqual(
            {str(path.relative_to(COMPONENT)) for path in self.paths}, set(ledger)
        )
        for path in self.paths:
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                ledger[str(path.relative_to(COMPONENT))],
            )
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(ledger, defaults["postgresql_bootstrap_expected_hashes"])
        plugin_text = PLUGIN.read_text()
        literal = plugin_text.split("_EXPECTED_OBJECT_HASHES = ", 1)[1].split(
            "\n_EXPECTED_ARGUMENT_KEYS", 1
        )[0]
        plugin_hashes = ast.literal_eval(literal)
        expected = {}
        for identity, obj in self.by_identity.items():
            payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
            expected[identity] = hashlib.sha256(payload).hexdigest()
        self.assertEqual(expected, plugin_hashes)

    def test_image_security_storage_and_retention(self) -> None:
        spec = self.statefulset["spec"]
        self.assertEqual("shared-postgresql", spec["serviceName"])
        self.assertEqual(
            {"whenDeleted": "Retain", "whenScaled": "Retain"},
            spec["persistentVolumeClaimRetentionPolicy"],
        )
        pod = spec["template"]["spec"]
        self.assertEqual("shared-postgresql", pod["serviceAccountName"])
        self.assertFalse(pod["automountServiceAccountToken"])
        self.assertEqual(999, pod["securityContext"]["runAsUser"])
        self.assertEqual(999, pod["securityContext"]["runAsGroup"])
        self.assertEqual(999, pod["securityContext"]["fsGroup"])
        container = pod["containers"][0]
        self.assertEqual(DIGEST, container["image"])
        self.assertTrue(container["securityContext"]["readOnlyRootFilesystem"])
        self.assertEqual(["ALL"], container["securityContext"]["capabilities"]["drop"])
        claim = spec["volumeClaimTemplates"][0]
        self.assertEqual("ansible", claim["metadata"]["labels"]["app.kubernetes.io/managed-by"])
        self.assertEqual("local-path", claim["spec"]["storageClassName"])
        self.assertEqual("40Gi", claim["spec"]["resources"]["requests"]["storage"])

    def test_tls_scram_hba_and_value_free_secret_references(self) -> None:
        hba = self.by_identity[
            ("v1", "ConfigMap", "shared-services", "shared-postgresql-pg-hba")
        ]["data"]["pg_hba.conf"]
        for line in (
            "local all all scram-sha-256",
            "hostssl all all 127.0.0.1/32 scram-sha-256",
            "hostssl all all ::1/128 scram-sha-256",
            "hostssl all all 10.42.0.0/16 scram-sha-256",
            "hostnossl all all 0.0.0.0/0 reject",
        ):
            self.assertIn(line, hba)
        self.assertNotIn(" trust", hba)
        pod = self.statefulset["spec"]["template"]["spec"]
        container = pod["containers"][0]
        env = {item["name"]: item["value"] for item in container["env"]}
        self.assertEqual("/etc/postgresql/admin/username", env["POSTGRES_USER_FILE"])
        self.assertEqual("/etc/postgresql/admin/password", env["POSTGRES_PASSWORD_FILE"])
        for expected in (
            "ssl=on",
            "ssl_min_protocol_version=TLSv1.2",
            "ssl_cert_file=/tls/tls.crt",
            "ssl_key_file=/tls/tls.key",
            "hba_file=/etc/postgresql/pg_hba.conf",
            "password_encryption=scram-sha-256",
        ):
            self.assertIn(expected, container["args"])
        secret_volumes = {
            volume["name"]: volume["secret"]["secretName"]
            for volume in pod["volumes"]
            if "secret" in volume
        }
        self.assertEqual(
            {
                "shared-postgresql-admin": "shared-postgresql-admin",
                "shared-postgresql-tls-input": "shared-postgresql-tls",
            },
            secret_volumes,
        )
        init = pod["initContainers"][0]
        command = " ".join(init["command"] + init["args"])
        self.assertIn("chmod 0600 /tls/tls.key", command)
        self.assertIn("999:600", command)

    def test_probes_authenticate_verify_tls_and_reject_plaintext(self) -> None:
        container = self.statefulset["spec"]["template"]["spec"]["containers"][0]
        for name in ("startupProbe", "readinessProbe", "livenessProbe"):
            text = " ".join(container[name]["exec"]["command"])
            self.assertIn("PGSSLMODE=verify-full", text)
            self.assertIn("PGSSLROOTCERT=/tls/ca.crt", text)
            self.assertIn("psql -h localhost", text)
            self.assertIn("SELECT ssl FROM pg_stat_ssl", text)
            self.assertIn(")\" = 't'", text)
            self.assertIn('PGPASSWORD="$(cat /etc/postgresql/admin/password)"', text)
            self.assertIn("PGSSLMODE=disable", text)
            self.assertIn("then exit 13; fi", text)
            self.assertNotIn("--password", text)

    def test_service_and_network_policy_are_private(self) -> None:
        service = self.by_identity[
            ("v1", "Service", "shared-services", "shared-postgresql")
        ]
        self.assertEqual("ClusterIP", service["spec"]["type"])
        self.assertEqual(5432, service["spec"]["ports"][0]["port"])
        self.assertEqual("postgresql", service["spec"]["ports"][0]["targetPort"])
        self.assertEqual(
            {
                "app.kubernetes.io/name": "shared-postgresql",
                "app.kubernetes.io/part-of": "cristex-platform",
            },
            service["spec"]["selector"],
        )
        self.assertNotIn("nodePort", service["spec"]["ports"][0])
        self.assertNotIn("externalIPs", service["spec"])
        deny = self.by_identity[
            ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "shared-postgresql-default-deny")
        ]["spec"]
        self.assertEqual({"Ingress", "Egress"}, set(deny["policyTypes"]))
        ingress = self.by_identity[
            ("networking.k8s.io/v1", "NetworkPolicy", "shared-services", "shared-postgresql-ingress")
        ]["spec"]["ingress"][0]
        self.assertEqual(5432, ingress["ports"][0]["port"])
        self.assertEqual(2, len(ingress["from"]))
        namespaced, keycloak = ingress["from"]
        values = namespaced["namespaceSelector"]["matchExpressions"][0]["values"]
        self.assertEqual(
            {
                "cristexhub-dev",
                "cristexhub-prod",
                "reactive-resume-dev",
                "reactive-resume-prod",
            },
            set(values),
        )
        self.assertNotIn("namespaceSelector", keycloak)
        self.assertEqual(
            {
                "app.kubernetes.io/name": "keycloak",
                "cristex.io/database-client": "shared-postgresql",
            },
            keycloak["podSelector"]["matchLabels"],
        )

    def test_guarded_entrypoint_and_readiness_contract(self) -> None:
        wrapper = WRAPPER.read_text()
        tasks = TASKS.read_text()
        plugin = PLUGIN.read_text()
        for required in ("check|apply", "/usr/bin/env -i", "--diff", "--limit crtxweb"):
            self.assertIn(required, wrapper)
        for required in (
            "stateful_database_secret_contract:",
            "storage_contract: true",
            "pvc_prestate_count",
            "identity_set_sha256",
            "Refuse unmodeled existing PostgreSQL StatefulSet workload drift",
            "Require exact PostgreSQL StatefulSet workload post-state",
            "postgresql_bootstrap_pvc_name == 'postgresql-data-shared-postgresql-0'",
            "spec.sessionAffinity == 'None'",
            "status.observedGeneration",
            "status.currentRevision",
            "Verify the bound PostgreSQL PV claim identity and provisioner",
            "pv.kubernetes.io/provisioned-by",
            "spec.dataSourceRef is not defined",
            "Verify the PostgreSQL Service remains private ClusterIP-only",
            "no_delete_path: true",
        ):
            self.assertIn(required, tasks)
        for required in (
            "_EXPECTED_OBJECT_HASHES",
            "TASK_SELECTION_GUARD",
            "MUTATION_ARGUMENT_GUARD",
            'definition.get("kind") in {"Secret", "PersistentVolumeClaim"}',
        ):
            self.assertIn(required, plugin)
        self.assertNotIn("state: absent", tasks)

    def test_negative_fixtures_fail_before_kubernetes(self) -> None:
        selection = subprocess.run(
            [str(ROOT / "tests/reject_postgresql_task_selection.sh")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, selection.returncode, selection.stdout + selection.stderr)
        internal = subprocess.run(
            [
                str(ROOT / ".venv/bin/ansible-playbook"),
                "-i",
                "localhost,",
                str(ROOT / "tests/reject_postgresql_internal_injection.yml"),
                "--extra-vars",
                '{"postgresql_bootstrap_internal_preflight_binding":"forged"}',
            ],
            cwd=ANSIBLE,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, internal.returncode)
        self.assertIn("INTERNAL_VARIABLE_GUARD", internal.stdout + internal.stderr)
        action_only = subprocess.run(
            [
                str(ROOT / ".venv/bin/ansible-playbook"),
                "-i",
                "localhost,",
                str(ROOT / "tests/reject_postgresql_action_only.yml"),
            ],
            cwd=ANSIBLE,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, action_only.returncode)
        output = action_only.stdout + action_only.stderr
        self.assertIn("ENTRYPOINT_GUARD", output)
        self.assertIn("canonical guarded role task source", output)
        self.assertNotIn("Failed to connect", output)


if __name__ == "__main__":
    unittest.main()
