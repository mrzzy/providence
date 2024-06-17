#
# Providence
# Pipelines
# UOB Transforms
#

import re
from datetime import date
from pandas import DataFrame
from pandas.api.types import pandas_dtype

EXPORT_PATTERN = re.compile(
    r"ACC_TXN_History_(?P<day>\d{2})(?P<month>\d{2})(?P<year>\d{4})\d*\."
)


def promote_header(df: DataFrame) -> DataFrame:
    """Promote the first row as Dataframe Header"""
    df.columns = df.iloc[0]
    df = df[1:]  # type: ignore
    df.columns.name = None
    return df


def extract_uob(df: DataFrame) -> DataFrame:
    """Extract UOB Bank transactions from the given excel transactions export."""
    # Extract metadata as transposed 3-5 rows from header section
    meta_df = df.iloc[2:6, :2].T
    # strip trailing ':', adapt transposed headers as column headers
    meta_df.iloc[0] = meta_df.iloc[0].str.strip(":")
    meta_df = promote_header(meta_df)
    # currency is oddly placed, so we extract it manually
    meta_df["Currency"] = df.iloc[3, 2]

    # Extract transactions section
    transactions_df = promote_header(df[6:])  # type: ignore
    # broadcast metadata dataframe into transforms
    transactions_df[meta_df.columns[1:]] = meta_df.iloc[0, 1:]
    # reset index based on transactions rows
    transactions_df = transactions_df.reset_index(drop=True)
    transactions_df.columns.name = None

    # enforce consistent schema regardless of inferred types
    return transactions_df.astype(
        {
            "Transaction Date": pandas_dtype("O"),
            "Transaction Description": pandas_dtype("O"),
            "Withdrawal": pandas_dtype("float64"),
            "Deposit": pandas_dtype("float64"),
            "Available Balance": pandas_dtype("float64"),
            "Account Number": pandas_dtype("O"),
            "Account Type": pandas_dtype("O"),
            "Statement Period": pandas_dtype("O"),
            "Currency": pandas_dtype("O"),
        }
    )


def parse_scraped_on(filename: str) -> date:
    """Parse scraped on date from the given UOB export filename.

    Args:
        filename:
            UOB export filename to parse date from in the format:
                'ACC_TXN_History_<DDMMYYYY>*.xls'.
    Returns:
        Scraped on date parsed from the given filename.
    """
    match = EXPORT_PATTERN.match(filename)
    if match is None:
        raise ValueError("Filename did not match expected pattern.")
    return date(
        int(match.group("year")), int(match.group("month")), int(match.group("day"))
    )
