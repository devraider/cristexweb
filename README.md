# Cristex infrastructure

## Current live checkpoint — 2026-08-21

Private CristexHub PROD activation is live at the pinned revision
`751885a42798d282e168131db147f13694a0a621`: Argo reports `Synced/Healthy`,
backend/Celery/frontend/oauth2-proxy/Redis are each `1/1 Ready`, backend root
returns `200`, oauth2-proxy returns the expected private `302`, and Celery is ready
on the PROD RabbitMQ vhost. The guarded OIDC CONNECT proxy policy includes PROD
clients and app-level `200`/`302` smoke passed; authenticated OIDC/callback and live
positive/negative CONNECT validation remain open.

The shared MongoDB engine is live as operator-managed MongoDB `8.0.12` with
TLS/SCRAM, but **private PROD acceptance is blocked**: no NetworkPolicy currently
selects the live MongoDB pod and the legacy selectors do not match the live MongoDB
or backend/Celery labels. RabbitMQ is live, but its observed PROD principal and
broad permission expressions require least-privilege reconciliation; its exposed
credential, the MongoDB credential, and the reused GHCR pull credential require
verified rotation before public cutover. The exposed DeepSeek key also remains a
separate revoke/replace residual.

OpenTofu now manages the imported Cloudflare Tunnel and existing Keycloak/DEV DNS
routes from protected host state with encrypted backup/readback and isolated restore
evidence. The PROD Tunnel-ingress/DNS definitions are committed but unapplied because
the available OAuth credential lacks DNS-record permission; `hub.cristex-soft.com`
therefore remains unresolved. Historical source-only checkpoints below are retained
as evidence and are explicitly not current-state claims.

## Historical source-only/checkpoint evidence

