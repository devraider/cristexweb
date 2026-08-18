#!/bin/sh
set -eu
repository_root="$(CDPATH= cd -- "$(/usr/bin/dirname -- "$0")/.." && pwd -P)"
helm_bin="${HELM_BIN:-helm}"
[ -f "$helm_bin" ] && [ -x "$helm_bin" ] && [ ! -L "$helm_bin" ] || {
  printf '%s\n' 'HELM_BIN must name a regular executable Helm v3.19.0 binary' >&2
  exit 69
}
[ "$($helm_bin version --template '{{.Version}}')" = v3.19.0 ] || {
  printf '%s\n' 'refusing an unpinned Helm renderer' >&2
  exit 78
}
temporary_render="$(/usr/bin/mktemp "${TMPDIR:-/tmp}/cristexweb-argocd-render.XXXXXX")"
cleanup() { /bin/rm -f -- "$temporary_render"; }
trap cleanup EXIT HUP INT TERM
cd -- "$repository_root"
"$helm_bin" template argocd \
  ansible/files/vendor/argocd/10.3.0/argo-cd-10.3.0.tgz \
  --namespace argocd \
  -f ansible/files/components/argocd/CHART-RENDER-EVIDENCE-VALUES.yaml \
  >"$temporary_render"
"$repository_root/.venv/bin/python" - "$temporary_render" <<'PY'
from pathlib import Path
import hashlib
import sys

import yaml

base = Path("ansible/files/components/argocd")
render = [value for value in yaml.safe_load_all(Path(sys.argv[1]).read_text()) if value]
committed = [
    yaml.safe_load(path.read_text())
    for directory in ("crds", "config", "runtime", "rbac", "network")
    for path in (base / directory).glob("*.yaml")
]
mapping = yaml.safe_load((base / "SOURCE-MAPPING.yml").read_text())


def identity(value):
    metadata = value["metadata"]
    return "|".join(
        (
            value["apiVersion"],
            value["kind"],
            metadata.get("namespace", ""),
            metadata["name"],
        )
    )


rendered = {identity(value) for value in render}
closure = {identity(value) for value in committed}
promoted = set(mapping["chartRenderedIdentitiesPromoted"])
custom = set(mapping["customHardenedIdentities"])
omitted = set(mapping["intentionallyOmittedRenderedIdentities"])
assert len(render) == len(rendered) == 35
assert len(committed) == len(closure) == 32
assert rendered & closure == promoted
assert closure - rendered == custom
assert rendered - closure == omitted
assert len(promoted) == 24 and len(custom) == 8 and len(omitted) == 11
for entry in mapping["promotedCrds"]:
    source = next(
        value
        for value in render
        if value["kind"] == "CustomResourceDefinition"
        and value["metadata"]["name"] == entry["name"]
    )
    target = yaml.safe_load((base / entry["target"]).read_text())
    assert source["spec"] == target["spec"]
archive = Path(mapping["chart"]["vendoredArchive"])
assert hashlib.sha256(archive.read_bytes()).hexdigest() == mapping["chart"]["vendoredArchiveSha256"]
print(
    "PASS: exact 35-object chart render partitions into 24 promoted, "
    "8 custom, and 11 omitted identities; 3 CRD specs and chart hash match"
)
PY
