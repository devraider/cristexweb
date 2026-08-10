from __future__ import annotations

import base64
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from ansible.plugins.action import ActionBase
from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID

_EXPECTED_TASK_SOURCE = (
    "/Users/paul/Projects/cristexweb/ansible/roles/"
    "argocd_bootstrap/tasks/main.yml"
)
_EXPECTED_MATERIALIZER_TASK_SOURCE = (
    "/Users/paul/Projects/cristexweb/ansible/roles/"
    "infisical_argocd_secrets_bootstrap/tasks/main.yml"
)
_TASK_SOURCE_CONTRACTS = {
    _EXPECTED_TASK_SOURCE: "argocd-bootstrap",
    _EXPECTED_MATERIALIZER_TASK_SOURCE: "infisical-materializer",
}
_BCRYPT_PATTERN = re.compile(r"^\$2[aby]\$12\$[./A-Za-z0-9]{53}$")
_UTC_RFC3339_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
_CERTIFICATE_PEM_PATTERN = re.compile(
    rb"\A-----BEGIN CERTIFICATE-----\r?\n"
    rb"(?:[A-Za-z0-9+/]{1,64}={0,2}\r?\n)+"
    rb"-----END CERTIFICATE-----\r?\n?\Z"
)
_PRIVATE_KEY_PEM_PATTERN = re.compile(
    rb"\A-----BEGIN (?P<label>PRIVATE KEY|RSA PRIVATE KEY|EC PRIVATE KEY)-----\r?\n"
    rb"(?:[A-Za-z0-9+/]{1,64}={0,2}\r?\n)+"
    rb"-----END (?P=label)-----\r?\n?\Z"
)
_REQUIRED_TLS_DNS_NAMES = {
    "argocd-server.argocd.svc",
    "localhost",
}
_MINIMUM_REMAINING_VALIDITY = timedelta(hours=24)


def _decode(secret: dict[str, Any], key: str) -> bytes:
    encoded = (secret.get("data") or {}).get(key)
    if not isinstance(encoded, str):
        raise ValueError("missing Secret data")
    return base64.b64decode(encoded, validate=True)


def _validate_bcrypt_hash(encoded_hash: bytes) -> None:
    try:
        password_hash = encoded_hash.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("administrator password hash is not ASCII") from exc
    if _BCRYPT_PATTERN.fullmatch(password_hash) is None:
        raise ValueError("invalid administrator password hash")
    # bcrypt.hashpw parses the version, cost, and salt using the pinned bcrypt
    # implementation. The plaintext is a fixed non-secret parse probe; it is
    # never related to, or emitted from, the administrator credential.
    try:
        parsed = bcrypt.hashpw(b"cristexweb-bcrypt-contract-parse-probe", encoded_hash)
    except (TypeError, ValueError) as exc:
        raise ValueError("administrator password hash is not parseable bcrypt") from exc
    if len(parsed) != 60:
        raise ValueError("administrator password hash has a noncanonical length")


def _load_exact_certificate(pem: bytes) -> x509.Certificate:
    if _CERTIFICATE_PEM_PATTERN.fullmatch(pem) is None:
        raise ValueError("certificate PEM contains residue or multiple blocks")
    try:
        return x509.load_pem_x509_certificate(pem)
    except (TypeError, ValueError, UnsupportedAlgorithm) as exc:
        raise ValueError("certificate PEM is not parseable") from exc


def _load_exact_private_key(pem: bytes) -> Any:
    if _PRIVATE_KEY_PEM_PATTERN.fullmatch(pem) is None:
        raise ValueError("private-key PEM contains residue or multiple blocks")
    try:
        return serialization.load_pem_private_key(pem, password=None)
    except (TypeError, ValueError, UnsupportedAlgorithm) as exc:
        raise ValueError("private-key PEM is not parseable or is encrypted") from exc


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


def _require_current(certificate: x509.Certificate, now: datetime) -> None:
    if not certificate.not_valid_before_utc <= now < certificate.not_valid_after_utc:
        raise ValueError("certificate validity failure")
    if certificate.not_valid_after_utc - now < _MINIMUM_REMAINING_VALIDITY:
        raise ValueError("certificate expires too soon")


def _require_certificate_signature(certificate: x509.Certificate) -> None:
    try:
        signature_hash = certificate.signature_hash_algorithm
    except UnsupportedAlgorithm as exc:
        raise ValueError("unsupported certificate signature algorithm") from exc
    if not isinstance(signature_hash, (hashes.SHA256, hashes.SHA384, hashes.SHA512)):
        raise ValueError("weak certificate signature algorithm")


