# Single-node k3s architecture plan

## Status

This target design has five bounded Ansible implementations: read-only discovery,
the executed Kubernetes-module dependency bootstrap, and executed group-scoped
k3s administrator access under `ansible/`; effective-user readability,
fresh-session cluster listing, and idempotence passed. The executed user-scoped
kubectl client-defaults playbook also passed warning-free fresh-session queries and
idempotence. The approved one-reboot recovery playbook is implemented but not run.
They are not a general host
baseline, hosted runtime, or IaC reconciler.
Python is limited to offline contract tests. No hosted orchestration,
DNS, tunnels, GitOps, secrets, databases, backups, or recovery are implemented.
CristexHub local Compose assets remain an external application-repository concern.

## Known facts

A read-only host inspection observed a Debian 13 single-node k3s server with about
16 GiB RAM, an NVMe system disk, a separate unmounted 1 TB NTFS disk, and Tailscale
installed. k3s is active. Approved elevated discovery has reverified the datastore,
node, Traefik, local-path StorageClass, and curated kube-system workload indicators
through the root-only kubeconfig. CNI behavior, NetworkPolicy enforcement, and
recovery access still require separate approved verification.

The external CristexHub application repository publishes backend, frontend, and
code-runner images to GHCR. This repository implements Ansible discovery, the
reviewed dependency bootstrap, and the bounded k3s administrator access playbook;
it still has no Kubernetes desired state, Helm, Kustomize, OpenTofu, GitHub Actions,
or general host baseline. Debian plus Ansible is the
selected host-configuration owner.

## Goals

- Teach one infrastructure layer at a time without an enterprise-sized platform.
- Reproduce host intent, external resources, and Kubernetes desired state from Git.
- Keep DEV and all administrative surfaces private.
- Expose only approved PROD application routes through Cloudflare Tunnel.
- Fit DEV and PROD within one resource-constrained node using explicit limits.
- Recover on replacement hardware from Git, secret recovery material, images, and
  verified off-host backups.

## Non-goals

- high availability or zero downtime;
- a second ingress controller, service mesh, Longhorn, or autoscaling platform;
- public databases, brokers, Argo CD, k3s API, SSH, or dashboards;
- self-hosted secrets, registry, or CI runner during the first implementation;
- automatic PROD promotion or destructive automatic rollback;
- moving privileged code-runner onto the shared node without separate isolation.

## Ownership model

| Layer | Owner | State source |
|---|---|---|
| Debian host and k3s baseline | Ansible | playbooks and inventory under `ansible/` |
| Cloudflare and GitHub resources | OpenTofu | configuration under `opentofu/` plus protected remote state |
| Kubernetes objects | Argo CD | manifests and Helm values under `kubernetes/` |
| Secret values and rotation | Infisical Cloud initially | separate DEV, PROD, and infrastructure scopes |
| CI and image publication | GitHub Actions | workflows and immutable GHCR digests |
| Approvals and recovery | Human operator | reviewed evidence and runbooks |

One resource has one owner. OpenTofu must not reconcile Kubernetes resources also
owned by Argo CD. GitHub Actions validates and publishes; it does not deploy.
Operational procedures belong under `runbooks/` when implementation is approved.

## Traffic model

```text
Private administration and DEV
operator device -> Tailscale -> SSH/k3s API or an explicitly private service

Public PROD
Internet -> Cloudflare -> cloudflared -> bundled Traefik -> PROD frontend gateway
```

Bundled k3s Traefik remains the sole ingress controller. The frontend nginx image
in the external CristexHub application repository remains the application gateway
for `auth_request`, API proxying, and WebSockets; it is not the cluster ingress
controller. Application source, local Compose, Keycloak theme, and Browserless
gateway assets remain in that application repository and are not owned here.

The first private DEV hostname may use a tailnet name. A custom private
`dev-hub.cristex-soft.com` name requires a later private-DNS and certificate
decision. The intended public PROD host is `hub.cristex-soft.com`.

Cloudflare Tunnel must never route DEV, SSH, k3s API, Argo CD, databases, Redis,
RabbitMQ management, Browserless, code-runner, or identity administration.
Cloudflare and Tailscale do not replace application OIDC/JWT enforcement.

## Namespace model

| Namespace | Purpose |
|---|---|
| `argocd` | Argo CD controllers and private UI/API |
| Infisical operator namespace | Secret synchronization controller; exact name follows the selected chart |
| `shared-data` | Shared PostgreSQL and MongoDB engines only |
| `cristexhub-dev` | DEV applications and environment-local dependencies |
| `cristexhub-prod` | PROD applications and environment-local dependencies |
| Optional backup/monitoring namespaces | Added only when their first workload is approved |

Namespace names organize ownership but are not a hard security boundary. Service
accounts, RBAC, NetworkPolicy, database authorization, credentials, and negative
connectivity tests provide the enforceable controls.

