# Reactive Resume hosted architecture

## Status

**SOURCE POLICY ONLY — RUNTIME BLOCKED / DEV CONTRACT INCOMPLETE.** Reactive Resume
is a planned private DEV MVP in `cristexhub-dev`. A bounded read-only inventory on
2026-08-21 found no matching Reactive Resume Kubernetes objects; this is point-in-time
evidence, not reconciliation. This revision adds only a value-free blocker inventory and does not add a deployable manifest,
apply-capable wrapper, Secret, image digest, Namespace, database object, identity
mutation, route, or runtime state. PROD remains a reservation/template only and
cannot be activated from this policy.

The canonical contract is
[`reactive-resume-architecture.yml`](../ansible/files/policies/reactive-resume-architecture.yml).
`executable_source_allowed` remains `false`. No runtime/API/provider operation is
authorized by this document.

## Source boundary

Local Compose tags, callbacks, credentials, development realms, and application
assets are not hosted inputs. The official upstream release, immutable linux/amd64
image digest, publisher/build trust, SBOM, vulnerability disposition, off-node OCI
recovery, and target pull/admission evidence remain unselected. GitHub Actions does
not rebuild the upstream image and no mutable tag is deployable.

No first-party Kubernetes operator/chart has been accepted. Any future Kubernetes
translation must be based on one reviewed upstream release and must not silently
copy Compose assumptions, environment-variable names, health endpoints, migration
behavior, storage semantics, or printer/browser dependencies.

## DEV placement and explicit blockers

The intended application namespace is `cristexhub-dev`, not `shared-services`.
`shared-services` supplies only shared infrastructure and the dedicated PostgreSQL
logical scope. The future application boundary is one private single-replica
Deployment, one private ClusterIP Service, exact deny-first NetworkPolicy objects,
and no Ingress, NodePort, LoadBalancer, Cloudflare Tunnel, Cloudflare DNS, public
route, or direct origin. Those objects are absent until a separate executable
closure is reviewed.

The DEV contract is incomplete and blocked on all of the following:

- **Dedicated Infisical lane:** the existing broad 11-target database seam,
  shared manager Secret reads, broad Secret writer, and alternate-target VAPs are
  forbidden for Reactive Resume. The namespace-inequality validation is the correct
  deny predicate and must not be inverted; activation is instead blocked on the
  existing match-condition skip behavior, unobserved CEL type-check status, exact
  allowlist expansion, complete foreign-object inventory, and truth-table tests.
  The inequality validation is an allow-outside/deny-inside guard: `true` passes and
  `false` denies. Future checks must prove zero type-check warnings. A
  new RR-DEV-only path, machine identity, exact runtime Secret
  key set, target-namespace materialization, exact VAP, and exact writer RBAC must
  be designed and separately checked. Broad lanes must never be mislabeled DEV-only.
- **Dedicated PostgreSQL lane:** the current all-consumer provisioning wrapper and
  CloudNativePG Database/DatabaseRole source overlap in lifecycle ownership and are
  forbidden for RR activation as a combined path. Select exactly one lifecycle
  owner before source: the current candidate is CloudNativePG CRs via bounded
  Ansible, while any helper is limited to read-only verification and narrowly
  reviewed ACL hardening. Its DEV selector cannot include PROD. The owner must be `reactive_resume_dev_owner` with
  `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOINHERIT`, `NOREPLICATION`, and
  `NOBYPASSRLS`; revoke PUBLIC `CONNECT`, `TEMPORARY`, and schema creation, prove
  empty `pg_auth_members` plus denied `SET ROLE` to every foreign role, grant only
  the exact own database privileges, and run every DEV↔PROD/CristexHub/Keycloak/role-creation
  negative test. Shared-engine failure and contention are acknowledged; connection,
  storage, migration, backup-staging, and restore headroom must be measured before
  apply. Database apply requires engine readiness, backup, exact Secret, check,
  separate approval, apply, and idempotence.
- **CNPG/TLS/NetworkPolicy:** one canonical PostgreSQL Service identity, CA/TLS
  Secret, server TLS Secret, and CNPG-compatible database NetworkPolicy remain
  unresolved blockers. Legacy selectors or an assumed `shared-postgresql` versus
  `shared-postgresql-rw` identity are not acceptable. Permit only exact app-to-DB
  traffic and required DNS; deny direct/public origins and broad namespace
  selectors.
