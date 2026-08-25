#!/bin/sh
# Read-only catalog check for the observed DEV successor database and roles.
# This script never creates, alters, grants, revokes, drops, or reads credentials.
set -eu
umask 077

psql_bin=/usr/bin/psql
pg_socket=/controller/run
database=reactive_resume_dev_successor
runtime_role=reactive_resume_dev_runtime
migration_role=reactive_resume_dev_migrator

[ -x "$psql_bin" ] || {
  printf '%s\n' 'REACTIVE_RESUME_DEV_SUCCESSOR:BLOCKED psql_unavailable' >&2
  exit 20
}
# CNPG's postgres container exposes its local Unix socket below /controller/run.
# Explicit PGHOST plus env -i rejects inherited libpq service, password-file,
# password, routing, and other credential overrides.
[ -S "$pg_socket/.s.PGSQL.5432" ] || {
  printf '%s\n' 'REACTIVE_RESUME_DEV_SUCCESSOR:BLOCKED local_socket_unavailable' >&2
  exit 21
}
psql_catalog() {
  database_name=$1
  query=$2
  /usr/bin/env -i \
    PATH=/usr/bin:/bin HOME=/tmp LC_ALL=C \
    PGHOST="$pg_socket" PGPORT=5432 PGUSER=postgres PGDATABASE="$database_name" \
    "$psql_bin" -X -v ON_ERROR_STOP=1 -h "$pg_socket" -p 5432 \
    -U postgres -d "$database_name" -Atqc "$query"
}

failures=
expected_relation_acl="{${migration_role}=arwdDxtm/${migration_role},${runtime_role}=arwd/${migration_role}}"
expected_default_relation_acl="{${runtime_role}=arwd/${migration_role}}"
expected_default_sequence_acl="{${runtime_role}=rwU/${migration_role}}"
check_eq() {
  label=$1
  expected=$2
  query=$3
  actual=''
  if ! actual=$(psql_catalog postgres "$query"); then
    failures="${failures},${label}_query"
  elif [ "$actual" != "$expected" ]; then
    failures="${failures},${label}"
  fi
}
check_target_eq() {
  label=$1
  expected=$2
  query=$3
  actual=''
  if ! actual=$(psql_catalog "$database" "$query"); then
    failures="${failures},${label}_query"
  elif [ "$actual" != "$expected" ]; then
    failures="${failures},${label}"
  fi
}

check_eq current_user postgres "SELECT current_user"
check_eq role_count 2 "SELECT count(*) FROM pg_roles WHERE rolname IN ('$runtime_role','$migration_role')"
check_eq role_attributes 2 "SELECT count(*) FROM pg_roles WHERE rolname IN ('$runtime_role','$migration_role') AND rolsuper=false AND rolcreatedb=false AND rolcreaterole=false AND rolinherit=false AND rolcanlogin=true AND rolreplication=false AND rolbypassrls=false"
check_eq membership_count 0 "SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member WHERE r.rolname IN ('$runtime_role','$migration_role')"
check_eq database_count 1 "SELECT count(*) FROM pg_database WHERE datname='$database' AND datallowconn AND NOT datistemplate"
check_eq database_owner "$migration_role" "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname='$database'"
check_eq target_public_connect f "SELECT has_database_privilege('public','$database','CONNECT')"
check_eq target_public_temporary f "SELECT has_database_privilege('public','$database','TEMPORARY')"
check_eq runtime_connect t "SELECT has_database_privilege('$runtime_role','$database','CONNECT')"
check_eq migration_connect t "SELECT has_database_privilege('$migration_role','$database','CONNECT')"
check_eq database_acl_foreign 0 "SELECT count(*) FROM pg_database d CROSS JOIN LATERAL aclexplode(coalesce(d.datacl,'{}'::aclitem[])) a LEFT JOIN pg_roles g ON g.oid=a.grantee WHERE d.datname='$database' AND (a.grantee=0 OR g.rolname IS NULL OR g.rolname NOT IN ('$runtime_role','$migration_role','pg_database_owner') OR (g.rolname='$runtime_role' AND a.privilege_type <> 'CONNECT') OR (g.rolname='pg_database_owner' AND a.privilege_type NOT IN ('CONNECT','CREATE','TEMPORARY')) OR (g.rolname='$migration_role' AND a.privilege_type NOT IN ('CONNECT','CREATE','TEMPORARY')) )"
check_target_eq schema_count 0 "SELECT count(*) FROM pg_namespace WHERE nspname NOT IN ('public','drizzle') AND nspname !~ '^pg_' AND nspname <> 'information_schema'"
check_target_eq target_public_schema_create f "SELECT has_schema_privilege('public','public','CREATE')"
check_target_eq target_public_schema_usage t "SELECT has_schema_privilege('public','public','USAGE')"
check_target_eq runtime_schema_usage t "SELECT has_schema_privilege('$runtime_role','public','USAGE')"
check_target_eq runtime_schema_create f "SELECT has_schema_privilege('$runtime_role','public','CREATE')"
check_target_eq migration_schema_usage t "SELECT has_schema_privilege('$migration_role','public','USAGE')"
check_target_eq migration_schema_create t "SELECT has_schema_privilege('$migration_role','public','CREATE')"
check_target_eq schema_acl_foreign 0 "SELECT count(*) FROM pg_namespace n CROSS JOIN LATERAL aclexplode(coalesce(n.nspacl,'{}'::aclitem[])) a LEFT JOIN pg_roles g ON g.oid=a.grantee WHERE n.nspname IN ('public','drizzle') AND ( (a.grantee=0 AND a.privilege_type <> 'USAGE') OR (a.grantee <> 0 AND (g.rolname IS NULL OR g.rolname NOT IN ('$runtime_role','$migration_role','pg_database_owner') OR (g.rolname='$runtime_role' AND a.privilege_type <> 'USAGE') OR (g.rolname='pg_database_owner' AND a.privilege_type NOT IN ('USAGE','CREATE')) OR (g.rolname='$migration_role' AND a.privilege_type NOT IN ('USAGE','CREATE'))) ) )"