The repository's bounded Ansible implementation contains discovery, the executed
two-package module bootstrap, an executed group-scoped k3s administrator access
playbook, an executed non-destructive storage-discovery increment, and an
executed temporary CNI/NetworkPolicy functional probe under
[`ansible/`](ansible/). The separately approved extended storage discovery and
functional probe both passed against the live host/cluster. The probe ran
with an independently verified digest-qualified linux/amd64 image and temporary Argo
ownership exception. The probe never creates or deletes a Namespace; generated names, two fixed ownership
labels, private mode-`0600` ledger recovery, fixed-kind read-only rediscovery, exact
UID preconditions, non-cascading `Orphan` deletion, and an `always` cleanup path
bound every temporary object. Effective-user readability,
fresh-session cluster listing, and second-run idempotence have passed. The executed
user-scoped client-defaults playbook removes k3s multicall warnings without exposing
server configuration. The separately approved one-reboot recovery playbook passed
with SSH/Tailscale return, running services, a Ready node, and preserved access.
Discovery gathers curated host indicators with built-ins and exact Kubernetes
kinds with `kubernetes.core.k8s_info`. The separately approved schema-v3 elevated
read-only rerun passed and projects only the existing curated Node name/cluster
scope and kubelet `v1.36.2+k3s1`; all 15 bounded queries were available and the exact
`shared-services` PVC query returned zero objects. A gated Ansible
playbook pins the OpenTofu CLI. Its
approved host check passed at `ok=27 changed=6 failed=0`; the first live attempt
stopped at `ok=21 changed=2 failed=1` because the host had no route to GitHub, after
creating only exact parent directories and the empty protected state directory. The
reviewed controller-transfer check then passed at `ok=33 changed=6 failed=0`, the
live recovery installed the verified CLI at `ok=39 changed=6 failed=0`, and the
second run converged at `ok=30 changed=0 failed=0` without requiring host egress.
At that historical installer checkpoint the protected state directory remained
empty and no provider operation had run. Later separately approved import, backup,
readback, restore, and existing-route management checkpoints supersede that absence
evidence. The committed PROD route alone remains unapplied. Committed Kubernetes
source contains exactly five Namespace manifests: `argocd`, `platform-edge`, `shared-services`, live
`cristexhub-dev`, and live `cristexhub-prod`; the PROD Namespace, credential seam,
Argo registration, and private workloads are active/idempotent, while public PROD
routing remains unapplied. The
MongoDB
operator control plane runs in the separately created live `mongodb-system` Namespace and watches the MongoDB runtime retained in `shared-services`. The historical
`argocd`/`platform-edge` wrapper check, first apply, and idempotence retry completed
under separate approvals and that exception remains closed. Exact present-only
source and a new dedicated guarded wrapper now exist for `shared-services`. After a
non-interactive missing-sudo stop (`ok=10 changed=0 failed=1`), the interactive check
passed at `ok=20 changed=1 failed=0` and predicted exactly that one Namespace without
mutation. The separately approved first apply passed at `ok=22 changed=1 failed=0`,
created and verified exact labels/`Active`, and preserved k3s/Tailscale health.
The separately approved idempotence apply passed at
`ok=22 changed=0 unreachable=0 failed=0 skipped=0`; the exact Namespace checkpoint is
complete. Dedicated [CristexHub DEV Namespace source](runbooks/cristexhub-dev-namespace-bootstrap.md)
is present-only and fail-closed. Its separately approved check passed at
`ok=20 changed=1 unreachable=0 failed=0 skipped=2`, predicting only that Namespace
without mutation. The first apply passed at
`ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created/verified the exact
Namespace and preserved k3s/Tailscale health. Idempotence passed at
`ok=22 changed=0 unreachable=0 failed=0 skipped=0`; the DEV Namespace checkpoint is
complete. The separately approved PROD Namespace checkpoint is now `Active` and
idempotent; the earlier pre-checkpoint source-only absence evidence is historical.
A separate source-only, fail-closed
[CristexHub PROD runtime Infisical seam](runbooks/infisical-cristexhub-prod-runtime-materialization.md)
now freezes the exact `/cristexhub/prod/runtime` source, independent PROD Auth and
Universal Auth names, a ten-key source `cristexhub-prod-runtime` plus separate
`cristexhub-prod-ghcr-pull` targets, exact PROD-scoped admission, additive
least-privilege writer RBAC, manifest/action hashes, and guarded check/apply source.
**Historical pre-activation checkpoint (superseded):** the PROD Namespace was
complete while Universal Auth values, runtime-seam apply, sync, Secret targets, and
workloads were still absent. The fixed Infisical `prod` slug remains only a Cloud
environment identifier. A separate guarded
[CristexHub PROD Argo registration](runbooks/cristexhub-prod-argocd-registration.md)
source now pins the protected-main application revision
`751885a42798d282e168131db147f13694a0a621` in a five-object, namespaced,
historical manual-sync closure. That pre-activation state is superseded by the
current private PROD registration and automated non-pruning sync recorded in
`AGENTS.md`; it never implied public-route activation.
The superseded `platform-secrets`/`platform-identity` source was never run; removing
it does not claim a live rename or deletion. Runtime checkpoint history remains recorded in `AGENTS.md` and the component
runbooks; this source-only increment performs no runtime action. The live
`cristexhub-prod` Namespace, runtime Secrets, registration, and private workload are
now live/idempotent; only its public Cloudflare route remains absent. The source-selection paragraphs below preserve
historical pre-runtime absence checkpoints and must not be read as current Namespace
absence evidence; `AGENTS.md` is authoritative for completed runtime checkpoints. The Argo CD candidate and release
records bind chart
`10.3.0`, app `v3.5.0`, provenance, and exact linux/amd64 image children. The
[guarded Argo CD bootstrap](runbooks/argocd-hardened-design.md) now promotes an exact
32-object committed-manifest closure: three Ansible-owned CRDs plus a deny-all default
AppProject and a private minimal controller/repo-server/server/standalone-Redis core. ApplicationSet runtime, Dex,
notifications, commit server, cluster RBAC, public exposure, PVCs, metrics Services,
hooks, and Secret objects are absent. The source requires exact precreated
Infisical-owned `argocd-secret`, `argocd-redis`, and `argocd-server-tls` metadata and
cryptographic contracts and refuses `argocd-initial-admin-secret`. Its non-passthrough
`check|apply` wrapper validates an empty-API check without resolving the absent
AppProject GVK and waits for Established CRDs on apply. It is source-ready but no live check/apply/idempotence or runtime proof has occurred.
Admission, node pulls, private TLS/login, NetworkPolicy positives/negatives, recovery,
and later Git reconciliation remain blocked. The companion
[Keycloak OIDC bootstrap design](runbooks/keycloak-oidc-bootstrap-design.md) and
[release selection](runbooks/keycloak-release-selection.md) retain the private
Keycloak `26.7.1` workload, PostgreSQL `17.10`, PROD-compatibility realm
`cristexhub`, and issuer `https://auth.cristex-soft.com/realms/cristexhub`.
The separate [DEV successor realm runbook](runbooks/keycloak-dev-realm-migration.md)
defines the value-free, check-only `cristexhub-dev` source lane; no DEV realm or
application cutover is implied. The value-free hosted policy selects exact client IDs, environment role templates,
Argo groups, deny-default authorization, Namespace trust, and Universal Auth
direction. The separate [shared database architecture](runbooks/shared-database-architecture.md)
freezes one PostgreSQL and one MongoDB engine in `shared-services`: CristexHub
DEV/PROD receive isolated scopes on both engines, while Reactive Resume DEV/PROD and
Keycloak receive dedicated PostgreSQL scopes. Infisical owns credential values,
exposure is private-only, and promotion gates remain closed. The
[shared RabbitMQ architecture](runbooks/shared-rabbitmq-architecture.md) fixes one
future broker with exact isolated DEV/PROD scopes and reviewed future-consumer
admission. The [shared backup architecture](runbooks/shared-stateful-backup-architecture.md)
requires private authenticated catalog/retrieval, encrypted timestamped archives,
non-destructive off-node copy, integrity checks, and isolated restore. Both remain
source-ready for PostgreSQL and standalone MongoDB but runtime-blocked; the RabbitMQ
and backup implementations remain policy-only. The separate [Reactive Resume hosted architecture](runbooks/reactive-resume-hosted-architecture.md)
includes only a planned private DEV workload reservation. Broad-lane DEV and
unapproved PROD PostgreSQL CRs plus Infisical-owned Secrets are already live but
unaccepted; roles retain `INHERIT`, no NetworkPolicy selects shared PostgreSQL, and
review-log exposure requires credential rotation/revocation. A dedicated source-only
rotation contract now freezes exact scope/no-output/stop semantics but remains
non-executable because Infisical documents no CAS. CNPG documents `basic-auth`,
while its pinned controller accepts the live key-correct `Opaque` targets; that
normalization drift is separate from rotation. Dedicated DEV-only Infisical/VAP/RBAC and PostgreSQL lanes, realm/issuer/callback/claims, accepted image,
durable private object storage, application-key custody, disabled v5 Agent/Redis,
patched OIDC, locked split-role migration, backup/restore, RPO/RTO,
NetworkPolicy/TLS identity, and runtime remain blocked; PROD is reservation-only and
public exposure is forbidden.
PostgreSQL and standalone MongoDB now have hash-bound present-only source closures
with retained 40/80 GiB PVCs, bounded resources, private standard Services,
mandatory TLS/authentication, exact cryptographic Secret validation, and guarded
readiness. Image trust/pullability, Secret materialization, provisioning, logical
authorization, backup/restore, recovery, check/apply/idempotence, and all runtime
acceptance remain blocked. No workload, Secret, route, or runtime is approved.
A separate
[source-only cloudflared provenance record](runbooks/cloudflared-candidate-provenance.md)
binds the selected official release, unsigned source, immutable linux/amd64 image,
token-file, health, and edge-transport evidence. Reviewed cloudflared and Infisical
token-materialization source closures now exist, but runtime is **NOT RUN/BLOCKED**;
no Secret value, Kubernetes object, Cloudflare resource, DNS record, route, or
deployment has been applied. A third
[source-only Infisical Operator candidate provenance record](runbooks/infisical-operator-candidate-provenance.md)
distinguishes the incomplete public `v0.11.8` distribution observation from the
version-aligned `v0.11.7` set. The separate
[release selection](runbooks/infisical-operator-release-selection.md) selects
`v0.11.7` only for offline source authoring and Universal Auth as direction. The
[inert privileged-prerequisites inventory](runbooks/infisical-operator-privileged-prerequisites-design.md)
binds the seven raw CRD templates and known RBAC/scoping defects to the vendored
archive. The [implementation profile](runbooks/infisical-operator-implementation-profile.md)
binds the official controller commit and selected security profile. The guarded
[idle bootstrap closure](runbooks/infisical-operator-bootstrap.md) now promotes an
exact 44-object source closure: six namespaced CRDs, six fail-closed admission
policies and bindings, exact five-Namespace RBAC, one metrics-off digest-pinned
controller, one authenticated TLS Squid proxy, and eight NetworkPolicies. The
quarantined archive is never a runtime input. The three recovered proxy Secrets and
the historical 40-object checkpoint passed; the later 42-object source was not
separately applied. The current 44-object expansion passed check/apply/post-check/
idempotence at `ok=30 changed=1`, `ok=35 changed=1`, `ok=30 changed=0`, and
`ok=35 changed=0`. Broader admission/RBAC/traffic acceptance remains pending. The first local age/Drive writer attempt stopped before Kubernetes on expired
Drive OAuth; its plaintext residue and unused encrypted artifact were removed without
reading values. An unused debug-exposed age identity was revoked/regenerated before
upload/Kubernetes. The hardened retry proved cleanup, encrypted-pending resume and a
Keychain copy, confirmed zero Kubernetes Secrets, then stopped on the same expired
controller OAuth. That transfer path is superseded: guarded host transfer/readback and exact
`drive-verified` now pass; exactly three proxy bootstrap Secrets exist. The historical
runtime checkpoint applied exactly 40 Infisical Operator/proxy objects and its
idempotence converged. The later 42-object source was not separately runtime-applied;
the 44-object, five-Namespace PROD expansion is now applied/idempotent. It created no
Infisical CR, Universal Auth value, application/database Secret, application workload,
or route. No other application PROD scope or self-hosted Infisical server exists at
runtime. The fixed
Infisical Cloud environment slug `prod` is only a licensing-constrained source
identifier and does not activate any of those PROD scopes. A separate source-only
[Infisical Argo CD Secret materialization seam](runbooks/infisical-argocd-secret-materialization.md)
freezes one same-Namespace Universal Auth reference, one Connection/Auth/StaticSecret
closure, exactly three orphaned Argo Secret targets, additive exact-name Secret and
workload-list RBAC, and fail-closed admission. Its credential Secret, check/apply,
sync, target values, and runtime remain **NOT RUN/BLOCKED**. A separate source-only
[Infisical database Secret materialization seam](runbooks/infisical-database-secret-materialization.md)
freezes one shared Connection, separate PostgreSQL/MongoDB Universal Auth references,
two StaticSecrets, four stateful-database target contracts, scoped fail-closed VAPs,
and additive writer RBAC. Its credential Secrets, check/apply, sync, values, and
runtime remain **NOT RUN/BLOCKED**. The separate source-only
[CristexHub PROD runtime seam](runbooks/infisical-cristexhub-prod-runtime-materialization.md)
freezes the exact `/cristexhub/prod/runtime` source, independent PROD identity,
ten-key source runtime plus `cristexhub-prod-ghcr-pull` target, exact Namespace-scoped
VAPs, least-privilege RBAC, hashes, and guarded check/apply source. The prior nine-key
target remains live; the ten-key update is **NOT RUN/BLOCKED**. Its Namespace,
Universal Auth values, sync, targets, workload, and promotion remain **NOT RUN/BLOCKED**.
A separate source-only
[Universal Auth/value lane](runbooks/infisical-universal-auth-value-lane.md) accepts
protected file inputs only and keeps values out of Git, argv, environment, logs, and
evidence. Separate guarded [logical database provisioning](runbooks/shared-database-provisioning.md)
consumes precreated per-consumer Secrets through temporary UID-bound helper Pods;
all empty reservations and PROD activation remain **NOT RUN/BLOCKED**. No general
host baseline or deployment exists.
Python is otherwise test-only; thirty-two exact-scope Ansible action plugins are
the reviewed focused exception—ten enforce canonical Namespace and
Infisical/Argo/database/CristexHub DEV/PROD Secret/seam/Universal Auth mutation
boundaries, two guard host rclone install/transfer, two perform no-log cryptographic
validation of exact Argo and stateful-database Secret contracts, five guard the
standalone MongoDB, PostgreSQL, Keycloak, RabbitMQ, and OIDC CONNECT proxy object
closures, four guard cloudflared/route closures, four guard CoreDNS/DEV/PROD
registration/sync boundaries, two guard fixed temporary logical-provisioning
execution/Kubernetes objects, one guards the dedicated shared-MongoDB NetworkPolicy
closure, and two guard the source-only Keycloak DEV successor identity and
transport/actor/Infisical-CAS/API transition contracts. No general-purpose
operational Python or infrastructure collector exists.

