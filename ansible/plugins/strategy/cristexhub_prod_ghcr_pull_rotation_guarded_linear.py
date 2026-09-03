from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath

from ansible import context
from ansible.errors import AnsibleError
from ansible.plugins.strategy.linear import StrategyModule as LinearStrategyModule


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_WRAPPER_SOURCE = _REPOSITORY_ROOT / "ansible/bin/check-cristexhub-prod-ghcr-pull-rotation"
_TASK_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_ghcr_pull_rotation_preflight/tasks/main.yml"
_DEFAULTS_SOURCE = _REPOSITORY_ROOT / "ansible/roles/cristexhub_prod_ghcr_pull_rotation_preflight/defaults/main.yml"
_PLAYBOOK_SOURCE = _REPOSITORY_ROOT / "ansible/playbooks/check_cristexhub_prod_ghcr_pull_rotation.yml"
_METADATA_SOURCE = _REPOSITORY_ROOT / "ansible/library/cristexhub_prod_ghcr_pull_secret_metadata.py"
_POLICY_SOURCE = _REPOSITORY_ROOT / "ansible/files/policies/cristexhub-prod-ghcr-pull-rotation.yml"
_STRATEGY_SOURCE = _REPOSITORY_ROOT / "ansible/plugins/strategy/cristexhub_prod_ghcr_pull_rotation_guarded_linear.py"
_INVENTORY_SOURCE = _REPOSITORY_ROOT / "ansible/inventory/hosts.yml"
_ANSIBLE_CONFIG_SOURCE = _REPOSITORY_ROOT / "ansible/ansible.cfg"
_REQUIREMENTS_SOURCE = _REPOSITORY_ROOT / "ansible/requirements.yml"
_COLLECTION_MANIFEST_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/collections/ansible_collections/kubernetes/core/MANIFEST.json"
_COLLECTION_FILES_SOURCE = _REPOSITORY_ROOT / "ansible/.ansible/collections/ansible_collections/kubernetes/core/FILES.json"
_COLLECTION_ROOT = _REPOSITORY_ROOT / "ansible/.ansible/collections/ansible_collections/kubernetes/core"
_CONTROLLER_SOURCE = _REPOSITORY_ROOT / ".venv/bin/ansible-playbook"

_TASK_SHA256 = "9dea31a595df794a2881ebc3f6d24a97bc9ef787e93636380d34e530b32b612a"
_DEFAULTS_SHA256 = "6200250ef5a92050f9fd55271014a075db92ef17e7cdad9f69238104b0c29603"
_PLAYBOOK_SHA256 = "1aa2553934d39f23f425921f9ed7d78addb9079a2beea9a7a1e0819de4e8b061"
_METADATA_SHA256 = "be834fae4afd0001f15f807f6e52f511dd040a843747bf03c2b5ddc3efd0068e"
_POLICY_SHA256 = "6cfd66000b544ff848c2f81542d2c65d7f53bb615d95b3227b4adcc93f82407d"
_INVENTORY_SHA256 = "843dd43cdce256061d8e6b58b563acd00c3a1d7a1357e5f59ea30040af244752"
_ANSIBLE_CONFIG_SHA256 = "4e39dec40f1f0a0735e7f27e35f464093de3b16e8be1e5fa05299005528a85d9"
_REQUIREMENTS_SHA256 = "f82d9e5ba1b64324710eb66c956d0447c46d3958722f635a4502bcb6c3efc75f"
_COLLECTION_MANIFEST_SHA256 = "dc32e90ca987d6199e9091f749ecb40fd3380b40aabb7c18961ec75582cfc6df"
_COLLECTION_FILES_SHA256 = "9d30dde4e4d6d04ec2e9b00a2d787114f13577fd2c456d25726865e3db39fa69"
_CONTROLLER_SHA256 = "baf52d00491b00126ccc19ec1a2e018e107c134e663885e748e5fe4e3777b3fd"
_STRATEGY_CANONICAL_SHA256 = "23e591d7483a02b8e0b6902b4938db16bc86acfef0a2f3c5d5251f7ca8dd164f"
_EXPECTED_COLLECTION_ACTION_PATHS = {
    "helm.py": "k8s_info.py",
    "helm_info.py": "k8s_info.py",
    "helm_plugin.py": "k8s_info.py",
    "helm_plugin_info.py": "k8s_info.py",
    "helm_repository.py": "k8s_info.py",
    "k8s.py": "k8s_info.py",
    "k8s_cluster_info.py": "k8s_info.py",
    "k8s_cp.py": "k8s_info.py",
    "k8s_drain.py": "k8s_info.py",
    "k8s_exec.py": "k8s_info.py",
    "k8s_json_patch.py": "k8s_info.py",
    "k8s_log.py": "k8s_info.py",
    "k8s_rollback.py": "k8s_info.py",
    "k8s_scale.py": "k8s_info.py",
    "k8s_service.py": "k8s_info.py",
    "k8s_info.py": None,
}

