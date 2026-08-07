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
| KIF-NS-01 | KIF-002, KIF-005, KIF-006, KIF-010, KIF-030 | Bounded platform Namespace bootstrap offline contract | Exact committed `argocd` and `platform-edge` Namespace manifests are the sole definition and the architecture/task checklist places them in a documented pre-Stage-4 exception with separate check/apply/idempotence approvals that waives no Stage 4 entry gate; a non-passthrough entrypoint rejects `--start-at-task`, `--step`, and all extra arguments; the wrapper launches the repository `.venv` controller in an allowlisted clean environment and supplies a private random single-run attestation; the mutating task independently requires that attestation, reloads only literal manifest paths, and rejects extra top-level/metadata keys; a first-task internal-variable guard, canonical non-symlink ancestor/leaf validation, approval/diff/exact-limit/kubeconfig/protected-result gates, foreign-existing refusal, present-only reconciliation, exact post-verification, truthful ownership labels, executable closure, and no deletion/other-kind path are enforced | PASS — focused structural, stage-boundary, control-flow, and synthetic ancestor-symlink contracts, controller-only forged-extra-var rejection, full offline suite, syntax, synthetic discovery validation, and production lint passed without inventory or Kubernetes API contact |
| KIF-NS-02 | KIF-002, KIF-005, KIF-010, KIF-030 | Platform Namespace bootstrap runtime | Reviewed check predicts exactly the two absent Namespaces; approved live run creates them, verifies labels/services, and second run converges changed=0 without installing Argo CD/cloudflared or creating a route | PASS — wrapper check passed without mutation; separately approved first apply passed at ok=21/changed=1/unreachable=0/failed=0/skipped=0 and changed exactly `argocd` plus `platform-edge`. During the separately approved idempotence checkpoint, a local sudo authentication failure stopped the initial invocation before service preflight/reconciliation at ok=10/changed=0/unreachable=0/failed=1/skipped=0; the retry passed at ok=21/changed=0/unreachable=0/failed=0/skipped=0, both exact items were `ok`, post-state identity/labels/Active passed, and service health was preserved |
| KIF-ARGO-01 | KIF-005, KIF-008, KIF-010, KIF-013, KIF-015, KIF-023, KIF-030 | Argo CD candidate provenance and target-minor screen | A secret-free record binds exact official chart/index/provenance/image/render evidence plus the approved target kubelet and official Argo CD tested-version sources; it narrowly concludes only that Kubernetes minor `1.36` is in Argo CD `3.5`'s tested matrix and passes chart `10.3.0`'s semver gate, while preserving the exact two-Namespace source set and blocking exact k3s/runtime, rendered API/CRD, trust, selection/soak, Secret, private Git, image/traffic, ownership, and runtime gates | PASS — 5 focused provenance contracts enforce exact associations and qualified boundaries; chart `10.3.0`/app `v3.5.0` remain CANDIDATE — NOT DEPLOYABLE — NOT SELECTED; Argo runtime NOT RUN and no chart, values, Kubernetes object, secret, or deployment source was added |
| KIF-ARGO-02 | KIF-005, KIF-008, KIF-010, KIF-013, KIF-015, KIF-021, KIF-023, KIF-030 | Argo CD online/static readiness refresh | A secret-free committed record curates refreshed official bytes plus deterministic render, upstream API registration, RBAC/network, image trust/availability/vulnerability, private-Git, and Namespace-adoption evidence while preserving exact two-Namespace source closure and all live admission/runtime gates | PASS — 9 focused provenance contracts and 71 full offline tests pass; chart `10.3.0`/app `v3.5.0` remain CANDIDATE — NOT DEPLOYABLE — NOT SELECTED; live API, server-side dry-run, install, Secret, provider, and runtime operations remain NOT RUN; no chart, values, rendered YAML, Kubernetes object, credential, or deployment source was added |
| KIF-CF-01 | KIF-005, KIF-011, KIF-013, KIF-015, KIF-021, KIF-023, KIF-030 | Source-only cloudflared candidate provenance | A secret-free record mutation-resistently binds exact official release/source/asset and architecture-specific image evidence, explicitly qualifies the unsigned trust boundary, captures token-file precedence, connection-aware readiness versus independent health, fixed metrics/quick-tunnel management-surface and edge-transport constraints, preserves exact two-Namespace and zero-resource OpenTofu source sets, and blocks trust/selection/soak, image assurance/availability, hardening, Infisical token recovery, OpenTofu state/resource work, Argo handoff, exact DNS/Traefik/edge policy, route approval, single-node risk, and runtime | PASS — 5 focused contracts enforce exact evidence associations, trust qualifications, token/health/network semantics, unchanged source sets, operational-command hygiene, and effective RFC1918/loopback sentinels; `2026.7.3` remains CANDIDATE — NOT DEPLOYABLE — NOT SELECTED; runtime NOT RUN and no OpenTofu resource, Kubernetes object, secret, route, or deployment source was added |
| KIF-INF-01 | KIF-005, KIF-013–KIF-015, KIF-021, KIF-023, KIF-030 | Source-only Infisical Operator candidate provenance | A secret-free record binds the latest `v0.11.8` source release and time-qualified public chart/image distribution gap separately from the last observed version-aligned `v0.11.7` chart/source/image set; association-sensitive evidence qualifies unverified chart provenance, observed SLSA content, missing SBOM observation, chart defaults, and exact architecture child digest while preserving the two-Namespace and zero-resource OpenTofu source sets and blocking selection/trust, compatibility, dedicated Namespace, scoped RBAC, Argo handoff, secret-zero/recovery, traffic, single-node, and runtime | PASS — 5 focused contracts enforce exact evidence associations, qualified trust/absence wording, source closure, operational-command hygiene, and effective RFC1918/loopback sentinels; both versions remain CANDIDATE — NOT DEPLOYABLE — NOT SELECTED; runtime NOT RUN and no chart, values, CRD, Kubernetes object, credential, Secret, or deployment source was added |

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
[`infisical-operator-candidate-provenance.md`](../../runbooks/infisical-operator-candidate-provenance.md);
both versions are **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED**, and runtime is **NOT
RUN**.

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
[`argocd-candidate-provenance.md`](../../runbooks/argocd-candidate-provenance.md);
it is **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED**, and runtime is **NOT RUN**.

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
signing-key trust/status, human selection/soak, Secret recovery, private Git,
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
application remain **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED**; Argo CD runtime is
**NOT RUN**, and this evidence closes no manual QA case.

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
| KIF-DOC-01 | KIF-004, KIF-030 | Required shape and links | Canonical root/spec documents, locked uv project files, Ansible discovery files, source-only Argo/cloudflared/Infisical candidate provenance, and offline contract tests exist; local Markdown links resolve | PASS — bounded offline documentation check passed |
| KIF-DOC-02 | KIF-005, KIF-009, KIF-022 | Ownership consistency | Ansible/OpenTofu/Argo CD/Infisical/GitHub Actions have non-overlapping owners; the exact two-Namespace present-only exception truthfully records Ansible as bootstrap writer and Argo CD only as future desired owner pending install/adoption/Application/sync evidence; Traefik remains sole ingress | PASS — authoritative documents remain consistent; a label alone is not a handoff |
| KIF-DOC-03 | KIF-001–KIF-003, KIF-006 | Honest implementation boundary | Executed Ansible evidence distinguishes completed OpenTofu installation, completed Namespace check/first apply/idempotence checkpoints including the pre-reconciliation credential failure, and non-deployable Argo/cloudflared/Infisical candidate provenance; only the exact two Namespaces were created, with no controller install, state/provider operation, general host baseline, hosted runtime, or deployment claimed | PASS — repository scan and status wording passed |
| KIF-DOC-04 | KIF-013–KIF-015 | No committed secret/address material | Repository source contains no private-key block, provider token, kubeconfig content, credential value, or private IPv4 address | PASS — bounded source scan passed |
| KIF-DOC-05 | KIF-016–KIF-021 | Shared-services and policy risk | Separate principals/backups/vhosts and negative tests remain required; object listings alone do not prove policy enforcement | PASS — functional probe evidence and remaining application-isolation QA are explicit |
| KIF-DOC-06 | KIF-023–KIF-030 | Honest future evidence | One future discovery case is PARTIAL, eleven future runtime cases remain NOT RUN, one manual case passes, and twelve manual cases remain PENDING | PASS — counts and status assertions passed |

