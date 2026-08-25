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
| KIF-ANS-15 | KIF-001, KIF-002, KIF-007, KIF-008, KIF-013, KIF-015, KIF-028, KIF-030 | Source-only k3s datastore/encryption preflight contract | Dedicated non-passthrough check-only wrapper requires the canonical controller, clean environment, mode-0600 attestation, exact one-host/check/diff/elevation gates, and fixed ignored inventory; the role runs fixed read-only argv under `no_log`, parses version/config/ExecStart/datastore/encryption/service/Node stages strictly, fails closed on unknown stages, and writes only a deterministic mode-0600 schema-v2 artifact with the exact disclosure-control booleans; no backup, restore, enable/disable/rotate/reencrypt, host, SSH, cluster, or Secret mutation exists | PARTIAL — focused contract requiring fixed `--become`/`--ask-become-pass` CLI elevation while preserving controller-local `become: false`, YAML parse, wrapper-negative, and synthetic disclosure fixture pass; the live read-only wrapper invocation failed before collection at the `ansible_become` gate because it supplied `--ask-become-pass` without `--become`; no collection probe or report was produced, and no datastore, Kubernetes API, Secret, backup, restore, or encryption mutation ran |
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
| KIF-OIDC-01 | KIF-005, KIF-008, KIF-013, KIF-021, KIF-030 | Guarded CristexHub DEV OIDC CONNECT proxy source | Exact ten-object value-free Squid closure, pinned image, CONNECT-only `auth.cristex-soft.com:443` ACL, private/reserved destination denies, exact backend/oauth2-proxy ingress and consumer egress NetworkPolicies, hash-bound non-passthrough wrapper/action, no-delete path, and source-only runtime gate pass without Kubernetes mutation | HISTORICAL PASS SOURCE-ONLY — `python3 -m unittest -v tests.test_oidc_connect_proxy_contract` passed; manifests parse and wrapper shell syntax pass at the pre-apply checkpoint. Current private PROD OIDC evidence is recorded below |
| KIF-STO-01 | KIF-001, KIF-003, KIF-008, KIF-030 | Non-destructive storage discovery offline contract | Built-in facts project only curated device/partition size, rotational/removable state, direct mount state, and mounted filesystem types; exact StorageClass behavior fields, bounded PV placement booleans, and PVC metadata from five fixed namespaces omit device serials, UUIDs, addresses, backing paths, filesystem contents, Secret/ConfigMap kinds, and broad PVC queries | PASS — focused contracts, all 28 offline tests, collision-safe synthetic render, discovery syntax, and production lint passed; no inventory host, kubeconfig, Kubernetes API, or filesystem content was accessed |
| KIF-STO-02 | KIF-001, KIF-008, KIF-030 | Extended storage discovery runtime | A separately approved one-host elevated check/diff run renders valid mode-0600 JSON and human review establishes actual curated device, StorageClass, PV, and PVC indicators without mutation or sensitive metadata | PASS — ok=17/changed=1 local report/failed=0; unmounted 1 TB rotational disk with one partition, NVMe/root capacity, local-path `Delete`/`WaitForFirstConsumer`/no expansion, and zero PV/PVC objects confirmed. Historical boundary: that report's fifth PVC scope was `shared-data`; KIF-ANS-13 later live-verifies the current zero-count `shared-services` query. Filesystem/content/health and reuse decision remain unknown; no disk mutation |
| KIF-REC-01 | KIF-002, KIF-003, KIF-013, KIF-015, KIF-028, KIF-030 | Replacement-host recovery first offline increment | Secret-free runbook/register truthfully separate same-host reboot from replacement, require old-host fencing and exclusive storage ownership, stop split brain, require exactly one preserve-existing or create-new identity decision, and leave datastore/version/token/storage/RPO/RTO/off-node prerequisites explicitly unknown without guessed commands | PASS — 5 focused offline recovery contracts and the full offline suite passed; documentation contains no executable recovery command or secret-shaped value and no host/provider/API was accessed |
| KIF-REC-02 | KIF-007, KIF-015, KIF-026–KIF-030 | Replacement-host recovery rehearsal/runtime | An isolated, approved replacement follows an actual version/datastore/storage-specific plan; proves one authoritative cluster/storage writer, desired state, mutable data, encryption behavior, isolation, and measured RPO/RTO before public reactivation | NOT RUN/BLOCKED — identity model and datastore, exact version/config, token custody, storage, RPO/RTO, off-node artifacts, restore procedures, and approvals remain `UNKNOWN — STOP`; reboot success is not replacement proof |
| KIF-TOFU-01 | KIF-002, KIF-005, KIF-006, KIF-013, KIF-030 | Pinned host installer offline contract | Source structurally requires default-false install and separate rollback approval, diff/one-host gates, Debian 13 x86_64, reviewed checksum-pinned archive/payload digests, an existing non-root operator without UID aliases, strict remote and controller-cache modes, symlink-safe controller preflight, controller-only download plus verified Ansible transfer, absent-only version extraction, an exact managed selector, protected state directory, service preservation, check-mode prediction, and selector-only state-preserving rollback | PASS — focused structural contracts, full offline suite, syntax, and production lint passed; controller transfer fix used no host/provider contact and negative runtime branches remain NOT RUN |
| KIF-TOFU-02 | KIF-002, KIF-007, KIF-030 | Historical OpenTofu host-install runtime | Approved check/diff, reviewed live run, exact version verification, preserved k3s/Tailscale, and a changed=0 rerun pass before provider import | HISTORICAL PASS PRE-IMPORT — initial check passed at ok=27/changed=6/failed=0; bounded host-egress failure stopped at ok=21/changed=2/failed=1; reviewed controller-transfer check passed at ok=33/changed=6/failed=0, live recovery passed at ok=39/changed=6/failed=0, and second run converged at ok=30/changed=0/failed=0. The exact CLI and selector exist; the then-empty protected directory is historical evidence |
| KIF-TOFU-03 | KIF-004–KIF-006, KIF-013 | Historical Cloudflare-only zero-resource scaffold | Exact OpenTofu/provider pins and local backend path existed with zero resources/data/modules/imports/variables/outputs at the pre-import source checkpoint | HISTORICAL PASS PRE-IMPORT — static contract passed; `tofu fmt/validate` and provider initialization were not run at that checkpoint because no approved controller binary/provider download existed. Current source adds the reviewed PROD route to imported-resource state |
| KIF-TOFU-04 | KIF-013, KIF-028, KIF-030 | Historical local-state encryption and off-node recovery gate | Timestamped encrypted Google Drive copies, independent key custody, integrity verification, and isolated restore were required before the first provider apply | HISTORICAL NOT RUN/BLOCKED — no state existed at the pre-import checkpoint; later protected state backup/readback and isolated restore passed for imported existing resources; the pending PROD route remains separately gated |
| KIF-TOFU-05 | KIF-005, KIF-013, KIF-028, KIF-030 | Separate GitHub-root state backup and first-genesis absence source closure | Fixed `/var/lib/opentofu/cristexweb/github.tfstate` is encrypted into timestamped immutable three-leaf archives under the unique GitHub archive root, read back byte-for-byte, and restored only into an isolated temporary path for checksum/JSON/`tofu state list` validation; first-genesis absence uses a dedicated expiring three-leaf encrypted attestation/restore root with no state write; exact parent/state symlink, recipient, remote-type, three-address, incomplete-directory, explicit-Python, per-run-attestation, and no-timer-state guards are source-bound and cannot select the foundation path | PASS SOURCE-ONLY — focused GitHub recovery contract, YAML parse, shell syntax, Python compile, affected layout/namespace/recovery contracts, and diff hygiene passed. No inventory host, Google Drive, Infisical, OpenTofu provider, state file, timer, or archive was contacted or mutated; controller syntax/lint and focused offline validation passed; backup/test/restore/attest/restore-absence remain blocked pending separate state-genesis and approvals |
| KIF-NS-01 | KIF-002, KIF-005, KIF-006, KIF-010, KIF-030 | Bounded platform Namespace bootstrap offline contract | Exact committed `argocd` and `platform-edge` Namespace manifests are the sole object definitions consumed by the closed historical bootstrap, and the architecture/task checklist places them in a documented pre-Stage-4 exception with separate check/apply/idempotence approvals that waives no Stage 4 entry gate; a non-passthrough entrypoint rejects `--start-at-task`, `--step`, and all extra arguments; the wrapper launches the repository `.venv` controller in an allowlisted clean environment and supplies a private random single-run attestation; the mutating task independently requires that attestation, reloads only literal manifest paths, and rejects extra top-level/metadata keys; a first-task internal-variable guard, canonical non-symlink ancestor/leaf validation, approval/diff/exact-limit/kubeconfig/protected-result gates, foreign-existing refusal, present-only reconciliation, exact post-verification, truthful ownership labels, executable closure, and no deletion/other-kind path are enforced | PASS — focused structural, stage-boundary, control-flow, and synthetic ancestor-symlink contracts, controller-only forged-extra-var rejection, full offline suite, syntax, synthetic discovery validation, and production lint passed without inventory or Kubernetes API contact |
| KIF-NS-02 | KIF-002, KIF-005, KIF-010, KIF-030 | Platform Namespace bootstrap runtime | Reviewed check predicts exactly the two absent Namespaces; approved live run creates them, verifies labels/services, and second run converges changed=0 without installing Argo CD/cloudflared or creating a route | PASS — wrapper check passed without mutation; separately approved first apply passed at ok=21/changed=1/unreachable=0/failed=0/skipped=0 and changed exactly `argocd` plus `platform-edge`. During the separately approved idempotence checkpoint, a local sudo authentication failure stopped the initial invocation before service preflight/reconciliation at ok=10/changed=0/unreachable=0/failed=1/skipped=0; the retry passed at ok=21/changed=0/unreachable=0/failed=0/skipped=0, both exact items were `ok`, post-state identity/labels/Active passed, and service health was preserved |
| KIF-NS-03 | KIF-002, KIF-005, KIF-006, KIF-010, KIF-016, KIF-030 | Historical foundation Namespace source checkpoint | Exact `platform-secrets` and `platform-identity` source plus a guarded present-only wrapper passed offline validation, but the wrapper never ran and the placement was superseded before runtime | SUPERSEDED SOURCE-ONLY — historical validation remains truthful; no cluster object was created or deleted by this checkpoint |
| KIF-ARGO-01 | KIF-005, KIF-008, KIF-010, KIF-013, KIF-015, KIF-023, KIF-030 | Argo CD candidate provenance and target-minor screen | Historical secret-free evidence binds exact official chart/index/provenance/image/render inputs plus target kubelet and tested-version sources while the separate release record now selects chart `10.3.0` / app `v3.5.0` only for offline source authoring | PASS — focused provenance contracts preserve exact associations and target-minor qualification; selection remains NOT DEPLOYABLE and Argo runtime remains NOT RUN/BLOCKED |
| KIF-ARGO-02 | KIF-005, KIF-008, KIF-010, KIF-013, KIF-015, KIF-021, KIF-023, KIF-030 | Argo CD online/static readiness refresh | A secret-free record curates deterministic render, upstream API registration, RBAC/network, image trust/availability/vulnerability, private-Git, and Namespace-adoption evidence while all live admission/runtime gates remain blocked | PASS — focused provenance contracts preserve the 44-document render and security blockers; no values, rendered YAML, Kubernetes object, credential, or deployable controller source was added |
| KIF-ARGO-03 | KIF-002, KIF-003, KIF-005, KIF-008, KIF-010, KIF-013–KIF-015, KIF-021, KIF-030 | Historical Argo CD source-only hardened-design checkpoint | At that checkpoint, a secret-free design fixed private access, retained quiescent ApplicationSet, supplemental default-deny, phased least privilege, private Git/secret custody, adoption, stop/rollback, and ownership without deployable source | PASS HISTORICAL/SUPERSEDED — the checkpoint was valid when recorded; current guarded cases KIF-ARGO-04 through KIF-ARGO-10 implement an exact private core with ApplicationSet runtime absent while runtime remains blocked |
| KIF-IDP-01 | KIF-002, KIF-003, KIF-005, KIF-010, KIF-012–KIF-017, KIF-021, KIF-023, KIF-026–KIF-030 | Source-only Ansible bootstrap and Keycloak OIDC architecture | Ansible is the selected bounded bootstrap installer and privileged lifecycle owner with no dual reconciliation; direct Argo OIDC separates Keycloak authentication/groups, Argo RBAC, and Kubernetes RBAC while preserving private administration, Infisical-owned values, a dedicated Keycloak logical database/role on the general shared PostgreSQL engine, stable issuer, exact approvals, and handoff gates | PASS — Keycloak `26.7.1`, PostgreSQL `17.10`, realm, issuer, clients, group templates, default theme, separate deployment, and shared-engine isolation policy are selected only for offline authoring; no executable component source, credential, route, or runtime was added |
| KIF-IDP-02 | KIF-005, KIF-010–KIF-015, KIF-021, KIF-025, KIF-030 | CristexHub PROD browser identity source contract | The value-free policy selects confidential client `cristexhub-prod` with PKCE S256, the stable `cristexhub` issuer, exact callback/origin/post-logout URLs for `hub.cristex-soft.com`, environment-bound PROD groups, and fail-closed claims while preserving DEV and administrative privacy | PASS SOURCE-ONLY — 21 focused policy/design tests pass; the PROD client secret remains an Infisical-owned key name only, Reactive Resume/Argo callbacks remain unselected, no route or runtime activation is authorized, and no Keycloak/API/provider operation ran |
| KIF-DB-01 | KIF-005, KIF-013, KIF-016–KIF-019, KIF-021, KIF-026–KIF-030 | Shared database source-only architecture | One PostgreSQL and one MongoDB engine are placed in `shared-services`; exact consumers remain isolated and the approved source profile fixes NVMe `local-path`, 40/80 GiB PVCs, bounded resources, private standard Services/TLS, Ansible→Argo ownership direction, and daily/14-day/24h/4h backup targets | HISTORICAL PASS SOURCE-ONLY — exact consumer/profile contracts pass; the historical MongoDB source selected `8.0.28` standalone/non-authoritative closure. Current operator-managed `8.0.12` evidence and its NetworkPolicy blocker are recorded below |
| KIF-MQ-01 | KIF-005, KIF-013, KIF-016, KIF-019–KIF-021, KIF-026–KIF-030 | Shared RabbitMQ source-only architecture | Exactly one future RabbitMQ engine belongs in `shared-services`; DEV/PROD have dedicated vhost/user/Infisical credential/permission/limit/recovery scopes, deny-first cross-vhost/admin/public-management rules, and future consumers require reviewed exact changes | HISTORICAL PASS SOURCE-ONLY — canonical value-free policy and fail-closed contracts pass at the pre-runtime checkpoint. Current broker/Celery evidence and least-privilege/recovery residuals are recorded below |
| KIF-BKP-01 | KIF-005, KIF-013, KIF-017–KIF-020, KIF-026–KIF-030 | Shared stateful backup access architecture | PostgreSQL, MongoDB, and RabbitMQ use encrypted timestamped separate-purpose archives, private authenticated metadata/list/retrieve/verify access, non-destructive off-node copy, integrity and isolated restore; RabbitMQ definitions remain distinct from queued-message recovery | PASS SOURCE-ONLY — daily archives, 14-day local/off-node retention, RPO 24h, and RTO 4h are fixed; pinned host rclone `1.71.1` replaces the container direction and its install/idempotence pass, but identities, staging, credentials, dumps, jobs, schedules, deletion, restore, and runtime remain blocked |
| KIF-GHA-01 | KIF-005, KIF-022–KIF-025, KIF-030 | GitHub-hosted infrastructure source CI | Exactly one workflow uses SHA-pinned actions, a fixed runner, read-only permission, bounded triggers/timeouts/concurrency, frozen controller dependencies, and exact offline tests without Secret/package/registry/provider/host/cluster/deploy access | PASS SOURCE AND HOSTED CI — focused/full contracts passed; run `31311995461` and job `93241094377` completed successfully for exact commit `e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`; branch protection, GHCR publication, digest evidence, and deployment remain NOT RUN/BLOCKED |
| KIF-RR-01 | KIF-012–KIF-017, KIF-019, KIF-021, KIF-023, KIF-026–KIF-030 | Reactive Resume private-MVP source architecture | Include environment-local Reactive Resume DEV in the private MVP, reserve separate PROD, bind exact OIDC clients and dedicated shared-PostgreSQL scopes, keep Infisical value ownership/private exposure, and gate image/callback/object/Secret/recovery/handoff/runtime promotion | PASS SOURCE AND PRIVATE DEV CHECKPOINT — value-free source, private hostname/runtime validation, shared-realm client source check, and private application cycle are checkpointed. The prior schema-1 non-empty backup passed with a sanitized receipt, while hardened schema-2 install/backup/restore remains pending. Argo check is blocked on missing `argocd-repository-cristexweb` credential metadata; PROD/public promotion, soak, and final handoff remain pending |
| KIF-CF-01 | KIF-005, KIF-011, KIF-013, KIF-015, KIF-021, KIF-023, KIF-030 | Historical source-only cloudflared candidate provenance | A secret-free record mutation-resistently binds exact official release/source/asset and architecture-specific image evidence while preserving the pre-import OpenTofu state/resource boundary | HISTORICAL PASS — 5 focused contracts enforce exact evidence associations, trust qualifications, token/health/network semantics, unchanged source sets, operational-command hygiene, and RFC1918/loopback sentinels; the candidate remains NOT DEPLOYABLE/NOT SELECTED. Current imported Cloudflare state and pending PROD route are recorded in the live checkpoint |
| KIF-CF-02 | KIF-005, KIF-010, KIF-011, KIF-012, KIF-013, KIF-015, KIF-021, KIF-030 | Phased Cloudflare-to-Keycloak route contract | A value-free policy fixes Cloudflare -> cloudflared/platform-edge -> Traefik/kube-system -> Keycloak/shared-services, separates account/state, tunnel/token, connector, Traefik, DNS, validation, and production approvals, forbids token disclosure and direct origin exposure, requires positive flow plus negative admin/management/DEV/Argo/data reachability tests, and defines exact-route rollback while runtime remains blocked | PASS SOURCE-ONLY — focused contract validates path, ownership, token boundaries, separate approvals, deny-first public surfaces, negative reachability, rollback, and no runtime source |
| KIF-INF-01 | KIF-005, KIF-013–KIF-015, KIF-021, KIF-023, KIF-030 | Source-only Infisical Operator provenance and selection boundary | Historical evidence distinguishes unselected `v0.11.8` distribution observations from the aligned `v0.11.7` set selected only as the offline baseline; trust, compatibility, scoped RBAC, Universal Auth recovery, traffic, and runtime remain blocked | PASS — focused contracts enforce exact evidence associations, qualified trust wording, immutable child direction, and no deployable controller source or Secret |
| KIF-INF-02 | KIF-005, KIF-013–KIF-015, KIF-021, KIF-023, KIF-030 | Inert Infisical privileged-prerequisite inventory | Bind exactly seven raw CRD templates and observed RBAC/scoping seams—including ineffective scoped-Role access to cluster-scoped TokenReview/ClusterGenerator and the singular/plural metrics defects—without adding valid CRD/RBAC, values, render, Ansible entrypoint, Secret, or runtime source | PASS — inventory remains inert; completed foundation Namespaces and the separately selected watch profile are now truthful gates while all deployable/runtime gates remain false |
| KIF-INF-03 | KIF-005, KIF-013–KIF-016, KIF-021, KIF-023, KIF-030 | Infisical source audit and implementation profile | Hash-bind official `v0.11.7` controller commit as quarantined evidence and prove controller/auth/ClusterGenerator behavior; select exact five-Namespace source-only watch/separate-identity intent, metrics-off, no cluster manager/generator/review-token permission, authenticated Squid direction, age/Drive secret-zero direction, and non-sensitive ConfigMap proof while same-Namespace enforcement remains blocked | PASS SOURCE-ONLY — 6 focused/64 affected/165 full contracts, source hashes, compile, Markdown, and diff checks pass; no embedded artifact is promoted as Kubernetes/Ansible/proxy/credential/runtime source |
| KIF-INF-04 | KIF-005, KIF-013–KIF-016, KIF-021, KIF-023, KIF-030 | Guarded Infisical idle deployable closure | Promote exactly six hash-mapped namespaced CRDs, six fail-closed same-Namespace admission policies/bindings with Universal-Auth-only enforcement including legacy service-account/service-token rejection, exact five-Namespace read-only target RBAC, metrics-off digest-pinned Operator, authenticated TLS Squid, proxy-only egress, and a 44-object guarded check/apply path; commit no Secret value, Infisical CR, PROD workload, or self-hosted server | PASS RUNTIME — source contracts passed for the exact 44-object closure. After two local mode-only safe stops were corrected without cluster mutation, check passed at `ok=30 changed=1 failed=0 skipped=5`; first apply passed at `ok=35 changed=1 failed=0`; post-check converged at `ok=30 changed=0 failed=0 skipped=5`; separately confirmed idempotence passed at `ok=35 changed=0 failed=0`. Both Deployments and k3s/Tailscale remained healthy. No Infisical CR, Universal Auth, application Secret/workload, PVC, database, or route was created; broader admission/RBAC/traffic and every credential-bearing PROD phase remain blocked |
| KIF-INF-05 | KIF-005, KIF-013–KIF-015, KIF-023, KIF-027, KIF-030 | Infisical proxy secret-zero recovery and write | Generate exact TLS/Basic/client material only in a private temp directory; age-encrypt it, verify it off-node through the guarded host transfer, then write exactly three no-log Secrets through a guarded action | STOPPED BEFORE KUBERNETES — historical hardened retry proved cleanup, encrypted-pending resume, Keychain copy, and zero Kubernetes Secrets, then stopped on Drive `invalid_grant`. Source now removes controller rclone and requires exact `drive-verified`; installer apply/idempotence and host OAuth passed; transfer check passed, but apply stopped on unsupported `--local-umask` before a successful upload and exact cleanup removed staging; transfer retry passed `ok=39 changed=7`; proxy Secret bootstrap passed `ok=15 changed=1`; exactly three proxy Secrets now exist and implicit rotation is refused |
| KIF-INF-06 | KIF-005, KIF-010, KIF-013–KIF-016, KIF-021, KIF-023, KIF-030 | Infisical Argo CD Secret materialization seam | One same-Namespace Universal Auth credential reference, fixed project/environment/path identifiers, explicit safe source options (`recursive: false`, empty `tagSlugs`, no `projectId`, fixed sync options), exact Connection/Auth/StaticSecret source closure, explicit orphaned templates for exactly three Argo CD Secrets, additive exact-name Secret/workload-list RBAC, fail-closed admission, and a guarded check/apply wrapper; no credential Secret or values are committed | PASS SOURCE-ONLY / RUNTIME NOT RUN-BLOCKED — 10 focused contracts, source/manifest hashes, v0.11.7 CRD fields, exact Connection/Auth/LastReconcileStatus readiness, six Established-CRD prerequisites, alternate-target preflight, VAP type-check/effective waits, immutable-target refusal, syntax, lint, action-only, forged-internal, and task-selection boundaries pass; credential/source creation, check/apply, sync, target values, and live admission remain blocked |
| KIF-INF-07 | KIF-005, KIF-013–KIF-015, KIF-021, KIF-023, KIF-030 | Infisical database Secret materialization seam | Exactly 15 value-free objects freeze one `shared-services/infisical-cloud` Connection, separate PostgreSQL/MongoDB Auth and Universal Auth credential names, paths `/shared-services/postgresql` and `/shared-services/mongodb`, two StaticSecrets, eleven targets aligned with engine and seven per-consumer contracts, eight scoped fail-closed VAP/bindings, and additive exact-name writer RBAC without workload write/delete; corrected Argo/database VAP match conditions block foreign target writers, unreviewed Operator names, and cross-policy interference | PASS SOURCE CONTRACT / REACTIVE RESUME LIVE DRIFT BLOCKED — 9 focused contracts, byte/canonical/identity hash checks, VAP cross-policy negatives, source-key/path/type/label/orphan checks, syntax, production lint, compile, shell, action-only, forged-internal, and task-selection fixtures pass. Read-only evidence proves the two Reactive Resume PostgreSQL targets are live and Infisical-owned despite historical blocked wording; provenance/live admission are unresolved, credentials require rotation/revocation, and recovery/runtime remain blocked |
| KIF-INF-08 | KIF-005, KIF-013–KIF-015, KIF-021, KIF-023, KIF-027, KIF-030 | Infisical Universal Auth and protected value lane | Exact writer/runtime identity separation, three fixed paths, engine plus seven deterministic consumer credentials, exact encrypted archive closure, no fake endpoint, ambiguous-POST stop, exact response-key checks, and a fresh preflight-hash/k3s-version/datastore-bound recovery attestation gate precede any credential-bearing Kubernetes Secret write | PASS SOURCE-ONLY / RUNTIME NOT RUN-BLOCKED — 7 focused contracts and full validation pass; vendor API semantics, identities, values, recovery attestation, upload, and Kubernetes seed remain absent/unverified |
| KIF-K3S-02 | KIF-002, KIF-005, KIF-007, KIF-013–KIF-015, KIF-027, KIF-030 | Read-only k3s datastore/encryption preflight | Check-only fixed commands classify only safely parsed default/exact data-dir evidence, privately bound config markers, official JSON encryption status/rotation with stable hash-match gates, protect every datastore/output path component, clear raw facts before report construction, and emit only sanitized local evidence | PASS SOURCE-ONLY / LIVE UNKNOWN EVIDENCE — focused contract, parser, disclosure, duplicate/type/malformed config, custom-data-dir, external/cluster-init ambiguity, JSON stderr/nonzero/malformed, active/stable/hash-mismatch, wrapper, syntax/lint, compile, shell, and diff checks pass offline. The separately approved live read-only run passed `ok=45 changed=1 unreachable=0 failed=0`; sanitized artifact v1.36.2+k3s1 reported `config_status=present_safe`, `data_dir_source=config_override_unknown`, and datastore/encryption/rotation `unknown`. No backup, restore, key/hash/error, host, cluster, or Secret mutation ran. Official source pin: K3s `v1.36.2+k3s1`, commit `01b6f04aaa69e8b09303f0393d4b4f1811da23aa` |
| KIF-DB-02 | KIF-013–KIF-021, KIF-023, KIF-026–KIF-030 | Guarded logical database provisioning | Exact five PostgreSQL and two MongoDB empty reservations consume precreated file-mounted credentials through UID-bound tokenless helpers; exact Ingress/Egress policy allows only database and CoreDNS, complete scopes are data-empty, PostgreSQL role-only interruption is repairable, and all PROD scopes remain inactive | PASS SOURCE-ONLY / RUNTIME NOT RUN-BLOCKED — 7 focused contracts now execute both exact helper definitions against the mutation guard, with current hash binding, credential-item closure, shell/playbook syntax, and lint; check/apply/idempotence, authorization, backup/restore, and PROD acceptance are not run |
| KIF-SRC-01 | KIF-005, KIF-010, KIF-013–KIF-015, KIF-023, KIF-030 | Deterministic hosted source-baseline closure | Exact release records, value-free identity/authorization policy, chart/provenance/public-key bytes, SHA256SUMS, safe chart roots, exact five-Namespace manifest closure, and exact allowlisted component source are enforced offline | PASS — source-selection plus affected provenance/design/layout contracts pass; exact hashes verified; no live/runtime operation or staged file |
| KIF-NS-04 | KIF-002, KIF-003, KIF-005, KIF-013–KIF-017, KIF-021, KIF-026–KIF-030 | Shared-services placement correction | Replace never-run `platform-secrets`/`platform-identity` source with one exact present-only `shared-services` Namespace; reserve `platform-edge` for cloudflared; place Infisical Operator, separate Keycloak, and one general PostgreSQL instance in commons intent; give Keycloak only a dedicated logical database/role/credential on that engine | PASS — 78 focused and 115 full offline tests, 9 syntax checks, production lint, fail-closed fixtures, archive hashes, links, closure, hygiene, and historical-source preservation passed; no discovery, check, apply, deletion, workload, Secret, database, route, or runtime operation |
| KIF-NS-05 | KIF-002, KIF-005, KIF-016, KIF-030 | Shared-services Namespace runtime | A successful wrapper check predicts only the absent exact `shared-services` Namespace; separately approved first apply creates/verifies it; separately approved idempotence converges at changed=0 | PASS — check retry passed at `ok=20 changed=1 failed=0`; first apply passed at `ok=22 changed=1 failed=0`; separately approved idempotence passed at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`, with exact identity/three labels/`Active` and k3s/Tailscale health preserved. No component was deployed |
| KIF-NS-06 | KIF-002, KIF-005, KIF-006, KIF-010, KIF-016, KIF-025, KIF-030 | CristexHub DEV Namespace source and runtime | Dedicated guarded source reconciles only `cristexhub-dev` with four approved labels and present-only semantics; check predicts only that Namespace without mutation; first apply creates/verifies it; idempotence converges; PROD runtime and all other kinds remain absent | PASS — check passed at `ok=20 changed=1 failed=0 skipped=2`; first apply passed at `ok=22 changed=1 failed=0 skipped=0`; idempotence passed at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`, with exact labels/`Active` and service health preserved |
| KIF-NS-07 | KIF-002, KIF-005, KIF-006, KIF-010, KIF-016, KIF-025, KIF-030 | CristexHub PROD Namespace guarded bootstrap | Dedicated non-passthrough source defines only `cristexhub-prod` with exact four PROD labels, the mandatory Kubernetes Namespace-name label at runtime, a non-overridable literal SHA-256 manifest binding, canonical task-source/action-only guard, private attestation/preflight binding, foreign-existing refusal, present-only semantics, and no deletion path | PASS RUNTIME — approved check predicted the single absent Namespace at `ok=20 changed=1 failed=0 skipped=2`; first apply created it but the historical four-label post-check stopped after mutation; read-only inspection confirmed exact intended labels plus Kubernetes' mandatory label and `Active`; corrected check passed at `ok=20 changed=0 failed=0 skipped=2`; separately approved idempotence passed at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`, with exact post-state and k3s/Tailscale health |
| KIF-ARGO-12 | KIF-005, KIF-006, KIF-010, KIF-016, KIF-021, KIF-025, KIF-030 | CristexHub PROD Argo registration source-only closure | Exactly five value-free objects pin protected-main revision `751885a42798d282e168131db147f13694a0a621` and path `infra/kubernetes/cristexhub-prod`; the Project/destination/cluster-registration Secret/RBAC are PROD-only, no-delete, no-cluster-resource, `CreateNamespace=false`, `Prune=false`, manual, and protected by an always-active deny window plus present-only attestation/preflight/hash/foreign-object guards | HISTORICAL PASS SOURCE-ONLY — 11 focused offline contracts, action compile, wrapper shell, and playbook syntax validate the exact closure; the live Namespace was `Active` at this checkpoint. Current registration/sync evidence is recorded below |