_EXPECTED_COLLECTION_MODULES = {
    "__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "helm.py": "9c4d458c103a3af799958449283c3f5f201e289855387b3c19a714678dd35883",
    "helm_info.py": "86cad6e59f97bdcbebbf53eeb0ea9eaf7a031eef477ecd76bf109cb872c7fa1e",
    "helm_plugin.py": "c99d47fc5fcffafc060416fae69f740b6d18700f00843f0de2315eb32432c113",
    "helm_plugin_info.py": "42afe7b57c92837736d4df8f9e48fe3b71c2f529970acb65ad6b6fb5cf8e0148",
    "helm_pull.py": "051273964c4dd1d9498bca767673641ebabcc4f61b06ac95b741dcd4a38562ff",
    "helm_registry_auth.py": "59a27d6856c4af04d206c6eea6d3e844062e40073bda04bda0536a2857a6694d",
    "helm_repository.py": "c38905b50074a1337e41434e78ae6b79410e46c7c72632197544e6cf431172b0",
    "helm_template.py": "e736084eaa09c21be061d93d5ee21676103bd4955898e906aa17db4184e78545",
    "k8s.py": "079286f5c97131e6486b55624223c7800c64ba370729240bba7ceea2b8e8e848",
    "k8s_cluster_info.py": "0616d8c6ac9c83a572a1afe2d7cc68f5870bfac77a618171f003b9eb25c5877c",
    "k8s_cp.py": "8f19067c472d4761792fdbf93578c9224714bf241bf0eae4015892589ce3c237",
    "k8s_drain.py": "4fbe4f78cb74344bb8231315f27d3f09da3d23df1ed3a88f13771659652719ac",
    "k8s_exec.py": "c7e7ea0d37b1c65904ea29b07aa2fc41e085482216bcf9f97fd27486347ae062",
    "k8s_info.py": "e035cfa69a8955c1f97dc4aabf4763784691f20973a8638461ffaa699dfbc21d",
    "k8s_json_patch.py": "75b605254a576da3a146019e448d319a4cefdee2d2f3d4ada80e2c2b1c51d0ef",
    "k8s_log.py": "fc05e30eb060ff3bce8403eeb5f9748ab82242ef28a34dfe5ae20227e57fcbc5",
    "k8s_rollback.py": "f8bf4bf26cc8634882fd70e704cef6033642a15a316a4859cc03544fd3c31013",
    "k8s_scale.py": "cf508fa2f02619293fa664cf55531d5dd1b15d8d35f2bfe382fdc9f756a826c3",
    "k8s_service.py": "079bdfa6f65254fc1547b985e4713d25e6c5ff9c28332b9358e7a4456ff57979",
    "k8s_taint.py": "85d951125ea30ae907d40e79ef22d6e6be5aa5613cfa561de361be7ad5bb30ec",
}
_EXPECTED_COLLECTION_MODULE_UTILS_DIRECTORIES = {
    "plugins/module_utils",
    "plugins/module_utils/client",
    "plugins/module_utils/k8s",
}
_EXPECTED_COLLECTION_MODULE_UTILS = {
    "plugins/module_utils/client/discovery.py": "d30f9c5a9c90972264289b0e5cee95effe9319595e23aeaa4e079afeb716338a",
    "plugins/module_utils/client/resource.py": "5ecbd5410095b770939270966962c5e939b7e662eb6f51c1271d294e6e683ee2",
    "plugins/module_utils/k8s/client.py": "0056d2093cab9094eaa5cbeccd9256317f61f5c50d5044b2baf30dc5ba94fd97",
    "plugins/module_utils/k8s/core.py": "a54455932f24cd7580024e2058e290414fcad3b597332d4b0627b8898b3b95c3",
    "plugins/module_utils/k8s/exceptions.py": "68fc2551bb7c65b1d0352c6761d2f75a6ca59fa773f08faa3356ab4787c040eb",
    "plugins/module_utils/k8s/resource.py": "78f2e91fa52267f93d7f72191bdddcffaf92c9a9978c5c923f8f5912f3691fb6",
    "plugins/module_utils/k8s/runner.py": "8e0c6b86b38a86d491cf3898c91903f3ccce9fa213d8d06c84a6b43762f3d441",
    "plugins/module_utils/k8s/service.py": "fc53953488c8e4a53afa7aaf3c8fa70bcb197dc20555e7e0042ae66b7c84e4fe",
    "plugins/module_utils/k8s/waiter.py": "aee5d2ea1701a4dbd2ce21c8228ad1385b636613cc164c091b15b44b2c5c2341",
    "plugins/module_utils/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "plugins/module_utils/_version.py": "da42772669215aa2e1592bfcba0b4cef17d06cdbcdcfeb0ae05e431252fc5a16",
    "plugins/module_utils/ansiblemodule.py": "cde56b067dc7815d559ff8eb2335ad50ef43fc92fcc50812b44c61fb4b854ba6",
    "plugins/module_utils/apply.py": "8f568ec79b19a7e6c601b92dc62e6bb540fd295dc0730460f3b6e0e35a1d4441",
    "plugins/module_utils/args_common.py": "dbd6a5c7b2d504de36fa0b75571b8df4c8c07f11d4b6b0dbe296e313e4937355",
    "plugins/module_utils/common.py": "2b9252ccc909f3013e7a05a5845d9fbb1e5f24e6d44c956a14ed3ae90d3b0a1d",
    "plugins/module_utils/copy.py": "aec7f7effed09d03fe2b8b4218e51d6b3c921a01c05e0c2d26a58e90e35f708a",
    "plugins/module_utils/exceptions.py": "4256700ac9b1b0b29a0daa8d24da068a8435413cdd927b9613f4fa568e5ee450",
    "plugins/module_utils/hashes.py": "a8ccce48ad134285d61384ea7598c1efdbd9ae4222e0566d154d86ecbfa3a02e",
    "plugins/module_utils/helm.py": "2fe2e843b583f80c259c4c13c6ca278b3d6faa7036d314c2001f3d94161f842a",
    "plugins/module_utils/helm_args_common.py": "6561042a0092f0b1187d469b972acbc320b0d6a1355f1c0bf6bc6c894f78b074",
    "plugins/module_utils/k8sdynamicclient.py": "6b44b539981affc25ede49cc8a7f994fe19b5c60aaa1e400a480e735f7ed1be6",
    "plugins/module_utils/selector.py": "d5e15a8ac4f916ee4b578450449a525dbda727b77178941a81c21e9e228e7987",
    "plugins/module_utils/version.py": "c009a2e470b5c1e2cfc73efb061b3289f3da5064c85ad31dd664433ddb7b97b7",
}

