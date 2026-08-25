from __future__ import annotations

import hashlib
import stat
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "ansible/files/components/reactive-resume-object-storage-history"
CURRENT_ALLOW = ROOT / (
    "ansible/files/components/reactive-resume-dev-networkpolicy/network/"
    "reactive-resume-object-storage-allow-dev.yaml"
)
ROLE = ROOT / "ansible/roles/reactive_resume_object_storage_source_check"
TASKS = ROLE / "tasks/main.yml"
DEFAULTS = ROLE / "defaults/main.yml"
PLAYBOOK = ROOT / "ansible/playbooks/check_reactive_resume_object_storage_source.yml"
WRAPPER = ROOT / "ansible/bin/check-reactive-resume-object-storage-source"
RUNBOOK = ROOT / "runbooks/reactive-resume-object-storage-source-recovery.md"

EXPECTED = {
    "network/allow-dev.yaml": "c50f60fa16fb8ab0e018f19c55b8be2eaa1b7db8960b8dde3b8d43cdd39814ad",
    "network/allow-dns.yaml": "73bb421065fd6991ab8b8217fea165ddd9739104ee37f2f42f91f6e697e32b4d",
    "network/default-deny.yaml": "350e97eeeae636af9cf6d4a8494d9c8002d760c0123a985dd19fe9987969f559",
    "runtime/configmap.yaml": "7cabd8c56001737adfd66f68932fa8811a754e506828ba23562f89f604975516",
    "runtime/service.yaml": "46fda04ad1b7ad2c3469c0c99d0f3a697084a6730b104df9227ff96a3cd75b38",
    "runtime/serviceaccount.yaml": "087cf2fbfe5f333cefd3367707a19f05e1b7bac4b48d75668a825834542f447a",
    "runtime/statefulset.yaml": "275ec75e893d3b18b3f48fc30e5216f5a74d1664319981229f91e8c55ecf23c6",
    "source/reactive-resume-object-storage-auth.yaml": "547626072d1ae6013d6513eed641fbb5f422c6f305ab641fe059873be4f905b2",
}


