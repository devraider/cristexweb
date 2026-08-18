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
  object_count: 44
  crd_count: 6
  prestate_count: 44
  proxy_secret_count: 3
  namespace_count: 5
  namespace_contract: true
  identity_keys:
    - "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicalauths.secrets.infisical.com"
    - "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicalconnections.secrets.infisical.com"
    - "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicaldynamicsecrets.secrets.infisical.com"
    - "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicalpushsecrets.secrets.infisical.com"
    - "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicalsecrets.secrets.infisical.com"
    - "apiextensions.k8s.io/v1|CustomResourceDefinition||infisicalstaticsecrets.secrets.infisical.com"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-auth-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-auth-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-connection-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-connection-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-dynamic-secret-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-dynamic-secret-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-push-secret-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-push-secret-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-secret-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-secret-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicyBinding||infisical-static-secret-boundary"
    - "admissionregistration.k8s.io/v1|ValidatingAdmissionPolicy||infisical-static-secret-boundary"
    - "apps/v1|Deployment|shared-services|infisical-operator-controller"
    - "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-operator-allow-api"
    - "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-operator-allow-dns"
    - "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-operator-allow-proxy"
    - "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-operator-default-deny"
    - "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-proxy-allow-dns"
    - "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-proxy-allow-external-https"
    - "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-proxy-allow-operator"
    - "networking.k8s.io/v1|NetworkPolicy|shared-services|infisical-proxy-default-deny"
    - "v1|ConfigMap|shared-services|infisical-egress-proxy"
    - "apps/v1|Deployment|shared-services|infisical-egress-proxy"
    - "v1|Service|shared-services|infisical-egress-proxy"
    - "v1|ServiceAccount|shared-services|infisical-operator-controller"
    - "rbac.authorization.k8s.io/v1|Role|shared-services|infisical-operator-leader-election"
    - "rbac.authorization.k8s.io/v1|RoleBinding|shared-services|infisical-operator-leader-election"
    - "rbac.authorization.k8s.io/v1|Role|argocd|infisical-operator-manager"
    - "rbac.authorization.k8s.io/v1|Role|cristexhub-dev|infisical-operator-manager"
    - "rbac.authorization.k8s.io/v1|Role|cristexhub-prod|infisical-operator-manager"
    - "rbac.authorization.k8s.io/v1|Role|shared-services|infisical-operator-manager"
    - "rbac.authorization.k8s.io/v1|Role|platform-edge|infisical-operator-manager"
    - "rbac.authorization.k8s.io/v1|RoleBinding|platform-edge|infisical-operator-manager"
    - "rbac.authorization.k8s.io/v1|RoleBinding|argocd|infisical-operator-manager"
    - "rbac.authorization.k8s.io/v1|RoleBinding|cristexhub-dev|infisical-operator-manager"
    - "rbac.authorization.k8s.io/v1|RoleBinding|cristexhub-prod|infisical-operator-manager"
    - "rbac.authorization.k8s.io/v1|RoleBinding|shared-services|infisical-operator-manager"
    - "v1|ServiceAccount|shared-services|infisical-egress-proxy"
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
