from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any

from ansible import context
from ansible_collections.kubernetes.core.plugins.action.k8s import (
    ActionModule as KubernetesActionModule,
)

_TASK_SOURCES = {
    "/Users/paul/Projects/cristexweb/ansible/roles/shared_postgresql_provisioning/tasks/main.yml": "postgresql",
    "/Users/paul/Projects/cristexweb/ansible/roles/shared_mongodb_provisioning/tasks/main.yml": "mongodb",
}
_ARGUMENT_KEYS = {"state", "definition", "kubeconfig", "wait", "wait_timeout", "delete_options"}
_IMAGES = {
    "postgresql": "docker.io/library/postgres@sha256:dbbeb22a65db2503050cdbbe5e78f017478f10a1002a226463f049dbb017e99b",
    "mongodb": "docker.io/library/mongo@sha256:b112b1c1e552ab2b5bf5935b5662e1d19347d68effa8f2595687a42abfac5df4",
}
_SCRIPTS = {
    "postgresql": "postgresql-apply.sh",
    "mongodb": "mongodb-apply.sh",
}
_SCRIPT_HASHES = {
    "postgresql": "08a98b5796c2be31d63c6b47e391aaed741bb6620023cc22e3af6abe514cbc4a",
    "mongodb": "571301f932cd2a36d40813313c9da077380114452542cd622e0d6d379a4990f6",
}
_SECRET_NAMES = {
    "postgresql": {
        "shared-postgresql-admin",
        "shared-postgresql-tls",
        "shared-postgresql-cristexhub-dev",
        "shared-postgresql-cristexhub-prod",
        "shared-postgresql-reactive-resume-dev",
        "shared-postgresql-reactive-resume-prod",
        "shared-postgresql-keycloak",
    },
    "mongodb": {
        "shared-mongodb-auth",
        "shared-mongodb-tls",
        "shared-mongodb-cristexhub-dev",
        "shared-mongodb-cristexhub-prod",
    },
}
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _source_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "ansible" / "files" / "database-provisioning" / name


def _selected() -> bool:
    start_at_task = context.CLIARGS.get("start_at_task")
    step = bool(context.CLIARGS.get("step"))
    tags = list(context.CLIARGS.get("tags") or [])
    skip_tags = list(context.CLIARGS.get("skip_tags") or [])
    return not start_at_task and not step and tags in ([], ["all"]) and not skip_tags


def _labels(definition: dict[str, Any]) -> dict[str, str]:
    return (definition.get("metadata") or {}).get("labels") or {}