# Every application relation is owned by the migration role, has no PUBLIC or
# foreign grant, and gives runtime only the reviewed relation privileges.
check_target_eq relation_acl 0 "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('public','drizzle') AND c.relkind IN ('r','p','v','m') AND (pg_get_userbyid(c.relowner) <> '$migration_role' OR (c.relkind IN ('r','p') AND NOT (has_table_privilege('$runtime_role',c.oid,'SELECT') AND has_table_privilege('$runtime_role',c.oid,'INSERT') AND has_table_privilege('$runtime_role',c.oid,'UPDATE') AND has_table_privilege('$runtime_role',c.oid,'DELETE'))) OR (c.relkind IN ('v','m') AND NOT has_table_privilege('$runtime_role',c.oid,'SELECT')) OR has_table_privilege('public',c.oid,'SELECT') OR has_table_privilege('public',c.oid,'INSERT') OR has_table_privilege('public',c.oid,'UPDATE') OR has_table_privilege('public',c.oid,'DELETE') OR has_table_privilege('$runtime_role',c.oid,'TRUNCATE') OR has_table_privilege('$runtime_role',c.oid,'REFERENCES') OR has_table_privilege('$runtime_role',c.oid,'TRIGGER') OR NOT (has_table_privilege('$migration_role',c.oid,'SELECT') AND has_table_privilege('$migration_role',c.oid,'INSERT') AND has_table_privilege('$migration_role',c.oid,'UPDATE') AND has_table_privilege('$migration_role',c.oid,'DELETE') AND has_table_privilege('$migration_role',c.oid,'TRUNCATE') AND has_table_privilege('$migration_role',c.oid,'REFERENCES') AND has_table_privilege('$migration_role',c.oid,'TRIGGER')) OR EXISTS (SELECT 1 FROM aclexplode(coalesce(c.relacl,'{}'::aclitem[])) x LEFT JOIN pg_roles gx ON gx.oid=x.grantee WHERE gx.rolname IS NULL OR gx.rolname NOT IN ('$runtime_role','$migration_role','pg_database_owner') OR (gx.rolname='$runtime_role' AND x.privilege_type NOT IN ('SELECT','INSERT','UPDATE','DELETE')) OR (gx.rolname='pg_database_owner' AND x.privilege_type NOT IN ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER')) OR (gx.rolname='$migration_role' AND x.privilege_type NOT IN ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER')))"
check_target_eq sequence_acl 0 "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('public','drizzle') AND c.relkind='S' AND (pg_get_userbyid(c.relowner) <> '$migration_role' OR NOT has_sequence_privilege('$runtime_role',c.oid,'USAGE') OR NOT has_sequence_privilege('$runtime_role',c.oid,'SELECT') OR has_sequence_privilege('$runtime_role',c.oid,'UPDATE') OR NOT has_sequence_privilege('$migration_role',c.oid,'USAGE') OR NOT has_sequence_privilege('$migration_role',c.oid,'SELECT') OR NOT has_sequence_privilege('$migration_role',c.oid,'UPDATE') OR has_sequence_privilege('public',c.oid,'USAGE') OR has_sequence_privilege('public',c.oid,'SELECT') OR has_sequence_privilege('public',c.oid,'UPDATE') OR EXISTS (SELECT 1 FROM aclexplode(coalesce(c.relacl,'{}'::aclitem[])) x LEFT JOIN pg_roles gx ON gx.oid=x.grantee WHERE gx.rolname IS NULL OR gx.rolname NOT IN ('$runtime_role','$migration_role','pg_database_owner') OR (gx.rolname='$runtime_role' AND x.privilege_type NOT IN ('USAGE','SELECT')) OR (gx.rolname='$migration_role' AND x.privilege_type NOT IN ('USAGE','SELECT','UPDATE'))))"
check_target_eq function_acl 0 "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('public','drizzle') AND p.prokind='f' AND (pg_get_userbyid(p.proowner) <> '$migration_role' OR NOT has_function_privilege('$runtime_role',p.oid,'EXECUTE') OR NOT has_function_privilege('$migration_role',p.oid,'EXECUTE') OR has_function_privilege('public',p.oid,'EXECUTE') OR EXISTS (SELECT 1 FROM aclexplode(coalesce(p.proacl,'{}'::aclitem[])) x LEFT JOIN pg_roles gx ON gx.oid=x.grantee WHERE gx.rolname IS NULL OR gx.rolname NOT IN ('$runtime_role','$migration_role','pg_database_owner') OR x.privilege_type <> 'EXECUTE'))"

