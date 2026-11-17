from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np


def validate_ohlcv_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates and cleans a raw OHLCV Pandas DataFrame.
    Handles:
      A. Missing Values (NaNs / nulls)
      B. Duplicate Trading Dates
      C. Inconsistent Data (High < Low, Open/Close outside High-Low range, negative prices/volume)
    
    Returns:
      (cleaned_df, validation_report)
    """
    report: Dict[str, Any] = {
        "initial_rows": 0,
        "duplicate_dates_removed": 0,
        "missing_values_handled": 0,
        "missing_rows_dropped": 0,
        "inconsistent_rows_removed": 0,
        "final_valid_rows": 0,
        "is_valid": False,
        "issues_log": []
    }

    if df is None or df.empty:
        report["issues_log"].append("Input DataFrame is empty or None.")
        return pd.DataFrame(), report

    # Work on a copy to avoid mutating caller's DataFrame
    work_df = df.copy()

    # If the date is in the DataFrame index (default for yfinance), reset it to a column
    if "trade_date" not in work_df.columns:
        work_df = work_df.reset_index()
        # Rename standard yfinance date column ('Date' or 'index') to 'trade_date'
        for col in ["Date", "Datetime", "index", "date"]:
            if col in work_df.columns:
                work_df = work_df.rename(columns={col: "trade_date"})
                break

    # Standardize column names to lowercase snake_case
    rename_map = {
        "Open": "open_price",
        "High": "high_price",
        "Low": "low_price",
        "Close": "close_price",
        "Volume": "volume",
        "open": "open_price",
        "high": "high_price",
        "low": "low_price",
        "close": "close_price",
    }
    work_df = work_df.rename(columns=rename_map)

    required_cols = ["trade_date", "open_price", "high_price", "low_price", "close_price", "volume"]
    missing_cols = [c for c in required_cols if c not in work_df.columns]
    if missing_cols:
        report["issues_log"].append(f"Missing required columns: {missing_cols}")
        return pd.DataFrame(), report

    # Keep only the required OHLCV columns
    work_df = work_df[required_cols].copy()
    report["initial_rows"] = int(len(work_df))

    # ---------------------------------------------------------
    # 1. VALIDATE & NORMALIZE TRADING DATES + DUPLICATE DATES
    # ---------------------------------------------------------
    work_df["trade_date"] = pd.to_datetime(work_df["trade_date"], errors="coerce").dt.date
    invalid_dates = int(work_df["trade_date"].isna().sum())
    if invalid_dates > 0:
        work_df = work_df.dropna(subset=["trade_date"])
        report["issues_log"].append(f"Dropped {invalid_dates} rows with unparseable dates.")

    # Sort chronologically before checking duplicates or forward-filling
    work_df = work_df.sort_values(by="trade_date", ascending=True).reset_index(drop=True)

    # B. Detect and remove duplicate trading dates (keep latest entry)
    dup_mask = work_df.duplicated(subset=["trade_date"], keep="last")
    dup_count = int(dup_mask.sum())
    if dup_count > 0:
        work_df = work_df[~dup_mask].reset_index(drop=True)
        report["duplicate_dates_removed"] = dup_count
        report["issues_log"].append(f"Removed {dup_count} duplicate trading date records.")

    # ---------------------------------------------------------
    # 2. HANDLE MISSING VALUES (NaN / Inf)
    # ---------------------------------------------------------
    price_cols = ["open_price", "high_price", "low_price", "close_price"]

    # Coerce all price & volume columns to numeric and replace +/-inf with NaN
    for col in price_cols + ["volume"]:
        work_df[col] = pd.to_numeric(work_df[col], errors="coerce")
    work_df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Count total missing cells before cleaning
    total_missing_cells = int(work_df[price_cols + ["volume"]].isna().sum().sum())
    report["missing_values_handled"] = total_missing_cells

    # If volume is missing, fill with 0
    if work_df["volume"].isna().any():
        work_df["volume"] = work_df["volume"].fillna(0)

    # If Open/High/Low is missing on a row where Close is present, or vice versa,
    # drop rows where ALL prices are NaN first, then allow 1-period forward fill for isolated gaps
    rows_before_na_drop = len(work_df)
    work_df = work_df.dropna(subset=price_cols, how="all")
    work_df[price_cols] = work_df[price_cols].ffill(limit=1)

    # Drop any remaining rows that still have missing OHLC values
    work_df = work_df.dropna(subset=price_cols).reset_index(drop=True)
    rows_dropped_na = rows_before_na_drop - len(work_df)
    if rows_dropped_na > 0:
        report["missing_rows_dropped"] = int(rows_dropped_na)
        report["issues_log"].append(f"Dropped {rows_dropped_na} rows with unrecoverable missing OHLC prices.")

    # ---------------------------------------------------------
    # 3. LOGICAL CONSISTENCY VALIDATION (NumPy Vectorized Checks)
    # ---------------------------------------------------------
    # Apply small floating-point tolerance (1e-4) for rounding edge cases from market feeds
    tol = 1e-4
    o = work_df["open_price"].to_numpy(dtype=float)
    h = work_df["high_price"].to_numpy(dtype=float)
    l = work_df["low_price"].to_numpy(dtype=float)
    c = work_df["close_price"].to_numpy(dtype=float)
    v = work_df["volume"].to_numpy(dtype=float)

    valid_mask = (
        (o > 0) & (h > 0) & (l > 0) & (c > 0) &
        (v >= 0) &
        (h + tol >= l) &
        (h + tol >= o) &
        (h + tol >= c) &
        (l - tol <= o) &
        (l - tol <= c)
    )

    inconsistent_count = int((~valid_mask).sum())
    if inconsistent_count > 0:
        work_df = work_df[valid_mask].reset_index(drop=True)
        report["inconsistent_rows_removed"] = inconsistent_count
        report["issues_log"].append(
            f"Removed {inconsistent_count} logically inconsistent rows (e.g., High < Low or Open/Close outside High-Low)."
        )

    # Clamp tiny floating-point rounding discrepancies so Postgres CHECK constraint passes strictly
    if not work_df.empty:
        work_df["high_price"] = work_df[["open_price", "high_price", "low_price", "close_price"]].max(axis=1)
        work_df["low_price"] = work_df[["open_price", "high_price", "low_price", "close_price"]].min(axis=1)
        work_df[price_cols] = work_df[price_cols].round(4)
        work_df["volume"] = work_df["volume"].astype(np.int64)

    report["final_valid_rows"] = int(len(work_df))
    report["is_valid"] = report["final_valid_rows"] > 0

    return work_df, report


def clean_financial_statement_df(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Cleans a raw financial statement DataFrame (Income Statement, Balance Sheet, or Cash Flow)
    where columns are fiscal period dates and rows are financial line items.
    Replaces NaN/Inf with None so it can be safely serialized into PostgreSQL JSONB.
    
    Returns:
      { "2025-03-31": {"Total Revenue": 1536700000000.0, "Net Income": ...}, ... }
    """
    if df is None or df.empty:
        return {}

    cleaned_by_period: Dict[str, Dict[str, Any]] = {}

    for col in df.columns:
        # Convert column header (Timestamp) to 'YYYY-MM-DD' string
        try:
            period_str = pd.to_datetime(col).strftime("%Y-%m-%d")
        except Exception:
            continue

        series = df[col]
        period_dict: Dict[str, Any] = {}
        for metric_name, val in series.items():
            if pd.isna(val) or (isinstance(val, (float, np.floating)) and np.isinf(val)):
                period_dict[str(metric_name)] = None
            elif isinstance(val, (np.integer, int)):
                period_dict[str(metric_name)] = int(val)
            elif isinstance(val, (np.floating, float)):
                period_dict[str(metric_name)] = round(float(val), 4)
            else:
                period_dict[str(metric_name)] = str(val)

        # Only keep periods that have at least one non-null financial metric
        if any(v is not None for v in period_dict.values()):
            cleaned_by_period[period_str] = period_dict

    return cleaned_by_period