## Shared data design

A single PostgreSQL engine and a single MongoDB engine save memory. This is an
explicitly accepted shared failure and contention domain.

PostgreSQL requires separate databases and owner roles, including at minimum
`cristexhub_dev` and `cristexhub_prod`. MongoDB requires separate databases and
users with privileges limited to their own database. DEV and PROD never share an
application credential, encryption key, migration target, or backup prefix.

The application role must not create roles or databases. A bounded, idempotent,
Argo-managed provisioning job or a later approved operator creates principals from
Infisical references. Its administrator credential is not available to application
pods.

Redis remains per environment because Redis database numbers are not sufficient
security isolation. A shared RabbitMQ is permitted only with distinct users,
virtual hosts, limits, and negative access tests. A later capacity decision may
separate it.

NetworkPolicy must allow each application namespace to reach only its own approved
database endpoints and deny cross-environment application traffic. Database engines
remain ClusterIP-only.

## Secrets

Infisical Cloud stores values during the initial implementation; self-hosting is
out of scope. Git stores only secret references. DEV, PROD, and infrastructure use
separate scopes and machine identities with least privilege. The bootstrap method
is a decision gate because Argo private-repository access, Infisical
authentication, GHCR pulls, and Cloudflare connector credentials form a secret-zero
sequence.

Secret values must not pass through OpenTofu state, saved plans, Argo parameters,
committed manifests, examples, or CI logs. Recovery material, including application
encryption keys, is stored off-node in at least two protected locations.

## Delivery flow

```text
Pull request -> tests and offline IaC validation
merge -> build once -> push SHA-tagged image to GHCR
reviewed Git change -> pin image digest in DEV
Argo CD -> reconcile DEV -> validate and soak
reviewed promotion -> same digest in PROD
Argo CD -> private PROD validation -> approved Cloudflare cutover
```

`latest` may be published for compatibility but must never be deployed. Initial
PROD sync and promotion remain manual and reviewed.

## Storage and backup

Live database PVCs are expected on the NVMe through the discovered local
StorageClass. The separate 1 TB disk is not usable until its contents, ownership,
filesystem choice, mount path, and destructive formatting approval are confirmed.

Backups require database-consistent PostgreSQL and MongoDB dumps, separate DEV/PROD
paths, compression, encryption, integrity checks, local retention, and an encrypted
off-host copy. The intended off-host target is Google Drive through containerized
`rclone copy`, not destructive `sync`. k3s datastore and recovery token, OpenTofu
state, Infisical recovery credentials, and runbooks require separate recovery
coverage.

A successful backup job is not acceptance. An isolated restore and application
verification must meet the declared RPO/RTO before PROD.

## Staged delivery

### Stage 0 — documentation foundation

- Entry: approved technology direction.
- Work: rules, architecture, requirements, tasks, and tests only.
- Gate: offline documentation checks and independent review.
- Stop: any wording claims an implemented hosted environment.
- Rollback: revert documentation changes.

### Stage 1 — read-only discovery

- Entry: the offline Ansible discovery implementation is approved; actual SSH,
  host, cluster, or elevated access still requires its own explicit approval.
- Work: use Ansible built-ins for bounded host facts and
  `kubernetes.core.k8s_info` for exact Kubernetes kinds. Project only curated OS,
  capacity, service, filesystem, datastore-presence, and object-name/count fields
  into one controller-local report.
- Safety: the play requires check/diff mode, an explicit one-host limit, default
  non-elevation, and two explicit flags before narrowly scoped become tasks. It
  never uses shell/command automation or queries Secret, ConfigMap, Events, or a
  broad `all` resource set.
- Limit: object listings are configuration/capability indicators only. CNI behavior
  and NetworkPolicy enforcement require later approved functional probes and are
  not proven by discovery.
- Current evidence: the locked local environment, syntax, lint, and non-elevated
  one-host report pass. The approved bootstrap directly requested only
  `python3-kubernetes` and `python3-jsonpatch`; apt installed 37 packages including
  dependencies, and post-install imports pass. The
  elevated report confirms the datastore and nine available exact Kubernetes
  queries. CNI behavior, NetworkPolicy enforcement, and recovery remain unproven.
- Gate: human-reviewed local report and decision register update.
- Stop: a task needs mutation, secret output, or elevated access beyond the two
  approved dependency packages and discovery scope.
- Rollback: the only approved target-state change is the recorded apt transaction.
  Any package removal requires a separately reviewed apt plan; do not remove
  transitive packages blindly. The discovery play's only write is the explicitly
  requested controller-local report.

### Stage 2 — host safety baseline

