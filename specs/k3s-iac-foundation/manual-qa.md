# Manual QA — k3s IaC foundation

## Evidence rules

Every executed case records date/time, tester, Git revision, deployed image digest,
environment, redacted evidence location, result, and rollback outcome. Never paste
passwords, tokens, cookies, kubeconfigs, connection strings, private keys, database
rows, personal data, or full secret-bearing command output.

MQA-01 now **PASSES**; MQA-14 and MQA-17 are **PARTIAL**; the other fourteen cases
remain **PENDING** because their hosted-runtime, rollback, isolation, recovery, or exposure
evidence does not yet exist. Separate approved non-elevated and elevated Ansible runs produced reviewed
host and cluster-indicator reports. A
separately approved two-package dependency bootstrap completed and all nine exact
Kubernetes queries now pass. Persistent group-scoped kubectl access and the
all-namespace listing, warning-free client defaults, and the single-node reboot
recovery pass. The operator manually confirmed independent fallback access, active
services, and warning-free queries after reboot. A separately approved generated-
name CNI/NetworkPolicy probe passed live baseline, deny, selective allow/deny,
rollback, exact-UID cleanup, and a separate zero-residue check with no Namespace or
public exposure. Extended live storage discovery captured curated device,
StorageClass, PV, and bounded PVC indicators without disk mutation or secret output;
its fifth PVC scope was the then-current `shared-data` and it did not capture a
Kubernetes version. The separately approved schema-v3 rerun passed read-only and
confirmed kubelet `v1.36.2+k3s1`, all 15 bounded queries available, and the exact
`shared-services` PVC query with count zero. Argo CD `3.5`'s official tested matrix
contains target minor `1.36`, and chart `10.3.0` admits it. Static render
reproducibility and upstream API registration now pass; exact k3s admission/runtime
and CRD structural/defaulting behavior remain unproven. The same Tailscale/SSH path remained
available, closing MQA-01.
The first replacement-host increment is documented offline: a
secret-free runbook/register separates reboot from replacement, stops on old-host or
storage split-brain risk, and requires an explicit recovery identity decision. Its
datastore/version/token/storage/RPO/RTO/off-node entries remain `UNKNOWN — STOP`.
The OpenTofu installer now passes its reviewed controller-mediated live recovery
and `changed=0` idempotence run after the first host-side GitHub retrieval failed.
The protected state directory remains empty; state encryption/off-node restore,
provider operations, and external ownership remain pending and close no manual
case. Exact `argocd` and `platform-edge` Namespace manifests plus their present-only
Ansible bootstrap pass offline contracts. The separately approved wrapper check
passed without mutation, and the separately approved first apply created and
verified exactly those two Active Namespaces with the reviewed labels while
preserving service health. The separately approved idempotence checkpoint initially
stopped before service preflight and Kubernetes reconciliation on failed local sudo
authentication with `changed=0`; its retry passed at
`ok=21 changed=0 unreachable=0 failed=0 skipped=0`, with both exact items `ok`, exact
post-state assertions passing, and service health preserved. These bounded
checkpoints close no manual QA case. The source-only
[Argo CD candidate provenance record](../../runbooks/argocd-candidate-provenance.md)
retains historical evidence; the release record selects chart `10.3.0` / app
`v3.5.0` only for offline source authoring. It remains **NOT DEPLOYABLE**, with no live
API or runtime evidence. Its exact render reproducibility, stable upstream API registration screen,
and controller-side image closure passed online/static review. Exact k3s admission
and runtime, node pullability, signing/index-to-child and Redis trust, wildcard/broad
RBAC, ingress-only/unrestricted-egress policy, Secret recovery, private Git
secret-zero, Namespace adoption, version selection/soak, and runtime approvals remain
blocked. This online/static evidence closes no manual QA case. The separate
[guarded Argo CD bootstrap](../../runbooks/argocd-hardened-design.md) now implements
an exact 32-object source closure with private ClusterIP/loopback-only access,
ApplicationSet runtime absent, a deny-all default AppProject, default-deny component
flows with a documented broad ports-only weakness, namespaced idle least privilege,
and three externally materialized cryptographically validated Secret contracts. It
still proves no live runtime case; later adoption Applications are separate future
source. The companion
[source-only Keycloak OIDC bootstrap design](../../runbooks/keycloak-oidc-bootstrap-design.md)
and release record select Keycloak `26.7.1`, PostgreSQL `17.10`, the stable issuer,
direct OIDC, and value-free RBAC policy only for offline authoring. The exact
CristexHub DEV/PROD browser callbacks and origins are source-selected, but these
records do not add executable source or prove Ansible bootstrap, database recovery,
runtime callbacks, runtime RBAC, or private exposure. MQA-02 private administration
and identity authorization,
MQA-03 Infisical rotation, and MQA-12 rollback safety remain **PENDING**; these
designs close no manual QA case.
The separate source-only
[cloudflared candidate provenance record](../../runbooks/cloudflared-candidate-provenance.md)
is also **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED** with runtime **NOT RUN**. Its
unsigned source, immutable image, token-file, health, and edge-transport evidence do
not close publisher trust, image assurance/availability, hardening, Infisical token
recovery, OpenTofu state/resource, Argo handoff, exact traffic-policy, route,
single-node risk, soak, or runtime gates. The source-only
[Infisical Operator candidate provenance record](../../runbooks/infisical-operator-candidate-provenance.md)
retains historical evidence. The inert
[privileged-prerequisites inventory](../../runbooks/infisical-operator-privileged-prerequisites-design.md)
remains the raw-chart defect record, while the
[implementation profile](../../runbooks/infisical-operator-implementation-profile.md)
remains canonical policy. The guarded [Infisical idle bootstrap](../../runbooks/infisical-operator-bootstrap.md) now provides
exact deployable source for six CRDs, native same-Namespace admission, scoped RBAC,
the metrics-off Operator, authenticated TLS proxy, and NetworkPolicy. It contains no
committed Secret value or Infisical CR and Operator runtime is still **NOT
RUN/BLOCKED**. A separate source-only [Argo CD Secret materialization seam](../../runbooks/infisical-argocd-secret-materialization.md)
freezes one same-Namespace Universal Auth reference, fixed source identifiers,
exact orphaned Argo targets, additive exact-name RBAC, and fail-closed admission;
its credential/source creation, Secret values, sync, and runtime remain blocked and
close no manual case. The first local secret-zero/Drive attempt stopped before Kubernetes on
expired OAuth; its plaintext residue and unused encrypted artifact were removed
without reading values. An unused debug-exposed age identity was revoked/regenerated
before upload/Kubernetes. The hardened retry proved early cleanup, encrypted-pending
resume and a Keychain copy, confirmed zero Kubernetes Secrets, then stopped on the
same expired controller OAuth. That transfer path is superseded by guarded host
rclone source. Host install/idempotence, OAuth, encrypted transfer/readback/controller
decrypt, proxy Secret recovery/write, and Operator check/apply/idempotence passed.
MQA-03 remains pending until broader live admission/RBAC/traffic, Universal Auth,
ConfigMap sync, rotation, revocation, and recovery pass. A separate
source-only database Secret materialization seam freezes 15 value-free objects, two
engine-specific Auth/credential identities, two path-scoped StaticSecrets, eleven
engine/consumer target contracts, eight scoped operator-or-target VAP/bindings with operator-only
validation, additive writer RBAC, and offline negative/hash contracts; its values,
check/apply, sync, rotation, recovery, and runtime remain blocked. This source does
not close a manual case. Argo CD, cloudflared, Infisical runtime, databases,
application workloads, and routes are not installed, so this source increment closes no manual case. No deployment, replacement
recovery proof, or complete manual runtime validation
occurred. The separate source-only k3s datastore/encryption preflight completed one
approved live read-only run at `ok=45 changed=1`; the sole change was its ignored
mode-`0600` sanitized artifact, whose datastore/encryption stages remained unknown.
It performed no host, backup, restore, encryption, cluster, or Secret mutation and
closes no manual QA case. MQA-13 remains pending specifically
because the managed-profile rollback path has not been executed and verified, even
though warning-free fresh-session behavior passed. These results do not satisfy the
remaining manual cases. The offline `shared-services` source correction adds no live
Namespace, workload, database, credential, or route and therefore closes no manual
case. The separate exact present-only `cristexhub-prod` Namespace manifest, guarded
wrapper, and action source now exist, but the live PROD Namespace remains absent;
its check/apply/API path and all runtime gates are NOT RUN/BLOCKED. Future placement
is cloudflared-only `platform-edge`, with the Infisical
Operator, separate Keycloak deployment, one general PostgreSQL engine, and one
shared MongoDB engine in `shared-services`. The value-free database policy closes no
manual case: PostgreSQL and MongoDB source-only contracts exist, but Secret
materialization, check/apply/idempotence, storage behavior, provisioning,
authorization, backup/restore, and runtime evidence remain pending. The SHA-pinned CI and Reactive Resume
policy source also closes no full manual case. Infrastructure CI run `31311995461`
passed for exact commit `e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`; the private
application run is not observable with the available unauthenticated API, no image
was published, and no Reactive Resume image/callback/object/Secret/runtime is
selected.

