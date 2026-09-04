from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOFU = ROOT / "opentofu"
BIN = TOFU / "bin"
PLAN = BIN / "plan-foundation-prod-route"
VALIDATE = BIN / "validate-foundation-prod-plan"
RECONCILE = BIN / "reconcile-foundation-state"
SCOPE = BIN / "validate-foundation-state-scope"
MANIFEST = BIN / "SOURCE.sha256"
RUNBOOK = ROOT / "runbooks/opentofu-foundation-state-reconciliation.md"
FIXTURE = ROOT / "tests/fixtures/opentofu-1.12.5-cloudflare-5.23.0-prod-route.json"
PROVENANCE = ROOT / "tests/fixtures/opentofu-1.12.5-cloudflare-5.23.0-prod-route.provenance.md"
IDENTITY_RECEIPT = ROOT / "tests/fixtures/opentofu-1.12.5-cloudflare-5.23.0-prod-route.identity-receipt.json"

EXISTING = {
    "cloudflare_dns_record.argocd_tailscale",
    "cloudflare_dns_record.cristexhub_dev",
    "cloudflare_dns_record.keycloak",
    "cloudflare_dns_record.reactive_resume_dev_tailscale",
    "cloudflare_zero_trust_tunnel_cloudflared.keycloak",
    "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak",
}
UPDATE = "cloudflare_zero_trust_tunnel_cloudflared_config.keycloak"
CREATE = "cloudflare_dns_record.cristexhub_prod"
PROVIDER = "registry.opentofu.org/cloudflare/cloudflare"
ACCOUNT = "8b0f511214c7a4a52ddfb62ca92c5e80"
ZONE = "3cbee16e56d7656440f93e685807e779"
TUNNEL = "f9442440-96df-4cf1-855b-7257868ed9bc"
TUNNEL_TARGET = f"{TUNNEL}.cfargotunnel.com"
SERVICE = "http://traefik.kube-system.svc.cluster.local:80"
COMMENT = "Managed by OpenTofu; Cloudflare Tunnel to CristexHub PROD via private Traefik origin"
DNS_STATES = {
    "cloudflare_dns_record.argocd_tailscale": {
        "zone_id": ZONE,
        "name": "argo.cristex-soft.com",
        "type": "A",
        "content": "100.122.139.32",
        "ttl": 300,
        "proxied": False,
        "comment": "Managed by OpenTofu; private Argo CD endpoint on Tailscale",
    },
    "cloudflare_dns_record.cristexhub_dev": {
        "zone_id": ZONE,
        "name": "dev-hub.cristex-soft.com",
        "type": "CNAME",
        "content": TUNNEL_TARGET,
        "ttl": 1,
        "proxied": True,
        "comment": "Managed by OpenTofu; Cloudflare Tunnel to CristexHub DEV via private Traefik origin",
    },
    "cloudflare_dns_record.keycloak": {
        "zone_id": ZONE,
        "name": "auth.cristex-soft.com",
        "type": "CNAME",
        "content": TUNNEL_TARGET,
        "ttl": 1,
        "proxied": True,
        "comment": "Managed by OpenTofu; Cloudflare Tunnel to private Traefik origin",
    },
    "cloudflare_dns_record.reactive_resume_dev_tailscale": {
        "zone_id": ZONE,
        "name": "resume-dev.cristex-soft.com",
        "type": "A",
        "content": "100.122.139.32",
        "ttl": 300,
        "proxied": False,
        "comment": "Managed by OpenTofu; private Reactive Resume DEV endpoint on Tailscale",
    },
}

# Sanitized values copied from the pinned Cloudflare 5.23.0 provider's local
# offline state fixture.  They exercise every computed DNS field without
# carrying any provider credential or protected state value.
DNS_RECORD_IDS = {
    "cloudflare_dns_record.argocd_tailscale": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1",
    "cloudflare_dns_record.cristexhub_dev": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb2",
    "cloudflare_dns_record.keycloak": "ccccccccccccccccccccccccccccccc3",
    "cloudflare_dns_record.reactive_resume_dev_tailscale": "ddddddddddddddddddddddddddddddd4",
}
DNS_COMPUTED = {
    "created_on": "2026-01-01T00:00:00Z",
    "modified_on": "2026-01-01T00:00:00Z",
    "comment_modified_on": "2026-01-01T00:00:00Z",
    "proxiable": True,
    "data": None,
    "meta": "{}",
    "priority": None,
    "private_routing": None,
    "settings": {"flatten_cname": False, "ipv4_only": False, "ipv6_only": False},
    "tags": [],
    "tags_modified_on": None,
}
TUNNEL_COMPUTED = {
    # Cloudflare's account_tag is the owning account ID, not an arbitrary
    # account-shaped placeholder.
    "account_tag": ACCOUNT,
    "connections": [],
    "conns_active_at": None,
    "conns_inactive_at": None,
    "created_at": "2026-01-01T00:00:00Z",
    "deleted_at": None,
    "metadata": "{}",
    "remote_config": False,
    "status": "healthy",
    "tun_type": "cfd_tunnel",
    "tunnel_secret": None,
}
OUTPUTS = {
    "tunnel_id": TUNNEL,
    "tunnel_name": "cristexhub-keycloak",
    "public_hostname": "auth.cristex-soft.com",
    "dns_record_name": "auth.cristex-soft.com",
    "token_handoff": "MANUAL_INFISICAL_HANDOFF_REQUIRED",
}
CHECKS = [
    {
        "address": {"kind": "var", "name": "cloudflare_account_id", "to_display": "var.cloudflare_account_id"},
        "status": "pass",
        "instances": [{"address": {"to_display": "var.cloudflare_account_id"}, "status": "pass"}],
    },
    {
        "address": {"kind": "var", "name": "cloudflare_tunnel_name", "to_display": "var.cloudflare_tunnel_name"},
        "status": "pass",
        "instances": [{"address": {"to_display": "var.cloudflare_tunnel_name"}, "status": "pass"}],
    },
    {
        "address": {"kind": "var", "name": "cloudflare_zone_id", "to_display": "var.cloudflare_zone_id"},
        "status": "pass",
        "instances": [{"address": {"to_display": "var.cloudflare_zone_id"}, "status": "pass"}],
    },
    {
        "address": {"kind": "var", "name": "public_hostname", "to_display": "var.public_hostname"},
        "status": "pass",
        "instances": [{"address": {"to_display": "var.public_hostname"}, "status": "pass"}],
    },
    {
        "address": {"kind": "var", "name": "traefik_origin_service", "to_display": "var.traefik_origin_service"},
        "status": "pass",
        "instances": [{"address": {"to_display": "var.traefik_origin_service"}, "status": "pass"}],
    },
]
RELEVANT_ATTRIBUTES = [
    {"resource": "cloudflare_dns_record.keycloak", "attribute": ["name"]},
    {"resource": "cloudflare_zero_trust_tunnel_cloudflared.keycloak", "attribute": ["id"]},
    {"resource": "cloudflare_zero_trust_tunnel_cloudflared.keycloak", "attribute": ["name"]},
]
IDENTITY = {
    "schema": 1,
    "scope": "cloudflare-foundation-prod-route-6-to-7",
    "account_id": ACCOUNT,
    "zone_id": ZONE,
    "tunnel_id": TUNNEL,
    "tunnel_account_tag": TUNNEL_COMPUTED["account_tag"],
    "dns_record_ids": DNS_RECORD_IDS,
}


def config_expressions(address: str) -> dict:
    if address.startswith("cloudflare_dns_record."):
        state = DNS_STATES.get(address, {
            "zone_id": ZONE,
            "name": "hub.cristex-soft.com",
            "type": "CNAME",
            "content": TUNNEL_TARGET,
            "ttl": 1,
            "proxied": True,
            "comment": COMMENT,
        })
        expressions = {
            "comment": {"constant_value": state["comment"]},
            "name": {"constant_value": state["name"]},
            "proxied": {"constant_value": state["proxied"]},
            "ttl": {"constant_value": state["ttl"]},
            "type": {"constant_value": state["type"]},
            "zone_id": {"references": ["var.cloudflare_zone_id"]},
        }
        expressions["content"] = (
            {"constant_value": state["content"]}
            if state["type"] == "A"
            else {"references": ["cloudflare_zero_trust_tunnel_cloudflared.keycloak.id", "cloudflare_zero_trust_tunnel_cloudflared.keycloak"]}
        )
        return expressions
    if address == "cloudflare_zero_trust_tunnel_cloudflared.keycloak":
        return {
            "account_id": {"references": ["var.cloudflare_account_id"]},
            "config_src": {"constant_value": "cloudflare"},
            "name": {"references": ["var.cloudflare_tunnel_name"]},
        }
    return {
        "account_id": {"references": ["var.cloudflare_account_id"]},
        "config": {"references": ["var.public_hostname", "var.traefik_origin_service", "var.traefik_origin_service", "var.traefik_origin_service"]},
        "source": {"constant_value": "cloudflare"},
        "tunnel_id": {"references": ["cloudflare_zero_trust_tunnel_cloudflared.keycloak.id", "cloudflare_zero_trust_tunnel_cloudflared.keycloak"]},
    }


