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
    "/Users/paul/Projects/cristexweb/ansible/roles/keycloak_dev_identity_transition_bootstrap/tasks/main.yml",
    "/home/paul/projects/cristexweb/ansible/roles/keycloak_dev_identity_transition_bootstrap/tasks/main.yml",
}
_EXPECTED_ARGUMENT_KEYS = {"state", "definition"}
_EXPECTED_REALM = "cristexhub-dev"
_LEGACY_REALM = "cristexhub"
_COMPONENT = "keycloak-dev-identity-transition"
_EXPECTED_DEFINITION_HASHES: dict[str, str] = {
    "KeycloakAdminTransportContract/cristexhub-dev-admin-rest-port-forward": "06bcc65419865a5254ea5f2537662bbe6246e822d7686c4ba495b617e1dcd936",
    "KeycloakIdentityActorContract/cristexhub-dev-successor-actors": "168422c3aa802b325ec01a8e56c365d9d343a22d9e100255a197e6f44343b3cc",
    "InfisicalSuccessorValueContract/cristexhub-dev-successor-identity-values": "8fec3fb602d5bfbd49b2f6741cc4e3df58ea60ec4a2f243485bb9734d8fbca8c",
    "KeycloakDevIdentityApiTransitionContract/cristexhub-dev-present-update-api-transition": "6ea2b2fda727afa71968b635e1bcb98aeac9900e324c7e897423a35fa56f41af",
}
_EXPECTED_IDENTITY_SET_SHA256 = "b18beb541a118a4cc08fec680ff2ca42b4512f413a5b3582738faea9b4af8070"
_EXPECTED_KEY_NAMES = [
    "OIDC_CLIENT_SECRET",
    "ADMIN_SERVICE_CLIENT_SECRET",
    "KEYCLOAK_DEV_BOOTSTRAP_CLIENT_SECRET",
    "KEYCLOAK_DEV_REALM_RECONCILER_CLIENT_SECRET",
]
_SENSITIVE_KEYS = {
    "secret",
    "password",
    "token",
    "accessToken",
    "refreshToken",
    "clientSecret",
    "privateKey",
}


def _canonical_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _identity(definition: dict[str, Any]) -> str:
    metadata = definition.get("metadata") or {}
    return f"{definition.get('kind', '')}/{metadata.get('name', '')}"


