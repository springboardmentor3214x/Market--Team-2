
from datetime import date
from typing import Any

import pandas as pd


def validate_ohlcv_data(data: Any) -> dict:
    """
    Validate OHLCV data received from Module 2.

    Checks:
    - Required columns
    - Missing values
    - Duplicate dates
    - Positive prices
    - Non-negative volume
    - High/low/open/close consistency
    """

    required_columns = [
        "date", "open", "high", "low", "close", "volume"
    ]

    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        return {
            "is_valid": False,
            "errors": ["Input must be a list or pandas DataFrame."]
        }

    errors = []

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        return {
            "is_valid": False,
            "errors": [f"Missing columns: {missing_columns}"]
        }

    if df.empty:
        return {
            "is_valid": False,
            "errors": ["OHLCV data is empty."]
        }

    if df[required_columns].isnull().any().any():
        errors.append("OHLCV data contains missing values.")

    if df["date"].duplicated().any():
        errors.append("Duplicate dates detected.")

    numeric_columns = ["open", "high", "low", "close", "volume"]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df[numeric_columns].isnull().any().any():
        errors.append("OHLCV data contains invalid numeric values.")

    if not df[numeric_columns].isnull().any().any():
        if (df[["open", "high", "low", "close"]] <= 0).any().any():
            errors.append("Stock prices must be greater than zero.")

        if (df["volume"] < 0).any():
            errors.append("Volume cannot be negative.")

        if (df["high"] < df[["open", "close", "low"]].max(axis=1)).any():
            errors.append("High price is inconsistent.")

        if (df["low"] > df[["open", "close", "high"]].min(axis=1)).any():
            errors.append("Low price is inconsistent.")

    try:
        pd.to_datetime(df["date"], errors="raise")
    except (ValueError, TypeError):
        errors.append("Invalid date values detected.")

    return {
        "is_valid": len(errors) == 0,
        "total_records": len(df),
        "errors": errors
    }


def validate_financial_statement(data: dict) -> dict:
    """
    Validate basic financial statement fields.
    """

    if not isinstance(data, dict):
        return {
            "is_valid": False,
            "errors": ["Financial statement must be a dictionary."]
        }

    errors = []

    required_fields = [
        "revenue",
        "net_income",
        "total_assets",
        "total_debt",
    ]

    for field in required_fields:
        if field not in data or data[field] is None:
            continue

        try:
            value = float(data[field])

            if field in ["revenue", "total_assets", "total_debt"] and value < 0:
                errors.append(f"{field} cannot be negative.")

        except (ValueError, TypeError):
            errors.append(f"{field} must be numeric.")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }
