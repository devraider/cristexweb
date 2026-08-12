from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "ansible/files/components/infisical-cloudflared-secrets"


class InfisicalCloudflaredSecretsContractTests(unittest.TestCase):
    def test_manifest_ledger_matches_yaml_leaves(self) -> None:
        entries = {}
        for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines():
            digest, relative = line.split("  ", 1)
            entries[relative] = digest
        leaves = sorted(p.relative_to(COMPONENT).as_posix() for p in COMPONENT.rglob("*.yaml"))
        self.assertEqual(leaves, sorted(entries))
        for relative, digest in entries.items():
            self.assertEqual(digest, hashlib.sha256((COMPONENT / relative).read_bytes()).hexdigest())

    def test_exact_prod_source_and_single_token_target(self) -> None:
        path = COMPONENT / "source/cloudflared-infisical-secrets.yaml"
        source = yaml.safe_load(path.read_text())
        self.assertEqual(source["metadata"]["namespace"], "platform-edge")
        self.assertEqual(source["spec"]["sources"], [{
            "projectId": "619656da-14f3-4872-857b-be103cdc5326",
            "environmentSlug": "prod",
            "secretPath": "/platform-edge/cloudflared",
            "recursive": False,
            "tagSlugs": [],
        }])
        target = source["spec"]["targets"]
        self.assertEqual(len(target), 1)
        self.assertEqual(target[0]["name"], "cloudflared-token")
        self.assertEqual(target[0]["namespace"], "platform-edge")
        self.assertEqual(target[0]["secretType"], "Opaque")
        self.assertEqual(target[0]["creationPolicy"], "Orphan")
        self.assertEqual(target[0]["metadata"], {"annotations": {}, "labels": {"app.kubernetes.io/managed-by": "infisical", "app.kubernetes.io/part-of": "cloudflared", "cristex.io/value-owner": "infisical-cloud"}})
        self.assertEqual(target[0]["template"]["engineVersion"], "v1")
        self.assertEqual(set(target[0]["template"]["data"]), {"token"})
        self.assertEqual(target[0]["template"]["data"]["token"], "{{ .CLOUDFLARE_TUNNEL_TOKEN.Value }}")
        self.assertNotRegex(path.read_text(), r"CLOUDFLARE_TUNNEL_TOKEN\s*:\s*[^'{\s]")

    def test_boundaries_and_rbac_are_fail_closed(self) -> None:
        policies = [yaml.safe_load(p.read_text()) for p in (COMPONENT / "admission").glob("*.yaml") if "binding" not in p.name]
        bindings = [yaml.safe_load(p.read_text()) for p in (COMPONENT / "admission").glob("*-binding.yaml")]
        self.assertEqual(4, len(policies))
        self.assertEqual(4, len(bindings))
        self.assertTrue(all(p["spec"]["failurePolicy"] == "Fail" for p in policies))
        self.assertTrue(all(b["spec"]["validationActions"] == ["Deny"] for b in bindings))
        role = yaml.safe_load((COMPONENT / "rbac/cloudflared-secret-writer-role.yaml").read_text())
        self.assertEqual(role["metadata"]["namespace"], "platform-edge")
        self.assertEqual(role["rules"][1]["resourceNames"], ["cloudflared-token"])
        verbs = {verb for rule in role["rules"] for verb in rule["verbs"]}
        self.assertNotIn("delete", verbs)
        self.assertNotIn("patch", verbs)

    def test_wrapper_is_non_passthrough_and_apply_requires_explicit_mode(self) -> None:
        wrapper = (ROOT / "ansible/bin/bootstrap-infisical-cloudflared-secrets").read_text()
        self.assertIn("check|apply", wrapper)
        self.assertIn("--diff", wrapper)
        self.assertIn("CRISTEXWEB_INFISICAL_CLOUDFLARED_SECRETS_BOOTSTRAP_TOKEN", wrapper)
        self.assertNotIn("CLOUDFLARE_TUNNEL_TOKEN=", wrapper)
        self.assertNotIn("CLOUDFLARE_TUNNEL_TOKEN=", wrapper)


if __name__ == "__main__":
    unittest.main()
