#!/bin/sh
set -eu

readonly wrapper="$(CDPATH= cd -- "$(/usr/bin/dirname -- "$0")/.." && pwd -P)/ansible/bin/upload-infisical-bootstrap-values"
temporary_directory="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/cristexweb-infisical-upload.XXXXXX")"
output_file="$temporary_directory/output"
cleanup() { /bin/rm -rf -- "$temporary_directory"; }
trap cleanup EXIT HUP INT TERM
for argument in check --dry-run --rotate --endpoint http://127.0.0.1:1; do
  set +e
  "$wrapper" apply "$argument" >"$output_file" 2>&1
  status=$?
  set -e
  [ "$status" -ne 0 ]
done
! grep -Fq 'generated, encrypted, uploaded' "$output_file"
printf '%s\n' 'PASS: Infisical value uploader passthrough and rotation arguments are rejected'
