# Keycloak OIDC bootstrap design

## Status and boundary

**SOURCE POLICY SELECTED — EXISTING PRIVATE WORKLOAD; DEV SUCCESSOR SOURCE-ONLY.**
The shared self-hosted Keycloak workload is an existing private runtime checkpoint.
Keycloak `26.7.1`, PostgreSQL `17.10`, the retained PROD-compatibility realm
`cristexhub`, and issuer `https://auth.cristex-soft.com/realms/cristexhub` remain
canonical. The exact release identities are recorded in the [Keycloak release
selection](keycloak-release-selection.md). A separate source-only DEV successor
contract now defines realm `cristexhub-dev` and issuer
`https://auth.cristex-soft.com/realms/cristexhub-dev`; it has no runtime activation.

The DEV successor lane authorizes only offline source validation. It performs no
Admin API request and authorizes no apply, Secret operation, database mutation,
route change, application cutover, or cluster mutation. The next transition source
closure defines a blocked strict-TLS controller-local Kubernetes API port-forward,
dedicated one-time bootstrap and FGAP V2 realm-scoped reconciler actor contracts,
four separated Infisical value paths with CAS semantics still unverified, and a
future phase-specific API allowlist; all remain apply-blocked. No public hostname
is an Admin REST transport. The existing
workload closure remains separately owned by Ansible until any future handoff.
Argo CD chart `10.3.0` / app `v3.5.0` and Infisical Operator `v0.11.7` retain their
independent source and runtime boundaries.

## Bounded bootstrap ownership

Ansible is selected as the future bounded bootstrap installer for foundational
Namespaces, the Infisical Cloud Kubernetes Operator, Argo CD, Keycloak, and their
privileged cluster-scoped prerequisites. Each component requires a separate exact
source closure, dedicated non-passthrough entrypoint, reviewed check/diff, separately
approved apply, and separately approved idempotence checkpoint. The existing workload
closure is separate; the DEV successor adds only its dedicated check-only source lane
and grants no runtime or apply approval.

Ansible remains lifecycle owner of foundation CRDs, ClusterRoles,
ClusterRoleBindings, and Keycloak realm, client, group, and group-claim
reconciliation unless a later explicit ownership decision replaces it. Ansible may
bootstrap namespaced workload specifications, but a specification can hand off to
Argo only after its exact writer is stopped, the object is registered or adopted,
and successful sync plus managed-field evidence passes. Ansible and Argo must never
reconcile the same object concurrently.

The previously completed `argocd` and `platform-edge` Namespace exception remains
closed. The DEV successor realm/client/group/mapper source and its check-only
wrapper are documented in [the DEV realm migration runbook](keycloak-dev-realm-migration.md);
they preserve `cristexhub` as retained PROD compatibility state and do not imply a
runtime transition. `shared-services` now exists through its distinct bounded Ansible wrapper;
check and separately approved first apply/idempotence passed, with the final run at
`changed=0`. The superseded `platform-secrets` and
`platform-identity` source was never run; its removal is not a live deletion. The old
historical wrapper is unchanged and must not be reused or reopened.

## Authentication and authorization layers

The three enforcement layers remain independent:

| Layer | Responsibility | Fail-closed direction |
|---|---|---|
| Keycloak | Authenticate people and emit reviewed group claims | No group implies no Argo access |
| Argo CD RBAC | Map exact Keycloak groups to Argo administrator or read-only capabilities | No default privilege and no wildcard group mapping |
| Kubernetes RBAC | Limit Argo ServiceAccounts to the exact cluster and namespaced operations they require | Equal to or narrower than Argo Project policy |

A Keycloak administrator group never implies Kubernetes administrator access. Direct
Argo OIDC is the selected direction and Dex remains absent. The value-free hosted policy fixes `argocd-admin`, `argocd-readonly`, and an
ungrouped deny default. Read-only is limited to application/project get for the exact
reviewed project set and receives no logs, sync, action, override, delete, exec, or
configuration mutation. These mappings still require positive and negative runtime
acceptance. The OIDC client secret is an Infisical-owned value and is never
stored in Git, Ansible variables, OpenTofu state, Argo parameters, examples, or logs.