## Current runtime evidence — 2026-08-21

The source-only rows above intentionally preserve their pre-activation checkpoints.
They are historical evidence, not current absence claims.

- **PROD runtime/Argo:** The Infisical runtime seam apply and final idempotence
  passed at `ok=62 changed=0 failed=0 skipped=3`. Argo registration at revision
  `751885a42798d282e168131db147f13694a0a621` uses the exact in-cluster server and
  `selfHeal=true`, `prune=false`, `allowEmpty=false`; Argo is `Synced/Healthy` and
  the five PROD Deployments are each `1/1 Ready`.
- **OIDC:** The CONNECT proxy policy is applied and includes the PROD backend,
  Celery, and oauth2-proxy clients. App-level smoke returned backend `200`,
  oauth2-proxy root/start `302`, and Celery readiness; this is not full authenticated
  OIDC/CONNECT validation. Source confirms the exact allowlist
  `auth.cristex-soft.com:443` and `api.deepseek.com:443`; no public route is implied.
- **RabbitMQ:** The shared broker is live and Celery is connected/ready on
  `/cristexhub-prod`. The observed principal is `cristexhub_prod_user` and its
  broad `^[^*]+$` permission expressions require least-privilege reconciliation;
  definitions/queued-message recovery and exposed-credential rotation remain open.
