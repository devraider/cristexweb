from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
COMPONENT = ANSIBLE / "files/components"
ROLE_DEFAULTS = ANSIBLE / "roles/argocd_target_cache_repair/defaults/main.yml"
ROLE_TASKS = ANSIBLE / "roles/argocd_target_cache_repair/tasks/main.yml"
ACTION = ANSIBLE / "plugins/action/argocd_target_cache_repair_guarded_k8s.py"
WRAPPER = ANSIBLE / "bin/bootstrap-argocd-target-cache-repair"
PLAYBOOK = ANSIBLE / "playbooks/bootstrap_argocd_target_cache_repair.yml"


class ArgoTargetCacheRepairContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.defaults = yaml.safe_load(ROLE_DEFAULTS.read_text())
        cls.tasks = ROLE_TASKS.read_text()
        cls.action = ACTION.read_text()
        cls.wrapper = WRAPPER.read_text()
        cls.configmap = yaml.safe_load((COMPONENT / "argocd/config/configmap-argocd-cm.yaml").read_text())
        cls.role = yaml.safe_load((COMPONENT / "cristexhub-prod-registration/rbac/role-argocd-application-controller-cristexhub-prod.yaml").read_text())
        cls.controller = yaml.safe_load((COMPONENT / "argocd/runtime/statefulset-argocd-application-controller.yaml").read_text())

    def test_exact_target_inclusion_allowlist(self) -> None:
        inclusions = yaml.safe_load(self.configmap["data"]["resource.inclusions"])
        self.assertEqual(
            [
                {"apiGroups": [""], "kinds": ["ConfigMap", "Service", "ServiceAccount"], "clusters": ["https://kubernetes.default.svc"]},
                {"apiGroups": ["apps"], "kinds": ["Deployment"], "clusters": ["https://kubernetes.default.svc"]},
                {"apiGroups": ["networking.k8s.io"], "kinds": ["Ingress", "NetworkPolicy"], "clusters": ["https://kubernetes.default.svc"]},
            ],
            inclusions,
        )
        self.assertNotIn("'*'", self.configmap["data"]["resource.inclusions"])
        self.assertNotIn('"*"', self.configmap["data"]["resource.inclusions"])
        self.assertNotIn("Secret", json.dumps(inclusions))
        self.assertNotIn("StatefulSet", json.dumps(inclusions))

    def test_prod_role_only_adds_read_serviceaccount_rule(self) -> None:
        rules = [rule for rule in self.role["rules"] if "serviceaccounts" in rule.get("resources", [])]
        self.assertEqual([{"apiGroups": [""], "resources": ["serviceaccounts"], "verbs": ["get", "list", "watch"]}], rules)
        self.assertFalse({"create", "update", "patch", "delete"} & set(rules[0]["verbs"]))

    def test_controller_rollout_annotation_is_bounded(self) -> None:
        annotations = self.controller["spec"]["template"]["metadata"]["annotations"]
        self.assertEqual("v1", annotations["cristex.io/target-cache-repair"])
        config_digest = hashlib.sha256((COMPONENT / "argocd/config/configmap-argocd-cm.yaml").read_bytes()).hexdigest()
        role_digest = hashlib.sha256((COMPONENT / "cristexhub-prod-registration/rbac/role-argocd-application-controller-cristexhub-prod.yaml").read_bytes()).hexdigest()
        self.assertEqual(config_digest, annotations["checksum/cm"])
        self.assertEqual(role_digest, annotations["checksum/cristexhub-prod-read-rbac"])
        self.assertNotIn("deployment-argocd-server", self.tasks)
        self.assertNotIn("deployment-argocd-repo-server", self.tasks)

    def test_dedicated_three_object_closure_and_no_secrets(self) -> None:
        self.assertEqual(3, self.defaults["argocd_target_cache_repair_object_count"])
        self.assertEqual(3, len(self.defaults["argocd_target_cache_repair_sources"]))
        identities = sorted(entry["identity"] for entry in self.defaults["argocd_target_cache_repair_sources"])
        self.assertEqual(
            [
                "apps/v1|StatefulSet|argocd|argocd-application-controller",
                "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod",
                "v1|ConfigMap|argocd|argocd-cm",
            ],
            identities,
        )
        self.assertNotIn("kind: Secret", self.tasks)
        self.assertNotIn("kind: Deployment", self.tasks)
        self.assertNotIn("kind: RoleBinding", self.tasks)
        self.assertIn("peer_targets", self.tasks)
        self.assertIn("server/repo-server", self.tasks)
        self.assertIn("ConfigMap, PROD Role, and controller StatefulSet", self.tasks)
        self.assertIn("no_delete_path", self.tasks)
        self.assertIn("internal_attestation_state", self.tasks.split("- name: Require the exact target-cache repair entrypoint contract", 1)[0])
        self.assertIn("internal_statefulset_target_spec", self.tasks.split("- name: Require the exact target-cache repair entrypoint contract", 1)[0])

    def test_exact_cas_process_and_postvalidation_guards_are_present(self) -> None:
        for required in (
            "_proc_cmdline",
            "_proc_starttime",
            "_ancestor",
            "_source_closure_valid",
            "_wrapper_binding_valid",
            "resourceVersion",
            '"op": "test"',
            "kubernetes.core.k8s_json_patch",
            "Wait for only the application-controller StatefulSet",
            "Wait for the exact PROD Argo Application",
            "Synced",
            "Healthy",
            "no_log: true",
        ):
            self.assertIn(required, self.action + self.tasks)
        self.assertIn("bootstrap_argocd_target_cache_repair.yml", self.wrapper)
        self.assertIn("--diff", self.wrapper)
        self.assertIn("--limit crtxweb", self.wrapper)
        self.assertIn("resource.inclusions", self.action + self.tasks)
        self.assertNotIn("clusters:\n        - '*'", self.wrapper + self.tasks)

    def test_sources_have_pinned_hashes_and_uids(self) -> None:
        self.assertEqual(3, len(self.defaults["argocd_target_cache_repair_expected_uids"]))
        for entry in self.defaults["argocd_target_cache_repair_sources"]:
            path = ROOT / entry["path"].split("/home/paul/projects/cristexweb/", 1)[1]
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertRegex(self.defaults["argocd_target_cache_repair_expected_uids"][entry["identity"]], r"^[0-9a-f-]{36}$")
        self.assertIn("_EXPECTED_UIDS", self.action)
        self.assertIn("_EXPECTED_DEFINITION_HASHES", self.action)

    def test_entrypoint_is_non_passthrough_and_playbook_is_dedicated(self) -> None:
        self.assertTrue(WRAPPER.is_file())
        self.assertTrue(PLAYBOOK.is_file())
        self.assertTrue(WRAPPER.stat().st_mode & 0o111)
        self.assertEqual("#!/bin/dash", self.wrapper.splitlines()[0])
        self.assertIn('"$#" -ne 1', self.wrapper)
        self.assertIn("check", self.wrapper)
        self.assertIn("apply", self.wrapper)
        self.assertNotIn("bootstrap_argocd.yml", self.wrapper)
        self.assertIn("argocd_target_cache_repair", PLAYBOOK.read_text())

    def test_wrapper_process_and_dependency_pins_are_exact(self) -> None:
        self.assertIn('CDPATH= cd -- "$repository_root/ansible"', self.wrapper)
        self.assertIn("python_tool=/usr/bin/python3.13", self.wrapper)
        self.assertIn("regular file", self.wrapper)
        self.assertIn("CRISTEXWEB_ARGOCD_TARGET_CACHE_REPAIR_OPERATOR=$controller_user", self.wrapper)
        self.assertIn("action_source=\"$repository_root/ansible/plugins/action/argocd_target_cache_repair_guarded_k8s.py\"", self.wrapper)
        self.assertIn('[ ! -L "$action_source" ]', self.wrapper)
        self.assertIn("k8s_json_patch.py", self.wrapper)
        self.assertIn("3f4a8318615ea5401fdea6d1177c181ad11e31e48eaf7f8f0fa6554a053fb16b", self.wrapper)

    def test_action_requires_complete_preflight_and_ordered_identity_binding(self) -> None:
        self.assertIn("_preflight_binding_valid", self.action)
        self.assertIn('_AnsibleTaggedStr" and value == "true"', self.action)
        self.assertIn("_EXPECTED_TARGET_IDENTITIES_ORDER", self.action)
        self.assertIn("prestate_bindings", self.action)
        self.assertIn("resourceVersion", self.action)
        self.assertIn("no_delete_path", self.action)
        self.assertIn("_K8S_JSON_PATCH_SOURCE", self.action)
        self.assertIn("_K8S_JSON_PATCH_SOURCE.resolve() == _K8S_JSON_PATCH_REAL_SOURCE", self.action)
        self.assertIn("python3.13", self.action)

    def test_statefulset_requires_full_spec_and_safe_partial_recovery_is_documented(self) -> None:
        self.assertIn("internal_statefulset_target_spec", self.tasks)
        self.assertIn("internal_statefulset_legacy_spec", self.tasks)
        self.assertIn("exact annotation replacement", self.tasks)
        self.assertIn("combine({'annotations': argocd_target_cache_repair_legacy_controller_annotations}, recursive=False)", self.tasks)
        self.assertNotIn("combine({'annotations': argocd_target_cache_repair_legacy_controller_annotations}, recursive=True)", self.tasks)
        self.assertIn("item.resources[0].spec ==", self.tasks)
        runbook = (ROOT / "runbooks/argocd-target-cache-repair.md").read_text()
        self.assertIn("Safe partial states and recovery", runbook)
        self.assertIn("no automatic rollback", runbook)
        self.assertIn("observedGeneration ==", runbook)
        self.assertIn("server/repo-server", runbook)
        self.assertIn("trusted controller-UID boundary", runbook)

    def test_wrapper_rejects_passthrough_without_running_ansible(self) -> None:
        import subprocess

        result = subprocess.run([str(WRAPPER), "check", "unexpected"], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(64, result.returncode)
        self.assertNotIn("ansible-playbook", result.stdout + result.stderr)

    def test_canonical_check_is_read_only_and_reaches_metadata_queries(self) -> None:
        self.assertIn("mode=$1", self.wrapper)
        self.assertIn("if [ \"$mode\" = check ]; then set -- \"$@\" --check; fi", self.wrapper)
        self.assertIn("kubernetes.core.k8s_info", self.tasks)
        self.assertIn("app.kubernetes.io/name=argocd-application-controller", self.tasks)
        self.assertGreaterEqual(
            self.tasks.count('kubeconfig: "{{ argocd_target_cache_repair_kubeconfig }}"'),
            6,
        )
        self.assertIn("Query the exact three target-cache repair prestates", self.tasks)
        self.assertIn("Query exact target-cache repair poststate", self.tasks)
        self.assertIn("when: not ansible_check_mode", self.tasks)
        self.assertNotIn("kubectl", self.wrapper)

    def test_sequential_patch_tasks_bind_identity_order_and_idempotent_application_rv(self) -> None:
        for name in (
            "Apply only the exact target-cache repair PROD Role patch",
            "Apply only the exact target-cache repair ConfigMap patch",
            "Apply only the exact target-cache repair controller StatefulSet patch",
        ):
            self.assertIn(name, self.tasks)
        self.assertIn("transition_plan", self.tasks)
        self.assertIn("internal_legacy_bindings | default([]) | map(attribute='identity') | list", self.tasks)
        self.assertIn("legacy_bindings | default([]) | length == 0", self.tasks)
        self.assertIn("status.sync.revision", self.tasks)
        self.assertIn("status.comparedTo.source.repoURL", self.tasks)
        self.assertIn("status.operationState.phase", self.tasks)