Approved non-elevated and extended elevated check/diff runs produced the ignored
local report. The extended report confirms the unmounted 1 TB rotational disk,
NVMe/root capacity, local-path behavior, and zero current PV/PVC objects without
identifying the unmounted filesystem or touching disk contents. That historical
live report queried `shared-data` as its fifth PVC scope and did not capture a
Kubernetes version. The approved schema-v3 rerun instead queried `shared-services`
and projected `status.nodeInfo.kubeletVersion` from the existing exact Node query.
Human review confirmed Kubernetes minor `1.36`; Argo CD `3.5` lists that minor in
its official tested matrix and chart `10.3.0` admits the exact target through its
semver gate. This is only target-minor screening, not k3s-specific runtime, rendered
API/CRD, trust, selection, or deployment evidence. An earlier
approved elevated attempt identified missing remote Python dependencies. The
bounded two-package Ansible bootstrap was reviewed and installed; post-install
imports and the prior nine exact Kubernetes queries pass. That report confirms the
k3s datastore and curated cluster indicators; it predates the extended StorageClass,
PV, and namespace-bounded PVC projection. Hosted application runtime and the future public PROD route were outside that
historical report. OpenTofu now has five imported protected state resources and
completed backup/readback/restore evidence; only the PROD Tunnel-config/DNS plan
remains unapplied. Helm chart, image publication, deployment, database, and
replacement recovery remain separately gated. One SHA-pinned read-only CI workflow has no package-write, Secret, registry, provider,
host, cluster, or deploy path; exact infrastructure run `31311995461` passed commit
`e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`. The private application-run outcome
remains unobserved. The
first replacement-host increment is documentation-only: it adds a secret-free
runbook and artifact register with fail-closed decision gates, not recovery
automation or runtime proof. Debian plus Ansible is the host-management owner.

