#!/bin/sh
set -eu

# A guarded seed must reject every task-selection request before Kubernetes contact.
readonly wrapper="$(CDPATH= cd -- "$(/usr/bin/dirname -- "$0")/.." && pwd -P)/ansible/bin/seed-infisical-universal-auth"
temporary_directory="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/cristexweb-seed-task-start.XXXXXX")"
output_file="$temporary_directory/output"
cleanup() { /bin/rm -rf -- "$temporary_directory"; }
trap cleanup EXIT HUP INT TERM
set +e
"$wrapper" apply --start-at-task 'Seed exactly the three Universal Auth credential Secrets' >"$output_file" 2>&1
status=$?
set -e
[ "$status" -ne 0 ]
! grep -Fq 'Universal Auth credential seed completed' "$output_file"
printf '%s\n' 'PASS: Universal Auth seed task-selection bypass is rejected'