class ReactiveResumeObjectStorageSourceCheckContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = (HISTORY / "MANIFESTS.sha256").read_text()
        cls.tasks = TASKS.read_text()
        cls.defaults = DEFAULTS.read_text()
        cls.wrapper = WRAPPER.read_text()
        cls.runbook = RUNBOOK.read_text()
        cls.objects = []
        for relative in EXPECTED:
            path = HISTORY / relative
            cls.objects.append(yaml.safe_load(path.read_text()))

    def test_historical_manifest_ledger_is_exact_and_value_free(self) -> None:
        actual = {}
        for line in self.manifest.splitlines():
            relative, digest = line.split(maxsplit=1)
            actual[relative] = digest
        self.assertEqual(EXPECTED, actual)
        self.assertEqual(set(EXPECTED), {str(p.relative_to(HISTORY)) for p in HISTORY.rglob("*.yaml")})
        for relative, digest in EXPECTED.items():
            path = HISTORY / relative
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest(), relative)
            self.assertEqual(0o644, stat.S_IMODE(path.stat().st_mode), relative)
            self.assertNotIn("AGE-SECRET-KEY-", path.read_text())

    def test_exact_eight_object_partition_and_private_contract(self) -> None:
        identities = {
            f"{obj['apiVersion']}|{obj['kind']}|{obj['metadata'].get('namespace', '')}|{obj['metadata']['name']}"
            for obj in self.objects
        }
        self.assertEqual(8, len(identities))
        self.assertEqual(1, sum(obj["kind"] == "InfisicalStaticSecret" for obj in self.objects))
        self.assertEqual(3, sum(obj["kind"] == "NetworkPolicy" for obj in self.objects))
        self.assertEqual(1, sum(obj["kind"] == "StatefulSet" for obj in self.objects))
        self.assertFalse(any(obj["kind"] in {"Secret", "PersistentVolumeClaim", "Ingress", "Job"} for obj in self.objects))
        statefulset = next(obj for obj in self.objects if obj["kind"] == "StatefulSet")
        self.assertEqual(1, statefulset["spec"]["replicas"])
        self.assertEqual("local-path", statefulset["spec"]["volumeClaimTemplates"][0]["spec"]["storageClassName"])
        self.assertEqual("20Gi", statefulset["spec"]["volumeClaimTemplates"][0]["spec"]["resources"]["requests"]["storage"])
        self.assertEqual("Retain", statefulset["spec"]["persistentVolumeClaimRetentionPolicy"]["whenDeleted"])
        self.assertEqual("Retain", statefulset["spec"]["persistentVolumeClaimRetentionPolicy"]["whenScaled"])
        images = {
            container["image"]
            for container in statefulset["spec"]["template"]["spec"]["containers"]
            + statefulset["spec"]["template"]["spec"]["initContainers"]
        }
        self.assertEqual(
            {
                "chrislusf/seaweedfs:4.44@sha256:c927ea0755b1d7dd5a3101081e4717126d00e75e89d3142e21df374b0a90acad"
            },
            images,
        )
        service = next(obj for obj in self.objects if obj["kind"] == "Service")
        self.assertEqual("ClusterIP", service["spec"]["type"])
        self.assertNotIn("externalIPs", service["spec"])
        self.assertNotIn("loadBalancerIP", service["spec"])

    def test_secret_and_network_boundaries_are_value_free(self) -> None:
        auth = next(obj for obj in self.objects if obj["kind"] == "InfisicalStaticSecret")
        self.assertEqual("/reactive-resume/dev/runtime", auth["spec"]["sources"][0]["secretPath"])
        self.assertEqual("prod", auth["spec"]["sources"][0]["environmentSlug"])
        self.assertEqual({"accessKey", "secretKey"}, set(auth["spec"]["targets"][0]["template"]["data"]))
        combined = "\n".join(path.read_text() for path in HISTORY.rglob("*.yaml"))
        self.assertNotRegex(combined, r"(?im)^\s*(?:password|clientsecret|token)\s*[:=]\s*[^$<\n]")
        policies = {obj["metadata"]["name"]: obj for obj in self.objects if obj["kind"] == "NetworkPolicy"}
        self.assertEqual({"Ingress", "Egress"}, set(policies["reactive-resume-object-storage-default-deny"]["spec"]["policyTypes"]))
        self.assertEqual({53}, {port["port"] for port in policies["reactive-resume-object-storage-allow-dns"]["spec"]["egress"][0]["ports"]})
        self.assertEqual(8333, policies["reactive-resume-object-storage-allow-dev"]["spec"]["ingress"][0]["ports"][0]["port"])

    def test_current_source_difference_is_bound(self) -> None:
        current = yaml.safe_load(CURRENT_ALLOW.read_text())
        historical = next(obj for obj in self.objects if obj["metadata"]["name"] == "reactive-resume-object-storage-allow-dev")
        self.assertEqual("reactive-resume-dev-networkpolicy", current["metadata"]["labels"]["cristex.io/component"])
        self.assertEqual("object-storage", historical["metadata"]["labels"]["cristex.io/component"])
        self.assertIn("cristex.io/source-service", current["metadata"]["annotations"])
        self.assertNotIn("annotations", historical["metadata"])
        self.assertEqual("cristexhub", current["spec"]["ingress"][0]["from"][0]["podSelector"]["matchLabels"]["app.kubernetes.io/part-of"])
        self.assertEqual(0, CURRENT_ALLOW.stat().st_mode & 0o022)

    def test_role_is_read_only_and_ownership_guarded(self) -> None:
        for required in (
            "ansible_check_mode",
            "kubernetes.core.k8s_info:",
            "check_mode: false",
            "metadata_only secret_data_read=false pvc_data_read=false",
            "reactive_resume_object_storage_source_check_argo_revision",
            "reactive_resume_object_storage_source_check_internal_live_objects",
            "Refusing a foreign current object-storage identity",
        ):
            self.assertIn(required, self.tasks, required)
        for forbidden in (
            "kubernetes.core.k8s:",
            "kubernetes.core.k8s_delete",
            "ansible.builtin.command:",
            "ansible.builtin.shell:",
            "kubectl apply",
            "state: present",
        ):
            self.assertNotIn(forbidden, self.tasks, forbidden)

    def test_wrapper_is_check_only_and_non_passthrough(self) -> None:
        subprocess.run(["sh", "-n", str(WRAPPER)], check=True)
        self.assertEqual(0o755, stat.S_IMODE(WRAPPER.stat().st_mode))
        for required in (
            "usage: ansible/bin/check-reactive-resume-object-storage-source check",
            "--check",
            "--diff",
            "--limit crtxweb",
            "ENTRYPOINT=v1",
            "CRISTEXWEB_REACTIVE_RESUME_OBJECT_STORAGE_SOURCE_ATTESTATION_FILE",
            "playbooks/check_reactive_resume_object_storage_source.yml",
        ):
            self.assertIn(required, self.wrapper, required)
        for forbidden in ("apply", "kubectl apply", "tofu apply", "exec \"$@\""):
            self.assertNotIn(forbidden, self.wrapper, forbidden)

    def test_docs_preserve_historical_and_argo_boundaries(self) -> None:
        for required in (
            "historical/recovery source record",
            "No task in this lane creates",
            "dd7d4cedd902e68266d9713d1dbb8e90f0b529b1",
            "Secret data or PVC contents",
            "current leaf has component label",
            "default-deny and DNS policies",
            "ansible/bin/check-reactive-resume-object-storage-source check",
            "No secret values",
        ):
            self.assertIn(required, self.runbook, required)


if __name__ == "__main__":
    unittest.main()
