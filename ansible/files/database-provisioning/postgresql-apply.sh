#!/bin/sh
set -eu
umask 077
trap 'rm -f -- /tmp/*.pgpass' 0 HUP INT TERM

PG_ADMIN_USERNAME_FILE="${PG_ADMIN_USERNAME_FILE:-/run/database-credentials/shared-postgresql-admin/username}"
PG_ADMIN_PASSWORD_FILE="${PG_ADMIN_PASSWORD_FILE:-/run/database-credentials/shared-postgresql-admin/password}"
PG_CA_FILE="${PG_CA_FILE:-/run/database-tls/ca.crt}"
PG_TARGET_HOST="${PG_TARGET_HOST:-shared-postgresql.shared-services.svc}"
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
[ -s "$PG_ADMIN_PASSWORD_FILE" ] || exit 25
[ -s "$PG_CA_FILE" ] || exit 26

admin_pgpass=/tmp/postgresql-admin.pgpass
admin_password=$(read_single_line "$PG_ADMIN_PASSWORD_FILE")
printf '%s:%s:*:%s:%s\n' "$PG_TARGET_HOST" "$PG_TARGET_PORT" "$admin_username" "$admin_password" > "$admin_pgpass"
chmod 600 "$admin_pgpass"
unset admin_password value

psql_admin() {
  PGPASSFILE="$admin_pgpass" PGSSLMODE=verify-full PGSSLROOTCERT="$PG_CA_FILE" \
    psql -X -w -v ON_ERROR_STOP=1 -h "$PG_TARGET_HOST" -p "$PG_TARGET_PORT" \
      -U "$admin_username" "$@"
}

scope_database=''
scope_role=''
role_row=''
database_row=''
role_exists=0
database_exists=0
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
  expected_role='0|0|0|0|1|0|0'
  [ "$role_row" = "$expected_role" ] || { printf '%s' DRIFT; return; }
  if [ "$database_exists" -eq 0 ]; then
    printf '%s' ROLE_ONLY
    return
  fi
  database_owner=${database_row%%|*}
  database_connect=${database_row##*|}
  [ "$database_owner" = "$scope_role" ] || { printf '%s' DRIFT; return; }
  [ "$database_connect" = 1 ] || { printf '%s' DRIFT; return; }
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

consumer_directory() {
  case "$1" in
    cristexhub_dev_owner) printf '%s' /run/database-credentials/shared-postgresql-cristexhub-dev ;;
    cristexhub_prod_owner) printf '%s' /run/database-credentials/shared-postgresql-cristexhub-prod ;;
    reactive_resume_dev_owner) printf '%s' /run/database-credentials/shared-postgresql-reactive-resume-dev ;;
    reactive_resume_prod_owner) printf '%s' /run/database-credentials/shared-postgresql-reactive-resume-prod ;;
    keycloak_owner) printf '%s' /run/database-credentials/shared-postgresql-keycloak ;;
    *) exit 27 ;;
  esac
}

consumer_pgpass() {
  database=$1
  role=$2
  directory=$(consumer_directory "$role")
  username=$(read_single_line "$directory/username")
  [ "$username" = "$role" ] || exit 28
  password=$(read_single_line "$directory/password")
  passfile="/tmp/${role}.pgpass"
  printf '%s:%s:%s:%s:%s\n' "$PG_TARGET_HOST" "$PG_TARGET_PORT" "$database" "$role" "$password" > "$passfile"
  chmod 600 "$passfile"
  unset username password value
  printf '%s' "$passfile"
}

consumer_login() {
  database=$1
  role=$2
  passfile=$(consumer_pgpass "$database" "$role")
  PGPASSFILE="$passfile" PGSSLMODE=verify-full PGSSLROOTCERT="$PG_CA_FILE" \
    psql -X -w -v ON_ERROR_STOP=1 -h "$PG_TARGET_HOST" -p "$PG_TARGET_PORT" \
      -U "$role" -d "$database" -Atqc 'SELECT current_user'
}

negative_authorization() {
  database=$1
  role=$2
  passfile=$(consumer_pgpass "$database" "$role")
  for other_database in \
    cristexhub_dev cristexhub_prod reactive_resume_dev reactive_resume_prod keycloak; do
    [ "$other_database" = "$database" ] && continue
    if PGPASSFILE="$passfile" PGSSLMODE=verify-full PGSSLROOTCERT="$PG_CA_FILE" \
      psql -X -w -h "$PG_TARGET_HOST" -p "$PG_TARGET_PORT" -U "$role" \
        -d "$other_database" -Atqc 'SELECT 1' >/dev/null 2>&1; then
      exit 41
    fi
  done
  if PGPASSFILE="$passfile" PGSSLMODE=verify-full PGSSLROOTCERT="$PG_CA_FILE" \
    psql -X -w -h "$PG_TARGET_HOST" -p "$PG_TARGET_PORT" -U "$role" \
      -d "$database" -Atqc 'SELECT rolcreatedb FROM pg_roles WHERE rolname = current_user' \
      | grep -qx t; then
    exit 42
  fi
  if PGPASSFILE="$passfile" PGSSLMODE=verify-full PGSSLROOTCERT="$PG_CA_FILE" \
    psql -X -w -h "$PG_TARGET_HOST" -p "$PG_TARGET_PORT" -U "$role" \
      -d "$database" -Atqc 'SELECT rolcreaterole FROM pg_roles WHERE rolname = current_user' \
      | grep -qx t; then
    exit 43
  fi
}

