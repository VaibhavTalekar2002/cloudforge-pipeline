import os
import pandas as pd
import time
from metadata_manager import MetadataManager
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy import create_engine, text

from validator import DataValidator
from s3_handler import S3Handler
from profiler import DataProfiler


@dataclass(frozen=True)
class PipelineRunContext:
    run_id: str
    source: str
    source_type: str
    started_at: str


class ETLPipeline:

    # ── SUPPORTED SOURCE TYPES ──────────────────────────────
    SUPPORTED_SOURCES = [
        ".csv",
        ".xlsx",
        ".xls",
        ".json",
        ".parquet",
        "sqlite",
        "mysql",
        "postgresql"
    ]

    def __init__(self, config, logger):

        self.config = config
        self.logger = logger

        self.validator = DataValidator(config, logger)

        self.s3_handler = S3Handler(config, logger)

        self.metadata_manager = MetadataManager(logger)

    # ══════════════════════════════════════════════════════
    # EXTRACT LAYER — Universal Source Handler
    # ══════════════════════════════════════════════════════

    def extract(self, source, source_type=None, **kwargs):
        """
        Universal extract method.
        Detects source type automatically or uses provided type.

        Supported:
        - CSV  file path
        - Excel file path (.xlsx / .xls)
        - JSON  file path
        - Parquet file path
        - SQLite database path
        - MySQL connection string
        - PostgreSQL connection string
        - pandas DataFrame (pass directly)

        kwargs for SQL sources:
        - query : SQL query to run (default: SELECT * FROM table)
        - table : table name to read
        """

        self.logger.info(
            f"Starting extraction from source: {source}"
        )

        # ── AUTO DETECT SOURCE TYPE ──────────────────────
        if source_type is None:
            source_type = self._detect_source_type(source)

        self.logger.info(
            f"Detected source type: {source_type}"
        )

        # ── ROUTE TO CORRECT READER ──────────────────────
        if source_type == "csv":
            return self._read_csv(source)

        elif source_type in ["xlsx", "xls", "excel"]:
            return self._read_excel(source, **kwargs)

        elif source_type == "json":
            return self._read_json(source)

        elif source_type == "parquet":
            return self._read_parquet(source)

        elif source_type == "sqlite":
            return self._read_sqlite(source, **kwargs)

        elif source_type == "mysql":
            return self._read_sql(source, **kwargs)

        elif source_type == "postgresql":
            return self._read_sql(source, **kwargs)

        elif source_type == "dataframe":
            self.logger.info("Source is already a DataFrame")
            return source

        else:
            raise ValueError(
                f"Unsupported source type: {source_type}\n"
                f"Supported: {self.SUPPORTED_SOURCES}"
            )


    # ══════════════════════════════════════════════════════
    # SOURCE TYPE DETECTOR
    # ══════════════════════════════════════════════════════

    def _detect_source_type(self, source):
        """
        Auto-detects source type from file extension
        or connection string prefix.
        """

        # If it's already a DataFrame
        if isinstance(source, pd.DataFrame):
            return "dataframe"

        source_str = str(source).lower()

        # Database connection strings
        if source_str.startswith("sqlite:///"):
            return "sqlite"
        elif source_str.startswith("mysql"):
            return "mysql"
        elif source_str.startswith("postgresql") or source_str.startswith("postgres"):
            return "postgresql"

        # File extensions
        _, ext = os.path.splitext(source_str)

        ext_map = {
            ".csv":     "csv",
            ".xlsx":    "xlsx",
            ".xls":     "xls",
            ".json":    "json",
            ".parquet": "parquet"
        }

        if ext in ext_map:
            return ext_map[ext]

        raise ValueError(
            f"Cannot detect source type for: {source}\n"
            f"Please provide source_type manually."
        )


    # ══════════════════════════════════════════════════════
    # FILE READERS
    # ══════════════════════════════════════════════════════

    def _read_csv(self, file_path):
        """Read CSV file."""

        self._validate_file_exists(file_path)

        self.logger.info(f"Reading CSV: {file_path}")

        df = pd.read_csv(
            file_path,
            encoding="utf-8",
            on_bad_lines="skip"
        )

        self.logger.info(
            f"CSV loaded: {len(df):,} rows x {len(df.columns)} columns"
        )

        return df


    def _read_excel(self, file_path, sheet_name=0, **kwargs):
        """Read Excel file (.xlsx or .xls)."""

        self._validate_file_exists(file_path)

        self.logger.info(
            f"Reading Excel: {file_path} | Sheet: {sheet_name}"
        )

        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine="openpyxl" if str(file_path).endswith(".xlsx") else "xlrd"
        )

        self.logger.info(
            f"Excel loaded: {len(df):,} rows x {len(df.columns)} columns"
        )

        return df


    def _read_json(self, file_path):
        """Read JSON file."""

        self._validate_file_exists(file_path)

        self.logger.info(f"Reading JSON: {file_path}")

        df = pd.read_json(file_path)

        self.logger.info(
            f"JSON loaded: {len(df):,} rows x {len(df.columns)} columns"
        )

        return df


    def _read_parquet(self, file_path):
        """Read Parquet file."""

        self._validate_file_exists(file_path)

        self.logger.info(f"Reading Parquet: {file_path}")

        df = pd.read_parquet(file_path)

        self.logger.info(
            f"Parquet loaded: {len(df):,} rows x {len(df.columns)} columns"
        )

        return df


    # ══════════════════════════════════════════════════════
    # DATABASE READERS
    # ══════════════════════════════════════════════════════

    def _read_sqlite(self, db_path, table=None, query=None, **kwargs):
        """
        Read from SQLite database.

        Usage:
        - provide table name  : reads full table
        - provide SQL query   : runs custom query
        """

        self._validate_file_exists(db_path)

        conn_string = f"sqlite:///{db_path}"

        self.logger.info(
            f"Connecting to SQLite: {db_path}"
        )

        engine = create_engine(conn_string)

        with engine.connect() as conn:

            if query:
                self.logger.info(f"Running query: {query}")
                df = pd.read_sql(text(query), conn)

            elif table:
                self.logger.info(f"Reading table: {table}")
                df = pd.read_sql_table(table, conn)

            else:
                # List all tables and read first one
                tables = pd.read_sql(
                    text("SELECT name FROM sqlite_master WHERE type='table'"),
                    conn
                )

                if tables.empty:
                    raise ValueError("No tables found in SQLite database")

                first_table = tables["name"].iloc[0]
                self.logger.info(
                    f"No table specified. Reading first table: {first_table}"
                )
                df = pd.read_sql_table(first_table, conn)

        self.logger.info(
            f"SQLite loaded: {len(df):,} rows x {len(df.columns)} columns"
        )

        return df


    def _read_sql(self, connection_string, table=None, query=None, **kwargs):
        """
        Read from MySQL or PostgreSQL database.

        connection_string examples:
        MySQL:      mysql+pymysql://user:password@host:3306/dbname
        PostgreSQL: postgresql+psycopg2://user:password@host:5432/dbname
        """

        self.logger.info(
            f"Connecting to SQL database..."
        )

        engine = create_engine(connection_string)

        with engine.connect() as conn:

            if query:
                self.logger.info(f"Running query: {query}")
                df = pd.read_sql(text(query), conn)

            elif table:
                self.logger.info(f"Reading table: {table}")
                df = pd.read_sql_table(table, conn)

            else:
                raise ValueError(
                    "Please provide either 'table' or 'query' for SQL sources"
                )

        self.logger.info(
            f"SQL loaded: {len(df):,} rows x {len(df.columns)} columns"
        )

        return df


    # ══════════════════════════════════════════════════════
    # TRANSFORM LAYER
    # ══════════════════════════════════════════════════════

    def transform(self, df):
        """
        Apply standard transformations to any dataset.
        Works regardless of source type.
        """

        df = df.copy()

        self.logger.info("Starting data transformation")

        # Standardize column names
        df.columns = [
            col.strip().lower().replace(" ", "_")
            for col in df.columns
        ]

        # Fill numeric nulls with 0
        numeric_cols = df.select_dtypes(include="number").columns
        df[numeric_cols] = df[numeric_cols].fillna(0)

        # Fill text nulls with Unknown
        text_cols = df.select_dtypes(include="object").columns
        df[text_cols] = df[text_cols].fillna("Unknown")

        # Add pipeline metadata
        df["_pipeline_source"]    = "CloudForge"
        df["_processed_at"]       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df["_row_id"]             = range(1, len(df) + 1)

        self.logger.info(
            f"Transformation complete: {len(df):,} rows processed"
        )

        return df


    # ══════════════════════════════════════════════════════
    # LOAD LAYER — Multi-format output
    # ══════════════════════════════════════════════════════

         # ══════════════════════════════════════════════════════
    # LOAD LAYER — Multi-format output
    # ══════════════════════════════════════════════════════

    def load(self, df, source, output_format="csv", run_id=None):
        """
        Save transformed dataset.
        Supports CSV and Parquet output formats.
        Generates enterprise-style output filenames.
        """

        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        # ── TIMESTAMP ─────────────────────────────
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # ── EXTRACT ORIGINAL FILE NAME ───────────
        original_filename = os.path.basename(str(source))

        # Remove extension
        base_name = os.path.splitext(original_filename)[0]

        # Clean name
        base_name = (
            base_name
            .replace(" ", "_")
            .replace("-", "_")
            .lower()
        )

        # ── FINAL OUTPUT FILE NAME ───────────────
        output_filename = (
            f"processed_{base_name}_{run_id or timestamp}.{output_format}"
        )

        output_file = os.path.join(output_dir, output_filename)

        # ── SAVE FILE ────────────────────────────
        if output_format == "parquet":

            df.to_parquet(
                output_file,
                index=False,
                compression="snappy"
            )

            self.logger.info(
                f"Saved Parquet output: {output_file}"
            )

        else:

            df.to_csv(
                output_file,
                index=False
            )

            self.logger.info(
                f"Saved CSV output: {output_file}"
            )

        return output_file

    # ══════════════════════════════════════════════════════
    # PIPELINE RUNNER
    # ══════════════════════════════════════════════════════

    def run_pipeline(
        self,
        source,
        source_type=None,
        output_format="csv",
        **kwargs
    ):
        """
        Execute complete ETL pipeline.
        """

        self.logger.info("=" * 50)
        self.logger.info("CloudForge ETL Pipeline — Starting")
        self.logger.info("=" * 50)
        start_time = time.time()
        resolved_source_type = source_type or self._detect_source_type(source)
        context = PipelineRunContext(
            run_id=datetime.now().strftime("%Y%m%d%H%M%S%f"),
            source=str(source),
            source_type=resolved_source_type,
            started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        profiler = DataProfiler(self.logger)

        # ─────────────────────────────────────────────
        # STEP 1 — Upload RAW source file
        # ─────────────────────────────────────────────

        raw_s3_uri = None

        if os.path.exists(str(source)):

            raw_s3_uri = self.s3_handler.upload_raw_file(source)

            self.logger.info(
                f"RAW layer upload complete: {raw_s3_uri}"
            )

        # ─────────────────────────────────────────────
        # STEP 2 — Extract
        # ─────────────────────────────────────────────

        df = self.extract(source, resolved_source_type, **kwargs)

        if df.empty:
            return self._fail_pipeline(
                context=context,
                stage="etl",
                reason="empty_dataset",
                start_time=start_time,
                debug_info={
                    "checkpoint": "extract",
                    "rows_processed": 0
                }
            )

        # ─────────────────────────────────────────────
        # STEP 3 — Validate
        # ─────────────────────────────────────────────

        df, validation_status = self.validator.validate_dataset(

    df,

    expected_columns=kwargs.get(
        "expected_columns"
    ),

    expected_types=kwargs.get(
        "expected_types"
    ),

    business_rules=kwargs.get(
        "business_rules"
    ),

    run_id=context.run_id
)

        if not validation_status:
            validation_results = self.validator.last_validation_results or {}

            return self._fail_pipeline(
                context=context,
                stage="validation",
                reason=validation_results.get(
                    "failure_reason",
                    "validation_failure"
                ),
                start_time=start_time,
                debug_info={
                    "validation_report": validation_results.get("report_file"),
                    "validation_results": validation_results
                },
                columns=list(df.columns)
            )

        # ─────────────────────────────────────────────
        # STEP 4 — Save STAGING file
        # ─────────────────────────────────────────────

        staging_dir = "staging"

        os.makedirs(staging_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        source_name = os.path.splitext(
            os.path.basename(str(source))
        )[0]

        staging_file = os.path.join(
            staging_dir,
            f"staging_{source_name}_{context.run_id}.csv"
        )

        df.to_csv(staging_file, index=False)

        # Upload STAGING layer

        staging_s3_uri = self.s3_handler.upload_staging_file(
            staging_file
        )

        self.logger.info(
            f"STAGING layer upload complete: {staging_s3_uri}"
        )

        # ─────────────────────────────────────────────
        # STEP 5 — Transform
        # ─────────────────────────────────────────────

        df = self.transform(df)

        if df.empty:
            return self._fail_pipeline(
                context=context,
                stage="etl",
                reason="empty_dataset",
                start_time=start_time,
                debug_info={
                    "checkpoint": "transform",
                    "rows_processed": 0
                },
                columns=list(df.columns)
            )

        profile = profiler.generate_profile(
            df,
            run_id=context.run_id,
            validation_status=validation_status
        )

        if profile.get("status") == "failed":
            return self._fail_pipeline(
                context=context,
                stage="profiler",
                reason=profile.get("reason", "profiling_failure"),
                start_time=start_time,
                debug_info=profile.get("debug_info", {}),
                columns=list(df.columns)
            )

        profile_file = profiler.save_profile(
            profile,
            run_id=context.run_id
        )

        # ─────────────────────────────────────────────
        # STEP 6 — Load final processed file
        # ─────────────────────────────────────────────

        output_file = self.load(
            df,
            source,
            output_format,
            run_id=context.run_id
        )

        # Upload PROCESSED layer

        processed_s3_uri = self.s3_handler.upload_processed_file(
            output_file
        )

        self.logger.info(
            f"PROCESSED layer upload complete: {processed_s3_uri}"
        )

        self.logger.info("=" * 50)
        self.logger.info("CloudForge ETL Pipeline — Complete")
        self.logger.info("=" * 50)
        execution_time = time.time() - start_time

        metadata = self.metadata_manager.generate_metadata(
            source=source,
            source_type=resolved_source_type,
            rows_processed=len(df),
            columns=list(df.columns),
            validation_passed=validation_status,
            output_file=output_file,
            execution_time=execution_time,
            profile_file=profile_file,
            run_id=context.run_id
        )

        metadata_file = self.metadata_manager.save_metadata(metadata)

        return {
            "run_id": context.run_id,
            "status": "success",
            "source": str(source),
            "source_type": resolved_source_type,
            "output_format": output_format,
            "validation_passed": validation_status,
            "output_file": output_file,
            "rows_processed": len(df),
            "columns": list(df.columns),
            "raw_s3_uri": raw_s3_uri,
            "staging_s3_uri": staging_s3_uri,
            "processed_s3_uri": processed_s3_uri,
            "metadata_file": metadata_file
        }
    # ══════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════

    def _validate_file_exists(self, file_path):
        """Check file exists before reading."""
        if not os.path.exists(str(file_path)):
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(
                f"Source file not found: {file_path}"
            )

    def _fail_pipeline(
        self,
        context,
        stage,
        reason,
        start_time,
        debug_info=None,
        columns=None
    ):
        failure = {
            "run_id": context.run_id,
            "status": "failed",
            "stage": stage,
            "reason": reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "debug_info": debug_info or {}
        }

        self.logger.error(
            f"Pipeline failed | run_id={context.run_id} | "
            f"stage={stage} | reason={reason}"
        )

        metadata = self.metadata_manager.generate_failure_metadata(
            failure=failure,
            source=context.source,
            source_type=context.source_type,
            execution_time=time.time() - start_time,
            columns=columns or []
        )

        metadata_file = self.metadata_manager.save_metadata(metadata)
        failure["debug_info"]["metadata_file"] = metadata_file

        return failure
