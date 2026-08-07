# Argo CD candidate provenance and bounded compatibility evidence

## Status and boundary

**CANDIDATE — NOT DEPLOYABLE — NOT SELECTED.** Argo CD runtime evidence is **NOT RUN**.

This document records initial controller-side public-source research captured at
`2026-08-07T05:42:22Z`, then a bounded target-minor compatibility review completed
after the separately approved schema-v3 read-only discovery. It does not select a
release, authorize a bootstrap, or add a Helm chart, values file, Kubernetes object,
credential, or secret value. The ignored research files and curated local inventory
report are evidence inputs only; they are not committed installation source. The
initial candidate research used no inventory, SSH, host, become, kubeconfig,
Kubernetes API, provider, authenticated registry, secret store, deployment, or
runtime operation. The later target discovery was read-only and wrote only the
ignored controller-local report; no Argo CD object or runtime was created.

The candidate may become deployable source only after every remaining blocker below
is resolved, a human selects the chart/application versions, and a separate change
adds reviewed desired state under the existing ownership and approval rules.

## Upstream chart and verification evidence

| Item | Verified candidate evidence |
|---|---|
| Official argo-helm index | SHA-256 `d0281dd436a64de6ce419d231bec7beb61ffa890b1e9aac4bec60380d7a4360f` |
| Chart/application | `argo-cd` chart `10.3.0`; application `v3.5.0` |
| Official chart URL | `https://github.com/argoproj/argo-helm/releases/download/argo-cd-10.3.0/argo-cd-10.3.0.tgz` |
| Chart archive | SHA-256 `d08882d22d0c76e3174e005cc09abe300c70ba556aec76725a4410d172b9c1f3` |
| Declared Kubernetes range | `kubeVersion: >=1.25.0-0` |
| Official provenance file | SHA-256 `52157f1e9cf2a68cc26e6e456bff03afdfe11a8f1637078a72262e980fb5cd02` |
| Official signing-key URL | `https://argoproj.github.io/argo-helm/pgp_keys.asc` |
| Signing-key fingerprint | `2B8F22F57260EFA67BE1C5824B11F800CD9D2252` |
| Helm verification result | Succeeded as `Argo Helm maintainers`; the verified chart hash matched the archive SHA-256 above |
| Verification tool | Helm `v3.21.3+g1ad6e68`; archive SHA-256 `19879a848cad832b7a1ac24b767a481d20fb3b95ab53a220849649422ada144e` |

Helm verified that the captured provenance signature is valid under the captured key
fingerprint and binds the captured chart hash. This evidence does **not** independently
establish the signing key's publisher identity, current authorization, trust path, or
revocation status. That trust decision remains blocked, alongside exact k3s
admission, CRD structural/defaulting/pruning/CEL behavior, operational correctness,
human selection, and soak.

## Target-minor compatibility evidence

| Item | Bounded evidence |
|---|---|
| Approved discovery report time | `2026-08-07T08:09:31Z` |
| Target kubelet | `v1.36.2+k3s1`; Kubernetes minor `1.36` |
| Compatibility evidence retrieval | `2026-08-07T08:13:26Z` |
| Official Argo CD v3.5.0 source archive | SHA-256 `f63ae068404901496f8501f386386aa89566bce37b18d44b6026d01a23abfc24` |
| Official tested-version matrix | SHA-256 `5f32e19055811f9fea77e31e4f6f9bd1b5a809d845ffa4832162fc3dea9f65df`; Argo CD `3.5` tested with Kubernetes `v1.36`, `v1.35`, `v1.34`, and `v1.33` |
| Official CI workflow | SHA-256 `14ba51038ddc46a4e5ad7dbdbb2772662ebce13d116d61d53ba378ff04c742ef`; includes k3s `v1.36.0` |
| Official Go module file | SHA-256 `c1dd593a09cccaf6e51a6a3cf64b9c2e2af6c4f453c8f8b9ced8f1b41fff3799`; includes `k8s.io/kubernetes v1.36.1` |
| Chart semver gate | chart `10.3.0` / app `v3.5.0` declares `kubeVersion: >=1.25.0-0` |

The captured target Kubernetes minor `1.36` is in Argo CD `3.5`'s official tested
matrix, and the chart's declared semver gate admits target version
`v1.36.2+k3s1`. This closes only the candidate's target-minor screening. The CI and
Go module associations are supporting official-source evidence, not proof that this
exact k3s patch/distribution, candidate values, rendered APIs and CRDs, RBAC,
NetworkPolicies, storage-free topology, or single-node behavior work on the target.
No chart was installed or rendered against the live API, and no Argo CD runtime
validation succeeded or was attempted.

## Image provenance evidence

The manifest-list/index digests identify the multi-platform tags observed during
research. The candidate render uses the verified linux/amd64 child digests, not the
index digests.