CristexHub application source, local Compose assets, Keycloak theme, and Browserless
gateway remain in the separate CristexHub application repository.

## Read first

1. [`AGENTS.md`](AGENTS.md) — authoritative ownership and safety rules.
2. [`architecture-plan.md`](architecture-plan.md) — target design, staged delivery, gates, rollback, and unresolved decisions.
3. [`ansible/README.md`](ansible/README.md) — discovery contract and approved command shape.
4. [`runbooks/k3s-datastore-preflight.md`](runbooks/k3s-datastore-preflight.md) — source-only, check-only datastore/encryption stages and disclosure boundary.
5. [`runbooks/replacement-host-recovery.md`](runbooks/replacement-host-recovery.md) — replacement boundary, isolation gates, and decision-first recovery contract.
6. [`runbooks/argocd-candidate-provenance.md`](runbooks/argocd-candidate-provenance.md) — source provenance and image evidence for Argo CD.
7. [`runbooks/argocd-hardened-design.md`](runbooks/argocd-hardened-design.md) — guarded private 32-object bootstrap source, exact Secret contracts, and remaining runtime gates.
8. [`runbooks/argocd-release-selection.md`](runbooks/argocd-release-selection.md) — source-baseline selection and vendored-input boundary.
9. [`runbooks/foundation-namespace-bootstrap.md`](runbooks/foundation-namespace-bootstrap.md) — completed exact `shared-services` Namespace check/first-apply/idempotence evidence.
10. [`runbooks/keycloak-oidc-bootstrap-design.md`](runbooks/keycloak-oidc-bootstrap-design.md) — source-only Ansible-bootstrap, shared-identity, OIDC/RBAC, PostgreSQL, recovery, and private-exposure design.
11. [`runbooks/keycloak-release-selection.md`](runbooks/keycloak-release-selection.md) — immutable Keycloak/PostgreSQL and issuer source selection.
12. [`runbooks/shared-database-architecture.md`](runbooks/shared-database-architecture.md) — value-free PostgreSQL/MongoDB topology, isolation, and closed deployment gates.
13. [`runbooks/postgresql-bootstrap.md`](runbooks/postgresql-bootstrap.md) — guarded source-only PostgreSQL pod closure and runtime stop gates.
14. [`runbooks/shared-rabbitmq-architecture.md`](runbooks/shared-rabbitmq-architecture.md) — value-free shared broker isolation, future-consumer admission, and recovery boundary.
15. [`runbooks/shared-stateful-backup-architecture.md`](runbooks/shared-stateful-backup-architecture.md) — private operator backup access, non-destructive off-node copy, integrity, and restore gates.
16. [`runbooks/reactive-resume-hosted-architecture.md`](runbooks/reactive-resume-hosted-architecture.md) — private-DEV MVP placement, dedicated database/OIDC scopes, and closed image/runtime gates.
17. [`runbooks/cloudflared-candidate-provenance.md`](runbooks/cloudflared-candidate-provenance.md) — source-only, non-deployable cloudflared candidate evidence and blockers.
18. [`runbooks/infisical-operator-candidate-provenance.md`](runbooks/infisical-operator-candidate-provenance.md) — historical Infisical Operator candidate evidence and blockers.
19. [`runbooks/infisical-operator-release-selection.md`](runbooks/infisical-operator-release-selection.md) — `v0.11.7` source-baseline and Universal Auth boundary.
20. [`runbooks/infisical-operator-privileged-prerequisites-design.md`](runbooks/infisical-operator-privileged-prerequisites-design.md) — inert seven-CRD/RBAC observation and promotion-gate inventory; not deployable source.
21. [`runbooks/infisical-operator-implementation-profile.md`](runbooks/infisical-operator-implementation-profile.md) — commit-bound controller audit and selected watch/identity/egress/secret-zero profile.
22. [`runbooks/infisical-operator-bootstrap.md`](runbooks/infisical-operator-bootstrap.md) — guarded 44-object, five-namespace idle closure, proxy Secret prerequisites, validation, and rollback.
23. [`runbooks/infisical-argocd-secret-materialization.md`](runbooks/infisical-argocd-secret-materialization.md) — exact value-free Infisical-to-Argo Secret seam and blocked runtime gates.
24. [`runbooks/infisical-database-secret-materialization.md`](runbooks/infisical-database-secret-materialization.md) — exact value-free Infisical database Secret seam, scoped admission, and blocked runtime gates.
25. [`runbooks/infisical-universal-auth-value-lane.md`](runbooks/infisical-universal-auth-value-lane.md) — protected value generation/upload contracts and Secret-at-rest recovery gate.
26. [`runbooks/shared-database-provisioning.md`](runbooks/shared-database-provisioning.md) — guarded empty-reservation provisioning and helper isolation boundary.
27. [`runbooks/infisical-cristexhub-prod-runtime-materialization.md`](runbooks/infisical-cristexhub-prod-runtime-materialization.md) — applied/idempotent CristexHub PROD runtime Secret seam and residual rotation gates.
28. [`runbooks/cristexhub-prod-argocd-registration.md`](runbooks/cristexhub-prod-argocd-registration.md) — exact-revision automated non-pruning PROD Argo registration and private activation evidence.
29. [`specs/k3s-iac-foundation/testcases.md`](specs/k3s-iac-foundation/testcases.md) — validation contract and honest current results.

## Read-only Ansible discovery

The committed inventory contains only the SSH alias `crtxweb`; it contains no IP,
user, key, credential, or become secret. The playbook:

- refuses to run without `--check --diff`, an explicit `--limit`, and exactly one
  selected host;
- defaults to `become: false`;
- requires two explicit approval variables before narrowly scoped elevated k3s
  queries;
- uses `setup`, `service_facts`, and `stat` for host facts and
  `kubernetes.core.k8s_info` for exact resource kinds;
- never uses shell, raw, script, command, an embedded command allowlist, or automatic
  dependency installation;
- never queries Secret, ConfigMap, Events, or a broad `all` resource set;
- marks raw facts and Kubernetes results `no_log`, disables persistent fact caching,
  and projects only curated fields;
- projects device/partition size and state without serials, UUIDs, addresses, mount
  sources/paths, or contents, plus exact StorageClass behavior fields and bounded
  PV/PVC placement metadata from five fixed PVC namespaces;
- lets `k8s_info` load the normal root-only k3s kubeconfig for authentication, but
  never separately slurps, copies, registers, logs, or renders its content;
- writes one ignored controller-local JSON report, mode `0600`, with diff disabled
  and symlink refusal.

Listing NetworkPolicy and platform objects supplies configuration indicators only;
the listings themselves do not prove enforcement. The separately gated functional
probe has now established bounded live evidence for current CNI behavior,
NetworkPolicy deny/selective-allow semantics, rollback, and cleanup.

The probe uses one existing fixed namespace, a selectorless ClusterIP service with
an explicit EndpointSlice, a hardened server Pod, and short-lived standalone client
Pods to prove baseline success, deny failure, selective
allow/deny, rollback success, and zero labeled residue. It uses no remote exec and
never creates or deletes a Namespace. Argo CD is the intended namespaced
reconciler only for exact object sets after Ansible stops reconciling them and
handoff evidence passes; Ansible retains privileged lifecycle ownership. The closed
historical exception was limited to creating or reconciling the committed `argocd`
and `platform-edge` Namespaces with state present. Any future component bootstrap
requires its own separately approved exact exception. The separately approved wrapper check passed at
`ok=19 changed=1 unreachable=0 failed=0 skipped=2` and predicted changes for exactly
those two absent Namespace items; the recap counts the single changed loop task.
The separately approved first apply then passed at
`ok=21 changed=1 unreachable=0 failed=0 skipped=0`, changed exactly both Namespace
items, verified both identities, all three labels, Active phase, and service health,
and created no other kind. The exception has no delete path. The separately approved
idempotence checkpoint first stopped before service preflight and Kubernetes
reconciliation on failed local sudo authentication at
`ok=10 changed=0 unreachable=0 failed=1 skipped=0`, so that attempt made no mutation
and proved no idempotence. Its retry passed at
`ok=21 changed=0 unreachable=0 failed=0 skipped=0`; both exact reconciliation items
were `ok`, protected post-state identity/label/Active assertions passed, and
k3s/Tailscale remained running. The completed temporary probe exception used the verified image and explicit approvals documented in
[`ansible/README.md`](ansible/README.md); every future run requires fresh approvals
and a unique Run ID.

The approved non-elevated discovery run passed and its curated host report was
reviewed locally. It did not use become or query Kubernetes. Syntax and lint also
passed. The approved schema-v3 elevated rerun refreshed the ignored mode-`0600`
report without target mutation. Operational discovery must explicitly load the
ignored local inventory because the default inventory contains only the neutral
alias. Use this one-line zsh shape only after the required approval:

```zsh
cd ~/Projects/cristexweb/ansible && uv run ansible-playbook -i .ansible/inventory.local.yml playbooks/discover.yml --check --diff --limit crtxweb -e read_only_discovery_enable_elevated=true -e read_only_discovery_elevated_approved=true --ask-become-pass
```

Any further or elevated run still requires separate approval; complete command
contracts are documented in [`ansible/README.md`](ansible/README.md).

## Source-only k3s datastore and encryption preflight

The dedicated `ansible/bin/preflight-k3s-datastore check` wrapper is the only
entrypoint for the new read-only preflight. It accepts exactly `check`, requires
`--check --diff --limit crtxweb --become --ask-become-pass`, requires explicit
elevation approval, preserves `become: false` on controller-local delegated tasks,
uses a clean environment and ephemeral mode-`0600` attestation, and
rejects direct role/playbook invocation, passthrough arguments, task selection,
and forged internal variables before host contact. It performs no backup,
restore, encryption mutation, service/configuration mutation, host mutation,
cluster mutation, or Secret operation.

Fixed read-only argv for k3s version, systemd health/ExecStart properties,
`secrets-encrypt status --output json`, and a JSON Node query run under `no_log`;
metadata-only stat calls inspect the executable, while a bounded private slurp
reads only the fixed root-owned mode-`0600` config after its size gate. The config
parser accepts only a bounded mapping with unique, correctly typed selected
top-level fields; fixed private systemd `Environment`/`EnvironmentFiles` queries
must both be empty before a local/default data-directory source is trusted. The
selected config fields are (`data-dir`, `datastore-endpoint`, `cluster-init`, and
`secrets-encryption`) and projects booleans/enums only. The encryption JSON parser
accepts only the bounded official object shape, emits status/rotation enums, and
distinguishes initial `start` from completed `reencrypt_finished`, requires
`hashmatch=true` before either stable projection, and never treats `start` as
completed reencryption; active key names, hash errors, hashes, endpoints, paths,
and other raw values are never
projected. Private raw probe facts are cleared before report construction. The
ignored controller artifact `ansible/.ansible/k3s-datastore-preflight.local.json`
is mode `0600` and schema v2; it contains only validated version/stage values,
datastore marker booleans, encryption status/rotation stage, service and bounded
Node health, and disclosure-control booleans. It never contains raw output,
config/status content, paths, URLs, key metadata, tokens, kubeconfig, Secret data,
or node identities. Synthetic disclosure/parser fixtures and the focused contract
are `tests/validate_k3s_datastore_preflight.yml`,
`tests/validate_k3s_datastore_preflight_parser.yml`, and
`tests/test_k3s_datastore_preflight_contract.py`.

