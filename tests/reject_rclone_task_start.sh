#!/usr/bin/env bash
set -euo pipefail
repository_root="$(CDPATH= cd -- "$(/usr/bin/dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
temporary_directory="$(/usr/bin/mktemp -d)"
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
run_negative() {
  component=$1
  playbook=$2
  task=$3
  entrypoint=$4
  token_name=$5
  attestation_name=$6
  token="$(/usr/bin/openssl rand -hex 32)"
  token_sha256="$(printf '%s' "$token" | /usr/bin/shasum -a 256 | /usr/bin/awk '{print $1}')"
  attestation="$temporary_directory/$component.attestation"
  variables="$temporary_directory/$component.yml"
  printf '%s:entrypoint\n' "$token" >"$attestation"
  /bin/chmod 0600 "$attestation"
  if [[ "$component" == install ]]; then
    cat >"$variables" <<YAML
rclone_install_approved: true
rclone_install_rollback_approved: false
rclone_install_state: present
rclone_install_internal_preflight_binding:
  attestation_sha256: $token_sha256
  service_contract: true
  platform_contract: true
YAML
  else
    cat >"$variables" <<YAML
rclone_proxy_transfer_approved: true
rclone_proxy_transfer_cleanup_approved: false
rclone_proxy_transfer_state: transfer
rclone_proxy_transfer_internal_preflight_binding:
  attestation_sha256: $token_sha256
  ciphertext_sha256: 3562c730814440dc836c3f38d34efc41f0ca6f180635135ba92314990b121d28
  remote_directory: drive:cristexweb-recovery/infisical-proxy/20260810T095421Z
  operator_home: /home/fixture
  service_contract: true
YAML
  fi
  set +e
  env "$entrypoint=v1" "$token_name=$token" "$attestation_name=$attestation" \
    "$repository_root/.venv/bin/ansible-playbook" \
    -i "$temporary_directory/inventory.yml" "playbooks/$playbook" \
    --diff --limit crtxweb --start-at-task "$task" \
    --extra-vars "@$variables" >"$temporary_directory/$component.log" 2>&1
  status=$?
  set -e
  [[ $status -ne 0 ]]
  /usr/bin/grep -Fq 'TASK_SELECTION_GUARD' "$temporary_directory/$component.log"
  ! /usr/bin/grep -Fq 'Failed to connect' "$temporary_directory/$component.log"
}
run_negative install install_rclone.yml 'Select the exact rclone executable' CRISTEXWEB_RCLONE_INSTALL_ENTRYPOINT CRISTEXWEB_RCLONE_INSTALL_TOKEN CRISTEXWEB_RCLONE_INSTALL_ATTESTATION_FILE
run_negative proxy_transfer transfer_infisical_proxy_recovery.yml 'Upload immutable pending proxy ciphertext' CRISTEXWEB_RCLONE_PROXY_TRANSFER_ENTRYPOINT CRISTEXWEB_RCLONE_PROXY_TRANSFER_TOKEN CRISTEXWEB_RCLONE_PROXY_TRANSFER_ATTESTATION_FILE
printf '%s\n' 'PASS: combined task-start and forged preflight bindings are rejected at both guarded rclone boundaries'
