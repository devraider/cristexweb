#!/usr/bin/env bash
set -euo pipefail
readonly repository_root="$(CDPATH= cd -- "$(/usr/bin/dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly temporary_directory="$(/usr/bin/mktemp -d)"
readonly output_file="$temporary_directory/output.log"
readonly attestation_file="$temporary_directory/attestation"
readonly attestation_token="$(/usr/bin/openssl rand -hex 32)"
readonly attestation_sha256="$(printf '%s' "$attestation_token" | /usr/bin/shasum -a 256 | /usr/bin/awk '{print $1}')"
readonly injected_variables="$temporary_directory/injected-variables.yml"
/bin/chmod 0700 "$temporary_directory"
printf '%s:entrypoint\n' "$attestation_token" >"$attestation_file"
/bin/chmod 0600 "$attestation_file"
cat >"$injected_variables" <<YAML
infisical_operator_bootstrap_approved: true
infisical_operator_bootstrap_internal_preflight_binding:
  attestation_sha256: $attestation_sha256
  object_count: 40
  crd_count: 6
  prestate_count: 40
  proxy_secret_count: 3
  api_service_contract: true
  service_contract: true
infisical_operator_bootstrap_internal_crds:
YAML
awk '\
  NR == 1 && $0 == "---" { next } \
  !started { print "  - " $0; started = 1; next } \
  { print "    " $0 }' \
  "$repository_root/ansible/files/components/infisical-operator/crds/infisicalauths.yaml" \
  >>"$injected_variables"
cleanup() { /bin/rm -rf -- "$temporary_directory"; }
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
CRISTEXWEB_INFISICAL_BOOTSTRAP_ENTRYPOINT=v1 \
CRISTEXWEB_INFISICAL_BOOTSTRAP_TOKEN="$attestation_token" \
CRISTEXWEB_INFISICAL_BOOTSTRAP_ATTESTATION_FILE="$attestation_file" \
  "$repository_root/.venv/bin/ansible-playbook" \
  -i "$temporary_directory/inventory.yml" \
  playbooks/bootstrap_infisical_operator.yml \
  --check --diff --limit crtxweb \
  --extra-vars "@$injected_variables" \
  --start-at-task \
  'infisical_operator_bootstrap : Reconcile only the six approved Infisical CRDs' \
  >"$output_file" 2>&1
readonly status=$?
set -e
[[ $status -ne 0 ]]
grep -Fq 'TASK_SELECTION_GUARD' "$output_file"
! grep -Fq 'INTERNAL_VARIABLE_GUARD' "$output_file"
printf '%s\n' 'PASS: Infisical combined task-start and injected-binding bypass is rejected'
