#
# Transforms
# Transformations
#

from typing import Dict, Callable

import pandas as pd
from pandas import DataFrame


def promote_header(df: DataFrame) -> DataFrame:
    """Promote the first row as Dataframe Header"""
    df.columns = df.iloc[0]
    df = df[1:]
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
    transactions_df = promote_header(df[6:])
    # broadcast metadata dataframe into transforms
    transactions_df[meta_df.columns[1:]] = meta_df.iloc[0, 1:]
    # reset index based on transactions rows
    transactions_df = transactions_df.reset_index(drop=True)
    transactions_df.columns.name = None

    return transactions_df
