# Infrastructure Agent Rules

This root `AGENTS.md` is authoritative for the entire repository.

## Current boundary

- Operational implementation is limited to read-only Ansible discovery, the executed two-package dependency bootstrap, the executed group-scoped k3s administrator access playbook, the executed user-scoped kubectl client-defaults playbook, the executed single-node reboot recovery playbook, and the executed temporary NetworkPolicy probe under `ansible/`. Admin access, warning-free cluster listing, idempotence, reboot, SSH/Tailscale return, Ready node, kubeconfig recovery, current CNI behavior, NetworkPolicy enforcement, rollback, and zero-residue cleanup succeeded; replacement-host recovery remains pending. No general host baseline or deployment exists.
- Python exists only in offline contract tests; it is not operational infrastructure automation.
- This repository also contains a zero-resource Cloudflare-only OpenTofu scaffold and a gated pinned-CLI host installer. The first live attempt stopped when the host had no route to GitHub after creating only exact parent directories and the empty protected state directory. The reviewed controller-transfer recovery then passed check, installed the exact CLI without host egress, and converged at `changed=0`. The protected directory remains empty: no state file, provider initialization, plan, apply, or external resource exists.
- No hosted runtime, general Ansible host baseline, or executable Helm controller source exists here yet. One SHA-pinned, read-only GitHub-hosted CI workflow validates repository source only; it has no Secret, package-write, registry, provider, host, cluster, or deployment path. Exact run `31311995461` passed commit `e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`; no build or publication occurred. Committed persistent Kubernetes source contains exactly three Namespace manifests: `argocd`, `platform-edge`, and `shared-services`. The historical wrapper check passed, the separately approved first apply created exactly those two Namespaces (`argocd` and `platform-edge`), and the idempotence retry passed at `changed=0` under separate approval; that exception remains closed. Exact present-only source plus a distinct bounded wrapper now exist only for `shared-services`. The non-interactive first check attempt stopped before service preflight/reconciliation for missing sudo (`ok=10 changed=0 failed=1`); the interactive retry then passed at `ok=20 changed=1 unreachable=0 failed=0 skipped=2`. The only change-capable task and manifest predicted creation of exactly `shared-services`; check mode made no mutation. First apply and idempotence remain **NOT RUN** and require separate approvals. The superseded `platform-secrets`/`platform-identity` source was never run; its removal is not a live rename or deletion. No Infisical Operator, Argo CD, cloudflared, Keycloak, PostgreSQL, MongoDB, RabbitMQ, Secret, workload, Service, policy, PVC, route, or other persistent kind exists from this new increment.
- CristexHub application source, local Compose assets, development Keycloak realm/theme assets, and Browserless gateway remain external concerns in the CristexHub application repository and must not be copied here. Keycloak `26.7.1`, PostgreSQL `17.10`, realm `cristexhub`, and issuer `https://auth.cristex-soft.com/realms/cristexhub` are selected only for offline source authoring; the official default Keycloak theme is the first-bootstrap direction. A value-free hosted policy freezes client IDs, environment group templates, Argo mappings, Namespace trust, and Universal Auth direction without adding workload, route, Secret, or executable controller source. A separate value-free shared-database policy freezes one PostgreSQL and one MongoDB engine in `shared-services`: CristexHub DEV/PROD have isolated scopes on both engines, Reactive Resume DEV/PROD and Keycloak have dedicated PostgreSQL scopes, exposure is private-only, and all promotion gates remain closed. Separate value-free RabbitMQ and backup policies freeze one future shared broker with exact DEV/PROD scopes, reviewed future-consumer admission, private authenticated backup catalog/retrieval, encrypted non-destructive off-node copy, and distinct definitions/message recovery semantics; they add no executable source. The Reactive Resume hosted policy includes private DEV in the MVP but leaves its image, callbacks, objects, Secrets, and runtime unselected or blocked. MongoDB source/topology and all stateful runtime inputs remain unselected.
- Argo CD chart `10.3.0` / app `v3.5.0` and Infisical Operator `v0.11.7` are selected only as offline source baselines. Hash-bound public chart, provenance, and public-key inputs are vendored under `ansible/files/vendor/`; they are not executable controller source or runtime approval. The [Infisical privileged-prerequisites inventory](runbooks/infisical-operator-privileged-prerequisites-design.md) is an inert design/promotion contract derived from the vendored archive; it adds no CRD, RBAC, values, rendered object, or Ansible entrypoint. Image trust/SBOM/vulnerability/off-node recovery, Infisical scoped RBAC and Universal Auth recovery, exact rendered objects, and every live gate remain blocked.
- Approved discovery, dependency installation, and the group-scoped k3s administrator access mutation have completed. The access playbook verified effective readability as the selected account and a second run was idempotent. Any other host mutation or later implementation remains blocked until its explicit approval gate. Offline validation remains allowed. The accepted Ansible bootstrap direction authorizes no run; executable source currently exists only for the one exact `shared-services` foundation Namespace, while all controller/component bootstrap source remains absent.

