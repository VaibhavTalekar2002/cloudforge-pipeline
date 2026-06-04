import os
import json
import pandas as pd
from datetime import datetime


class DataValidator:

    def __init__(self, config, logger):

        self.config = config
        self.logger = logger

        # Validation reports folder
        self.report_dir = "validation_reports"
        self.last_validation_results = None

        os.makedirs(self.report_dir, exist_ok=True)

    # ══════════════════════════════════════════════════════
    # MAIN VALIDATION PIPELINE
    # ══════════════════════════════════════════════════════

    def validate_dataset(
        self,
        df,
        expected_columns=None,
        expected_types=None,
        business_rules=None,
        run_id=None
    ):

        self.logger.info("Starting dataset validation")

        validation_results = {
            "run_id": run_id,
            "status": "success",
            "stage": "validation",
            "failure_reason": None
        }

        # ─────────────────────────────────────────────
        # BASIC VALIDATION
        # ─────────────────────────────────────────────

        validation_results["row_count"] = len(df)

        validation_results["column_count"] = len(df.columns)

        validation_results["null_counts"] = (
            df.isnull()
            .sum()
            .to_dict()
        )

        validation_results["duplicate_rows"] = (
            int(df.duplicated().sum())
        )

        if df.empty:

            validation_results["status"] = "failed"
            validation_results["failure_reason"] = "empty_dataset"
            validation_results["schema_valid"] = False
            validation_results["datatype_valid"] = False
            validation_results["business_rules_valid"] = False
            validation_results["overall_validation_status"] = False

            report_file = self.save_validation_report(
                validation_results,
                run_id=run_id
            )

            validation_results["report_file"] = report_file
            self.last_validation_results = validation_results

            self.logger.error(
                "Validation failed | Reason: empty_dataset"
            )

            return df, False

        # ─────────────────────────────────────────────
        # SCHEMA VALIDATION
        # ─────────────────────────────────────────────

        schema_results = self.validate_schema(
            df,
            expected_columns
        )

        validation_results.update(schema_results)

        # ─────────────────────────────────────────────
        # DATATYPE VALIDATION
        # ─────────────────────────────────────────────

        datatype_results = self.validate_datatypes(
            df,
            expected_types
        )

        validation_results.update(datatype_results)

        # ─────────────────────────────────────────────
        # BUSINESS RULE VALIDATION
        # ─────────────────────────────────────────────

        business_results = self.validate_business_rules(
            df,
            business_rules
        )

        validation_results.update(business_results)

        # ─────────────────────────────────────────────
        # FINAL STATUS
        # ─────────────────────────────────────────────

        overall_status = (
            validation_results["schema_valid"]
            and validation_results["datatype_valid"]
            and validation_results["business_rules_valid"]
        )

        validation_results["overall_validation_status"] = overall_status

        if not overall_status:

            validation_results["status"] = "failed"
            validation_results["failure_reason"] = self._derive_failure_reason(
                validation_results
            )

        # ─────────────────────────────────────────────
        # SAVE VALIDATION REPORT
        # ─────────────────────────────────────────────

        report_file = self.save_validation_report(
            validation_results,
            run_id=run_id
        )

        validation_results["report_file"] = report_file
        self.last_validation_results = validation_results

        self.logger.info(
            f"Validation complete | Status: {overall_status}"
        )

        return df, overall_status

    # ══════════════════════════════════════════════════════
    # SCHEMA VALIDATION
    # ══════════════════════════════════════════════════════

    def validate_schema(
        self,
        df,
        expected_columns
    ):

        if not expected_columns:

            return {
                "schema_valid": True,
                "missing_columns": [],
                "extra_columns": []
            }

        actual_columns = list(df.columns)

        missing_columns = [
            col for col in expected_columns
            if col not in actual_columns
        ]

        extra_columns = [
            col for col in actual_columns
            if col not in expected_columns
        ]

        schema_valid = (
            len(missing_columns) == 0
            and len(extra_columns) == 0
        )

        if missing_columns:

            self.logger.warning(
                f"Missing columns: {missing_columns}"
            )

        return {
            "schema_valid": schema_valid,
            "missing_columns": missing_columns,
            "extra_columns": extra_columns
        }

    # ══════════════════════════════════════════════════════
    # DATATYPE VALIDATION
    # ══════════════════════════════════════════════════════

    def validate_datatypes(
        self,
        df,
        expected_types
    ):

        if not expected_types:

            return {
                "datatype_valid": True,
                "datatype_issues": {}
            }

        datatype_issues = {}

        for column, expected_dtype in expected_types.items():

            if column not in df.columns:
                datatype_issues[column] = {
                    "expected": expected_dtype,
                    "actual": "missing_column"
                }

                self.logger.warning(
                    f"Datatype check failed because column is missing: {column}"
                )

                continue

            actual_dtype = str(df[column].dtype)

            if actual_dtype != expected_dtype:

                datatype_issues[column] = {
                    "expected": expected_dtype,
                    "actual": actual_dtype
                }

                self.logger.warning(
                    f"Datatype mismatch in {column}"
                )

        datatype_valid = len(datatype_issues) == 0

        return {
            "datatype_valid": datatype_valid,
            "datatype_issues": datatype_issues
        }

    # ══════════════════════════════════════════════════════
    # BUSINESS RULE VALIDATION
    # ══════════════════════════════════════════════════════

    def validate_business_rules(
        self,
        df,
        business_rules
    ):

        if not business_rules:

            return {
                "business_rules_valid": True,
                "business_rule_failures": {}
            }

        failures = {}

        for column, rule in business_rules.items():

            if column not in df.columns:
                failures[column] = {
                    "rule": rule,
                    "failed_rows": None,
                    "reason": "missing_column"
                }

                self.logger.warning(
                    f"Business rule check failed because column is missing: {column}"
                )

                continue

            try:

                # >= RULE
                if rule.startswith(">="):

                    threshold = float(rule.replace(">=", ""))

                    invalid_rows = df[
                        df[column] < threshold
                    ]

                # > RULE
                elif rule.startswith(">"):

                    threshold = float(rule.replace(">", ""))

                    invalid_rows = df[
                        df[column] <= threshold
                    ]

                # EMAIL RULE
                elif rule == "email":

                    invalid_rows = df[
                        ~df[column]
                        .astype(str)
                        .str.contains("@", na=False)
                    ]

                else:

                    continue

                if not invalid_rows.empty:

                    failures[column] = {
                        "rule": rule,
                        "failed_rows": len(invalid_rows)
                    }

                    self.logger.warning(
                        f"Business rule failed: {column}"
                    )

            except Exception as e:

                self.logger.error(
                    f"Rule validation error for {column}: {e}"
                )

        business_rules_valid = len(failures) == 0

        return {
            "business_rules_valid": business_rules_valid,
            "business_rule_failures": failures
        }

    # ══════════════════════════════════════════════════════
    # SAVE VALIDATION REPORT
    # ══════════════════════════════════════════════════════

    def save_validation_report(
        self,
        validation_results,
        run_id=None
    ):

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = (
            f"validation_report_{run_id}.json"
            if run_id
            else f"validation_report_{timestamp}.json"
        )

        filepath = os.path.join(
            self.report_dir,
            filename
        )

        with open(filepath, "w") as f:

            json.dump(
                validation_results,
                f,
                indent=4
            )

        self.logger.info(
            f"Validation report saved: {filepath}"
        )

        return filepath

    def _derive_failure_reason(self, validation_results):

        if validation_results.get("row_count") == 0:
            return "empty_dataset"

        if not validation_results.get("schema_valid", True):
            return "schema_mismatch"

        if not validation_results.get("datatype_valid", True):
            return "type_error"

        if not validation_results.get("business_rules_valid", True):
            return "business_rule_violation"

        return "validation_failure"
