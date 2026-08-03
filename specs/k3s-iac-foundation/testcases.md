# Test Cases — k3s IaC foundation

## Documentation foundation — 2026-08-03

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-DOC-01 | KIF-004, KIF-030 | Required documentation shape and links | All nine canonical Markdown files, `.gitignore`, the approved collector package, and its test file exist; all six spec files exist; local Markdown links resolve | PASS — nine Markdown files, `.gitignore`, three approved Python files, and six spec files found; local links resolved |
| KIF-DOC-02 | KIF-005, KIF-009, KIF-022 | Ownership and ingress consistency | Ansible/OpenTofu/Argo CD/Infisical/GitHub Actions have non-overlapping owners; Traefik is sole ingress | PASS — ownership and sole-ingress assertions found |
| KIF-DOC-03 | KIF-001–KIF-003, KIF-006 | Implementation boundary | The local read-only collector and tests are the only approved code; no Ansible, OpenTofu, Kubernetes, Helm, workflow, unexpected executable, or other implementation artifact exists | PASS — allowlisted-file and prohibited-artifact scans found no unexpected files |
| KIF-DOC-04 | KIF-013–KIF-015 | No secret or private address material | Repository text contains no private-key block, provider token, kubeconfig content, credential assignment value, or private IPv4 address | PASS — bounded pattern scan across approved text files returned no matches |
| KIF-DOC-05 | KIF-016–KIF-021 | Shared-data risk is explicit | Separate databases/principals/credentials/backups and negative access tests are required; shared failure domain remains documented | PASS — architecture, requirements, tasks, and QA agree |
| KIF-DOC-06 | KIF-026–KIF-030 | Honest evidence | Exactly 12 future runtime cases are NOT RUN, at least 12 manual cases are PENDING, and status is agent:in-progress/implementing with runtime inventory not run | PASS — 12 NOT RUN future cases, 12 PENDING manual cases, implementation status, and no-runtime statement found |
| KIF-DOC-07 | KIF-005, KIF-007 | Host automation standard | G1 explicitly uses Debian plus Ansible, defers NixOS, prefers built-in modules, and limits Python to justified, testable extensions | PASS — authoritative agent policy records the selected host path and Python learning guardrails |

## Stage 1 collector implementation — 2026-08-03

These are offline tests of the collector implementation. They do not execute an
inventory check against the actual server or cluster.

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-COL-01 | KIF-001, KIF-003, KIF-008 | Immutable allowlist safety and coverage | Only static argv tuples cover required host/k3s indicators; no sudo, shell, direct Secret/kubeconfig/token/process-environment display, or arbitrary file target exists; every kubectl command disables disk cache | PASS — allowlist, empty-cache, forbidden-target, findmnt-field, and coverage unit tests passed |
| KIF-COL-02 | KIF-013, KIF-030 | Best-effort sanitization | Host/root/sudo-user identities, local email, padded IP, colon/dotted MAC, broad UUID/filesystem/LVM IDs, credential assignments, and bearer values are redacted in every textual result field | PASS — extended sanitizer category, derived-hostname boundary, sudo-user, and recursive report unit tests passed |
| KIF-COL-03 | KIF-001, KIF-030 | Bounded subprocess outcomes | `shell=False`, fixed minimal environment, wall-clock timeout through reader completion, output bounds, and ok/nonzero/not-found/timeout statuses behave consistently | PASS — subprocess tests passed, including a detached descendant retaining pipes, without network, root, or k3s |
| KIF-COL-04 | KIF-001, KIF-030 | Deterministic report schema and partial results | Stable IDs and field shapes, versions, UTC time, privilege indicator, warning, and ordinary failed checks remain a valid report | PASS — schema, shape, warning, partial-result, and CLI collection unit tests passed |
| KIF-COL-05 | KIF-006, KIF-013 | Secure report output | JSON is atomically replaced at mode `0600`; symlink destinations are rejected; temp files are removed | PASS — secure atomic output unit tests passed |
| KIF-COL-06 | KIF-001, KIF-030 | Sudo ownership and identity | Valid ASCII Linux-range `SUDO_UID`/`SUDO_GID` use descriptor-based `fchown` and resolve the invoking username for sanitization; malformed, Unicode, huge, or spoofed non-root cases fail safely | PASS — mocked bounds, ownership, sudo-username, and clean collector-error tests passed; sudo was not executed |
| KIF-COL-07 | KIF-001, KIF-030 | CLI boundary | `--list-checks` performs no collection; collection requires `--local` and one output path; arbitrary/incomplete arguments fail | PASS — CLI list, collection, failure, and argument unit tests passed |
| KIF-COL-08 | KIF-008, KIF-021 | CNI/DNS/Traefik indicators | Interface/link, kube-system, DNS, Traefik, HelmChart, and NetworkPolicy-object checks are present without claiming policy enforcement | PASS — focused allowlist coverage passed; functional enforcement probes remain unexecuted and separately gated |
| KIF-COL-09 | KIF-001, KIF-008 | Actual inventory capture | Collector runs only after the applicable access/elevation approval and its report receives human review | NOT RUN — no collector execution, sudo, SSH, server, or cluster access occurred |