A separately approved live read-only run passed at `ok=45 changed=1
unreachable=0 failed=0`; its sanitized schema-v1 artifact recorded
`v1.36.2+k3s1`, `config_status=present_safe`,
`data_dir_source=config_override_unknown`, and unknown datastore/encryption/rotation
stages. This remains unknown evidence, not a backup/recovery or mutation approval.
The offline source pin is official K3s tag `v1.36.2+k3s1`, commit
`01b6f04aaa69e8b09303f0393d4b4f1811da23aa`. Any recovery operation remains
**NOT RUN/BLOCKED**.

## Selected direction

| Concern | Selected direction |
|---|---|
| Runtime target | Existing single-node k3s host; downtime accepted |
| Private access | Host Tailscale for SSH/k3s administration; explicit private service exposure only when required |
| Public access | Cloudflare Tunnel for approved PROD application routes only |
| Ingress | Bundled k3s Traefik, retained as the sole ingress controller |
| Host configuration | Minimal Ansible on Debian |
| External resources | OpenTofu for Cloudflare and GitHub only |
| Foundation bootstrap | Ansible for exact future Namespaces, Infisical Operator, Argo CD, Keycloak, privileged CRDs/cluster RBAC, and Keycloak realm/client/group lifecycle under component-specific approvals |
| Cluster reconciliation | Argo CD for namespaced desired state only after Ansible stops each exact object set and evidenced adoption/sync completes; no dual reconciliation |
| Identity | One future self-hosted Keycloak shared by CristexHub, Reactive Resume, and Argo CD; architecture target only, with direct Argo OIDC and private administration |
| Secrets | Infisical Cloud plus its Kubernetes Operator initially; no self-hosted Infisical and no plaintext values in Git or OpenTofu state |
| CI and images | SHA-pinned read-only GitHub Actions source CI now; private GHCR publication remains blocked pending immutable application build inputs and digest evidence |
| Environments | `cristexhub-dev` and `cristexhub-prod` |
| Shared services | Infisical Cloud Operator, separate Keycloak, one PostgreSQL, one MongoDB, and one RabbitMQ engine in `shared-services`; every consumer retains isolated logical scopes and Infisical-owned credentials |
| Other data services | Redis per environment; shared RabbitMQ uses exact dedicated users/vhosts/permissions/limits, with future consumers admitted only by reviewed policy changes |
| Backups | Application-consistent encrypted archives, metadata-only private operator catalog/retrieval, non-destructive off-host Google Drive copy direction, and isolated restore before PROD |

## Repository layout

```text
.github/workflows/       # read-only source CI only; no publish or deploy path
ansible/                 # discovery plus guarded host/Kubernetes/database source closures
  bin/                    # non-passthrough operational entrypoints
  inventory/
  playbooks/
  plugins/action/         # thirty-two exact-scope mutation/validation guards
  roles/                  # bounded discovery, host, Namespace, controller, Secret, and database roles
  files/components/       # hash-bound Argo, Infisical, PostgreSQL, and MongoDB source
  files/vendor/           # hash-bound public chart/provenance/key inputs only
  files/policies/         # value-free identity, database, backup, and application policies
opentofu/                # reviewed Cloudflare Tunnel/DNS source; apply blocked
kubernetes/              # exact platform/application Namespace source; future Argo desired state
runbooks/                # recovery, provenance, guarded source, materialization, and provisioning records
  argocd-hardened-design.md
  cristexhub-dev-namespace-bootstrap.md
  foundation-namespace-bootstrap.md
  infisical-operator-bootstrap.md
  infisical-argocd-secret-materialization.md
  infisical-database-secret-materialization.md
  infisical-cristexhub-prod-runtime-materialization.md
  infisical-universal-auth-value-lane.md
  k3s-datastore-preflight.md
  postgresql-bootstrap.md
  rclone-host-transfer.md
  shared-database-architecture.md
  shared-database-provisioning.md
  replacement-host-recovery.md
  recovery-artifact-register.md
  ... candidate, release-selection, policy, and recovery records
tests/                   # offline contract tests and negative/executable parser fixtures
```