class ActionModule(KubernetesActionModule):
    """Guard only the short-lived value-free UID-bound helper Pod and NetworkPolicy.

    SECRET_ARGV_GUARD rejects any attempt to replace Secret references with inline values.
    """

    def run(
        self,
        tmp: str | None = None,
        task_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task_vars = task_vars or {}
        args = self._task.args
        task_source = str(self._task.get_path()).rsplit(":", 1)[0]
        engine = _TASK_SOURCES.get(task_source)
        if engine is None:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: refusing helper mutation outside the canonical role"}
        if not _selected():
            return {"changed": False, "failed": True, "msg": "TASK_SELECTION_GUARD: refusing helper mutation under task selection"}
        if set(args) != _ARGUMENT_KEYS:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing unmodeled helper arguments"}
        token = os.environ.get("CRISTEXWEB_SHARED_DATABASE_PROVISIONING_TOKEN", "")
        attestation_path = os.environ.get("CRISTEXWEB_SHARED_DATABASE_PROVISIONING_ATTESTATION_FILE", "")
        try:
            attestation = os.stat(attestation_path, follow_symlinks=False)
            contents = Path(attestation_path).read_text().strip()
        except (OSError, ValueError):
            attestation = None
            contents = ""
        valid_attestation = (
            os.environ.get("CRISTEXWEB_SHARED_DATABASE_PROVISIONING_ENTRYPOINT") == "v1"
            and re.fullmatch(r"[0-9a-f]{64}", token) is not None
            and attestation is not None
            and stat.S_ISREG(attestation.st_mode)
            and not stat.S_ISLNK(attestation.st_mode)
            and stat.S_IMODE(attestation.st_mode) == 0o600
            and attestation.st_uid == os.getuid()
            and contents == f"{token}:entrypoint"
        )
        binding = task_vars.get(
            "shared_postgresql_provisioning_internal_preflight_binding",
            task_vars.get(
                "shared_mongodb_provisioning_internal_preflight_binding",
                task_vars.get("shared_database_provisioning_internal_preflight_binding", {}),
            ),
        )
        valid_binding = (
            isinstance(binding, dict)
            and binding.get("attestation_sha256") == hashlib.sha256(token.encode()).hexdigest()
            and binding.get("namespace_contract") is True
            and binding.get("ready_pod_contract") is True
            and binding.get("secret_contract") is True
            and binding.get("no_delete_path") is True
        )
        approved = task_vars.get(
            "shared_postgresql_provisioning_approved",
            task_vars.get("shared_mongodb_provisioning_approved"),
        )
        if not valid_attestation or not valid_binding or approved is not True:
            return {"changed": False, "failed": True, "msg": "ENTRYPOINT_GUARD: refusing helper mutation without the validated wrapper and preflight"}
        definition = args.get("definition")
        if not isinstance(definition, dict) or args.get("kubeconfig") != "/etc/rancher/k3s/k3s.yaml":
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing helper identity drift"}
        metadata = definition.get("metadata") or {}
        if (
            definition.get("apiVersion") not in {"v1", "networking.k8s.io/v1"}
            or metadata.get("namespace") != "shared-services"
            or metadata.get("name", "").startswith("shared-") is False
            or definition.get("kind") not in {"Pod", "NetworkPolicy"}
        ):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing unknown helper object"}
        labels = _labels(definition)
        run_id = token[:24]
        expected_name = f"shared-{engine}-provision-"
        if (
            labels.get("app.kubernetes.io/managed-by") != "ansible"
            or labels.get("cristex.io/component") != "database-logical-provisioning"
            or labels.get("cristex.io/provisioning-engine") != engine
            or labels.get("cristex.io/provisioning-run") != run_id
        ):
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing helper ownership drift"}
        state = args.get("state")
        delete_options = args.get("delete_options") or {}
        if state == "absent":
            expected_delete_name = f"{expected_name}{run_id}"
            if definition["kind"] == "NetworkPolicy":
                expected_delete_name = f"{expected_name}network-{run_id}"
            preconditions = delete_options.get("preconditions") or {}
            if (
                metadata.get("name") != expected_delete_name
                or set(delete_options) != {"propagationPolicy", "preconditions"}
                or set(preconditions) != {"uid"}
                or not _UUID.fullmatch(str(preconditions.get("uid", "")))
                or delete_options.get("propagationPolicy") != "Orphan"
                or args.get("wait") is not True
                or args.get("wait_timeout") != 60
            ):
                return {"changed": False, "failed": True, "msg": "UID_DELETE_GUARD: refusing helper cleanup without an exact UID precondition"}
        elif state == "present":
            if args.get("wait") is not False or args.get("wait_timeout") != 60 or delete_options:
                return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing non-present helper mutation"}
            if definition["kind"] == "Pod":
                if metadata.get("name") != f"{expected_name}{run_id}" or not self._valid_pod(definition, engine):
                    return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing helper Pod shape or source drift"}
            elif metadata.get("name") != f"{expected_name}network-{run_id}" or not self._valid_policy(definition, engine, run_id):
                return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing helper NetworkPolicy shape or source drift"}
        else:
            return {"changed": False, "failed": True, "msg": "MUTATION_ARGUMENT_GUARD: refusing an unsupported helper state"}
        original_action = self._task.action
        self._task.action = "kubernetes.core.k8s"
        try:
            return super().run(tmp=tmp, task_vars=task_vars)
        finally:
            self._task.action = original_action

    @staticmethod
    def _valid_pod(definition: dict[str, Any], engine: str) -> bool:
        spec = definition.get("spec") or {}
        containers = spec.get("containers") or []
        if (
            spec.get("restartPolicy") != "Never"
            or spec.get("automountServiceAccountToken") is not False
            or spec.get("hostNetwork", False)
            or spec.get("hostPID", False)
            or spec.get("hostIPC", False)
            or spec.get("serviceAccountName") is not None
            or spec.get("initContainers", [])
            or len(containers) != 1
            or spec.get("volumes") is None
        ):
            return False
        pod_security = spec.get("securityContext") or {}
        container = containers[0]
        security = container.get("securityContext") or {}
        if (
            container.get("image") != _IMAGES[engine]
            or container.get("imagePullPolicy") != "IfNotPresent"
            or security.get("runAsNonRoot") is not True
            or security.get("readOnlyRootFilesystem") is not True
            or security.get("allowPrivilegeEscalation") is not False
            or security.get("capabilities", {}).get("drop") != ["ALL"]
            or pod_security.get("runAsUser") != 999
            or pod_security.get("runAsGroup") != 999
            or pod_security.get("seccompProfile", {}).get("type") != "RuntimeDefault"
        ):
            return False
        command = container.get("command") or []
        shell = "/bin/bash" if engine == "mongodb" else "/bin/sh"
        if len(command) != 3 or command[:2] != [shell, "-ec"]:
            return False
        script = _source_path(_SCRIPTS[engine])
        try:
            source = script.read_text()
        except OSError:
            return False
        if hashlib.sha256(source.encode()).hexdigest() != _SCRIPT_HASHES[engine] or command[2] != source:
            return False
        if container.get("env") not in (None, []):
            return False
        allowed_secrets = _SECRET_NAMES[engine]
        expected_tls_name = "shared-postgresql-tls" if engine == "postgresql" else "shared-mongodb-tls"
        expected_secret_volumes = {
            "postgresql": {
                "postgresql-admin": "shared-postgresql-admin",
                "postgresql-tls": "shared-postgresql-tls",
                "cristexhub-dev": "shared-postgresql-cristexhub-dev",
                "cristexhub-prod": "shared-postgresql-cristexhub-prod",
                "reactive-resume-dev": "shared-postgresql-reactive-resume-dev",
                "reactive-resume-prod": "shared-postgresql-reactive-resume-prod",
                "keycloak": "shared-postgresql-keycloak",
            },
            "mongodb": {
                "mongodb-admin": "shared-mongodb-auth",
                "mongodb-cristexhub-dev": "shared-mongodb-cristexhub-dev",
                "mongodb-cristexhub-prod": "shared-mongodb-cristexhub-prod",
                "mongodb-tls": "shared-mongodb-tls",
            },
        }[engine]
        for volume in spec.get("volumes") or []:
            if any(key in volume for key in ("persistentVolumeClaim", "hostPath", "configMap", "projected")):
                return False
            if "secret" in volume:
                secret = volume["secret"]
                if expected_secret_volumes.get(volume.get("name")) != secret.get("secretName"):
                    return False
                if secret.get("secretName") not in allowed_secrets:
                    return False
                if secret.get("secretName") == expected_tls_name:
                    if secret.get("defaultMode") != 292 or secret.get("items") != [{"key": "ca.crt", "path": "ca.crt"}]:
                        return False
                elif (
                    secret.get("defaultMode") != 288
                    or secret.get("items")
                    != [
                        {"key": "username", "path": "username"},
                        {"key": "password", "path": "password"},
                    ]
                ):
                    return False
        expected_mounts = {
            "postgresql": {
                "postgresql-admin": ("/run/database-credentials/shared-postgresql-admin", True),
                "postgresql-tls": ("/run/database-tls", True),
                "cristexhub-dev": ("/run/database-credentials/shared-postgresql-cristexhub-dev", True),
                "cristexhub-prod": ("/run/database-credentials/shared-postgresql-cristexhub-prod", True),
                "reactive-resume-dev": ("/run/database-credentials/shared-postgresql-reactive-resume-dev", True),
                "reactive-resume-prod": ("/run/database-credentials/shared-postgresql-reactive-resume-prod", True),
                "keycloak": ("/run/database-credentials/shared-postgresql-keycloak", True),
                "tmp": ("/tmp", False),
            },
            "mongodb": {
                "mongodb-admin": ("/run/database-credentials/shared-mongodb-auth", True),
                "mongodb-cristexhub-dev": ("/run/database-credentials/shared-mongodb-cristexhub-dev", True),
                "mongodb-cristexhub-prod": ("/run/database-credentials/shared-mongodb-cristexhub-prod", True),
                "mongodb-tls": ("/run/database-tls", True),
                "tmp": ("/tmp", False),
            },
        }[engine]
        mounts = {
            mount.get("name"): (mount.get("mountPath"), mount.get("readOnly", False))
            for mount in container.get("volumeMounts") or []
        }
        if mounts != expected_mounts:
            return False
        return True

    @staticmethod
    def _valid_policy(definition: dict[str, Any], engine: str, run_id: str) -> bool:
        spec = definition.get("spec") or {}
        expected_db = {
            "app.kubernetes.io/name": f"shared-{engine}",
            "app.kubernetes.io/part-of": "cristex-platform" if engine == "postgresql" else "shared-databases",
        }
        expected_helper = {
            "app.kubernetes.io/name": f"shared-{engine}-provision-helper",
            "cristex.io/database-provisioner": f"shared-{engine}",
            "cristex.io/provisioning-run": run_id,
        }
        database_port = 5432 if engine == "postgresql" else 27017
        expected_selector = {
            "matchExpressions": [
                {
                    "key": "app.kubernetes.io/name",
                    "operator": "In",
                    "values": [f"shared-{engine}", f"shared-{engine}-provision-helper"],
                }
            ]
        }
        expected_egress = [
            {
                "to": [{"podSelector": {"matchLabels": expected_db}}],
                "ports": [{"protocol": "TCP", "port": database_port}],
            },
            {
                "to": [
                    {
                        "namespaceSelector": {
                            "matchLabels": {"kubernetes.io/metadata.name": "kube-system"}
                        },
                        "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}},
                    }
                ],
                "ports": [
                    {"protocol": "UDP", "port": 53},
                    {"protocol": "TCP", "port": 53},
                ],
            },
        ]
        ingress = spec.get("ingress") or []
        return (
            spec.get("podSelector") == expected_selector
            and spec.get("policyTypes") == ["Ingress", "Egress"]
            and len(ingress) == 1
            and ingress[0].get("from") == [{"podSelector": {"matchLabels": expected_helper}}]
            and ingress[0].get("ports") == [{"protocol": "TCP", "port": database_port}]
            and spec.get("egress") == expected_egress
        )
