# Requirements — k3s IaC foundation

## Discovery and safety

| ID | Requirement |
|---|---|
| KIF-001 | All host, cluster, and external discovery begins read-only and records curated, human-reviewed evidence before mutation; current host/cluster discovery is Ansible-first. |
| KIF-002 | Every mutating stage has explicit operator approval, a stop condition, and a rollback checkpoint. |
| KIF-003 | No disk format, namespace/PVC deletion, external destroy, secret export, or public cutover is used as an implicit setup or rollback step. |

## Repository and ownership

| ID | Requirement |
|---|---|
| KIF-004 | Future infrastructure source and runbooks live at repository-root `ansible/`, `opentofu/`, `kubernetes/`, and `runbooks/`; application source and local-runtime assets remain external. |
| KIF-005 | Ansible owns host configuration and is the selected bounded bootstrap installer for exact foundational Namespaces, the Infisical Cloud Kubernetes Operator, Argo CD, one self-hosted Keycloak, privileged CRDs/cluster RBAC, and Keycloak realm/client/group reconciliation; OpenTofu owns approved external resources; Argo CD owns namespaced desired state only after object-by-object handoff; Infisical Cloud owns secret values. Exact present-only source and a distinct guarded wrapper exist for `platform-secrets` and `platform-identity`, but their check/apply/idempotence remain separately approved and NOT RUN. Every component bootstrap requires its own exact source closure and approvals. Ansible must stop reconciling an object before registration/adoption/successful-sync evidence transfers it to Argo; dual reconciliation is forbidden. The completed `argocd`/`platform-edge` exception remains closed. |
| KIF-006 | The protective root `.gitignore` excludes the local `.venv`, Ansible collections/runtime data, generated state, plans, credentials, kubeconfigs, facts, local variable/override/crash files, and generated secrets, while `uv.lock` and `.terraform.lock.hcl` remain tracked. |

## Host and cluster

| ID | Requirement |
|---|---|
| KIF-007 | Ansible host changes are bounded, reviewable in check/diff mode, idempotent, and preserve SSH/Tailscale recovery access. |
| KIF-008 | The existing k3s datastore, exact Node kubelet version, CNI/interface indicators, NetworkPolicy objects, DNS, Traefik, StorageClass, disks, and resource capacity are discovered before design choices are applied; CNI behavior, NetworkPolicy enforcement, and component compatibility require later approved evidence and are not inferred from object listings alone. |
| KIF-009 | Bundled k3s Traefik remains the sole ingress controller until an explicitly approved replacement migration. |

## Networking and exposure

| ID | Requirement |
|---|---|
| KIF-010 | DEV, SSH, k3s API, Argo CD, dashboards, databases, brokers, Keycloak administration/management, and other administrative endpoints remain private through Tailscale or explicit port-forwarding. |
| KIF-011 | Only an approved PROD application hostname and a separately approved stable Keycloak browser-authentication issuer may become public through Cloudflare Tunnel to Traefik; neither authorization permits direct WAN origin exposure or any identity administration/management path. |
| KIF-012 | Every exposure has positive route/auth tests and negative public-reachability tests for all private surfaces; a later Keycloak browser-authentication route requires separate approval, exact auth-path closure, direct-origin closure, rollback evidence, and proof that identity administration and management remain private. |

## Secrets and identity

| ID | Requirement |
|---|---|
| KIF-013 | Git, OpenTofu state/plans, Argo parameters, CI logs, examples, and documentation contain no plaintext runtime secret values. |
| KIF-014 | Infisical Cloud initially provides separate DEV, PROD, and infrastructure scopes/identities with least-privilege Kubernetes service accounts; only its Kubernetes Operator is bootstrapped and self-hosted Infisical is deferred. Keycloak authenticates and emits groups, Argo RBAC authorizes Argo actions, and Kubernetes RBAC independently constrains controllers; direct Argo OIDC is intended with Dex absent. |
| KIF-015 | Bootstrap credentials, Keycloak administrator and OIDC client material, Infisical machine authentication, and application encryption keys have documented, off-node, tested recovery and rotation procedures. |

