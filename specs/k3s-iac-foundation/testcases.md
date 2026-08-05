# Test Cases — k3s IaC foundation

## Ansible-first discovery implementation — 2026-08-04

The offline contract tests and locked project-local `uv` validation do not invoke
SSH, become, the inventory host, Kubernetes API, a provider, or report generation.
`uv` and `ansible-galaxy` contacted package registries to resolve the ignored
`.venv` and local Galaxy collection path; nothing was installed on the inventory
host. Separately approved non-elevated and elevated runtime attempts are recorded
below; the dependency mutation remains unexecuted.

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-ANS-01 | KIF-001, KIF-004, KIF-008 | Ansible-first ownership | Operational Python collector is removed; minimal inventory, playbook, role, pinned collection, template, and Ansible documentation exist | PASS — layout contract test passed |
| KIF-ANS-02 | KIF-001, KIF-003 | Declarative read-only discovery | Host discovery uses setup/service_facts/stat; cluster discovery uses exact k8s_info queries; the discovery role contains no shell, command, raw, script, package, apt, or pip task | PASS — discovery module-boundary tests passed; the separate approved bootstrap is covered below |
| KIF-ANS-03 | KIF-001, KIF-002, KIF-007 | Invocation and elevation gates | Play fails without check/diff, explicit limit, and one selected host; become defaults false; elevated queries need both approval flags | PASS — approved positive non-elevated and elevated attempts passed the gates; negative invocation branches NOT RUN |
| KIF-ANS-04 | KIF-013, KIF-030 | Bounded data projection | Raw discovery registrations are no_log; fact cache is memory-only; report omits addresses, MACs, UUIDs, annotations, labels, environment fields, secrets, chart values, raw specs, command output, and kubeconfig content | PARTIAL — non-elevated report passed; elevated report safely recorded nine unavailable queries but captured no Kubernetes objects |
| KIF-ANS-05 | KIF-006, KIF-013 | Local report safety | Exactly one ignored controller-local JSON destination defaults under the repository root, mode 0600, diff disabled, become false, and symlink-refused | PASS — offline task/template contract and actual ignored mode-0600 report write passed; negative symlink runtime case remains offline-tested only |
| KIF-ANS-06 | KIF-008, KIF-021 | Kubernetes query boundary | Exact non-secret kinds provide object indicators; Secret, ConfigMap, Events, and broad all queries are absent; CNI and NetworkPolicy enforcement remain explicitly unproven | PASS — query boundary and template assertions passed |
| KIF-ANS-07 | KIF-007, KIF-030 | Ansible syntax and lint | Locked project tooling and the locally pinned collection pass syntax and production-profile lint before any host access | PASS — ansible-core 2.19.0 syntax check and ansible-lint 26.6.0 production profile passed; package-registry access only |
| KIF-ANS-08 | KIF-001, KIF-008 | Elevated cluster inventory capture | A separately approved one-host elevated check/diff run produces a human-reviewed host, datastore, and Kubernetes indicator report | PARTIAL — become succeeded and datastore exists, but all nine Kubernetes queries were unavailable; no cluster objects were captured |
| KIF-ANS-09 | KIF-006, KIF-007 | Reproducible controller environment | `pyproject.toml` and `uv.lock` pin the ignored project `.venv`; Galaxy installs the pinned collection only into the ignored local Ansible path | PASS — `uv sync --locked`, dependency-pin contract, ignore checks, and project-local Ansible commands passed |
| KIF-ANS-10 | KIF-001, KIF-007, KIF-030 | Approved non-elevated host discovery | Ansible ping and exactly one check/diff-limited host run pass; only the ignored controller-local report changes and receives human review | PASS — ping changed=false; play recap ok=14, changed=1 local report, failed=0, unreachable=0, skipped=1; valid JSON mode 0600 reviewed; no become or Kubernetes query |
| KIF-ANS-11 | KIF-001, KIF-008, KIF-030 | Elevated failure diagnosis | Human-reviewed elevated report and a bounded read-only import probe explain unavailable Kubernetes queries without emitting kubeconfig or secrets | PASS — datastore exists; nine queries unavailable; remote `kubernetes`, `yaml`, and `jsonpatch` imports all false |
| KIF-DEP-01 | KIF-002, KIF-007 | Approved dependency bootstrap contract | Separate one-host playbook requires explicit approval and directly requests only `python3-kubernetes` and `python3-jsonpatch`; no cache refresh, shell, command, latest, upgrade, or other direct package exists | PASS — contract test, syntax check, and production-profile lint passed |
| KIF-DEP-02 | KIF-002, KIF-007 | Dependency bootstrap execution | Check/diff package plan is reviewed before the approved actual installation; subsequent import probe and elevated discovery pass | PARTIAL — first check proposed 35 new, 0 upgraded/removed but omitted non-transitive jsonpatch, so it was not accepted; revised two-package check and installation NOT RUN |

