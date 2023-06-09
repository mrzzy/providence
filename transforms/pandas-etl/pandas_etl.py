#
# Providence
# Transforms
# Pandas
#

from datetime import datetime
from typing import Dict, Callable, Any
from os.path import splitext
from textwrap import dedent
from argparse import ArgumentParser
from urllib.parse import urlparse, urlunparse

import pandas as pd
from pandas import DataFrame, factorize

from transforms import extract_uob

# Dict of file extensions to their pandas read implementation
pandas_read = {
    ".xls": pd.read_excel,
}

# Dict of transform_ids to transform functions
transforms: Dict[str, Callable[[DataFrame], DataFrame]] = {
    "noop": lambda df: df,
    "extract_uob": extract_uob,
}

# Dict of file extensions to their pandas write implementation
pandas_write: Dict[str, Callable[[DataFrame, str], Any]] = {
    ".csv": lambda df, path: df.to_csv(path),
    ".pq": lambda df, path: df.to_parquet(path),
}

if __name__ == "__main__":
    # parse & check command line arguments
    parser = ArgumentParser(
        description=dedent(
            """Lightweight S3 to S3 data transforms based on Pandas.

            Environment Variables:
            AWS_ACCESS_KEY_ID     AWS access key id used to authenticate with AWS.
            AWS_SECRET_ACCESS_KEY AWS access key used to authenticate with AWS.
            AWS_DEFAULT_REGION    AWS Region to use.
            """
        )
    )
    parser.add_argument(
        "transform_id", help="ID of the transform to apply.", choices=transforms.keys()
    )
    parser.add_argument(
        "src_url",
        help="URL or path specifying the source file storing input data.",
        type=urlparse,
    )
    parser.add_argument(
        "dest_url",
        help="URL or path specifying the destination file to store the transformed data.",
        type=urlparse,
    )
    args = parser.parse_args()

    # read, transform with pandas
    _, src_ext = splitext(args.src_url.path)
    df = pandas_read[src_ext](urlunparse(args.src_url))
    df = transforms[args.transform_id](df)

    # add pandas_etl metadata
    meta_prefx = "_pandas_etl"
    df[f"{meta_prefx}_transformed_on"] = datetime.utcnow().isoformat()

    # write results to dest_url
    _, dest_ext = splitext(args.dest_url.path)
    pandas_write[dest_ext](df, urlunparse(args.dest_url))
