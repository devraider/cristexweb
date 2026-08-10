#!/bin/sh
set -eu
repository_root="$(CDPATH= cd -- "$(/usr/bin/dirname -- "$0")/.." && pwd -P)"
temporary_directory="$(/usr/bin/mktemp -d)"
output_file="$temporary_directory/output.log"
attestation_file="$temporary_directory/attestation"
attestation_token="$(/usr/bin/openssl rand -hex 32)"
cleanup() { /bin/rm -rf -- "$temporary_directory"; }
trap cleanup EXIT HUP INT TERM
/bin/chmod 0700 "$temporary_directory"
printf '%s:entrypoint\n' "$attestation_token" >"$attestation_file"
/bin/chmod 0600 "$attestation_file"
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
CRISTEXWEB_ARGOCD_BOOTSTRAP_ENTRYPOINT=v1 \
CRISTEXWEB_ARGOCD_BOOTSTRAP_TOKEN="$attestation_token" \
CRISTEXWEB_ARGOCD_BOOTSTRAP_ATTESTATION_FILE="$attestation_file" \
  "$repository_root/.venv/bin/ansible-playbook" \
  -i "$temporary_directory/inventory.yml" playbooks/bootstrap_argocd.yml \
  --check --diff --limit crtxweb \
  --extra-vars '{"argocd_bootstrap_approved":true}' >"$output_file" 2>&1
status=$?
set -e
[ "$status" -ne 0 ]
/usr/bin/grep -Fq 'k3s and tailscaled must already be running' "$output_file"
! /usr/bin/grep -Fq 'Refusing missing, unsafe, mode-drifted, or hash-drifted Argo CD source' "$output_file"
! /usr/bin/grep -Fq "object of type 'dict' has no attribute" "$output_file"
printf '%s\n' 'PASS: default Argo CD role inputs validate through the exact 32-object inventory and stop at the intentional host-service prerequisite'