_EXPECTED_ENV_PREFIX = "CRISTEXWEB_CRISTEXHUB_PROD_GHCR_PULL_ROTATION_PREFLIGHT_"
_FORBIDDEN_ENV = (
    "ANSIBLE_INVENTORY",
    "ANSIBLE_PLAYBOOK_DIR",
    "ANSIBLE_STRATEGY",
    "ANSIBLE_ACTION_PLUGINS",
    "ANSIBLE_STRATEGY_PLUGINS",
    "ANSIBLE_LIBRARY",
    "ANSIBLE_COLLECTIONS_PATH",
    "ANSIBLE_STDOUT_CALLBACK",
    "ANSIBLE_CALLBACK_PLUGINS",
    "ANSIBLE_LOAD_CALLBACK_PLUGINS",
    "ANSIBLE_VAULT_PASSWORD_FILE",
    "ANSIBLE_PRIVATE_KEY_FILE",
    "ANSIBLE_REMOTE_USER",
    "ANSIBLE_BECOME_EXE",
    "ANSIBLE_BECOME_METHOD",
    "ANSIBLE_BECOME_USER",
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTHONOPTIMIZE",
    "PYTHONINSPECT",
    "PYTHONBREAKPOINT",
    "VIRTUAL_ENV",
)


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeError):
        return ""


