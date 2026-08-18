from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/mongodb"
DEFAULTS = ROOT / "ansible/roles/mongodb_bootstrap/defaults/main.yml"
TASKS = ROOT / "ansible/roles/mongodb_bootstrap/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/mongodb_guarded_k8s.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-mongodb"
RUNBOOK = ROOT / "runbooks/shared-database-architecture.md"
DIGEST = "docker.io/library/mongo@sha256:b112b1c1e552ab2b5bf5935b5662e1d19347d68effa8f2595687a42abfac5df4"


class SharedMongoDbBootstrapContractTests(unittest.TestCase):
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

    def test_exact_object_inventory_and_hash_ledger(self) -> None:
        self.assertEqual(5, len(self.paths))
        self.assertEqual(5, len(self.by_identity))
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
        defaults = yaml.safe_load(DEFAULTS.read_text())
        configured_paths = {
            path.split("/ansible/files/components/mongodb/", 1)[1]
            for path in defaults["mongodb_bootstrap_manifest_paths"]
        }
        self.assertEqual(set(ledger), configured_paths)
        configured_hashes = defaults["mongodb_bootstrap_expected_hashes"]
        self.assertEqual(ledger, configured_hashes)
        identity_keys = sorted("|".join(identity) for identity in self.by_identity)
        identity_digest = hashlib.sha256("\n".join(identity_keys).encode()).hexdigest()
        self.assertEqual(
            "2dafb88dd68d2031c0e558a9c8b18b2ee5bdd6c6f7116163e222c7dbe71c470e",
            identity_digest,
        )
        self.assertIn(identity_digest, plugin_text)

    def test_standalone_statefulset_image_storage_and_resources(self) -> None:
        statefulset = self.by_identity[("apps/v1", "StatefulSet", "shared-services", "shared-mongodb")]
        spec = statefulset["spec"]
        self.assertEqual(1, spec["replicas"])
        self.assertEqual("shared-mongodb", spec["serviceName"])
        self.assertEqual(
            {"whenDeleted": "Retain", "whenScaled": "Retain"},
            spec["persistentVolumeClaimRetentionPolicy"],
        )
        container = spec["template"]["spec"]["containers"][0]
        self.assertEqual(DIGEST, container["image"])
        self.assertEqual(
            {"cpu": "500m", "memory": "1Gi"},
            container["resources"]["requests"],
        )
        self.assertEqual(
            {"cpu": "2", "memory": "3Gi"},
            container["resources"]["limits"],
        )
        pvc = spec["volumeClaimTemplates"][0]["spec"]
        self.assertEqual(["ReadWriteOnce"], pvc["accessModes"])
        self.assertEqual("local-path", pvc["storageClassName"])
        self.assertEqual("80Gi", pvc["resources"]["requests"]["storage"])
        self.assertEqual("Filesystem", pvc["volumeMode"])
        pod_spec = spec["template"]["spec"]
        self.assertEqual("shared-mongodb", pod_spec["serviceAccountName"])
        self.assertFalse(pod_spec["automountServiceAccountToken"])
        self.assertEqual(
            {"kubernetes.io/arch": "amd64", "kubernetes.io/os": "linux"},
            pod_spec["nodeSelector"],
        )
        pod_security = pod_spec["securityContext"]
        self.assertEqual(999, pod_security["runAsUser"])
        self.assertEqual(999, pod_security["runAsGroup"])
        self.assertEqual(999, pod_security["fsGroup"])
        self.assertEqual("OnRootMismatch", pod_security["fsGroupChangePolicy"])
        self.assertEqual("RuntimeDefault", pod_security["seccompProfile"]["type"])
        self.assertTrue(container["securityContext"]["runAsNonRoot"])
        self.assertEqual(999, container["securityContext"]["runAsUser"])
        self.assertEqual(999, container["securityContext"]["runAsGroup"])
        self.assertTrue(container["securityContext"]["readOnlyRootFilesystem"])
        self.assertFalse(container["securityContext"]["allowPrivilegeEscalation"])
        self.assertEqual(["ALL"], container["securityContext"]["capabilities"]["drop"])
        init = spec["template"]["spec"]["initContainers"][0]
        self.assertEqual(DIGEST, init["image"])
        self.assertEqual(999, init["securityContext"]["runAsUser"])
        self.assertEqual(999, init["securityContext"]["runAsGroup"])
        self.assertTrue(init["securityContext"]["readOnlyRootFilesystem"])
        init_command = " ".join(init["command"] + init["args"])
        self.assertIn("chmod 0400", init_command)
        self.assertIn("stat -c '%u:%a'", init_command)
        self.assertIn("999:400", init_command)
        self.assertIn("tls-source", init_command)
        self.assertIn("tls-runtime", init_command)
        self.assertEqual({"cpu": "500m", "memory": "1Gi"}, init["resources"]["requests"])
        self.assertEqual({"cpu": "2", "memory": "3Gi"}, init["resources"]["limits"])

    def test_auth_tls_references_final_arguments_and_probes(self) -> None:
        statefulset = self.by_identity[("apps/v1", "StatefulSet", "shared-services", "shared-mongodb")]
        pod = statefulset["spec"]["template"]["spec"]
        container = pod["containers"][0]
        self.assertEqual(
            {
                "MONGO_INITDB_ROOT_USERNAME": ("shared-mongodb-auth", "username"),
                "MONGO_INITDB_ROOT_PASSWORD": ("shared-mongodb-auth", "password"),
            },
            {
                env["name"]: (
                    env["valueFrom"]["secretKeyRef"]["name"],
                    env["valueFrom"]["secretKeyRef"]["key"],
                )
                for env in container["env"]
            },
        )
        secret_volumes = {
            volume["name"]: volume["secret"]["secretName"]
            for volume in pod["volumes"]
            if "secret" in volume
        }
        self.assertEqual(
            {"mongodb-auth": "shared-mongodb-auth", "mongodb-tls-source": "shared-mongodb-tls"},
            secret_volumes,
        )
        runtime_volume = next(volume for volume in pod["volumes"] if volume["name"] == "mongodb-tls-runtime")
        self.assertEqual({"medium": "Memory"}, runtime_volume["emptyDir"])
        main_mount_names = {mount["name"] for mount in container["volumeMounts"]}
        self.assertNotIn("mongodb-tls-source", main_mount_names)
        self.assertIn("mongodb-tls-runtime", main_mount_names)
        tls_source = next(volume for volume in pod["volumes"] if volume["name"] == "mongodb-tls-source")
        self.assertEqual(288, tls_source["secret"]["defaultMode"])
        args = container["args"]
        self.assertIn("mongod", args)
        self.assertIn("--auth", args)
        self.assertIn("--setParameter=authenticationMechanisms=SCRAM-SHA-256", args)
        self.assertIn("--tlsMode=requireTLS", args)
        self.assertIn("--tlsCertificateKeyFile=/etc/mongodb/tls/tls.pem", args)
        self.assertIn("--tlsCAFile=/etc/mongodb/tls/ca.crt", args)
        self.assertIn("--tlsAllowConnectionsWithoutCertificates", args)
        self.assertNotIn("--replSet", " ".join(args))
        for probe_name in ("startupProbe", "readinessProbe", "livenessProbe"):
            command = " ".join(container[probe_name]["exec"]["command"])
            self.assertIn("mongosh", command)
            self.assertIn("--tls", command)
            self.assertIn("--tlsCAFile=/etc/mongodb/tls/ca.crt", command)
            self.assertIn("process.env.MONGO_INITDB_ROOT_USERNAME", command)
            self.assertIn("process.env.MONGO_INITDB_ROOT_PASSWORD", command)
            self.assertIn("if mongosh --quiet --norc --host localhost", command)
            self.assertIn("then exit 13; fi", command)
            self.assertNotIn("--password", command)
        mounts = {mount["mountPath"]: mount["name"] for mount in container["volumeMounts"]}
        self.assertEqual("mongodb-configdb", mounts["/data/configdb"])
        configdb = next(volume for volume in pod["volumes"] if volume["name"] == "mongodb-configdb")
        self.assertEqual({}, configdb["emptyDir"])

    def test_private_service_and_exact_network_policy(self) -> None:
        service = self.by_identity[("v1", "Service", "shared-services", "shared-mongodb")]
        self.assertEqual("ClusterIP", service["spec"]["type"])
        self.assertEqual(27017, service["spec"]["ports"][0]["port"])
        self.assertEqual("mongodb", service["spec"]["ports"][0]["targetPort"])
        self.assertEqual(
            {
                "app.kubernetes.io/name": "shared-mongodb",
                "app.kubernetes.io/instance": "shared-mongodb",
            },
            service["spec"]["selector"],
        )
        self.assertNotIn("nodePort", service["spec"]["ports"][0])
        self.assertNotIn("externalIPs", service["spec"])
        policies = {
            obj["metadata"]["name"]: obj
            for obj in self.objects
            if obj["kind"] == "NetworkPolicy"
        }
        self.assertEqual(
            {"shared-mongodb-default-deny", "shared-mongodb-ingress"}, set(policies)
        )
        deny = policies["shared-mongodb-default-deny"]["spec"]
        self.assertEqual(["Ingress", "Egress"], deny["policyTypes"])
        ingress = policies["shared-mongodb-ingress"]["spec"]
        self.assertEqual(["Ingress"], ingress["policyTypes"])
        self.assertEqual(27017, ingress["ingress"][0]["ports"][0]["port"])
        self.assertEqual(2, len(ingress["ingress"][0]["from"]))
        for item in ingress["ingress"][0]["from"]:
            self.assertEqual("shared-mongodb", item["podSelector"]["matchLabels"]["cristex.io/database-client"])

    def test_no_secret_values_or_delete_path_and_temporary_tls_contract(self) -> None:
        all_source = "\n".join(path.read_text() for path in self.paths)
        self.assertNotIn("kind: Secret", all_source)
        self.assertNotIn("state: absent", TASKS.read_text())
        self.assertNotIn("kubectl", WRAPPER.read_text())
        runbook = " ".join(RUNBOOK.read_text().split())
        for required in (
            "standalone",
            "non-authoritative",
            "temporary loopback initialization",
            "allowTLS",
            "plaintext",
            "replica-set",
            "transaction",
            "Infisical-owned",
            "uid/gid `999`",
            "mode `0400`",
            "projected group-readable private key",
        ):
            self.assertIn(required, runbook)

    def test_wrapper_role_and_plugin_are_guarded(self) -> None:
        wrapper = WRAPPER.read_text()
        tasks = TASKS.read_text()
        plugin = PLUGIN.read_text()
        for required in (
            "check|apply",
            "/usr/bin/env -i",
            "--diff",
            "--limit crtxweb",
            "CRISTEXWEB_MONGODB_BOOTSTRAP_ATTESTATION_FILE",
            "mongodb_bootstrap_approved",
        ):
            self.assertIn(required, wrapper)
        for forbidden in ("--tags", "--skip-tags", "--start-at-task", "--step", "--ask-become-pass"):
            self.assertNotIn(forbidden, wrapper)
        self.assertIn("mongodb_bootstrap_internal_preflight_binding", tasks)
        self.assertIn("mongodb_bootstrap_internal_manifests", tasks)
        self.assertIn("storage_contract: true", tasks)
        self.assertIn("pvc_prestate_count", tasks)
        self.assertIn("Refuse unmodeled existing MongoDB StatefulSet workload drift", tasks)
        self.assertIn("Require exact MongoDB StatefulSet workload post-state", tasks)
        self.assertIn("mongodb_bootstrap_pvc_name == 'mongodb-data-shared-mongodb-0'", tasks)
        self.assertIn("spec.sessionAffinity == 'None'", tasks)
        self.assertIn("Wait for the generated retained MongoDB PVC", tasks)
        self.assertIn("Verify the bound MongoDB PV claim identity and provisioner", tasks)
        self.assertIn("pv.kubernetes.io/provisioned-by", tasks)
        self.assertIn("spec.dataSourceRef is not defined", tasks)
        self.assertIn("Wait for the exact MongoDB Pod Ready condition", tasks)
        self.assertIn("Verify the MongoDB Service remains private ClusterIP-only", tasks)
        self.assertIn("no_delete_path: true", tasks)
        self.assertNotIn("state: absent", tasks)
        for required in (
            "_EXPECTED_OBJECT_HASHES",
            "_EXPECTED_TASK_SOURCE",
            "TASK_SELECTION_GUARD",
            "MUTATION_ARGUMENT_GUARD",
            "binding.get('storage_contract') is True",
            "definition.get('kind') in {'Secret', 'PersistentVolumeClaim'}",
        ):
            self.assertIn(required, plugin)

    def test_negative_fixtures_fail_before_kubernetes(self) -> None:
        action_only = ROOT / "tests/reject_shared_mongodb_action_only.yml"
        internal = ROOT / "tests/reject_shared_mongodb_internal_injection.yml"
        task_start = ROOT / "tests/reject_shared_mongodb_task_start.sh"
        self.assertTrue(action_only.is_file())
        self.assertTrue(internal.is_file())
        self.assertTrue(task_start.is_file())

        result = subprocess.run(
            [str(task_start)], cwd=ROOT, capture_output=True, text=True, check=False
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("TASK_SELECTION_GUARD", task_start.read_text())

        internal_result = subprocess.run(
            [
                str(ROOT / ".venv/bin/ansible-playbook"),
                "-i",
                "localhost,",
                str(internal),
                "--extra-vars",
                '{"mongodb_bootstrap_internal_manifests":[]}',
            ],
            cwd=ROOT / "ansible",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, internal_result.returncode)
        self.assertIn(
            "INTERNAL_VARIABLE_GUARD", internal_result.stdout + internal_result.stderr
        )

        token = "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            attestation = Path(directory) / "attestation"
            attestation.write_text(f"{token}:entrypoint\n")
            os.chmod(attestation, 0o600)
            env = os.environ.copy()
            env.update(
                {
                    "ANSIBLE_CONFIG": str(ROOT / "ansible/ansible.cfg"),
                    "CRISTEXWEB_MONGODB_BOOTSTRAP_ENTRYPOINT": "v1",
                    "CRISTEXWEB_MONGODB_BOOTSTRAP_TOKEN": token,
                    "CRISTEXWEB_MONGODB_BOOTSTRAP_ATTESTATION_FILE": str(attestation),
                }
            )
            action_result = subprocess.run(
                [
                    str(ROOT / ".venv/bin/ansible-playbook"),
                    "-i",
                    "localhost,",
                    str(action_only),
                ],
                cwd=ROOT / "ansible",
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(0, action_result.returncode)
        output = action_result.stdout + action_result.stderr
        self.assertIn("ENTRYPOINT_GUARD", output)
        self.assertIn("canonical guarded role task source", output)
        self.assertNotIn("Failed to connect", output)


if __name__ == "__main__":
    unittest.main()
