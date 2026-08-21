# Requirements — k3s IaC foundation

## Discovery and safety

| ID | Requirement |
|---|---|
| KIF-001 | All host, cluster, and external discovery begins read-only and records curated, human-reviewed evidence before mutation; current host/cluster discovery is Ansible-first. |
| KIF-002 | Every mutating stage has explicit operator approval, a stop condition, and a rollback checkpoint. |
| KIF-003 | No disk format, namespace/PVC deletion, external destroy, secret export, or public cutover is used as an implicit setup or rollback step. |

## Repository and ownership

| ID | Requirement |
|---|---|
| KIF-004 | Future infrastructure source and runbooks live at repository-root `ansible/`, `opentofu/`, `kubernetes/`, and `runbooks/`; application source and local-runtime assets remain external. |
| KIF-005 | Ansible owns host configuration and is the selected bounded bootstrap installer for exact foundational Namespaces, the Infisical Cloud Kubernetes Operator, Argo CD, one self-hosted Keycloak, privileged CRDs/cluster RBAC, and Keycloak realm/client/group reconciliation; OpenTofu owns approved external resources; Argo CD owns namespaced desired state only after object-by-object handoff; Infisical Cloud owns secret values. Exact present-only source and a distinct guarded wrapper exist for `shared-services`; check, separately approved first apply, and separately approved idempotence passed, with final `changed=0`. Dedicated exact present-only `cristexhub-dev` and `cristexhub-prod` Namespace checkpoints are Active/idempotent; the DEV check passed at `ok=20 changed=1 unreachable=0 failed=0 skipped=2` before its approved apply. The PROD runtime seam apply and final idempotence passed at `ok=62 changed=0 failed=0 skipped=3`; the five-object PROD registration is live at the pinned revision with automated non-pruning sync, and private workloads are `Synced/Healthy`. Earlier source-only absence evidence is historical pre-checkpoint evidence. OpenTofu PROD route apply and MongoDB private acceptance remain separate open gates. Every component bootstrap requires its own exact source closure and approvals. Ansible must stop reconciling an object before registration/adoption/successful-sync evidence transfers it to Argo; dual reconciliation is forbidden. The completed `argocd`/`platform-edge` exception remains closed. |
| KIF-006 | The protective root `.gitignore` excludes the local `.venv`, Ansible collections/runtime data, generated state, plans, credentials, kubeconfigs, facts, local variable/override/crash files, and generated secrets, while `uv.lock` and `.terraform.lock.hcl` remain tracked. |

## Host and cluster

| ID | Requirement |
|---|---|
| KIF-007 | Ansible host changes are bounded, reviewable in check/diff mode, idempotent, and preserve SSH/Tailscale recovery access. |
| KIF-008 | The existing k3s datastore, exact Node kubelet version, CNI/interface indicators, NetworkPolicy objects, DNS, Traefik, StorageClass, disks, and resource capacity are discovered before design choices are applied; a separate source-only k3s datastore/encryption preflight may validate only fixed version/config/datastore/encryption stages and bounded service/Node health; CNI behavior, NetworkPolicy enforcement, and component compatibility require later approved evidence and are not inferred from object listings alone. |
| KIF-009 | Bundled k3s Traefik remains the sole ingress controller until an explicitly approved replacement migration. |

## Networking and exposure

| ID | Requirement |
|---|---|
| KIF-010 | DEV, SSH, k3s API, Argo CD, dashboards, databases, brokers, Keycloak administration/management, and other administrative endpoints remain private through Tailscale or explicit port-forwarding. |
| KIF-011 | Only an approved PROD application hostname and a separately approved stable Keycloak browser-authentication issuer may become public through Cloudflare Tunnel to Traefik; neither authorization permits direct WAN origin exposure or any identity administration/management path. |
| KIF-012 | Every exposure has positive route/auth tests and negative public-reachability tests for all private surfaces; a later Keycloak browser-authentication route requires separate approval, exact auth-path closure, direct-origin closure, rollback evidence, and proof that identity administration and management remain private. |

## Secrets and identity