overall=READY
missing_count=0
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
    DRIFT) printf 'POSTGRESQL_PROVISION:DRIFT\n' > /dev/termination-log; exit 31 ;;
    MISSING|ROLE_ONLY) overall=BOOTSTRAP_REQUIRED; missing_count=$((missing_count + 1)) ;;
    READY) ;;
    *) exit 32 ;;
  esac
done

if [ "$overall" = READY ]; then
  for scope in \
    'cristexhub_dev|cristexhub_dev_owner' \
    'cristexhub_prod|cristexhub_prod_owner' \
    'reactive_resume_dev|reactive_resume_dev_owner' \
    'reactive_resume_prod|reactive_resume_prod_owner' \
    'keycloak|keycloak_owner'; do
    database=${scope%%|*}
    role=${scope##*|}
    consumer_login "$database" "$role" >/dev/null
    negative_authorization "$database" "$role"
  done
  rm -f -- /tmp/*.pgpass
  printf 'POSTGRESQL_PROVISION:READY\n' > /dev/termination-log
  printf 'POSTGRESQL_PROVISION:READY\n'
  exit 0
fi

# Preflight has proven every non-empty scope exact; create only absent reservations.
for scope in \
  'cristexhub_dev|cristexhub_dev_owner' \
  'cristexhub_prod|cristexhub_prod_owner' \
  'reactive_resume_dev|reactive_resume_dev_owner' \
  'reactive_resume_prod|reactive_resume_prod_owner' \
  'keycloak|keycloak_owner'; do
  database=${scope%%|*}
  role=${scope##*|}
  state=$(scope_state "$database" "$role")
  [ "$state" = MISSING ] || [ "$state" = ROLE_ONLY ] || continue
  password_file="$(consumer_directory "$role")/password"
  [ -s "$password_file" ] || exit 33
  if [ "$state" = MISSING ]; then
    role_statement="CREATE ROLE \"$role\" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD :'role_password';"
  else
    role_statement="ALTER ROLE \"$role\" PASSWORD :'role_password';"
  fi
  PGPASSFILE="$admin_pgpass" PGSSLMODE=verify-full PGSSLROOTCERT="$PG_CA_FILE" \
    psql -X -w -v ON_ERROR_STOP=1 -h "$PG_TARGET_HOST" -p "$PG_TARGET_PORT" \
      -U "$admin_username" -d postgres <<SQL
\set role_password `cat "$password_file"`
$role_statement
SQL
  unset role_statement
  PGPASSFILE="$admin_pgpass" PGSSLMODE=verify-full PGSSLROOTCERT="$PG_CA_FILE" \
    psql -X -w -v ON_ERROR_STOP=1 -h "$PG_TARGET_HOST" -p "$PG_TARGET_PORT" \
      -U "$admin_username" -d postgres -c \
      "CREATE DATABASE \"$database\" OWNER \"$role\" TEMPLATE template0" >/dev/null
  PGPASSFILE="$admin_pgpass" PGSSLMODE=verify-full PGSSLROOTCERT="$PG_CA_FILE" \
    psql -X -w -v ON_ERROR_STOP=1 -h "$PG_TARGET_HOST" -p "$PG_TARGET_PORT" \
      -U "$admin_username" -d postgres -c \
      "REVOKE CONNECT, TEMPORARY ON DATABASE \"$database\" FROM PUBLIC; GRANT CONNECT ON DATABASE \"$database\" TO \"$role\"" >/dev/null
  PGPASSFILE="$admin_pgpass" PGSSLMODE=verify-full PGSSLROOTCERT="$PG_CA_FILE" \
    psql -X -w -v ON_ERROR_STOP=1 -h "$PG_TARGET_HOST" -p "$PG_TARGET_PORT" \
      -U "$admin_username" -d "$database" -c \
      "REVOKE CREATE ON SCHEMA public FROM PUBLIC; GRANT USAGE, CREATE ON SCHEMA public TO \"$role\"" >/dev/null
done

for scope in \
  'cristexhub_dev|cristexhub_dev_owner' \
  'cristexhub_prod|cristexhub_prod_owner' \
  'reactive_resume_dev|reactive_resume_dev_owner' \
  'reactive_resume_prod|reactive_resume_prod_owner' \
  'keycloak|keycloak_owner'; do
  database=${scope%%|*}
  role=${scope##*|}
  [ "$(scope_state "$database" "$role")" = READY ] || {
    printf 'POSTGRESQL_PROVISION:DRIFT\n' > /dev/termination-log
    exit 34
  }
  consumer_login "$database" "$role" >/dev/null
  negative_authorization "$database" "$role"
done
rm -f -- /tmp/*.pgpass
printf 'POSTGRESQL_PROVISION:CHANGED:%s\n' "$missing_count" > /dev/termination-log
printf 'POSTGRESQL_PROVISION:CHANGED:%s\n' "$missing_count"
