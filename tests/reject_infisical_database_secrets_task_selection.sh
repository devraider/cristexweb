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
infisical_database_secrets_bootstrap_approved: true
infisical_database_secrets_bootstrap_internal_preflight_binding:
  attestation_sha256: $attestation_sha256
  object_count: 13
  identity_set_sha256: 9101cb207aaa89c2036770a26229ab6d23d1af19ec13486d507440aadee6c4fc
  prestate_count: 13
  admission_count: 6
  rbac_count: 2
  source_count: 5
  alternate_target_count: 3
  static_secret_inventory_count: 0
  credential_contract: true
  target_contract: true
  namespace_contract: true
  crd_count: 6
infisical_database_secrets_bootstrap_internal_rbac_objects:
YAML
for manifest in \
  "$repository_root/ansible/files/components/infisical-database-secrets/rbac/infisical-database-secret-writer-role.yaml" \
  "$repository_root/ansible/files/components/infisical-database-secrets/rbac/infisical-database-secret-writer-rolebinding.yaml"; do
  awk 'NR == 1 && $0 == "---" { next } !started { print "  - " $0; started = 1; next } { print "    " $0 }' "$manifest" >>"$injected_variables"
done
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
CRISTEXWEB_INFISICAL_DATABASE_SECRETS_BOOTSTRAP_ENTRYPOINT=v1 \
CRISTEXWEB_INFISICAL_DATABASE_SECRETS_BOOTSTRAP_TOKEN="$attestation_token" \
CRISTEXWEB_INFISICAL_DATABASE_SECRETS_BOOTSTRAP_ATTESTATION_FILE="$attestation_file" \
  "$repository_root/.venv/bin/ansible-playbook" -i "$temporary_directory/inventory.yml" \
  playbooks/bootstrap_infisical_database_secrets.yml --check --diff --limit crtxweb \
  --extra-vars "@$injected_variables" --start-at-task \
  'infisical_database_secrets_bootstrap : Reconcile exact Infisical database Secret seam RBAC after admission' >"$output_file" 2>&1
readonly status=$?
set -e
[[ $status -ne 0 ]]
grep -Eq 'TASK_SELECTION_GUARD|ENTRYPOINT_GUARD' "$output_file"
! grep -Fq 'INTERNAL_VARIABLE_GUARD' "$output_file"
printf '%s\n' 'PASS: Infisical database Secret seam task-selection and injected-binding bypass is rejected'