| Candidate image | Index digest | linux/amd64 child digest | Config evidence |
|---|---|---|---|
| `quay.io/argoproj/argocd:v3.5.0` | `sha256:c298cedbaeb31532ba8d4e9904eba9e4987e067293fbd86400c5194e78f743d5` | `sha256:521d6b62ecd0434c9cc6e9242a74f0e1137bb8fc0026b2c483ea88f3f17e725d` | `sha256:79eb3a49a62f9a6ec75db06bee304030272f9a6bd3b86279f88562ddfc3c4695`; `linux`; `amd64`; user `999` |
| Candidate Redis override `docker.io/library/redis:8.6.4-alpine` | `sha256:2cc044fc5a07c9b701f8f1255a309ae9ad7856e694ac03513bf3648c01e40763` | `sha256:c64af41b8fc06a2d9b8fde812dd781aa157bed6fcf8ae1656ad4e79f3f9fc9b1` | `sha256:28a8a19f9dd9e63eb5b00e62e385739e9727aacdf1275a037ab52e517c419ded`; `linux`; `amd64` |

## Ignored candidate render evidence

The controller-side values, render, and summary remain ignored. Their hashes bind
this report to the exact research inputs without making those files deployable:

| Ignored evidence | SHA-256 |
|---|---|
| Minimal candidate values | `fb1564687186fdf9742c56de5534eed6e9c1496a8aa65cf5ade8b875ea0f839a` |
| Rendered output | `51bb87262f6896d9621a05fb0a340ccf12cac0a45cdfb72516be821892c15480` |
| Render summary | `26ed8310c453152cdbd78e7914e66a5d8039acf7dbbe74b3cf09d09c5f2c47a0` |

The candidate render contains 44 documents:

- 3 CustomResourceDefinitions;
- 4 Deployments, including the ApplicationSet controller;
- 1 StatefulSet;
- 1 `redis-secret-init` Job and 1 Secret;
- 4 ClusterIP Services and 4 NetworkPolicies;
- 2 ClusterRoles and 2 ClusterRoleBindings;
- 5 Roles, 5 RoleBindings, and 5 ServiceAccounts;
- 7 ConfigMaps.

There are 7 image occurrences. Every one uses a tag plus its verified linux/amd64
child digest. Every retained container and init container has both resource requests
and limits. Each Deployment and the StatefulSet has one replica. The render has no
PVC and no ingress-like object. Dex, notifications, and `redis-ha` were disabled in
the ignored candidate values.

**Correction:** chart `10.3.0` has no effective `applicationSet.enabled` disable
gate. The candidate render retains the ApplicationSet controller and its associated
objects. ApplicationSet is represented as retained, never disabled.

These topology facts are render inspection results, not an approval of the RBAC,
CRDs, NetworkPolicies, resource sizing, security contexts, service exposure, Secret
lifecycle, or one-replica failure characteristics.

## Online readiness refresh

Four read-only controller-side lanes refreshed official Argo CD, argo-helm,
Kubernetes, GitHub, Quay, Docker Hub, and Docker Registry evidence between
`2026-08-07T11:21:53Z` and `2026-08-07T11:27:54Z`. They used anonymous HTTPS and
private temporary directories only. No inventory, SSH, become, kubeconfig,
Kubernetes API, server-side dry-run, Secret, provider, installation, deployment, or
runtime action occurred. The online reports are ignored research inputs; the durable
facts needed to interpret this record are curated below so a clean clone does not
depend on them.

Fresh official responses reproduced the existing chart index, chart archive,
provenance, Argo source, tested-version matrix, CI workflow, and Go module hashes in
this record. Using the unchanged captured candidate values, Helm
`v3.21.3+g1ad6e68` rendered chart `10.3.0` with release and Namespace
`argocd`, and Kubernetes capability `1.36.2`; the resulting 44-document SHA-256 was
again `51bb87262f6896d9621a05fb0a340ccf12cac0a45cdfb72516be821892c15480`.
This is deterministic source/render evidence, not live API admission or runtime proof.

## Static API, topology, RBAC, and network findings

Every rendered built-in kind uses a stable API registered in upstream Kubernetes
`v1.36.2`: core `v1`, `apps/v1`, `batch/v1`, `networking.k8s.io/v1`,
`rbac.authorization.k8s.io/v1`, or `apiextensions.k8s.io/v1`. The three Argo CRDs
use `apiextensions.k8s.io/v1`, include OpenAPI v3 schemas, have no conversion webhook,
and each serves and stores one Argo-owned `argoproj.io/v1alpha1` version. This static
registration screen does not prove exact k3s `v1.36.2+k3s1` admission, CRD structural
schema, defaulting, pruning, CEL validation, admission warnings, or managed-field
behavior. A later target-server admission checkpoint remains separately approval-gated.

The render retains ApplicationSet because chart `10.3.0` has no effective parent
disable gate. Its four Services are ClusterIP. It contains no Ingress, Gateway,
route, NodePort, LoadBalancer, PVC, or hostPath. Retained containers render with
non-root, read-only-root, no-privilege-escalation, capability-drop, and seccomp
controls. These strengths do not compensate for the blocking security posture:

- the application-controller ClusterRole grants wildcard cluster-wide API groups,
  resources, verbs, and non-resource URLs;
- the server ClusterRole grants broad cross-resource `delete`, `get`, and `patch`;
- all four rendered NetworkPolicies are ingress-only and pod egress is unrestricted;
- server ingress is allow-all, while ApplicationSet and the Redis secret-init Job
  have no rendered NetworkPolicy; and
