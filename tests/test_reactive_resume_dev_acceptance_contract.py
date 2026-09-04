from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/reactive-resume-dev-offline-acceptance.json"
SOAK_DEFAULTS = ROOT / "ansible/roles/reactive_resume_dev_soak/defaults/main.yml"
SOAK_TASKS = ROOT / "ansible/roles/reactive_resume_dev_soak/tasks/main.yml"
SOAK_SAMPLE = ROOT / "ansible/roles/reactive_resume_dev_soak/tasks/sample.yml"
SOAK_RUNBOOK = ROOT / "runbooks/reactive-resume-dev-soak.md"
BACKUP_SOURCE = ROOT / "ansible/files/backup/reactive-resume-dev-backup"
RESTORE_SOURCE = ROOT / "ansible/files/backup/restore-reactive-resume-dev-backup-rehearsal"
BACKUP_PLAYBOOK = ROOT / "ansible/playbooks/configure_reactive_resume_dev_backup.yml"
BACKUP_RUNBOOK = ROOT / "runbooks/reactive-resume-dev-backup.md"
TESTCASES = ROOT / "specs/k3s-iac-foundation/testcases.md"

RUN_ID = re.compile(r"^20[0-9]{6}T[0-9]{6}Z$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SOAK_CHECKS = (
    "hostname_root_http",
    "hostname_tls_http",
    "oidc_issuer",
    "oidc_jwks",
    "app_ready",
    "backup_timer_active_enabled",
    "prod_reactive_resume_markers_absent",
    "exposure_pass",
)
REVIEWED_OBJECT_PREFIXES = (
    "uploads/user-pictures/",
    "pictures/",
    "uploads/user-agent/",
)
EXPECTED_OBJECT_INVENTORY = {
    "uploads/user-pictures/fixture-a.bin": 512,
    "pictures/fixture-b.bin": 384,
    "uploads/user-agent/fixture-c.bin": 338,
}
EXPECTED_OBJECT_COUNT = len(EXPECTED_OBJECT_INVENTORY)
EXPECTED_OBJECT_BYTES = sum(EXPECTED_OBJECT_INVENTORY.values())
MAX_RPO_SECONDS = 86400
MAX_RTO_SECONDS = 14400
EXPECTED_POSTGRES_ARCHIVE_SHA256 = "d" * 64
EXPECTED_OBJECT_ARCHIVE_SHA256 = "e" * 64
BACKUP_RECEIPT_KEYS = {
    "backup_status",
    "service",
    "run_id",
    "database",
    "object_bucket",
    "object_count",
    "total_object_bytes",
    "backup_duration_seconds",
    "readback",
    "encrypted",
    "private_residue",
}
RESTORE_RECEIPT_KEYS = {
    "restore_status",
    "schema",
    "source_run_id",
    "backup_completed_epoch",
    "backup_duration_seconds",
    "restore_duration_seconds",
    "rto_seconds",
    "rpo_seconds",
    "postgres_archive_sha256",
    "object_archive_sha256",
    "postgres_logical_entry_count",
    "postgres_logical_table_count",
    "postgres_logical_archive_bytes",
    "postgres_catalog_table_count",
    "object_count",
    "object_bytes",
    "checksum",
    "target",
    "private_residue",
}


def _strict_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _receipt_integer(fields: dict[str, str], name: str, *, positive: bool = False) -> int:
    value = fields.get(name)
    assert isinstance(value, str) and re.fullmatch(r"[0-9]+", value)
    parsed = int(value)
    if positive:
        assert parsed > 0
    else:
        assert parsed >= 0
    return parsed


def _parse_receipt(line: str, expected_keys: set[str]) -> dict[str, str]:
    """Parse only the synthetic, whitespace-delimited receipt fixture."""
    fields: dict[str, str] = {}
    for token in line.split():
        key, separator, value = token.partition("=")
        if not separator or not key or not value or key in fields:
            raise AssertionError("receipt must contain unique non-empty key=value fields")
        fields[key] = value
    if set(fields) != expected_keys:
        raise AssertionError("receipt keys differ from the exact sanitized contract")
    return fields