| ID | Requirements | Scenario | Expected | Status |
|---|---|---|---|---|
| MQA-01 | KIF-001, KIF-007, KIF-008 | Read-only Ansible inventory and recovery access | The approved one-host check/diff run leaves SSH/Tailscale available; actual curated k3s/storage facts are captured without mutation or secret output | PASS — schema-v3 rerun ok=17/changed=1 local mode-0600 report/unreachable=0/failed=0; kubelet `v1.36.2+k3s1`, all 15 bounded queries, exact zero-count `shared-services` PVC query, running k3s/Tailscale, curated storage, and continuing access reviewed; no target mutation |
| MQA-02 | KIF-005, KIF-009, KIF-010, KIF-012–KIF-015, KIF-021 | Private administration and identity authorization | Argo CD and k3s API work through the approved private path; Keycloak administration/management and Argo remain publicly unreachable; direct OIDC grants exact administrator/read-only groups, denies read-only mutation and ungrouped/invalid/expired identities, and preserves tested local break-glass recovery | PENDING |
| MQA-03 | KIF-013–KIF-015 | Infisical rotation | A test secret rotates and revokes without plaintext in Git/logs; recovery credential remains usable | PENDING |
| MQA-04 | KIF-016–KIF-021 | DEV isolation | DEV reaches only its databases/services and dedicated RabbitMQ vhost; it cannot authenticate to or connect to PROD databases, services, vhost, users, or management authority | PENDING |
| MQA-05 | KIF-017, KIF-018 | Database authorization | DEV and PROD PostgreSQL/MongoDB principals receive bidirectional denial; unwanted PostgreSQL `PUBLIC` connection/schema privileges are absent; the dedicated Keycloak role reaches only its logical database; application/Keycloak roles cannot create databases or roles; MongoDB workload users have no any-database, user-admin, role-admin, or out-of-scope write authority | PENDING |
| MQA-06 | KIF-022–KIF-025 | DEV promotion and rollback | Argo deploys a reviewed immutable digest and Git revert restores the prior verified digest | PENDING |
| MQA-07 | KIF-026–KIF-028 | Backup and isolated restore | A private authenticated operator lists metadata, retrieves and verifies an encrypted timestamped off-node archive, restores it in isolation within RPO/RTO, validates the application, restores RabbitMQ definitions separately, and proves queued-work reconciliation | PENDING |
| MQA-08 | KIF-025 | Private PROD acceptance | PROD auth, API, workers, migration, data isolation, resource headroom, backup, and rollback pass before public routing | PENDING |
| MQA-09 | KIF-010–KIF-012 | Public identity and application cutover | The separately approved stable Keycloak browser-authentication issuer and `hub.cristex-soft.com` work through exact Cloudflare Tunnel routes; identity administration/management, DEV, Argo, and data endpoints remain publicly unreachable | PENDING |
| MQA-10 | KIF-007, KIF-028–KIF-030 | Reboot and replacement recovery | Host reboot preserves access/workloads; documented replacement-host recovery restores desired state and data | PENDING |
| MQA-11 | KIF-019, KIF-020, KIF-029 | Single-node pressure | Database, RabbitMQ connection/vhost/queue, and application limits preserve control-plane headroom; alerts arrive for disk/resource/queue/backup failure | PENDING |
| MQA-12 | KIF-003, KIF-030 | Rollback safety | Git, image, route, secret, and host rollback avoid namespace/PVC deletion and blind external destroy | PENDING |
| MQA-13 | KIF-007 | Warning-free kubectl client | A genuinely fresh selected-user session inherits client-only defaults; node and all-namespace queries succeed without server-config warnings; root-only config remains protected; rollback removes only managed profile blocks | PENDING |
| MQA-14 | KIF-022–KIF-024 | GitHub-hosted delivery containment | Reviewed infrastructure and application CI runs pass on the exact revision with read-only permissions, no Secret/package/deploy path, and future publication emits immutable digest/SBOM/provenance evidence without rebuilding for PROD | PARTIAL — infrastructure run `31311995461` passed exact commit `e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`; private application-run result is unobserved and publication remains BLOCKED |
| MQA-15 | KIF-012–KIF-017, KIF-021 | Private Reactive Resume DEV | Digest-pinned DEV instance uses the exact private Keycloak client and its dedicated PostgreSQL scope; cross-environment/database access and public/admin exposure fail closed; backup/restore succeeds | PENDING — source policy only; image, callbacks, objects, Secrets, database, and runtime are blocked |
| MQA-16 | KIF-002, KIF-005, KIF-010, KIF-012, KIF-015 | Private Argo CD bootstrap | Guarded check/apply/idempotence, CRD establishment, all four workloads, TLS/login, exact NetworkPolicy flows and negatives, and recovery pass without public exposure | PENDING — source contracts pass; Secrets and live runtime remain blocked |
| MQA-17 | KIF-002, KIF-005, KIF-007, KIF-013–KIF-015, KIF-027, KIF-030 | Host rclone and encrypted proxy recovery | Pinned host install/idempotence, non-root host OAuth, ciphertext-only staging, immutable Drive upload/readback, controller decrypt, cleanup, exact marker, and recovery evidence pass without host plaintext or age identity | PARTIAL — after two historical pre-host-mutation stops and reviewed fixes, a fresh check passed at ok=25/changed=1 and the separately approved corrected install passed at ok=34/changed=4, selected verified rclone 1.71.1, and preserved k3s/Tailscale. The idempotence apply passed at ok=32/changed=0. Host OAuth and transfer check passed; apply stopped on unsupported `--local-umask` after exact encrypted staging, and cleanup passed with zero residue. After transient host return, transfer check/apply passed at ok=26/changed=0 and ok=39/changed=7; proxy Secret bootstrap passed at ok=15/changed=1. Infisical Operator check/apply/idempotence passed. Broader admission/RBAC/traffic, Universal Auth, and database runtime remain pending |

