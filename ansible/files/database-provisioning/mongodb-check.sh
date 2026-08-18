#!/bin/bash
set -euo pipefail
umask 077

MONGO_TARGET_HOST="${MONGO_TARGET_HOST:-localhost}"
MONGO_TARGET_PORT="${MONGO_TARGET_PORT:-27017}"
MONGO_ROOT_USERNAME_FILE="${MONGO_ROOT_USERNAME_FILE:-/etc/mongodb/auth/username}"
MONGO_ROOT_PASSWORD_FILE="${MONGO_ROOT_PASSWORD_FILE:-/etc/mongodb/auth/password}"
MONGO_CA_FILE="${MONGO_CA_FILE:-/etc/mongodb/tls/ca.crt}"
[[ -s "$MONGO_ROOT_USERNAME_FILE" && -s "$MONGO_ROOT_PASSWORD_FILE" ]] || exit 21
[[ -s "$MONGO_CA_FILE" ]] || exit 22

mongo_root_eval() {
  local expression=$1
  mongosh --quiet --norc --tls --tlsCAFile="$MONGO_CA_FILE" \
    --host "$MONGO_TARGET_HOST" --port "$MONGO_TARGET_PORT" \
    --eval "const fs = require('fs'); const rootUser = fs.readFileSync('$MONGO_ROOT_USERNAME_FILE', 'utf8').trim(); const rootPassword = fs.readFileSync('$MONGO_ROOT_PASSWORD_FILE', 'utf8').trim(); if (!rootUser || !rootPassword) quit(30); const admin = db.getSiblingDB('admin'); if (admin.auth({user: rootUser, pwd: rootPassword}) !== 1) quit(31); ${expression}"
}

scope_state() {
  local scope_database=$1
  local scope_user=$2
  local result
  [[ "$scope_database" =~ ^[a-z][a-z0-9_]{0,62}$ ]] || exit 23
  [[ "$scope_user" =~ ^[a-z][a-z0-9_]{0,62}$ ]] || exit 24
  result=$(mongo_root_eval "
    const target = db.getSiblingDB('$scope_database');
    const collections = target.getCollectionNames();
    if (collections.length !== 0) { print('DRIFT'); quit(0); }
    const user = target.getUser('$scope_user');
    if (user === null) { print('MISSING'); quit(0); }
    const roles = user.roles || [];
    const exact = roles.length === 1 && roles[0].role === 'readWrite' && roles[0].db === '$scope_database';
    if (!exact) { print('DRIFT'); quit(0); }
    print('READY');")
  printf '%s\n' "$result" | tail -n 1
}

overall=READY
for scope in \
  'cristexhub_dev|cristexhub_dev_user' \
  'cristexhub_prod|cristexhub_prod_user'; do
  database=${scope%%|*}
  user=${scope##*|}
  state=$(scope_state "$database" "$user")
  case "$state" in
    DRIFT) overall=DRIFT ;;
    MISSING) [[ "$overall" == READY ]] && overall=BOOTSTRAP_REQUIRED ;;
    READY) ;;
    *) exit 25 ;;
  esac
done
printf 'MONGODB_PROVISION_CHECK:%s\n' "$overall" > /dev/termination-log
printf 'MONGODB_PROVISION_CHECK:%s\n' "$overall"
[[ "$overall" != DRIFT ]]
