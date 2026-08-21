# Reactive Resume hosted architecture

## Status

**SOURCE POLICY ONLY — RUNTIME BLOCKED / DEV CONTRACT INCOMPLETE.** Reactive Resume
is a planned private DEV MVP in `cristexhub-dev`. A bounded read-only inventory on
2026-08-21 found no matching Reactive Resume Kubernetes objects; this is point-in-time
evidence, not reconciliation. This revision adds only a value-free blocker inventory
and a candidate-only image provenance record; the recorded digest is not selected or
deployable. It adds no deployable manifest, apply-capable wrapper, Secret, Namespace,
database object, identity mutation, route, or runtime state. PROD remains a
reservation/template only and
cannot be activated from this policy.

The canonical contract is
[`reactive-resume-architecture.yml`](../ansible/files/policies/reactive-resume-architecture.yml).
`executable_source_allowed` remains `false`. No runtime/API/provider operation is
authorized by this document.

## Source boundary

Local Compose tags, callbacks, credentials, development realms, and application
assets are not hosted inputs. Read-only source and Docker Hub review recorded
upstream tag `v5.2.7` at commit
`5392728f22580ac107cad25a5ccfcde962133535`, OCI index
`sha256:656a7ce0409ea1b8fcdb4985320d8b687b94da1201d10af13fd1e2c7c74f6083`,
linux/amd64 child
`sha256:befa93b3af3e8fe91a4dd02401fc7996c4aa2f19641463e3b2aaa77089caff5a`,
and config
`sha256:7f2c997d1f48b152e649c2561e0e23e2d5bc7d9e7e7dbf3e6cac7dd1a6f002f7`.
This is specifically `docker.io/amruthpillai/reactive-resume`; it makes no GHCR
registry-equivalence claim.

The image config instead identifies revision
`3221afda9ddfb03d6cce87927b0ce47338b4cfa8`, 16 commits and 150 files beyond the
release tag, and was created after that release. The index signature plus SPDX and
SLSA attestations were observed, but direct linux/amd64-child signing was not;
vulnerability disposition, off-node OCI recovery, and target admission remain
absent. The digest is therefore candidate-only, **not selected and not deployable**.
GitHub Actions does not rebuild it.

No first-party Kubernetes operator/chart has been accepted. Any future Kubernetes
translation requires a patched, reproducibly bound source/image and must not
silently copy Compose assumptions. Reviewed source facts include container port
`3000`, `GET /api/health` returning `200` or `503` from database/storage checks, no
Browserless requirement, and client-side PDF rendering; they are evidence, not a
runtime contract.

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
  `${APP_URL}/api/auth/oauth2/callback/custom`, web origin, scopes, and audience.
  The reviewed integration has sound signed-cookie/DB-backed one-time state but no
  PKCE or OIDC nonce, decodes ID tokens without signature/JWKS/issuer/audience/
  expiry verification, hardcodes new OAuth users as email-verified, leaves the
  direct username/password endpoint usable despite the email-auth flag, permits
  insufficiently trusted account linking, does not consistently bind accounts to
  OIDC `sub`, and performs only local logout. Configuration alone cannot remediate
  this. A reviewed source patch or equivalent validating broker must add exact token
  validation, PKCE S256, nonce/replay handling, trustworthy `email_verified`, full
  local-auth disablement, stable account continuity, and RP-initiated logout.
  Keycloak groups/organizations must not become an application authorization
  boundary. Wrong issuer/audience/key, replay, expired-token, local-login,
  account-linking, and cross-environment tests remain mandatory. PROD gets a
  separate client only after DEV acceptance.
- **Object storage:** PostgreSQL stores resume JSON but is not the whole application
  state. Reviewed v5 candidates also persist pictures and PDFs; screenshots are
  cache-like objects whose recovery semantics still require review. The observed
  upstream public-read ACL, unauthenticated and publicly immutable-cacheable
  `/uploads` behavior, and arbitrary upload MIME acceptance are activation blockers.
  Partial S3 configuration also silently falls back to local storage, while health
  proves only a fixed-key put/delete. A source patch plus a private backend with
  separate DEV/PROD scope, authenticated reads, strict MIME policy, encryption,
  versioning/immutable manifests, URL continuity, checksum/readback, bucket-policy
  proof, and database/object-consistent encrypted backup and isolated restore are
  required. Local ephemeral container storage is forbidden.
- **Redis and AI:** v5.2.7 contains a server Agent workspace. It conditionally
  requires `REDIS_URL` and `ENCRYPTION_SECRET`; Agent attachments additionally
  require private S3, and Redis is absent from `/api/health`. Agent and Redis remain
  disabled and unselected for the MVP. They may not be deployed until a separate
  feature, health, Secret, storage, NetworkPolicy, backup, and recovery review is
  accepted. Browser-local AI-key state is not authoritative server state.
- **Application keys:** reviewed candidate keys include required `AUTH_SECRET` and
  custom-provider `OAUTH_CLIENT_SECRET`. `ENCRYPTION_SECRET` is a genuine upstream
  conditional key with a minimum length of 32 for saved AI-provider credentials and
  the Agent workspace. This inventory is not a materialization contract because the
  source patch and enabled feature set are not selected. Exact per-environment paths,
  independent custody, retrieval/decryption rehearsal, rotation/revocation, and
  key-loss recovery remain blockers. Values never enter Git, argv, environment
  examples, logs, or evidence.
- **Migrations and recovery:** v5.2.7 always runs embedded Drizzle migrations with
  the runtime `DATABASE_URL` before listening. Failure is fail-closed by rethrow and
  process exit, and pending SQL runs in one transaction; however, selection is by
  migration name rather than checksum and there is no advisory/distributed lock,
  timeout, migration-only mode, startup-disable flag, or separate migration URL.
  Broad/destructive DDL exists. The existing CNPG role also has `inherit: true`,
  contradicting the required `NOINHERIT`, and the unpatched runtime cannot use a
  DDL-free role. Executable source therefore requires a reviewed source patch plus a
  single-run locked migration Job, distinct migration/runtime privileges,
  pre-migration backup, forward-compatible expand/contract policy, and schema
  rollback evidence. Separate PostgreSQL, object-storage, application-key, and (if
  enabled) Redis recovery scopes, encrypted off-node copies, integrity/readback,
  isolated restore, login/upload validation, and measured RPO/RTO are absent
  blockers. The
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
Infisical, database, or provider mutation was performed. Read-only contact was
limited to GitHub source/release metadata, Docker Hub OCI metadata/attestations, and
the bounded Kubernetes absence inventory recorded above.
Rollback is a Git revert; namespace/PVC/database deletion and implicit credential
rotation are forbidden.