- Entry: recovery access, current backup, and reviewed Ansible check/diff.
- Work: bounded SSH, firewall, mount, kubeconfig, and k3s configuration changes.
- Gate: second Ansible run is idempotent; SSH and Tailscale recovery survive reboot.
- Stop: loss of access, unexpected package/network change, or disk ambiguity.
- Rollback: restore preserved host configuration and known-good access path.

### Stage 3 — external-resource preparation

- Entry: protected OpenTofu state backend, least-privilege credentials, reviewed plan.
- Work: Cloudflare/GitHub resources only; no public route yet.
- Gate: plan contains only approved resources and state recovery is tested.
- Stop: secret value in state/plan or destructive replacement.
- Rollback: reviewed reverse plan; never blind destroy.

### Stage 4 — minimal GitOps and secrets bootstrap

- Entry: pinned versions and approved secret-zero procedure.
- Work: bounded Argo CD bootstrap, private repository access, Infisical operator,
  and one non-sensitive demonstration secret.
- Gate: Argo is private, reconciles a demo workload, and secret values remain absent
  from Git/logs.
- Stop: admin endpoint becomes public or bootstrap credentials cannot be recovered.
- Rollback: uninstall only newly bootstrapped stateless controllers after evidence
  capture; preserve data and access.

### Stage 5 — isolation and shared data

- Entry: StorageClass, capacity, backup, and resource-limit decisions approved.
- Work: namespaces, service accounts, RBAC, NetworkPolicy, PostgreSQL, MongoDB,
  principals, and environment-local Redis.
- Gate: positive own-environment access, negative cross-environment access, backup,
  and isolated restore all pass.
- Stop: cross-access succeeds, backup cannot restore, or node pressure is unsafe.
- Rollback: restore verified data/config; never delete PVCs as routine rollback.

### Stage 6 — DEV

- Entry: shared-data gate passes.
- Work: deploy the minimum CristexHub DEV slice privately and add services only after
  measuring capacity.
- Gate: authentication, API, workers, migrations, resource headroom, and rollback to
  a prior digest pass during soak.
- Stop: migration ambiguity, excessive pressure, or any public DEV route.
- Rollback: Git revert to verified digest/config and restore data if required.

### Stage 7 — backup and recovery rehearsal

- Entry: stable DEV and declared RPO/RTO.
- Work: scheduled dumps, encryption, local retention, off-host copy, clean-host
  reconstruction steps, and restore rehearsal.
- Gate: recovery evidence proves secrets, desired state, mutable data, and access can
  be restored independently.
- Stop: backup exists only on the node or recovery depends on unavailable secrets.
- Rollback: disable the new schedule without removing retained backups.

### Stage 8 — private PROD

- Entry: DEV soak and recovery gates pass; explicit operator approval.
- Work: separate PROD credentials/data and the same verified image digest, reachable
  privately only.
- Gate: PROD isolation, auth, smoke, resource, backup, restore, and rollback pass.
- Stop: DEV can reach PROD or any PROD admin/data endpoint is public.
- Rollback: Git revert and verified data recovery procedure.

### Stage 9 — public PROD cutover

- Entry: private PROD accepted and external exposure review approved.
- Work: Cloudflare Tunnel route for the explicit PROD application hostname.
- Gate: external tests show PROD works while DEV/admin/data endpoints remain
  unreachable; direct WAN ports remain closed.
- Stop: unintended route, auth bypass, or direct-origin exposure.
- Rollback: remove/disable only the reviewed route and verify private PROD remains.

## Decision register

Implementation is blocked until each relevant item is resolved:

- Infisical Cloud bootstrap authentication, export/recovery, and machine-identity rotation;
- Argo CD private-repository bootstrap and recovery;
- OpenTofu encrypted remote state, locking, and recovery;
- Cloudflare connector ownership and credential rotation;
- current k3s datastore, CNI indicators, NetworkPolicy objects and later enforcement
  probes, DNS, Traefik, StorageClass, and firewall;
- live PVC placement and approved use of the 1 TB disk;
- backup retention, encryption, Google Drive identity, RPO, and RTO;
- private GHCR pull authentication and image retention;
- identity provider placement and hosted OIDC URLs;
- exact initial CristexHub service slice and code-runner disposition;
- private DEV naming: tailnet name or custom private DNS.

## Recovery order

A replacement host is recovered in this order:

1. restore documented host access and prerequisites;
2. install the pinned k3s version/configuration;
3. restore or reconstruct external state safely;
4. bootstrap Argo CD private access;
5. restore Infisical/GHCR/Cloudflare access references;
6. reconcile namespaces, policies, and stateful services;
7. restore databases and application encryption keys;
8. reconcile DEV/PROD workloads by immutable digest;
9. validate privately;
10. re-enable the public PROD route only after acceptance.

Git and Argo reconstruct desired state. They do not restore mutable data, secret
values, or external state by themselves.
