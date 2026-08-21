from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible.plugins.action import ActionBase

_EXPECTED_TASK_SOURCES = {
    "/Users/paul/Projects/cristexweb/ansible/roles/keycloak_dev_identity_bootstrap/tasks/main.yml",
    "/home/paul/projects/cristexweb/ansible/roles/keycloak_dev_identity_bootstrap/tasks/main.yml",
}
_EXPECTED_ARGUMENT_KEYS = {"state", "definition"}
_EXPECTED_REALM = "cristexhub-dev"
_LEGACY_REALM = "cristexhub"
_EXPECTED_CLIENTS = ["cristexhub-dev", "cristexhub-admin-svc-dev"]
_EXPECTED_GROUPS = ["cristexhub-dev-super-admin"]
_EXPECTED_MAPPERS = ["groups", "organization", "cristexhub-dev-audience"]
_FORBIDDEN_IDENTITIES = {
    "cristexhub-prod",
    "cristexhub-admin-svc-prod",
    "cristexhub-prod-super-admin",
    "argocd-admin",
    "argocd-readonly",
    "master-admin",
}
_SENSITIVE_KEYS = {
    "secret",
    "password",
    "token",
    "accessToken",
    "refreshToken",
    "clientSecret",
    "privateKey",
}

# Canonical hashes bind invocations to the four committed value-free definitions.
_EXPECTED_DEFINITION_HASHES: dict[str, str] = {
    "KeycloakRealmContract/cristexhub-dev": "72b5f5d99614983fc6f20fc5104aa8e9f2b7b69f31c7c40b4ca8208d42166d85",
    "KeycloakClientContract/cristexhub-dev-clients": "28839beb1e7cec30c182d9928b5c45f133e432b047dd59f19c6830afc742d76a",
    "KeycloakStaticGroupContract/cristexhub-dev-static-groups": "90b7252cb4a5c7a5673ad114d24304ffbaa91c7bb44f494eed2993b0475bc456",
    "KeycloakProtocolMapperContract/cristexhub-dev-claims": "a96dc0e388aed0000ecef540f0e00df97815d54b0b6466b22618418bc9d467c5",
}
_EXPECTED_IDENTITY_SET_SHA256 = "019e67b41b810f59175ebea88f0250ed1dc59d582d531c7becebd9cfadfd624f"