| ID | Requirement |
|---|---|
| KIF-013 | Git, OpenTofu state/plans, Argo parameters, CI logs, examples, and documentation contain no plaintext runtime secret values. |
| KIF-014 | Infisical Cloud provides separate DEV, PROD, and infrastructure scopes/identities; the Kubernetes Operator is live in `shared-services`, and self-hosted Infisical remains deferred. The source-only database Secret seam remains a value-free blocked contract. The separate CristexHub PROD runtime seam is materialized at `/cristexhub/prod/runtime` with independent PROD Auth/Universal Auth names, exact nine-key runtime plus GHCR-pull targets, scoped VAP/bindings, and writer RBAC; apply and final idempotence passed at `ok=62 changed=0 failed=0 skipped=3`. Keycloak is a separate deployment in `shared-services`; it authenticates and emits groups, Argo RBAC authorizes Argo actions, and Kubernetes RBAC independently constrains controllers; direct Argo OIDC is selected with Dex absent. Residual MongoDB/RabbitMQ/GHCR credential rotation and MongoDB NetworkPolicy acceptance remain open. |
| KIF-015 | Bootstrap credentials, Keycloak administrator and OIDC client material, Infisical machine authentication, and application encryption keys have documented, off-node, tested recovery and rotation procedures. |

## Environment and data isolation

| ID | Requirement |
|---|---|
| KIF-016 | Committed source contains active `argocd`, cloudflared-only `platform-edge`, active `shared-services`, and active/idempotent `cristexhub-dev` and `cristexhub-prod`. The PROD runtime seam, Argo registration, and private application workloads are live/idempotent at the protected revision; public routing remains unapplied. `shared-services` is the placement for the Infisical Operator, separate Keycloak deployment, shared PostgreSQL, shared MongoDB, and shared RabbitMQ. MongoDB private ingress acceptance remains blocked by the absent/mismatched NetworkPolicy, and RabbitMQ least-privilege/recovery evidence remains open. The planned private DEV MVP reserves a future environment-local Reactive Resume deployment with its own OIDC/database/Secret scopes, but executable source and runtime remain blocked; future PROD remains separate. Applications retain separate DEV/PROD credentials, migrations, and backup paths. |
| KIF-017 | One general PostgreSQL engine provides separate CristexHub DEV, CristexHub PROD, Reactive Resume DEV, Reactive Resume PROD, and Keycloak logical databases, owner roles, Infisical-owned credentials, migration scopes, and backup scopes. No consumer receives a separate PostgreSQL deployment/PVC; `PUBLIC` connection/schema privileges are revoked where unwanted, every workload role is denied cross-database access, and workload roles cannot create databases or roles. |
| KIF-018 | One shared operator-managed MongoDB `8.0.12` engine provides the live DEV/PROD runtime boundary with TLS/SCRAM and retained storage. Database-scoped users, cross-database denial, backup/restore, and authoritative-data acceptance remain separate gates. Private ingress isolation is currently unproven because no NetworkPolicy selects `shared-mongodb-0` and legacy selectors do not match the live MongoDB or backend/Celery labels; no private MongoDB acceptance may be claimed until that policy and its positive/negative tests pass. |
| KIF-019 | Shared-engine failure and contention risks are documented. PostgreSQL and the operator-managed MongoDB runtime have retained single-node storage and private Services. MongoDB connection authorization, the NetworkPolicy gap, trust/recovery, cross-database negatives, and authoritative runtime acceptance remain blocked; no consumer receives a separate engine/PVC. |
| KIF-020 | Redis is environment-local. Exactly one live shared RabbitMQ engine belongs in `shared-services`; CristexHub DEV/PROD use dedicated vhosts and live workload credentials, and PROD Celery is connected and ready. The observed PROD principal/permission expressions require least-privilege reconciliation; definitions/queued-message recovery, measured RPO/RTO, and the exposed RabbitMQ credential rotation remain open. Future consumers require reviewed exact policy/test/runbook changes; wildcard or dynamic admission is forbidden. |
| KIF-021 | NetworkPolicy and RBAC deny unapproved cross-namespace and control-plane access while allowing required DNS and service flows. Infisical Secret VAPs are namespace-scoped and match only the exact Operator identity or reviewed target names; validation requires the Operator identity plus exact target contracts, preventing foreign target writers, unreviewed Operator names, and Argo/database cross-policy interference. |

## Delivery

