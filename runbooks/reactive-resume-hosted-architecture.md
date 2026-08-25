# Reactive Resume hosted architecture

## Status

**DEV PRIVATE RUNTIME AND ARGO HANDOFF CHECKPOINTED — FULL ACCEPTANCE AND SOAK REMAIN OPEN.**
Reactive Resume DEV runs in `cristexhub-dev` at the private hostname
`https://resume-dev.cristex-soft.com`. The shared `cristexhub` Keycloak client is
represented by an exact guarded value-free source contract; its secret remains
Infisical/Kubernetes-owned and no client or user outside that additive contract is
reconciled by the source. A separate recorded private-runtime acceptance covered
shared-realm OIDC/session/logout application flow for the active client; that
runtime evidence is not attributed to the source wrapper. The former same-named
`cristexhub-dev` client is disabled, retained only for rollback, and deletion is
forbidden.

Historical absence inventories remain historical and must not be read as current
state. The pinned live Argo revision
`dd7d4cedd902e68266d9713d1dbb8e90f0b529b1` contains exactly seven value-free
Argo manifests (including the default-deny NetworkPolicy), the private Traefik
route, the Infisical-owned `reactive-resume-dev-runtime` Secret, and materialized
DEV CA projections. Current HEAD contains eight YAML manifests in the checked-in
path, adding `networkpolicy-allow-backend.yaml`; that eighth manifest is
source-only and is not claimed live, Argo-managed, or applied. Argo revision
`dd7d4cedd902e68266d9713d1dbb8e90f0b529b1` is `Synced/Healthy`; the superseded
Ansible alignment and route lanes refuse reconciliation after handoff. Remaining gates are full OIDC/database acceptance,
measured non-empty schema-2 recovery correlation, TLS renewal installation, and
DEV soak. Existing broad database drift remains unaccepted; PROD remains a
reservation/template only and cannot be activated from this policy.

The canonical contract is
[`reactive-resume-architecture.yml`](../ansible/files/policies/reactive-resume-architecture.yml).
The separately approved, source-only [PostgreSQL exposure-rotation contract](reactive-resume-postgresql-exposure-rotation.md)
freezes only the two exposed DEV/PROD password scopes and remains blocked on
official Infisical CAS and CNPG Secret-type decisions.
`executable_source_allowed` is bounded to the reviewed private-DEV/Argo handoff
closure; this document authorizes
no new runtime/API/provider operation.

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
The candidate record is specifically
`docker.io/amruthpillai/reactive-resume`. GHCR metadata was also inspected
read-only, but it is a separate registry identity and no equivalence, selection, or
mirror claim is made.

The image config instead identifies revision
`3221afda9ddfb03d6cce87927b0ce47338b4cfa8`, 16 commits and 150 files beyond the
release tag, and was created after that release. The index signature plus SPDX and
SLSA attestations were observed, but direct linux/amd64-child signing was not;
vulnerability disposition, off-node OCI recovery, and target admission remain
absent. That Docker Hub digest remains candidate-only, **not selected and not deployable**.
The live private DEV source separately selects the immutable GHCR runtime digest
`sha256:720ff5a60a7f6b91a75535e230dbb664207fdf1bc5cb8732d584bae7ebdac13c` and
migration digest
`sha256:a4f0157e023c10c1c6ff163d34bf25c3343647247eddb1d4f9bfa9b46e1a3093`.
Those DEV selections are not provenance, vulnerability, off-node recovery, or
PROD promotion acceptance; GHCR equivalence to the Docker Hub candidate remains
unclaimed. GitHub Actions does not rebuild it.

No first-party Kubernetes operator/chart has been accepted. Any future Kubernetes
translation requires a patched, reproducibly bound source/image and must not
silently copy Compose assumptions. Facts reviewed at the annotated tag source—not
at the mismatched candidate image revision—include production `NODE_ENV`, port
`3000`, `GET /api/health` returning `200` or `503` from database/storage checks, no
Browserless requirement, and client-side PDF rendering. `NODE_ENV` is read outside
the validated schema; a non-production value can select the development port and
weaken rate limiting, so exact production metadata is mandatory. Candidate image source behavior remains unreviewed;
none of these facts is a runtime contract.

