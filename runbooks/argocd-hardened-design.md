# Argo CD guarded private bootstrap

## Status and boundary

**PRIVATE RUNTIME LIVE/IDEMPOTENT; ORIGINAL SOURCE INCREMENT PRESERVED.** Chart
`10.3.0` and Argo CD `v3.5.0` are the pinned baseline. The exact 32-object closure
remains executable only through `ansible/bin/bootstrap-argocd check|apply` with the
three Infisical-owned Secret contracts. The original source increment made no live
call, but later separately approved check/apply/idempotence established the private
Argo core. Public exposure and omitted components remain blocked.

Helm is not a runtime reconciler. The pinned local Helm binary was used only to
render the vendored chart as offline evidence. Runtime reads the committed manifests
under `ansible/files/components/argocd/`; it never invokes Helm against the cluster.
`SOURCE-MAPPING.yml`, `CHART-RENDER-EVIDENCE-VALUES.yaml`, and
`MANIFESTS.sha256` bind the chart, transformations, and exact promoted leaves. The
mapping partitions every 35-object chart render identity into 24 promoted and 11
intentionally omitted identities; eight custom hardened identities complete the
32-object committed closure.

## Exact closure

The closure contains exactly three Argo CRDs, one deny-all `AppProject/default`,
seven ConfigMaps, four ServiceAccounts, two Roles, two RoleBindings, six NetworkPolicies, three ClusterIP
Services, three Deployments, and one StatefulSet. Ansible remains lifecycle owner of
the three CRDs and bootstrap owner of the exact namespaced objects until a later
evidenced object-by-object handoff stops Ansible reconciliation.

ApplicationSet runtime is absent. The committed render safely removes its Deployment,
ServiceAccount, Service, Role, and RoleBinding while retaining the ApplicationSet CRD
for API compatibility. Dex, notifications, commit server, metrics Services,
ServiceMonitors, hooks/jobs, Redis secret initialization, chart NetworkPolicies,
aggregate/ClusterRoles and bindings, Ingress/routes, and PVCs are absent. There are no
Application, ApplicationSet, Namespace, or Secret objects. The precreated default
project denies every source, destination, cluster resource, and namespaced resource;
it prevents the server's empty-install project-creation path without granting create
authority.

The retained minimal core is one application-controller StatefulSet, one repo-server
Deployment, one server Deployment, and standalone Redis. Argo uses
`quay.io/argoproj/argocd@sha256:521d6b62ecd0434c9cc6e9242a74f0e1137bb8fc0026b2c483ea88f3f17e725d`.
Redis uses
`docker.io/library/redis@sha256:c64af41b8fc06a2d9b8fde812dd781aa157bed6fcf8ae1656ad4e79f3f9fc9b1`.
Both are exact selected linux/amd64 children. Every container has resources,
non-root execution, RuntimeDefault seccomp, read-only root filesystem, no privilege
escalation, and all capabilities dropped. Repo-server and Redis receive no API token.

## Secret and administration contract

The source contains no Secret values or Secret objects. Bootstrap fails closed unless
these precreated objects exist in `argocd`, have exact type/key metadata and cryptographic value validity, and carry
`app.kubernetes.io/managed-by=infisical`, `app.kubernetes.io/part-of=argocd`, plus
`cristex.io/value-owner=infisical-cloud`:

| Secret | Type | Exact keys |
|---|---|---|
| `argocd-secret` | `Opaque` | `admin.password`, `admin.passwordMtime`, `server.secretkey` |
| `argocd-redis` | `Opaque` | `auth` |
| `argocd-server-tls` | `kubernetes.io/tls` | `ca.crt`, `tls.crt`, `tls.key` |

A no-log exact-scope action validates a generated/parseable canonical bcrypt
representation at cost 12 (using the pinned offline `bcrypt` dependency), strict UTC
RFC3339 password timestamp, minimum signing/Redis key lengths, and an exact one-CA,
one-leaf, one-private-key PEM closure with no residue or extra blocks. The private,
leaf, and CA keys must be RSA >=2048 or EC >=256; both certificate signatures must
use SHA-256, SHA-384, or SHA-512; the CA must have `BasicConstraints.ca` and
`KeyUsage.keyCertSign`; and both certificates must have at least 24 hours remaining.
The leaf validity must be contained by the issuer, its SAN set is exactly
`argocd-server.argocd.svc` and `localhost`, its only EKU is server authentication,
its public key matches the private key, and its signature is verified as a direct
issuance by the one supplied CA before any mutation.

### API-based dynamic Secret consumption