| ID | Requirement |
|---|---|
| KIF-022 | The infrastructure repository has one SHA-pinned, read-only GitHub-hosted CI workflow for source validation only. Application CI validates backend, frontend, and code-runner; no current workflow can publish packages, read Secrets, contact infrastructure, or deploy. Argo CD alone reconciles reviewed Git desired state after handoff. |
| KIF-023 | Future CristexHub-owned publication requires reviewed immutable build inputs, exact commit/digest evidence, SBOM/provenance, collision handling, and recovery. Any future upstream Reactive Resume or platform image selection must use an accepted immutable digest rather than a rebuild or mutable tag; the current Reactive Resume digest is candidate-only and not selected, and workloads never deploy `latest`. |
| KIF-024 | A CristexHub-owned image is built once, its immutable digest is validated in DEV, and reviewed PROD promotion reuses that exact digest without rebuilding. |
| KIF-025 | DEV acceptance and soak preceded private PROD synchronization. Private PROD workloads are currently healthy, but full private acceptance remains blocked by the MongoDB NetworkPolicy gap and residual credential rotations; Cloudflare public cutover remains unapplied and must remain last. |

## Backup, recovery, and operations

| ID | Requirement |
|---|---|
| KIF-026 | Application-consistent encrypted backups are separated by service, environment, or identity purpose, retained locally and off-node, integrity checked, and copied without destructive mirror semantics; Keycloak uses `pg_dump`, not live-volume synchronization or realm export. Pinned host rclone `1.71.1` is the selected transfer-tool direction, but database paths, Drive identity, OAuth recovery, encryption-key recovery, jobs, retention enforcement, and runtime remain unapproved until exact source and isolated restore evidence exist. |
| KIF-027 | Private authenticated operators can list metadata, retrieve, verify, and restore predictable timestamped archives without public/anonymous links. An isolated restore proves the declared RPO/RTO before PROD acceptance; a successful backup exit code alone is insufficient. RabbitMQ definitions restore is distinct from queued-message reconciliation. |
| KIF-028 | Recovery covers k3s datastore/token, protected host-local single-writer OpenTofu state through encrypted timestamped off-node copies and independent key custody, Infisical bootstrap material, Keycloak database/realm/admin/OIDC material, application encryption keys, desired state, mutable application data, RabbitMQ definitions, and proof that non-authoritative queued work reconciles from application state. |
| KIF-029 | Resource headroom, disk usage, certificate/tunnel health, workload health, and backup freshness have bounded monitoring before public PROD. |
| KIF-030 | Every phase records actual commands/results, revisions/digests, residual risks, and rollback evidence without leaking sensitive values. |

## Traceability

