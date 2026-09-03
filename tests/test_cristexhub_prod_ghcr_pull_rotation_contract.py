from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import sys
import time
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
COMPONENT = ANSIBLE / "files/components/cristexhub-prod-ghcr-pull-rotation"
MANIFEST = COMPONENT / "SOURCE-CLOSURE.sha256"
WRAPPER = ANSIBLE / "bin/check-cristexhub-prod-ghcr-pull-rotation"
TASKS = ANSIBLE / "roles/cristexhub_prod_ghcr_pull_rotation_preflight/tasks/main.yml"
DEFAULTS = ANSIBLE / "roles/cristexhub_prod_ghcr_pull_rotation_preflight/defaults/main.yml"
PLAYBOOK = ANSIBLE / "playbooks/check_cristexhub_prod_ghcr_pull_rotation.yml"
MODULE = ANSIBLE / "library/cristexhub_prod_ghcr_pull_secret_metadata.py"
POLICY = ANSIBLE / "files/policies/cristexhub-prod-ghcr-pull-rotation.yml"
STRATEGY = ANSIBLE / "plugins/strategy/cristexhub_prod_ghcr_pull_rotation_guarded_linear.py"
CONFIG = ANSIBLE / "ansible.cfg"
INVENTORY = ANSIBLE / "inventory/hosts.yml"
REQUIREMENTS = ANSIBLE / "requirements.yml"
COLLECTION_MANIFEST = ANSIBLE / ".ansible/collections/ansible_collections/kubernetes/core/MANIFEST.json"
COLLECTION_FILES = ANSIBLE / ".ansible/collections/ansible_collections/kubernetes/core/FILES.json"
INFISICAL_SOURCE = ANSIBLE / "files/components/infisical-cristexhub-prod-runtime/source/cristexhub-prod-runtime-static-secret.yaml"
RUNBOOK = ROOT / "runbooks/cristexhub-prod-ghcr-pull-rotation.md"


class CristexHubProdGhcrPullRotationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wrapper = WRAPPER.read_text()
        cls.tasks = TASKS.read_text()
        cls.defaults = yaml.safe_load(DEFAULTS.read_text())
        cls.playbook = yaml.safe_load(PLAYBOOK.read_text())
        cls.policy = yaml.safe_load(POLICY.read_text())
        cls.infisical_source = yaml.safe_load(INFISICAL_SOURCE.read_text())
        cls.runbook = RUNBOOK.read_text()
        cls.manifest_lines = MANIFEST.read_text().splitlines()

    def test_exact_source_closure_and_modes(self) -> None:
        self.assertEqual(0o755, stat.S_IMODE(WRAPPER.stat().st_mode))
        self.assertEqual(0o644, stat.S_IMODE(MANIFEST.stat().st_mode))
        expected = {
            "ansible/roles/cristexhub_prod_ghcr_pull_rotation_preflight/tasks/main.yml": TASKS,
            "ansible/roles/cristexhub_prod_ghcr_pull_rotation_preflight/defaults/main.yml": DEFAULTS,
            "ansible/playbooks/check_cristexhub_prod_ghcr_pull_rotation.yml": PLAYBOOK,
            "ansible/library/cristexhub_prod_ghcr_pull_secret_metadata.py": MODULE,
            "ansible/files/policies/cristexhub-prod-ghcr-pull-rotation.yml": POLICY,
            "ansible/plugins/strategy/cristexhub_prod_ghcr_pull_rotation_guarded_linear.py": STRATEGY,
        }
        self.assertEqual(set(expected), {line.split(maxsplit=1)[1] for line in self.manifest_lines})
        self.assertEqual(6, len(self.manifest_lines))
        for line in self.manifest_lines:
            digest, relative = line.split(maxsplit=1)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            path = ROOT / relative
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(0o644, stat.S_IMODE(path.stat().st_mode))

    def test_wrapper_canonical_hash_and_source_manifest_pin(self) -> None:
        manifest_digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
        self.assertIn(f"source_manifest_expected='{manifest_digest}'", self.wrapper)
        match = re.search(r"^wrapper_canonical_sha256_expected='([0-9a-f]{64})'$", self.wrapper, re.MULTILINE)
        self.assertIsNotNone(match)
        canonical = re.sub(
            r"^source_manifest_expected='[0-9a-f]{64}'$",
            "source_manifest_expected='" + "0" * 64 + "'",
            self.wrapper,
            flags=re.MULTILINE,
        )
        canonical = re.sub(
            r"^wrapper_canonical_sha256_expected='[0-9a-f]{64}'$",
            "wrapper_canonical_sha256_expected='" + "0" * 64 + "'",
            canonical,
            flags=re.MULTILINE,
        )
        self.assertEqual(match.group(1), hashlib.sha256(canonical.encode()).hexdigest())

    def test_wrapper_canonicalizer_uses_exactly_64_zero_placeholders(self) -> None:
        for prefix in (
            "s/^source_manifest_expected=",
            "s/^wrapper_canonical_sha256_expected=",
        ):
            line = next(line for line in self.wrapper.splitlines() if prefix in line)
            placeholder = re.search(r"\\x27(0+)\\x27", line)
            self.assertIsNotNone(placeholder, line)
            self.assertEqual(64, len(placeholder.group(1)), line)

    def test_shell_canonicalizer_handles_both_quote_styles_and_rejects_malformed_sentinel(self) -> None:
        sha_stdin = re.search(r"(?ms)^sha_stdin\(\) \{.*?^\}", self.wrapper)
        canonical_file_sha = re.search(r"(?ms)^canonical_file_sha\(\) \{.*?^\}", self.wrapper)
        self.assertIsNotNone(sha_stdin)
        self.assertIsNotNone(canonical_file_sha)
        probe_source = "\n".join(
            (
                "#!/bin/sh",
                "set -eu",
                "sha_tool=/usr/bin/sha256sum",
                "sed_tool=/usr/bin/sed",
                sha_stdin.group(0),
                canonical_file_sha.group(0),
                'canonical_file_sha "$1" "$2"',
                "",
            )
        )
        pattern = re.compile(
            r"(?m)^(_STRATEGY_CANONICAL_SHA256\s*=\s*)(['\"])([0-9a-f]{64})(\2)(\s*)$"
        )
        with tempfile.TemporaryDirectory() as temporary:
            probe = Path(temporary) / "probe.sh"
            probe.write_text(probe_source)
            probe.chmod(0o755)
            for quote, value in (("'", "a" * 64), ('"', "b" * 64)):
                fixture = Path(temporary) / f"fixture-{ord(quote)}"
                content = f"_STRATEGY_CANONICAL_SHA256 = {quote}{value}{quote}\n"
                fixture.write_text(content)
                match = pattern.match(content.rstrip("\n"))
                self.assertIsNotNone(match)
                canonical = (
                    match.group(1)
                    + match.group(2)
                    + "0" * 64
                    + match.group(4)
                    + match.group(5)
                    + "\n"
                )
                expected = hashlib.sha256(canonical.encode()).hexdigest()
                result = subprocess.run(
                    ["/bin/dash", str(probe), str(fixture), "_STRATEGY_CANONICAL_SHA256"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(expected, result.stdout.strip())
            malformed = Path(temporary) / "malformed"
            malformed_content = "_STRATEGY_CANONICAL_SHA256 = `" + "c" * 64 + "`\n"
            malformed.write_text(malformed_content)
            result = subprocess.run(
                ["/bin/dash", str(probe), str(malformed), "_STRATEGY_CANONICAL_SHA256"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(hashlib.sha256(malformed_content.encode()).hexdigest(), result.stdout.strip())

    def test_strategy_accepts_dash_via_bin_sh_but_rejects_other_executables(self) -> None:
        spec = importlib.util.spec_from_file_location("ghcr_rotation_strategy_test", STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        strategy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strategy)
        self.assertIn("/bin/sh", {"/bin/sh", "/bin/dash"})
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary) / "dash-child.sh"
            script.write_text("#!/bin/sh\nwhile :; do sleep 1; done\n")
            script.chmod(0o755)
            process = subprocess.Popen(["/bin/sh", str(script)])
            try:
                for _ in range(40):
                    if Path(f"/proc/{process.pid}/exe").exists():
                        break
                    time.sleep(0.025)
                self.assertTrue(
                    strategy._canonical_shell(
                        process.pid,
                        ["/bin/sh", str(script), "check"],
                    )
                )
                self.assertFalse(
                    strategy._canonical_shell(
                        process.pid,
                        ["/bin/bash", str(script), "check"],
                    )
                )
            finally:
                process.terminate()
                process.wait(timeout=3)

    def test_clean_environment_keeps_two_consecutive_collection_starts_exact_and_cache_free(self) -> None:
        source_root = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core")
        if not source_root.is_dir():
            self.skipTest("pinned kubernetes.core installation is not available")
        controller_python = Path(sys.executable)
        try:
            subprocess.run(
                [controller_python, "-c", "import ansible"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("controller Python cannot import ansible")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            collection_root = root / "ansible_collections/kubernetes/core"
            shutil.copytree(source_root, collection_root, symlinks=True)
            files_manifest = json.loads((collection_root / "FILES.json").read_text(encoding="utf-8"))
            expected_tree = {
                item["name"]: item["ftype"]
                for item in files_manifest["files"]
                if item["name"] != "."
            }
            expected_tree.update({"FILES.json": "file", "MANIFEST.json": "file"})

            def tree_snapshot() -> dict[str, str]:
                snapshot: dict[str, str] = {}
                for entry in collection_root.rglob("*"):
                    relative = entry.relative_to(collection_root).as_posix()
                    if entry.is_symlink() or entry.is_file():
                        snapshot[relative] = "file"
                    elif entry.is_dir():
                        snapshot[relative] = "dir"
                    else:
                        self.fail(f"unexpected collection filesystem entry: {relative}")
                return snapshot

            self.assertEqual(expected_tree, tree_snapshot())
            self.assertFalse(any("__pycache__" in entry for entry in expected_tree))
            startup = (
                "import importlib; "
                "importlib.import_module('ansible_collections.kubernetes.core.plugins.action.k8s_info'); "
                "importlib.import_module('ansible_collections.kubernetes.core.plugins.modules.k8s_info')"
            )
            environment = {
                **os.environ,
                "PYTHONPATH": str(root),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            for attempt in range(2):
                with self.subTest(attempt=attempt + 1):
                    result = subprocess.run(
                        [str(controller_python), "-c", startup],
                        cwd=root,
                        env=environment,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(0, result.returncode, result.stderr)
                    actual_tree = tree_snapshot()
                    self.assertEqual(expected_tree, actual_tree)
                    self.assertFalse(any("__pycache__" in entry for entry in actual_tree))
                    self.assertEqual([], list(collection_root.rglob("*.pyc")))

    def test_collection_toolchain_matches_pinned_files_manifest(self) -> None:
        source_root = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core")
        if not source_root.is_dir():
            self.skipTest("pinned kubernetes.core installation is not available")
        spec = importlib.util.spec_from_file_location("ghcr_rotation_collection_test", STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        strategy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strategy)
        with tempfile.TemporaryDirectory() as directory:
            collection_root = Path(directory) / "core"
            shutil.copytree(source_root, collection_root, symlinks=True)
            for pycache in collection_root.rglob("__pycache__"):
                shutil.rmtree(pycache)
            patches = {
                "_COLLECTION_ROOT": collection_root,
                "_COLLECTION_MANIFEST_SOURCE": collection_root / "MANIFEST.json",
                "_COLLECTION_FILES_SOURCE": collection_root / "FILES.json",
            }
            with mock.patch.multiple(strategy, **patches):
                self.assertTrue(strategy._collection_toolchain_valid())

    def test_collection_toolchain_rejects_adversarial_temp_copy_mutations(self) -> None:
        source_root = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core")
        if not source_root.is_dir():
            self.skipTest("pinned kubernetes.core installation is not available")
        spec = importlib.util.spec_from_file_location("ghcr_rotation_collection_adversarial_test", STRATEGY)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        strategy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strategy)
        mutations = (
            ("plugins/action/k8s.py", "replace"),
            ("plugins/action/k8s_info.py", "replace"),
            ("plugins/modules/k8s_info.py", "replace"),
            ("plugins/modules/__init__.py", "replace"),
            ("plugins/module_utils/version.py", "replace"),
            ("__init__.py", "extra"),
            ("plugins/__init__.py", "extra"),
            ("plugins/action/__init__.py", "extra"),
            ("plugins/modules/evil.so", "extra"),
            ("plugins/action/__pycache__/evil.pyc", "extra"),
        )
        for relative, kind in mutations:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                collection_root = Path(directory) / "core"
                shutil.copytree(source_root, collection_root, symlinks=True)
                for pycache in collection_root.rglob("__pycache__"):
                    shutil.rmtree(pycache)
                patches = {
                    "_COLLECTION_ROOT": collection_root,
                    "_COLLECTION_MANIFEST_SOURCE": collection_root / "MANIFEST.json",
                    "_COLLECTION_FILES_SOURCE": collection_root / "FILES.json",
                }
                with mock.patch.multiple(strategy, **patches):
                    self.assertTrue(strategy._collection_toolchain_valid())
                    victim = collection_root / relative
                    victim.parent.mkdir(parents=True, exist_ok=True)
                    if victim.is_symlink():
                        victim.unlink()
                    if kind == "extra" and relative.endswith("evil.pyc"):
                        victim.write_bytes(b"malicious bytecode")
                    else:
                        victim.write_bytes(b"malicious collection content")
                    victim.chmod(0o644)
                    self.assertFalse(strategy._collection_toolchain_valid())

    def test_collection_package_initializers_and_native_artifacts_are_not_unchecked(self) -> None:
        source_root = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core")
        if not source_root.is_dir():
            self.skipTest("pinned kubernetes.core installation is not available")
        strategy_spec = importlib.util.spec_from_file_location("ghcr_rotation_collection_init_test", STRATEGY)
        self.assertIsNotNone(strategy_spec)
        self.assertIsNotNone(strategy_spec.loader)
        strategy = importlib.util.module_from_spec(strategy_spec)
        strategy_spec.loader.exec_module(strategy)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            collection_root = root / "ansible_collections/kubernetes/core"
            shutil.copytree(source_root, collection_root, symlinks=True)
            for pycache in collection_root.rglob("__pycache__"):
                shutil.rmtree(pycache)
            marker = root / "executed"
            victim = collection_root / "plugins/__init__.py"
            victim.write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed')\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import importlib; importlib.import_module('ansible_collections.kubernetes.core.plugins')",
                ],
                cwd=root,
                env={**os.environ, "PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1"},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("executed", marker.read_text(encoding="utf-8"))
            with mock.patch.multiple(
                strategy,
                _COLLECTION_ROOT=collection_root,
                _COLLECTION_MANIFEST_SOURCE=collection_root / "MANIFEST.json",
                _COLLECTION_FILES_SOURCE=collection_root / "FILES.json",
            ):
                self.assertFalse(strategy._collection_toolchain_valid())

    def test_assert_loops_execute_before_malformed_kubeconfig_api_boundary(self) -> None:
        """Exercise both looped assertions with Ansible 2.19 before an API parse failure."""
        tasks = yaml.safe_load(self.tasks)
        source_task = deepcopy(
            next(task for task in tasks if task.get("name") == "Require regular and mode-correct GHCR rotation source leaves")
        )
        workload_task = deepcopy(
            next(task for task in tasks if task.get("name") == "Require immutable images, exact pull Secret, and current readiness")
        )
        for task in (source_task, workload_task):
            self.assertIn("loop", task)
            self.assertIn("loop_control", task)
            self.assertNotIn("loop", task["ansible.builtin.assert"])
            self.assertNotIn("loop_control", task["ansible.builtin.assert"])
            self.assertTrue(task.get("no_log"))

        source_items = [
            {
                "item": f"/tmp/ghcr-source-{index}",
                "stat": {
                    "isreg": True,
                    "islnk": False,
                    "mode": "0644",
                    "checksum": "a" * 64,
                },
            }
            for index in range(7)
        ]
        names = ["backend", "celery-worker", "frontend", "oauth2-proxy", "redis"]

        def deployment_result(name: str) -> dict[str, object]:
            deployment = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": name,
                    "namespace": "cristexhub-prod",
                    "uid": "b" * 32,
                    "resourceVersion": "1",
                    "generation": 1,
                    "annotations": {"deployment.kubernetes.io/revision": "1"},
                    "labels": {"app.kubernetes.io/name": name, "app.kubernetes.io/part-of": "cristexhub"},
                    "ownerReferences": [],
                },
                "spec": {
                    "selector": {"matchLabels": {"app.kubernetes.io/name": name}},
                    "replicas": 1,
                    "template": {
                        "spec": {
                            "containers": [{"image": f"registry.example/{name}@sha256:{'c' * 64}"}],
                        }
                    },
                },
                "status": {
                    "observedGeneration": 1,
                    "replicas": 1,
                    "updatedReplicas": 1,
                    "availableReplicas": 1,
                    "readyReplicas": 1,
                    "unavailableReplicas": 0,
                    "conditions": [
                        {"type": "Available", "status": "True"},
                        {"type": "Progressing", "status": "True"},
                    ],
                },
            }
            if name in {"backend", "celery-worker", "frontend"}:
                deployment["spec"]["template"]["spec"]["imagePullSecrets"] = [
                    {"name": "cristexhub-prod-ghcr-pull"}
                ]
            return {"item": name, "resources": [deployment]}

        deployment_results = [deployment_result(name) for name in names]
        inventory = {"resources": [result["resources"][0] for result in deployment_results]}

        controller = ROOT / ".venv/bin/ansible-playbook"
        if not controller.is_file():
            controller = Path("/home/paul/projects/cristexweb/.venv/bin/ansible-playbook")
        if not controller.is_file():
            self.skipTest("offline controller environment is not installed")
        collection_path = ANSIBLE / ".ansible/collections"
        if not (collection_path / "ansible_collections/kubernetes/core").is_dir():
            collection_path = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections")
        if not (collection_path / "ansible_collections/kubernetes/core").is_dir():
            self.skipTest("pinned kubernetes.core collection is not available")
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            malformed_kubeconfig = temporary_root / "malformed-kubeconfig"
            malformed_kubeconfig.write_text("not: [valid kubeconfig\n", encoding="utf-8")
            fixture = temporary_root / "ghcr-loop-execution.yml"
            fixture.write_text(
                yaml.safe_dump(
                    [
                        {
                            "name": "Exercise GHCR assert loops before the API boundary",
                            "hosts": "localhost",
                            "gather_facts": False,
                            "connection": "local",
                            "vars": {
                                "cristexhub_prod_ghcr_pull_rotation_preflight_internal_source_states": {
                                    "results": source_items
                                },
                                "cristexhub_prod_ghcr_pull_rotation_preflight_internal_deployments": {
                                    "results": deployment_results
                                },
                                "cristexhub_prod_ghcr_pull_rotation_preflight_internal_deployment_inventory": inventory,
                                "cristexhub_prod_ghcr_pull_rotation_preflight_private_deployments": [
                                    "backend", "celery-worker", "frontend"
                                ],
                                "cristexhub_prod_ghcr_pull_rotation_preflight_public_deployments": [
                                    "oauth2-proxy", "redis"
                                ],
                            },
                            "tasks": [
                                source_task,
                                workload_task,
                                {
                                    "name": "Probe malformed kubeconfig pre-API boundary",
                                    "kubernetes.core.k8s_info": {
                                        "api_version": "v1",
                                        "kind": "Namespace",
                                        "name": "pre-api-probe",
                                        "kubeconfig": str(malformed_kubeconfig),
                                    },
                                    "register": "malformed_kubeconfig_probe",
                                    "ignore_errors": True,
                                    "changed_when": False,
                                },
                                {
                                    "name": "Confirm GHCR assert loop tasks reached pre-API boundary",
                                    "ansible.builtin.assert": {
                                        "that": ["true"]
                                    },
                                },
                            ],
                        }
                    ],
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            environment = {
                **os.environ,
                "ANSIBLE_CONFIG": str(CONFIG),
                "ANSIBLE_COLLECTIONS_PATH": str(collection_path),
                "ANSIBLE_NOCOLOR": "1",
                "ANSIBLE_LOCALHOST_WARNING": "false",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            result = subprocess.run(
                [str(controller), "-i", "localhost,", str(fixture), "--check", "--diff"],
                cwd=ANSIBLE,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            output = result.stdout + result.stderr
            self.assertEqual(0, result.returncode, output)
            self.assertIn("Probe malformed kubeconfig pre-API boundary", output)
            self.assertIn("Confirm GHCR assert loop tasks reached pre-API boundary", output)
            self.assertNotIn("Unsupported parameters for (assert) module: loop", output)
            self.assertNotIn("loop is not a valid parameter", output)

    def test_attestation_contains_wrapper_starttime(self) -> None:
        self.assertIn(
            "printf '%s:entrypoint:%s:%s:%s\\n' \"$token\" \"$wrapper_pid\" \"$wrapper_starttime\" \"$wrapper_sha\"",
            self.wrapper,
        )
        self.assertIn(
            'content == f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\\n"',
            STRATEGY.read_text(),
        )

    def test_exact_value_free_custody_contract(self) -> None:
        self.assertEqual("source-only-check-only-not-run", self.policy["policy_status"])
        custody = self.policy["custody"]
        self.assertEqual("infisical-cloud", custody["value_owner"])
        self.assertEqual("prod", custody["environment_slug"])
        self.assertEqual("/cristexhub/prod/runtime", custody["secret_path"])
        self.assertEqual("DOCKER_CONFIG_JSON", custody["source_key"])
        self.assertFalse(custody["recursive"])
        self.assertEqual(
            {
                "name": "cristexhub-prod-ghcr-pull",
                "namespace": "cristexhub-prod",
                "type": "kubernetes.io/dockerconfigjson",
                "keys": [".dockerconfigjson"],
                "creation_policy": "Orphan",
                "metadata_labels": {
                    "app.kubernetes.io/managed-by": "infisical",
                    "app.kubernetes.io/part-of": "cristexhub",
                    "cristex.io/value-owner": "infisical-cloud",
                },
                "metadata_annotations": {
                    "required_keys": ["secrets.infisical.com/version"],
                    "values": "operator-generated-nonempty",
                },
            },
            custody["target"],
        )
        registry = custody["registry"]
        self.assertEqual("github-container-registry", registry["owner"])
        self.assertEqual("private-ghcr-only", registry["scope"])
        for key in ("token_values_in_source", "token_values_in_argv", "token_values_in_environment", "token_values_in_logs"):
            self.assertFalse(registry[key])
        self.assertEqual("NOT-RUN-BLOCKED", self.policy["preflight"]["predecessor_revoke_gate"])
        self.assertEqual("FUTURE-CONTROLLED-ONE-WORKLOAD-AT-A-TIME", self.policy["preflight"]["rollout_gate"])

    def test_metadata_only_secret_and_no_mutation(self) -> None:
        combined = "\n".join((self.wrapper, self.tasks, self.playbook[0].__repr__(), self.runbook))
        self.assertIn("PartialObjectMetadata", MODULE.read_text())
        self.assertIn("metadata_only=True", MODULE.read_text())
        self.assertIn("ordinary_secret_json: forbidden", self.policy["preflight"] and POLICY.read_text())
        for forbidden in (
            "ansible.builtin.k8s:",
            "kubernetes.core.k8s:",
            "ansible.builtin.command:",
            "ansible.builtin.shell:",
            "ansible.builtin.raw:",
            "ansible.builtin.script:",
            "kubectl",
            "infisical login",
            "gh auth",
            "curl",
            "wget",
        ):
            self.assertNotIn(forbidden, combined.lower())
        self.assertNotIn("state: present", self.tasks)
        self.assertNotIn("state: absent", self.tasks)
        self.assertIn("check-only", self.tasks)
        self.assertIn("no_mutation: true", self.tasks)
        self.assertIn("no_secret_data_read: true", self.tasks)
        self.assertIn("data", MODULE.read_text())
        self.assertIn("data reads", self.tasks)

    def test_exact_infisical_and_target_contract_is_in_source(self) -> None:
        targets = self.infisical_source["spec"]["targets"]
        self.assertEqual(
            ["cristexhub-prod-runtime", "cristexhub-prod-ghcr-pull"],
            [target["name"] for target in targets],
        )
        pull_target = targets[1]
        self.assertEqual({}, pull_target["metadata"]["annotations"])
        self.assertEqual(
            "{{ .DOCKER_CONFIG_JSON.Value }}",
            pull_target["template"]["data"][".dockerconfigjson"],
        )
        for required in (
            "InfisicalStaticSecret",
            "secrets.infisical.com/v1beta1",
            "cristexhub-prod-runtime",
            "cristexhub-prod-infisical-auth",
            "DOCKER_CONFIG_JSON",
            "kubernetes.io/dockerconfigjson",
            "creationPolicy == 'Orphan'",
            "template.data | length == 1",
            "e3sgLkRPQ0tFUl9DT05GSUdfSlNPTi5WYWx1ZSB9fQ==",
            "Query only imagePullSecret metadata through PartialObjectMetadata",
            "metadata_only | bool",
            "ownerReferences == []",
            "map(attribute='name') | list == ['cristexhub-prod-runtime', 'cristexhub-prod-ghcr-pull']",
            "deployment.kubernetes.io/revision",
            "^[1-9][0-9]*$",
        ):
            self.assertIn(required, self.tasks)
        expected_template = base64.b64encode(b"{{ .DOCKER_CONFIG_JSON.Value }}").decode()
        self.assertEqual("e3sgLkRPQ0tFUl9DT05GSUdfSlNPTi5WYWx1ZSB9fQ==", expected_template)

    def test_generated_target_annotation_and_identity_closure_are_strict(self) -> None:
        materialized = self.tasks.split(
            "- name: Require exact materialized imagePullSecret metadata without data reads",
            1,
        )[1]
        self.assertNotIn("internal_target_metadata.metadata.annotations == {}", materialized)
        self.assertIn(
            "keys() | list | sort ==\n        ['secrets.infisical.com/version']",
            materialized,
        )
        self.assertIn(
            "metadata.annotations['secrets.infisical.com/version'] |\n        default('', true) | length > 0",
            materialized,
        )
        self.assertIn(
            "metadata.uid is match('^[0-9a-f-]{16,}$')",
            self.tasks,
        )
        self.assertIn(
            "metadata.resourceVersion is match('^[0-9]+$')",
            self.tasks,
        )
        self.assertIn("Bind the exact source CR UID and resourceVersion closure", self.tasks)
        self.assertIn("source_cr_uid:", self.tasks)
        self.assertIn("source_cr_resource_version:", self.tasks)
        self.assertIn("'resource_version': item.resources[0].metadata.resourceVersion", self.tasks)
        self.assertIn("Require the bound Deployment UID and resourceVersion closure", self.tasks)
        self.assertIn("metadata.deletionTimestamp | default('', true) == ''", self.tasks)
        self.assertIn("metadata.uid ==\n        (cristexhub_prod_ghcr_pull_rotation_preflight_internal_deployment_inventory.resources", self.tasks)
        self.assertIn("metadata.resourceVersion ==\n        (cristexhub_prod_ghcr_pull_rotation_preflight_internal_deployment_inventory.resources", self.tasks)
        self.assertIn(
            "metadata.labels == {\n        'app.kubernetes.io/name': item.item,\n        'app.kubernetes.io/part-of': 'cristexhub'}",
            self.tasks,
        )

    def test_adversarial_target_and_identity_drift_is_rejected(self) -> None:
        materialized = self.tasks.split(
            "- name: Require exact materialized imagePullSecret metadata without data reads",
            1,
        )[1]
        self.assertNotIn("metadata.annotations == {}", materialized)
        self.assertIn("metadata.ownerReferences == []", materialized)
        self.assertIn("source_cr_binding.uid ==", self.tasks)
        self.assertIn("source_cr_binding.resource_version ==", self.tasks)
        self.assertIn("cristexhub_prod_ghcr_pull_rotation_preflight_internal_workload_bindings | length == 5", self.tasks)
        self.assertIn("map(attribute='revision') | select('match', '^[1-9][0-9]*$') | list | length == 5", self.tasks)
        self.assertIn("metadata.deletionTimestamp | default('', true) == ''", self.tasks)

    def test_exact_five_immutable_ready_consumers_and_gates(self) -> None:
        names = ["backend", "celery-worker", "frontend", "oauth2-proxy", "redis"]
        private = ["backend", "celery-worker", "frontend"]
        public = ["oauth2-proxy", "redis"]
        self.assertEqual(names, self.defaults["cristexhub_prod_ghcr_pull_rotation_preflight_deployments"])
        self.assertEqual(private, self.defaults["cristexhub_prod_ghcr_pull_rotation_preflight_private_deployments"])
        self.assertEqual(public, self.defaults["cristexhub_prod_ghcr_pull_rotation_preflight_public_deployments"])
        for required in (
            "Query the complete PROD workload inventory for the rollout gate",
            "Require exactly the five approved GHCR consumers",
            "Require immutable images, exact pull Secret, and current readiness",
            "Bind sanitized consumer rollout identities and image digests",
            "imagePullSecrets",
            "imagePullSecrets | default([])",
            "cristexhub_prod_ghcr_pull_rotation_preflight_private_deployments",
            "cristexhub_prod_ghcr_pull_rotation_preflight_public_deployments",
            "@sha256:[0-9a-f]{64}",
            "status.readyReplicas | int == 1",
            "FUTURE-CONTROLLED-ONE-WORKLOAD-AT-A-TIME",
            "NOT-RUN-BLOCKED",
            "cristexhub-prod-ghcr-pull",
        ):
            self.assertIn(required, self.tasks)
        self.assertEqual(names, self.policy["preflight"]["expected_consumers"])
        self.assertTrue(self.policy["preflight"]["image_pull_secret_must_not_change"])
        self.assertTrue(self.policy["preflight"]["images_must_be_digest_pinned"])
        self.assertEqual("github-container-registry", self.policy["custody"]["registry"]["owner"])

    def test_live_deployment_shape_fixture_distinguishes_private_and_public_pull_secrets(self) -> None:
        private = {"backend", "celery-worker", "frontend"}
        public = {"oauth2-proxy", "redis"}
        expected = private | public
        pull_secret = [{"name": "cristexhub-prod-ghcr-pull"}]
        fixtures = [
            {"metadata": {"name": name}, "spec": {"template": {"spec": {"imagePullSecrets": pull_secret}}}}
            for name in sorted(private)
        ] + [
            {"metadata": {"name": "oauth2-proxy"}, "spec": {"template": {"spec": {}}}},
            {"metadata": {"name": "redis"}, "spec": {"template": {"spec": {"imagePullSecrets": []}}}},
        ]

        def valid_shape(items: list[dict[str, object]]) -> bool:
            names = [item["metadata"]["name"] for item in items]
            if len(items) != len(expected) or len(names) != len(set(names)) or set(names) != expected:
                return False
            for item in items:
                name = item["metadata"]["name"]
                spec = item["spec"]["template"]["spec"]
                image_pull_secrets = spec.get("imagePullSecrets", [])
                required = pull_secret if name in private else []
                if image_pull_secrets != required:
                    return False
            return True

        self.assertTrue(valid_shape(fixtures))
        adversarial = (
            fixtures + [{"metadata": {"name": "extra"}, "spec": {"template": {"spec": {}}}}],
            fixtures[:1] + fixtures[2:],
            [
                *fixtures[:-2],
                {"metadata": {"name": "oauth2-proxy"}, "spec": {"template": {"spec": {"imagePullSecrets": pull_secret}}}},
                fixtures[-1],
            ],
            [
                *fixtures[:-1],
                {"metadata": {"name": "redis"}, "spec": {"template": {"spec": {"imagePullSecrets": pull_secret}}}},
            ],
        )
        for candidate in adversarial:
            with self.subTest(candidate=candidate):
                self.assertFalse(valid_shape(candidate))

    def test_strategy_hash_pin_and_canonical_binding_are_consistent(self) -> None:
        strategy_digest = hashlib.sha256(STRATEGY.read_bytes()).hexdigest()
        self.assertIn(f"strategy_sha256_expected='{strategy_digest}'", self.wrapper)
        match = re.search(
            r"^strategy_canonical_sha256_expected='([0-9a-f]{64})'$",
            self.wrapper,
            re.MULTILINE,
        )
        self.assertIsNotNone(match)
        canonical = re.sub(
            r'^_STRATEGY_CANONICAL_SHA256 = "[0-9a-f]{64}"$',
            '_STRATEGY_CANONICAL_SHA256 = "' + "0" * 64 + '"',
            STRATEGY.read_text(),
            flags=re.MULTILINE,
        )
        self.assertEqual(match.group(1), hashlib.sha256(canonical.encode()).hexdigest())
        self.assertIn('suffix in {"WRAPPER_SHA256", "STRATEGY_SHA256"}', STRATEGY.read_text())

    def test_wrapper_hash_binds_controller_inventory_config_and_toolchain(self) -> None:
        for required in (
            "ansible_config_sha256_expected=",
            "inventory_sha256_expected=",
            "controller_sha256_expected=",
            "requirements_sha256_expected=",
            "collection_manifest_sha256_expected=",
            "collection_files_sha256_expected=",
            "strategy_sha256_expected=",
            "strategy_canonical_sha256_expected=",
            "verify_external \"$config_source\"",
            "verify_external \"$inventory_source\"",
            "verify_external \"$toolchain_path\"",
            "verify_source ansible/plugins/strategy/cristexhub_prod_ghcr_pull_rotation_guarded_linear.py \"$strategy_source\" 644",
            "STRATEGY_SHA256",
            "ANSIBLE_CONFIG_SHA256",
            "INVENTORY_SHA256",
            "CONTROLLER_SHA256",
            "REQUIREMENTS_SHA256",
            "COLLECTION_MANIFEST_SHA256",
            "COLLECTION_FILES_SHA256",
        ):
            self.assertIn(required, self.wrapper)
        self.assertEqual(hashlib.sha256(CONFIG.read_bytes()).hexdigest(), "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9")
        self.assertEqual(hashlib.sha256(INVENTORY.read_bytes()).hexdigest(), "843dd43cdce256061d8e6b58b563acd00c3a1d7a1357e5f59ea30040af244752")
        self.assertEqual(hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest(), "f82d9e5ba1b64324710eb66c956d0447c46d3958722f635a4502bcb6c3efc75f")
        self.assertIn("dc32e90ca987d6199e9091f749ecb40fd3380b40aabb7c18961ec75582cfc6df", self.wrapper)
        self.assertIn("9d30dde4e4d6d04ec2e9b00a2d787114f13577fd2c456d25726865e3db39fa69", self.wrapper)

    def test_provenance_strategy_is_non_skippable(self) -> None:
        self.assertEqual("cristexhub_prod_ghcr_pull_rotation_guarded_linear", self.playbook[0]["strategy"])
        for required in (
            "_canonical_argv",
            "_selection_is_canonical",
            "_wrapper_binding_valid",
            "_source_contract",
            "_collection_toolchain_valid",
            "_collection_manifest_tree_valid",
            "TASK_SELECTION_GUARD",
            "start_at_task",
            "skip_tags",
        ):
            self.assertIn(required, STRATEGY.read_text())

    def test_wrapper_is_check_only_and_bound(self) -> None:
        for required in (
            "usage: ansible/bin/check-cristexhub-prod-ghcr-pull-rotation check",
            "--check --diff",
            "--limit crtxweb",
            "--connection local",
            "env -i",
            "PYTHONDONTWRITEBYTECODE=1 \\",
            "CRISTEXWEB_CRISTEXHUB_PROD_GHCR_PULL_ROTATION_PREFLIGHT_ENTRYPOINT=v1",
            "SOURCE_CLOSURE_SHA256",
            "WRAPPER_PID",
            "WRAPPER_STARTTIME",
            "refusing GHCR rotation wrapper source drift",
            "refusing a dirty source tree",
            "umask 077",
        ):
            self.assertIn(required, self.wrapper)
        for forbidden in ("--apply", "--tags", "--skip-tags", "--start-at-task", "tofu", "docker login", "gh auth", "kubectl"):
            self.assertNotIn(forbidden, self.wrapper.lower())
        self.assertIn("set -- \"$toolchain_path\"", self.wrapper)
        self.assertIn("--extra-vars '{\"cristexhub_prod_ghcr_pull_rotation_preflight_approved\":true}'", self.wrapper)
        result = subprocess.run([str(WRAPPER)], check=False, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(64, result.returncode)
        self.assertNotIn("ansible-playbook", result.stdout + result.stderr)

    def test_playbook_is_single_host_local_role(self) -> None:
        self.assertEqual(1, len(self.playbook))
        play = self.playbook[0]
        self.assertEqual("crtxweb", play["hosts"])
        self.assertFalse(play["gather_facts"])
        self.assertFalse(play["become"])
        self.assertEqual("local", play["connection"])
        self.assertEqual(
            "cristexhub_prod_ghcr_pull_rotation_preflight",
            play["roles"][0]["role"],
        )

    def test_runbook_freezes_non_atomic_replacement_and_revoke_order(self) -> None:
        normalized = " ".join(self.runbook.split())
        for required in (
            "SOURCE-ONLY / CHECK-ONLY / NOT RUN / BLOCKED",
            "Infisical Cloud",
            "/cristexhub/prod/runtime",
            "DOCKER_CONFIG_JSON",
            "PartialObjectMetadata",
            "never requests, parses, returns, logs, or compares `data`",
            "five PROD Deployments",
            "backend",
            "celery-worker",
            "frontend",
            "oauth2-proxy",
            "redis",
            "FUTURE-CONTROLLED-ONE-WORKLOAD-AT-A-TIME",
            "GitHub Container Registry owns token issuance and predecessor revocation",
            "NOT-RUN-BLOCKED",
            "fresh authentication failure",
            "does not create a successor token",
            "does not call GitHub",
            "does not call Infisical",
            "does not restart a Deployment",
            "does not revoke a registry token",
        ):
            self.assertIn(required, normalized)
        self.assertNotRegex(self.runbook, r"-----BEGIN [^-]+ PRIVATE KEY-----")
        self.assertNotRegex(self.runbook, r"(?:https?|ssh)://[^\s`]+:[^\s@`]+@")

    def test_module_is_syntax_valid(self) -> None:
        result = subprocess.run(
            ["/usr/bin/python3", "-m", "py_compile", str(MODULE)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        cache = MODULE.parent / "__pycache__"
        if cache.exists():
            for path in cache.glob("cristexhub_prod_ghcr_pull_secret_metadata*.pyc"):
                path.unlink()
            try:
                cache.rmdir()
            except OSError:
                pass

    def test_shell_syntax_valid(self) -> None:
        result = subprocess.run(["/bin/sh", "-n", str(WRAPPER)], check=False, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