## Documentation and traceability

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-DOC-01 | KIF-004, KIF-030 | Required shape and links | Canonical root/spec documents, locked uv project files, Ansible discovery files, and offline contract test exist; local Markdown links resolve | PASS — bounded offline documentation check passed |
| KIF-DOC-02 | KIF-005, KIF-009, KIF-022 | Ownership consistency | Ansible/OpenTofu/Argo CD/Infisical/GitHub Actions have non-overlapping owners; Traefik remains sole ingress | PASS — authoritative documents remain consistent |
| KIF-DOC-03 | KIF-001–KIF-003, KIF-006 | Honest implementation boundary | Only read-only discovery and the approved two-package bootstrap are implemented; the dependency mutation, hosted runtime, providers, Kubernetes desired state, and deployment are not claimed as executed | PASS — repository scan and status wording passed |
| KIF-DOC-04 | KIF-013–KIF-015 | No committed secret/address material | Repository source contains no private-key block, provider token, kubeconfig content, credential value, or private IPv4 address | PASS — bounded source scan passed |
| KIF-DOC-05 | KIF-016–KIF-021 | Shared-data and policy risk | Separate principals/backups and negative tests remain required; object listings do not prove policy enforcement | PASS — requirements and manual QA remain explicit |
| KIF-DOC-06 | KIF-023–KIF-030 | Honest future evidence | Twelve future runtime cases remain NOT RUN and twelve manual cases remain PENDING | PASS — counts and status assertions passed |

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
  ansible/roles/read_only_discovery/defaults/main.yml
  ansible/roles/read_only_discovery/tasks/main.yml
  ansible/roles/read_only_discovery/tasks/host.yml
  ansible/roles/read_only_discovery/tasks/kubernetes.yml
  ansible/roles/read_only_discovery/tasks/report.yml
  ansible/roles/read_only_discovery/templates/report.json.j2
  tests/test_ansible_contract.py
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
assert len(re.findall(r"^\| KIF-FUT-\d{2} .* \| NOT RUN —", (spec_dir / "testcases.md").read_text(), re.MULTILINE)) == 12
assert len(re.findall(r"^\| MQA-\d{2} .* \| PENDING \|$", (spec_dir / "manual-qa.md").read_text(), re.MULTILINE)) >= 12

status = (spec_dir / "status.md").read_text()
for statement in [
    "state: agent:in-progress",
    "phase: implementing",
    "elevated discovery attempted but 9 Kubernetes queries unavailable",
    "One explicitly approved SSH ping",
]:
    assert statement in status, statement

for future_path in [Path("opentofu"), Path("kubernetes"), Path("runbooks"), Path(".github/workflows")]:
    assert not future_path.exists(), future_path

for pattern in [
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\bghp_[A-Za-z0-9]+",
    r"\bgithub_pat_[A-Za-z0-9_]+",
    r"(?im)^\s*(?:certificate-authority-data|client-certificate-data|client-key-data|token):\s*\S+",
    r"\b(?:(?:[a-z0-9]+[-_])*(?:token|password|passwd|(?-i:pass)|secret|client[-_]secret|api[-_]key|credentials?|access[-_]key)(?:[-_][a-z0-9]+)*)\s*[=:]\s*['\"]?[^<{\s'\"\]]+",
    r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
    r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
    r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
]:
    assert not re.search(pattern, combined, re.IGNORECASE), pattern

for path in text_paths:
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        assert line == line.rstrip(), (path, line_number)

print("PASS: Ansible layout, links, 30 requirement IDs, 12 future cases, 12 manual cases, status/implementation boundary, and bounded source scan")
PY

git check-ignore -q --no-index inventory.local.ansible.json
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
Ran 12 tests
OK
PASS: Ansible layout, links, 30 requirement IDs, 12 future cases, 12 manual cases, status/implementation boundary, and bounded source scan
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
uv run ansible-lint playbooks roles/read_only_discovery
```

Actual result (exit 0 on 2026-08-05):

```text
kubernetes.core:6.1.0 was installed successfully to ansible/.ansible/collections
playbook: playbooks/discover.yml
playbook: playbooks/bootstrap_dependencies.yml
Passed: 0 failure(s), 0 warning(s) in 9 files processed; production profile
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
removals. It correctly included PyYAML transitively but omitted `python3-jsonpatch`,
which the import probe showed absent; therefore no installation was accepted or
run. A read-only apt-cache check found Debian candidate `1.32-5`, the operator
approved adding it explicitly, and the revised two-package playbook passed offline
validation. Its revised check/diff and actual installation remain NOT RUN. No
Kubernetes objects were captured, so cluster inventory and policy-enforcement gates
remain open.

## Future validation contract

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-FUT-01 | KIF-001, KIF-007, KIF-008, KIF-028 | Read-only Ansible discovery | Curated report proves actual k3s, storage, resource, and recovery indicators without mutation; human review passes | NOT RUN — runtime gate remains pending |
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
