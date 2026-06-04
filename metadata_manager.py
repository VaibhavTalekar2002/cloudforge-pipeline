import os
import json
from datetime import datetime


class MetadataManager:

    def __init__(self, logger):

        self.logger = logger

        # Main metadata folder
        self.metadata_dir = "metadata"

        # Master history file
        self.history_file = os.path.join(
            self.metadata_dir,
            "pipeline_history.json"
        )

        os.makedirs(self.metadata_dir, exist_ok=True)

    # ══════════════════════════════════════════════════════
    # GENERATE METADATA
    # ══════════════════════════════════════════════════════

    def generate_metadata(
        self,
        source,
        source_type,
        rows_processed,
        columns,
        validation_passed,
        output_file,
        execution_time,
        pipeline_status="success",
        profile_file=None,
        run_id=None,
        failure=None
    ):

        # ── HEALTH SCORE LOGIC ─────────────────────

        health_score = 100

        if execution_time > 10:
            health_score -= 20

        if not validation_passed:
            health_score -= 40

        if rows_processed == 0:
            health_score -= 30

        # ── ESTIMATED PROCESSING COST ─────────────

        estimated_cost = round(
            rows_processed * 0.00001,
            4
        )

        # ── BUILD METADATA ────────────────────────

        metadata = {

            "pipeline_run_id":
                run_id or datetime.now().strftime("%Y%m%d_%H%M%S"),

            "processed_at":
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            "pipeline_status":
                pipeline_status,

            "source":
                str(source),

            "source_type":
                source_type,

            "rows_processed":
                rows_processed,

            "columns":
                columns,

            "column_count":
                len(columns),

            "validation_passed":
                validation_passed,

            "output_file":
                output_file,

            "execution_time_seconds":
                round(execution_time, 2),

            "health_score":
                health_score,

            "estimated_processing_cost":
                estimated_cost,

            "profile_file": profile_file,

            "failure": failure
        }

        return metadata

    def generate_failure_metadata(
        self,
        failure,
        source=None,
        source_type=None,
        execution_time=0,
        columns=None
    ):

        return self.generate_metadata(
            source=source or "",
            source_type=source_type or "",
            rows_processed=0,
            columns=columns or [],
            validation_passed=False,
            output_file="",
            execution_time=execution_time,
            pipeline_status="failed",
            profile_file=None,
            run_id=failure.get("run_id"),
            failure=failure
        )

    # ══════════════════════════════════════════════════════
    # SAVE INDIVIDUAL METADATA FILE
    # ══════════════════════════════════════════════════════

    def save_metadata(self, metadata):

        filename = (
            f"metadata_"
            f"{metadata['pipeline_run_id']}.json"
        )

        filepath = os.path.join(
            self.metadata_dir,
            filename
        )

        with open(filepath, "w") as f:

            json.dump(
                metadata,
                f,
                indent=4
            )

        self.logger.info(
            f"Metadata saved: {filepath}"
        )

        # ALSO update master history
        self.update_pipeline_history(metadata)

        return filepath

    # ══════════════════════════════════════════════════════
    # UPDATE MASTER PIPELINE HISTORY
    # ══════════════════════════════════════════════════════

    def update_pipeline_history(self, metadata):

        history = []

        # ── LOAD EXISTING HISTORY ─────────────────

        if os.path.exists(self.history_file):

            try:

                with open(self.history_file, "r") as f:

                    history = json.load(f)

            except Exception as e:

                self.logger.warning(
                    f"Could not load history file: {e}"
                )

                history = []

        # ── APPEND NEW RUN ────────────────────────

        history.append(metadata)

        # ── SAVE UPDATED HISTORY ──────────────────

        with open(self.history_file, "w") as f:

            json.dump(
                history,
                f,
                indent=4
            )

        self.logger.info(
            f"Pipeline history updated: {self.history_file}"
        )

    # ══════════════════════════════════════════════════════
    # LOAD PIPELINE HISTORY
    # ══════════════════════════════════════════════════════

    def load_pipeline_history(self):

        if not os.path.exists(self.history_file):

            return []

        try:

            with open(self.history_file, "r") as f:

                history = json.load(f)

            return history

        except Exception as e:

            self.logger.error(
                f"Failed to load pipeline history: {e}"
            )

            return []
