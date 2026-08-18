#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
ANSIBLE_PLAYBOOK=${ANSIBLE_PLAYBOOK:-$ROOT/.venv/bin/ansible-playbook}
ANSIBLE_CONFIG=${ANSIBLE_CONFIG:-$ROOT/ansible/ansible.cfg}
TOKEN=$(printf 'b%.0s' $(seq 1 64))
ATTESTATION=$(mktemp)
trap 'rm -f "$ATTESTATION"' EXIT
printf '%s:entrypoint\n' "$TOKEN" >"$ATTESTATION"
chmod 600 "$ATTESTATION"

set +e
wrapper_output=$($ROOT/ansible/bin/bootstrap-postgresql check --start-at-task 2>&1)
wrapper_status=$?
set -e
[ "$wrapper_status" -eq 64 ]
printf '%s\n' "$wrapper_output" | grep -F 'refusing passthrough arguments' >/dev/null

set +e
output=$(
  cd "$ROOT/ansible" &&
  ANSIBLE_CONFIG="$ANSIBLE_CONFIG" \
  CRISTEXWEB_POSTGRESQL_BOOTSTRAP_ENTRYPOINT=v1 \
  CRISTEXWEB_POSTGRESQL_BOOTSTRAP_TOKEN="$TOKEN" \
  CRISTEXWEB_POSTGRESQL_BOOTSTRAP_ATTESTATION_FILE="$ATTESTATION" \
  "$ANSIBLE_PLAYBOOK" playbooks/bootstrap_postgresql.yml \
    -i .ansible/inventory.local.yml --limit crtxweb --diff \
    --start-at-task 'Reconcile only the approved PostgreSQL objects' \
    --extra-vars '{"postgresql_bootstrap_approved":true,"postgresql_bootstrap_state":"present","postgresql_bootstrap_internal_preflight_binding":{"object_count":6,"prestate_count":6,"identity_set_sha256":"29c7c24d94405550370d3528c12df31e6beeea06dda23edfba417d3e15a8baf4","secret_count":2,"pvc_prestate_count":0,"namespace_contract":true,"storage_contract":true,"service_contract":true,"no_delete_path":true,"k3s_state":"running","tailscale_state":"running"},"postgresql_bootstrap_internal_manifests":[{"apiVersion":"v1","kind":"ConfigMap","metadata":{"name":"shared-postgresql-pg-hba","namespace":"shared-services"},"data":{"pg_hba.conf":"forged"}}]}' 2>&1
)
status=$?
set -e
[ "$status" -ne 0 ]
if ! printf '%s\n' "$output" | grep -E '(TASK_SELECTION_GUARD|ENTRYPOINT_GUARD)' >/dev/null; then
  printf '%s\n' "$output" >&2
  exit 1
fi
if printf '%s\n' "$output" | grep -F 'Failed to connect to the host via ssh' >/dev/null; then
  printf '%s\n' "$output" >&2
  exit 1
fi