# Default privileges are checked as catalog rows, including the function class,
# and no unrelated owner may widen the future runtime boundary.
check_target_eq default_acl_count 2 "SELECT count(*) FROM pg_default_acl d JOIN pg_roles r ON r.oid=d.defaclrole JOIN pg_namespace n ON n.oid=d.defaclnamespace WHERE r.rolname='$migration_role' AND n.nspname='public' AND ((d.defaclobjtype='r' AND d.defaclacl::text='$expected_default_relation_acl') OR (d.defaclobjtype='S' AND d.defaclacl::text='$expected_default_sequence_acl'))"
check_target_eq default_acl_invalid 0 "SELECT count(*) FROM pg_default_acl d LEFT JOIN pg_roles r ON r.oid=d.defaclrole LEFT JOIN pg_namespace n ON n.oid=d.defaclnamespace WHERE r.rolname='$migration_role' AND (n.nspname IS DISTINCT FROM 'public' OR d.defaclobjtype NOT IN ('r','S') OR (d.defaclobjtype='r' AND d.defaclacl::text <> '$expected_default_relation_acl') OR (d.defaclobjtype='S' AND d.defaclacl::text <> '$expected_default_sequence_acl'))"
check_target_eq default_function_acl 0 "SELECT count(*) FROM pg_default_acl d JOIN pg_roles r ON r.oid=d.defaclrole WHERE r.rolname='$migration_role' AND d.defaclobjtype='f'"
check_target_eq runtime_default_acl 0 "SELECT count(*) FROM pg_default_acl d JOIN pg_roles r ON r.oid=d.defaclrole WHERE r.rolname='$runtime_role'"
check_target_eq owner_default_acl 0 "SELECT count(*) FROM pg_default_acl d JOIN pg_roles r ON r.oid=d.defaclrole WHERE r.rolname='reactive_resume_dev_owner'"

# No role can connect to another database through PUBLIC or an accidental
# explicit grant. This is an intentional sanitized blocker while shared engine
# platform defaults remain broad.
check_eq foreign_database_connect 0 "SELECT count(*) FROM pg_database WHERE datallowconn AND NOT datistemplate AND datname <> '$database' AND (has_database_privilege('$runtime_role',datname,'CONNECT') OR has_database_privilege('$migration_role',datname,'CONNECT'))"
check_eq runtime_create_database f "SELECT rolcreatedb FROM pg_roles WHERE rolname='$runtime_role'"
check_eq migration_create_database f "SELECT rolcreatedb FROM pg_roles WHERE rolname='$migration_role'"
check_eq runtime_create_role f "SELECT rolcreaterole FROM pg_roles WHERE rolname='$runtime_role'"
check_eq migration_create_role f "SELECT rolcreaterole FROM pg_roles WHERE rolname='$migration_role'"

if [ -n "$failures" ]; then
  printf 'REACTIVE_RESUME_DEV_SUCCESSOR:BLOCKED checks=%s database_catalog=observed roles_catalog=observed crs_not_required=true ca_source=existing-reactive-resume-dev-ca mutation=none\n' "${failures#,}" >&2
  exit 31
fi
printf '%s\n' 'REACTIVE_RESUME_DEV_SUCCESSOR:READY catalog=roles-database-schema-relation-sequence-function-default-acl-foreign verified crs_not_required=true ca_source=existing-reactive-resume-dev-ca mutation=none'
