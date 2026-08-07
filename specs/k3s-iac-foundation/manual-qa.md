# Manual QA — k3s IaC foundation

## Evidence rules

Every executed case records date/time, tester, Git revision, deployed image digest,
environment, redacted evidence location, result, and rollback outcome. Never paste
passwords, tokens, cookies, kubeconfigs, connection strings, private keys, database
rows, personal data, or full secret-bearing command output.

MQA-01 now **PASSES**; the other twelve cases remain **PENDING** because their
hosted-runtime, rollback, isolation, recovery, or exposure evidence does not yet
exist. Separate approved non-elevated and elevated Ansible runs produced reviewed
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
is **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED** and records no live API or runtime
evidence. Its exact render reproducibility, stable upstream API registration screen,
and controller-side image closure passed online/static review. Exact k3s admission
and runtime, node pullability, signing/index-to-child and Redis trust, wildcard/broad
RBAC, ingress-only/unrestricted-egress policy, Secret recovery, private Git
secret-zero, Namespace adoption, version selection/soak, and runtime approvals remain
blocked. This online/static evidence closes no manual QA case.
The separate source-only
[cloudflared candidate provenance record](../../runbooks/cloudflared-candidate-provenance.md)
is also **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED** with runtime **NOT RUN**. Its
unsigned source, immutable image, token-file, health, and edge-transport evidence do
not close publisher trust, image assurance/availability, hardening, Infisical token
recovery, OpenTofu state/resource, Argo handoff, exact traffic-policy, route,
single-node risk, soak, or runtime gates. The source-only
[Infisical Operator candidate provenance record](../../runbooks/infisical-operator-candidate-provenance.md)
is also **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED** with runtime **NOT RUN**. Its
`v0.11.8` distribution-gap observation and version-aligned `v0.11.7` evidence close
no chart/CRD/API compatibility despite the captured target, trust, Namespace,
scoped-RBAC, Argo handoff, secret-zero,
rotation/revocation, traffic, recovery, single-node, or runtime gate. Argo CD,
cloudflared, Infisical, Secrets, workloads, Services, and routes are not installed,
so this closes no manual case. No deployment, replacement
recovery proof, or complete manual runtime validation
occurred. MQA-13 remains pending specifically
because the managed-profile rollback path has not been executed and verified, even
though warning-free fresh-session behavior passed. These results do not satisfy the
remaining manual cases.

| ID | Requirements | Scenario | Expected | Status |
|---|---|---|---|---|
| MQA-01 | KIF-001, KIF-007, KIF-008 | Read-only Ansible inventory and recovery access | The approved one-host check/diff run leaves SSH/Tailscale available; actual curated k3s/storage facts are captured without mutation or secret output | PASS — schema-v3 rerun ok=17/changed=1 local mode-0600 report/unreachable=0/failed=0; kubelet `v1.36.2+k3s1`, all 15 bounded queries, exact zero-count `shared-services` PVC query, running k3s/Tailscale, curated storage, and continuing access reviewed; no target mutation |
| MQA-02 | KIF-005, KIF-009, KIF-010 | Private administration | Argo CD and k3s API work through the approved private path and are unreachable publicly | PENDING |
| MQA-03 | KIF-013–KIF-015 | Infisical rotation | A test secret rotates and revokes without plaintext in Git/logs; recovery credential remains usable | PENDING |
| MQA-04 | KIF-016–KIF-021 | DEV isolation | DEV reaches only its databases/services and cannot authenticate to or connect to PROD resources | PENDING |
| MQA-05 | KIF-017, KIF-018 | Database authorization | DEV PostgreSQL/MongoDB principals receive explicit denial against PROD data, and vice versa | PENDING |
| MQA-06 | KIF-022–KIF-025 | DEV promotion and rollback | Argo deploys a reviewed immutable digest and Git revert restores the prior verified digest | PENDING |
| MQA-07 | KIF-026–KIF-028 | Backup and isolated restore | Encrypted off-node backup restores into isolation within RPO/RTO and application validation passes | PENDING |
| MQA-08 | KIF-025 | Private PROD acceptance | PROD auth, API, workers, migration, data isolation, resource headroom, backup, and rollback pass before public routing | PENDING |
| MQA-09 | KIF-010–KIF-012 | Public cutover | `hub.cristex-soft.com` works through Cloudflare Tunnel; DEV/admin/data endpoints remain publicly unreachable | PENDING |
| MQA-10 | KIF-007, KIF-028–KIF-030 | Reboot and replacement recovery | Host reboot preserves access/workloads; documented replacement-host recovery restores desired state and data | PENDING |
| MQA-11 | KIF-019, KIF-029 | Single-node pressure | Database and application limits preserve control-plane headroom; alerts arrive for disk/resource/backup failure | PENDING |
| MQA-12 | KIF-003, KIF-030 | Rollback safety | Git, image, route, secret, and host rollback avoid namespace/PVC deletion and blind external destroy | PENDING |
| MQA-13 | KIF-007 | Warning-free kubectl client | A genuinely fresh selected-user session inherits client-only defaults; node and all-namespace queries succeed without server-config warnings; root-only config remains protected; rollback removes only managed profile blocks | PENDING |

## Public exposure checklist

Before MQA-09 can pass, verify from outside the LAN/tailnet:

- only the approved PROD hostname resolves/routes;
- application OIDC/JWT enforcement remains active;
- deliberate unauthenticated application routes are enumerated and abuse-tested;
- DEV, Argo CD, k3s API, SSH, databases, brokers, dashboards, Browserless,
  code-runner, and identity administration are unreachable;
- direct-origin WAN ports are closed;
- disabling the Cloudflare route removes public access without breaking private PROD.

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
- OpenTofu state and external-resource ownership;
- application encryption keys;
- PostgreSQL and MongoDB data;
- immutable images or reproducible builds;
- private validation before public route reactivation.