def _mutate_coupled_restore_end_and_rpo(payload: dict) -> None:
    restore = payload["backup_restore"]["restore"]
    restore["completed_epoch"] = 4070910500
    restore["rpo_seconds"] = 1700
    restore["receipt"] = restore["receipt"].replace("rpo_seconds=1800", "rpo_seconds=1700")


def _validate_soak_fixture(payload: dict) -> None:
    metadata = payload["_fixture_metadata"]
    assert metadata == {
        "kind": "synthetic-offline-contract-input",
        "runtime_evidence": False,
        "live_receipt": False,
        "purpose": "exercise source contracts without contacting a host, cluster, provider, or secret store",
    }
    soak = payload["soak"]
    assert soak["duration_seconds"] == 900
    assert soak["interval_seconds"] == 60
    assert soak["sample_count"] == 16
    assert soak["measured_elapsed_seconds"] >= soak["duration_seconds"]
    assert soak["values_output"] is False
    assert soak["exposure_pass"] is True

    samples = soak["samples"]
    assert len(samples) == soak["sample_count"]
    assert [sample["sample"] for sample in samples] == list(range(16))
    assert [sample["offset_seconds"] for sample in samples] == [index * 60 for index in range(16)]
    assert samples[0]["offset_seconds"] == 0
    assert samples[-1]["offset_seconds"] == 900
    for sample in samples:
        assert set(SOAK_CHECKS) <= set(sample)
        assert all(sample[key] is True for key in SOAK_CHECKS)


