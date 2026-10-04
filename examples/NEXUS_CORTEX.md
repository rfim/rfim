# NEXUS Cortex: from trusted rows to trusted answers

**Status:** design concept and synthetic animation. This is not a deployed chatbot, a production semantic database, or a claim about Lifepal's existing platform.

NEXUS already has a useful starting point: tenant-scoped ingestion, contracts, CDC replay safety, quality gates, and curated data. The next layer would give that data shared business meaning. An assistant could then answer from approved definitions and show how it got there.

```text
Tenant sources → contracts + CDC → Silver entities → Gold models
                                                   ↓
                               versioned semantic definitions
                               metric · grain · joins · time · owner
                                                   ↓
Question → approved metric → tenant policy → SQL → result + evidence
```

## What gives the layer memory

The semantic registry would store five linked kinds of object:

| Object | What it records |
| --- | --- |
| Entity | Business key, grain, tenant key, owner, and approved Gold model |
| Relationship | Approved join path and cardinality between entities |
| Metric | Formula, filters, dimensions, calendar rules, and version |
| Policy | Who can request each metric, row scope, and sensitive fields |
| Lineage | Source contracts, transforms, quality checks, and freshness |

These relationships can start as versioned metadata over existing Gold tables and native catalog objects. The question planner traverses only approved links, so “paid orders by tenant” has one traceable meaning. A schema change event can traverse lineage in reverse to find affected metrics; AI may draft a revised definition, but an owner reviews it before publication. This turns the ingestion controls into a feedback loop for the semantic layer.

## One answer, end to end

The animation asks: **“How many paid orders did Aurora have last week?”** Its answer, **128**, is illustrative synthetic data.

1. Resolve “paid orders” to the approved `paid_orders` metric, rather than inventing a new calculation.
2. Bind the caller to Aurora before planning the query; a requested tenant name alone never grants access.
3. Resolve “last week” as the previous complete ISO week in the metric's declared timezone. Keep a half-open interval so midnight boundaries do not overlap.
4. Generate a parameterised query against a certified Gold model. Count distinct order IDs with `status = 'paid'`.
5. Return the number alongside metric version, SQL or query ID, data freshness, quality status, and Gold-to-source lineage.

An example semantic definition could be versioned separately from the ingestion YAML:

```yaml
metric: paid_orders
version: 1
description: Distinct orders whose current approved state is paid
owner: commerce_analytics
model: gold.orders
entity_key: order_id
tenant_key: tenant_id
time_key: paid_at
timezone: Europe/London
measure: count_distinct(order_id)
filter: "status = 'paid'"
dimensions: [tenant_id, paid_date]
quality_gate: gold_orders_current
```

The corresponding **illustrative** query for the previous ISO week at 4 October 2026 is:

```sql
SELECT COUNT(DISTINCT order_id) AS paid_orders
FROM gold.orders
WHERE tenant_id = :authorised_tenant_id
  AND status = 'paid'
  AND paid_at >= :week_start_utc
  AND paid_at < :week_end_utc;
```

The application computes `:week_start_utc` and `:week_end_utc` from the declared `Europe/London` calendar week. The caller's authorised tenant, not the text of the question, supplies `:authorised_tenant_id`.

## How I would build the first slice

| Step | Deliverable | Acceptance check |
| --- | --- | --- |
| 1. Canonical model | Tenant-scoped Gold `orders` with stable keys, state, event time, and source IDs | CDC replay and late arrivals do not change a settled result incorrectly |
| 2. Semantic contract | Reviewed definition of `paid_orders`, its grain, timezone, owner, and permitted dimensions | SQL and metric definition return the same result for a fixed fixture |
| 3. Policy + answer | Caller identity is mapped to authorised tenants before query execution | Cross-tenant question is denied even when phrased convincingly |
| 4. Evidence | Answer includes definition version, query, freshness, quality status, and lineage | A reviewer can reproduce or reject the number |
| 5. Change response | Schema/quality events identify affected metrics and suggest a revision | AI suggestions remain drafts until owner review |

The semantic contract can be mapped to [Databricks Unity Catalog metric views](https://docs.databricks.com/aws/en/uc-semantics/metric-views) for Delta-serving data, or to [Snowflake semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/overview) if a Gold product is served there. [Databricks Genie](https://docs.databricks.com/gcp/en/genie/) and [Snowflake Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) provide native natural-language interfaces to governed semantics. The application still has to enforce its caller permissions and return evidence in the user experience.

**Why this order?** The first milestone is a repeatable answer to one question, backed by one approved metric. A larger “brain” becomes useful as each new metric, entity, relation, and policy is versioned and verified.
