# Test Cases — k3s IaC foundation

## Ansible-first discovery implementation — 2026-08-04

The offline contract tests and locked project-local `uv` validation do not invoke
SSH, become, the inventory host, Kubernetes API, a provider, or report generation.
`uv` and `ansible-galaxy` contacted package registries to resolve the ignored
`.venv` and local Galaxy collection path; nothing was installed on the inventory
host. Separately approved non-elevated and elevated runtime attempts are recorded
below, followed by the approved dependency installation and successful elevated
rerun. The admin-access check, mutation, effective-user readability, fresh-session
all-namespace query, and idempotence succeeded. The user-scoped client-defaults
check, execution, warning-free fresh-session queries, and idempotence also passed.
The separately approved one-reboot recovery and manual post-reboot checks passed.

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-ANS-01 | KIF-001, KIF-004, KIF-008 | Ansible-first ownership | Operational Python collector is removed; minimal inventory, playbook, role, pinned collection, template, and Ansible documentation exist | PASS — layout contract test passed |
| KIF-ANS-02 | KIF-001, KIF-003 | Declarative read-only discovery | Host discovery uses setup/service_facts/stat; cluster discovery uses exact k8s_info queries; the discovery role contains no shell, command, raw, script, package, apt, or pip task | PASS — discovery module-boundary tests passed; the separate approved bootstrap is covered below |
| KIF-ANS-03 | KIF-001, KIF-002, KIF-007 | Invocation and elevation gates | Play fails without check/diff, explicit limit, and one selected host; become defaults false; elevated queries need both approval flags | PASS — approved positive non-elevated and elevated attempts passed the gates; negative invocation branches NOT RUN |
| KIF-ANS-04 | KIF-013, KIF-030 | Bounded data projection | Raw discovery registrations are no_log; fact cache is memory-only; report omits addresses, MACs, UUIDs, annotations, labels, environment fields, secrets, chart values, raw specs, command output, and kubeconfig content | PASS — non-elevated and elevated reports were reviewed; all projected query results contain only curated names/counts |
| KIF-ANS-05 | KIF-006, KIF-013 | Local report safety | Exactly one ignored controller-local JSON destination defaults under the repository root, mode 0600, diff disabled, become false, and symlink-refused | PASS — offline task/template contract and actual ignored mode-0600 report write passed; negative symlink runtime case remains offline-tested only |
| KIF-ANS-06 | KIF-008, KIF-021 | Kubernetes query boundary | Exact non-secret kinds provide object indicators; Secret, ConfigMap, Events, and broad all queries are absent; listing evidence alone never claims CNI or NetworkPolicy enforcement | PASS — query boundary and template assertions passed; separate functional evidence is recorded in KIF-NET-02 |
| KIF-ANS-07 | KIF-007, KIF-030 | Ansible syntax and lint | Locked project tooling and the locally pinned collection pass syntax and production-profile lint before any host access | PASS — ansible-core 2.19.0 syntax check and ansible-lint 26.6.0 production profile passed; package-registry access only |
| KIF-ANS-08 | KIF-001, KIF-008 | Elevated cluster inventory capture | A separately approved one-host elevated check/diff run produces a human-reviewed host, datastore, and Kubernetes indicator report | PASS — datastore exists; all nine exact queries available; curated node, namespace, StorageClass, ingress, kube-system workload, and HelmChart indicators captured |
| KIF-ANS-09 | KIF-006, KIF-007 | Reproducible controller environment | `pyproject.toml` and `uv.lock` pin the ignored project `.venv`; Galaxy installs the pinned collection only into the ignored local Ansible path | PASS — `uv sync --locked`, dependency-pin contract, ignore checks, and project-local Ansible commands passed |
| KIF-ANS-10 | KIF-001, KIF-007, KIF-030 | Approved non-elevated host discovery | Ansible ping and exactly one check/diff-limited host run pass; only the ignored controller-local report changes and receives human review | PASS — ping changed=false; play recap ok=14, changed=1 local report, failed=0, unreachable=0, skipped=1; valid JSON mode 0600 reviewed; no become or Kubernetes query |
| KIF-ANS-11 | KIF-001, KIF-008, KIF-030 | Elevated failure diagnosis | Human-reviewed elevated report and a bounded read-only import probe explain unavailable Kubernetes queries without emitting kubeconfig or secrets | PASS — datastore exists; nine queries unavailable; remote `kubernetes`, `yaml`, and `jsonpatch` imports all false |
| KIF-ANS-12 | KIF-001, KIF-008, KIF-030 | Exact Node version projection offline contract | Schema v3 adds an exact existing-Node branch that emits only curated name/cluster scope and `status.nodeInfo.kubeletVersion`; missing metadata/status/nodeInfo safely fall back to `unknown`; raw resource/nodeInfo, other Node status, IDs, addresses, labels/annotations, kernel/container-runtime fields, and new query kinds remain absent | PASS — exact-branch static contract and a three-Node synthetic render (complete, missing status, missing nodeInfo) passed with sensitive fixture fields omitted and exact `unknown` fallbacks; full offline suite, syntax, and production lint passed without inventory or Kubernetes API access |
| KIF-ANS-13 | KIF-001, KIF-002, KIF-008, KIF-030 | Target kubelet version and current PVC scope runtime | One separately approved elevated read-only check/diff rerun refreshes the ignored mode-0600 report; human review confirms actual kubelet version and `shared-services` scope before Argo CD compatibility is decided | PASS — report `2026-08-07T08:09:31Z`, schema 3, ok=17/changed=1 local report/unreachable=0/failed=0/skipped=1; kubelet `v1.36.2+k3s1`, exactly 15 available queries, 4 Namespaces, and available zero-count `shared-services` PVC query reviewed; target remained read-only |
| KIF-ANS-14 | KIF-001, KIF-007, KIF-030 | Operational inventory command contract | Every operational discovery example explicitly loads ignored `.ansible/inventory.local.yml`; default `ansible.cfg` remains the neutral alias-only inventory and no address/user/secret enters Git | PASS — first omitted-inventory attempt stopped before discovery at ok=3/changed=0/unreachable=1; corrected command passed; offline contract rejects the omission in root, Ansible, and testcase documentation |
| KIF-DEP-01 | KIF-002, KIF-007 | Approved dependency bootstrap contract | Separate one-host playbook requires explicit approval and directly requests only `python3-kubernetes` and `python3-jsonpatch`; no cache refresh, shell, command, latest, upgrade, or other direct package exists | PASS — contract test, syntax check, and production-profile lint passed |
| KIF-DEP-02 | KIF-002, KIF-007 | Dependency bootstrap execution | Check/diff package plan is reviewed before the approved actual installation; subsequent import probe and elevated discovery pass | PASS — incomplete first plan rejected; revised plan reviewed 37 new, 0 upgraded/removed; installation, package verification, imports, and elevated discovery passed |
| KIF-ADM-01 | KIF-002, KIF-007 | Group-scoped admin access contract | Explicit approval and one-host limit gate an existing nonzero-UID account; exact dedicated group rejects GID 0, numeric aliases, and unexpected members; check-safe creation, no home creation, persistent `0640` settings, hidden diff, safe rollback baseline, conditional restart, polling, metadata assertions, and effective readability as the selected user are present | PASS — contract test, syntax check, and production-profile lint passed |
| KIF-ADM-02 | KIF-002, KIF-007 | Admin-access check/diff | Approved one-host check predicts only rollback baseline, group, membership, two k3s config settings, and conditional restart without mutation | PASS — recap ok=16, changed=6, unreachable=0, failed=0, skipped=13 |
| KIF-ADM-03 | KIF-007 | Admin-access mutation and recovery | Approved run succeeds; new SSH session has group access; kubeconfig is root/group `0640`; kubectl, SSH, Tailscale, reboot recovery, and second-run idempotence pass | PASS — mutation ok=24/changed=6; selected-user readability and fresh-session queries pass; idempotent rerun ok=28/changed=0/failed=0; reboot recovery passed in KIF-REB-02 |
| KIF-ADM-04 | KIF-002, KIF-007 | Warning-free kubectl client contract | Explicit approval, diff, one-host limit, selected non-root exclusive group member, Bash/home/profile safety, user-scoped environment defaults, hidden profile diff, present/absent rollback, no server-config permission change, and no restart are enforced | PASS — 15 contract tests, syntax check, and production-profile lint passed |
| KIF-ADM-05 | KIF-007 | Warning-free kubectl client runtime | Check/diff predicts only selected-user profile blocks; accepted run and fresh login remove server-config warnings from node/all-namespace queries; second run reports changed=0 | PASS — check recap ok=14/changed=1/failed=0 predicted two profile blocks; operator confirmed accepted run, expected client defaults, warning-free queries, and idempotent changed=0/failed=0 rerun |
| KIF-REB-01 | KIF-002, KIF-007 | Single-node reboot recovery contract | Explicit approval, fallback-access confirmation, diff, one-host limit, preflight services/backup/access/Ready node, exactly one reboot, new boot ID, SSH return, post-reboot services/Ready node/access, no config mutation, and hidden sensitive facts are enforced | PASS — 15 contract tests, syntax check, and production-profile lint passed |
| KIF-REB-02 | KIF-007 | Single-node reboot recovery runtime | Check/diff predicts exactly one reboot; accepted run returns through Tailscale SSH with a new boot ID, running k3s/Tailscale, one Ready node, and unchanged group-scoped kubeconfig access | PASS — operator confirmed fallback; check ok=19/changed=1/unreachable=0/failed=0/skipped=7; reboot ok=26/changed=1/unreachable=0/failed=0/skipped=0; operator manually confirmed active services and warning-free node/all-namespace queries |
| KIF-NET-01 | KIF-002, KIF-003, KIF-005, KIF-008, KIF-021, KIF-030 | Temporary CNI/NetworkPolicy functional-probe contract | Plan/run/cleanup truth tables, immutable image and approval gates, API-generated names, fixed existing namespace, selectorless ClusterIP plus explicit EndpointSlice, hardened standalone Pods with exact terminal-state checks, private exact-UID ledger recovery, dual-label fixed-kind interruption discovery, UID-preconditioned non-cascading cleanup, zero residue, and no remote exec or Namespace mutation are enforced | PASS — focused contracts, syntax, and production lint passed offline; no inventory host, image registry, or Kubernetes API was accessed |
| KIF-NET-02 | KIF-002, KIF-003, KIF-005, KIF-008, KIF-021, KIF-030 | Temporary CNI/NetworkPolicy functional runtime | After independent image verification and a reviewed ownership exception plus separate create/delete approvals, baseline success, deny failure, selective allow/deny, rollback success, and exact cleanup pass | PASS — official BusyBox linux/amd64 digest and `httpd`/`wget` paths verified; run check ok=18/changed=0; eight phases passed; execution ok=225/changed=43/failed=0; 12 remaining identities removed after two policy deletes; post-cleanup check ok=20/changed=0/exact_identity_count=0 |
| KIF-STO-01 | KIF-001, KIF-003, KIF-008, KIF-030 | Non-destructive storage discovery offline contract | Built-in facts project only curated device/partition size, rotational/removable state, direct mount state, and mounted filesystem types; exact StorageClass behavior fields, bounded PV placement booleans, and PVC metadata from five fixed namespaces omit device serials, UUIDs, addresses, backing paths, filesystem contents, Secret/ConfigMap kinds, and broad PVC queries | PASS — focused contracts, all 28 offline tests, collision-safe synthetic render, discovery syntax, and production lint passed; no inventory host, kubeconfig, Kubernetes API, or filesystem content was accessed |
| KIF-STO-02 | KIF-001, KIF-008, KIF-030 | Extended storage discovery runtime | A separately approved one-host elevated check/diff run renders valid mode-0600 JSON and human review establishes actual curated device, StorageClass, PV, and PVC indicators without mutation or sensitive metadata | PASS — ok=17/changed=1 local report/failed=0; unmounted 1 TB rotational disk with one partition, NVMe/root capacity, local-path `Delete`/`WaitForFirstConsumer`/no expansion, and zero PV/PVC objects confirmed. Historical boundary: that report's fifth PVC scope was `shared-data`; KIF-ANS-13 later live-verifies the current zero-count `shared-services` query. Filesystem/content/health and reuse decision remain unknown; no disk mutation |
| KIF-REC-01 | KIF-002, KIF-003, KIF-013, KIF-015, KIF-028, KIF-030 | Replacement-host recovery first offline increment | Secret-free runbook/register truthfully separate same-host reboot from replacement, require old-host fencing and exclusive storage ownership, stop split brain, require exactly one preserve-existing or create-new identity decision, and leave datastore/version/token/storage/RPO/RTO/off-node prerequisites explicitly unknown without guessed commands | PASS — 5 focused offline recovery contracts and the full offline suite passed; documentation contains no executable recovery command or secret-shaped value and no host/provider/API was accessed |
| KIF-REC-02 | KIF-007, KIF-015, KIF-026–KIF-030 | Replacement-host recovery rehearsal/runtime | An isolated, approved replacement follows an actual version/datastore/storage-specific plan; proves one authoritative cluster/storage writer, desired state, mutable data, encryption behavior, isolation, and measured RPO/RTO before public reactivation | NOT RUN/BLOCKED — identity model and datastore, exact version/config, token custody, storage, RPO/RTO, off-node artifacts, restore procedures, and approvals remain `UNKNOWN — STOP`; reboot success is not replacement proof |
| KIF-TOFU-01 | KIF-002, KIF-005, KIF-006, KIF-013, KIF-030 | Pinned host installer offline contract | Source structurally requires default-false install and separate rollback approval, diff/one-host gates, Debian 13 x86_64, reviewed checksum-pinned archive/payload digests, an existing non-root operator without UID aliases, strict remote and controller-cache modes, symlink-safe controller preflight, controller-only download plus verified Ansible transfer, absent-only version extraction, an exact managed selector, protected state directory, service preservation, check-mode prediction, and selector-only state-preserving rollback | PASS — focused structural contracts, full offline suite, syntax, and production lint passed; controller transfer fix used no host/provider contact and negative runtime branches remain NOT RUN |
| KIF-TOFU-02 | KIF-002, KIF-007, KIF-030 | OpenTofu host install runtime | Approved check/diff, reviewed live run, exact version verification, preserved k3s/Tailscale, and a changed=0 rerun pass without provider or state operations | PASS — initial check passed at ok=27/changed=6/failed=0; bounded host-egress failure stopped at ok=21/changed=2/failed=1; reviewed controller-transfer check passed at ok=33/changed=6/failed=0, live recovery passed at ok=39/changed=6/failed=0, and second run converged at ok=30/changed=0/failed=0. The exact CLI and selector exist; the protected directory remains empty and no provider/state operation ran |
| KIF-TOFU-03 | KIF-004–KIF-006, KIF-013 | Cloudflare-only zero-resource scaffold | Exact OpenTofu/provider pins and local backend path exist with zero resources/data/modules/imports/variables/outputs and no forbidden provider, credential, lockfile, state, or plan | PASS — static contract passed; `tofu fmt/validate` and provider initialization are honestly NOT RUN because no approved controller binary/provider download exists |
| KIF-TOFU-04 | KIF-013, KIF-028, KIF-030 | Local-state encryption and off-node recovery gate | Timestamped encrypted Google Drive copies, independent key custody, integrity verification, and isolated restore pass before the first apply | NOT RUN/BLOCKED — no state exists; encryption, Drive identity, copy, retention, key recovery, and restore remain `UNKNOWN — STOP` |
| KIF-NS-01 | KIF-002, KIF-005, KIF-006, KIF-010, KIF-030 | Bounded platform Namespace bootstrap offline contract | Exact committed `argocd` and `platform-edge` Namespace manifests are the sole object definitions consumed by the closed historical bootstrap, and the architecture/task checklist places them in a documented pre-Stage-4 exception with separate check/apply/idempotence approvals that waives no Stage 4 entry gate; a non-passthrough entrypoint rejects `--start-at-task`, `--step`, and all extra arguments; the wrapper launches the repository `.venv` controller in an allowlisted clean environment and supplies a private random single-run attestation; the mutating task independently requires that attestation, reloads only literal manifest paths, and rejects extra top-level/metadata keys; a first-task internal-variable guard, canonical non-symlink ancestor/leaf validation, approval/diff/exact-limit/kubeconfig/protected-result gates, foreign-existing refusal, present-only reconciliation, exact post-verification, truthful ownership labels, executable closure, and no deletion/other-kind path are enforced | PASS — focused structural, stage-boundary, control-flow, and synthetic ancestor-symlink contracts, controller-only forged-extra-var rejection, full offline suite, syntax, synthetic discovery validation, and production lint passed without inventory or Kubernetes API contact |
| KIF-NS-02 | KIF-002, KIF-005, KIF-010, KIF-030 | Platform Namespace bootstrap runtime | Reviewed check predicts exactly the two absent Namespaces; approved live run creates them, verifies labels/services, and second run converges changed=0 without installing Argo CD/cloudflared or creating a route | PASS — wrapper check passed without mutation; separately approved first apply passed at ok=21/changed=1/unreachable=0/failed=0/skipped=0 and changed exactly `argocd` plus `platform-edge`. During the separately approved idempotence checkpoint, a local sudo authentication failure stopped the initial invocation before service preflight/reconciliation at ok=10/changed=0/unreachable=0/failed=1/skipped=0; the retry passed at ok=21/changed=0/unreachable=0/failed=0/skipped=0, both exact items were `ok`, post-state identity/labels/Active passed, and service health was preserved |
| KIF-NS-03 | KIF-002, KIF-005, KIF-006, KIF-010, KIF-016, KIF-030 | Historical foundation Namespace source checkpoint | Exact `platform-secrets` and `platform-identity` source plus a guarded present-only wrapper passed offline validation, but the wrapper never ran and the placement was superseded before runtime | SUPERSEDED SOURCE-ONLY — historical validation remains truthful; no cluster object was created or deleted by this checkpoint |
| KIF-ARGO-01 | KIF-005, KIF-008, KIF-010, KIF-013, KIF-015, KIF-023, KIF-030 | Argo CD candidate provenance and target-minor screen | Historical secret-free evidence binds exact official chart/index/provenance/image/render inputs plus target kubelet and tested-version sources while the separate release record now selects chart `10.3.0` / app `v3.5.0` only for offline source authoring | PASS — focused provenance contracts preserve exact associations and target-minor qualification; selection remains NOT DEPLOYABLE and Argo runtime remains NOT RUN/BLOCKED |
| KIF-ARGO-02 | KIF-005, KIF-008, KIF-010, KIF-013, KIF-015, KIF-021, KIF-023, KIF-030 | Argo CD online/static readiness refresh | A secret-free record curates deterministic render, upstream API registration, RBAC/network, image trust/availability/vulnerability, private-Git, and Namespace-adoption evidence while all live admission/runtime gates remain blocked | PASS — focused provenance contracts preserve the 44-document render and security blockers; no values, rendered YAML, Kubernetes object, credential, or deployable controller source was added |
| KIF-ARGO-03 | KIF-002, KIF-003, KIF-005, KIF-008, KIF-010, KIF-013–KIF-015, KIF-021, KIF-030 | Historical Argo CD source-only hardened-design checkpoint | At that checkpoint, a secret-free design fixed private access, retained quiescent ApplicationSet, supplemental default-deny, phased least privilege, private Git/secret custody, adoption, stop/rollback, and ownership without deployable source | PASS HISTORICAL/SUPERSEDED — the checkpoint was valid when recorded; current guarded cases KIF-ARGO-04 through KIF-ARGO-10 implement an exact private core with ApplicationSet runtime absent while runtime remains blocked |
| KIF-IDP-01 | KIF-002, KIF-003, KIF-005, KIF-010, KIF-012–KIF-017, KIF-021, KIF-023, KIF-026–KIF-030 | Source-only Ansible bootstrap and Keycloak OIDC architecture | Ansible is the selected bounded bootstrap installer and privileged lifecycle owner with no dual reconciliation; direct Argo OIDC separates Keycloak authentication/groups, Argo RBAC, and Kubernetes RBAC while preserving private administration, Infisical-owned values, a dedicated Keycloak logical database/role on the general shared PostgreSQL engine, stable issuer, exact approvals, and handoff gates | PASS — Keycloak `26.7.1`, PostgreSQL `17.10`, realm, issuer, clients, group templates, default theme, separate deployment, and shared-engine isolation policy are selected only for offline authoring; no executable component source, credential, route, or runtime was added |
| KIF-DB-01 | KIF-005, KIF-013, KIF-016–KIF-019, KIF-021, KIF-026–KIF-030 | Shared database source-only architecture | One PostgreSQL and one MongoDB engine are placed in `shared-services`; exact consumers remain isolated and the approved source profile fixes NVMe `local-path`, 40/80 GiB PVCs, bounded resources, private standard Services/TLS, Ansible→Argo ownership direction, and daily/14-day/24h/4h backup targets | PASS SOURCE-ONLY — exact consumer/profile contracts pass; PostgreSQL keeps its selected-but-untrusted baseline, MongoDB source/topology and implementation details remain unselected, all promotion gates are false, the current exact four-Namespace closure includes only source-ready `cristexhub-dev` beyond the completed platform set, and no executable database source or runtime operation was added |
| KIF-MQ-01 | KIF-005, KIF-013, KIF-016, KIF-019–KIF-021, KIF-026–KIF-030 | Shared RabbitMQ source-only architecture | Exactly one future RabbitMQ engine belongs in `shared-services`; DEV/PROD have dedicated vhost/user/Infisical credential/permission/limit/recovery scopes, deny-first cross-vhost/admin/public-management rules, and future consumers require reviewed exact changes | PASS SOURCE-ONLY — canonical value-free policy/runbook and fail-closed contracts pass; image/topology/storage/ports/resources/TLS/NetworkPolicy/restore/runtime remain unselected and no executable source was added |
| KIF-BKP-01 | KIF-005, KIF-013, KIF-017–KIF-020, KIF-026–KIF-030 | Shared stateful backup access architecture | PostgreSQL, MongoDB, and RabbitMQ use encrypted timestamped separate-purpose archives, private authenticated metadata/list/retrieve/verify access, non-destructive off-node copy, integrity and isolated restore; RabbitMQ definitions remain distinct from queued-message recovery | PASS SOURCE-ONLY — daily archives, 14-day local/off-node retention, RPO 24h, and RTO 4h are fixed; pinned host rclone `1.71.1` replaces the container direction, but host install, identities, staging, credentials, dumps, jobs, schedules, deletion, restore, and runtime remain blocked |
| KIF-GHA-01 | KIF-005, KIF-022–KIF-025, KIF-030 | GitHub-hosted infrastructure source CI | Exactly one workflow uses SHA-pinned actions, a fixed runner, read-only permission, bounded triggers/timeouts/concurrency, frozen controller dependencies, and exact offline tests without Secret/package/registry/provider/host/cluster/deploy access | PASS SOURCE AND HOSTED CI — focused/full contracts passed; run `31311995461` and job `93241094377` completed successfully for exact commit `e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`; branch protection, GHCR publication, digest evidence, and deployment remain NOT RUN/BLOCKED |
| KIF-RR-01 | KIF-012–KIF-017, KIF-019, KIF-021, KIF-023, KIF-026–KIF-030 | Reactive Resume private-MVP source architecture | Include environment-local Reactive Resume DEV in the private MVP, reserve separate PROD, bind exact OIDC clients and dedicated shared-PostgreSQL scopes, keep Infisical value ownership/private exposure, and block image/callback/object/Secret/recovery/handoff/runtime promotion | PASS SOURCE-ONLY — value-free policy/runbook and exact contracts pass; no local Compose input was promoted and no upstream image, callback, object, Secret, database, route, or runtime was selected or created |
| KIF-CF-01 | KIF-005, KIF-011, KIF-013, KIF-015, KIF-021, KIF-023, KIF-030 | Source-only cloudflared candidate provenance | A secret-free record mutation-resistently binds exact official release/source/asset and architecture-specific image evidence, explicitly qualifies the unsigned trust boundary, captures token-file precedence, connection-aware readiness versus independent health, fixed metrics/quick-tunnel management-surface and edge-transport constraints, reserves `platform-edge` for cloudflared within the exact current four-Namespace and zero-resource OpenTofu source sets, and blocks trust/selection/soak, image assurance/availability, hardening, Infisical token recovery, OpenTofu state/resource work, Argo handoff, exact DNS/Traefik/edge policy, route approval, single-node risk, and runtime | PASS — 5 focused contracts enforce exact evidence associations, trust qualifications, token/health/network semantics, unchanged source sets, operational-command hygiene, and effective RFC1918/loopback sentinels; `2026.7.3` remains CANDIDATE — NOT DEPLOYABLE — NOT SELECTED; runtime NOT RUN and no OpenTofu resource, Kubernetes object, secret, route, or deployment source was added |
| KIF-INF-01 | KIF-005, KIF-013–KIF-015, KIF-021, KIF-023, KIF-030 | Source-only Infisical Operator provenance and selection boundary | Historical evidence distinguishes unselected `v0.11.8` distribution observations from the aligned `v0.11.7` set selected only as the offline baseline; trust, compatibility, scoped RBAC, Universal Auth recovery, traffic, and runtime remain blocked | PASS — focused contracts enforce exact evidence associations, qualified trust wording, immutable child direction, and no deployable controller source or Secret |
| KIF-INF-02 | KIF-005, KIF-013–KIF-015, KIF-021, KIF-023, KIF-030 | Inert Infisical privileged-prerequisite inventory | Bind exactly seven raw CRD templates and observed RBAC/scoping seams—including ineffective scoped-Role access to cluster-scoped TokenReview/ClusterGenerator and the singular/plural metrics defects—without adding valid CRD/RBAC, values, render, Ansible entrypoint, Secret, or runtime source | PASS — inventory remains inert; completed foundation Namespaces and the separately selected watch profile are now truthful gates while all deployable/runtime gates remain false |
| KIF-INF-03 | KIF-005, KIF-013–KIF-016, KIF-021, KIF-023, KIF-030 | Infisical source audit and implementation profile | Hash-bind official `v0.11.7` controller commit as quarantined evidence and prove controller/auth/ClusterGenerator behavior; select exact three-Namespace separate-identity intent, metrics-off, no cluster manager/generator/review-token permission, authenticated Squid direction, age/Drive secret-zero direction, and non-sensitive ConfigMap proof while same-Namespace enforcement remains blocked | PASS SOURCE-ONLY — 6 focused/64 affected/165 full contracts, source hashes, compile, Markdown, and diff checks pass; no embedded artifact is promoted as Kubernetes/Ansible/proxy/credential/runtime source |
| KIF-INF-04 | KIF-005, KIF-013–KIF-016, KIF-021, KIF-023, KIF-030 | Guarded Infisical idle deployable closure | Promote exactly six hash-mapped namespaced CRDs, six fail-closed same-Namespace admission policies/bindings, exact three-Namespace read-only target RBAC, metrics-off digest-pinned Operator, authenticated TLS Squid, proxy-only egress, and a 40-object guarded check/apply path; commit no Secret value, Infisical CR, PROD scope, or self-hosted server | PASS SOURCE / RUNTIME NOT RUN — 15 focused/180 full contracts, 12 syntax checks, production lint, Operator/proxy action-only, task-start/injection fixtures, hashes/docs/diff pass; live check/apply/idempotence remain required |
| KIF-INF-05 | KIF-005, KIF-013–KIF-015, KIF-023, KIF-027, KIF-030 | Infisical proxy secret-zero recovery and write | Generate exact TLS/Basic/client material only in a private temp directory; age-encrypt it, verify it off-node through the guarded host transfer, then write exactly three no-log Secrets through a guarded action | STOPPED BEFORE KUBERNETES — historical hardened retry proved cleanup, encrypted-pending resume, Keychain copy, and zero Kubernetes Secrets, then stopped on Drive `invalid_grant`. Source now removes controller rclone and requires exact `drive-verified`; new installer/OAuth/transfer/Secret checkpoints are NOT RUN/BLOCKED |
| KIF-SRC-01 | KIF-005, KIF-010, KIF-013–KIF-015, KIF-023, KIF-030 | Deterministic hosted source-baseline closure | Exact release records, value-free identity/authorization policy, chart/provenance/public-key bytes, SHA256SUMS, safe chart roots, exact four-Namespace manifest closure, and exact allowlisted component source are enforced offline | PASS — source-selection plus affected provenance/design/layout contracts pass; exact hashes verified; no live/runtime operation or staged file |
| KIF-NS-04 | KIF-002, KIF-003, KIF-005, KIF-013–KIF-017, KIF-021, KIF-026–KIF-030 | Shared-services placement correction | Replace never-run `platform-secrets`/`platform-identity` source with one exact present-only `shared-services` Namespace; reserve `platform-edge` for cloudflared; place Infisical Operator, separate Keycloak, and one general PostgreSQL instance in commons intent; give Keycloak only a dedicated logical database/role/credential on that engine | PASS — 78 focused and 115 full offline tests, 9 syntax checks, production lint, fail-closed fixtures, archive hashes, links, closure, hygiene, and historical-source preservation passed; no discovery, check, apply, deletion, workload, Secret, database, route, or runtime operation |
| KIF-NS-05 | KIF-002, KIF-005, KIF-016, KIF-030 | Shared-services Namespace runtime | A successful wrapper check predicts only the absent exact `shared-services` Namespace; separately approved first apply creates/verifies it; separately approved idempotence converges at changed=0 | PASS — check retry passed at `ok=20 changed=1 failed=0`; first apply passed at `ok=22 changed=1 failed=0`; separately approved idempotence passed at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`, with exact identity/three labels/`Active` and k3s/Tailscale health preserved. No component was deployed |
| KIF-NS-06 | KIF-002, KIF-005, KIF-006, KIF-010, KIF-016, KIF-025, KIF-030 | CristexHub DEV Namespace source and runtime | Dedicated guarded source reconciles only `cristexhub-dev` with four approved labels and present-only semantics; check predicts only that Namespace without mutation; first apply creates/verifies it; idempotence converges; PROD and all other kinds remain absent | PASS — check passed at `ok=20 changed=1 failed=0 skipped=2`; first apply passed at `ok=22 changed=1 failed=0 skipped=0`; idempotence passed at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`, with exact labels/`Active` and service health preserved |