## Current DEV identity selection

The current private DEV identity contract supersedes the earlier successor-realm
selection below. Reactive Resume DEV uses the retained `cristexhub` realm so its
shared login theme and SSO are the same as CristexHub. The exact value-free
selection is:

- issuer/discovery: `https://auth.cristex-soft.com/realms/cristexhub`;
- browser hostname: `https://resume-dev.cristex-soft.com`;
- exact callback: `https://resume-dev.cristex-soft.com/api/auth/oauth2/callback/custom`;
- exact web origin: `https://resume-dev.cristex-soft.com`;
- exact RP-initiated post-logout redirect: `https://resume-dev.cristex-soft.com/`;
- client: `reactive-resume-dev` in realm `cristexhub`, with PKCE S256.

The former `reactive-resume-dev` client in `cristexhub-dev` is disabled and
retained only as a rollback handle. It must not be deleted. Re-enabling it is a
separate, explicitly reviewed rollback operation after recording the current
shared-realm metadata; rollback restores the old issuer/discovery values and
application configuration without deleting identities or mutating the `cristexhub`
CristexHub client. This runbook authorizes no delete or implicit re-enable path.

## DEV placement and explicit blockers

The intended application namespace is `cristexhub-dev`, not `shared-services`.
`shared-services` supplies only shared infrastructure and the dedicated PostgreSQL
logical scope. The live application boundary is one private single-replica Deployment, one
private ClusterIP Service, the pinned revision's seven exact Argo manifests
including deny-first NetworkPolicies and a private Traefik Ingress. Current HEAD
also contains the separately identified, unapplied `networkpolicy-allow-backend.yaml`;
it is not part of the live Argo count. It has no NodePort, LoadBalancer,
Cloudflare Tunnel, Cloudflare DNS, public route, or direct origin. The public
Cloudflare route remains separately forbidden.

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
  The existing PostgreSQL DEV and PROD credential Secrets are live from the broad
  lane, not accepted application-runtime materialization. During review, one local
  child queried their Secret data into its private session log. The exact child and
  async artifacts were removed without repeating values, but both credentials now
  require successor rotation and predecessor revocation before any use.
- **Dedicated PostgreSQL lane:** the current all-consumer provisioning wrapper and
  CloudNativePG Database/DatabaseRole source overlap in lifecycle ownership and are
  forbidden for RR activation as a combined path. Select exactly one lifecycle
  owner before source: the current candidate is CloudNativePG CRs via bounded
  Ansible, while any helper is limited to read-only verification and narrowly
  reviewed ACL hardening. Its DEV selector cannot include PROD. The successor runtime role is `reactive_resume_dev_runtime` and the separate
migration role is `reactive_resume_dev_migrator` in logical database
`reactive_resume_dev_successor`; both are NOINHERIT and remain subject to ACL
acceptance. The owner must be `reactive_resume_dev_runtime` with
  `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOINHERIT`, `NOREPLICATION`, and
  `NOBYPASSRLS`; revoke PUBLIC `CONNECT`, `TEMPORARY`, and schema creation, prove
  empty `pg_auth_members` plus denied `SET ROLE` to every foreign role, grant only
  the exact own database privileges, and run every DEV↔PROD/CristexHub/Keycloak/role-creation
  negative test. The live broad-lane DEV and PROD Database/DatabaseRole CRs do not
  satisfy this contract: both are applied with `INHERIT`, PUBLIC retains `CONNECT`
  and `TEMPORARY` across the five shared databases, and PROD creation was not RR
  promotion approval. They must not be used, deleted, or recreated by this policy.
  Shared-engine failure and contention are acknowledged; connection,
  storage, migration, backup-staging, and restore headroom must be measured before
  apply. Database apply requires engine readiness, backup, exact Secret, check,
  separate approval, apply, and idempotence.
