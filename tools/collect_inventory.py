"""Collect a bounded, sanitized, read-only local host and k3s inventory."""

from __future__ import annotations

import argparse
import getpass
import ipaddress
import json
import os
import pwd
import re
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, NamedTuple, Sequence

SCHEMA_VERSION = "1.0"
COLLECTOR_VERSION = "0.1.0"
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_OUTPUT_BYTES = 64 * 1024
LINUX_ID_MAX = (2**32) - 2
SANITIZATION_WARNING = (
    "WARNING: BEST-EFFORT SANITIZATION ONLY. Human review is required before "
    "sharing or committing this report; unknown sensitive values may remain."
)

FIXED_ENV = MappingProxyType(
    {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
    }
)


KUBECTL_PREFIX: tuple[str, ...] = ("k3s", "kubectl", "--cache-dir=")


class Check(NamedTuple):
    """One immutable, statically approved discovery command."""

    check_id: str
    description: str
    argv: tuple[str, ...]
    root_may_be_required: bool = False


# Keep this allowlist static, immutable, argument-vector based, and read-only.
CHECKS: tuple[Check, ...] = (
    Check("os_release", "Operating system release", ("cat", "/etc/os-release")),
    Check("kernel", "Kernel and machine architecture", ("uname", "-a")),
    Check("cpu", "CPU topology and capabilities", ("lscpu",)),
    Check("memory", "RAM usage in bytes", ("free", "--bytes")),
    Check(
        "block_devices",
        "Block-device and filesystem metadata",
        (
            "lsblk",
            "--bytes",
            "--fs",
            "--output",
            "NAME,TYPE,SIZE,FSTYPE,FSVER,LABEL,UUID,MOUNTPOINTS",
        ),
    ),
    Check(
        "filesystems",
        "Mounted real filesystems",
        (
            "findmnt",
            "--real",
            "--bytes",
            "--output",
            "SOURCE,TARGET,FSTYPE,SIZE,USED,AVAIL",
        ),
    ),
    Check(
        "network_links",
        "Detailed network interface and link state",
        ("ip", "-details", "link", "show"),
    ),
    Check(
        "network_addresses",
        "Detailed network interface addresses",
        ("ip", "-details", "address", "show"),
    ),
    Check(
        "routes",
        "All kernel routes",
        ("ip", "-details", "route", "show", "table", "all"),
    ),
    Check(
        "listening_tcp_ports",
        "Listening TCP sockets without process data",
        ("ss", "-lnt"),
    ),
    Check(
        "k3s_service",
        "k3s systemd service state",
        (
            "systemctl",
            "show",
            "k3s",
            "--no-pager",
            "--property=LoadState,ActiveState,SubState,UnitFileState",
        ),
    ),
    Check(
        "tailscaled_service",
        "tailscaled systemd service state",
        (
            "systemctl",
            "show",
            "tailscaled",
            "--no-pager",
            "--property=LoadState,ActiveState,SubState,UnitFileState",
        ),
    ),
    Check("k3s_version", "Installed k3s version", ("k3s", "--version")),
    Check(
        "kubectl_nodes",
        "Kubernetes nodes",
        KUBECTL_PREFIX + ("get", "nodes", "-o", "wide"),
        True,
    ),
    Check(
        "kubectl_namespaces",
        "Kubernetes namespaces",
        KUBECTL_PREFIX + ("get", "namespaces"),
        True,
    ),
    Check(
        "kubectl_pods",
        "Kubernetes pods",
        KUBECTL_PREFIX + ("get", "pods", "-A", "-o", "wide"),
        True,
    ),
    Check(
        "kubectl_services",
        "Kubernetes services",
        KUBECTL_PREFIX + ("get", "services", "-A", "-o", "wide"),
        True,
    ),
    Check(
        "kubectl_ingresses",
        "Kubernetes ingresses",
        KUBECTL_PREFIX + ("get", "ingresses", "-A", "-o", "wide"),
        True,
    ),
    Check(
        "kubectl_ingress_classes",
        "Kubernetes ingress classes",
        KUBECTL_PREFIX + ("get", "ingressclasses"),
        True,
    ),
    Check(
        "kubectl_storage_classes",
        "Kubernetes storage classes",
        KUBECTL_PREFIX + ("get", "storageclasses"),
        True,
    ),
    Check(
        "kubectl_network_policies",
        "Kubernetes NetworkPolicy objects (not enforcement proof)",
        KUBECTL_PREFIX + ("get", "networkpolicies", "-A"),
        True,
    ),
    Check(
        "kubectl_kube_system_components",
        "kube-system component indicators",
        KUBECTL_PREFIX
        + (
            "get",
            "pods,services,deployments,daemonsets",
            "-n",
            "kube-system",
            "-o",
            "wide",
        ),
        True,
    ),
    Check(
        "kubectl_dns_resources",
        "kube-system DNS resource indicators",
        KUBECTL_PREFIX
        + (
            "get",
            "pods,services,deployments",
            "-n",
            "kube-system",
            "-l",
            "k8s-app=kube-dns",
            "-o",
            "wide",
        ),
        True,
    ),
    Check(
        "kubectl_traefik_resources",
        "kube-system Traefik resource indicators",
        KUBECTL_PREFIX
        + (
            "get",
            "pods,services,deployments,daemonsets",
            "-n",
            "kube-system",
            "-l",
            "app.kubernetes.io/name=traefik",
            "-o",
            "wide",
        ),
        True,
    ),
    Check(
        "kubectl_helm_charts",
        "k3s HelmChart and HelmChartConfig objects",
        KUBECTL_PREFIX
        + ("get", "helmcharts.helm.cattle.io,helmchartconfigs.helm.cattle.io", "-A"),
        True,
    ),
    Check(
        "kubectl_workload_controllers",
        "Kubernetes workload controllers",
        (
            *KUBECTL_PREFIX,
            "get",
            "deployments,statefulsets,daemonsets,replicasets,jobs,cronjobs",
            "-A",
            "-o",
            "wide",
        ),
        True,
    ),
    Check(
        "kubectl_persistent_volumes",
        "Kubernetes persistent volumes",
        KUBECTL_PREFIX + ("get", "persistentvolumes"),
        True,
    ),
    Check(
        "kubectl_persistent_volume_claims",
        "Kubernetes persistent volume claims",
        KUBECTL_PREFIX + ("get", "persistentvolumeclaims", "-A"),
        True,
    ),
    Check(
        "datastore_directory",
        "k3s datastore directory metadata only",
        (
            "find",
            "/var/lib/rancher/k3s/server/db",
            "-mindepth",
            "1",
            "-maxdepth",
            "2",
            "-printf",
            "%y %m %u:%g %s %TY-%Tm-%TdT%TH:%TM:%TS %p\\n",
        ),
        True,
    ),
    Check(
        "etcd_snapshots",
        "k3s etcd snapshot listing",
        ("k3s", "etcd-snapshot", "ls"),
        True,
    ),
    Check(
        "nftables", "nftables ruleset", ("nft", "--numeric", "list", "ruleset"), True
    ),
    Check("ufw", "UFW firewall status", ("ufw", "status", "verbose"), True),
)