| KIF-RCLONE-01 | KIF-002, KIF-005, KIF-007, KIF-013, KIF-030 | Guarded pinned host rclone installer | Exact official sums/archive/binary pins and five-file layout; controller cache and host transfer; Debian 13 x86_64; root-owned cache/version/selector; interactive sudo only; check-safe; selector-only rollback; direct/task-selection/injection negatives | PARTIAL — check passed at `ok=25 changed=1 failed=0`; first apply stopped before mutation at `ok=22 changed=0 failed=1` on missing nested-module `normal` dispatch; regression fix and controller-local integration passed; apply retry/idempotence/rollback remain NOT RUN |
| KIF-RCLONE-02 | KIF-002, KIF-005, KIF-013–KIF-015, KIF-027, KIF-030 | Exact pending encrypted proxy host transfer | Inventory/getent non-root operator without UID alias; exact selector/binary/config metadata; sole `drive:` remote and no-log read-only OAuth check; fixed timestamp/digest/destination; ciphertext-only mode-0700/0600 staging; four immutable copyto boundaries; encrypted readback/cleanup; controller verification and exact marker before Secret mutation | PASS SOURCE-ONLY — controller rclone removed, native wrapper booleans/task-start guards, exact archive membership, and marker contracts pass; OAuth, host transfer/readback/cleanup, Drive and Secret/Kubernetes runtime are NOT RUN/BLOCKED |

## Guarded host rclone source validation — 2026-08-10

Commands:

```bash
.venv/bin/python -m unittest -v tests.test_rclone_host_contract tests.test_shared_stateful_backup_architecture_contract
.venv/bin/python -m unittest discover -s tests -v
cd ansible
for playbook in playbooks/*.yml; do ../.venv/bin/ansible-playbook -i .ansible/inventory.local.yml "$playbook" --syntax-check; done
../.venv/bin/ansible-lint --offline --profile production
cd ..
for script in ansible/bin/*; do sh -n "$script"; done
for script in tests/*.sh; do bash -n "$script"; done
.venv/bin/python -m compileall -q tests ansible/plugins/action
tests/reject_rclone_task_start.sh
.venv/bin/python - <<'PY'
from pathlib import Path
import re
excluded = {'.git', '.venv', '.pi-subagents', 'vendor', '.ansible', '.pytest_cache'}
paths = [path for path in Path('.').rglob('*.md') if excluded.isdisjoint(path.parts)]
for path in paths:
    text = path.read_text()
    assert not any(line.endswith((' ', '\t')) for line in text.splitlines()), path
    for target in re.findall(r'\[[^]]+\]\(([^)]+)\)', text):
        if '://' not in target and not target.startswith('#'):
            local = target.split('#', 1)[0]
            if local:
                assert (path.parent / local).resolve().exists(), (path, target)
assert len(paths) == 31, len(paths)
PY
git diff --check
git diff --cached --quiet
```

Source-only validation used no inventory host, OAuth endpoint, Google Drive remote,
or Kubernetes API. Focused rclone/backup contracts passed `14` tests; direct action,
internal-injection, task-start, passthrough, and cleanup boundaries failed closed.
The full suite passed `190` tests. All `15` playbooks passed syntax check;
production `ansible-lint` passed `80` files with zero warnings/failures; shell syntax,
Python compile, `31` repository Markdown links/trailing-whitespace, `git diff
--check`, and no-staged-files checks passed. The ignored pending ciphertext filename,
checksum file, and SHA-256 remained exact, `drive-verified` remained absent, and no
plaintext temp residue was found. Independent tests/docs/provenance and final
security/runtime reviews returned **APPROVED** after config-content, backend-type,
check-mode OAuth, documentation-count, and controller-tempfile findings were closed.
Every live installer, OAuth, transfer, cleanup, Secret, Infisical, Argo, and database
backup checkpoint remained **NOT RUN/BLOCKED** at that source checkpoint.

## Guarded host rclone first check, stopped apply, and dispatch fix — 2026-08-10

The separately approved installer check made no mutation and passed:

```text
crtxweb: ok=25 changed=1 unreachable=0 failed=0 skipped=11 rescued=0 ignored=0
```

The sole change was the bounded check-mode prediction. The separately initiated
first apply then stopped before any installer action completed:

```text
fatal: [crtxweb -> localhost]: FAILED! changed=false
msg: unable to load guarded action ansible.builtin.file
crtxweb: ok=22 changed=0 unreachable=0 failed=1 skipped=0 rescued=0 ignored=0
```

Root cause: `ansible.builtin.file` and `ansible.builtin.get_url` have no dedicated
action plugin in ansible-core `2.19.0`; normal task execution falls back to
`ansible.builtin.normal`, but the two exact-scope rclone guards did not. Both guarded
dispatch helpers now preserve dedicated actions for `copy`, `fetch`, and `command`
and use `ansible.builtin.normal` only when the requested module has no dedicated
action. Task action/arguments are restored in `finally`.

Validation:

```bash
.venv/bin/python -m unittest -v tests.test_rclone_host_contract
.venv/bin/python -m unittest discover -s tests -v
cd ansible
for playbook in playbooks/*.yml; do
  ../.venv/bin/ansible-playbook -i .ansible/inventory.local.yml \
    "$playbook" --syntax-check
done
../.venv/bin/ansible-lint --offline --profile production
cd ..
.venv/bin/python -m compileall -q ansible/plugins/action tests
git diff --check
# A disposable localhost-only action probe invoked each production helper with
# ansible.builtin.file and required mode-0700 /tmp directory creation.
```

Actual result: all `7` focused and `191` full contracts passed; all `15` playbooks
passed syntax; production lint passed `80` files with zero failures/warnings; compile
and diff checks passed. The disposable controller-local integration completed at
`localhost: ok=2 changed=2 failed=0`; its two temporary directories were removed by
trap. No inventory host, OAuth endpoint, Drive remote, Secret, or Kubernetes API was
accessed by fix validation. Independent dispatch/security/documentation review returned
**APPROVED**; residual live retry, idempotence, rollback, OAuth, Drive, cleanup, and
Secret/Kubernetes risks remain open. Live apply retry and idempotence remain **NOT
RUN**.

## Schema-v3 elevated discovery and target-minor review — 2026-08-07

The operator ran the separately approved elevated one-host read-only discovery. The
first attempt omitted `-i .ansible/inventory.local.yml`; because `ansible.cfg`
defaults only to the neutral alias-only inventory, it stopped before discovery at
`ok=3 changed=0 unreachable=1` and made no host or report change. The corrected
operational command explicitly loaded the ignored mode-`0600` local inventory. The
become password was entered only at the local prompt and is not recorded.

```bash
cd ansible
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/discover.yml \
  --check --diff --limit crtxweb \
  -e read_only_discovery_enable_elevated=true \
  -e read_only_discovery_elevated_approved=true \
  --ask-become-pass
```

Actual result and bounded human review:

```text
Play recap: ok=17 changed=1 unreachable=0 failed=0 skipped=1 rescued=0 ignored=0
Only change: ignored controller-local inventory.local.ansible.json
Report: regular non-symlink, mode 0600, schema_version=3
Generated: 2026-08-07T08:09:31Z
Services: k3s running; tailscaled running; k3s executable exists and is executable
Kubernetes: exactly 15 bounded queries; all available
Node: count=1; projection keys exactly name/namespace/kubelet_version
Target kubelet: v1.36.2+k3s1
Namespaces: count=4
Target Namespaces absent: argocd, platform-edge, shared-services, cristexhub-dev, cristexhub-prod
shared-services PVC query: available=true; count=0
```

`changed=1` is only the controller-local report write; host and Kubernetes discovery
remained read-only. The ignored report and private inventory are not copied into Git.
The result permits requesting a separately approved
`ansible/bin/bootstrap-platform-namespaces check`; it does not authorize or execute
that wrapper, Namespace mutation, Argo CD, Infisical, cloudflared, or any other
persistent object.

Official Argo CD `v3.5.0` source compatibility evidence was retrieved at
`2026-08-07T08:13:26Z`. The source archive SHA-256 is
`f63ae068404901496f8501f386386aa89566bce37b18d44b6026d01a23abfc24`.
The official tested matrix SHA-256 is
`5f32e19055811f9fea77e31e4f6f9bd1b5a809d845ffa4832162fc3dea9f65df`
and lists Argo CD `3.5` with Kubernetes `v1.36`, `v1.35`, `v1.34`, and `v1.33`.
The official CI file SHA-256
`14ba51038ddc46a4e5ad7dbdbb2772662ebce13d116d61d53ba378ff04c742ef`
includes k3s `v1.36.0`; the official `go.mod` SHA-256
`c1dd593a09cccaf6e51a6a3cf64b9c2e2af6c4f453c8f8b9ced8f1b41fff3799`
includes `k8s.io/kubernetes v1.36.1`. Chart `10.3.0` / app `v3.5.0` declares
`kubeVersion: >=1.25.0-0`. Therefore only the target-minor screen passes: target
minor `1.36` is in the official tested matrix and the chart semver gate admits the
exact target. This is not k3s-specific runtime, rendered API/CRD, installation,
trust, selection, Secret, egress, recovery, ownership, soak, or deployment proof.

Offline source/evidence validation:

```bash
python3 -m unittest -v \
  tests.test_ansible_contract.AnsibleSafetyTests.test_operational_discovery_examples_require_local_inventory \
  tests.test_argocd_provenance_contract \
  tests.test_infisical_operator_provenance_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint playbooks/discover.yml roles/read_only_discovery ../tests/validate_storage_report.yml
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
# Run the embedded documentation/traceability validation under
# "Exact command and actual result" below.
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 11 focused discovery/Argo/Infisical contracts — OK
Ran 65 full offline tests — OK
PASS: Python compile
PASS: syntax for all 8 production playbooks
Passed: 0 failure(s), 0 warning(s) in 9 files processed of 9 encountered; production profile
Passed: 0 failure(s), 0 warning(s) in 38 files processed of 42 encountered; production profile
PASS: embedded documentation/traceability validation
PASS: exact source closure, git diff check, and no staged files
```

## Infisical Operator candidate provenance source-only validation — 2026-08-07

This validation was controller-local and source-only. It verified 24 selected ignored
public release, source, chart, provenance, key-association, registry, and attestation
evidence hashes but copied no raw evidence into Git. It used no inventory, SSH, host,
become, kubeconfig, Kubernetes API, Infisical authentication, secret store, Helm,
provider, deployment, or runtime mutation. A later repository commit provides source
traceability and is not runtime evidence. The evidence record is
[`infisical-operator-candidate-provenance.md`](../../runbooks/infisical-operator-candidate-provenance.md).
At that historical checkpoint both versions were **CANDIDATE — NOT DEPLOYABLE — NOT
SELECTED**, and runtime was **NOT RUN**; the later selection supersedes only the
`v0.11.7` offline version choice.

```bash
python3 -m unittest -v tests.test_infisical_operator_provenance_contract
python3 -m unittest -v tests.test_replacement_recovery_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint playbooks/discover.yml roles/read_only_discovery ../tests/validate_storage_report.yml
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
# Run the embedded documentation/traceability validation under
# "Exact command and actual result" below.
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 5 focused Infisical Operator candidate provenance contracts — OK
Ran 5 focused replacement-recovery contracts — OK
PASS: exact v0.11.8 distribution-gap and v0.11.7 aligned-set associations, qualified chart/SLSA/SBOM trust boundaries, Namespace/RBAC/secret-zero blockers, source closure, and hygiene sentinels
Ran 63 full offline tests — OK
PASS: Python compile
PASS: syntax for all 8 production playbooks
Passed: 0 failure(s), 0 warning(s) in 9 files processed of 9 encountered; production profile
Passed: 0 failure(s), 0 warning(s) in 38 files processed of 42 encountered; production profile
PASS: embedded documentation/traceability validation
PASS: exact Kubernetes/OpenTofu source closure, git diff check, and no staged files
```

The active virtual environment warning only states that the separate application
repository environment is ignored in favor of this repository's locked `.venv`.
Human version/trust selection, refreshed distribution evidence, chart/CRD/API
compatibility for the now-captured target, chart signature and signer authorization,
image signature/SBOM/vulnerability/off-node availability, dedicated Namespace, scoped
RBAC, Argo handoff, secret-zero/recovery/rotation/revocation, exact traffic policy,
single-node acceptance, and every runtime approval remain blocked. No manual QA case
is closed.

## cloudflared candidate provenance source-only validation — 2026-08-07

This validation was controller-local and source-only. It read previously captured,
ignored public release, source, CLI-help, registry, and firewall-documentation
evidence but did not copy raw evidence into Git. It used no inventory, SSH, host,
become, kubeconfig, Kubernetes API, Cloudflare-authenticated API or provider, secret,
deployment, or route. A later repository commit provides source traceability and is
not runtime evidence. The evidence record is
[`cloudflared-candidate-provenance.md`](../../runbooks/cloudflared-candidate-provenance.md);
it is **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED**, and runtime is **NOT RUN**.

