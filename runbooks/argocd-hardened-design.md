# Argo CD hardened design

## Status and boundary

**DESIGN ONLY — SOURCE BASELINE SELECTED.** Chart `10.3.0` and Argo CD
`v3.5.0` are selected only for offline source authoring. They remain **NOT
DEPLOYABLE**, and Argo CD runtime remains **NOT RUN/BLOCKED**.

This source-only record accepts a hardened design direction. It does not authorize
bootstrap, contact the cluster, or add a values file,
rendered YAML, manifest, Secret, Application, AppProject, NetworkPolicy, RBAC object,
GitHub resource, Infisical resource, route, or other deployable source. Ansible is
selected as the future bounded bootstrap installer and lifecycle owner of privileged
CRDs and cluster RBAC; exact source, credentials, approvals, proposed future
Namespaces, and runtime evidence remain unresolved.

## Private administration and exposure

Every Argo Service remains `ClusterIP`. The design contains no Ingress, Gateway API
route, Traefik route, NodePort, LoadBalancer, `externalIPs`, host port, Cloudflare
route, or public DNS route. Initial administration follows this private path:

`authorized operator device -> Tailscale -> authenticated k3s API -> loopback-only Kubernetes port-forward -> argocd-server`

The port-forward must bind only to the operator's loopback interface and must stop at
the end of the administrative session. No executable invocation or address is
committed here. Kubernetes authentication, a narrowly authorized port-forward
permission, and Argo authentication remain independent controls. Server TLS remains
enabled; certificate bypass is not a routine access method. Port-forward behavior
through kube-router and the future default-deny policy remains a live acceptance gate,
not an assumed success.

Dex and notifications remain absent. Metrics Services and ServiceMonitors remain
absent. UI exec, extensions, public webhooks, and public administration remain
disabled. Direct OIDC to the selected shared Keycloak is the selected direction,
but external identity-provider egress remains disabled until its stable issuer,
callback, TLS, NetworkPolicy, Secret, and positive/negative authorization evidence
are separately designed and approved.

## Retained quiescent ApplicationSet

Chart `10.3.0` cannot disable ApplicationSet through an effective parent enable gate,
so the controller is retained with `allowAnyNamespace=false`. SCM providers and
credentialed generators remain disabled. The controller begins quiescent: it receives
no Application create, update, or delete permission, no Secret read permission, and
only exact leader-election and status permissions proven necessary by later evidence.

Webhook exposure and use are disabled, but the listener is not absent. The retained
controller still starts its webhook listener and the chart still renders its
`ClusterIP` Service on TCP `7000`. No credential, Ingress, HTTPRoute, ListenerSet,
Traefik route, Cloudflare route, or pod-origin ingress allowance reaches it. Removing
the listener or Service would require a separately reviewed packaging change.

## Supplemental network-policy design

Every chart-generated component NetworkPolicy must be disabled. Kubernetes policy
allows are combined by union, so adding stricter policies cannot repair a permissive
chart policy. A future supplemental set owns the complete policy boundary:

- one namespace-wide default-deny selects every `argocd` pod for both ingress and
  egress;
- component allows select exact labels from the reviewed hardened render;
- controller, server, repo-server, and ApplicationSet receive UDP/TCP `53` egress
  only to CoreDNS pods selected in `kube-system`; the exact CoreDNS labels require
  read-only target verification;
- Redis receives no DNS allowance and no egress;
- metrics ports `8082`, `8083`, and `8084` receive no pod-origin ingress;
- ApplicationSet ports `7000`, `8080`, and `8081` receive no pod-origin ingress;
- no ApplicationSet-to-Redis flow exists; and
- image acquisition remains node/containerd traffic outside pod NetworkPolicy.

### Component flow closure

| Flow | Protocol and port | Design purpose |
|---|---|---|
| server to repo-server | TCP `8081` | Reviewed repository and render requests |
| application-controller to repo-server | TCP `8081` | Manifest generation |
| ApplicationSet to repo-server | TCP `8081` | Approved non-SCM generator support |
| server to Redis | TCP `6379` | Session and cache traffic |
| application-controller to Redis | TCP `6379` | Controller cache traffic |
| repo-server to Redis | TCP `6379` | Repository cache traffic |
| server to API class | TCP `443` and conservative translated TCP `6443` | Argo control-plane access |
| application-controller to API class | TCP `443` and conservative translated TCP `6443` | Watches and reconciliation |
| ApplicationSet to API class | TCP `443` and conservative translated TCP `6443` | Bounded Argo-resource reconciliation |
| repo-server to approved HTTPS | broad TCP `443` | Exact private repository and reviewed HTTPS dependencies |
| server to selected OIDC issuer | conditional future TCP `443` | Direct OIDC discovery, code exchange, and key retrieval only after identity approval |
| DNS clients to CoreDNS | UDP/TCP `53` | Name resolution for controller, server, repo-server, and ApplicationSet |
| loopback port-forward to server | node-origin stream to TCP `8080` | Private UI, API, and gRPC administration |

