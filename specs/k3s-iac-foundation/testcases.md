# Test Cases — k3s IaC foundation

## Documentation foundation — 2026-08-03

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-DOC-01 | KIF-004, KIF-030 | Required documentation shape and links | All nine canonical Markdown files plus `.gitignore` exist; all six spec files exist; local Markdown links resolve | PASS — nine Markdown files, `.gitignore`, and six spec files found; local links resolved |
| KIF-DOC-02 | KIF-005, KIF-009, KIF-022 | Ownership and ingress consistency | Ansible/OpenTofu/Argo CD/Infisical/GitHub Actions have non-overlapping owners; Traefik is sole ingress | PASS — ownership and sole-ingress assertions found |
| KIF-DOC-03 | KIF-001–KIF-003, KIF-006 | Documentation-only boundary | No executable Ansible, OpenTofu, Kubernetes, Helm, workflow, or other implementation artifact exists | PASS — canonical-file and implementation-artifact scans found no unexpected files |
| KIF-DOC-04 | KIF-013–KIF-015 | No secret or private address material | Documentation contains no private-key block, provider token, kubeconfig content, credential assignment, or private IPv4 address | PASS — bounded pattern scan returned no matches |
| KIF-DOC-05 | KIF-016–KIF-021 | Shared-data risk is explicit | Separate databases/principals/credentials/backups and negative access tests are required; shared failure domain remains documented | PASS — architecture, requirements, tasks, and QA agree |
| KIF-DOC-06 | KIF-026–KIF-030 | Honest evidence | Exactly 12 future cases are NOT RUN, at least 12 manual cases are PENDING, and status remains backlog/planned | PASS — 12 NOT RUN future cases, 12 PENDING manual cases, and backlog/planned status found |

### Exact command and actual result

Run this exact offline validation block from the repository root:

```bash
set -euo pipefail

required=(
  AGENTS.md
  README.md
  architecture-plan.md
  .gitignore
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

python3 - <<'PY'
import re
from pathlib import Path

root_docs = [Path("AGENTS.md"), Path("README.md"), Path("architecture-plan.md")]
spec_dir = Path("specs/k3s-iac-foundation")
spec_names = {"brief.md", "requirements.md", "tasks.md", "testcases.md", "manual-qa.md", "status.md"}
spec_docs = sorted(spec_dir.glob("*.md"))
assert {path.name for path in spec_docs} == spec_names, spec_docs
paths = root_docs + spec_docs
assert len(paths) == 9, paths
assert len(list(Path(".").glob("*.md"))) == 3
assert len(list(Path("specs").glob("**/*.md"))) == 6

for path in paths:
    text = path.read_text()
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        local_target = target.split("#", 1)[0]
        if local_target:
            resolved = (path.parent / local_target).resolve()
            assert resolved.exists(), (path, target)

combined = "\n".join(path.read_text() for path in paths)
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
]:
    assert term in combined, term

expected_ids = {f"KIF-{number:03d}" for number in range(1, 31)}
for name in ["requirements.md", "testcases.md"]:
    found = set(re.findall(r"KIF-\d{3}", (spec_dir / name).read_text()))
    assert found == expected_ids, (name, sorted(expected_ids - found), sorted(found - expected_ids))

status = (spec_dir / "status.md").read_text()
assert "(G1)" in status
assert "state: backlog" in status
assert "phase: planned" in status
assert "implementation and runtime validation not run" in status

future = (spec_dir / "testcases.md").read_text()
assert len(re.findall(r"^\| KIF-FUT-\d{2} .* \| NOT RUN —", future, re.MULTILINE)) == 12
manual_qa = (spec_dir / "manual-qa.md").read_text()
assert len(re.findall(r"^\| MQA-\d{2} .* \| PENDING \|$", manual_qa, re.MULTILINE)) >= 12

for pattern in [
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\bghp_[A-Za-z0-9]+",
    r"\bgithub_pat_[A-Za-z0-9_]+",
    r"\b(?:token|password|client_secret|api_key)\s*[=:]\s*['\"][^<'\"]+['\"]",
    r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
    r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
    r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
]:
    assert not re.search(pattern, combined, re.IGNORECASE), pattern

for path in paths + [Path(".gitignore")]:
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        assert line == line.rstrip(), (path, line_number, "trailing whitespace")

print("PASS: 9 Markdown files + .gitignore; 6 specs; links resolved; 30 IDs in requirements/testcases; 12 NOT RUN; 12 PENDING; bounded scan clean")
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
if git check-ignore -q --no-index opentofu/cloudflare/.terraform.lock.hcl; then
  exit 1
fi
printf '%s\n' 'PASS: protective ignore policy; .terraform.lock.hcl remains trackable'

unexpected=$(find . -type f \
  -not -path './.git/*' \
  -not -path './.pi-subagents/*' \
  -not -path './AGENTS.md' \
  -not -path './README.md' \
  -not -path './architecture-plan.md' \
  -not -path './.gitignore' \
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
  \( -name '*.tf' -o -name '*.tfvars' -o -name '*.tfstate*' \
     -o -name 'Chart.yaml' -o -name 'kustomization.yaml' \
     -o -name 'playbook.yml' -o -name 'playbook.yaml' \
     -o -path '*/.github/workflows/*' -o -perm -111 \) \
  -print -quit | grep -q .; then
  exit 1
fi

git diff --check
git diff --cached --quiet
printf '%s\n' 'PASS: implementation-artifact scan, git diff --check, and no-staged-file check'
```