Local Argo authentication is one-time bootstrap and independently recoverable
break-glass access only. Routine local authentication may be disabled only after
OIDC administrator access, read-only mutation denial, ungrouped denial, invalid and
expired token denial, logout behavior, and break-glass recovery all pass.

## Hosted client, group, and Namespace policy

The exact value-free policy source is
`ansible/files/policies/hosted-identity-authorization.yml`. It is neither a realm
import nor a Kubernetes object. Client IDs are `cristexhub-dev`, `cristexhub-prod`,
`reactive-resume-dev`, `reactive-resume-prod`, `argocd`,
`cristexhub-admin-svc-dev`, and `cristexhub-admin-svc-prod`.

The CristexHub browser contracts are selected. Legacy DEV and private PROD
consumers are live on the retained realm; the DEV successor remains unactivated.
DEV remains bound to `https://dev-hub.cristex-soft.com` and PROD is bound only to
`https://hub.cristex-soft.com`. The `cristexhub-prod` client is confidential, uses
PKCE `S256`, and permits exactly this callback:
`https://hub.cristex-soft.com/oauth2/callback`. Its only web origin is
`https://hub.cristex-soft.com` and its only post-logout redirect is
`https://hub.cristex-soft.com/`. The client secret is an Infisical-owned value at
`prod:/cristexhub/prod/runtime`, represented only by the key name
`OIDC_CLIENT_SECRET`, which is the same source/key projected by the PROD runtime
StaticSecret; no value is present here. Reactive Resume and
Argo CD browser clients remain inactive until their own exact private callbacks and
origins are selected; no hostname or route is invented.

The per-client group authorization contract is explicit and environment-bound:

| Client | Accepted tenant-role form | Accepted super-administrator form | Rejected forms |
|---|---|---|---|
| `cristexhub-dev` | `cristexhub-dev-<organization-alias>-<role>` with only `admin`, `hr`, `viewer`, or `interviewer` | `cristexhub-dev-super-admin` | Every `cristexhub-prod-*` group, every unmatched form, and missing/ambiguous groups |
| `cristexhub-prod` | `cristexhub-prod-<organization-alias>-<role>` with only `admin`, `hr`, `viewer`, or `interviewer` | `cristexhub-prod-super-admin` | Every `cristexhub-dev-*` group, every unmatched form, and missing/ambiguous groups |

The PROD client is environment-bound to the exact role-group template
`cristexhub-prod-<organization-alias>-<role>` and super-administrator group
`cristexhub-prod-super-admin`; DEV uses the corresponding exact
`cristexhub-dev-<organization-alias>-<role>` and
`cristexhub-dev-super-admin` forms. The claims contract emits roles from `groups`
and organizations from `organization`, requires `sub`, `email`, `email_verified`,
and `preferred_username`, and does not use full group paths. Missing, unverified,
ambiguous, unmatched, or cross-environment group claims fail closed; the policy's
canonical missing/ambiguous decision is `deny`. The application owns dynamic
Organizations, memberships, and organization role groups; Ansible owns static
realm settings, client/mappers, and the static Argo groups.

Namespace trust is explicit: `platform-edge` is reserved for cloudflared only;
`shared-services` contains the Infisical Cloud Operator, a separate Keycloak
deployment, one general PostgreSQL engine, and one shared MongoDB engine; `argocd`
receives only its
materialized OIDC client value; and `cristexhub-dev` and `cristexhub-prod` receive
only their own environment identities. Keycloak receives a dedicated logical
database, dedicated owner role, and dedicated credential values inside that shared
PostgreSQL engine. DEV and PROD credentials must never cross. Selecting the PROD
browser contract does not create or activate `cristexhub-prod`, publish a route, or
change the private DEV boundary. The two administrative service clients remain
`browser_flow_allowed: false`; Keycloak administration, management, health, and
metrics remain private.

## External application-asset boundary

The existing CristexHub Compose Keycloak, realm export, theme, local issuer, local
redirects, development users, development passwords, and bootstrap defaults remain
external development-only inputs in the application repository. They are not hosted
source and must not be copied here. The future production realm may reuse reviewed
identity intent and independently built theme source only after credentials and
local-only configuration are removed, an immutable image is published, and exact
compatibility is proven.

Development startup, an embedded development database, mutable image tags, wildcard
redirects or origins, disabled TLS requirements, and default administrator
credentials are forbidden.