- **MongoDB:** Operator-managed MongoDB `8.0.12` with TLS/SCRAM is live, but private
  acceptance is blocked. No NetworkPolicy selects `shared-mongodb-0`, and legacy
  selectors do not match the live MongoDB or backend/Celery labels. Do not claim
  private MongoDB acceptance until an exact deny-first policy and positive/negative
  connectivity tests pass. Engine connectivity and runtime Secret presence do not
  prove logical database authorization or cross-access negatives. MongoDB URL and
  GHCR pull credentials require verified rotation; the exposed DeepSeek key requires
  separate revoke/replace.
- **OpenTofu:** Existing protected state manages imported Cloudflare Tunnel,
  Keycloak/DEV DNS, and private Argo DNS resources; encrypted backup/readback and
  isolated restore pass. The committed PROD Tunnel/DNS source remains unapplied
  pending a protected DNS-capable credential and exact plan.
- **Reactive Resume DEV:** The source and private runtime/hostname checkpoint are
  implemented, and the shared `cristexhub` client source check passed without
  Keycloak/API or Kubernetes mutation. The prior installed source produced the
  sanitized schema-1 non-empty receipt `run_id=20260825T065948Z
  object_count=1 total_object_bytes=50 readback=verified encrypted=true
  private_residue=none`. Hardened schema-2 install, fresh non-empty backup,
  isolated restore, measured RPO/RTO, and final scheduler enable/idempotence are
  pending. The guarded Argo check reached live dependency metadata and stopped on
  the missing Infisical-owned `argocd-repository-cristexweb` credential metadata;
  no registration, sync, or handoff occurred. PROD and public routing remain
  inactive.

## Historical Infisical Operator PROD watch source validation — 2026-08-18

At the pre-runtime source checkpoint, offline-only validation covered the proposed
44-object increment (after the historical
40-object runtime checkpoint; the intermediate 42-object source was not separately
runtime-applied):

```bash
ANSIBLE_COLLECTIONS_PATH=/home/paul/.ansible/collections \
  .venv/bin/python -m unittest -v \
  tests.test_infisical_operator_bootstrap_contract \
  tests.test_infisical_operator_implementation_profile_contract \
  tests.test_infisical_cristexhub_prod_runtime_contract
.venv/bin/python -m py_compile \
  ansible/plugins/action/infisical_operator_guarded_k8s.py \
  tests/test_infisical_operator_bootstrap_contract.py \
  tests/test_infisical_operator_implementation_profile_contract.py \
  tests/test_infisical_cristexhub_prod_runtime_contract.py
for script in ansible/bin/*; do sh -n "$script"; done
for script in tests/*.sh; do bash -n "$script"; done
.venv/bin/python -m unittest discover -s tests -q
cd ansible
for playbook in playbooks/*.yml; do
  ../.venv/bin/ansible-playbook -i .ansible/inventory.local.yml "$playbook" --syntax-check
done
../.venv/bin/ansible-lint --offline --profile production .
cd ..
if .venv/bin/ansible-playbook -i localhost, tests/reject_infisical_operator_action_only.yml --limit localhost; then
  echo 'FAIL: action-only Infisical fixture unexpectedly succeeded' >&2
  exit 1
fi
.venv/bin/ansible-playbook -i localhost, tests/reject_infisical_operator_internal_injection.yml --limit localhost
tests/reject_infisical_operator_task_start.sh
git diff --check
git diff --cached --quiet
```

Result: **PASS SOURCE-ONLY** — 31 focused Operator/implementation-profile/PROD
contracts passed; the full offline matrix discovered 385 tests. Exact 44-object
inventory, six CRDs, six policies/bindings, five manager Roles/Bindings, no
Secret/ClusterRole/ClusterRoleBinding, exact raw/canonical hashes, ordered identity
closure, five-namespace Active preflight, and PROD generic-only admission source
passed. Compilation, shell checks, playbook syntax, production lint, negative
fixtures, and diff checks are required in this matrix. At this historical source
checkpoint, no Kubernetes, provider, or Infisical API was contacted; no runtime
apply, Namespace creation, value, Secret, workload, or route operation ran. The
separately recorded runtime checkpoint below supersedes only the unrun status, not
this offline validation evidence.

## Infisical Operator 44-object runtime checkpoint — 2026-08-18

The first two wrapper checks stopped at the controller-side manifest mode guard
because newly introduced leaves were `0664`; no Kubernetes API mutation occurred.
After exact local normalization to `0644`, the separately guarded sequence passed:

```text
check:            ok=30 changed=1 unreachable=0 failed=0 skipped=5
apply:            ok=35 changed=1 unreachable=0 failed=0 skipped=0
post-apply check: ok=30 changed=0 unreachable=0 failed=0 skipped=5
idempotence:      ok=35 changed=0 unreachable=0 failed=0 skipped=0
```

The check predicted exactly three generic admission-policy updates, the controller
five-Namespace watch update, and the PROD manager Role/RoleBinding. Apply and
idempotence kept both Deployments Available and preserved k3s/Tailscale health. The
checkpoint created no Namespace, Secret, Infisical custom resource, credential,
application workload, PVC, database, route, or provider resource. PROD Universal
Auth, Secret materialization, stateful logical scopes, Keycloak client/groups, Argo
registration/sync, application Pods, and Cloudflare routing remain separately
blocked.

## CristexHub PROD Namespace source-only validation

Offline-only commands:

```bash
python3 -m unittest -v tests.test_cristexhub_prod_namespace_contract
python3 - <<'PY'
from pathlib import Path
import yaml
for path in (
    Path('kubernetes/applications/namespaces/cristexhub-prod.yaml'),
    Path('ansible/playbooks/bootstrap_cristexhub_prod_namespace.yml'),
    Path('ansible/roles/cristexhub_prod_namespace_bootstrap/defaults/main.yml'),
    Path('ansible/roles/cristexhub_prod_namespace_bootstrap/tasks/main.yml'),
    Path('tests/reject_cristexhub_prod_namespace_action_only.yml'),
    Path('tests/reject_cristexhub_prod_namespace_internal_injection.yml'),
):
    yaml.safe_load(path.read_text())
PY
python3 -m py_compile \
  ansible/plugins/action/cristexhub_prod_namespace_guarded_k8s.py \
  tests/test_cristexhub_prod_namespace_contract.py
sh -n ansible/bin/bootstrap-cristexhub-prod-namespace \
  tests/validate_cristexhub_prod_namespace_clean_controller.sh
bash -n tests/reject_cristexhub_prod_namespace_task_start.sh
git diff --check
git diff --cached --quiet
```

Actual result: **PASS RUNTIME** — 7 focused offline contract tests, YAML parsing,
Python compile, shell syntax, and diff hygiene pass. The approved check predicted
exactly `cristexhub-prod` at `ok=20 changed=1 failed=0 skipped=2`. First apply created
it (`changed=1`) before the historical post-check rejected Kubernetes' mandatory
`kubernetes.io/metadata.name` label. Read-only inspection found the Namespace
`Active` with exact intended labels plus that mandatory label. After correcting the
exact closure and using existing unprivileged `k3s-admin` access, a fresh check passed
at `ok=20 changed=0 failed=0 skipped=2`; separately approved idempotence passed at
`ok=22 changed=0 unreachable=0 failed=0 skipped=0`. No Secret, workload, PVC,
database, broker, Argo registration/sync, provider, DNS, or Cloudflare route was
created.
| KIF-MONGO-01 | KIF-002, KIF-005, KIF-018, KIF-021, KIF-023, KIF-030 | Guarded standalone MongoDB source closure | Exact hash-bound manifests define one standalone non-authoritative `shared-mongodb` StatefulSet with the pinned MongoDB digest, one replica, private ClusterIP, tokenless ServiceAccount, retained `80Gi` local-path RWO PVC template, exact resources/probes, no delete path, no Secret values, no public exposure, and default-deny/exact consumer ingress | PASS SOURCE-ONLY — focused source/architecture contracts, syntax, production lint, compile, and diff checks passed; no Secret, host, Kubernetes API, provider, Infisical, or runtime operation was accessed |
| KIF-MONGO-02 | KIF-002, KIF-005, KIF-013–KIF-015, KIF-021, KIF-023, KIF-030 | MongoDB official-entrypoint temporary-init TLS nuance | Final args include `--auth --tlsMode=requireTLS`, `--tlsCertificateKeyFile=/etc/mongodb/tls/tls.pem`, and `--tlsCAFile=/etc/mongodb/tls/ca.crt`; each probe authenticates through environment references without password argv and fails when a plaintext ping succeeds, so temporary loopback `allowTLS` cannot become Ready | PASS SOURCE-ONLY — focused contract checks final args, TLS Secret refs, explicit plaintext-negative probe logic, `allowTLS` documentation, and no plaintext value |
| KIF-MONGO-03 | KIF-018, KIF-019, KIF-021, KIF-023, KIF-026–KIF-030 | Future MongoDB plaintext/auth/authority negatives | A separately approved private runtime QA must reject plaintext MongoDB connections, invalid CA/hostname, bad credentials, cross-database access, workload user/role administration, and any attempt to claim replica-set transactions or authoritative data from this standalone pod | NOT RUN/BLOCKED — no Secret materialization, Kubernetes apply, client, backup/restore, negative runtime test, replica-set/transaction/HA decision, or authoritative-data acceptance exists |

## Standalone MongoDB guarded source closure — 2026-08-10

Commands:

```bash
.venv/bin/python -m unittest -v \
  tests.test_shared_mongodb_bootstrap_contract \
  tests.test_shared_database_architecture_contract
.venv/bin/python -m compileall -q ansible/plugins/action tests
cd ansible
../.venv/bin/ansible-playbook playbooks/bootstrap_mongodb.yml --syntax-check
../.venv/bin/ansible-lint --offline --profile production \
  playbooks/bootstrap_mongodb.yml roles/mongodb_bootstrap
cd ..
git diff --check
git diff --cached --quiet
```

Actual result:

```text
PASS — 17 focused MongoDB/database architecture tests
PASS — Python compile
PASS — MongoDB playbook syntax
PASS — production-profile lint: 0 failures, 0 warnings
PASS — diff check and no staged files
NOT RUN — wrapper check/apply, host, Kubernetes API, Secret values, PVC, Pod, or Service
```