def _canonical_hash(path: Path, symbol: str) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        source, count = re.subn(
            rf"(?m)^({re.escape(symbol)}\s*=\s*[\"'])([0-9a-f]{{64}})([\"']\s*)$",
            rf"\g<1>{'0' * 64}\g<3>",
            source,
        )
        return hashlib.sha256(source.encode("utf-8")).hexdigest() if count == 1 else ""
    except (OSError, UnicodeError):
        return ""


def _regular(path: Path, mode: int, owner: int | None = None) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
    except OSError:
        return False
    return (
        stat.S_ISREG(state.st_mode)
        and not path.is_symlink()
        and stat.S_IMODE(state.st_mode) == mode
        and (owner is None or (state.st_uid == owner and state.st_gid == os.getgid()))
    )


def _regular_file(path: Path, mode: int = 0o644, owner: int | None = None) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
        return (
            stat.S_ISREG(state.st_mode)
            and not path.is_symlink()
            and stat.S_IMODE(state.st_mode) == mode
            and (owner is None or state.st_uid == owner)
        )
    except OSError:
        return False


def _directory(path: Path, mode: int = 0o755, owner: int | None = None) -> bool:
    try:
        state = path.stat(follow_symlinks=False)
        return (
            stat.S_ISDIR(state.st_mode)
            and not path.is_symlink()
            and stat.S_IMODE(state.st_mode) == mode
            and (owner is None or state.st_uid == owner)
        )
    except OSError:
        return False


def _pinned_relative_symlink(source: Path, target: Path, link_target: str, owner: int | None = None) -> bool:
    try:
        state = source.stat(follow_symlinks=False)
        return (
            stat.S_ISLNK(state.st_mode)
            and (owner is None or state.st_uid == owner)
            and os.readlink(source) == link_target
            and source.resolve(strict=True) == target.resolve(strict=True)
        )
    except (OSError, RuntimeError):
        return False


def _collection_tree_entries(path: Path) -> set[str]:
    return {
        entry.relative_to(path).as_posix()
        for entry in path.rglob('*')
        if entry.is_symlink() or entry.is_file()
    }


def _collection_tree_directories(path: Path) -> set[str]:
    return {
        entry.relative_to(path).as_posix()
        for entry in path.rglob('*')
        if entry.is_dir() and not entry.is_symlink()
    }


def _collection_has_forbidden_artifacts(path: Path) -> bool:
    forbidden_suffixes = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.pyd'}
    try:
        return any(
            entry.name == '__pycache__' or entry.suffix.lower() in forbidden_suffixes
            for entry in path.rglob('*')
        )
    except (OSError, RuntimeError):
        return True


