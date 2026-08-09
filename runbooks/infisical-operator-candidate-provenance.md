# Infisical Operator candidate provenance — source-only evidence

## Status and boundary

**HISTORICAL CANDIDATE EVIDENCE — v0.11.7 SOURCE BASELINE SELECTED — NOT
DEPLOYABLE.** The aligned `v0.11.7` set is selected only for offline source authoring
in the [release selection](infisical-operator-release-selection.md). Runtime evidence
is **NOT RUN/BLOCKED**.

This document records controller-side public-source research captured from
`2026-08-07T07:02:15Z` through `2026-08-07T07:29:40Z`. Twenty-four selected ignored
evidence hashes verified. It distinguishes the unselected latest source release from
the version-aligned public chart/image set later selected only as the offline source
baseline. It does not add values, CRD, Kubernetes object, OpenTofu resource,
credential, secret value, or deployment source. The ignored evidence inputs remain
outside Git; no raw attestation, public key, registry response, local path, or client
metadata is copied here.

No inventory, SSH, host, become, kubeconfig, Kubernetes API, Infisical
authentication, secret store, Helm operation, provider operation, deployment, or
runtime mutation was used to collect or validate this record. A later repository
commit is source traceability, not runtime evidence.

## Latest v0.11.8 source release and distribution gap

| Item | Captured candidate evidence |
|---|---|
| Evidence capture began | `2026-08-07T07:02:15Z` |
| Evidence capture finalized | `2026-08-07T07:29:40Z` |
| Selected evidence hashes | `24` verified |
| Latest GitHub release | `infisical-k8-operator/v0.11.8` |
| Release state | draft `false`; prerelease `false` |
| Published time | `2026-08-06T20:12:56Z` |
| Source commit | `fc5931fb329feeeeb17b84646772bfcabe1f7dc1` |
| GitHub commit verification | `verified: true`; reason `valid` |
| Source archive | SHA-256 `9cc6354d5dfe212687988b92dd08d4496797d56f93c3cf150f2d04e7461fd743` |
| Source chart alignment | chart `v0.11.8`; app `v0.11.8`; default image tag `v0.11.8` |
| Public distribution observation | matching Cloudsmith chart entry/archive and Docker Hub image tag were not observed at retrieval |

The source release is real, but the captured public distribution channels did not
provide a matching chart archive or image tag during the bounded observation. This
is a time-qualified observation, not proof of permanent absence. Mutable indexes and
tags must be refreshed before any future selection of `v0.11.8`. GitHub's valid commit verification does
not independently establish release authorization or bind the source, chart,
container image, and current publisher trust chain.

## Last observed version-aligned v0.11.7 candidate

| Item | Captured candidate evidence |
|---|---|
| Candidate status | selected offline source baseline; not deployable or runtime-approved |
| Release/chart/app/image | `v0.11.7` / `v0.11.7` / `v0.11.7` / `v0.11.7` |
| Source commit | `64d2d81da3707d81dc271410da6fd88254b6c9b3` |
| GitHub commit verification | `verified: true`; reason `valid` |
| Chart archive | SHA-256 `7f8846c4f6b1cdca2cea23cf00a29d12a38f42eb8da8e125dc196a1e5683aea8` |
| Chart provenance file | SHA-256 `a39ae4be9ca25f7dc0b50b6633c92fc320d427fd67364b50e82c0d512db7b933` |
| Observed OCI index | `sha256:89e211167a7cb2a271b63684aeceff0b599dc4b9f770e92f6ee0526cb64a4e68` |
| Required linux/amd64 child | `sha256:5f1767f440407d8f10fb8bd7e051e26ecf18f16731a64273c20fe206947510ae` |
| linux/amd64 config | `sha256:2c7bf8b4e450afba645bc504c5a5fef3ad8e728f6562599c830a0b2dbbf57bf4` |
| Config user and entrypoint | `65532:65532`; `/manager` |

This set was version-aligned in the captured source, chart index/archive, and image
registry. Alignment supports the later offline source-baseline selection but is not
target-cluster compatibility, publisher authorization, image assurance, or deployment approval.
The tag and package index remain mutable; any future source must use the reviewed
linux/amd64 child digest rather than a tag or index alone.

## Chart provenance and trust qualification

| Item | Captured candidate evidence |
|---|---|
| Provenance payload binding | names the matching chart archive SHA-256 `7f8846c4f6b1cdca2cea23cf00a29d12a38f42eb8da8e125dc196a1e5683aea8` |
| Provenance issuer fingerprint | `D5CAFD69577534F2F6698C2BCFEA742D3B8FF4D5` |
| Captured Cloudsmith public-key fingerprint | `D5CAFD69577534F2F6698C2BCFEA742D3B8FF4D5` |
| Cryptographic chart verification | **NOT RUN**; captured verifier attempt reported `gpg: command not found` |
| Independent trust result | Infisical authorization, trust path, revocation status, and current signer authority remain blocked |

The matching fingerprints associate the provenance issuer with the public package
key retrieved from Cloudsmith. They do not establish that Infisical authorized that
key, that the key is currently trusted, or that it was unrevoked and authorized at
signing time. Because no available verifier cryptographically checked the signature,
the chart provenance must not be described as verified.

## OCI image and attached SLSA content

| Item | Captured candidate evidence |
|---|---|
| amd64 attestation manifest | `sha256:0e561fbd350b7cf57b58acd27a5ff3a5de0c5a882e973681517dee318d30780a` |
| SLSA statement layer | `sha256:416cef4ba2778a2ed020d3f58c138ff4f5d0a79cc98bd553a7514edbbd0ec56c` |
| Predicate type | `https://slsa.dev/provenance/v1` |
| Subject binding | linux/amd64 child `sha256:5f1767f440407d8f10fb8bd7e051e26ecf18f16731a64273c20fe206947510ae` |
| Source revision | `64d2d81da3707d81dc271410da6fd88254b6c9b3` |
| Builder identity | empty |
| Completeness | BuildKit request and resolved-dependency completeness are false |
| SBOM observation | no SBOM was observed in the bounded evidence; this is not proof of absence |