## Public exposure checklist

Before MQA-09 can pass, verify from outside the LAN/tailnet:

- only the separately approved stable Keycloak browser-authentication issuer and PROD
  application hostnames resolve/route;
- only the reviewed Keycloak authentication paths are reachable, positive login
  passes, and identity administration/management paths are denied;
- application OIDC/JWT enforcement remains active;
- deliberate unauthenticated application routes are enumerated and abuse-tested;
- DEV, Argo CD, k3s API, SSH, databases, brokers, dashboards, Browserless,
  code-runner, and identity administration/management are unreachable;
- direct-origin WAN ports are closed;
- disabling each Cloudflare route removes only its public access without breaking the
  remaining private identity and PROD recovery paths.

## Recovery checklist

A restore rehearsal must start from a clean isolated target only after independent
old-host fencing/storage-exclusivity evidence and approval of exactly one
preserve-existing-identity or create-new-cluster model. The
[replacement-host runbook](../../runbooks/replacement-host-recovery.md) and
[secret-free artifact register](../../runbooks/recovery-artifact-register.md) remain
blocked on unknown prerequisites. A later rehearsal must prove recovery of:

- pinned host/k3s configuration;
- Argo CD repository access;
- Infisical bootstrap access and environment identities;
- the dedicated Keycloak logical database/role/realm state on the shared PostgreSQL
  engine, administrator recovery, TLS, and OIDC client material;
