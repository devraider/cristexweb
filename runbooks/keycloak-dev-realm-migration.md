# Keycloak DEV successor-realm configuration

## Status and scope

**SOURCE-ONLY / CHECK-ONLY / NOT RUN.** The existing `cristexhub` realm and
issuer remain the retained PROD-compatibility identity:

- realm: `cristexhub`
- issuer: `https://auth.cristex-soft.com/realms/cristexhub`

This phase adds only a value-free source contract for a future DEV successor:

- realm: `cristexhub-dev`
- issuer: `https://auth.cristex-soft.com/realms/cristexhub-dev`

No Keycloak Admin API check has been run from this phase, and no realm, client,
group, mapper, Secret, route, application, Kubernetes, or provider mutation is
authorized by this source. The existing private Keycloak workload and legacy
realm are outside this lane.

The only entrypoint is:

```text
ansible/bin/bootstrap-keycloak-dev-identity check
```

The wrapper rejects `apply`; it always invokes Ansible with `--check --diff`.
The role and action plugin also fail closed unless Ansible check mode is active.
A future present/update transition requires a new reviewed successor lane and a
separate approval. This lane has no destructive path.

## Exact source closure

The four hash-bound, value-free source leaves are:

1. `ansible/files/components/keycloak-dev-identity/realm/cristexhub-dev.yaml`
2. `ansible/files/components/keycloak-dev-identity/client/cristexhub-dev.yaml`
3. `ansible/files/components/keycloak-dev-identity/groups/static-groups.yaml`
4. `ansible/files/components/keycloak-dev-identity/mappers/protocol-mappers.yaml`

The closure contains:

- realm settings for `cristexhub-dev` with registration and direct grants disabled;
- browser client `cristexhub-dev` with the exact DEV callback/origin/logout URI,
  confidential PKCE S256 settings, and no credential value;
- bearer-only service client `cristexhub-admin-svc-dev` with browser flow disabled;
- static group `cristexhub-dev-super-admin` only;
- `groups`, `organization`, and DEV audience protocol-mapper contracts;
- Infisical ownership/path/key metadata only, never a client credential;
- application ownership of dynamic organization membership groups.

The source explicitly rejects PROD, Argo, master, and other cross-environment
identity names. It does not copy the legacy realm export or any local Compose
realm asset.

## Guard and transport boundary

`ansible/roles/keycloak_dev_identity_bootstrap/` and
`ansible/plugins/action/keycloak_dev_identity_guarded.py` implement a focused,
read-only Admin API preflight using `ansible.builtin.uri` internally. For each
source leaf, the action:

1. verifies the one-shot wrapper attestation and exact source hash;
2. verifies a controller-local administrator token file is a regular mode-0600
   file owned by the invoking user without printing or exporting its contents;
3. reads the retained `cristexhub` realm and refuses legacy identity drift;
4. reads only the DEV realm inventory, clients, groups, and required mappers;
5. rejects PROD, Argo, master, or foreign identities;
6. reports absent or differing DEV state as predicted change without issuing a
   write request.

The wrapper passes only the protected token-file **path** and fixed API base URL.
The token value never enters Git, argv, examples, evidence, or returned Ansible
results. The action removes URI response content and invocation data before
returning. The current Keycloak route source does not change in this phase; an
Admin API transport/private route for future execution requires its own review.

The lane is present/update-oriented in its contract but check-only in execution.
It contains no write verb and no resource-removal behavior. The retained legacy
realm is never a target object.

## Migration gates before any DEV cutover

The following are separate gates and are not implied by source or check mode:

1. fresh encrypted Keycloak database backup with role/ownership metadata;
2. isolated restore using the exact Keycloak release, validating both realm rows,
   clients, groups, mappers, admin access, and a synthetic login;
3. `identity-preservation-review`: no-output inventory of legacy users, stable IDs,
   organizations, memberships, dynamic groups, client settings, and mapper contracts;
4. proof that DEV users and memberships can be represented in the successor realm;
5. proof of `(issuer, subject)` continuity or a separately reviewed application
   identity remapping migration;
6. successor client credential generation and Infisical custody without replacing
   PROD values;
7. private route/discovery/JWKS and callback source for the successor issuer;
8. clean immutable CristexHub application revision with DEV issuer and realm
   changes only;
9. DEV-first rollout, authenticated login/callback/logout tests, negative
   cross-environment tests, and a soak period;
10. separate PROD compatibility retirement approval after the rollback/token-drain
    window.

The existing `cristexhub` realm is retained during all gates. Realm deletion,
client deletion, credential revocation, database restore, public route change,
and PROD application cutover each require distinct approval.

## Required private validation

For `cristexhub-dev`:

- discovery issuer and JWKS remain inside `/realms/cristexhub-dev`;
- exact DEV client, audience, PKCE, callback, origin, and logout settings;
- `groups`, `organization`, and required identity claims are emitted as designed;
- DEV group forms authorize only DEV roles;
- PROD groups, wrong audience, wrong issuer, and legacy-realm tokens are denied;
- DEV service client has no browser flow and cannot administer PROD or master;
- login, callback, refresh, logout, and organization membership behavior succeed;
- direct admin, management, health, metrics, and origin paths remain private;
- CONNECT proxy positive/negative behavior is recorded without credentials or
  Authorization headers;
- no Secret values, cookies, tokens, or private identity material appear in logs.

Cross-environment negative tests must prove PROD tokens cannot authenticate to DEV and DEV tokens cannot authenticate to PROD. Static source contracts do not substitute for those tests.

## Rollback boundary

Before successor acceptance, rollback is source-only: revert the migration commit
and leave `cristexhub` unchanged. During a future migration window, rollback must
restore the previous protected DEV application revision and predecessor client
credential through a dedicated protected lane; it must not delete the successor
realm or restore a production database as routine rollback. The legacy realm,
issuer, users, and backup remain retained until a separately approved retirement.