- **CNPG/TLS/NetworkPolicy:** one canonical PostgreSQL Service identity, CA/TLS
  Secret, server TLS Secret, and CNPG-compatible database NetworkPolicy remain
  unresolved blockers. Legacy selectors or an assumed `shared-postgresql` versus
  `shared-postgresql-rw` identity are not acceptable. Permit only exact app-to-DB
  traffic and required DNS; deny direct/public origins and broad namespace
  selectors.
- **OIDC:** the accepted private DEV identity uses the shared `cristexhub` realm
  and issuer `https://auth.cristex-soft.com/realms/cristexhub`, with shared login
  theme/SSO. The `reactive-resume-dev` client is pinned to hostname
  `https://resume-dev.cristex-soft.com`, callback
  `/api/auth/oauth2/callback/custom`, exact web origin, exact post-logout redirect,
  and PKCE S256. The old same-named client in `cristexhub-dev` remains a
  rollback-only handle; deletion is forbidden and disable requires a separate
  approval after private acceptance. Before any retirement, record the shared
  client metadata, verify private login/session/logout and negative alternate-auth
  tests, then disable only the old client. Rollback re-enables the old client and
  restores the old issuer/discovery pair without deleting users or touching the
  CristexHub client. The historical upstream review found sound signed-cookie/
  DB-backed one-time state but no PKCE or OIDC nonce, decoded ID tokens without
  signature/JWKS/issuer/audience/expiry verification, hardcoded new OAuth users as
  email-verified, left the direct username/password endpoint usable despite the
  email-auth flag, unconditionally enabled passkeys, and enabled
  Google/GitHub/LinkedIn whenever credentials existed. Those alternate providers
  and credentials remain forbidden for the Keycloak-only boundary and require
  direct negative tests. It also permits
  insufficiently trusted account linking, does not consistently bind accounts to
  OIDC `sub`, and performs only local logout. Configuration alone cannot remediate
  this. A reviewed source patch or equivalent validating broker must add exact token
  validation, PKCE S256, nonce/replay handling, trustworthy `email_verified`, full
  local-auth disablement, stable account continuity, and RP-initiated logout.
  Keycloak groups/organizations must not become an application authorization
  boundary. Wrong issuer/audience/key, replay, expired-token, local-login,
  account-linking, and cross-environment tests remain mandatory. OAuth access,
  refresh, and ID tokens are stored without application-level token encryption;
  activation additionally requires a reviewed per-environment encryption/key-custody
  patch. Without SMTP, reset and verification message contents are logged, which is
  also a privacy blocker. PROD gets a separate client only after DEV acceptance.
- **Object storage:** PostgreSQL stores resume JSON but is not the whole application
  state. Reviewed v5.2.7 persists profile pictures plus application resume/cover-letter
  PDFs under the pictures prefix and private Agent attachments under a separate
  Agent prefix. `screenshots` and `pdfs` appear as delete-only legacy prefixes whose
  residual-object exposure remains unreviewed, while resume-export PDFs are streamed
  rather than persisted. The observed upstream
  public-read ACL, unauthenticated and publicly immutable-cacheable
  `/uploads` behavior, and arbitrary upload MIME acceptance are activation blockers.
  Partial S3 configuration also silently falls back to local storage, while delete
  pagination/completeness, prefix boundaries, timestamp collisions, and health's
  root fixed-key put/delete are unaccepted. A source patch plus a private backend with
  separate DEV/PROD scope, authenticated reads, byte-validated MIME allowlisting,
  safe disposition and `nosniff`, active-content denial, complete paginated prefix
  deletion, encryption, versioning/immutable manifests, URL continuity, checksum/
  readback, private-sentinel cleanup, Object Ownership/Public Access Block, anonymous
  `Get/List/Head/Put/Delete` denial, cross-environment prefix denial, bucket-policy
  proof, and database/object-consistent encrypted backup and isolated restore are
  required. Local ephemeral container storage is forbidden.
