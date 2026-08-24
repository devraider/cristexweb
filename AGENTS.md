# Infrastructure Agent Rules

This root `AGENTS.md` is authoritative for the entire repository.

## Current boundary

The Infisical project `cristexweb-infrastructure` has no `bootstrap` environment under the current licensing. All guarded source-only Infisical secret-zero, Argo, PostgreSQL, MongoDB, and materialization contracts therefore use the fixed Infisical environment slug `prod`. This is an Infisical Cloud environment identifier only and did not itself authorize Kubernetes PROD. The separately approved `cristexhub-prod` Namespace, credential seam, Argo registration, and private workload activation are now live; the Cloudflare public route remains unapplied pending protected provider authorization.

One explicitly approved one-time Linux-host CLI exception created the previously absent Infisical folders `prod:/shared-services/postgresql` and atomically uploaded the exact 15 PostgreSQL administrator, TLS, and reserved consumer keys. A later approved backup-custody operation created `prod:/shared-services/backup-recovery`, uploaded exactly one dedicated age private identity without value output, verified exact remote equality/closure, securely removed the private identity from the host, and retained only its public recipient there. Values were generated randomly without value output; PostgreSQL usernames, 64-lowercase-hex password contracts, direct-CA TLS, all three exact SANs, leaf/key correspondence, exact remote key closure, and zero plaintext temporary residue passed. This exception created no Kubernetes Secret, Infisical CR, workload, PVC, database, Namespace, route, or PROD activation. The canonical broad uploader must now refuse this prepopulated PostgreSQL path; any later value replacement is an explicit rotation and must preserve the exact contracts.