### Exact command and actual result

Run this exact offline validation block from the repository root. It lists checks
but deliberately does not invoke collection mode.

```bash
set -euo pipefail

required=(
  AGENTS.md
  README.md
  architecture-plan.md
  .gitignore
  tools/__init__.py
  tools/collect_inventory.py
  tests/test_collect_inventory.py
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

python3 -m unittest discover -s tests -v
python3 -m compileall -q tools tests
test_count=$(python3 - <<'PY'
import unittest
print(unittest.defaultTestLoader.discover("tests").countTestCases())
PY
)
check_count=$(python3 -m tools.collect_inventory --list-checks | python3 -c 'import json, sys; print(len(json.load(sys.stdin)))')
printf 'PASS: %s unit tests; compileall; %s allowlisted checks listed without collection\n' "$test_count" "$check_count"

python3 - <<'PY'
import re
from pathlib import Path

root_docs = [Path("AGENTS.md"), Path("README.md"), Path("architecture-plan.md")]
spec_dir = Path("specs/k3s-iac-foundation")
spec_names = {"brief.md", "requirements.md", "tasks.md", "testcases.md", "manual-qa.md", "status.md"}
spec_docs = sorted(spec_dir.glob("*.md"))
assert {path.name for path in spec_docs} == spec_names, spec_docs
doc_paths = root_docs + spec_docs
python_paths = [Path("tools/__init__.py"), Path("tools/collect_inventory.py"), Path("tests/test_collect_inventory.py")]
text_paths = doc_paths + python_paths + [Path(".gitignore")]
assert len(doc_paths) == 9, doc_paths
assert len(list(Path(".").glob("*.md"))) == 3
assert len(list(Path("specs").glob("**/*.md"))) == 6

for path in doc_paths:
    text = path.read_text()
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        local_target = target.split("#", 1)[0]
        if local_target:
            resolved = (path.parent / local_target).resolve()
            assert resolved.exists(), (path, target)

combined = "\n".join(path.read_text() for path in text_paths)
for term in [
    "Ansible",
    "OpenTofu",
    "Argo CD",
    "Infisical Cloud",
    "GitHub Actions",
    "private GHCR",
    "bundled k3s Traefik",
    "shared-data",
    "Cloudflare Tunnel",
    "Tailscale",
    "NixOS",
    "Ansible built-in modules",
    "Learning Python",
]:
    assert term in combined, term

expected_ids = {f"KIF-{number:03d}" for number in range(1, 31)}
for name in ["requirements.md", "testcases.md"]:
    found = set(re.findall(r"KIF-\d{3}", (spec_dir / name).read_text()))
    assert found == expected_ids, (name, sorted(expected_ids - found), sorted(found - expected_ids))

status = (spec_dir / "status.md").read_text()
assert "(G1)" in status
assert "state: agent:in-progress" in status
assert "phase: implementing" in status
assert "runtime inventory not run" in status

future = (spec_dir / "testcases.md").read_text()
assert len(re.findall(r"^\| KIF-FUT-\d{2} .* \| NOT RUN —", future, re.MULTILINE)) == 12
manual_qa = (spec_dir / "manual-qa.md").read_text()
assert len(re.findall(r"^\| MQA-\d{2} .* \| PENDING \|$", manual_qa, re.MULTILINE)) >= 12

for pattern in [
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\bghp_[A-Za-z0-9]+",
    r"\bgithub_pat_[A-Za-z0-9_]+",
    r"\b(?:(?:[a-z0-9]+[-_])*(?:token|password|passwd|pass|secret|client[-_]secret|api[-_]key|credentials?|access[-_]key)(?:[-_][a-z0-9]+)*)\s*[=:]\s*['\"][^<'\"]+['\"]",
    r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
    r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
    r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
]:
    assert not re.search(pattern, combined, re.IGNORECASE), pattern

for path in text_paths:
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        assert line == line.rstrip(), (path, line_number, "trailing whitespace")

print("PASS: 9 Markdown files + .gitignore + 3 Python files; 6 specs; links; 30 IDs; implementation boundary; 12 runtime NOT RUN; 12 PENDING; bounded scan clean")
PY

git check-ignore -q --no-index opentofu/cloudflare/.terraform/provider
git check-ignore -q --no-index opentofu/cloudflare/local.tfstate
git check-ignore -q --no-index opentofu/cloudflare/review.tfplan
git check-ignore -q --no-index opentofu/cloudflare/local.tfvars
git check-ignore -q --no-index ansible/site.retry
git check-ignore -q --no-index ansible/fact_cache/host
git check-ignore -q --no-index kubernetes/kubeconfig.local
git check-ignore -q --no-index runbooks/.env.local
git check-ignore -q --no-index runbooks/operator.key
git check-ignore -q --no-index kubernetes/generated-secrets/value
git check-ignore -q --no-index inventory.local.sanitized.json
git check-ignore -q --no-index inventory.raw.json
git check-ignore -q --no-index tools/__pycache__/collect_inventory.pyc
if git check-ignore -q --no-index opentofu/cloudflare/.terraform.lock.hcl; then
  exit 1
fi
if git check-ignore -q --no-index docs/inventory.sanitized.md; then
  exit 1
fi
printf '%s\n' 'PASS: protective ignore policy includes local reports/cache; sanitized documentation and .terraform.lock.hcl remain trackable'

unexpected=$(find . -type f \
  -not -path './.git/*' \
  -not -path './.pi-subagents/*' \
  -not -path '*/__pycache__/*' \
  -not -path './AGENTS.md' \
  -not -path './README.md' \
  -not -path './architecture-plan.md' \
  -not -path './.gitignore' \
  -not -path './tools/__init__.py' \
  -not -path './tools/collect_inventory.py' \
  -not -path './tests/test_collect_inventory.py' \
  -not -path './specs/k3s-iac-foundation/brief.md' \
  -not -path './specs/k3s-iac-foundation/requirements.md' \
  -not -path './specs/k3s-iac-foundation/tasks.md' \
  -not -path './specs/k3s-iac-foundation/testcases.md' \
  -not -path './specs/k3s-iac-foundation/manual-qa.md' \
  -not -path './specs/k3s-iac-foundation/status.md' \
  -print)
test -z "$unexpected"

if find . -type f \
  -not -path './.git/*' \
  -not -path './.pi-subagents/*' \
  -not -path '*/__pycache__/*' \
  \( -name '*.tf' -o -name '*.tfvars' -o -name '*.tfstate*' \
     -o -name 'Chart.yaml' -o -name 'kustomization.yaml' \
     -o -name 'playbook.yml' -o -name 'playbook.yaml' \
     -o -path '*/.github/workflows/*' -o -perm -111 \) \
  -print -quit | grep -q .; then
  exit 1
fi

git diff --check
git diff --cached --quiet
printf '%s\n' 'PASS: approved-file allowlist, prohibited-artifact scan, git diff --check, and no-staged-file check'
```