## Production Keycloak and database gates

The live Keycloak `26.7.1` workload uses the immutable CristexHub-derived digest
recorded in its Deployment and production startup, never `start-dev`. The official
linux/amd64 digest
`sha256:7523ccfbd950f59783504cdf5a0138dae48746dfe36075bbfccdb5a9ee245ee2`
remains upstream selection evidence rather than the live image identity. Any image
replacement requires separate publisher trust, SBOM/vulnerability disposition,
off-node recovery, node pullability, and rollout approval. One replica on one node
is explicitly not high availability.

Keycloak requires PostgreSQL `17.10` at linux/amd64 child digest
`sha256:dbbeb22a65db2503050cdbbe5e78f017478f10a1002a226463f049dbb017e99b`,
a dedicated logical database and dedicated owner role on the one general shared
PostgreSQL instance. The canonical value-free consumer/isolation contract is
[`shared-database-architecture.yml`](../ansible/files/policies/shared-database-architecture.yml);
Keycloak has no MongoDB consumer scope. Keycloak remains a separate deployment from PostgreSQL. No
separate Keycloak PostgreSQL deployment or PVC is selected; the shared engine and
PVC remain a shared failure domain. The database version is supported by the selected Keycloak release. Encrypted
application-consistent backup, immutable off-node readback, and isolated restore
have runtime evidence; realm/client/admin behavioral recovery, role/ownership
restoration, measured RPO/RTO, and full production recovery acceptance remain open.
Before any identity migration or authoritative recovery claim, the design requires:

- application-consistent `pg_dump` backup rather than live-volume synchronization;
- encryption and independently recoverable key custody;
- timestamped non-destructive off-node copy;
- integrity verification and retention policy;
- an isolated restore rehearsal covering database, roles, controlled test realm
  state, and clients;
- declared and measured RPO/RTO; and
- a pre-upgrade backup because startup schema migration makes downgrade an unsafe
  routine rollback assumption.

StorageClass, placement, capacity, backup identity, backup destination, database TLS,
connection limits, migration sequencing, and recovery custodians remain unresolved.
The Keycloak role cannot access application databases, and application roles cannot
access the Keycloak database; negative grant tests are mandatory. The Keycloak role
must not create databases or roles. PVC deletion, database recreation, realm
re-import, and release downgrade are never routine rollback.

## Stable issuer and private-first exposure

The selected production issuer,
`https://auth.cristex-soft.com/realms/cristexhub`, is the one stable TLS identity from
the first accepted login. Every callback, certificate, DNS, proxy-header trust, and
Traefik configuration must use it. A
session-local or development issuer cannot later be substituted without token and
client breakage. The CristexHub PROD callback is the exact
`https://hub.cristex-soft.com/oauth2/callback` contract above, while DEV uses its
separate exact callback. The Argo callback must match the future private
administration URL exactly, and Reactive Resume receives a separate exact client
and callback when that contract is selected.

The existing reviewed browser-auth route and DEV application route are live.
Keycloak administration and its management health/metrics surface remain private.
The management listener receives no public Service, Ingress, Tunnel route, or public
DNS route, and Traefik remains the sole ingress controller. The new DEV successor
realm path is not created or separately activated by this source-only contract.

The `hub.cristex-soft.com` PROD application route remains unapplied and requires its
own Cloudflare plan/apply, positive login tests, negative administration/management
reachability tests, and rollback evidence. Public authentication never makes the admin console, management
listener, database, Argo CD, k3s API, or host publicly reachable.

## Network-policy direction

A future default-deny design must prove only these classes of traffic:

| Flow | Purpose |
|---|---|
| reviewed browser or private operator path to Keycloak application listener | Authentication only |
| Keycloak to the general PostgreSQL Service using only its dedicated database and role | Identity-state persistence |
| Keycloak and approved OIDC clients to CoreDNS | Name resolution |
| Argo server to selected stable OIDC issuer | Discovery, authorization-code exchange, and key retrieval |
| approved application gateways to selected stable OIDC issuer | Application SSO |
| approved internal administration client to exact Keycloak administration surface | Bounded realm/client/group reconciliation |