- Operational implementation is limited to read-only Ansible discovery, the source-only check-only k3s datastore/encryption preflight, the executed two-package dependency bootstrap, the executed group-scoped k3s administrator access playbook, the executed user-scoped kubectl client-defaults playbook, the executed single-node reboot recovery playbook, the executed temporary NetworkPolicy probe, the source-only check-only Keycloak DEV successor identity preflight, and the source-only check-only Keycloak DEV successor transport/actor/Infisical-CAS/API transition preflight under `ansible/`. The datastore/encryption preflight has completed one separately approved live read-only run at `ok=45 changed=1 unreachable=0 failed=0`; its sole change was the ignored mode-`0600` controller artifact, whose sanitized datastore/encryption stages remained unknown. It performed no backup, restore, encryption, host, cluster, or Secret mutation. Admin access, warning-free cluster listing, idempotence, reboot, SSH/Tailscale return, Ready node, kubeconfig recovery, current CNI behavior, NetworkPolicy enforcement, rollback, and zero-residue cleanup succeeded; replacement-host recovery remains pending. No general host baseline or deployment exists.
- Python exists in offline contract tests and in thirty-three exact-scope Ansible action plugins: ten enforce canonical Namespace and Infisical/Argo/database/CristexHub DEV and PROD Secret/seam/Universal Auth mutation boundaries; two guard pinned host rclone installation and encrypted proxy-recovery transfer boundaries; two perform no-log cryptographic validation of exact Argo and stateful-database Secret contracts; five guard the exact standalone MongoDB, PostgreSQL, Keycloak, RabbitMQ, and OIDC CONNECT proxy object closures; five guard cloudflared/route closures; four guard CoreDNS/DEV/PROD registration/sync boundaries; two guard the fixed temporary logical-database provisioning helpers; one guards the dedicated shared-MongoDB NetworkPolicy closure; one guards the source-only Keycloak DEV successor identity preflight; one guards the source-only Keycloak DEV successor transport/actor/Infisical-CAS/API transition contract. These reviewed plugins are focused exceptions permitted by the host automation standard; no general-purpose operational Python or infrastructure collector exists.
- This repository also contains approved executable source for a host-managed PostgreSQL `keycloak` backup service and daily systemd timer. It uses pinned host rclone `1.71.1`, Debian age `1.2.1-1+b5`, CloudNativePG `pg_dump`, immutable timestamped Google Drive copy/readback, sanitized journald receipts, a 14-day encrypted local retention boundary, and an Infisical-custodied private age identity. Installation, one backup, isolated restore, and timer enablement remain distinct guarded modes. Installation, immutable Google Drive upload/readback, Infisical key retrieval/decryption, isolated PostgreSQL 17 restore, exact temporary-Pod cleanup, and zero private residue now pass; the final timer enable apply and idempotence now pass. The timer is enabled and active (`waiting`) on its daily schedule; independent Google-account recovery, measured multi-run RPO/RTO, remote retention, other database scopes, and production recovery acceptance remain blocked. No Kubernetes CronJob, backup Secret, public share, or remote deletion is authorized. A separate guarded MongoDB source closure now mirrors the host scheduler pattern for the complete `shared-mongodb` replica set using authenticated TLS, oplog-consistent archive, immutable Google Drive copy/readback, isolated digest-pinned MongoDB `8.0.12` restore, and exact temporary-Pod cleanup. Its installation, oplog-consistent backup, immutable readback, Infisical-key decrypt, isolated MongoDB `8.0.12` restore, exact cleanup, and zero residue now pass; its timer enable apply now passes, is active (`waiting`), and final idempotence converged at `changed=0`.
- This repository also contains a Cloudflare-only OpenTofu root and a gated pinned-CLI host installer. The first live installer attempt stopped when the host had no route to GitHub after creating only exact parent directories and the empty protected state directory. The reviewed controller-transfer recovery then passed check, installed the exact CLI without host egress, and converged at `changed=0`. Later separately approved work imported the existing Tunnel and Keycloak/DEV DNS resources into protected host state; encrypted off-node backup/readback and isolated restore now pass. PROD Tunnel-ingress/DNS source is committed but unapplied pending a protected DNS-capable provider credential.
- No general Ansible host baseline exists. Separately approved hosted runtime checkpoints now include private Argo CD, shared services, cloudflared, and CristexHub DEV; Helm remains offline render evidence only and is never a runtime reconciler. One SHA-pinned, read-only GitHub-hosted CI workflow validates repository source only; it has no Secret, package-write, registry, provider, host, cluster, or deployment path. Exact run `31311995461` passed commit `e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`; no build or publication occurred. Committed persistent Kubernetes source contains exactly five Namespace manifests: `argocd`, `platform-edge`, `shared-services`, live `cristexhub-dev`, and `cristexhub-prod`; the separately approved PROD Namespace checkpoint is now Active/idempotent, while the source-only database materialization and other unactivated seams remain blocked; the PROD runtime seam, Argo registration, and private workloads are separately live/idempotent. The separately approved MongoDB-operator migration created the separate live `mongodb-system` Namespace, moved only the MongoDB Community Operator control-plane Deployment and ServiceAccount there, retained its namespaced RBAC and watched database resources in `shared-services`, validated successful reconciliation, and removed the superseded operator Deployment and ServiceAccount from `shared-services`. The historical wrapper check passed, the separately approved first apply created exactly those two Namespaces (`argocd` and `platform-edge`), and the idempotence retry passed at `changed=0` under separate approval; that exception remains closed. Exact present-only source plus a distinct bounded wrapper now exist only for `shared-services`. The non-interactive first check attempt stopped before service preflight/reconciliation for missing sudo (`ok=10 changed=0 failed=1`); the interactive retry then passed at `ok=20 changed=1 unreachable=0 failed=0 skipped=2`. The only change-capable task and manifest predicted creation of exactly `shared-services`; check mode made no mutation. The separately approved first apply passed at `ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created exactly that Namespace, verified its exact labels and `Active` phase, and preserved k3s/Tailscale health. The separately approved idempotence apply passed at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`; exact post-state and service health remained valid. The `shared-services` Namespace bootstrap checkpoint is complete. Dedicated present-only [CristexHub DEV Namespace source](runbooks/cristexhub-dev-namespace-bootstrap.md) exists with approved application/environment/bootstrap/future-owner labels. Its check passed at `ok=20 changed=1 unreachable=0 failed=0 skipped=2` without mutation. The first apply then passed at `ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created only that Namespace, and verified all four labels/`Active` plus k3s/Tailscale health. Idempotence passed at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`; the `cristexhub-dev` Namespace checkpoint is complete. The separately approved `cristexhub-prod` Namespace checkpoint is now Active/idempotent; earlier pre-checkpoint absence evidence remains historical. The superseded `platform-secrets`/`platform-identity` source was never run; its removal is not a live rename or deletion. The exact three Infisical proxy bootstrap Secrets exist. The historical runtime checkpoint applied exactly 40 Infisical Operator/proxy objects and its idempotence converged; the later 42-object source was not separately runtime-applied. The separately approved 44-object expansion then passed check at `ok=30 changed=1 failed=0 skipped=5`, apply at `ok=35 changed=1 failed=0`, post-check at `ok=30 changed=0 failed=0 skipped=5`, and idempotence at `ok=35 changed=0 failed=0`; both Deployments and k3s/Tailscale remained healthy. Separately approved private Argo CD, cloudflared, Keycloak, RabbitMQ, shared database, CristexHub DEV, and private CristexHub PROD runtime checkpoints now exist; the PROD Cloudflare route remains absent. The CristexHub PROD runtime Infisical seam is live/idempotent with exact `/cristexhub/prod/runtime`, independent PROD Auth/Universal Auth names, nine-key runtime plus `cristexhub-prod-ghcr-pull`, scoped fail-closed admission, bounded administrator credential rotation, least-privilege writer RBAC, hash-bound manifests, and a guarded wrapper. Its first hardened read-only check stopped safely at `ok=15 changed=0 failed=1` on exact live Operator pod-template drift before runtime reconciliation. The bounded rollout receipt is now explicitly tolerated and the required `SSL_CERT_DIR=/etc/ssl/certs:/etc/infisical-proxy-ca` trust-store contract is now canonical source. The fresh Operator check passed at `ok=30 changed=0 failed=0 skipped=5`; after separately approved credential materialization, the runtime seam apply created its exact 13 objects and target Secrets, and final idempotence passed at `ok=62 changed=0 failed=0 skipped=3`. The five-object PROD Argo registration pins revision `751885a42798d282e168131db147f13694a0a621`, uses namespaced no-delete controller RBAC, exact in-cluster server destination, and automated `selfHeal=true`, `prune=false`, `allowEmpty=false`; apply passed and active-state idempotence converged at `changed=0`. A local proxy secret-zero attempt generated private recovery material and contacted Google Drive OAuth, then stopped before Ansible/Kubernetes on `invalid_grant`; the discovered plaintext temp residue and unused encrypted artifact were removed without reading values. No Kubernetes Secret was created. The corrected writer now installs cleanup before generation, resumes one exact encrypted pending bundle, verifies downloaded ciphertext/checksum/decrypt plus TLS/key/auth relationships, and refuses implicit rotation. An unused age identity exposed during local debug tracing was revoked/regenerated before upload or Kubernetes and the trace was removed. The hardened retry left zero plaintext temp residue, retained only the encrypted pending bundle/checksum plus a login-Keychain identity copy, confirmed zero Kubernetes Secrets, and stopped on the same expired controller Drive OAuth. That transfer path is superseded; guarded host rclone `1.71.1` installation/idempotence, host OAuth, immutable encrypted transfer/readback, `drive-verified`, and exact proxy Secret bootstrap now pass. The guarded host-rclone installer check passed and was reconfirmed at
  `ok=25 changed=1 failed=0`. The first apply stopped before host mutation at
  `ok=22 changed=0 failed=1` on missing nested-module `normal` dispatch. After that
  fallback fix, the approved retry created only the exact ignored controller cache
  (`changed=2`) and stopped before host mutation at
  `ok=24 changed=2 failed=1` because the action guard read the raw templated role
  default instead of the resolved operator identity. Both rclone guards now bind the
  resolved operator into the attested internal preflight; focused and full offline
  validation passed. A fresh check reconfirmed `ok=25 changed=1 failed=0`, then the
  separately approved install retry passed at
  `ok=34 changed=4 unreachable=0 failed=0 skipped=2`: it created only the exact host
  cache/config parents, transferred and extracted the pinned payload, selected the
  exact symlink, verified version `1.71.1`, and preserved k3s/Tailscale health.
  The separately approved idempotence apply then passed at
  `ok=32 changed=0 unreachable=0 failed=0 skipped=4`. The initial transfer check
  stopped safely on absent OAuth config. Host OAuth then completed through a private
  callback tunnel; token-bearing config exists only on the host. Transfer check
  passed at `ok=26 changed=0 failed=0`. Apply verified OAuth and prepared exact
  encrypted staging, then stopped at `ok=25 changed=1 failed=1` before successful
  upload because pinned rclone rejects unsupported `--local-umask`. Approved cleanup
  passed at `ok=26 changed=1 failed=0` with zero host staging residue. The reviewed
  source fix removes that flag and protects exact readback leaves at mode `0600`;
  `258/258` offline contracts pass. Its mandatory fresh check could not begin because
  the host became transiently Tailscale-offline/SSH-unreachable (`ok=0 unreachable=1`).
  After return, check passed at `ok=26 changed=0 failed=0`; transfer apply passed at
  `ok=39 changed=7 failed=0`, including immutable upload/readback, controller-only
  cryptographic verification, marker creation, and zero host staging residue. Proxy
  Secret bootstrap passed at `ok=15 changed=1 failed=0` and created exactly three
  no-log Secrets. Infisical Operator source fixes then passed review; final check
  passed at `ok=24 changed=2 failed=0`, first apply at `ok=29 changed=2 failed=0`,
  and idempotence at `ok=29 changed=0 failed=0` for the historical 40-object
  runtime checkpoint. The later 42-object source was not separately runtime-applied;
  the 44-object source closure is runtime-applied/idempotent and both Deployments are
  Available. PROD Universal Auth and application Secrets are now live; private
  PROD workloads are `Synced/Healthy`, while public routing remains unapplied.
