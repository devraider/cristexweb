from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ansible/files/components/keycloak-dev-identity-transition"
DEFAULTS = ROOT / "ansible/roles/keycloak_dev_identity_transition_bootstrap/defaults/main.yml"
TASKS = ROOT / "ansible/roles/keycloak_dev_identity_transition_bootstrap/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/keycloak_dev_identity_transition_guarded.py"
WRAPPER = ROOT / "ansible/bin/bootstrap-keycloak-dev-identity-transition"
PLAYBOOK = ROOT / "ansible/playbooks/bootstrap_keycloak_dev_identity_transition.yml"
RUNBOOK = ROOT / "runbooks/keycloak-dev-realm-migration.md"
POLICY = ROOT / "ansible/files/policies/hosted-identity-authorization.yml"
FIXTURE = ROOT / "tests/reject_keycloak_dev_identity_transition_action_only.yml"


class KeycloakDevIdentityTransitionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.leaves = sorted(COMPONENT.rglob("*.yaml"))
        cls.documents = [yaml.safe_load(path.read_text()) for path in cls.leaves]
        cls.by_kind = {document["kind"]: document for document in cls.documents}
        cls.defaults = yaml.safe_load(DEFAULTS.read_text())
        cls.tasks_text = TASKS.read_text()
        cls.plugin_text = PLUGIN.read_text()
        cls.wrapper_text = WRAPPER.read_text()
        cls.runbook_text = RUNBOOK.read_text()
        cls.policy = yaml.safe_load(POLICY.read_text())

    def test_exact_hash_bound_four_leaf_closure(self) -> None:
        self.assertEqual(4, len(self.leaves))
        self.assertEqual(
            {
                "KeycloakAdminTransportContract",
                "KeycloakIdentityActorContract",
                "InfisicalSuccessorValueContract",
                "KeycloakDevIdentityApiTransitionContract",
            },
            set(self.by_kind),
        )
        ledger = {}
        for line in (COMPONENT / "MANIFESTS.sha256").read_text().splitlines():
            digest, path = line.split("  ", 1)
            ledger[path] = digest
        self.assertEqual(
            {str(path.relative_to(COMPONENT)) for path in self.leaves}, set(ledger)
        )
        for path in self.leaves:
            self.assertEqual(0o644, stat.S_IMODE(path.stat().st_mode), path)
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                ledger[str(path.relative_to(COMPONENT))],
            )
        self.assertEqual(4, self.defaults["keycloak_dev_identity_transition_bootstrap_object_count"])
        self.assertEqual(4, len(self.defaults["keycloak_dev_identity_transition_bootstrap_expected_hashes"]))

    def test_plugin_canonical_hashes_match_every_exact_document(self) -> None:
        plugin_hashes = dict(
            re.findall(
                r'"([^"/]+/[^"/]+)": "([0-9a-f]{64})"',
                self.plugin_text,
            )
        )
        expected = {}
        for document in self.documents:
            identity = f"{document['kind']}/{document['metadata']['name']}"
            canonical = json.dumps(document, sort_keys=True, separators=(",", ":"))
            expected[identity] = hashlib.sha256(canonical.encode()).hexdigest()
        self.assertEqual(expected, plugin_hashes)

    def test_private_loopback_kubernetes_api_port_forward_is_exact(self) -> None:
        spec = self.by_kind["KeycloakAdminTransportContract"]["spec"]
        self.assertEqual("source-only-check-only", spec["status"])
        self.assertEqual(
            "blocked-current-keycloak-has-no-https-admin-listener", spec["activation"]
        )
        self.assertEqual("controller-kubernetes-api-port-forward", spec["mode"])
        self.assertTrue(spec["controllerOnly"])
        target = spec["target"]
        self.assertEqual("shared-services", target["namespace"])
        self.assertEqual("keycloak", target["deployment"])
        self.assertEqual(
            {
                "app.kubernetes.io/name": "keycloak",
                "app.kubernetes.io/part-of": "cristex-platform",
            },
            target["selector"],
        )
        self.assertEqual("exactly-one-ready-pod", target["readiness"])
        self.assertEqual("required-at-runtime", target["uidBinding"])
        self.assertEqual(8080, target["currentHttpPort"])
        self.assertEqual("forbidden", target["currentHttpUse"])
        self.assertEqual(8443, target["futureHttpsPort"])
        self.assertEqual("absent-blocker", spec["futureTls"]["listener"])
        self.assertEqual("required", spec["futureTls"]["privateCa"])
        self.assertEqual(["IP:127.0.0.1"], spec["futureTls"]["serverCertificateSan"])
        self.assertEqual("required", spec["futureTls"]["leafKeyCorrespondence"])
        self.assertEqual("absent-blocker", spec["futureTls"]["certificateSource"])
        self.assertEqual("absent-blocker", spec["futureTls"]["caCertificateSha256"])
        self.assertEqual("absent-blocker", spec["futureTls"]["leafCertificateSha256"])
        self.assertEqual("required", spec["futureTls"]["exactCaVerification"])
        self.assertTrue(spec["futureTls"]["validateCertificates"])
        self.assertEqual("forbidden", spec["futureTls"]["insecureSkipVerify"])
        forwarding = spec["portForward"]
        self.assertEqual("blocked-pending-pinned-focused-client", forwarding["implementation"])
        self.assertEqual("forbidden-unpinned", forwarding["externalKubectlBinary"])
        self.assertEqual("127.0.0.1", forwarding["address"])
        self.assertEqual("18443:8443", forwarding["mapping"])
        self.assertEqual("loopback-only", forwarding["listenerScope"])
        self.assertEqual("forbidden", forwarding["persistentKubernetesObjects"])
        self.assertEqual("required", forwarding["cleanup"]["alwaysCloseStream"])
        self.assertEqual("required", forwarding["cleanup"]["verifyListenerGone"])
        self.assertEqual("unknown-stop", forwarding["cleanup"]["ambiguousCleanup"])
        self.assertEqual("https://127.0.0.1:18443", spec["adminRest"]["endpoint"])
        self.assertEqual(
            "/realms/master/protocol/openid-connect/token",
            spec["adminRest"]["bootstrapTokenPath"],
        )
        self.assertEqual("forbidden-disabled-actor", spec["adminRest"]["auditorTokenPath"])
        for key in ("publicHostname", "authHostname", "cloudflare", "ingress", "service", "helperPod", "nodePort", "loadBalancer"):
            self.assertEqual("forbidden", spec["publicExposure"][key])
        self.assertNotIn("auth.cristex-soft.com", json.dumps(spec))

    def test_actor_contract_is_successor_scoped_and_least_privilege(self) -> None:
        spec = self.by_kind["KeycloakIdentityActorContract"]["spec"]
        self.assertEqual(["GET"], spec["legacyRealm"]["readMethods"])
        self.assertEqual([], spec["legacyRealm"]["writeMethods"])
        bootstrap = spec["bootstrapActor"]
        self.assertEqual("cristexhub-dev-bootstrap", bootstrap["clientId"])
        self.assertEqual(["create-realm"], bootstrap["requiredMasterRoles"])
        self.assertEqual("forbidden", bootstrap["existingBootstrapAdminReuse"])
        self.assertEqual("forbidden", bootstrap["existingBreakGlassReuse"])
        self.assertEqual("one-transition", bootstrap["maxUse"])
        self.assertEqual("forbidden", bootstrap["recurringReconciliation"])
        self.assertEqual("absent-blocker", spec["retirementCustodian"]["status"])
        self.assertEqual(
            "required",
            bootstrap["automaticCreatorGrantLedger"]["roleRemovalBeforeRecurringAudit"],
        )
        auditor = spec["recurringAuditor"]
        self.assertEqual("cristexhub-dev-auditor", auditor["clientId"])
        self.assertEqual("cristexhub-dev", auditor["realm"])
        self.assertEqual("forbidden", auditor["masterRealmAccess"])
        self.assertFalse(auditor["enabled"])
        self.assertEqual("forbidden-while-disabled", auditor["credentialMaterialization"])
        self.assertEqual(
            "blocked-no-viable-least-privilege-admin-rest-role", auditor["recurringUse"]
        )
        self.assertEqual([], auditor["directRealmManagementRoles"])
        self.assertIn("manage-realm", auditor["forbiddenRealmManagementRoles"])
        self.assertIn("manage-clients", auditor["forbiddenRealmManagementRoles"])
        rejected = auditor["rejectedDirectRoleBindings"]
        self.assertEqual(
            "forbidden-can-enumerate-all-confidential-client-secrets",
            rejected["query-clients"],
        )
        self.assertEqual("forbidden-enumerates-all-group-metadata", rejected["query-groups"])
        fgap = auditor["fineGrainedAdminPermissionsV2"]
        self.assertEqual("none", fgap["recurringActorPolicies"])
        self.assertEqual("forbidden-exposes-confidential-client-secret", fgap["clientView"])
        self.assertEqual("forbidden-exposes-membership-data", fgap["groupView"])
        self.assertEqual("forbidden", fgap["manage"])
        self.assertEqual("forbidden", fgap["selfManagement"])
        self.assertEqual("fail-closed-no-create", auditor["missingOwnedObjectBehavior"])
        for resource in ("users", "memberships", "dynamic-groups", "routes", "prod-clients", "protocol-mapper-writes"):
            self.assertIn(resource, auditor["forbiddenResources"])
        self.assertEqual("forbidden", spec["credentialCustody"]["valuesInSource"])

    def test_infisical_successor_keys_and_cas_are_exact(self) -> None:
        spec = self.by_kind["InfisicalSuccessorValueContract"]["spec"]
        self.assertEqual("cristexweb-infrastructure", spec["project"]["name"])
        self.assertEqual("619656da-14f3-4872-857b-be103cdc5326", spec["project"]["id"])
        self.assertEqual("prod", spec["project"]["environment"])
        contracts = spec["contracts"]
        self.assertEqual(
            ["browser", "admin-service", "bootstrap", "auditor"],
            [item["name"] for item in contracts],
        )
        self.assertEqual(
            [
                "prod:/cristexhub/dev/identity/browser",
                "prod:/cristexhub/dev/identity/admin-service",
                "prod:/cristexhub/dev/identity/bootstrap",
                "prod:/cristexhub/dev/identity/auditor",
            ],
            [item["path"] for item in contracts],
        )
        self.assertEqual(
            [
                "OIDC_CLIENT_SECRET",
                "ADMIN_SERVICE_CLIENT_SECRET",
                "KEYCLOAK_DEV_BOOTSTRAP_CLIENT_SECRET",
                "KEYCLOAK_DEV_REALM_AUDITOR_CLIENT_SECRET",
            ],
            [key for item in contracts for key in item["exactKeys"]],
        )
        self.assertEqual("forbidden", spec["predecessor"]["mutation"])
        self.assertEqual("absent", spec["writers"]["dedicatedSuccessorWriter"])
        self.assertEqual("forbidden", spec["writers"]["broadUploaderReuse"])
        cas = spec["cas"]
        self.assertEqual("absent", spec["bootstrapAbsencePreflight"]["requiredState"])
        self.assertEqual(
            "fail-closed-foreign-or-unknown-stop",
            spec["bootstrapAbsencePreflight"]["preExistingValue"],
        )
        self.assertEqual("unverified-blocker", cas["apiSemantics"])
        self.assertEqual("forbidden", cas["blindRetry"])
        self.assertEqual("forbidden", cas["overwriteWithoutExpectedRevision"])
        self.assertEqual("never-returned", spec["noOutput"]["values"])
        self.assertEqual("forbidden", spec["kubernetesAdmission"]["materializationCurrentPhase"])

    def test_api_transition_is_present_update_only_and_apply_blocked(self) -> None:
        spec = self.by_kind["KeycloakDevIdentityApiTransitionContract"]["spec"]
        self.assertEqual("forbidden", spec["apply"])
        self.assertEqual(["GET"], spec["legacyProd"]["allowedMethods"])
        self.assertEqual([], spec["legacyProd"]["writeMethods"])
        self.assertEqual(["GET", "POST", "PUT"], spec["bootstrapPhase"]["allowedMethods"])
        bootstrap = spec["bootstrapPhase"]
        self.assertEqual("required", bootstrap["automaticCreatorGrantLedger"])
        self.assertEqual("absent-blocker", bootstrap["retirementCustodianCapability"])
        recurring = spec["recurringAuditPhase"]
        self.assertEqual(
            "blocked-no-viable-least-privilege-keycloak-admin-role", recurring["status"]
        )
        self.assertFalse(recurring["actorEnabled"])
        self.assertEqual("forbidden", recurring["credentialMaterialization"])
        self.assertEqual([], recurring["allowedMethods"])
        self.assertEqual([], recurring["directRealmRoles"])
        self.assertEqual([], recurring["fgapPolicies"])
        self.assertEqual(
            "can-enumerate-all-confidential-client-secrets",
            recurring["rejectedCapabilities"]["query-clients"],
        )
        self.assertEqual("forbidden", recurring["adminRestCalls"])
        self.assertEqual("one-shot-transition-only", recurring["protocolMapperInventory"])
        self.assertEqual("fail-closed-no-create", recurring["missingOwnedObjectBehavior"])
        self.assertEqual("forbidden", spec["resourceIds"]["deriveFromNames"])
        self.assertEqual(["DELETE", "PATCH"], spec["forbidden"]["methods"])
        for resource in ("users", "memberships", "dynamic-groups", "routes", "legacy-prod-realm"):
            self.assertIn(resource, spec["forbidden"]["resources"])
        for key in (
            "noDeletePath",
            "noPatchPath",
            "noProdWritePath",
            "noUserPath",
            "noMembershipPath",
            "noDynamicGroupPath",
            "noRoutePath",
            "noBlindRetry",
            "idempotenceRequired",
        ):
            self.assertTrue(spec["safety"][key])
        self.assertEqual(201, spec["responseContract"]["createStatus"])
        self.assertEqual("204-empty-body", spec["responseContract"]["updateStatus"])
        self.assertEqual("409-not-success", spec["responseContract"]["conflictStatus"])
        self.assertEqual("unknown-stop", spec["responseContract"]["timeoutOrConnectionLoss"])
        self.assertEqual("forbidden", spec["responseContract"]["ambiguousPostRetry"])

    def test_action_and_role_are_offline_only(self) -> None:
        self.assertNotIn("ansible.builtin.uri", self.plugin_text)
        self.assertNotIn("_execute_module", self.plugin_text)
        self.assertNotIn("ansible.builtin.uri", self.tasks_text)
        self.assertNotIn("ansible.builtin.command", self.tasks_text)
        self.assertNotIn("ansible.builtin.shell", self.tasks_text)
        self.assertIn("apply_blocked", self.tasks_text)
        self.assertIn("offline_source_only", self.tasks_text)
        self.assertIn("noProdWritePath", self.tasks_text)
        self.assertIn("noDeletePath", self.tasks_text)
        self.assertIn("noPatchPath", self.tasks_text)

    def test_wrapper_is_check_only_and_rejects_runtime_inputs(self) -> None:
        self.assertIn("bootstrap-keycloak-dev-identity-transition check", self.wrapper_text)
        self.assertIn("--check", self.wrapper_text)
        self.assertIn("--diff", self.wrapper_text)
        self.assertIn("inventory.local.yml", self.wrapper_text)
        self.assertIn("CRISTEXWEB_KEYCLOAK_DEV_TRANSITION_ADMIN_TOKEN_FILE", self.wrapper_text)
        self.assertIn("CRISTEXWEB_KEYCLOAK_DEV_TRANSITION_API_BASE_URL", self.wrapper_text)
        self.assertIn("CRISTEXWEB_KEYCLOAK_DEV_TRANSITION_KUBECONFIG", self.wrapper_text)
        self.assertIn("ANSIBLE_RUN_TAGS", self.wrapper_text)
        self.assertIn("ANSIBLE_SKIP_TAGS", self.wrapper_text)
        self.assertIn("ANSIBLE_START_AT_TASK", self.wrapper_text)
        self.assertNotIn("apply", self.wrapper_text.split("usage=", 1)[1].split("\n", 1)[0])
        self.assertIn("role: keycloak_dev_identity_transition_bootstrap", PLAYBOOK.read_text())

    def test_direct_action_and_wrapper_injection_are_rejected(self) -> None:
        controller = ROOT / ".venv/bin/ansible-playbook"
        if not controller.exists():
            controller = Path("/home/paul/projects/cristexweb/.venv/bin/ansible-playbook")
        direct = subprocess.run(
            [str(controller), "-i", "localhost,", str(FIXTURE), "--check", "--diff"],
            cwd=ROOT / "ansible",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertNotEqual(0, direct.returncode, direct.stdout)
        self.assertIn("ENTRYPOINT_GUARD", direct.stdout)
        environment = os.environ.copy()
        environment["ANSIBLE_RUN_TAGS"] = "definitely-not-present"
        wrapper = subprocess.run(
            [str(WRAPPER), "check"],
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(78, wrapper.returncode, wrapper.stdout)
        self.assertNotIn("PLAY [", wrapper.stdout)

    def test_policy_and_runbook_bind_next_phase(self) -> None:
        successor = self.policy["realm_transition"]["successor_dev"]
        self.assertEqual("ansible/files/components/keycloak-dev-identity-transition", successor["transition_source_path"])
        self.assertEqual("transport/admin-rest-port-forward.yaml", successor["transport_contract"])
        self.assertEqual("identity/least-privilege-actors.yaml", successor["actor_contract"])
        self.assertEqual("infisical/successor-cas-contract.yaml", successor["infisical_cas_contract"])
        self.assertEqual("api/present-update-transition.yaml", successor["api_transition_contract"])
        self.assertEqual("offline-check-only", successor["transition_execution"])
        self.assertEqual("forbidden", successor["api_apply"])
        for required in (
            "Next source-only transition phase",
            "current HTTP `8080` listener is explicitly forbidden",
            "disabled realm-local auditor placeholder with no role, FGAP policy, credential\n  materialization, or Admin REST method",
            "provider CAS semantics explicitly unverified",
            "DELETE`/`PATCH`/users/memberships/dynamic-groups/routes/PROD-write denial",
            "private transport\nactivation",
            "CAS writes",
        ):
            self.assertIn(required, self.runbook_text)


if __name__ == "__main__":
    unittest.main()
