from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/oidc-connect-proxy"
ROLE = ROOT / "ansible/roles/oidc_connect_proxy_bootstrap"
PLUGIN = ROOT / "ansible/plugins/action/oidc_connect_proxy_guarded_k8s.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-oidc-connect-proxy"
RUNBOOK = ROOT / "runbooks/oidc-connect-proxy.md"


class OidcConnectProxyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = sorted(COMPONENT.rglob("*.yaml"))
        cls.objects = [yaml.safe_load(path.read_text()) for path in cls.paths]
        cls.by_name = {obj["metadata"]["name"]: obj for obj in cls.objects}

    def test_exact_value_free_closure_and_hash_ledger(self):
        self.assertEqual(11, len(self.objects))
        self.assertEqual(
            {"ConfigMap": 1, "NetworkPolicy": 7, "ServiceAccount": 1, "Deployment": 1, "Service": 1},
            {kind: sum(obj["kind"] == kind for obj in self.objects) for kind in {obj["kind"] for obj in self.objects}},
        )
        self.assertFalse(any(obj["kind"] in {"Secret", "Ingress", "PersistentVolumeClaim"} for obj in self.objects))
        ledger = {}
        for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines():
            digest, relative = line.split("  ", 1)
            ledger[relative] = digest
        self.assertEqual({str(path.relative_to(COMPONENT)) for path in self.paths}, set(ledger))
        for path in self.paths:
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), ledger[str(path.relative_to(COMPONENT))])

    def test_squid_is_exact_connect_host_and_port_allowlist(self):
        config = self.by_name["oidc-connect-proxy-config"]["data"]["squid.conf"]
        self.assertIn("http_port 3128", config)
        self.assertIn("acl connect_method method CONNECT", config)
        self.assertIn(
            "acl allowed_https_host dstdomain auth.cristex-soft.com api.deepseek.com fonts.gstatic.com",
            config,
        )
        self.assertIn("acl tls_port port 443", config)
        self.assertIn("http_access deny !connect_method", config)
        self.assertIn("http_access deny !tls_port", config)
        self.assertIn("http_access deny !allowed_https_host", config)
        self.assertIn("http_access deny all", config)
        self.assertIn("access_log none", config)
        domain_lines = [line.strip() for line in config.splitlines() if " dstdomain " in line]
        self.assertEqual(
            ["acl allowed_https_host dstdomain auth.cristex-soft.com api.deepseek.com fonts.gstatic.com"],
            domain_lines,
        )

    def test_network_policies_are_least_privilege(self):
        policies = {obj["metadata"]["name"]: obj for obj in self.objects if obj["kind"] == "NetworkPolicy"}
        self.assertEqual(
            {
                "oidc-connect-proxy-default-deny",
                "oidc-connect-proxy-allow-clients",
                "oidc-connect-proxy-allow-dns",
                "oidc-connect-proxy-allow-reactive-resume-dev",
                "oidc-connect-proxy-allow-auth-egress",
                "cristexhub-backend-allow-oidc-proxy",
                "oauth2-proxy-allow-oidc-proxy",
            },
            set(policies),
        )
        deny = policies["oidc-connect-proxy-default-deny"]["spec"]
        self.assertEqual(["Ingress", "Egress"], deny["policyTypes"])
        self.assertNotIn("egress", deny)
        clients = policies["oidc-connect-proxy-allow-clients"]["spec"]["ingress"]
        self.assertEqual(6, len(clients[0]["from"]))
        self.assertEqual(
            {"cristexhub-dev", "cristexhub-prod"},
            {
                peer["namespaceSelector"]["matchLabels"]["kubernetes.io/metadata.name"]
                for peer in clients[0]["from"]
            },
        )
        self.assertEqual(
            {"backend", "celery-worker", "oauth2-proxy"},
            {
                peer["podSelector"]["matchLabels"]["app.kubernetes.io/name"]
                for peer in clients[0]["from"]
            },
        )
        self.assertEqual({3128}, {port["port"] for port in clients[0]["ports"]})
        external = policies["oidc-connect-proxy-allow-auth-egress"]["spec"]["egress"][0]
        self.assertEqual({443}, {port["port"] for port in external["ports"]})
        self.assertGreaterEqual(len(external["to"][0]["ipBlock"]["except"]), 10)
        for name in ("cristexhub-backend-allow-oidc-proxy", "oauth2-proxy-allow-oidc-proxy"):
            policy = policies[name]
            self.assertEqual("cristexhub-dev", policy["metadata"]["namespace"])
            self.assertEqual(["Egress"], policy["spec"]["policyTypes"])
            ports = {port["port"] for rule in policy["spec"]["egress"] for port in rule["ports"]}
            self.assertEqual({53, 3128}, ports)

    def test_workload_hardening_and_private_service(self):
        deployment = next(obj for obj in self.objects if obj["kind"] == "Deployment" and obj["metadata"]["name"] == "oidc-connect-proxy")
        pod = deployment["spec"]["template"]
        self.assertFalse(pod["spec"]["automountServiceAccountToken"])
        self.assertTrue(pod["spec"]["securityContext"]["runAsNonRoot"])
        container = pod["spec"]["containers"][0]
        self.assertRegex(container["image"], r"ubuntu/squid@sha256:[0-9a-f]{64}$")
        config_hash = hashlib.sha256(
            (COMPONENT / "config/configmap-oidc-connect-proxy.yaml").read_bytes()
        ).hexdigest()
        self.assertEqual(
            config_hash,
            pod["metadata"]["annotations"]["cristex.io/proxy-config-sha256"],
        )
        self.assertEqual(13, pod["spec"]["securityContext"]["runAsUser"])
        self.assertFalse(container["securityContext"]["allowPrivilegeEscalation"])
        self.assertTrue(container["securityContext"]["readOnlyRootFilesystem"])
        self.assertEqual(["ALL"], container["securityContext"]["capabilities"]["drop"])
        service = next(obj for obj in self.objects if obj["kind"] == "Service" and obj["metadata"]["name"] == "oidc-connect-proxy")
        self.assertEqual("ClusterIP", service["spec"]["type"])
        self.assertEqual(3128, service["spec"]["ports"][0]["port"])
        self.assertFalse(any(key in service["spec"] for key in ("externalIPs", "externalName", "loadBalancerIP")))

    def test_guarded_entrypoint_and_source_only_documentation(self):
        defaults = (ROLE / "defaults/main.yml").read_text()
        tasks = (ROLE / "tasks/main.yml").read_text()
        plugin = PLUGIN.read_text()
        wrapper = WRAPPER.read_text()
        runbook = RUNBOOK.read_text()
        for text in (defaults, tasks, plugin, wrapper):
            self.assertNotIn("state: absent", text)
            self.assertNotIn("kubectl delete", text)
        self.assertIn("oidc_connect_proxy_guarded_k8s", tasks)
        self.assertIn("TASK_SELECTION_GUARD", plugin)
        self.assertIn("MUTATION_ARGUMENT_GUARD", plugin)
        self.assertIn("--diff", wrapper)
        self.assertIn("--check", wrapper)
        self.assertIn("APP-LEVEL SMOKE ONLY", runbook)
        self.assertIn("auth.cristex-soft.com:443` and `api.deepseek.com:443", runbook)
        self.assertIn("Full private validation must still prove", runbook)
        self.assertNotIn("Authorization: Bearer", runbook)


if __name__ == "__main__":
    unittest.main()