The TCP `443` and `6443` rules are peer-less, ports-only allowances because standard
NetworkPolicy cannot identify the host-process k3s API, a Kubernetes Service name,
dynamic Git endpoints, FQDNs, or TLS identities without committing target-specific
addresses. They permit arbitrary destinations on those ports. This is explicit port
isolation, not GitHub isolation, Kubernetes-Service isolation, FQDN isolation, TLS
identity isolation, or endpoint isolation. Whether kube-router enforces policy before
or after Kubernetes Service DNAT—and therefore observes API traffic on Service port
`443`, translated port `6443`, or both—remains unproven. A separately approved live
positive/negative acceptance must prove that behavior; failure is a stop condition.
Strict endpoint isolation would require a separately selected authenticated egress
proxy, mirror, or FQDN-aware policy system.

The Redis initializer is disabled in the selected design through
`redisSecretInit.enabled=false`, and `argocd-redis` must be precreated through the
approved secret custody path. A retained initializer in a future render is a stop condition.
If a temporary initializer is ever separately approved, default-deny must cover it
and allow only DNS plus API-class egress for its bounded lifetime.

## Phased RBAC and AppProject design

AppProject policy and Kubernetes RBAC are independent enforcement layers. Kubernetes
RBAC must be equal to or narrower than the matching AppProject resource policy.
Neither layer may contain wildcard source repositories, destinations, API groups,
resources, verbs, or non-resource URLs.

### Privileged installation boundary

Ansible is selected for a future bounded privileged installation phase, which still
requires a dedicated exact source closure and separate check, apply, and idempotence
approvals. Its short-lived bootstrap credential is never mounted in an Argo pod and
is revoked after the window. Ansible remains lifecycle owner of Argo CRDs,
ClusterRoles, and ClusterRoleBindings unless a later explicit decision replaces it.
Argo must not update its own cluster authorization by default because that would
permit privilege escalation.

### Runtime identities

- The application-controller receives inventory-derived read permissions and
  namespace-specific RoleBindings only after exact resource evidence exists.
- The server does not receive the chart's broad ClusterRole. Its Kubernetes access is
  limited to exact Argo control-plane reads and any exact-name Application operation
  later proven necessary.
- Repo-server has a dedicated ServiceAccount, no API token, no Role, and no
  RoleBinding.
- ApplicationSet remains quiescent under its exact leader-election/status boundary.
- Redis has no API access and no mounted API token.

Initial runtime rules omit `delete`, `deletecollection`, `escalate`, `bind`,
impersonation, service-account token creation, Namespace creation, CRD mutation,
webhook mutation, and cluster-RBAC mutation. No runtime identity may create future
Namespaces. Destructive verbs can be considered only per exact namespaced kind after
prune and rollback acceptance; Kubernetes RBAC cannot limit deletion to Argo-tracked
objects.

### Project model

The built-in `default` AppProject becomes effective deny-all before any Application
exists. Future Projects use exact repository URLs, exact local-cluster destinations,
positive kind allowlists, orphan warnings, and no unrestricted role:

| Project | Initial posture |
|---|---|
| `namespace-adoption` | Only the Namespace kind; Kubernetes RBAC restricts names to `platform-edge` and `argocd` |
| `argocd-system` | Disabled pending safe self-management split; no cluster authorization |
| `platform-edge` | Exact approved cloudflared namespaced kinds only |
| `shared-services` | Disabled until Namespace creation and exact stateful inventory are approved |
| `cristexhub-dev` | Exact DEV namespaced kinds only; no cluster resources |
| `cristexhub-prod` | Exact PROD namespaced kinds with a distinct manual promotion role |

Ordinary users cannot manage AppProjects, ApplicationSets, repositories, cluster
credentials, extensions, exec, overrides, or certificates. Git writers remain
deployment authorities within the combined repository, Project, and Kubernetes RBAC
boundary. One shared controller identity remains a common DEV/PROD compromise domain;
this design does not misrepresent AppProjects as hard isolation.

## Private Git and value-free secret custody

The selected design would use one private GitHub App scoped to exactly one future
selected private repository. It receives repository `Contents: read-only` and no write,
administration, webhook, organization, Actions, or unrelated permission. Argo uses
the canonical HTTPS repository URL with normal TLS verification and one direct,
project-scoped `repository` Secret; no broad `repo-creds` prefix template is used.
The repository identity, Secret object, private key, IDs, and every credential value
are absent from this increment.

A value-free custody ledger covers only object names, expected key names, writer and
value-owner identities, expiry, recovery custodians, rotation state, and boolean
validation results. It never records values, encodings, low-entropy hashes, command
arguments, environment examples, or matching disclosure context.

