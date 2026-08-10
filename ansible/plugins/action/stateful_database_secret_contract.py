from __future__ import annotations

import base64
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from ansible.plugins.action import ActionBase
from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID

_TASK_SOURCE_CONTRACTS = {
    (
        "/Users/paul/Projects/cristexweb/ansible/roles/"
        "postgresql_bootstrap/tasks/main.yml"
    ): "postgresql",
    (
        "/Users/paul/Projects/cristexweb/ansible/roles/"
        "mongodb_bootstrap/tasks/main.yml"
    ): "mongodb",
}
_REQUIRED_TLS_DNS_NAMES = {
    "postgresql": {
        "localhost",
        "shared-postgresql.shared-services.svc",
        "shared-postgresql.shared-services.svc.cluster.local",
    },
    "mongodb": {
        "localhost",
        "shared-mongodb.shared-services.svc",
        "shared-mongodb.shared-services.svc.cluster.local",
    },
}
_EXPECTED_SECRET_CONTRACTS = {
    "postgresql": {
        "shared-postgresql-admin": ("Opaque", {"username", "password"}),
        "shared-postgresql-tls": (
            "kubernetes.io/tls",
            {"ca.crt", "tls.crt", "tls.key"},
        ),
    },
    "mongodb": {
        "shared-mongodb-auth": ("Opaque", {"username", "password"}),
        "shared-mongodb-tls": ("Opaque", {"ca.crt", "tls.pem"}),
    },
}
_USERNAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
_CERTIFICATE_PATTERN = re.compile(
    rb"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", re.DOTALL
)
_PRIVATE_KEY_PATTERN = re.compile(
    rb"-----BEGIN (?:RSA |EC |)PRIVATE KEY-----.*?"
    rb"-----END (?:RSA |EC |)PRIVATE KEY-----",
    re.DOTALL,
)
_MINIMUM_REMAINING_VALIDITY = timedelta(hours=24)


def _decode(secret: dict[str, Any], key: str) -> bytes:
    encoded = (secret.get("data") or {}).get(key)
    if not isinstance(encoded, str):
        raise ValueError("missing Secret data")
    return base64.b64decode(encoded, validate=True)


def _secret_map(secret_results: Any, engine: str) -> dict[str, dict[str, Any]]:
    if not isinstance(secret_results, list) or len(secret_results) != 2:
        raise ValueError("invalid Secret result closure")
    secrets: dict[str, dict[str, Any]] = {}
    for result in secret_results:
        resources = result.get("resources") if isinstance(result, dict) else None
        if not isinstance(resources, list) or len(resources) != 1:
            raise ValueError("invalid Secret result")
        secret = resources[0]
        if not isinstance(secret, dict):
            raise ValueError("invalid Secret resource")
        metadata = secret.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError("invalid Secret metadata")
        name = metadata.get("name")
        if not isinstance(name, str) or name in secrets:
            raise ValueError("invalid Secret identity")
        labels = metadata.get("labels") or {}
        data = secret.get("data") or {}
        if not isinstance(labels, dict) or not isinstance(data, dict):
            raise ValueError("invalid Secret contract fields")
        expected_type, expected_keys = _EXPECTED_SECRET_CONTRACTS[engine].get(
            name, (None, set())
        )
        if (
            secret.get("apiVersion") != "v1"
            or secret.get("kind") != "Secret"
            or metadata.get("namespace") != "shared-services"
            or secret.get("type") != expected_type
            or set(data) != expected_keys
            or labels.get("app.kubernetes.io/managed-by") != "infisical"
            or labels.get("app.kubernetes.io/part-of") != "shared-databases"
            or labels.get("cristex.io/value-owner") != "infisical-cloud"
        ):
            raise ValueError("invalid Secret contract")
        secrets[name] = secret
    if set(secrets) != set(_EXPECTED_SECRET_CONTRACTS[engine]):
        raise ValueError("invalid Secret identity closure")
    return secrets


def _certificate_and_key(engine: str, tls_secret: dict[str, Any]) -> tuple[bytes, bytes, bytes]:
    ca_pem = _decode(tls_secret, "ca.crt")
    if engine == "postgresql":
        return ca_pem, _decode(tls_secret, "tls.crt"), _decode(tls_secret, "tls.key")
    combined_pem = _decode(tls_secret, "tls.pem")
    certificates = _CERTIFICATE_PATTERN.findall(combined_pem)
    private_keys = _PRIVATE_KEY_PATTERN.findall(combined_pem)
    residue = _CERTIFICATE_PATTERN.sub(b"", combined_pem)
    residue = _PRIVATE_KEY_PATTERN.sub(b"", residue)
    if len(certificates) != 1 or len(private_keys) != 1 or residue.strip():
        raise ValueError("invalid combined TLS PEM closure")
    return ca_pem, certificates[0], private_keys[0]


def _load_exact_certificates(pem: bytes) -> list[x509.Certificate]:
    blocks = _CERTIFICATE_PATTERN.findall(pem)
    if not blocks or _CERTIFICATE_PATTERN.sub(b"", pem).strip():
        raise ValueError("invalid certificate PEM closure")
    return [x509.load_pem_x509_certificate(block) for block in blocks]


