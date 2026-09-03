from __future__ import annotations

import base64
import hashlib
import re
import stat
import subprocess
import unittest
from pathlib import Path

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
RUNBOOK = ROOT / "runbooks/cristexhub-prod-ghcr-pull-rotation.md"


class CristexHubProdGhcrPullRotationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wrapper = WRAPPER.read_text()
        cls.tasks = TASKS.read_text()
        cls.defaults = yaml.safe_load(DEFAULTS.read_text())
        cls.playbook = yaml.safe_load(PLAYBOOK.read_text())
        cls.policy = yaml.safe_load(POLICY.read_text())
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
        }
        self.assertEqual(set(expected), {line.split(maxsplit=1)[1] for line in self.manifest_lines})
        self.assertEqual(5, len(self.manifest_lines))
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
        self.assertNotIn("metadata.deletionTimestamp | default('') == ''", self.tasks)

    def test_exact_five_immutable_ready_consumers_and_gates(self) -> None:
        names = ["backend", "celery-worker", "frontend", "oauth2-proxy", "redis"]
        self.assertEqual(names, self.defaults["cristexhub_prod_ghcr_pull_rotation_preflight_deployments"])
        for required in (
            "Query the complete PROD workload inventory for the rollout gate",
            "Require exactly the five approved GHCR consumers",
            "Require immutable images, exact pull Secret, and current readiness",
            "Bind sanitized consumer rollout identities and image digests",
            "imagePullSecrets",
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

    def test_wrapper_is_check_only_and_bound(self) -> None:
        for required in (
            "usage: ansible/bin/check-cristexhub-prod-ghcr-pull-rotation check",
            "--check --diff",
            "--limit crtxweb",
            "--connection local",
            "env -i",
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
