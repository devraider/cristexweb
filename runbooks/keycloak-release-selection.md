# Keycloak and identity database source selection

## Status

Keycloak `26.7.1` and PostgreSQL `17.10` are **SELECTED FOR OFFLINE SOURCE
AUTHORING ONLY**. They are not deployable, installed, or approved for check/apply.
Keycloak and PostgreSQL runtime remain **NOT RUN/BLOCKED**.

The exact selected identities are:

| Component | Selected identity |
|---|---|
| Keycloak | official repository `quay.io/keycloak/keycloak`; version `26.7.1`; immutable linux/amd64 pull reference `quay.io/keycloak/keycloak@sha256:7523ccfbd950f59783504cdf5a0138dae48746dfe36075bbfccdb5a9ee245ee2` |
| PostgreSQL | Docker Official Image repository `docker.io/library/postgres`; version `17.10`; immutable linux/amd64 pull reference `docker.io/library/postgres@sha256:dbbeb22a65db2503050cdbbe5e78f017478f10a1002a226463f049dbb017e99b` |
| Realm | `cristexhub` |
| Stable issuer | `https://auth.cristex-soft.com/realms/cristexhub` |
| First-bootstrap theme | Keycloak default theme from the selected official image |

The separate CristexHub theme is deliberately deferred. Shipping it requires a
separately built, signed, scanned, immutable `26.7.1`-derived image; this selection
must not claim that the official Keycloak child contains that theme.

## Selection boundary

Selection fixes repository, version, architecture, digest, realm, and issuer inputs
so policy and future source can be deterministic. It does not close image publisher trust,
SBOM, vulnerability disposition, off-node OCI recovery, node pullability, k3s
admission, writable paths, probes, resources, proxy trust, TLS, callback, route,
storage, database TLS, backup, restore, or runtime gates.

No image layer is vendored in Git. Before the first private non-authoritative
bootstrap, an exact OCI recovery path must preserve the selected children off-node,
verify integrity, and prove restore/import or pull on the target node. The selected
PostgreSQL child is intended for one general instance in `shared-services`, not a
separate Keycloak database server. Keycloak requires its own logical database, owner
role, credential, database-scoped application-consistent encrypted `pg_dump`,
independent key custody, non-destructive off-node copy, isolated restore, and
measured RPO/RTO. The shared PostgreSQL engine and PVC remain a common failure
domain.

## Hosted identity policy

The value-free policy at
`ansible/files/policies/hosted-identity-authorization.yml` freezes the exact realm,
issuer, images, client IDs, environment group templates, Argo mappings, Namespace
trust boundaries, ownership, and Infisical Universal Auth direction. It is data for
review and later Ansible reconciliation; it is not a Keycloak realm import,
Kubernetes object, executable playbook, credential, or runtime approval.

All browser clients remain blocked until their exact origins, callbacks, and
post-logout origins are selected. No public Keycloak route is authorized. The future
browser-authentication route remains separate from private administration and the
management listener.

## Stop conditions

Stop before executable source or runtime on a mutable image, local-development realm
copy, `start-dev`, seeded user, seeded credential, wildcard redirect/origin,
unselected callback, public administration, missing database recovery, secret value
in source, custom-theme claim against the official image, or unavailable break-glass
recovery.
