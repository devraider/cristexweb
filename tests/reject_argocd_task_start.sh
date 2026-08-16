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
argocd_bootstrap_approved: true
argocd_bootstrap_internal_preflight_binding:
  attestation_sha256: $attestation_sha256
  object_count: 32
  identity_set_sha256: 53672a1267926abdbe773a90cfaa84cf958b343fde292c1c2d2e199f2c16778c
  crd_count: 3
  prestate_count: 32
  deferred_custom_resource_count: 0
  secret_count: 3
  namespace_contract: true
  service_contract: true
argocd_bootstrap_internal_crds:
YAML
awk 'NR == 1 && $0 == "---" { next } !started { print "  - " $0; started = 1; next } { print "    " $0 }' \
  "$repository_root/ansible/files/components/argocd/crds/applications.argoproj.io.yaml" >>"$injected_variables"
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
CRISTEXWEB_REPOSITORY_ROOT="$repository_root" \
CRISTEXWEB_ARGOCD_BOOTSTRAP_ENTRYPOINT=v1 \
CRISTEXWEB_ARGOCD_BOOTSTRAP_TOKEN="$attestation_token" \
CRISTEXWEB_ARGOCD_BOOTSTRAP_ATTESTATION_FILE="$attestation_file" \
  "$repository_root/.venv/bin/ansible-playbook" -i "$temporary_directory/inventory.yml" \
  playbooks/bootstrap_argocd.yml --check --diff --limit crtxweb \
  --extra-vars "@$injected_variables" --start-at-task \
  'argocd_bootstrap : Reconcile exact Argo CD CRD prerequisites' >"$output_file" 2>&1
readonly status=$?
set -e
[[ $status -ne 0 ]]
grep -Fq 'TASK_SELECTION_GUARD' "$output_file"
! grep -Fq 'INTERNAL_VARIABLE_GUARD' "$output_file"
printf '%s\n' 'PASS: Argo CD combined task-start and injected-binding bypass is rejected'