# --- SELF-TEST BLOCK ---
if __name__ == "__main__":
    print("🧪 Running Module 2 Data Validator Self-Test...")
    sample_raw_data = pd.DataFrame({
        "Date": [
            "2026-10-01",
            "2026-10-01",  # B. Duplicate date!
            "2026-10-02",  # Valid row
            "2026-10-03",  # A. Missing close_price!
            "2026-10-04",  # C. Inconsistent row: High (1400) < Low (1450)!
            "2026-10-05",  # C. Inconsistent row: Close (1600) > High (1520)!
        ],
        "Open":   [1450.0, 1450.0, 1480.0, 1490.0, 1420.0, 1500.0],
        "High":   [1500.0, 1500.0, 1510.0, 1520.0, 1400.0, 1520.0],
        "Low":    [1430.0, 1430.0, 1470.0, 1485.0, 1450.0, 1490.0],
        "Close":  [1480.0, 1480.0, 1495.0, np.nan, 1430.0, 1600.0],
        "Volume": [50000,  50000,  62000,  np.nan, 40000,  55000]
    })

    cleaned_df, validation_report = validate_ohlcv_dataframe(sample_raw_data)
    print("📋 Validation Report:", validation_report)
    print("\n✅ Cleaned OHLCV DataFrame:")
    print(cleaned_df)