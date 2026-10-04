# Non-CDC self-healing for a tenant file route

This is a **synthetic reference design** for Beacon's S3 file route in the
[shared YAML](multitenant-ingestion.yaml). It demonstrates how a non-CDC file
can repair a known, low-risk formatting defect without silently accepting a
new schema or inventing business values.

## The sequence

1. Identify the object by tenant, dataset, bucket, key, and non-null S3 version
   ID. Verify a SHA-256 checksum of the bytes. A committed version with the
   same checksum is a no-op on retry; the same identity with different content
   is an integrity error. S3 versioning provides distinct IDs for versions of
   an object, and S3 supports checksums for integrity verification:
   [version IDs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/versioning-workflows.html),
   [checksums](https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html).
2. Compare the file's fields with the approved contract. An unknown column
   holds the **whole file** in a restricted location. A schema-only review
   packet can be sent to an AI advisor; it contains no row values or secrets.
   The model can suggest a classification or mapping, but cannot approve it.
3. For the known `amount` field, the sole approved repair is an exact cast from
   a numeric string with at most two decimal places to a two-place decimal.
   This is a deterministic rule. A malformed amount goes to row quarantine
   with a reason; the valid rows still land. Missing business values are never
   fabricated.
4. Commit the file manifest, accepted rows, and quarantined rows with an
   idempotent protocol. The local SQLite demo uses one transaction. In a Delta
   deployment, separate Bronze, quarantine, and manifest tables are **not**
   one cross-table transaction; each sink needs stable write identities and a
   recovery procedure. Delta supports `txnAppId` and `txnVersion` for retryable
   writes: [Delta streaming writes](https://docs.delta.io/delta-streaming/).

For API ingestion, the same idea applies to a stable request/page identity,
response checksum, approved normalisation rules, and a cursor advanced only
after the result is durably recorded. This animation shows the file route.

## Run the local reference

```bash
python -m pip install -r examples/requirements.txt
python examples/non_cdc_self_heal_demo.py
```

The demo uses synthetic NDJSON objects and in-memory SQLite. It shows one
exact repair, one row quarantine, a duplicate object no-op, rejection of a
conflicting object, and a second file held for schema review. The AI suggestion
is mocked. It does not connect to S3, Delta Lake, or a model provider.
