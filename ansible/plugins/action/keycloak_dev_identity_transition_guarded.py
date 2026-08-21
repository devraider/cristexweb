from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any

from ansible import context
from ansible.plugins.action import ActionBase

_EXPECTED_WRAPPER_PATHS = {
    "/Users/paul/Projects/cristexweb/ansible/bin/bootstrap-keycloak-dev-identity-transition",
    "/home/paul/projects/cristexweb/ansible/bin/bootstrap-keycloak-dev-identity-transition",
}
_EXPECTED_WRAPPER_SHA256 = "e9bef7f4297437d057c35e907806c3327893bdaca70e72fd7715abe4ba20c4cd"
_EXPECTED_TASK_SOURCES = {
    "/Users/paul/Projects/cristexweb/ansible/roles/keycloak_dev_identity_transition_bootstrap/tasks/main.yml",
    "/home/paul/projects/cristexweb/ansible/roles/keycloak_dev_identity_transition_bootstrap/tasks/main.yml",
}
_EXPECTED_ARGUMENT_KEYS = {"state", "definition"}
_EXPECTED_REALM = "cristexhub-dev"
_LEGACY_REALM = "cristexhub"
_COMPONENT = "keycloak-dev-identity-transition"
_EXPECTED_DEFINITION_HASHES: dict[str, str] = {
    "KeycloakAdminTransportContract/cristexhub-dev-admin-rest-port-forward": "4c81e84442bfb5046c19f9cb5a7126747ddaf273923457ba44d91d4e74eb36b9",
    "KeycloakIdentityActorContract/cristexhub-dev-successor-actors": "d90895459aa4f244d1b0408e7ed97ccfea88a9184bb64ffab666c4ca86a6995d",
    "InfisicalSuccessorValueContract/cristexhub-dev-successor-identity-values": "0b73d72d0c4f1fb42064da6f47954bbf059a26648adf8ccea600662a32571b9e",
    "KeycloakDevIdentityApiTransitionContract/cristexhub-dev-present-update-api-transition": "ba4f5e4383a1f309f6101e68b28a00ff9de85bf39210891894170344b3e5d346",
}
_EXPECTED_IDENTITY_SET_SHA256 = "b18beb541a118a4cc08fec680ff2ca42b4512f413a5b3582738faea9b4af8070"
_EXPECTED_KEY_NAMES = [
    "OIDC_CLIENT_SECRET",
    "ADMIN_SERVICE_CLIENT_SECRET",
    "KEYCLOAK_DEV_BOOTSTRAP_CLIENT_SECRET",
    "KEYCLOAK_DEV_REALM_AUDITOR_CLIENT_SECRET",
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


def _parent_pid(pid: int) -> int:
    proc_stat = Path(f"/proc/{pid}/stat")
    if proc_stat.is_file():
        tail = proc_stat.read_text().rsplit(") ", 1)[1].split()
        return int(tail[1])
    result = subprocess.run(
        ["/bin/ps", "-o", "ppid=", "-p", str(pid)],
        check=False,
        capture_output=True,
        text=True,
        timeout=2,
    )
    return int(result.stdout.strip()) if result.returncode == 0 else 0


def _wrapper_process_valid() -> bool:
    pid_text = os.environ.get("CRISTEXWEB_KEYCLOAK_DEV_TRANSITION_WRAPPER_PID", "")
    if not re.fullmatch(r"[1-9][0-9]*", pid_text):
        return False
    wrapper_pid = int(pid_text)
    current = os.getpid()
    ancestors: set[int] = set()
    try:
        while current > 1 and current not in ancestors:
            ancestors.add(current)
            current = _parent_pid(current)
        if wrapper_pid not in ancestors:
            return False
        cmdline_path = Path(f"/proc/{wrapper_pid}/cmdline")
        if cmdline_path.is_file():
            argv = [
                item.decode("utf-8", "strict")
                for item in cmdline_path.read_bytes().split(b"\0")
                if item
            ]
        else:
            result = subprocess.run(
                ["/bin/ps", "-o", "command=", "-p", str(wrapper_pid)],
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
            )
            argv = result.stdout.strip().split() if result.returncode == 0 else []
        wrapper_arg_present = any(
            item in _EXPECTED_WRAPPER_PATHS
            or item == "ansible/bin/bootstrap-keycloak-dev-identity-transition"
            for item in argv
        )
        wrapper = next(
            (
                Path(item)
                for item in _EXPECTED_WRAPPER_PATHS
                if Path(item).is_file()
                and hashlib.sha256(Path(item).read_bytes()).hexdigest()
                == _EXPECTED_WRAPPER_SHA256
            ),
            None,
        )
        if not wrapper_arg_present or wrapper is None or not argv or argv[-1] != "check":
            return False
        wrapper_stat = wrapper.lstat()
        return (
            stat.S_ISREG(wrapper_stat.st_mode)
            and not wrapper.is_symlink()
            and stat.S_IMODE(wrapper_stat.st_mode) == 0o755
            and wrapper_stat.st_uid == os.getuid()
        )
    except (OSError, ValueError, IndexError, subprocess.SubprocessError, UnicodeError):
        return False


def _transport_valid(spec: dict[str, Any]) -> bool:
    target = spec.get("target") or {}
    forwarding = spec.get("portForward") or {}
    tls = spec.get("futureTls") or {}
    public = spec.get("publicExposure") or {}
    return (
        spec.get("status") == "source-only-check-only"
        and spec.get("activation")
        == "blocked-current-keycloak-has-no-https-admin-listener"
        and spec.get("mode") == "controller-kubernetes-api-port-forward"
        and spec.get("controllerOnly") is True
        and target.get("namespace") == "shared-services"
        and target.get("deployment") == "keycloak"
        and target.get("selector")
        == {
            "app.kubernetes.io/name": "keycloak",
            "app.kubernetes.io/part-of": "cristex-platform",
        }
        and target.get("readiness") == "exactly-one-ready-pod"
        and target.get("uidBinding") == "required-at-runtime"
        and target.get("currentHttpPort") == 8080
        and target.get("currentHttpUse") == "forbidden"
        and target.get("futureHttpsPort") == 8443
        and tls.get("listener") == "absent-blocker"
        and tls.get("privateCa") == "required"
        and tls.get("serverCertificateSan") == ["IP:127.0.0.1"]
        and tls.get("leafKeyCorrespondence") == "required"
        and tls.get("certificateSource") == "absent-blocker"
        and tls.get("caCertificateSha256") == "absent-blocker"
        and tls.get("leafCertificateSha256") == "absent-blocker"
        and tls.get("exactCaVerification") == "required"
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
        and forwarding.get("persistentKubernetesObjects") == "forbidden"
        and (forwarding.get("cleanup") or {}).get("alwaysCloseStream") == "required"
        and (forwarding.get("cleanup") or {}).get("verifyListenerGone") == "required"
        and (forwarding.get("cleanup") or {}).get("ambiguousCleanup") == "unknown-stop"
        and (spec.get("adminRest") or {}).get("endpoint")
        == "https://127.0.0.1:18443"
        and (spec.get("adminRest") or {}).get("basePath") == "/admin"
        and (spec.get("adminRest") or {}).get("bootstrapTokenPath")
        == "/realms/master/protocol/openid-connect/token"
        and (spec.get("adminRest") or {}).get("auditorTokenPath")
        == "forbidden-disabled-actor"
        and (spec.get("adminRest") or {}).get("followRedirects") is False
        and all(public.get(key) == "forbidden" for key in (
            "publicHostname", "authHostname", "cloudflare", "ingress",
            "service", "helperPod", "nodePort", "loadBalancer"
        ))
        and spec.get("currentExecution") == "forbidden"
    )


def _identity_contract_valid(spec: dict[str, Any]) -> bool:
    bootstrap = spec.get("bootstrapActor") or {}
    auditor = spec.get("recurringAuditor") or {}
    legacy = spec.get("legacyRealm") or {}
    fgap = auditor.get("fineGrainedAdminPermissionsV2") or {}
    custodian = spec.get("retirementCustodian") or {}
    prod_auditor = spec.get("prodCompatibilityAuditor") or {}
    return (
        spec.get("status") == "source-only-check-only"
        and spec.get("activation")
        == "blocked-pending-bootstrap-custodian-and-no-viable-least-privilege-recurring-admin-auditor"
        and legacy.get("name") == _LEGACY_REALM
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
        and bootstrap.get("allowedOperations") == [
            "POST /admin/realms target=cristexhub-dev",
            "GET /admin/realms/cristexhub-dev after-create-or-409-only",
            "initialize-exact-dev-clients-group-mappers-and-disabled-auditor",
        ]
        and custodian.get("name") == "keycloak-dev-bootstrap-retirement-custodian"
        and custodian.get("status") == "absent-blocker"
        and custodian.get("clientId") == "unselected-blocker"
        and custodian.get("realm") == "master"
        and custodian.get("credentialPath") == "unselected-blocker"
        and custodian.get("credentialKey") == "unselected-blocker"
        and custodian.get("requiredRoleSet") == "unselected-blocker"
        and custodian.get("distinctFromBootstrapActor") is True
        and custodian.get("recurringUse") == "forbidden"
        and custodian.get("allowedOperations") == [
            "disable-exact-bootstrap-service-account",
            "revoke-exact-create-realm-role-mapping",
            "remove-exact-automatic-target-realm-role-mappings",
        ]
        and custodian.get("forbiddenOperations") == [
            "successor-object-reconciliation", "users", "memberships", "prod-writes"
        ]
        and prod_auditor.get("name") == "keycloak-prod-compatibility-auditor"
        and prod_auditor.get("status") == "absent-blocker"
        and prod_auditor.get("clientId") == "unselected-blocker"
        and prod_auditor.get("realm") == _LEGACY_REALM
        and prod_auditor.get("credentialPath") == "unselected-blocker"
        and prod_auditor.get("credentialKey") == "unselected-blocker"
        and prod_auditor.get("allowedMethods") == ["GET"]
        and prod_auditor.get("allowedPaths") == [
            "/admin/realms/cristexhub",
            "/admin/realms/cristexhub/clients?clientId=cristexhub-prod",
            "/admin/realms/cristexhub/groups?search=cristexhub-prod-super-admin",
        ]
        and prod_auditor.get("writeMethods") == []
        and (bootstrap.get("automaticCreatorGrantLedger") or {}).get("captureBeforeCreate")
        == "required"
        and (bootstrap.get("automaticCreatorGrantLedger") or {}).get("captureAfterCreate")
        == "required"
        and (bootstrap.get("automaticCreatorGrantLedger") or {}).get("allRealmRolesExpected") is True
        and (bootstrap.get("automaticCreatorGrantLedger") or {}).get(
            "roleRemovalBeforeRecurringAudit"
        )
        == "required"
        and auditor.get("clientId") == "cristexhub-dev-auditor"
        and auditor.get("credentialPath")
        == "prod:/cristexhub/dev/identity/auditor"
        and auditor.get("realm") == _EXPECTED_REALM
        and auditor.get("masterRealmAccess") == "forbidden"
        and auditor.get("enabled") is False
        and auditor.get("credentialMaterialization") == "forbidden-while-disabled"
        and auditor.get("recurringUse")
        == "blocked-no-viable-least-privilege-admin-rest-role"
        and auditor.get("directRealmManagementRoles") == []
        and "manage-realm" in (auditor.get("forbiddenRealmManagementRoles") or [])
        and "manage-clients" in (auditor.get("forbiddenRealmManagementRoles") or [])
        and (auditor.get("rejectedDirectRoleBindings") or {}).get("query-clients")
        == "forbidden-can-enumerate-all-confidential-client-secrets"
        and (auditor.get("rejectedDirectRoleBindings") or {}).get("query-groups")
        == "forbidden-enumerates-all-group-metadata"
        and fgap.get("recurringActorPolicies") == "none"
        and fgap.get("clientView")
        == "forbidden-exposes-confidential-client-secret"
        and fgap.get("groupView") == "forbidden-exposes-group-role-mapping-and-detail-data"
        and fgap.get("manage") == "forbidden"
        and fgap.get("selfManagement") == "forbidden"
        and auditor.get("missingOwnedObjectBehavior") == "fail-closed-no-create"
        and auditor.get("allowedResources") == []
        and "all-client-collections" in (auditor.get("forbiddenResources") or [])
        and "all-group-collections" in (auditor.get("forbiddenResources") or [])
        and "users" in (auditor.get("forbiddenResources") or [])
        and "memberships" in (auditor.get("forbiddenResources") or [])
        and "client-resource-detail" in (auditor.get("forbiddenResources") or [])
        and "group-resource-detail" in (auditor.get("forbiddenResources") or [])
        and "client-protocol-mapper-inventory"
        in (auditor.get("forbiddenResources") or [])
        and "protocol-mapper-writes" in (auditor.get("forbiddenResources") or [])
        and "routes" in (auditor.get("forbiddenResources") or [])
        and spec.get("currentExecution") == "forbidden"
    )


def _infisical_contract_valid(spec: dict[str, Any]) -> bool:
    project = spec.get("project") or {}
    contracts = spec.get("contracts") or []
    cas = spec.get("cas") or {}
    admission = spec.get("kubernetesAdmission") or {}
    predecessor = spec.get("predecessor") or {}
    writers = spec.get("writers") or {}
    absence = spec.get("bootstrapAbsencePreflight") or {}
    no_output = spec.get("noOutput") or {}
    names = [item.get("name") for item in contracts if isinstance(item, dict)]
    paths = [item.get("path") for item in contracts if isinstance(item, dict)]
    keys = [
        key
        for item in contracts
        if isinstance(item, dict)
        for key in (item.get("exactKeys") or [])
    ]
    return (
        spec.get("status") == "source-only-check-only"
        and spec.get("activation") == "blocked-no-writer-no-target-no-verified-cas"
        and project.get("name") == "cristexweb-infrastructure"
        and project.get("id") == "619656da-14f3-4872-857b-be103cdc5326"
        and project.get("environment") == "prod"
        and names == ["browser", "admin-service", "bootstrap", "auditor"]
        and paths == [
            "prod:/cristexhub/dev/identity/browser",
            "prod:/cristexhub/dev/identity/admin-service",
            "prod:/cristexhub/dev/identity/bootstrap",
            "prod:/cristexhub/dev/identity/auditor",
        ]
        and keys == _EXPECTED_KEY_NAMES
        and all(item.get("recursive") is False and item.get("tags") == [] for item in contracts)
        and contracts[2].get("lifecycle") == "one-time-successor-create-then-retire"
        and contracts[2].get("kubernetesTarget") == "forbidden-controller-input-only"
        and contracts[3].get("lifecycle") == "reserved-no-value-while-auditor-disabled"
        and contracts[3].get("kubernetesTarget") == "forbidden-while-disabled"
        and predecessor == {
            "path": "prod:/shared-services/keycloak",
            "key": "CRISTEXHUB_DEV_OIDC_CLIENT_SECRET",
            "mutation": "forbidden",
            "retention": "through-accepted-cutover-and-rollback-window",
        }
        and writers.get("identityPerPath") == "required"
        and writers.get("dedicatedSuccessorWriter") == "absent"
        and writers.get("currentExecution") == "forbidden"
        and writers.get("broadUploaderReuse") == "forbidden"
        and writers.get("runtimeReaderReuse") == "forbidden"
        and writers.get("predecessorOverwrite") == "forbidden"
        and absence.get("path") == "prod:/cristexhub/dev/identity/bootstrap"
        and absence.get("exactKey") == "KEYCLOAK_DEV_BOOTSTRAP_CLIENT_SECRET"
        and absence.get("metadataOnly") is True
        and absence.get("requiredState") == "absent"
        and absence.get("preExistingValue")
        == "fail-closed-foreign-or-unknown-stop"
        and absence.get("ownershipAdoption") == "forbidden"
        and cas.get("apiSemantics") == "unverified-blocker"
        and cas.get("requiredBehavior") == [
            "metadata-only-preflight",
            "exact-absence-or-expected-revision-precondition",
            "conditional-write",
            "conflict-fails-closed",
            "ambiguous-write-unknown-stop-no-retry",
            "metadata-only-key-closure-and-revision-readback",
        ]
        and cas.get("ifMatchOrEquivalent")
        == "required-after-provider-api-verification"
        and cas.get("blindRetry") == "forbidden"
        and cas.get("overwriteWithoutExpectedRevision") == "forbidden"
        and all(no_output.get(key) == "no-log-mode-0600-memory-only" for key in (
            "requestBodies", "responses", "accessTokens"
        ))
        and no_output.get("values") == "never-returned"
        and admission.get("existingDevRuntimeVapReuse") == "forbidden"
        and admission.get("existingSharedServicesVapReuse") == "forbidden"
        and admission.get("additiveExactVapSourceRequired") is True
        and admission.get("additiveExactRbacSourceRequired") is True
        and admission.get("materializationCurrentPhase") == "forbidden"
        and spec.get("currentExecution") == "forbidden"
    )


def _api_contract_valid(spec: dict[str, Any]) -> bool:
    legacy = spec.get("legacyProd") or {}
    bootstrap = spec.get("bootstrapPhase") or {}
    recurring = spec.get("recurringAuditPhase") or {}
    forbidden = spec.get("forbidden") or {}
    safety = spec.get("safety") or {}
    response = spec.get("responseContract") or {}
    return (
        spec.get("status") == "source-only-check-only"
        and spec.get("activation") == "apply-blocked-pending-all-transition-gates"
        and spec.get("apply") == "forbidden"
        and spec.get("transportRef") == "cristexhub-dev-admin-rest-port-forward"
        and spec.get("bootstrapActorRef") == "keycloak-dev-successor-bootstrap"
        and spec.get("recurringAuditorRef") == "keycloak-dev-auditor"
        and spec.get("retirementCustodianRef")
        == "keycloak-dev-bootstrap-retirement-custodian"
        and legacy.get("realm") == _LEGACY_REALM
        and legacy.get("actorRef") == "keycloak-prod-compatibility-auditor"
        and legacy.get("actorCapability") == "absent-blocker"
        and legacy.get("allowedMethods") == ["GET"]
        and legacy.get("writeMethods") == []
        and legacy.get("allowedPaths") == [
            "GET /admin/realms/cristexhub",
            "GET /admin/realms/cristexhub/clients?clientId=cristexhub-prod",
            "GET /admin/realms/cristexhub/groups?search=cristexhub-prod-super-admin",
        ]
        and legacy.get("rawResponseSha256BeforeAfter") == "required-sanitized"
        and legacy.get("canonicalProjectionSha256BeforeAfter") == "required-sanitized"
        and legacy.get("mutation") == "forbidden"
        and bootstrap.get("actor") == "keycloak-dev-successor-bootstrap"
        and bootstrap.get("allowedMethods") == ["GET", "POST", "PUT"]
        and (bootstrap.get("realmCreate") or {}) == {
            "method": "POST",
            "path": "/admin/realms",
            "exactTarget": "cristexhub-dev",
            "status": 201,
            "retry": "forbidden",
            "conflictResolution": "one-exact-get-then-operator-review",
        }
        and bootstrap.get("automaticCreatorGrantLedger") == "required"
        and bootstrap.get("retirementCustodianCapability") == "absent-blocker"
        and bootstrap.get("retirementBeforeRecurringAudit") == "required"
        and recurring.get("status")
        == "blocked-no-viable-least-privilege-keycloak-admin-role"
        and recurring.get("actor") == "keycloak-dev-auditor"
        and recurring.get("actorEnabled") is False
        and recurring.get("credentialMaterialization") == "forbidden"
        and recurring.get("allowedMethods") == []
        and recurring.get("directRealmRoles") == []
        and recurring.get("fgapPolicies") == []
        and (recurring.get("rejectedCapabilities") or {}).get("query-clients")
        == "can-enumerate-all-confidential-client-secrets"
        and (recurring.get("rejectedCapabilities") or {}).get("query-groups")
        == "enumerates-all-group-metadata"
        and (recurring.get("rejectedCapabilities") or {}).get("client-view")
        == "exposes-confidential-client-secret"
        and (recurring.get("rejectedCapabilities") or {}).get("group-view")
        == "exposes-group-role-mapping-and-detail-data"
        and recurring.get("adminRestCalls") == "forbidden"
        and recurring.get("protocolMapperInventory") == "one-shot-transition-only"
        and recurring.get("missingOwnedObjectBehavior") == "fail-closed-no-create"
        and (spec.get("resourceIds") or {}) == {
            "deriveFromNames": "forbidden",
            "captureFromSameOriginLocationOrExactGet": "required",
            "bindToEphemeralAttestation": "required",
            "duplicateOrForeignOwned": "fail-closed",
        }
        and forbidden.get("methods") == ["DELETE", "PATCH"]
        and "users" in (forbidden.get("resources") or [])
        and "memberships" in (forbidden.get("resources") or [])
        and "dynamic-groups" in (forbidden.get("resources") or [])
        and forbidden.get("paths") == [
            "/admin/realms/cristexhub/users",
            "/admin/realms/cristexhub-dev/users",
            "/admin/realms/cristexhub/groups/{id}/members",
            "/admin/realms/cristexhub-dev/groups/{id}/members",
            "/admin/realms/cristexhub-dev/role-mappings",
            "routes",
            "ingress",
            "cloudflare",
            "prod-writes",
        ]
        and "legacy-prod-realm" in (forbidden.get("resources") or [])
        and response.get("conflictStatus") == "409-not-success"
        and response.get("timeoutOrConnectionLoss") == "unknown-stop"
        and response.get("ambiguousPostRetry") == "forbidden"
        and all(safety.get(key) is True for key in (
            "noDeletePath", "noPatchPath", "noProdWritePath", "noUserPath",
            "noMembershipPath", "noDynamicGroupPath", "noRoutePath", "noBlindRetry"
        ))
        and safety.get("currentExecution") == "not-run"
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
            os.environ.get("CRISTEXWEB_KEYCLOAK_DEV_TRANSITION_ENTRYPOINT") == "v2"
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
            or not _wrapper_process_valid()
            or not valid_binding
        ):
            return {"changed": False, "failed": True, "msg": "CHECK_ONLY_GUARD"}
        return {
            "changed": True,
            "failed": False,
            "msg": "DEV transition source validated offline; API and apply state were not inspected",
        }