## Ownership

Each resource has exactly one reconciliation owner:

| Area | Owner |
|---|---|
| Debian host, mounts, firewall, Tailscale host access, k3s installation | Ansible |
| Bounded foundation bootstrap, privileged CRDs/cluster RBAC, and Keycloak realm/client/group reconciliation | Ansible |
| Cloudflare and GitHub resources | OpenTofu |
| Namespaced Kubernetes desired state after evidenced object-by-object handoff | Argo CD |
| Runtime secret values and rotation | Infisical Cloud |
| Source tests and future immutable private-GHCR publication | GitHub Actions; current cristexweb workflow is read-only CI only |
| Production approvals and destructive operations | Human operator |

Ansible may plan and, only after an explicit separately reviewed exception, execute
the bounded ephemeral Kubernetes QA probe. The implementation uses API-generated
names, run labels, an exact-UID cleanup ledger, UID delete preconditions,
non-cascading `Orphan` propagation, and no Namespace create/delete. Execution still requires a verified
image plus separate create/delete approvals. One additional bounded bootstrap
exception may create or reconcile only the committed `argocd` and `platform-edge`
Namespaces with `state: present`; it refuses foreign existing namespaces and has no
deletion path. Its only authorized entrypoint is the committed non-passthrough
wrapper, which uses an allowlisted clean environment, the repository `.venv`
controller, and an ephemeral single-run attestation; direct playbook invocation and
task-skipping/selection controls are forbidden. The manifests truthfully label Ansible as bootstrap writer and Argo CD
only as future desired owner. Argo ownership remains pending until Argo CD is
installed, the Namespaces are adopted or registered through an Application, and a
successful sync is evidenced; a label alone is not a handoff. That completed
exception authorizes no other persistent Kubernetes object and must not be reopened
or reused.

Ansible is selected as the bounded bootstrap installer for future exact foundational
Namespaces, the Infisical Cloud Kubernetes Operator, Argo CD, one self-hosted
Keycloak, and privileged cluster-scoped prerequisites. Each component requires its
own exact source closure and separate check/apply/idempotence approvals; foundation
Namespace executable source exists, but no new runtime approval exists yet. Ansible remains lifecycle
owner of foundation CRDs, ClusterRoles, ClusterRoleBindings, and Keycloak
realm/client/group reconciliation unless a later explicit decision replaces it.
Namespaced workload specifications may hand off to Argo one exact object set at a
time only after Ansible stops reconciling those objects and registration, adoption,
successful sync, and managed-field evidence pass. Dual reconciliation is forbidden.
Exact present-only source and a dedicated guarded wrapper exist for
`shared-services`; after one missing-sudo stop, its interactive wrapper-check retry
passed and predicted exactly the one `shared-services` Namespace without mutation.
First apply and idempotence remain separately approved and **NOT RUN**. The historical wrapper remains closed. Future cloudflared
namespaced objects belong only in `platform-edge`. The Infisical Cloud Operator, a
separate Keycloak deployment, one general PostgreSQL instance, and one shared
MongoDB engine belong in `shared-services`.
The [foundation Namespace bootstrap runbook](runbooks/foundation-namespace-bootstrap.md)
defines that boundary. The source-only
[Keycloak OIDC bootstrap design](runbooks/keycloak-oidc-bootstrap-design.md) records
the production identity, database, recovery, exposure, and handoff gates.

Implementation belongs at repository-root `ansible/`, `opentofu/`,
`kubernetes/`, and `runbooks/`. Do not use OpenTofu Kubernetes or Helm providers
for objects reconciled by Argo CD. GitHub Actions must not deploy directly with
`kubectl`, Helm, or Argo CD.

## Host automation standard

- Debian plus Ansible is the approved host-management path for G1. NixOS migration
  is out of scope unless a later architecture decision explicitly replaces this
  owner.
- Prefer Ansible built-in modules over `shell` or `command`. Use shell execution
  only when no suitable module exists, make it idempotent, and document why.
- The current discovery uses Ansible built-ins plus `kubernetes.core.k8s_info`; it
  contains no operational Python, command allowlist, shell, raw, script, or command
  task.
- Controller tools are pinned by root `pyproject.toml` and `uv.lock`; `uv` owns the
  ignored project-local `.venv`, while Galaxy collections install only into the
  ignored `ansible/.ansible/collections/` path.