- **Redis and AI:** v5.2.7 contains a server Agent workspace. It conditionally
  requires `REDIS_URL` and `ENCRYPTION_SECRET`; Agent attachments additionally
  require private S3, and Redis is absent from `/api/health`. Agent and Redis remain
  disabled and unselected for the MVP. They may not be deployed until a separate
  feature, health, Secret, storage, NetworkPolicy, backup, and recovery review is
  accepted. Redis recovery is not applicable while Agent is disabled but becomes
  mandatory if Agent/Redis is selected; a Redis backup must never be presented as
  authoritative application state. Browser-local AI-key state is not authoritative
  server state.
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
  Migration schema/ledger bootstrap occurs outside the transaction that wraps the
  pending SQL and ledger inserts. Broad/destructive DDL exists. Both DEV and PROD
  Reactive Resume roles in the current broad CNPG source have `inherit: true`,
  contradicting required `NOINHERIT`; that all-consumer source remains forbidden for
  activation, and the unpatched runtime cannot use a DDL-free role. Executable
  source therefore requires a reviewed source patch plus a
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

The private DEV Traefik Ingress is live and Argo-managed through the Tailscale-only
hostname. NodePort, LoadBalancer, Cloudflare Tunnel/DNS routing, public
administration, public Traefik routing, and direct origins remain forbidden. Any
future public route requires separate provider, hostname, positive-flow,
negative-admin/direct-origin, and rollback approval and is last. Argo now owns the exact seven-object namespaced workload set from pinned
revision `dd7d4cedd902e68266d9713d1dbb8e90f0b529b1`; the current-HEAD
`networkpolicy-allow-backend.yaml` is not claimed live or Argo-managed. The
superseded Ansible alignment and route lanes refuse tracked objects. The API omits `metadata.managedFields`, so that
evidence is unavailable rather than claimed. Dual reconciliation remains
forbidden.

## PROD reservation/template only

Reactive Resume PROD is represented only as a promotion template for
`cristexhub-prod`, `reactive-resume-prod`, `reactive_resume_prod`, and separate
credential/backup scopes. This Reactive Resume template has no generated manifests,
runtime objects, Secret values, selected callbacks, accepted database provisioning,
or public route. Existing broad-lane PROD database/role/credential objects are
unapproved drift, not fulfillment of this reservation. No PROD object may be generated
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

## Current runtime boundary and custody

The private DEV Deployment, Service, ServiceAccount, three workload NetworkPolicies,
private Ingress, runtime Secret, materialized CA, and Argo Application are live
checkpoints. The seven workload manifests are value-free; Secret values remain
Infisical-owned. The live image digest is a DEV selection only and is not accepted
for promotion. PostgreSQL data restore, role/ACL restore, and credential custody are
separate contracts. No PROD workload or public route is authorized. Read-only contact included
GitHub source/release metadata, separate Docker Hub and GHCR OCI metadata/
attestations without an equivalence claim, workload/Argo absence inventory, and
CloudNativePG/NetworkPolicy/Secret metadata. One review child improperly requested
Secret data; no value is repeated here, all exact local child/async artifacts were
removed, and DEV/PROD PostgreSQL credential rotation plus predecessor revocation is
now mandatory.
Rollback is a Git revert; namespace/PVC/database deletion and implicit credential
rotation are forbidden.


The selected immutable GHCR runtime digest is a DEV-only selection; provenance, promotion, and recovery acceptance remain unaccepted.

Logical restore is data-only: roles, ownership, ACLs, and login credentials are not in the archive; their custody is separate.

The private Traefik Ingress is live and Argo-managed; the public Cloudflare route remains forbidden.
