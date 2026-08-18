# Infisical Kubernetes Operator offline source-baseline selection

## Status

At this historical selection checkpoint, Infisical Cloud Kubernetes Operator
`v0.11.7` was **SELECTED FOR OFFLINE SOURCE AUTHORING ONLY** because the captured
chart, source, and image version align. A separately promoted 44-object closure has since passed guarded
check/apply/post-check/idempotence. Chart installation remains forbidden; broader
admission/RBAC/traffic acceptance and credential-bearing PROD phases remain
**NOT RUN/BLOCKED**.

The `v0.11.8` public distribution gap remains a time-qualified observation and is not
selected. The candidate provenance record remains authoritative for trust,
compatibility, RBAC, image, recovery, and runtime limitations.

## Vendored public inputs

The clean-clone public-input closure is exactly:

- `ansible/files/vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz`;
- `ansible/files/vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz.prov`;
- `ansible/files/vendor/infisical-operator/0.11.7/cloudsmith-signing-key.asc`;
- `ansible/files/vendor/infisical-operator/0.11.7/kubernetes-operator-64d2d81.tar.gz`;
  and
- `ansible/files/vendor/infisical-operator/0.11.7/SHA256SUMS`.

The archive SHA-256 is
`7f8846c4f6b1cdca2cea23cf00a29d12a38f42eb8da8e125dc196a1e5683aea8`.
The provenance-file SHA-256 is
`a39ae4be9ca25f7dc0b50b6633c92fc320d427fd67364b50e82c0d512db7b933`.
The public-key-input SHA-256 is
`7693c83a40ef1536cfdefe0e27806bf8027d272d847bafcea44807d08400b8c9`.
The captured provenance issuer and public-key fingerprint are
`D5CAFD69577534F2F6698C2BCFEA742D3B8FF4D5`. The official controller source archive
binds commit `64d2d81da3707d81dc271410da6fd88254b6c9b3` at SHA-256
`a08141c750404c653d23b35ecb29ab33e788845c3f666f0984fa156b9c468415`. It contains
upstream install/chart/config/build material as quarantined evidence only and is not
an operational input or promoted object closure.

Cryptographic chart verification is still **NOT RUN**. Matching fingerprints and
payload hashes do not establish Infisical authorization, trust path, current signer
authority, or revocation status.

## Immutable image and authentication direction

Future source must use the reviewed linux/amd64 child digest
`sha256:5f1767f440407d8f10fb8bd7e051e26ecf18f16731a64273c20fe206947510ae`.
No image layer is vendored here. Image signature/attestation trust, SBOM and
vulnerability disposition, encrypted off-node OCI recovery, and target-node
availability remain blocked.

Universal Auth is selected as the secret-zero direction. Its machine identity and
bootstrap credential values remain outside Git under encrypted, independently
recoverable off-node custody. This selection adds no credential or Secret. Separate
infrastructure, DEV, and PROD identities/environments remain mandatory.

## Not closed by selection

The chart has no Kubernetes version declaration, defaults to cluster-wide watching,
and contains a scoped-RBAC inconsistency: plural `scopedNamespaces` does not prevent
metrics ClusterRoles from rendering, while a namespaced manager Role contains
cluster-scoped review permissions that cannot work there. Future source must disable
chart CRD installation, explicitly inventory Ansible-owned CRDs/cluster permissions,
use non-empty scopes, and suppress or replace unused aggregate/metrics permissions.

Exact remaining CRD/API upgrade compatibility, broader k3s admission/RBAC/
NetworkPolicy negatives, signer verification, Infisical API traffic, Universal Auth
bootstrap/rotation/revocation/recovery, one non-sensitive sync, and generated Secret
lifecycle remain **NOT RUN/BLOCKED**. The separately promoted 44-object closure's
check/apply/idempotence is recorded in its bootstrap runbook.
