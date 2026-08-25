# Reactive Resume DEV object-storage source and ownership check

## Status

This is a **historical/recovery source record and read-only ownership check**, not
an active runtime owner. The exact eight-manifest SeaweedFS/S3 closure is retained
under
`ansible/files/components/reactive-resume-object-storage-history/` because the
current Argo workload revision does not contain those shared-services manifests.
No task in this lane creates, patches, deletes, syncs, adopts, or reconciles a
Kubernetes object, PVC, Secret, or Argo Application.

The current private DEV Argo Application is revision
`dd7d4cedd902e68266d9713d1dbb8e90f0b529b1`, with pruning and empty applications
disabled. The source check reads object metadata plus normalized non-secret full
specs and ConfigMap data required for exact source comparison. Secret custody
and alternate-producer checks use the Kubernetes PartialObjectMetadata media
type, so no Secret data or stringData is requested or returned; Secret values or PVC contents are never queried. It requires all eight historical source
identities in repository custody, while only seven non-secret runtime
identities are required live. The historical InfisicalStaticSecret source
record is intentionally absent live; live Secret custody is checked separately
by metadata only, without an InfisicalStaticSecret apply or adoption path. The live objects retain Ansible
ownership labels, while exact Argo tracking markers are absent; this proves
that handoff is not established rather than treating a desired-owner label as
ownership. The current Argo Application is checked separately and must contain
exactly its seven `cristexhub-dev` resources, with no `shared-services`
resource. A live Argo-tracked object is evidence of an ownership boundary,
never permission to reopen an Ansible apply path.

## Exact historical source closure

The source record contains exactly eight value-free objects in `shared-services`:

- one `InfisicalStaticSecret` for `reactive-resume-object-storage-auth`;
- three NetworkPolicies: default deny, DEV application ingress on TCP 8333, and
  DNS egress to kube-dns on TCP/UDP 53;
- one tokenless ServiceAccount;
- one ConfigMap containing the SeaweedFS S3 identity/bucket policy template;
- one private ClusterIP Service on port 8333;
- one one-replica StatefulSet with a retained `local-path` 20Gi volume template.

The StatefulSet uses the immutable SeaweedFS `4.44` image digest recorded in the
manifest. TLS is referenced through the precreated
`reactive-resume-object-storage-tls` Secret; credentials are projected by the
InfisicalStaticSecret from `/reactive-resume/dev/runtime`. No secret values are
present in this source record.

The manifest ledger is `MANIFESTS.sha256`; the read-only role verifies its exact
bytes and verifies the complete history-tree file, directory, and symlink
inventory at runtime. Every leaf is checked for exact bytes, regular-file
status, owner, and mode. The StatefulSet's volume template is historical source
only and is not a request to create or replace the live PVC.

## Bound current/source differences

The current repository contains only
`ansible/files/components/reactive-resume-dev-networkpolicy/network/reactive-resume-object-storage-allow-dev.yaml`.
The check binds its exact current SHA-256 and records these intentional
source differences rather than silently normalizing them:

- the current leaf has component label `reactive-resume-dev-networkpolicy`, while
  the historical closure uses `object-storage`;
- the current leaf has source annotations identifying `reactive-resume-dev` and
  port `8333`, while the historical leaf has no annotations;
- the current application selector includes `app.kubernetes.io/part-of:
  cristexhub`, while the historical source intentionally carries only the app
  name selector;
- the historical closure adds the missing default-deny and DNS policies plus
  runtime/auth source; this record does not authorize their creation or imply
  that an Argo handoff has occurred.

The check reads the current StatefulSet, Service, ServiceAccount, ConfigMap,
and NetworkPolicy identities and requires every runtime identity to be present
exactly once with the reviewed object-storage name, Ansible ownership labels,
and no Argo tracking annotation/instance label. It records the historical
InfisicalStaticSecret identity as an absent source-only object and checks the
separate live Secret custody metadata. It compares normalized full specs and
ConfigMap data (using the current DEV policy leaf where the source intentionally
differs). Foreign, absent, duplicate, or Argo-tracked identities fail closed.
The metadata inventory records ownerReferences, managedFields provenance,
finalizers, deletion timestamps, and alternate producer identities; any foreign
owner, producer, or pending deletion fails closed. Secret values, PVC data, and
object contents are never queried.

## Read-only entrypoint

Run only the non-passthrough check entrypoint:

```text
ansible/bin/check-reactive-resume-object-storage-source check
```

The wrapper requires the canonical controller, one `crtxweb` host, a private
single-use attestation, `--check --diff`, and the clean environment. It has no
`apply` mode. Direct playbook invocation, task selection, passthrough arguments,
Argo sync, Helm, `kubectl apply`, PVC mutation, and deletion are outside this
lane and must remain blocked.

## Remaining gates and risks

This source check does not prove SeaweedFS data inventory, bucket policy,
encryption/versioning, anonymous denial, cross-environment isolation, backup
correlation, object checksums/readback, or isolated restore. The application
upload/MIME/disposition/delete review remains separate. Existing live labels,
UIDs, managed fields, image provenance, retained PVC contents, and Argo source
lineage must be reviewed before any future source adaptation. Any future runtime
handoff requires a separate exact Argo source closure, adoption/sync evidence,
backup/recovery acceptance, and explicit approval; this task provides none.
