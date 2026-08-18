#!/bin/bash
set -euo pipefail
umask 077

MONGO_TARGET_HOST="${MONGO_TARGET_HOST:-shared-mongodb.shared-services.svc}"
MONGO_TARGET_PORT="${MONGO_TARGET_PORT:-27017}"
MONGO_ROOT_USERNAME_FILE="${MONGO_ROOT_USERNAME_FILE:-/run/database-credentials/shared-mongodb-auth/username}"
MONGO_ROOT_PASSWORD_FILE="${MONGO_ROOT_PASSWORD_FILE:-/run/database-credentials/shared-mongodb-auth/password}"
MONGO_CA_FILE="${MONGO_CA_FILE:-/run/database-tls/ca.crt}"

[[ -s "$MONGO_ROOT_USERNAME_FILE" && -s "$MONGO_ROOT_PASSWORD_FILE" ]] || exit 21
[[ -s "$MONGO_CA_FILE" ]] || exit 22

validate_identifier() {
  [[ "$1" =~ ^[a-z][a-z0-9_]{0,62}$ ]] || exit 23
}

consumer_directory() {
  case "$1" in
    cristexhub_dev_user) printf '%s' /run/database-credentials/shared-mongodb-cristexhub-dev ;;
    cristexhub_prod_user) printf '%s' /run/database-credentials/shared-mongodb-cristexhub-prod ;;
    *) exit 24 ;;
  esac
}

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
  validate_identifier "$scope_database"
  validate_identifier "$scope_user"
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

consumer_auth() {
  local scope_database=$1
  local scope_user=$2
  local directory
  validate_identifier "$scope_database"
  validate_identifier "$scope_user"
  directory=$(consumer_directory "$scope_user")
  [[ -s "$directory/username" && -s "$directory/password" ]] || exit 25
  mongosh --quiet --norc --tls --tlsCAFile="$MONGO_CA_FILE" \
    --host "$MONGO_TARGET_HOST" --port "$MONGO_TARGET_PORT" \
    --eval "
      const fs = require('fs');
      const target = db.getSiblingDB('$scope_database');
      const username = fs.readFileSync('$directory/username', 'utf8').trim();
      const password = fs.readFileSync('$directory/password', 'utf8').trim();
      if (username !== '$scope_user' || !password) quit(40);
      if (target.auth({user: username, pwd: password}) !== 1) quit(41);
      if (target.runCommand({ping: 1}).ok !== 1) quit(42);"
}

negative_authorization() {
  local scope_database=$1
  local scope_user=$2
  local other_database=$3
  local directory
  validate_identifier "$scope_database"
  validate_identifier "$scope_user"
  validate_identifier "$other_database"
  directory=$(consumer_directory "$scope_user")
  [[ -s "$directory/username" && -s "$directory/password" ]] || exit 26
  mongosh --quiet --norc --tls --tlsCAFile="$MONGO_CA_FILE" \
    --host "$MONGO_TARGET_HOST" --port "$MONGO_TARGET_PORT" \
    --eval "
      const fs = require('fs');
      const own = db.getSiblingDB('$scope_database');
      const username = fs.readFileSync('$directory/username', 'utf8').trim();
      const password = fs.readFileSync('$directory/password', 'utf8').trim();
      if (username !== '$scope_user' || !password) quit(43);
      if (own.auth({user: username, pwd: password}) !== 1) quit(44);
      const other = db.getSiblingDB('$other_database');
      if (other.runCommand({listCollections: 1}).ok === 1) quit(45);
      const authInfo = own.runCommand({connectionStatus: 1}).authInfo || {};
      const roles = authInfo.authenticatedUserRoles || [];
      if (roles.some((role) => ['root', 'readAnyDatabase', 'readWriteAnyDatabase', 'dbAdminAnyDatabase', 'userAdminAnyDatabase'].includes(role.role))) quit(46);
      if (roles.some((role) => role.role === 'readWrite' && role.db !== '$scope_database')) quit(47);"
}

scopes=(
  'cristexhub_dev|cristexhub_dev_user|cristexhub_prod'
  'cristexhub_prod|cristexhub_prod_user|cristexhub_dev'
)

overall=READY
missing_count=0
for scope in "${scopes[@]}"; do
  database=${scope%%|*}
  rest=${scope#*|}
  user=${rest%%|*}
  other_database=${rest##*|}
  state=$(scope_state "$database" "$user")
  case "$state" in
    DRIFT) printf 'MONGODB_PROVISION:DRIFT\n' > /dev/termination-log; exit 31 ;;
    MISSING) overall=BOOTSTRAP_REQUIRED; missing_count=$((missing_count + 1)) ;;
    READY) ;;
    *) exit 32 ;;
  esac
done

if [[ "$overall" == READY ]]; then
  for scope in "${scopes[@]}"; do
    database=${scope%%|*}
    rest=${scope#*|}
    user=${rest%%|*}
    other_database=${rest##*|}
    consumer_auth "$database" "$user" >/dev/null
    negative_authorization "$database" "$user" "$other_database"
  done
  printf 'MONGODB_PROVISION:READY\n' > /dev/termination-log
  printf 'MONGODB_PROVISION:READY\n'
  exit 0
fi

for scope in "${scopes[@]}"; do
  database=${scope%%|*}
  rest=${scope#*|}
  user=${rest%%|*}
  other_database=${rest##*|}
  state=$(scope_state "$database" "$user")
  [[ "$state" == MISSING ]] || continue
  directory=$(consumer_directory "$user")
  [[ -s "$directory/username" && -s "$directory/password" ]] || exit 33
  mongo_root_eval "
    const fs = require('fs');
    const target = db.getSiblingDB('$database');
    const username = fs.readFileSync('$directory/username', 'utf8').trim();
    const password = fs.readFileSync('$directory/password', 'utf8').trim();
    if (username !== '$user' || !password) quit(34);
    target.createUser({user: username, pwd: password, roles: [{role: 'readWrite', db: '$database'}]});" >/dev/null
  consumer_auth "$database" "$user" >/dev/null
  negative_authorization "$database" "$user" "$other_database"
done

for scope in "${scopes[@]}"; do
  database=${scope%%|*}
  rest=${scope#*|}
  user=${rest%%|*}
  other_database=${rest##*|}
  [[ "$(scope_state "$database" "$user")" == READY ]] || {
    printf 'MONGODB_PROVISION:DRIFT\n' > /dev/termination-log
    exit 35
  }
  consumer_auth "$database" "$user" >/dev/null
  negative_authorization "$database" "$user" "$other_database"
done
printf 'MONGODB_PROVISION:CHANGED:%s\n' "$missing_count" > /dev/termination-log
printf 'MONGODB_PROVISION:CHANGED:%s\n' "$missing_count"