- token mounts, unbounded writable volumes, active metrics listeners, exact RBAC,
  and default-deny ingress/egress require redesign and validation.

## Refreshed image trust and availability findings

Fresh controller-side registry requests reproduced both candidate index, linux/amd64
child, and config digests. All 17 referenced Argo config/layer blobs and all 8 Redis
config/layer blobs were reachable at the recorded window. This time-bounded
controller observation does not prove k3s-node/containerd pullability, registry
availability during recovery, or an acceptable rate-limit and mirror policy.

The Argo multi-platform index has an observed keyless Sigstore bundle and SLSA
provenance associated with the official `v3.5.0` release workflow and source commit.
The release SBOM identifies the exact linux/amd64 child and its layers. No direct
signature was observed on that child digest, so a human must decide how the observed
signed-index-to-child relationship is accepted while deployment remains child-digest
pinned.
Redis has index-bound SPDX and SLSA statements for the exact child, but no publisher
signature was observed; Redis publisher trust remains unresolved.

A time-bounded public Quay response for the exact Argo child reported `status=scanned`
and 296 vulnerability occurrences: 14 Low, 163 Medium, and 119 Unknown, with no High
or Critical occurrence in that response. It exposed no bounded scan time or database
build time. This is not a clean bill of health, exploitability assessment, or
deployment decision. Redis vulnerability status is **UNKNOWN — NOT RUN**.

## Private Git and Namespace adoption findings

Argo CD `v3.5.0` supports private Git through HTTPS, SSH, or GitHub App credentials.
Version-pinned Argo documentation identifies repository `Contents: read-only` as the
minimum GitHub App permission for this use. That is an available design, not a selected
repository, credential type, App owner, permission set, or custody model. Repository
credentials are Secret data and may never enter Git, output, diffs, command arguments,
or logs. The temporary writer, Infisical cutover, successor-key rotation, revocation,
off-node custody, and isolated recovery remain undecided.

Argo defaults to annotation tracking. The existing
`cristex.io/desired-owner=argocd` labels record intent only and are not Argo tracking
or ownership. Live Namespace UIDs, managed fields, last-applied state, finalizers, and
tracking metadata have not been queried for adoption. `CreateNamespace`, managed
Namespace metadata, prune, cascading Application deletion, `Replace`, `Force`, and
server-side apply can change or delete critical resources. Argo's exact option for
disabling client-side apply migration is `ClientSideApplyMigration=false`. No apply
mode, one-versus-two Application layout, prune protection, or adoption sequence is
selected; successful sync evidence remains required before any ownership handoff.

## Blocking decisions and evidence

All items below block deployable Argo CD source and runtime:

1. **Trust and human selection:** accept or reject the argo-helm key, Argo tag signer,
   GitHub Actions/Cosign identity, index-to-child trust model, and revocation
   assumptions; then select or reject chart `10.3.0` and application `v3.5.0`.
2. **Cryptographic replay and Redis trust:** replay the observed Sigstore/SLSA and
   chart evidence with pinned trusted tools and roots, and decide whether the Redis
   evidence is sufficient without an observed publisher signature.
3. **Vulnerability policy:** define severity, fixed-version, exception, re-scan-age,
   and Redis scanning requirements; online counts alone close no gate.
4. **Kubernetes authorization:** replace wildcard/broad RBAC with reviewed cluster
   read, exact namespace write, cluster-scoped permissions, and a narrowly scoped
   AppProject/source/destination/resource design.
5. **Network architecture:** select and prove default-deny ingress/egress, Kubernetes
   host-process API reachability, DNS, Redis, and dynamic Git/OCI access without
   committing private addresses or pretending standard NetworkPolicy matches FQDNs.
6. **Private administration and identity:** choose a private admin path, TLS/gRPC
   behavior, OIDC/Casbin policy, local-admin disablement, and break-glass recovery.
7. **Secrets and secret-zero** — decide ownership, creation, rotation, backup, and
   recovery for Argo internal Secrets, the initial admin, TLS/signing material, Redis,
   private Git, and Infisical bootstrap/cutover writers without value disclosure.
8. **Namespace adoption:** choose source layout, inspect live managed fields, define
   prune/cascade protection, select first-sync apply behavior, and prove UID and
   unrelated-metadata preservation before handoff.
9. **ApplicationSet:** explicitly accept and harden the retained controller or select
   another reviewed packaging strategy; it cannot be treated as disabled.
10. **Runtime and recovery:** prove node image acquisition, exact k3s admission,
    workloads, Secret lifecycle, component flows, restart/recovery, single-node
    downtime acceptance, soak, and every separately approved runtime checkpoint.

No blocker above is closed by online documentation, registry reachability, or static
rendering alone. No GitHub App, OIDC, port-forward, Traefik route, egress design,
apply mode, adoption layout, chart, or application version is selected here. Until
these gates close, rollback for this increment is only a Git revert of this
documentation and its offline contract test. There is no runtime rollback because
Argo CD runtime is **NOT RUN**.