def resource(address: str, actions: list[str], before, after) -> dict:
    change = {
        "actions": actions,
        "after": after,
        "after_unknown": {},
        "after_sensitive": {},
    }
    # OpenTofu 1.12.5 emits explicit null/false markers for an unset create
    # pre-state. Existing and updated resources carry concrete before values.
    change["before"] = before
    change["before_sensitive"] = False if before is None else {}
    return {
        "address": address,
        "mode": "managed",
        "type": address.split(".", 1)[0],
        "name": address.split(".", 1)[1],
        "provider_name": PROVIDER,
        "change": change,
    }


def state_resource(address: str, values: dict, depends_on: list[str] | None = None) -> dict:
    resource_type = address.split(".", 1)[0]
    if resource_type == "cloudflare_dns_record":
        sensitive_values = {"tags": []}
        if address in {
            "cloudflare_dns_record.cristexhub_dev",
            "cloudflare_dns_record.keycloak",
            CREATE,
        }:
            sensitive_values = {"settings": {}, "tags": []}
    elif resource_type == "cloudflare_zero_trust_tunnel_cloudflared":
        sensitive_values = {"connections": [], "tunnel_secret": True}
    else:
        ingress = values.get("config", {}).get("ingress", []) if isinstance(values, dict) else []
        sensitive_values = {"config": {"ingress": [{} for _ in ingress]}}
    resource = {
        "address": address,
        "mode": "managed",
        "type": resource_type,
        "name": address.split(".", 1)[1],
        "provider_name": PROVIDER,
        "schema_version": 500,
        "values": copy.deepcopy(values),
        "sensitive_values": sensitive_values,
    }
    if depends_on is not None:
        resource["depends_on"] = list(depends_on)
    return resource


def valid_plan() -> dict:
    before_rules = [
        {"hostname": "auth.cristex-soft.com", "service": SERVICE},
        {"hostname": "dev-hub.cristex-soft.com", "service": SERVICE},
        {"service": "http_status:404"},
    ]
    after_rules = [
        before_rules[0],
        before_rules[1],
        {"hostname": "hub.cristex-soft.com", "service": SERVICE},
        before_rules[2],
    ]
    tunnel_before = {
        "account_id": ACCOUNT,
        "tunnel_id": TUNNEL,
        "config": {
            "ingress": [
                {"hostname": "auth.cristex-soft.com", "origin_request": None, "path": None, "service": SERVICE},
                {"hostname": "dev-hub.cristex-soft.com", "origin_request": None, "path": None, "service": SERVICE},
                {"hostname": None, "origin_request": None, "path": None, "service": "http_status:404"},
            ],
            "origin_request": None,
        },
        "created_at": "2026-01-01T00:00:00Z",
        "id": TUNNEL,
        "source": "cloudflare",
        "version": 1,
    }
    tunnel_after = copy.deepcopy(tunnel_before)
    tunnel_after["config"]["ingress"].insert(
        2, {"hostname": "hub.cristex-soft.com", "origin_request": None, "path": None, "service": SERVICE}
    )
    tunnel_after.pop("created_at")
    tunnel_after.pop("version")
    changes = []
    for address in sorted(EXISTING - {UPDATE}):
        if address in DNS_STATES:
            state = copy.deepcopy(DNS_STATES[address])
            state.update(copy.deepcopy(DNS_COMPUTED))
            state["id"] = DNS_RECORD_IDS[address]
            if address in {
                "cloudflare_dns_record.argocd_tailscale",
                "cloudflare_dns_record.reactive_resume_dev_tailscale",
            }:
                state["settings"] = None
        else:
            state = {
                "account_id": ACCOUNT,
                "id": TUNNEL,
                "name": "cristexhub-keycloak",
                "config_src": "cloudflare",
                **copy.deepcopy(TUNNEL_COMPUTED),
            }
        changes.append(resource(address, ["no-op"], state, copy.deepcopy(state)))
    changes.extend(
        [
            resource(UPDATE, ["update"], tunnel_before, tunnel_after),
            resource(
                CREATE,
                ["create"],
                None,
                {
                    "zone_id": ZONE,
                    "name": "hub.cristex-soft.com",
                    "type": "CNAME",
                    "content": TUNNEL_TARGET,
                    "ttl": 1,
                    "proxied": True,
                    "comment": COMMENT,
                    "data": None,
                    "priority": None,
                    "private_routing": None,
                },
            ),
        ]
    )
    for item in changes:
        address = item["address"]
        change = item["change"]
        if address in DNS_STATES:
            marker = {"tags": []}
            if address in {
                "cloudflare_dns_record.cristexhub_dev",
                "cloudflare_dns_record.keycloak",
            }:
                marker = {"settings": {}, "tags": []}
            change["before_sensitive"] = copy.deepcopy(marker)
            change["after_sensitive"] = copy.deepcopy(marker)
        elif address == "cloudflare_zero_trust_tunnel_cloudflared.keycloak":
            marker = {"connections": [], "tunnel_secret": True}
            change["before_sensitive"] = copy.deepcopy(marker)
            change["after_sensitive"] = copy.deepcopy(marker)
        elif address == UPDATE:
            change["before_sensitive"] = {"config": {"ingress": [{}, {}, {}]}}
            change["after_sensitive"] = {"config": {"ingress": [{}, {}, {}, {}]}}
            change["after_unknown"] = {
                "config": {"ingress": [{}, {}, {}, {}]},
                "created_at": True,
                "version": True,
            }
        elif address == CREATE:
            change["after_sensitive"] = {"settings": {}, "tags": []}
            change["after_unknown"] = {
                "comment_modified_on": True,
                "created_on": True,
                "id": True,
                "meta": True,
                "modified_on": True,
                "proxiable": True,
                "settings": True,
                "tags": True,
                "tags_modified_on": True,
            }
    output_changes = {
        name: {
            "actions": ["no-op"],
            "before": value,
            "after": value,
            "after_unknown": False,
            "before_sensitive": False,
            "after_sensitive": False,
        }
        for name, value in OUTPUTS.items()
    }
    changes_by_address = {item["address"]: item for item in changes}
    # This is the actual 1.12.5 plan envelope shape, with provider-computed
    # Cloudflare state fields represented by sanitized offline fixture values.
    return {
        "format_version": "1.2",
        "terraform_version": "1.12.5",
        "variables": {
            "cloudflare_account_id": {"value": ACCOUNT},
            "cloudflare_zone_id": {"value": ZONE},
            "cloudflare_tunnel_name": {"value": "cristexhub-keycloak"},
            "public_hostname": {"value": "auth.cristex-soft.com"},
            "traefik_origin_service": {"value": SERVICE},
        },
        "planned_values": {
            "outputs": {
                name: {"sensitive": False, "type": "string", "value": value}
                for name, value in OUTPUTS.items()
            },
            "root_module": {
                "resources": [
                    state_resource(address, changes_by_address[address]["change"]["after"])
                    for address in sorted(EXISTING | {CREATE})
                ],
            },
        },
        "resource_changes": changes,
        "resource_drift": [],
        "output_changes": output_changes,
        "prior_state": {
            "format_version": "1.0",
            "terraform_version": "1.12.5",
            "values": {
                "outputs": {
                    name: {"sensitive": False, "type": "string", "value": value}
                    for name, value in OUTPUTS.items()
                },
                "root_module": {
                    "resources": [
                        state_resource(
                            address,
                            changes_by_address[address]["change"]["before"],
                            ["cloudflare_zero_trust_tunnel_cloudflared.keycloak"]
                            if address in {
                                "cloudflare_dns_record.cristexhub_dev",
                                "cloudflare_dns_record.keycloak",
                                UPDATE,
                            }
                            else None,
                        )
                        for address in sorted(EXISTING)
                    ],
                },
            },
        },
        "configuration": {
            "provider_config": {
                "cloudflare": {
                    "name": "cloudflare",
                    "full_name": PROVIDER,
                    "version_constraint": "5.23.0",
                    "expressions": {
                        "api_token": {"constant_value": "SANITIZED_PROVIDER_TOKEN"},
                        "base_url": {"constant_value": "https://api.cloudflare.com/client/v4"},
                    },
                }
            },
            "root_module": {
                "variables": {
                    "cloudflare_account_id": {
                        "type": "string",
                        "description": "Cloudflare account ID. Supply through an uncommitted tfvars file or environment variable.",
                        "required": True,
                    },
                    "cloudflare_zone_id": {
                        "type": "string",
                        "description": "Cloudflare zone ID for cristex-soft.com. Supply through an uncommitted tfvars file or environment variable.",
                        "required": True,
                    },
                    "cloudflare_tunnel_name": {
                        "type": "string",
                        "description": "Stable human-readable name for the remotely managed Cloudflare Tunnel.",
                        "default": "cristexhub-keycloak",
                    },
                    "public_hostname": {
                        "type": "string",
                        "description": "Approved public hostname routed by the Tunnel.",
                        "default": "auth.cristex-soft.com",
                    },
                    "traefik_origin_service": {
                        "type": "string",
                        "description": "Private Traefik origin URL reached by cloudflared inside the cluster.",
                        "default": SERVICE,
                    },
                },
                "outputs": {
                    "dns_record_name": {
                        "description": "DNS record name managed for the Tunnel hostname.",
                        "expression": {"references": ["cloudflare_dns_record.keycloak.name", "cloudflare_dns_record.keycloak"]},
                    },
                    "public_hostname": {
                        "description": "Public hostname configured for the Tunnel.",
                        "expression": {"references": ["var.public_hostname"]},
                    },
                    "token_handoff": {
                        "description": "The Tunnel token is intentionally not retrieved, output, or stored by OpenTofu.",
                        "expression": {"constant_value": "MANUAL_INFISICAL_HANDOFF_REQUIRED"},
                    },
                    "tunnel_id": {
                        "description": "Cloudflare Tunnel UUID; required for the separately guarded token handoff.",
                        "expression": {"references": ["cloudflare_zero_trust_tunnel_cloudflared.keycloak.id", "cloudflare_zero_trust_tunnel_cloudflared.keycloak"]},
                    },
                    "tunnel_name": {
                        "description": "Cloudflare Tunnel name.",
                        "expression": {"references": ["cloudflare_zero_trust_tunnel_cloudflared.keycloak.name", "cloudflare_zero_trust_tunnel_cloudflared.keycloak"]},
                    },
                },
                "resources": [
                    {
                        "address": address,
                        "mode": "managed",
                        "type": address.split(".", 1)[0],
                        "name": address.split(".", 1)[1],
                        "provider_config_key": "cloudflare",
                        "expressions": config_expressions(address),
                        "schema_version": 500,
                    }
                    for address in sorted(EXISTING | {CREATE})
                ],
            },
        },
        "relevant_attributes": copy.deepcopy(RELEVANT_ATTRIBUTES),
        "checks": copy.deepcopy(CHECKS),
        "timestamp": "2026-01-01T00:00:00Z",
        "errored": False,
    }