def _collection_manifest_tree_valid(path: Path, files_manifest: dict) -> bool:
    try:
        entries = files_manifest.get('files')
        if not isinstance(entries, list):
            return False
        expected: dict[str, tuple[str, str | None]] = {}
        for item in entries:
            if not isinstance(item, dict):
                return False
            name = item.get('name')
            kind = item.get('ftype')
            if name == '.':
                if kind != 'dir':
                    return False
                continue
            if not isinstance(name, str) or not name:
                return False
            relative = PurePosixPath(name)
            if (
                relative.is_absolute()
                or relative.as_posix() != name
                or any(part in {'', '.', '..'} for part in relative.parts)
                or kind not in {'file', 'dir'}
                or name in expected
            ):
                return False
            digest = item.get('chksum_sha256')
            if kind == 'file' and (
                not isinstance(digest, str) or re.fullmatch(r'[0-9a-f]{64}', digest) is None
            ):
                return False
            if kind == 'dir' and digest not in (None, ''):
                return False
            expected[name] = (kind, digest if kind == 'file' else None)
        expected['FILES.json'] = ('file', None)
        expected['MANIFEST.json'] = ('file', None)
        actual: dict[str, str] = {}
        symlinks: set[str] = set()
        for entry in path.rglob('*'):
            name = entry.relative_to(path).as_posix()
            if entry.is_symlink():
                actual[name] = 'file'
                symlinks.add(name)
            elif entry.is_dir():
                actual[name] = 'dir'
            elif entry.is_file():
                actual[name] = 'file'
            else:
                return False
        if actual != {name: kind for name, (kind, _) in expected.items()}:
            return False
        allowed_symlinks = {
            f'plugins/action/{name}'
            for name, target in _EXPECTED_COLLECTION_ACTION_PATHS.items()
            if target is not None
        }
        if symlinks != allowed_symlinks:
            return False
        for name, (kind, digest) in expected.items():
            entry = path / name
            state = entry.stat(follow_symlinks=False)
            if kind == 'dir':
                if (
                    entry.is_symlink()
                    or not stat.S_ISDIR(state.st_mode)
                    or stat.S_IMODE(state.st_mode) != 0o755
                    or state.st_uid != os.getuid()
                ):
                    return False
                continue
            if entry.is_symlink():
                if name not in allowed_symlinks or state.st_uid != os.getuid():
                    return False
            elif (
                not stat.S_ISREG(state.st_mode)
                or state.st_uid != os.getuid()
                or stat.S_IMODE(state.st_mode) not in {0o644, 0o755}
            ):
                return False
            if digest is not None and _sha256(entry) != digest:
                return False
        return True
    except (OSError, RuntimeError, UnicodeError, ValueError, TypeError):
        return False


