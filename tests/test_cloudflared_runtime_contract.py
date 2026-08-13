from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/cloudflared"


class CloudflaredRuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = sorted(COMPONENT.rglob("*.yaml"))
        cls.objects = [yaml.safe_load(path.read_text()) for path in cls.paths]

    def test_exact_private_source_closure(self):
        self.assertEqual(5, len(self.objects))
        self.assertEqual({"NetworkPolicy": 3, "ServiceAccount": 1, "Deployment": 1}, {
            kind: sum(obj["kind"] == kind for obj in self.objects) for kind in {obj["kind"] for obj in self.objects}
        })
        self.assertFalse(any(obj["kind"] in {"Secret", "Service", "Ingress"} for obj in self.objects))
        self.assertTrue(all(obj["metadata"]["namespace"] == "platform-edge" for obj in self.objects))

    def test_hardened_digest_pinned_deployment(self):
        deployment = next(obj for obj in self.objects if obj["kind"] == "Deployment")
        pod = deployment["spec"]["template"]
        container = pod["spec"]["containers"][0]
        self.assertRegex(container["image"], r"cloudflare/cloudflared@sha256:[0-9a-f]{64}$")
        self.assertEqual(65532, pod["spec"]["securityContext"]["runAsUser"])
        self.assertEqual(65532, pod["spec"]["securityContext"]["runAsGroup"])
        self.assertEqual(65532, pod["spec"]["securityContext"]["fsGroup"])
        self.assertEqual("OnRootMismatch", pod["spec"]["securityContext"]["fsGroupChangePolicy"])
        self.assertIn(pod["spec"]["volumes"][0]["secret"]["defaultMode"], (0o440, "0440"))
        self.assertTrue(container["securityContext"]["readOnlyRootFilesystem"])
        self.assertFalse(container["securityContext"]["allowPrivilegeEscalation"])
        self.assertEqual(["ALL"], container["securityContext"]["capabilities"]["drop"])
        self.assertEqual("/etc/cloudflared/token/token", container["args"][-1])
        self.assertIn("--token-file", container["args"])
        self.assertEqual("/ready", container["startupProbe"]["httpGet"]["path"])
        self.assertEqual("/healthcheck", container["livenessProbe"]["httpGet"]["path"])
        self.assertEqual(20241, container["ports"][0]["containerPort"])

    def test_network_policy_is_default_deny_and_exact_egress(self):
        policies = {obj["metadata"]["name"]: obj for obj in self.objects if obj["kind"] == "NetworkPolicy"}
        self.assertEqual({"cloudflared-default-deny", "cloudflared-allow-egress", "cloudflared-allow-traefik-origin"}, set(policies))
        self.assertEqual(["Ingress", "Egress"], policies["cloudflared-default-deny"]["spec"]["policyTypes"])
        ports = {port["port"] for rule in policies["cloudflared-allow-egress"]["spec"]["egress"] for port in rule["ports"]}
        self.assertIn(7844, ports)
        self.assertEqual({80, 8000}, {port["port"] for port in policies["cloudflared-allow-traefik-origin"]["spec"]["egress"][0]["ports"]})

    def test_infisical_source_owns_token_secret_without_value(self):
        source = ROOT / "ansible/files/components/infisical-cloudflared-secrets/source/cloudflared-infisical-secrets.yaml"
        text = source.read_text()
        self.assertIn("secretPath: /platform-edge/cloudflared", text)
        self.assertIn("CLOUDFLARE_TUNNEL_TOKEN", text)
        self.assertIn("name: cloudflared-token", text)
        self.assertIn("cristex.io/value-owner: infisical-cloud", text)
        self.assertNotRegex(text, r"(?m)^\s+token:\s+[^'{\n]")


if __name__ == "__main__":
    unittest.main()
