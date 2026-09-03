from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / 'ansible/files/components/shared-mongodb-networkpolicy'
NETWORK = COMPONENT / 'network'
DEFAULTS = ROOT / 'ansible/roles/shared_mongodb_networkpolicy_bootstrap/defaults/main.yml'
TASKS = ROOT / 'ansible/roles/shared_mongodb_networkpolicy_bootstrap/tasks/main.yml'
PLUGIN = ROOT / 'ansible/plugins/action/shared_mongodb_networkpolicy_guarded_k8s.py'
WRAPPER = ROOT / 'ansible/bin/bootstrap-shared-mongodb-networkpolicy'
PLAYBOOK = ROOT / 'ansible/playbooks/bootstrap_shared_mongodb_networkpolicy.yml'
PLUGIN_MODULE = None


class SharedMongoDbNetworkPolicyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = sorted(NETWORK.glob('*.yaml'))
        cls.objects = [yaml.safe_load(path.read_text()) for path in cls.paths]
        cls.by_name = {obj['metadata']['name']: obj for obj in cls.objects}
        package_names = [
            'ansible_collections',
            'ansible_collections.kubernetes',
            'ansible_collections.kubernetes.core',
            'ansible_collections.kubernetes.core.plugins',
            'ansible_collections.kubernetes.core.plugins.action',
        ]
        fake_modules: dict[str, ModuleType] = {}
        for name in package_names:
            package = ModuleType(name)
            package.__path__ = []
            fake_modules[name] = package
        k8s_module = ModuleType('ansible_collections.kubernetes.core.plugins.action.k8s')
        k8s_module.ActionModule = type('KubernetesActionModule', (), {})
        fake_modules[k8s_module.__name__] = k8s_module
        spec = importlib.util.spec_from_file_location(
            'shared_mongodb_networkpolicy_guarded_k8s_contract', PLUGIN
        )
        assert spec is not None and spec.loader is not None
        cls.plugin = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, fake_modules):
            spec.loader.exec_module(cls.plugin)

    def test_exact_two_object_hash_bound_inventory(self) -> None:
        self.assertEqual(
            {
                'shared-mongodb-networkpolicy-allow',
                'shared-mongodb-networkpolicy-default-deny',
            },
            set(self.by_name),
        )
        ledger = {}
        for line in (COMPONENT / 'MANIFESTS.sha256').read_text().splitlines():
            digest, relative = line.split('  ', 1)
            ledger[relative] = digest
        self.assertEqual({str(path.relative_to(COMPONENT)) for path in self.paths}, set(ledger))
        for path in self.paths:
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                ledger[str(path.relative_to(COMPONENT))],
            )
        plugin = PLUGIN.read_text()
        literal = plugin.split('_EXPECTED_OBJECT_HASHES = ', 1)[1].split(
            '\n_EXPECTED_ARGUMENT_KEYS', 1
        )[0]
        plugin_hashes = ast.literal_eval(literal)
        expected = {}
        for obj in self.objects:
            identity = (
                obj['apiVersion'],
                obj['kind'],
                obj['metadata']['namespace'],
                obj['metadata']['name'],
            )
            expected[identity] = hashlib.sha256(
                json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()
            ).hexdigest()
        self.assertEqual(expected, plugin_hashes)
        self.assertIn('11352b9439d10f2ffdfad385ee31f524885fead8d74d38937101614f742ab575', plugin)
        defaults = yaml.safe_load(DEFAULTS.read_text())
        self.assertEqual(
            '/etc/rancher/k3s/k3s.yaml',
            defaults['shared_mongodb_networkpolicy_bootstrap_kubeconfig'],
        )
        self.assertEqual(2, defaults['shared_mongodb_networkpolicy_bootstrap_object_count'])
        self.assertIn('shared-mongodb-networkpolicy-default-deny.yaml', defaults['shared_mongodb_networkpolicy_bootstrap_manifest_paths'][0])
        self.assertIn('shared-mongodb-networkpolicy-allow.yaml', defaults['shared_mongodb_networkpolicy_bootstrap_manifest_paths'][1])
        self.assertEqual(
            sorted(self.by_name),
            sorted(defaults['shared_mongodb_networkpolicy_bootstrap_target_names']),
        )
        configured_hashes = {
            entry['path'].split('}}/', 1)[1]: entry['sha256']
            for entry in defaults['shared_mongodb_networkpolicy_bootstrap_expected_hashes']
        }
        self.assertEqual(set(ledger), set(configured_hashes))
        self.assertEqual(ledger, configured_hashes)
        identity_keys = sorted(
            '|'.join((obj['apiVersion'], obj['kind'], obj['metadata']['namespace'], obj['metadata']['name']))
            for obj in self.objects
        )
        self.assertEqual(
            '11352b9439d10f2ffdfad385ee31f524885fead8d74d38937101614f742ab575',
            hashlib.sha256('\n'.join(identity_keys).encode()).hexdigest(),
        )

    def test_live_operator_selector_and_exact_default_deny(self) -> None:
        selector = {
            'app': 'shared-mongodb-svc',
            'app.kubernetes.io/part-of': 'shared-databases',
            'cristex.io/component': 'mongodb',
        }
        deny = self.by_name['shared-mongodb-networkpolicy-default-deny']
        self.assertEqual('shared-services', deny['metadata']['namespace'])
        self.assertEqual(selector, deny['spec']['podSelector']['matchLabels'])
        self.assertEqual(['Ingress', 'Egress'], deny['spec']['policyTypes'])
        self.assertNotIn('ingress', deny['spec'])
        self.assertNotIn('egress', deny['spec'])

    def test_allow_policy_has_only_requested_ingress_and_egress(self) -> None:
        allow = self.by_name['shared-mongodb-networkpolicy-allow']['spec']
        selector = {
            'app': 'shared-mongodb-svc',
            'app.kubernetes.io/part-of': 'shared-databases',
            'cristex.io/component': 'mongodb',
        }
        self.assertEqual(selector, allow['podSelector']['matchLabels'])
        self.assertEqual(['Ingress', 'Egress'], allow['policyTypes'])
        self.assertEqual(1, len(allow['ingress']))
        ingress = allow['ingress'][0]
        self.assertEqual([{'protocol': 'TCP', 'port': 27017}], ingress['ports'])
        self.assertEqual(5, len(ingress['from']))
        self.assertEqual(
            [
                ('cristexhub-dev', 'backend'),
                ('cristexhub-dev', 'celery-worker'),
                ('cristexhub-prod', 'backend'),
                ('cristexhub-prod', 'celery-worker'),
            ],
            [
                (
                    source['namespaceSelector']['matchLabels']['kubernetes.io/metadata.name'],
                    source['podSelector']['matchLabels']['app.kubernetes.io/name'],
                )
                for source in ingress['from'][:4]
            ],
        )
        for source in ingress['from'][:4]:
            self.assertEqual(
                {'app.kubernetes.io/part-of': 'cristexhub'},
                {
                    key: value
                    for key, value in source['podSelector']['matchLabels'].items()
                    if key == 'app.kubernetes.io/part-of'
                },
            )
            self.assertNotIn('matchExpressions', source['podSelector'])
        self.assertEqual(selector, ingress['from'][4]['podSelector']['matchLabels'])
        self.assertNotIn('mongodb-system', json.dumps(allow))
        self.assertEqual(2, len(allow['egress']))
        same_set, dns = allow['egress']
        self.assertEqual(selector, same_set['to'][0]['podSelector']['matchLabels'])
        self.assertEqual([{'protocol': 'TCP', 'port': 27017}], same_set['ports'])
        self.assertEqual(
            {'kubernetes.io/metadata.name': 'kube-system'},
            dns['to'][0]['namespaceSelector']['matchLabels'],
        )
        self.assertEqual({'k8s-app': 'kube-dns'}, dns['to'][0]['podSelector']['matchLabels'])
        self.assertEqual({('TCP', 53), ('UDP', 53)}, {(x['protocol'], x['port']) for x in dns['ports']})

    def test_existing_target_uses_uid_resource_version_and_payload_cas(self) -> None:
        definition = copy.deepcopy(self.by_name['shared-mongodb-networkpolicy-default-deny'])
        prestate = {
            'name': definition['metadata']['name'],
            'uid': 'uid-default-deny',
            'resource_version': '17',
        }
        patch = self.plugin._networkpolicy_cas_patch(definition, prestate)
        self.assertEqual(
            [
                ('test', '/metadata/uid', 'uid-default-deny'),
                ('test', '/metadata/resourceVersion', '17'),
                ('test', '/metadata/labels', definition['metadata']['labels']),
                ('test', '/spec', definition['spec']),
            ],
            [(item['op'], item['path'], item['value']) for item in patch],
        )
        with self.assertRaises(ValueError):
            self.plugin._networkpolicy_cas_patch(definition, {
                'name': definition['metadata']['name'],
                'uid': 'uid-default-deny',
                'resource_version': 'stale',
            })

    def test_preflight_rejects_annotations_and_foreign_managed_field_ownership(self) -> None:
        definitions = copy.deepcopy(self.objects)
        pod = {
            'metadata': {'name': 'shared-mongodb-0', 'labels': self.plugin._MONGODB_POD_LABELS}
        }
        live = copy.deepcopy(definitions)
        for index, policy in enumerate(live):
            policy['metadata'].update({'uid': f'uid-{index}', 'resourceVersion': str(index + 1)})
        ledger = [
            {
                'name': policy['metadata']['name'],
                'uid': policy['metadata']['uid'],
                'resource_version': policy['metadata']['resourceVersion'],
            }
            for policy in live
        ]
        live[0]['metadata']['annotations'] = {'foreign.example/claim': 'x'}
        self.assertIn(
            'target NetworkPolicy drift',
            self.plugin._networkpolicy_preflight_error(live, definitions, pod, ledger),
        )
        live[0]['metadata'].pop('annotations')
        live[0]['metadata']['managedFields'] = [
            {'manager': 'argocd-application-controller', 'operation': 'Apply'}
        ]
        self.assertIn(
            'target NetworkPolicy drift',
            self.plugin._networkpolicy_preflight_error(live, definitions, pod, ledger),
        )
        live[0]['metadata']['managedFields'] = [
            {'manager': 'ansible', 'operation': 'Apply'}
        ]
        self.assertIsNone(
            self.plugin._networkpolicy_preflight_error(live, definitions, pod, ledger)
        )

    def test_portable_lock_requires_atomic_directory_owner_and_live_pid(self) -> None:
        with TemporaryDirectory() as directory:
            lock = Path(directory) / 'lock'
            lock.mkdir(mode=0o700)
            token = 'a' * 64
            starttime = '17'
            argv_sha256 = 'b' * 64
            (lock / 'owner').write_text(f'{token}:{os.getpid()}:{starttime}:{argv_sha256}\n')
            (lock / 'owner').chmod(0o600)
            with mock.patch.object(self.plugin, '_EXPECTED_LOCK_FILE', str(lock)), mock.patch.object(
                self.plugin, '_wrapper_process_valid', return_value=True
            ), mock.patch.dict(
                os.environ,
                {
                    'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_LOCK_FILE': str(lock),
                    'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_TOKEN': token,
                    'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_PID': str(os.getpid()),
                    'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_STARTTIME': starttime,
                    'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_ARGV_SHA256': argv_sha256,
                    'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_MODE': 'check',
                },
                clear=False,
            ):
                self.assertTrue(self.plugin._cooperative_lock_valid())
                (lock / 'owner').write_text(f'{token}:99999999:{starttime}:{argv_sha256}\n')
                self.assertFalse(self.plugin._cooperative_lock_valid())

    def test_cooperative_lock_rejects_unrelated_live_sleep_process(self) -> None:
        with TemporaryDirectory() as directory:
            lock = Path(directory) / 'lock'
            lock.mkdir(mode=0o700)
            token = 'c' * 64
            process = subprocess.Popen(['/bin/sleep', '5'])
            try:
                for _ in range(50):
                    observed = self.plugin._proc_stat(process.pid)
                    if observed is not None:
                        break
                    __import__('time').sleep(0.02)
                self.assertIsNotNone(observed)
                starttime = observed[1]
                argv_sha256 = 'd' * 64
                (lock / 'owner').write_text(
                    f'{token}:{process.pid}:{starttime}:{argv_sha256}\n'
                )
                (lock / 'owner').chmod(0o600)
                with mock.patch.object(self.plugin, '_EXPECTED_LOCK_FILE', str(lock)), mock.patch.dict(
                    os.environ,
                    {
                        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_LOCK_FILE': str(lock),
                        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_TOKEN': token,
                        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_PID': str(process.pid),
                        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_STARTTIME': str(starttime),
                        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_ARGV_SHA256': argv_sha256,
                        'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_MODE': 'check',
                    },
                    clear=False,
                ):
                    self.assertFalse(self.plugin._cooperative_lock_valid())
            finally:
                process.terminate()
                process.wait(timeout=5)

    def test_direct_action_process_cannot_claim_wrapper_ancestry(self) -> None:
        observed = self.plugin._proc_stat(os.getpid())
        self.assertIsNotNone(observed)
        self.assertFalse(
            self.plugin._wrapper_process_valid(
                os.getpid(), observed[1], 'check', 'e' * 64
            )
        )

    def test_wrapper_and_action_canonical_pins_match_their_source(self) -> None:
        for path, symbol in (
            (WRAPPER, 'wrapper_canonical_sha256_expected'),
            (PLUGIN, '_EXPECTED_ACTION_CANONICAL_SHA256'),
        ):
            source = path.read_text()
            match = re.search(
                rf'(?m)^({re.escape(symbol)}\s*=\s*[\'\"])([0-9a-f]{{64}})([\'\"]\s*)$',
                source,
            )
            self.assertIsNotNone(match)
            canonical = re.sub(
                rf'(?m)^({re.escape(symbol)}\s*=\s*[\'\"])[0-9a-f]{{64}}([\'\"]\s*)$',
                rf'\g<1>{"0" * 64}\g<2>',
                source,
            )
            self.assertEqual(match.group(2), hashlib.sha256(canonical.encode()).hexdigest())
        wrapper_action = re.search(
            r"(?m)^action_canonical_sha256_expected='([0-9a-f]{64})'$",
            WRAPPER.read_text(),
        )
        plugin_action = re.search(
            r"(?m)^_EXPECTED_ACTION_CANONICAL_SHA256 = '([0-9a-f]{64})'$",
            PLUGIN.read_text(),
        )
        self.assertIsNotNone(wrapper_action)
        self.assertIsNotNone(plugin_action)
        self.assertEqual(wrapper_action.group(1), plugin_action.group(1))

    def test_action_specific_canonical_hash_rejects_wrapper_sentinel_confusion(self) -> None:
        source = PLUGIN.read_text()
        canonical = self.plugin._canonical_file_hash(PLUGIN, '_EXPECTED_ACTION_CANONICAL_SHA256')
        self.assertEqual(self.plugin._EXPECTED_ACTION_CANONICAL_SHA256, canonical)
        self.assertIn('canonical_action_sha256()', WRAPPER.read_text())
        self.assertIn("canonical_action_sha256 \"$action_source\"", WRAPPER.read_text())
        self.assertNotIn('canonical_sha256 "$action_source"', WRAPPER.read_text())
        self.assertIn("_EXPECTED_ACTION_CANONICAL_SHA256 = '" + ('0' * 64) + "'", source.replace(
            self.plugin._EXPECTED_ACTION_CANONICAL_SHA256, '0' * 64
        ))

    def test_uv_python_symlink_contract_accepts_canonical_and_rejects_replacement(self) -> None:
        with TemporaryDirectory() as directory:
            link = Path(directory) / 'python'
            link.symlink_to('/usr/bin/python3')
            target = Path('/usr/bin/python3.13')
            with mock.patch.object(self.plugin, '_PYTHON_SOURCE', link), mock.patch.object(
                self.plugin, '_PYTHON_REAL_SOURCE', target
            ), mock.patch.object(self.plugin, '_EXPECTED_PYTHON_SHA256', hashlib.sha256(
                target.read_bytes()
            ).hexdigest()), mock.patch.object(self.plugin, '_regular_file', return_value=True):
                self.assertTrue(self.plugin._python_interpreter_valid())
                replacement = Path(directory) / 'replacement'
                replacement.write_bytes(b'replacement-python')
                link.unlink()
                link.symlink_to(replacement)
                self.assertFalse(self.plugin._python_interpreter_valid())

    def test_collection_action_symlink_and_module_hash_are_pinned(self) -> None:
        wrapper = WRAPPER.read_text()
        self.assertIn('case " $collection_module_utils_root_names " in\n      *" $tree_name "*)', wrapper)
        self.assertIn('case " client k8s " in *" $tree_name "*)', wrapper)
        plugin = PLUGIN.read_text()
        self.assertIn("readlink \"$json_patch_source\"", wrapper)
        self.assertIn("readlink \"$k8s_action_source\"", wrapper)
        self.assertIn("k8s_info_module_source", wrapper)
        self.assertIn("_K8S_ACTION_SOURCE", plugin)
        self.assertIn("_K8S_ACTION_TARGET", plugin)
        self.assertIn("_K8S_INFO_MODULE_SOURCE", plugin)
        self.assertIn("_JSON_PATCH_ACTION_SOURCE", plugin)
        self.assertIn("_JSON_PATCH_ACTION_TARGET", plugin)
        self.assertIn("_JSON_PATCH_MODULE_SOURCE", plugin)
        self.assertIn("_EXPECTED_COLLECTION_MANIFEST_SHA256", plugin)
        self.assertIn("_collection_toolchain_valid", plugin)
        self.assertIn("collection_manifest", wrapper)
        self.assertIn("collection_module_utils_expected", wrapper)
        self.assertIn("collection_modules_expected", wrapper)
        self.assertIn("check_exact_flat_collection_tree", wrapper)
        self.assertIn("check_collection_artifacts", wrapper)
        self.assertIn('check_collection_artifacts "$collection_root"', wrapper)
        self.assertIn("check_collection_manifest_tree", wrapper)
        self.assertIn('check_collection_manifest_tree "$collection_root" "$collection_files"', wrapper)
        self.assertIn("check_collection_namespace_tree", wrapper)
        self.assertIn('kubernetes.core-6.1.0.info', wrapper)
        self.assertIn("is_owned_directory_mode", wrapper)
        self.assertIn("kubernetes.core collection", wrapper)

    def test_new_collection_closure_paths_reject_each_adversarial_temp_copy(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            action_target = root / 'action' / 'k8s_info.py'
            action_source = root / 'action' / 'k8s.py'
            info_module = root / 'modules' / 'k8s_info.py'
            action_target.parent.mkdir()
            info_module.parent.mkdir()
            action_bytes = b'canonical action implementation\\n'
            module_bytes = b'canonical module implementation\\n'
            action_target.write_bytes(action_bytes)
            info_module.write_bytes(module_bytes)
            action_target.chmod(0o644)
            info_module.chmod(0o644)
            action_source.symlink_to('k8s_info.py')
            owner = os.getuid()
            action_digest = hashlib.sha256(action_bytes).hexdigest()
            module_digest = hashlib.sha256(module_bytes).hexdigest()
            self.assertTrue(self.plugin._pinned_relative_symlink(
                action_source, action_target, 'k8s_info.py', owner
            ))
            self.assertTrue(self.plugin._pinned_regular_file(action_target, action_digest, owner))
            self.assertTrue(self.plugin._pinned_regular_file(info_module, module_digest, owner))

            action_source.unlink()
            action_source.write_text('malicious action replacement\\n')
            self.assertFalse(self.plugin._pinned_relative_symlink(
                action_source, action_target, 'k8s_info.py', owner
            ))
            action_source.unlink()
            action_source.symlink_to('k8s_info.py')

            action_target.write_text('malicious action target\\n')
            self.assertFalse(self.plugin._pinned_regular_file(action_target, action_digest, owner))
            action_target.write_bytes(action_bytes)
            action_target.chmod(0o644)

            info_module.write_text('malicious k8s_info module\\n')
            self.assertFalse(self.plugin._pinned_regular_file(info_module, module_digest, owner))

    def test_wrapper_manifest_shell_harness_detects_clean_and_mutated_file(self) -> None:
        wrapper = WRAPPER.read_text()
        start = wrapper.index('check_collection_manifest_tree() {')
        end = wrapper.index('\ncheck_collection_namespace_tree()', start)
        harness = (
            '#!/bin/sh\n'
            'set -eu\n'
            f'python_tool={shlex.quote(sys.executable)}\n'
            + wrapper[start:end]
            + '\ncheck_collection_manifest_tree "$1" "$2"\n'
        )
        allowed_links = (
            'helm.py', 'helm_info.py', 'helm_plugin.py', 'helm_plugin_info.py',
            'helm_repository.py', 'k8s.py', 'k8s_cluster_info.py', 'k8s_cp.py',
            'k8s_drain.py', 'k8s_exec.py', 'k8s_json_patch.py', 'k8s_log.py',
            'k8s_rollback.py', 'k8s_scale.py', 'k8s_service.py',
        )
        with TemporaryDirectory() as directory:
            root = Path(directory) / 'collection'
            action = root / 'plugins/action'
            action.mkdir(parents=True)
            (root / 'plugins').chmod(0o755)
            action.chmod(0o755)
            readme = root / 'README.md'
            readme.write_bytes(b'clean README\n')
            readme.chmod(0o644)
            action_target = action / 'k8s_info.py'
            action_target.write_bytes(b'clean action\n')
            action_target.chmod(0o644)
            action_digest = hashlib.sha256(action_target.read_bytes()).hexdigest()
            readme_digest = hashlib.sha256(readme.read_bytes()).hexdigest()
            manifest_entries = [
                {'name': 'plugins', 'ftype': 'dir'},
                {'name': 'plugins/action', 'ftype': 'dir'},
                {'name': 'README.md', 'ftype': 'file', 'chksum_sha256': readme_digest},
                {
                    'name': 'plugins/action/k8s_info.py',
                    'ftype': 'file',
                    'chksum_sha256': action_digest,
                },
            ]
            for name in allowed_links:
                link = action / name
                link.symlink_to('k8s_info.py')
                manifest_entries.append({
                    'name': f'plugins/action/{name}',
                    'ftype': 'file',
                    'chksum_sha256': action_digest,
                })
            files = root / 'FILES.json'
            files.write_text(json.dumps({'files': manifest_entries}) + '\n')
            files.chmod(0o644)
            (root / 'MANIFEST.json').write_text('{}\n')
            (root / 'MANIFEST.json').chmod(0o644)
            harness_path = Path(directory) / 'check-manifest.sh'
            harness_path.write_text(harness)
            harness_path.chmod(0o755)
            clean = subprocess.run(
                [str(harness_path), str(root), str(files)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, clean.returncode, clean.stderr)
            readme.write_bytes(readme.read_bytes() + b'mutated\n')
            mutated = subprocess.run(
                [str(harness_path), str(root), str(files)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, mutated.returncode)

    def test_collection_toolchain_rejects_mutated_new_paths_in_temp_copies(self) -> None:
        source_root = Path('/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core')
        if not source_root.is_dir():
            self.skipTest('pinned kubernetes.core installation is not available')
        paths = (
            ('plugins/action/k8s.py', 'symlink'),
            ('plugins/action/k8s_info.py', 'regular'),
            ('plugins/modules/k8s_info.py', 'regular'),
        )
        for relative, kind in paths:
            with self.subTest(relative=relative), TemporaryDirectory() as directory:
                collection_root = Path(directory) / 'core'
                shutil.copytree(source_root, collection_root, symlinks=True)
                for pycache in collection_root.rglob('__pycache__'):
                    shutil.rmtree(pycache)
                patches = {
                    '_COLLECTION_ROOT': collection_root,
                    '_COLLECTION_MANIFEST_SOURCE': collection_root / 'MANIFEST.json',
                    '_COLLECTION_FILES_SOURCE': collection_root / 'FILES.json',
                    '_K8S_ACTION_SOURCE': collection_root / 'plugins/action/k8s.py',
                    '_K8S_ACTION_TARGET': collection_root / 'plugins/action/k8s_info.py',
                    '_K8S_INFO_MODULE_SOURCE': collection_root / 'plugins/modules/k8s_info.py',
                    '_JSON_PATCH_ACTION_SOURCE': collection_root / 'plugins/action/k8s_json_patch.py',
                    '_JSON_PATCH_ACTION_TARGET': collection_root / 'plugins/action/k8s_info.py',
                    '_JSON_PATCH_MODULE_SOURCE': collection_root / 'plugins/modules/k8s_json_patch.py',
                }
                with mock.patch.multiple(self.plugin, **patches):
                    self.assertTrue(self.plugin._collection_toolchain_valid())
                    victim = collection_root / relative
                    if kind == 'symlink':
                        victim.unlink()
                        victim.write_text('malicious action base\\n')
                    else:
                        victim.write_text('malicious collection file\\n')
                        victim.chmod(0o644)
                    self.assertFalse(self.plugin._collection_toolchain_valid())

    def test_internal_registered_facts_are_all_guarded_before_task_execution(self) -> None:
        tasks = TASKS.read_text()
        initial_guard = tasks.split('- name: Require fixed shared MongoDB NetworkPolicy source closure configuration', 1)[0]
        internal_names = set(re.findall(r'\b(shared_mongodb_networkpolicy_bootstrap_internal_[A-Za-z0-9_]+)', tasks))
        guarded_names = set(re.findall(r'\b(shared_mongodb_networkpolicy_bootstrap_internal_[A-Za-z0-9_]+)', initial_guard))
        self.assertEqual(internal_names, guarded_names)
        for name in internal_names:
            self.assertIn(f'    - {name}', initial_guard)

    def test_collection_exact_tree_rejects_bytecode_native_and_extra_precedence_leaves(self) -> None:
        source_root = Path('/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core')
        if not source_root.is_dir():
            self.skipTest('pinned kubernetes.core installation is not available')
        with TemporaryDirectory() as directory:
            collection_root = Path(directory) / 'core'
            shutil.copytree(source_root, collection_root, symlinks=True)
            for pycache in collection_root.rglob('__pycache__'):
                shutil.rmtree(pycache)
            patches = {
                '_COLLECTION_ROOT': collection_root,
                '_COLLECTION_MANIFEST_SOURCE': collection_root / 'MANIFEST.json',
                '_COLLECTION_FILES_SOURCE': collection_root / 'FILES.json',
                '_K8S_ACTION_SOURCE': collection_root / 'plugins/action/k8s.py',
                '_K8S_ACTION_TARGET': collection_root / 'plugins/action/k8s_info.py',
                '_K8S_INFO_MODULE_SOURCE': collection_root / 'plugins/modules/k8s_info.py',
                '_JSON_PATCH_ACTION_SOURCE': collection_root / 'plugins/action/k8s_json_patch.py',
                '_JSON_PATCH_ACTION_TARGET': collection_root / 'plugins/action/k8s_info.py',
                '_JSON_PATCH_MODULE_SOURCE': collection_root / 'plugins/modules/k8s_json_patch.py',
            }
            with mock.patch.multiple(self.plugin, **patches):
                self.assertTrue(self.plugin._collection_toolchain_valid())
                (collection_root / 'plugins/action/k8s.py').unlink()
                (collection_root / 'plugins/action/k8s.py').write_text('evil action precedence')
                self.assertFalse(self.plugin._collection_toolchain_valid())
        for relative in (
            'plugins/action/k8s_info.py',
            'plugins/modules/k8s_info.py',
            'plugins/module_utils/version.py',
            '__init__.py',
            'plugins/__init__.py',
            'plugins/action/__init__.py',
            'plugins/modules/extra.py',
            'plugins/module_utils/client/extra.py',
            'plugins/action/empty-dir',
            'plugins/modules/empty-dir',
            'plugins/module_utils/k8s/empty-dir',
        ):
            with TemporaryDirectory() as directory:
                collection_root = Path(directory) / 'core'
                shutil.copytree(source_root, collection_root, symlinks=True)
                for pycache in collection_root.rglob('__pycache__'):
                    shutil.rmtree(pycache)
                patches = {
                    '_COLLECTION_ROOT': collection_root,
                    '_COLLECTION_MANIFEST_SOURCE': collection_root / 'MANIFEST.json',
                    '_COLLECTION_FILES_SOURCE': collection_root / 'FILES.json',
                    '_K8S_ACTION_SOURCE': collection_root / 'plugins/action/k8s.py',
                    '_K8S_ACTION_TARGET': collection_root / 'plugins/action/k8s_info.py',
                    '_K8S_INFO_MODULE_SOURCE': collection_root / 'plugins/modules/k8s_info.py',
                    '_JSON_PATCH_ACTION_SOURCE': collection_root / 'plugins/action/k8s_json_patch.py',
                    '_JSON_PATCH_ACTION_TARGET': collection_root / 'plugins/action/k8s_info.py',
                    '_JSON_PATCH_MODULE_SOURCE': collection_root / 'plugins/modules/k8s_json_patch.py',
                }
                with mock.patch.multiple(self.plugin, **patches):
                    self.assertTrue(self.plugin._collection_toolchain_valid())
                    victim = collection_root / relative
                    victim.parent.mkdir(parents=True, exist_ok=True)
                    if victim.relative_to(collection_root).name == 'empty-dir':
                        victim.mkdir()
                    else:
                        if victim.is_symlink():
                            victim.unlink()
                            victim.symlink_to('k8s_info.py')
                        victim.write_bytes(b'evil')
                        victim.chmod(0o644)
                    self.assertFalse(self.plugin._collection_toolchain_valid())
        for relative in (
            '__pycache__/evil.pyc',
            'plugins/action/__pycache__/evil.pyc',
            'plugins/modules/evil.so',
        ):
            with TemporaryDirectory() as directory:
                collection_root = Path(directory) / 'core'
                shutil.copytree(source_root, collection_root, symlinks=True)
                for pycache in collection_root.rglob('__pycache__'):
                    shutil.rmtree(pycache)
                patches = {
                    '_COLLECTION_ROOT': collection_root,
                    '_COLLECTION_MANIFEST_SOURCE': collection_root / 'MANIFEST.json',
                    '_COLLECTION_FILES_SOURCE': collection_root / 'FILES.json',
                    '_K8S_ACTION_SOURCE': collection_root / 'plugins/action/k8s.py',
                    '_K8S_ACTION_TARGET': collection_root / 'plugins/action/k8s_info.py',
                    '_K8S_INFO_MODULE_SOURCE': collection_root / 'plugins/modules/k8s_info.py',
                    '_JSON_PATCH_ACTION_SOURCE': collection_root / 'plugins/action/k8s_json_patch.py',
                    '_JSON_PATCH_ACTION_TARGET': collection_root / 'plugins/action/k8s_info.py',
                    '_JSON_PATCH_MODULE_SOURCE': collection_root / 'plugins/modules/k8s_json_patch.py',
                }
                with mock.patch.multiple(self.plugin, **patches):
                    self.assertTrue(self.plugin._collection_toolchain_valid())
                    victim = collection_root / relative
                    victim.parent.mkdir(parents=True, exist_ok=True)
                    victim.write_bytes(b'evil')
                    self.assertFalse(self.plugin._collection_toolchain_valid())

    def test_collection_package_initializers_execute_before_guard_and_are_rejected(self) -> None:
        source_root = Path('/home/paul/projects/cristexweb/ansible/.ansible/collections/ansible_collections/kubernetes/core')
        source_requirements = Path('/home/paul/projects/cristexweb/ansible/requirements.yml')
        if not source_root.is_dir() or not source_requirements.is_file():
            self.skipTest('pinned kubernetes.core installation is not available')
        for relative, module_name in (
            ('__init__.py', 'ansible_collections.kubernetes.core'),
            ('plugins/__init__.py', 'ansible_collections.kubernetes.core.plugins'),
        ):
            with self.subTest(relative=relative), TemporaryDirectory() as directory:
                root = Path(directory)
                collection_root = root / 'ansible_collections/kubernetes/core'
                shutil.copytree(source_root, collection_root, symlinks=True)
                for pycache in collection_root.rglob('__pycache__'):
                    shutil.rmtree(pycache)
                marker = root / 'executed'
                victim = collection_root / relative
                victim.write_text(
                    'from pathlib import Path\n'
                    f"Path({str(marker)!r}).write_text('executed')\n",
                    encoding='utf-8',
                )
                result = subprocess.run(
                    [
                        sys.executable,
                        '-c',
                        'import importlib, sys; importlib.import_module(sys.argv[1])',
                        module_name,
                    ],
                    cwd=root,
                    env={**os.environ, 'PYTHONPATH': str(root)},
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual('executed', marker.read_text(encoding='utf-8'))
                for pycache in collection_root.rglob('__pycache__'):
                    shutil.rmtree(pycache)
                patches = {
                    '_COLLECTION_ROOT': collection_root,
                    '_COLLECTION_MANIFEST_SOURCE': collection_root / 'MANIFEST.json',
                    '_COLLECTION_FILES_SOURCE': collection_root / 'FILES.json',
                    '_REQUIREMENTS_SOURCE': source_requirements,
                    '_K8S_ACTION_SOURCE': collection_root / 'plugins/action/k8s.py',
                    '_K8S_ACTION_TARGET': collection_root / 'plugins/action/k8s_info.py',
                    '_K8S_INFO_MODULE_SOURCE': collection_root / 'plugins/modules/k8s_info.py',
                    '_JSON_PATCH_ACTION_SOURCE': collection_root / 'plugins/action/k8s_json_patch.py',
                    '_JSON_PATCH_ACTION_TARGET': collection_root / 'plugins/action/k8s_info.py',
                    '_JSON_PATCH_MODULE_SOURCE': collection_root / 'plugins/modules/k8s_json_patch.py',
                }
                with mock.patch.multiple(self.plugin, **patches):
                    self.assertFalse(self.plugin._collection_toolchain_valid())

    def test_isolated_no_user_bytecode_environment_is_required(self) -> None:
        wrapper = WRAPPER.read_text()
        plugin = PLUGIN.read_text()
        self.assertGreaterEqual(wrapper.count('PYTHONDONTWRITEBYTECODE=1'), 2)
        self.assertGreaterEqual(wrapper.count('PYTHONNOUSERSITE=1'), 2)
        self.assertGreaterEqual(wrapper.count('PYTHONPATH='), 2)
        self.assertIn("'PYTHONDONTWRITEBYTECODE': '1'", plugin)
        self.assertIn("'PYTHONNOUSERSITE': '1'", plugin)
        self.assertIn("'PYTHONPATH': ''", plugin)

    def test_complete_module_utils_closure_is_explicitly_hash_bound(self) -> None:
        wrapper = WRAPPER.read_text()
        tree = ast.parse(PLUGIN.read_text())
        assignment = next(
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == '_EXPECTED_COLLECTION_MODULE_UTILS'
                    for target in node.targets)
        )
        closure = ast.literal_eval(assignment.value)
        self.assertEqual(23, len(closure))
        self.assertTrue(all(path.startswith('plugins/module_utils/') for path in closure))
        self.assertTrue(all(re.fullmatch(r'[0-9a-f]{64}', digest) for digest in closure.values()))
        self.assertIn('plugins/module_utils/k8s/client.py', closure)
        self.assertIn('plugins/module_utils/client/discovery.py', closure)
        for path, digest in closure.items():
            self.assertIn(f'{path} {digest}', wrapper)
        self.assertIn('FILES.json', wrapper)
        module_tree = ast.literal_eval(next(
            node.value for node in ast.parse(PLUGIN.read_text()).body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == '_EXPECTED_COLLECTION_MODULES'
                    for target in node.targets)
        ))
        for path, digest in module_tree.items():
            self.assertIn(f'{path} {digest}', wrapper)

    def test_create_response_binds_numeric_uid_and_resource_version(self) -> None:
        module = (ROOT / 'ansible/library/shared_mongodb_networkpolicy_create.py').read_text()
        self.assertIn('created_uid', module)
        self.assertIn('created_resource_version', module)
        self.assertIn('re.fullmatch(r"[0-9]+", metadata.get("resourceVersion", ""))', module)
        self.assertIn('created_resource_version', TASKS.read_text())
        self.assertIn('immediate poststate', TASKS.read_text())
        self.assertIn('final server UID/resourceVersion', TASKS.read_text())

    def test_signal_cleanup_waits_for_child_before_releasing_lock(self) -> None:
        wrapper = WRAPPER.read_text()
        self.assertIn('child_pid=', wrapper)
        self.assertIn("/bin/kill -TERM -- \"-$child_pid\"", wrapper)
        self.assertIn('wait "$child_pid"', wrapper)
        self.assertIn('trap cleanup EXIT', wrapper)
        self.assertIn("trap '' EXIT HUP INT TERM", wrapper)
        self.assertIn('owner_written=1', wrapper)
        self.assertIn('umask 077', wrapper)
        self.assertIn('is_owned_regular_mode', wrapper)
        self.assertIn("[ ! -s \"$lock_file\" ]", wrapper)

        # Exercise the signal/lock ordering with a process-group child; this
        # catches the former bug where EXIT cleanup released the lock while the
        # Ansible child was still alive.
        with TemporaryDirectory() as directory:
            lock = Path(directory) / 'lock'
            marker = Path(directory) / 'child.pid'
            fixture = r'''#!/bin/sh
set -eu
lock=$1
marker=$2
umask 077
mkdir "$lock"
owner_written=1
printf '%s\n' "$$" >"$lock/owner"
child_pid=
forced_cleanup_status=
cleanup() {
  status=$?
  if [ -n "${forced_cleanup_status:-}" ]; then status=$forced_cleanup_status; fi
  trap - EXIT HUP INT TERM
  if [ "$owner_written" = 1 ]; then rm -f "$lock/owner"; fi
  rmdir "$lock"
  exit "$status"
}
terminate_child() {
  signal_status=$1
  trap '' EXIT HUP INT TERM
  if [ -n "${child_pid:-}" ]; then
    kill -TERM -- "-$child_pid" 2>/dev/null || kill -TERM "$child_pid" 2>/dev/null || true
    remaining=5
    while [ "$remaining" -gt 0 ] && kill -0 "$child_pid" 2>/dev/null; do
      sleep 1
      remaining=$((remaining - 1))
    done
    if kill -0 "$child_pid" 2>/dev/null; then
      kill -KILL -- "-$child_pid" 2>/dev/null || kill -KILL "$child_pid" 2>/dev/null || true
    fi
    wait "$child_pid" 2>/dev/null || true
    child_pid=
  fi
  forced_cleanup_status=$signal_status
  cleanup
}
trap cleanup EXIT
pending_signal=
trap 'pending_signal=143' TERM
setsid sleep 30 &
child_pid=$!
printf '%s\n' "$child_pid" >"$marker"
set +e
wait "$child_pid"
status=$?
set -e
if [ -n "$pending_signal" ]; then terminate_child "$pending_signal"; fi
exit "$status"
'''
            fixture_path = Path(directory) / 'fixture.sh'
            fixture_path.write_text(fixture)
            fixture_path.chmod(0o755)
            process = subprocess.Popen([str(fixture_path), str(lock), str(marker)])
            try:
                for _ in range(50):
                    if marker.exists():
                        break
                    __import__('time').sleep(0.02)
                self.assertTrue(marker.exists())
                child_pid = int(marker.read_text().strip())
                process.send_signal(__import__('signal').SIGTERM)
                self.assertEqual(143, process.wait(timeout=10))
                self.assertFalse(lock.exists())
                with self.assertRaises(ProcessLookupError):
                    os.kill(child_pid, 0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

    def test_stale_legacy_lock_is_migrated_only_when_exact_empty_owned_file(self) -> None:
        with TemporaryDirectory() as directory:
            lock = Path(directory) / 'lock'
            lock.touch(mode=0o600)
            lock.chmod(0o600)
            migrate = subprocess.run(
                [
                    'sh', '-c',
                    'set -eu; lock=$1; user=$(id -un); '
                    '[ -f "$lock" ] && [ ! -L "$lock" ] && [ ! -s "$lock" ] && '
                    '[ "$(find "$lock" -prune -type f -user "$user" -perm 600 -print)" = "$lock" ]; '
                    'rm -f -- "$lock"; umask 077; mkdir "$lock"; '
                    '[ "$(find "$lock" -prune -type d -user "$user" -perm 700 -print)" = "$lock" ]; rmdir "$lock"',
                    'stale-lock-test', str(lock),
                ],
                check=False,
            )
            self.assertEqual(0, migrate.returncode)
            symlink = Path(directory) / 'symlink'
            symlink.symlink_to(lock)
            rejected = subprocess.run(
                ['sh', '-c', '[ ! -L "$1" ]', 'symlink-lock-test', str(symlink)],
                check=False,
            )
            self.assertNotEqual(0, rejected.returncode)

    def test_legacy_lock_migration_rejects_an_active_flock_holder(self) -> None:
        with TemporaryDirectory() as directory:
            lock = Path(directory) / 'lock'
            lock.touch(mode=0o600)
            lock.chmod(0o600)
            holder = subprocess.Popen(['/usr/bin/flock', '-n', str(lock), 'sleep', '5'])
            try:
                import time
                for _ in range(50):
                    probe = subprocess.run(
                        [
                            'sh', '-c',
                            'exec 9<> "$1"; /usr/bin/flock -n 9',
                            'active-lock-probe', str(lock),
                        ],
                        check=False,
                    )
                    if probe.returncode != 0:
                        break
                    time.sleep(0.02)
                self.assertNotEqual(0, probe.returncode)
            finally:
                holder.terminate()
                holder.wait(timeout=5)

    def test_absent_target_uses_create_only_module_not_merge_update(self) -> None:
        plugin = PLUGIN.read_text()
        module = ROOT / 'ansible/library/shared_mongodb_networkpolicy_create.py'
        module_text = module.read_text()
        self.assertIn("module_name='shared_mongodb_networkpolicy_create'", plugin)
        self.assertIn('CREATE_ONLY_CONFLICT', module_text)
        self.assertIn('resource.create(', module_text)
        self.assertNotIn("self._task.action = 'kubernetes.core.k8s'", plugin)
        self.assertNotIn('state: absent', module_text)

    def test_selector_overlap_negative_cases_are_fail_closed(self) -> None:
        labels = {
            **self.plugin._MONGODB_POD_LABELS,
            'controller-revision-hash': 'example',
            'statefulset.kubernetes.io/pod-name': 'shared-mongodb-0',
        }
        overlap = self.plugin._selector_can_match_labels
        self.assertTrue(overlap({}, labels))
        self.assertTrue(overlap({'matchExpressions': [{'key': 'app', 'operator': 'Exists'}]}, labels))
        self.assertTrue(overlap({'matchExpressions': [{'key': 'future', 'operator': 'NotIn', 'values': ['x']}]}, labels))
        self.assertTrue(overlap({'matchExpressions': [{'key': 'future', 'operator': 'DoesNotExist'}]}, labels))
        self.assertFalse(overlap({'matchLabels': {'app': 'other'}}, labels))
        self.assertFalse(overlap({'matchExpressions': [{'key': 'app', 'operator': 'In', 'values': ['other']}]}, labels))
        self.assertFalse(overlap({'matchExpressions': [{'key': 'unknown', 'operator': 'Exists'}]}, labels))
        self.assertFalse(overlap({'matchExpressions': [{'key': 'app', 'operator': 'DoesNotExist'}]}, labels))

    def test_action_accepts_exact_role_preflight_binding_with_tagged_booleans(self) -> None:
        """The live role emits strings for templated values under Ansible 2.19."""
        definition = copy.deepcopy(self.by_name['shared-mongodb-networkpolicy-default-deny'])
        pod = {
            'metadata': {
                'name': 'shared-mongodb-0',
                'labels': dict(self.plugin._MONGODB_POD_LABELS),
            },
            'status': {
                'phase': 'Running',
                'conditions': [{'type': 'Ready', 'status': 'True'}],
            },
        }
        token = 'a' * 64
        wrapper_pid = str(os.getpid())
        wrapper_starttime = '12345'
        wrapper_argv_sha256 = 'b' * 64
        binding = {
            'attestation_sha256': hashlib.sha256(token.encode()).hexdigest(),
            'object_count': '2',
            'identity_set_sha256': self.plugin._EXPECTED_IDENTITY_SET_SHA256,
            'prestate_count': '0',
            'initial_prestate_count': '0',
            'networkpolicy_prestate': [],
            'transition_phase': 'initial',
            'mongodb_count': '1',
            'statefulset_count': '1',
            'statefulset_uid': 'statefulset-uid',
            'pod_count': '1',
            'pod_name': 'shared-mongodb-0',
            'pod_phase': 'Running',
            'pod_ready': 'True',
            'pod_terminating': 'False',
            'pod_owner_api_version': 'apps/v1',
            'pod_owner_kind': 'StatefulSet',
            'pod_owner_name': 'shared-mongodb',
            'pod_owner_uid': 'statefulset-uid',
            'pod_owner_controller': 'True',
            'networkpolicy_count': '0',
            'networkpolicy_names': [],
            'client_environment_count': '2',
            'coredns_count': '1',
            'kubeconfig_contract': 'True',
            'namespace_contract': 'True',
            'no_delete_path': 'True',
        }
        action = object.__new__(self.plugin.ActionModule)
        action._task = SimpleNamespace(
            args={
                'state': 'present',
                'definition': definition,
                'kubeconfig': '/etc/rancher/k3s/k3s.yaml',
                'wait': False,
                'wait_timeout': 60,
                'prestate_binding': {},
                'validation_only': False,
            },
            get_path=lambda: str(self.plugin._TASK_SOURCE),
        )
        original_cliargs = self.plugin.context.CLIARGS
        env = {
            'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_ENTRYPOINT': 'v1',
            'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_TOKEN': token,
            'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_ATTESTATION_FILE': '',
            'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_PID': wrapper_pid,
            'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_STARTTIME': wrapper_starttime,
            'CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_ARGV_SHA256': wrapper_argv_sha256,
        }
        with TemporaryDirectory() as directory, mock.patch.dict(os.environ, env, clear=False):
            attestation = Path(directory) / 'attestation'
            attestation.write_text(
                f'{token}:entrypoint:{wrapper_pid}:{wrapper_starttime}:{wrapper_argv_sha256}\n',
                encoding='utf-8',
            )
            attestation.chmod(0o600)
            os.environ['CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_ATTESTATION_FILE'] = str(attestation)
            with mock.patch.object(self.plugin, '_cooperative_lock_valid', return_value=True), \
                mock.patch.object(self.plugin, '_source_closure_valid', return_value=True), \
                mock.patch.object(self.plugin, '_runtime_binding_valid', return_value=True):
                self.plugin.context.CLIARGS = {
                    'check': True,
                    'start_at_task': None,
                    'step': False,
                    'tags': [],
                    'skip_tags': [],
                }
                result = action.run(task_vars={
                    'shared_mongodb_networkpolicy_bootstrap_mode': 'check',
                    'shared_mongodb_networkpolicy_bootstrap_approved': 'true',
                    'shared_mongodb_networkpolicy_bootstrap_state': 'present',
                    'shared_mongodb_networkpolicy_bootstrap_internal_preflight_binding': binding,
                    'shared_mongodb_networkpolicy_bootstrap_internal_all_networkpolicies': {'resources': []},
                    'shared_mongodb_networkpolicy_bootstrap_internal_manifests': copy.deepcopy(self.objects),
                    'shared_mongodb_networkpolicy_bootstrap_internal_pod': {'resources': [pod]},
                })
        self.plugin.context.CLIARGS = original_cliargs
        self.assertFalse(result.get('failed', False), result)
        self.assertTrue(result.get('create'))

    def test_action_guard_rejects_apply_and_task_selection_before_kubernetes(self) -> None:
        context = self.plugin.context
        original = context.CLIARGS
        action = object.__new__(self.plugin.ActionModule)
        action._task = SimpleNamespace(args={}, get_path=lambda: '/not-canonical:1')
        try:
            context.CLIARGS = {
                'check': False,
                'start_at_task': None,
                'step': False,
                'tags': [],
                'skip_tags': [],
            }
            result = action.run(task_vars={})
            self.assertTrue(result['failed'])
            self.assertIn('MODE_GUARD', result['msg'])
            context.CLIARGS = {
                'check': False,
                'start_at_task': 'forged',
                'step': False,
                'tags': [],
                'skip_tags': [],
            }
            result = action.run(task_vars={})
            self.assertTrue(result['failed'])
            self.assertIn('TASK_SELECTION_GUARD', result['msg'])
        finally:
            context.CLIARGS = original

    def test_action_preflight_rejects_foreign_overlap_and_target_drift(self) -> None:
        definitions = copy.deepcopy(self.objects)
        pod = {
            'metadata': {'name': 'shared-mongodb-0', 'labels': self.plugin._MONGODB_POD_LABELS}
        }
        foreign_empty = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'NetworkPolicy',
            'metadata': {'namespace': 'shared-services', 'name': 'foreign-empty'},
            'spec': {'podSelector': {}},
        }
        self.assertIn(
            'foreign NetworkPolicy selector overlaps',
            self.plugin._networkpolicy_preflight_error([foreign_empty], definitions, pod),
        )
        drifted = copy.deepcopy(definitions)
        drifted[0]['spec']['policyTypes'] = ['Ingress']
        drifted[0]['metadata']['name'] = definitions[0]['metadata']['name']
        self.assertIn(
            'target NetworkPolicy drift',
            self.plugin._networkpolicy_preflight_error(drifted, definitions, pod),
        )
        live = copy.deepcopy(definitions)
        for index, policy in enumerate(live):
            policy['metadata']['uid'] = f'uid-{index}'
            policy['metadata']['resourceVersion'] = str(index + 1)
        ledger = [
            {
                'name': policy['metadata']['name'],
                'uid': policy['metadata']['uid'],
                'resource_version': policy['metadata']['resourceVersion'],
            }
            for policy in live
        ]
        self.assertIsNone(self.plugin._networkpolicy_preflight_error(live, definitions, pod, ledger))
        for field, value in (
            ('deletionTimestamp', '2026-08-25T00:00:00Z'),
            ('deletionGracePeriodSeconds', 30),
            ('deletionGracePeriod', 30),
            ('finalizers', []),
            ('ownerReferences', []),
        ):
            terminating = copy.deepcopy(live)
            terminating[0]['metadata'][field] = value
            self.assertIn(
                'target NetworkPolicy drift',
                self.plugin._networkpolicy_preflight_error(terminating, definitions, pod, ledger),
            )
        replacement = copy.deepcopy(live)
        replacement[0]['metadata']['uid'] = 'replacement-uid'
        self.assertIn(
            'target NetworkPolicy replacement',
            self.plugin._networkpolicy_preflight_error(replacement, definitions, pod, ledger),
        )

    def test_guarded_entrypoint_has_separate_check_and_apply_modes(self) -> None:
        wrapper = WRAPPER.read_text()
        self.assertIn("usage: ansible/bin/bootstrap-shared-mongodb-networkpolicy check|apply", wrapper)
        self.assertIn('--check', wrapper)
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_APPLY_APPROVED', wrapper)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap_mode', wrapper)
        self.assertNotIn('mongodb_bootstrap', wrapper)
        self.assertNotIn('bootstrap-mongodb', wrapper)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap_approved', wrapper)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap_mode in [\'check\', \'apply\']', TASKS.read_text())
        self.assertIn('shared_mongodb_networkpolicy_bootstrap', TASKS.read_text())
        self.assertIn('shared_mongodb_networkpolicy_guarded_k8s:', TASKS.read_text())
        self.assertIn('source-only', TASKS.read_text())
        self.assertIn("mode not in {'check', 'apply'}", PLUGIN.read_text())
        self.assertIn('APPROVAL_GUARD', PLUGIN.read_text())
        self.assertIn('MUTATION_ARGUMENT_GUARD', PLUGIN.read_text())
        self.assertIn('TASK_SELECTION_GUARD', PLUGIN.read_text())
        self.assertIn('Enumerate every shared-services NetworkPolicy', TASKS.read_text())
        self.assertIn("status.phase == 'Running'", TASKS.read_text())
        self.assertIn("status.currentMongoDBMembers | int == 1", TASKS.read_text())
        self.assertIn("name == 'shared-mongodb-0'", TASKS.read_text())
        self.assertIn('Query the exact live MongoDB StatefulSet', TASKS.read_text())
        self.assertIn("status.readyReplicas | int == 1", TASKS.read_text())
        self.assertIn("ownerReferences[0].uid ==", TASKS.read_text())
        self.assertIn("shared_mongodb_networkpolicy_bootstrap_internal_statefulset.resources[0].metadata.uid", TASKS.read_text())
        self.assertIn("map(attribute='resources') | map('length') | sum", TASKS.read_text())
        self.assertIn("_safe_int(binding.get('prestate_count'))", PLUGIN.read_text())
        self.assertIn("initial_prestate_count", PLUGIN.read_text())
        self.assertIn("transition_phase", PLUGIN.read_text())
        self.assertIn("_networkpolicy_cas_patch", PLUGIN.read_text())
        self.assertIn("kubernetes.core.k8s_json_patch", PLUGIN.read_text())
        self.assertIn("'path': '/metadata/resourceVersion'", PLUGIN.read_text())
        self.assertIn('validation_only', PLUGIN.read_text())
        self.assertIn('Enumerate every NetworkPolicy after the complete closure mutation', TASKS.read_text())
        self.assertIn('Reconcile the exact default-deny policy before any allow policy', TASKS.read_text())
        self.assertIn("lock_file='/tmp/cristexweb-shared-mongodb-networkpolicy.lock'", WRAPPER.read_text())
        self.assertIn('/bin/mkdir "$lock_file"', WRAPPER.read_text())
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_LOCK_FILE=$lock_file', WRAPPER.read_text())
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_PID=$wrapper_pid', WRAPPER.read_text())
        self.assertIn('printf \'%s:%s:%s:%s\\n\' "$attestation_token" "$wrapper_pid" "$wrapper_starttime" "$wrapper_argv_sha256"', WRAPPER.read_text())
        self.assertIn("printf '%s\\0%s\\0%s' '/bin/sh' \"$script_path\" \"$mode\"", WRAPPER.read_text())
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_STARTTIME=$wrapper_starttime', WRAPPER.read_text())
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_WRAPPER_ARGV_SHA256=$wrapper_argv_sha256', WRAPPER.read_text())
        self.assertIn('_wrapper_process_valid', PLUGIN.read_text())
        self.assertIn('_proc_cmdline', PLUGIN.read_text())
        self.assertIn('_cooperative_lock_valid', PLUGIN.read_text())
        self.assertIn('_source_closure_valid', PLUGIN.read_text())
        self.assertIn('_runtime_binding_valid', PLUGIN.read_text())
        self.assertIn('managedFields', TASKS.read_text())
        self.assertIn('difference([\'ansible\'])', TASKS.read_text())
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_DEFAULTS_SHA256', TASKS.read_text())
        self.assertIn('CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_CONTROLLER_SHA256', TASKS.read_text())
        self.assertIn('is_owned_regular_mode "$controller" 755', WRAPPER.read_text())
        self.assertIn('_EXPECTED_CONTROLLER_MODE = 0o755', PLUGIN.read_text())
        self.assertIn('shared_mongodb_networkpolicy_create.py', WRAPPER.read_text())
        self.assertIn('resource.create(', (ROOT / 'ansible/library/shared_mongodb_networkpolicy_create.py').read_text())
        self.assertIn('/usr/bin/flock -n 9', WRAPPER.read_text())
        self.assertIn('legacy_lock_inode', WRAPPER.read_text())
        self.assertIn("binding.get('pod_owner_uid') == binding.get('statefulset_uid')", PLUGIN.read_text())
        self.assertIn('k8s-app=kube-dns', TASKS.read_text())
        self.assertIn('root:k3s-admin', TASKS.read_text())
        self.assertIn("spec.hostNetwork | default(false) | bool == false", TASKS.read_text())
        self.assertIn('shared_mongodb_networkpolicy_bootstrap_internal_all_networkpolicies', TASKS.read_text())
        self.assertIn("'deletionTimestamp' not in item.resources[0].metadata", TASKS.read_text())
        self.assertIn("'ownerReferences' not in item.resources[0].metadata", TASKS.read_text())
        self.assertIn('networkpolicy_prestate', PLUGIN.read_text())
        self.assertIn("initial_prestate_count in (0, 1, 2)", PLUGIN.read_text())
        self.assertIn("collection_files_sha256_expected", WRAPPER.read_text())
        self.assertIn("_EXPECTED_COLLECTION_MODULE_UTILS", PLUGIN.read_text())
        self.assertIn("_EXPECTED_COLLECTION_FILES_SHA256", PLUGIN.read_text())
        self.assertIn("/usr/bin/flock -n 9", WRAPPER.read_text())
        self.assertIn("legacy_lock_inode", WRAPPER.read_text())
        self.assertIn("trap cleanup EXIT", WRAPPER.read_text())
        self.assertIn("terminate_process_tree", WRAPPER.read_text())
        runbook = (ROOT / 'runbooks/shared-mongodb-networkpolicy-bootstrap.md').read_text()
        self.assertIn('cooperative lock', runbook.lower())
        self.assertIn('historical and predates the', runbook)
        self.assertIn('lifecycle/pre-state hardening', runbook)
        self.assertIn('fresh check is required', runbook)
        self.assertIn('Apply remains a', runbook)
        self.assertIn('no Kubernetes mutation', runbook)
        self.assertIn('shared_mongodb_networkpolicy_bootstrap', PLAYBOOK.read_text())

    def test_no_secret_workload_or_operator_exception_source(self) -> None:
        source = '\n'.join(path.read_text() for path in COMPONENT.rglob('*') if path.is_file())
        for forbidden in ('kind: Secret', 'kind: Deployment', 'kind: StatefulSet', 'kind: Service', 'mongodb-system'):
            self.assertNotIn(forbidden, source)
        self.assertNotIn('cristex.io/database-client', source)
        self.assertNotIn('mongodb_bootstrap', TASKS.read_text() + DEFAULTS.read_text() + PLUGIN.read_text())

    def test_wrapper_shell_syntax_and_apply_approval_gate(self) -> None:
        result = subprocess.run(['sh', '-n', str(WRAPPER)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        result = subprocess.run([str(WRAPPER), 'apply'], env={}, capture_output=True, text=True)
        self.assertEqual(77, result.returncode, result.stdout + result.stderr)
        self.assertIn('APPLY_APPROVED=v1', result.stderr)


if __name__ == '__main__':
    unittest.main()
