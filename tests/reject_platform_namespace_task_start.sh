#!/usr/bin/env bash
set -euo pipefail

readonly repository_root="$(CDPATH= cd -- "$(/usr/bin/dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly temporary_directory="$(/usr/bin/mktemp -d)"
readonly output_file="$temporary_directory/output.log"
cleanup() {
  /bin/rm -rf -- "$temporary_directory"
}
trap cleanup EXIT HUP INT TERM

cat >"$temporary_directory/inventory.yml" <<'YAML'
all:
  children:
    k3s_servers:
      hosts:
        crtxweb:
          ansible_connection: local
          ansible_become: false
YAML

cd -- "$repository_root/ansible"
set +e
CRISTEXWEB_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1 \
  "$repository_root/.venv/bin/ansible-playbook" \
  -i "$temporary_directory/inventory.yml" \
  playbooks/bootstrap_platform_namespaces.yml \
  --check --diff --limit crtxweb \
  --extra-vars platform_namespace_bootstrap_approved=true \
  --start-at-task \
  'platform_namespace_bootstrap : Create or reconcile only the approved platform Namespaces' \
  >"$output_file" 2>&1
readonly status=$?
set -e

[[ $status -ne 0 ]]
[[ $(grep -Ec 'skipping: \[crtxweb\].*item=(argocd|platform-edge)' "$output_file") -eq 2 ]]
! grep -Eq 'changed: \[crtxweb\].*item=(argocd|platform-edge)' "$output_file"
! grep -Fq 'INTERNAL_VARIABLE_GUARD' "$output_file"
printf '%s\n' 'PASS: direct task-start cannot mutate without the private single-run wrapper attestation'
