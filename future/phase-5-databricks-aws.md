# Phase 5: Databricks & AWS Integration

> Real cloud connectors — Unity Catalog, S3, Delta Lake, and job deployment

**Depends on:** Phase 3 (Desktop IDE), Phase 0 (Engine Extraction — connector interface)

---

## Goal

Replace simulated deployment with real cloud integration. Connect to Databricks SQL warehouses, query Unity Catalog tables, read/write Delta Lake, deploy notebooks as Databricks jobs, and integrate with AWS services (S3, Glue, Redshift). This is where PipelineGPT becomes a production tool.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  PipelineGPT Desktop IDE / CLI / API                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐      │
│  │  StackForge Engine (Python)                            │      │
│  │  ┌──────────────────────────────────────────────┐      │      │
│  │  │  Connector Layer (pluggable)                 │      │      │
│  │  │                                              │      │      │
│  │  │  ┌──────────┐  ┌────────────┐  ┌─────────┐  │      │      │
│  │  │  │ DuckDB   │  │ Databricks │  │ AWS     │  │      │      │
│  │  │  │ (local)  │  │ SQL        │  │ (S3,    │  │      │      │
│  │  │  │          │  │ Warehouse  │  │  Glue,  │  │      │      │
│  │  │  │          │  │            │  │  Redshift│  │      │      │
│  │  │  └──────────┘  └──────┬─────┘  └────┬────┘  │      │      │
│  │  └───────────────────────┼──────────────┼───────┘      │      │
│  └──────────────────────────┼──────────────┼──────────────┘      │
│                             │              │                     │
└─────────────────────────────┼──────────────┼─────────────────────┘
                              │              │
              ┌───────────────▼──────┐  ┌────▼──────────────┐
              │  Databricks          │  │  AWS               │
              │  ┌────────────────┐  │  │  ┌──────────────┐  │
              │  │ Unity Catalog  │  │  │  │ S3 Buckets   │  │
              │  │ (catalog.      │  │  │  │ (data lake)  │  │
              │  │  schema.table) │  │  │  └──────────────┘  │
              │  └────────────────┘  │  │  ┌──────────────┐  │
              │  ┌────────────────┐  │  │  │ Glue Catalog │  │
              │  │ Delta Lake     │  │  │  │ (metadata)   │  │
              │  │ (ACID tables)  │  │  │  └──────────────┘  │
              │  └────────────────┘  │  │  ┌──────────────┐  │
              │  ┌────────────────┐  │  │  │ Redshift     │  │
              │  │ Jobs / Workflows│  │  │  │ (warehouse)  │  │
              │  │ (scheduling)   │  │  │  └──────────────┘  │
              │  └────────────────┘  │  │                    │
              └──────────────────────┘  └────────────────────┘
```

---

## Requirements

### R5.1: Databricks SQL Connector

**User Story:** As a data engineer, I want to query my Databricks SQL warehouse directly from PipelineGPT, so I can build pipelines against real production data.

**Acceptance Criteria:**
- WHEN the user configures a Databricks connection (host, token, warehouse ID) THE SYSTEM SHALL establish a connection via `databricks-sql-connector`
- WHEN connected THE SYSTEM SHALL discover available catalogs, schemas, and tables via Unity Catalog
- WHEN the AI generates SQL THE SYSTEM SHALL execute it against the Databricks SQL warehouse
- WHEN queries return results THE SYSTEM SHALL convert them to Pandas DataFrames for the pipeline
- WHEN the connection fails THE SYSTEM SHALL show a clear error with troubleshooting steps
- THE CONNECTOR SHALL support connection pooling for performance

**Configuration:**
```toml
# .stackforge.toml
[connectors.databricks]
host = "adb-1234567890.cloud.databricks.com"
token = "${DATABRICKS_TOKEN}"          # Env var reference
http_path = "/sql/1.0/warehouses/abc"
catalog = "main"
schema = "default"
```

### R5.2: Unity Catalog Integration

**User Story:** As a data engineer, I want the AI to discover and query tables from Unity Catalog using the three-level namespace, so I get correct table references automatically.

**Acceptance Criteria:**
- WHEN connected to Databricks THE SYSTEM SHALL list catalogs via `SHOW CATALOGS`
- WHEN the user mentions a table THE AI SHALL use the three-level namespace: `catalog.schema.table`
- WHEN the AI generates code THE SYSTEM SHALL use proper Unity Catalog references in PySpark: `spark.read.table("catalog.schema.table")`
- WHEN column-level governance is configured THE SYSTEM SHALL enforce access by catalog/schema
- THE SYSTEM SHALL cache table schemas locally (TTL: 5 minutes) for performance
- THE SYSTEM SHALL support schema browsing in the IDE sidebar

### R5.3: Delta Lake Read/Write

**User Story:** As a data engineer, I want pipelines to read and write Delta Lake tables, so I get ACID transactions and time travel.

**Acceptance Criteria:**
- WHEN the pipeline reads from Delta THE SYSTEM SHALL generate: `spark.read.format("delta").load(path)` or `spark.read.table("catalog.schema.table")`
- WHEN the pipeline writes to Delta THE SYSTEM SHALL generate: `df.write.format("delta").mode("overwrite").save(path)`
- WHEN merge/upsert is requested THE SYSTEM SHALL generate `DeltaTable.forPath().merge()` patterns
- WHEN the user mentions "time travel" or "version" THE SYSTEM SHALL generate: `spark.read.format("delta").option("versionAsOf", n).load(path)`
- THE GENERATED CODE SHALL include partitioning (`partitionBy`), Z-ORDER optimization hints, and `OPTIMIZE` comments where appropriate

### R5.4: AWS S3 Integration

**User Story:** As a data engineer, I want to read and write data from S3 buckets in my pipelines.

**Acceptance Criteria:**
- WHEN the user mentions S3 THE AI SHALL generate S3 paths in `s3://bucket/prefix/` format
- WHEN reading from S3 THE SYSTEM SHALL generate appropriate Spark readers with format detection
- WHEN writing to S3 THE SYSTEM SHALL generate Spark writers with partitioning options
- THE SYSTEM SHALL support IAM role-based authentication (via instance profiles) — never hardcoded credentials
- THE SYSTEM SHALL support listing S3 objects for schema discovery
- THE CONNECTOR SHALL use `boto3` for S3 operations outside Spark

### R5.5: AWS Glue Catalog

**User Story:** As a data engineer, I want to query tables registered in AWS Glue Data Catalog.

**Acceptance Criteria:**
- WHEN connected to Glue THE SYSTEM SHALL discover databases and tables via the Glue API
- WHEN the AI generates PySpark code THE SYSTEM SHALL use Glue catalog references
- THE SYSTEM SHALL show Glue databases and tables in the IDE's data browser
- GOVERNANCE SHALL enforce access controls based on Glue database/table permissions

### R5.6: Redshift Connector

**User Story:** As a data engineer, I want to read from and write to Amazon Redshift in my pipelines.

**Acceptance Criteria:**
- WHEN reading from Redshift THE SYSTEM SHALL generate Spark JDBC reads with the Redshift JDBC driver
- WHEN writing to Redshift THE SYSTEM SHALL generate Spark JDBC writes or `COPY` commands
- THE CONNECTOR SHALL support temporary S3 staging for bulk operations
- THE SYSTEM SHALL show Redshift schemas and tables in the data browser

### R5.7: Databricks Job Deployment

**User Story:** As a data engineer, I want to deploy my generated pipeline as a Databricks job, so it runs on a schedule in production.

**Acceptance Criteria:**
- WHEN the user clicks "Deploy" THE SYSTEM SHALL create a Databricks notebook from the generated PySpark code
- THE DEPLOYMENT SHALL create a Databricks job with configurable:
  - Cluster type (job cluster or existing)
  - Runtime version
  - Schedule (cron expression)
  - Alerting (email on failure)
  - Retry policy
- WHEN deployment succeeds THE SYSTEM SHALL show: Job ID, notebook path, next scheduled run, and "Open in Databricks" link (real URL)
- WHEN deployment fails THE SYSTEM SHALL show the Databricks API error with remediation steps
- THE SYSTEM SHALL support dry-run deployment (validates configuration without creating resources)

**Deployment config:**
```yaml
deployment:
  workspace:
    notebook_path: /Shared/PipelineGPT/{pipeline_name}
    cluster_type: job_cluster
    runtime: "14.3.x-scala2.12"
    node_type: "i3.xlarge"
    num_workers: 2
  schedule:
    cron: "0 0 8 * * ?"    # Daily at 8 AM
    timezone: "America/Denver"
  alerting:
    on_failure: ["team@company.com"]
    on_duration_exceeded: 3600  # seconds
  delta_output:
    catalog: main
    schema: pipelines
    table: "{pipeline_name}_output"
```

### R5.8: Connection Manager

**User Story:** As a user, I want to manage multiple cloud connections from the IDE, so I can switch between environments.

**Acceptance Criteria:**
- THE IDE SHALL provide a "Connections" panel for managing data source connections
- THE SYSTEM SHALL support multiple named connections (e.g., "Dev Databricks", "Prod Databricks", "Data Lake S3")
- WHEN a connection is selected THE SYSTEM SHALL switch the active data source
- CONNECTION CREDENTIALS SHALL be stored securely (OS keychain via Tauri's secure storage)
- THE SYSTEM SHALL support connection testing ("Test Connection" button)
- THE SYSTEM SHALL show connection health status (connected/disconnected/error) in the status bar

---

## Governance Extensions

### Catalog Access Control
```python
# Extend governance to support Unity Catalog access rules
CATALOG_ACCESS = {
    "admin": {
        "allowed_catalogs": ["*"],     # All catalogs
        "allowed_schemas": ["*"],      # All schemas
    },
    "analyst": {
        "allowed_catalogs": ["main", "analytics"],
        "allowed_schemas": ["*"],
        "blocked_schemas": ["admin", "security"],
    },
    "viewer": {
        "allowed_catalogs": ["main"],
        "allowed_schemas": ["reporting", "dashboards"],
    },
}
```

### PII Column Masking in Databricks
When PII is detected and the role requires masking, the generated code includes:
```python
# Auto-generated masking for PII columns
from pyspark.sql.functions import sha2, lit, concat
df = df.withColumn("email", sha2(col("email"), 256))
df = df.withColumn("phone", lit("***-***-****"))
df = df.withColumn("ssn", lit("***-**-****"))
```

---

## Success Criteria

- [ ] Databricks SQL connector executes queries and returns results
- [ ] Unity Catalog browser shows catalogs → schemas → tables
- [ ] AI generates correct three-level namespace references
- [ ] Delta Lake read/write/merge code generation works
- [ ] S3 read/write with proper IAM authentication
- [ ] Databricks job deployment creates a real notebook and job
- [ ] Connection credentials stored securely in OS keychain
- [ ] Governance enforces catalog/schema access by role
- [ ] PII masking code is auto-generated in PySpark output