The Keycloak database accepts only the dedicated Keycloak role and bounded
backup/restore identities; application database roles are denied. The Keycloak
management listener accepts only exact private probes and approved monitoring after
its labels and ports are verified. Egress to arbitrary destinations, public
administration, direct database exposure, cross-environment identity credentials,
and a second ingress controller remain denied. Exact labels, ports, Service
translation behavior, DNS peers, TLS identity, and positive/negative policy tests
remain future evidence.

## Secret-zero and recovery

Infisical Cloud remains the secret-value owner; only its Kubernetes Operator is in
the bootstrap scope. Self-hosted Infisical is not selected. Universal Auth is the
selected bootstrap direction. Its machine identity and credential values have
separate out-of-band, encrypted, off-node custody and cannot depend only on the
operator they unlock.

Infisical eventually owns Keycloak database credentials, bootstrap-administrator
successor material, Argo OIDC client secret, application OIDC client secrets, TLS
material, and any approved service-account credential. A bounded temporary writer
may create one exact predecessor at a time only under separate Secret approval. The
successor must pass fresh behavior, scope, disclosure, rotation, and recovery checks
before separately approved predecessor revocation.

Realm exports are configuration aids, not database backups. Recovery must restore the
database and independently recover Infisical bootstrap access, administrator
break-glass material, OIDC client credentials, TLS keys, and the exact reviewed
Ansible realm/client/group reconciliation source.

## Non-circular bootstrap sequence

The remaining sequence is fixed but this design authorizes no additional step:

1. completed foundation checkpoint: the bounded Ansible exception created only the
   separately approved `shared-services` Namespace;
2. Ansible bootstraps the selected Infisical Cloud Kubernetes Operator, followed by
   separate secret-zero injection and one non-sensitive sync, rotation, revocation,
   and recovery proof;
3. Infisical materializes the exact precreated Argo Secrets and Ansible performs the
   separately approved hardened Argo bootstrap;
4. private Argo readiness and one-time local break-glass administration pass;
5. Keycloak image, PostgreSQL/storage, backup tooling/destination/key custody,
   provisional RPO/RTO, stable-issuer, and private-exposure gates pass before a
   separately approved private, non-authoritative Ansible bootstrap creates only
   controlled test identity state;
6. that test state is dumped, encrypted, copied off-node, integrity checked, and
   restored in isolation with measured RPO/RTO before authoritative identity state
   is accepted or OIDC is enabled;
7. direct OIDC and the administrator, read-only, ungrouped, invalid-token, logout,
   and recovery cases pass; and
8. namespaced specifications hand off one exact object set at a time only after
   Ansible reconciliation stops and Argo adoption/sync evidence passes.

No phase may infer approval for the next. No visual placeholder, ephemeral Keycloak,
development database, or temporary public route is acceptable.

## Stop and rollback

Stop on secret disclosure, development configuration, mutable or unverified image,
unsupported database, missing backup or restore evidence, unstable issuer, callback
mismatch, public administration, unexpected object or writer, wildcard identity
mapping, default Argo privilege, dual reconciliation, failed negative authorization,
failed recovery, or unreviewed database migration.

The DEV successor lane rolls back only by Git revert before any approved transition.
It has no runtime rollback because its check-only phase performs no write. Existing
Keycloak workload rollback remains governed by its separate runtime evidence and
backup procedure. Future identity rollback preserves PVCs and database backups,
stops traffic before mutation, restores only a verified compatible database
backup, and keeps a working predecessor credential until successor acceptance.

## Open decisions

- Keycloak and PostgreSQL image trust, SBOM/vulnerability disposition, and off-node
  OCI recovery for the selected children;
- storage placement, resource budget, backup identity, retention, and RPO/RTO;
- Reactive Resume and Argo client callbacks/origins, TLS source, proxy trust, and
  the later browser-auth route for the selected stable issuer (the CristexHub DEV
  and PROD callback/origin contracts are source-selected above);
- completed foundation Namespace check/first-apply/idempotence evidence;
- Infisical Operator scoped RBAC, Universal Auth recovery, and exact target scope;
- exact realm/client reconciliation implementation and runtime negative tests for
  the selected group/RBAC policy; and
- exact object-by-object Ansible-to-Argo handoff inventory and field ownership.

Until these decisions and the dedicated successor transition approvals exist, the
DEV successor remains source-only and no new realm identity is installed or activated
by this design.
