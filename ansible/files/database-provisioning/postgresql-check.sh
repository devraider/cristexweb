#!/bin/sh
set -eu
umask 077
trap 'rm -f -- /tmp/*.pgpass' 0 HUP INT TERM

PG_ADMIN_USERNAME_FILE="${PG_ADMIN_USERNAME_FILE:-/etc/postgresql/admin/username}"
PG_ADMIN_PASSWORD_FILE="${PG_ADMIN_PASSWORD_FILE:-/etc/postgresql/admin/password}"
PG_CA_FILE="${PG_CA_FILE:-/tls/ca.crt}"
PG_TARGET_HOST="${PG_TARGET_HOST:-localhost}"
PG_TARGET_PORT="${PG_TARGET_PORT:-5432}"

read_single_line() {
  [ -s "$1" ] || exit 21
  value=$(cat -- "$1")
  [ -n "$value" ] || exit 22
  case "$value" in
    *':'*|*'\\'*) exit 23 ;;
  esac
  printf '%s' "$value"
}

admin_username=$(read_single_line "$PG_ADMIN_USERNAME_FILE")
case "$admin_username" in
  *[!a-z0-9_]*|'') exit 24 ;;
esac
[ -s "$PG_CA_FILE" ] || exit 25
admin_password=$(read_single_line "$PG_ADMIN_PASSWORD_FILE")
admin_pgpass=/tmp/postgresql-admin.pgpass
printf '%s:%s:*:%s:%s\n' "$PG_TARGET_HOST" "$PG_TARGET_PORT" "$admin_username" "$admin_password" > "$admin_pgpass"
chmod 600 "$admin_pgpass"
unset admin_password value

psql_admin() {
  PGPASSFILE="$admin_pgpass" PGSSLMODE=verify-full PGSSLROOTCERT="$PG_CA_FILE" \
    psql -X -w -v ON_ERROR_STOP=1 -h "$PG_TARGET_HOST" -p "$PG_TARGET_PORT" \
      -U "$admin_username" "$@"
}

scope_state() {
  scope_database=$1
  scope_role=$2
  role_row=$(psql_admin -d postgres -Atqc \
    "SELECT rolsuper::int,rolinherit::int,rolcreaterole::int,rolcreatedb::int,rolcanlogin::int,rolreplication::int,rolbypassrls::int FROM pg_roles WHERE rolname = '$scope_role'")
  database_row=$(psql_admin -d postgres -Atqc \
    "SELECT pg_catalog.pg_get_userbyid(datdba),datallowconn::int FROM pg_database WHERE datname = '$scope_database'")
  role_exists=0
  database_exists=0
  [ -n "$role_row" ] && role_exists=1
  [ -n "$database_row" ] && database_exists=1
  if [ "$role_exists" -eq 0 ] && [ "$database_exists" -eq 1 ]; then
    printf '%s' DRIFT
    return
  fi
  if [ "$role_exists" -eq 0 ]; then
    printf '%s' MISSING
    return
  fi
  [ "$role_row" = '0|0|0|0|1|0|0' ] || { printf '%s' DRIFT; return; }
  if [ "$database_exists" -eq 0 ]; then
    printf '%s' ROLE_ONLY
    return
  fi
  [ "${database_row%%|*}" = "$scope_role" ] || { printf '%s' DRIFT; return; }
  [ "${database_row##*|}" = 1 ] || { printf '%s' DRIFT; return; }
  non_system_schema_count=$(psql_admin -d "$scope_database" -Atqc \
    "SELECT count(*) FROM pg_namespace WHERE nspname NOT IN ('pg_catalog','information_schema','public') AND nspname !~ '^pg_toast'")
  [ "$non_system_schema_count" = 0 ] || { printf '%s' DRIFT; return; }
  user_relation_count=$(psql_admin -d "$scope_database" -Atqc \
    "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relkind IN ('r','p','v','m','S','f')")
  [ "$user_relation_count" = 0 ] || { printf '%s' DRIFT; return; }
  public_acl=$(psql_admin -d postgres -Atqc \
    "SELECT has_database_privilege('public','$scope_database','CONNECT')::int || '|' || has_database_privilege('public','$scope_database','TEMPORARY')::int")
  [ "$public_acl" = '0|0' ] || { printf '%s' DRIFT; return; }
  public_schema_create=$(psql_admin -d "$scope_database" -Atqc \
    "SELECT has_schema_privilege('public','public','CREATE')::int")
  [ "$public_schema_create" = 0 ] || { printf '%s' DRIFT; return; }
  role_database_acl=$(psql_admin -d postgres -Atqc \
    "SELECT has_database_privilege('$scope_role','$scope_database','CONNECT')::int")
  [ "$role_database_acl" = 1 ] || { printf '%s' DRIFT; return; }
  printf '%s' READY
}

overall=READY
for scope in \
  'cristexhub_dev|cristexhub_dev_owner' \
  'cristexhub_prod|cristexhub_prod_owner' \
  'reactive_resume_dev|reactive_resume_dev_owner' \
  'reactive_resume_prod|reactive_resume_prod_owner' \
  'keycloak|keycloak_owner'; do
  database=${scope%%|*}
  role=${scope##*|}
  state=$(scope_state "$database" "$role")
  case "$state" in
    DRIFT) overall=DRIFT ;;
    MISSING|ROLE_ONLY) [ "$overall" = READY ] && overall=BOOTSTRAP_REQUIRED ;;
    READY) ;;
    *) exit 26 ;;
  esac
done
rm -f -- "$admin_pgpass"
printf 'POSTGRESQL_PROVISION_CHECK:%s\n' "$overall" > /dev/termination-log
printf 'POSTGRESQL_PROVISION_CHECK:%s\n' "$overall"
[ "$overall" != DRIFT ]
