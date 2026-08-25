#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
python=${PYTHON:-$root/.venv/bin/python}
if [ ! -x "$python" ] && [ -x /home/paul/projects/cristexweb/.venv/bin/python ]; then
  python=/home/paul/projects/cristexweb/.venv/bin/python
fi
[ -x "$python" ] || { printf '%s\n' 'missing pinned offline Python controller' >&2; exit 69; }
exec "$python" - "$root" <<'PY'
import hashlib
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

root = Path(sys.argv[1])
collection_root = root / "ansible/.ansible/collections"
if not (collection_root / "ansible_collections").is_dir():
    collection_root = Path("/home/paul/projects/cristexweb/ansible/.ansible/collections")
if (collection_root / "ansible_collections").is_dir():
    sys.path.insert(0, str(collection_root))
plugin_path = root / "ansible/plugins/action/cristexhub_prod_registration_guarded_k8s.py"
spec = importlib.util.spec_from_file_location("cristexhub_prod_registration_guarded_k8s", plugin_path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.EXPECTED_REPOSITORY_ROOT = str(root)

manifest_path = root / "ansible/files/components/cristexhub-prod-registration/config/application-cristexhub-prod.yaml"
import yaml
application = yaml.safe_load(manifest_path.read_text())
application["metadata"] = dict(application["metadata"], resourceVersion="8")

prestate = []
for index, (api_version, kind, namespace, name) in enumerate(sorted(module.EXPECTED), start=1):
    prestate.append({
        "apiVersion": api_version,
        "kind": kind,
        "namespace": namespace,
        "name": name,
        "identity": f"{api_version}|{kind}|{namespace}|{name}",
        "uid": f"00000000-0000-4000-8000-{index:012d}",
        "resourceVersion": "7",
        "generation": "1",
    })
token = "a" * 64
binding = {
    "attestation_sha256": hashlib.sha256(token.encode()).hexdigest(),
    "manifest_names": sorted(name for _, _, _, name in module.EXPECTED),
    "manifest_identities": sorted(f"{api}|{kind}|{namespace}|{name}" for api, kind, namespace, name in module.EXPECTED),
    "prestate_names": sorted(name for _, _, _, name in module.EXPECTED),
    "prestate_identities": sorted(f"{api}|{kind}|{namespace}|{name}" for api, kind, namespace, name in module.EXPECTED),
    "object_count": 5,
    "namespace_contract": True,
    "repository_contract": True,
    "revision": "751885a42798d282e168131db147f13694a0a621",
    "legacy_transition_kinds": ["AppProject", "Application"],
    "target_transition_kinds": [],
    "legacy_transition_change_count": 2,
    "legacy_transition_uids": module.LEGACY_TRANSITION_UIDS,
    "legacy_transition_spec_hashes": module.LEGACY_TRANSITION_SPEC_HASHES,
    "legacy_transition_manifest_hashes": module.LEGACY_TRANSITION_MANIFEST_HASHES,
    "legacy_transition_metadata_hash": module.LEGACY_TRANSITION_METADATA_HASH,
    "prestate_object_count": 5,
    "prestate_bindings": prestate,
    "transition_change_count": 2,
    "no_delete_path": True,
}
task_vars = {
    "cristexhub_prod_registration_internal_preflight_binding": binding,
    "cristexhub_prod_registration_approved": True,
    "cristexhub_prod_registration_state": "present",
}
with tempfile.NamedTemporaryFile(mode="w", delete=False) as attestation:
    attestation.write(f"{token}:entrypoint\n")
    attestation_path = attestation.name
os.chmod(attestation_path, 0o600)
try:
    action = module.ActionModule.__new__(module.ActionModule)
    action._task = SimpleNamespace(
        action="cristexhub_prod_registration_guarded_k8s",
        name="Reconcile registration source without synchronization",
        args={
            "state": "present",
            "definition": application,
            "kubeconfig": "/etc/rancher/k3s/k3s.yaml",
            "wait": False,
            "wait_timeout": 60,
        },
        get_path=lambda: str(root / "ansible/roles/cristexhub_prod_registration/tasks/main.yml") + ":1",
    )
    env = {
        "CRISTEXWEB_REPOSITORY_ROOT": str(root),
        "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ENTRYPOINT": "v1",
        "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_TOKEN": token,
        "CRISTEXWEB_CRISTEXHUB_PROD_REGISTRATION_ATTESTATION_FILE": attestation_path,
    }
    with mock.patch.object(module.context, "CLIARGS", {"tags": [], "skip_tags": []}), mock.patch.dict(os.environ, env, clear=False):
        result = action.run(task_vars=task_vars)
    assert result.get("failed") is True, result
    assert "resourceVersion" in result.get("msg", ""), result
finally:
    Path(attestation_path).unlink(missing_ok=True)
print("resourceVersion TOCTOU fixture rejected changed precondition")
PY
