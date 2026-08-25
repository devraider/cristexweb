from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "ansible/files/backup/reactive-resume-dev-backup"
RESTORE = ROOT / "ansible/files/backup/restore-reactive-resume-dev-backup-rehearsal"
SERVICE = ROOT / "ansible/files/backup/cristexweb-reactive-resume-dev-backup.service"
TIMER = ROOT / "ansible/files/backup/cristexweb-reactive-resume-dev-backup.timer"
NETWORK_POLICY = ROOT / "ansible/files/backup/reactive-resume-dev-backup-networkpolicy.yaml"
PLAYBOOK = ROOT / "ansible/playbooks/configure_reactive_resume_dev_backup.yml"
WRAPPER = ROOT / "ansible/bin/configure-reactive-resume-dev-backup"
ENTRYPOINT_GUARD = ROOT / "ansible/plugins/action/reactive_resume_dev_backup_entrypoint_guarded.py"
STRATEGY_GUARD = ROOT / "ansible/plugins/strategy/reactive_resume_dev_backup_guarded_linear.py"
ANSIBLE_CONFIG = ROOT / "ansible/ansible.cfg"
RUNBOOK = ROOT / "runbooks/reactive-resume-dev-backup.md"


class ReactiveResumeDevBackupContractTests(unittest.TestCase):
    def test_object_bytes_are_streamed_to_host_before_host_digest_validation(self):
        source = BACKUP.read_text()
        export = source.index('>"$work/object-storage.tar.gz" || fail object_archive_export')
        extract = source.index('ARCHIVE="$work/object-storage.tar.gz"')
        validate = source.index('OBJECT_ROOT="$work/object-export/objects"')
        self.assertLess(export, extract)
        self.assertLess(extract, validate)
        self.assertIn('assert member.isdir() or member.isfile()', source)
        self.assertIn('os.O_NOFOLLOW', source)
        self.assertNotIn('/usr/bin/tar --extract', source)
        self.assertIn('os.environ["OBJECT_ROOT"]', source)
        self.assertNotIn('os.path.join("/work/objects", key)', source)
        self.assertIn('member.size == expected[key]', source)
        self.assertIn('member.linkname == "" and not member.pax_headers', source)
        self.assertIn('not getattr(member, "sparse", None)', source)
        self.assertIn('member.uid == 1000 and member.gid == 1000', source)
        self.assertIn('member.mode in ((0o755, 0o2755) if member.isdir() else (0o644,))', source)
        self.assertIn('member_limit = len(expected) + len(allowed_directories)', source)
        self.assertIn('assert len(members) <= member_limit', source)
        self.assertIn('directories == allowed_directories', source)
        self.assertLess(source.index('directories == allowed_directories'), source.index('source = archive.extractfile(member)'))

    def test_restore_rejects_archive_links_and_consumes_one_use_attestation(self):
        source = RESTORE.read_text()
        self.assertIn('assert member.isdir() or member.isfile()', source)
        self.assertIn('os.O_NOFOLLOW', source)
        self.assertIn('not os.path.lexists(target)', source)
        self.assertIn('os.O_NOFOLLOW | os.O_NONBLOCK', source)
        self.assertIn('os.unlink(path)', source)
        self.assertIn('current.st_ino == opened.st_ino', source)
        self.assertIn('approval_attestation_consume', source)
        self.assertIn('object-storage-validated.tar.gz', source)
        self.assertIn('/usr/bin/rm -f -- "$work/object-storage.tar.gz"', source)
        self.assertNotIn('<"$work/object-storage.tar.gz" || fail object_restore_extract', source)
        self.assertIn('member.size == expected[key]', source)
        self.assertIn('member.linkname == "" and not member.pax_headers', source)
        self.assertIn('not getattr(member, "sparse", None)', source)
        self.assertIn('member.uid == 1000 and member.gid == 1000', source)
        self.assertIn('member.mode in ((0o755, 0o2755) if member.isdir() else (0o644,))', source)
        self.assertIn('member_limit = len(expected) + len(allowed_directories)', source)
        self.assertIn('assert len(members) <= member_limit', source)
        self.assertIn('directories == allowed_directories', source)
        self.assertLess(source.index('directories == allowed_directories'), source.index('source = archive.extractfile(member)'))
        archive_validation = source.index('ARCHIVE="$work/object-storage.tar.gz" OBJECT_VERIFY=')
        control_validation = source.index('not any(char in key for char in ("\\t", "\\r", "\\n", "\\x00"))', archive_validation)
        archive_write = source.index('source = archive.extractfile(member)', archive_validation)
        self.assertLess(control_validation, archive_write)

    def test_pg_table_count_excludes_table_data_and_attach_toc_entries(self):
        for source in (BACKUP.read_text(), RESTORE.read_text()):
            self.assertIn('TABLE\\s+(?!DATA\\s|ATTACH\\s)', source)
            self.assertNotIn('if " TABLE " in (" " + line + " ")', source)

    def test_restore_validates_manifest_keys_before_filesystem_reads(self):
        source = RESTORE.read_text()
        validation = source.index('allowed_prefixes =')
        first_read = source.index('os.path.isfile(path)', validation)
        self.assertLess(validation, first_read)
        for value in (
            '"uploads/user-pictures/", "pictures/", "uploads/user-agent/"',
            'not key.startswith("/")',
            '".." not in key.split("/")',
            '"\\\\" not in key',
            '("\\t", "\\r", "\\n", "\\x00")',
            'os.path.commonpath((root, os.path.abspath(os.path.join(root, key)))) == root',
        ):
            self.assertIn(value, source)

    def test_wrapper_and_playbook_bind_execution_source_closure(self):
        for value in (
            "reactive_resume_dev_backup_wrapper_sha256=",
            "canonical_sha256()",
            "refusing backup wrapper source drift",
            "refusing backup playbook source drift",
            "verify_source()",
            "ansible/files/backup/restore-reactive-resume-dev-backup-rehearsal",
        ):
            self.assertIn(value, WRAPPER.read_text())
        for value in (
            "ansible/bin/configure-reactive-resume-dev-backup",
            "reactive_resume_dev_backup_wrapper_sha256:",
            "reactive_resume_dev_backup_playbook_sha256:",
            "hash-bound backup source closure",
            "wrapper-created single-run attestation",
            "Reject externally supplied backup internal variables",
            "INTERNAL_VARIABLE_GUARD: refusing externally supplied backup internal variable",
            "reactive_resume_dev_backup_internal_preflight_complete",
            "Mark the complete guarded backup preflight",
            "Execute backup operations only after the complete guarded preflight",
            "Execute backup post-checks only after the complete guarded preflight",
            "reactive_resume_dev_backup_internal_preflight_complete | default(false) | bool",
        ):
            self.assertIn(value, PLAYBOOK.read_text())
        self.assertIn("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT_TOKEN", WRAPPER.read_text())
        self.assertIn("CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT_ATTESTATION_FILE", WRAPPER.read_text())
        self.assertIn('lambda match: match.group(1) + ("0" * 64)', WRAPPER.read_text())
        guard = ENTRYPOINT_GUARD.read_text()
        for value in (
            'context.CLIARGS.get("start_at_task")',
            'context.CLIARGS.get("step")',
            'TASK_SELECTION_GUARD',
            '_valid_source_states(source_states)',
            '_resolved_source_item(expected)',
            '_EXPECTED_SOURCE_RESULTS',
            '_EXPECTED_BINDING',
            '_EXPECTED_TASK_SOURCE',
            'source_contract_sha256',
            'reactive_resume_dev_backup_internal_preflight_complete',
        ):
            self.assertIn(value, guard)

    def test_playbook_preflight_binding_matches_action_contract(self):
        spec = importlib.util.spec_from_file_location("rr_backup_binding", ENTRYPOINT_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        play = yaml.safe_load(PLAYBOOK.read_text())[0]
        binding_tasks = [
            task
            for task in play["pre_tasks"]
            if task.get("name") == "Bind the canonical guarded backup preflight"
        ]
        self.assertEqual(1, len(binding_tasks))
        binding = binding_tasks[0]["ansible.builtin.set_fact"]
        self.assertEqual(
            module._EXPECTED_BINDING,
            binding["reactive_resume_dev_backup_internal_preflight_binding"],
        )

    def test_action_binds_canonical_playbook_content(self):
        spec = importlib.util.spec_from_file_location("rr_backup_playbook", ENTRYPOINT_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            module._PLAYBOOK_CANONICAL_SHA256,
            module._canonical_playbook_sha256(),
        )
        drifted = PLAYBOOK.read_text().replace(
            "reactive_resume_dev_backup_approved | bool",
            "not (reactive_resume_dev_backup_approved | bool)",
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / PLAYBOOK.name
            candidate.write_text(drifted)
            with mock.patch.object(module, "_PLAYBOOK_SOURCE", candidate):
                self.assertNotEqual(
                    module._PLAYBOOK_CANONICAL_SHA256,
                    module._canonical_playbook_sha256(),
                )

    def test_strategy_guard_rejects_start_at_task_before_iteration(self):
        spec = importlib.util.spec_from_file_location("rr_backup_strategy", STRATEGY_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        strategy = module.StrategyModule.__new__(module.StrategyModule)
        with mock.patch.object(module.context, "CLIARGS", {"start_at_task": "mutation"}):
            with self.assertRaisesRegex(Exception, "TASK_SELECTION_GUARD"):
                strategy.run(None, None)
        empty_selection = {
            "start_at_task": "",
            "step": False,
            "tags": [],
            "skip_tags": [],
        }
        with mock.patch.object(module.context, "CLIARGS", empty_selection):
            for argv in (
                ["ansible-playbook", "--start-at-task="],
                ["ansible-playbook", "--step="],
                ["ansible-playbook", "-t", "all"],
                ["ansible-playbook", "-t=all"],
                ["ansible-playbook", "-tall"],
                ["ansible-playbook", "--ta", "all"],
                ["ansible-playbook", "--ta=all"],
                ["ansible-playbook", "--tag", "all"],
                ["ansible-playbook", "--tag=all"],
            ):
                with self.subTest(argv=argv):
                    with mock.patch.object(module.sys, "argv", argv):
                        with self.assertRaisesRegex(Exception, "TASK_SELECTION_GUARD"):
                            strategy.run(None, None)

    def test_action_guard_rejects_empty_and_short_selection_controls(self):
        spec = importlib.util.spec_from_file_location("rr_backup_action", ENTRYPOINT_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        action = module.ActionModule.__new__(module.ActionModule)
        action._task = SimpleNamespace(
            action=module._EXPECTED_TASK_ACTION,
            name=module._EXPECTED_TASK_NAME,
            args={},
            get_path=lambda: f"{module._EXPECTED_TASK_SOURCE}:123",
        )
        cliargs = {"start_at_task": "", "step": False, "tags": [], "skip_tags": []}
        with mock.patch.object(module.ActionBase, "run", return_value={}):
            with mock.patch.object(
                module.context,
                "CLIARGS",
                {"start_at_task": None, "step": "", "tags": [], "skip_tags": []},
            ):
                with mock.patch.object(module.sys, "argv", ["ansible-playbook"]):
                    result = action.run(task_vars={})
                    self.assertTrue(result["failed"])
                    self.assertIn("TASK_SELECTION_GUARD", result["msg"])
        with mock.patch.object(module.ActionBase, "run", return_value={}):
            with mock.patch.object(module.context, "CLIARGS", cliargs):
                for argv in (
                    ["ansible-playbook"],
                    ["ansible-playbook", "-t", "all"],
                    ["ansible-playbook", "-t=all"],
                    ["ansible-playbook", "--step="],
                    ["ansible-playbook", "--ta", "all"],
                    ["ansible-playbook", "--tag=all"],
                ):
                    with self.subTest(argv=argv):
                        with mock.patch.object(module.sys, "argv", argv):
                            result = action.run(task_vars={})
                            self.assertTrue(result["failed"])
                            self.assertIn("TASK_SELECTION_GUARD", result["msg"])

    def test_action_guard_requires_canonical_task_binding_and_source_results(self):
        spec = importlib.util.spec_from_file_location("rr_backup_action_binding", ENTRYPOINT_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        token = "a" * 64
        source_results = [
            {
                "changed": False,
                "failed": False,
                "unreachable": False,
                "skipped": False,
                "ansible_loop_var": "item",
                "item": module._resolved_source_item(expected),
                "stat": {
                    "exists": True,
                    "isreg": True,
                    "islnk": False,
                    "pw_name": "paul",
                    "gr_name": "paul",
                    "mode": expected["mode"],
                    "checksum": module._resolved_source_item(expected)["sha256"],
                },
            }
            for expected in module._EXPECTED_SOURCE_RESULTS
        ]
        task_vars = {
            module._EXPECTED_SOURCE_REGISTER: {
                "changed": False,
                "failed": False,
                "results": source_results,
            },
            "reactive_resume_dev_backup_internal_preflight_binding": dict(module._EXPECTED_BINDING),
        }
        with tempfile.NamedTemporaryFile(mode="w") as attestation:
            attestation.write(f"{token}:entrypoint\n")
            attestation.flush()
            action = module.ActionModule.__new__(module.ActionModule)
            action._task = SimpleNamespace(
                action=module._EXPECTED_TASK_ACTION,
                name=module._EXPECTED_TASK_NAME,
                args={},
                get_path=lambda: f"{module._EXPECTED_TASK_SOURCE}:123",
            )
            with mock.patch.object(module.ActionBase, "run", return_value={}):
                with mock.patch.dict(
                    os.environ,
                    {
                        "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT_TOKEN": token,
                        "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT_ATTESTATION_FILE": attestation.name,
                    },
                    clear=False,
                ):
                    result = action.run(task_vars=task_vars)
                    self.assertFalse(result.get("failed"), result)
                    self.assertTrue(result["ansible_facts"]["reactive_resume_dev_backup_internal_preflight_complete"])
                    for mutation in (
                        lambda: source_results[0]["item"].update(path="forged"),
                        lambda: source_results.pop(),
                        lambda: source_results[0]["stat"].pop("checksum"),
                        lambda: task_vars["reactive_resume_dev_backup_internal_preflight_binding"].update(task_name="forged"),
                    ):
                        source_results = [dict(item) for item in source_results]
                        task_vars[module._EXPECTED_SOURCE_REGISTER] = {
                            "changed": False,
                            "failed": False,
                            "results": source_results,
                        }
                        mutation()
                        rejected = action.run(task_vars=task_vars)
                        self.assertTrue(rejected.get("failed"), rejected)
                        source_results = [
                            {
                                "changed": False,
                                "failed": False,
                                "unreachable": False,
                                "skipped": False,
                                "ansible_loop_var": "item",
                                "item": module._resolved_source_item(expected),
                                "stat": {
                                    "exists": True,
                                    "isreg": True,
                                    "islnk": False,
                                    "pw_name": "paul",
                                    "gr_name": "paul",
                                    "mode": expected["mode"],
                                    "checksum": module._resolved_source_item(expected)["sha256"],
                                },
                            }
                            for expected in module._EXPECTED_SOURCE_RESULTS
                        ]
                        task_vars[module._EXPECTED_SOURCE_REGISTER] = {
                            "changed": False,
                            "failed": False,
                            "results": source_results,
                        }
                        task_vars["reactive_resume_dev_backup_internal_preflight_binding"] = dict(module._EXPECTED_BINDING)

    def test_action_guard_rejects_direct_canonical_action_without_preflight(self):
        spec = importlib.util.spec_from_file_location("rr_backup_action_direct", ENTRYPOINT_GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        token = "b" * 64
        action = module.ActionModule.__new__(module.ActionModule)
        action._task = SimpleNamespace(
            action=module._EXPECTED_TASK_ACTION,
            name=module._EXPECTED_TASK_NAME,
            args={},
            get_path=lambda: f"{module._EXPECTED_TASK_SOURCE}:123",
        )
        with tempfile.NamedTemporaryFile(mode="w") as attestation:
            attestation.write(f"{token}:entrypoint\n")
            attestation.flush()
            with mock.patch.object(module.ActionBase, "run", return_value={}):
                with mock.patch.object(
                    module.context,
                    "CLIARGS",
                    {"start_at_task": None, "step": False, "tags": [], "skip_tags": []},
                ):
                    with mock.patch.dict(
                        os.environ,
                        {
                            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT_TOKEN": token,
                            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT_ATTESTATION_FILE": attestation.name,
                        },
                        clear=False,
                    ):
                        result = action.run(task_vars={})
        self.assertTrue(result.get("failed"), result)
        self.assertIn("ENTRYPOINT_GUARD", result.get("msg", ""))

    def test_wrapper_playbook_and_source_hash_pins_are_current(self):
        wrapper = WRAPPER.read_text()
        wrapper_declared = re.search(
            r"^reactive_resume_dev_backup_wrapper_sha256='([0-9a-f]{64})'$",
            wrapper,
            re.MULTILINE,
        ).group(1)
        wrapper_canonical = re.sub(
            r"(?m)^reactive_resume_dev_backup_wrapper_sha256='[0-9a-f]{64}'$",
            "reactive_resume_dev_backup_wrapper_sha256='" + ("0" * 64) + "'",
            wrapper,
        )
        self.assertEqual(wrapper_declared, hashlib.sha256(wrapper_canonical.encode()).hexdigest())

        playbook = PLAYBOOK.read_text()
        playbook_declared = re.search(
            r"^    reactive_resume_dev_backup_playbook_sha256: ([0-9a-f]{64})$",
            playbook,
            re.MULTILINE,
        ).group(1)
        playbook_canonical = re.sub(
            r"(?m)^(    reactive_resume_dev_backup_playbook_sha256: )[0-9a-f]{64}$",
            lambda match: match.group(1) + ("0" * 64),
            playbook,
        )
        self.assertEqual(playbook_declared, hashlib.sha256(playbook_canonical.encode()).hexdigest())
        self.assertIn(f"reactive_resume_dev_backup_wrapper_sha256: {wrapper_declared}", playbook)
        self.assertIn(f"sha256: {hashlib.sha256(WRAPPER.read_bytes()).hexdigest()}", playbook)
        guard_digest = hashlib.sha256(ENTRYPOINT_GUARD.read_bytes()).hexdigest()
        self.assertIn(guard_digest, wrapper)
        self.assertIn(f"sha256: {guard_digest}", playbook)
        for source in (STRATEGY_GUARD, ANSIBLE_CONFIG):
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertIn(digest, wrapper)
            self.assertIn(f"sha256: {digest}", playbook)
        strategy = STRATEGY_GUARD.read_text()
        self.assertIn('context.CLIARGS.get("start_at_task")', strategy)
        self.assertIn('TASK_SELECTION_GUARD', strategy)
        self.assertIn('strategy: reactive_resume_dev_backup_guarded_linear', playbook)
        for source in (BACKUP, RESTORE):
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertIn(digest, wrapper)
            self.assertIn(f"sha256: {digest}", playbook)

    @classmethod
    def setUpClass(cls) -> None:
        cls.backup = BACKUP.read_text()
        cls.restore = RESTORE.read_text()
        cls.service = SERVICE.read_text()
        cls.timer = TIMER.read_text()
        cls.playbook_text = PLAYBOOK.read_text()
        cls.playbook = yaml.safe_load(cls.playbook_text)[0]
        cls.wrapper = WRAPPER.read_text()
        cls.runbook = RUNBOOK.read_text()

    def test_scripts_are_shell_valid_executable_and_source_only(self) -> None:
        for path in (BACKUP, RESTORE, WRAPPER):
            subprocess.run(["sh", "-n", str(path)], check=True)
            self.assertEqual(0o755, stat.S_IMODE(path.stat().st_mode), path)
        for path in (SERVICE, TIMER, NETWORK_POLICY, PLAYBOOK, RUNBOOK):
            self.assertTrue(path.is_file(), path)
        combined = "\n".join((self.backup, self.restore, self.service, self.timer, NETWORK_POLICY.read_text(), self.playbook_text))
        self.assertNotIn("AGE-SECRET-KEY-", combined)
        self.assertNotRegex(combined, r"(?im)^\s*(?:password|clientsecret|token)\s*[:=]\s*[^$<\n]")

    def test_staging_capacity_is_fail_closed_and_plaintext_stays_ephemeral(self) -> None:
        for text in (self.backup, self.restore):
            for value in (
                "shm_capacity_preflight",
                "os.statvfs(path)",
                "f_bavail * stat.f_frsize",
                "shm_reserve_bytes=268435456",
                "shm_min_free_bytes=67108864",
                "fail shm_capacity",
                "mktemp -d \"$shm_path/",
            ):
                self.assertIn(value, text, value)
        self.assertIn('>"$work/reactive-resume-dev.dump"', self.backup)
        self.assertNotIn('>"$run_directory/reactive-resume-dev.dump"', self.backup)
        self.assertIn("postgres_source_bytes", self.backup)
        self.assertIn("object_source_bytes", self.backup)
        self.assertIn("rclone --config \"$rclone_config\" size --json", self.restore)
        self.assertIn("object_source_bytes", self.restore)
        self.assertIn("shm_capacity_preflight 1 \"$object_source_bytes\"", self.restore)

    def test_nonempty_object_and_timing_acceptance_contract(self) -> None:
        for value in (
            "object_storage_empty",
            '[ "$object_count" -gt 0 ] && [ "$total_object_bytes" -gt 0 ]',
            "backup_duration_seconds=",
            '"backup_duration_seconds": int(duration)',
            '"created_at_utc": run_id',
            '"completed_at_utc": completed',
            '"logical_entry_count": int(logical_entries)',
            '"logical_table_count": int(logical_tables)',
            '"logical_archive_bytes": int(logical_bytes)',
            'md5 = hashes.get("md5")',
            'assert md5_digest.hexdigest() == md5',
            '"sha256": digest.hexdigest()',
            "umask 022",
            "actual == seen",
            "pg_restore --list",
            "pg_logical_content",
            "clock_skew",
        ):
            self.assertIn(value, self.backup, value)
        for value in (
            "declared_rpo_seconds=86400",
            "declared_rto_seconds=14400",
            "completed_at_utc",
            "completion_timestamp",
            "now < source",
            "backup_duration_seconds",
            "restore_duration_seconds",
            "expected_pg_logical_bytes",
            "PG_EXPECTED_BYTES",
            "assert total <= expected",
            "assert total == expected",
            "rpo_seconds",
            "object_storage_empty",
            "restored_object_empty",
            "rpo_exceeded",
            "rto_exceeded",
            'run["created_at_utc"] == os.environ["RUN_ID"]',
            'run["object_storage"]["object_count"] > 0',
            'run["object_storage"]["total_object_bytes"] > 0',
            'run["database"]["bytes"] == pg["archive_bytes"]',
            'run["object_storage"]["bytes"] == obj["archive_bytes"]',
        ):
            self.assertIn(value, self.restore, value)
        self.assertIn(
            "backup_completed_epoch=[0-9]+ backup_duration_seconds=[0-9]+ restore_duration_seconds=[0-9]+ rto_seconds=[0-9]+ rpo_seconds=[0-9]+",
            self.playbook_text,
        )
        self.assertIn("object_count=[1-9][0-9]* object_bytes=[1-9][0-9]*", self.playbook_text)
        self.assertIn("--kill-after=30s", self.playbook_text)
        self.assertIn('reactive_resume_dev_backup_restore_timeout_seconds: 14400', self.playbook_text)
        self.assertIn("source_contract_sha256 == reactive_resume_dev_backup_source_contract_sha256", self.playbook_text)
        self.assertIn("wrapper_sha256 == reactive_resume_dev_backup_wrapper_sha256", self.playbook_text)
        self.assertIn("playbook_sha256 == reactive_resume_dev_backup_playbook_sha256", self.playbook_text)

    def test_combined_run_id_and_exact_sources(self) -> None:
        for value in (
            "database=reactive_resume_dev_successor",
            "object_bucket=reactive-resume-dev",
            "archive_root=/var/lib/cristexweb-backup/reactive-resume/dev",
            "remote_root=drive:cristexweb-recovery/reactive-resume/dev",
            "run_id=$timestamp",
            "pod_run_id=",
            "run-manifest.json",
            "postgresql.manifest.json",
            "object-storage.manifest.json",
            "source_cluster",
        ):
            self.assertIn(value, self.backup, value)
        self.assertIn("run_id=$selected", self.restore)
        self.assertIn("pod_run_id=", self.restore)
        for text in (self.backup, self.restore):
            self.assertIn("/usr/bin/tr '[:upper:]' '[:lower:]'", text)
        self.assertIn("run[\"run_id\"] == os.environ[\"RUN_ID\"]", self.restore)
        self.assertIn("reactive_resume_dev_successor", self.restore)
        self.assertIn("reactive-resume-dev", self.restore)

    def test_immutable_drive_readback_and_retention(self) -> None:
        for text in (self.backup, self.restore):
            self.assertIn("drive:cristexweb-recovery/reactive-resume/dev", text)
            self.assertIn("copyto --immutable", text) if text is self.backup else None
            self.assertNotRegex(text, r"rclone[^\n]*(?:sync|move|purge|delete)")
        for value in (
            "copyto --immutable",
            "cmp -s",
            "-mtime +14",
            "-mindepth 1 -maxdepth 1 -type d",
            "postgresql.dump.gz.age",
            "object-storage.tar.gz.age",
            "postgresql.dump.gz.age.sha256",
            "object-storage.tar.gz.age.sha256",
        ):
            self.assertIn(value, self.backup, value)
        self.assertIn("sha256sum -c", self.restore)
        self.assertIn('sha256sum "$work/postgresql.dump.gz.age"', self.restore)
        self.assertIn('sha256sum "$work/object-storage.tar.gz.age"', self.restore)
        self.assertIn('= "$pg_actual_sha256  postgresql.dump.gz.age"', self.restore)
        self.assertIn('= "$object_actual_sha256  object-storage.tar.gz.age"', self.restore)

    def test_postgresql_is_logical_only_and_no_raw_pv_copy(self) -> None:
        for value in (
            "pg_dump",
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "reactive_resume_dev_successor",
            "shared-postgresql",
            "reactive-resume-dev.dump",
            "primary_suffix=${primary#shared-postgresql-}",
            "*[!0-9]*) fail postgresql_primary_contract",
            "shared-postgresql:primary:true",
        ):
            self.assertIn(value, self.backup, value)
        combined = self.backup + "\n" + self.restore
        for forbidden in ("PersistentVolumeClaim", "rclone sync", "kubectl cp .*data", "shared-postgresql-reactive-resume"):
            self.assertNotIn(forbidden, combined, forbidden)
        self.assertIn("emptyDir", self.restore)
        for stage in (
            "remote_download",
            "postgresql_checksum",
            "object_checksum",
            "manifest_contract",
            "infisical_identity",
            "postgresql_decrypt",
            "object_decrypt",
            "object_archive_extract",
        ):
            self.assertIn(f"fail {stage}", self.restore)
        self.assertIn('obj["service"] == "seaweedfs"', self.restore)
        for value in (
            'pg["archive_sha256"] == os.environ["PG_ACTUAL_SHA256"]',
            'obj["archive_sha256"] == os.environ["OBJECT_ACTUAL_SHA256"]',
            'int(os.environ["PG_ACTUAL_BYTES"])',
            'int(os.environ["OBJECT_ACTUAL_BYTES"])',
        ):
            self.assertIn(value, self.restore)
        self.assertIn("listen_addresses=", self.restore)
        self.assertIn("pg_restore --exit-on-error --no-owner --no-privileges", self.restore)

    def test_object_storage_is_s3_tls_authenticated_and_prefix_bound(self) -> None:
        self.assertIn("-o go-template=", self.backup)
        self.assertNotIn('get secret "$object_tls_secret" -o json', self.backup)
        self.assertNotIn('get secret "$object_auth_secret" -o json', self.backup)
        self.assertNotIn("metadata_work", self.backup)
        self.assertIn("value-suppressing Kubernetes templates", self.runbook)
        for value in (
            "reactive-resume-object-storage",
            "reactive-resume-object-storage-tls",
            "reactive-resume-object-storage-auth",
            "RCLONE_CONFIG_S3_ENDPOINT",
            "RCLONE_CA_CERT",
            "tls_contract=",
            "auth_contract=",
            "https://$object_service.$namespace.svc.cluster.local:8333",
            "uploads/user-pictures/",
            "pictures/",
            "uploads/user-agent/",
            "object-storage.tar.gz.age",
            "raw-manifest.json.tmp",
            "mv /work/raw-manifest.json.tmp /work/raw-manifest.json",
            "touch /work/export.ready",
            "test -f /work/export.ready && test -s /work/raw-manifest.json",
            'wait --for=condition=Ready "pod/$helper_pod" --timeout=1800s',
            "failureThreshold: 900",
        ):
            self.assertIn(value, self.backup, value)
        for value in (
            "rclone check --one-way --checksum",
            "rclone lsjson --recursive --hash --metadata",
            "object_remote_checksum",
            "reactive-resume-object-storage-tls",
            "reactive-resume-object-storage-auth",
            "infisical_launcher=",
            "infisical_binary=",
            "infisical_version='0.43.121'",
            "infisical_binary_sha256=",
            "infisical_executable_hash",
            "infisical_version_output",
            "restore-networkpolicy",
            "policyTypes: [Ingress, Egress]",
            "cleanup_policy",
            "pg_policy_uid=",
            "storage_policy_uid=",
            "fail pg_restore_policy_uid",
            "fail storage_restore_policy_uid",
            "target=isolated-emptydir-postgresql-and-seaweedfs",
            "restore_wall_clock_timeout_seconds=14400",
            "backup_completed_epoch=",
            "rto_seconds=",
            "postgres_archive_sha256=",
            "postgres_logical_entry_count=",
            "stop_restore_watchdog",
            "seaweed_image",
            "emptyDir",
        ):
            self.assertIn(value, self.restore, value)
        self.assertNotIn("/data" + " ", self.backup)
        self.assertNotIn("PersistentVolume", self.restore)
        policies = list(yaml.safe_load_all(NETWORK_POLICY.read_text()))
        self.assertEqual(2, len(policies))
        policy = next(item for item in policies if item["metadata"]["name"] == "reactive-resume-object-storage-allow-backup")
        egress_policy = next(item for item in policies if item["metadata"]["name"] == "reactive-resume-dev-backup-egress")
        self.assertEqual("shared-services", policy["metadata"]["namespace"])
        self.assertEqual("never-match", policy["spec"]["podSelector"]["matchLabels"]["cristex.io/run-id"])
        self.assertEqual("never-match", policy["spec"]["ingress"][0]["from"][0]["podSelector"]["matchLabels"]["cristex.io/run-id"])
        self.assertEqual("never-match", egress_policy["spec"]["podSelector"]["matchLabels"]["cristex.io/run-id"])
        self.assertEqual(
            {
                "kubernetes.io/metadata.name": "shared-services",
            },
            policy["spec"]["ingress"][0]["from"][0]["namespaceSelector"]["matchLabels"],
        )
        self.assertEqual(
            {
                "app.kubernetes.io/name": "reactive-resume-dev-backup",
                "cristex.io/object-storage-client": "backup",
                "cristex.io/run-id": "never-match",
            },
            policy["spec"]["ingress"][0]["from"][0]["podSelector"]["matchLabels"],
        )
        self.assertEqual([{"protocol": "TCP", "port": 8333}], policy["spec"]["ingress"][0]["ports"])
        self.assertEqual(
            {
                "app.kubernetes.io/name": "reactive-resume-dev-backup",
                "cristex.io/object-storage-client": "backup",
                "cristex.io/run-id": "never-match",
            },
            egress_policy["spec"]["podSelector"]["matchLabels"],
        )
        self.assertEqual(["Egress"], egress_policy["spec"]["policyTypes"])
        self.assertEqual(
            [
                {
                    "to": [{
                        "namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "kube-system"}},
                        "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}},
                    }],
                    "ports": [{"protocol": "UDP", "port": 53}, {"protocol": "TCP", "port": 53}],
                },
                {
                    "to": [{
                        "namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "shared-services"}},
                        "podSelector": {"matchLabels": {"cnpg.io/cluster": "shared-postgresql", "cnpg.io/instanceRole": "primary"}},
                    }],
                    "ports": [{"protocol": "TCP", "port": 5432}],
                },
                {
                    "to": [{
                        "namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "shared-services"}},
                        "podSelector": {"matchLabels": {"app.kubernetes.io/name": "reactive-resume-object-storage", "app.kubernetes.io/part-of": "reactive-resume"}},
                    }],
                    "ports": [{"protocol": "TCP", "port": 8333}],
                },
            ],
            egress_policy["spec"]["egress"],
        )
        self.assertIn("reactive-resume-dev-backup-networkpolicy.yaml", self.playbook_text)
        self.assertIn("helper-networkpolicy.yaml", self.backup)
        self.assertIn("helper_ingress_policy_uid", self.backup)
        self.assertIn("helper_egress_policy_uid", self.backup)
        self.assertIn("reactive-resume-dev-postgresql-restore-$pod_run_id", self.restore)
        self.assertIn("reactive-resume-dev-storage-restore-$pod_run_id", self.restore)
        self.assertIn("ingress: []", self.restore)
        self.assertIn("egress: []", self.restore)

    def test_uid_bound_helper_cleanup_and_no_service_account(self) -> None:
        for text in (self.backup, self.restore):
            self.assertIn("automountServiceAccountToken: false", text)
            self.assertIn("cristex.io/run-id", text)
            self.assertIn('propagationPolicy":"Orphan"', text)
            self.assertIn('preconditions":{"uid":"%s"}', text)
            self.assertIn("current_uid", text)
            self.assertIn("wait --for=delete", text)
        self.assertIn('rm -rf -- "$run_directory" "$work"', self.backup)
        self.assertIn('backup_success=true', self.backup)
        self.assertIn("helper_uid=", self.backup)
        self.assertIn("pg_uid=", self.restore)
        self.assertIn("storage_uid=", self.restore)
        self.assertNotRegex(self.backup, r"cleanup_helper[^\n]*\|\| true")
        self.assertNotRegex(self.restore, r"cleanup_pod[^\n]*\|\| true")

    def test_age_custody_and_plaintext_cleanup(self) -> None:
        combined = self.backup + "\n" + self.restore
        for value in (
            "/etc/cristexweb-backup/age.recipient",
            "ce615905ec27fa6e085578d96e48dc798677b3f2ade5c417770f22e78248ad28",
            "age -r",
            "SHARED_DATABASE_BACKUP_AGE_IDENTITY",
            "infisical_path=/shared-services/backup-recovery",
            "trap cleanup_plaintext EXIT HUP INT TERM",
            "private_residue=none",
        ):
            self.assertIn(value, combined, value)
        self.assertNotIn("SHARED_DATABASE_BACKUP_AGE_IDENTITY=", combined)
        self.assertNotIn("--password=", combined)

    def test_twice_daily_systemd_unit_is_hardened_and_persistent(self) -> None:
        for value in (
            "User=paul",
            "Group=paul",
            "SupplementaryGroups=k3s-admin",
            "NoNewPrivileges=true",
            "ProtectSystem=strict",
            "ProtectHome=read-only",
            "PrivateTmp=true",
            "ReadWritePaths=/var/lib/cristexweb-backup /run/lock /home/paul/.config/rclone",
            "TimeoutStartSec=60min",
            "TimeoutStopSec=180s",
        ):
            self.assertIn(value, self.service, value)
        for value in (
            "OnCalendar=*-*-* 00,12:15:00 UTC",
            "RandomizedDelaySec=0",
            "Persistent=true",
            "AccuracySec=1m",
            "WantedBy=timers.target",
            "Unit=cristexweb-reactive-resume-dev-backup.service",
        ):
            self.assertIn(value, self.timer, value)
        self.assertNotIn("OnCalendar=Sun", self.timer)
        self.assertNotIn("RandomizedDelaySec=30m", self.timer)

    def test_playbook_gates_timer_until_restore_and_supports_idempotence(self) -> None:
        for value in (
            "reactive_resume_dev_backup_approved",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT",
            "reactive_resume_dev_backup_mode in ['install', 'test', 'restore', 'enable']",
            "Keep the twice-daily timer disabled until restore acceptance",
            "Execute the separately approved one-time combined backup test",
            "Execute the separately approved isolated combined restore rehearsal",
            "Enable the accepted twice-daily timer",
            "Inspect machine acceptance evidence before timer enablement",
            "Require successful current backup and restore evidence",
            "Record root-owned successful backup evidence",
            "reactive_resume_dev_backup_test_receipt",
            "reactive_resume_dev_backup_test_run_id",
            "Capture the exact sanitized successful backup journal receipt",
            "reactive_resume_dev_backup_journal_pattern",
            "run_id=20[0-9]{6}T[0-9]{6}Z",
            "receipt': reactive_resume_dev_backup_test_receipt",
            "Record root-owned successful restore evidence",
            "source_run_id == reactive_resume_dev_backup_acceptance_backup.run_id",
            "acceptance_restore.schema == 2",
            "acceptance_restore.receipt is match(reactive_resume_dev_backup_restore_receipt_pattern)",
            "acceptance_restore.source_contract_sha256 == reactive_resume_dev_backup_source_contract_sha256",
            "source_contract_sha256",
            "acceptance_backup.receipt is match(reactive_resume_dev_backup_journal_pattern)",
            "reactive_resume_dev_backup_acceptance_max_age_seconds: 86400",
            "reactive_resume_dev_backup_mode == 'enable'",
            "Roll back the timer after failed post-enable health",
            "Roll back a partially enabled timer",
            "Timer health acceptance failed; the timer was disabled and stopped.",
            "Timer enable failed; the timer was disabled and stopped.",
            "not ansible_check_mode",
            "failed_when: false",
            "Extract only the allowlisted restore failure stage",
            "restore_status=failed stage=([a-z0-9_-]+)",
            "reactive_resume_dev_backup_repository_root == '/home/paul/projects/cristexweb'",
        ):
            self.assertIn(value, self.playbook_text, value)
        self.assertEqual("crtxweb", self.playbook["hosts"])
        self.assertTrue(self.playbook["become"])
        self.assertIn("serial", self.playbook)

    def test_wrapper_is_fixed_non_passthrough_and_restore_scoped(self) -> None:
        for value in (
            "check|apply|test|restore|enable-check|enable-apply",
            "if [ \"$#\" -ne 1 ]",
            "refusing passthrough arguments or task selection",
            "--ask-become-pass",
            "--limit crtxweb",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_ENTRYPOINT=v1",
            "CRISTEXWEB_REACTIVE_RESUME_DEV_BACKUP_RESTORE_TOKEN",
            "/home/paul/projects/cristexweb",
            "/usr/bin/env -i",
        ):
            self.assertIn(value, self.wrapper, value)
        self.assertNotIn('exec "$@"', self.wrapper)

    def test_pipeline_failures_are_not_masked_and_clock_skew_is_fail_closed(self) -> None:
        for text in (self.backup, self.restore):
            self.assertNotIn("tar -C /work -czf - objects |", text)
            self.assertNotRegex(text, r"kubectl[^\n]*\|\s*(?:age|gzip)")
            self.assertNotRegex(text, r"(?:gzip|age -d)[^\n]*\|\s*(?:age|gzip)")
        self.assertIn("/usr/bin/age -d -i \"$work/identity\" \"$work/postgresql.dump.gz.age\" >\"$work/postgresql.dump.gz\"", self.restore)
        self.assertIn("backup_completed_epoch", self.restore)
        self.assertIn("raise SystemExit(\"clock_skew\")", self.restore)
        self.assertNotIn("max(0, now -", self.restore)

    def test_runbook_records_current_checkpoint_and_recovery_contract(self) -> None:
        normalized = " ".join(self.runbook.split())
        for value in (
            "SOURCE IMPLEMENTED / PRIOR SCHEMA-1 NON-EMPTY BACKUP PASSED / HARDENED SCHEMA-2 INSTALL, BACKUP, AND RESTORE PENDING",
            "run_id=20260825T065948Z object_count=1 total_object_bytes=50 readback=verified encrypted=true private_residue=none",
            "hardened schema-2",
            "Remaining hardened acceptance sequence",
            "reactive_resume_dev_successor",
            "reactive-resume-dev",
            "one UTC `YYYYmmddTHHMMSSZ` run ID",
            "OnCalendar=*-*-* 00,12:15:00 UTC",
            "14 days",
            "rclone copyto --immutable",
            "emptyDir",
            "no raw volume copy",
            "isolated PostgreSQL",
            "isolated SeaweedFS",
            "private_residue=none",
            "PROD has no source",
            "backup_duration_seconds",
            "restore_duration_seconds",
            "rpo_seconds",
            "non-empty backup",
            "RPO `86400` seconds (24 hours)",
            "RTO `14400` seconds (4 hours)",
            "twice-daily",
            "per-object checksum",
            "clock_skew",
            "journalctl -u cristexweb-reactive-resume-dev-backup.service",
            "Capture the exact sanitized successful backup journal receipt",
            "source_run_id",
            "--ask-become-pass",
            "controlling terminal",
            "do not pipe or redirect",
        ):
            self.assertIn(value, normalized, value)
        self.assertNotIn("SOURCE-ONLY DESIGN / NOT RUN / RUNTIME UNINSTALLED", self.runbook)
        self.assertNotIn("runtime was applied", self.runbook.lower())
        self.assertNotIn("weekly backup", self.runbook.lower())


if __name__ == "__main__":
    unittest.main()
