from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = ROOT / "ansible/roles/argocd_cluster_cache_scope_transition/defaults/main.yml"
TASKS = ROOT / "ansible/roles/argocd_cluster_cache_scope_transition/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/argocd_cluster_cache_scope_transition_guarded_k8s.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-argocd-cluster-cache-scope-transition"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_argocd_cluster_cache_scope_transition.yml"
RUNBOOK = ROOT / "runbooks/argocd-cluster-cache-scope-transition.md"
TARGET_NAMESPACES = "cristexhub-dev,cristexhub-prod"

SOURCE_PATHS = (
    ROOT / "ansible/files/components/cristexhub-dev-registration/config/secret-cluster-cristexhub-dev.yaml",
    ROOT / "ansible/files/components/cristexhub-prod-registration/config/secret-cluster-cristexhub-prod.yaml",
    ROOT / "ansible/files/components/reactive-resume-dev-argocd-registration/config/secret-cluster-reactive-resume-dev.yaml",
)


def load_plugin():
    collection_root = ROOT / "ansible/.ansible/collections"
    import sys

    if not (collection_root / "ansible_collections").is_dir():
        collection_root = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections")
    if (collection_root / "ansible_collections").is_dir():
        sys.path.insert(0, str(collection_root))
    spec = importlib.util.spec_from_file_location("argocd_cluster_cache_scope_transition", PLUGIN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArgoClusterCacheScopeTransitionContractTests(unittest.TestCase):
    def test_exact_three_original_sources_are_final_shared_scope(self) -> None:
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(3, defaults["argocd_cluster_cache_scope_transition_object_count"])
        self.assertEqual(TARGET_NAMESPACES, defaults["argocd_cluster_cache_scope_transition_expected_target_namespaces"])
        entries = defaults["argocd_cluster_cache_scope_transition_sources"]
        self.assertEqual({path.name for path in SOURCE_PATHS}, {Path(entry["path"]).name for entry in entries})
        for entry, path in zip(entries, SOURCE_PATHS):
            manifest = yaml.safe_load(path.read_text())
            self.assertEqual("Secret", manifest["kind"])
            self.assertEqual("Opaque", manifest["type"])
            self.assertEqual(
                {"name", "server", "namespaces", "clusterResources", "config"},
                set(manifest["stringData"]),
            )
            self.assertEqual(TARGET_NAMESPACES, manifest["stringData"]["namespaces"])
            self.assertEqual(entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertNotIn("data", manifest)
            self.assertNotIn("binaryData", manifest)

    def test_rendered_source_paths_are_single_exact_files_without_folded_space(self) -> None:
        defaults = yaml.safe_load(DEFAULTS.read_text())
        for entry in defaults["argocd_cluster_cache_scope_transition_sources"]:
            rendered = entry["path"].replace(
                "{{ argocd_cluster_cache_scope_transition_repository_root }}",
                str(ROOT),
            )
            self.assertEqual(rendered, " ".join(rendered.split()))
            self.assertNotIn("components/ ", rendered)
            self.assertTrue(rendered.startswith(str(ROOT / "ansible/files/components/")))
            self.assertTrue(Path(rendered).name.startswith("secret-cluster-"))

    def test_metadata_inventory_never_requests_secret_json_values(self) -> None:
        module = ROOT / "ansible/library/argocd_cluster_cache_secret_metadata.py"
        text = module.read_text()
        self.assertIn("PartialObjectMetadataList", text)
        self.assertIn('meta.k8s.io/v1', text)
        self.assertIn('PartialObjectMetadata', text)
        self.assertIn("metadata_only=True", text)
        self.assertNotIn("read_namespaced_secret", text)
        tasks = TASKS.read_text()
        self.assertIn("argocd_cluster_cache_secret_metadata:", tasks)
        self.assertIn("label_selector: 'argocd.argoproj.io/secret-type=cluster'", tasks)
        self.assertIn("items | length == 3", tasks)
        self.assertIn("item.stringData.keys() | list | sort", tasks)
        self.assertIn("map(attribute='apiVersion')", tasks)

    def test_strict_approval_accepts_only_canonical_boolean_forms(self) -> None:
        module = load_plugin()

        class _AnsibleTaggedBool:
            def __bool__(self):
                return True

        class _AnsibleTaggedStr(str):
            pass

        self.assertTrue(module._strict_true(True))
        self.assertTrue(module._strict_true(_AnsibleTaggedBool()))
        self.assertTrue(module._strict_true(_AnsibleTaggedStr("true")))
        for value in (False, 1, "true", "yes", _AnsibleTaggedStr("yes"), None):
            self.assertFalse(module._strict_true(value))

    def test_wrapper_contract_uses_dash_newline_and_exact_argv_binding(self) -> None:
        plugin = PLUGIN.read_text()
        wrapper = WRAPPER.read_text()
        self.assertIn('#!/bin/dash', wrapper)
        self.assertIn('content == f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\\n"', plugin)
        self.assertIn("_proc_cmdline(pid) == [\"/bin/dash\", str(_WRAPPER_SOURCE)", plugin)
        self.assertIn("sys.argv == _expected_ansible_argv()", plugin)
        self.assertIn('ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG_SOURCE)', plugin)
        self.assertIn('not any(os.environ.get(name)', plugin)
        self.assertIn('exec /bin/dash "$script_path" "$mode"', wrapper)

    def test_source_closure_pins_controller_and_python_identity(self) -> None:
        plugin = PLUGIN.read_text()
        self.assertIn('_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"', plugin)
        self.assertIn('_PYTHON_SHA256 = "17b78e0a93175e86f9ac03141924fd7a7f0c0c52e66b34bfa0de20ffef989df1"', plugin)
        self.assertIn('stat.S_IMODE(controller_state.st_mode) == 0o775', plugin)
        self.assertIn('stat.S_IMODE(_PYTHON_SOURCE.resolve().stat(follow_symlinks=False).st_mode) == 0o755', plugin)
        self.assertIn('Path(__file__).absolute() != _ACTION_SOURCE', plugin)

    def test_source_closure_and_wrapper_process_binding_are_pinned(self) -> None:
        module = load_plugin()
        self.assertTrue(module._source_closure_valid())
        self.assertNotEqual("0" * 64, module._ACTION_CANONICAL_SHA256)
        self.assertNotEqual("0" * 64, module._WRAPPER_CANONICAL_SHA256)
        self.assertNotEqual("0" * 64, module._TASK_SHA256)
        plugin = PLUGIN.read_text()
        wrapper = WRAPPER.read_text()
        for needle in (
            "_proc_starttime", "_ancestor", "WRAPPER_PID", "WRAPPER_STARTTIME",
            "WRAPPER_PATH", "WRAPPER_SHA256", "_canonical_file_hash",
            "_TASK_SHA256", "_DEFAULTS_SHA256", "_PLAYBOOK_SHA256",
            "_INVENTORY_SHA256", "_ANSIBLE_CONFIG_SHA256", "_METADATA_MODULE_SHA256",
            "_CONTROLLER_SOURCE", "_PYTHON_SOURCE", "_KUBECONFIG_SOURCE",
            "_EXPECTED_OPERATOR", "_EXPECTED_TASK_NAME", "_EXPECTED_TASK_ACTION",
        ):
            self.assertIn(needle, plugin)
        for needle in (
            "wrapper_pid=$$", "wrapper_starttime=", "WRAPPER_PID=",
            "WRAPPER_STARTTIME=", "WRAPPER_PATH=", "WRAPPER_SHA256=",
            "TASK_SHA256=", "DEFAULTS_SHA256=", "PLAYBOOK_SHA256=",
            "INVENTORY_SHA256=", "ANSIBLE_CONFIG_SHA256=", "METADATA_MODULE_SHA256=",
            "CONTROLLER_SHA256=", "PYTHON_SHA256=", "KUBECONFIG=", "OPERATOR=",
        ):
            self.assertIn(needle, wrapper)

    def test_plugin_target_hashes_and_patch_are_exact_scope_only(self) -> None:
        module = load_plugin()
        self.assertEqual({"/metadata/uid", "/metadata/resourceVersion", "/data/namespaces"}, {op["path"] for op in module.transition_patch(
            {
                "apiVersion": "v1", "kind": "Secret", "namespace": "argocd",
                "name": "argocd-cluster-cristexhub-dev",
                "identity": "v1|Secret|argocd|argocd-cluster-cristexhub-dev",
                "uid": "01234567-89ab-cdef-0123-456789abcdef",
                "resourceVersion": "42", "legacy_namespaces": "cristexhub-dev",
                "target_namespaces": TARGET_NAMESPACES, "observed_namespaces": "cristexhub-dev",
            },
            yaml.safe_load(SOURCE_PATHS[0].read_text()),
        )})
        patch = module.transition_patch(
            {
                "apiVersion": "v1", "kind": "Secret", "namespace": "argocd",
                "name": "argocd-cluster-cristexhub-dev",
                "identity": "v1|Secret|argocd|argocd-cluster-cristexhub-dev",
                "uid": "01234567-89ab-cdef-0123-456789abcdef",
                "resourceVersion": "42", "legacy_namespaces": "cristexhub-dev",
                "target_namespaces": TARGET_NAMESPACES, "observed_namespaces": "cristexhub-dev",
            },
            yaml.safe_load(SOURCE_PATHS[0].read_text()),
        )
        self.assertEqual(["test", "test", "test", "replace"], [op["op"] for op in patch])
        self.assertEqual(["/metadata/uid", "/metadata/resourceVersion", "/data/namespaces", "/data/namespaces"], [op["path"] for op in patch])
        self.assertEqual(base64.b64encode(b"cristexhub-dev").decode(), patch[2]["value"])
        self.assertEqual(base64.b64encode(TARGET_NAMESPACES.encode()).decode(), patch[3]["value"])
        self.assertNotIn("/data/name", {op["path"] for op in patch})
        self.assertNotIn("/metadata/labels", {op["path"] for op in patch})

    def test_patch_rejects_foreign_or_final_state(self) -> None:
        module = load_plugin()
        binding = {
            "apiVersion": "v1", "kind": "Secret", "namespace": "argocd",
            "name": "argocd-cluster-cristexhub-prod",
            "identity": "v1|Secret|argocd|argocd-cluster-cristexhub-prod",
            "uid": "01234567-89ab-cdef-0123-456789abcdef",
            "resourceVersion": "42", "legacy_namespaces": "cristexhub-prod",
            "target_namespaces": TARGET_NAMESPACES, "observed_namespaces": TARGET_NAMESPACES,
        }
        with self.assertRaises(ValueError):
            module.transition_patch(binding, yaml.safe_load(SOURCE_PATHS[1].read_text()))
        binding["observed_namespaces"] = "foreign"
        with self.assertRaises(ValueError):
            module.transition_patch(binding, yaml.safe_load(SOURCE_PATHS[1].read_text()))

    def test_role_isolated_from_stale_registration_and_rr_dependencies(self) -> None:
        text = TASKS.read_text()
        self.assertEqual(2, text.count("kubernetes.core.k8s_info:"))
        self.assertIn("kind: Secret", text)
        self.assertNotIn("Application", text)
        self.assertNotIn("AppProject", text)
        self.assertNotIn("reactive_resume_dev", text)
        self.assertNotIn("repository credential", text.lower())
        self.assertIn("no_log: true", text)
        self.assertIn("resourceVersion", text)
        self.assertIn("ownerReferences", text)
        self.assertIn("argocd_cluster_cache_scope_transition_internal_legacy_bindings", text)
        self.assertIn("argocd_cluster_cache_scope_transition_internal_target_bindings", text)
        self.assertIn("when: not ansible_check_mode", text)
        self.assertIn("argocd_cluster_cache_scope_transition_guarded_k8s:", text)

    def test_wrapper_rejects_invalid_invocation_without_starting_ansible(self) -> None:
        result = subprocess.run(
            [str(WRAPPER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(64, result.returncode)
        self.assertIn("refusing passthrough arguments", result.stderr)
        result = subprocess.run(
            [str(WRAPPER), "unexpected"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(64, result.returncode)
        self.assertNotIn("PLAY ", result.stdout + result.stderr)

    def test_wrapper_and_playbook_are_non_passthrough_and_attested(self) -> None:
        wrapper = WRAPPER.read_text()
        self.assertTrue(WRAPPER.stat().st_mode & stat.S_IXUSR)
        self.assertIn("check|apply", wrapper)
        self.assertIn("env -i", wrapper)
        self.assertIn("--diff", wrapper)
        self.assertIn("--limit crtxweb", wrapper)
        self.assertIn("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_TOKEN", wrapper)
        self.assertIn("CRISTEXWEB_ARGO_CLUSTER_CACHE_SCOPE_TRANSITION_ATTESTATION_FILE", wrapper)
        self.assertIn("rm -f", wrapper)
        self.assertNotIn("--tags", wrapper)
        self.assertNotIn("--start-at-task", wrapper)
        self.assertIn("argocd_cluster_cache_scope_transition", PLAYBOOK.read_text())
        self.assertIn("one-time", RUNBOOK.read_text())
        self.assertIn("No live check or apply is implied", RUNBOOK.read_text())

    def test_action_and_source_are_value_suppressed(self) -> None:
        plugin = PLUGIN.read_text()
        tasks = TASKS.read_text()
        self.assertIn("kubernetes.core.k8s_json_patch", plugin)
        self.assertIn('"/data/namespaces"', plugin)
        self.assertIn('"/metadata/resourceVersion"', plugin)
        self.assertIn("set(args) != ARGS", plugin)
        self.assertIn("source_sha256", plugin)
        self.assertIn("no_log: true", tasks)
        self.assertNotIn("print(", plugin)
        self.assertNotIn("debug:", tasks)

    def test_no_unintended_files_or_source_definitions(self) -> None:
        self.assertTrue((ROOT / "ansible/roles/argocd_cluster_cache_scope_transition/defaults/main.yml").is_file())
        self.assertTrue((ROOT / "ansible/roles/argocd_cluster_cache_scope_transition/tasks/main.yml").is_file())
        self.assertTrue(PLUGIN.is_file())
        self.assertEqual(3, len(SOURCE_PATHS))


if __name__ == "__main__":
    unittest.main()
