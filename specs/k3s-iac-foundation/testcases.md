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
| KIF-STO-02 | KIF-001, KIF-008, KIF-030 | Extended storage discovery runtime | A separately approved one-host elevated check/diff run renders valid mode-0600 JSON and human review establishes actual curated device, StorageClass, PV, and PVC indicators without mutation or sensitive metadata | NOT RUN — implementation and validation were controller-local only; the prior nine-query elevated report remains unchanged and no new disk or PV/PVC placement fact is claimed |
| KIF-REC-01 | KIF-002, KIF-003, KIF-013, KIF-015, KIF-028, KIF-030 | Replacement-host recovery first offline increment | Secret-free runbook/register truthfully separate same-host reboot from replacement, require old-host fencing and exclusive storage ownership, stop split brain, require exactly one preserve-existing or create-new identity decision, and leave datastore/version/token/storage/RPO/RTO/off-node prerequisites explicitly unknown without guessed commands | PASS — 5 focused offline recovery contracts and the full offline suite passed; documentation contains no executable recovery command or secret-shaped value and no host/provider/API was accessed |
| KIF-REC-02 | KIF-007, KIF-015, KIF-026–KIF-030 | Replacement-host recovery rehearsal/runtime | An isolated, approved replacement follows an actual version/datastore/storage-specific plan; proves one authoritative cluster/storage writer, desired state, mutable data, encryption behavior, isolation, and measured RPO/RTO before public reactivation | NOT RUN/BLOCKED — identity model and datastore, exact version/config, token custody, storage, RPO/RTO, off-node artifacts, restore procedures, and approvals remain `UNKNOWN — STOP`; reboot success is not replacement proof |

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
commands. Runtime storage evidence remains NOT RUN pending separate host-access and
elevation approval.

## Documentation and traceability

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-DOC-01 | KIF-004, KIF-030 | Required shape and links | Canonical root/spec documents, locked uv project files, Ansible discovery files, and offline contract test exist; local Markdown links resolve | PASS — bounded offline documentation check passed |
| KIF-DOC-02 | KIF-005, KIF-009, KIF-022 | Ownership consistency | Ansible/OpenTofu/Argo CD/Infisical/GitHub Actions have non-overlapping owners; Traefik remains sole ingress | PASS — authoritative documents remain consistent |
| KIF-DOC-03 | KIF-001–KIF-003, KIF-006 | Honest implementation boundary | Discovery, dependency bootstrap, admin access, user-scoped client defaults, and one-reboot recovery are executed; no other host baseline, hosted runtime, provider, Kubernetes desired state, or deployment is claimed | PASS — repository scan and status wording passed |
| KIF-DOC-04 | KIF-013–KIF-015 | No committed secret/address material | Repository source contains no private-key block, provider token, kubeconfig content, credential value, or private IPv4 address | PASS — bounded source scan passed |
| KIF-DOC-05 | KIF-016–KIF-021 | Shared-data and policy risk | Separate principals/backups and negative tests remain required; object listings do not prove policy enforcement | PASS — requirements and manual QA remain explicit |
| KIF-DOC-06 | KIF-023–KIF-030 | Honest future evidence | One future discovery case is PARTIAL, eleven future runtime cases remain NOT RUN, and thirteen manual cases remain PENDING | PASS — counts and status assertions passed |

All requirements KIF-001 through KIF-030 remain represented by the implementation,
documentation, manual, or future-runtime cases in this file. Offline implementation
success does not close any runtime gate.

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
  ansible/roles/read_only_discovery/defaults/main.yml
  ansible/roles/read_only_discovery/tasks/main.yml
  ansible/roles/read_only_discovery/tasks/host.yml
  ansible/roles/read_only_discovery/tasks/kubernetes.yml
  ansible/roles/read_only_discovery/tasks/report.yml
  ansible/roles/read_only_discovery/templates/report.json.j2
  tests/test_ansible_contract.py
  tests/test_replacement_recovery_contract.py
  runbooks/replacement-host-recovery.md
  runbooks/recovery-artifact-register.md
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
text_paths += sorted(Path("tests").glob("*.py"))
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
assert len(re.findall(r"^\| MQA-\d{2} .* \| PENDING \|$", (spec_dir / "manual-qa.md").read_text(), re.MULTILINE)) == 13
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
    "admin/client/reboot recovery and live CNI/NetworkPolicy probe pass",
    "all nine exact Kubernetes",
    "executed group-scoped k3s",
]:
    assert statement in status, statement

for future_path in [Path("opentofu"), Path("kubernetes"), Path(".github/workflows")]:
    assert not future_path.exists(), future_path
for recovery_doc in [
    Path("runbooks/replacement-host-recovery.md"),
    Path("runbooks/recovery-artifact-register.md"),
]:
    assert recovery_doc.is_file(), recovery_doc

for pattern in [
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\bghp_[A-Za-z0-9]+",
    r"\bgithub_pat_[A-Za-z0-9_]+",
    r"(?im)^\s*(?:certificate-authority-data|client-certificate-data|client-key-data|token):\s*\S+",
    r"\b(?!network_policy_probe_[a-z0-9_]*_pass\s*[=:])(?:(?:[a-z0-9]+[-_])*(?:token|password|passwd|(?-i:pass)|secret|client[-_]secret|api[-_]key|credentials?|access[-_]key)(?:[-_][a-z0-9]+)*)\s*[=:]\s*['\"]?[^<{\s'\"\]]+",
    r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
    r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
    r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
]:
    assert not re.search(pattern, combined, re.IGNORECASE), pattern

for path in text_paths:
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        assert line == line.rstrip(), (path, line_number)

print("PASS: Ansible layout, links, 30 requirement IDs, 12 future cases, 13 manual cases, status/implementation boundary, and bounded source scan")
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

Actual result (exit 0 on 2026-08-05):

```text
Ran 28 tests
OK
PASS: Ansible layout, links, 30 requirement IDs, 12 future cases, 13 manual cases, status/implementation boundary, and bounded source scan
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
| KIF-FUT-01 | KIF-001, KIF-007, KIF-008, KIF-028 | Read-only Ansible discovery | Curated report proves actual k3s, storage, resource, and recovery indicators without mutation; human review passes | PARTIAL — host, datastore, capacity, reboot recovery, Kubernetes object indicators, and functional CNI/NetworkPolicy evidence captured; extended storage and replacement-host recovery remain pending |
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
