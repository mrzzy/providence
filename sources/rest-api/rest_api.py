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
   REST_API_BEARER_TOKEN Optional. Bearer Token to pass for authentication.
"""
)


def ingest_api_s3(
    api_method: str,
    api_url: ParseResult,
    s3_url: ParseResult,
    api_token: Optional[str] = None,
    scraped_on: datetime = datetime.utcnow(),
):
    """Ingest the REST API response from the given URL into S3 at the given URL.


    Args:
        api_method: HTTP method used to make the REST API call.
        api_url: URL to make the REST API call & read the response from.
        s3_url: URL in the format s3://<bucket>/<key> of the location in S3 write to.
        api_token: Optional. Authorization bearer token to pass to the REST API
            when making the request.
        scraped_on: UTC timestamp defining when the REST API call was made.
    """
    # check given urls
    if api_url.scheme not in ["http", "https"]:
        raise ValueError(f"Unsupported API URI scheme: {api_url.scheme}://")
    if s3_url.scheme != "s3":
        raise ValueError(f"Unsupported S3 URI scheme: {s3_url.scheme}://")

    # retrieve response from REST API
    headers = {}
    if api_token is not None:
        headers["Authorization"] = f"Bearer {api_token}"
    response = requests.request(api_method, api_url.geturl(), headers=headers)
    content_type = response.headers.get("Content-Type", "missing")
    if content_type != "application/json":
        raise RuntimeError(f"Expected JSON response, got Content-Type: {content_type}")
    # raise error if request did not return 200 status code.
    response.raise_for_status()

    # splice scraped_on timestamp into response to uploaded into s3
    content = response.json()
    content["_rest_api_src_scraped_on"] = scraped_on.isoformat()

    # upload the response to s3
    s3 = boto3.client("s3")
    # [1:] to skip leading '/' in path
    bucket, key = s3_url.hostname, s3_url.path[1:]
    s3.upload_fileobj(BytesIO(json.dumps(content).encode()), bucket, key)


if __name__ == "__main__":
    # parse & check command line arguments
    parser = ArgumentParser(usage=USAGE)
    parser.add_argument("method")
    parser.add_argument("api_url", type=urlparse)
    parser.add_argument("s3_url", type=urlparse)
    args = parser.parse_args()

    ingest_api_s3(
        args.method, args.api_url, args.s3_url, os.environ.get("REST_API_BEARER_TOKEN")
    )