class OpenTofuFoundationProdPlanContractTests(unittest.TestCase):
    def run_validator(
        self,
        plan: dict,
        identity: dict = IDENTITY,
        extra_env: dict[str, str] | None = None,
        token_stdin: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "plan.json"
            identity_path = Path(temp) / "identity.json"
            path.write_text(json.dumps(plan))
            identity_path.write_text(json.dumps(identity))
            path.chmod(0o600)
            identity_path.chmod(0o600)
            # Use an explicit clean environment so these tests cannot inherit a
            # real provider credential or a controller-only hidden-input name.
            environment = {
                "HOME": "/tmp",
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
            }
            attestation_path = Path(temp) / "identity.attestation"
            attestation_path.write_text(
                "identity_sha256="
                + hashlib.sha256(identity_path.read_bytes()).hexdigest()
                + "\nidentity_scope=cloudflare-foundation-prod-route-6-to-7\n"
            )
            attestation_path.chmod(0o600)
            environment["CRISTEXWEB_PROD_ROUTE_IDENTITY_SHA256"] = hashlib.sha256(
                identity_path.read_bytes()
            ).hexdigest()
            environment["CRISTEXWEB_PROD_ROUTE_IDENTITY_ATTESTATION"] = str(attestation_path)
            if extra_env:
                environment.update(extra_env)
            command = ["/usr/bin/python3", str(VALIDATE), str(path), str(identity_path)]
            input_data = None
            if token_stdin is not None:
                command.append("--token-stdin")
                input_data = token_stdin + "\n"
            return subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                input=input_data,
                env=environment,
            )

    def test_exact_plan_is_accepted(self) -> None:
        result = self.run_validator(valid_plan())
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("existing_addresses=6", result.stdout)
        self.assertIn("created=cloudflare_dns_record.cristexhub_prod", result.stdout)
        self.assertIn("updated=cloudflare_zero_trust_tunnel_cloudflared_config.keycloak", result.stdout)
        self.assertIn("apply=not-run", result.stdout)
        self.assertIn("outputs=no-op", result.stdout)

    def test_direct_unbound_validator_invocation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_path = Path(temp) / "plan.json"
            identity_path = Path(temp) / "identity.json"
            plan_path.write_text(json.dumps(valid_plan()))
            identity_path.write_text(json.dumps(IDENTITY))
            plan_path.chmod(0o600)
            identity_path.chmod(0o600)
            environment = os.environ.copy()
            environment.pop("CRISTEXWEB_PROD_ROUTE_IDENTITY_SHA256", None)
            environment.pop("CRISTEXWEB_PROD_ROUTE_IDENTITY_ATTESTATION", None)
            result = subprocess.run(
                ["/usr/bin/python3", str(VALIDATE), str(plan_path), str(identity_path)],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("identity_profile_attestation", result.stdout)

    def test_pinned_cloudflare_provider_offline_fixture_is_accepted(self) -> None:
        candidate = json.loads(FIXTURE.read_text())
        result = self.run_validator(candidate)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("outputs=no-op", result.stdout)

    def test_standard_envelope_safety_markers_are_checked(self) -> None:
        for field, value in (
            ("planned_values", {"root_module": {"sensitive_values": {"token": True}}}),
            ("prior_state", {"values": {"sensitive_values": {"token": True}}}),
            ("configuration", {"root_module": {"sensitive": True}}),
        ):
            candidate = valid_plan()
            candidate[field] = value
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, field)
        candidate = valid_plan()
        candidate["configuration"]["unexpected"] = {}
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "configuration unknown key")
        candidate = valid_plan()
        candidate["prior_state"]["terraform_version"] = "1.10.0"
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "prior state version")

    def test_only_resource_drift_may_be_omitted(self) -> None:
        candidate = valid_plan()
        candidate.pop("resource_drift")
        result = self.run_validator(candidate)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for key in (
            "variables",
            "planned_values",
            "prior_state",
            "configuration",
            "relevant_attributes",
            "checks",
            "timestamp",
            "errored",
        ):
            candidate = valid_plan()
            candidate.pop(key)
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, f"required {key}")

    def test_adversarial_actions_and_scope_are_rejected(self) -> None:
        cases = []
        # Keep the case table explicit so every forbidden mutation is covered.
        for action in (["create"], ["delete"], ["replace"], ["read"], ["update", "create"]):
            candidate = valid_plan()
            update_change = next(
                item for item in candidate["resource_changes"] if item["address"] == UPDATE
            )
            update_change["change"]["actions"] = action
            cases.append(("action", candidate))
        for field, value in (
            ("replace_paths", [["name"]]),
            ("after_unknown", {"id": True}),
            ("before_unknown", {"id": True}),
            ("before_sensitive", {"content": True}),
            ("after_sensitive", {"content": True}),
        ):
            candidate = valid_plan()
            candidate["resource_changes"][0]["change"][field] = value
            cases.append((field, candidate))
        candidate = valid_plan()
        candidate["resource_changes"][0]["deposed"] = "old-instance"
        cases.append(("deposed", candidate))
        candidate = valid_plan()
        candidate["deferred_changes"] = [{"resource": "unexpected"}]
        cases.append(("deferred", candidate))
        candidate = valid_plan()
        candidate["output_changes"] = {"unexpected": {"actions": []}}
        cases.append(("outputs", candidate))
        candidate = valid_plan()
        update_change = next(
            item for item in candidate["resource_changes"] if item["address"] == UPDATE
        )
        update_change["change"]["after"]["config"]["ingress"].append(
            {"hostname": "evil.example", "service": SERVICE}
        )
        cases.append(("other-ingress", candidate))
        candidate = valid_plan()
        candidate["resource_changes"][-1]["change"]["after"]["name"] = "evil.example"
        cases.append(("wrong-dns-name", candidate))
        candidate = valid_plan()
        candidate["resource_changes"][-1]["change"]["after"]["proxied"] = False
        cases.append(("wrong-proxy", candidate))
        candidate = valid_plan()
        candidate["resource_changes"] = candidate["resource_changes"][:-1]
        cases.append(("missing-resource", candidate))
        candidate = valid_plan()
        candidate["resource_changes"].append(copy.deepcopy(candidate["resource_changes"][0]))
        cases.append(("duplicate-resource", candidate))
        for label, plan in cases:
            result = self.run_validator(plan)
            self.assertNotEqual(0, result.returncode, label)
            self.assertIn("prod_plan=refused", result.stdout, label)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "duplicate.json"
            identity_path = Path(temp) / "identity.json"
            identity_path.write_text(json.dumps(IDENTITY))
            identity_path.chmod(0o600)
            attestation_path = Path(temp) / "identity.attestation"
            profile_hash = hashlib.sha256(identity_path.read_bytes()).hexdigest()
            attestation_path.write_text(
                f"identity_sha256={profile_hash}\n"
                "identity_scope=cloudflare-foundation-prod-route-6-to-7\n"
            )
            attestation_path.chmod(0o600)
            validator_env = {
                **os.environ,
                "CRISTEXWEB_PROD_ROUTE_IDENTITY_SHA256": profile_hash,
                "CRISTEXWEB_PROD_ROUTE_IDENTITY_ATTESTATION": str(attestation_path),
            }
            path.write_text(
                '{"format_version":"1.2","resource_changes":[],'
                '"output_changes":{},"output_changes":{}}'
            )
            path.chmod(0o600)
            result = subprocess.run(
                ["/usr/bin/python3", str(VALIDATE), str(path), str(identity_path)],
                check=False,
                capture_output=True,
                text=True,
                env=validator_env,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("plan_json_parse", result.stdout)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nested-duplicate.json"
            identity_path = Path(temp) / "identity.json"
            identity_path.write_text(json.dumps(IDENTITY))
            identity_path.chmod(0o600)
            attestation_path = Path(temp) / "identity.attestation"
            profile_hash = hashlib.sha256(identity_path.read_bytes()).hexdigest()
            attestation_path.write_text(
                f"identity_sha256={profile_hash}\n"
                "identity_scope=cloudflare-foundation-prod-route-6-to-7\n"
            )
            attestation_path.chmod(0o600)
            validator_env = {
                **os.environ,
                "CRISTEXWEB_PROD_ROUTE_IDENTITY_SHA256": profile_hash,
                "CRISTEXWEB_PROD_ROUTE_IDENTITY_ATTESTATION": str(attestation_path),
            }
            raw = json.dumps(valid_plan()).replace(
                '"actions": ["no-op"],',
                '"actions": ["no-op"], "actions": ["delete"],',
                1,
            )
            path.write_text(raw)
            path.chmod(0o600)
            result = subprocess.run(
                ["/usr/bin/python3", str(VALIDATE), str(path), str(identity_path)],
                check=False,
                capture_output=True,
                text=True,
                env=validator_env,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("plan_json_parse", result.stdout)

    def test_variable_inventory_and_deprecated_metadata_are_exact(self) -> None:
        candidate = valid_plan()
        candidate["variables"].pop("cloudflare_zone_id")
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "missing variable")
        candidate = valid_plan()
        candidate["variables"]["cloudflare_zone_id"]["deprecated"] = "legacy"
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "deprecated variable metadata")
        candidate = valid_plan()
        candidate["variables"]["cloudflare_zone_id"]["value"] = ACCOUNT
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "wrong variable value")

    def test_configuration_expression_types_are_strict(self) -> None:
        # Python considers True == 1.  Configuration expressions are an
        # untrusted plan projection, so bool/int collisions must not pass.
        for address in (*DNS_STATES, CREATE):
            for field, malformed in (("proxied", 0), ("proxied", 1), ("ttl", True)):
                candidate = valid_plan()
                expression_resource = next(
                    resource
                    for resource in candidate["configuration"]["root_module"]["resources"]
                    if resource["address"] == address
                )
                expression_resource["expressions"][field]["constant_value"] = malformed
                result = self.run_validator(candidate)
                self.assertNotEqual(
                    0,
                    result.returncode,
                    f"configuration-{address}-{field}-{malformed!r}",
                )

    def test_token_bearing_plan_is_rejected_via_token_stdin_even_with_digest(self) -> None:
        marker = "SYNTHETIC_PROVIDER_TOKEN_9f2a"
        candidate = valid_plan()
        candidate["configuration"]["provider_config"]["cloudflare"]["expressions"][
            "api_token"
        ]["constant_value"] = marker
        result = self.run_validator(
            candidate,
            token_stdin=marker,
            extra_env={
                "CRISTEXWEB_PROD_PLAN_PROVIDER_TOKEN_SHA256": hashlib.sha256(
                    marker.encode()
                ).hexdigest()
            },
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("plan_provider_token", result.stdout)
        # The same stdin path must reject a token hidden in a nested key/value,
        # not only the provider configuration field.
        candidate = valid_plan()
        candidate["planned_values"]["root_module"]["resources"][0]["values"][
            "token"
        ] = marker
        result = self.run_validator(candidate, token_stdin=marker)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("plan_provider_token", result.stdout)

    def test_validator_rejects_internal_hidden_input_environment(self) -> None:
        for name in ("cloudflare_token", "read_hidden_result", "CLOUDFLARE_API_TOKEN"):
            result = self.run_validator(valid_plan(), extra_env={name: "synthetic"})
            self.assertNotEqual(0, result.returncode, name)
            self.assertIn("forbidden_environment", result.stdout, name)

    def test_token_transport_uses_real_exec_provider_shape(self) -> None:
        # The Cloudflare provider requires CLOUDFLARE_API_TOKEN in its process
        # environment.  Exercise the same stdin -> clean env -> shell read ->
        # export -> exec shape as the wrappers, with a provider-shaped helper.
        # The token is intentionally observable in the provider environment:
        # this test makes no false /proc confidentiality claim.
        marker = "PROC_TOKEN_SENTINEL_7d6f0a5e"
        marker_digest = hashlib.sha256(marker.encode()).hexdigest()
        transport = (
            "IFS= read -r CLOUDFLARE_API_TOKEN || exit 74; "
            "export CLOUDFLARE_API_TOKEN; exec \"$@\""
        )
        for wrapper in (PLAN, RECONCILE):
            source = wrapper.read_text()
            self.assertIn("printf '%s\\n' \"$cloudflare_token\" | /usr/bin/env -i", source)
            self.assertIn("IFS= read -r CLOUDFLARE_API_TOKEN", source, wrapper.name)
            self.assertIn('export CLOUDFLARE_API_TOKEN; exec "$@"', source, wrapper.name)
            self.assertNotIn("/usr/bin/sudo", source, wrapper.name)
            self.assertNotIn("provider_sudo", source, wrapper.name)
            self.assertIn("plan_stdout=", source, wrapper.name)
            self.assertIn('run_capture_with_token "$plan_stdout"', source, wrapper.name)
            self.assertNotIn('run_capture_with_token "$plan_file"', source, wrapper.name)
            self.assertNotIn(
                'CLOUDFLARE_API_TOKEN="$cloudflare_token"', source, wrapper.name
            )
            for forbidden in (
                "cloudflare_token|",
                "cloudflare_token_sha256|",
                "read_hidden_result)",
            ):
                self.assertIn(forbidden, source, wrapper.name)
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                provider = root / "provider-shaped.py"
                # The marker is supplied through stdin, not embedded in this
                # source file, argv, or the helper's inherited environment.
                provider.write_text(
                    "import hashlib, os, sys, time\n"
                    "token = os.environ.get('CLOUDFLARE_API_TOKEN', '')\n"
                    "if not token:\n"
                    "    raise SystemExit('missing provider token')\n"
                    "sys.stdout.write(hashlib.sha256(token.encode()).hexdigest() + '\\n')\n"
                    "sys.stdout.flush()\n"
                    "time.sleep(3)\n"
                )
                provider.chmod(0o700)
                child = subprocess.Popen(
                    [
                        "/usr/bin/env",
                        "-i",
                        "HOME=/tmp",
                        "PATH=/usr/local/bin:/usr/bin:/bin",
                        "LC_ALL=C",
                        "/bin/sh",
                        "-c",
                        transport,
                        "provider-child",
                        "/usr/bin/python3",
                        str(provider),
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env={"HOME": "/tmp", "PATH": "/usr/local/bin:/usr/bin:/bin"},
                )
                try:
                    assert child.stdin is not None
                    assert child.stdout is not None
                    child.stdin.write((marker + "\n").encode("ascii"))
                    child.stdin.close()
                    self.assertEqual(
                        (marker_digest + "\n").encode("ascii"),
                        child.stdout.readline(),
                    )
                    proc_dir = Path("/proc") / str(child.pid)
                    argv = (proc_dir / "cmdline").read_bytes()
                    self.assertNotIn(marker.encode(), argv)
                    provider_environment = (proc_dir / "environ").read_bytes()
                    self.assertIn(marker.encode(), provider_environment)
                    self.assertIsNone(child.poll())
                    self.assertNotIn(marker, os.environ)
                    for path in root.rglob("*"):
                        if path.is_file():
                            self.assertNotIn(marker.encode(), path.read_bytes(), str(path))
                finally:
                    if child.poll() is None:
                        child.terminate()
                    child.wait(timeout=2)
                    assert child.stdout is not None
                    assert child.stderr is not None
                    output = child.stdout.read() + child.stderr.read()
                    child.stdout.close()
                    child.stderr.close()
                    self.assertNotIn(marker.encode(), output)

    def test_sensitive_values_markers_are_exact_per_dns_record_kind(self) -> None:
        cases = (
            ("cloudflare_dns_record.argocd_tailscale", {"settings": {}, "tags": []}),
            ("cloudflare_dns_record.cristexhub_dev", {"tags": []}),
            (CREATE, {"tags": []}),
        )
        for address, marker in cases:
            candidate = valid_plan()
            resource = next(
                resource
                for resource in candidate["planned_values"]["root_module"]["resources"]
                if resource["address"] == address
            )
            resource["sensitive_values"] = marker
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, address)
        candidate = valid_plan()
        resource = next(
            resource
            for resource in candidate["planned_values"]["root_module"]["resources"]
            if resource["address"] == CREATE
        )
        self.assertEqual({"settings": {}, "tags": []}, resource["sensitive_values"])
        self.assertEqual(0, self.run_validator(candidate).returncode)
        for key in ("sensitive_values", "schema_version"):
            candidate = valid_plan()
            resource = next(
                resource
                for resource in candidate["planned_values"]["root_module"]["resources"]
                if resource["address"] == CREATE
            )
            resource.pop(key)
            self.assertNotEqual(0, self.run_validator(candidate).returncode, key)

    def test_state_resource_values_are_recursive_and_secret_free(self) -> None:
        for section in ("planned_values", "prior_state"):
            candidate = valid_plan()
            if section == "planned_values":
                resources = candidate[section]["root_module"]["resources"]
            else:
                resources = candidate[section]["values"]["root_module"]["resources"]
            resources[0]["values"] = {"tunnel_secret": "TOP-SECRET"}
            resources[0]["sensitive_values"] = {}
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, section)
        candidate = valid_plan()
        planned_config = next(
            resource for resource in candidate["planned_values"]["root_module"]["resources"]
            if resource["address"] == UPDATE
        )
        planned_config["values"]["config"]["ingress"][0]["hostname"] = "evil.example"
        self.assertNotEqual(0, self.run_validator(candidate).returncode, "planned-route-drift")
        candidate = valid_plan()
        prior_config = next(
            resource for resource in candidate["prior_state"]["values"]["root_module"]["resources"]
            if resource["address"] == UPDATE
        )
        prior_config["values"]["config"]["ingress"].append(
            {"hostname": "evil.example", "origin_request": None, "path": None, "service": SERVICE}
        )
        self.assertNotEqual(0, self.run_validator(candidate).returncode, "prior-route-drift")
        candidate = valid_plan()
        resource_change = next(
            item for item in candidate["resource_changes"]
            if item["address"] == "cloudflare_zero_trust_tunnel_cloudflared.keycloak"
        )
        resource_change["change"]["after_sensitive"] = False
        resource_change["change"]["after"]["tunnel_secret"] = "TOP-SECRET"
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "false-sensitive-marker")

    def test_sensitive_output_and_unknown_metadata_cannot_hide_in_plan(self) -> None:
        for top_level, value in (
            ("output_changes", {"token": {"actions": [], "sensitive": True}}),
            ("unknown", {"future": True}),
            ("resource_drift", [{"address": UPDATE}]),
        ):
            candidate = valid_plan()
            candidate[top_level] = value
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, top_level)

    def test_exact_five_outputs_are_noop_and_nonsensitive(self) -> None:
        self.assertEqual(
            set(OUTPUTS),
            set(re.findall(r'output "([^"]+)"', (TOFU / "outputs.tf").read_text())),
        )
        for name, output in OUTPUTS.items():
            change = valid_plan()["output_changes"][name]
            self.assertEqual(["no-op"], change["actions"])
            self.assertEqual(output, change["before"])
            self.assertEqual(output, change["after"])
            self.assertFalse(change["before_sensitive"])
            self.assertFalse(change["after_sensitive"])
            self.assertFalse(change["after_unknown"])
        for name, mutation in (
            ("tunnel_id", lambda change: change.update({"after": "0" * 36})),
            ("tunnel_name", lambda change: change.update({"actions": ["update"]})),
            ("public_hostname", lambda change: change.update({"after_unknown": True})),
            ("dns_record_name", lambda change: change.update({"after_sensitive": True})),
            ("token_handoff", lambda change: change.update({"extra": None})),
        ):
            candidate = valid_plan()
            mutation(candidate["output_changes"][name])
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, name)
        for name in ("tunnel_id", "tunnel_name", "public_hostname", "dns_record_name", "token_handoff"):
            candidate = valid_plan()
            candidate["output_changes"].pop(name)
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, f"missing-{name}")
        candidate = valid_plan()
        candidate["output_changes"]["extra_output"] = copy.deepcopy(
            candidate["output_changes"]["tunnel_id"]
        )
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "extra-output")

    def test_provider_computed_fields_are_allowlisted_typed_and_unchanged(self) -> None:
        for address, field, value in (
            ("cloudflare_dns_record.argocd_tailscale", "created_on", "not-a-timestamp"),
            ("cloudflare_dns_record.argocd_tailscale", "id", "0" * 32 + "/" + "a" * 32),
            ("cloudflare_dns_record.argocd_tailscale", "settings", {"unexpected": False}),
            ("cloudflare_dns_record.argocd_tailscale", "tags", [False]),
            ("cloudflare_dns_record.argocd_tailscale", "proxiable", "true"),
            ("cloudflare_zero_trust_tunnel_cloudflared.keycloak", "account_tag", "not-hex"),
            ("cloudflare_zero_trust_tunnel_cloudflared.keycloak", "connections", [False]),
            ("cloudflare_zero_trust_tunnel_cloudflared.keycloak", "metadata", "metadata"),
            ("cloudflare_zero_trust_tunnel_cloudflared.keycloak", "remote_config", 1),
            ("cloudflare_zero_trust_tunnel_cloudflared.keycloak", "tunnel_secret", "secret"),
        ):
            candidate = valid_plan()
            item = next(item for item in candidate["resource_changes"] if item["address"] == address)
            item["change"]["before"][field] = value
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, f"type-{address}-{field}")
        candidate = valid_plan()
        item = next(
            item for item in candidate["resource_changes"]
            if item["address"] == "cloudflare_dns_record.argocd_tailscale"
        )
        item["change"]["after"]["modified_on"] = "2026-01-02T00:00:00Z"
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "computed-drift")
        candidate = valid_plan()
        item = next(
            item for item in candidate["resource_changes"]
            if item["address"] == "cloudflare_zero_trust_tunnel_cloudflared.keycloak"
        )
        item["change"]["after"].pop("status")
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "computed-missing-side")

    def test_optional_schema_fields_and_unknown_keys_are_handled_exactly(self) -> None:
        # Documented resource/change fields are accepted only in their safe form.
        candidate = valid_plan()
        for item in candidate["resource_changes"]:
            item["index"] = None
            item["deposed"] = None
            item["schema_version"] = 0
            item["action_reason"] = ""
            item["previous_address"] = None
            item["module_address"] = None
            item["change"]["replace_paths"] = []
            item["change"]["importing"] = None
            item["change"]["generated_config"] = ""
            item["change"]["before_identity"] = {}
            item["change"]["after_identity"] = None
        result = self.run_validator(candidate)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for key, value in (
            ("deposed", False),
            ("action_reason", "unexpected"),
            ("errored", True),
            ("complete", False),
            ("proposed_unknown", {"future": True}),
            ("unknown", {"future": True}),
        ):
            candidate = valid_plan()
            candidate[key] = value
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, f"top-level {key}")
        for key, value in (
            ("deposed", "old-instance"),
            ("previous_address", "module.old.resource"),
            ("module_address", "module.old"),
            ("index", 0),
            ("action_reason", "replace_because_tainted"),
            ("unknown_resource_key", None),
        ):
            candidate = valid_plan()
            candidate["resource_changes"][0][key] = value
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, f"resource {key}")
        candidate = valid_plan()
        candidate["resource_changes"][0]["change"]["action_reason"] = None
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "change action_reason")

    def test_account_tag_is_bound_to_attested_account_across_projections(self) -> None:
        candidate = valid_plan()
        alternate = "f" * 32
        for item in candidate["resource_changes"]:
            for side in ("before", "after"):
                value = item["change"].get(side)
                if isinstance(value, dict) and "account_tag" in value:
                    value["account_tag"] = alternate
        for projection in (candidate["planned_values"], candidate["prior_state"]["values"]):
            for item in projection["root_module"]["resources"]:
                values = item.get("values")
                if isinstance(values, dict) and "account_tag" in values:
                    values["account_tag"] = alternate
        identity = copy.deepcopy(IDENTITY)
        identity["tunnel_account_tag"] = alternate
        result = self.run_validator(candidate, identity)
        self.assertNotEqual(0, result.returncode, "account-tag-must-equal-attested-account")

    def test_prompt_bound_identity_is_required_and_exact(self) -> None:
        candidate = valid_plan()
        identity = copy.deepcopy(IDENTITY)
        identity["dns_record_ids"]["cloudflare_dns_record.keycloak"] = "f" * 32
        self.assertNotEqual(0, self.run_validator(candidate, identity).returncode)
        identity = copy.deepcopy(IDENTITY)
        identity["tunnel_account_tag"] = "0" * 32
        self.assertNotEqual(0, self.run_validator(candidate, identity).returncode)
        identity = copy.deepcopy(IDENTITY)
        identity["dns_record_ids"] = {
            address: DNS_RECORD_IDS["cloudflare_dns_record.argocd_tailscale"]
            for address in DNS_STATES
        }
        self.assertNotEqual(0, self.run_validator(candidate, identity).returncode)
        identity = copy.deepcopy(IDENTITY)
        identity["account_id"] = "0" * 32
        self.assertNotEqual(0, self.run_validator(candidate, identity).returncode)
        identity = copy.deepcopy(IDENTITY)
        identity["schema"] = True
        self.assertNotEqual(0, self.run_validator(candidate, identity).returncode)
        with tempfile.TemporaryDirectory() as temp:
            plan_path = Path(temp) / "plan.json"
            identity_path = Path(temp) / "identity.json"
            plan_path.write_text(json.dumps(valid_plan()))
            identity_path.write_text(json.dumps(IDENTITY))
            plan_path.chmod(0o600)
            identity_path.chmod(0o644)
            result = subprocess.run(
                ["/usr/bin/python3", str(VALIDATE), str(plan_path), str(identity_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("identity_file_permissions", result.stdout)

    def test_identity_profile_hash_is_attested_before_provider_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            identity_path = Path(temp) / "identity.json"
            plan_path = Path(temp) / "plan.json"
            identity_path.write_text(json.dumps(IDENTITY, sort_keys=True, indent=2) + "\n")
            plan_path.write_text(json.dumps(valid_plan(), sort_keys=True, indent=2) + "\n")
            identity_path.chmod(0o600)
            plan_path.chmod(0o600)
            profile_hash = hashlib.sha256(identity_path.read_bytes()).hexdigest()
            attestation_path = Path(temp) / "identity.attestation"
            attestation_path.write_text(
                f"identity_sha256={profile_hash}\n"
                "identity_scope=cloudflare-foundation-prod-route-6-to-7\n"
            )
            attestation_path.chmod(0o600)
            accepted = subprocess.run(
                ["/usr/bin/python3", str(VALIDATE), str(plan_path), str(identity_path)],
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "CRISTEXWEB_PROD_ROUTE_IDENTITY_SHA256": profile_hash,
                    "CRISTEXWEB_PROD_ROUTE_IDENTITY_ATTESTATION": str(attestation_path),
                },
            )
            self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)
            rejected = subprocess.run(
                ["/usr/bin/python3", str(VALIDATE), str(plan_path), str(identity_path)],
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "CRISTEXWEB_PROD_ROUTE_IDENTITY_SHA256": "0" * 64,
                    "CRISTEXWEB_PROD_ROUTE_IDENTITY_ATTESTATION": str(attestation_path),
                },
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("identity_profile_attestation", rejected.stdout)

    def test_checks_relevant_attributes_and_cross_projections_are_exact(self) -> None:
        candidate = valid_plan()
        candidate["checks"][0]["status"] = "fail"
        self.assertNotEqual(0, self.run_validator(candidate).returncode)
        candidate = valid_plan()
        candidate["checks"][0]["instances"][0]["address"]["to_display"] = "var.evil"
        self.assertNotEqual(0, self.run_validator(candidate).returncode)
        candidate = valid_plan()
        candidate["relevant_attributes"][0]["attribute"] = ["content"]
        self.assertNotEqual(0, self.run_validator(candidate).returncode)
        candidate = valid_plan()
        candidate["relevant_attributes"].append(copy.deepcopy(candidate["relevant_attributes"][0]))
        self.assertNotEqual(0, self.run_validator(candidate).returncode)
        candidate = valid_plan()
        candidate["planned_values"]["outputs"]["tunnel_id"]["value"] = "TOP-SECRET"
        self.assertNotEqual(0, self.run_validator(candidate).returncode)
        candidate = valid_plan()
        candidate["planned_values"]["outputs"]["tunnel_id"]["deprecated"] = "legacy"
        self.assertNotEqual(0, self.run_validator(candidate).returncode)
        candidate = valid_plan()
        candidate["prior_state"]["values"]["outputs"]["public_hostname"]["value"] = "evil.example"
        self.assertNotEqual(0, self.run_validator(candidate).returncode)
        candidate = valid_plan()
        candidate["configuration"]["root_module"]["outputs"]["tunnel_id"]["metadata"] = {}
        self.assertNotEqual(0, self.run_validator(candidate).returncode)
        candidate = valid_plan()
        candidate["configuration"]["root_module"]["resources"][0]["metadata"] = {}
        self.assertNotEqual(0, self.run_validator(candidate).returncode)

    def test_provider_schema_projection_and_fixture_provenance_are_exact(self) -> None:
        provenance = PROVENANCE.read_text()
        for required in (
            "OpenTofu: `1.12.5`",
            "Cloudflare provider: `5.23.0`",
            "providers schema -json",
            "73c49687d5b31bc0ea15962be1bb3d75bda3d07782e7b02faeb3c4a1851332fd",
            "36dae7ca1e4f1552a6faef27179dc16ef403203e956f31416c17b3d87a38c3f4",
            "plain record UUID",
            "CNAME `settings` is normalized to all-false",
            "metadata is the normalized string",
            "after_unknown",
            "No API token",
            "one-to-one sanitization receipt",
            "protected identity values are not included",
            "distinct sanitized placeholders",
            "exact five passing source-variable",
            "relevant_attributes",
            "five output no-ops",
            "5a8b684fff73afaa2412142e5f6d3136e055d3de73fa9cbf6d7fbe207f9ebd71",
        ):
            self.assertIn(required, provenance)
        self.assertNotRegex(provenance, r"(?i)(api[_ -]?token|password|secret|authorization)\s*[:=]\s*[^`\n]+")
        receipt = json.loads(IDENTITY_RECEIPT.read_text())
        self.assertEqual(1, receipt["schema"])
        self.assertEqual("one-to-one sanitization receipt", receipt["kind"])
        self.assertFalse(receipt["protected_identity_values_included"])
        self.assertEqual(
            hashlib.sha256(IDENTITY_RECEIPT.read_bytes()).hexdigest(),
            "5a8b684fff73afaa2412142e5f6d3136e055d3de73fa9cbf6d7fbe207f9ebd71",
        )
        mappings = receipt["mappings"]
        self.assertEqual(5, len(mappings))
        self.assertEqual(5, len({entry["logical"] for entry in mappings}))
        self.assertEqual(5, len({entry["placeholder_value"] for entry in mappings}))
        self.assertTrue(all(entry["label"].startswith("SANITIZED_") for entry in mappings))
        fixture = json.loads(FIXTURE.read_text())
        fixture_identities = {
            **{
                f"{address}.id": next(
                    item["change"]["after"]["id"]
                    for item in fixture["resource_changes"]
                    if item["address"] == address
                )
                for address in DNS_STATES
            },
            "cloudflare_zero_trust_tunnel_cloudflared.keycloak.account_tag": next(
                item["change"]["after"]["account_tag"]
                for item in fixture["resource_changes"]
                if item["address"] == "cloudflare_zero_trust_tunnel_cloudflared.keycloak"
            ),
        }
        self.assertEqual(
            fixture_identities,
            {entry["logical"]: entry["placeholder_value"] for entry in mappings},
        )
        ids = [
            item["change"]["after"]["id"]
            for item in fixture["resource_changes"]
            if item["address"] in DNS_STATES
        ]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(4, len(ids))
        create = next(item for item in fixture["resource_changes"] if item["address"] == CREATE)
        self.assertIsNone(create["change"]["before"])
        self.assertIs(create["change"]["before_sensitive"], False)
        self.assertEqual(5, len(fixture["checks"]))
        self.assertTrue(all(entry["status"] == "pass" for entry in fixture["checks"]))
        self.assertEqual(RELEVANT_ATTRIBUTES, fixture["relevant_attributes"])
        self.assertEqual(
            {
                "comment_modified_on",
                "created_on",
                "id",
                "meta",
                "modified_on",
                "proxiable",
                "settings",
                "tags",
                "tags_modified_on",
            },
            set(create["change"]["after_unknown"]),
        )
        self.assertTrue(all(value is True for value in create["change"]["after_unknown"].values()))
        self.assertEqual(
            "{}",
            next(
                item["change"]["before"]["metadata"]
                for item in fixture["resource_changes"]
                if item["address"] == "cloudflare_zero_trust_tunnel_cloudflared.keycloak"
            ),
        )
        config = next(item for item in fixture["resource_changes"] if item["address"] == UPDATE)
        self.assertEqual(
            {"account_id", "config", "created_at", "id", "source", "tunnel_id", "version"},
            set(config["change"]["before"]),
        )
        self.assertEqual(
            {"account_id", "config", "id", "source", "tunnel_id"},
            set(config["change"]["after"]),
        )

    def test_dns_create_requires_explicit_null_before_and_false_sensitivity(self) -> None:
        for field in ("before", "before_sensitive"):
            candidate = valid_plan()
            create = next(item for item in candidate["resource_changes"] if item["address"] == CREATE)
            create["change"].pop(field)
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, field)
        for value in ({}, None, True, 0):
            candidate = valid_plan()
            create = next(item for item in candidate["resource_changes"] if item["address"] == CREATE)
            create["change"]["before_sensitive"] = value
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, repr(value))
        candidate = valid_plan()
        create = next(item for item in candidate["resource_changes"] if item["address"] == CREATE)
        create["change"]["before"] = {}
        self.assertNotEqual(0, self.run_validator(candidate).returncode)

    def test_dns_create_unknown_projection_is_schema_bounded(self) -> None:
        expected = {
            "comment_modified_on",
            "created_on",
            "id",
            "meta",
            "modified_on",
            "proxiable",
            "settings",
            "tags",
            "tags_modified_on",
        }
        for mutation in (
            lambda unknown: unknown.update({"name": True}),
            lambda unknown: unknown.update({"id": False}),
            lambda unknown: unknown.update({"settings": {"unexpected": True}}),
            lambda unknown: unknown.pop("id"),
        ):
            candidate = valid_plan()
            create = next(item for item in candidate["resource_changes"] if item["address"] == CREATE)
            mutation(create["change"]["after_unknown"])
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode)
        candidate = valid_plan()
        create = next(item for item in candidate["resource_changes"] if item["address"] == CREATE)
        self.assertEqual(expected, set(create["change"]["after_unknown"]))
        result = self.run_validator(candidate)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_root_module_sensitive_values_are_not_an_unbounded_surface(self) -> None:
        for section, root in (
            ("planned_values", lambda candidate: candidate["planned_values"]["root_module"]),
            ("prior_state", lambda candidate: candidate["prior_state"]["values"]["root_module"]),
        ):
            candidate = valid_plan()
            root(candidate)["sensitive_values"] = {}
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, section)
            candidate = valid_plan()
            root(candidate)["sensitive_values"] = {"token": True}
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, f"{section}-token")

    def test_protected_zone_tunnel_and_noop_state_values_are_exact(self) -> None:
        cases = []
        candidate = valid_plan()
        create = next(item for item in candidate["resource_changes"] if item["address"] == CREATE)
        create["change"]["after"]["zone_id"] = "0" * 32
        cases.append(("wrong-zone", candidate))
        candidate = valid_plan()
        create = next(item for item in candidate["resource_changes"] if item["address"] == CREATE)
        create["change"]["after"]["content"] = "00000000-0000-0000-0000-000000000000.cfargotunnel.com"
        cases.append(("wrong-tunnel-target", candidate))
        candidate = valid_plan()
        update = next(item for item in candidate["resource_changes"] if item["address"] == UPDATE)
        update["change"]["before"]["account_id"] = "0" * 32
        cases.append(("wrong-tunnel-account", candidate))
        candidate = valid_plan()
        update = next(item for item in candidate["resource_changes"] if item["address"] == UPDATE)
        update["change"]["after"]["tunnel_id"] = "00000000-0000-0000-0000-000000000000"
        cases.append(("wrong-tunnel-id", candidate))
        for address, field, value in (
            ("cloudflare_dns_record.argocd_tailscale", "content", "100.122.139.33"),
            ("cloudflare_dns_record.cristexhub_dev", "name", "evil.cristex-soft.com"),
            ("cloudflare_dns_record.keycloak", "proxied", False),
            ("cloudflare_dns_record.reactive_resume_dev_tailscale", "ttl", 60),
            ("cloudflare_dns_record.keycloak", "ttl", True),
            ("cloudflare_zero_trust_tunnel_cloudflared.keycloak", "name", "evil-tunnel"),
        ):
            candidate = valid_plan()
            item = next(item for item in candidate["resource_changes"] if item["address"] == address)
            item["change"]["before"][field] = value
            cases.append((f"wrong-noop-{address}-{field}", candidate))
        for label, candidate in cases:
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, label)
        candidate = valid_plan()
        noop = next(
            item for item in candidate["resource_changes"]
            if item["address"] == "cloudflare_dns_record.cristexhub_dev"
        )
        noop["change"]["after"]["content"] = "00000000-0000-0000-0000-000000000000.cfargotunnel.com"
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "wrong-noop-after")
        candidate = valid_plan()
        create = next(item for item in candidate["resource_changes"] if item["address"] == CREATE)
        create["change"]["after"]["id"] = "c" * 32
        result = self.run_validator(candidate)
        self.assertNotEqual(0, result.returncode, "computed-create-field")

    def test_ingress_must_precede_terminal_and_preserve_existing_order(self) -> None:
        cases = []
        candidate = valid_plan()
        update = next(item for item in candidate["resource_changes"] if item["address"] == UPDATE)
        ingress = update["change"]["after"]["config"]["ingress"]
        prod = ingress.pop(2)
        ingress.append(prod)
        cases.append(("after-terminal", candidate))
        candidate = valid_plan()
        update = next(item for item in candidate["resource_changes"] if item["address"] == UPDATE)
        update["change"]["after"]["config"]["ingress"][0]["hostname"] = "evil.example"
        cases.append(("existing-order-content", candidate))
        candidate = valid_plan()
        update = next(item for item in candidate["resource_changes"] if item["address"] == UPDATE)
        update["change"]["before"]["config"]["ingress"].insert(0, {"hostname": "evil.example", "service": SERVICE})
        cases.append(("before-order-content", candidate))
        candidate = valid_plan()
        update = next(item for item in candidate["resource_changes"] if item["address"] == UPDATE)
        update["change"]["before"]["config"]["ingress"].insert(
            2, {"hostname": "hub.cristex-soft.com", "service": SERVICE}
        )
        cases.append(("preexisting-prod-ingress", candidate))
        for label, candidate in cases:
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, label)

    def test_duplicate_json_nan_and_malformed_values_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nan.json"
            identity_path = Path(temp) / "identity.json"
            identity_path.write_text(json.dumps(IDENTITY))
            identity_path.chmod(0o600)
            attestation_path = Path(temp) / "identity.attestation"
            profile_hash = hashlib.sha256(identity_path.read_bytes()).hexdigest()
            attestation_path.write_text(
                f"identity_sha256={profile_hash}\n"
                "identity_scope=cloudflare-foundation-prod-route-6-to-7\n"
            )
            attestation_path.chmod(0o600)
            validator_env = {
                **os.environ,
                "CRISTEXWEB_PROD_ROUTE_IDENTITY_SHA256": profile_hash,
                "CRISTEXWEB_PROD_ROUTE_IDENTITY_ATTESTATION": str(attestation_path),
            }
            path.write_text(json.dumps(valid_plan()).replace('"format_version": "1.2"', '"format_version": NaN'))
            path.chmod(0o600)
            result = subprocess.run(
                ["/usr/bin/python3", str(VALIDATE), str(path), str(identity_path)],
                check=False,
                capture_output=True,
                text=True,
                env=validator_env,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("plan_json_parse", result.stdout)
        for malformed in (False, 0, [], "not-a-state"):
            candidate = valid_plan()
            update = next(item for item in candidate["resource_changes"] if item["address"] == UPDATE)
            update["change"]["before"] = malformed
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, repr(malformed))
            candidate = valid_plan()
            update = next(item for item in candidate["resource_changes"] if item["address"] == UPDATE)
            update["change"]["after"] = malformed
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, repr(malformed))
        for field in ("before", "after"):
            candidate = valid_plan()
            update = next(item for item in candidate["resource_changes"] if item["address"] == UPDATE)
            update["change"][field]["account_id"] = float("nan")
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, f"nested-{field}-nan")
        overflow = json.dumps(valid_plan()).replace(
            f'"account_id": "{ACCOUNT}"', '"account_id": 1e309', 1
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "overflow.json"
            identity_path = Path(temp) / "identity.json"
            identity_path.write_text(json.dumps(IDENTITY))
            identity_path.chmod(0o600)
            attestation_path = Path(temp) / "identity.attestation"
            profile_hash = hashlib.sha256(identity_path.read_bytes()).hexdigest()
            attestation_path.write_text(
                f"identity_sha256={profile_hash}\n"
                "identity_scope=cloudflare-foundation-prod-route-6-to-7\n"
            )
            attestation_path.chmod(0o600)
            validator_env = {
                **os.environ,
                "CRISTEXWEB_PROD_ROUTE_IDENTITY_SHA256": profile_hash,
                "CRISTEXWEB_PROD_ROUTE_IDENTITY_ATTESTATION": str(attestation_path),
            }
            path.write_text(overflow)
            path.chmod(0o600)
            result = subprocess.run(
                ["/usr/bin/python3", str(VALIDATE), str(path), str(identity_path)],
                check=False,
                capture_output=True,
                text=True,
                env=validator_env,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("plan_json_parse", result.stdout)
        for timestamp in ("not-a-timestamp", "2026-99-99T00:00:00Z", "2026-01-01"):
            candidate = valid_plan()
            candidate["timestamp"] = timestamp
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, timestamp)
        for field, malformed in (
            ("before_sensitive", "false"),
            ("after_sensitive", 0),
            ("before_unknown", ""),
            ("after_unknown", 1),
        ):
            candidate = valid_plan()
            update = next(item for item in candidate["resource_changes"] if item["address"] == UPDATE)
            update["change"][field] = malformed
            result = self.run_validator(candidate)
            self.assertNotEqual(0, result.returncode, field)

    def test_source_manifest_and_self_hashes_are_exact(self) -> None:
        lines = MANIFEST.read_text().splitlines()
        self.assertEqual(12, len(lines))
        expected_paths = {
            ".terraform.lock.hcl",
            "README.md",
            "backend.tf",
            "bin/plan-foundation-prod-route",
            "bin/reconcile-foundation-state",
            "bin/validate-foundation-prod-plan",
            "bin/validate-foundation-state-scope",
            "cloudflare.tf",
            "outputs.tf",
            "providers.tf",
            "variables.tf",
            "versions.tf",
        }
        paths = set()
        for line in lines:
            digest, relative = line.split("  ", 1)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            self.assertIn(relative, expected_paths)
            path = TOFU / relative
            self.assertTrue(path.is_file(), relative)
            self.assertFalse(path.is_symlink(), relative)
            expected_mode = 0o755 if relative.startswith("bin/") else 0o644
            self.assertEqual(expected_mode, stat.S_IMODE(path.stat().st_mode), relative)
            if relative == "bin/plan-foundation-prod-route":
                text = path.read_text()
                text = re.sub(
                    r"^source_manifest_expected_sha256='[0-9a-f]{64}'$",
                    "source_manifest_expected_sha256='__SOURCE_MANIFEST_SHA256__'",
                    text,
                    flags=re.MULTILINE,
                )
                text = re.sub(
                    r"^source_prod_expected_canonical_sha256='[0-9a-f]{64}'$",
                    "source_prod_expected_canonical_sha256='__SOURCE_PROD_SHA256__'",
                    text,
                    flags=re.MULTILINE,
                )
                actual = hashlib.sha256(text.encode()).hexdigest()
            elif relative == "bin/reconcile-foundation-state":
                text = path.read_text()
                text = re.sub(
                    r"^source_manifest_expected_sha256='[0-9a-f]{64}'$",
                    "source_manifest_expected_sha256='__SOURCE_MANIFEST_SHA256__'",
                    text,
                    flags=re.MULTILINE,
                )
                text = re.sub(
                    r"^source_reconcile_expected_canonical_sha256='[0-9a-f]{64}'$",
                    "source_reconcile_expected_canonical_sha256='__SOURCE_RECONCILE_SHA256__'",
                    text,
                    flags=re.MULTILINE,
                )
                actual = hashlib.sha256(text.encode()).hexdigest()
            else:
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, actual, relative)
            paths.add(relative)
        self.assertEqual(expected_paths, paths)
        manifest_hash = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
        self.assertIn(
            f"source_prod_expected_canonical_sha256='{next(d for d, p in (line.split('  ', 1) for line in lines) if p == 'bin/plan-foundation-prod-route')}'",
            PLAN.read_text(),
        )
        self.assertIn(
            f"source_reconcile_expected_canonical_sha256='{next(d for d, p in (line.split('  ', 1) for line in lines) if p == 'bin/reconcile-foundation-state')}'",
            RECONCILE.read_text(),
        )
        for path, field in (
            (PLAN, "source_manifest_expected_sha256"),
            (RECONCILE, "source_manifest_expected_sha256"),
        ):
            self.assertIn(f"{field}='{manifest_hash}'", path.read_text())

    def test_plan_wrapper_is_clean_dash_plan_only_and_exactly_bound(self) -> None:
        source = PLAN.read_text()
        self.assertEqual(0o755, stat.S_IMODE(PLAN.stat().st_mode))
        self.assertEqual(0o755, stat.S_IMODE(VALIDATE.stat().st_mode))
        reconcile_source = RECONCILE.read_text()
        self.assertIn("PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1", reconcile_source)
        self.assertIn("PYTHONNOUSERSITE|", reconcile_source)
        for required in (
            "usage: opentofu/bin/plan-foundation-prod-route check|plan",
            'readlink -f "/proc/$$/exe")" = /usr/bin/dash',
            "Refusing traced shell execution",
            "TF_CLI_ARGS_*",
            "TF_VAR_*",
            "CLOUDFLARE_API_TOKEN",
            "/var/lib/opentofu/cristexweb/foundation.tfstate",
            "/opt/opentofu/1.12.5/tofu",
            "validate-foundation-prod-plan",
            "validate-foundation-state-scope",
            "foundation-prod-route-identities.json",
            "Cloudflare Tunnel account_tag",
            "Existing Argo DNS record ID",
            "Existing CristexHub DEV DNS record ID",
            "Existing Keycloak DNS record ID",
            "Existing Reactive Resume DEV DNS record ID",
            "protected_account_id=8b0f511214c7a4a52ddfb62ca92c5e80",
            "protected_zone_id=3cbee16e56d7656440f93e685807e779",
            "protected_tunnel_id=f9442440-96df-4cf1-855b-7257868ed9bc",
            "state list -state=\"$state_file\"",
            "expected_changes=2",
            "PLAN PROD ROUTE 6 TO 7",
            "anonymous pipe",
            "TF_CLI_CONFIG_FILE=/dev/null",
            "PYTHONNOUSERSITE=1",
            "PYTHONNOUSERSITE|",
            "TF_DATA_DIR=",
            "TF_WORKSPACE=default",
            "TOFU_DISABLE_CHECKPOINT=1",
            "-lockfile=readonly",
            "plan -input=false -lock=true",
            "state_mutation=false",
            "provider=not-contacted",
            "outputs=no-op",
            "token_output=false",
        ):
            self.assertIn(required, source, required)
        for forbidden in (
            " tofu apply",
            " tofu destroy",
            " state rm",
            " state push",
            " tofu import",
            "--auto-approve",
            "-target=",
        ):
            self.assertNotIn(forbidden, source, forbidden)
        self.assertNotIn("TF_CLI_ARGS=", source)

    def test_shell_and_python_syntax_without_provider_execution(self) -> None:
        for path in (PLAN, RECONCILE):
            result = subprocess.run(["/bin/dash", "-n", str(path)], check=False, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
        result = subprocess.run(
            ["/usr/bin/python3", "-m", "py_compile", str(VALIDATE), str(SCOPE)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_runbook_records_separate_plan_boundary(self) -> None:
        docs = RUNBOOK.read_text()
        for required in (
            "PROD plan boundary",
            "plan-foundation-prod-route check",
            "plan-foundation-prod-route plan",
            "exact six-address protected state",
            "exactly two changes",
            "hub.cristex-soft.com",
            "8b0f511214c7a4a52ddfb62ca92c5e80",
            "3cbee16e56d7656440f93e685807e779",
            "f9442440-96df-4cf1-855b-7257868ed9bc",
            "immediately before the existing terminal",
            "no replacement, destroy, deferred, unknown, or sensitive values",
            "never apply",
            "provider-backed plan",
            "state mutation",
        ):
            self.assertIn(required, docs)


if __name__ == "__main__":
    unittest.main()