| KIF-RCLONE-01 | KIF-002, KIF-005, KIF-007, KIF-013, KIF-030 | Guarded pinned host rclone installer | Exact official sums/archive/binary pins and five-file layout; controller cache and host transfer; Debian 13 x86_64; root-owned cache/version/selector; protected sudo prompt; check-safe; selector-only rollback; direct/task-selection/injection negatives | PARTIAL — after two historical pre-host-mutation stops and reviewed fixes, a fresh check passed at `ok=25 changed=1 failed=0`; the separately approved corrected install passed at `ok=34 changed=4 failed=0`, selected verified rclone `1.71.1`, and preserved k3s/Tailscale. The idempotence apply passed at `ok=32 changed=0 failed=0`; rollback remains NOT RUN |
| KIF-RCLONE-02 | KIF-002, KIF-005, KIF-013–KIF-015, KIF-027, KIF-030 | Exact pending encrypted proxy host transfer | Inventory/getent non-root operator without UID alias; exact selector/binary/config metadata; sole `drive:` remote and no-log read-only OAuth check; fixed timestamp/digest/destination; ciphertext-only mode-0700/0600 staging; four immutable copyto boundaries; encrypted readback/cleanup; controller verification and exact marker before Secret mutation | PARTIAL RUNTIME — private-tunnel host OAuth completed and check passed `ok=26 changed=0 failed=0`. Apply verified OAuth and created only exact encrypted staging, then stopped at `ok=25 changed=1 failed=1` before successful upload because pinned rclone rejects `--local-umask`; cleanup passed `ok=26 changed=1 failed=0` with zero staging residue. Reviewed retry passed `ok=39 changed=7` with immutable upload/readback, controller verification, exact cleanup and `drive-verified`; proxy Secret apply passed `ok=15 changed=1` |

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

## Guarded host rclone reconfirmed check, second stopped apply, and identity-binding fix — 2026-08-11

The exact wrapper check was reconfirmed before retrying mutation:

```text
crtxweb: ok=25 changed=1 unreachable=0 failed=0 skipped=11 rescued=0 ignored=0
```

The sole change was the bounded check-mode prediction. The subsequent approved apply
reused the canonical wrapper and protected become prompt. It created/downloaded only
the three exact ignored controller-cache leaves, then stopped before the first host
installer mutation:

```text
fatal: [crtxweb]: FAILED! changed=false
msg: MUTATION_ARGUMENT_GUARD: unsafe operator identity
crtxweb: ok=24 changed=2 unreachable=0 failed=1 skipped=0 rescued=0 ignored=0
```

Controller-cache post-state was one mode-`0700` directory with exact mode-`0600`
`SHA256SUMS`, archive, and extracted binary leaves. Git remained clean before the
source correction because that cache is ignored. No `/opt/rclone`,
`/var/cache/rclone`, `/usr/local/bin/rclone`, operator config, OAuth, Drive,
Kubernetes, or Secret mutation task ran in that attempt. At the operator's explicit direction for this bounded installer sequence, the existing ignored
`.env` value was supplied only to Ansible's no-echo become prompt by a controller-
local adapter; it was not placed in argv, Ansible variables/inventory, child process
environment, or output. This was a one-time exception to the repository's documented
interactive-entry rule, not a reusable source contract; future unattended password
handling requires a separately reviewed design.

Root cause: role defaults keep the operator as `{{ ansible_user }}`. The role's
ordinary assertions render that expression, but an action plugin reading the raw
`task_vars` entry can receive the unresolved template. The install action therefore
rejected its own valid operator before host mutation; the transfer sibling had the
same latent defect. Both roles now add the rendered operator to the already protected
attested preflight binding, and both guards consume only that field. The install
mutation guard additionally binds the home exactly to `/home/<operator>`. Regression
coverage exercises the host-directory guard with a deliberately raw task-var default
and a rendered protected binding.

Validation:

```bash
uv run --offline python -m unittest -v tests.test_rclone_host_contract
uv run --offline python -m unittest discover -s tests -v
cd ansible
for playbook in playbooks/*.yml; do
  ../.venv/bin/ansible-playbook -i .ansible/inventory.local.yml \
    "$playbook" --syntax-check
done
../.venv/bin/ansible-lint --offline --profile production .
cd ..
python3 -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/install-rclone ansible/bin/transfer-infisical-proxy-recovery \
  tests/reject_rclone_task_start.sh
git diff --check
git diff --cached --quiet
```

Actual result: the focused contract passed `9/9`; after the related logical-helper
regression below, the full suite passed `256/256`;
all `23/23` playbooks passed syntax; production lint passed `162` processed files
with zero findings; compile, shell syntax, diff, and no-staged-files checks passed.
Independent dependency review also found one stale Universal Auth runbook sentence
that required schema 1 while the executable role, report template, and tests require
schema 2. The runbook now says schema 2; no executable Secret gate was changed.

Independent review approved the identity fix without a blocker. The corrected live
result is recorded in the next subsection. OAuth, transfer, proxy Secret, Infisical,
Argo CD, PostgreSQL, MongoDB, logical provisioning, and every later runtime gate
remain blocked.

## Guarded host rclone corrected install — 2026-08-11

After independent source review, the canonical check was run again through the
protected no-echo become prompt:

```text
crtxweb: ok=25 changed=1 unreachable=0 failed=0 skipped=11 rescued=0 ignored=0
```

Its sole change was the bounded check-mode prediction. The separately approved
corrected install then passed:

```text
crtxweb: ok=34 changed=4 unreachable=0 failed=0 skipped=2 rescued=0 ignored=0
```

The four changes were limited to the guarded host closure: exact cache/config parent
preparation, transfer of the already verified archive, extraction of the pinned
binary, and selection of `/usr/local/bin/rclone`. Exact post-state and version
`1.71.1` assertions passed, as did post-install k3s/Tailscale service checks.
Controller cache preparation/download checks converged without change. The same
controller-local adapter read the ignored mode-`0600` `.env` key only into memory and
sent it solely to the no-echo prompt; the value did not enter argv, inventory,
Ansible variables, child environment, or evidence. No OAuth, Drive transfer, proxy
ciphertext staging, Kubernetes, Secret, Infisical, Argo, or database task ran.
The separately approved installer idempotence apply then passed:

```text
crtxweb: ok=32 changed=0 unreachable=0 failed=0 skipped=4 rescued=0 ignored=0
```

Exact artifact, selector, version `1.71.1`, and k3s/Tailscale post-state checks passed
again without change. The following canonical read-only transfer check stopped safely
at the expected host OAuth boundary:

```text
crtxweb: ok=15 changed=0 unreachable=0 failed=1 skipped=0 rescued=0 ignored=0
failure: missing or unsafe operator OAuth config metadata
```

It failed before `listremotes`, OAuth, Drive access, staging, transfer, or controller
readback.

## Guarded host OAuth, transfer stop, and exact cleanup — 2026-08-11

Host OAuth completed through a temporary private SSH callback tunnel using the exact
non-root host config. Pinned rclone `1.71.1` does not implement the previously
documented `--auth-no-open-browser` flag; the successful no-output flow used
`config create drive drive config_is_local=true --no-output`. Only Google browser
consent was human; config/token content was not logged or copied. Temporary local
session files and the tunnel were removed.

The next canonical transfer check passed without mutation:

```text
crtxweb: ok=26 changed=0 unreachable=0 failed=0 skipped=14 rescued=0 ignored=0
```

The approved apply verified OAuth, prepared only the exact mode-`0700` encrypted host
staging/readback closure with mode-`0600` source leaves, then stopped at its first
upload:

```text
crtxweb: ok=25 changed=1 unreachable=0 failed=1 skipped=0 rescued=0 ignored=0
failure: pinned rclone rejected unsupported --local-umask before successful upload
```

No successful Drive upload or readback is evidenced. Cleanup check passed at
`ok=24 changed=1 failed=0`; the approved cleanup apply passed at
`ok=26 changed=1 failed=0`, removed only the exact timestamped host staging root,
and preserved k3s/Tailscale health. Controller pending ciphertext/checksum remain
unchanged; no Secret or Kubernetes mutation ran.

Source removes the unsupported flag. After each successful readback, the guarded
action immediately protects the exact leaf at mode `0600`; its ancestor remains
mode `0700`, so no other user can traverse the directory during the bounded interval.
The focused contract executes all four exact argv arrays, proves both simulated
readback leaves move from mode `0644` to `0600`, and proves upload operations receive
no file-mode action. Independent review approved the correction without blockers.
Offline validation passed `10/10` focused and `257/257` full contracts, all `23/23`
playbook syntax checks, production lint over 162 files, compile, shell, and diff
checks. The mandatory fresh transfer check was then attempted, but stopped before
facts at `ok=0 changed=0 unreachable=1` because SSH/Tailscale reachability to the host
timed out. No mutation ran in that invocation.

## Transfer/proxy Secret completion and Infisical Operator runtime — 2026-08-11

After the host returned, the fresh transfer check again passed at
`ok=26 changed=0 failed=0`. The approved retry passed:

```text
crtxweb: ok=39 changed=7 unreachable=0 failed=0 skipped=1 rescued=0 ignored=0
```

The seven changed tasks were exact encrypted staging, two immutable uploads, two
immutable readbacks, fetch of ciphertext-only readback, and exact staging cleanup.
Controller ciphertext/checksum equality, age decrypt, archive closure, TLS/key/auth
relationships, mode-`0600` `drive-verified`, protected host OAuth config, zero host
staging residue, and k3s/Tailscale health passed. No plaintext or age identity moved
to the host. The guarded proxy Secret apply then passed:

```text
crtxweb: ok=15 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

It created exactly `infisical-egress-proxy-tls`, `infisical-egress-proxy-auth`, and
`infisical-egress-proxy-client` in `shared-services` without value output. A later
invocation refused implicit credential rotation before Ansible/Kubernetes.

The first Operator check stopped before mutation at `ok=5 changed=0` because defaults
used unrendered absolute template strings as hash-map keys. Relative 40-key hashes
fixed that stop. The next check stopped before mutation at `ok=20 changed=0` because
CLI `key=true` produced a string while the action guard requires the exact boolean.
The wrapper now passes JSON `true`; both fixes passed focused validation and
independent review. Final results:

```text
check:       crtxweb: ok=24 changed=2 unreachable=0 failed=0 skipped=5
first apply: crtxweb: ok=29 changed=2 unreachable=0 failed=0 skipped=0
idempotence: crtxweb: ok=29 changed=0 unreachable=0 failed=0 skipped=0
```

Check mode predicted the CRD and runtime partitions without mutation. First apply
created/reconciled exactly the historical 40-object idle closure; all six CRDs became
Established, all exact post-state labels passed, both Deployments became Available,
and k3s/Tailscale remained healthy. Idempotence converged at `changed=0`. No Infisical
CR, Universal Auth credential, Argo/database target Secret, database, PVC, or public
route was created. The later 42-object source was not separately runtime-applied.
A subsequent checkpoint, recorded above, applied the 44-object expansion and passed
idempotence. Broader admission/RBAC/traffic negatives and recovery acceptance remain
pending. Final source validation passed
`16/16` focused Operator contracts, `258/258` full contracts, all `23/23` playbook
syntax checks, production lint over 162 files, compile, shell syntax, diff, and
no-staged checks.

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

At this historical pre-import checkpoint, `tofu fmt` and `tofu validate` were NOT
RUN: no controller OpenTofu binary was approved or installed, and provider
initialization/download was a later gate. The HCL was statically checked and
conventionally formatted, but that was not provider-aware validation. The original
host check, bounded failure, reviewed controller-transfer recovery, and idempotence
evidence are recorded below. At that checkpoint, lockfile generation, state creation
and encryption, off-node copy/restore, plan, and apply remained NOT RUN/BLOCKED;
later protected-state backup/readback and isolated restore evidence is recorded in
the current checkpoint.

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
    "At the historical pre-import checkpoint, provider initialization, state, plan, and\napply also remained unrun",
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
At this historical 2026-08-08 checkpoint, the then-current four Namespace
manifests were unchanged; this predates the later separate `cristexhub-prod`
source-only manifest and must not be read as current live Namespace evidence.
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

## Reactive Resume DEV blocker inventory hardening — 2026-08-21

The canonical Reactive Resume policy now records the live private DEV checkpoint
separately from full acceptance: seven Argo manifests including default-deny, private
Traefik route, materialized CA, runtime Secret `reactive-resume-dev-runtime`, selected
DEV digests, and successor PostgreSQL scope `reactive_resume_dev_successor`. Image
provenance/promotion, OIDC/database ACLs, data-only recovery with separate role/ACL/
credential custody, TLS renewal, soak, PROD, and public route remain blocked. It explicitly blocks reuse of the broad Infisical
11-target/VAP/RBAC lanes and all-consumer PostgreSQL/CloudNativePG lanes, and records
successor-realm runtime, required OIDC/local-auth source patch, CNPG
TLS/NetworkPolicy identity, private durable object storage, disabled v5 Agent/Redis
scope, application-key custody, locked split-role migration, backup, restore,
measured RPO/RTO, and DEV-soak gates. A read-only candidate record now binds Docker
Hub `v5.2.7` metadata while explicitly rejecting promotion because the image revision
is 16 commits/150 files beyond the annotated release tag. PROD remains a
reservation/template only. No manifest, workload, wrapper, Secret value, selected
image, PVC, route, or API/provider source was added.

```bash
.venv/bin/python -m unittest -v \
  tests.test_reactive_resume_architecture_contract
.venv/bin/python -m unittest discover \
  -s tests -p 'test_*.py' -q
