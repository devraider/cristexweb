from __future__ import annotations

import ast
import hashlib
import json
import stat
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = ROOT / "ansible/roles/reactive_resume_dev_argocd_alignment/defaults/main.yml"
TASKS = ROOT / "ansible/roles/reactive_resume_dev_argocd_alignment/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/reactive_resume_dev_argocd_alignment_guarded_k8s.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-reactive-resume-dev-argocd-alignment"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_reactive_resume_dev_argocd_alignment.yml"
RUNBOOK = ROOT / "runbooks/reactive-resume-dev-argocd-alignment.md"
DEV = ROOT / "ansible/files/components/reactive-resume-dev-argocd"
DESTINATION = [
    ROOT / "ansible/files/components/postgresql/network/postgresql-ingress.yaml",
    ROOT / "ansible/files/components/keycloak/network/keycloak-allow-reactive-resume-dev.yaml",
    ROOT / "ansible/files/components/oidc-connect-proxy/network/oidc-connect-proxy-allow-reactive-resume-dev.yaml",
    ROOT / "ansible/files/components/reactive-resume-dev-networkpolicy/network/reactive-resume-object-storage-allow-dev.yaml",
]


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


class ReactiveResumeDevArgoAlignmentContractTests(unittest.TestCase):
    def test_exact_eleven_object_closure(self) -> None:
        objects = [load(p) for p in sorted(DEV.glob("*.yaml"))] + [load(p) for p in DESTINATION]
        self.assertEqual(11, len(objects))
        self.assertEqual(7, sum(o["metadata"]["namespace"] == "cristexhub-dev" for o in objects))
        self.assertEqual(4, sum(o["metadata"]["namespace"] == "shared-services" for o in objects))
        self.assertEqual(7, sum(o["kind"] == "NetworkPolicy" for o in objects))
        self.assertFalse(any(o["kind"] in {"Job", "Secret"} for o in objects))
        self.assertTrue(all(o["metadata"]["labels"]["app.kubernetes.io/managed-by"] == "ansible" for o in objects))
        self.assertTrue(all(o["metadata"]["labels"].get("cristex.io/bootstrap-writer", o["metadata"]["labels"].get("app.kubernetes.io/bootstrap-writer")) == "ansible" for o in objects))

    def test_defaults_bind_exact_paths_and_raw_hashes(self) -> None:
        defaults = load(DEFAULTS)
        self.assertEqual(11, defaults["reactive_resume_dev_argocd_alignment_object_count"])
        self.assertEqual(7, defaults["reactive_resume_dev_argocd_alignment_source_object_count"])
        self.assertEqual(4, defaults["reactive_resume_dev_argocd_alignment_destination_policy_count"])
        self.assertEqual(11, len(defaults["reactive_resume_dev_argocd_alignment_manifest_paths"]))
        hashes = defaults["reactive_resume_dev_argocd_alignment_expected_hashes"]
        self.assertEqual(11, len(hashes))
        expected = [*sorted(DEV.glob("*.yaml")), *DESTINATION]
        for path, entry in zip(expected, hashes):
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"])
            canonical = hashlib.sha256(
                json.dumps(load(path), sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            self.assertIn(canonical, PLUGIN.read_text())

    def test_action_guard_is_exact_and_non_destructive(self) -> None:
        text = PLUGIN.read_text()
        self.assertIn("EXPECTED_IDENTITY_SET_SHA256", text)
        self.assertIn("EXPECTED_HASHES", text)
        self.assertIn("state\", \"definition\", \"kubeconfig\", \"wait\", \"wait_timeout\"", text)
        self.assertIn("no_delete_path", text)
        self.assertIn("no_job", text)
        self.assertIn("no_secret", text)
        self.assertIn("task selection controls are forbidden", text)
        self.assertNotIn("delete", text.lower().replace("no_delete_path", ""))
        self.assertNotIn("prune", text.lower())

    def test_role_and_wrapper_are_guarded(self) -> None:
        tasks = TASKS.read_text()
        wrapper = WRAPPER.read_text()
        self.assertIn("exactly seven DEV objects and four destination NetworkPolicies", tasks)
        self.assertIn("Reconcile only the exact eleven alignment objects", tasks)
        self.assertIn("kind', 'equalto', 'Job') | list | length == 0", tasks)
        self.assertIn("kind', 'equalto', 'Secret') | list | length == 0", tasks)
        self.assertIn("ownerReferences", tasks)
        self.assertIn("finalizers", tasks)
        self.assertIn("argocd.argoproj.io/tracking-id", tasks)
        self.assertIn("--diff", wrapper)
        self.assertIn("env -i", wrapper)
        self.assertIn("/home/paul/projects/cristexweb", wrapper)
        self.assertIn("CRISTEXWEB_REACTIVE_RESUME_DEV_ARGOCD_ALIGNMENT_ENTRYPOINT=v1", wrapper)
        self.assertEqual(0o755, stat.S_IMODE(WRAPPER.stat().st_mode))
        self.assertEqual("reactive_resume_dev_argocd_alignment", PLAYBOOK.read_text().split("role: ", 1)[1].splitlines()[0])

    def test_runbook_states_scope_and_not_run_boundary(self) -> None:
        text = RUNBOOK.read_text()
        for value in ("SOURCE-ONLY", "NOT RUN LIVE", "seven", "four", "migration Job", "no delete", "no prune", "check", "apply"):
            self.assertIn(value, text)
        self.assertNotIn("cristexhub-prod", text)


if __name__ == "__main__":
    unittest.main()
