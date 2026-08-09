# Reactive Resume hosted architecture

## Status

**SOURCE POLICY ONLY — RUNTIME BLOCKED.** Reactive Resume is included in the
private DEV MVP. A future PROD instance remains separate and blocked until DEV soak,
recovery, and promotion gates pass. This increment adds no deployable workload and
claims no Namespace, database, identity client, Secret, route, or runtime state.

The canonical value-free contract is
[`reactive-resume-architecture.yml`](../ansible/files/policies/reactive-resume-architecture.yml).

## Source boundary

The local Compose tag, callback, credentials, and development issuer are not hosted
inputs. Repository-local Compose and realm assets remain development-only evidence
and must not be copied into hosted configuration. The official hosted repository,
version, immutable linux/amd64 digest, publisher/build trust, SBOM, vulnerability
disposition, off-node OCI recovery, and target pull/admission evidence remain
unselected.

GitHub Actions does not rebuild the upstream Reactive Resume image. It may validate
CristexHub-owned source and later publish CristexHub-owned images only. Reactive
Resume selection requires a separate registry-evidence review and explicit approval.

## Environment and database isolation

The private MVP places DEV Reactive Resume in `cristexhub-dev`; future PROD belongs
only in `cristexhub-prod`. The deployments must not share identity clients,
credentials, encryption/authentication values, database principals, migrations, or
backup scopes.

Both environments use the one general PostgreSQL engine in `shared-services`, but
each receives its own logical database, owner role, Infisical-owned credential,
migration scope, and backup scope. Keycloak retains a third dedicated PostgreSQL
scope. No environment receives another PostgreSQL engine or PVC. PostgreSQL grants
and negative cross-database tests, not Namespace labels or NetworkPolicy alone,
enforce logical isolation.

## Identity and secret ownership

Reactive Resume uses the shared Keycloak issuer through separate
`reactive-resume-dev` and `reactive-resume-prod` clients. Exact callbacks, web
origins, post-logout behavior, supported OIDC configuration, administrator recovery,
and positive/negative login evidence remain unresolved. Wildcards and local
callbacks are forbidden for hosted activation.

Infisical Cloud owns every runtime value. DEV and PROD use separate scopes and
machine identities. Git stores no OIDC client secret, database credential,
authentication secret, signing material, Universal Auth credential, or generated
value. Secret-zero recovery and rotation must pass before private DEV activation.

## Exposure and ownership

Initial DEV access remains private through the approved administrative path. No
Reactive Resume administration, database endpoint, NodePort, LoadBalancer, or public
route is approved. Any future browser route requires exact hostname/path review,
OIDC validation, negative administration/direct-origin checks, and separate approval.

Ansible is the bounded bootstrap installer. Argo CD may receive an exact namespaced
object set only after Ansible stops reconciling it and registration, adoption,
successful sync, and managed-field evidence pass. Dual reconciliation is forbidden.

## Promotion gates

Stop before executable source until all of the following are resolved:

1. exact immutable image source, compatibility, trust, SBOM/vulnerability review,
   off-node recovery, and target admission;
2. exact callbacks, origins, OIDC behavior, private administration, and break-glass;
3. PostgreSQL storage, grants, backups, encrypted off-node copy, and isolated restore;
4. Infisical Cloud scopes, Universal Auth recovery, rotation, and revocation;
5. resources, probes, security context, Service, TLS, and NetworkPolicy;
6. exact Ansible bootstrap closure and object-by-object Argo handoff;
7. separate check, apply, idempotence, Secret, database, and private runtime approvals.

No Deployment, StatefulSet, Service, PVC, Secret, Ingress, route, or Argo Application
is added by this increment. No registry, GitHub runner, host, Kubernetes API,
Infisical, database, or runtime operation was performed.