```bash
python3 -m unittest -v tests.test_cloudflared_provenance_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint playbooks/discover.yml roles/read_only_discovery ../tests/validate_storage_report.yml
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
# Run the embedded documentation/traceability validation under
# "Exact command and actual result" below.
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 5 focused cloudflared candidate provenance contracts — OK
PASS: exact release/source/image associations, unsigned trust boundary, token/health/network and quick-tunnel management-surface constraints, source closure, and hygiene sentinels
Ran 57 full offline tests — OK
PASS: Python compile
PASS: syntax for all 8 production playbooks
Passed: 0 failure(s), 0 warning(s) in 9 files processed of 9 encountered; production profile
Passed: 0 failure(s), 0 warning(s) in 38 files processed of 42 encountered; production profile
PASS: embedded documentation/traceability validation
PASS: git diff check and no staged files
```

The active virtual environment warning only states that the separate application
repository environment is ignored in favor of this repository's locked `.venv`.
Publisher identity/trust and human version selection/soak, image signature/SBOM/
vulnerability/off-node availability, read-only-root/capability/seccomp/writable-path
compatibility, Infisical token-file secret-zero/recovery/rotation, OpenTofu provider/
state/resource gates, Argo installation/handoff, exact DNS/Traefik/edge policy and
negative tests, route approval, single-node availability acceptance, and every
runtime approval remain blocked.

## Argo CD candidate provenance source-only validation — 2026-08-07

This validation was controller-local and source-only. It read previously captured,
ignored public evidence but did not copy the raw chart, values, render, provenance
file, key, or registry responses into Git. It used no inventory, SSH, host, become,
kubeconfig, Kubernetes API, provider, authenticated registry, secret, deployment,
commit, or push. The evidence record is
[`argocd-candidate-provenance.md`](../../runbooks/argocd-candidate-provenance.md).
At that historical checkpoint it was **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED**,
and runtime was **NOT RUN**; the later selection supersedes only the offline version
choice.

```bash
python3 -m unittest -v tests.test_argocd_provenance_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint playbooks/discover.yml roles/read_only_discovery ../tests/validate_storage_report.yml
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
# Run the embedded documentation/traceability validation under
# "Exact command and actual result" below.
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 4 focused Argo CD candidate provenance contracts — OK
PASS: exact provenance table associations, qualified key-trust wording, image/flow blockers, and RFC1918/loopback scanner sentinels
Ran 52 full offline tests — OK
PASS: Python compile
PASS: syntax for all 8 production playbooks
Passed: 0 failure(s), 0 warning(s) in 9 focused files; production profile
Passed: 0 failure(s), 0 warning(s) in 38 files processed of 42 encountered; production profile
PASS: embedded documentation/traceability validation
PASS: git diff check and no staged files
```

The active virtual environment warning only stated that the separate application
repository environment was ignored in favor of this repository's locked `.venv`.
At this historical checkpoint, the target-minor screen passed through the later
schema-v3 review above, while exact k3s/runtime and rendered API/CRD compatibility,
signing-key trust/status, trust/soak acceptance, Secret recovery, private Git,
image/flow, bootstrap ownership, and all runtime approvals were still blocked. The
later KIF-ARGO-02 section supersedes only the static render/API and controller-side
image-availability parts of that historical boundary; live and decision gates remain.

## Argo CD online/static readiness source-only validation — 2026-08-07

The completed online research used only anonymous official-source HTTPS and private
temporary files. This committed increment curates durable results without depending
on ignored reports. Its acceptance validation below was offline and used no network,
inventory, SSH, become, kubeconfig, Kubernetes API, server-side dry-run, Helm
install/upgrade, provider, Secret, deployment, fixture, mutation, commit, or push.

```bash
python3 -m unittest -v tests.test_argocd_provenance_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
python3 - <<'PY'
from pathlib import Path
import re
import subprocess

expected = {
    "README.md",
    "architecture-plan.md",
    "runbooks/argocd-candidate-provenance.md",
    "specs/k3s-iac-foundation/brief.md",
    "specs/k3s-iac-foundation/manual-qa.md",
    "specs/k3s-iac-foundation/requirements.md",
    "specs/k3s-iac-foundation/status.md",
    "specs/k3s-iac-foundation/tasks.md",
    "specs/k3s-iac-foundation/testcases.md",
    "tests/test_argocd_provenance_contract.py",
}
actual = {
    line[3:]
    for line in subprocess.check_output(["git", "status", "--short"], text=True).splitlines()
    if line
}
assert actual == expected, actual ^ expected
for protected in ("ansible", "kubernetes", "opentofu", ".github/workflows"):
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "--", protected], text=True
    ).strip(), protected
assert {
    str(path.relative_to("kubernetes"))
    for path in Path("kubernetes").rglob("*")
    if path.is_file()
} == {
    "platform/namespaces/argocd.yaml",
    "platform/namespaces/platform-edge.yaml",
    "platform/namespaces/platform-secrets.yaml",
    "platform/namespaces/platform-identity.yaml",
}
for path in [
    Path("README.md"),
    Path("architecture-plan.md"),
    Path("runbooks/argocd-candidate-provenance.md"),
    *sorted(Path("specs/k3s-iac-foundation").glob("*.md")),
]:
    text = path.read_text()
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        local = target.split("#", 1)[0]
        if local:
            assert (path.parent / local).resolve().exists(), (path, target)
runbook = Path("runbooks/argocd-candidate-provenance.md").read_text()
assert ".pi-subagents" not in runbook
assert not re.search(r"\b[0-9a-f]{65}\b", runbook)
controller_home_pattern = "/" + "Users/" + r"[^/\s]+/"
assert not re.search(controller_home_pattern, runbook)
assert "CANDIDATE — NOT DEPLOYABLE — NOT SELECTED" in runbook
assert "Argo CD runtime is **NOT RUN**" in runbook
current = Path("specs/k3s-iac-foundation/testcases.md").read_text()
previous = subprocess.check_output(
    ["git", "show", "HEAD:specs/k3s-iac-foundation/testcases.md"], text=True
)
current_argo_01 = next(line for line in current.splitlines() if line.startswith("| KIF-ARGO-01 "))
previous_argo_01 = next(line for line in previous.splitlines() if line.startswith("| KIF-ARGO-01 "))
assert current_argo_01 == previous_argo_01
assert len([line for line in current.splitlines() if line.startswith("| KIF-ARGO-02 ")]) == 1
assert not subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True).strip()
print("PASS: exact closure, protected source, links, evidence hygiene, and KIF-ARGO traceability")
PY
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 9 focused Argo CD candidate provenance contracts — OK
Ran 71 full offline tests — OK
PASS: Python compile
PASS: syntax for all 8 production playbooks
Passed: 0 failure(s), 0 warning(s) in 38 files processed of 42 encountered; production profile
PASS: exact 10-file documentation/test closure and unchanged protected deployable source
PASS: exact two-file Kubernetes source closure; no chart, values, rendered YAML, or Argo object source
PASS: local Markdown links, evidence hygiene, KIF-ARGO-02 traceability, git diff, and no staged files
```

The active virtual environment warning only stated that the separate application
repository environment was ignored in favor of this repository's locked `.venv`.
The exact render reproducibility, stable upstream API registration screen, and
controller-side image closure pass. Exact k3s admission/runtime, node pullability,
trust selection, reduced RBAC/default-deny networking, Secret recovery, private Git
secret-zero, Namespace adoption, and all live approvals remain blocked. The chart and
At that historical validation checkpoint, the chart and application remained
**CANDIDATE — NOT DEPLOYABLE — NOT SELECTED** and Argo CD runtime was **NOT RUN**.
The later source-only selection supersedes only version choice; this evidence closes
no manual QA case.

## Argo CD hardened-design source-only validation — 2026-08-07

The [hardened design](../../runbooks/argocd-hardened-design.md) is documentation and
offline contract coverage only. Validation used no network, inventory, SSH, become,
kubeconfig, Kubernetes API, Helm operation, registry, GitHub API, Infisical API,
provider, secret operation, fixture, deployment, cleanup, mutation, staging, commit,
or push.

```bash
python3 -m unittest -v tests.test_argocd_hardened_design_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
python3 - <<'PY'
from pathlib import Path
import re
import subprocess

expected = {
    "README.md",
    "architecture-plan.md",
    "runbooks/argocd-hardened-design.md",
    "specs/k3s-iac-foundation/brief.md",
    "specs/k3s-iac-foundation/manual-qa.md",
    "specs/k3s-iac-foundation/requirements.md",
    "specs/k3s-iac-foundation/status.md",
    "specs/k3s-iac-foundation/tasks.md",
    "specs/k3s-iac-foundation/testcases.md",
    "tests/test_argocd_hardened_design_contract.py",
    "tests/test_replacement_recovery_contract.py",
}
actual = {
    line[3:]
    for line in subprocess.check_output(["git", "status", "--short"], text=True).splitlines()
    if line
}
assert actual == expected, actual ^ expected
for protected in ("ansible", "kubernetes", "opentofu", ".github/workflows"):
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "--", protected], text=True
    ).strip(), protected
assert {
    str(path.relative_to("kubernetes"))
    for path in Path("kubernetes").rglob("*")
    if path.is_file()
} == {
    "platform/namespaces/argocd.yaml",
    "platform/namespaces/platform-edge.yaml",
    "platform/namespaces/platform-secrets.yaml",
    "platform/namespaces/platform-identity.yaml",
}
assert {path.name for path in Path("opentofu").iterdir() if path.is_file()} == {
    "README.md", "backend.tf", "providers.tf", "versions.tf"
}
for path in [
    Path("README.md"),
    Path("architecture-plan.md"),
    Path("runbooks/argocd-hardened-design.md"),
    *sorted(Path("specs/k3s-iac-foundation").glob("*.md")),
]:
    text = path.read_text()
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        local = target.split("#", 1)[0]
        if local:
            assert (path.parent / local).resolve().exists(), (path, target)
runbook = Path("runbooks/argocd-hardened-design.md").read_text()
assert ".pi-subagents" not in runbook
assert not re.search(r"\b[0-9a-f]{65}\b", runbook)
controller_home_pattern = "/" + "Users/" + r"[^/\s]+/"
assert not re.search(controller_home_pattern, runbook)
for private_pattern in (
    r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
    r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
    r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
):
    assert not re.search(private_pattern, runbook)
for operational in (
    "kubectl ", "helm install", "helm upgrade", "helm uninstall",
    "argocd app ", "tofu apply", "ansible-playbook ", "--address",
):
    assert operational not in runbook.lower(), operational
assert "**DESIGN ONLY.**" in runbook
assert "CANDIDATE — NOT DEPLOYABLE — NOT SELECTED" in runbook
assert "Argo CD runtime remains **NOT RUN**" in runbook
current = Path("specs/k3s-iac-foundation/testcases.md").read_text()
previous = subprocess.check_output(
    ["git", "show", "HEAD:specs/k3s-iac-foundation/testcases.md"], text=True
)
for case_id in ("KIF-ARGO-01", "KIF-ARGO-02"):
    current_row = next(line for line in current.splitlines() if line.startswith(f"| {case_id} "))
    previous_row = next(line for line in previous.splitlines() if line.startswith(f"| {case_id} "))
    assert current_row == previous_row, case_id
assert len([line for line in current.splitlines() if line.startswith("| KIF-ARGO-03 ")]) == 1
assert not subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True).strip()
print("PASS: exact hardened-design closure, links, hygiene, and KIF-ARGO traceability")
PY
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 10 focused Argo CD hardened-design contracts — OK
Ran 81 full offline tests — OK
PASS: Python compile
PASS: syntax for all 8 production playbooks
Passed: 0 failure(s), 0 warning(s) in 38 files processed of 42 encountered; production profile
PASS: exact 11-file documentation/test closure and unchanged protected deployable source
PASS: exact two-file Kubernetes and four-file zero-resource OpenTofu closure
PASS: local Markdown links, evidence hygiene, unchanged KIF-ARGO-01/02, exactly one KIF-ARGO-03, git diff, and no staged files
```

The design accepts no candidate and authorizes no runtime. It introduces no chart,
values, manifest, Secret, Application, AppProject, RBAC object, NetworkPolicy,
GitHub/Infisical resource, route, or deployment source. Its privileged-installer,
future-Namespace, exact-resource-inventory, Infisical-recovery, and live-adoption-
apply decisions remain open. Argo CD remains **CANDIDATE — NOT DEPLOYABLE — NOT
SELECTED** with runtime **NOT RUN**, and no manual QA case closes.

## Ansible-bootstrap and Keycloak OIDC source-only design — 2026-08-07

The [Keycloak OIDC bootstrap design](../../runbooks/keycloak-oidc-bootstrap-design.md)
and corrected [Argo hardened design](../../runbooks/argocd-hardened-design.md) are
documentation and offline contracts only. Validation contacted no network, registry,
inventory, SSH endpoint, kubeconfig, Kubernetes/provider API, database, secret store,
or cluster and performed no check, apply, route, deployment, staging, commit, or push.

```bash
python3 -m unittest -v tests.test_argocd_hardened_design_contract
python3 -m unittest -v tests.test_keycloak_oidc_bootstrap_design_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
python3 - <<'PY'
from pathlib import Path
import re
import subprocess

expected = {
    "AGENTS.md",
    "README.md",
    "ansible/README.md",
    "architecture-plan.md",
    "runbooks/argocd-hardened-design.md",
    "runbooks/keycloak-oidc-bootstrap-design.md",
    "specs/k3s-iac-foundation/brief.md",
    "specs/k3s-iac-foundation/manual-qa.md",
    "specs/k3s-iac-foundation/requirements.md",
    "specs/k3s-iac-foundation/status.md",
    "specs/k3s-iac-foundation/tasks.md",
    "specs/k3s-iac-foundation/testcases.md",
    "tests/test_argocd_hardened_design_contract.py",
    "tests/test_keycloak_oidc_bootstrap_design_contract.py",
    "tests/test_platform_namespace_contract.py",
    "tests/test_replacement_recovery_contract.py",
}
actual = {
    line[3:]
    for line in subprocess.check_output(["git", "status", "--short"], text=True).splitlines()
    if line
}
assert actual == expected, actual ^ expected
for protected in (
    "ansible/bin", "ansible/playbooks", "ansible/roles", "kubernetes",
    "opentofu", ".github/workflows",
):
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "--", protected], text=True
    ).strip(), protected
assert {
    str(path.relative_to("kubernetes"))
    for path in Path("kubernetes").rglob("*")
    if path.is_file()
} == {
    "platform/namespaces/argocd.yaml",
    "platform/namespaces/platform-edge.yaml",
    "platform/namespaces/platform-secrets.yaml",
    "platform/namespaces/platform-identity.yaml",
}
assert {path.name for path in Path("opentofu").iterdir() if path.is_file()} == {
    "README.md", "backend.tf", "providers.tf", "versions.tf"
}
for path in [
    Path("AGENTS.md"), Path("README.md"), Path("ansible/README.md"),
    Path("architecture-plan.md"),
    *sorted(Path("runbooks").glob("*.md")),
    *sorted(Path("specs/k3s-iac-foundation").glob("*.md")),
]:
    text = path.read_text()
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        local = target.split("#", 1)[0]
        if local:
            assert (path.parent / local).resolve().exists(), (path, target)
for runbook in (
    Path("runbooks/argocd-hardened-design.md"),
    Path("runbooks/keycloak-oidc-bootstrap-design.md"),
):
    text = runbook.read_text()
    assert ".pi-subagents" not in text
    assert not re.search("/" + "Users/" + r"[^/\s]+/", text)
    for pattern in (
        r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
        r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
        r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
    ):
        assert not re.search(pattern, text)
    for operational in (
        "kubectl ", "helm install", "helm upgrade", "helm uninstall",
        "argocd app ", "tofu apply", "ansible-playbook ", "--address",
    ):
        assert operational not in text.lower(), operational
current = Path("specs/k3s-iac-foundation/testcases.md").read_text()
assert len([line for line in current.splitlines() if line.startswith("| KIF-ARGO-03 ")]) == 1
assert len([line for line in current.splitlines() if line.startswith("| KIF-IDP-01 ")]) == 1
assert not subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True).strip()
print("PASS: exact source-only ownership/identity closure, links, hygiene, traceability, and no staged files")
PY
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 11 focused Argo CD hardened-design contracts — OK
Ran 9 focused Keycloak OIDC/bootstrap design contracts — OK
Ran 91 full offline tests — OK
PASS: Python compile
PASS: syntax for all 8 production playbooks
Passed: 0 failure(s), 0 warning(s) in 38 files processed of 42 encountered; production profile
PASS: exact 16-file documentation/test closure and unchanged protected deployable source
PASS: exact two-file Kubernetes and four-file zero-resource OpenTofu closure
PASS: local Markdown links, secret/address/command hygiene, one KIF-ARGO-03, one KIF-IDP-01, git diff, and no staged files
```

Ansible is selected as the future bounded bootstrap installer and privileged
lifecycle owner, but this record authorizes no run. Keycloak is an architecture
target, not a selected release or deployment. At this historical checkpoint, a later
increment added present-only `platform-secrets` and `platform-identity` Namespace
source. That wrapper never ran, and KIF-NS-04 subsequently superseded the source
before runtime. All Argo/Infisical candidate and runtime boundaries remained
unchanged, and MQA-02 remained pending.

## Foundation Namespace deployable-source validation — 2026-08-07

The [foundation Namespace bootstrap](../../runbooks/foundation-namespace-bootstrap.md)
is deployable source with no runtime evidence. This validation was controller-local
and offline. It used no inventory, SSH, become,
kubeconfig, Kubernetes API, host, provider, registry, secret store, check, apply, or
runtime operation. The source is deployable, but every live checkpoint is NOT RUN.

```bash
python3 -m unittest -v tests.test_foundation_namespace_contract
python3 -m unittest -v tests.test_platform_namespace_contract tests.test_argocd_provenance_contract tests.test_argocd_hardened_design_contract tests.test_cloudflared_provenance_contract tests.test_infisical_operator_provenance_contract tests.test_keycloak_oidc_bootstrap_design_contract tests.test_replacement_recovery_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
sh -n ansible/bin/bootstrap-foundation-namespaces
bash -n tests/reject_foundation_namespace_task_start.sh
sh -n tests/validate_foundation_namespace_clean_controller.sh
cd ansible
uv run ansible-playbook playbooks/bootstrap_foundation_namespaces.yml --syntax-check
uv run ansible-playbook ../tests/reject_foundation_namespace_internal_injection.yml -e foundation_namespace_bootstrap_internal_prestate=forged
cd ..
tests/reject_foundation_namespace_task_start.sh
tests/validate_foundation_namespace_clean_controller.sh
cd ansible
for playbook in playbooks/*.yml; do uv run ansible-playbook "$playbook" --syntax-check; done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 10 focused foundation Namespace contracts — OK
Ran 59 affected contracts — OK
Ran 101 full offline tests — OK
Python compile and wrapper/fixture shell syntax — PASS
Forged-internal fixture and direct task-start validator — PASS
Clean-controller validator and all 9 production syntax checks — PASS
Production ansible-lint — PASS, 0 failures/warnings in 42 files processed of 47 encountered
Local Markdown links, exact 31-file/four-Namespace global source closure, historical two-manifest wrapper closure, hygiene, diff check, and no staged files — PASS
Network, inventory, SSH, become, kubeconfig, Kubernetes API, check, apply, and runtime — NOT RUN
```

The future commands are only
`ansible/bin/bootstrap-foundation-namespaces check` and
`ansible/bin/bootstrap-foundation-namespaces apply`. Check, first apply, and the
later idempotence apply each require separate approval. Nothing in this validation
infers any approval or runtime state.

## Node version discovery source-only validation — 2026-08-06

This validation was controller-local only. It did not use inventory, SSH, become,
the protected kubeconfig, a Kubernetes API, host, provider, registry, secret, or
deployment operation. It did not read or rewrite the ignored live report. The
synthetic Node versions, missing-field cases, and sensitive input fields are test data,
not claims about the target cluster.

```bash
python3 -m unittest -v \
  tests.test_ansible_contract.AnsibleSafetyTests.test_node_version_projection_is_exact_and_bounded \
  tests.test_ansible_contract.AnsibleSafetyTests.test_kubernetes_queries_are_exact_and_exclude_sensitive_kinds \
  tests.test_ansible_contract.AnsibleSafetyTests.test_storage_queries_are_exact_and_pvc_scopes_are_bounded \
  tests.test_ansible_contract.AnsibleSafetyTests.test_storage_report_is_curated_and_omits_identifying_raw_fields
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
uv run ansible-playbook ../tests/validate_storage_report.yml
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint playbooks/discover.yml roles/read_only_discovery ../tests/validate_storage_report.yml
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
# Run the embedded documentation/traceability validation under
# "Exact command and actual result" below.
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 4 focused discovery contracts — OK
Ran 48 full offline tests — OK
PASS: Python compile
Synthetic schema-v3 Node/storage render: ok=4 changed=0 failed=0
PASS: syntax for all 8 production playbooks
Passed: 0 failure(s), 0 warning(s) in 9 focused files; production profile
Passed: 0 failure(s), 0 warning(s) in 38 files processed of 42 encountered; production profile
PASS: embedded documentation/traceability validation
PASS: git diff check and no staged files
```