`argocd-server-tls` is consumed by the Argo CD server through the Kubernetes Secret
API, not as a projected pod volume. Official Argo CD `v3.5.0` source names this
Secret in [`externalServerTLSSecretName`](https://github.com/argoproj/argo-cd/blob/v3.5.0/util/settings/settings.go#L534-L535), calls
[`GetSecretByName`](https://github.com/argoproj/argo-cd/blob/v3.5.0/util/settings/settings.go#L810-L817) from
`updateSettingsFromSecret`, and passes its `tls.crt`/`tls.key` data to
[`loadTLSCertificate`](https://github.com/argoproj/argo-cd/blob/v3.5.0/util/settings/settings.go#L1771-L1819).
The certificate cache is keyed by the Secret name and `resourceVersion`, so a
settings refresh can observe a changed external Secret without a server volume
mount or pod restart. The committed `argocd-server` Role therefore grants only
`get`, `list`, and `watch` on Secrets; this read path is the intentional wiring.

The official [`v3.5.0` settings tests](https://github.com/argoproj/argo-cd/blob/v3.5.0/util/settings/settings_test.go#L1278-L1335) verify that
`argocd-server-tls` takes precedence over `argocd-secret`; the adjacent
[create/delete cases](https://github.com/argoproj/argo-cd/blob/v3.5.0/util/settings/settings_test.go#L1547-L1617) verify that changing the
external Secret changes the selected certificate on a subsequent settings read.
The offline contract test mirrors this evidence by asserting that
the server Deployment contains no `argocd-server-tls` volume reference and that
its Secret RBAC remains read-only.

The `tls-certs` volume mounted at `/app/config/tls` is intentionally different:
it sources the committed `argocd-tls-certs-cm` ConfigMap, which is Argo CD's
repository trust CA store for outbound repository TLS. It is not the server
certificate source and must not be replaced with `argocd-server-tls`. Keeping this
ConfigMap mount while leaving the external server Secret API-based preserves the
reviewed 32-object closure and runtime behavior.

`argocd-initial-admin-secret` must remain absent. Its presence is a stop condition.
Local administrator authentication is initially enabled; OIDC is not configured.
The public repository is `https://github.com/devraider/cristexweb.git` on `develop`,
so the later smoke proof needs no Git credential Secret. No Application is included
in this bootstrap.

All Services are ClusterIP. There is no Ingress, Gateway route, NodePort,
LoadBalancer, external IP, host port, Cloudflare route, or public DNS route. Private
administration is an authenticated k3s API port-forward bound to operator loopback
over Tailscale. Kubernetes NetworkPolicy does not govern node-to-local-pod traffic in
the same way as ordinary pod traffic; that behavior and TLS presentation require a
live positive/negative test before acceptance.

## Network and RBAC limits

A namespace-wide ingress/egress default deny covers every pod. Exact policies allow
controller and server to repo-server TCP 8081, controller/server/repo-server to Redis
TCP 6379, controller/server API-class TCP 443 and translated 6443, repo-server HTTPS
TCP 443, and DNS clients to CoreDNS UDP/TCP 53. Redis has no egress. No metrics port
has pod-origin ingress.

The peer-less TCP 443 and 6443 egress entries are deliberately described as port-only
controls. Standard NetworkPolicy cannot prove a Service name, FQDN, GitHub identity,
TLS identity, or host-process k3s API destination. They may allow arbitrary endpoints
on those ports. A live test must establish service-DNAT behavior and negatives;
strict identity isolation would require a separately selected proxy or FQDN-aware
policy system.

Only two namespaced Roles exist. Controller may read projects/configuration, observe
and update Application status/finalizers, write Events, and maintain a Lease. Server
has read-only Argo/configuration/Event access. Repo-server and Redis have no Role or
RoleBinding. No rule grants wildcard, delete, deletecollection, escalate, bind,
impersonate, token creation, Namespace/CRD mutation, or cluster-RBAC mutation. This
is idle-health authority, not database Application deployment authority; later exact
Application and target Namespace permissions require separate review.

## Guarded execution and stop conditions

The non-passthrough wrapper accepts only `check` or `apply`, uses the existing
root:k3s-admin mode-0640 kubeconfig without sudo, supplies a private single-run
attestation, and rejects task selection. The role checks the exact active Namespace,
source hashes, unique 32-object identity set, and the same exact Infisical-owned
target metadata contract used by the materializer (name, type, key set, labels, no
binary data, no immutability, and no owner references), plus initial-admin absence,
existing object ownership, and k3s/Tailscale health before mutation. The action plugin accepts
only canonical role-task calls, exact object canonical hashes, present-only arguments,
and the complete preflight binding. It has no deletion path. On an empty cluster,
check mode records the absent AppProject API and defers only that one unresolved
custom-resource dry run while still validating its source/hash/identity; it does not
mutate the CRD. Apply waits for all three CRDs to report `Established=True` before it
creates the deny-all default project or any other runtime object. Apply then rechecks
exact post-state and all four workload readiness states.

Stop on a missing or foreign Secret, initial-admin Secret creation, public exposure,
unknown/foreign object, hash drift, unexpected image or object, widened RBAC, failed
NetworkPolicy negative, unhealthy workload, k3s/Tailscale degradation, or credential
disclosure. Check, reviewed first apply, readiness, private TLS/login, API/HTTPS flow
positives and negatives, idempotent apply, recovery, and later Infisical rotation all
remain required. Rollback before runtime is Git revert; no runtime rollback is claimed.
