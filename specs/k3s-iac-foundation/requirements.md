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
| KIF-005 | Ansible owns host configuration, OpenTofu owns approved external resources, Argo CD is the intended persistent Kubernetes reconciler, and Infisical owns secret values without overlapping reconciliation. Ansible may implement the bounded ephemeral QA probe under its guarded exception. One separate bootstrap exception may create or reconcile only the committed `argocd` and `platform-edge` Namespaces with state present, foreign-existing refusal, no deletion path, and a non-passthrough entrypoint that rejects task-skipping controls, launches only the repository controller in an allowlisted clean environment, and binds mutation to an ephemeral single-run attestation. Those manifests identify Ansible as bootstrap writer and Argo CD only as future desired owner; handoff remains pending Argo CD installation, Namespace adoption or Application registration, and successful sync evidence. |
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
| KIF-010 | DEV, SSH, k3s API, Argo CD, dashboards, databases, brokers, and administrative endpoints remain private through Tailscale or explicit port-forwarding. |
| KIF-011 | Only an approved PROD application hostname may become public through Cloudflare Tunnel to Traefik; no direct WAN origin exposure is introduced. |
| KIF-012 | Every exposure has positive route/auth tests and negative public-reachability tests for all private surfaces. |

## Secrets and identity

| ID | Requirement |
|---|---|
| KIF-013 | Git, OpenTofu state/plans, Argo parameters, CI logs, examples, and documentation contain no plaintext runtime secret values. |
| KIF-014 | Infisical Cloud initially provides separate DEV, PROD, and infrastructure scopes/identities with least-privilege Kubernetes service accounts; self-hosting is deferred. |
| KIF-015 | Bootstrap credentials and application encryption keys have documented, off-node, tested recovery and rotation procedures. |

## Environment and data isolation

| ID | Requirement |
|---|---|
| KIF-016 | The cluster uses separate `argocd`, `platform-edge`, future `shared-services`, `cristexhub-dev`, and `cristexhub-prod` namespaces; applications retain separate DEV/PROD credentials, migrations, and backup paths. |
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
| KIF-026 | Database-consistent, encrypted backups are separated by environment, retained locally and off-node, integrity checked, and copied without destructive mirror semantics. |
| KIF-027 | An isolated restore proves the declared RPO/RTO before PROD acceptance; a successful backup exit code alone is insufficient. |
| KIF-028 | Recovery covers k3s datastore/token, protected host-local single-writer OpenTofu state through encrypted timestamped off-node copies and independent key custody, Infisical bootstrap material, application encryption keys, desired state, and mutable application data. |
| KIF-029 | Resource headroom, disk usage, certificate/tunnel health, workload health, and backup freshness have bounded monitoring before public PROD. |
| KIF-030 | Every phase records actual commands/results, revisions/digests, residual risks, and rollback evidence without leaking sensitive values. |

## Traceability

`tasks.md` references these requirement IDs by stage. `testcases.md` maps every ID
to offline, integration, security, recovery, or manual evidence. The current
Ansible discovery satisfies its offline, syntax/lint, approved host-access,
dependency-bootstrap, curated host/cluster-indicator, and functional
CNI/NetworkPolicy enforcement gates. The exact kubelet-version projection passes
source-only validation, but the target value and compatibility gate remain NOT RUN.
Exact platform Namespace source and its bounded
bootstrap pass offline contracts only; cluster execution remains pending. The
foundation does not satisfy replacement-host recovery, general host-baseline, or
later platform mutation gates. Unresolved storage, secret bootstrap, and RPO/RTO
choices remain decision gates rather than implied requirements.