- OpenTofu state and external-resource ownership;
- application encryption keys;
- PostgreSQL and MongoDB data;
- immutable images or reproducible builds;
- private validation before public route reactivation.

## MQA-16 — Private Argo CD bootstrap and idempotence

Status: **PENDING / NOT RUN**. After Infisical has created exact `argocd-secret`,
`argocd-redis`, and `argocd-server-tls` contracts, review
`ansible/bin/bootstrap-argocd check`, then separately approve the first `apply` and
idempotent `apply`. Prove all four workloads Ready, all three Services ClusterIP,
`argocd-initial-admin-secret` absent, loopback-only TLS/login over the authenticated
k3s API, public and pod-origin negatives, exact API/repo/Redis flows, blocked metrics
ports, repository read from `https://github.com/devraider/cristexweb.git` at
`develop`, and unchanged k3s/Tailscale health. Stop on any unexpected object, public
reachability, RBAC widening, policy bypass, credential disclosure, or nonzero second
apply.

## MQA-17 — Host rclone, OAuth, and encrypted proxy recovery transfer

Status: **PARTIAL / TRANSFER, PROXY SECRETS, AND OPERATOR IDEMPOTENCE PASSED**. Historical
applies stopped before host mutation on nested action dispatch and an unresolved
operator default. Both fixes pass focused/full validation and independent review. A
fresh check passed at `ok=25 changed=1 failed=0`; the corrected install passed at
`ok=34 changed=4 failed=0`; the separately approved idempotence apply passed at
`ok=32 changed=0 failed=0`. Exact version `1.71.1`, digests,
root-owned cache/payload/selector, and unchanged k3s/Tailscale passed. Host OAuth
completed through a private callback tunnel with config/token only on the host.
Transfer check passed at `ok=26 changed=0 failed=0`; apply created only exact encrypted
staging, then stopped on unsupported `--local-umask`. Approved cleanup passed at
`ok=26 changed=1 failed=0` with zero staging residue. After transient host return, transfer check passed at `ok=26 changed=0`; apply passed
at `ok=39 changed=7` with the exact pending ciphertext/checksum, four immutable host
`copyto` boundaries, encrypted readback, exact staging cleanup, controller TLS/key/auth
checks without output, and mode-`0600` `drive-verified`. Proxy Secret bootstrap passed
at `ok=15 changed=1`. Infisical Operator final check/apply/idempotence passed at
`ok=24 changed=2`, `ok=29 changed=2`, and `ok=29 changed=0`. Stop on selector/config/staging/remote collision,
residue, digest, ownership, service, decryption, or relationship drift. Cleanup may
remove only exact host ciphertext residue and must never delete Drive content.
Secret bootstrap remains a later separate approval.
