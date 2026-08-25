from __future__ import annotations

import hashlib
import importlib.util
import stat
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

import yaml
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "ansible/files/components/reactive-resume-object-storage-history"
CURRENT_ALLOW = ROOT / (
    "ansible/files/components/reactive-resume-dev-networkpolicy/network/"
    "reactive-resume-object-storage-allow-dev.yaml"
)
ROLE = ROOT / "ansible/roles/reactive_resume_object_storage_source_check"
FULL_SPEC_GUARD = ROOT / "ansible/plugins/action/reactive_resume_object_storage_full_spec_guarded.py"
METADATA_MODULE = ROOT / "ansible/library/reactive_resume_object_storage_metadata.py"
_metadata_spec = importlib.util.spec_from_file_location("reactive_resume_object_storage_metadata", METADATA_MODULE)
assert _metadata_spec and _metadata_spec.loader
_metadata_module = importlib.util.module_from_spec(_metadata_spec)
_metadata_spec.loader.exec_module(_metadata_module)
_metadata_response = _metadata_module._metadata
_spec = importlib.util.spec_from_file_location("reactive_resume_object_storage_full_spec_guarded", FULL_SPEC_GUARD)
assert _spec and _spec.loader
_full_spec_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_full_spec_module)
_normalized = _full_spec_module._normalized
_normalized_pair = _full_spec_module._normalized_pair
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
    "runtime/statefulset.yaml": "ae0dd122924c798d9c0a9b86e64e40d2b81e8772641d334b7857f876e626cab4",
    "source/reactive-resume-object-storage-auth.yaml": "547626072d1ae6013d6513eed641fbb5f422c6f305ab641fe059873be4f905b2",
}