def _collection_toolchain_valid() -> bool:
    """Require the installed kubernetes.core tree to match its pinned FILES.json."""
    try:
        plugins = _COLLECTION_ROOT / 'plugins'
        actions = plugins / 'action'
        modules = plugins / 'modules'
        module_utils = plugins / 'module_utils'
        if not all(_directory(item, 0o755, os.getuid()) for item in (
            _COLLECTION_ROOT, plugins, actions, modules, module_utils,
        )):
            return False
        if any(_collection_has_forbidden_artifacts(item) for item in (plugins,)):
            return False
        if _collection_tree_entries(actions) != set(_EXPECTED_COLLECTION_ACTION_PATHS):
            return False
        if _collection_tree_directories(actions):
            return False
        if _collection_tree_entries(modules) != set(_EXPECTED_COLLECTION_MODULES):
            return False
        if _collection_tree_directories(modules):
            return False
        expected_utils_files = {
            name.removeprefix('plugins/module_utils/')
            for name in _EXPECTED_COLLECTION_MODULE_UTILS
        }
        if _collection_tree_entries(module_utils) != expected_utils_files:
            return False
        expected_utils_dirs = {
            name.removeprefix('plugins/module_utils/')
            for name in _EXPECTED_COLLECTION_MODULE_UTILS_DIRECTORIES
            if name != 'plugins/module_utils'
        }
        if _collection_tree_directories(module_utils) != expected_utils_dirs:
            return False
        if not _regular_file(_COLLECTION_MANIFEST_SOURCE, 0o644, os.getuid()):
            return False
        if _sha256(_COLLECTION_MANIFEST_SOURCE) != _COLLECTION_MANIFEST_SHA256:
            return False
        if not _regular_file(_COLLECTION_FILES_SOURCE, 0o644, os.getuid()):
            return False
        if _sha256(_COLLECTION_FILES_SOURCE) != _COLLECTION_FILES_SHA256:
            return False
        files_manifest = json.loads(_COLLECTION_FILES_SOURCE.read_text(encoding='utf-8'))
        if not _collection_manifest_tree_valid(_COLLECTION_ROOT, files_manifest):
            return False
        manifest_files = {
            item.get('name'): item.get('chksum_sha256')
            for item in files_manifest.get('files', [])
            if isinstance(item, dict)
            and item.get('ftype') == 'file'
            and isinstance(item.get('name'), str)
            and (
                item['name'].startswith('plugins/action/')
                or item['name'].startswith('plugins/modules/')
                or item['name'].startswith('plugins/module_utils/')
            )
        }
        expected_manifest_files = {
            **{
                f'plugins/action/{name}': '3f4a8318615ea5401fdea6d1177c181ad11e31e48eaf7f8f0fa6554a053fb16b'
                for name in _EXPECTED_COLLECTION_ACTION_PATHS
            },
            **{f'plugins/modules/{name}': digest for name, digest in _EXPECTED_COLLECTION_MODULES.items()},
            **_EXPECTED_COLLECTION_MODULE_UTILS,
        }
        if manifest_files != expected_manifest_files:
            return False
        if not all(
            _regular_file(modules / name, 0o644, os.getuid())
            and _sha256(modules / name) == digest
            for name, digest in _EXPECTED_COLLECTION_MODULES.items()
        ):
            return False
        if not all(
            _regular_file(_COLLECTION_ROOT / name, 0o644, os.getuid())
            and _sha256(_COLLECTION_ROOT / name) == digest
            for name, digest in _EXPECTED_COLLECTION_MODULE_UTILS.items()
        ):
            return False
        if not all(
            _directory(_COLLECTION_ROOT / name, 0o755, os.getuid())
            for name in _EXPECTED_COLLECTION_MODULE_UTILS_DIRECTORIES
        ):
            return False
        manifest = json.loads(_COLLECTION_MANIFEST_SOURCE.read_text(encoding='utf-8'))
        info = manifest.get('collection_info', {})
        if info.get('namespace') != 'kubernetes' or info.get('name') != 'core' or info.get('version') != '6.1.0':
            return False
        for name, target in _EXPECTED_COLLECTION_ACTION_PATHS.items():
            action_path = actions / name
            if target is None:
                if not _regular_file(
                    action_path, 0o644, os.getuid()
                ) or _sha256(action_path) != '3f4a8318615ea5401fdea6d1177c181ad11e31e48eaf7f8f0fa6554a053fb16b':
                    return False
            elif not _pinned_relative_symlink(
                action_path, actions / 'k8s_info.py', target, os.getuid()
            ):
                return False
        return True
    except (OSError, RuntimeError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        return False


def _inventory_contract() -> bool:
    try:
        content = _INVENTORY_SOURCE.read_bytes()
    except OSError:
        return False
    return (
        _regular(_INVENTORY_SOURCE, 0o644, os.getuid())
        and hashlib.sha256(content).hexdigest() == _INVENTORY_SHA256
        and content
        == b"---\nall:\n  children:\n    k3s_servers:\n      hosts:\n        crtxweb:\n"
    )


def _source_contract() -> bool:
    expected = (
        (_WRAPPER_SOURCE, "WRAPPER_SHA256", 0o755, None),
        (_TASK_SOURCE, "TASK_SHA256", 0o644, os.getuid()),
        (_DEFAULTS_SOURCE, "DEFAULTS_SHA256", 0o644, os.getuid()),
        (_PLAYBOOK_SOURCE, "PLAYBOOK_SHA256", 0o644, os.getuid()),
        (_METADATA_SOURCE, "METADATA_MODULE_SHA256", 0o644, os.getuid()),
        (_POLICY_SOURCE, "POLICY_SHA256", 0o644, os.getuid()),
        (_STRATEGY_SOURCE, "STRATEGY_SHA256", 0o644, os.getuid()),
        (_ANSIBLE_CONFIG_SOURCE, "ANSIBLE_CONFIG_SHA256", 0o644, os.getuid()),
        (_REQUIREMENTS_SOURCE, "REQUIREMENTS_SHA256", 0o644, os.getuid()),
        (_COLLECTION_MANIFEST_SOURCE, "COLLECTION_MANIFEST_SHA256", 0o644, os.getuid()),
        (_COLLECTION_FILES_SOURCE, "COLLECTION_FILES_SHA256", 0o644, os.getuid()),
        (_INVENTORY_SOURCE, "INVENTORY_SHA256", 0o644, os.getuid()),
        (_CONTROLLER_SOURCE, "CONTROLLER_SHA256", 0o755, os.getuid()),
    )
    fixed = {
        "TASK_SHA256": _TASK_SHA256,
        "DEFAULTS_SHA256": _DEFAULTS_SHA256,
        "PLAYBOOK_SHA256": _PLAYBOOK_SHA256,
        "METADATA_MODULE_SHA256": _METADATA_SHA256,
        "POLICY_SHA256": _POLICY_SHA256,
        "ANSIBLE_CONFIG_SHA256": _ANSIBLE_CONFIG_SHA256,
        "REQUIREMENTS_SHA256": _REQUIREMENTS_SHA256,
        "COLLECTION_MANIFEST_SHA256": _COLLECTION_MANIFEST_SHA256,
        "COLLECTION_FILES_SHA256": _COLLECTION_FILES_SHA256,
        "INVENTORY_SHA256": _INVENTORY_SHA256,
        "CONTROLLER_SHA256": _CONTROLLER_SHA256,
    }
    if (
        not _inventory_contract()
        or not _collection_toolchain_valid()
        or _canonical_hash(_STRATEGY_SOURCE, "_STRATEGY_CANONICAL_SHA256") != _STRATEGY_CANONICAL_SHA256
    ):
        return False
    if os.environ.get(_EXPECTED_ENV_PREFIX + "STRATEGY_CANONICAL_SHA256") != _STRATEGY_CANONICAL_SHA256:
        return False
    for path, suffix, mode, owner in expected:
        if not _regular(path, mode, owner):
            return False
        digest = _sha256(path)
        supplied = os.environ.get(_EXPECTED_ENV_PREFIX + suffix, "")
        if suffix in {"WRAPPER_SHA256", "STRATEGY_SHA256"}:
            if digest != supplied:
                return False
        elif digest != fixed[suffix] or digest != supplied:
            return False
    return True


def _proc_parent(pid: int) -> int:
    try:
        text = Path(f"/proc/{pid}/status").read_text(encoding="ascii")
        return int(next(line for line in text.splitlines() if line.startswith("PPid:")).split()[1])
    except (OSError, UnicodeError, StopIteration, ValueError, IndexError):
        return 0


def _proc_starttime(pid: int) -> str:
    try:
        tail = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").rsplit(") ", 1)[1].split()
        return tail[19]
    except (OSError, UnicodeError, IndexError):
        return ""


