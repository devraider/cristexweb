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
cristexhub_dev_namespace_bootstrap_approved: true
cristexhub_dev_namespace_bootstrap_internal_preflight_binding:
  attestation_sha256: $attestation_sha256
  manifest_names:
    - cristexhub-dev
  prestate_names:
    - cristexhub-dev
  controller_path_count: 4
  manifest_path_count: 1
  kubeconfig_contract: true
  service_contract: true
YAML
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
CRISTEXWEB_CRISTEXHUB_DEV_NAMESPACE_BOOTSTRAP_ENTRYPOINT=v1 \
  CRISTEXWEB_CRISTEXHUB_DEV_NAMESPACE_BOOTSTRAP_TOKEN="$attestation_token" \
  CRISTEXWEB_CRISTEXHUB_DEV_NAMESPACE_BOOTSTRAP_ATTESTATION_FILE="$attestation_file" \
  "$repository_root/.venv/bin/ansible-playbook" \
  -i "$temporary_directory/inventory.yml" \
  playbooks/bootstrap_cristexhub_dev_namespace.yml \
  --check --diff --limit crtxweb \
  --extra-vars "@$injected_variables" \
  --start-at-task \
  'cristexhub_dev_namespace_bootstrap : Create or reconcile only the approved CristexHub DEV Namespace' \
  >"$output_file" 2>&1
readonly status=$?
set -e

[[ $status -ne 0 ]]
grep -Fq 'TASK_SELECTION_GUARD' "$output_file"
! grep -Eq 'changed: \[crtxweb\].*item=cristexhub-dev' "$output_file"
! grep -Fq 'INTERNAL_VARIABLE_GUARD' "$output_file"
printf '%s\n' 'PASS: combined task-start and injected-binding bypass is rejected before the Kubernetes module'