| Material | Bootstrap direction | Steady-state direction |
|---|---|---|
| `argocd-secret` and signing key | Precreated by an approved temporary writer | One exact Infisical-owned target after cutover |
| One-time local administrator state | Preseeded without exposing plaintext | Disabled only after an independent administration and break-glass path passes |
| `argocd-redis` | Precreated before workloads; initializer disabled | One exact Infisical-owned target with coordinated rotation |
| `argocd-server-tls` | Dedicated precreated TLS material | One exact Infisical-owned target with independent renewal and recovery |
| Direct repository credential | Injected only after Argo is healthy without Git | Infisical-owned successor GitHub App key after fresh-read proof |
| Direct Keycloak OIDC client | Absent until stable issuer and Keycloak readiness pass | Infisical-owned client secret after OIDC positive/negative and recovery proof |
| Infisical authentication | Separate out-of-band bootstrap custody | Independently recoverable; never dependent only on Infisical itself |

`argocd-initial-admin-secret` must remain absent; unexpected creation stops the
bootstrap. Chart ownership must not overwrite Infisical-owned Secrets. The temporary
writer is single-run, name/key bounded, time bounded, and stopped before Infisical
takes one target at a time.

Git credential handoff uses overlapping GitHub App keys. Infisical receives only the
successor; a deliberately fresh repository read of the reviewed revision must pass,
negative scope and disclosure checks must pass, and only then may a separately
approved revocation remove the predecessor. Independent encrypted off-node custody
must recover the GitHub App, internal signing, TLS, Redis, administrator, and
Infisical bootstrap materials without the lost node.

## Two-Application Namespace adoption

The recommended design uses two future adoption Applications: one renders only
`platform-edge`, and one renders only `argocd`. The current directory renders both
Namespace files together, so separate reviewed source entry points are required in a
later deployable-source change. Permanent selective sync is not a substitute.

Both Applications are registered without sync. Automated sync, prune, self-heal,
Application finalizers, `CreateNamespace`, managed namespace metadata, `Replace`,
`Force`, cascading deletion, and shared-resource acceptance remain disabled. No
server-side-apply choice is made. First-sync apply mode remains unresolved until live
UID, phase, deletion state, finalizers, labels, annotations, tracking identity,
managed fields, last-applied state, installation ID, resource tree, and diff evidence
are reviewed.

Adoption order is `platform-edge` first, followed by a freeze and evidence review,
then `argocd`. Each pass requires exactly one Namespace in the resource tree,
unchanged UID, `Active` phase, no deletion timestamp, all three committed labels,
preserved unrelated metadata, matching tracking identity, healthy k3s/Tailscale, and
no other mutation. Only successful sync evidence may establish Argo ownership; the
existing desired-owner label remains intent and the bootstrap-writer label remains
historical provenance.

## Stop and rollback

Future work stops on secret disclosure, public Argo reachability, unexpected render
or object, an unexpected writer, any chart-generated permissive NetworkPolicy,
GitHub repository or permission widening, unreviewed privilege, mixed Redis
credentials, missing recovery custody, Namespace UID/deletion/phase change,
protected metadata loss, or any prune/cascade/replace/force proposal.

Routine rollback never deletes or recreates a Namespace, performs a release-wide
uninstall, cascades Application deletion, prunes, replaces, forces, or revokes a
working predecessor before successor acceptance. Before first sync, Application
removal must preserve resources. Secret rollback restores a still-valid predecessor
through the bounded temporary writer and verifies dependent behavior; a compromised
predecessor is replaced rather than restored.

This source-only increment has only Git revert as rollback. There is no runtime
rollback because no runtime action occurred.

## Open architecture decisions

| ID | Decision | Why still open |
|---|---|---|
| D1 | Exact Ansible controller bootstrap closure and credentials | Vendored public chart inputs exist, but exact rendered objects, credential lifetime, escalation controls, and separate approvals remain undefined |
| D2 | Foundation Namespace runtime checkpoints | Exact `shared-services` check and separately approved first apply passed; idempotence remains separately approved and NOT RUN, every component remains undeployed, and the earlier exception remains closed |
| D3 | Exact resource, GVR, and discovery inventory | Runtime Roles and Projects cannot be authored safely before every required kind and discovery path is enumerated |
| D4 | Infisical Universal Auth and independent recovery | Universal Auth is selected as direction, but exact scope, custodians, rotation/revocation proof, RPO/RTO, and isolated recovery remain unproven |
| D5 | Live Namespace-adoption apply mode | Managed-field, tracking, last-applied, and diff evidence is unavailable until a separately approved read-only checkpoint |
| D6 | Activate selected Keycloak/Argo OIDC policy | Issuer, client ID, groups, and deny-default mappings are selected; private callback/origin, TLS, materialized value, negative authorization, logout, and recovery evidence remain absent |

## Closure

The private ClusterIP/loopback-only administration model, quiescent retained
ApplicationSet, supplemental default-deny policy model, explicit ports-only weakness,
phased least-privilege direction, exact one-repository GitHub App model, value-free
secret custody, and two-Application adoption recommendation are accepted design
directions only. Version choice and public chart-byte availability are resolved for
offline source authoring; trust acceptance, exact deployable RBAC/policy inventory,
the six decisions above, target admission, node pullability, installation, runtime
behavior, recovery rehearsal, and ownership handoff remain open.