The active virtual environment warning only stated that the separate application
repository environment was ignored in favor of this repository's locked `.venv`.
At the time of this source-only validation, target kubelet and `shared-services`
runtime evidence were pending. The later schema-v3 validation above supersedes that
boundary and records the passed target-minor screen without claiming full Argo CD
compatibility.

## Replacement-host recovery first increment offline validation — 2026-08-05

This validation was controller-local and documentation-only. It did not use
inventory, SSH, a host, kubeconfig, Kubernetes/provider APIs, secret storage, backup
storage, or a registry. It did not isolate a host, read or recover a token, attach
storage, restore data, create a cluster, change a route, or prove replacement
recovery.

```bash
python3 -m unittest -v tests.test_replacement_recovery_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 5 focused replacement recovery tests — OK
Ran 28 full offline tests — OK
PASS: Python compile, diff check, and no staged files
```

The secret-free register intentionally leaves every recovery prerequisite at
`UNKNOWN — STOP`. Operational recovery remains NOT RUN/BLOCKED pending old-host
fencing, exactly one approved identity model, resolved off-node artifacts, and a
later version/datastore/storage-specific execution plan and isolated rehearsal.

## Temporary network probe offline validation — 2026-08-05

This validation was controller-local only. It did not use an inventory file, SSH,
the protected kubeconfig, a Kubernetes API, or an image registry, and it did not
execute plan, run, or cleanup. No digest was resolved or fabricated.

```bash
python3 -m unittest -v tests.test_ansible_contract.NetworkPolicyProbeContractTests
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
uv run ansible-playbook playbooks/probe_k3s_network_policy.yml --syntax-check
uv run ansible-lint playbooks/probe_k3s_network_policy.yml roles/network_policy_probe
cd ..
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 5 focused NetworkPolicy probe contracts — OK
Ran 28 full offline tests — OK
playbook: playbooks/probe_k3s_network_policy.yml
Passed: 0 failure(s), 0 warning(s) in 15 files processed; production profile
PASS: independent final blocker review — APPROVED
PASS: Python compile, diff check, and no staged files
```

The controller environment emitted only a warning that an active virtual
environment from the separate application repository was ignored in favor of this
repository's locked `.venv`; validation still exited zero.

## Temporary network probe live validation — 2026-08-05

The operator supplied the existing Tailscale SSH target and selected account, then
explicitly approved the temporary Argo CD ownership exception and separate create
and delete gates. Those connection details remain only in the ignored mode-`0600`
local inventory and are not recorded in Git. No sudo or secret value was used.

Registry verification selected official BusyBox 1.37.0 index
`sha256:9db7b59979c38555a39def84a31fb98b5296952f9e3afd4f6f11f05b07adfab0`
and its linux/amd64 manifest
`sha256:7a3ebe5bfd1a4a19797d20b0c0bb39d44393e9a03fd852c0865b0f540d868df0`.
Read-only direct inspection of layer
`sha256:436a1b1fd078ee8e117111472724c2827077657189af7a781829d0825d48d2ab`
confirmed `bin/httpd` and `bin/wget`. An attempted local `docker run --rm` could not
connect to the inactive Docker Desktop daemon; it did not affect the later registry
or cluster evidence.

```bash
cd ansible
uv run ansible -i .ansible/inventory.local.yml k3s_servers \
  --limit crtxweb -m ansible.builtin.ping
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/probe_k3s_network_policy.yml \
  --check --diff --limit crtxweb \
  -e k3s_network_probe_action=plan

# The same approved run request was executed first with --check --diff, then with
# only --diff after the exact zero-change plan passed.
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/probe_k3s_network_policy.yml \
  --diff --limit crtxweb \
  -e k3s_network_probe_action=run \
  -e network_policy_probe_run_id=8d96ec2146d54312e182fd12 \
  -e network_policy_probe_image=docker.io/library/busybox@sha256:7a3ebe5bfd1a4a19797d20b0c0bb39d44393e9a03fd852c0865b0f540d868df0 \
  -e network_policy_probe_image_architecture=linux/amd64 \
  -e network_policy_probe_image_verification_reference=docker-busybox-1.37.0-linux-amd64-7a3ebe5b-httpd-wget \
  -e network_policy_probe_ownership_exception_approved=true \
  -e network_policy_probe_create_approved=true \
  -e network_policy_probe_delete_approved=true

uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/probe_k3s_network_policy.yml \
  --check --diff --limit crtxweb \
  -e k3s_network_probe_action=cleanup \
  -e network_policy_probe_run_id=8d96ec2146d54312e182fd12 \
  -e network_policy_probe_ownership_exception_approved=true \
  -e network_policy_probe_delete_approved=true
```

Actual result:

```text
Ansible ping: SUCCESS, changed=false
Read-only planner: ok=12 changed=0 unreachable=0 failed=0
Run check: ok=18 changed=0 unreachable=0 failed=0
Phases: baseline-allowed Succeeded; baseline-denied Succeeded;
        deny-allowed Failed; deny-denied Failed;
        selective-allowed Succeeded; selective-denied Failed;
        rollback-allowed Succeeded; rollback-denied Succeeded
Functional run: ok=225 changed=43 unreachable=0 failed=0 skipped=14
Cleanup: 12 live exact identities removed after two policies were UID-deleted;
         cleanup_verified=true; Namespace/public exposure not created
Post-cleanup check: ok=20 changed=0 unreachable=0 failed=0;
                    exact_identity_count=0; deletion_performed=false
```

This proves bounded CNI connectivity and NetworkPolicy enforcement on the current
single-node cluster at the tested revision. It is not a permanent workload, a
future-cluster guarantee, replacement-host evidence, or permission for another run
without fresh approvals and a unique Run ID.

## Storage discovery increment offline validation — 2026-08-05

This validation was controller-local only. It did not use inventory, SSH, become,
the protected kubeconfig, a Kubernetes API, or filesystem content. It did not alter
or replace the prior elevated discovery or CNI/NetworkPolicy evidence.

```bash
python3 -m unittest -v \
  tests.test_ansible_contract.AnsibleSafetyTests.test_storage_queries_are_exact_and_pvc_scopes_are_bounded \
  tests.test_ansible_contract.AnsibleSafetyTests.test_storage_report_is_curated_and_omits_identifying_raw_fields \
  tests.test_ansible_contract.AnsibleSafetyTests.test_storageclass_and_volume_projection_is_exact_and_path_safe
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
uv run ansible-playbook ../tests/validate_storage_report.yml
uv run ansible-playbook playbooks/discover.yml --syntax-check
uv run ansible-lint playbooks/discover.yml roles/read_only_discovery
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint .
cd ..
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Focused storage tests and full offline suite — OK
PASS: synthetic collision-safe storage render ok=3 changed=0 failed=0
playbook: playbooks/discover.yml
Passed: 0 failure(s), 0 warning(s) in 8 focused files; production profile
PASS: syntax for all 6 playbooks
Passed: 0 failure(s), 0 warning(s) in 30 files processed of 33 encountered; production profile
PASS: Python compile, diff check, and no staged files
```

The same benign project-environment warning described above appeared on `uv`
commands.

## Extended storage discovery live validation — 2026-08-06

The operator ran the separately approved elevated one-host check/diff from the
ignored local inventory and entered the become password only at the local prompt.
The play did not mount, repair, format, read filesystem contents, or otherwise
mutate a disk or Kubernetes object.

```bash
cd ansible
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/discover.yml \
  --check --diff --limit crtxweb \
  -e read_only_discovery_enable_elevated=true \
  -e read_only_discovery_elevated_approved=true \
  --ask-become-pass
```

Actual result and human review:

```text
Play recap: ok=17 changed=1 unreachable=0 failed=0 skipped=1
Only write: ignored controller-local inventory.local.ansible.json, mode 0600
Host: Debian 13 x86_64; 6 cores; 15839 MiB memory
Root filesystem: ext4; 472339357696 bytes total; 445053747200 available
NVMe: 500107862016 bytes; non-rotational; three partitions
Separate disk: 1000204886016 bytes; rotational; non-removable; one unmounted partition
Unmounted filesystem/content/health: UNKNOWN — no inference from mount-only facts
StorageClass: local-path; reclaim Delete; WaitForFirstConsumer; expansion false
PersistentVolumes: 0
PersistentVolumeClaims in five bounded namespaces: 0
```

Historical scope boundary: the fifth PVC query in that approved live report was
`shared-data`. The later separately approved schema-v3 rerun recorded above now
live-verifies the current exact `shared-services` query with count zero. The
historical report itself was not edited.

Decision boundary: keep initial k3s workloads on the NVMe-backed local-path storage.
Treat the separate disk only as a backup candidate until a separately approved
non-destructive filesystem, health, and content inspection resolves its state. Do
not mount, repair, format, repartition, or write it. Local backup capacity never
replaces the required encrypted off-node copy.

## OpenTofu host-installer and zero-resource scaffold offline validation — 2026-08-06

The initial installer validation and the later controller-transfer fix validation
were controller-local only. They used no inventory, SSH, become,
Kubernetes/provider API, provider registry, Cloudflare authentication, Google Drive,
or state. The fix validation did not contact the host or write the ignored controller
cache. It created no lockfile, state, plan, credential, resource, or host change.

Authenticated release provenance was independently verified controller-side before
this implementation. The official sources and reviewed values are:

- `https://github.com/opentofu/opentofu/releases/download/v1.12.5/tofu_1.12.5_SHA256SUMS`
  — SHA-256 `120345f8a2493375aebbca072106de425b2eb227837f8064440b8d911e36f987`;
- `https://github.com/opentofu/opentofu/releases/download/v1.12.5/tofu_1.12.5_SHA256SUMS.gpgsig`
  — verified signer fingerprint `E3E6E43D84CB852EADB0051D0C0AF313E5FD9F80`;
- `tofu_1.12.5_linux_amd64.tar.gz` — signed-manifest SHA-256
  `a6894d45ae7a17ce83189cce8fe04b5a65f68cefceb62455b5a6a89fa53ab38f`;
- extracted `tofu` — independently verified SHA-256
  `36dae7ca1e4f1552a6faef27179dc16ef403203e956f31416c17b3d87a38c3f4`.

The controller-transfer role enforces the reviewed archive digest before and after
transfer, and the host enforces the extracted-payload digest. It does not download
the checksum manifest or repeat OpenPGP verification. No network provenance
verification was rerun during this offline fix pass.

```bash
python3 -m unittest -v tests.test_opentofu_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
uv run ansible-playbook playbooks/install_opentofu.yml --syntax-check
uv run ansible-lint playbooks/install_opentofu.yml roles/opentofu_install
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint .
cd ..
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Focused OpenTofu contracts — PASS, 7 tests
Full offline suite — PASS, 35 tests
Python compile — PASS
OpenTofu installer syntax — PASS
Focused production lint — PASS, 0 failures and 0 warnings in 4 files
All 7 playbook syntax checks — PASS
Full production lint — PASS, 0 failures and 0 warnings; 33 of 36 files processed
git diff --check and no-staged-files — PASS
```

`tofu fmt` and `tofu validate` are NOT RUN: no controller OpenTofu binary was
approved or installed, and provider initialization/download is a later gate. The HCL
is statically checked and conventionally formatted, but that is not provider-aware
validation. The original host check, bounded failure, reviewed controller-transfer recovery,
and idempotence evidence are recorded below. Lockfile generation, state creation and
encryption, off-node copy/restore, plan, and apply remain NOT RUN/BLOCKED.

## OpenTofu first host installation attempt — 2026-08-06

The operator used the ignored local inventory and entered the become password only
at the local prompt. The approved controller-to-host check completed without
mutation:

```text
crtxweb: ok=27 changed=6 unreachable=0 failed=0 skipped=12
```

The separately approved live attempt then failed at the old remote
`ansible.builtin.get_url` task before an archive was written:

```text
Request failed: <urlopen error [Errno 113] No route to host>
crtxweb: ok=21 changed=2 unreachable=0 failed=1 skipped=3
```

The two changed tasks created only the exact root-owned parent directories and the
empty operator-owned mode-`0700` project state directory. No archive, versioned
binary, `/usr/local/bin/tofu` selector, state file, provider operation, Kubernetes
operation, or external resource was created. k3s and Tailscale had passed the
pre-install running-state gate; the failed attempt did not contain a service
mutation task. A blind retry was rejected. The revised role downloads the pinned
archive into ignored controller-local `ansible/.ansible/cache/opentofu/`, transfers
it using `ansible.builtin.copy`, and rechecks the root-owned host archive before
extraction.

The reviewed recovery check produced the expected six predictions without mutation:

```text
crtxweb: ok=33 changed=6 unreachable=0 failed=0 skipped=15
```

The separately approved live recovery then downloaded and verified the archive on
the controller, transferred and reverified it on the host, extracted the exact
payload, selected `/usr/local/bin/tofu`, verified version `1.12.5` as the non-root
operator, and confirmed k3s/Tailscale remained running:

```text
crtxweb: ok=39 changed=6 unreachable=0 failed=0 skipped=9
```

The immediate approved second run revalidated every boundary and converged:

```text
crtxweb: ok=30 changed=0 unreachable=0 failed=0 skipped=18
```

The ignored controller archive is current-controller-owned mode `0600` with SHA-256
`a6894d45ae7a17ce83189cce8fe04b5a65f68cefceb62455b5a6a89fa53ab38f`;
its cache directories are mode `0700`. The protected host project directory remains
empty: no state file, provider initialization, lockfile, plan, apply, Kubernetes
operation, or external resource was created. Rollback remains selector-only and was
not run.

## Platform Namespace bootstrap offline validation — 2026-08-06

This validation was controller-local only. It used no inventory, SSH, become,
kubeconfig, Kubernetes API, registry, provider, or external credential. It created
no Namespace or other Kubernetes object. The committed manifests define only
`argocd` and `platform-edge`; `shared-services`, DEV, and PROD remain future names
and were not created. Argo CD and cloudflared themselves remain uninstalled.

```bash
python3 -m unittest -v tests.test_platform_namespace_contract
python3 -m unittest -v \
  tests.test_platform_namespace_contract.PlatformNamespaceBootstrapContractTests.test_synthetic_ancestor_symlink_is_noncanonical
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
sh -n ansible/bin/bootstrap-platform-namespaces
bash -n tests/reject_platform_namespace_task_start.sh
sh -n tests/validate_platform_namespace_clean_controller.sh
tests/validate_platform_namespace_clean_controller.sh
tests/reject_platform_namespace_task_start.sh
cd ansible
uv run ansible-playbook -i localhost, -c local \
  ../tests/reject_platform_namespace_internal_injection.yml \
  --extra-vars '{"platform_namespace_bootstrap_internal_prestate":{"resources":[]},"platform_namespace_bootstrap_internal_manifests":[]}'
uv run ansible-playbook playbooks/bootstrap_platform_namespaces.yml --syntax-check
uv run ansible-lint playbooks/bootstrap_platform_namespaces.yml roles/platform_namespace_bootstrap
uv run ansible-lint ../tests/reject_platform_namespace_internal_injection.yml
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-playbook ../tests/validate_storage_report.yml
uv run ansible-lint .
cd ..
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Focused platform Namespace contracts — PASS, 12 tests
Synthetic ancestor-symlink negative contract — PASS, 1 test
Non-passthrough control-flow/toolchain negatives — PASS; wrapper returned 64 before Ansible for `--start-at-task` and `--step`, uses no bare `uv`, launches the repository `.venv` controller through `env -i`, and binds mutation to a mode-0600 random single-run attestation; direct task-start with only the old static marker skipped both Namespace items and could not mutate
Controller-only forged internal-variable fixture — PASS, ok=4 changed=0 failed=0 rescued=1; unique first-task guard rejected both extra vars before approval/path/API tasks
Full offline suite — PASS, 47 tests
Python compile, wrapper/clean-controller `sh -n`, and task-start fixture `bash -n` — PASS
Wrapper-equivalent clean controller startup — PASS with `LC_ALL=C.UTF-8`; Namespace playbook syntax parsed under `env -i`
Namespace bootstrap and all 8 playbook syntax checks — PASS
Synthetic storage report — PASS, ok=3 changed=0 failed=0
Focused production lint — PASS, 0 failures/warnings in 4 files
Controller-only negative fixture production lint — PASS, 0 failures/warnings in 3 files
Full production lint — PASS, 0 failures/warnings; 37 of 41 files processed
git diff --check and no-staged-files — PASS
```

At this source-validation checkpoint runtime remained NOT RUN. The later separately
approved check evidence below supersedes only that check boundary. The check uses only
`ansible/bin/bootstrap-platform-namespaces check`; live and idempotence runs must use
only its `apply` mode. The wrapper supplies the exact ignored inventory, `--diff`,
one-host limit, approval, and become prompt, and accepts no passthrough options. A foreign existing
`argocd` or `platform-edge` Namespace fails closed unless all bootstrap/future-owner
labels already match. Ansible remains the truthful bootstrap writer. Argo CD is only
the future desired owner: handoff remains pending its installation, Namespace
adoption or Application registration, and successful sync evidence. The label alone
is not a handoff. Live reconciliation is state-present-only. Rollback preserves the
Namespaces; deletion is a separate destructive future decision and is not present
in this playbook.

## Namespace stage-boundary source-only correction — 2026-08-07

This controller-local correction makes the exact two-Namespace present-only
bootstrap a documented pre-Stage-4 exception in both the architecture and task
checklist, with separate check, first-apply, and idempotence approvals. The contract
also binds that placement to root `AGENTS.md` authority and fails on stale Stage 4
Namespace checklist entries. It leaves the Stage 4 pinned-version, reviewed-kubelet
compatibility, and approved-secret-zero entry gates mandatory for Argo CD,
Infisical, cloudflared, and every other persistent Kubernetes object. It changed no
manifest or executable bootstrap source and used no inventory, SSH, become,
kubeconfig, Kubernetes API, provider, secret, or deployment operation.

```bash
python3 -m unittest -v tests.test_platform_namespace_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint playbooks/bootstrap_platform_namespaces.yml roles/platform_namespace_bootstrap
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
# Run the embedded documentation/traceability validation under
# "Exact command and actual result" below.
python3 - <<'PY'
import subprocess

changed = set(
    subprocess.check_output(["git", "diff", "--name-only"], text=True).splitlines()
)
assert changed == {
    "architecture-plan.md",
    "specs/k3s-iac-foundation/tasks.md",
    "specs/k3s-iac-foundation/testcases.md",
    "tests/test_platform_namespace_contract.py",
}
assert not any(
    path.startswith("ansible/") or path.startswith("kubernetes/")
    for path in changed
)
print("PASS: exact four-file source-only diff; no manifest or executable bootstrap change")
PY
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Focused platform Namespace contracts — PASS, 13 tests
Full offline suite — PASS, 58 tests
Python compile — PASS
All 8 production playbook syntax checks — PASS
Focused production lint — PASS, 0 failures/warnings in 4 files
Full production lint — PASS, 0 failures/warnings in 38 files processed of 42 encountered
Embedded documentation/traceability validation — PASS
Exact four-file source-only diff with no manifest or executable change — PASS
Git diff check and no-staged-files check — PASS
```

At this source-correction checkpoint runtime remained **NOT RUN**. The later
separately approved check evidence below supersedes only the wrapper-check boundary;
at that checkpoint both applies remained unrun. This source correction itself was not
approval for discovery, the Namespace wrapper, Argo CD, Infisical, cloudflared, or any
other live action.

## Platform Namespace wrapper check — 2026-08-07

The operator separately approved and ran only the non-passthrough wrapper check from
the repository root:

```bash
# Run from the repository root.
ansible/bin/bootstrap-platform-namespaces check
```

Actual bounded result:

```text
Play recap: ok=19 changed=1 unreachable=0 failed=0 skipped=2 rescued=0 ignored=0
Protected approval/attestation/path/manifest/service/kubeconfig/pre-state/foreign-existing assertions: PASS
Manifest contract: exactly v1 Namespace argocd and platform-edge; exactly three reviewed labels each
Labels: app.kubernetes.io/part-of=cristex-platform; cristex.io/bootstrap-writer=ansible; cristex.io/desired-owner=argocd
Prediction: changed item=argocd; changed item=platform-edge
Live post-state query and identity verification: skipped by design in check mode
k3s and tailscaled service assertions before/after: PASS
Namespace or other Kubernetes-object mutation: none
```

The recap reports `changed=1` because one loop task predicted changes for both exact
items; it does not mean only one Namespace was predicted. The manifests remain
present-only and authorize no deletion or other kind. The raw verbose output and
controller-local username, UID, inode, timestamp, and path metadata are not copied
into Git. At this historical checkpoint the check did not approve the first apply;
both applies were **NOT RUN**. The later separately approved first-apply and
idempotence evidence below supersedes both historical execution boundaries. Argo CD
is still only the future desired owner; the
labels are not an ownership handoff, and no Stage 4 gate is waived.

Offline evidence-record validation:

```bash
python3 -m unittest -v tests.test_platform_namespace_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint playbooks/bootstrap_platform_namespaces.yml roles/platform_namespace_bootstrap
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
# Run the embedded documentation/traceability validation under
# "Exact command and actual result" below.
python3 - <<'PY'
import subprocess

expected_changed_files = {
    "AGENTS.md",
    "README.md",
    "ansible/README.md",
    "architecture-plan.md",
    "specs/k3s-iac-foundation/brief.md",
    "specs/k3s-iac-foundation/manual-qa.md",
    "specs/k3s-iac-foundation/requirements.md",
    "specs/k3s-iac-foundation/status.md",
    "specs/k3s-iac-foundation/tasks.md",
    "specs/k3s-iac-foundation/testcases.md",
    "tests/test_platform_namespace_contract.py",
}
status_lines = subprocess.check_output(
    ["git", "status", "--short"], text=True
).splitlines()
changed_files = {line[3:] for line in status_lines if line}
assert changed_files == expected_changed_files, changed_files ^ expected_changed_files
for protected_path in (
    "ansible/bin",
    "ansible/playbooks",
    "ansible/roles",
    "kubernetes",
    "opentofu",
    ".github/workflows",
):
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "--", protected_path], text=True
    ).strip(), protected_path
print("PASS: exact 11-file documentation/test closure; deployable source unchanged")
PY
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Focused platform Namespace contracts — PASS, 14 tests
Full offline suite — PASS, 66 tests
Python compile — PASS
All 8 production playbook syntax checks — PASS
Focused production lint — PASS, 0 failures/warnings in 4 files
Full production lint — PASS, 0 failures/warnings in 38 files processed of 42 encountered
Embedded documentation/traceability validation — PASS
Exact documentation/test-only source closure — PASS
Git diff check and no-staged-files check — PASS
```

## Platform Namespace first apply — 2026-08-07

The operator separately approved and ran only the first non-passthrough wrapper
apply from the repository root:

```bash
# Run from the repository root.
ansible/bin/bootstrap-platform-namespaces apply
```

Actual bounded result:

```text
Play recap: ok=21 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
Protected internal-variable/approval/attestation/path/manifest/service/kubeconfig/pre-state/foreign-existing assertions: PASS
Manifest contract: exactly v1 Namespace argocd and platform-edge; exactly three reviewed labels each
Labels: app.kubernetes.io/part-of=cristex-platform; cristex.io/bootstrap-writer=ansible; cristex.io/desired-owner=argocd
Reconciliation: changed item=argocd; changed item=platform-edge
Post-state requery: ok for both exact items
Exact identity, all three labels, and status.phase=Active assertions: ok for both exact items under no_log
k3s and tailscaled service assertions before/after: PASS
Skipped/failed/unreachable tasks: none
Other persistent kind authorized or changed: none
```

The recap reports `changed=1` because one loop task changed both exact Namespace
items. The wrapper authorized only the two committed `state: present` Namespace
manifests; no deletion or other kind was authorized. Argo CD, Infisical, cloudflared,
Secrets, workloads, Services, routes, and other persistent objects were not installed
or created. Argo CD remains only the future desired owner: labels do not establish an
ownership handoff. The raw verbose output and controller-local username, UID, inode,
timestamp, and stat/path metadata are not copied into Git. At this historical
first-apply checkpoint, the second idempotence apply had not yet run and still needed
its separate approval with `changed=0` required. The later idempotence section
supersedes that execution boundary.

Offline evidence-record validation:

```bash
python3 -m unittest -v tests.test_platform_namespace_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint playbooks/bootstrap_platform_namespaces.yml roles/platform_namespace_bootstrap
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
# Run the embedded documentation/traceability validation under
# "Exact command and actual result" below.
python3 - <<'PY'
import subprocess

expected_changed_files = {
    "AGENTS.md",
    "README.md",
    "ansible/README.md",
    "architecture-plan.md",
    "specs/k3s-iac-foundation/brief.md",
    "specs/k3s-iac-foundation/manual-qa.md",
    "specs/k3s-iac-foundation/requirements.md",
    "specs/k3s-iac-foundation/status.md",
    "specs/k3s-iac-foundation/tasks.md",
    "specs/k3s-iac-foundation/testcases.md",
    "tests/test_platform_namespace_contract.py",
}
status_lines = subprocess.check_output(
    ["git", "status", "--short"], text=True
).splitlines()
changed_files = {line[3:] for line in status_lines if line}
assert changed_files == expected_changed_files, changed_files ^ expected_changed_files
for protected_path in (
    "ansible/bin",
    "ansible/playbooks",
    "ansible/roles",
    "kubernetes",
    "opentofu",
    ".github/workflows",
):
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "--", protected_path], text=True
    ).strip(), protected_path
print("PASS: exact 11-file documentation/test closure; deployable source unchanged")
PY
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Focused platform Namespace contracts — PASS, 15 tests
Full offline suite — PASS, 67 tests
Python compile — PASS
All 8 production playbook syntax checks — PASS
Focused production lint — PASS, 0 failures/warnings in 4 files
Full production lint — PASS, 0 failures/warnings in 38 files processed of 42 encountered
Embedded documentation/traceability validation — PASS
Exact 11-file documentation/test-only source closure — PASS
Git diff check and no-staged-files check — PASS
```

## Platform Namespace idempotence apply — 2026-08-07

The operator separately approved the idempotence checkpoint and used only the
non-passthrough wrapper from the repository root:

```bash
# Run from the repository root.
ansible/bin/bootstrap-platform-namespaces apply
```

The initial invocation passed controller-side internal-variable, approval,
attestation, canonical-path, and exact manifest assertions, then stopped on failed
local sudo authentication before service preflight or any Kubernetes pre-state or
reconciliation task:

```text
Play recap: ok=10 changed=0 unreachable=0 failed=1 skipped=0 rescued=0 ignored=0
Failure boundary: before service preflight and Kubernetes reconciliation
Namespace or other Kubernetes-object mutation: none
Idempotence proof from this attempt: none
```

No password or raw verbose output is recorded. Because this invocation did not reach
Kubernetes reconciliation, its `changed=0` is only non-mutation evidence, not
idempotence evidence.

The operator retried the already separately approved idempotence checkpoint with the
same exact wrapper command. The accepted bounded result was:

```text
Play recap: ok=21 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
Protected internal-variable/approval/attestation/path/manifest/service/kubeconfig/pre-state/foreign-existing assertions: PASS
Manifest contract: exactly v1 Namespace argocd and platform-edge; exactly three reviewed labels each
Labels: app.kubernetes.io/part-of=cristex-platform; cristex.io/bootstrap-writer=ansible; cristex.io/desired-owner=argocd
Reconciliation: ok item=argocd; ok item=platform-edge
Post-state requery: ok for both exact items
Exact identity, all three labels, and status.phase=Active assertions: ok for both exact items under no_log
k3s and tailscaled service assertions before/after: PASS
Changed/skipped/failed/unreachable tasks: none
Other persistent kind authorized or changed: none
```

The successful retry is the idempotence proof: the one present-only reconciliation
task reported both exact items `ok` and the play recap reported `changed=0`. The
wrapper authorized only the committed `argocd` and `platform-edge` Namespace
manifests and has no deletion path. Argo CD remains only the future desired owner;
no installation, adoption, Application registration, sync, or ownership handoff is
claimed. No Argo CD, Infisical, cloudflared, Secret, workload, Service, route, other
Namespace, or other persistent kind was authorized or created. The exact check,
first apply, and idempotence checkpoints are complete, and this pre-Stage-4 bounded
exception is closed without waiving any Stage 4 gate.

The supplied verbose output included controller-local identity and stat/path
metadata. Those values, the password, inventory, kubeconfig, host/address data, and
raw output are deliberately not copied into Git; only the sanitized task boundaries
and recaps above are retained.

## Documentation and traceability

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-DOC-01 | KIF-004, KIF-030 | Required shape and links | Canonical root/spec documents, locked uv project files, Ansible discovery files, source-only Argo/cloudflared/Infisical candidate provenance, Keycloak OIDC/bootstrap design, and offline contract tests exist; local Markdown links resolve | PASS — bounded offline documentation check passed |
| KIF-DOC-02 | KIF-005, KIF-009, KIF-022 | Ownership consistency | Ansible/OpenTofu/Argo CD/Infisical/GitHub Actions have non-overlapping owners; Ansible owns bounded bootstrap/privileged lifecycle, Argo owns namespaced state only after Ansible stops and evidenced object-by-object handoff passes, the completed two-Namespace exception remains closed, and Traefik remains sole ingress | PASS — authoritative documents remain consistent; a label alone is not a handoff and dual reconciliation is forbidden |
| KIF-DOC-03 | KIF-001–KIF-003, KIF-006 | Honest implementation boundary | Executed Ansible evidence distinguishes completed OpenTofu installation, completed Namespace check/first apply/idempotence checkpoints including the pre-reconciliation credential failure, and non-deployable Argo/cloudflared/Infisical candidate provenance; only the exact two Namespaces were created, with no controller install, state/provider operation, general host baseline, hosted runtime, or deployment claimed | PASS — repository scan and status wording passed |
| KIF-DOC-04 | KIF-013–KIF-015 | No committed secret/address material | Repository source contains no private-key block, provider token, kubeconfig content, credential value, or private IPv4 address | PASS — bounded source scan passed |
| KIF-DOC-05 | KIF-016–KIF-021 | Shared-services and policy risk | Separate principals/backups/vhosts and negative tests remain required; object listings alone do not prove policy enforcement | PASS — functional probe evidence and remaining application-isolation QA are explicit |
| KIF-DOC-06 | KIF-023–KIF-030 | Honest future evidence | One future discovery case is PARTIAL, eleven future runtime cases remain NOT RUN, one manual case passes, one manual case is PARTIAL, and thirteen manual cases remain PENDING | PASS — counts and status assertions passed |

All requirements KIF-001 through KIF-030 remain represented by the implementation,
documentation, manual, or future-runtime cases in this file. Only the explicit live
CNI, storage, and OpenTofu evidence above closes their bounded runtime gates; the
platform Namespace bootstrap has a passed non-mutating wrapper check, first apply,
and `changed=0` idempotence retry after a pre-reconciliation credential failure.
Argo CD/cloudflared/Infisical candidate provenance and the Keycloak identity design
remain source-only with no runtime evidence. The records are
[`argocd-candidate-provenance.md`](../../runbooks/argocd-candidate-provenance.md),
[`argocd-hardened-design.md`](../../runbooks/argocd-hardened-design.md),
[`keycloak-oidc-bootstrap-design.md`](../../runbooks/keycloak-oidc-bootstrap-design.md),
[`cloudflared-candidate-provenance.md`](../../runbooks/cloudflared-candidate-provenance.md),
and [`infisical-operator-candidate-provenance.md`](../../runbooks/infisical-operator-candidate-provenance.md),
not deployable desired state.

## Exact command and actual result

Run from the repository root:

```bash
set -euo pipefail

required=(
  AGENTS.md
  README.md
  architecture-plan.md
  .gitignore
  pyproject.toml
  uv.lock
  ansible/ansible.cfg
  ansible/requirements.yml
  ansible/README.md
  ansible/inventory/hosts.yml
  ansible/playbooks/discover.yml
  ansible/playbooks/bootstrap_dependencies.yml
  ansible/playbooks/configure_k3s_admin_access.yml
  ansible/playbooks/install_opentofu.yml
  ansible/playbooks/bootstrap_platform_namespaces.yml
  ansible/bin/bootstrap-platform-namespaces
  ansible/roles/opentofu_install/defaults/main.yml
  ansible/roles/opentofu_install/tasks/main.yml
  ansible/roles/platform_namespace_bootstrap/defaults/main.yml
  ansible/roles/platform_namespace_bootstrap/tasks/main.yml
  ansible/roles/read_only_discovery/defaults/main.yml
  ansible/roles/read_only_discovery/tasks/main.yml
  ansible/roles/read_only_discovery/tasks/host.yml
  ansible/roles/read_only_discovery/tasks/kubernetes.yml
  ansible/roles/read_only_discovery/tasks/report.yml
  ansible/roles/read_only_discovery/templates/report.json.j2
  opentofu/README.md
  opentofu/backend.tf
  opentofu/providers.tf
  opentofu/versions.tf
  kubernetes/platform/namespaces/argocd.yaml
  kubernetes/platform/namespaces/platform-edge.yaml
  kubernetes/platform/namespaces/platform-secrets.yaml
  kubernetes/platform/namespaces/platform-identity.yaml
  ansible/bin/bootstrap-foundation-namespaces
  ansible/playbooks/bootstrap_foundation_namespaces.yml
  ansible/roles/foundation_namespace_bootstrap/defaults/main.yml
  ansible/roles/foundation_namespace_bootstrap/tasks/main.yml
  tests/reject_foundation_namespace_internal_injection.yml
  tests/reject_foundation_namespace_task_start.sh
  tests/validate_foundation_namespace_clean_controller.sh
  tests/test_foundation_namespace_contract.py
  runbooks/foundation-namespace-bootstrap.md
  tests/test_ansible_contract.py
  tests/test_opentofu_contract.py
  tests/test_platform_namespace_contract.py
  tests/reject_platform_namespace_internal_injection.yml
  tests/reject_platform_namespace_task_start.sh
  tests/validate_platform_namespace_clean_controller.sh
  tests/test_replacement_recovery_contract.py
  tests/test_argocd_provenance_contract.py
  tests/test_argocd_hardened_design_contract.py
  tests/test_keycloak_oidc_bootstrap_design_contract.py
  tests/test_cloudflared_provenance_contract.py
  tests/test_infisical_operator_provenance_contract.py
  tests/validate_storage_report.yml
  runbooks/replacement-host-recovery.md
  runbooks/recovery-artifact-register.md
  runbooks/argocd-candidate-provenance.md
  runbooks/argocd-hardened-design.md
  runbooks/keycloak-oidc-bootstrap-design.md
  runbooks/cloudflared-candidate-provenance.md
  runbooks/infisical-operator-candidate-provenance.md
  specs/k3s-iac-foundation/brief.md
  specs/k3s-iac-foundation/requirements.md
  specs/k3s-iac-foundation/tasks.md
  specs/k3s-iac-foundation/testcases.md
  specs/k3s-iac-foundation/manual-qa.md
  specs/k3s-iac-foundation/status.md
)
for path in "${required[@]}"; do
  test -f "$path"
done

test ! -e tools/collect_inventory.py
test ! -e tools/__init__.py
test ! -e tests/test_collect_inventory.py

python3 -m unittest discover -s tests -v
python3 -m compileall -q tests

python3 - <<'PY'
import re
from pathlib import Path

spec_dir = Path("specs/k3s-iac-foundation")
expected_specs = {"brief.md", "requirements.md", "tasks.md", "testcases.md", "manual-qa.md", "status.md"}
assert {path.name for path in spec_dir.glob("*.md")} == expected_specs

text_paths = [Path("AGENTS.md"), Path("README.md"), Path("architecture-plan.md"), Path(".gitignore"), Path("pyproject.toml"), Path("uv.lock")]
text_paths += [path for path in sorted(Path("ansible").rglob("*")) if ".ansible" not in path.parts]
text_paths += sorted(Path("opentofu").glob("*"))
text_paths += [path for path in sorted(Path("kubernetes").rglob("*")) if path.is_file()]
text_paths += [path for path in sorted(Path("tests").glob("*")) if path.is_file()]
text_paths += sorted(Path("runbooks").glob("*.md"))
text_paths += sorted(spec_dir.glob("*.md"))
text_paths = [path for path in text_paths if path.is_file()]
combined = "\n".join(path.read_text() for path in text_paths)

for path in [Path("README.md"), Path("architecture-plan.md"), *sorted(spec_dir.glob("*.md"))]:
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", path.read_text()):
        if "://" in target or target.startswith("#"):
            continue
        local = target.split("#", 1)[0]
        if local:
            assert (path.parent / local).resolve().exists(), (path, target)

expected_ids = {f"KIF-{number:03d}" for number in range(1, 31)}
found_ids = set(re.findall(r"KIF-\d{3}", (spec_dir / "testcases.md").read_text()))
assert found_ids == expected_ids, sorted(expected_ids - found_ids)
assert len(re.findall(r"^\| KIF-FUT-\d{2} .* \| NOT RUN —", (spec_dir / "testcases.md").read_text(), re.MULTILINE)) == 11
assert len(re.findall(r"^\| KIF-FUT-\d{2} .* \| PARTIAL —", (spec_dir / "testcases.md").read_text(), re.MULTILINE)) == 1
assert len(re.findall(r"^\| MQA-\d{2} .* \| PENDING(?: —[^|]*)? \|$", (spec_dir / "manual-qa.md").read_text(), re.MULTILINE)) == 13
assert len(re.findall(r"^\| MQA-\d{2} .* \| PARTIAL —", (spec_dir / "manual-qa.md").read_text(), re.MULTILINE)) == 1
assert len(re.findall(r"^\| MQA-\d{2} .* \| PASS —", (spec_dir / "manual-qa.md").read_text(), re.MULTILINE)) == 1
assert re.search(
    r"^\| KIF-ADM-05 .* \| PASS —",
    (spec_dir / "testcases.md").read_text(),
    re.MULTILINE,
)
assert re.search(
    r"^\| KIF-REB-02 .* \| PASS —",
    (spec_dir / "testcases.md").read_text(),
    re.MULTILINE,
)

status = (spec_dir / "status.md").read_text()
for statement in [
    "state: agent:in-progress",
    "phase: implementing",
    "historical Namespace idempotence plus deployable-but-NOT-RUN foundation Namespace source, Argo 3.5 readiness, and Argo/Keycloak architecture contracts pass",
    "candidate selection, six architecture decisions, security/Secret/adoption/runtime, and provider/state/backup pending",
    "all nine exact Kubernetes",
    "Exact k3s\n  admission/runtime and node pullability remain unproven",
    "CANDIDATE — NOT DEPLOYABLE — NOT SELECTED",
    "executed group-scoped k3s",
]:
    assert statement in status, statement

brief = (spec_dir / "brief.md").read_text()
for statement in [
    "The approved\nhost check passed",
    "the first live run created only the exact managed parent and\nempty protected state directories",
    "reviewed controller-transfer recovery then passed check, live installation, and a\n`changed=0` rerun",
    "Exact `argocd` and `platform-edge` Namespace\nmanifests and a bounded present-only Ansible bootstrap are implemented. Its\nseparately approved non-passthrough wrapper check passed",
    "The retry passed at\n`ok=21 changed=0 unreachable=0 failed=0 skipped=0`",
    "Provider initialization, state, plan, and apply also remain unrun",
]:
    assert statement in brief, statement
assert "host check/live run" not in brief
assert "controller-transfer retry and idempotence remain unrun" not in brief

assert {path.name for path in Path("opentofu").iterdir() if path.is_file()} == {
    "README.md", "backend.tf", "providers.tf", "versions.tf"
}
assert {
    str(path.relative_to(Path("kubernetes")))
    for path in Path("kubernetes").rglob("*")
    if path.is_file()
} == {
    "platform/namespaces/argocd.yaml",
    "platform/namespaces/platform-edge.yaml",
    "platform/namespaces/platform-secrets.yaml",
    "platform/namespaces/platform-identity.yaml",
}
namespace_playbook = Path("ansible/playbooks/bootstrap_platform_namespaces.yml")
assert namespace_playbook.read_text() == """---
- name: Bootstrap the approved persistent platform Namespaces
  hosts: k3s_servers
  gather_facts: false
  become: true
  any_errors_fatal: true
  serial: 1

  roles:
    - role: platform_namespace_bootstrap
"""
namespace_role = Path("ansible/roles/platform_namespace_bootstrap")
assert {
    str(path.relative_to(namespace_role))
    for path in namespace_role.rglob("*")
    if path.is_file()
} == {"defaults/main.yml", "tasks/main.yml"}
for executable in [namespace_playbook, *sorted((namespace_role / "tasks").rglob("*.yml"))]:
    executable_text = executable.read_text()
    for forbidden in [
        "pre_tasks:", "post_tasks:", "include_tasks:", "import_tasks:",
        "include_role:", "import_role:",
    ]:
        assert forbidden not in executable_text, (executable, forbidden)
assert not Path(".github/workflows").exists()
for recovery_doc in [
    Path("runbooks/replacement-host-recovery.md"),
    Path("runbooks/recovery-artifact-register.md"),
]:
    assert recovery_doc.is_file(), recovery_doc

sensitive_assignment_pattern = (
    r"\b(?!network_policy_probe_[a-z0-9_]*_pass\s*[=:])"
    r"(?:(?:[a-z0-9]+[-_])*(?:token|password|passwd|(?-i:pass)|secret|"
    r"client[-_]secret|api[-_]key|credentials?|access[-_]key)"
    r"(?:[-_][a-z0-9]+)*)\s*[=:]\s*['\"]?[^<{$\s'\"\]]+"
)
assert re.search(
    sensitive_assignment_pattern,
    "bootstrap_" + "to" + "ken" + "=" + "committed-value",
    re.IGNORECASE,
)
assert not re.search(
    sensitive_assignment_pattern,
    "bootstrap_" + "to" + "ken" + "=" + "$runtime_value",
    re.IGNORECASE,
)

for pattern in [
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\bghp_[A-Za-z0-9]+",
    r"\bgithub_pat_[A-Za-z0-9_]+",
    r"(?im)^\s*(?:certificate-authority-data|client-certificate-data|client-key-data|token):\s*\S+",
    sensitive_assignment_pattern,
    r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
    r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
    r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
]:
    assert not re.search(pattern, combined, re.IGNORECASE), pattern

for path in text_paths:
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        assert line == line.rstrip(), (path, line_number)

print("PASS: Ansible/OpenTofu/Namespace layout, Argo/cloudflared/Infisical candidate provenance, Keycloak identity design, links, 30 requirement IDs, 12 future cases, 1 passing and 12 pending manual cases, status/implementation boundary, and bounded source scan")
PY

git check-ignore -q --no-index inventory.local.ansible.json
git check-ignore -q --no-index ansible/network-policy-probe.local.json
git check-ignore -q --no-index .venv/bin/ansible
git check-ignore -q --no-index ansible/.ansible/collections/ansible_collections
git check-ignore -q --no-index ansible/site.retry
git check-ignore -q --no-index ansible/fact_cache/host
if git check-ignore -q --no-index ansible/requirements.yml; then
  exit 1
fi

git diff --check
git diff --cached --quiet
printf '%s\n' 'PASS: ignore policy, git diff check, and no-staged-files check'
```