class ReactiveResumeObjectStorageSourceCheckContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = (HISTORY / "MANIFESTS.sha256").read_text()
        cls.tasks = TASKS.read_text()
        cls.full_spec_guard = FULL_SPEC_GUARD.read_text()
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
        config_volume_mode = next(
            volume for volume in statefulset["spec"]["template"]["spec"]["volumes"]
            if volume["name"] == "object-storage-config"
        )["configMap"]["defaultMode"]
        tls_volume_mode = next(
            volume for volume in statefulset["spec"]["template"]["spec"]["volumes"]
            if volume["name"] == "object-storage-tls"
        )["secret"]["defaultMode"]
        self.assertEqual(288, config_volume_mode)
        self.assertEqual(288, tls_volume_mode)
        self.assertEqual(2, (HISTORY / "runtime/statefulset.yaml").read_text().count("defaultMode: 288"))
        config_volume = next(
            volume for volume in statefulset["spec"]["template"]["spec"]["volumes"]
            if volume["name"] == "object-storage-config"
        )
        self.assertEqual(
            "reactive-resume-object-storage-config",
            config_volume["configMap"]["name"],
        )
        seaweed = next(
            container for container in statefulset["spec"]["template"]["spec"]["containers"]
            if container["name"] == "seaweedfs"
        )
        config_mount = next(
            mount for mount in seaweed["volumeMounts"]
            if mount["name"] == "object-storage-config"
        )
        self.assertEqual("/etc/seaweedfs/s3.json", config_mount["mountPath"])
        self.assertEqual("s3.json", config_mount["subPath"])
        self.assertIn("-s3.config=/etc/seaweedfs/s3.json", seaweed["args"])
        images = {
            container["image"]
            for container in statefulset["spec"]["template"]["spec"]["containers"]
            + statefulset["spec"]["template"]["spec"]["initContainers"]
        }
        self.assertEqual(
            {
                "sha256:c927ea0755b1d7dd5a3101081e4717126d00e75e89d3142e21df374b0a90acad"
            },
            {image.split("@", 1)[1] for image in images},
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

    def test_argo_handoff_contract_is_exactly_bound(self) -> None:
        defaults = yaml.safe_load(self.defaults)
        self.assertEqual(8, defaults["reactive_resume_object_storage_source_check_object_count"])
        self.assertEqual(7, defaults["reactive_resume_object_storage_source_check_live_runtime_object_count"])
        self.assertEqual("MANIFESTS.sha256", defaults["reactive_resume_object_storage_source_check_manifest_ledger_relative"])
        self.assertEqual(64, len(defaults["reactive_resume_object_storage_source_check_manifest_ledger_sha256"]))
        self.assertEqual(
            hashlib.sha256((HISTORY / "MANIFESTS.sha256").read_bytes()).hexdigest(),
            defaults["reactive_resume_object_storage_source_check_manifest_ledger_sha256"],
        )
        self.assertEqual("shared-services", defaults["reactive_resume_object_storage_source_check_secret_metadata_resource"]["namespace"])
        self.assertEqual("reactive-resume-object-storage-auth", defaults["reactive_resume_object_storage_source_check_secret_metadata_resource"]["name"])
        producers = defaults["reactive_resume_object_storage_source_check_alternate_producers"]
        self.assertEqual(
            ["InfisicalSecret", "InfisicalStaticSecret", "InfisicalPushSecret", "InfisicalDynamicSecret", "ExternalSecret", "SealedSecret", "SecretProviderClass"],
            [item["kind"] for item in producers],
        )
        self.assertEqual(
            ["secrets.infisical.com/v1alpha1", "secrets.infisical.com/v1beta1", "secrets.infisical.com/v1alpha1", "secrets.infisical.com/v1alpha1", "external-secrets.io/v1beta1", "bitnami.com/v1alpha1", "secrets-store.csi.x-k8s.io/v1"],
            [item["api_version"] for item in producers],
        )
        self.assertTrue(all("name" not in item for item in producers))
        self.assertTrue(all(item["target_namespace"] == "shared-services" for item in producers))
        self.assertTrue(all(item["target_name"] == "reactive-resume-object-storage-auth" for item in producers))
        self.assertTrue(all("/namespaces/shared-services/" in item["api_path"] and not item["api_path"].endswith("/reactive-resume-object-storage-auth") for item in producers))
        self.assertEqual("ssh://git@ssh.github.com:443/devraider/cristexweb.git",
            defaults["reactive_resume_object_storage_source_check_argo_repo_url"],
        )
        self.assertEqual(
            "ansible/files/components/reactive-resume-dev-argocd",
            defaults["reactive_resume_object_storage_source_check_argo_path"],
        )
        self.assertEqual(
            "https://kubernetes.default.svc",
            defaults["reactive_resume_object_storage_source_check_argo_destination_server"],
        )
        self.assertEqual(
            "cristexhub-dev",
            defaults["reactive_resume_object_storage_source_check_argo_destination_namespace"],
        )
        self.assertEqual("reactive-resume-dev", defaults["reactive_resume_object_storage_source_check_argo_project"])
        managers = defaults["reactive_resume_object_storage_source_check_managed_field_managers"]
        self.assertEqual(8, len(managers))
        self.assertEqual(
            ["kubectl-client-side-apply", "kubectl-rollout", "k3s"],
            managers["apps/v1|StatefulSet|shared-services|reactive-resume-object-storage"],
        )
        self.assertEqual(
            ["kubectl-client-side-apply", "OpenAPI-Generator"],
            managers["networking.k8s.io/v1|NetworkPolicy|shared-services|reactive-resume-object-storage-allow-dev"],
        )
        self.assertEqual(
            ["kubectl-client-side-apply"],
            managers["v1|Secret|shared-services|reactive-resume-object-storage-auth"],
        )
        self.assertTrue(defaults["reactive_resume_object_storage_source_check_argo_self_heal"])
        self.assertEqual(
            [
                "CreateNamespace=false",
                "Prune=false",
                "ServerSideApply=false",
                "Replace=false",
                "FailOnSharedResource=true",
            ],
            defaults["reactive_resume_object_storage_source_check_argo_sync_options"],
        )

    def test_normalized_full_spec_guard_is_read_only_and_default_aware(self) -> None:
        for required in (
            "_METADATA_DROPS",
            "_SERVICE_SPEC_DROPS",
            "_SERVICE_ALLOCATOR_FIELDS",
            "_SERVICE_SINGLE_STACK_FAMILIES",
            "_service_allocator_default_is_canonical",
            "_SERVICE_DEFAULTS",
            "_STATEFULSET_DEFAULTS",
            "kubectl.kubernetes.io/last-applied-configuration",
            "clusterIP",
            "revisionHistoryLimit",
            "TRANSFERS_FILES = False",
            "normalized Kubernetes object drift",
        ):
            self.assertIn(required, self.full_spec_guard, required)
        self.assertNotIn("kubernetes.core.k8s", self.full_spec_guard)
        desired = yaml.safe_load((HISTORY / "runtime/service.yaml").read_text())
        live = yaml.safe_load((HISTORY / "runtime/service.yaml").read_text())
        live["metadata"].update({"uid": "generated", "resourceVersion": "generated"})
        live["spec"].update({"clusterIP": "10.0.0.1", "clusterIPs": ["10.0.0.1"], "ipFamilies": ["IPv4"], "ipFamilyPolicy": "SingleStack", "sessionAffinity": "None"})
        live["metadata"]["annotations"] = {"kubectl.kubernetes.io/last-applied-configuration": "generated"}
        self.assertEqual(_normalized_pair(desired, live)[0], _normalized_pair(desired, live)[1])
        behavior_drift = yaml.safe_load((HISTORY / "runtime/service.yaml").read_text())
        behavior_drift["spec"]["sessionAffinity"] = "ClientIP"
        self.assertNotEqual(_normalized_pair(desired, behavior_drift)[0], _normalized_pair(desired, behavior_drift)[1])
        headless = yaml.safe_load((HISTORY / "runtime/service.yaml").read_text())
        headless["spec"].update({
            "clusterIP": "None",
            "clusterIPs": ["None"],
            "ipFamilies": ["IPv4"],
            "ipFamilyPolicy": "SingleStack",
        })
        self.assertNotEqual(_normalized_pair(desired, headless)[0], _normalized_pair(desired, headless)[1])
        dual_stack = yaml.safe_load((HISTORY / "runtime/service.yaml").read_text())
        dual_stack["spec"].update({
            "clusterIP": "10.0.0.1",
            "clusterIPs": ["10.0.0.1", "2001:db8::1"],
            "ipFamilies": ["IPv4", "IPv6"],
            "ipFamilyPolicy": "RequireDualStack",
        })
        self.assertNotEqual(_normalized_pair(desired, dual_stack)[0], _normalized_pair(desired, dual_stack)[1])
        external_name = yaml.safe_load((HISTORY / "runtime/service.yaml").read_text())
        external_name["spec"]["type"] = "ExternalName"
        external_live = yaml.safe_load((HISTORY / "runtime/service.yaml").read_text())
        external_live["spec"]["type"] = "ExternalName"
        external_live["spec"].update({
            "clusterIP": "10.0.0.1",
            "clusterIPs": ["10.0.0.1"],
            "ipFamilies": ["IPv4"],
            "ipFamilyPolicy": "SingleStack",
        })
        self.assertNotEqual(_normalized_pair(external_name, external_live)[0], _normalized_pair(external_name, external_live)[1])
        deleting = yaml.safe_load((HISTORY / "runtime/service.yaml").read_text())
        deleting["metadata"]["deletionTimestamp"] = "2026-01-01T00:00:00Z"
        self.assertNotEqual(_normalized_pair(desired, deleting)[0], _normalized_pair(desired, deleting)[1])
        statefulset = yaml.safe_load((HISTORY / "runtime/statefulset.yaml").read_text())
        live_statefulset = yaml.safe_load((HISTORY / "runtime/statefulset.yaml").read_text())
        live_statefulset["spec"]["revisionHistoryLimit"] = 10
        self.assertEqual(_normalized_pair(statefulset, live_statefulset)[0], _normalized_pair(statefulset, live_statefulset)[1])

    def test_managed_field_operation_predicate_requires_observed_update(self) -> None:
        tasks = (ROLE / "tasks/main.yml").read_text()
        expression = "rejectattr('operation', 'equalto', 'Update') | list | length == 0"
        self.assertEqual(2, tasks.count(expression))
        template = Environment().from_string(
            "{{ entries | rejectattr('operation', 'equalto', 'Update') | list | length }}"
        )
        self.assertEqual("0", template.render(entries=[{"operation": "Update"}]))
        self.assertEqual("1", template.render(entries=[{"operation": "Apply"}]))
        self.assertEqual("1", template.render(entries=[{"operation": "Create"}]))

    def test_metadata_request_never_returns_secret_body(self) -> None:
        class RecordingClient:
            def __init__(self):
                self.calls = []

            def call_api(self, *args, **kwargs):
                self.calls.append((args, kwargs))
                return {"apiVersion": "meta.k8s.io/v1", "kind": "PartialObjectMetadataList", "metadata": {}, "items": None}

        client = RecordingClient()
        self.assertEqual([], _metadata_module._metadata_list(_metadata_module._call(client, "/apis/example/v1/widgets", _metadata_module._PARTIAL_METADATA_LIST_ACCEPT)))
        self.assertEqual(
            _metadata_module._PARTIAL_METADATA_LIST_ACCEPT,
            client.calls[0][1]["header_params"]["Accept"],
        )
        text = METADATA_MODULE.read_text()
        self.assertIn("PartialObjectMetadata", text)
        self.assertIn("PartialObjectMetadataList", text)
        self.assertIn("_PARTIAL_METADATA_ACCEPT", text)
        self.assertIn("_PARTIAL_METADATA_LIST_ACCEPT", text)
        self.assertIn("_PARTIAL_METADATA_TOP_LEVEL_KEYS", text)
        self.assertIn("_PARTIAL_METADATA_METADATA_KEYS", text)
        self.assertIn("module.fail_json", text)
        self.assertIn('resource_kind"] == "Secret"', text)
        self.assertIn("refusing collection target inspection for Secret resources", text)
        self.assertNotIn("request failed: %s", text)
        self.assertNotIn("inspection failed: %s", text)
        self.assertNotIn('"data"', text)
        self.assertNotIn('"stringData"', text)
        managed_field = {
            "manager": "infisical",
            "operation": "Apply",
            "apiVersion": "v1",
            "fieldsType": "FieldsV1",
            "fieldsV1": {"f:metadata": {"f:labels": {}}},
        }
        exact = {
            "apiVersion": "meta.k8s.io/v1",
            "kind": "PartialObjectMetadata",
            "metadata": {"name": "safe", "managedFields": [managed_field]},
        }
        self.assertEqual({"name": "safe", "managedFields": [managed_field]}, _metadata_response(exact))
        exact_list = {
            "apiVersion": "meta.k8s.io/v1",
            "kind": "PartialObjectMetadataList",
            "metadata": {"resourceVersion": "safe"},
            "items": [exact],
        }
        self.assertEqual(
            [{"name": "safe", "managedFields": [managed_field]}],
            _metadata_module._metadata_list(exact_list),
        )
        self.assertEqual([], _metadata_module._metadata_list({**exact_list, "items": []}))
        self.assertEqual([], _metadata_module._metadata_list({**exact_list, "items": None}))
        self.assertIsNone(_metadata_module._metadata_list({**exact_list, "items": None, "metadata": {"continue": "next"}}))
        self.assertIsNone(_metadata_module._metadata_list({**exact_list, "items": [], "metadata": {"continue": "next"}}))
        self.assertIsNone(_metadata_module._metadata_list({**exact_list, "items": [], "metadata": {"remainingItemCount": 1}}))
        self.assertEqual(
            [{"name": "safe-target", "namespace": "shared-services", "kind": "Secret"}],
            _metadata_module._producer_targets(
                {
                    "apiVersion": "secrets.infisical.com/v1beta1",
                    "kind": "InfisicalStaticSecret",
                    "metadata": {"name": "shared-postgresql", "namespace": "shared-services", "uid": "uid-shared-postgresql", "resourceVersion": "1"},
                    "spec": {"targets": [{"name": "safe-target", "namespace": "shared-services", "kind": "Secret", "template": {"data": {"password": "not-returned"}}}]},
                },
                "InfisicalStaticSecret",
                "secrets.infisical.com/v1beta1",
                {"name": "shared-postgresql", "namespace": "shared-services", "uid": "uid-shared-postgresql", "resourceVersion": "1"},
            ),
        )
        self.assertEqual(
            [{"name": "safe-target", "namespace": "shared-services", "kind": "Secret"}],
            _metadata_module._producer_targets(
                {
                    "apiVersion": "secrets.infisical.com/v1alpha1",
                    "kind": "InfisicalSecret",
                    "metadata": {"name": "shared-postgresql", "namespace": "shared-services", "uid": "uid-shared-postgresql", "resourceVersion": "1"},
                    "spec": {"managedSecretReference": {"secretName": "safe-target", "secretNamespace": "shared-services"}},
                },
                "InfisicalSecret",
                "secrets.infisical.com/v1alpha1",
                {"name": "shared-postgresql", "namespace": "shared-services", "uid": "uid-shared-postgresql", "resourceVersion": "1"},
            ),
        )
        self.assertEqual(
            [
                {"name": "direct", "namespace": "shared-services", "kind": "Secret"},
                {"name": "generated", "namespace": "shared-services", "kind": "Secret"},
            ],
            _metadata_module._producer_targets(
                {
                    "apiVersion": "secrets.infisical.com/v1alpha1",
                    "kind": "InfisicalPushSecret",
                    "metadata": {"name": "push", "namespace": "shared-services", "uid": "uid-push", "resourceVersion": "1"},
                    "spec": {"push": {
                        "secret": {"secretName": "direct", "secretNamespace": "shared-services"},
                        "generators": [{"destinationSecretName": "generated"}],
                    }},
                },
                "InfisicalPushSecret",
                "secrets.infisical.com/v1alpha1",
                {"name": "push", "namespace": "shared-services", "uid": "uid-push", "resourceVersion": "1"},
            ),
        )
        self.assertEqual(
            [{"name": "dynamic-target", "namespace": "shared-services", "kind": "Secret"}],
            _metadata_module._producer_targets(
                {
                    "apiVersion": "secrets.infisical.com/v1alpha1",
                    "kind": "InfisicalDynamicSecret",
                    "metadata": {"name": "dynamic", "namespace": "shared-services"},
                    "spec": {"managedSecretReference": {"secretName": "dynamic-target", "secretNamespace": "shared-services"}},
                },
                "InfisicalDynamicSecret",
                "secrets.infisical.com/v1alpha1",
                {"name": "dynamic", "namespace": "shared-services"},
            ),
        )
        self.assertIsNone(
            _metadata_module._producer_targets(
                {
                    "apiVersion": "secrets.infisical.com/v1alpha1",
                    "kind": "InfisicalDynamicSecret",
                    "metadata": {"name": "dynamic", "namespace": "shared-services", "uid": "uid-dynamic", "resourceVersion": "1"},
                    "spec": {},
                },
                "InfisicalDynamicSecret",
                "secrets.infisical.com/v1alpha1",
                {"name": "dynamic", "namespace": "shared-services", "uid": "uid-dynamic", "resourceVersion": "1"},
            )
        )
        self.assertEqual(
            [{"name": "external", "namespace": "shared-services", "kind": "Secret"}],
            _metadata_module._producer_targets(
                {
                    "apiVersion": "external-secrets.io/v1beta1",
                    "kind": "ExternalSecret",
                    "metadata": {"name": "external", "namespace": "shared-services", "uid": "uid-external", "resourceVersion": "1"},
                    "spec": {},
                },
                "ExternalSecret",
                "external-secrets.io/v1beta1",
                {"name": "external", "namespace": "shared-services", "uid": "uid-external", "resourceVersion": "1"},
            ),
        )
        self.assertEqual(
            [{"name": "sealed-target", "namespace": "shared-services", "kind": "Secret"}],
            _metadata_module._producer_targets(
                {
                    "apiVersion": "bitnami.com/v1alpha1",
                    "kind": "SealedSecret",
                    "metadata": {"name": "sealed", "namespace": "shared-services"},
                    "spec": {"template": {"metadata": {"name": "sealed-target", "namespace": "shared-services"}}},
                },
                "SealedSecret",
                "bitnami.com/v1alpha1",
                {"name": "sealed", "namespace": "shared-services"},
            ),
        )
        self.assertEqual(
            [{"name": "csi-target", "namespace": "shared-services", "kind": "Secret"}],
            _metadata_module._producer_targets(
                {
                    "apiVersion": "secrets-store.csi.x-k8s.io/v1",
                    "kind": "SecretProviderClass",
                    "metadata": {"name": "csi", "namespace": "shared-services"},
                    "spec": {"secretObjects": [{"secretName": "csi-target"}]},
                },
                "SecretProviderClass",
                "secrets-store.csi.x-k8s.io/v1",
                {"name": "csi", "namespace": "shared-services"},
            ),
        )
        for invalid in (
            {**exact, "data": {"password": "must-not-be-accepted"}},
            {**exact, "metadata": {"name": "safe", "managedFields": [{**managed_field, "fieldsV1": {}}]}},
            {**exact, "metadata": {"name": "safe", "managedFields": [{**managed_field, "fieldsV1": {"unexpected": {}}}]}},
            {**exact, "metadata": {"name": "safe", "managedFields": [{**managed_field, "subresource": "status"}]}},
            {**exact, "metadata": {"name": "safe", "managedFields": [{**managed_field, "fieldsType": "Other"}]}},

            {**exact_list, "items": [{**exact, "data": {"password": "must-not-be-accepted"}}]},
            {**exact_list, "kind": "SecretList"},
            {**exact, "kind": "Secret"},
            {**exact, "apiVersion": "v1"},
            {**exact, "metadata": {"name": "safe", "unexpected": "field"}},
        ):
            self.assertIsNone(_metadata_response(invalid))

    def test_metadata_main_sanitizes_406_and_refuses_secret_collections(self) -> None:
        class StopMain(Exception):
            pass

        class FakeModule:
            def __init__(self, params):
                self.params = params
                self.calls = []
                self.result = None

            def fail_json(self, **payload):
                self.result = payload
                raise StopMain

            def exit_json(self, **payload):
                self.result = payload
                raise StopMain

        class ApiError(Exception):
            status = 406

            def __init__(self):
                super().__init__("response body contains SECRET_VALUE")
                self.body = '{"data":"SECRET_VALUE"}'

        class RecordingClient:
            def __init__(self, error=None):
                self.error = error
                self.calls = []

            def call_api(self, *args, **kwargs):
                self.calls.append((args, kwargs))
                if self.error is not None:
                    raise self.error
                return {}

        def run_main(params, api):
            fake_module = FakeModule(params)
            fake_kubernetes = types.ModuleType("kubernetes")
            fake_kubernetes.client = types.SimpleNamespace(ApiClient=lambda: api)
            fake_kubernetes.config = types.SimpleNamespace(load_kube_config=lambda **_: None)
            with mock.patch.object(_metadata_module, "AnsibleModule", lambda **_: fake_module):
                with mock.patch.dict(sys.modules, {"kubernetes": fake_kubernetes}):
                    with self.assertRaises(StopMain):
                        _metadata_module.main()
            return fake_module

        failed = run_main(
            {
                "kubeconfig": "/does/not/exist",
                "api_path": "/apis/example/v1/widgets",
                "collection": True,
                "resource_kind": "Widget",
                "resource_api_version": "example/v1",
            },
            RecordingClient(ApiError()),
        )
        self.assertIn("406", failed.result["msg"])
        self.assertNotIn("SECRET_VALUE", failed.result["msg"])

        class SequenceClient(RecordingClient):
            def __init__(self):
                super().__init__()
                self.responses = [{
                    "apiVersion": "meta.k8s.io/v1",
                    "kind": "PartialObjectMetadataList",
                    "metadata": {"resourceVersion": "safe"},
                    "items": [{
                        "apiVersion": "meta.k8s.io/v1",
                        "kind": "PartialObjectMetadata",
                        "metadata": {"name": "producer", "namespace": "shared-services"},
                    }],
                }, ApiError()]

            def call_api(self, *args, **kwargs):
                self.calls.append((args, kwargs))
                response = self.responses.pop(0)
                if isinstance(response, Exception):
                    raise response
                return response

        producer_error_api = SequenceClient()
        producer_failed = run_main(
            {
                "kubeconfig": "/does/not/exist",
                "api_path": "/apis/example/v1/widgets",
                "collection": True,
                "resource_kind": "Widget",
                "resource_api_version": "example/v1",
            },
            producer_error_api,
        )
        self.assertIn("406", producer_failed.result["msg"])
        self.assertNotIn("SECRET_VALUE", producer_failed.result["msg"])

        secret_api = RecordingClient()
        refused = run_main(
            {
                "kubeconfig": "/does/not/exist",
                "api_path": "/api/v1/namespaces/shared-services/secrets",
                "collection": True,
                "resource_kind": "Secret",
                "resource_api_version": "v1",
            },
            secret_api,
        )
        self.assertIn("refusing collection target inspection for Secret resources", refused.result["msg"])
        self.assertEqual([], secret_api.calls)

    def test_malformed_managed_fields_fail_closed(self) -> None:
        valid = {
            "manager": "ansible",
            "operation": "Update",
            "apiVersion": "v1",
            "fieldsType": "FieldsV1",
            "fieldsV1": {"f:metadata": {"f:labels": {}}},
        }
        base = {
            "apiVersion": "meta.k8s.io/v1",
            "kind": "PartialObjectMetadata",
            "metadata": {"name": "target", "managedFields": [valid]},
        }
        self.assertIsNotNone(_metadata_response(base))
        malformed = [
            {**valid, "operation": "Delete"},
            {**valid, "manager": ""},
            {**valid, "apiVersion": ""},
            {**valid, "fieldsType": "Other"},
            {**valid, "fieldsV1": {}},
            {**valid, "fieldsV1": {"metadata": {}}},
            {**valid, "subresource": "status"},
            {**valid, "unexpected": True},
            {key: value for key, value in valid.items() if key != "fieldsV1"},
        ]
        for entry in malformed:
            with self.subTest(entry=entry):
                candidate = {**base, "metadata": {"name": "target", "managedFields": [entry]}}
                self.assertIsNone(_metadata_response(candidate))
        for malformed_collection in (
            {**base, "metadata": {"name": "target", "managedFields": []}},
            {**base, "metadata": {"name": "target", "managedFields": [{**valid, "fieldsV1": {"f:metadata": []}}]}},
        ):
            self.assertIsNone(_metadata_response(malformed_collection))

    def test_role_is_read_only_and_ownership_guarded(self) -> None:
        for required in (
            "ansible_check_mode",
            "kubernetes.core.k8s_info:",
            "check_mode: false",
            "partial_metadata_and_nonsecret_full_spec secret_values_requested=false pvc_data_read=false",
            "reactive_resume_object_storage_source_check_internal_manifest_ledger",
            "reactive_resume_object_storage_source_check_internal_history_files",
            "reactive_resume_object_storage_source_check_internal_history_directories",
            "reactive_resume_object_storage_source_check_internal_history_links",
            "Require the exact historical source directory inventory",
            "historical Infisical source absence",
            "reactive_resume_object_storage_metadata:",
            "without requesting Secret data",
            "exact PartialObjectMetadata closure",
            "alternate Secret producer",
            "InfisicalSecret",
            "InfisicalStaticSecret",
            "InfisicalPushSecret",
            "InfisicalDynamicSecret",
            "v1alpha1",
            "target_namespace",
            "target_name",
            "owner provenance and deletion metadata",
            "live Secret custody",
            "reactive_resume_object_storage_source_check_live_secret_name",
            "reactive_resume_object_storage_source_check_argo_revision",
            "reactive_resume_object_storage_source_check_internal_live_objects",
            "reactive_resume_object_storage_source_check_managed_field_managers",
            "PartialObjectMetadataList",
            "collection: true",
            "target_identities",
            "api_available",
            "selectattr('kind', 'equalto', 'Secret')",
            "without requesting Secret data",
            "source_check_live_secret_type",
            "managedFields",
            "Require every historical runtime object-storage identity to be live exactly once",
            "Require current object ownership to remain Ansible pending Argo handoff",
            "argocd.argoproj.io/instance",
            "argocd.argoproj.io/tracking-id",
            "Require exact normalized current object full-spec fidelity",
            "reactive_resume_object_storage_full_spec_guarded",
            "reactive_resume_object_storage_source_check_live_secret_labels",
            "fieldsType",
            "fieldsV1",
            "type_debug",
            "subresource",
            "spec.source.repoURL",
            "spec.source.path",
            "spec.destination.server",
            "spec.destination.namespace",
            "spec.project",
            "automated.selfHeal",
            "syncPolicy.syncOptions",
            "status.sync.status",
            "status.health.status",
            "argo_resource_identities",
            "shared-services object",
        ):
            self.assertIn(required, self.tasks, required)
        for forbidden in (
            "kubernetes.core.k8s:",
            "kubernetes.core.k8s_delete",
            "ansible.builtin.command:",
            "ansible.builtin.shell:",
            "kubectl apply",
            "state: present",
            "hidden_fields:",
            "metadata_allowed_managers",
            "runtime_managed_field_managers",
            "secret_managed_field_managers",
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
            "Secret values or PVC contents",
            "current leaf has component label",
            "normalized non-secret full",
            "complete history-tree file, directory, and symlink",
            "exactly once",
            "default-deny and DNS policies",
            "ansible/bin/check-reactive-resume-object-storage-source check",
            "No secret values",
        ):
            self.assertIn(required, self.runbook, required)


if __name__ == "__main__":
    unittest.main()
