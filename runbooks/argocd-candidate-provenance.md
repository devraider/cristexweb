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
revocation status. That trust decision remains blocked, alongside full rendered-API
and CRD compatibility, operational correctness, human selection, and soak.

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

## Blocking decisions and evidence

All items below block deployable Argo CD source and runtime:

1. **Full target Kubernetes compatibility:** the captured target minor `1.36` is in
   Argo CD `3.5`'s official tested matrix and passes chart `10.3.0`'s declared
   semver gate. This does not prove exact k3s patch/distribution behavior, rendered
   API/CRD compatibility, RBAC, NetworkPolicy, Secret lifecycle, or operational
   correctness. Offline render/schema review and separately approved target runtime
   validation remain blocked.
2. **Human trust, selection, and soak:** chart `10.3.0` and application `v3.5.0`
   are only a candidate with captured signature/hash-binding evidence. A human must
   independently accept or reject the signing-key trust/status, select or reject the
   versions, and approve the required compatibility/soak policy.
3. **Generated and internal Secret ownership/recovery:** decide the exact owner,
   creation sequence, rotation, backup, and recovery for `argocd-secret`, the initial
   admin credential, TLS/signing material, and the Redis secret initialized by the
   `redis-secret-init` Job. No value may enter Git or logs.
4. **Private Git secret-zero and recovery:** approve private repository credentials,
   least privilege, off-node custody, rotation, and non-disclosing recovery before
   Argo can read desired state.
5. **Image acquisition and component traffic:** prove node/containerd availability
   of the exact Quay and Docker Hub child digests, or approve a verified preload or
   mirror. Define and test an explicit component flow matrix for Kubernetes API,
   DNS, Redis, and the selected GitHub HTTPS or SSH transport, including negative
   tests for unrelated control-plane, namespace, and public access. The captured
   chart NetworkPolicies are ingress-only and do not establish egress default-deny.
6. **Bootstrap ownership exception:** review the exact non-Argo objects needed to
   install Argo, the bounded writer and rollback, Namespace adoption or Application
   registration, and successful-sync evidence that completes handoff. Future-owner
   labels alone do not establish Argo ownership.
7. **Runtime approvals:** obtain separate approvals for Namespace check, Namespace
   apply/idempotence, any persistent-object bootstrap, secret creation, and runtime
   validation. Argo CD must remain private; no public route is authorized.

Until these gates close, the rollback for this increment is only a Git revert of
this documentation and its offline contract test. There is no runtime rollback
because Argo CD runtime is **NOT RUN**.