Actual result (exit 0 on 2026-08-07):

```text
Ran 67 tests
OK
PASS: Ansible/OpenTofu/Namespace layout, Argo/cloudflared/Infisical candidate provenance, links, 30 requirement IDs, 12 future cases, 1 passing and 12 pending manual cases, status/implementation boundary, and bounded source scan
PASS: ignore policy, git diff check, and no-staged-files check
```

The Ansible-specific validation used the locked project environment and did not
execute the play against the inventory host:

```bash
set -euo pipefail
uv sync --locked
cd ansible
uv run ansible-galaxy collection install \
  -r requirements.yml \
  -p .ansible/collections
uv run ansible-playbook playbooks/discover.yml --syntax-check
uv run ansible-playbook playbooks/bootstrap_dependencies.yml --syntax-check
uv run ansible-playbook playbooks/configure_k3s_admin_access.yml --syntax-check
uv run ansible-playbook playbooks/configure_k3s_kubectl_client.yml --syntax-check
uv run ansible-playbook playbooks/verify_k3s_reboot_recovery.yml --syntax-check
uv run ansible-playbook playbooks/probe_k3s_network_policy.yml --syntax-check
uv run ansible-playbook ../tests/validate_storage_report.yml
uv run ansible-lint . ../tests/validate_storage_report.yml
```

Actual result (exit 0 on 2026-08-05):

```text
kubernetes.core:6.1.0 was installed successfully to ansible/.ansible/collections
playbook: playbooks/discover.yml
playbook: playbooks/bootstrap_dependencies.yml
playbook: playbooks/configure_k3s_admin_access.yml
playbook: playbooks/configure_k3s_kubectl_client.yml
playbook: playbooks/verify_k3s_reboot_recovery.yml
playbook: playbooks/probe_k3s_network_policy.yml
synthetic storage render: ok=3 changed=0 failed=0
Passed: 0 failure(s), 0 warning(s) in 30 files processed of 33 encountered; production profile
```

The separately approved non-elevated runtime used an ignored operator-owned local
inventory file. The private address and SSH details are intentionally not recorded
in Git:

```bash
cd ansible
uv run ansible \
  -i .ansible/inventory.local.yml \
  k3s_servers \
  --limit crtxweb \
  -m ansible.builtin.ping
uv run ansible-playbook \
  -i .ansible/inventory.local.yml \
  playbooks/discover.yml \
  --check \
  --diff \
  --limit crtxweb
```

Actual result (2026-08-05):

```text
ping: SUCCESS, changed=false
play recap: ok=14 changed=1 unreachable=0 failed=0 skipped=1
changed=1 is only the ignored controller-local report write
report: valid JSON, mode 0600, check=true, diff=true, elevated=false
host indicators: Debian 13, k3s running, tailscaled running
Kubernetes queries: 0
```

The report was reviewed locally and remains ignored. The operator then separately
approved and ran the elevated branch with the two approval flags and
`--ask-become-pass`; the password was entered only in the operator terminal and is
not recorded. The resulting ignored report showed:

```text
generated_at_utc: 2026-08-05T16:19:28Z
check=true, diff=true, elevated=true
k3s datastore: exists=true, is_directory=true
9 exact Kubernetes queries: available=false, count=0
report: valid JSON, mode 0600
```

A subsequent bounded non-elevated `ansible.builtin.command` import probe used static
argv to inspect only module availability and returned:

```text
rc=0
kubernetes=false, yaml=false, jsonpatch=false
Ansible reported changed=true by command-module default; the probe performed no write
```

The first dependency check/diff proposed 35 new packages, 0 upgrades, and 0
removals, but omitted non-transitive `python3-jsonpatch`; no installation was
accepted. A read-only apt-cache check found Debian candidate `1.32-5`. After explicit
approval, the revised plan proposed 37 new packages with 0 upgraded/removed. The
operator ran the approved installation: `ok=2 changed=1 failed=0 unreachable=0`.
Read-only verification then found `python3-jsonpatch 1.32-5` and
`python3-kubernetes 30.1.0-2` installed, with `kubernetes`, `yaml`, and `jsonpatch`
imports all true.

The final elevated discovery report was generated at `2026-08-05T16:56:17Z`, is
valid JSON mode `0600`, and records datastore presence plus nine available exact
queries: 1 Node, 4 Namespaces, 0 NetworkPolicies, 1 StorageClass, 1 IngressClass, 4
kube-system Deployments, 1 kube-system DaemonSet, 2 HelmCharts, and 0
HelmChartConfigs. The local-path StorageClass, Traefik ingress/chart indicators, and
CoreDNS deployment are present. Object listing alone does not prove CNI behavior or
NetworkPolicy enforcement; the later KIF-NET-02 functional run closes those gates
for the current cluster.

The approved admin-access check predicted the rollback baseline, dedicated group,
membership, two persistent settings, and conditional restart without mutation:
`ok=16 changed=6 unreachable=0 failed=0 skipped=13`. The accepted mutation returned
`ok=24 changed=6 unreachable=0 failed=0 skipped=5`; the kubeconfig became
`root:k3s-admin` mode `0640`. A fresh login included `k3s-admin`, `kubectl get nodes`
reported the single Ready control-plane node, and `kubectl get all -A` successfully
listed the seven kube-system pods plus Services, DaemonSet, Deployments, ReplicaSets,
and completed Traefik jobs. The k3s multicall client emitted three permission
warnings for its separate root-only server config while returning successful data.
The idempotent Ansible rerun verified effective readability as the selected user and
returned `ok=28 changed=0 unreachable=0 failed=0 skipped=2`. Finally, the read-only
probe below returned the Ready node with no server-config warning, establishing the
client-default mechanism before implementation:

```bash
K3S_CONFIG_FILE=/dev/null \
KUBECONFIG=/etc/rancher/k3s/k3s.yaml \
kubectl get nodes
```

No password, kubeconfig content, private address, or server-config content was
recorded. The client-defaults check then returned `ok=14 changed=1 unreachable=0
failed=0 skipped=1` and predicted exactly the selected login-profile and `.bashrc`
blocks. The operator confirmed the accepted execution, a fresh session with
`K3S_CONFIG_FILE=/dev/null` and the approved `KUBECONFIG`, warning-free node and
all-namespace queries, and a second-run result of `changed=0 failed=0`.

The reboot validation used the approved local inventory and interactive become
prompt; no password was recorded:

```bash
cd ansible
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/verify_k3s_reboot_recovery.yml \
  --check --diff --limit crtxweb \
  -e k3s_reboot_recovery_approved=true \
  -e k3s_recovery_access_confirmed=true \
  -e k3s_admin_user=paul \
  --ask-become-pass
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/verify_k3s_reboot_recovery.yml \
  --diff --limit crtxweb \
  -e k3s_reboot_recovery_approved=true \
  -e k3s_recovery_access_confirmed=true \
  -e k3s_admin_user=paul \
  --ask-become-pass
```

The operator manually confirmed independent physical or LAN fallback access before
reboot testing. The approved reboot check predicted exactly one reboot and returned `ok=19 changed=1
unreachable=0 failed=0 skipped=7`. The accepted run returned through the Tailscale
inventory path with a changed boot ID, running k3s and tailscaled services, one Ready
node, and preserved root:k3s-admin mode-0640 effective access at `ok=26 changed=1
unreachable=0 failed=0 skipped=0`. The operator manually confirmed in a fresh
session that both services were active and `kubectl get nodes` plus
`kubectl get all -A` were warning-free.
Replacement-host recovery remains pending and is not implied by this reboot proof.

## Hosted identity/controller offline source-baseline closure — 2026-08-08

This controller-local validation used no inventory, SSH, host, become, kubeconfig,
Kubernetes API, Helm install/upgrade, provider, secret store, route, deployment,
network retrieval, or runtime operation. It validated only committed and proposed
repository source.

```bash
python3 -m unittest -v \
  tests.test_hosted_auth_source_selection_contract \
  tests.test_argocd_provenance_contract \
  tests.test_argocd_hardened_design_contract \
  tests.test_infisical_operator_provenance_contract \
  tests.test_keycloak_oidc_bootstrap_design_contract \
  tests.test_ansible_contract.AnsibleLayoutTests.test_minimal_ansible_layout_exists \
  tests.test_platform_namespace_contract.PlatformNamespaceBootstrapContractTests.test_namespace_bootstrap_is_a_pre_stage_4_bounded_exception \
  tests.test_replacement_recovery_contract.ReplacementRecoveryContractTests.test_secret_free_recovery_documents_exist_without_executable_automation
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
(cd ansible/files/vendor/argocd/10.3.0 && sha256sum -c SHA256SUMS)
(cd ansible/files/vendor/infisical-operator/0.11.7 && sha256sum -c SHA256SUMS)
# Run repository-local Markdown link/trailing-whitespace, selected source hygiene,
# exact four-Namespace, and no component operational-source closure checks.
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 45 focused source-selection/provenance/design/layout contracts — OK
Ran 109 full offline tests — OK
PASS: Python compile
PASS: syntax for all 9 production playbooks
Passed: 0 failure(s), 0 warning(s) in 43 files processed of 56 encountered; production profile
PASS: all six chart/provenance/public-key entries against their SHA256SUMS
PASS: repository Markdown links and trailing-whitespace hygiene
PASS: selected docs/policy/vendor secret, private-address, and local-metadata scan
PASS: exact four-Namespace and no component operational-source closure
PASS: git diff check and no staged files
```

The first broad link-check attempt incorrectly traversed the ignored `.venv` and
reported an unrelated broken link inside installed `ansible-lint` package metadata.
The corrected repository-source scan explicitly excluded `.venv`, `.ansible`,
`.git`, and `.pi-subagents` and passed. No source change was made for that tool-local
false positive.

Exact vendored-input SHA-256 closure:

```text
d08882d22d0c76e3174e005cc09abe300c70ba556aec76725a4410d172b9c1f3  argo-cd-10.3.0.tgz
52157f1e9cf2a68cc26e6e456bff03afdfe11a8f1637078a72262e980fb5cd02  argo-cd-10.3.0.tgz.prov
36366596211a1587d018be5b178687799cb2edfc3e3e3c6ccd661b33fc6305ca  pgp_keys.asc
7f8846c4f6b1cdca2cea23cf00a29d12a38f42eb8da8e125dc196a1e5683aea8  secrets-operator-0.11.7.tgz
a39ae4be9ca25f7dc0b50b6633c92fc320d427fd67364b50e82c0d512db7b933  secrets-operator-0.11.7.tgz.prov
7693c83a40ef1536cfdefe0e27806bf8027d272d847bafcea44807d08400b8c9  cloudsmith-signing-key.asc
```

Selection closes only deterministic offline version/policy/public-input authoring.
Signer authorization/revocation and image trust/SBOM/vulnerability/recovery remain
blocked. Infisical chart cryptographic verification remains NOT RUN. Exact rendered
controller objects, scoped RBAC, secret-zero recovery, callbacks/origins, k3s
admission, check/apply/idempotence, and all runtime evidence remain NOT RUN/BLOCKED.
At this 2026-08-08 checkpoint, the exact four Namespace manifests were unchanged,
and `platform-secrets` plus `platform-identity` runtime remained NOT RUN. KIF-NS-04
later superseded those two never-run source leaves with `shared-services`; it did not
rewrite or imply runtime evidence for this historical validation.

### Independent source-policy review fixes — 2026-08-08

The independent review found two bounded source-policy inconsistencies: stale Argo
wording treated the already-selected offline version baseline as still awaiting
selection, and the Keycloak/PostgreSQL image identities omitted their OCI
repositories. The follow-up now records immutable repository-qualified pull
references, distinguishes offline version selection from deployable-use trust
acceptance, and adds negative regression assertions.

```bash
# From the repository root.
python3 -m unittest -v \
  tests.test_hosted_auth_source_selection_contract \
  tests.test_argocd_provenance_contract \
  tests.test_keycloak_oidc_bootstrap_design_contract
python3 -m unittest discover -s tests -v
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 26 focused source-policy/design contracts — OK
Ran 109 full offline tests — OK
PASS: repository-qualified Keycloak/PostgreSQL pull-reference consistency
PASS: stale Argo select-or-reject wording absent
PASS: git diff check and no staged files
```

The value-free policy SHA-256 after repository qualification is
`076a1cb78f5aae7b23c6b4b51c6c3095a5728f8ddb895f202cc0cfcef5ec837d`.
An initial controller invocation omitted the repository `cd` and therefore failed
only with local import/file-not-found errors; the corrected commands above passed. A
broad literal metadata scan then matched negative test assertions and the documented
`.pi-subagents` exclusion itself; the corrected content-aware scan of the selected
runbooks and policy passed. No network, server, Kubernetes, registry, secret,
provider, or runtime operation was performed.

## Infisical privileged-prerequisites design inventory — 2026-08-09

The [design record](../../runbooks/infisical-operator-privileged-prerequisites-design.md)
and inert policy bind seven raw CRD templates plus observed manager/metrics/user-RBAC
seams to the hash-verified vendored `v0.11.7` chart. The contract correlates the
cluster-scoped `ClusterGenerator` and TokenReview rules with their ineffective
namespaced manager Role placement, records the singular metrics Role and plural
metrics ClusterRole failure modes, and freezes the four aggregate-role labels. They
do not add a valid CRD,
RBAC object, values file, rendered object, Ansible entrypoint, controller, Secret, or
runtime approval. No network, inventory, SSH, host, kubeconfig, Kubernetes API,
registry, Infisical account, provider, secret store, Helm operation, or mutation was
used.

```bash
python3 -m unittest -v \
  tests.test_infisical_operator_privileged_prerequisites_contract \
  tests.test_infisical_operator_provenance_contract \
  tests.test_hosted_auth_source_selection_contract
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
(
  cd ansible/files/vendor/infisical-operator/0.11.7
  shasum -a 256 -c SHA256SUMS
)
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Ran 19 focused Infisical/source-selection contracts — OK
Ran 115 full offline tests — OK
PASS: Python compile
PASS: all 9 production playbook syntax checks
PASS: production-profile Ansible lint
PASS: exact vendored Infisical SHA-256 closure
PASS: exact seven-template CRD inventory, cluster-scope correlation, metrics failure-mode, and aggregate-label sentinels
PASS: exact four-Namespace Kubernetes source and absence of Infisical operational source
PASS: local links, evidence/value hygiene, git diff check, and no staged files
```

The first test-driven focused invocation occurred before documentation links were
added: five new cases passed and only the intentionally missing-link case failed.
The first full run then exposed three exact source-closure expectations that had not
yet admitted the new inert policy/runbook; those tests were updated, and the second
full run passed all 115 cases. Independent review then found that the scoped manager
Role inventory named TokenReview but omitted its equally ineffective cluster-scoped
`ClusterGenerator` permission and did not freeze the singular metrics Role failure
or four aggregate labels. The policy, design, and contract now cover those seams;
19 focused and 115 full tests passed again. The completed closure passed the commands
above. GPG and Helm remain unavailable on
the controller, so chart-signature replay and deterministic rendering are honestly
**NOT RUN**. Signer authorization/revocation, CRD/API compatibility, exact scope and
RBAC, Universal Auth recovery, image trust/SBOM/vulnerability/off-node recovery,
traffic policy, foundation Namespace runtime, and all component/runtime approvals
remain **NOT RUN/BLOCKED**. This design closes no manual QA case.

## Shared-services placement source correction — 2026-08-09

This offline-only correction supersedes the never-run `platform-secrets` and
`platform-identity` intent with one exact `shared-services` Namespace manifest and
retargets the guarded foundation wrapper to that singleton. It does not rename or
delete a live Namespace. `platform-edge` is reserved for cloudflared; the Infisical
Cloud Operator, separate Keycloak deployment, and one general PostgreSQL instance
belong in `shared-services`. Keycloak receives a dedicated logical database, owner
role, credential, and backup scope on that shared engine, not another PostgreSQL
workload or PVC.

```bash
.venv/bin/python -m unittest -v \
  tests.test_foundation_namespace_contract \
  tests.test_platform_namespace_contract \
  tests.test_hosted_auth_source_selection_contract \
  tests.test_keycloak_oidc_bootstrap_design_contract \
  tests.test_infisical_operator_provenance_contract \
  tests.test_infisical_operator_privileged_prerequisites_contract \
  tests.test_argocd_hardened_design_contract \
  tests.test_argocd_provenance_contract \
  tests.test_cloudflared_provenance_contract
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q tests
sh -n ansible/bin/bootstrap-foundation-namespaces
bash -n tests/reject_foundation_namespace_task_start.sh
sh -n tests/validate_foundation_namespace_clean_controller.sh
tests/reject_foundation_namespace_task_start.sh
tests/validate_foundation_namespace_clean_controller.sh
cd ansible
uv run ansible-playbook ../tests/reject_foundation_namespace_internal_injection.yml \
  -e foundation_namespace_bootstrap_internal_prestate=forged
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
(cd ansible/files/vendor/argocd/10.3.0 && shasum -a 256 -c SHA256SUMS)
(cd ansible/files/vendor/infisical-operator/0.11.7 && shasum -a 256 -c SHA256SUMS)
.venv/bin/python - <<'PY'
from pathlib import Path
import re

excluded = {'.git', '.venv', '.pi-subagents', 'vendor', '.ansible'}
paths = [path for path in Path('.').rglob('*.md') if excluded.isdisjoint(path.parts)]
for path in paths:
    for target in re.findall(r'\[[^]]+\]\(([^)]+)\)', path.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        local = target.split('#', 1)[0]
        if local:
            assert (path.parent / local).resolve().exists(), (path, target)
print(f'PASS: local Markdown links in {len(paths)} files')
PY
python3 - <<'PY'
from pathlib import Path

expected = {
    'platform/namespaces/argocd.yaml',
    'platform/namespaces/platform-edge.yaml',
    'platform/namespaces/shared-services.yaml',
}
actual = {
    str(path.relative_to('kubernetes'))
    for path in Path('kubernetes').rglob('*')
    if path.is_file()
}
assert actual == expected
foundation = '\n'.join(
    path.read_text()
    for path in Path('ansible/roles/foundation_namespace_bootstrap').rglob('*')
    if path.is_file()
)
assert 'shared-services' in foundation
assert 'platform-secrets' not in foundation
assert 'platform-identity' not in foundation
print('PASS: exact three-Namespace source and singleton foundation target')
PY
git diff --exit-code -- \
  kubernetes/platform/namespaces/argocd.yaml \
  kubernetes/platform/namespaces/platform-edge.yaml \
  ansible/bin/bootstrap-platform-namespaces \
  ansible/playbooks/bootstrap_platform_namespaces.yml \
  ansible/roles/platform_namespace_bootstrap
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Observed incremental red checkpoint: 78 focused tests ran with 16 source/placement failures
Ran 78 focused placement/closure contracts — OK
Ran 115 full offline tests — OK
PASS: Python compile and wrapper/fixture shell syntax
PASS: forged internal-variable and direct task-start fixtures fail closed
PASS: wrapper-equivalent clean-controller validation
PASS: all 9 production playbook syntax checks
PASS: production-profile Ansible lint, 0 failures/warnings in 44 files processed of 57 encountered
PASS: Argo and Infisical vendored SHA-256 closures
PASS: exact three-Namespace closure and singleton shared-services foundation target
PASS: closed historical argocd/platform-edge bootstrap source remains untouched
PASS: 24 scoped local Markdown documents, secret hygiene, diff, and no staged files
```

The incremental 16-failure red checkpoint was captured while tests were being changed
in bounded steps; it is not claimed as a clean final-tests-over-`HEAD` reconstruction
and no raw log is committed. Independent review reconstructed that different state
and observed 18 failures, so both counts are retained with their scopes rather than
presented as identical evidence.

The first all-recursive Markdown-link check incorrectly entered the ignored `.venv`
and failed on an installed ansible-lint documentation link. Restricting the check to
repository-owned Markdown passed all 24 files; no repository link was broken. No
inventory, SSH, become, kubeconfig, Kubernetes API, Namespace check/apply, database,
Secret, provider, registry, Helm, Infisical, Cloudflare, route, or runtime operation
occurred. `shared-services` existence remains unproved and its check, first apply,
and idempotence require separate approvals. If later read-only discovery finds either
superseded Namespace, stop; do not delete it. This source correction closes no manual
QA case.

## Shared database source-only architecture — 2026-08-09

This offline-only increment adds a value-free canonical contract for exactly one
PostgreSQL and one MongoDB engine in `shared-services`. PostgreSQL has isolated DEV,
PROD, and Keycloak consumer scopes; MongoDB has isolated DEV and PROD scopes only.
All credentials remain Infisical-owned, database exposure remains private-only, and
engine-specific negative authorization tests are mandatory. MongoDB source and
topology, stateful objects, storage, provisioning, backup/restore, RPO/RTO, handoff,
and runtime remain unselected or blocked.