- **OIDC:** new DEV identity targets the successor `cristexhub-dev` realm and issuer;
  runtime state for that realm and its Reactive Resume client remains unaccepted.
  The retained `cristexhub` realm remains PROD-compatible and read-only during this
  transition. Do not mutate either client from this policy. Before runtime, pin one
  upstream release and verify its candidate custom callback
  `${APP_URL}/api/auth/oauth2/callback/custom`, web origin, issuer/JWKS/signature/
  nonce enforcement, PKCE, scopes, audience, logout/account-linking, and local
  password-login disablement. Upstream profile mapping must not manufacture trusted
  `email_verified`, and Keycloak groups/organizations must not become an application
  authorization boundary. Wrong issuer/audience/key, replay, expired-token, and
  cross-environment tests remain mandatory. PROD gets a separate client only after
  DEV acceptance.
- **Object storage:** PostgreSQL stores resume JSON but is not the whole application
  state. Reviewed v5 candidates also persist pictures and PDFs; screenshots are
  cache-like objects whose recovery semantics still require review. The observed
  upstream public-read ACL and unauthenticated `/uploads` behavior are activation
  blockers. Select a private backend with separate DEV/PROD scope, encryption,
  versioning/immutable manifests, URL continuity, checksum/readback, bucket-policy
  proof, and database/object-consistent encrypted backup and isolated restore. Local
  ephemeral container storage is forbidden.
- **Redis and AI:** no server-side Agent or Redis requirement is accepted for the
  reviewed v5 candidate. Do not deploy Redis or claim server-side AI state. Any
  future release that adds those dependencies requires a new pinned review; browser
  local AI-key state is not authoritative server state.
- **Application keys:** exact key names remain unselected until one upstream release
  is pinned. Current candidate names include `AUTH_SECRET`, `OAUTH_CLIENT_SECRET`,
  while `ENCRYPTION_SECRET` was not observed and must not be invented. Candidate
  names are not an exact contract. Key names, per-environment paths, independent custody,
  retrieval/decryption rehearsal, rotation/revocation, and key-loss recovery are
  unselected blockers. Values never enter Git, argv, environment examples, logs, or
  evidence.
- **Migrations and recovery:** reviewed v5 startup migrations and their non-failing
  error handling are unaccepted blockers. Executable source requires upstream
  hardening or a separately proven fail-closed migration mechanism, lock,
  pre-migration backup, forward-compatible expand/contract policy, and schema rollback evidence are
  required. Separate PostgreSQL, object-storage, application-key, and (if enabled)
  Redis recovery scopes, encrypted off-node copies, integrity/readback, isolated
  restore, login/upload validation, and measured RPO/RTO are absent blockers. The
  current 24-hour RPO/4-hour RTO values are targets, not acceptance evidence.

No blocker above is satisfied by a policy reservation or by the existing broad
shared-services lanes.

## Environment and database isolation

DEV and PROD must not share identity clients, credentials, application keys,
database principals, migrations, object-storage paths, any future Redis scopes, or backup
scopes. They may share only the one general PostgreSQL engine as a common failure
domain. Namespace labels and NetworkPolicy are not substitutes for PostgreSQL ACL
and negative authorization tests.

## Exposure and ownership

Initial access, if ever approved, remains private through an approved administrative
path. Ingress, Traefik public routes, NodePort, LoadBalancer, Cloudflare Tunnel,
Cloudflare DNS, public administration, and direct origins are forbidden in this
source-only revision. A future route requires separate provider, hostname,
positive-flow, negative-admin/direct-origin, and rollback approval and is last.

Ansible is the bounded bootstrap owner only for a future exact closure. Argo CD may
receive one exact namespaced object set only after Ansible stops reconciling it and
registration, adoption, successful sync, and managed-field evidence pass. Dual
reconciliation is forbidden.

## PROD reservation/template only

Reactive Resume PROD is represented only as a promotion template for
`cristexhub-prod`, `reactive-resume-prod`, `reactive_resume_prod`, and separate
credential/backup scopes. This Reactive Resume template has no generated manifests,
runtime objects, Secret values, selected
callbacks, database provisioning, or public route. No PROD object may be generated
from a reservation, and no PROD activation may happen before private DEV validation
and an explicit DEV soak.

The machine-readable promotion order is mandatory:

1. complete source/image/identity/Infisical/database/storage/recovery blockers;
2. separately approve and validate private DEV;
3. complete the declared DEV soak and recovery evidence;
4. only then design/check/apply separate PROD scopes and private validation;
5. public routing is last and independently approved.

Simultaneous DEV and PROD activation is forbidden because it destroys causal
validation evidence and can expose the shared PostgreSQL failure domain to two
unaccepted migrations/workloads.

## No mutation in this revision

No Deployment, StatefulSet, Service, PVC, Secret, Infisical CR, Database object,
Ingress, Argo Application, route, image pull, registry write, host, Kubernetes,
Infisical, database, or provider mutation was performed. The only runtime contact
was the bounded read-only Kubernetes inventory recorded above.
Rollback is a Git revert; namespace/PVC/database deletion and implicit credential
rotation are forbidden.
