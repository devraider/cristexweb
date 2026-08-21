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
- disabled future service-account client `cristexhub-admin-svc-dev`, with browser,
  direct-grant, and service-account flows blocked until exact least-privilege roles
  and audiences are selected;
- static group `cristexhub-dev-super-admin` only;
- `groups`, scope/context-bound `organization`, and DEV audience mapper contracts;
- native Keycloak Organizations enabled, with dynamic membership migration blocked;
- Infisical ownership/path/key metadata only, never a client credential;
- application ownership of dynamic organization membership groups.

The source explicitly rejects PROD, Argo, master, and other cross-environment
identity names. It does not copy the legacy realm export or any local Compose
realm asset.

## Guard and transport boundary

`ansible/roles/keycloak_dev_identity_bootstrap/` and
`ansible/plugins/action/keycloak_dev_identity_guarded.py` implement an offline
source validator. For each source leaf, the action:

1. verifies the one-shot wrapper attestation and exact canonical source hash;
2. validates the exact DEV realm, clients, group, mappers, and successor-only
   Infisical metadata;
3. rejects PROD, Argo, master, cross-environment, secret-bearing, or deletion
   contracts;
4. reports predicted change because runtime state is deliberately unknown.

The wrapper rejects administrator-token and API-base environment inputs. It does
not contact Keycloak, Kubernetes, Infisical, Cloudflare, or any other runtime.
The public Keycloak hostname is not an approved Admin REST transport, and the
current route source remains unchanged.

Before any runtime preflight, the separate transition closure requires a dedicated
Keycloak HTTPS listener, exact private-CA certificate with the reviewed loopback SAN,
and controller-local Kubernetes API port-forward bound to the exact Ready Pod UID.
The current HTTP `8080` listener is explicitly forbidden for Admin credentials.
The future mapping is `127.0.0.1:18443` to HTTPS `8443`, with strict certificate
validation and no public `/admin` or `/realms/master` exposure. Its implementation
remains blocked until a focused controller client is pinned; an unpinned external
`kubectl` binary is not selected.

The source contract is present/update-oriented, but execution remains offline and
check-only. It contains no API request, write verb, or resource-removal behavior.
The retained legacy realm is never a target object.

## Next source-only transition phase

The next phase is represented by the separate four-leaf closure under
`ansible/files/components/keycloak-dev-identity-transition/` and the only entrypoint
is:

```text
ansible/bin/bootstrap-keycloak-dev-identity-transition check
```

It validates, without contacting any runtime:

- a blocked strict-TLS controller-local port-forward contract targeting one exact
  Ready Keycloak Pod UID, with no helper Pod, Service, route, or unpinned binary;
- a dedicated one-transition master service account with only `create-realm`, an
  explicit automatic-role ledger, and a still-absent separate retirement custodian;
- a disabled realm-local auditor placeholder with no role, FGAP policy, credential
  materialization, or Admin REST method: exact Keycloak 26.7.1 collection/projection
  semantics for `query-clients` and `query-groups` remain an unverified blocker;
  `view-clients` and client FGAP `view` authorize secret-bearing reads, while group
  `view` exposes role-mapping
  and detail data beyond the auditor boundary;
- four separate Infisical path reservations for browser, disabled admin-service,
  one-time bootstrap, and disabled auditor metadata, with no Kubernetes targets,
  no writer, and provider CAS semantics explicitly unverified; and
- phase-specific API contracts: bootstrap GET/POST/PUT, no recurring Admin REST
  method, and no PROD compatibility GET until an exact role and field projection
  are separately selected,
  opaque resource-ID binding, PROD before/after digests, ambiguous-write
  UNKNOWN-STOP, and unconditional
  `DELETE`/`PATCH`/users/memberships/dynamic-groups/routes/PROD-write denial.

The wrapper rejects `apply`, public-host/API/token inputs, task-selection controls,
unsafe inventory, and non-loopback transport values. The action additionally binds
the live ancestor PID, exact canonical wrapper argv/path/hash/owner/mode, and its
single-run mode-`0600` attestation; a directly invoked official playbook with a
self-minted receipt fails closed. The controller account itself remains a trusted
boundary and is not defended against a malicious same-UID process that deliberately
emulates process provenance. This phase does not start a
port-forward, acquire an Admin REST credential, read Infisical, call Kubernetes, or
create/update the successor realm. API transition apply, private transport
activation, actor materialization, CAS writes, client Secret materialization,
identity migration, and authenticated validation remain separately approved and
blocked.

## Migration gates before any DEV cutover

The following are separate gates and are not implied by source or check mode:

1. fresh encrypted Keycloak database backup plus separately recoverable
   role/ownership metadata (the current dump excludes ownership/privileges);
2. isolated restore using the exact Keycloak release, validating roles/ownership,
   realm rows, clients, groups, mappers, admin access, and a synthetic login rather
   than only catalog count;
3. `identity-preservation-review`: no-output inventory of legacy users, stable IDs,
   organizations, memberships, dynamic groups, client settings, and mapper contracts;
4. proof that DEV users and memberships can be represented in the successor realm;
5. proof of `(issuer, subject)` continuity or a separately reviewed application
   identity remapping migration;
6. successor credentials through the four exact `/cristexhub/dev/identity/*`
   paths, only after Infisical provider CAS semantics and a dedicated no-output
   writer are verified, without replacing predecessor or PROD values;
7. dedicated HTTPS listener plus strict-TLS controller-local Kubernetes API
   port-forward transport and precreated
   one-transition bootstrap and separate retirement-custodian identities; recurring
   Admin REST audit remains blocked until a genuinely narrower capability exists;
8. private route/discovery/JWKS and callback source for the successor issuer;
9. clean immutable CristexHub application revision with DEV issuer and realm
   changes only;
10. DEV-first rollout, authenticated login/callback/logout tests, negative
    cross-environment tests, and a soak period;
11. separate PROD compatibility retirement approval after the rollback/token-drain
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