def _proc_cmdline(pid: int) -> list[str]:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        if not raw.endswith(b"\0"):
            return []
        return [part.decode("utf-8", "strict") for part in raw[:-1].split(b"\0")]
    except (OSError, UnicodeError):
        return []


def _proc_executable(pid: int) -> Path | None:
    try:
        return Path(os.readlink(f"/proc/{pid}/exe")).resolve(strict=True)
    except (OSError, RuntimeError):
        return None


def _canonical_shell(pid: int, command: list[str]) -> bool:
    if not command or command[0] not in {"/bin/sh", "/bin/dash"}:
        return False
    try:
        dash = Path("/usr/bin/dash").resolve(strict=True)
        requested = Path(command[0]).resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    return requested == dash and _proc_executable(pid) == dash


def _is_ancestor(pid: int) -> bool:
    current = os.getpid()
    seen: set[int] = set()
    while current > 1 and current not in seen:
        if current == pid:
            return True
        seen.add(current)
        current = _proc_parent(current)
    return False


def _canonical_wrapper_argument(argument: str, pid: int) -> bool:
    try:
        cwd = Path(os.readlink(f"/proc/{pid}/cwd"))
        return (cwd / argument).resolve() == _WRAPPER_SOURCE
    except OSError:
        return False


def _wrapper_binding_valid() -> bool:
    prefix = _EXPECTED_ENV_PREFIX
    token = os.environ.get(prefix + "TOKEN", "")
    attestation = os.environ.get(prefix + "ATTESTATION_FILE", "")
    pid_text = os.environ.get(prefix + "WRAPPER_PID", "")
    starttime = os.environ.get(prefix + "WRAPPER_STARTTIME", "")
    wrapper_sha = os.environ.get(prefix + "WRAPPER_SHA256", "")
    try:
        pid = int(pid_text)
        state = Path(attestation).stat(follow_symlinks=False)
        content = Path(attestation).read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return False
    command = _proc_cmdline(pid)
    return (
        os.environ.get(prefix + "ENTRYPOINT") == "v1"
        and re.fullmatch(r"[0-9a-f]{64}", token) is not None
        and pid > 1
        and _is_ancestor(pid)
        and _proc_starttime(pid) == starttime
        and stat.S_ISREG(state.st_mode)
        and not stat.S_ISLNK(state.st_mode)
        and stat.S_IMODE(state.st_mode) == 0o600
        and state.st_uid == os.getuid()
        and state.st_gid == os.getgid()
        and state.st_nlink == 1
        and _canonical_shell(pid, command)
        and len(command) == 3
        and _canonical_wrapper_argument(command[1], pid)
        and command[2] == "check"
        and content == f"{token}:entrypoint:{pid}:{starttime}:{wrapper_sha}\n"
        and os.environ.get(prefix + "WRAPPER_PATH") == str(_WRAPPER_SOURCE)
        and wrapper_sha == _sha256(_WRAPPER_SOURCE)
        and os.environ.get(prefix + "ANSIBLE_CONFIG_PATH") == str(_ANSIBLE_CONFIG_SOURCE)
        and os.environ.get(prefix + "INVENTORY_PATH") == str(_INVENTORY_SOURCE)
        and os.environ.get(prefix + "CONTROLLER_PATH") == str(_CONTROLLER_SOURCE)
        and os.environ.get(prefix + "TOOLCHAIN_PATH") == str(_COLLECTION_MANIFEST_SOURCE)
        and os.environ.get(prefix + "STRATEGY_PATH") == str(_STRATEGY_SOURCE)
        and os.environ.get(prefix + "STRATEGY_CANONICAL_SHA256") == _STRATEGY_CANONICAL_SHA256
        and os.environ.get("ANSIBLE_CONFIG") == str(_ANSIBLE_CONFIG_SOURCE)
        and not any(os.environ.get(name) for name in _FORBIDDEN_ENV)
    )