cd ansible && for f in playbooks/*.yml; do \
  ../.venv/bin/ansible-playbook "$f" --syntax-check >/dev/null || exit; done
../.venv/bin/ansible-lint . ../tests/validate_storage_report.yml
cd ..
.venv/bin/python -m compileall -q \
  tests/test_reactive_resume_architecture_contract.py
git diff --check
git diff --cached --quiet
set -eu
inventory="$(kubectl get deployments,statefulsets,services,ingresses,networkpolicies,pvc,serviceaccounts,configmaps \
  -n cristexhub-dev -o name)"
argo_inventory="$(kubectl get applications.argoproj.io -n argocd -o name)"
matches="$(printf '%s\n' "$inventory" | grep -Ei 'reactive|resume|rxresume' || true)"
argo_matches="$(printf '%s\n' "$argo_inventory" | grep -Ei 'reactive|resume|rxresume' || true)"
test -z "${matches}${argo_matches}"
```

Actual result:

```text
Reactive Resume focused architecture tests: 16 passed
Reactive Resume PostgreSQL exposure-rotation contract tests: 9 passed
Full offline suite: 452/452 passed
All 47 playbook syntax checks passed
Production-profile lint passed with only 14 configured pre-existing warnings
Python compile: passed
Diff hygiene passed; bounded read-only Kubernetes inventory found
reactive_resume_matching_application_or_argo_object_count=0; separate safe metadata discovery found the broad-lane DEV/PROD PostgreSQL Database/DatabaseRole CRs and credential Secrets live but unaccepted, with zero NetworkPolicies selecting shared PostgreSQL; no Reactive Resume or provider mutation occurred
```

The DEV runtime remains blocked pending dedicated source lanes, a reproducibly bound
and directly attested image, patched PKCE/token-validation/local-auth/account-linking/
logout behavior, successor realm, canonical PostgreSQL owner/NOINHERIT/ACL and
negative tests, CNPG-compatible TLS/NetworkPolicy, authenticated private object
storage and backup/restore, application-key recovery, a locked migration Job with a
DDL-free runtime role, measured RPO/RTO, private validation, and an explicit DEV
soak. PROD cannot be generated or activated from its reservation.

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
Kubernetes source: PASS, exactly five persistent Namespace manifests including `cristexhub-prod`; historical pre-checkpoint source evidence recorded the live PROD Namespace absent, while the current Namespace checkpoint is Active/idempotent
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
ANSIBLE_COLLECTIONS_PATH=/home/paul/.ansible/collections \
  .venv/bin/python -m unittest -v \
  tests.test_infisical_operator_bootstrap_contract \
  tests.test_infisical_operator_implementation_profile_contract \
  tests.test_infisical_cristexhub_prod_runtime_contract
PASS: 31 focused source/profile/PROD contracts

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
PASS: 44 single-document objects; exact kind/name/namespace closure; zero Secret,
ClusterRole, ClusterRoleBinding, ClusterGenerator, metrics Service, route, or PROD
workload/value object

CRD source mapping and MANIFESTS.sha256
PASS: six promoted namespaced CRDs map to exact hash-bound chart templates; all 44
manifest hashes match; action guard contains 44 canonical object hashes

Markdown links/hygiene and git diff --check
PASS: documentation links resolve, no trailing whitespace, no staged files
```

The source selects six CRDs, six `failurePolicy: Fail` admission policies and six
Deny bindings, five manager Roles/Bindings, exact leader-election RBAC, two
ServiceAccounts, one authenticated TLS Squid ConfigMap/Service/Deployment, one
metrics-off Operator Deployment, and eight NetworkPolicies. The controller watches
exactly `shared-services`, `argocd`, `cristexhub-dev`, `cristexhub-prod`, and
`platform-edge`; ClusterGenerator, review/token permissions, metrics, direct
Internet 443, self-hosted Infisical, PROD values, and PROD workloads remain absent.

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
The failed controller-rclone path is now superseded. Host rclone install/idempotence
pass, and host OAuth now passes. Remaining recovery-write blockers are encrypted transfer/readback,
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
| KIF-ARGO-07 | KIF-005, KIF-013–KIF-015 | Infisical-owned precreated Secrets | Source has zero Secret objects/values; exact three names/types/keys/labels and cryptographic value validity required; initial-admin Secret absent | PASS OFFLINE — no-log exact-scope validator requires bcrypt structure/cost, strict UTC timestamp, key lengths, parseable current direct-CA TLS chain, exact server identity closure, non-CA leaf, server usage, and matching leaf/key; cost, noncanonical/malformed-time, unrelated-key, extra-SAN, and CA-leaf negatives pass; materialization/recovery NOT RUN |
| KIF-ARGO-08 | KIF-002, KIF-005, KIF-030 | Non-passthrough guarded mutation | Only check/apply wrapper, private attestation, canonical task source, exact canonical hashes, present-only, foreign-object refusal, task-selection/injection negatives | PASS OFFLINE — wrapper approval is native boolean; direct valid-attestation action and combined start-at-task/injection fail closed before Kubernetes; default-role smoke reaches only host prerequisites |
| KIF-ARGO-09 | KIF-002, KIF-010, KIF-012, KIF-015 | Live check/apply/readiness/idempotence/private login/recovery | Separate reviewed check, first apply, Ready/TLS/login/traffic negatives, Git read, second apply changed=0, recovery | NOT RUN/BLOCKED — requires exact Infisical-owned Secrets and parent approvals |
| KIF-ARGO-10 | KIF-005, KIF-008, KIF-010, KIF-021 | Empty-install default project startup | A committed `AppProject/default` exists before workloads, denies every source/destination/resource, server/controller may read it, neither can mutate projects, first check tolerates absent discovery without mutation, and apply waits for Established CRDs | PASS OFFLINE — exact deny-all project, non-mutating project RBAC, one-object check deferral, and CRD wait contract are hash/task-bound; live startup remains part of KIF-ARGO-09 |

## Argo CD v3.5.0 server TLS API-consumption regression — 2026-08-10

This source-only regression closes the false finding that `argocd-server-tls` must
be mounted into the server Pod. Official Argo CD `v3.5.0` settings code reads that
Secret through the Kubernetes API and caches the parsed certificate by Secret
`resourceVersion`; the committed server Role already grants read-only Secret access.
The mounted `argocd-tls-certs-cm` ConfigMap is separately documented and tested as
the repository trust CA store. No manifest, Secret, host, cluster, Kubernetes API, or
runtime behavior changed.

Commands:

```bash
.venv/bin/python -m unittest -v \
  tests.test_argocd_hardened_design_contract.ArgoCdHardenedDesignContractTests.test_server_tls_secret_is_api_loaded_and_ca_configmap_is_distinct
# The focused command used the existing controller `.venv` outside the isolated
# worktree because ignored environments are not copied into worktrees.
git diff --check
git diff --cached --quiet
```

Actual result:

```text
PASS — 1 focused API-consumption/ConfigMap-distinction contract
PASS — git diff --check
PASS — no staged files
NOT RUN — host, cluster, Kubernetes API, Secret values, and runtime access
```

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-ARGO-11 | KIF-005, KIF-008, KIF-013, KIF-021, KIF-030 | Argo server external TLS wiring | Official v3.5.0 API-based `argocd-server-tls` loading is documented; Deployment has no server-TLS Secret volume; server Role has only Secret `get/list/watch`; `argocd-tls-certs-cm` remains the repository trust CA ConfigMap; exact 32-object closure is unchanged | PASS OFFLINE — focused regression and diff checks passed; runtime remains NOT RUN/BLOCKED |

## Autonomous workflow policy — 2026-08-10

Commands:

```bash
grep -nE "research → plan → implement → test → review → fix → next task|six concurrently running subagents|gpt-5.6-luna|thinking=max|own git worktree|fastest reversible solution" AGENTS.md
git diff --check
```

Actual result: **PASS** — `AGENTS.md` records the full recurring task loop,
autonomous unblocking, the six-subagent floor, required model and max thinking, isolated worktrees,
iteration-speed priority, and the bounded one-time operational exception. The
exception explicitly preserves all infrastructure Safety gates and operator approvals.

## Infisical Argo CD Secret materialization seam source-only validation — 2026-08-10

The source-only seam validation used the isolated controller worktree and the
locked offline `.venv`. It did not use inventory, SSH, become, kubeconfig,
Kubernetes API, Infisical API, credentials, Secret values, provider state, check,
apply, or runtime mutation. The preceding 42-object idle Infisical closure was not
changed by that historical seam validation; the later 44-object expansion was
subsequently applied/idempotent as documented above. The seam source freezes Connection `infisical-cloud`, Auth
`argocd-infisical-auth`, StaticSecret `argocd-infisical-secrets`, credential
Secret metadata `argocd/argocd-infisical-universal-auth`, project slug
`cristexweb-infrastructure`, Infisical environment `prod`, path `/argocd`, and exactly
seven non-secret source key names. The Infisical `prod` slug does not activate the
Kubernetes `cristexhub-prod` Namespace or PROD workloads/routes.

```bash
uv sync --locked --offline
.venv/bin/python -m unittest -v tests.test_infisical_argocd_secrets_contract
cd ansible
../.venv/bin/ansible-playbook -i localhost, playbooks/bootstrap_infisical_argocd_secrets.yml --syntax-check
../.venv/bin/ansible-lint --offline --profile production playbooks/bootstrap_infisical_argocd_secrets.yml roles/infisical_argocd_secrets_bootstrap
set -e; for playbook in playbooks/*.yml; do ../.venv/bin/ansible-playbook -i localhost, "$playbook" --syntax-check; done
../.venv/bin/ansible-lint --offline --profile production .
cd ..
.venv/bin/python -m compileall -q tests ansible/plugins/action
for script in ansible/bin/*; do sh -n "$script"; done
for script in tests/*.sh; do bash -n "$script"; done
git diff --check
git diff --cached --quiet
```

Actual results:

```text
Ran 10 focused Infisical Argo CD Secret seam contracts — OK
PASS: source and canonical object hash checks, including updated CEL/source options
PASS: new seam syntax check
PASS: focused production-profile ansible-lint (0 failures/warnings in 4 files)
PASS: all 16 production playbook syntax checks
PASS: production ansible-lint (0 failures/warnings in 95 files processed of 117 encountered)
PASS: Python compile, shell syntax, git diff check, and no staged files
PASS: direct seam action-only, forged-internal, and task-selection fixtures fail before Kubernetes
```

The broad offline suite ran 201 tests; 200 passed and one pre-existing Argo
`reject_argocd_task_start.sh` validator could not pass from the isolated temporary
worktree because the repository's existing action guard intentionally pins the
canonical controller task path. This is a worktree-path validation limitation, not
a seam failure; the parent checkout must rerun the full suite after integration.
The new seam's action-only, forged-internal, and task-selection fixtures passed in
this worktree. Runtime remains **NOT RUN/BLOCKED**. Human creation of the
credential/source identifiers, Infisical authentication, target sync and values,
Argo readiness, idempotence, rotation, recovery, and live admission/RBAC negative
tests remain open approvals.

## Integrated database closures and Infisical seam — 2026-08-10

This canonical-checkout validation covered the final value-free PostgreSQL,
standalone MongoDB, shared cryptographic Secret validator, and Infisical-to-Argo
Secret materialization seam. It used no inventory connection, SSH, become,
kubeconfig, Kubernetes/Infisical/provider API, Secret value, PVC, or database. No
check/apply/idempotence or live runtime claim is made.

Commands:

```bash
.venv/bin/python -m unittest -v \
  tests.test_stateful_database_secret_contract \
  tests.test_shared_mongodb_bootstrap_contract \
  tests.test_postgresql_bootstrap_contract
.venv/bin/python -m unittest -v \
  tests.test_infisical_argocd_secrets_contract \
  tests.test_infisical_database_secrets_contract
.venv/bin/python -m unittest discover -s tests -v
cd ansible
for playbook in playbooks/*.yml; do ../.venv/bin/ansible-playbook "$playbook" --syntax-check; done
../.venv/bin/ansible-lint --offline --profile production
cd ..
.venv/bin/python -m compileall -q ansible/plugins/action tests
for script in ansible/bin/*; do sh -n "$script"; done
for script in tests/*.sh; do bash -n "$script"; done
git diff --check
git diff --cached --quiet
```

Actual results:

```text
PASS: 20 focused PostgreSQL/MongoDB/Secret-validator tests
PASS: 10 focused Infisical-to-Argo seam tests plus 7 focused Infisical database seam tests
HISTORICAL PARTIAL OFFLINE: isolated-worktree suite — 229 tests, 226 passed; three path-limited fixtures failed in that temporary worktree. This evidence was superseded by the then-final primary-worktree 253/253 result below, which is itself superseded by the current 258/258 result later in this file.
HISTORICAL PASS: all 18 then-existing playbook syntax checks; superseded by the final 23/23 result below.
PASS: production ansible-lint — 0 failures, 0 warnings; 135 files processed of 163 encountered
PASS: Python compile and shell syntax
PASS: git diff --check and no staged files
PASS: database seam cross-policy tests prove Argo VAP contains no database target names, database VAP contains no Argo target names, and both Secret VAPs use namespace plus operator-or-target match conditions with operator-only exact validation
NOT RUN/BLOCKED: every host, cluster, Secret, PVC, database, Infisical, Argo, check/apply/idempotence, backup/restore, and runtime operation
```

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-DBI-01 | KIF-005, KIF-013, KIF-019, KIF-021, KIF-023 | Exact database object closures | PostgreSQL has six and MongoDB five unique value-free hash-bound objects with exact immutable image identities | PASS OFFLINE — ledger/default/action canonical hashes agree |
| KIF-DBI-02 | KIF-013–KIF-015, KIF-021 | Exact precreated Secret values | Canonical-task-bound no-log validation rejects wrong identity/type/keys/labels, short credentials, malformed/ambiguous/encrypted PEM, non-current or weak CA/leaf keys, wrong CA constraints/signature, missing or extra SAN kinds, wrong EKU, forged issuance, and key mismatch | PASS OFFLINE — six validator contracts including both valid engines and negative matrix |
| KIF-DBI-03 | KIF-016, KIF-019, KIF-021 | PostgreSQL final-state readiness | `shared-postgresql` uses SCRAM-SHA-256, authenticated `verify-full` probes proving `pg_stat_ssl.ssl=t`, plaintext-negative probes, exact localhost/service SANs, and private 5432 policy including exact same-Namespace Keycloak selection | PASS OFFLINE — structural/probe contracts; runtime NOT RUN |
| KIF-DBI-04 | KIF-016, KIF-018, KIF-019, KIF-021 | MongoDB final-state readiness | Standalone MongoDB requires TLS and SCRAM-SHA-256, explicitly permits certificate-less TLS clients rather than distributing client keys, proves authenticated CA-validated TLS, and rejects plaintext | PASS OFFLINE — structural/probe contracts; runtime NOT RUN |
| KIF-DBI-05 | KIF-010, KIF-019, KIF-021 | Drift and private exposure | Pre/post checks reject foreign or dangerous Service, NetworkPolicy, ServiceAccount, and StatefulSet drift; Services remain one-port ClusterIP-only with no public fields | PASS OFFLINE — source checks and production lint; live drift NOT RUN |
| KIF-DBI-06 | KIF-019, KIF-026–KIF-028 | Generated retained PVC safety | Exact generated names, ownership labels, no data source/selector, `local-path`, `Filesystem`, `ReadWriteOnce`, 40/80 GiB, bound PV claim UID/name/namespace, and local-path provisioner are checked before reuse and after binding; no PVC/delete source exists | PASS OFFLINE — foreign-PVC guards present; storage runtime NOT RUN |
| KIF-DBI-07 | KIF-002, KIF-005, KIF-030 | Present-only mutation boundary | Non-passthrough wrappers, private attestations, exact task source/argument/hash/identity bindings, and task-selection/action-only/internal-injection negatives fail closed | PASS OFFLINE — negative fixtures stop before Kubernetes |
| KIF-INF-SEAM-11 | KIF-005, KIF-013–KIF-015, KIF-021, KIF-023, KIF-030 | Integrated exact Infisical-to-Argo seam | Thirteen value-free objects constrain one Connection/Auth/StaticSecret, exact three orphan targets, four VAP/four bindings, exact source options, all-existing StaticSecret/alternate-target preflight, immutable-target rejection, additive RBAC, effective admission, and actual v0.11.7 readiness conditions | HISTORICAL PASS OFFLINE — 10 focused plus the then-final 253/253 primary-worktree suite; superseded by 258/258 below; live sync NOT RUN |
| KIF-INF-SEAM-12 | KIF-005, KIF-013–KIF-015, KIF-021, KIF-023, KIF-030 | Exact Infisical database Secret seam | Fifteen value-free objects constrain one shared Connection, separate PostgreSQL/MongoDB Auth and credential identities, two fixed path StaticSecrets, eleven target contracts, eight VAP/binding objects, namespace-scoped operator-or-target match conditions, operator-only exact validation, additive no-delete/no-workload-write RBAC, all-existing StaticSecret/alternate-target preflight, byte/canonical/identity hashes, and action-only/internal/task-selection negatives | HISTORICAL PASS OFFLINE — 9 focused plus the then-final 253/253 primary-worktree suite; superseded by 258/258 below; credential sync, target values, and runtime NOT RUN/BLOCKED |
| KIF-DBI-08 | KIF-026–KIF-030 | Runtime, authorization, recovery, handoff, and production acceptance | Separate approvals and live evidence prove check/apply/idempotence, trust/pullability, Secret sync/rotation, TLS/auth, NetworkPolicy, logical isolation, backup/restore, Argo handoff, and authoritative-data decisions | NOT RUN/BLOCKED |

## Source-only logical provisioning lane — offline contract

The following source-only lane was added without host, cluster, Infisical, database,
Secret, PVC, backup, restore, or provider access:

```text
ansible/bin/provision-shared-postgresql check|apply
ansible/bin/provision-shared-mongodb check|apply
```

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-DBP-01 | KIF-017, KIF-021, KIF-030 | Frozen logical identities | Five PostgreSQL database/owner pairs and two MongoDB database/user pairs match the canonical policy; every scope is an empty reservation and PROD is inactive | PASS OFFLINE — policy/defaults/tests assert exact maps; runtime NOT RUN |
| KIF-DBP-02 | KIF-013–KIF-015, KIF-017 | Infisical consumer credential seam | Exact precreated `Opaque` Secrets contain only `username`/`password`, carry Infisical ownership labels, and values are never generated or passed in argv | PASS OFFLINE — role preflight and source tests; materialization/runtime NOT RUN |
| KIF-DBP-03 | KIF-017, KIF-021, KIF-030 | Native logical authorization | PostgreSQL own-scope positives, cross-database and CREATE DATABASE/ROLE negatives; MongoDB own-scope positives, bidirectional cross-database and user/role-administration negatives | PASS OFFLINE — fixed scripts and runbook contract; live authorization NOT RUN |
| KIF-DBP-04 | KIF-002, KIF-005, KIF-026, KIF-030 | Helper lifecycle safety | Temporary digest-pinned tokenless Pod and exact NetworkPolicy are cleaned by UID precondition with zero residue; no database/user/PVC delete path exists | PASS OFFLINE — action guards/roles reject foreign and stale helpers; runtime NOT RUN |
| KIF-DBP-05 | KIF-017, KIF-026–KIF-030 | Promotion and recovery gates | MongoDB remains standalone/non-authoritative; backup, isolated restore, RPO/RTO, Argo handoff, runtime, trust, and production activation remain blocked | PASS OFFLINE — docs/policy retain false gates; NOT RUN/BLOCKED |

## Logical provisioning helper guard closure correction — 2026-08-11

Read-only deployment audit found three independent fail-closed stops before database
or helper-Pod mutation. `database_provisioning_guarded_k8s.py` still embedded
superseded apply-script hashes even though the executable scripts, execution guard,
and role defaults agreed on the current digests. It also required exact
`username`/`password` item projection for every credential Secret, while only the
MongoDB helper definitions supplied those items. PostgreSQL supplied only
`secretName` and `defaultMode`, so its otherwise exact helper could not pass the
mutation guard. Finally, Ansible's file lookup strips trailing whitespace by default,
while both guards bind the exact script bytes including the final newline; all four
check/apply lookup expressions therefore needed explicit `rstrip=False`.

The Kubernetes guard now pins the actual current apply-script SHA-256 values:

```text
postgresql-apply.sh 08a98b5796c2be31d63c6b47e391aaed741bb6620023cc22e3af6abe514cbc4a
mongodb-apply.sh    571301f932cd2a36d40813313c9da077380114452542cd622e0d6d379a4990f6
```

All six PostgreSQL credential volumes now project only `username` and `password`,
matching the existing guard and MongoDB pattern. Both check/apply lookups for each
engine preserve the complete source with `rstrip=False`. A new executable unit
regression loads each exact role helper definition, substitutes only its already-
pinned rendered image/script values, requires `_valid_pod` success, removes one
credential `items` closure, and requires fail-closed rejection. It also requires all
four non-stripping lookups. The existing hash test now parses and compares the
Kubernetes guard's embedded apply hashes to role defaults and actual script bytes.

```bash
uv run --offline python -m unittest -v \
  tests.test_shared_database_provisioning_contract
```

Actual result: `7/7` focused contracts passed. No host, Kubernetes API, Infisical,
database, Secret, PVC, network, or provider action ran. Logical check/apply,
idempotence, authorization, backup/restore, and all stateful runtime approvals remain
**NOT RUN/BLOCKED**.

## Final integrated source validation — 2026-08-11

Commands:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
cd ansible
for playbook in playbooks/*.yml; do ../.venv/bin/ansible-playbook "$playbook" --syntax-check; done
../.venv/bin/ansible-lint --offline --profile production
cd ..
ANSIBLE_CONFIG="$PWD/ansible/ansible.cfg" .venv/bin/ansible-playbook -i localhost, tests/validate_k3s_datastore_preflight_parser.yml
.venv/bin/python -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/*
bash -n ansible/files/database-provisioning/*.sh tests/*.sh
git diff --check
git diff --cached --quiet
```

Actual results:

```text
PASS: 258/258 offline Python contracts in the primary worktree
PASS: all 23/23 playbook syntax checks
PASS: production ansible-lint — 0 failures, 0 warnings; 162 files processed of 198 encountered
PASS: executable k3s datastore parser fixtures — ok=140 changed=0 failed=0
PASS: Python compile, shell syntax, and git diff --check
PASS: no staged files
NOT RUN/BLOCKED: live k3s datastore/encryption preflight, recovery attestation, Infisical API/identity/value work, Kubernetes Secret writes, Argo/database apply, PVC/database provisioning, backup/restore, PROD activation/traffic, and acceptance
```

This result supersedes the historical temporary-worktree 229/226 partial result and
the then-current 18-playbook syntax count. It validates source only and does not
supply any runtime approval or recovery evidence.

### Post-review fail-closed remediation

After independent review, source now additionally rejects unsafe/multiply-linked
preflight destinations and writable output ancestors, malformed split encryption
status, incomplete preflight invocation/health/disclosure evidence, inherited curl
configuration/environment, non-exact archive manifests, unverified persisted upload
key closure, and unreviewed Infisical-owned database target identities.

```text
PASS: 24 focused preflight/Universal-Auth/database-seam contracts
PASS: executable parser fixture including empty-header plus separate Status negative
PASS: 3 affected playbook syntax checks
PASS: production-profile focused lint — 0 failures, 0 warnings; 14 files processed
PASS: shell syntax and git diff --check
```

Final review follow-up corrected the preflight-to-seed executable stage binding from
`available` to the emitted `safe` value, requires exactly one enabled rotation-stage
line, and narrows Infisical login/metadata/upload parsing to exact response fields with
a positive integer `revision`. The 15 focused preflight/Universal-Auth contracts, two
affected playbook syntax checks, executable parser (`ok=140`), focused production
lint, shell syntax, and diff check pass; live vendor compatibility remains blocked.

## First live k3s datastore preflight attempt — 2026-08-11

Approved command:

```bash
ansible/bin/preflight-k3s-datastore check
```

Actual result:

```text
PLAY RECAP: ok=1 changed=0 unreachable=0 failed=1 skipped=0
Failure: ansible_become evaluated false before collection.
Artifact: absent.
```

The wrapper asked for the become password but had not enabled become explicitly. The
role's fail-closed invocation gate stopped before every datastore, encryption,
Kubernetes, and service probe. No host, datastore, cluster, Secret, backup, restore,
or encryption mutation occurred. The first correction added `--become` but also injected highest-precedence
`ansible_become: true`. A second approved read-only attempt reached the protected
controller-local attestation check, where that extra variable incorrectly overrode
task-level `become: false` and attempted local sudo. It stopped at `ok=3 changed=0
unreachable=0 failed=1 skipped=0`; no artifact or remote collection was produced and
no host, datastore, cluster, Secret, backup, restore, or encryption mutation occurred.

The final correction retains wrapper `--become --ask-become-pass` and play-level
`become: true`, removes the nonexistent task-variable gate and unsafe extra-variable
override, and verifies every controller-local delegated task remains `become: false`.

Corrected-source validation:

```bash
.venv/bin/python -m unittest -v tests.test_k3s_datastore_preflight_contract
sh -n ansible/bin/preflight-k3s-datastore
cd ansible
../.venv/bin/ansible-playbook playbooks/preflight_k3s_datastore.yml --syntax-check
../.venv/bin/ansible-lint --offline --profile production roles/k3s_datastore_preflight playbooks/preflight_k3s_datastore.yml
cd ..
git diff --check
```

Actual result: all 8 focused contracts passed, the affected playbook syntax check
passed, production lint processed 6 files with zero findings, shell syntax and diff
checks passed, and independent review returned **APPROVED**.

## Successful live read-only k3s datastore preflight — 2026-08-11

Approved command:

```bash
ansible/bin/preflight-k3s-datastore check
```

Actual result:

```text
PLAY RECAP: ok=45 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
Artifact: ansible/.ansible/k3s-datastore-preflight.local.json
Artifact SHA-256: cef563e8d81f4b8feb892c1b2e107b21fa93ad7f125d2c5864162d782aa34b46
Artifact metadata: controller-owned regular file, mode 0600, one hard link
```

The sole change was the ignored sanitized controller artifact. It reported k3s
`v1.36.2+k3s1`, safe executable/config metadata, running k3s/Tailscale, and one Ready
node, while correctly retaining `config_override_unknown`, datastore `unknown`,
encryption command/status `unknown`, and rotation `unknown`. No raw config, command
output, endpoint, node identity, token, key, Secret value, backup, restore, host,
cluster, datastore, or encryption mutation entered the artifact or evidence.

## Private config and official encryption-JSON parser enhancement — 2026-08-11

Enhanced source emits schema v2 so the Universal Auth gate rejects the earlier
schema-v1 runtime artifact and all pre-enhancement evidence. The source is pinned to
official K3s tag `v1.36.2+k3s1`, commit
`01b6f04aaa69e8b09303f0393d4b4f1811da23aa`. Fixed argv now requests
`secrets-encrypt status --output json`. The role privately reads only the bounded,
stable, single-link root-owned `config.yaml`, validates selected top-level fields,
projects booleans/enums only, and clears raw facts before report construction.
Official stage `start` maps only to `initial`; only `reencrypt_finished` with
`hashmatch=true` maps to `finished`. Universal Auth continues to require `finished`
plus separately attested backup, key recovery, and isolated restore.

Validation commands:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -q
ANSIBLE_CONFIG="$PWD/ansible/ansible.cfg" .venv/bin/ansible-playbook -i localhost, tests/validate_k3s_datastore_preflight_parser.yml
cd ansible
for playbook in playbooks/*.yml; do ../.venv/bin/ansible-playbook "$playbook" --syntax-check; done
../.venv/bin/ansible-lint --offline --profile production
cd ..
.venv/bin/python -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/*
bash -n ansible/files/database-provisioning/*.sh tests/*.sh
git diff --check
git diff --cached --quiet
```

Historical actual result for this preflight revision, superseded by the current
258/258 and 162-file integrated result recorded earlier:

```text
HISTORICAL PASS: 253/253 offline Python contracts
PASS: executable parser fixtures — ok=757 changed=0 failed=0 skipped=186 ignored=4
PASS: all 23/23 playbook syntax checks
HISTORICAL PASS: production ansible-lint — 0 failures, 0 warnings; 162 files processed
PASS: Python compile, shell syntax, diff check, and no staged files
NOT RUN/BLOCKED: enhanced live preflight, recovery attestation, Secret writes, Infisical/database runtime
```

A focused fail-closed follow-up adds the distinct
`environment_override_unknown` source stage and accepts the exact official K3s JSON
shape `{"stage":"","activekey":""}` only as encryption `disabled` with rotation
`not_applicable`. It does not convert absent encryption configuration into permission
to write Secrets. The 15 focused contracts, 757-task executable parser fixture, two
affected syntax checks, focused production lint, and diff check pass.

## Approved one-time Infisical PostgreSQL value upload — 2026-08-11

The operator explicitly approved a one-time Linux-host CLI exception after selecting
project `cristexweb-infrastructure`. Metadata-only preflight confirmed the fixed
Infisical environment `prod` existed and `/shared-services/postgresql` did not.
The operation created only folders `shared-services/postgresql`, generated values in
a private temporary directory, and uploaded one exact file-bound batch containing
15 PostgreSQL administrator, TLS, and reserved consumer keys. No value appeared in
argv, environment, command output, or this evidence.

Sanitized acceptance evidence:

```text
folders_created=shared-services,shared-services/postgresql
pre_upload_secret_count=0
remote_key_count=15
remote_key_closure=exact
credential_contract=valid
TLS direct-CA, exact localhost/service/cluster-local SANs, and leaf/key match=valid
plaintext_temp_residue=none
Infisical CLI=0.43.121
```

This exception created no Universal Auth identity, Kubernetes Secret, Infisical CR,
workload, PVC, database, Namespace, route, or PROD activation. The canonical broad
uploader must fail closed on this now-prepopulated PostgreSQL path. Any later password
replacement is rotation and must preserve the exact usernames, key closure, password
contract, and TLS relationships. Universal Auth, database Secret materialization,
PostgreSQL check/apply/idempotence, and runtime remain **NOT RUN/BLOCKED**.

## MongoDB operator namespace migration — 2026-08-12

The operator explicitly approved moving the MongoDB Community Operator control plane
from `shared-services` to the dedicated `mongodb-system` Namespace and removing the
superseded control-plane objects from `shared-services`. The existing MongoDB custom
resource, Pod, Services, Secrets, and PVCs remained in `shared-services`.

Sanitized acceptance evidence:

```text
mongodb-system Namespace=created
mongodb-system/mongodb-kubernetes-operator=1/1 Running
WATCH_NAMESPACE=shared-services
cross-namespace get MongoDBCommunity/update StatefulSet=yes
old shared-services operator Deployment and ServiceAccount=absent
shared-mongodb phase=Running version=8.0.12 members=1
shared-mongodb-0=2/2 Ready, zero restarts
MongoDB PVCs=80Gi Bound + 5Gi Bound
new operator reconciliation=successful; TLS config valid; all agents at goal state
PostgreSQL and MongoDB data Pods=uninterrupted
```

## Approved Keycloak PostgreSQL backup preparation — 2026-08-12

The operator approved host-managed systemd scheduling, direct encrypted Google Drive
backup, Infisical custody for the private age identity, and one isolated restore
rehearsal before timer activation. The guarded dependency play installed exact Debian
`age 1.2.1-1+b5`; post-state verified `amd64`, k3s active, and Tailscale active. The
host rclone `drive:` remote passed authentication without token output.

A dedicated age identity was generated in protected host storage, uploaded by
file-bound Infisical CLI input to `prod:/shared-services/backup-recovery`, fetched
into private temporary memory-backed storage for exact comparison, and securely
removed from the host. Sanitized evidence:

```text
Infisical remote key count=1
remote key closure=SHARED_DATABASE_BACKUP_AGE_IDENTITY only
remote/local private identity equality=valid
host private identity residue=none
host public recipient=retained
secret value output=none
```

Guarded Ansible source now defines an unprivileged hardened oneshot service and a
daily persistent timer for only PostgreSQL database `keycloak`. It performs custom
`pg_dump`, compression, age encryption, SHA-256/manifest generation, immutable
rclone upload, exact readback comparison, plaintext cleanup, sanitized journald
receipts, and bounded encrypted local retention. Install/test/enable remain separate;
timer enablement is blocked until the Google Drive download/decrypt/isolated
PostgreSQL 17 restore rehearsal passes with zero residue.

The first backup test then passed through the installed systemd service. It produced
an encrypted custom-format dump, exact checksum and value-free manifest, uploaded the
three leaves immutably, downloaded each leaf, and verified byte equality. The first
restore attempt stopped safely on an RFC 1123 uppercase Pod name before object
creation. The corrected retry created and removed only its exact temporary Pod but
stopped on root-owned `emptyDir` permissions. A same-image, capability-bounded init
container corrected only UID/GID `999` data-directory ownership. The final isolated
restore passed and cleanup removed the exact UID-bound Pod and all private temporary
material.

```text
backup service result=success
Google Drive leaf closure=archive + checksum + manifest
readback=verified
host plaintext residue=none
host private age identity=absent
isolated PostgreSQL 17 restore=success
restore target storage=emptyDir
restore Pod residue=none
private decryption/key residue=none
shared-postgresql Ready=true, restarts=0
k3s/tailscaled=active
backup timer initial gate=disabled/inactive
final enable apply=enabled/active (waiting)
final idempotence=ok=18 changed=0 failed=0
next scheduled trigger=registered by systemd
```

## MongoDB shared backup scheduler source — 2026-08-12

A separate guarded host source closure now mirrors the accepted PostgreSQL scheduler
without modifying or coupling its active timer. It targets the complete
`shared-mongodb` one-member replica set and uses the existing Infisical-owned admin
credential only through a mode-`0700` memory-backed temporary config fed on stdin to
`mongodump`; no credential enters argv, environment, journal, or evidence. TLS is
CA-validated against the exact operator-mounted CA, and `--oplog` provides a
replica-set-consistent archive.

The source encrypts to the same pinned public age recipient, performs immutable
Google Drive upload plus exact readback, retains only encrypted local artifacts, and
defines a separate daily `03:45` systemd timer. Restore source retrieves the private
identity temporarily from Infisical and restores into a digest-pinned MongoDB
`8.0.12` Pod with `emptyDir`, no Service/PVC/Kubernetes Secret/token, bounded init
permissions, exact UID-precondition cleanup, and sanitized receipt. Installation, oplog-consistent backup, immutable Google Drive readback, Infisical-key
decrypt, isolated MongoDB `8.0.12` restore, exact UID-bound cleanup, production
non-mutation, and zero residue passed. The MongoDB timer remains disabled/inactive
then its final enable apply passed, activated the timer, and idempotence converged at
`ok=18 changed=0 failed=0`.


The manifest now declares `mongodb-system`, places only the operator Deployment and
operator ServiceAccount there, keeps workload ServiceAccount and namespaced RBAC in
`shared-services`, and pins `WATCH_NAMESPACE=shared-services`. MongoDB TLS identity
contracts now include the operator-used member FQDN in addition to localhost and the
stable Service identities. Backup/restore and production acceptance remain blocked.


## phased Cloudflare edge route contract source-only validation — 2026-08-12

This validation checks only the value-free Cloudflare edge policy and its
source-only runbook. It performs no Cloudflare API/provider operation, DNS
mutation, Tunnel creation, token read/materialization, Kubernetes operation,
Traefik reconciliation, route publication, or runtime validation.

```bash
python3 -m unittest -v tests.test_cloudflare_edge_architecture_contract
```

Expected result: policy path, exact namespace ownership, separate approval
phases, token non-disclosure, deny-first public surfaces, negative reachability,
rollback, and blocked-runtime assertions pass. The route remains unapproved and
runtime remains NOT RUN/BLOCKED.

## CristexHub DEV Argo registration and DNS recovery — 2026-08-14

The approved repository credential was uploaded to Infisical without value
output and materialized as `argocd/argocd-repository-cristexhub`. The local
private deploy key was securely removed after SSH-over-443 verification.
Guarded Infisical, Argo core, registration, and CoreDNS checks/applies passed.
Final idempotence results were respectively `changed=0` for all four wrappers.

Argo renders the pinned CristexHub revision as 18 objects and reports
`OutOfSync`, `Missing`, with no comparison conditions. Automated sync remains
disabled because application image digests are still zero and the eight-key
runtime Secret/OIDC egress gates are incomplete. CoreDNS external forwarding
now uses the exact guarded `1.1.1.1`/`1.0.0.1` field replacement; external
`ssh.github.com` resolution passed after one controlled CoreDNS reload.

## Infrastructure CI source-closure reconciliation

After the guarded CristexHub DEV registration, runtime-secret, OIDC proxy, private
Argo route, TLS lifecycle, CoreDNS and sync-transition source was added, several
historical exact-inventory tests and lint scope exclusions still described the older
repository closure. CI consequently failed before validating the current source.
The exact allowlists now include only those reviewed additions; the Argo shell smoke
binds the canonical repository root and accepts the controller's safe pre-mutation
missing-Kubernetes-library stop; lint excludes only the already contract-tested
new exact source directories. Validation now passes: `353/353` offline contracts,
all Ansible playbook syntax checks, production-profile `ansible-lint` with zero
failures, Python compileall, and both vendored SHA256 ledgers.

## Branded hosted Keycloak theme

The CristexHub-owned theme `1.1.0` was built as a private immutable image from the
exact Keycloak `26.7.1` digest with SBOM/provenance and promoted as
`ghcr.io/devraider/cristexhub/keycloak@sha256:c1c49aa925127c2a9277f9d0d6fffee888030a4c5710e8478c0a5b26ccbda0ac`.
The existing GHCR Docker configuration was copied without value output into
Infisical `prod:/shared-services/keycloak`, exact remote equality was verified, and
a create-only `kubernetes.io/dockerconfigjson` pull Secret was installed in
`shared-services`. Updated source extends the future Infisical materialization and
admission closure to that exact target; the absent dedicated Universal Auth remains
a fail-closed rotation/materialization follow-up.

Keycloak guarded check predicted one Deployment change; apply converged with
`changed=1`, and idempotence passed with `changed=0`. The live realm now selects
`loginTheme=cristexhub`. Public login HTML references only the local custom CSS, the
served SVG equals the reviewed Cristex Soft asset, and public `/admin/` and
`/realms/master` both remain `404`. No Secret value was printed.

## CristexHub DEV authenticated PDF CSP correction

The guarded Argo revision transition to
`7985616c6278fc7c3122fe5ca9fe197ff1d7b9b8` passed apply. Argo reached
`Synced / Healthy`, the frontend rollout completed, and the public
`/employees/import` response now carries the exact least-privilege directive
`frame-src 'self' blob:`. A subsequent guarded apply converged at `changed=0`.

## Exact DeepSeek HTTPS proxy admission

The shared CONNECT proxy now admits exactly `api.deepseek.com:443` in addition to
the existing public Keycloak hostname; arbitrary HTTPS destinations remain denied.
Guarded check predicted one change, apply converged with `changed=1`, and idempotence
passed at `changed=0`. From the backend Pod, unauthenticated DeepSeek `/models`
returned the expected `401` (transport reachable), Keycloak discovery remained
`200`, and `example.com` remained blocked. No API token value was read or output.

## Celery AI proxy client admission and DEV rollout

The exact CONNECT-proxy ingress closure now admits the `cristexhub-dev` Celery
worker in addition to backend and oauth2-proxy; Squid still permits only the exact
Keycloak and DeepSeek HTTPS hosts. Guarded proxy check/apply passed, and idempotence
converged at `changed=0`. Argo revision
`8e83e43e72eae04141d5d6f89ed52761a3cf0de8` reached `Synced / Healthy`; backend,
frontend and Celery use promoted immutable images. From the worker Pod,
DeepSeek `/models` returned expected unauthenticated `401`, proving transport through
the proxy without token output. Celery is Ready with zero restarts and no deprecated
pidbox queue reconnect loop. The prior stuck import recovered to `pending_review`
after its queued task was consumed; the operator can retry it safely.

## DeepSeek V4 JSON-mode runtime correction

Argo revision `cdc97f49d89298d01f1a06c160147e2e23732e8f` reached
`Synced / Healthy` with promoted immutable backend/frontend images. Backend and
Celery rollouts completed. The runtime now appends an explicit JSON instruction and
registered schema for `json_mode`, satisfying DeepSeek V4's requirement that prompts
mention JSON while avoiding unsupported thinking-mode `tool_choice`.

DeepSeek structured-completion correction revision
`1d930a46c24b465dbd349bbfab871abc455bbd0e` reached `Synced / Healthy`; the
Celery rollout completed. The promoted runtime disables DeepSeek thinking for
bounded structured extraction, preventing reasoning-only exhaustion at 2048 tokens.

Resume education-degree compatibility revision
`ccf861877fbec4fac7ee70bdb852243096abdde5` reached `Synced / Healthy`; backend,
Celery, and frontend rollouts completed. Resume parsing now preserves optional degree
data rather than rejecting valid provider output.

### CRISTEXHUB-DEV-REVIEW-FIXES-PROMOTION — 2026-08-17

The guarded automated-sync source advances only `Application/cristexhub-dev` from
the previously verified revision to immutable application revision
`9c4ce3cd624fac3239a58d759778f46846cedd97`. That revision selects the
source-bound backend and frontend GHCR digests published for
`86e729e2704c461337a6a1d55684f0304b2a3c4e`; `prune=false`, `selfHeal=true`,
`CreateNamespace=false`, and the existing destination/project boundaries remain
unchanged. Focused offline contracts passed (`19 tests`) before the guarded check.
Runtime check/apply, rollout, Argo health, image identity, and public/private smoke
results follow below.

The guarded check passed at `ok=22 changed=1 failed=0 skipped=2`; apply passed at
`ok=24 changed=1 failed=0 skipped=0`. Argo reached the requested revision and the
new frontend/Celery images became Ready, but backend startup was blocked before
migration `030`: Beanie requested the new sparse unique
`background_action_event_dedupe` index while MongoDB's one-member replica-set
index build remained at commit-readiness. Repeated startup attempts created a
bounded queue of identical builds. After verifying 69 records and zero existing
`event_key` values, recovery aborted only the exact in-progress index builds; no
records or collections were deleted. The source-bound rollback to
`ccf861877fbec4fac7ee70bdb852243096abdde5` passed guarded check/apply and restored
Argo `Synced / Healthy` plus backend `1/1` readiness. The new images remain
published but are **not deployed**. Reattempt is blocked until the MongoDB internal
TLS/index-commit path is reviewed and repaired under a separate stateful approval.
Final recovery held a 30-second clear observation window after aborting the last
queued exact build; all 69 records remained and no `event_key` value or plaintext
credential residue was introduced. Public root returned `200`, OIDC start returned
`302`, and all five DEV Deployments were Ready.

### MONGODB-TLS-CLIENTAUTH-ROTATION-20260818

A same-day oplog-consistent encrypted backup had completed successfully before the
approved stateful repair. The MongoDB leaf was confirmed `serverAuth`-only while
MongoDB uses it for both listeners and replica-set member authentication. Source
now requires `serverAuth,clientAuth`; exact four SANs, CA/leaf verification, and
key correspondence passed without value output.

Infisical rotation used a bounded dual-trust sequence: application trust first,
then the exact `MONGODB_TLS_CA_CRT`/`MONGODB_TLS_PEM` pair, then removal of the old
CA. Cross-component Secret updates initially exposed overlapping shared-services
VAP match conditions; the database, Keycloak, and RabbitMQ write policies were
scoped to their exact target names and applied before retry. Infisical reconciliation
returned True for both MongoDB and DEV runtime sources. MongoDB 8.0.12 returned to
`Running`; the mounted leaf reports both SSL server and client purposes, and no
post-rotation `unsupported certificate purpose` event was observed.

The previously blocked `background_action_event_dedupe` sparse unique index then
committed with quorum in 150 ms, preserving all records. Guarded DEV revision check
passed at `ok=22 changed=1 failed=0 skipped=2`; apply passed at
`ok=24 changed=1 failed=0 skipped=0`. Argo reached `Synced / Healthy` at
`2bba6aaacb0886705abc0a57f9caafac0cb67e90`; backend, Celery, and frontend are
Ready on the promoted immutable digests with zero new Pod restarts. All 35 migrations,
including `030` through `035`, are recorded. Public root returned `200` and OIDC
start returned `302`.

## CristexHub PROD browser identity source-only increment

The value-free hosted identity policy now selects `cristexhub-prod` as a
confidential PKCE `S256` client for realm `cristexhub`, issuer
`https://auth.cristex-soft.com/realms/cristexhub`, and only the exact
`https://hub.cristex-soft.com/oauth2/callback` callback,
`https://hub.cristex-soft.com` web origin, and
`https://hub.cristex-soft.com/` post-logout redirect. Its groups are bound to
`cristexhub-prod-<organization-alias>-<role>` and
`cristexhub-prod-super-admin`; required identity claims and missing/ambiguous-group
denial remain fail-closed. The DEV contract and both administrative service
clients remain private. Reactive Resume and Argo callbacks remain unselected.
This source increment adds no Keycloak runtime reconciliation, route, Secret value,
provider operation, or cluster contact.

Offline validation commands:

```text
python3 -m unittest -v tests.test_hosted_auth_source_selection_contract tests.test_keycloak_oidc_bootstrap_design_contract
git diff --check
git diff --cached --quiet
```

Result: **PASS** — 21 focused policy/design tests, diff check, and no-staged-files
check passed. Keycloak/API/provider access, Secret access, runtime reconciliation,
and public-route validation were **NOT RUN**.

## CristexHub PROD runtime Infisical seam — hardened check STOPPED/BLOCKED

Historical prior-source evidence (nine-key checkpoint): the value-free production seam adapts the DEV contract without sharing names or
Universal Auth identity. It binds Infisical project
`cristexweb-infrastructure` / `619656da-14f3-4872-857b-be103cdc5326`, the Cloud
identifier slug `prod`, exact source `/cristexhub/prod/runtime`, existing Active
and idempotent target Namespace `cristexhub-prod`, independent
`cristexhub-prod-infisical-auth` and
`cristexhub-prod-infisical-universal-auth` names, the nine-key
`cristexhub-prod-runtime` target, and separate
`cristexhub-prod-ghcr-pull` dockerconfig target. Four namespace-scoped
fail-closed VAP/binding pairs, additive exact-name writer RBAC, canonical
manifest/default/action hashes, a guarded non-passthrough wrapper/playbook/role,
and an offline value-free policy/runbook are committed. No Secret object or
value is committed.

Offline validation:

```bash
.venv/bin/python -m unittest -v tests.test_infisical_cristexhub_prod_runtime_contract
.venv/bin/python -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/bootstrap-infisical-cristexhub-prod-runtime
git diff --check
```

Actual result: focused production seam contracts passed (`9` tests), the full
suite passed (`385/385`), all 44 playbook syntax checks passed, production lint
passed with only 14 known ignored warnings, and source hashes, shell syntax,
Python compilation, and diff checks passed. The guarded read-only wrapper check
contacted Kubernetes and stopped safely at `ok=15 changed=0 unreachable=0 failed=1`
on exact live Operator pod-template drift. Source now explicitly bounds the rollout
receipt and canonically includes `SSL_CERT_DIR=/etc/ssl/certs:/etc/infisical-proxy-ca`.
A fresh Operator check passed at `ok=30 changed=0 failed=0 skipped=5`; the runtime
check advanced to the intended absent Universal Auth gate and stopped at
`ok=23 changed=0 failed=1`. Both checks made no mutation. The original stop was before runtime
reconciliation and made no mutation. No Infisical API write, Namespace creation,
Universal Auth value, Secret sync, workload, route, or PROD promotion was run.
Apply, identity materialization, values, and runtime remain **NOT RUN/BLOCKED**.

## Source-only CristexHub PROD Argo registration — NOT RUN/BLOCKED

The exact five-object closure pins protected-main CristexHub revision
`751885a42798d282e168131db147f13694a0a621` and
`infra/kubernetes/cristexhub-prod`. The Application remains manual, has no
finalizer, and sets `CreateNamespace=false`, `Prune=false`,
`ServerSideApply=false`, `Replace=false`, and `FailOnSharedResource=true`. Its
AppProject contains an always-active deny window with `manualSync=false`.
Namespace-scoped controller RBAC has no delete verb or cluster role. The guarded
role verifies raw hashes, the absent-or-owned pre-state, exact PROD Namespace,
and Infisical-owned repository credential metadata before binding the preflight
to the present-only action plugin.

Offline validation:

```bash
.venv/bin/python -m unittest -v tests.test_cristexhub_prod_registration_contract
.venv/bin/python -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/bootstrap-cristexhub-prod-registration
cd ansible && ../.venv/bin/ansible-playbook playbooks/bootstrap_cristexhub_prod_registration.yml --syntax-check
```

Actual result: `11` focused contracts plus compile, shell, and playbook syntax
checks passed. The `cristexhub-prod` Namespace is already Active/idempotent from its
separate checkpoint. No wrapper check/apply, Kubernetes API, Argo registration/sync,
Secret, image publication, workload, database, broker, DNS, provider, or Cloudflare
action ran.


## CristexHub PROD private activation — APPLIED / SYNCED / HEALTHY

This section supersedes the earlier source-only runtime and registration evidence
above without rewriting those historical stops.

- The PROD Infisical runtime seam final idempotence passed at
  `ok=62 changed=0 failed=0 skipped=3`; the exact runtime and GHCR target Secrets
  exist and remote/target key closure matched without value output.
- The five-object Argo registration and active-state retry passed. The Application
  uses the in-cluster server, `selfHeal=true`, `prune=false`, `allowEmpty=false`, and
  `CreateNamespace=false` at revision
  `751885a42798d282e168131db147f13694a0a621`.
- Read-only validation on 2026-08-20 reported Argo `Synced/Healthy`; backend,
  Celery, frontend, oauth2-proxy, and Redis were each `1/1 Ready`; backend root
  returned `200`; oauth2-proxy root/start returned `302`; backend logged completed
  startup; and Celery logged a TLS RabbitMQ connection and ready state.
- The PROD OIDC proxy client policy is applied and includes the PROD namespace;
  the exact eight PROD NetworkPolicies are present.
- Source validation at commit `255aa62f7f3e9e662c9d65e830f85aac3b39fdda`
  passed `385/385` offline contracts and all playbook syntax checks. GitHub Actions
  runs `32375586986` (main) and `32375590391` (develop) completed successfully.
- OpenTofu source now contains exactly the PROD Tunnel ingress and proxied DNS
  record. Provider planning stopped safely with `403` because the available OAuth
  credential lacks DNS-record permission; no provider mutation occurred and
  `hub.cristex-soft.com` remains unresolved.
- A local retained reviewer transcript exposed base64 Secret data and was removed.
  Universal Auth and application/OIDC values were rotated. MongoDB/RabbitMQ URL
  credentials and the reused GHCR pull credential still require verified rotation
  before public cutover.

## Shared MongoDB NetworkPolicy guarded check — PASSED / APPLY BLOCKED

A dedicated two-policy, check-only closure now selects the live operator-managed
`shared-mongodb-0`, fails closed on additive foreign policy overlap, binds exact
StatefulSet/pod/client/CoreDNS health, and has no legacy workload or Secret path.
The hardened guarded check passed at
`ok=34 changed=1 unreachable=0 failed=0 skipped=0`; it predicted exactly the two
absent NetworkPolicies and made no Kubernetes mutation. Apply and the required
positive/negative enforcement probe remain separately approved and NOT RUN/BLOCKED.

## Keycloak DEV successor realm source — OFFLINE CHECK PASSED / APPLY BLOCKED

The retained `cristexhub` realm remains the current PROD-compatible issuer and is
not a mutation target. A distinct four-leaf, hash-bound, value-free source contract
now reserves successor realm `cristexhub-dev`, browser client `cristexhub-dev`, a
disabled future `cristexhub-admin-svc-dev` service client, static DEV super-admin
group, and exact groups/organization/audience mapper intent. Native Organizations
are enabled in the contract; organization scope/context is mandatory; user,
membership, dynamic-group, route, Secret, and runtime migration remain blocked.

The dedicated wrapper accepts only `check`, validates the protected local inventory,
uses local connection, rejects task-selection environment controls and API/token
inputs, and invokes an offline action guard. No Keycloak, Kubernetes, Infisical,
Cloudflare, provider, host, or application runtime request is made. Successor
credential metadata reserves the separate browser and disabled admin-service
paths below `prod:/cristexhub/dev/identity/`; no writer or value exists.

Validation completed on 2026-08-21:

```bash
ansible/bin/bootstrap-keycloak-dev-identity check
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -q
cd ansible && for f in playbooks/*.yml; do ../.venv/bin/ansible-playbook "$f" --syntax-check; done
cd ansible && ../.venv/bin/ansible-lint . ../tests/validate_storage_report.yml
.venv/bin/python -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/bootstrap-keycloak-dev-identity
git diff --check
```

Actual result: offline wrapper `ok=14 changed=1 unreachable=0 failed=0 skipped=0`;
`409/409` unit tests passed; every playbook syntax check passed; production-profile
Ansible lint passed with only the 14 pre-existing ignored warnings; compile, shell,
and diff checks passed. The predicted change means runtime state is intentionally
unknown, not that a mutation occurred. Realm creation, private Admin REST transport,
bootstrap retirement custodian and disabled auditor placeholder, credential CAS/materialization, identity
migration, application cutover, and authenticated positive/negative tests remain
**NOT RUN/BLOCKED** and require separate approvals.

## Keycloak DEV successor transition design — OFFLINE CHECK PASSED / RUNTIME BLOCKED

A second four-leaf, hash-bound, value-free closure now defines only future
transition prerequisites. It rejects the current plaintext Keycloak `8080` listener
for Admin credentials and requires a still-absent strict-TLS `8443` listener, exact
private CA/loopback SAN, one Ready Pod UID, and a focused pinned controller client
for loopback port-forwarding. It creates no Service, helper Pod, route, listener,
certificate, or Kubernetes object.

The actor contract separates a one-transition master service account with only
`create-realm` from a disabled `cristexhub-dev` auditor placeholder. Automatic
creator grants require an exact role-ID ledger and removal by a distinct retirement
custodian that remains absent/blocking. The auditor receives no direct role, FGAP
policy, credential materialization, or Admin REST method: exact Keycloak 26.7.1
collection/projection semantics for `query-clients` and `query-groups` remain an
unverified blocker; `view-clients` and client FGAP `view` authorize secret-bearing
reads, while group `view` exposes role-mapping/detail data beyond the boundary. Recurring Admin REST audit therefore remains blocked
until a genuinely narrower capability exists. Four distinct Infisical paths reserve browser, disabled admin-service,
bootstrap value metadata and a disabled-auditor reservation; auditor value materialization is forbidden. There is no writer or Kubernetes target; existing
VAP/RBAC seams cannot be reused, and provider CAS semantics remain an explicit
unverified blocker.

Validation completed on 2026-08-21:

```bash
ansible/bin/bootstrap-keycloak-dev-identity check
ansible/bin/bootstrap-keycloak-dev-identity-transition check
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -q
cd ansible && for f in playbooks/*.yml; do ../.venv/bin/ansible-playbook "$f" --syntax-check; done
cd ansible && ../.venv/bin/ansible-lint . ../tests/validate_storage_report.yml
.venv/bin/python -m compileall -q ansible/plugins/action tests
git diff --check
```

Actual result: base successor check `ok=14 changed=1 failed=0`; transition check
`ok=15 changed=1 failed=0`; `420/420` unit tests passed; all 47 playbook syntax checks
passed; production-profile Ansible lint passed with only 14 pre-existing ignored
warnings; compile and diff checks passed. Both predicted changes are offline source
predictions only. No Keycloak/Admin API, Kubernetes, Infisical, Secret, database,
host, application, route, or provider operation ran. HTTPS listener source/apply,
backup role/ownership recovery, pinned transport implementation, actor/value
creation, CAS writer/VAP/RBAC, Admin API preflight/apply/idempotence, identity
migration, application cutover, and authenticated tests remain **NOT RUN/BLOCKED**
and require separate approvals.

## Browserless runtime secret durability (2026-08-22)

| ID | Scenario | Expected | Actual |
|---|---|---|---|
| KIF-BR-01 | DEV/PROD Browserless credential contract | The guarded Infisical StaticSecret source, target-write admission, role assertions, policies, and hash ledgers require exactly one additional `BROWSERLESS_TOKEN` without committing a value or granting Argo Secret ownership | PASS — focused DEV/PROD runtime contract tests; source closure is ten keys and remains unapplied pending approved Infisical value insertion |
| KIF-BR-02 | Ownership boundary | Browserless/gateway and code-runner workload manifests stay in `cristexhub`; `cristexweb` owns only Infisical materialization and pinned Argo registration, preventing dual Ansible/Argo reconciliation | PASS — existing AppProject/RBAC already permits Deployment, Service, ConfigMap, and NetworkPolicy while excluding Secret writes |
| KIF-BR-03 | Review-log credential incident | A read-only reviewer accidentally emitted existing DEV/PROD runtime Secret data into its private session; exact child/async artifacts are removed without repeating values and affected credentials must be rotated before the ten-key seam or revision transition is applied | BLOCKED — rotation/revocation requires a separately approved no-output Infisical operation; no runtime apply or Argo revision mutation is authorized by this source change |
