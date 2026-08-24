from __future__ import annotations

import hashlib
import json
import re
import stat
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/reactive-resume-dev-route"
ROLE = ROOT / "ansible/roles/reactive_resume_dev_route_bootstrap"
PLUGIN = ROOT / "ansible/plugins/action/reactive_resume_dev_route_guarded_k8s.py"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_reactive_resume_dev_route.yml"
WRAPPER = ROOT / "ansible/bin/bootstrap-reactive-resume-dev-route"
RUNBOOK = ROOT / "runbooks/reactive-resume-dev-private-route.md"


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ReactiveResumeDevPrivateRouteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = sorted(COMPONENT.rglob("*.yaml"))
        cls.objects = [yaml.safe_load(path.read_text()) for path in cls.paths]
        cls.role_tasks = (ROLE / "tasks/main.yml").read_text()
        cls.role_defaults = (ROLE / "defaults/main.yml").read_text()
        cls.plugin = PLUGIN.read_text()
        cls.playbook = PLAYBOOK.read_text()
        cls.wrapper = WRAPPER.read_text()
        cls.runbook = RUNBOOK.read_text()

    def test_exact_two_object_value_free_component(self) -> None:
        self.assertEqual(2, len(self.objects))
        self.assertEqual({"Ingress", "NetworkPolicy"}, {obj["kind"] for obj in self.objects})
        self.assertNotIn("Secret", {obj["kind"] for obj in self.objects})
        combined = "\n".join(path.read_text() for path in self.paths)
        self.assertNotRegex(combined, r"(?im)(tls\.key|tls\.crt)\s*:")
        self.assertNotRegex(combined, r"(?m)^data:\s*$")
        for path in self.paths:
            self.assertEqual(0o644, stat.S_IMODE(path.stat().st_mode), path)
            self.assertFalse(path.is_symlink(), path)

    def test_ingress_hostname_tls_and_service_contract(self) -> None:
        ingress = next(obj for obj in self.objects if obj["kind"] == "Ingress")
        self.assertEqual("reactive-resume-dev-private", ingress["metadata"]["name"])
        self.assertEqual("cristexhub-dev", ingress["metadata"]["namespace"])
        self.assertEqual("traefik", ingress["spec"]["ingressClassName"])
        self.assertEqual(
            {"resume-dev.cristex-soft.com"},
            set(ingress["spec"]["tls"][0]["hosts"]),
        )
        self.assertEqual("reactive-resume-dev-tls", ingress["spec"]["tls"][0]["secretName"])
        rule = ingress["spec"]["rules"][0]
        self.assertEqual("resume-dev.cristex-soft.com", rule["host"])
        path = rule["http"]["paths"][0]
        self.assertEqual("/", path["path"])
        self.assertEqual("Prefix", path["pathType"])
        self.assertEqual("reactive-resume-dev", path["backend"]["service"]["name"])
        self.assertEqual(3000, path["backend"]["service"]["port"]["number"])
        self.assertEqual("websecure", ingress["metadata"]["annotations"]["traefik.ingress.kubernetes.io/router.entrypoints"])
        self.assertEqual("true", ingress["metadata"]["annotations"]["traefik.ingress.kubernetes.io/router.tls"])

    def test_exact_traefik_only_network_policy(self) -> None:
        policy = next(obj for obj in self.objects if obj["kind"] == "NetworkPolicy")
        self.assertEqual("reactive-resume-dev-route-allow-traefik", policy["metadata"]["name"])
        self.assertEqual("cristexhub-dev", policy["metadata"]["namespace"])
        self.assertEqual(["Ingress"], policy["spec"]["policyTypes"])
        self.assertEqual(
            {"app.kubernetes.io/name": "reactive-resume-dev", "app.kubernetes.io/part-of": "cristexhub"},
            policy["spec"]["podSelector"]["matchLabels"],
        )
        ingress = policy["spec"]["ingress"]
        self.assertEqual(1, len(ingress))
        self.assertEqual(1, len(ingress[0]["from"]))
        peer = ingress[0]["from"][0]
        self.assertEqual(
            {"kubernetes.io/metadata.name": "kube-system"},
            peer["namespaceSelector"]["matchLabels"],
        )
        self.assertEqual({"app.kubernetes.io/name": "traefik"}, peer["podSelector"]["matchLabels"])
        self.assertEqual([{"protocol": "TCP", "port": 3000}], ingress[0]["ports"])

    def test_manifest_ledger_and_role_hashes(self) -> None:
        ledger = {
            relative: digest
            for digest, relative in (
                line.split("  ", 1)
                for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines()
                if line.strip()
            )
        }
        self.assertEqual({str(path.relative_to(COMPONENT)) for path in self.paths}, set(ledger))
        for path in self.paths:
            self.assertEqual(ledger[str(path.relative_to(COMPONENT))], hashlib.sha256(path.read_bytes()).hexdigest())
            obj = yaml.safe_load(path.read_text())
            self.assertIn(f"{str(path.relative_to(COMPONENT))}: {ledger[str(path.relative_to(COMPONENT))]}", self.role_defaults)
            identity = (
                obj["apiVersion"],
                obj["kind"],
                obj["metadata"]["namespace"],
                obj["metadata"]["name"],
            )
            self.assertIn(repr(identity), self.plugin)
            self.assertIn(canonical_hash(obj), self.plugin)

    def test_precreated_tls_secret_is_metadata_only_and_source_refuses_secrets(self) -> None:
        self.assertIn("reactive-resume-dev-tls", self.role_tasks)
        self.assertIn("kubernetes.io/tls", self.role_tasks)
        self.assertIn("['tls.crt', 'tls.key']", self.role_tasks)
        self.assertIn("reactive_resume_dev_route_bootstrap_internal_tls_secret", self.role_tasks)
        self.assertIn("definition.get('kind') in {'Secret'", self.plugin)
        self.assertIn("selectattr('kind', 'equalto', 'Secret') | list | length == 0", self.role_tasks)

    def test_guarded_role_playbook_and_wrapper_are_non_passthrough(self) -> None:
        for value in (
            "reactive_resume_dev_route_bootstrap_approved",
            "reactive_resume_dev_route_bootstrap_state == 'present'",
            "ansible_diff_mode",
            "reactive_resume_dev_route_bootstrap_manifest_paths | length == 2",
            "reactive_resume_dev_route_bootstrap_object_count == 2",
            "reactive_resume_dev_route_bootstrap_namespace == 'cristexhub-dev'",
            "Require exact private Reactive Resume DEV Service",
            "spec.type == 'ClusterIP'",
            "spec.ports[0].port == 3000",
            "spec.ports[0].targetPort == 'http'",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_ROUTE_BOOTSTRAP_ENTRYPOINT",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_ROUTE_BOOTSTRAP_TOKEN",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_ROUTE_BOOTSTRAP_ATTESTATION_FILE",
            "no_delete_path: true",
        ):
            self.assertIn(value, self.role_tasks, value)
        self.assertIn("role: reactive_resume_dev_route_bootstrap", self.playbook)
        self.assertIn("hosts: k3s_servers", self.playbook)
        self.assertIn("become: false", self.playbook)
        for value in (
            "check|apply",
            "refusing passthrough arguments or task selection", 
            "--diff",
            "--limit crtxweb",
            "--check",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_ROUTE_BOOTSTRAP_ENTRYPOINT=v1",
            "/usr/bin/env -i",
            "reactive_resume_dev_route_bootstrap_approved",
        ):
            self.assertIn(value, self.wrapper, value)
        self.assertNotIn('exec "$@"', self.wrapper)

    def test_action_plugin_has_exact_scope_and_no_delete_or_secret_path(self) -> None:
        for value in (
            "reactive_resume_dev_route_bootstrap_internal_preflight_binding",
            "object_count', -1)) == 2",
            "prestate_count', -1)) == 2",
            "namespace_contract') is True",
            "no_delete_path') is True",
            "state') != 'present'",
            "PersistentVolumeClaim",
            "Service",
            "Deployment",
            "IngressRoute",
            "Secret",
        ):
            self.assertIn(value, self.plugin, value)
        self.assertNotIn("state: absent", self.role_tasks)
        self.assertNotIn("kubernetes.core.k8s_delete", self.role_tasks)

    def test_runbook_is_source_only_and_private(self) -> None:
        normalized = " ".join(self.runbook.split())
        for value in (
            "source-only guarded closure",
            "resume-dev.cristex-soft.com",
            "cristexhub-dev",
            "reactive-resume-dev-tls",
            "No Keycloak, Infisical, Secret, PROD",
            "No provider, DNS, Infisical, Keycloak, Kubernetes",
            "negative non-Tailscale reachability",
        ):
            self.assertIn(value, normalized, value)
        self.assertIn("no DNS/provider path", self.runbook)


if __name__ == "__main__":
    unittest.main()