def _require_current(certificate: x509.Certificate, now: datetime) -> None:
    if not certificate.not_valid_before_utc <= now < certificate.not_valid_after_utc:
        raise ValueError("certificate validity failure")
    if certificate.not_valid_after_utc - now < _MINIMUM_REMAINING_VALIDITY:
        raise ValueError("certificate expires too soon")


def _require_strong_key(key: Any) -> None:
    if isinstance(key, (rsa.RSAPrivateKey, rsa.RSAPublicKey)):
        if key.key_size < 2048:
            raise ValueError("RSA key is too small")
        return
    if isinstance(key, (ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey)):
        if key.key_size < 256:
            raise ValueError("elliptic-curve key is too small")
        return
    raise ValueError("unsupported key type")


def _validate_tls(engine: str, tls_secret: dict[str, Any], now: datetime) -> None:
    ca_pem, leaf_pem, private_key_pem = _certificate_and_key(engine, tls_secret)
    ca_certificates = _load_exact_certificates(ca_pem)
    leaf_certificates = _load_exact_certificates(leaf_pem)
    if not ca_certificates or len(leaf_certificates) != 1:
        raise ValueError("invalid certificate closure")
    leaf = leaf_certificates[0]
    private_key_blocks = _PRIVATE_KEY_PATTERN.findall(private_key_pem)
    if (
        len(private_key_blocks) != 1
        or _PRIVATE_KEY_PATTERN.sub(b"", private_key_pem).strip()
    ):
        raise ValueError("invalid private key PEM closure")
    private_key = serialization.load_pem_private_key(private_key_blocks[0], password=None)
    _require_strong_key(private_key)
    _require_current(leaf, now)
    if leaf.signature_hash_algorithm.name not in {"sha256", "sha384", "sha512"}:
        raise ValueError("weak certificate signature algorithm")
    leaf_constraints = leaf.extensions.get_extension_for_class(
        x509.BasicConstraints
    ).value
    if leaf_constraints.ca:
        raise ValueError("server leaf cannot be a CA")

    subject_alternative_names = leaf.extensions.get_extension_for_class(
        x509.SubjectAlternativeName
    ).value
    names = set(subject_alternative_names.get_values_for_type(x509.DNSName))
    if (
        names != _REQUIRED_TLS_DNS_NAMES[engine]
        or len(subject_alternative_names) != len(names)
    ):
        raise ValueError("server identity closure is not exact")
    extended_key_usage = leaf.extensions.get_extension_for_class(
        x509.ExtendedKeyUsage
    ).value
    if ExtendedKeyUsageOID.SERVER_AUTH not in extended_key_usage:
        raise ValueError("server authentication usage is absent")

    leaf_public = leaf.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_public = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    if leaf_public != private_public:
        raise ValueError("certificate and private key do not match")

    valid_issuers = []
    for certificate in ca_certificates:
        _require_current(certificate, now)
        _require_strong_key(certificate.public_key())
        if certificate.signature_hash_algorithm.name not in {
            "sha256",
            "sha384",
            "sha512",
        }:
            raise ValueError("weak CA signature algorithm")
        basic_constraints = certificate.extensions.get_extension_for_class(
            x509.BasicConstraints
        ).value
        if not basic_constraints.ca or leaf.issuer != certificate.subject:
            continue
        try:
            leaf.verify_directly_issued_by(certificate)
        except (InvalidSignature, ValueError):
            continue
        valid_issuers.append(certificate)
    if len(valid_issuers) != 1:
        raise ValueError("leaf certificate does not have one valid direct CA issuer")


def validate_secret_results(
    engine: str, secret_results: Any, now: datetime | None = None
) -> None:
    if engine not in _EXPECTED_SECRET_CONTRACTS:
        raise ValueError("unknown database engine")
    secrets = _secret_map(secret_results, engine)
    auth_name = (
        "shared-postgresql-admin" if engine == "postgresql" else "shared-mongodb-auth"
    )
    tls_name = (
        "shared-postgresql-tls" if engine == "postgresql" else "shared-mongodb-tls"
    )
    username = _decode(secrets[auth_name], "username").decode("ascii")
    if _USERNAME_PATTERN.fullmatch(username) is None:
        raise ValueError("invalid administrator username")
    if len(_decode(secrets[auth_name], "password")) < 32:
        raise ValueError("administrator password is too short")
    _validate_tls(engine, secrets[tls_name], now or datetime.now(timezone.utc))


class ActionModule(ActionBase):
    """Validate exact database Secret values without disclosure or mutation."""

    TRANSFERS_FILES = False

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = super().run(tmp=tmp, task_vars=task_vars)
        task_source = str(self._task.get_path()).rsplit(":", 1)[0]
        engine = _TASK_SOURCE_CONTRACTS.get(task_source)
        if engine is None or set(self._task.args) != {"secret_results"}:
            result.update(
                failed=True,
                changed=False,
                msg="SECRET_CONTRACT_GUARD: refusing non-canonical validation",
            )
            return result
        try:
            validate_secret_results(engine, self._task.args.get("secret_results"))
        except (
            TypeError,
            ValueError,
            UnicodeError,
            UnsupportedAlgorithm,
            x509.ExtensionNotFound,
        ):
            result.update(
                failed=True,
                changed=False,
                msg="SECRET_CONTRACT_GUARD: invalid database Secret value contract",
            )
            return result
        result.update(
            changed=False,
            msg="Database Secret value contract is cryptographically valid",
        )
        return result