class Sanitizer:
    """Best-effort sanitizer for known sensitive textual categories."""

    _email = re.compile(
        r"(?<![\w.+-])[A-Z0-9._%+-]+@(?:LOCALHOST|[A-Z0-9-]+(?:\.[A-Z0-9-]+)*)(?![\w.-])",
        re.IGNORECASE,
    )
    _mac = re.compile(
        r"(?<![0-9A-F])(?:(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}|[0-9A-F]{4}\.[0-9A-F]{4}\.[0-9A-F]{4})(?![0-9A-F])",
        re.IGNORECASE,
    )
    _uuid = re.compile(
        r"(?<![0-9A-F])[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}(?![0-9A-F])",
        re.IGNORECASE,
    )
    _compact_filesystem_id = re.compile(
        r"(?<![0-9A-F])(?:[0-9A-F]{4}-[0-9A-F]{4}|[0-9A-F]{16})(?![0-9A-F])",
        re.IGNORECASE,
    )
    _lvm_id = re.compile(
        r"(?<![A-Z0-9])[A-Z0-9]{6}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{6}(?![A-Z0-9])",
        re.IGNORECASE,
    )
    _ipv4_candidate = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
    _ipv6_candidate = re.compile(
        r"(?<![0-9A-Fa-f:.])(?=[0-9A-Fa-f:.]*:)[0-9A-Fa-f:.]+(?:%[\w.-]+)?(?![0-9A-Fa-f:.])"
    )
    _bearer = re.compile(r"\bBearer\s+[^\s,;]+", re.IGNORECASE)
    _assignment = re.compile(
        r"\b((?:[A-Z0-9]+[-_])*(?:TOKEN|PASSWORD|PASSWD|PASS|SECRET|CLIENT[-_]SECRET|API[-_]KEY|APIKEY|ACCESS[-_]KEY|CREDENTIALS?)"
        r"(?:[-_][A-Z0-9]+)*|DATABASE[-_]URL|MONGO[-_]URL|REDIS[-_]URL)"
        r"""(\s*[:=]\s*)(?:(['"])(.*?)\3|([^\s,;]+))""",
        re.IGNORECASE,
    )

    def __init__(
        self, hostname: str = "", username: str = "", sudo_username: str = ""
    ) -> None:
        identities: list[tuple[re.Pattern[str], str]] = []
        seen: set[tuple[str, str]] = set()
        normalized_hostname = hostname.rstrip(".")
        for value, replacement in (
            (normalized_hostname, "<local-hostname>"),
            (
                normalized_hostname.split(".", 1)[0] if normalized_hostname else "",
                "<local-hostname>",
            ),
            (username, "<local-user>"),
            (sudo_username, "<sudo-user>"),
        ):
            identity = (value.casefold(), replacement)
            if value and identity not in seen:
                seen.add(identity)
                identities.append(
                    (
                        re.compile(
                            rf"(?<![A-Z0-9]){re.escape(value)}(?![A-Z0-9])",
                            re.IGNORECASE,
                        ),
                        replacement,
                    )
                )
        self._identities = tuple(identities)

    @staticmethod
    def _replace_ip(match: re.Match[str], version: int) -> str:
        candidate = match.group(0)
        address = candidate.split("%", 1)[0]
        if version == 4:
            octets = address.split(".")
            if len(octets) == 4 and all(
                octet.isascii() and octet.isdecimal() and int(octet) <= 255
                for octet in octets
            ):
                return "<ipv4>"
            return candidate
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            return candidate
        return "<ipv6>" if parsed.version == 6 else candidate

    def sanitize(self, text: str) -> str:
        value = self._bearer.sub("Bearer <redacted>", text)
        value = self._assignment.sub(
            lambda match: f"{match.group(1)}{match.group(2)}<redacted>", value
        )
        value = self._email.sub("<email>", value)
        value = self._mac.sub("<mac>", value)
        value = self._uuid.sub("<uuid>", value)
        value = self._lvm_id.sub("<lvm-id>", value)
        value = self._compact_filesystem_id.sub("<filesystem-id>", value)
        value = self._ipv6_candidate.sub(
            lambda match: self._replace_ip(match, 6), value
        )
        value = self._ipv4_candidate.sub(
            lambda match: self._replace_ip(match, 4), value
        )
        for identity, replacement in self._identities:
            value = identity.sub(replacement, value)
        return value