The repository includes guarded Argo, Infisical, PostgreSQL, MongoDB,
Secret-materialization, protected-value, datastore-preflight, logical-provisioning,
and cloudflared closures under `ansible/`; each runbook distinguishes live from
source-only checkpoints. The reviewed OpenTofu source manages five imported protected
Cloudflare resources; its sixth PROD DNS resource and associated Tunnel-config update
remain unapplied. Exactly five persistent Namespace manifests exist under
`kubernetes/`, including live `cristexhub-prod`. Its credential seam, Argo registration,
and private workloads are live/idempotent; MongoDB NetworkPolicy apply/enforcement,
credential rotations, and public routing remain blocked. Earlier source-only absence
statements are historical pre-checkpoint evidence. An exact
manifest and a distinct guarded wrapper now exist
for `shared-services`; its interactive check retry predicted exactly that one
Namespace, the separately approved first apply created and verified it, and the
separately approved idempotence apply converged at `changed=0`. `platform-edge` now
contains the live private cloudflared connector; Infisical Operator, separate
Keycloak, one general PostgreSQL engine, and one shared
MongoDB engine belong in `shared-services`. Hash-bound, present-only PostgreSQL and
standalone MongoDB StatefulSet/Service source now exists; it adds no Secret value,
standalone PVC manifest, provisioning object, check/apply evidence, or runtime
approval. Kustomize remains intended for first-party application overlays;
Helm is reserved for selected third-party components. Argo ownership remains pending
until Argo CD is installed, `shared-services` is adopted or registered through an
Application, and successful sync evidence exists; the future-owner label alone is
not a handoff.

## Repository hygiene

The protective [`.gitignore`](.gitignore) excludes local inventory reports,
OpenTofu/Terraform state and plans, Ansible runtime data, kubeconfigs, local
credentials/keys, and generated secret material. It deliberately tracks provider
lock files.

## Non-goals for the foundation

- multi-node or high availability;
- Longhorn, service mesh, policy engines, or autoscaling platforms;
- self-hosted registry, Infisical server, or GitHub runner;
- a second ingress controller;
- automated production promotion;
- public DEV or public administrative dashboards;
- migration of existing data or any external/platform change.

## Project-local tool environment and validation

`uv sync --locked` creates the ignored `.venv/` from the committed `pyproject.toml`
and `uv.lock`. The pinned `kubernetes.core` collection is installed into the
ignored `ansible/.ansible/collections/` path. Nothing is installed on the inventory
host by this setup.

```bash
uv sync --locked
cd ansible
uv run ansible-galaxy collection install \
  -r requirements.yml \
  -p .ansible/collections
uv run ansible-playbook playbooks/discover.yml --syntax-check
uv run ansible-lint playbooks/discover.yml roles/read_only_discovery
cd ..
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
git diff --check
git diff --cached --quiet
```

The complete reproducible commands and actual results are recorded in
[`testcases.md`](specs/k3s-iac-foundation/testcases.md).

## Guarded host rclone source

[Guarded host rclone and proxy recovery transfer](runbooks/rclone-host-transfer.md)

[Shared stateful backup architecture and guarded Keycloak PostgreSQL scheduler](runbooks/shared-stateful-backup-architecture.md)
keeps every rclone/Google Drive command on the Debian k3s/database host while the Mac
retains plaintext verification and the age identity. Installer check passed twice.
The first apply stopped at `changed=0` on missing normal-module dispatch; the next
retry created only the verified ignored controller cache and stopped at
`ok=24 changed=2 failed=1` before host mutation because the action guard consumed an
unrendered operator default. Both focused fixes and the transfer and Operator compatibility fixes pass the 258-test offline suite,
23 syntax checks, and production lint. A fresh check passed at
`ok=25 changed=1 failed=0`; the separately approved corrected install then passed at
`ok=34 changed=4 failed=0`, selected verified rclone `1.71.1`, and preserved
k3s/Tailscale health. The separately approved idempotence apply passed at
`ok=32 changed=0 failed=0`. Host OAuth then completed through a temporary private
callback tunnel; rclone config/token remains exclusively on the host. Transfer check
passed at `ok=26 changed=0 failed=0`. Apply created only exact encrypted staging and
stopped on unsupported `--local-umask`; approved cleanup removed staging at
`ok=26 changed=1 failed=0`. The reviewed compatibility fixes pass `258/258`, but its
fresh check initially stopped before facts because the host became transiently
Tailscale-offline. After return, check passed `ok=26 changed=0`; transfer/readback
passed `ok=39 changed=7`; proxy Secret bootstrap passed `ok=15 changed=1`. The
historical Infisical Operator checkpoint applied exactly 40 objects and passed
check/apply/idempotence (`ok=24 changed=2`, `ok=29 changed=2`, and
`ok=29 changed=0`). The later 42-object source was not separately runtime-applied.
The 44-object expansion then passed check/apply/post-check/idempotence at
`ok=30 changed=1`, `ok=35 changed=1`, `ok=30 changed=0`, and `ok=35 changed=0`.
Universal Auth, application/database Secrets, and later PROD runtime remain
**NOT RUN/BLOCKED**.

The source-only Cloudflare edge policy now fixes the phased future flow
`Cloudflare → cloudflared/platform-edge → Traefik/kube-system → Keycloak/shared-services`.
It separates Cloudflare account/state, Tunnel/token, connector, Traefik, DNS,
validation, and production approvals; requires negative public reachability for
Keycloak administration/management, master, health/metrics, DEV, Argo, databases,
RabbitMQ, and direct origins; and defines exact-route rollback. Reviewed cloudflared
runtime and Infisical token-materialization source now exist, but no Tunnel, DNS
record, Ingress, token value, or public route has been applied; runtime remains
**NOT RUN/BLOCKED**.
