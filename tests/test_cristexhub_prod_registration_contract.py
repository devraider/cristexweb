from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

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
        self.assertNotIn("cristexhub-dev", text)
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
                "namespaces": "cristexhub-prod",
                "clusterResources": "false",
                "config": "{}",
            },
            cluster["stringData"],
        )

    def test_application_is_exact_revision_and_automated_without_prune(self) -> None:
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
                "name": "cristexhub-prod-local",
                "server": "",
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

    def test_project_is_namespaced_least_privilege_for_exact_cluster_alias(self) -> None:
        project = next(manifest for manifest in objects() if manifest["kind"] == "AppProject")
        spec = project["spec"]
        self.assertEqual([], spec["clusterResourceWhitelist"])
        self.assertEqual(
            [{"name": "cristexhub-prod-local", "namespace": "cristexhub-prod"}],
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
        for forbidden in ("--tags", "--skip-tags", "--start-at-task", "kubectl", "state: absent"):
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
            tmpdir.mkdir()
            script.write_text(
                wrapper.replace(
                    "expected_repository_root=/home/paul/projects/cristexweb",
                    f"expected_repository_root={root}",
                )
            )
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

    def test_action_guard_is_exact_present_only(self) -> None:
        plugin = PLUGIN.read_text()
        for needle in (
            "EXPECTED_REPOSITORY_ROOT",
            "TASK_SUFFIX",
            "task selection controls are forbidden",
            'args.get("state") != "present"',
            "complete preflight binding",
            "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ENTRYPOINT",
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
                    "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ENTRYPOINT": "v1",
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
            "LIVE STATUS UNKNOWN / RECONCILIATION APPLY PENDING",
            "cristexhub-prod-local",
            "HISTORICAL REGISTRATION APPLIED",
            "Synced/Healthy",
            "separately approved registration apply",
            "does not create the Namespace",
            "prune=false",
            "Cloudflare",
            "protected\nDNS-capable Cloudflare credential plus exact two-change plan/apply",
        ):
            self.assertIn(needle, runbook)


if __name__ == "__main__":
    unittest.main()