def _integer(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        if any(key in _SENSITIVE_KEYS for key in value):
            return True
        return any(_contains_sensitive_key(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _labels_valid(definition: dict[str, Any]) -> bool:
    labels = (definition.get("metadata") or {}).get("labels") or {}
    return (
        labels.get("cristex.io/component") == _COMPONENT
        and labels.get("cristex.io/environment") == "dev"
        and labels.get("cristex.io/managed-by") == "ansible"
        and labels.get("cristex.io/value-owner") == "infisical-cloud"
    )


def _transport_valid(spec: dict[str, Any]) -> bool:
    target = spec.get("target") or {}
    forwarding = spec.get("portForward") or {}
    tls = spec.get("futureTls") or {}
    public = spec.get("publicExposure") or {}
    return (
        spec.get("mode") == "controller-kubernetes-api-port-forward"
        and spec.get("controllerOnly") is True
        and target.get("namespace") == "shared-services"
        and target.get("deployment") == "keycloak"
        and target.get("readiness") == "exactly-one-ready-pod"
        and target.get("uidBinding") == "required-at-runtime"
        and target.get("currentHttpPort") == 8080
        and target.get("currentHttpUse") == "forbidden"
        and target.get("futureHttpsPort") == 8443
        and tls.get("listener") == "absent-blocker"
        and tls.get("serverCertificateSan") == ["IP:127.0.0.1"]
        and tls.get("validateCertificates") is True
        and tls.get("insecureSkipVerify") == "forbidden"
        and forwarding.get("implementation")
        == "blocked-pending-pinned-focused-client"
        and forwarding.get("externalKubectlBinary") == "forbidden-unpinned"
        and forwarding.get("address") == "127.0.0.1"
        and forwarding.get("localPort") == 18443
        and forwarding.get("remotePort") == 8443
        and forwarding.get("mapping") == "18443:8443"
        and forwarding.get("listenerScope") == "loopback-only"
        and (spec.get("adminRest") or {}).get("endpoint")
        == "https://127.0.0.1:18443"
        and all(public.get(key) == "forbidden" for key in (
            "publicHostname", "authHostname", "cloudflare", "ingress",
            "service", "helperPod", "nodePort", "loadBalancer"
        ))
        and spec.get("currentExecution") == "forbidden"
    )


def _identity_contract_valid(spec: dict[str, Any]) -> bool:
    bootstrap = spec.get("bootstrapActor") or {}
    reconciler = spec.get("reconcilerActor") or {}
    legacy = spec.get("legacyRealm") or {}
    fgap = reconciler.get("fineGrainedAdminPermissionsV2") or {}
    return (
        legacy.get("name") == _LEGACY_REALM
        and legacy.get("readMethods") == ["GET"]
        and legacy.get("writeMethods") == []
        and bootstrap.get("clientId") == "cristexhub-dev-bootstrap"
        and bootstrap.get("credentialPath")
        == "prod:/cristexhub/dev/identity/bootstrap"
        and bootstrap.get("requiredMasterRoles") == ["create-realm"]
        and bootstrap.get("existingBootstrapAdminReuse") == "forbidden"
        and bootstrap.get("existingBreakGlassReuse") == "forbidden"
        and bootstrap.get("maxUse") == "one-transition"
        and bootstrap.get("recurringReconciliation") == "forbidden"
        and reconciler.get("clientId") == "cristexhub-dev-reconciler"
        and reconciler.get("credentialPath")
        == "prod:/cristexhub/dev/identity/reconciler"
        and reconciler.get("realm") == _EXPECTED_REALM
        and reconciler.get("masterRealmAccess") == "forbidden"
        and reconciler.get("directRealmManagementRoles")
        == ["query-clients", "query-groups"]
        and "manage-realm" in (reconciler.get("forbiddenRealmManagementRoles") or [])
        and "manage-clients" in (reconciler.get("forbiddenRealmManagementRoles") or [])
        and (fgap.get("clientResource") or {}).get("clientId") == "cristexhub-dev"
        and (fgap.get("groupResource") or {}).get("path")
        == "/cristexhub-dev-super-admin"
        and fgap.get("selfManagement") == "forbidden"
        and reconciler.get("missingOwnedObjectBehavior") == "fail-closed-no-create"
        and "users" in (reconciler.get("forbiddenResources") or [])
        and "memberships" in (reconciler.get("forbiddenResources") or [])
        and "routes" in (reconciler.get("forbiddenResources") or [])
    )


def _infisical_contract_valid(spec: dict[str, Any]) -> bool:
    project = spec.get("project") or {}
    contracts = spec.get("contracts") or []
    cas = spec.get("cas") or {}
    admission = spec.get("kubernetesAdmission") or {}
    names = [item.get("name") for item in contracts if isinstance(item, dict)]
    paths = [item.get("path") for item in contracts if isinstance(item, dict)]
    keys = [
        key
        for item in contracts
        if isinstance(item, dict)
        for key in (item.get("exactKeys") or [])
    ]
    return (
        project.get("name") == "cristexweb-infrastructure"
        and project.get("id") == "619656da-14f3-4872-857b-be103cdc5326"
        and project.get("environment") == "prod"
        and names == ["browser", "admin-service", "bootstrap", "reconciler"]
        and paths == [
            "prod:/cristexhub/dev/identity/browser",
            "prod:/cristexhub/dev/identity/admin-service",
            "prod:/cristexhub/dev/identity/bootstrap",
            "prod:/cristexhub/dev/identity/reconciler",
        ]
        and keys == _EXPECTED_KEY_NAMES
        and (spec.get("writers") or {}).get("dedicatedSuccessorWriter") == "absent"
        and (spec.get("writers") or {}).get("broadUploaderReuse") == "forbidden"
        and (spec.get("predecessor") or {}).get("mutation") == "forbidden"
        and cas.get("apiSemantics") == "unverified-blocker"
        and cas.get("blindRetry") == "forbidden"
        and cas.get("overwriteWithoutExpectedRevision") == "forbidden"
        and (spec.get("noOutput") or {}).get("values") == "never-returned"
        and admission.get("existingDevRuntimeVapReuse") == "forbidden"
        and admission.get("existingSharedServicesVapReuse") == "forbidden"
        and admission.get("materializationCurrentPhase") == "forbidden"
    )


def _api_contract_valid(spec: dict[str, Any]) -> bool:
    legacy = spec.get("legacyProd") or {}
    bootstrap = spec.get("bootstrapPhase") or {}
    recurring = spec.get("recurringPhase") or {}
    forbidden = spec.get("forbidden") or {}
    safety = spec.get("safety") or {}
    response = spec.get("responseContract") or {}
    return (
        spec.get("apply") == "forbidden"
        and legacy.get("realm") == _LEGACY_REALM
        and legacy.get("allowedMethods") == ["GET"]
        and legacy.get("writeMethods") == []
        and legacy.get("rawResponseSha256BeforeAfter") == "required-sanitized"
        and bootstrap.get("actor") == "keycloak-dev-successor-bootstrap"
        and bootstrap.get("allowedMethods") == ["GET", "POST", "PUT"]
        and recurring.get("actor") == "keycloak-dev-reconciler"
        and recurring.get("allowedMethods") == ["GET", "PUT"]
        and recurring.get("missingOwnedObjectBehavior") == "fail-closed-no-create"
        and (spec.get("resourceIds") or {}).get("deriveFromNames") == "forbidden"
        and forbidden.get("methods") == ["DELETE", "PATCH"]
        and "users" in (forbidden.get("resources") or [])
        and "memberships" in (forbidden.get("resources") or [])
        and "dynamic-groups" in (forbidden.get("resources") or [])
        and response.get("conflictStatus") == "409-not-success"
        and response.get("timeoutOrConnectionLoss") == "unknown-stop"
        and response.get("ambiguousPostRetry") == "forbidden"
        and all(safety.get(key) is True for key in (
            "noDeletePath", "noPatchPath", "noProdWritePath", "noUserPath",
            "noMembershipPath", "noDynamicGroupPath", "noRoutePath", "noBlindRetry"
        ))
    )


class ActionModule(ActionBase):
    """Validate the next DEV transition source without API, host, or cluster access."""

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
        if _contains_sensitive_key(definition) or not _labels_valid(definition):
            return {"changed": False, "failed": True, "msg": "SOURCE_VALUE_OR_LABEL_GUARD"}
        spec = definition.get("spec") or {}
        kind = definition.get("kind")
        valid = {
            "KeycloakAdminTransportContract": _transport_valid(spec),
            "KeycloakIdentityActorContract": _identity_contract_valid(spec),
            "InfisicalSuccessorValueContract": _infisical_contract_valid(spec),
            "KeycloakDevIdentityApiTransitionContract": _api_contract_valid(spec),
        }.get(kind, False)
        if not valid:
            return {"changed": False, "failed": True, "msg": "TRANSITION_SCOPE_GUARD"}
        binding = task_vars.get(
            "keycloak_dev_identity_transition_bootstrap_internal_preflight_binding", {}
        )
        token = os.environ.get("CRISTEXWEB_KEYCLOAK_DEV_TRANSITION_TOKEN", "")
        attestation_file = os.environ.get(
            "CRISTEXWEB_KEYCLOAK_DEV_TRANSITION_ATTESTATION_FILE", ""
        )
        try:
            state = os.stat(attestation_file, follow_symlinks=False)
            value = Path(attestation_file).read_text().strip()
        except (OSError, ValueError):
            state, value = None, ""
        valid_attestation = (
            os.environ.get("CRISTEXWEB_KEYCLOAK_DEV_TRANSITION_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and bool(attestation_file)
            and os.path.isabs(attestation_file)
            and state is not None
            and stat.S_ISREG(state.st_mode)
            and not stat.S_ISLNK(state.st_mode)
            and stat.S_IMODE(state.st_mode) == 0o600
            and state.st_uid == os.getuid()
            and value == f"{token}:entrypoint"
        )
        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256")
            == hashlib.sha256(token.encode()).hexdigest()
            and _integer(binding.get("object_count")) == 4
            and binding.get("identity_set_sha256") == _EXPECTED_IDENTITY_SET_SHA256
            and binding.get("offline_source_only") is True
            and binding.get("apply_blocked") is True
            and binding.get("legacy_realm") == _LEGACY_REALM
        )
        if (
            task_vars.get("keycloak_dev_identity_transition_bootstrap_approved") is not True
            or task_vars.get("keycloak_dev_identity_transition_bootstrap_state") != "present"
            or not task_vars.get("ansible_check_mode")
            or not context.CLIARGS.get("diff")
            or not valid_attestation
            or not valid_binding
        ):
            return {"changed": False, "failed": True, "msg": "CHECK_ONLY_GUARD"}
        return {
            "changed": True,
            "failed": False,
            "msg": "DEV transition source validated offline; API and apply state were not inspected",
        }
