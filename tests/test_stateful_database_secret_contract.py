from __future__ import annotations

import base64
import importlib.util
import ipaddress
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "ansible/plugins/action/stateful_database_secret_contract.py"
SPEC = importlib.util.spec_from_file_location("database_secret_contract", PLUGIN_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _certificate_material(
    names: set[str],
    *,
    eku: x509.ObjectIdentifier = ExtendedKeyUsageOID.SERVER_AUTH,
    leaf_key_size: int = 2048,
    ca_key_size: int = 2048,
    expired: bool = False,
    not_yet_valid: bool = False,
    mismatched_key: bool = False,
    ca_is_ca: bool = True,
    leaf_is_ca: bool = False,
    forged_signature: bool = False,
    extra_ip_san: bool = False,
) -> tuple[bytes, bytes, bytes]:
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=ca_key_size)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Cristex Test CA")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(NOW - timedelta(days=2))
        .not_valid_after(NOW + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=ca_is_ca, path_length=0 if ca_is_ca else None),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )
    leaf_key = rsa.generate_private_key(public_exponent=65537, key_size=leaf_key_size)
    if expired:
        not_before, not_after = NOW - timedelta(days=3), NOW - timedelta(days=1)
    elif not_yet_valid:
        not_before, not_after = NOW + timedelta(days=1), NOW + timedelta(days=30)
    else:
        not_before, not_after = NOW - timedelta(days=1), NOW + timedelta(days=30)
    signing_key = (
        rsa.generate_private_key(public_exponent=65537, key_size=2048)
        if forged_signature
        else ca_key
    )
    leaf = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "database")]))
        .issuer_name(ca.subject)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName(name) for name in sorted(names)]
                + (
                    [x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
                    if extra_ip_san
                    else []
                )
            ),
            critical=False,
        )
        .add_extension(x509.ExtendedKeyUsage([eku]), critical=False)
        .add_extension(
            x509.BasicConstraints(ca=leaf_is_ca, path_length=0 if leaf_is_ca else None),
            critical=True,
        )
        .sign(signing_key, hashes.SHA256())
    )
    exported_key = (
        rsa.generate_private_key(public_exponent=65537, key_size=leaf_key_size)
        if mismatched_key
        else leaf_key
    )
    return (
        ca.public_bytes(serialization.Encoding.PEM),
        leaf.public_bytes(serialization.Encoding.PEM),
        exported_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ),
    )


def _results(
    engine: str,
    *,
    names: set[str] | None = None,
    password: bytes = b"a-secure-database-password-with-32-bytes",
    eku: x509.ObjectIdentifier = ExtendedKeyUsageOID.SERVER_AUTH,
    leaf_key_size: int = 2048,
    ca_key_size: int = 2048,
    expired: bool = False,
    not_yet_valid: bool = False,
    mismatched_key: bool = False,
    ca_is_ca: bool = True,
    leaf_is_ca: bool = False,
    forged_signature: bool = False,
    extra_ip_san: bool = False,
) -> list[dict]:
    required = MODULE._REQUIRED_TLS_DNS_NAMES[engine]
    ca_pem, leaf_pem, key_pem = _certificate_material(
        names if names is not None else required,
        eku=eku,
        leaf_key_size=leaf_key_size,
        ca_key_size=ca_key_size,
        expired=expired,
        not_yet_valid=not_yet_valid,
        mismatched_key=mismatched_key,
        ca_is_ca=ca_is_ca,
        leaf_is_ca=leaf_is_ca,
        forged_signature=forged_signature,
        extra_ip_san=extra_ip_san,
    )
    if engine == "postgresql":
        auth_name, tls_name = "shared-postgresql-admin", "shared-postgresql-tls"
        tls_data = {"ca.crt": _b64(ca_pem), "tls.crt": _b64(leaf_pem), "tls.key": _b64(key_pem)}
    else:
        auth_name, tls_name = "shared-mongodb-auth", "shared-mongodb-tls"
        tls_data = {"ca.crt": _b64(ca_pem), "tls.pem": _b64(leaf_pem + key_pem)}
    labels = {
        "app.kubernetes.io/managed-by": "infisical",
        "app.kubernetes.io/part-of": "shared-databases",
        "cristex.io/value-owner": "infisical-cloud",
    }
    auth = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": auth_name, "namespace": "shared-services", "labels": labels},
        "type": "Opaque",
        "data": {"username": _b64(b"db_admin"), "password": _b64(password)},
    }
    tls = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": tls_name, "namespace": "shared-services", "labels": labels},
        "type": "kubernetes.io/tls" if engine == "postgresql" else "Opaque",
        "data": tls_data,
    }
    return [{"resources": [auth]}, {"resources": [tls]}]


