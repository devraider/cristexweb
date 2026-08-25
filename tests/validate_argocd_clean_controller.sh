#!/bin/sh
set -eu
repository_root="$(CDPATH= cd -- "$(/usr/bin/dirname -- "$0")/.." && pwd -P)"
controller_user="$(/usr/bin/id -un)"
controller_home="$(/usr/bin/getent passwd "$controller_user" | /usr/bin/cut -d: -f6)"
[ -n "$controller_home" ] && [ -d "$controller_home" ] || {
  printf '%s\n' 'Unable to resolve the controller home directory.' >&2
  exit 78
}
controller="$repository_root/.venv/bin/ansible-playbook"
cd -- "$repository_root/ansible"
/usr/bin/env -i \
  "HOME=$controller_home" \
  "USER=$controller_user" \
  "LOGNAME=$controller_user" \
  'PATH=/usr/bin:/bin:/usr/sbin:/sbin' \
  'LC_ALL=C.UTF-8' \
  "ANSIBLE_CONFIG=$PWD/ansible.cfg" \
  "$controller" playbooks/bootstrap_argocd.yml --syntax-check
printf '%s\n' 'PASS: Argo CD bootstrap syntax starts under the clean controller environment'
