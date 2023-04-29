# Providence
# Sources
# REST API Source
#

import json
import os
import sys
from io import BytesIO
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import ParseResult, urlparse
from dataclasses import asdict, dataclass, make_dataclass
from textwrap import dedent
from argparse import ArgumentParser


import boto3
import requests

USAGE = dedent(
    """Error: Invalid arguments or environment variablevbbbhkjk.

   Usage: python rest_api.py <method> <api_url> <s3_url>

   Ingest the response of a REST API call into AWS S3

   Arguments:
   <method>  HTTP method to use in the REST API call.
   <api_url> URL to make the REST API call & read the response from.
   <s3_url>  URL in the format s3://<bucket>/<key> of the location in S3 write to.

   Environment Variables:
   AWS_ACCESS_KEY_ID     AWS access key id used to authenticate with AWS.
   AWS_SECRET_ACCESS_KEY AWS access key used to authenticate with AWS.
   AWS_DEFAULT_REGION    AWS Region to use.
   REST_API_BEARER_TOKEN Optional. Bearer Token pas for authentication to the  REST API.
"""
)


def ingest_api_s3(
    api_url: ParseResult, s3_url: ParseResult, token: Optional[str] = None
):
    """Ingest the REST API response from the given URL into S3 at the given URL.


    Args:
        api_url: URL to make the REST API call & read the response from.
        s3_url: URL in the format s3://<bucket>/<key> of the location in S3 write to.
        token: Optional. Authorization bearer token to pass to the REST API
            when making the request.
    """
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    # retrieve response from REST API
    response = requests.request(args.method, args.api_url.geturl(), headers=headers)
    # raise error if request did not return 200 status code.
    response.raise_for_status()

    # upload the response to s3
    s3 = boto3.client("s3")
    # [1:] to skip leading '/' in path
    bucket, key = args.s3_url.hostname, args.s3_url.path[1:]
    s3.upload_fileobj(BytesIO(response.content), bucket, key)


if __name__ == "__main__":
    # parse & check command line arguments
    parser = ArgumentParser(usage=USAGE)
    parser.add_argument("method")
    parser.add_argument("api_url", type=urlparse)
    parser.add_argument("s3_url", type=urlparse)
    args = parser.parse_args()

    args_scheme, s3_scheme = args.api_url.scheme, args.s3_url.scheme
    if args_scheme != "http" or args_scheme != "https":
        raise ValueError(f"Unsupported API URI scheme: {args_scheme}://")
    if s3_scheme != "s3":
        raise ValueError(f"Unsupported S3 URI scheme: {s3_scheme}://")

    ingest_api_s3(args.api_url, args.s3_url, os.environ.get("REST_API_BEARER_TOKEN"))
