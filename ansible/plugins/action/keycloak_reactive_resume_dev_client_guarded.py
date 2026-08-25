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

EXPECTED_TASK_SUFFIX = "/ansible/roles/keycloak_reactive_resume_dev_client_bootstrap/tasks/main.yml"
EXPECTED_ARGUMENT_KEYS = {"state", "definition"}
EXPECTED_IDENTITY = "KeycloakClientContract/reactive-resume-dev-shared-client"
EXPECTED_REALM = "cristexhub"
EXPECTED_CLIENT = "reactive-resume-dev"
EXPECTED_CALLBACK = "https://resume-dev.cristex-soft.com/api/auth/oauth2/callback/custom"
EXPECTED_ORIGIN = "https://resume-dev.cristex-soft.com"
EXPECTED_LOGOUT = "https://resume-dev.cristex-soft.com/"
EXPECTED_OLD_REALM = "cristexhub-dev"
SENSITIVE_KEYS = {"secret", "password", "token", "clientSecret", "privateKey"}
FORBIDDEN_NAMES = {"cristexhub-prod", "cristexhub-admin-svc-prod", "master-admin", "argocd-admin"}
EXPECTED_DEFINITION_SHA256 = "55f1f54d4ab9f0ec1e547da7f6d692e5d51840ad5cf4f01ecf8b7de5c0af97fd"
EXPECTED_IDENTITY_SET_SHA256 = "bbdf59674c3383c00ad8648c8707a17bba16f693c3377148f09898f521075cf5"


def canonical(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sensitive(value: Any) -> bool:
    if isinstance(value, dict):
        return any(k in SENSITIVE_KEYS for k in value) or any(sensitive(v) for v in value.values())
    if isinstance(value, list):
        return any(sensitive(v) for v in value)
    return False


class ActionModule(ActionBase):
    """Validate the exact shared-realm RR client source without Keycloak/API access."""

    def run(self, tmp: str | None = None, task_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        del tmp
        task_vars = task_vars or {}
        source = str(self._task.get_path()).rsplit(":", 1)[0]
        root = str(Path(os.environ.get("CRISTEXWEB_REPOSITORY_ROOT", "")).resolve())
        if source != root + EXPECTED_TASK_SUFFIX:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD"}
        if (context.CLIARGS.get("start_at_task") or context.CLIARGS.get("step")
                or list(context.CLIARGS.get("tags") or []) not in ([], ["all"])
                or context.CLIARGS.get("skip_tags")):
            return {"changed": False, "failed": True, "msg": "TASK_SELECTION_GUARD"}
        args = self._task.args
        definition = args.get("definition")
        if set(args) != EXPECTED_ARGUMENT_KEYS or args.get("state") != "present":
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD"}
        if not isinstance(definition, dict) or f"{definition.get('kind')}/{(definition.get('metadata') or {}).get('name')}" != EXPECTED_IDENTITY:
            return {"changed": False, "failed": True, "msg": "SOURCE_IDENTITY_GUARD"}
        if canonical(definition) != EXPECTED_DEFINITION_SHA256 or sensitive(definition):
            return {"changed": False, "failed": True, "msg": "SOURCE_HASH_OR_SECRET_GUARD"}
        spec = definition.get("spec") or {}
        clients = spec.get("clients") or []
        if spec.get("realm") != EXPECTED_REALM or len(clients) != 1:
            return {"changed": False, "failed": True, "msg": "REALM_SCOPE_GUARD"}
        client = clients[0]
        attrs = client.get("attributes") or {}
        credential = client.get("credentialContract") or {}
        rollback = (spec.get("rollback") or {}).get("oldClient") or {}
        exact = (
            client.get("clientId") == EXPECTED_CLIENT and client.get("enabled") is True
            and client.get("publicClient") is False and client.get("bearerOnly") is False
            and client.get("standardFlowEnabled") is True and client.get("implicitFlowEnabled") is False
            and client.get("directAccessGrantsEnabled") is False and client.get("serviceAccountsEnabled") is False
            and client.get("redirectUris") == [EXPECTED_CALLBACK] and client.get("webOrigins") == [EXPECTED_ORIGIN]
            and attrs == {"pkce.code.challenge.method": "S256", "post.logout.redirect.uris": EXPECTED_LOGOUT}
            and credential == {"owner": "infisical-cloud", "path": "prod:/reactive-resume/dev/runtime", "key": "OAUTH_CLIENT_SECRET", "materialization": "materialized-private-runtime"}
            and spec.get("additive") is True and spec.get("preserve_existing_clients") is True
            and spec.get("preserve_existing_users") is True and spec.get("client_deletion") == "forbidden"
            and rollback == {"clientId": EXPECTED_CLIENT, "realm": EXPECTED_OLD_REALM, "status": "disabled-rollback-only", "deletion": "forbidden", "enable_requires": "separate-reviewed-rollback", "issuer": "https://auth.cristex-soft.com/realms/cristexhub-dev", "discovery": "https://auth.cristex-soft.com/realms/cristexhub-dev/.well-known/openid-configuration"}
            and not any(str(v) in FORBIDDEN_NAMES for v in (client.get("clientId"), rollback.get("clientId")))
        )
        if not exact:
            return {"changed": False, "failed": True, "msg": "CLIENT_CONTRACT_GUARD"}
        binding = task_vars.get("keycloak_reactive_resume_dev_client_bootstrap_internal_preflight_binding", {})
        token = os.environ.get("CRISTEXWEB_KEYCLOAK_REACTIVE_RESUME_DEV_CLIENT_TOKEN", "")
        attestation_file = os.environ.get("CRISTEXWEB_KEYCLOAK_REACTIVE_RESUME_DEV_CLIENT_ATTESTATION_FILE", "")
        try:
            st = os.stat(attestation_file, follow_symlinks=False)
            value = Path(attestation_file).read_text().strip()
        except (OSError, ValueError):
            st, value = None, ""
        attested = (os.environ.get("CRISTEXWEB_KEYCLOAK_REACTIVE_RESUME_DEV_CLIENT_ENTRYPOINT") == "v1"
                    and re.fullmatch(r"[0-9a-f]{64}", token) is not None and st is not None
                    and stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode)
                    and stat.S_IMODE(st.st_mode) == 0o600 and st.st_uid == os.getuid()
                    and value == f"{token}:entrypoint")
        bound = (binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
                 and binding.get("object_count") == 1 and binding.get("identity_set_sha256") == EXPECTED_IDENTITY_SET_SHA256
                 and binding.get("no_delete_path") is True and binding.get("offline_source_only") is True
                 and binding.get("runtime_api_access") is False and binding.get("preserve_existing_clients") is True
                 and binding.get("preserve_existing_users") is True)
        if (task_vars.get("keycloak_reactive_resume_dev_client_bootstrap_approved") is not True
                or task_vars.get("keycloak_reactive_resume_dev_client_bootstrap_state") != "present"
                or not task_vars.get("ansible_check_mode") or not context.CLIARGS.get("diff") or not attested or not bound):
            return {"changed": False, "failed": True, "msg": "CHECK_ONLY_GUARD"}
        return {"changed": True, "failed": False, "msg": "shared cristexhub Reactive Resume client source validated offline; runtime state was not inspected"}