Actual result (exit 0 on 2026-08-03):

```text
Ran 33 tests in 0.4s
OK
PASS: 33 unit tests; compileall; 32 allowlisted checks listed without collection
PASS: 9 Markdown files + .gitignore + 3 Python files; 6 specs; links; 30 IDs; implementation boundary; 12 runtime NOT RUN; 12 PENDING; bounded scan clean
PASS: protective ignore policy includes local reports/cache; sanitized documentation and .terraform.lock.hcl remain trackable
PASS: approved-file allowlist, prohibited-artifact scan, git diff --check, and no-staged-file check
```

## Future validation contract

These runtime cases remain intentionally unexecuted by the collector implementation
deliverable. Provider-backed, elevated, or mutating commands require the matching
approval gate.

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-FUT-01 | KIF-001, KIF-007, KIF-008, KIF-028 | Read-only host/cluster discovery | Sanitized inventory proves actual k3s, network, storage, resource, and recovery state without mutation | NOT RUN — runtime gate remains pending |
| KIF-FUT-02 | KIF-002, KIF-003, KIF-007 | Ansible safety/idempotence | Lint/syntax/check/diff pass before approval; two approved runs converge and preserve recovery access | NOT RUN — runtime gate remains pending |
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

Exact commands and versions are selected only after discovery. Expected families:

```text
ansible-lint; ansible-playbook --syntax-check; ansible-playbook --check --diff
tofu fmt -check; tofu validate; reviewed tofu plan
helm template; kustomize build; kubeconform or an approved schema validator
argocd app diff/get/sync/rollback under the approved private access path
kubectl auth can-i and bounded positive/negative NetworkPolicy probes
database-native authorization, dump, integrity, and isolated restore checks
external reachability tests from both tailnet and non-tailnet clients
```

Tool absence is recorded as NOT RUN, never converted into a fabricated PASS.
