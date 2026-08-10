#!/usr/bin/env bash
set -euo pipefail
readonly repository_root="$(CDPATH= cd -- "$(/usr/bin/dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly temporary_directory="$(/usr/bin/mktemp -d)"
readonly output_file="$temporary_directory/output.log"
readonly attestation_file="$temporary_directory/attestation"
readonly token="$(/usr/bin/openssl rand -hex 32)"
/bin/chmod 0700 "$temporary_directory"
printf '%s:entrypoint\n' "$token" >"$attestation_file"
/bin/chmod 0600 "$attestation_file"
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
CRISTEXWEB_SHARED_DATABASE_PROVISIONING_ENTRYPOINT=v1 \
CRISTEXWEB_SHARED_DATABASE_PROVISIONING_TOKEN="$token" \
CRISTEXWEB_SHARED_DATABASE_PROVISIONING_ATTESTATION_FILE="$attestation_file" \
  "$repository_root/.venv/bin/ansible-playbook" -i "$temporary_directory/inventory.yml" \
  playbooks/provision_shared_postgresql.yml --check --diff --limit crtxweb \
  --extra-vars '{"shared_postgresql_provisioning_approved":true}' \
  --start-at-task 'shared_postgresql_provisioning : Run the read-only PostgreSQL logical-state check first' >"$output_file" 2>&1
readonly status=$?
set -e
[[ $status -ne 0 ]]
grep -Eq 'TASK_SELECTION_GUARD|ENTRYPOINT_GUARD' "$output_file"
! grep -Fq 'Failed to connect' "$output_file"
printf '%s\n' 'PASS: shared database provisioning task-selection bypass is rejected'
