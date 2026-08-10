from __future__ import annotations

import base64
import re
from datetime import datetime, timezone
from typing import Any

from ansible.plugins.action import ActionBase
from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import ExtendedKeyUsageOID

_EXPECTED_TASK_SOURCE = (
    "/Users/paul/Projects/cristexweb/ansible/roles/"
    "argocd_bootstrap/tasks/main.yml"
)
_BCRYPT_PATTERN = re.compile(r"^\$2[aby]\$12\$[./A-Za-z0-9]{53}$")
_UTC_RFC3339_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
_REQUIRED_TLS_DNS_NAMES = {
    "argocd-server.argocd.svc",
    "localhost",
}


def _decode(secret: dict[str, Any], key: str) -> bytes:
    encoded = (secret.get("data") or {}).get(key)
    if not isinstance(encoded, str):
        raise ValueError("missing Secret data")
    return base64.b64decode(encoded, validate=True)


def _require_current(certificate: x509.Certificate, now: datetime) -> None:
    if not certificate.not_valid_before_utc <= now < certificate.not_valid_after_utc:
        raise ValueError("certificate validity failure")


def validate_secret_results(secret_results: Any, now: datetime | None = None) -> None:
    if not isinstance(secret_results, list) or len(secret_results) != 3:
        raise ValueError("invalid Secret result closure")
    secrets: dict[str, dict[str, Any]] = {}
    for result in secret_results:
        resources = result.get("resources") if isinstance(result, dict) else None
        if not isinstance(resources, list) or len(resources) != 1:
            raise ValueError("invalid Secret result")
        secret = resources[0]
        name = (secret.get("metadata") or {}).get("name")
        if not isinstance(name, str) or name in secrets:
            raise ValueError("invalid Secret identity")
        secrets[name] = secret
    if set(secrets) != {"argocd-secret", "argocd-redis", "argocd-server-tls"}:
        raise ValueError("invalid Secret identity closure")

    argocd_secret = secrets["argocd-secret"]
    password_hash = _decode(argocd_secret, "admin.password").decode("ascii")
    if _BCRYPT_PATTERN.fullmatch(password_hash) is None:
        raise ValueError("invalid administrator password hash")
    password_mtime = _decode(argocd_secret, "admin.passwordMtime").decode("ascii")
    if _UTC_RFC3339_PATTERN.fullmatch(password_mtime) is None:
        raise ValueError("invalid administrator password timestamp")
    parsed_mtime = datetime.strptime(password_mtime, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    if parsed_mtime > (now or datetime.now(timezone.utc)):
        raise ValueError("administrator password timestamp is in the future")
    if len(_decode(argocd_secret, "server.secretkey")) < 32:
        raise ValueError("server signing key is too short")
    if len(_decode(secrets["argocd-redis"], "auth")) < 32:
        raise ValueError("Redis password is too short")

    tls_secret = secrets["argocd-server-tls"]
    ca_certificates = x509.load_pem_x509_certificates(_decode(tls_secret, "ca.crt"))
    leaf_certificates = x509.load_pem_x509_certificates(_decode(tls_secret, "tls.crt"))
    if not ca_certificates or len(leaf_certificates) != 1:
        raise ValueError("invalid certificate closure")
    leaf = leaf_certificates[0]
    private_key = serialization.load_pem_private_key(
        _decode(tls_secret, "tls.key"), password=None
    )
    validation_time = now or datetime.now(timezone.utc)
    _require_current(leaf, validation_time)
    leaf_constraints = leaf.extensions.get_extension_for_class(
        x509.BasicConstraints
    ).value
    if leaf_constraints.ca:
        raise ValueError("server leaf cannot be a CA")
    subject_alternative_names = leaf.extensions.get_extension_for_class(
        x509.SubjectAlternativeName
    ).value
    leaf_names = set(subject_alternative_names.get_values_for_type(x509.DNSName))
    if (
        leaf_names != _REQUIRED_TLS_DNS_NAMES
        or len(subject_alternative_names) != len(leaf_names)
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
        _require_current(certificate, validation_time)
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


class ActionModule(ActionBase):
    """Validate only the exact Argo CD Secret value contract without disclosure."""

    TRANSFERS_FILES = False

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = super().run(tmp=tmp, task_vars=task_vars)
        task_source = str(self._task.get_path()).rsplit(":", 1)[0]
        if task_source != _EXPECTED_TASK_SOURCE or set(self._task.args) != {
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
