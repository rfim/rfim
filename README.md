### hi, i'm vim 👋

<a href="https://rfim.github.io/nexus-73strings/"><img src="assets/nexus-data-rescue.gif" alt="Animated NEXUS architecture: two valid records continue to delivery while one invalid record branches into quarantine, is corrected, and replays" width="960"></a>

**Senior Data Engineer** in London. 10+ years building data platforms across insurance, fintech and enterprise, from Deloitte consulting to insurtech scale-ups.

I design platforms that stay trustworthy as they grow: contract-governed pipelines, medallion lakehouses, CDC and streaming ingestion, and the CI/CD and quality checks that keep them honest. Lately I've been pairing that with AI: agentic ops, self-healing pipelines, and LLM interfaces over governed data.

📍 London, UK · 🎓 MSc Computer Science (UVSQ, France) · 🧑‍🏫 Data Engineering instructor at HACKTIV8 since 2019

### NEXUS — data in motion


Three synthetic records show how valid updates keep moving while an exception waits for repair and safe replay. [Explore the interactive architecture and working code](https://rfim.github.io/nexus-73strings/).

### One YAML, many ingestion routes

<a href="https://github.com/rfim/rfim/blob/main/examples/multitenant-ingestion.yaml"><img src="assets/multitenant-ingestion.gif" alt="Animated multi-tenant ingestion design: one YAML file expands into three independently checkpointed tenant routes, each landing in Delta Bronze" width="960"></a>

One config can define each tenant's source, contract, secret reference, checkpoint, Bronze destination and quarantine path. A controller validates it, then runs each tenant and dataset route independently so one tenant can be replayed without resetting the others. [Inspect the example YAML](https://github.com/rfim/rfim/blob/main/examples/multitenant-ingestion.yaml). This is a synthetic architecture sketch.

#### CDC guardrails

<a href="https://github.com/rfim/rfim/blob/main/examples/CDC_GUARDRAILS.md"><img src="assets/cdc-guardrails.gif" alt="Animated CDC design: one event is applied, a replay becomes a no-op, and a new personal field is held while AI drafts a metadata-only suggestion for human review" width="960"></a>

In this reference design, the Postgres route handles duplicate and older events, holds schema changes for review, and keeps unapproved fields out of the curated path. An AI advisory hook receives only a schema diff; the runnable demo uses a mock suggestion, and a reviewer decides whether to change the contract. Privacy controls are explicit rules, with the wider GDPR assessment owned by the organisation.

[Inspect the CDC design and runnable reference](https://github.com/rfim/rfim/blob/main/examples/CDC_GUARDRAILS.md).

[![Play Pipeline Rush](https://img.shields.io/badge/play-Pipeline%20Rush%20%F0%9F%8E%AE-e6b422?style=for-the-badge)](https://rfim.github.io/rfim/play/)

🎮 **Pipeline Rush**: a 60-second game where you fix bad records between bronze and gold before the SLA runs out.

<a href="https://rfim.github.io/rfim/play/"><img src="play/pipeline-rush-preview.gif" alt="Animated Pipeline Rush preview: clean records reach Gold, a duplicate is fixed at the Silver gate, and a corrupt row is quarantined" width="680"></a>

---

### 🧰 Toolkit

**Platforms**<br>
<img src="https://img.shields.io/badge/Databricks-FF3621?style=flat-square&logo=databricks&logoColor=white" alt="Databricks"> <img src="https://img.shields.io/badge/Snowflake-29B5E8?style=flat-square&logo=snowflake&logoColor=white" alt="Snowflake"> <img src="https://img.shields.io/badge/BigQuery-4285F4?style=flat-square&logo=googlebigquery&logoColor=white" alt="BigQuery"> <img src="https://img.shields.io/badge/Redshift-8C4FFF?style=flat-square&logo=amazonredshift&logoColor=white" alt="Redshift"> <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL">

**Processing**<br>
<img src="https://img.shields.io/badge/Apache%20Spark-E25A1C?style=flat-square&logo=apachespark&logoColor=white" alt="Apache Spark"> <img src="https://img.shields.io/badge/dbt-FF694B?style=flat-square&logo=dbt&logoColor=white" alt="dbt"> <img src="https://img.shields.io/badge/SQL-555555?style=flat-square" alt="SQL"> <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">

**Streaming & CDC**<br>
<img src="https://img.shields.io/badge/Kafka-231F20?style=flat-square&logo=apachekafka&logoColor=white" alt="Kafka"> <img src="https://img.shields.io/badge/Pulsar-188FFF?style=flat-square&logo=apachepulsar&logoColor=white" alt="Pulsar"> <img src="https://img.shields.io/badge/Debezium-91D443?style=flat-square" alt="Debezium">

**Orchestration & ops**<br>
<img src="https://img.shields.io/badge/Airflow-017CEE?style=flat-square&logo=apacheairflow&logoColor=white" alt="Airflow"> <img src="https://img.shields.io/badge/Dagster-4F43DD?style=flat-square&logo=dagster&logoColor=white" alt="Dagster"> <img src="https://img.shields.io/badge/GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="GitHub Actions"> <img src="https://img.shields.io/badge/Terraform-844FBA?style=flat-square&logo=terraform&logoColor=white" alt="Terraform"> <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">

**Quality & governance**<br>
<img src="https://img.shields.io/badge/data%20contracts-enforced%20%E2%9C%93-2ea44f?style=flat-square&labelColor=2b3137" alt="data contracts: enforced ✓"> <img src="https://img.shields.io/badge/Great%20Expectations-all%20passing-ff6310?style=flat-square&labelColor=2b3137" alt="Great Expectations: all passing"> <img src="https://img.shields.io/badge/Unity%20Catalog-governed-FF3621?style=flat-square&labelColor=2b3137&logo=databricks&logoColor=white" alt="Unity Catalog: governed"> <img src="https://img.shields.io/badge/lineage-source%20%E2%86%92%20dashboard-6f42c1?style=flat-square&labelColor=2b3137" alt="lineage: source → dashboard">

**Modelling**<br>
<img src="https://img.shields.io/badge/Kimball-%E2%AD%90%20star%20schema-e6b422?style=flat-square&labelColor=2b3137" alt="Kimball: ⭐ star schema"> <img src="https://img.shields.io/badge/Data%20Vault-hubs%20%C2%B7%20links%20%C2%B7%20sats-0e7c86?style=flat-square&labelColor=2b3137" alt="Data Vault: hubs · links · sats"> <img src="https://img.shields.io/badge/medallion-%F0%9F%A5%89%20%E2%86%92%20%F0%9F%A5%88%20%E2%86%92%20%F0%9F%A5%87-b08d57?style=flat-square&labelColor=2b3137" alt="medallion: 🥉 → 🥈 → 🥇">

---

### 🎓 Teaching

- **Kelas Semanggi**: open source data engineering curriculum I maintain
- **HACKTIV8**: teaching Databricks, Spark, dbt and dimensional modelling to career switchers since 2019

### ✍️ Writing

Notes on data platforms and engineering on [Medium](https://medium.com/@rfim).

---

### 📫 Get in touch

[LinkedIn](https://www.linkedin.com/in/firmaninsan/) · [Medium](https://medium.com/@rfim)

Open to senior and lead data engineering roles in London and remote UK.