- CristexHub application source, local Compose assets, development Keycloak realm/theme assets, and Browserless gateway remain external concerns in the CristexHub application repository and must not be copied here. Keycloak `26.7.1`, PostgreSQL `17.10`, realm `cristexhub`, and issuer `https://auth.cristex-soft.com/realms/cristexhub` are selected only for offline source authoring; the official default Keycloak theme is the first-bootstrap direction. A value-free hosted policy freezes client IDs, environment group templates, Argo mappings, Namespace trust, and Universal Auth direction without adding workload, route, Secret, or executable controller source. A shared-database policy freezes one PostgreSQL and one MongoDB engine in `shared-services`: CristexHub DEV/PROD have isolated scopes on both engines, Reactive Resume DEV/PROD and Keycloak have dedicated PostgreSQL scopes, and exposure is private-only. MongoDB `8.0.12` now runs as a private one-member operator-managed replica set in `shared-services` with mandatory TLS, SCRAM identities, an `80Gi` data PVC, and a `5Gi` logs PVC; its dedicated operator control plane runs in `mongodb-system`. Backup, restore, authoritative-data acceptance, and production activation remain blocked. Separate value-free RabbitMQ and backup policies freeze one future shared broker with exact DEV/PROD scopes, reviewed future-consumer admission, private authenticated backup catalog/retrieval, encrypted non-destructive off-node copy, and distinct definitions/message recovery semantics; they add no executable source. The Reactive Resume hosted policy includes only a planned private DEV workload reservation; read-only evidence now shows the broad all-consumer lane already applied both DEV and unapproved PROD PostgreSQL Database/DatabaseRole CRs plus Infisical-owned credential Secrets. Both roles retain `INHERIT`, PUBLIC `CONNECT`/`TEMPORARY` remains broad, and zero NetworkPolicies select shared PostgreSQL, so these live objects are unaccepted drift rather than activation. A review child exposed both credential Secret data to its private local session logs; the exact child/async artifacts were removed without repeating values, and successor rotation plus predecessor revocation is mandatory before any use. A dedicated value-free exposure-rotation contract now freezes same-principal successor semantics, no-output custody, exact two-key scope, broad-lane refusal, and fail-closed stop states, but adds no writer or wrapper: official Infisical APIs document no CAS/If-Match contract, so runtime rotation remains blocked. CNPG 1.30 documents `kubernetes.io/basic-auth`, but its pinned controller accepts the live key-correct `Opaque` targets and both DatabaseRoles are applied; that type difference remains separate source-normalization drift, not the rotation blocker. A separate source-only `opentofu/github/` root now reserves private standalone repository `devraider/cristex-reactive-resume` with Actions disabled, provider `6.13.0`, `prevent_destroy`, and independent `github.tfstate`; controller-only initialization and warning-free validation pass while the backend state remains absent; no plan, apply, state mutation, repository, source push, workflow, or GHCR package exists yet. A dedicated source-only encrypted `github.tfstate` backup/readback/isolated-restore lane now exists with fixed independent local/remote roots and units; it remains NOT RUN/BLOCKED until the state genesis and its separate approvals. Dedicated Infisical/VAP/RBAC and PostgreSQL lanes, realm runtime and patched OIDC validation/local-auth controls, candidate image provenance mismatch, private durable object storage, application-key custody, disabled v5 Agent/Redis scope, locked split-role migration, backup/restore, RPO/RTO, NetworkPolicy/TLS identity, and runtime remain unresolved or blocked. PROD remains reservation/template-only despite the unapproved database drift, and public exposure is forbidden. MongoDB remains single-node and non-authoritative; recovery and every production stateful acceptance gate remain blocked.
- Argo CD chart `10.3.0` / app `v3.5.0` now has a separate guarded private bootstrap closure: exactly three Ansible-owned CRDs and 29 namespaced objects, including a deny-all default AppProject, for controller, repo-server, server, and standalone Redis. ApplicationSet runtime, Dex, notifications, commit server, cluster RBAC, public exposure, PVCs, hooks, metrics Services, and Secret objects are absent. The closure requires exact precreated, cryptographically valid Infisical-owned `argocd-secret`, `argocd-redis`, and `argocd-server-tls` contracts and refuses `argocd-initial-admin-secret`; empty-API check defers only the unresolved default-project GVK and apply waits for Established CRDs; that pre-runtime source status is historical, and the separately approved private Argo core is now live/idempotent. The Infisical [privileged-prerequisites inventory](runbooks/infisical-operator-privileged-prerequisites-design.md) remains historical evidence and the [implementation profile](runbooks/infisical-operator-implementation-profile.md) remains canonical policy. Infisical Operator `v0.11.7` now has a separate guarded [idle bootstrap closure](runbooks/infisical-operator-bootstrap.md): exactly six promoted namespaced CRDs, native same-Namespace admission, five namespaced manager Roles for the five reviewed namespaces, metrics off, no ClusterGenerator/review-token privilege, one digest-pinned controller, and a digest-pinned authenticated TLS Squid proxy. The quarantined chart/source archives remain evidence only and are never runtime inputs. The 44-object closure contains no Secret or Infisical CR; its PROD watch/RBAC expansion is runtime-applied/idempotent, PROD admission allows only the exact reviewed Auth/Connection/StaticSecret identities while Secret/PushSecret/DynamicSecret remain excluded, and check/apply require three separately recovered proxy bootstrap Secrets. The 44-object closure is live; the separately guarded PROD Universal Auth/runtime seam and private workload activation now also pass. A separate source-only guarded Infisical database Secret materialization seam now contains exactly 15 value-free objects: one shared Connection, separate PostgreSQL/MongoDB Auths and credential identities, two StaticSecrets, eight scoped fail-closed VAP/bindings, and one additive Secret-writer Role/Binding. It freezes four target Secret contracts aligned with the no-log stateful database validator. Historical source text described credential values/check/apply/sync as blocked, but read-only evidence now proves at least the two Reactive Resume PostgreSQL targets are live and Infisical-owned; their apply provenance is unresolved, both were exposed to local review logs, and rotation/revocation plus all runtime acceptance remain blocked. Its VAPs constrain exact target Secrets, StaticSecrets, Connections, and Auths; the Argo seam has the same scoped source/target boundaries. A separate source-only Universal Auth/value lane accepts protected file inputs only, keeps values out of Git/argv/environment/evidence, and remains NOT RUN/BLOCKED. Separate source-only PostgreSQL/MongoDB logical-provisioning lanes consume precreated per-consumer Secrets through temporary UID-bound helper Pods and NetworkPolicies; all seven empty reservations, including inactive PROD scopes, remain runtime-unrun and blocked on engine readiness and Secret materialization.
- Approved discovery, dependency installation, group-scoped k3s administrator access, and the approved `argocd`, `platform-edge`, `shared-services`, `cristexhub-dev`, and `cristexhub-prod` Namespace checkpoints have completed; the PROD Namespace is Active/idempotent. Earlier source-only pre-checkpoint absence evidence is retained as historical. Offline validation remains allowed. The current 44-object Infisical closure, private Argo CD core, PROD credential seam, and private PROD workloads are live/idempotent; the public Cloudflare route remains absent. MongoDB `8.0.12` is live with TLS/SCRAM, but private acceptance remains blocked because no NetworkPolicy selects `shared-mongodb-0` and legacy selectors do not match live MongoDB/backend/Celery labels. RabbitMQ is live for PROD Celery, while observed principal/permission drift and recovery acceptance remain open. MongoDB/RabbitMQ URL credentials and the reused GHCR pull credential require verified rotation; the exposed DeepSeek key requires separate revoke/replace. Their distinct non-passthrough `check|apply` wrappers use existing `k3s-admin` access without sudo and fail closed until their exact precreated Secret metadata exists. No runtime action is approved by source alone.

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
The separately approved first apply created and verified it, and the separately
approved idempotence apply converged at `changed=0`; the Namespace checkpoint is
complete. The historical wrapper remains closed. Future cloudflared
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
- Because the current Infisical licensing does not provide a separate `bootstrap` environment, the infrastructure project currently uses the fixed Infisical environment slug `prod` for guarded source-only bootstrap material. This is a documented temporary exception to environment-level separation, not a security boundary or Kubernetes PROD authorization. DEV and PROD must still use separate identities, application credentials, encryption keys, database principals, logical paths, and backup paths; no PROD workload, Namespace, route, or credential activation follows from the Infisical slug.
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