Actual result (exit 0):

```text
PASS: 9 Markdown files + .gitignore; 6 specs; links resolved; 30 IDs in requirements/testcases; 12 NOT RUN; 12 PENDING; bounded scan clean
PASS: protective ignore policy; .terraform.lock.hcl remains trackable
PASS: implementation-artifact scan, git diff --check, and no-staged-file check
```

## Future validation contract

These cases are intentionally not executed by the documentation milestone.
Provider-backed or mutating commands require the matching approval gate.

| ID | Requirements | Scenario | Expected | Actual |
|---|---|---|---|---|
| KIF-FUT-01 | KIF-001, KIF-007, KIF-008, KIF-028 | Read-only host/cluster discovery | Sanitized inventory proves actual k3s, network, storage, resource, and recovery state without mutation | NOT RUN — milestone backlog |
| KIF-FUT-02 | KIF-002, KIF-003, KIF-007 | Ansible safety/idempotence | Lint/syntax/check/diff pass before approval; two approved runs converge and preserve recovery access | NOT RUN — milestone backlog |
| KIF-FUT-03 | KIF-005, KIF-006, KIF-013, KIF-028 | OpenTofu state and plans | Format/validate pass; protected state recovers; reviewed plan has no secrets or unapproved destroy | NOT RUN — milestone backlog |
| KIF-FUT-04 | KIF-005, KIF-009, KIF-022, KIF-023 | Render and GitOps reconciliation | Helm/Kustomize/schema checks pass; Argo reconciles private desired state and restores controlled drift | NOT RUN — milestone backlog |
| KIF-FUT-05 | KIF-010, KIF-011, KIF-012, KIF-021 | Network exposure | Required private/public routes work and all DEV/admin/data negative public checks fail closed | NOT RUN — milestone backlog |
| KIF-FUT-06 | KIF-013, KIF-014, KIF-015 | Secret lifecycle | Infisical sync/rotation/revocation and bootstrap recovery pass without plaintext disclosure | NOT RUN — milestone backlog |
| KIF-FUT-07 | KIF-016, KIF-017, KIF-019, KIF-021 | PostgreSQL isolation | Each environment role reaches only its database; cross-environment access is denied and bounded | NOT RUN — milestone backlog |
| KIF-FUT-08 | KIF-016, KIF-018, KIF-019, KIF-021 | MongoDB isolation | Each environment user reaches only its database; cross-environment access is denied and bounded | NOT RUN — milestone backlog |
| KIF-FUT-09 | KIF-020, KIF-021 | Redis/RabbitMQ isolation | Redis is environment-local; RabbitMQ users/vhosts and limits prevent cross-environment access | NOT RUN — milestone backlog |
| KIF-FUT-10 | KIF-022, KIF-023, KIF-024, KIF-025 | Immutable build and promotion | CI publishes once, DEV deploys a digest, and reviewed PROD promotion uses the identical digest | NOT RUN — milestone backlog |
| KIF-FUT-11 | KIF-026, KIF-027, KIF-028 | Backup and restore | Encrypted local/off-node backups pass integrity and isolated restore within declared RPO/RTO | NOT RUN — milestone backlog |
| KIF-FUT-12 | KIF-025, KIF-029, KIF-030 | DEV/PROD operations | DEV soak, private PROD, resource headroom, alerts, rollback, and public-last cutover all pass | NOT RUN — milestone backlog |

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
