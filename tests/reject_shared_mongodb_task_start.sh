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
mongodb_bootstrap_approved: true
mongodb_bootstrap_state: present
mongodb_bootstrap_internal_preflight_binding:
  attestation_sha256: $attestation_sha256
  object_count: 5
  identity_set_sha256: 2dafb88dd68d2031c0e558a9c8b18b2ee5bdd6c6f7116163e222c7dbe71c470e
  prestate_count: 5
  secret_count: 2
  pvc_prestate_count: 0
  namespace_contract: true
  storage_contract: true
  service_contract: true
  no_delete_path: true
mongodb_bootstrap_internal_runtime_objects:
YAML
awk 'NR == 1 && $0 == "---" { next } !started { print "  - " $0; started = 1; next } { print "    " $0 }' \
  "$repository_root/ansible/files/components/mongodb/network/mongodb-default-deny.yaml" >>"$injected_variables"
cleanup() { /bin/rm -rf -- "$temporary_directory"; }
trap cleanup EXIT HUP INT TERM
cat >"$temporary_directory/inventory.yml" <<'YAML'
all:
  hosts:
    crtxweb:
      ansible_connection: local
      ansible_become: false
YAML
cd -- "$repository_root/ansible"
set +e
CRISTEXWEB_MONGODB_BOOTSTRAP_ENTRYPOINT=v1 \
CRISTEXWEB_MONGODB_BOOTSTRAP_TOKEN="$attestation_token" \
CRISTEXWEB_MONGODB_BOOTSTRAP_ATTESTATION_FILE="$attestation_file" \
  "$repository_root/.venv/bin/ansible-playbook" -i "$temporary_directory/inventory.yml" \
  playbooks/bootstrap_mongodb.yml --check --diff --limit crtxweb \
  --extra-vars "@$injected_variables" --start-at-task \
  'mongodb_bootstrap : Reconcile only the exact MongoDB object closure' >"$output_file" 2>&1
readonly status=$?
set -e
[[ $status -ne 0 ]]
grep -Eq '(TASK_SELECTION_GUARD|ENTRYPOINT_GUARD)' "$output_file" || {
  /bin/cat "$output_file" >&2
  exit 1
}
! grep -Fq 'INTERNAL_VARIABLE_GUARD' "$output_file"
! grep -Fq 'Failed to connect' "$output_file"
printf '%s\n' 'PASS: MongoDB combined task-start and injected-binding bypass is rejected'