## Environment and data isolation

| ID | Requirement |
|---|---|
| KIF-016 | The cluster uses separate `argocd`, `platform-edge`, future `shared-services`, `cristexhub-dev`, and `cristexhub-prod` namespaces; exact `platform-secrets` and `platform-identity` manifests exist but runtime remains separately approved and NOT RUN; applications retain separate DEV/PROD credentials, migrations, and backup paths. |
| KIF-017 | Shared PostgreSQL provides separate DEV/PROD databases and owner roles; each role is denied access to the other environment. |
| KIF-018 | Shared MongoDB provides separate DEV/PROD databases and users; each user is denied access to the other environment. |
| KIF-019 | Shared-engine failure and contention risks are documented, bounded with requests/limits/connection limits, and accepted before PROD. |
| KIF-020 | Redis is environment-local; any shared RabbitMQ uses separate users/vhosts, limits, and negative cross-access tests. |
| KIF-021 | NetworkPolicy and RBAC deny unapproved cross-namespace and control-plane access while allowing required DNS and service flows. |

## Delivery

| ID | Requirement |
|---|---|
| KIF-022 | GitHub Actions validates and builds but does not deploy directly; Argo CD reconciles reviewed Git desired state. |
| KIF-023 | Workloads deploy immutable image digests or commit-SHA references and never deploy `latest`. |
| KIF-024 | The same built image digest is validated in DEV before reviewed promotion to PROD. |
| KIF-025 | DEV acceptance and soak precede PROD creation; private PROD acceptance precedes Cloudflare public cutover. |

## Backup, recovery, and operations

| ID | Requirement |
|---|---|
| KIF-026 | Database-consistent, encrypted backups are separated by environment or identity purpose, retained locally and off-node, integrity checked, and copied without destructive mirror semantics; Keycloak uses application-consistent `pg_dump`, not live-volume synchronization or realm export as backup. |
| KIF-027 | An isolated restore proves the declared RPO/RTO before PROD acceptance; a successful backup exit code alone is insufficient. |
| KIF-028 | Recovery covers k3s datastore/token, protected host-local single-writer OpenTofu state through encrypted timestamped off-node copies and independent key custody, Infisical bootstrap material, Keycloak database/realm/admin/OIDC material, application encryption keys, desired state, and mutable application data. |
| KIF-029 | Resource headroom, disk usage, certificate/tunnel health, workload health, and backup freshness have bounded monitoring before public PROD. |
| KIF-030 | Every phase records actual commands/results, revisions/digests, residual risks, and rollback evidence without leaking sensitive values. |

## Traceability

