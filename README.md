# ☁️ CloudForge — Cloud-Native ETL & Data Quality Pipeline

> A production-grade, cloud-aware ETL pipeline with automated data validation, column profiling, multi-layer AWS S3 storage, and a real-time Streamlit analytics dashboard.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Pipeline Flow](#pipeline-flow)
- [Supported Sources](#supported-sources)
- [AWS S3 Layer System](#aws-s3-layer-system)
- [Data Validation Engine](#data-validation-engine)
- [Data Profiler](#data-profiler)
- [Metadata & Pipeline History](#metadata--pipeline-history)
- [Streamlit Dashboard](#streamlit-dashboard)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
- [Output Artifacts](#output-artifacts)
- [Tech Stack](#tech-stack)

---

## Overview

**CloudForge** is a modular, end-to-end ETL pipeline built for real-world data engineering workflows. It ingests data from multiple sources (CSV, Excel, JSON, Parquet, SQLite, MySQL, PostgreSQL), validates and transforms it, profiles every column, and uploads the data across three structured AWS S3 storage layers — all with full metadata tracking and a live operational dashboard.

It is designed to reflect production analytics engineering practices: modular architecture, layered cloud storage, structured failure handling, and an observable pipeline with logs and run history.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CloudForge Pipeline                     │
│                                                             │
│  Source Input                                               │
│  CSV / Excel / JSON / Parquet / SQLite / MySQL / PostgreSQL │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────┐   ┌────────────┐   ┌───────────┐              │
│  │ EXTRACT │ → │  VALIDATE  │ → │ TRANSFORM │              │
│  └─────────┘   └────────────┘   └───────────┘              │
│       │               │               │                     │
│       ▼               ▼               ▼                     │
│  RAW S3 Layer   Validation      PROFILE + LOAD              │
│  (raw/)         Report JSON     STAGING → PROCESSED         │
│                                       │                     │
│                               ┌───────────────┐            │
│                               │  AWS S3 Layers │            │
│                               │  raw/          │            │
│                               │  staging/      │            │
│                               │  processed/    │            │
│                               │  archive/      │            │
│                               └───────────────┘            │
│                                                             │
│  Metadata JSON + Pipeline History → Streamlit Dashboard     │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

- **Universal Source Ingestion** — Auto-detects source type from file extension or connection string. Supports 8 source types out of the box.
- **3-Stage Validation Engine** — Schema validation, datatype validation, and configurable business rule validation with structured JSON reports.
- **Automated Column Profiler** — Generates per-column statistics (nulls, uniques, min/max/mean/std for numerics, top value/avg length for text).
- **AWS S3 Multi-Layer Storage** — Uploads data at each pipeline stage: raw, staging, processed, and archive layers with enterprise-style timestamped filenames.
- **Structured Failure Handling** — Every failure produces a metadata record with stage, reason, run ID, and debug context. Failures never crash silently.
- **Pipeline Health Scoring** — Each run gets a health score (0–100) based on execution time, validation outcome, and rows processed.
- **Run Metadata & History** — Every pipeline run writes a JSON metadata file and appends to a master `pipeline_history.json`.
- **Colour-Coded Console Logging** — `colorlog`-powered logs with file persistence under `logs/`.
- **Streamlit Dashboard** — Live operational dashboard with pipeline execution, run history, validation report viewer, column profiling, S3 snapshot, and execution log viewer.
- **Multi-format Output** — Outputs processed datasets as CSV (default) or Parquet with Snappy compression.

---

## Project Structure

```
cloudforge/
│
├── main.py                  # CLI entry point — runs pipeline directly
├── dashboard.py             # Streamlit dashboard app
│
├── etl.py                   # Core ETL engine (Extract, Transform, Load)
├── validator.py             # 3-stage data validation engine
├── profiler.py              # Per-column data profiler
├── s3_handler.py            # AWS S3 multi-layer upload/archive/delete
├── metadata_manager.py      # Pipeline metadata + history manager
├── logger.py                # Coloured console + file logger
├── utils.py                 # Config loader, env helpers, data utilities
│
├── config/
│   └── pipeline_config.json # Pipeline settings + S3 layer paths
│
├── data/
│   └── sales_data.csv       # Sample input dataset
│
├── output/                  # Processed output files (CSV / Parquet)
├── staging/                 # Pre-transform staging snapshots
├── metadata/                # Per-run JSON metadata + pipeline_history.json
├── profiling/               # Per-run column profile JSON files
├── validation_reports/      # Per-run validation report JSON files
├── logs/                    # Daily rotating pipeline log files
│
├── .env                     # AWS credentials (not committed)
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Pipeline Flow

Every `run_pipeline()` call executes these steps in order:

| Step | Stage | Description |
|------|-------|-------------|
| 1 | **RAW Upload** | Uploads original source file to `s3://bucket/raw/` before any processing |
| 2 | **Extract** | Reads source into a pandas DataFrame using auto-detected reader |
| 3 | **Validate** | Runs schema, datatype, and business rule checks; fails fast on empty datasets |
| 4 | **Staging Save + Upload** | Saves pre-transform snapshot locally and uploads to `s3://bucket/staging/` |
| 5 | **Transform** | Standardises column names, fills nulls, adds `_pipeline_source`, `_processed_at`, `_row_id` columns |
| 6 | **Profile** | Generates per-column statistics for the transformed dataset |
| 7 | **Load + Processed Upload** | Saves final output as CSV or Parquet; uploads to `s3://bucket/processed/` |
| 8 | **Metadata Save** | Writes run metadata JSON + appends to master history file |

If any step fails, `_fail_pipeline()` is called — it generates a failure metadata record and returns a structured failure dict with `run_id`, `stage`, `reason`, and `debug_info`. The pipeline never raises unhandled exceptions to the caller.

---

## Supported Sources

| Source Type | Format / Connection |
|-------------|---------------------|
| CSV | `.csv` file path |
| Excel | `.xlsx` / `.xls` file path |
| JSON | `.json` file path |
| Parquet | `.parquet` file path |
| SQLite | `sqlite:///path/to/db` |
| MySQL | `mysql+pymysql://user:pass@host:3306/db` |
| PostgreSQL | `postgresql+psycopg2://user:pass@host:5432/db` |
| DataFrame | Pass a `pd.DataFrame` directly |

Source type is auto-detected from the file extension or connection string prefix. You can also pass `source_type` explicitly to override detection.

---

## AWS S3 Layer System

CloudForge implements a **4-layer data lake architecture** on S3:

```
s3://your-bucket/
├── raw/          ← Original source files (untouched)
├── staging/      ← Post-validation, pre-transform snapshots
├── processed/    ← Final transformed output files
└── archive/      ← Archived files moved from other layers
```

All files uploaded to S3 receive enterprise-style timestamped filenames:

```
20240615_143022_sales_data.csv
```

Layer paths are configurable in `config/pipeline_config.json` under the `s3.layers` key.

---

## Data Validation Engine

`validator.py` runs three validation stages on every dataset:

### 1. Schema Validation
Checks that all expected columns are present and no unexpected extra columns exist. Produces a list of `missing_columns` and `extra_columns`.

### 2. Datatype Validation
Compares actual pandas dtype of each column against an expected dtype map. Reports mismatches per column.

### 3. Business Rule Validation
Applies configurable row-level rules per column:

| Rule syntax | Meaning |
|-------------|---------|
| `>= 0` | Column value must be ≥ 0 |
| `> 100` | Column value must be > 100 |
| `email` | Column must contain `@` |

Failed rows are counted per rule. All rules are optional — if no rules are provided, this stage passes automatically.

### Validation Report Output

Each run saves a JSON report to `validation_reports/validation_report_{run_id}.json`:

```json
{
    "run_id": "20240615143022",
    "status": "failed",
    "stage": "validation",
    "row_count": 1500,
    "duplicate_rows": 3,
    "schema_valid": false,
    "missing_columns": ["email"],
    "datatype_valid": true,
    "business_rules_valid": false,
    "business_rule_failures": {
        "salary": { "rule": ">= 0", "failed_rows": 12 }
    },
    "overall_validation_status": false,
    "failure_reason": "schema_mismatch"
}
```

---

## Data Profiler

`profiler.py` generates a per-column statistical profile of the transformed dataset.

**Numeric columns:** min, max, mean, median, std deviation, null count, null %, unique count

**Text columns:** top value (mode), average string length, null count, null %, unique count

Profile saved to `profiling/profile_{run_id}.json`:

```json
{
    "run_id": "20240615143022",
    "status": "success",
    "row_count": 1500,
    "column_count": 8,
    "columns": {
        "salary": {
            "dtype": "float64",
            "null_count": 0,
            "null_percent": 0.0,
            "unique_count": 842,
            "min": 15000.0,
            "max": 250000.0,
            "mean": 72400.5,
            "median": 65000.0,
            "std": 41200.3
        }
    }
}
```

---

## Metadata & Pipeline History

Every pipeline run produces two metadata artefacts:

**1. Individual run file** → `metadata/metadata_{run_id}.json`

```json
{
    "pipeline_run_id": "20240615143022",
    "processed_at": "2024-06-15 14:30:22",
    "pipeline_status": "success",
    "source": "data/sales_data.csv",
    "source_type": "csv",
    "rows_processed": 1500,
    "columns": ["id", "name", "salary"],
    "column_count": 3,
    "validation_passed": true,
    "output_file": "output/processed_sales_data_20240615143022.csv",
    "execution_time_seconds": 4.21,
    "health_score": 100,
    "estimated_processing_cost": 0.015
}
```

**Health score logic:**

| Condition | Deduction |
|-----------|-----------|
| Execution time > 10 seconds | −20 |
| Validation failed | −40 |
| Zero rows processed | −30 |

**2. Master history file** → `metadata/pipeline_history.json`
Appends every run (success and failure) for full audit history.

---

## Streamlit Dashboard

Run the dashboard with:

```bash
streamlit run dashboard.py
```

**Dashboard sections:**

| Section | Description |
|---------|-------------|
| **Pipeline Execution** | Configure source, output format, validation rules, and execute pipeline directly from the UI |
| **Pipeline Metrics** | Live KPIs — rows processed, execution time, health score, validation status |
| **Pipeline Runs History** | Filterable table of all runs with status, source type, row count, timing, and CSV export |
| **Validation Failures** | Latest validation report with missing columns, datatype issues, and business rule failures |
| **Data Quality Insights** | Preview of the latest processed dataset (up to 100 rows) with shape metrics |
| **Storage Snapshot** | Read-only view of all current S3 bucket objects |
| **Execution Logs** | Parsed log viewer with level filter (INFO / WARNING / ERROR) and raw log tail |

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- AWS account with an S3 bucket and IAM credentials (read/write access)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/cloudforge.git
cd cloudforge
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Copy the example env file and fill in your AWS credentials:

```bash
cp .env.example .env
```

Edit `.env` — see [Environment Variables](#environment-variables) section below.

### 5. Set up pipeline config

Create `config/pipeline_config.json`:

```json
{
    "s3": {
        "layers": {
            "raw":       "raw/",
            "staging":   "staging/",
            "processed": "processed/",
            "archive":   "archive/"
        }
    },
    "validation": {
        "expected_columns": ["id", "name", "salary", "department"],
        "expected_types": {
            "id":     "int64",
            "salary": "float64"
        },
        "business_rules": {
            "salary": ">= 0"
        }
    }
}
```

---

## Configuration

`config/pipeline_config.json` controls the pipeline behaviour:

| Key | Description |
|-----|-------------|
| `s3.layers.raw` | S3 prefix for raw uploads |
| `s3.layers.staging` | S3 prefix for staging uploads |
| `s3.layers.processed` | S3 prefix for final output uploads |
| `s3.layers.archive` | S3 prefix for archived files |
| `validation.expected_columns` | List of columns the dataset must contain |
| `validation.expected_types` | Dict of `{ column: dtype }` for type checking |
| `validation.business_rules` | Dict of `{ column: rule }` for row-level rules |

All validation keys are optional — if omitted, those checks are skipped and validation passes by default.

---

## Environment Variables

Create a `.env` file in the project root:

```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=ap-south-1
AWS_BUCKET_NAME=your-s3-bucket-name
```

> ⚠️ Never commit `.env` to version control. It is listed in `.gitignore`.

---

## Running the Project

### Option 1 — Run pipeline via CLI

Edit `main.py` to point to your source file, then:

```bash
python main.py
```

### Option 2 — Run pipeline programmatically

```python
from logger import setup_logger
from utils import load_config
from etl import ETLPipeline

logger = setup_logger()
config = load_config()

pipeline = ETLPipeline(config=config, logger=logger)

# Basic CSV run
result = pipeline.run_pipeline("data/sales_data.csv")

# With validation rules
result = pipeline.run_pipeline(
    "data/sales_data.csv",
    expected_columns=["id", "name", "salary"],
    expected_types={"salary": "float64"},
    business_rules={"salary": ">= 0"},
    output_format="parquet"
)

print(result)
```

### Option 3 — Run via Streamlit dashboard

```bash
streamlit run dashboard.py
```

---

## Output Artifacts

After a successful pipeline run, the following files are generated locally:

| Location | File | Description |
|----------|------|-------------|
| `output/` | `processed_{name}_{run_id}.csv` | Final transformed dataset |
| `staging/` | `staging_{name}_{run_id}.csv` | Pre-transform snapshot |
| `metadata/` | `metadata_{run_id}.json` | Full run metadata |
| `metadata/` | `pipeline_history.json` | Master history of all runs |
| `profiling/` | `profile_{run_id}.json` | Column-level data profile |
| `validation_reports/` | `validation_report_{run_id}.json` | Validation result details |
| `logs/` | `pipeline_{YYYYMMDD}.log` | Daily rotating log file |

And on AWS S3:

| S3 Layer | Content |
|----------|---------|
| `raw/` | Original source file |
| `staging/` | Pre-transform CSV snapshot |
| `processed/` | Final output file (CSV or Parquet) |

---

## Tech Stack

| Category | Technology |
|----------|-----------|
| Language | Python 3.9+ |
| Data Processing | pandas 2.2 |
| Cloud Storage | AWS S3 via boto3 |
| Database Support | SQLAlchemy (SQLite, MySQL, PostgreSQL) |
| Dashboard | Streamlit |
| Logging | logging + colorlog |
| Config | JSON + python-dotenv |
| Output Formats | CSV, Parquet (Snappy compression) |
| Excel Support | openpyxl |

---

## Author

**Vaibhav Talekar**
Data Analyst · BI Developer

[LinkedIn](https://www.linkedin.com/in/vaibhav-talekar-37056224b/)

[Portfolio](https://vaibhav-portfolio-indol-three.vercel.app/)

---

> Built as part of a real-world analytics engineering portfolio to demonstrate end-to-end pipeline architecture, cloud integration, and production-oriented Python development.