## Source-only host rclone boundary

Guarded source now pins host rclone `1.71.1` and an exact encrypted Infisical proxy
recovery transfer; see [the host rclone runbook](runbooks/rclone-host-transfer.md).
Every rclone/Google Drive command executes as the inventory-resolved non-root
operator on the Debian k3s/database host. The Mac/controller retains plaintext
creation/decryption and the age private identity. Earlier applies stopped before host
mutation on missing normal-module dispatch and an unresolved operator-default guard.
Both source defects have focused regressions. A fresh check passed at
`ok=25 changed=1 failed=0`, and the separately approved corrected install passed at
`ok=34 changed=4 failed=0`, selected verified rclone `1.71.1`, and preserved
k3s/Tailscale health. The separately approved idempotence apply passed at
`ok=32 changed=0 failed=0`. Host OAuth later completed through a private callback
tunnel; the Mac held no rclone config/token. Transfer check passed at
`ok=26 changed=0 failed=0`. After one stopped apply and exact cleanup, the reviewed
compatibility retry passed at `ok=39 changed=7 failed=0`; immutable Drive
upload/readback, controller verification, `drive-verified`, and zero host staging
residue passed. Proxy Secret bootstrap then passed at `ok=15 changed=1 failed=0` and
created exactly three no-log Secrets. Infisical Operator check/apply/idempotence now
also pass. That historical boundary is superseded for the two Reactive Resume
PostgreSQL targets only: their Infisical-owned Secrets and Database/DatabaseRole CRs
are live but unaccepted, their credentials require rotation/revocation after local
review-log exposure, and all database runtime checks remain **NOT RUN/BLOCKED**. Ansible never reads,
templates, copies, or logs rclone token or
config content; rollback removes only the exact selector, and transfer cleanup
removes only exact host ciphertext staging residue.