`tasks.md` references these requirement IDs by stage. `testcases.md` maps every ID
to offline, integration, security, recovery, or manual evidence. The current
Ansible discovery satisfies its offline, syntax/lint, approved host-access,
dependency-bootstrap, curated host/cluster-indicator, and functional
CNI/NetworkPolicy enforcement gates. The separately approved schema-v3 discovery
captured kubelet `v1.36.2+k3s1`, all 15 bounded queries available, and the current
`shared-services` PVC query with count zero. Argo CD `3.5`'s official tested matrix
contains target minor `1.36`, chart `10.3.0` admits the target, the exact 44-document
render reproduced at Kubernetes capability `1.36.2`, stable upstream API registration
screened successfully, and controller-side image closure was reachable. Exact k3s
admission/runtime and node pullability remain unproven. The deployable-but-not-run
[foundation Namespace bootstrap](../../runbooks/foundation-namespace-bootstrap.md)
maps KIF-002, KIF-005, KIF-006, KIF-010, KIF-016, and KIF-030 to exact present-only
source while retaining separate check/apply/idempotence approvals. The source-only
[Argo CD candidate provenance record](../../runbooks/argocd-candidate-provenance.md)
binds public chart, captured signature/hash-binding, image, online/static API, RBAC,
network, private-Git, and adoption evidence for KIF-005, KIF-008, KIF-010, KIF-013,
KIF-015, KIF-021, KIF-023, and KIF-030 without selecting a version, closing its
security/Secret/adoption gates, or adding deployable source. The separate
[source-only Argo CD hardened design](../../runbooks/argocd-hardened-design.md)
maps the private exposure, stop/rollback, ownership, RBAC, policy, secret-custody,
and evidence direction to KIF-002, KIF-003, KIF-005, KIF-008, KIF-010, KIF-013
through KIF-015, KIF-021, and KIF-030. It accepts ClusterIP/loopback-only
administration, quiescent retained ApplicationSet, supplemental default-deny with a
truthful broad ports-only weakness, one-repository read-only GitHub App credentials,
value-free Infisical custody, disabled Redis initialization, and two independent
adoption Applications as design only. Ansible is selected as bounded bootstrap
installer and privileged lifecycle owner. Component source/credentials, the
separately approved NOT-RUN foundation Namespace checkpoints,
resource/GVR/discovery inventory, Infisical authentication/recovery, live adoption
apply mode, and stable Keycloak OIDC remain six open architecture decisions;
selection, component source, admission, runtime, and handoff
gates also remain open. The source-only
[Keycloak OIDC bootstrap design](../../runbooks/keycloak-oidc-bootstrap-design.md)
maps KIF-002, KIF-003, KIF-005, KIF-010, KIF-012 through KIF-016, KIF-021, KIF-023,
and KIF-026 through KIF-030 to one future shared self-hosted identity architecture
target. It distinguishes Keycloak authentication/groups, Argo RBAC, and Kubernetes
RBAC; retains direct OIDC with Dex absent, private administration, Infisical-owned
client secrets, dedicated PostgreSQL, encrypted off-node backup/isolated restore,
and object-by-object handoff. It selects no Keycloak release/image/package,
database version, hostname, route, credential, or deployable source; runtime remains
**NOT RUN**. The source-only
[cloudflared candidate provenance record](../../runbooks/cloudflared-candidate-provenance.md)
binds exact release/source/image, token-file, health, and edge-transport evidence for
KIF-005, KIF-011, KIF-013, KIF-015, KIF-021, KIF-023, and KIF-030 while explicitly
leaving publisher trust, image assurance/availability, hardening, secret recovery,
external-resource state, policy, route, and runtime gates blocked. It selects no
version and adds no deployable source. The source-only
[Infisical Operator candidate provenance record](../../runbooks/infisical-operator-candidate-provenance.md)
binds the observed `v0.11.8` public distribution gap and the last observed
version-aligned `v0.11.7` chart/source/image evidence for KIF-005, KIF-013 through
KIF-015, KIF-021, KIF-023, and KIF-030. It selects neither version, adds no deployable
source, and leaves chart/CRD/API compatibility despite the now-captured target,
trust, Namespace, scoped-RBAC, Argo handoff, secret-zero/recovery, traffic,
single-node, and runtime gates blocked. Exact
platform Namespace source and its bounded bootstrap pass offline contracts; the
separately approved wrapper check predicted exactly `argocd` and `platform-edge`
without mutation, and the separately approved first apply created and verified those
exact Active Namespaces with the reviewed labels and preserved service health. The
separately approved idempotence checkpoint had one credential failure before service
preflight or Kubernetes reconciliation (`changed=0`, no mutation), then passed on
retry at `ok=21 changed=0 unreachable=0 failed=0 skipped=0` with exact post-state and
service-health verification. The foundation does not satisfy replacement-host
recovery, general host-baseline, or later platform
mutation gates. Unresolved storage, secret bootstrap, and RPO/RTO
choices remain decision gates rather than implied requirements.
