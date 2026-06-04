import json
import os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import time

# Load environment variables once
load_dotenv()


# -------------------------------
# CONFIG LOADER (SAFE + REUSABLE)
# -------------------------------
def load_config(config_path="config/pipeline_config.json"):
    """
    Loads pipeline configuration JSON safely.
    """

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r") as file:
            return json.load(file)

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")


# -------------------------------
# ENV VARIABLE HANDLER
# -------------------------------
def get_env_variable(variable_name, default=None):
    """
    Fetch environment variable safely with optional default.
    """

    value = os.getenv(variable_name)

    if value is None:
        if default is not None:
            return default

        raise EnvironmentError(f"Missing environment variable: {variable_name}")

    return value


# -------------------------------
# PATH UTILITIES
# -------------------------------
def ensure_directory(path):
    """
    Creates directory if it does not exist.
    Useful for logs, output, staging layers.
    """

    os.makedirs(path, exist_ok=True)
    return path


def get_timestamp():
    """
    Standard timestamp for pipeline runs.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_run_id():
    """
    Unique pipeline run ID.
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")


# -------------------------------
# DATA UTILITIES
# -------------------------------
def save_dataframe(df, path, index=False):
    """
    Save DataFrame safely with folder creation.
    """

    ensure_directory(os.path.dirname(path))
    df.to_csv(path, index=index)


def load_dataframe(path):
    """
    Load CSV safely with validation.
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")

    return pd.read_csv(path)


# -------------------------------
# SIMPLE LOGGER HELPER (OPTIONAL USE)
# -------------------------------
def format_log(message, level="INFO"):
    """
    Standard log format for consistent logging across modules.
    """

    return f"{get_timestamp()} | {level} | {message}"
def log_pipeline_run(result, execution_time=None):
    history_file = "output/pipeline_history.csv"

    new_row = {
        "run_id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rows_processed": result.get("rows_processed", 0),
        "status": result.get("status", "unknown"),
        "output_file": result.get("output_file", ""),
        "execution_time_sec": round(execution_time, 2) if execution_time else 0
    }

    if os.path.exists(history_file):
        df = pd.read_csv(history_file)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])

    df.to_csv(history_file, index=False)