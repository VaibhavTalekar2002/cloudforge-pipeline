import os
import json
import pandas as pd
from datetime import datetime


class DataProfiler:

    def __init__(self, logger):

        self.logger = logger
        self.profile_dir = "profiling"

        os.makedirs(self.profile_dir, exist_ok=True)

    # ══════════════════════════════════════════════════════
    # MAIN PROFILING ENGINE
    # ══════════════════════════════════════════════════════

    def generate_profile(self, df, run_id=None, validation_status=True):

        self.logger.info("Starting column profiling")

        if not validation_status:

            self.logger.error(
                "Profiler rejected dataset because validation failed"
            )

            return {
                "run_id": run_id,
                "status": "failed",
                "stage": "profiler",
                "reason": "validation_failed",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "debug_info": {}
            }

        if df is None or df.empty:

            self.logger.error(
                "Profiler rejected empty dataset"
            )

            return {
                "run_id": run_id,
                "status": "failed",
                "stage": "profiler",
                "reason": "empty_dataset",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "debug_info": {}
            }

        profile = {
            "run_id": run_id,
            "status": "success",
            "stage": "profiler",
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {}
        }

        for column in df.columns:

            col_data = df[column]

            col_profile = {
                "dtype": str(col_data.dtype),
                "null_count": int(col_data.isnull().sum()),
                "null_percent": float(col_data.isnull().mean() * 100),
                "unique_count": int(col_data.nunique())
            }

            # ── NUMERIC COLUMNS ─────────────────────────
            if pd.api.types.is_numeric_dtype(col_data):

                col_profile.update({
                    "min": float(col_data.min()) if not col_data.isnull().all() else None,
                    "max": float(col_data.max()) if not col_data.isnull().all() else None,
                    "mean": float(col_data.mean()) if not col_data.isnull().all() else None,
                    "median": float(col_data.median()) if not col_data.isnull().all() else None,
                    "std": float(col_data.std()) if not col_data.isnull().all() else None
                })

            # ── TEXT COLUMNS ────────────────────────────
            else:

                col_profile.update({
                    "top_value": col_data.mode().iloc[0] if not col_data.mode().empty else None,
                    "avg_length": float(
                        col_data.astype(str).map(len).mean()
                    )
                })

            profile["columns"][column] = col_profile

        self.logger.info("Profiling completed successfully")

        return profile

    # ══════════════════════════════════════════════════════
    # SAVE PROFILE
    # ══════════════════════════════════════════════════════

    def save_profile(self, profile, run_id=None):

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = (
            f"profile_{run_id}.json"
            if run_id
            else f"profile_{timestamp}.json"
        )

        filepath = os.path.join(self.profile_dir, filename)

        with open(filepath, "w") as f:
            json.dump(profile, f, indent=4)

        self.logger.info(f"Profile saved: {filepath}")

        return filepath
