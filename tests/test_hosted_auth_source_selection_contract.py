from __future__ import annotations

import hashlib
import re
import tarfile
import unittest
from pathlib import Path, PurePosixPath

import yaml


ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
KUBERNETES = ROOT / "kubernetes"
POLICY = ANSIBLE / "files/policies/hosted-identity-authorization.yml"
PROD_RUNTIME_POLICY = ANSIBLE / "files/policies/cristexhub-prod-runtime-materialization.yml"
PROD_RUNTIME_STATIC_SECRET = (
    ANSIBLE
    / "files/components/infisical-cristexhub-prod-runtime/source/"
    / "cristexhub-prod-runtime-static-secret.yaml"
)
DATABASE_POLICY = ANSIBLE / "files/policies/shared-database-architecture.yml"

ARGO_VENDOR = ANSIBLE / "files/vendor/argocd/10.3.0"
INFISICAL_VENDOR = ANSIBLE / "files/vendor/infisical-operator/0.11.7"

EXPECTED_VENDOR = {
    "files/vendor/argocd/10.3.0/SHA256SUMS": None,
    "files/vendor/argocd/10.3.0/argo-cd-10.3.0.tgz":
        "d08882d22d0c76e3174e005cc09abe300c70ba556aec76725a4410d172b9c1f3",
    "files/vendor/argocd/10.3.0/argo-cd-10.3.0.tgz.prov":
        "52157f1e9cf2a68cc26e6e456bff03afdfe11a8f1637078a72262e980fb5cd02",
    "files/vendor/argocd/10.3.0/pgp_keys.asc":
        "36366596211a1587d018be5b178687799cb2edfc3e3e3c6ccd661b33fc6305ca",
    "files/vendor/infisical-operator/0.11.7/SHA256SUMS": None,
    "files/vendor/infisical-operator/0.11.7/cloudsmith-signing-key.asc":
        "7693c83a40ef1536cfdefe0e27806bf8027d272d847bafcea44807d08400b8c9",
    "files/vendor/infisical-operator/0.11.7/kubernetes-operator-64d2d81.tar.gz":
        "a08141c750404c653d23b35ecb29ab33e788845c3f666f0984fa156b9c468415",
    "files/vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz":
        "7f8846c4f6b1cdca2cea23cf00a29d12a38f42eb8da8e125dc196a1e5683aea8",
    "files/vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz.prov":
        "a39ae4be9ca25f7dc0b50b6633c92fc320d427fd67364b50e82c0d512db7b933",
}


class HostedAuthSourceSelectionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_text = POLICY.read_text()
        cls.policy = yaml.safe_load(cls.policy_text)
        cls.prod_runtime_policy = yaml.safe_load(PROD_RUNTIME_POLICY.read_text())
        cls.prod_runtime_static_secret = yaml.safe_load(PROD_RUNTIME_STATIC_SECRET.read_text())
        cls.database_policy = yaml.safe_load(DATABASE_POLICY.read_text())

    def test_exact_vendor_closure_and_hashes(self) -> None:
        actual = {
            str(path.relative_to(ANSIBLE)): path
            for root in (ARGO_VENDOR, INFISICAL_VENDOR)
            for path in root.iterdir()
            if path.is_file()
        }
        self.assertEqual(set(EXPECTED_VENDOR), set(actual))
        for relative, expected in EXPECTED_VENDOR.items():
            if expected is None:
                continue
            digest = hashlib.sha256(actual[relative].read_bytes()).hexdigest()
            self.assertEqual(expected, digest, relative)

        self.assertEqual(
            """d08882d22d0c76e3174e005cc09abe300c70ba556aec76725a4410d172b9c1f3  argo-cd-10.3.0.tgz
52157f1e9cf2a68cc26e6e456bff03afdfe11a8f1637078a72262e980fb5cd02  argo-cd-10.3.0.tgz.prov
36366596211a1587d018be5b178687799cb2edfc3e3e3c6ccd661b33fc6305ca  pgp_keys.asc
""",
            (ARGO_VENDOR / "SHA256SUMS").read_text(),
        )
        self.assertEqual(
            """7f8846c4f6b1cdca2cea23cf00a29d12a38f42eb8da8e125dc196a1e5683aea8  secrets-operator-0.11.7.tgz
a39ae4be9ca25f7dc0b50b6633c92fc320d427fd67364b50e82c0d512db7b933  secrets-operator-0.11.7.tgz.prov
7693c83a40ef1536cfdefe0e27806bf8027d272d847bafcea44807d08400b8c9  cloudsmith-signing-key.asc
a08141c750404c653d23b35ecb29ab33e788845c3f666f0984fa156b9c468415  kubernetes-operator-64d2d81.tar.gz
""",
            (INFISICAL_VENDOR / "SHA256SUMS").read_text(),
        )

    def test_vendored_archives_have_safe_exact_chart_roots(self) -> None:
        for archive, expected_root in (
            (ARGO_VENDOR / "argo-cd-10.3.0.tgz", "argo-cd"),
            (INFISICAL_VENDOR / "secrets-operator-0.11.7.tgz", "secrets-operator"),
        ):
            with tarfile.open(archive, "r:gz") as bundle:
                members = bundle.getmembers()
            self.assertTrue(members)
            for member in members:
                path = PurePosixPath(member.name)
                self.assertFalse(path.is_absolute(), member.name)
                self.assertNotIn("..", path.parts, member.name)
                self.assertEqual(expected_root, path.parts[0], member.name)
                self.assertFalse(member.issym() or member.islnk(), member.name)

    def test_selected_realm_clients_groups_and_images_are_exact(self) -> None:
        self.assertEqual("cristex-hosted-identity-v3", self.policy["policy_schema"])
        self.assertEqual("source-selected-runtime-blocked", self.policy["policy_status"])
        self.assertEqual("cristexhub", self.policy["realm"]["name"])
        self.assertEqual(
            "https://auth.cristex-soft.com/realms/cristexhub",
            self.policy["realm"]["issuer"],
        )
        self.assertEqual("keycloak-default", self.policy["realm"]["production_theme"])
        self.assertEqual(
            "quay.io/keycloak/keycloak",
            self.policy["images"]["keycloak"]["repository"],
        )
        self.assertEqual(
            "sha256:7523ccfbd950f59783504cdf5a0138dae48746dfe36075bbfccdb5a9ee245ee2",
            self.policy["images"]["keycloak"]["linux_amd64_digest"],
        )
        self.assertEqual(
            "quay.io/keycloak/keycloak@sha256:7523ccfbd950f59783504cdf5a0138dae48746dfe36075bbfccdb5a9ee245ee2",
            self.policy["images"]["keycloak"]["pull_reference"],
        )
        self.assertEqual(
            "docker.io/library/postgres",
            self.policy["images"]["postgresql"]["repository"],
        )
        self.assertEqual(
            "sha256:dbbeb22a65db2503050cdbbe5e78f017478f10a1002a226463f049dbb017e99b",
            self.policy["images"]["postgresql"]["linux_amd64_digest"],
        )
        self.assertEqual(
            "docker.io/library/postgres@sha256:dbbeb22a65db2503050cdbbe5e78f017478f10a1002a226463f049dbb017e99b",
            self.policy["images"]["postgresql"]["pull_reference"],
        )
        browser_ids = [entry["id"] for entry in self.policy["clients"]["browser"]]
        self.assertEqual(
            [
                "cristexhub-dev",
                "cristexhub-prod",
                "reactive-resume-dev",
                "reactive-resume-prod",
                "argocd",
            ],
            browser_ids,
        )
        browser = {entry["id"]: entry for entry in self.policy["clients"]["browser"]}
        dev = browser["cristexhub-dev"]
        self.assertTrue(dev["callback_selected"])
        self.assertEqual("confidential", dev["client_type"])
        self.assertEqual("S256", dev["pkce_method"])
        self.assertEqual(["https://dev-hub.cristex-soft.com/oauth2/callback"], dev["redirect_uris"])
        self.assertEqual(["https://dev-hub.cristex-soft.com"], dev["web_origins"])
        self.assertEqual(["https://dev-hub.cristex-soft.com/"], dev["post_logout_redirect_uris"])
        self.assertEqual("infisical-cloud", dev["client_secret_owner"])
        self.assertEqual("prod:/shared-services/keycloak", dev["client_secret_path"])
        self.assertEqual("CRISTEXHUB_DEV_OIDC_CLIENT_SECRET", dev["client_secret_key"])

        prod = browser["cristexhub-prod"]
        self.assertEqual("cristexhub-prod", prod["namespace"])
        self.assertTrue(prod["callback_selected"])
        self.assertEqual("keycloak-configured-application-runtime-blocked", prod["activation"])
        self.assertEqual("confidential", prod["client_type"])
        self.assertEqual("S256", prod["pkce_method"])
        self.assertEqual(["https://hub.cristex-soft.com/oauth2/callback"], prod["redirect_uris"])
        self.assertEqual(["https://hub.cristex-soft.com"], prod["web_origins"])
        self.assertEqual(["https://hub.cristex-soft.com/"], prod["post_logout_redirect_uris"])
        self.assertEqual("infisical-cloud", prod["client_secret_owner"])
        self.assertEqual("prod:/cristexhub/prod/runtime", prod["client_secret_path"])
        self.assertEqual("OIDC_CLIENT_SECRET", prod["client_secret_key"])
        self.assertNotIn("CRISTEXHUB_PROD_OIDC_CLIENT_SECRET", self.policy_text)

        self.assertTrue(
            all(
                not entry["callback_selected"]
                for key, entry in browser.items()
                if key not in {"cristexhub-dev", "cristexhub-prod"}
            )
        )
        claims = self.policy["claims"]
        self.assertEqual("groups", claims["roles"])
        self.assertEqual("organization", claims["organizations"])
        self.assertEqual(
            ["sub", "email", "email_verified", "preferred_username"],
            claims["required_identity"],
        )
        self.assertFalse(claims["groups_use_full_path"])
        service_ids = [entry["id"] for entry in self.policy["clients"]["service"]]
        self.assertEqual(
            ["cristexhub-admin-svc-dev", "cristexhub-admin-svc-prod"], service_ids
        )
        roles = self.policy["roles"]["cristexhub"]
        self.assertEqual(["admin", "hr", "viewer", "interviewer"], roles["values"])
        self.assertEqual(
            "cristexhub-dev-<organization-alias>-<role>", roles["dev_group_template"]
        )
        self.assertEqual(
            "cristexhub-prod-<organization-alias>-<role>", roles["prod_group_template"]
        )
        self.assertEqual("cristexhub-dev-super-admin", roles["dev_super_admin_group"])
        self.assertEqual("cristexhub-prod-super-admin", roles["prod_super_admin_group"])
        self.assertEqual("deny", roles["missing_or_ambiguous_group"])

    def test_prod_oidc_source_is_shared_with_runtime_static_secret(self) -> None:
        source = self.prod_runtime_policy["oidc_client_secret_source"]
        self.assertEqual(
            {
                "owner": "infisical-cloud",
                "project_id": "619656da-14f3-4872-857b-be103cdc5326",
                "environment_slug": "prod",
                "path": "/cristexhub/prod/runtime",
                "key": "OIDC_CLIENT_SECRET",
                "target_key": "OIDC_CLIENT_SECRET",
                "values": "absent",
            },
            source,
        )
        prod = {
            entry["id"]: entry for entry in self.policy["clients"]["browser"]
        }["cristexhub-prod"]
        self.assertEqual(
            f'{source["environment_slug"]}:{source["path"]}',
            prod["client_secret_path"],
        )
        self.assertEqual(source["owner"], prod["client_secret_owner"])
        self.assertEqual(source["key"], prod["client_secret_key"])
        self.assertEqual(source["project_id"], self.prod_runtime_policy["project"]["id"])
        self.assertEqual(source["environment_slug"], self.prod_runtime_policy["project"]["environment"])
        self.assertEqual(source["path"], self.prod_runtime_policy["project"]["source_path"])
        self.assertEqual(source["path"], self.prod_runtime_policy["sources"]["infisical"]["path"])

        static_spec = self.prod_runtime_static_secret["spec"]
        self.assertEqual(
            {
                "projectId": source["project_id"],
                "environmentSlug": source["environment_slug"],
                "secretPath": source["path"],
                "recursive": False,
                "tagSlugs": [],
            },
            static_spec["sources"][0],
        )
        runtime_target = static_spec["targets"][0]
        self.assertEqual(source["target_key"], "OIDC_CLIENT_SECRET")
        self.assertEqual(
            "{{ .OIDC_CLIENT_SECRET.Value }}",
            runtime_target["template"]["data"][source["target_key"]],
        )
        self.assertIn(source["target_key"], self.prod_runtime_policy["target_keys"])

    def test_cristexhub_clients_have_explicit_environment_group_authorization(self) -> None:
        roles = self.policy["roles"]["cristexhub"]
        browser = {entry["id"]: entry for entry in self.policy["clients"]["browser"]}
        for environment, other_environment in (("dev", "prod"), ("prod", "dev")):
            authorization = browser[f"cristexhub-{environment}"]["group_authorization"]
            accepted = authorization["accepted_group_forms"]
            self.assertEqual(environment, authorization["environment"])
            self.assertEqual(
                f"cristexhub-{environment}-<organization-alias>-<role>",
                accepted["tenant_role"]["template"],
            )
            self.assertEqual(roles["values"], accepted["tenant_role"]["allowed_roles"])
            self.assertEqual(
                f"cristexhub-{environment}-super-admin",
                accepted["super_admin"]["exact"],
            )
            rejected = authorization["rejected_group_forms"]
            self.assertEqual("deny", rejected["cross_environment"])
            self.assertEqual("deny", rejected["unmatched"])
            self.assertEqual("deny", authorization["missing_or_ambiguous"])
            self.assertEqual(
                [
                    f"cristexhub-{other_environment}-<organization-alias>-<role>",
                    f"cristexhub-{other_environment}-super-admin",
                ],
                rejected["examples"],
            )

    @staticmethod
    def _accepted_group(group: str, authorization: dict) -> bool:
        accepted = authorization["accepted_group_forms"]
        if group == accepted["super_admin"]["exact"]:
            return True
        template = accepted["tenant_role"]["template"]
        prefix, alias_marker, suffix = template.partition("<organization-alias>")
        role_prefix, role_marker, role_suffix = suffix.partition("<role>")
        if not alias_marker or not role_marker or role_suffix:
            return False
        roles = "|".join(
            re.escape(role) for role in accepted["tenant_role"]["allowed_roles"]
        )
        pattern = (
            re.escape(prefix)
            + r"[a-z0-9]+(?:-[a-z0-9]+)*"
            + re.escape(role_prefix)
            + f"(?:{roles})"
        )
        return re.fullmatch(pattern, group) is not None

    def test_environment_group_authorization_denies_cross_environment_and_ambiguous_groups(
        self,
    ) -> None:
        browser = {entry["id"]: entry for entry in self.policy["clients"]["browser"]}
        for environment, other_environment in (("dev", "prod"), ("prod", "dev")):
            authorization = browser[f"cristexhub-{environment}"]["group_authorization"]
            accepted = authorization["accepted_group_forms"]
            self.assertTrue(
                self._accepted_group(
                    f"cristexhub-{environment}-acme-admin", authorization
                )
            )
            self.assertTrue(
                self._accepted_group(
                    accepted["super_admin"]["exact"], authorization
                )
            )
            for group in (
                f"cristexhub-{other_environment}-acme-admin",
                f"cristexhub-{other_environment}-super-admin",
                f"cristexhub-{environment}-acme-owner",
                f"cristexhub-{environment}-acme-admin-extra",
                "cristexhub-unknown-acme-admin",
            ):
                self.assertFalse(self._accepted_group(group, authorization), group)
            self.assertEqual("deny", authorization["missing_or_ambiguous"])
            self.assertEqual("deny", authorization["rejected_group_forms"]["cross_environment"])
            self.assertEqual("deny", authorization["rejected_group_forms"]["unmatched"])

    def test_argocd_and_namespace_authorization_is_deny_first(self) -> None:
        argo = self.policy["roles"]["argocd"]
        self.assertEqual("argocd-admin", argo["administrator_group"])
        self.assertEqual("argocd-readonly", argo["readonly_group"])
        self.assertEqual("deny", argo["ungrouped_default"])
        self.assertEqual(["applications:get", "projects:get"], argo["readonly_permissions"])
        self.assertEqual(
            ["logs", "sync", "action", "override", "delete", "exec", "configuration-mutation"],
            argo["readonly_forbidden"],
        )
        self.assertFalse(argo["dex_enabled"])
        self.assertEqual(
            {
                "platform-edge",
                "argocd",
                "cristexhub-dev",
                "cristexhub-prod",
                "shared-services",
            },
            set(self.policy["namespaces"]),
        )
        edge = self.policy["namespaces"]["platform-edge"]
        self.assertEqual(["cloudflared"], edge["allows"])
        self.assertEqual(
            {
                "infisical-kubernetes-operator",
                "keycloak-runtime",
                "shared-postgresql-engine",
                "shared-mongodb-engine",
                "shared-rabbitmq-engine",
                "application-databases",
            },
            set(edge["denies"]),
        )
        shared = self.policy["namespaces"]["shared-services"]
        self.assertEqual(
            {
                "infisical-kubernetes-operator",
                "keycloak-runtime",
                "shared-postgresql-engine",
                "shared-mongodb-engine",
                "shared-rabbitmq-engine",
                "application-databases",
                "keycloak-dedicated-database",
                "keycloak-dedicated-database-role",
                "keycloak-dedicated-database-credential",
                "keycloak-dedicated-backup-scope",
            },
            set(shared["allows"]),
        )
        self.assertEqual(
            {
                "keycloak-role-access-to-application-databases",
                "application-role-access-to-keycloak-database",
                "keycloak-role-create-database",
                "keycloak-role-create-role",
                "application-role-create-database",
                "application-role-create-role",
            },
            set(shared["denies"]),
        )
        self.assertIn("prod-credentials", self.policy["namespaces"]["cristexhub-dev"]["denies"])
        self.assertIn("dev-credentials", self.policy["namespaces"]["cristexhub-prod"]["denies"])
        self.assertTrue(
            all(not entry["browser_flow_allowed"] for entry in self.policy["clients"]["service"])
        )

        database = self.policy["database_architecture"]
        self.assertEqual(
            "ansible/files/policies/shared-database-architecture.yml",
            database["policy_path"],
        )
        self.assertEqual(
            self.database_policy["policy_schema"], database["policy_schema"]
        )
        self.assertEqual("keycloak", database["keycloak_consumer"])
        self.assertTrue(database["keycloak_deployment_separate_from_postgresql"])
        self.assertEqual(
            {
                "policy_path": "ansible/files/policies/shared-rabbitmq-architecture.yml",
                "policy_schema": "cristex-shared-rabbitmq-v1",
            },
            self.policy["rabbitmq_architecture"],
        )
        self.assertEqual(
            {
                "policy_path": "ansible/files/policies/shared-stateful-backup-architecture.yml",
                "policy_schema": "cristex-shared-stateful-backup-v1",
            },
            self.policy["backup_architecture"],
        )
        self.assertEqual(
            "dedicated-owner-role",
            self.database_policy["engines"]["postgresql"]["consumers"]["keycloak"][
                "principal"
            ],
        )

    def test_universal_auth_and_ownership_are_value_free(self) -> None:
        self.assertEqual("infisical-cloud", self.policy["secrets"]["value_owner"])
        self.assertEqual("universal-auth", self.policy["secrets"]["operator_authentication"])
        self.assertFalse(self.policy["secrets"]["values_allowed_in_source"])
        self.assertEqual(
            "cristexhub-application",
            self.policy["roles"]["cristexhub"]["dynamic_organization_group_owner"],
        )
        self.assertIn("static-realm-settings", self.policy["ownership"]["ansible"])
        self.assertIn(
            "dynamic-organization-role-groups",
            self.policy["ownership"]["cristexhub-application"],
        )
        self.assertIn("all-runtime-check-apply-idempotence", self.policy["blocked"])

    def test_selection_records_are_source_only_and_runtime_blocked(self) -> None:
        records = {
            "argocd-release-selection.md": ("10.3.0", "v3.5.0"),
            "infisical-operator-release-selection.md": ("v0.11.7", "Universal Auth"),
            "keycloak-release-selection.md": ("26.7.1", "17.10"),
        }
        for name, required in records.items():
            text = (ROOT / "runbooks" / name).read_text()
            normalized = " ".join(text.split())
            self.assertIn("SELECTED FOR OFFLINE SOURCE AUTHORING ONLY", normalized)
            self.assertIn("NOT RUN/BLOCKED", normalized)
            for value in required:
                self.assertIn(value, text)
            self.assertNotIn(".pi-subagents", text)
            self.assertNotIn("/Users/", text)

        keycloak = (ROOT / "runbooks" / "keycloak-release-selection.md").read_text()
        self.assertIn("quay.io/keycloak/keycloak@sha256:", keycloak)
        self.assertIn("docker.io/library/postgres@sha256:", keycloak)

    def test_only_infisical_controller_source_widens_outside_kubernetes_tree(self) -> None:
        self.assertEqual(
            {
                "platform/namespaces/argocd.yaml",
                "platform/namespaces/platform-edge.yaml",
                "platform/namespaces/shared-services.yaml",
                "applications/namespaces/cristexhub-dev.yaml",
                "applications/namespaces/cristexhub-prod.yaml",
            },
            {
                str(path.relative_to(KUBERNETES))
                for path in KUBERNETES.rglob("*")
                if path.is_file()
            },
        )
        operational = [
            path
            for root in (ANSIBLE / "bin", ANSIBLE / "playbooks", ANSIBLE / "roles")
            for path in root.rglob("*")
            if path.is_file()
        ]
        self.assertEqual(
            {
                "ansible/bin/bootstrap-keycloak",
                "ansible/playbooks/bootstrap_keycloak.yml",
                "ansible/roles/keycloak_bootstrap/defaults/main.yml",
                "ansible/roles/keycloak_bootstrap/tasks/main.yml",
                "ansible/bin/bootstrap-keycloak-route",
                "ansible/playbooks/bootstrap_keycloak_route.yml",
                "ansible/roles/keycloak_route_bootstrap/defaults/main.yml",
                "ansible/roles/keycloak_route_bootstrap/tasks/main.yml",
            },
            {
                str(path.relative_to(ROOT))
                for path in operational
                if "keycloak" in str(path).lower() and "backup" not in str(path).lower()
            },
        )
        self.assertEqual(
            {
                "ansible/bin/bootstrap-postgresql",
                "ansible/bin/configure-postgresql-keycloak-backup",
                "ansible/bin/provision-shared-postgresql",
                "ansible/playbooks/bootstrap_postgresql.yml",
                "ansible/playbooks/configure_postgresql_keycloak_backup.yml",
                "ansible/playbooks/provision_shared_postgresql.yml",
                "ansible/roles/postgresql_bootstrap/defaults/main.yml",
                "ansible/roles/postgresql_bootstrap/tasks/main.yml",
                "ansible/roles/shared_postgresql_provisioning/defaults/main.yml",
                "ansible/roles/shared_postgresql_provisioning/tasks/main.yml",
            },
            {
                str(path.relative_to(ROOT))
                for path in operational
                if "postgresql" in str(path).lower()
            },
        )
        self.assertEqual(
            {
                "ansible/bin/bootstrap-mongodb",
                "ansible/bin/configure-mongodb-shared-backup",
                "ansible/bin/provision-shared-mongodb",
                "ansible/playbooks/bootstrap_mongodb.yml",
                "ansible/playbooks/configure_mongodb_shared_backup.yml",
                "ansible/playbooks/provision_shared_mongodb.yml",
                "ansible/roles/mongodb_bootstrap/defaults/main.yml",
                "ansible/roles/mongodb_bootstrap/tasks/main.yml",
                "ansible/roles/shared_mongodb_provisioning/defaults/main.yml",
                "ansible/roles/shared_mongodb_provisioning/tasks/main.yml",
            },
            {
                str(path.relative_to(ROOT))
                for path in operational
                if "mongodb" in str(path).lower()
            },
        )
        self.assertEqual(
            {
                "bootstrap-argocd",
                "bootstrap_argocd.yml",
                "bootstrap-infisical-argocd-secrets",
                "bootstrap_infisical_argocd_secrets.yml",
                "bootstrap-argocd-route",
                "bootstrap_argocd_route.yml",
                "validate-argocd-ui-tls-material",
                "main.yml",
            },
            {path.name for path in operational if "argocd" in str(path).lower()},
        )
        self.assertEqual(
            {
                "bootstrap-infisical-operator",
                "bootstrap-infisical-proxy-secrets",
                "bootstrap_infisical_operator.yml",
                "bootstrap_infisical_proxy_secrets.yml",
                "bootstrap-infisical-argocd-secrets",
                "bootstrap_infisical_argocd_secrets.yml",
                "bootstrap-infisical-database-secrets",
                "bootstrap_infisical_database_secrets.yml",
                "transfer-infisical-proxy-recovery",
                "transfer_infisical_proxy_recovery.yml",
                "seed-infisical-universal-auth",
                "seed_infisical_universal_auth.yml",
                "upload-infisical-bootstrap-values",
                "materialize-infisical-cristexhub-dev-runtime",
                "bootstrap-infisical-cristexhub-dev-runtime",
                "bootstrap_infisical_cristexhub_dev_runtime.yml",
                "bootstrap-infisical-cristexhub-prod-runtime",
                "bootstrap_infisical_cristexhub_prod_runtime.yml",
                "bootstrap-infisical-cloudflared-secrets",
                "bootstrap_infisical_cloudflared_secrets.yml",
                "main.yml",
            },
            {path.name for path in operational if "infisical" in str(path).lower()},
        )

    def test_policy_and_selection_hygiene(self) -> None:
        texts = [
            self.policy_text,
            *((ROOT / "runbooks" / name).read_text() for name in (
                "argocd-release-selection.md",
                "infisical-operator-release-selection.md",
                "keycloak-release-selection.md",
            )),
        ]
        combined = "\n".join(texts)
        for pattern in (
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"\bghp_[A-Za-z0-9]+\b",
            r"\bgithub_pat_[A-Za-z0-9_]+\b",
            r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
            r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
            r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
            r"/Users/[^/\s]+/",
        ):
            self.assertNotRegex(combined, pattern)
        self.assertNotRegex(
            combined,
            r"(?im)^\s*(?:password|token|client_secret|api_key|credentials?)\s*:\s*\S+",
        )


if __name__ == "__main__":
    unittest.main()
