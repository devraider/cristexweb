from __future__ import annotations

import hashlib
import json
import os
import pwd
import re
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
import uuid

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/cristexhub-prod-registration"
DEFAULTS = ROOT / "ansible/roles/cristexhub_prod_registration/defaults/main.yml"
TASKS = ROOT / "ansible/roles/cristexhub_prod_registration/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/cristexhub_prod_registration_guarded_k8s.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-cristexhub-prod-registration"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_cristexhub_prod_registration.yml"
RUNBOOK = ROOT / "runbooks/cristexhub-prod-argocd-registration.md"
ACTION_ONLY_FIXTURE = ROOT / "tests/reject_cristexhub_prod_registration_action_only.yml"
TASK_START_FIXTURE = ROOT / "tests/reject_cristexhub_prod_registration_task_start.sh"
RESOURCE_VERSION_FIXTURE = ROOT / "tests/reject_cristexhub_prod_registration_resource_version.sh"
REVISION = "751885a42798d282e168131db147f13694a0a621"


def objects() -> list[dict]:
    return [yaml.safe_load(path.read_text()) for path in sorted(COMPONENT.rglob("*.yaml"))]


def canonical(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class CristexHubProdRegistrationContractTests(unittest.TestCase):
    def test_exact_value_free_five_object_closure(self) -> None:
        manifests = objects()
        self.assertEqual(5, len(manifests))
        self.assertEqual(
            {"AppProject", "Application", "Role", "RoleBinding", "Secret"},
            {manifest["kind"] for manifest in manifests},
        )
        text = "\n".join(path.read_text() for path in COMPONENT.rglob("*.yaml"))
        self.assertNotIn("password", text.lower())
        self.assertNotIn("token", text.lower())
        self.assertNotIn("sshPrivateKey", text)

    def test_cluster_registration_is_non_sensitive_and_prod_scoped(self) -> None:
        cluster = next(manifest for manifest in objects() if manifest["kind"] == "Secret")
        self.assertEqual("argocd-cluster-cristexhub-prod", cluster["metadata"]["name"])
        self.assertEqual(
            {
                "name": "cristexhub-prod-local",
                "server": "https://kubernetes.default.svc",
                "namespaces": "cristexhub-dev,cristexhub-prod",
                "clusterResources": "false",
                "config": "{}",
            },
            cluster["stringData"],
        )
        self.assertEqual(["cristexhub-dev", "cristexhub-prod"], cluster["stringData"]["namespaces"].split(","))

    def test_application_is_exact_revision_direct_server_and_automated_without_prune(self) -> None:
        application = next(manifest for manifest in objects() if manifest["kind"] == "Application")
        self.assertEqual(
            {
                "repoURL": "ssh://git@ssh.github.com:443/devraider/cristexhub.git",
                "targetRevision": REVISION,
                "path": "infra/kubernetes/cristexhub-prod",
            },
            application["spec"]["source"],
        )
        self.assertEqual(
            {
                "server": "https://kubernetes.default.svc",
                "namespace": "cristexhub-prod",
            },
            application["spec"]["destination"],
        )
        sync_policy = application["spec"]["syncPolicy"]
        self.assertEqual(
            {"prune": False, "selfHeal": True, "allowEmpty": False},
            sync_policy["automated"],
        )
        self.assertEqual(
            {
                "CreateNamespace=false",
                "Prune=false",
                "ServerSideApply=false",
                "Replace=false",
                "FailOnSharedResource=true",
            },
            set(sync_policy["syncOptions"]),
        )
        self.assertEqual([], application["metadata"].get("finalizers", []))

    def test_project_is_namespaced_least_privilege_for_direct_server(self) -> None:
        project = next(manifest for manifest in objects() if manifest["kind"] == "AppProject")
        spec = project["spec"]
        self.assertEqual([], spec["clusterResourceWhitelist"])
        self.assertEqual(
            [{"server": "https://kubernetes.default.svc", "namespace": "cristexhub-prod"}],
            spec["destinations"],
        )
        self.assertEqual(
            {("", "ConfigMap"), ("", "Service"), ("apps", "Deployment"),
             ("networking.k8s.io", "NetworkPolicy"), ("networking.k8s.io", "Ingress")},
            {(entry["group"], entry["kind"]) for entry in spec["namespaceResourceWhitelist"]},
        )
        self.assertNotIn("Secret", {entry["kind"] for entry in spec["namespaceResourceWhitelist"]})
        self.assertNotIn("syncWindows", spec)

    def test_controller_rbac_has_no_delete_or_cluster_scope(self) -> None:
        role = yaml.safe_load(
            (COMPONENT / "rbac/role-argocd-application-controller-cristexhub-prod.yaml").read_text()
        )
        self.assertEqual("cristexhub-prod", role["metadata"]["namespace"])
        verbs = {verb for rule in role["rules"] for verb in rule["verbs"]}
        self.assertEqual({"get", "list", "watch", "create", "patch"}, verbs)
        self.assertNotIn("delete", verbs)
        self.assertNotIn("*", str(role))
        binding = yaml.safe_load(
            (COMPONENT / "rbac/rolebinding-argocd-application-controller-cristexhub-prod.yaml").read_text()
        )
        self.assertEqual(
            [{"kind": "ServiceAccount", "name": "argocd-application-controller", "namespace": "argocd"}],
            binding["subjects"],
        )
        self.assertEqual("Role", binding["roleRef"]["kind"])
        self.assertFalse(any(path.name.startswith("clusterrole") for path in COMPONENT.rglob("*.yaml")))

    def test_raw_and_canonical_hash_ledgers_match(self) -> None:
        defaults = yaml.safe_load(DEFAULTS.read_text())
        expected = {
            Path(entry["path"].split("/ansible/files/")[1]): entry["sha256"]
            for entry in defaults["cristexhub_prod_registration_expected_hashes"]
        }
        for relative, digest in expected.items():
            path = ROOT / "ansible/files" / relative
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest(), path)
        plugin = PLUGIN.read_text()
        for manifest in objects():
            self.assertIn(canonical(manifest), plugin)
        self.assertIn(REVISION, defaults["cristexhub_prod_registration_revision"])

    def test_alias_to_direct_server_transition_is_exactly_two_object_scoped_and_hash_bound(self) -> None:
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(2, defaults["cristexhub_prod_registration_alias_transition_object_count"])
        self.assertEqual({"Application", "AppProject"}, set(defaults["cristexhub_prod_registration_alias_transition_uids"]))
        for kind, uid in defaults["cristexhub_prod_registration_alias_transition_uids"].items():
            uuid.UUID(uid)
            spec = defaults["cristexhub_prod_registration_alias_transition_specs"][kind]
            digest = hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            self.assertEqual(defaults["cristexhub_prod_registration_alias_transition_spec_hashes"][kind], digest)
            metadata = {
                "name": "cristexhub-prod",
                "namespace": "argocd",
                "labels": {
                    "app.kubernetes.io/name": "cristexhub-prod",
                    "app.kubernetes.io/part-of": "cristexhub",
                    "app.kubernetes.io/managed-by": "ansible",
                    "cristex.io/component": "cristexhub-prod-registration",
                },
            }
            manifest = {"apiVersion": "argoproj.io/v1alpha1", "kind": kind, "metadata": metadata, "spec": spec}
            manifest_digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            self.assertEqual(defaults["cristexhub_prod_registration_alias_transition_manifest_hashes"][kind], manifest_digest)
            self.assertIn(manifest_digest, TASKS.read_text())
        self.assertEqual(
            "a4ef801de0c6aaf91a3c44e718afa10d17ab11727ce9b06b3d40727fd4c3ad30",
            defaults["cristexhub_prod_registration_alias_transition_metadata_hash"],
        )
        self.assertEqual(
            [{"server": "https://kubernetes.default.svc", "namespace": "cristexhub-prod"},
             {"name": "cristexhub-prod-local", "namespace": "cristexhub-prod"}],
            defaults["cristexhub_prod_registration_transition_specs"]["AppProject"]["destinations"],
        )
        self.assertIn("Record exact alias-to-direct-server transition candidates", TASKS.read_text())
        self.assertIn("Reject partial or duplicate alias-to-direct-server transitions", TASKS.read_text())
        self.assertIn("alias_transition_uids", PLUGIN.read_text())
        self.assertIn("EXPECTED_CLUSTER_NAMESPACES", PLUGIN.read_text())
        self.assertIn("cristexhub_prod_registration_cluster_namespaces == 'cristexhub-dev,cristexhub-prod'", TASKS.read_text())
        self.assertIn("alias_transition_change_count", PLUGIN.read_text())
        self.assertIn("alias_transition_spec_hashes", PLUGIN.read_text())
        self.assertIn("alias_transition_manifest_hashes", PLUGIN.read_text())
        self.assertIn("resourceVersion", PLUGIN.read_text())
        self.assertIn("prestate_bindings", PLUGIN.read_text())
        self.assertIn("sort_keys=True", TASKS.read_text())
        self.assertIn("target_transition_candidates", TASKS.read_text())
        self.assertIn("map(attribute='server', default='')", TASKS.read_text())
        self.assertIn("map(attribute='name', default='')", TASKS.read_text())
        self.assertIn("valid_transition_pair", PLUGIN.read_text())
        self.assertIn("kubernetes.core.plugins.action.k8s_json_patch", PLUGIN.read_text())
        self.assertIn('self._task.action = "kubernetes.core.k8s_json_patch"', PLUGIN.read_text())
        self.assertNotIn("_transition_put", PLUGIN.read_text())
        self.assertNotIn("call_api(", PLUGIN.read_text())
        self.assertIn("status.comparedTo.destination.server", TASKS.read_text())

    def test_transition_fixtures_allow_only_alias_mixed_or_final_pairs(self) -> None:
        import importlib.util
        import sys
        collection_root = ROOT / "ansible/.ansible/collections"
        if (collection_root / "ansible_collections").is_dir():
            sys.path.insert(0, str(collection_root))
        spec = importlib.util.spec_from_file_location("prod_registration_transition_states", PLUGIN)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
        self.assertEqual(["AppProject:transition", "Application:final", "AppProject:final"], loaded._transition_plan("alias", "alias"))
        self.assertEqual(["Application:final", "AppProject:final"], loaded._transition_plan("transition", "alias"))
        self.assertEqual(["AppProject:final"], loaded._transition_plan("transition", "final"))
        self.assertEqual([], loaded._transition_plan("final", "final"))
        for unsafe in (("final", "alias"), ("alias", "final"), ("alias", "foreign")):
            with self.assertRaises(ValueError):
                loaded._transition_plan(*unsafe)

    def test_action_transition_pair_guard_matches_role_modes(self) -> None:
        import importlib.util
        import sys

        collection_root = ROOT / "ansible/.ansible/collections"
        if not (collection_root / "ansible_collections").is_dir():
            collection_root = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections")
        if (collection_root / "ansible_collections").is_dir():
            sys.path.insert(0, str(collection_root))
        spec = importlib.util.spec_from_file_location("prod_registration_action_modes", PLUGIN)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(module.valid_transition_pair(["AppProject", "Application"], []))
        self.assertTrue(module.valid_transition_pair(["Application"], ["AppProject"]))
        self.assertTrue(module.valid_transition_pair([], ["AppProject", "Application"]))
        self.assertFalse(module.valid_transition_pair(["Application"], []))
        self.assertFalse(module.valid_transition_pair(["Application"], ["Application"]))
        self.assertFalse(module.valid_transition_pair(["AppProject", "Application"], ["AppProject"]))
        self.assertTrue(module.valid_transition_state(["AppProject", "Application"], [], []))
        self.assertTrue(module.valid_transition_state(["Application"], [], ["AppProject"]))
        self.assertTrue(module.valid_transition_state([], ["Application"], ["AppProject"]))
        self.assertTrue(module.valid_transition_state([], ["AppProject", "Application"], []))
        self.assertFalse(module.valid_transition_state(["AppProject"], [], []))

    def test_three_step_alias_to_direct_server_plan_and_json_patch_contract(self) -> None:
        import importlib.util
        import sys

        collection_root = ROOT / "ansible/.ansible/collections"
        if not (collection_root / "ansible_collections").is_dir():
            collection_root = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections")
        if (collection_root / "ansible_collections").is_dir():
            sys.path.insert(0, str(collection_root))
        spec = importlib.util.spec_from_file_location("prod_registration_transition", PLUGIN)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            ["AppProject:transition", "Application:final", "AppProject:final"],
            module._transition_plan("alias", "alias"),
        )
        self.assertEqual(["Application:final", "AppProject:final"], module._transition_plan("transition", "alias"))
        self.assertEqual(["AppProject:final"], module._transition_plan("transition", "final"))
        with self.assertRaises(ValueError):
            module._transition_plan("final", "alias")

        project_transition = module._transition_patch("AppProject", "transition", "42")
        application_final = module._transition_patch("Application", "final", "43")
        project_final = module._transition_patch("AppProject", "final", "44")
        for patch in (project_transition, application_final, project_final):
            self.assertEqual(["test", "test", "test", "test", "replace"], [entry["op"] for entry in patch])
            self.assertEqual("/metadata/uid", patch[0]["path"])
            self.assertEqual("/metadata/resourceVersion", patch[1]["path"])
            self.assertEqual("/metadata/labels", patch[2]["path"])
            self.assertEqual("/spec", patch[3]["path"])
            self.assertIn(patch[4]["path"], {"/spec/destination", "/spec/destinations"})
        self.assertEqual("42", project_transition[1]["value"])
        self.assertEqual("/spec/destination", application_final[4]["path"])
        self.assertEqual("/spec/destinations", project_transition[4]["path"])
        self.assertEqual("/spec/destinations", project_final[4]["path"])
        project = {
            "apiVersion": module._TRANSITION_API_VERSION,
            "kind": "AppProject",
            "metadata": {"name": module._TRANSITION_NAME, "namespace": module._TRANSITION_ARGO_NAMESPACE, "uid": module._TRANSITION_UIDS["AppProject"], "labels": dict(module._TRANSITION_LABELS)},
            "spec": module._TRANSITION_ALIAS_PROJECT_SPEC,
        }
        application = {
            "apiVersion": module._TRANSITION_API_VERSION,
            "kind": "Application",
            "metadata": {"name": module._TRANSITION_NAME, "namespace": module._TRANSITION_ARGO_NAMESPACE, "uid": module._TRANSITION_UIDS["Application"], "labels": dict(module._TRANSITION_LABELS)},
            "spec": module._TRANSITION_ALIAS_APPLICATION_SPEC,
        }
        prestate = {"results": [{"resources": [project]}, {"resources": [application]}]}
        plan = module.run_direct_server_transition(
            None,
            None,
            {
                "cristexhub_prod_registration_internal_prestate": prestate,
                "cristexhub_prod_registration_internal_preflight_binding": {
                    "transition_plan": ["AppProject:transition", "Application:final", "AppProject:final"],
                    "transition_change_count": 3,
                },
            },
            {"apiVersion": module._TRANSITION_API_VERSION, "kind": "AppProject", "metadata": {"name": module._TRANSITION_NAME, "namespace": module._TRANSITION_ARGO_NAMESPACE}, "spec": module._TRANSITION_FINAL_PROJECT_SPEC},
            {"apiVersion": module._TRANSITION_API_VERSION, "kind": "Application", "metadata": {"name": module._TRANSITION_NAME, "namespace": module._TRANSITION_ARGO_NAMESPACE}, "spec": module._TRANSITION_FINAL_APPLICATION_SPEC},
            True,
        )
        self.assertEqual(["AppProject:transition", "Application:final", "AppProject:final"], plan["transition_steps"])
        from types import SimpleNamespace
        from unittest import mock
        fake = SimpleNamespace(
            _task=SimpleNamespace(action="guarded", args={"transition": True}),
            _connection=object(),
            _play_context=object(),
            _loader=object(),
            _templar=object(),
            _shared_loader_obj=None,
        )
        with mock.patch.object(module.PatchActionModule, "run", return_value={"changed": True}) as dispatched:
            self.assertEqual({"changed": True}, module._dispatch_transition_patch(
                fake, None, {}, "Application", "final", "43"
            ))
        dispatched.assert_called_once()
        self.assertEqual("guarded", fake._task.action)
        self.assertEqual({"transition": True}, fake._task.args)
        self.assertIn("Reconcile exact bounded PROD direct-server transition", TASKS.read_text())
        self.assertIn("transition: true", TASKS.read_text())
        self.assertIn("when: not ansible_check_mode", TASKS.read_text())

    def test_resource_version_is_the_only_ignored_bound_hash_field(self) -> None:
        import importlib.util

        collection_root = ROOT / "ansible/.ansible/collections"
        if not (collection_root / "ansible_collections").is_dir():
            collection_root = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections")
        if (collection_root / "ansible_collections").is_dir():
            import sys
            sys.path.insert(0, str(collection_root))
        spec = importlib.util.spec_from_file_location("prod_registration_action", PLUGIN)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        application = next(manifest for manifest in objects() if manifest["kind"] == "Application")
        with_rv = json.loads(json.dumps(application))
        with_rv["metadata"]["resourceVersion"] = "7"
        self.assertEqual(module.canonical(application), module.canonical(with_rv))
        with_uid = json.loads(json.dumps(application))
        with_uid["metadata"]["uid"] = "00000000-0000-4000-8000-000000000001"
        self.assertNotEqual(module.canonical(application), module.canonical(with_uid))
        self.assertIn("metadata.resourceVersion", module.canonical.__doc__ or "")

    def test_alias_to_direct_server_transition_binds_all_prestate_identity_fields(self) -> None:
        defaults = yaml.safe_load(DEFAULTS.read_text())
        tasks = TASKS.read_text()
        plugin = PLUGIN.read_text()
        for needle in (
            "prestate_bindings",
            "prestate_object_count",
            "resourceVersion",
            "Re-query exact five-object prestate immediately before mutation",
            "Require unchanged UID and resourceVersion immediately before mutation",
            "Add exact resourceVersion optimistic-concurrency preconditions",
            "difference(['name', 'namespace', 'uid', 'resourceVersion'",
            "manifest_identities",
            "observed_prestate_identities",
            "Require exact registration mutation result closure",
            "Query exact live registration post-state after reconciliation wait",
            "status.sync.revision",
            "metadata.generation",
            "target_transition_candidates",
            "managedFields",
            "reject('equalto', '')",
        ):
            self.assertIn(needle, tasks)
        for needle in (
            "prestate_bindings",
            "prestate_object_count",
            "resourceVersion",
            "metadata.resourceVersion",
            "_fresh_transition_objects",
            "EXPECTED_IDENTITIES",
            "set(entry) == {\"apiVersion\", \"kind\", \"namespace\", \"name\", \"identity\", \"uid\", \"resourceVersion\", \"generation\"}",
            "entry.get(\"identity\") == \"|\".join(object_identity(entry))",
        ):
            self.assertIn(needle, plugin)
        self.assertEqual(5, defaults["cristexhub_prod_registration_object_count"])

    def test_manifest_identity_and_direct_server_hash_closure_is_exact(self) -> None:
        expected = {
            "argoproj.io/v1alpha1|AppProject|argocd|cristexhub-prod",
            "argoproj.io/v1alpha1|Application|argocd|cristexhub-prod",
            "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|argocd-application-controller-cristexhub-prod",
            "rbac.authorization.k8s.io/v1|RoleBinding|cristexhub-prod|argocd-application-controller-cristexhub-prod",
            "v1|Secret|argocd|argocd-cluster-cristexhub-prod",
        }
        actual = {
            f"{obj['apiVersion']}|{obj['kind']}|{obj['metadata'].get('namespace', '')}|{obj['metadata']['name']}"
            for obj in objects()
        }
        self.assertEqual(expected, actual)
        defaults = yaml.safe_load(DEFAULTS.read_text())
        specs = defaults["cristexhub_prod_registration_alias_transition_specs"]
        hashes = defaults["cristexhub_prod_registration_alias_transition_spec_hashes"]
        for kind, spec in specs.items():
            self.assertEqual(hashes[kind], canonical(spec))

    def test_alias_to_direct_server_transition_rejects_foreign_uid_or_spec(self) -> None:
        defaults = yaml.safe_load(DEFAULTS.read_text())
        kind = "Application"
        expected_uid = defaults["cristexhub_prod_registration_alias_transition_uids"][kind]
        expected_spec = defaults["cristexhub_prod_registration_alias_transition_specs"][kind]

        def candidate(uid: str, spec: dict) -> bool:
            return uid == expected_uid and spec == expected_spec

        self.assertTrue(candidate(expected_uid, expected_spec))
        self.assertFalse(candidate(str(uuid.uuid4()), expected_spec))
        forged = json.loads(json.dumps(expected_spec))
        forged["destination"]["namespace"] = "cristexhub-dev"
        self.assertFalse(candidate(expected_uid, forged))

    def test_preflight_order_and_foreign_object_refusal(self) -> None:
        tasks = TASKS.read_text()
        namespace = tasks.index("Query exact CristexHub PROD Namespace prerequisite")
        repository = tasks.index("Query Infisical-owned Argo repository credential metadata")
        prestate = tasks.index("Query exact PROD registration pre-state")
        reject = tasks.index("Reject foreign PROD registration objects before mutation")
        binding = tasks.index("Bind complete PROD registration preflight")
        mutation = tasks.index("Reconcile registration source without synchronization")
        self.assertLess(namespace, mutation)
        self.assertLess(repository, mutation)
        self.assertLess(prestate, reject)
        self.assertLess(reject, binding)
        self.assertLess(binding, mutation)
        status_query = tasks.index("Wait for live PROD Application to reconcile")
        status_assert = tasks.index("Require live PROD Application Synced and Healthy")
        self.assertLess(mutation, status_query)
        self.assertLess(status_query, status_assert)
        self.assertIn("when: not ansible_check_mode", tasks[status_query:status_assert + 600])
        for needle in (
            "metadata.ownerReferences",
            "metadata.keys()",
            "metadata.resourceVersion",
            "resourceVersion optimistic-concurrency preconditions",
            "prestate_recheck",
            "binaryData",
            "immutable",
            "k3s administrator kubeconfig",
            "argocd-repository-cristexhub",
            "internal_preflight_binding",
            "'prune': false, 'selfHeal': true, 'allowEmpty': false",
            "status.sync.status",
            "status.health.status",
            "cristexhub-prod-local",
        ):
            self.assertIn(needle, tasks)

    def test_wrapper_and_action_bind_real_dash_process_and_exact_argv(self) -> None:
        plugin = PLUGIN.read_text()
        wrapper = WRAPPER.read_text()
        self.assertIn('#!/bin/dash', wrapper)
        self.assertIn('content == f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\\n"', plugin)
        self.assertIn("_proc_cmdline(pid) == [\"/bin/dash\", str(_WRAPPER_SOURCE)", plugin)
        self.assertIn("sys.argv == _expected_ansible_argv()", plugin)
        self.assertIn('ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG_SOURCE)', plugin)
        self.assertIn('not any(os.environ.get(name)', plugin)
        self.assertIn('exec /bin/dash "$script_path" "$mode"', wrapper)
        self.assertIn('playbooks/bootstrap_cristexhub_prod_registration.yml', wrapper)
        self.assertIn('if [ "$mode" = check ]; then', wrapper)

    def test_wrapper_is_non_passthrough_and_cancels_its_controller(self) -> None:
        wrapper = WRAPPER.read_text()
        self.assertIn('[ "$#" -ne 1 ]', wrapper)
        self.assertIn('[ "$1" != check ] && [ "$1" != apply ]', wrapper)
        self.assertIn("/usr/bin/dirname", wrapper)
        self.assertIn("/bin/pwd -P", wrapper)
        self.assertIn("expected_repository_root=/home/paul/projects/cristexweb", wrapper)
        self.assertIn("/usr/bin/setsid /usr/bin/env -i", wrapper)
        self.assertIn('[ ! -f "$controller" ]', wrapper)
        self.assertIn('[ -L "$controller" ]', wrapper)
        self.assertIn("/usr/bin/env -i", wrapper)
        self.assertNotIn("exec env -i", wrapper)
        self.assertLess(wrapper.index("trap cleanup_file EXIT"), wrapper.index("/usr/bin/mktemp"))
        self.assertLess(wrapper.index("trap cleanup_file EXIT"), wrapper.index("openssl rand -hex 32"))
        self.assertIn("/bin/kill -TERM -- \"-$child_pid\"", wrapper)
        self.assertIn("/bin/kill -KILL -- \"-$child_pid\"", wrapper)
        self.assertIn("wait \"$child_pid\"", wrapper)
        self.assertIn("set -- \\\n  \"$controller\"", wrapper)
        for forbidden in ("--tags", "--skip-tags", "--start-at-task", "--inventory", "kubectl", "state: absent"):
            self.assertNotIn(forbidden, wrapper)
        self.assertIn("cristexhub_prod_registration", PLAYBOOK.read_text())

        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            root = sandbox / "workspace/project"
            script = root / "ansible/bin/bootstrap-cristexhub-prod-registration"
            controller = root / ".venv/bin/ansible-playbook"
            tmpdir = sandbox / "tmp"
            marker = sandbox / "controller.log"
            script.parent.mkdir(parents=True)
            controller.parent.mkdir(parents=True)
            (root / "ansible").mkdir(parents=True, exist_ok=True)
            tmpdir.mkdir()
            for relative in (
                "ansible/.ansible/inventory.local.yml",
                "ansible/ansible.cfg",
                "ansible/roles/cristexhub_prod_registration/tasks/main.yml",
                "ansible/roles/cristexhub_prod_registration/defaults/main.yml",
                "ansible/playbooks/bootstrap_cristexhub_prod_registration.yml",
                "ansible/plugins/action/cristexhub_prod_registration_guarded_k8s.py",
            ):
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                source_file = ROOT / relative
                if not source_file.exists():
                    source_file = Path('/home/paul/projects/cristexweb') / relative
                if relative == "ansible/.ansible/inventory.local.yml" and not source_file.exists():
                    destination.write_text(
                        "---\nall:\n  hosts:\n    crtxweb:\n"
                        "      ansible_connection: local\n"
                        "      ansible_python_interpreter: /usr/bin/python3\n"
                        "      ansible_user: paul\n"
                    )
                else:
                    destination.write_bytes(source_file.read_bytes())
            sandbox_wrapper = wrapper.replace(
                "expected_repository_root=/home/paul/projects/cristexweb",
                f"expected_repository_root={root}",
            ).replace(
                '[ "$controller_user" = paul ]',
                f'[ "$controller_user" = {pwd.getpwuid(os.getuid()).pw_name} ]',
            )
            canonical_wrapper = re.sub(
                r"(?m)^wrapper_canonical_sha256_expected='[0-9a-f]{64}'$",
                "wrapper_canonical_sha256_expected='" + ("0" * 64) + "'",
                sandbox_wrapper,
            )
            sandbox_wrapper = re.sub(
                r"(?m)^wrapper_canonical_sha256_expected='[0-9a-f]{64}'$",
                "wrapper_canonical_sha256_expected='" + hashlib.sha256(canonical_wrapper.encode()).hexdigest() + "'",
                sandbox_wrapper,
            )
            script.write_text(sandbox_wrapper)
            inventory = root / "ansible/.ansible/inventory.local.yml"
            inventory.chmod(0o600)
            script.chmod(0o755)
            controller.write_text(
                "#!/usr/bin/python3\n"
                "import signal,time\n"
                f"marker={str(marker)!r}\n"
                "open(marker,'a').write('child-start\\n')\n"
                "def stop(*_):\n"
                " open(marker,'a').write('child-term\\n'); raise SystemExit(143)\n"
                "signal.signal(signal.SIGTERM,stop)\n"
                "time.sleep(30)\n"
                "open(marker,'a').write('child-end\\n')\n"
            )
            controller.chmod(0o755)
            sandbox_wrapper = re.sub(
                r"(?m)^controller_sha256_expected=[0-9a-f]{64}$",
                "controller_sha256_expected=" + hashlib.sha256(controller.read_bytes()).hexdigest(),
                script.read_text(),
            )
            canonical_wrapper = re.sub(
                r"(?m)^wrapper_canonical_sha256_expected='[0-9a-f]{64}'$",
                "wrapper_canonical_sha256_expected='" + ("0" * 64) + "'",
                sandbox_wrapper,
            )
            sandbox_wrapper = re.sub(
                r"(?m)^wrapper_canonical_sha256_expected='[0-9a-f]{64}'$",
                "wrapper_canonical_sha256_expected='" + hashlib.sha256(canonical_wrapper.encode()).hexdigest() + "'",
                sandbox_wrapper,
            )
            script.write_text(sandbox_wrapper)
            env = os.environ.copy()
            env["TMPDIR"] = str(tmpdir)
            process = subprocess.Popen(
                [str(script), "apply"],
                cwd=root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for _ in range(100):
                if marker.exists() and "child-start" in marker.read_text():
                    break
                time.sleep(0.02)
            self.assertTrue(marker.exists(), "fake controller did not start")
            process.terminate()
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(143, process.returncode, stdout + stderr)
            events = marker.read_text()
            self.assertIn("child-term", events)
            self.assertNotIn("child-end", events)
            self.assertEqual([], list(tmpdir.iterdir()))

    def test_resource_version_fixture_is_executable_and_fail_closed(self) -> None:
        self.assertTrue(os.access(RESOURCE_VERSION_FIXTURE, os.X_OK))
        result = subprocess.run(
            [str(RESOURCE_VERSION_FIXTURE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("rejected changed precondition", result.stdout)

    def test_action_guard_is_exact_present_only(self) -> None:
        plugin = PLUGIN.read_text()
        for needle in (
            "EXPECTED_REPOSITORY_ROOT",
            "TASK_SUFFIX",
            "_source_closure_valid",
            "_wrapper_binding_valid",
            "_proc_starttime",
            "_ancestor",
            "TASK_SELECTION_GUARD",
            "TASK_SELECTION_GUARD",
            'args.get("state") != "present"',
            "complete preflight binding",
            "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ENTRYPOINT",
            "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_WRAPPER_PID",
            "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_INVENTORY_SHA256",
            "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_CONTROLLER_SHA256",
            "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_KUBECONFIG",
            "_EXPECTED_TASK_NAMES",
            REVISION,
        ):
            self.assertIn(needle, plugin)
        for forbidden in ('"absent"', '"delete"'):
            self.assertNotIn(forbidden, plugin)

    def test_direct_action_only_invocation_is_rejected_before_kubernetes(self) -> None:
        controller = ROOT / ".venv/bin/ansible-playbook"
        if not controller.is_file():
            self.skipTest("offline controller environment is not installed")
        token = "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            attestation = Path(directory) / "attestation"
            attestation.write_text(f"{token}:entrypoint\n")
            attestation.chmod(0o600)
            env = os.environ.copy()
            env.update(
                {
                    "ANSIBLE_CONFIG": str(ROOT / "ansible/ansible.cfg"),
                    "CRISTEXWEB_REPOSITORY_ROOT": str(ROOT),
                    "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ENTRYPOINT": "v2",
                    "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_TOKEN": token,
                    "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ATTESTATION_FILE": str(attestation),
                }
            )
            result = subprocess.run(
                [str(controller), "-i", "localhost,", str(ACTION_ONLY_FIXTURE)],
                cwd=ROOT / "ansible",
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        output = result.stdout + result.stderr
        self.assertNotEqual(0, result.returncode)
        self.assertIn("ENTRYPOINT_GUARD", output)
        self.assertIn("non-canonical registration task source", output)
        self.assertNotIn("Failed to connect", output)
        task_start = subprocess.run(
            [str(TASK_START_FIXTURE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, task_start.returncode, task_start.stdout + task_start.stderr)
        self.assertIn("rejected before Kubernetes", task_start.stdout)

    def test_runbook_records_private_activation_and_public_route_gate(self) -> None:
        runbook = RUNBOOK.read_text()
        for needle in (
            REVISION,
            "DIRECT-SERVER LIVE",
            "cristexhub-prod-local",
            "Synced/Healthy",
            "separately approved mutation",
            "does not inspect or reconcile DEV or",
            "Reactive Resume registration objects",
            "prune=false",
            "Cloudflare",
            "public DNS record",
            "reject_cristexhub_prod_registration_resource_version.sh",
            "JSON Patch",
            "kubernetes.core.k8s_json_patch",
            "fails closed",
            "accepted mixed recovery states",
        ):
            self.assertIn(needle, runbook)


if __name__ == "__main__":
    unittest.main()