All requirements KIF-001 through KIF-030 remain represented by the implementation,
documentation, manual, or future-runtime cases in this file. Only the explicit live
CNI, storage, and OpenTofu evidence above closes their bounded runtime gates; the
platform Namespace bootstrap has a passed non-mutating wrapper check, first apply,
and `changed=0` idempotence retry after a pre-reconciliation credential failure.
Argo CD/cloudflared/Infisical candidate
provenance remains source-only with no runtime evidence. The candidate records are
[`argocd-candidate-provenance.md`](../../runbooks/argocd-candidate-provenance.md),
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
  tests/test_ansible_contract.py
  tests/test_opentofu_contract.py
  tests/test_platform_namespace_contract.py
  tests/reject_platform_namespace_internal_injection.yml
  tests/reject_platform_namespace_task_start.sh
  tests/validate_platform_namespace_clean_controller.sh
  tests/test_replacement_recovery_contract.py
  tests/test_argocd_provenance_contract.py
  tests/test_cloudflared_provenance_contract.py
  tests/test_infisical_operator_provenance_contract.py
  tests/validate_storage_report.yml
  runbooks/replacement-host-recovery.md
  runbooks/recovery-artifact-register.md
  runbooks/argocd-candidate-provenance.md
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
assert len(re.findall(r"^\| MQA-\d{2} .* \| PENDING \|$", (spec_dir / "manual-qa.md").read_text(), re.MULTILINE)) == 12
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
    "Namespace idempotence plus Argo 3.5 online/static render/API/image readiness contracts pass",
    "exact k3s admission/security/Secret/adoption/runtime and provider/state/backup pending",
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