class StatefulDatabaseSecretContractTests(unittest.TestCase):
    def test_valid_exact_postgresql_and_mongodb_contracts(self) -> None:
        for engine in ("postgresql", "mongodb"):
            with self.subTest(engine=engine):
                MODULE.validate_secret_results(engine, _results(engine), NOW)

    def test_rejects_weak_auth_and_wrong_secret_closure(self) -> None:
        for engine in ("postgresql", "mongodb"):
            with self.subTest(engine=engine, failure="password"):
                with self.assertRaises(ValueError):
                    MODULE.validate_secret_results(engine, _results(engine, password=b"short"), NOW)
            wrong = _results(engine)
            wrong[0]["resources"][0]["metadata"]["name"] = "attacker-secret"
            with self.subTest(engine=engine, failure="identity"):
                with self.assertRaises(ValueError):
                    MODULE.validate_secret_results(engine, wrong, NOW)

    def test_rejects_missing_identity_wrong_eku_expiry_and_key_mismatch(self) -> None:
        for engine in ("postgresql", "mongodb"):
            cases = (
                {"names": {"localhost"}},
                {"eku": ExtendedKeyUsageOID.CLIENT_AUTH},
                {"expired": True},
                {"not_yet_valid": True},
                {"mismatched_key": True},
                {"leaf_key_size": 1024},
                {"ca_key_size": 1024},
                {"ca_is_ca": False},
                {"leaf_is_ca": True},
                {"forged_signature": True},
                {"extra_ip_san": True},
            )
            for case in cases:
                with self.subTest(engine=engine, case=case):
                    with self.assertRaises(ValueError):
                        MODULE.validate_secret_results(engine, _results(engine, **case), NOW)

    def test_rejects_metadata_data_encoding_and_encrypted_key_drift(self) -> None:
        cases = []
        wrong_namespace = _results("postgresql")
        wrong_namespace[0]["resources"][0]["metadata"]["namespace"] = "attacker"
        cases.append(wrong_namespace)
        extra_key = _results("postgresql")
        extra_key[0]["resources"][0]["data"]["extra"] = _b64(b"value")
        cases.append(extra_key)
        malformed_base64 = _results("postgresql")
        malformed_base64[0]["resources"][0]["data"]["password"] = "%%%"
        cases.append(malformed_base64)
        malformed_resource = _results("postgresql")
        malformed_resource[0]["resources"][0] = []
        cases.append(malformed_resource)
        for results in cases:
            with self.subTest(results=cases.index(results)):
                with self.assertRaises(ValueError):
                    MODULE.validate_secret_results("postgresql", results, NOW)

        encrypted = _results("postgresql")
        encrypted_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        encrypted[1]["resources"][0]["data"]["tls.key"] = _b64(
            encrypted_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.BestAvailableEncryption(b"not-a-secret-fixture"),
            )
        )
        with self.assertRaises(ValueError):
            MODULE.validate_secret_results("postgresql", encrypted, NOW)

    def test_mongodb_combined_pem_must_be_one_leaf_and_one_key(self) -> None:
        results = _results("mongodb")
        tls_data = results[1]["resources"][0]["data"]
        tls_data["tls.pem"] = _b64(base64.b64decode(tls_data["tls.pem"]) + base64.b64decode(tls_data["tls.pem"]))
        with self.assertRaises(ValueError):
            MODULE.validate_secret_results("mongodb", results, NOW)

    def test_plugin_is_source_bound_and_roles_never_log_values(self) -> None:
        source = PLUGIN_PATH.read_text()
        self.assertIn("_TASK_SOURCE_CONTRACTS", source)
        self.assertIn('set(self._task.args) != {"secret_results"}', source)
        self.assertNotIn("invocation", source)
        labels = {"postgresql": "PostgreSQL", "mongodb": "MongoDB"}
        for engine in ("postgresql", "mongodb"):
            tasks = (ROOT / f"ansible/roles/{engine}_bootstrap/tasks/main.yml").read_text()
            validation = tasks.split(
                f"- name: Validate exact {labels[engine]} Secret values without disclosure",
                1,
            )[1].split("\n\n", 1)[0]
            self.assertIn("no_log: true", validation)
            self.assertIn("stateful_database_secret_contract:", validation)
            self.assertNotIn("engine:", validation)


if __name__ == "__main__":
    unittest.main()