- Use Python only for offline tests or a later approved focused plugin/custom module
  when built-in Ansible behavior is demonstrably insufficient. Do not recreate
  package, file, service, user, mount, or information modules.
- Operational simplicity, idempotence, safety, and maintainability are the
  acceptance criteria.

## Safety gates

Explicit operator approval is required before any of these actions:

- SSH command that mutates a host;
- Ansible play without check/diff mode;
- `tofu apply`, import, state mutation, or destroy;
- Helm install/upgrade, Argo sync, or Kubernetes apply/delete;
- namespace, PVC, database, volume, or backup deletion;
- disk partitioning, formatting, mounting, or k3s reinstall;
- DNS, Cloudflare Tunnel, firewall, Tailscale ACL, or public-route mutation;
- secret creation, export, rotation, or revocation;
- DEV or PROD deployment and public cutover.

Discovery commands must be read-only. Never combine discovery and mutation in one
script or approval request. Never use namespace/PVC deletion or blind OpenTofu
destroy as routine rollback.

## Networking

- Retain bundled k3s Traefik as the sole ingress controller unless a later approved migration replaces it. Do not add a second ingress controller.
- PROD application traffic may become public only through an explicitly reviewed Cloudflare Tunnel route to Traefik.
- DEV, SSH, the k3s API, Argo CD, dashboards, databases, brokers, code-runner, Keycloak administration/management, and other administrative endpoints remain private through host Tailscale or explicit port-forwarding.
- Databases and brokers must never receive public Ingress, NodePort, or Tunnel routes.
- A future shared Keycloak browser-authentication route requires its own public-route approval and negative administration/management reachability tests; no Keycloak route is authorized now.
- Every exposure change must document authentication, source, destination, port, expected public status, negative reachability checks, and rollback.

## Secrets and state

- Never commit plaintext credentials, kubeconfigs, private keys, tunnel tokens, database URLs containing credentials, Infisical machine credentials, or real `.env` files.
- Kubernetes manifests contain only Infisical references, never secret values.
- Do not place secret values in OpenTofu variables, plans, outputs, committed state, examples, CI logs, or review artifacts. The selected local backend is single-writer host state outside k3s; its encrypted off-node copy, key recovery, integrity check, and isolated restore must pass before any apply.
- The root [`.gitignore`](.gitignore) protects OpenTofu/Terraform working directories, state, plans, local variable/override/crash files; Ansible retry/cache/facts; kubeconfigs; local environment/credential/key artifacts; and generated secret material. `.terraform.lock.hcl` is deliberately tracked so provider selections are reviewable.
- DEV and PROD use separate Infisical environments, identities, application credentials, encryption keys, database principals, and backup paths.
- Preserve and back up application encryption keys independently; losing them can make encrypted application data unrecoverable.

## Data and recovery

- Shared PostgreSQL and MongoDB engines are an accepted resource-saving design, not an availability or security boundary.
- DEV and PROD must have separate databases, owners/users, credentials, migrations, backup sets, and negative cross-access tests.
- Redis remains environment-local. One shared RabbitMQ belongs in `shared-services`; current DEV/PROD consumers require separate users, vhosts, permissions, limits, and recovery scopes, and every future consumer requires a reviewed exact policy/test change with no wildcard admission.
- Stateful work requires a verified backup before mutation and an isolated restore rehearsal before production acceptance. Operator access to backup catalogs/retrieval is private and authenticated; archives remain encrypted, timestamped, integrity-checked, off-node, and never exposed by public or anonymous links.
- Future Keycloak remains a separate deployment and requires a dedicated logical database, owner role, credential, and backup scope on the one general PostgreSQL instance in `shared-services`; it does not receive a separate PostgreSQL deployment or PVC. Encrypted application-consistent `pg_dump`, non-destructive off-node copy, integrity verification, independent key custody, negative cross-database authorization tests, and an isolated restore meeting declared RPO/RTO are required before identity state is accepted. The shared engine/PVC remains a common failure domain.
- Rollback prefers Git revert and a previously verified image digest. Database changes must be forward-compatible or have a tested data recovery plan.

## Delivery and evidence

- Deploy immutable image digests or commit-SHA references; never deploy `latest`.
- DEV must pass validation and soak before PROD is created or promoted.
- PROD must pass private validation before any Cloudflare public cutover.
- Each change updates the relevant `specs/<milestone>/testcases.md` with actual commands and results.
- Run offline checks before provider-backed plans, provider-backed plans before applies, and private validation before public validation.
- Record residual risks honestly. A single node and shared database engines remain shared failure domains even after logical isolation tests pass.
