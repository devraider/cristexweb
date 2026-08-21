from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any
from urllib.parse import quote

from ansible import context
from ansible.plugins.action import ActionBase

_EXPECTED_TASK_SOURCES = {
    "/Users/paul/Projects/cristexweb/ansible/roles/keycloak_dev_identity_bootstrap/tasks/main.yml",
    "/home/paul/projects/cristexweb/ansible/roles/keycloak_dev_identity_bootstrap/tasks/main.yml",
}
_EXPECTED_ARGUMENT_KEYS = {"state", "definition", "api_base_url", "token_file", "timeout"}
_EXPECTED_API_BASE_URL = "https://auth.cristex-soft.com"
_EXPECTED_REALM = "cristexhub-dev"
_LEGACY_REALM = "cristexhub"
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

# These hashes bind the action invocation to the four committed, value-free leaves.
# The role separately verifies the file hashes and mode before invoking this action.
_EXPECTED_DEFINITION_HASHES: dict[str, str] = {
    "KeycloakRealmContract/cristexhub-dev": "403c53be6dffcebc882d645be1564c0e3514ee78fd4bf6ff156aa3b0f5c4bda4",
    "KeycloakClientContract/cristexhub-dev-clients": "09da4599a04214e537ed2c8682fa8c49846892f82c66c35b7660f6f228fe01f2",
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


def _forbidden_identity(value: Any) -> bool:
    identity = str(value or "")
    return (
        identity in _FORBIDDEN_IDENTITIES
        or identity.startswith("cristexhub-prod")
        or identity.startswith("cristexhub-admin-svc-prod")
        or identity.startswith("argocd")
        or identity.startswith("master")
    )


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        if any(key in _SENSITIVE_KEYS for key in value):
            return True
        return any(_contains_sensitive_key(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _subset_matches(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and _subset_matches(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return actual == expected
    return actual == expected


class ActionModule(ActionBase):
    """Read-only, exact-scope DEV realm identity preflight."""

    def _safe_uri(
        self,
        url: str,
        token: str,
        task_vars: dict[str, Any],
        tmp: str | None,
        timeout: int,
    ) -> tuple[int, Any, str | None]:
        result = self._execute_module(
            module_name="ansible.builtin.uri",
            module_args={
                "url": url,
                "method": "GET",
                "headers": {"Authorization": f"Bearer {token}", "Accept": "application/json"},
                "return_content": True,
                "status_code": [200, 404],
                "timeout": timeout,
                "validate_certs": True,
                "follow_redirects": "none",
            },
            task_vars=task_vars,
            tmp=tmp,
        )
        content = result.pop("content", "")
        # Never return module invocation data: it contains the bearer header.
        result.pop("invocation", None)
        status = _integer(result.pop("status", 0), 0)
        if result.get("failed"):
            return status, None, "Keycloak read-only API request failed"
        try:
            payload = json.loads(content) if content else None
        except (TypeError, ValueError):
            return status, None, "Keycloak read-only API returned non-JSON content"
        return status, payload, None

    def _legacy_guard(
        self,
        base_url: str,
        token: str,
        task_vars: dict[str, Any],
        tmp: str | None,
        timeout: int,
    ) -> tuple[bool, str | None]:
        status, payload, error = self._safe_uri(
            f"{base_url}/admin/realms/{_LEGACY_REALM}", token, task_vars, tmp, timeout
        )
        if error or status != 200 or not isinstance(payload, dict):
            return False, "Refusing DEV identity preflight without the retained legacy realm"
        if payload.get("realm") != _LEGACY_REALM:
            return False, "Refusing DEV identity preflight after legacy realm identity drift"
        return True, None

    def _target_inventory(
        self,
        base_url: str,
        token: str,
        task_vars: dict[str, Any],
        tmp: str | None,
        timeout: int,
    ) -> tuple[int, dict[str, Any] | None, str | None]:
        status, realm, error = self._safe_uri(
            f"{base_url}/admin/realms/{_EXPECTED_REALM}", token, task_vars, tmp, timeout
        )
        if error:
            return status, None, error
        if status == 404:
            return status, None, None
        if not isinstance(realm, dict) or realm.get("realm") != _EXPECTED_REALM:
            return status, None, "Refusing a DEV identity response for another realm"
        clients_status, clients, clients_error = self._safe_uri(
            f"{base_url}/admin/realms/{_EXPECTED_REALM}/clients",
            token,
            task_vars,
            tmp,
            timeout,
        )
        if clients_error or clients_status != 200 or not isinstance(clients, list):
            return clients_status, None, "Refusing DEV identity preflight without client inventory"
        groups_status, groups, groups_error = self._safe_uri(
            f"{base_url}/admin/realms/{_EXPECTED_REALM}/groups",
            token,
            task_vars,
            tmp,
            timeout,
        )
        if groups_error or groups_status != 200 or not isinstance(groups, list):
            return groups_status, None, "Refusing DEV identity preflight without group inventory"
        client_ids = [
            str(item.get("clientId"))
            for item in clients
            if isinstance(item, dict) and item.get("clientId")
        ]
        group_names = [
            str(item.get("name"))
            for item in groups
            if isinstance(item, dict) and item.get("name")
        ]
        forbidden_clients = {
            identity for identity in client_ids if _forbidden_identity(identity)
        }
        forbidden_groups = {
            identity for identity in group_names if _forbidden_identity(identity)
        }
        if (
            forbidden_clients
            or forbidden_groups
            or len(client_ids) != len(set(client_ids))
            or len(group_names) != len(set(group_names))
        ):
            return status, None, "Refusing cross-environment, duplicate, or privileged DEV identity"
        return status, {"realm": realm, "clients": clients, "groups": groups}, None

    def _compare_definition(
        self,
        definition: dict[str, Any],
        inventory: dict[str, Any] | None,
        base_url: str,
        token: str,
        task_vars: dict[str, Any],
        tmp: str | None,
        timeout: int,
    ) -> tuple[bool, str | None]:
        if inventory is None:
            return True, None
        kind = definition.get("kind")
        spec = definition.get("spec") or {}
        if kind == "KeycloakRealmContract":
            desired = {
                key: value
                for key, value in spec.items()
                if key
                not in {
                    "issuer",
                    "legacyRealm",
                    "mutation",
                }
            }
            return not _subset_matches(inventory["realm"], desired), None
        if kind == "KeycloakClientContract":
            current_by_id = {
                str(item.get("clientId")): item
                for item in inventory["clients"]
                if isinstance(item, dict) and item.get("clientId")
            }
            for desired_client in spec.get("clients", []):
                client_id = str(desired_client.get("clientId", ""))
                current = current_by_id.get(client_id)
                if current is None:
                    return True, None
                desired = {
                    key: value
                    for key, value in desired_client.items()
                    if key != "credentialContract"
                }
                if not _subset_matches(current, desired):
                    return True, None
            return False, None
        if kind == "KeycloakStaticGroupContract":
            current_by_name = {
                str(item.get("name")): item
                for item in inventory["groups"]
                if isinstance(item, dict) and item.get("name")
            }
            for desired_group in spec.get("groups", []):
                name = str(desired_group.get("name", ""))
                current = current_by_name.get(name)
                if current is None:
                    return True, None
                if not _subset_matches(
                    current,
                    {key: desired_group[key] for key in ("name", "path") if key in desired_group},
                ):
                    return True, None
            return False, None
        if kind == "KeycloakProtocolMapperContract":
            client_id = str(spec.get("clientId", ""))
            client = next(
                (
                    item
                    for item in inventory["clients"]
                    if isinstance(item, dict) and item.get("clientId") == client_id
                ),
                None,
            )
            if not client or not client.get("id"):
                return True, None
            status, mappers, error = self._safe_uri(
                f"{base_url}/admin/realms/{_EXPECTED_REALM}/clients/"
                f"{quote(str(client['id']), safe='')}/protocol-mappers/models",
                token,
                task_vars,
                tmp,
                timeout,
            )
            if error or status != 200 or not isinstance(mappers, list):
                return False, "Refusing DEV identity preflight without protocol-mapper inventory"
            current_by_name = {
                str(item.get("name")): item
                for item in mappers
                if isinstance(item, dict) and item.get("name")
            }
            for desired_mapper in spec.get("mappers", []):
                name = str(desired_mapper.get("name", ""))
                current = current_by_name.get(name)
                if current is None:
                    return True, None
                desired = {
                    key: value
                    for key, value in desired_mapper.items()
                    if key != "credentialContract"
                }
                if not _subset_matches(current, desired):
                    return True, None
            return False, None
        return False, "Refusing an unknown DEV identity contract kind"

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
        if args.get("api_base_url") != _EXPECTED_API_BASE_URL or args.get("timeout") != 15:
            return {"changed": False, "failed": True, "msg": "API_ENDPOINT_GUARD"}
        if not isinstance(definition, dict) or _identity(definition) not in _EXPECTED_DEFINITION_HASHES:
            return {"changed": False, "failed": True, "msg": "SOURCE_IDENTITY_GUARD"}
        if _canonical_hash(definition) != _EXPECTED_DEFINITION_HASHES[_identity(definition)]:
            return {"changed": False, "failed": True, "msg": "SOURCE_HASH_GUARD"}
        if _contains_sensitive_key(definition):
            return {"changed": False, "failed": True, "msg": "SECRET_SOURCE_GUARD"}
        binding = task_vars.get("keycloak_dev_identity_bootstrap_internal_preflight_binding", {})
        token = os.environ.get("CRISTEXWEB_KEYCLOAK_DEV_IDENTITY_TOKEN", "")
        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and _integer(binding.get("object_count")) == 4
            and binding.get("identity_set_sha256") == _EXPECTED_IDENTITY_SET_SHA256
            and binding.get("no_delete_path") is True
            and binding.get("check_only") is True
            and binding.get("legacy_realm") == _LEGACY_REALM
        )
        if (
            task_vars.get("keycloak_dev_identity_bootstrap_approved") is not True
            or task_vars.get("keycloak_dev_identity_bootstrap_state") != "present"
            or not task_vars.get("ansible_check_mode")
            or not valid_binding
        ):
            return {"changed": False, "failed": True, "msg": "CHECK_ONLY_GUARD"}
        token_file = str(args.get("token_file", ""))
        try:
            token_state = os.stat(token_file, follow_symlinks=False)
            admin_token = Path(token_file).read_text().strip()
        except (OSError, ValueError):
            token_state, admin_token = None, ""
        if (
            not os.path.isabs(token_file)
            or token_state is None
            or not stat.S_ISREG(token_state.st_mode)
            or stat.S_ISLNK(token_state.st_mode)
            or stat.S_IMODE(token_state.st_mode) != 0o600
            or token_state.st_uid != os.getuid()
            or not admin_token
        ):
            return {"changed": False, "failed": True, "msg": "SECRET_FILE_GUARD"}
        ok, error = self._legacy_guard(args["api_base_url"], admin_token, task_vars, tmp, 15)
        if not ok:
            return {"changed": False, "failed": True, "msg": error or "LEGACY_REALM_GUARD"}
        _, inventory, error = self._target_inventory(
            args["api_base_url"], admin_token, task_vars, tmp, 15
        )
        if error:
            return {"changed": False, "failed": True, "msg": error}
        changed, error = self._compare_definition(
            definition,
            inventory,
            args["api_base_url"],
            admin_token,
            task_vars,
            tmp,
            15,
        )
        if error:
            return {"changed": False, "failed": True, "msg": error}
        return {"changed": changed, "failed": False, "msg": "DEV identity state inspected read-only"}