```bash
.venv/bin/python -m unittest -v \
  tests.test_shared_database_architecture_contract \
  tests.test_hosted_auth_source_selection_contract \
  tests.test_keycloak_oidc_bootstrap_design_contract \
  tests.test_cloudflared_provenance_contract \
  tests.test_foundation_namespace_contract \
  tests.test_platform_namespace_contract
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q tests
python3 - <<'PY'
from pathlib import Path
import yaml
for path in (
    Path('ansible/files/policies/hosted-identity-authorization.yml'),
    Path('ansible/files/policies/shared-database-architecture.yml'),
):
    assert isinstance(yaml.safe_load(path.read_text()), dict), path
PY
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
(cd ansible/files/vendor/argocd/10.3.0 && shasum -a 256 -c SHA256SUMS)
(cd ansible/files/vendor/infisical-operator/0.11.7 && shasum -a 256 -c SHA256SUMS)
.venv/bin/python - <<'PY'
from pathlib import Path
import re
excluded = {'.git', '.venv', '.pi-subagents', 'vendor', '.ansible'}
paths = [path for path in Path('.').rglob('*.md') if excluded.isdisjoint(path.parts)]
for path in paths:
    text = path.read_text()
    assert not any(line.endswith((' ', '\t')) for line in text.splitlines()), path
    for target in re.findall(r'\[[^]]+\]\(([^)]+)\)', text):
        if '://' in target or target.startswith('#'):
            continue
        local = target.split('#', 1)[0]
        if local:
            assert (path.parent / local).resolve().exists(), (path, target)
print(f'PASS: local Markdown links and trailing whitespace in {len(paths)} files')
PY
python3 - <<'PY'
from pathlib import Path
expected = {
    'platform/namespaces/argocd.yaml',
    'platform/namespaces/platform-edge.yaml',
    'platform/namespaces/shared-services.yaml',
}
actual = {
    str(path.relative_to('kubernetes'))
    for path in Path('kubernetes').rglob('*')
    if path.is_file()
}
assert actual == expected
operational = [
    path
    for root in ('ansible/bin', 'ansible/playbooks', 'ansible/roles')
    for path in Path(root).rglob('*')
    if path.is_file()
]
assert not any(
    token in path.name.lower()
    for path in operational
    for token in ('postgres', 'mongo', 'database')
)
PY
git diff --exit-code -- \
  kubernetes/platform/namespaces/argocd.yaml \
  kubernetes/platform/namespaces/platform-edge.yaml \
  ansible/bin/bootstrap-platform-namespaces \
  ansible/playbooks/bootstrap_platform_namespaces.yml \
  ansible/roles/platform_namespace_bootstrap
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Test-first red checkpoint: 47 tests ran; 1 expected error because the canonical policy was absent
Ran 56 focused shared-database/identity/placement contracts — OK
Ran 124 full offline tests — OK
PASS: Python compile and both value-free policy files parse as YAML
PASS: all 9 production playbook syntax checks
PASS: production-profile Ansible lint, 0 failures/warnings in 45 files processed of 58 encountered
PASS: Argo and Infisical vendored SHA-256 closures
PASS: local Markdown links and trailing whitespace in 25 repository files
PASS: exact three-Namespace closure and no executable database source
PASS: closed historical argocd/platform-edge bootstrap source remains untouched
PASS: diff hygiene and no staged files
```

No MongoDB repository, version, digest, topology, database/user name, Service/port,
storage value, credential reference/value, provisioning writer, or backup tool was
invented. No StatefulSet, Deployment, Service, PVC, Secret, Job, CronJob,
NetworkPolicy, Ansible component wrapper/role/playbook, Helm source, Argo object,
provider resource, or route was added. No host, SSH, registry, Kubernetes API,
Infisical, Secret, provider, Helm, database, or runtime operation occurred. This
source-only policy closes no manual QA case.

## GitHub source CI and Reactive Resume private-MVP policy — 2026-08-09

This increment adds one infrastructure source-CI workflow and a value-free Reactive
Resume hosted policy. The workflow validates repository source only: it has no
Secret, package-write, registry, provider, host, cluster, or deploy path. Reactive
Resume DEV is now included in private MVP intent with a separate future PROD
instance, exact OIDC clients, and dedicated PostgreSQL scopes. Its upstream image,
callbacks, objects, Secrets, recovery, and runtime remain unselected or blocked.

```bash
git ls-remote https://github.com/actions/checkout.git \
  refs/tags/v4.2.2
git ls-remote https://github.com/actions/setup-python.git \
  refs/tags/v5.6.0
git ls-remote https://github.com/actions/setup-node.git \
  refs/tags/v4.4.0
.venv/bin/python -m unittest -v \
  tests.test_github_actions_contract \
  tests.test_reactive_resume_architecture_contract \
  tests.test_shared_database_architecture_contract \
  tests.test_hosted_auth_source_selection_contract \
  tests.test_keycloak_oidc_bootstrap_design_contract \
  tests.test_argocd_hardened_design_contract
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q tests
python3 - <<'PY'
from pathlib import Path
import yaml
workflow_paths = list(Path('.github/workflows').glob('*.yml'))
assert [path.name for path in workflow_paths] == ['ci.yml']
workflow = yaml.safe_load(workflow_paths[0].read_text())
assert set(workflow['on']) == {'push', 'pull_request'}
for path in (
    Path('ansible/files/policies/reactive-resume-architecture.yml'),
    Path('ansible/files/policies/shared-database-architecture.yml'),
):
    assert isinstance(yaml.safe_load(path.read_text()), dict)
PY
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
(cd ansible/files/vendor/argocd/10.3.0 && shasum -a 256 -c SHA256SUMS)
(cd ansible/files/vendor/infisical-operator/0.11.7 && shasum -a 256 -c SHA256SUMS)
.venv/bin/python - <<'PY'
from pathlib import Path
import re
excluded = {'.git', '.venv', '.pi-subagents', 'vendor', '.ansible'}
paths = [path for path in Path('.').rglob('*.md') if excluded.isdisjoint(path.parts)]
for path in paths:
    text = path.read_text()
    assert not any(line.endswith((' ', '\t')) for line in text.splitlines()), path
    for target in re.findall(r'\[[^]]+\]\(([^)]+)\)', text):
        if '://' in target or target.startswith('#'):
            continue
        local = target.split('#', 1)[0]
        if local:
            assert (path.parent / local).resolve().exists(), (path, target)
print(f'PASS: {len(paths)} Markdown files')
PY
git diff --exit-code -- \
  kubernetes/platform/namespaces/argocd.yaml \
  kubernetes/platform/namespaces/platform-edge.yaml \
  ansible/bin/bootstrap-platform-namespaces \
  ansible/playbooks/bootstrap_platform_namespaces.yml \
  ansible/roles/platform_namespace_bootstrap
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Test-first red checkpoint: missing workflow/policy produced 2 expected setup errors
Ran 48 focused workflow/Reactive Resume/database/identity/Argo contracts — OK
Ran 135 full offline tests — OK
PASS: Python compile, exact one-workflow closure, and policy/workflow YAML
PASS: all 9 production playbook syntax checks
PASS: production-profile Ansible lint
PASS: Argo and Infisical vendored SHA-256 closures
PASS: repository-scoped Markdown links/trailing whitespace
PASS: exact three-Namespace and no-executable-component closure
PASS: closed historical argocd/platform-edge bootstrap source remains untouched
PASS: diff hygiene and no staged files
PASS: bounded independent final security/workflow review — APPROVED
```

Public action-tag resolution returned checkout `v4.2.2` commit
`11bd71901bbe5b1630ceea73d27597364c9af683`, setup-python `v5.6.0` commit
`a26af69be951a213d495a4c3e4e4022e16d87065`, and setup-node `v4.4.0` commit
`49933ea5288caeca8642d1e84afbd3f7d6820020`. Only checkout/setup-python are
used here; setup-node is used by the separately validated application source CI.
At this source-authoring checkpoint the bounded unauthenticated public Git lookup
was the only network operation. No workflow had yet been pushed or run, and no
GitHub setting, registry login, Docker build, image publication, digest,
SBOM/provenance, Secret, provider, host, Kubernetes API, Infisical, database, route,
or runtime operation occurred.

## First hosted infrastructure source-CI evidence — 2026-08-09

```bash
git rev-parse HEAD
git push origin develop
curl --fail --silent --show-error \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  'https://api.github.com/repos/devraider/cristexweb/actions/runs/31311995461'
curl --fail --silent --show-error \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  'https://api.github.com/repos/devraider/cristexweb/actions/runs/31311995461/jobs?per_page=20'
.venv/bin/python -m unittest -v \
  tests.test_github_actions_contract \
  tests.test_reactive_resume_architecture_contract \
  tests.test_shared_database_architecture_contract \
  tests.test_hosted_auth_source_selection_contract \
  tests.test_keycloak_oidc_bootstrap_design_contract \
  tests.test_argocd_hardened_design_contract
.venv/bin/python -m unittest discover -s tests
git diff --check
git diff --cached --quiet
git status --short --branch
git rev-parse HEAD
git rev-parse origin/develop
```

Actual result:

```text
Initial local SHA precondition: STOPPED before git push because the unverified full
  SHA literal did not equal HEAD; no remote operation occurred
Verified HEAD: e200efd8f294a04df8d3c5ea84fd90b8a24e01d1
Push: eed3f84..e200efd develop -> develop
Run 31311995461: completed / success / push / exact verified HEAD
Job 93241094377: validate / completed / success
Evidence-doc validation: 48 focused and 135 full tests — OK
Manual-QA ledger: initial exact-PENDING-only count check failed; corrected living
  regex includes annotated PENDING rows and proves 1 PASS / 1 PARTIAL / 13 PENDING
Diff hygiene and no staged files: PASS
Repository before evidence edits: develop synchronized with origin/develop; clean tree
```

Run URL: <https://github.com/devraider/cristexweb/actions/runs/31311995461>.
The approved push and read-only public API observation proved only infrastructure
source CI. The private `cristexhub` push also succeeded, but its unauthenticated
repository/API and badge endpoints returned HTTP 404; its runner result is therefore
**UNOBSERVED**, not PASS or FAIL. Local `gh` was unavailable (`gh: command not
found`), and no token or browser credential was introduced. No GitHub setting,
registry login, Docker build, image publication, digest, SBOM/provenance, Secret,
provider, host, Kubernetes API, Infisical, database, route, or deployment operation
occurred. MQA-14 is PARTIAL; publication and application-run review remain open.

## Shared database all-environment consumer correction — 2026-08-09

The approved closure keeps one shared PostgreSQL engine and one shared MongoDB
engine in `shared-services`. CristexHub DEV/PROD receive isolated logical scopes on
both engines; Reactive Resume DEV/PROD and Keycloak receive dedicated PostgreSQL
scopes. Sharing an engine does not share databases, principals, credential values,
migration scopes, or backup scopes.

```bash
.venv/bin/python -m unittest -v \
  tests.test_shared_database_architecture_contract \
  tests.test_reactive_resume_architecture_contract \
  tests.test_hosted_auth_source_selection_contract \
  tests.test_keycloak_oidc_bootstrap_design_contract \
  tests.test_foundation_namespace_contract \
  tests.test_argocd_hardened_design_contract
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m compileall -q tests
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
policy = yaml.safe_load(
    Path('ansible/files/policies/shared-database-architecture.yml').read_text()
)
assert set(policy['engines']['postgresql']['consumers']) == {
    'cristexhub-dev',
    'cristexhub-prod',
    'reactive-resume-dev',
    'reactive-resume-prod',
    'keycloak',
}
assert set(policy['engines']['mongodb']['consumers']) == {
    'cristexhub-dev',
    'cristexhub-prod',
}
assert policy['namespace'] == 'shared-services'
assert policy['executable_source_allowed'] is False
assert all(value is False for value in policy['promotion_gates'].values())
PY
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
git diff --exit-code -- \
  kubernetes/platform/namespaces/argocd.yaml \
  kubernetes/platform/namespaces/platform-edge.yaml \
  kubernetes/platform/namespaces/shared-services.yaml \
  ansible/bin/bootstrap-platform-namespaces \
  ansible/playbooks/bootstrap_platform_namespaces.yml \
  ansible/roles/platform_namespace_bootstrap
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Test-first red checkpoint: exact PostgreSQL closure failed with missing
  cristexhub-dev and cristexhub-prod — expected
First integrated rerun: shared policy passed; Reactive Resume cross-contract and
  full suite each exposed one stale exact-three-consumer assertion — corrected
Final focused contracts: 53 passed
Final full offline suite: 135 passed
PASS: exact five PostgreSQL / two MongoDB consumer closure
PASS: every consumer has dedicated value-free database/principal/migration/backup
PASS: Python compile; all 9 Ansible syntax checks; production-profile lint
PASS: 26 repository Markdown files; exact Namespace/historical source preserved
PASS: diff hygiene and no staged files
```

No database role, playbook, wrapper, manifest, StatefulSet, Service, PVC, Secret,
provisioning job, image selection, host access, Kubernetes API, Infisical, registry,
or runtime operation was added or run. The `shared-services` Namespace remains
source-defined but its check/apply/idempotence evidence remains **NOT RUN**.

## Shared RabbitMQ and private backup-access policies — 2026-08-09

This source-only increment confirms one shared RabbitMQ engine in `shared-services`
with exact isolated CristexHub DEV/PROD scopes and reviewed explicit admission for
future consumers. It also defines easy backup access as private authenticated
metadata/list/retrieve/verify operations over encrypted timestamped separate-purpose
archives. At that historical checkpoint, non-destructive Google
Drive/containerized-`rclone copy` remained intended-not-approved; current
KIF-RCLONE-01/02 source supersedes the transfer-tool direction with pinned host
rclone while leaving all database backup runtime gates blocked.

```bash
.venv/bin/python -m unittest -v \
  tests.test_shared_rabbitmq_architecture_contract \
  tests.test_shared_stateful_backup_architecture_contract \
  tests.test_shared_database_architecture_contract \
  tests.test_hosted_auth_source_selection_contract \
  tests.test_reactive_resume_architecture_contract \
  tests.test_replacement_recovery_contract \
  tests.test_foundation_namespace_contract
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m compileall -q tests
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in (
    Path('ansible/files/policies/shared-database-architecture.yml'),
    Path('ansible/files/policies/shared-rabbitmq-architecture.yml'),
    Path('ansible/files/policies/shared-stateful-backup-architecture.yml'),
):
    policy = yaml.safe_load(path.read_text())
    assert policy['policy_status'] == 'source-policy-only-runtime-blocked'
    assert policy['executable_source_allowed'] is False
    assert all(value is False for value in policy['promotion_gates'].values())
PY
.venv/bin/python - <<'PY'
from pathlib import Path
import re
excluded = {
    '.git',
    '.venv',
    '.pi-subagents',
    '.pytest_cache',
    'vendor',
    '.ansible',
}
paths = [path for path in Path('.').rglob('*.md') if excluded.isdisjoint(path.parts)]
for path in paths:
    text = path.read_text()
    assert not any(line.endswith((' ', '\t')) for line in text.splitlines()), path
    for target in re.findall(r'\[[^]]+\]\(([^)]+)\)', text):
        if '://' in target or target.startswith('#'):
            continue
        local = target.split('#', 1)[0]
        if local:
            assert (path.parent / local).resolve().exists(), (path, target)
print(f'PASS: {len(paths)} Markdown files')
PY
cd ansible
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
uv run ansible-lint . ../tests/validate_storage_report.yml
cd ..
git diff --exit-code -- \
  kubernetes/platform/namespaces/argocd.yaml \
  kubernetes/platform/namespaces/platform-edge.yaml \
  kubernetes/platform/namespaces/shared-services.yaml \
  ansible/bin/bootstrap-platform-namespaces \
  ansible/playbooks/bootstrap_platform_namespaces.yml \
  ansible/roles/platform_namespace_bootstrap
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Test-first red checkpoint: 3 expected errors — missing RabbitMQ policy, missing
  backup policy, and missing database future-consumer admission
First policy/runbook checkpoint: 25 passed / 1 exact phrase mismatch — corrected
Integrated closure checkpoint: 149 passed / 3 expected exact-layout failures for
  the two new policies and two new runbooks — expected sets updated
Approved-profile red checkpoint: 2 expected failures and 1 expected missing-key error
  for storage/resources/Services and backup cadence/retention/RPO/RTO — corrected
Independent review found duplicate null local-staging retention beside the approved
  14-day schedule retention — set to 14d and regression assertion added
Final focused contracts: 55 passed
Final full offline suite: 152 passed
PASS: exact RabbitMQ engine plus DEV/PROD vhost/user/permission/limit/recovery scopes
PASS: future database/RabbitMQ/backup consumers require reviewed exact changes
PASS: private authenticated metadata catalog/retrieval and copy-not-sync contract
PASS: database source profile local-path, 40/80 GiB, bounded resources, private
  5432/27017 ClusterIP Services, mandatory TLS, and Ansible→Argo ownership direction
PASS: backup source profile daily / 14-day retention / RPO 24h / RTO 4h
PASS: RabbitMQ definitions recovery separated from queued-work reconciliation
PASS: policy YAML, Python compile, all promotion gates false
PASS: all 9 Ansible syntax checks and production-profile lint
PASS: 27 repository-owned Markdown files, exact three-Namespace/historical source,
  diff/no-staged
```

No image/digest lookup, registry, host, disk, Google Drive, Infisical, Kubernetes API,
backup, restore, Secret, StatefulSet, Service, PVC, Job, CronJob, route, or runtime
operation occurred. RabbitMQ source/topology/storage/ports/resources/TLS and backup
image/identities/staging path/schedule implementation/retention enforcement/RPO/RTO
restore proof remain unselected or unproved.
`shared-services` first apply/idempotence remain separately approved and **NOT RUN**.

## Shared-services Namespace first check attempt — 2026-08-09

Approved command:

```bash
ansible/bin/bootstrap-foundation-namespaces check
```

Actual result:

```text
Non-interactive attempt: ok=10 changed=0 unreachable=0 failed=1 skipped=0
Failure: Missing sudo password before service preflight/reconciliation
Interactive retry: ok=20 changed=1 unreachable=0 failed=0 skipped=2
```

The first attempt made no mutation. The interactive retry passed all protected
preflight gates. Committed source contains exactly one manifest and the role contains
exactly one change-capable reconciliation item, both naming `shared-services`; the
single check-mode change therefore predicts creation of only that Namespace. The two
post-state tasks were skipped in check mode as designed, and no object was created or
modified. The first apply required and received a new explicit mutation approval; idempotence
still requires another approval after post-state review.

## Shared-services Namespace first apply — 2026-08-09

Approved command:

```bash
ansible/bin/bootstrap-foundation-namespaces apply
```

Actual result:

```text
Create or reconcile only the approved foundation Namespaces:
changed: [crtxweb] => (item=shared-services)
Exact Namespace identity and pending Argo desired ownership — PASS
k3s and Tailscale remained running — PASS
PLAY RECAP: ok=22 changed=1 unreachable=0 failed=0 skipped=0
```

The apply created exactly `shared-services` with the three committed labels, verified
its `Active` phase, and preserved both required host services. There was no deletion,
other kind, Secret, workload, Service, PVC, policy, route, or component deployment.
Idempotence remains **NOT RUN** and requires a new explicit approval.

Evidence validation initially found two stale exact contract expectations after the
truthful runtime update; they were updated rather than weakening assertions.
Independent review then found six additional current-state documents that still said
first apply was NOT RUN; all were corrected and a cross-document regression contract
was added. Final validation passed 36 affected contracts and 153 full offline tests,
plus Python compile, 27 repository-owned Markdown links/hygiene, diff check, and no
staged files.

## Shared-services Namespace idempotence apply — 2026-08-09

The operator separately approved the idempotence checkpoint and ran only:

```bash
ansible/bin/bootstrap-foundation-namespaces apply
```

Actual result:

```text
PLAY RECAP: ok=22 changed=0 unreachable=0 failed=0 skipped=0
```

This is the idempotence proof: the exact present-only reconciliation changed nothing,
post-state verification passed again, and k3s/Tailscale remained running. The
`shared-services` Namespace check/first-apply/idempotence sequence is complete. No
Infisical Operator, Argo CD, Keycloak, PostgreSQL, MongoDB, RabbitMQ, Secret,
workload, Service, PVC, policy, route, or application Namespace was created by this
run. Independent review found that two current summaries still counted completed
foundation Namespace runtime among six open decisions; they were corrected to five
open component decisions plus closed D2 evidence. Rereview returned **APPROVED** and
final validation passed 36 affected/153 full tests, compile, Markdown, and diff
checks.

## CristexHub DEV Namespace deployable-source validation — 2026-08-09

This controller-local increment is source-only. The
[CristexHub DEV Namespace bootstrap](../../runbooks/cristexhub-dev-namespace-bootstrap.md)
adds one exact `cristexhub-dev` Namespace manifest with the four operator-approved
labels and a dedicated guarded Ansible role/playbook/wrapper/action plugin. It does
not reuse completed wrappers and contains no PROD, policy, workload, Secret, PVC, Service, route, or component object.

Test-first checkpoint:

```text
New focused contract: ERROR as expected because
ansible/playbooks/bootstrap_cristexhub_dev_namespace.yml did not exist
```

Validation commands:

```bash
.venv/bin/python -m unittest -v tests.test_cristexhub_dev_namespace_contract
.venv/bin/python -m unittest discover -s tests
bash -n ansible/bin/bootstrap-cristexhub-dev-namespace
bash -n tests/reject_cristexhub_dev_namespace_task_start.sh
sh -n tests/validate_cristexhub_dev_namespace_clean_controller.sh
.venv/bin/python -m py_compile \
  ansible/plugins/action/cristexhub_dev_namespace_guarded_k8s.py
tests/reject_cristexhub_dev_namespace_task_start.sh
tests/validate_cristexhub_dev_namespace_clean_controller.sh
cd ansible
../.venv/bin/ansible-playbook \
  ../tests/reject_cristexhub_dev_namespace_internal_injection.yml \
  -e cristexhub_dev_namespace_bootstrap_internal_prestate=forged
for playbook in playbooks/*.yml; do
  ../.venv/bin/ansible-playbook "$playbook" --syntax-check
done
../.venv/bin/ansible-lint . ../tests/validate_storage_report.yml \
  ../tests/reject_cristexhub_dev_namespace_internal_injection.yml
cd ..
.venv/bin/python -m compileall -q tests
.venv/bin/python - <<'PY'
from pathlib import Path
import re
excluded = {'.git', '.venv', '.pi-subagents', '.pytest_cache', 'vendor', '.ansible'}
paths = [path for path in Path('.').rglob('*.md') if excluded.isdisjoint(path.parts)]
for path in paths:
    text = path.read_text()
    assert not any(line.endswith((' ', '\t')) for line in text.splitlines()), path
    for target in re.findall(r'\[[^]]+\]\(([^)]+)\)', text):
        if '://' in target or target.startswith('#'):
            continue
        local = target.split('#', 1)[0]
        if local:
            assert (path.parent / local).resolve().exists(), (path, target)
print(f'PASS: {len(paths)} Markdown files')
PY
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Focused contract: 6 passed
First integrated run: 159 tests / 2 expected source-closure failures
  (new wrapper and runbook absent from two exact inventories)
Final full offline suite: 159 passed
Combined task-start + forged preflight-binding fixture: PASS; the action plugin read
  controller CLI context directly and failed before the Kubernetes module
Internal-injection fixture: ok=4 changed=0 failed=0 rescued=1
Clean-controller syntax fixture: PASS
Shell syntax and Python compile: PASS
All 10 playbooks: syntax PASS
Action plugin compile: PASS
Production-profile lint: 0 failures, 0 warnings in 54 files processed
Markdown links/hygiene: PASS, 28 repository-owned files
Kubernetes source: PASS, exactly four Namespace manifests
Diff hygiene/no staged files: PASS
```

One exploratory lint command launched from the repository root failed because that
working directory did not load `ansible/ansible.cfg` and therefore could not resolve
the role/collection paths. The documented `cd ansible` invocation passed. At source-validation time, network, operational inventory, SSH, become, kubeconfig,
Kubernetes API, wrapper `check`, wrapper `apply`, and runtime were **NOT RUN**. Independent security review first
returned **NEEDS-FIX** because task-start and variable-injection protections could be
combined against the initial role. The mutation now runs only through an exact-scope
action plugin that reads non-variable Ansible CLI context, rejects task selection and
argument drift before the Kubernetes module, and is covered by the combined bypass
fixture. Tests/documentation review also found and corrected the `no inventory`
wording and missing Markdown-validation command. Independent rereview then inspected
the action plugin, combined fixture, exact source closure, commands/results, and
runtime boundary and returned **APPROVED** with no blockers. Separate security-only
review attempts timed out without a verdict; they made no edits and ran no live
operation, so the completed independent approval is the review evidence.

### Separately approved first check — 2026-08-09

Approved command:

```bash
ansible/bin/bootstrap-cristexhub-dev-namespace check
```

Actual result:

```text
crtxweb : ok=20 changed=1 unreachable=0 failed=0 skipped=2 rescued=0 ignored=0
```

The committed closure contains one change-capable custom action, one exact loop item,
and one exact Namespace manifest. Therefore the one check-mode change predicted only
creation of `cristexhub-dev`; the two skipped tasks are live post-state query and
verification, and check mode made no mutation. Source-validation evidence and the
passed check authorize neither first apply nor idempotence. No PROD, policy, workload,
Secret, PVC, Service, route, Infisical, Argo CD, database, broker, or application
component was deployed. First apply requires a new explicit approval after review of
this evidence; idempotence requires another approval after first-apply evidence.
Independent review found two stale source-only summaries that still said the completed
check was NOT RUN. Both were corrected, regression assertions now reject those stale
phrases across all current checkpoint documents, 6 focused/159 full tests passed
again, and final rereview returned **APPROVED**.

### First apply — 2026-08-09

Executed command:

```bash
ansible/bin/bootstrap-cristexhub-dev-namespace apply
```

Actual result:

```text
crtxweb : ok=22 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

The single exact mutation created only `cristexhub-dev`. Zero skipped/failed tasks
show that protected post-state and service verification ran: all four labels and
`Active` passed, and k3s/Tailscale remained running. No PROD, policy, workload,
Secret, PVC, Service, route, Infisical, Argo CD, database, broker, or application
component was deployed. At that first-apply checkpoint, idempotence had not yet run;
the next section records its later `changed=0` completion. Six focused and 159 full
contracts plus Markdown/diff hygiene passed. Independent review confirmed the
one-object closure, post-state/service assertions, and then-pending idempotence plus
blocked PROD/components and returned **APPROVED**.

### Idempotence — 2026-08-09

Executed command:

```bash
ansible/bin/bootstrap-cristexhub-dev-namespace apply
```

Actual result:

```text
crtxweb : ok=22 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

The exact present-only reconciliation changed nothing. Protected post-state checks
again verified all four labels and `Active`; k3s/Tailscale remained running. The
`cristexhub-dev` Namespace checkpoint is complete. No PROD, policy, workload, Secret,
PVC, Service, route, Infisical, Argo CD, database, broker, or application component
was deployed. Independent review found and corrected one stale first-apply
idempotence statement and one historical Namespace-absence sentence; case-insensitive
regressions now cover both. Six focused/159 full tests passed, and final rereview
returned **APPROVED**.

## Infisical implementation-profile source validation — 2026-08-10

The source-only
[Infisical implementation profile](../../runbooks/infisical-operator-implementation-profile.md)
binds the official `v0.11.7` controller commit as quarantined evidence and records the
confirmed technical profile without promoting any Kubernetes object, operational
Ansible entrypoint, proxy source, credential, or runtime operation. The profile
selects distinct `shared-services`, `argocd`, and `cristexhub-dev` identity intent and
watch scopes; same-Namespace reference enforcement remains blocked and PROD remains
absent/unwatched.

Test-first checkpoint:

```text
New focused contract: ERROR as expected because
ansible/files/policies/infisical-operator-implementation-profile.yml did not exist
```

Validation commands:

```bash
.venv/bin/python -m unittest -v \
  tests.test_infisical_operator_implementation_profile_contract
.venv/bin/python -m unittest -v \
  tests.test_infisical_operator_provenance_contract \
  tests.test_infisical_operator_privileged_prerequisites_contract \
  tests.test_infisical_operator_implementation_profile_contract \
  tests.test_hosted_auth_source_selection_contract \
  tests.test_keycloak_oidc_bootstrap_design_contract \
  tests.test_replacement_recovery_contract tests.test_ansible_contract
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m compileall -q tests
cd ansible/files/vendor/infisical-operator/0.11.7
shasum -a 256 -c SHA256SUMS
cd ../../../../..
git diff --check
git diff --cached --quiet
```

Actual result:

```text
Test-first checkpoint: expected missing implementation-profile policy error
First focused implementation run: 5 passed / 1 exact source-call mismatch
First integrated run: 153 tests / 4 exact-closure failures / 1 binary-read error
Final focused profile: 6 passed
Final affected suite: 64 passed
Final full offline suite: 165 passed
Official source archive: 307 safe members; exact SHA-256 matched
Vendored Infisical SHA256SUMS: PASS
Python compile: PASS
Markdown links/hygiene: PASS
Diff hygiene/no staged files: PASS
```

The source audit proves all six namespaced reconcilers are registered. ClusterGenerator
has no reconciler or eager watch; a forbidden explicit reference would perform an
on-demand cache-backed read that may create a lazy informer. Universal Auth does not use
TokenReview or service-account token creation, and `--metrics-bind-address=0` disables
metrics. The full archive contains upstream install/chart/config/build material but
is forbidden as an operational input. No Helm/GPG runtime, promoted Kubernetes
object, operational Ansible, Squid source, credential, Infisical account/API,
inventory, SSH, kubeconfig, cluster API, or runtime mutation occurred. Deployable source remains blocked pending trust,
compatibility, exact render/RBAC, proxy image/config, and recovery evidence.
Independent review found and corrected the embedded-source quarantine boundary,
cross-Namespace reference-isolation overclaim, release-selection closure, complete
gate regression, and ClusterGenerator lazy-informer wording. Final rereview confirmed
exactly three true gates, no operational archive consumer, and blocked deployable/
runtime source and returned **APPROVED**.

## Infisical guarded idle deployable-source validation — 2026-08-10

The [guarded bootstrap runbook](../../runbooks/infisical-operator-bootstrap.md)
records the exact value-free closure. This checkpoint authored source only. It used no
inventory, SSH, kubeconfig, Kubernetes API, Infisical account/API, Google Drive,
Secret value, check, apply, or runtime mutation.

```text
.venv/bin/python -m unittest -v tests.test_infisical_operator_bootstrap_contract
PASS: 15 focused contracts

.venv/bin/python -m unittest discover -s tests
PASS: 180 full offline contracts

cd ansible
for playbook in playbooks/*.yml; do
  ../.venv/bin/ansible-playbook "$playbook" --syntax-check
done
PASS: 12 playbook syntax checks

cd ansible && ../.venv/bin/ansible-lint --profile production
PASS: 0 failures, 0 warnings; production profile

.venv/bin/python -m py_compile \
  ansible/plugins/action/infisical_operator_guarded_k8s.py \
  ansible/plugins/action/infisical_proxy_secret_zero_guarded_k8s.py \
  tests/test_infisical_operator_bootstrap_contract.py
sh -n ansible/bin/bootstrap-infisical-operator \
  ansible/bin/bootstrap-infisical-proxy-secrets \
  tests/validate_infisical_operator_clean_controller.sh
bash -n tests/reject_infisical_operator_task_start.sh
PASS: Python and shell syntax

tests/validate_infisical_operator_clean_controller.sh
tests/reject_infisical_operator_task_start.sh
cd ansible && ../.venv/bin/ansible-playbook -i localhost, \
  ../tests/reject_infisical_operator_internal_injection.yml \
  -e infisical_operator_bootstrap_internal_preflight_binding=forged
PASS: clean controller, direct action-only guard, combined task-start/injected
binding, and first-task internal-variable fixtures

YAML parse and inventory contract
PASS: 40 single-document objects; exact kind/name/namespace closure; zero Secret,
ClusterRole, ClusterRoleBinding, ClusterGenerator, metrics Service, route, or PROD
object

CRD source mapping and MANIFESTS.sha256
PASS: six promoted namespaced CRDs map to exact hash-bound chart templates; all 40
manifest hashes match; action guard contains 40 canonical object hashes

Markdown links/hygiene and git diff --check
PASS: documentation links resolve, no trailing whitespace, no staged files
```

The source selects six CRDs, six `failurePolicy: Fail` admission policies and six
Deny bindings, three manager Roles/Bindings, exact leader-election RBAC, two
ServiceAccounts, one authenticated TLS Squid ConfigMap/Service/Deployment, one
metrics-off Operator Deployment, and eight NetworkPolicies. The controller watches
only `shared-services`, `argocd`, and `cristexhub-dev`; ClusterGenerator,
review/token permissions, metrics, direct Internet 443, self-hosted Infisical, and
PROD remain absent.

The install check intentionally fails before mutation until the runtime-only proxy
TLS, NCSA, and authenticated URL Secrets exist with exact metadata. The guarded
secret-zero writer source generates these values, requires age-encrypted local and
Google Drive recovery verification before mutation, and exposes no check/diff mode.
Its first live attempt stopped before Ansible/Kubernetes because the existing Drive
OAuth refresh returned `invalid_grant`. Independent review found that the original
cleanup trap was installed too late; the exact mode-0700 plaintext temp residue and
unused encrypted artifact/checksum were removed without reading their content. A
subsequent local debug trace disclosed the unused age identity; it was immediately
revoked and regenerated before any archive upload or Kubernetes mutation, and the
trace was removed. The hardened retry again stopped on `invalid_grant` but proved its
early cleanup, one encrypted pending bundle/checksum, redundant login-Keychain
identity, and zero Kubernetes Secrets. The writer now resumes that exact bundle,
verifies ciphertext/checksum/decrypt and TLS/key/auth relationships, refuses foreign
Secret adoption and implicit rotation, and has direct Operator/proxy action negatives.
The failed controller-rclone path is now superseded. Remaining recovery-write blockers
are host rclone install/idempotence, host OAuth, encrypted transfer/readback,
independent age-key custody, controller verification, and exact Secret write. Live
CRD/CEL admission, image pull/behavior, proxy TLS/auth, NetworkPolicy, controller readiness,
RBAC negatives, check, first apply, idempotence, Universal Auth, and ConfigMap sync
are **NOT RUN/BLOCKED** at this source checkpoint.

## Future validation contract

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-FUT-01 | KIF-001, KIF-007, KIF-008, KIF-028 | Read-only Ansible discovery | Curated report proves actual k3s, storage, resource, and recovery indicators without mutation; human review passes | PARTIAL — host, datastore, capacity, reboot recovery, extended storage, Kubernetes indicators, and functional CNI/NetworkPolicy evidence captured; disk decision and replacement-host recovery remain pending |
| KIF-FUT-02 | KIF-002, KIF-003, KIF-007 | Host baseline safety/idempotence | Syntax/lint/check/diff pass before approval; two approved host-baseline runs converge and preserve recovery access | NOT RUN — runtime gate remains pending |
| KIF-FUT-03 | KIF-005, KIF-006, KIF-013, KIF-028 | OpenTofu state and plans | Format/validate pass; protected state recovers; reviewed plan has no secrets or unapproved destroy | NOT RUN — runtime gate remains pending |
| KIF-FUT-04 | KIF-005, KIF-009, KIF-022, KIF-023 | Render and GitOps reconciliation | Helm/Kustomize/schema checks pass; Argo reconciles private desired state and restores controlled drift | NOT RUN — runtime gate remains pending |
| KIF-FUT-05 | KIF-010, KIF-011, KIF-012, KIF-021 | Network exposure | Required private/public routes work and all DEV/admin/data negative public checks fail closed | NOT RUN — runtime gate remains pending |
| KIF-FUT-06 | KIF-013, KIF-014, KIF-015 | Secret lifecycle | Infisical sync/rotation/revocation and bootstrap recovery pass without plaintext disclosure | NOT RUN — runtime gate remains pending |
| KIF-FUT-07 | KIF-016, KIF-017, KIF-019, KIF-021 | PostgreSQL isolation | DEV, PROD, and Keycloak roles reach only their own logical databases on the general engine; bidirectional cross-access and role/database creation are denied | NOT RUN — runtime gate remains pending |
| KIF-FUT-08 | KIF-016, KIF-018, KIF-019, KIF-021 | MongoDB isolation | Each environment user reaches only its database; cross-environment access is denied and bounded | NOT RUN — runtime gate remains pending |
| KIF-FUT-09 | KIF-020, KIF-021 | Redis/RabbitMQ isolation | Redis is environment-local; RabbitMQ users/vhosts and limits prevent cross-environment access | NOT RUN — runtime gate remains pending |
| KIF-FUT-10 | KIF-022, KIF-023, KIF-024, KIF-025 | Immutable build and promotion | CI publishes once, DEV deploys a digest, and reviewed PROD promotion uses the identical digest | NOT RUN — runtime gate remains pending |
| KIF-FUT-11 | KIF-026, KIF-027, KIF-028 | Backup and restore | Encrypted local/off-node backups pass integrity and isolated restore within declared RPO/RTO | NOT RUN — runtime gate remains pending |
| KIF-FUT-12 | KIF-025, KIF-029, KIF-030 | DEV/PROD operations | DEV soak, private PROD, resource headroom, alerts, rollback, and public-last cutover all pass | NOT RUN — runtime gate remains pending |

## Prospective command families

Exact commands and versions beyond the pinned Ansible collection are selected only
after discovery. Expected families:

```text
ansible-playbook --syntax-check; ansible-lint; approved ansible-playbook --check --diff
reviewed host-baseline Ansible runs and idempotence checks
tofu fmt -check; tofu validate; reviewed tofu plan
helm template; kustomize build; approved schema validation
argocd app diff/get/sync/rollback under the approved private access path
kubectl auth can-i and bounded positive/negative NetworkPolicy probes
database-native authorization, dump, integrity, and isolated restore checks
external reachability tests from both tailnet and non-tailnet clients
```

Tool absence is recorded as NOT RUN, never converted into a fabricated PASS.

## Guarded private Argo CD source — 2026-08-10

Commands:

- `.venv/bin/python -m unittest -v tests.test_argocd_hardened_design_contract`
- `.venv/bin/python -m unittest discover -s tests`
- `cd ansible && ../.venv/bin/ansible-playbook playbooks/bootstrap_argocd.yml --syntax-check`
- `cd ansible && ../.venv/bin/ansible-lint --profile production`
- `tests/validate_argocd_clean_controller.sh`
- `tests/validate_argocd_role_defaults.sh`
- `tests/reject_argocd_task_start.sh`
- `HELM_BIN=/tmp/darwin-arm64/helm tests/validate_argocd_chart_render.sh`
- `git diff --check` plus Markdown link/hygiene and staged-file checks

Actual result: **PASS OFFLINE / RUNTIME NOT RUN** — 15 focused Argo contracts and
184 full contracts passed; all 13 playbooks passed syntax; production-profile lint
passed with zero failures/warnings; clean-controller, direct valid-attestation action,
combined task-start/injected-binding, and first-task internal-injection negatives all
failed closed before Kubernetes. The wrapper's exact JSON extra-var representation
was positively evaluated by Ansible as native boolean `true`. A production-role
default smoke passed all exact 32-source/hash/identity assertions and stopped only at
the deliberately absent local k3s/Tailscale prerequisite. Empty-API check mode now
defers only the unresolved AppProject dry run; apply requires all three CRDs to become
Established before runtime objects. Cryptographic Secret tests reject a noncanonical bcrypt cost, lexically non-RFC3339
or malformed UTC time, and an unrelated TLS key. The pinned 35-object
chart render partitions exactly into 24 promoted, eight custom-hardened, and 11
intentionally omitted identities; all three promoted CRD specs equaled the render;
32 raw hashes, canonical object hashes, unique identities, and the preflight identity
set digest matched. After two NEEDS-FIX rounds closed runtime, hash-templating,
cryptographic, fixture, and living-document defects, independent runtime/security and
tests/docs re-reviews both returned **APPROVED**. Live cases remain blocked as
recorded below.

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-ARGO-04 | KIF-005, KIF-008, KIF-023, KIF-030 | Vendored chart and exact promoted closure | Chart `10.3.0`, app `v3.5.0`, three CRDs, deterministic identity partition, exact hash ledger/source mapping, 32 unique objects, runtime consumes no Helm | PASS OFFLINE — pinned chart hash; exact 35 = 24 promoted + 8 custom + 11 omitted partition; all three promoted CRD specs equal render; 32 hashes/identities match |
| KIF-ARGO-05 | KIF-005, KIF-010, KIF-021, KIF-023 | Minimal private hardened core | Controller, repo-server, server, Redis only; exact digests/resources/security; three ClusterIP Services; no public field/ApplicationSet/Dex/notifications/commit server/PVC/hook/metrics Service | PASS OFFLINE — structural contract |
| KIF-ARGO-06 | KIF-008, KIF-010, KIF-021 | Default-deny and idle namespaced RBAC | Exact six policies and component flows; no metrics ingress; no wildcard/delete/escalate/bind/impersonate/token/Namespace/CRD/cluster-RBAC mutation | PASS OFFLINE — structural contract; port-only 443/6443 limitation documented |
| KIF-ARGO-07 | KIF-005, KIF-013–KIF-015 | Infisical-owned precreated Secrets | Source has zero Secret objects/values; exact three names/types/keys/labels and cryptographic value validity required; initial-admin Secret absent | PASS OFFLINE — no-log exact-scope validator requires bcrypt structure/cost, strict UTC timestamp, key lengths, parseable current direct-CA TLS chain, server identities/usage, and matching leaf/key; cost, noncanonical/malformed-time, and unrelated-key negatives pass; materialization/recovery NOT RUN |
| KIF-ARGO-08 | KIF-002, KIF-005, KIF-030 | Non-passthrough guarded mutation | Only check/apply wrapper, private attestation, canonical task source, exact canonical hashes, present-only, foreign-object refusal, task-selection/injection negatives | PASS OFFLINE — wrapper approval is native boolean; direct valid-attestation action and combined start-at-task/injection fail closed before Kubernetes; default-role smoke reaches only host prerequisites |
| KIF-ARGO-09 | KIF-002, KIF-010, KIF-012, KIF-015 | Live check/apply/readiness/idempotence/private login/recovery | Separate reviewed check, first apply, Ready/TLS/login/traffic negatives, Git read, second apply changed=0, recovery | NOT RUN/BLOCKED — requires exact Infisical-owned Secrets and parent approvals |
| KIF-ARGO-10 | KIF-005, KIF-008, KIF-010, KIF-021 | Empty-install default project startup | A committed `AppProject/default` exists before workloads, denies every source/destination/resource, server/controller may read it, neither can mutate projects, first check tolerates absent discovery without mutation, and apply waits for Established CRDs | PASS OFFLINE — exact deny-all project, non-mutating project RBAC, one-object check deferral, and CRD wait contract are hash/task-bound; live startup remains part of KIF-ARGO-09 |