print("PASS: Ansible/OpenTofu/Namespace layout, Argo/cloudflared/Infisical candidate provenance, links, 30 requirement IDs, 12 future cases, 1 passing and 12 pending manual cases, status/implementation boundary, and bounded source scan")
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

## Future validation contract

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-FUT-01 | KIF-001, KIF-007, KIF-008, KIF-028 | Read-only Ansible discovery | Curated report proves actual k3s, storage, resource, and recovery indicators without mutation; human review passes | PARTIAL — host, datastore, capacity, reboot recovery, extended storage, Kubernetes indicators, and functional CNI/NetworkPolicy evidence captured; disk decision and replacement-host recovery remain pending |
| KIF-FUT-02 | KIF-002, KIF-003, KIF-007 | Host baseline safety/idempotence | Syntax/lint/check/diff pass before approval; two approved host-baseline runs converge and preserve recovery access | NOT RUN — runtime gate remains pending |
| KIF-FUT-03 | KIF-005, KIF-006, KIF-013, KIF-028 | OpenTofu state and plans | Format/validate pass; protected state recovers; reviewed plan has no secrets or unapproved destroy | NOT RUN — runtime gate remains pending |
| KIF-FUT-04 | KIF-005, KIF-009, KIF-022, KIF-023 | Render and GitOps reconciliation | Helm/Kustomize/schema checks pass; Argo reconciles private desired state and restores controlled drift | NOT RUN — runtime gate remains pending |
| KIF-FUT-05 | KIF-010, KIF-011, KIF-012, KIF-021 | Network exposure | Required private/public routes work and all DEV/admin/data negative public checks fail closed | NOT RUN — runtime gate remains pending |
| KIF-FUT-06 | KIF-013, KIF-014, KIF-015 | Secret lifecycle | Infisical sync/rotation/revocation and bootstrap recovery pass without plaintext disclosure | NOT RUN — runtime gate remains pending |
| KIF-FUT-07 | KIF-016, KIF-017, KIF-019, KIF-021 | PostgreSQL isolation | Each environment role reaches only its database; cross-environment access is denied and bounded | NOT RUN — runtime gate remains pending |
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