class _BoundedCapture:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.data = bytearray()
        self.truncated = False
        self._lock = threading.Lock()

    def read_stream(self, stream: Any) -> None:
        try:
            while True:
                chunk = stream.read(8192)
                if not chunk:
                    break
                with self._lock:
                    remaining = self.limit - len(self.data)
                    if remaining > 0:
                        self.data.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        self.truncated = True
        except (OSError, ValueError):
            # A timed-out check may close its pipe descriptor to unblock this reader.
            return

    def snapshot(self) -> tuple[str, bool]:
        with self._lock:
            text = bytes(self.data).decode("utf-8", errors="replace")
            return text, self.truncated


def _result_template(check: Check) -> dict[str, Any]:
    return {
        "description": check.description,
        "argv": list(check.argv),
        "root_may_be_required": check.root_may_be_required,
        "status": "nonzero",
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "stdout_truncated": False,
        "stderr_truncated": False,
        "duration_ms": 0,
        "error": "",
    }


def run_check(
    check: Check,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_bytes: int = MAX_OUTPUT_BYTES,
    sanitizer: Sanitizer | None = None,
) -> dict[str, Any]:
    """Execute one approved argv vector without a shell and return a fixed-shape result."""

    if timeout_seconds <= 0 or max_output_bytes <= 0:
        raise ValueError("timeout and output bounds must be positive")
    sanitizer = sanitizer or Sanitizer()
    result = _result_template(check)
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            check.argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            shell=False,
            env=dict(FIXED_ENV),
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        result["status"] = "not-found"
        result["error"] = sanitizer.sanitize(str(exc))
        result["duration_ms"] = round((time.monotonic() - started) * 1000)
        return result
    except OSError as exc:
        result["status"] = "nonzero"
        result["error"] = sanitizer.sanitize(str(exc))
        result["duration_ms"] = round((time.monotonic() - started) * 1000)
        return result

    assert process.stdout is not None
    assert process.stderr is not None
    stdout = _BoundedCapture(max_output_bytes)
    stderr = _BoundedCapture(max_output_bytes)
    readers = (
        threading.Thread(
            target=stdout.read_stream, args=(process.stdout,), daemon=True
        ),
        threading.Thread(
            target=stderr.read_stream, args=(process.stderr,), daemon=True
        ),
    )
    for reader in readers:
        reader.start()

    def terminate_process_group() -> None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        except OSError:
            try:
                process.kill()
            except ProcessLookupError:
                return

    deadline = started + timeout_seconds
    timed_out = False
    try:
        process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        timed_out = True
        terminate_process_group()
        try:
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            process.kill()

    for reader in readers:
        reader.join(timeout=max(0.0, deadline - time.monotonic()))
    if any(reader.is_alive() for reader in readers):
        timed_out = True
        terminate_process_group()
        for stream, reader in zip((process.stdout, process.stderr), readers):
            if reader.is_alive():
                try:
                    stream.close()
                except (OSError, ValueError):
                    pass
        for reader in readers:
            reader.join(timeout=0.05)

    for stream, reader in zip((process.stdout, process.stderr), readers):
        if not reader.is_alive():
            try:
                stream.close()
            except OSError:
                pass

    stdout_text, stdout_truncated = stdout.snapshot()
    stderr_text, stderr_truncated = stderr.snapshot()
    result.update(
        {
            "status": (
                "timeout"
                if timed_out
                else ("ok" if process.returncode == 0 else "nonzero")
            ),
            "returncode": process.returncode,
            "stdout": sanitizer.sanitize(stdout_text),
            "stderr": sanitizer.sanitize(stderr_text),
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "error": sanitizer.sanitize(
                f"check exceeded {timeout_seconds:g} seconds" if timed_out else ""
            ),
        }
    )
    return result


