from __future__ import annotations

import hashlib
import json
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
    "KeycloakRealmContract/cristexhub-dev": "403c53be6dffcebc882d645be1564c0e3514ee78fd4bf6ff156aa3b0f5c4bda4",
    "KeycloakClientContract/cristexhub-dev-clients": "3166a87c9d10f74ec29858833b213c8f2dacfb6c688ef3b4b73cf29e6bf6f69f",
    "KeycloakStaticGroupContract/cristexhub-dev-static-groups": "bdddde4f93723c6f87edfdf3ac76bf14f9408d63062e0d11dc65af645d002722",
    "KeycloakProtocolMapperContract/cristexhub-dev-claims": "5d42db820b4975eb1b228a2d49eb64452639de273ac902a4b9f13df913ef422c",
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
        return all(
            (item.get("credentialContract") or {}).get("path")
            == "prod:/cristexhub/dev/identity"
            and (item.get("credentialContract") or {}).get("materialization")
            == "blocked-pending-successor-value-lane"
            for item in clients
        )
    if kind == "KeycloakStaticGroupContract":
        groups = spec.get("groups") or []
        names = [item.get("name") for item in groups if isinstance(item, dict)]
        return (
            names == _EXPECTED_GROUPS
            and not any(_forbidden_identity(item) for item in names)
            and (spec.get("mutation") or {}).get("deletion") == "forbidden"
        )
    if kind == "KeycloakProtocolMapperContract":
        mappers = spec.get("mappers") or []
        names = [item.get("name") for item in mappers if isinstance(item, dict)]
        return spec.get("clientId") == "cristexhub-dev" and names == _EXPECTED_MAPPERS
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
        valid_binding = (
            isinstance(binding, dict)
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
            or not valid_binding
        ):
            return {"changed": False, "failed": True, "msg": "CHECK_ONLY_GUARD"}
        return {
            "changed": True,
            "failed": False,
            "msg": "DEV identity source validated offline; runtime state was not inspected",
        }
