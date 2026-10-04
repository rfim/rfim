# CDC guardrails for one tenant route

This is a **synthetic reference design**, not a deployed service or a GDPR
certification. The [shared YAML](multitenant-ingestion.yaml) gives Aurora's
Postgres CDC route a stable key, source ordering, a versioned contract, an
approved field list, and an AI advisory policy. The other tenants continue
independently when Aurora is held for review.

## Flow

1. Capture Debezium create, update, and delete events with source LSN and
   transaction ordering metadata. Use a unique source event identity including
   tenant, dataset, source, table, LSN, transaction ID, event order, and row key.
   Enable Debezium's `provide.transaction.metadata` setting for event order.
2. Record applied identities and compare `(LSN, event order)` for each row key.
   An exact replay becomes a no-op; an older event cannot overwrite newer state.
   The same source identity with different content is an integrity error, not
   a duplicate.
   Preserve a delete tombstone with the latest source position so an old update
   cannot resurrect a deleted row.
3. Compare the incoming schema with the approved contract. Hold the affected
   route on unknown, dropped, or incompatible fields. Persist held events in a
   restricted, durable quarantine **before** advancing the source checkpoint;
   otherwise a restart could lose the change. After a reviewed contract version
   is deployed, replay that tenant from its held events.
4. Apply explicit privacy controls: a purpose and field allowlist, approved
   tokenisation, tenant-scoped access, retention, deletion propagation, and
   audit logs. An AI reviewer receives only a schema-diff packet and can draft
   classification or migration suggestions. It cannot approve a contract,
   expose raw records, or release held data.
5. Apply ordered upserts/deletes to Delta using a deterministic key and source
   position. For retryable `foreachBatch` appends, use stable `txnAppId` and
   `txnVersion`; make MERGE logic idempotent too. Separate Bronze, quarantine,
   and audit writes need a deliberate replay protocol because they are not one
   cross-table transaction.

Debezium can emit duplicates while recovering from a fault; its PostgreSQL
events expose source metadata for deduplication. [Debezium PostgreSQL connector
documentation](https://debezium.io/documentation/reference/stable/connectors/postgresql.html).
Delta documents retryable batch transaction identifiers and CDC MERGE patterns:
[streaming writes](https://docs.delta.io/delta-streaming/) and
[MERGE](https://docs.delta.io/delta-update/).

## AI and privacy boundary

The AI review packet contains field names, types, the contract reference, and
the declared processing purpose. It contains no row values or credentials.
Any external model use still needs an approved provider, data handling terms,
and a review of the metadata being sent. A human owner decides whether a new
   field is necessary for the stated purpose and approves the versioned contract.
   The local demo's `approve_field` method simulates that decision; a real
   service needs authenticated approval and an immutable audit record.

UK GDPR compliance depends on the organisation's lawful basis, purpose,
retention, access controls, rights handling, and risk assessment. The ICO's
[data protection by design guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/guide-to-accountability-and-governance/data-protection-by-design-and-by-default)
and [AI data minimisation guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-should-we-assess-security-and-data-minimisation-in-ai)
explain why those controls need to be built into the processing design. A
[DPIA](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/what-is-a-dpia/)
is required when the processing is likely to be high risk.

## Run the local reference

```bash
python -m pip install -r examples/requirements.txt
python examples/cdc_guardrails_demo.py
```

The demo uses synthetic events and an in-memory SQLite transaction to show
apply, exact duplicate no-op, stale no-op, schema hold, a **mock** AI
suggestion, explicit reviewer approval, tokenised replay, and a delete
tombstone. It does not connect to Debezium, a model provider, or Delta Lake.
