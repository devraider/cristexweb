# Argo CD offline source-baseline selection

## Status

Argo CD chart `10.3.0` with application `v3.5.0` is **SELECTED FOR OFFLINE SOURCE
AUTHORING ONLY**. It is not deployable or approved for installation. Argo CD runtime
remains **NOT RUN/BLOCKED**.

The candidate provenance and hardened-design records remain authoritative for all
security, trust, secret, adoption, and live blockers. This selection resolves only
the version choice and clean-clone chart-byte availability.

## Vendored public inputs

The clean-clone public-input closure is exactly:

- `ansible/files/vendor/argocd/10.3.0/argo-cd-10.3.0.tgz`;
- `ansible/files/vendor/argocd/10.3.0/argo-cd-10.3.0.tgz.prov`;
- `ansible/files/vendor/argocd/10.3.0/pgp_keys.asc`; and
- `ansible/files/vendor/argocd/10.3.0/SHA256SUMS`.

The archive SHA-256 is
`d08882d22d0c76e3174e005cc09abe300c70ba556aec76725a4410d172b9c1f3`.
The provenance-file SHA-256 is
`52157f1e9cf2a68cc26e6e456bff03afdfe11a8f1637078a72262e980fb5cd02`.
The public-key-input SHA-256 is
`36366596211a1587d018be5b178687799cb2edfc3e3e3c6ccd661b33fc6305ca`.

The provenance signature/hash replay already succeeded against the captured key and
fingerprint `2B8F22F57260EFA67BE1C5824B11F800CD9D2252`. That proves the captured
signature association; it does not independently prove current publisher
authorization, trust path, or revocation status.

## Immutable image direction

Future source must use the reviewed linux/amd64 Argo child digest
`sha256:521d6b62ecd0434c9cc6e9242a74f0e1137bb8fc0026b2c483ea88f3f17e725d`.
The reviewed Redis child digest is
`sha256:c64af41b8fc06a2d9b8fde812dd781aa157bed6fcf8ae1656ad4e79f3f9fc9b1`.
No image layer is vendored here. Direct child-signature policy, Redis publisher trust,
SBOM/vulnerability disposition, encrypted off-node OCI recovery, target-node
availability, and soak remain blocked.

## Not closed by selection

The selected chart defaults are unsafe for this platform. Future source must disable
chart CRDs, cluster RBAC, permissive chart NetworkPolicies, aggregate roles, and the
Redis initializer, then provide exact Ansible-owned privileged prerequisites and
reviewed namespaced objects. Private ClusterIP-only administration, quiescent
ApplicationSet, supplemental default-deny, exact non-wildcard RBAC, Infisical-owned
Secret values, direct Keycloak OIDC with Dex absent, and one-writer handoff remain
required.

Exact GVR inventory, deterministic hardened render, k3s admission, API service DNAT
behavior, node pullability, secret-zero/recovery, private Git, Namespace managed
fields, adoption apply mode, check/apply/idempotence approvals, and runtime evidence
remain **NOT RUN/BLOCKED**.