`tasks.md` references these requirement IDs by stage. `testcases.md` maps every ID
to offline, integration, security, recovery, or manual evidence. The current
Ansible discovery satisfies its offline, syntax/lint, approved host-access,
dependency-bootstrap, curated host/cluster-indicator, and functional
CNI/NetworkPolicy enforcement gates. The separately approved schema-v3 discovery
captured kubelet `v1.36.2+k3s1`, all 15 bounded queries available, and the current
`shared-services` PVC query with count zero. Argo CD `3.5`'s official tested matrix
contains target minor `1.36`, chart `10.3.0` admits the target, the exact 44-document
render reproduced at Kubernetes capability `1.36.2`, stable upstream API registration
screened successfully, and controller-side image closure was reachable. Exact k3s
admission/runtime and node pullability remain unproven. The executed
[foundation Namespace bootstrap](../../runbooks/foundation-namespace-bootstrap.md)
maps KIF-002, KIF-005, KIF-006, KIF-010, KIF-016, and KIF-030 to exact present-only
source; check and separately approved first apply/idempotence passed, with the final
run converging at `changed=0`. The dedicated
[CristexHub DEV Namespace bootstrap](../../runbooks/cristexhub-dev-namespace-bootstrap.md)
maps KIF-002, KIF-005, KIF-006, KIF-010, KIF-016, KIF-025, and KIF-030 to one exact
source-ready Namespace with no PROD/policy/workload/Secret/PVC/route object. Its
check passed with one exact prediction and no mutation; first apply passed at
`ok=22 changed=1 unreachable=0 failed=0 skipped=0` with exact post-state/service
verification. Idempotence passed at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`;
the Namespace checkpoint is complete. The source-only
[Argo CD candidate provenance record](../../runbooks/argocd-candidate-provenance.md)
binds public chart, captured signature/hash-binding, image, online/static API, RBAC,
network, private-Git, and adoption evidence for KIF-005, KIF-008, KIF-010, KIF-013,
KIF-015, KIF-021, KIF-023, and KIF-030. The separate release record selects chart
`10.3.0` / app `v3.5.0` only for offline source authoring without closing trust,
security/Secret/adoption, admission, recovery, or runtime gates. The separate
[guarded Argo CD bootstrap](../../runbooks/argocd-hardened-design.md) maps private
exposure, stop/rollback, ownership, RBAC, policy, secret custody, and evidence to
KIF-002, KIF-003, KIF-005, KIF-008, KIF-010, KIF-013 through KIF-015, KIF-021,
and KIF-030. Its exact deployable source implements a 32-object private core,
ApplicationSet runtime absent, a deny-all default AppProject, supplemental
default-deny with a truthful broad ports-only weakness, disabled Redis initialization,
exact namespaced idle RBAC, three external Infisical-owned Secret contracts, and
Ansible bootstrap/privileged-CRD ownership. Secret materialization and recovery,
Infisical Universal Auth, live check/apply/readiness/idempotence, private TLS/login and
traffic evidence, future adoption Applications, live adoption mode, Git reconciliation,
OIDC activation, runtime acceptance, and handoff remain open. The source-only
[Keycloak OIDC bootstrap design](../../runbooks/keycloak-oidc-bootstrap-design.md)
maps KIF-002, KIF-003, KIF-005, KIF-010, KIF-012 through KIF-017, KIF-021, KIF-023,
and KIF-026 through KIF-030 to one future shared self-hosted identity architecture
target. It distinguishes Keycloak authentication/groups, Argo RBAC, and Kubernetes
RBAC; retains direct OIDC with Dex absent, private administration, Infisical-owned
client secrets, a dedicated Keycloak database/role on the shared PostgreSQL engine,
encrypted off-node backup/isolated restore, and object-by-object handoff. The release record selects Keycloak `26.7.1`,
PostgreSQL `17.10`, realm `cristexhub`, and stable issuer
`https://auth.cristex-soft.com/realms/cristexhub` only for offline source authoring.
The exact CristexHub DEV and PROD callbacks/origins are source-selected; Reactive
Resume/Argo callbacks and origins, trust/recovery, executable source, routes,
credentials, and runtime remain **NOT RUN/BLOCKED**. The value-free
[shared database architecture](../../runbooks/shared-database-architecture.md) maps
KIF-005, KIF-013, KIF-016 through KIF-019, KIF-021, and KIF-026 through KIF-030 to
an exact one-PostgreSQL/one-MongoDB source-only policy. It fixes the approved
storage/resource/private-Service/TLS/ownership/backup profile. Present-only,
hash-bound PostgreSQL and standalone MongoDB object closures now exist with guarded
PVC/drift checks and no-log cryptographic Secret validation, but they close no image
trust, Secret materialization, provisioning, restore, check/apply/idempotence, or
runtime gate. The value-free
[shared RabbitMQ architecture](../../runbooks/shared-rabbitmq-architecture.md) maps
KIF-005, KIF-013, KIF-016, KIF-019 through KIF-021, KIF-023, and KIF-026 through
KIF-030 to one exact source-only shared broker with DEV/PROD isolation and reviewed
future admission. The [shared backup architecture](../../runbooks/shared-stateful-backup-architecture.md)
maps KIF-005, KIF-013, KIF-017 through KIF-020, and KIF-026 through KIF-030 to
private operator catalog/retrieval, encrypted non-destructive copies, integrity, and
isolated restore semantics. Both leave images, identities, paths, schedules,
retention, RPO/RTO, executable source, and runtime blocked. The value-free
[Reactive Resume hosted architecture](../../runbooks/reactive-resume-hosted-architecture.md)
maps KIF-012 through KIF-017, KIF-019, KIF-021, KIF-023, and KIF-026 through KIF-030
to the private DEV MVP/future separate PROD direction without selecting an image,
callback, object, Secret, database runtime, or route. The SHA-pinned source-CI
workflow maps KIF-005, KIF-022 through KIF-025, and KIF-030 to local source
validation only; runner execution and publication remain separate evidence. The
source-only
[cloudflared candidate provenance record](../../runbooks/cloudflared-candidate-provenance.md)
binds exact release/source/image, token-file, health, and edge-transport evidence for
KIF-005, KIF-011, KIF-013, KIF-015, KIF-021, KIF-023, and KIF-030 while explicitly
leaving publisher trust, image assurance/availability, hardening, secret recovery,
external-resource state, policy, route, and runtime gates blocked. It selects no
version and adds no deployable source. The source-only
[Infisical Operator candidate provenance record](../../runbooks/infisical-operator-candidate-provenance.md)
binds the observed `v0.11.8` public distribution gap and the last observed
version-aligned `v0.11.7` chart/source/image evidence for KIF-005, KIF-013 through
KIF-015, KIF-021, KIF-023, and KIF-030. The release record selects `v0.11.7` only as
the offline source baseline and Universal Auth as direction, adds no deployable
controller source, and leaves chart/CRD/API compatibility despite the captured target,
trust, Namespace, scoped-RBAC, Argo handoff, secret-zero/recovery, traffic,
single-node, and runtime gates blocked. The inert
[Infisical privileged-prerequisites inventory](../../runbooks/infisical-operator-privileged-prerequisites-design.md)
maps KIF-005, KIF-013 through KIF-015, KIF-021, KIF-023, and KIF-030 to the exact
seven raw CRD templates, ownership boundaries, and known RBAC defects without adding
a valid Kubernetes or operational Ansible source. The
[Infisical implementation profile](../../runbooks/infisical-operator-implementation-profile.md)
binds the official controller commit as quarantined evidence and maps the confirmed
exact watch/separate-identity intent, metrics, ClusterGenerator, authenticated-proxy,
secret-zero, and ConfigMap-proof choices to KIF-005 and KIF-013 through KIF-016.
Foundation Namespace, source-audit, technical-profile, native same-Namespace
admission source, proxy image/config, and guarded deployable-source gates are now
evidenced by the exact 44-object, five-Namespace
[bootstrap closure](../../runbooks/infisical-operator-bootstrap.md). Its guarded
check/apply/post-check/idempotence passed; broader live admission, image behavior,
RBAC/traffic negatives, Universal Auth, and credential-bearing PROD runtime remain
closed. A separate
source-only [Infisical Argo CD Secret materialization seam](../../runbooks/infisical-argocd-secret-materialization.md)
now freezes one same-Namespace Universal Auth reference, fixed non-secret source
identifiers, exact orphaned targets, additive exact-name RBAC, and fail-closed
admission; credential/source creation, values, sync, check/apply, and runtime remain
closed. The [Argo](../../runbooks/argocd-release-selection.md),
[Infisical](../../runbooks/infisical-operator-release-selection.md), and
[Keycloak/PostgreSQL](../../runbooks/keycloak-release-selection.md) selection records
plus `ansible/files/policies/hosted-identity-authorization.yml` and
`ansible/files/policies/shared-database-architecture.yml`,
`ansible/files/policies/shared-rabbitmq-architecture.yml`,
`ansible/files/policies/shared-stateful-backup-architecture.yml`, and
`ansible/files/policies/reactive-resume-architecture.yml` map KIF-005,
KIF-010, and KIF-013 through KIF-015 to exact value-free offline inputs while
preserving every deployment and runtime gate. Exact
platform Namespace source and its bounded bootstrap pass offline contracts; the
separately approved wrapper check predicted exactly `argocd` and `platform-edge`
without mutation, and the separately approved first apply created and verified those
exact Active Namespaces with the reviewed labels and preserved service health. The
separately approved idempotence checkpoint had one credential failure before service
preflight or Kubernetes reconciliation (`changed=0`, no mutation), then passed on
retry at `ok=21 changed=0 unreachable=0 failed=0 skipped=0` with exact post-state and
service-health verification. The foundation does not satisfy replacement-host
recovery, general host-baseline, or later platform
mutation gates. Unresolved storage, secret bootstrap, and RPO/RTO
choices remain decision gates rather than implied requirements.

The guarded Argo CD source increment advances KIF-005, KIF-008, KIF-010,
KIF-013–KIF-015, KIF-021, KIF-023, and KIF-030 with an exact 32-object private
closure, immutable linux/amd64 image children, three precreated Infisical-owned Secret
metadata and cryptographic contracts, no committed Secret, no public Service/route,
namespaced idle RBAC, default-deny component flows, an empty-API check deferral,
Established-CRD apply ordering, a canonical hash-bound present-only mutation path,
and explicit blocked live/recovery gates. It does not close runtime acceptance.