The attached statement is observed registry content. The exact subject and source
revision link the candidate image to the stated build input, but an empty builder
identity, incomplete fields, and absence of independent signature verification mean
it is not a verified publisher signature or trusted build attestation. Image
signature policy, SBOM retrieval, vulnerability review, and independent off-node
availability remain unresolved.

## Chart defaults and runtime implications

| Item | Captured candidate evidence |
|---|---|
| Kubernetes compatibility declaration | no `kubeVersion` declaration |
| Controller replicas | `1` |
| CRD behavior | seven CRD templates; `installCRDs: true` |
| Default watch scope | all Namespaces; `scopedNamespaces: []`; `scopedRBAC: false` |
| Metrics Service | private `ClusterIP` |
| Container hardening defaults | non-root; read-only root filesystem; privilege escalation disabled; all capabilities dropped |
| Pod hardening defaults | `runAsNonRoot: true`; `RuntimeDefault` seccomp |
| Image template behavior | concatenates repository and tag; digest rendering must be proven before source |

These are chart defaults, not runtime results. The approved schema-v3 discovery now
captures target kubelet `v1.36.2+k3s1`, but the missing compatibility declaration
means chart, CRD/API, and exact k3s compatibility remain unproven. Cluster-wide
watching and unscoped RBAC are not least-privilege defaults for this platform. Future
values must use an explicit non-empty target scope or document and separately approve why cluster-wide
access is required. The repository/tag template must be rendered offline to prove a
reviewed `tag@linux/amd64-digest` reference works before deployable source is added.

## Blocking decisions and evidence

Every item below still blocks deployable Infisical Operator controller source and runtime:

1. **Trust and soak acceptance:** `v0.11.7` is selected only as the offline source
   baseline. Refresh mutable release/chart/image evidence, record signer/build trust
   decisions, and approve a soak policy before controller source or runtime.
2. **Target compatibility:** the approved schema-v3 discovery captured kubelet
   `v1.36.2+k3s1`, but the chart has no `kubeVersion` declaration. Review every
   rendered CRD/API version and prove exact chart and k3s compatibility before any
   deployable controller source.
3. **Chart and image assurance:** cryptographically verify the chart signature,
   establish independent Infisical key authorization and revocation status, verify
   image signature/attestation identity, obtain or disposition an SBOM and
   vulnerability review, and prove off-node availability of the exact child digest.
4. **Shared operator Namespace:** exact present-only source and a distinct bounded
   Ansible wrapper exist for `shared-services`; check and separately approved first
   apply passed, while idempotence and all Operator checkpoints remain separately
   approved and **NOT RUN**. The completed
   `argocd`/`platform-edge` wrapper remains closed. The Operator is intentionally
   co-located with separate Keycloak and PostgreSQL deployments, but still requires
   its own ServiceAccount, exact scoped RBAC, watch scope, resource limits, and
   pod-selective NetworkPolicy. It must not be placed in `platform-edge`, `argocd`,
   `cristexhub-dev`, or `cristexhub-prod`.
5. **Ansible bootstrap and later ownership handoff:** Ansible is the selected bounded
   installer and privileged lifecycle owner. Exact operator source, credentials, and
   approvals remain absent. A namespaced object may hand off to Argo only after
   Ansible stops reconciling it and registration/adoption, successful sync, and
   managed-field evidence pass; dual reconciliation is forbidden.
6. **Watch scope and least-privilege RBAC:** select explicit target Namespaces and
   prove scoped authorization plus negative cross-environment access. Any
   cluster-wide decision requires separate justification, review, and tests.
7. **CRD lifecycle and permissions:** approve CRD install/upgrade/rollback behavior,
   cluster-scoped permissions, conversion/storage compatibility, and recovery. CRD
   or generated Secret deletion is not routine rollback.
8. **Exact component traffic policy:** review and positively/negatively test only the
   required Kubernetes API, DNS, Infisical API, and private metrics flows. Deny
   unrelated namespace, control-plane, metadata, Internet, and public access.
9. **Secret-zero, recovery, rotation, and revocation:** implement the selected
   Universal Auth direction with an exact bootstrap identity, least privilege, off-node recovery,
   rotation, compromise response, and non-disclosing revocation proof. Argo owns
   committed CR/reference objects; Infisical owns generated Secret values. No
   bootstrap credential may enter Git, OpenTofu state/plan, command arguments,
   environment examples, CI logs, or review artifacts.
10. **Environment separation and bootstrap circularity:** use separate
    infrastructure, DEV, and PROD identities/environments. Resolve private Git and
    operator bootstrap ordering without assuming the operator can create credentials
    needed before Argo or the operator itself starts.
11. **Single-node availability:** one replica on one physical node is a shared
    failure domain. Accept the availability risk and define restart, alerting,
    recovery, and soak expectations.
12. **Runtime approvals:** the foundation Namespace check and first apply are
    complete; separately approve its idempotence checkpoint, then separately approve operator
    CRDs/RBAC/controller creation, authentication bootstrap, one non-sensitive sync,
    rotation, revocation, recovery, any later Argo handoff, and any upgrade.
    Runtime remains **NOT RUN**.

Until these gates close, rollback for this increment is only a Git revert of source.
There is no runtime rollback because no Infisical Namespace, CRD, controller,
credential, Secret, or deployment was created.