def _sanitize_value(value: Any, sanitizer: Sanitizer) -> Any:
    if isinstance(value, str):
        return sanitizer.sanitize(value)
    if isinstance(value, list):
        return [_sanitize_value(item, sanitizer) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_value(item, sanitizer) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_value(item, sanitizer) for key, item in value.items()}
    return value


def _parse_linux_id(name: str, value: str | None) -> int:
    if value is None or not value.isascii() or not value.isdecimal():
        raise ValueError(f"{name} must be an ASCII decimal Linux ID")
    normalized = value.lstrip("0") or "0"
    maximum = str(LINUX_ID_MAX)
    if len(normalized) > len(maximum) or (
        len(normalized) == len(maximum) and normalized > maximum
    ):
        raise ValueError(f"{name} exceeds the Linux ID range")
    return int(normalized)


def _sudo_owner(
    environ: Mapping[str, str], effective_uid: int
) -> tuple[int, int] | None:
    sudo_uid = environ.get("SUDO_UID")
    sudo_gid = environ.get("SUDO_GID")
    if effective_uid != 0 or (sudo_uid is None and sudo_gid is None):
        return None
    if sudo_uid is None or sudo_gid is None:
        raise ValueError("SUDO_UID and SUDO_GID must both be present")
    return _parse_linux_id("SUDO_UID", sudo_uid), _parse_linux_id("SUDO_GID", sudo_gid)