## Autonomous delivery workflow

1. Start by investigating project documentation and repository evidence. Build and continuously refresh an ordered list of unfinished or partially implemented tasks; do not rely on chat state alone.
2. Execute every task through this loop: **research → plan → implement → test → review → fix → next task**. A task advances only after accepted review findings are fixed and affected checks pass.
3. Operate autonomously. Unblock routine questions through repository/external research or a sensible, goal-aligned engineering decision; escalate only decisions that are irreversible, high-risk, or genuinely require user ownership.
4. During active backlog execution, maintain at least **six concurrently running subagents** and replace completed workers immediately so the floor remains six. Every subagent must use **`gpt-5.6-luna`** with **`thinking=max`**. Give each worker a distinct, useful lane; never create busywork merely to inflate concurrency.
5. Every task or lane executed in parallel must use its own git worktree. Never allow parallel writers to share a checkout; the orchestrator integrates and validates worktree results.
6. There are no real clients yet. Within the repository's safety and approval boundaries, prefer the fastest reversible solution and iteration speed over complexity, premature abstraction, or long-term optimization; assume the implementation may be rewritten.
7. One-time operational work, such as initial server setup, may be handled in real time outside the full recurring loop when that is faster. This exception does not waive any Safety gate, explicit operator approval, verification, or accurate evidence requirement in this file.

## Cloudflare edge boundary

The approved architecture direction is `Cloudflare -> cloudflared/platform-edge ->
Traefik/kube-system -> reviewed private services`. The canonical policy is
`ansible/files/policies/cloudflare-edge-architecture.yml`; historical phase evidence
is retained in `runbooks/cloudflared-candidate-provenance.md`. The existing Tunnel,
Keycloak/DEV DNS routes, protected token handoff, and private connector are live;
OpenTofu manages their five imported resource addresses. The PROD Tunnel-config
update and `hub.cristex-soft.com` DNS record remain unapplied and require separate
provider, DNS, validation, and public-cutover approvals. Keycloak administration,
management/master/health/metrics, Argo, data services, and direct origins must remain
publicly unreachable. The Tunnel token belongs only in Infisical at
`prod:/platform-edge/cloudflared`, key `CLOUDFLARE_TUNNEL_TOKEN`; it must never enter
Git, OpenTofu state/plan, argv, examples, logs, or evidence. Rollback must disable
only the exact route/record, preserve existing private health and administrative
privacy, rotate/revoke the token through Infisical when needed, and avoid blind
destroy.