def _validate_backup_restore_fixture(payload: dict) -> None:
    metadata = payload["_fixture_metadata"]
    assert metadata["runtime_evidence"] is False
    assert metadata["live_receipt"] is False

    evidence = payload["backup_restore"]
    closure = evidence["source_closure"]
    assert set(closure) == {"source_contract_sha256", "wrapper_sha256", "playbook_sha256"}
    assert all(isinstance(value, str) and HEX64.fullmatch(value) for value in closure.values())

    objects = evidence["objects"]
    assert isinstance(objects, list)
    assert len(objects) == EXPECTED_OBJECT_COUNT
    assert all(isinstance(item, dict) and set(item) == {"key", "size"} for item in objects)
    keys = [item["key"] for item in objects]
    assert len(keys) == len(set(keys))
    assert all(isinstance(key, str) and key == key.strip() and key for key in keys)
    assert all(
        any(key.startswith(prefix) and key[len(prefix) :] for prefix in REVIEWED_OBJECT_PREFIXES)
        for key in keys
    )
    assert all(
        not key.startswith("/")
        and "\\" not in key
        and "\x00" not in key
        and "\t" not in key
        and "\r" not in key
        and "\n" not in key
        and all(part not in {"", ".", ".."} for part in key.split("/"))
        for key in keys
    )
    assert {prefix for key in keys for prefix in REVIEWED_OBJECT_PREFIXES if key.startswith(prefix)} == set(
        REVIEWED_OBJECT_PREFIXES
    )
    inventory = {item["key"]: item["size"] for item in objects}
    assert inventory == EXPECTED_OBJECT_INVENTORY
    assert all(_strict_int(size) and size > 0 for size in inventory.values())
    expected_object_count = len(inventory)
    expected_object_bytes = sum(inventory.values())
    assert expected_object_count == EXPECTED_OBJECT_COUNT
    assert expected_object_bytes == EXPECTED_OBJECT_BYTES

    backup = evidence["backup"]
    restore = evidence["restore"]
    backup_receipt = _parse_receipt(backup["receipt"], BACKUP_RECEIPT_KEYS)
    restore_receipt = _parse_receipt(restore["receipt"], RESTORE_RECEIPT_KEYS)

    run_id = backup["run_id"]
    assert isinstance(run_id, str) and RUN_ID.fullmatch(run_id)
    assert backup["kind"] == "reactive-resume-dev-backup-test"
    assert backup["status"] == "success"
    assert backup["private_residue"] == "none"
    assert backup["manifest"]["schema"] == 2
    assert backup["manifest"]["run_id"] == run_id
    assert backup["manifest"]["source_closure"] == closure
    assert backup["manifest"]["object_count"] == expected_object_count
    assert backup["manifest"]["total_object_bytes"] == expected_object_bytes
    assert backup_receipt["backup_status"] == "success"
    assert backup_receipt["service"] == "reactive-resume-dev"
    assert backup_receipt["database"] == "reactive_resume_dev_successor"
    assert backup_receipt["object_bucket"] == "reactive-resume-dev"
    assert backup_receipt["readback"] == "verified"
    assert backup_receipt["encrypted"] == "true"
    assert backup_receipt["run_id"] == run_id
    assert _receipt_integer(backup_receipt, "object_count", positive=True) == expected_object_count
    assert _receipt_integer(backup_receipt, "total_object_bytes", positive=True) == expected_object_bytes
    backup_duration = _receipt_integer(backup_receipt, "backup_duration_seconds")
    assert _strict_int(backup["started_epoch"]) and backup["started_epoch"] >= 0
    assert _strict_int(backup["completed_epoch"]) and backup["completed_epoch"] >= backup["started_epoch"]
    assert backup["completed_epoch"] - backup["started_epoch"] == backup_duration
    assert backup_receipt["private_residue"] == "none"

    assert restore["kind"] == "reactive-resume-dev-restore"
    assert restore["status"] == "success"
    assert restore["schema"] == 2
    assert restore["source_run_id"] == run_id
    assert restore["source_closure"] == closure
    assert restore["private_residue"] == "none"
    assert restore["object_count"] == expected_object_count
    assert restore["object_bytes"] == expected_object_bytes
    assert _strict_int(restore["restore_started_epoch"])
    assert restore["restore_started_epoch"] >= backup["completed_epoch"]
    assert _strict_int(restore["completed_epoch"]) and restore["completed_epoch"] >= restore["restore_started_epoch"]
    restore_rpo = restore["completed_epoch"] - backup["completed_epoch"]
    assert _strict_int(restore["rpo_seconds"]) and restore["rpo_seconds"] == restore_rpo
    assert 0 <= restore_rpo <= MAX_RPO_SECONDS
    restore_duration = restore["completed_epoch"] - restore["restore_started_epoch"]
    assert _strict_int(restore["rto_seconds"]) and restore["rto_seconds"] == restore_duration
    assert 0 <= restore_duration <= MAX_RTO_SECONDS
    assert restore_receipt["restore_status"] == "success"
    assert restore_receipt["schema"] == "2"
    assert restore_receipt["source_run_id"] == run_id
    assert _receipt_integer(restore_receipt, "backup_completed_epoch") == backup["completed_epoch"]
    assert _receipt_integer(restore_receipt, "backup_duration_seconds") == backup_duration
    assert _receipt_integer(restore_receipt, "restore_duration_seconds") == restore_duration
    assert _receipt_integer(restore_receipt, "rto_seconds") == restore_duration
    assert _receipt_integer(restore_receipt, "object_count", positive=True) == expected_object_count
    assert _receipt_integer(restore_receipt, "object_bytes", positive=True) == expected_object_bytes
    assert _receipt_integer(restore_receipt, "rpo_seconds") == restore_rpo
    assert HEX64.fullmatch(restore_receipt["postgres_archive_sha256"])
    assert HEX64.fullmatch(restore_receipt["object_archive_sha256"])
    assert restore_receipt["postgres_archive_sha256"] == EXPECTED_POSTGRES_ARCHIVE_SHA256
    assert restore_receipt["object_archive_sha256"] == EXPECTED_OBJECT_ARCHIVE_SHA256
    assert restore_receipt["checksum"] == "verified"
    assert restore_receipt["private_residue"] == "none"


class ReactiveResumeDevAcceptanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.soak_defaults = SOAK_DEFAULTS.read_text()
        cls.soak_tasks = SOAK_TASKS.read_text()
        cls.soak_sample = SOAK_SAMPLE.read_text()
        cls.soak_runbook = SOAK_RUNBOOK.read_text()
        cls.backup_source = BACKUP_SOURCE.read_text()
        cls.restore_source = RESTORE_SOURCE.read_text()
        cls.backup_playbook = BACKUP_PLAYBOOK.read_text()
        cls.backup_runbook = BACKUP_RUNBOOK.read_text()
        cls.testcases = TESTCASES.read_text()

    def test_fixture_is_explicitly_synthetic_and_not_live_evidence(self) -> None:
        metadata = self.fixture["_fixture_metadata"]
        self.assertEqual("synthetic-offline-contract-input", metadata["kind"])
        self.assertFalse(metadata["runtime_evidence"])
        self.assertFalse(metadata["live_receipt"])
        self.assertNotIn("20260825T065948Z", FIXTURE.read_text())
        self.assertNotIn("20990101T000000Z", self.soak_runbook + self.backup_runbook)

    def test_soak_fixture_proves_exact_samples_window_and_exposure(self) -> None:
        _validate_soak_fixture(self.fixture)
        soak = self.fixture["soak"]
        self.assertEqual(16, len(soak["samples"]))
        self.assertEqual(900, soak["samples"][-1]["offset_seconds"])
        self.assertTrue(all(sample["exposure_pass"] for sample in soak["samples"]))

    def test_soak_fixture_rejects_short_window_duplicate_or_failed_exposure(self) -> None:
        mutations = (
            lambda value: value["soak"]["samples"].pop(),
            lambda value: value["soak"]["samples"].__setitem__(15, {**value["soak"]["samples"][14], "sample": 14}),
            lambda value: value["soak"].update(measured_elapsed_seconds=899),
            lambda value: value["soak"]["samples"][7].update(exposure_pass=False),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                candidate = copy.deepcopy(self.fixture)
                mutate(candidate)
                with self.assertRaises(AssertionError):
                    _validate_soak_fixture(candidate)

    def test_soak_source_binds_exact_fixture_window_and_all_sample_passes(self) -> None:
        for text in (self.soak_defaults, self.soak_tasks, self.soak_sample, self.soak_runbook):
            self.assertNotIn("Authorization: Bearer", text)
            self.assertNotIn("BEGIN PRIVATE KEY", text)
        for value in (
            "reactive_resume_dev_soak_duration_seconds: 900",
            "reactive_resume_dev_soak_interval_seconds: 60",
            "reactive_resume_dev_soak_sample_count: 16",
            "reactive_resume_dev_soak_sample_count == (reactive_resume_dev_soak_duration_seconds // reactive_resume_dev_soak_interval_seconds) + 1",
            "range(0, reactive_resume_dev_soak_sample_count)",
            "map(attribute='sample')",
            "reactive_resume_dev_soak_internal_elapsed_seconds >= reactive_resume_dev_soak_duration_seconds",
            "selectattr('exposure_pass', 'equalto', true)",
            "samples: \"{{ reactive_resume_dev_soak_sample_count }}\"",
            "exposure_pass: true",
            "values_output: false",
        ):
            self.assertIn(value, self.soak_tasks + self.soak_defaults, value)
        self.assertIn("16 samples", self.soak_runbook)
        self.assertIn("900 seconds", self.soak_runbook)
        self.assertIn("exposure_pass: true", self.soak_runbook)

    def test_backup_restore_fixture_correlates_inventory_counts_rpo_rto_and_closure(self) -> None:
        _validate_backup_restore_fixture(self.fixture)
        evidence = self.fixture["backup_restore"]
        self.assertEqual(evidence["backup"]["run_id"], evidence["restore"]["source_run_id"])
        self.assertEqual(evidence["backup"]["manifest"]["schema"], evidence["restore"]["schema"])
        self.assertEqual(evidence["backup"]["manifest"]["source_closure"], evidence["restore"]["source_closure"])
        self.assertEqual(evidence["backup"]["manifest"]["object_count"], evidence["restore"]["object_count"])
        self.assertEqual(evidence["backup"]["manifest"]["total_object_bytes"], evidence["restore"]["object_bytes"])
        self.assertEqual(1800, evidence["restore"]["completed_epoch"] - evidence["backup"]["completed_epoch"])
        self.assertEqual(1800, evidence["restore"]["rpo_seconds"])
        self.assertEqual(1200, evidence["restore"]["rto_seconds"])

    def test_backup_restore_fixture_rejects_object_identity_totals_or_timing_drift(self) -> None:
        mutations = (
            (
                "duplicate key",
                lambda value: value["backup_restore"]["objects"][1].update(
                    key=value["backup_restore"]["objects"][0]["key"]
                ),
            ),
            (
                "unreviewed prefix",
                lambda value: value["backup_restore"]["objects"][0].update(
                    key="private/fixture-a.bin"
                ),
            ),
            (
                "path traversal",
                lambda value: value["backup_restore"]["objects"][0].update(
                    key="uploads/user-pictures/../fixture-a.bin"
                ),
            ),
            (
                "changed total",
                lambda value: value["backup_restore"]["objects"][0].update(size=513),
            ),
            (
                "backup completion",
                lambda value: value["backup_restore"]["backup"].update(
                    completed_epoch=4070908799
                ),
            ),
            (
                "backup duration",
                lambda value: value["backup_restore"]["backup"]["receipt"].replace(
                    "backup_duration_seconds=42", "backup_duration_seconds=43"
                ),
            ),
            (
                "restore before backup",
                lambda value: value["backup_restore"]["restore"].update(
                    completed_epoch=4070908799
                ),
            ),
            (
                "restore rpo",
                lambda value: value["backup_restore"]["restore"].update(rpo_seconds=1799),
            ),
            (
                "restore receipt completion",
                lambda value: value["backup_restore"]["restore"]["receipt"].replace(
                    "backup_completed_epoch=4070908800", "backup_completed_epoch=4070908799"
                ),
            ),
            (
                "restore rto",
                lambda value: value["backup_restore"]["restore"].update(rto_seconds=1199),
            ),
            (
                "restore duration",
                lambda value: value["backup_restore"]["restore"]["receipt"].replace(
                    "restore_duration_seconds=1200", "restore_duration_seconds=1199"
                ),
            ),
            (
                "restore start epoch",
                lambda value: value["backup_restore"]["restore"].update(
                    restore_started_epoch=4070909500
                ),
            ),
            (
                "coupled restore end and RPO",
                lambda value: _mutate_coupled_restore_end_and_rpo(value),
            ),
            (
                "restore receipt backup duration",
                lambda value: value["backup_restore"]["restore"].update(
                    receipt=value["backup_restore"]["restore"]["receipt"].replace(
                        "backup_duration_seconds=42", "backup_duration_seconds=43"
                    )
                ),
            ),
        )
        for name, mutate in mutations:
            with self.subTest(mutation=name):
                candidate = copy.deepcopy(self.fixture)
                result = mutate(candidate)
                if isinstance(result, str):
                    if name == "backup duration":
                        candidate["backup_restore"]["backup"]["receipt"] = result
                    elif name in {"restore receipt completion", "restore duration"}:
                        candidate["backup_restore"]["restore"]["receipt"] = result
                with self.assertRaises(AssertionError):
                    _validate_backup_restore_fixture(candidate)

    def test_backup_restore_fixture_rejects_receipt_keys_and_archive_hash_drift(self) -> None:
        mutations = (
            (
                "backup receipt extra key",
                lambda value: value["backup_restore"]["backup"].update(
                    receipt=value["backup_restore"]["backup"]["receipt"] + " unexpected=1"
                ),
            ),
            (
                "backup receipt missing key",
                lambda value: value["backup_restore"]["backup"].update(
                    receipt=value["backup_restore"]["backup"]["receipt"].replace(
                        "encrypted=true ", ""
                    )
                ),
            ),
            (
                "restore receipt extra key",
                lambda value: value["backup_restore"]["restore"].update(
                    receipt=value["backup_restore"]["restore"]["receipt"] + " unexpected=1"
                ),
            ),
            (
                "restore receipt missing key",
                lambda value: value["backup_restore"]["restore"].update(
                    receipt=value["backup_restore"]["restore"]["receipt"].replace(
                        "checksum=verified ", ""
                    )
                ),
            ),
            (
                "postgres archive hash",
                lambda value: value["backup_restore"]["restore"].update(
                    receipt=value["backup_restore"]["restore"]["receipt"].replace(
                        EXPECTED_POSTGRES_ARCHIVE_SHA256, "f" * 64
                    )
                ),
            ),
            (
                "object archive hash",
                lambda value: value["backup_restore"]["restore"].update(
                    receipt=value["backup_restore"]["restore"]["receipt"].replace(
                        EXPECTED_OBJECT_ARCHIVE_SHA256, "f" * 64
                    )
                ),
            ),
        )
        for name, mutate in mutations:
            with self.subTest(mutation=name):
                candidate = copy.deepcopy(self.fixture)
                mutate(candidate)
                with self.assertRaises(AssertionError):
                    _validate_backup_restore_fixture(candidate)

    def test_backup_restore_fixture_rejects_correlation_drift(self) -> None:
        mutations = (
            lambda value: value["backup_restore"]["restore"].update(source_run_id="20990101T000100Z"),
            lambda value: value["backup_restore"]["restore"].update(schema=1),
            lambda value: value["backup_restore"]["restore"]["source_closure"].update(wrapper_sha256="f" * 64),
            lambda value: value["backup_restore"]["restore"].update(object_count=2),
            lambda value: value["backup_restore"]["restore"]["receipt"].replace("rpo_seconds=1800", "rpo_seconds=1801"),
            lambda value: value["backup_restore"]["restore"].update(private_residue="present"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                candidate = copy.deepcopy(self.fixture)
                result = mutate(candidate)
                if isinstance(result, str):
                    candidate["backup_restore"]["restore"]["receipt"] = result
                with self.assertRaises(AssertionError):
                    _validate_backup_restore_fixture(candidate)

    def test_backup_restore_source_exposes_only_required_schema2_contract(self) -> None:
        for value in (
            '"schema": 2',
            '"run_id": run_id',
            '"object_count": int(count)',
            '"total_object_bytes": int(total)',
            'correlated-stability-fence-not-atomic',
            'restore_status=success schema=2 source_run_id=',
            "backup_completed_epoch=",
            "restore_start_epoch=",
            "restore_duration_seconds=",
            "rto_seconds=",
            "rpo_seconds=",
            "object_count=",
            "object_bytes=",
            "private_residue=none",
            'run["run_id"] == os.environ["RUN_ID"]',
            'run["object_storage"]["object_count"] > 0',
            'run["object_storage"]["total_object_bytes"] > 0',
            "assert key not in seen",
            "assert actual == seen",
            'allowed = ("uploads/user-pictures/", "pictures/", "uploads/user-agent/")',
        ):
            self.assertIn(value, self.backup_source + self.restore_source, value)
        for value in (
            "acceptance_restore.schema == 2",
            "acceptance_restore.source_run_id == reactive_resume_dev_backup_acceptance_backup.run_id",
            "source_contract_sha256 == reactive_resume_dev_backup_source_contract_sha256",
            "wrapper_sha256 == reactive_resume_dev_backup_wrapper_sha256",
            "playbook_sha256 == reactive_resume_dev_backup_playbook_sha256",
            "backup_completed_epoch=[0-9]+ backup_duration_seconds=[0-9]+ restore_duration_seconds=[0-9]+ rto_seconds=[0-9]+ rpo_seconds=[0-9]+",
            "postgres_archive_sha256=[0-9a-f]{64} object_archive_sha256=[0-9a-f]{64}",
            "object_count=[1-9][0-9]* object_bytes=[1-9][0-9]*",
            "private_residue=none$",
        ):
            self.assertIn(value, self.backup_playbook, value)

    def test_testcase_record_is_offline_only_and_keeps_live_acceptance_pending(self) -> None:
        row_start = self.testcases.index("| KIF-RR-02 |")
        row_end = self.testcases.index("\n", row_start)
        row = self.testcases[row_start:row_end]
        self.assertIn("offline contract", row)
        self.assertIn("PASS SOURCE-ONLY", row)
        self.assertIn("NOT RUN/BLOCKED", row)
        self.assertIn("No inventory host", row)
        self.assertNotIn("runtime acceptance passed", row.lower())
        self.assertIn("live 16-sample soak", row.lower())

    def test_fixture_object_inventory_is_exact_and_value_free(self) -> None:
        objects = self.fixture["backup_restore"]["objects"]
        self.assertEqual(3, len(objects))
        self.assertEqual(1234, sum(item["size"] for item in objects))
        serialized = json.dumps(self.fixture, sort_keys=True)
        for forbidden in ("password", "client_secret", "Authorization", "AGE-SECRET-KEY-"):
            self.assertNotIn(forbidden, serialized)
        self.assertNotIn("source_contract_sha256=", self.fixture["backup_restore"]["backup"]["receipt"])


if __name__ == "__main__":
    unittest.main()