def _sudo_username(owner: tuple[int, int] | None) -> str:
    if owner is None:
        return ""
    try:
        return pwd.getpwuid(owner[0]).pw_name
    except KeyError:
        return ""


def collect_inventory(
    *,
    runner: Callable[..., dict[str, Any]] = run_check,
    now: datetime | None = None,
    hostname: str | None = None,
    username: str | None = None,
    environ: Mapping[str, str] | None = None,
    effective_uid: int | None = None,
) -> dict[str, Any]:
    """Collect all allowlisted checks; individual command failures remain results."""

    local_hostname = socket.gethostname() if hostname is None else hostname
    local_username = getpass.getuser() if username is None else username
    runtime_environ = os.environ if environ is None else environ
    runtime_uid = os.geteuid() if effective_uid is None else effective_uid
    sudo_owner = _sudo_owner(runtime_environ, runtime_uid)
    sanitizer = Sanitizer(local_hostname, local_username, _sudo_username(sudo_owner))
    timestamp = now or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)

    results: dict[str, Any] = {}
    for check in CHECKS:
        result = runner(check, sanitizer=sanitizer)
        results[check.check_id] = _sanitize_value(result, sanitizer)

    report = {
        "schema_version": SCHEMA_VERSION,
        "collector_version": COLLECTOR_VERSION,
        "collected_at_utc": timestamp.isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "privilege": {
            "effective_uid": runtime_uid,
            "is_root": runtime_uid == 0,
            "invoked_via_sudo": sudo_owner is not None,
        },
        "sanitization_warning": SANITIZATION_WARNING,
        "results": results,
    }
    return _sanitize_value(report, sanitizer)


def handoff_sudo_ownership(
    file_descriptor: int,
    *,
    environ: Mapping[str, str] | None = None,
    effective_uid: int | None = None,
) -> None:
    """Give an open output file to the invoking sudo user without following a path."""

    owner = _sudo_owner(
        os.environ if environ is None else environ,
        os.geteuid() if effective_uid is None else effective_uid,
    )
    if owner is not None:
        os.fchown(file_descriptor, owner[0], owner[1])


def write_report_atomic(
    destination: Path | str,
    report: Mapping[str, Any],
    *,
    environ: Mapping[str, str] | None = None,
    effective_uid: int | None = None,
) -> None:
    """Atomically write a mode-0600 JSON report, rejecting a symlink destination."""

    path = Path(destination)
    if os.path.lexists(path) and stat.S_ISLNK(path.lstat().st_mode):
        raise ValueError(f"refusing symlink output destination: {path}")
    parent = path.parent
    if not parent.is_dir():
        raise ValueError(f"output parent directory does not exist: {parent}")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=parent
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        payload = (
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        with os.fdopen(descriptor, "wb", closefd=False) as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        handoff_sudo_ownership(
            descriptor,
            environ=environ,
            effective_uid=effective_uid,
        )
        os.close(descriptor)
        descriptor = -1

        if os.path.lexists(path) and stat.S_ISLNK(path.lstat().st_mode):
            raise ValueError(f"refusing symlink output destination: {path}")
        os.replace(temporary_path, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def list_checks() -> list[dict[str, Any]]:
    return [
        {
            "id": check.check_id,
            "description": check.description,
            "argv": list(check.argv),
            "root_may_be_required": check.root_may_be_required,
        }
        for check in CHECKS
    ]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m tools.collect_inventory", description=__doc__
    )
    parser.add_argument(
        "--local", action="store_true", help="collect only on this local machine"
    )
    parser.add_argument(
        "--sanitized-output", type=Path, help="destination for sanitized JSON"
    )
    parser.add_argument(
        "--list-checks",
        action="store_true",
        help="list the immutable check allowlist and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    if arguments.list_checks:
        if arguments.local or arguments.sanitized_output is not None:
            parser.error("--list-checks cannot be combined with collection options")
        print(json.dumps(list_checks(), indent=2, sort_keys=True))
        return 0
    if not arguments.local or arguments.sanitized_output is None:
        parser.error("collection requires --local and --sanitized-output PATH")

    try:
        report = collect_inventory()
        write_report_atomic(arguments.sanitized_output, report)
    except (OSError, ValueError) as exc:
        print(f"collector error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
