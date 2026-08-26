#!/usr/bin/env bash
set -euo pipefail

readonly repository_root="$(CDPATH= cd -- "$(/usr/bin/dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly temporary_directory="$(/usr/bin/mktemp -d)"
trap '/bin/rm -rf -- "$temporary_directory"' EXIT HUP INT TERM
/bin/chmod 0700 "$temporary_directory"
readonly output_file="$temporary_directory/output.log"
readonly attestation_file="$temporary_directory/attestation"
readonly token="$(/usr/bin/openssl rand -hex 32)"
readonly token_sha256="$(printf '%s' "$token" | /usr/bin/shasum -a 256 | /usr/bin/awk '{print $1}')"
printf '%s:entrypoint\n' "$token" >"$attestation_file"
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
cat >"$temporary_directory/injected.yml" <<YAML
cristexhub_prod_registration_approved: true
cristexhub_prod_registration_internal_preflight_binding:
  attestation_sha256: $token_sha256
  manifest_names:
    - argocd-application-controller-cristexhub-prod
    - argocd-application-controller-cristexhub-prod
    - argocd-cluster-cristexhub-prod
    - cristexhub-prod
    - cristexhub-prod
  prestate_names:
    - argocd-application-controller-cristexhub-prod
    - argocd-application-controller-cristexhub-prod
    - argocd-cluster-cristexhub-prod
    - cristexhub-prod
    - cristexhub-prod
  object_count: 5
  namespace_contract: true
  repository_contract: true
  revision: 751885a42798d282e168131db147f13694a0a621
  no_delete_path: true
cristexhub_prod_registration_internal_manifests:
  - apiVersion: argoproj.io/v1alpha1
    kind: Application
    metadata:
      name: cristexhub-prod
      namespace: argocd
      labels:
        app.kubernetes.io/name: cristexhub-prod
        app.kubernetes.io/part-of: cristexhub
        app.kubernetes.io/managed-by: ansible
        cristex.io/component: cristexhub-prod-registration
    spec:
      project: cristexhub-prod
      source:
        repoURL: ssh://git@ssh.github.com:443/devraider/cristexhub.git
        targetRevision: 751885a42798d282e168131db147f13694a0a621
        path: infra/kubernetes/cristexhub-prod
      destination:
        name: cristexhub-prod-local
        server: ''
        namespace: cristexhub-prod
      syncPolicy:
        syncOptions:
          - CreateNamespace=false
          - Prune=false
          - ServerSideApply=false
          - Replace=false
          - FailOnSharedResource=true
YAML
cd -- "$repository_root/ansible"
set +e
CRISTEXWEB_REPOSITORY_ROOT="$repository_root" \
CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ENTRYPOINT=v1 \
CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_TOKEN="$token" \
CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ATTESTATION_FILE="$attestation_file" \
  "$repository_root/.venv/bin/ansible-playbook" \
  -i "$temporary_directory/inventory.yml" \
  playbooks/bootstrap_cristexhub_prod_registration.yml \
  --check --diff --limit crtxweb \
  --extra-vars "@$temporary_directory/injected.yml" \
  --start-at-task \
  'Reconcile registration source without synchronization' \
  >"$output_file" 2>&1
readonly status=$?
set -e
[[ $status -ne 0 ]]
grep -Fq 'TASK_SELECTION_GUARD' "$output_file" || {
  /bin/cat "$output_file" >&2
  exit 1
}
! grep -Fq 'Failed to connect' "$output_file"
printf '%s\n' 'PASS: PROD registration task-start and forged preflight bypass is rejected before Kubernetes'
