#!/bin/sh
set -eu

repository_root="$(CDPATH= cd -- "$(/usr/bin/dirname -- "$0")/.." && pwd -P)"
controller_home="$(CDPATH= cd -- "$repository_root/../.." && pwd -P)"
controller_user="$(/usr/bin/id -un)"
controller="$repository_root/.venv/bin/ansible-playbook"
cd -- "$repository_root/ansible"

/usr/bin/env -i \
  "HOME=$controller_home" \
  "USER=$controller_user" \
  "LOGNAME=$controller_user" \
  'PATH=/usr/bin:/bin:/usr/sbin:/sbin' \
  'LC_ALL=C.UTF-8' \
  "ANSIBLE_CONFIG=$PWD/ansible.cfg" \
  "$controller" playbooks/bootstrap_foundation_namespaces.yml --syntax-check

printf '%s\n' 'PASS: Namespace bootstrap syntax starts under the wrapper-equivalent clean controller environment'