def _canonical_argv() -> bool:
    expected = [
        "-i",
        str(_INVENTORY_SOURCE),
        str(_PLAYBOOK_SOURCE),
        "--check",
        "--diff",
        "--limit",
        "crtxweb",
        "--connection",
        "local",
        "--extra-vars",
        '{"cristexhub_prod_ghcr_pull_rotation_preflight_approved":true}',
    ]
    return sys.argv[1:] == expected


def _selection_is_canonical() -> bool:
    tags = list(context.CLIARGS.get("tags") or [])
    skip_tags = list(context.CLIARGS.get("skip_tags") or [])
    inventory = context.CLIARGS.get("inventory") or []
    inventory = [inventory] if isinstance(inventory, str) else list(inventory)
    selection_argv = any(
        argument == "-t"
        or (argument.startswith("-t") and len(argument) > 2)
        or argument in {"--tags", "--skip-tags", "--start-at-task", "--step"}
        or argument.startswith(("--tags=", "--skip-tags=", "--start-at-task=", "--step="))
        for argument in sys.argv[1:]
    )
    return (
        not selection_argv
        and context.CLIARGS.get("start_at_task") is None
        and not context.CLIARGS.get("step")
        and tags in ([], ["all"])
        and not skip_tags
        and context.CLIARGS.get("subset") == "crtxweb"
        and context.CLIARGS.get("check") is True
        and context.CLIARGS.get("diff") is True
        and inventory == [str(_INVENTORY_SOURCE)]
    )


class StrategyModule(LinearStrategyModule):
    """Run provenance checks before Ansible can iterate or skip role tasks."""

    def run(self, iterator, play_context):  # type: ignore[no-untyped-def]
        if not _canonical_argv() or not _selection_is_canonical() or not _source_contract() or not _wrapper_binding_valid():
            raise AnsibleError(
                "TASK_SELECTION_GUARD: GHCR rotation requires the complete canonical wrapper provenance"
            )
        os.environ[_EXPECTED_ENV_PREFIX + "STRATEGY_ATTESTED"] = "v1"
        return super().run(iterator, play_context)