def validate_secret_results(secret_results: Any, now: datetime | None = None) -> None:
    if not isinstance(secret_results, list) or len(secret_results) != 3:
        raise ValueError("invalid Secret result closure")
    secrets: dict[str, dict[str, Any]] = {}
    for result in secret_results:
        resources = result.get("resources") if isinstance(result, dict) else None
        if not isinstance(resources, list) or len(resources) != 1:
            raise ValueError("invalid Secret result")
        secret = resources[0]
        if not isinstance(secret, dict):
            raise ValueError("invalid Secret resource")
        name = (secret.get("metadata") or {}).get("name")
        if not isinstance(name, str) or name in secrets:
            raise ValueError("invalid Secret identity")
        secrets[name] = secret
    if set(secrets) != {"argocd-secret", "argocd-redis", "argocd-server-tls"}:
        raise ValueError("invalid Secret identity closure")

    validation_time = now or datetime.now(timezone.utc)
    if validation_time.tzinfo is None or validation_time.utcoffset() is None:
        raise ValueError("validation time must be timezone-aware")

    argocd_secret = secrets["argocd-secret"]
    _validate_bcrypt_hash(_decode(argocd_secret, "admin.password"))
    password_mtime = _decode(argocd_secret, "admin.passwordMtime").decode("ascii")
    if _UTC_RFC3339_PATTERN.fullmatch(password_mtime) is None:
        raise ValueError("invalid administrator password timestamp")
    parsed_mtime = datetime.strptime(password_mtime, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    if parsed_mtime > validation_time:
        raise ValueError("administrator password timestamp is in the future")
    if len(_decode(argocd_secret, "server.secretkey")) < 32:
        raise ValueError("server signing key is too short")
    if len(_decode(secrets["argocd-redis"], "auth")) < 32:
        raise ValueError("Redis password is too short")

    tls_secret = secrets["argocd-server-tls"]
    ca = _load_exact_certificate(_decode(tls_secret, "ca.crt"))
    leaf = _load_exact_certificate(_decode(tls_secret, "tls.crt"))
    private_key = _load_exact_private_key(_decode(tls_secret, "tls.key"))

    _require_strong_key(private_key)
    _require_strong_key(leaf.public_key())
    _require_strong_key(ca.public_key())
    _require_certificate_signature(leaf)
    _require_certificate_signature(ca)
    _require_current(leaf, validation_time)
    _require_current(ca, validation_time)

    leaf_constraints = leaf.extensions.get_extension_for_class(
        x509.BasicConstraints
    ).value
    if leaf_constraints.ca:
        raise ValueError("server leaf cannot be a CA")
    ca_constraints = ca.extensions.get_extension_for_class(x509.BasicConstraints).value
    if not ca_constraints.ca:
        raise ValueError("issuer is not a CA")
    try:
        ca_key_usage = ca.extensions.get_extension_for_class(x509.KeyUsage).value
    except x509.ExtensionNotFound as exc:
        raise ValueError("CA key usage is absent") from exc
    if not ca_key_usage.key_cert_sign:
        raise ValueError("CA keyCertSign usage is absent")

    if (
        leaf.not_valid_before_utc < ca.not_valid_before_utc
        or leaf.not_valid_after_utc > ca.not_valid_after_utc
    ):
        raise ValueError("leaf validity is not contained by issuer validity")

    subject_alternative_names = leaf.extensions.get_extension_for_class(
        x509.SubjectAlternativeName
    ).value
    leaf_names = {
        general_name.value
        for general_name in subject_alternative_names
        if isinstance(general_name, x509.DNSName)
    }
    if (
        len(subject_alternative_names) != len(_REQUIRED_TLS_DNS_NAMES)
        or len(leaf_names) != len(subject_alternative_names)
        or leaf_names != _REQUIRED_TLS_DNS_NAMES
    ):
        raise ValueError("server identity closure is not exact")
    extended_key_usage = leaf.extensions.get_extension_for_class(
        x509.ExtendedKeyUsage
    ).value
    if set(extended_key_usage) != {ExtendedKeyUsageOID.SERVER_AUTH}:
        raise ValueError("server authentication usage is not exact")

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

    if leaf.issuer != ca.subject:
        raise ValueError("leaf issuer is not the supplied CA")
    try:
        leaf.verify_directly_issued_by(ca)
    except (InvalidSignature, ValueError) as exc:
        raise ValueError("leaf certificate is not directly issued by the supplied CA") from exc


class ActionModule(ActionBase):
    """Validate the exact Argo CD Secret value contract without disclosure."""

    TRANSFERS_FILES = False

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = super().run(tmp=tmp, task_vars=task_vars)
        task_source = str(self._task.get_path()).rsplit(":", 1)[0]
        if task_source not in _TASK_SOURCE_CONTRACTS or set(self._task.args) != {
            "secret_results"
        }:
            result.update(
                failed=True,
                changed=False,
                msg="SECRET_CONTRACT_GUARD: refusing non-canonical validation",
            )
            return result
        try:
            validate_secret_results(self._task.args.get("secret_results"))
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
                msg="SECRET_CONTRACT_GUARD: invalid Argo CD Secret value contract",
            )
            return result
        result.update(
            changed=False,
            msg="Argo CD Secret value contract is cryptographically valid",
        )
        return result
