#!/usr/bin/env bash
set -euo pipefail

readonly repository_root="$(CDPATH= cd -- "$(/usr/bin/dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly temporary_directory="$(/usr/bin/mktemp -d)"
readonly output_file="$temporary_directory/output.log"
readonly attestation_file="$temporary_directory/attestation"
readonly attestation_token="$(/usr/bin/openssl rand -hex 32)"
/bin/chmod 0700 "$temporary_directory"
printf '%s:entrypoint\n' "$attestation_token" >"$attestation_file"
/bin/chmod 0600 "$attestation_file"
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
CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1 \
  CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_TOKEN="$attestation_token" \
  CRISTEXWEB_FOUNDATION_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE="$attestation_file" \
  "$repository_root/.venv/bin/ansible-playbook" \
  -i "$temporary_directory/inventory.yml" \
  playbooks/bootstrap_foundation_namespaces.yml \
  --check --diff --limit crtxweb \
  --extra-vars foundation_namespace_bootstrap_approved=true \
  --start-at-task \
  'foundation_namespace_bootstrap : Create or reconcile only the approved foundation Namespaces' \
  >"$output_file" 2>&1
readonly status=$?
set -e

[[ $status -ne 0 ]]
[[ $(grep -Ec 'skipping: \[crtxweb\].*item=(platform-secrets|platform-identity)' "$output_file") -eq 2 ]]
! grep -Eq 'changed: \[crtxweb\].*item=(platform-secrets|platform-identity)' "$output_file"
! grep -Fq 'INTERNAL_VARIABLE_GUARD' "$output_file"
printf '%s\n' 'PASS: forged wrapper-format attestation cannot bypass the protected in-run preflight binding'