def _canonical_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _integer(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _identity(definition: dict[str, Any]) -> str:
    metadata = definition.get("metadata") or {}
    return f"{definition.get('kind', '')}/{metadata.get('name', '')}"


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        if any(key in _SENSITIVE_KEYS for key in value):
            return True
        return any(_contains_sensitive_key(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _forbidden_identity(value: Any) -> bool:
    identity = str(value or "")
    return (
        identity in _FORBIDDEN_IDENTITIES
        or identity.startswith("cristexhub-prod")
        or identity.startswith("cristexhub-admin-svc-prod")
        or identity.startswith("argocd")
        or identity.startswith("master")
    )


def _scope_valid(definition: dict[str, Any]) -> bool:
    kind = definition.get("kind")
    spec = definition.get("spec") or {}
    if spec.get("realm") != _EXPECTED_REALM:
        return False
    if kind == "KeycloakRealmContract":
        legacy = spec.get("legacyRealm") or {}
        mutation = spec.get("mutation") or {}
        return (
            spec.get("issuer")
            == "https://auth.cristex-soft.com/realms/cristexhub-dev"
            and spec.get("organizationsEnabled") is True
            and legacy.get("name") == _LEGACY_REALM
            and legacy.get("mutation") == "forbidden"
            and mutation.get("deletion") == "forbidden"
            and mutation.get("masterRealm") == "forbidden"
        )
    if kind == "KeycloakClientContract":
        clients = spec.get("clients") or []
        ids = [item.get("clientId") for item in clients if isinstance(item, dict)]
        if ids != _EXPECTED_CLIENTS or any(_forbidden_identity(item) for item in ids):
            return False
        browser, service = clients
        return (
            (browser.get("authorizationScopeContract") or {}).get(
                "organizationContextRequired"
            )
            is True
            and service.get("enabled") is False
            and service.get("serviceAccountsEnabled") is False
            and (service.get("authorizationContract") or {}).get("status")
            == "blocked-pending-least-privilege-role-selection"
            and all(
                (item.get("credentialContract") or {}).get("path")
                in {
                    "prod:/cristexhub/dev/identity/browser",
                    "prod:/cristexhub/dev/identity/admin-service",
                }
                and (item.get("credentialContract") or {}).get("materialization")
                == "blocked-pending-successor-value-lane"
                for item in clients
            )
        )
    if kind == "KeycloakStaticGroupContract":
        groups = spec.get("groups") or []
        names = [item.get("name") for item in groups if isinstance(item, dict)]
        return (
            names == _EXPECTED_GROUPS
            and not any(_forbidden_identity(item) for item in names)
            and (spec.get("dynamicGroupModel") or {}).get("membershipMigration")
            == "blocked"
            and (spec.get("mutation") or {}).get("deletion") == "forbidden"
        )
    if kind == "KeycloakProtocolMapperContract":
        mappers = spec.get("mappers") or []
        names = [item.get("name") for item in mappers if isinstance(item, dict)]
        organization = next(
            (item for item in mappers if item.get("name") == "organization"), {}
        )
        return (
            spec.get("clientId") == "cristexhub-dev"
            and names == _EXPECTED_MAPPERS
            and (organization.get("scopeContract") or {}).get(
                "organizationContextRequired"
            )
            is True
        )
    return False


class ActionModule(ActionBase):
    """Validate the exact DEV successor identity source without contacting Keycloak."""

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del tmp
        task_vars = task_vars or {}
        source = str(self._task.get_path()).rsplit(":", 1)[0]
        if source not in _EXPECTED_TASK_SOURCES:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD"}
        if (
            context.CLIARGS.get("start_at_task")
            or context.CLIARGS.get("step")
            or list(context.CLIARGS.get("tags") or []) not in ([], ["all"])
            or context.CLIARGS.get("skip_tags")
        ):
            return {"changed": False, "failed": True, "msg": "TASK_SELECTION_GUARD"}
        args = self._task.args
        definition = args.get("definition")
        if set(args) != _EXPECTED_ARGUMENT_KEYS or args.get("state") != "present":
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD"}
        identity = _identity(definition) if isinstance(definition, dict) else ""
        if identity not in _EXPECTED_DEFINITION_HASHES:
            return {"changed": False, "failed": True, "msg": "SOURCE_IDENTITY_GUARD"}
        if _canonical_hash(definition) != _EXPECTED_DEFINITION_HASHES[identity]:
            return {"changed": False, "failed": True, "msg": "SOURCE_HASH_GUARD"}
        if _contains_sensitive_key(definition):
            return {"changed": False, "failed": True, "msg": "SECRET_SOURCE_GUARD"}
        if not _scope_valid(definition):
            return {"changed": False, "failed": True, "msg": "DEV_SCOPE_GUARD"}
        binding = task_vars.get(
            "keycloak_dev_identity_bootstrap_internal_preflight_binding", {}
        )
        entrypoint_token = os.environ.get(
            "CRISTEXWEB_KEYCLOAK_DEV_IDENTITY_TOKEN", ""
        )
        attestation_file = os.environ.get(
            "CRISTEXWEB_KEYCLOAK_DEV_IDENTITY_ATTESTATION_FILE", ""
        )
        try:
            attestation_state = os.stat(attestation_file, follow_symlinks=False)
            attestation_value = Path(attestation_file).read_text().strip()
        except (OSError, ValueError):
            attestation_state, attestation_value = None, ""
        valid_attestation = (
            os.environ.get("CRISTEXWEB_KEYCLOAK_DEV_IDENTITY_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", entrypoint_token) is not None
            and bool(attestation_file)
            and os.path.isabs(attestation_file)
            and attestation_state is not None
            and stat.S_ISREG(attestation_state.st_mode)
            and not stat.S_ISLNK(attestation_state.st_mode)
            and stat.S_IMODE(attestation_state.st_mode) == 0o600
            and attestation_state.st_uid == os.getuid()
            and attestation_value == f"{entrypoint_token}:entrypoint"
        )
        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256")
            == hashlib.sha256(entrypoint_token.encode()).hexdigest()
            and _integer(binding.get("object_count")) == 4
            and binding.get("identity_set_sha256") == _EXPECTED_IDENTITY_SET_SHA256
            and binding.get("no_delete_path") is True
            and binding.get("offline_source_only") is True
            and binding.get("runtime_api_access") is False
            and binding.get("legacy_realm") == _LEGACY_REALM
        )
        if (
            task_vars.get("keycloak_dev_identity_bootstrap_approved") is not True
            or task_vars.get("keycloak_dev_identity_bootstrap_state") != "present"
            or not task_vars.get("ansible_check_mode")
            or not context.CLIARGS.get("diff")
            or not valid_attestation
            or not valid_binding
        ):
            return {"changed": False, "failed": True, "msg": "CHECK_ONLY_GUARD"}
        return {
            "changed": True,
            "failed": False,
            "msg": "DEV identity source validated offline; runtime state was not inspected",
        }
