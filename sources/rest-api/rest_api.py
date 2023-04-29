#
# Providence
# REST API Source
#

import json
import os
import sys
from io import BytesIO
from datetime import datetime
from typing import Any, Dict
from urllib.parse import urlparse
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
   <method> HTTP method to use in the REST API call.
   <api_url>    URL of the the REST API call to read the response from.
   <s3_url> URL in the format s3://<bucket>/<key> to write to.

   Environment Variables:
   AWS_ACCESS_KEY_ID     AWS access key id used to authenticate with AWS.
   AWS_SECRET_ACCESS_KEY AWS access key used to authenticate with AWS.
   AWS_DEFAULT_REGION    AWS Region to use.
   REST_API_BEARER_TOKEN Optional. Bearer Token pas for authentication to the  REST API.
"""
)

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

    # retrieve response from REST API
    headers = {}
    if "REST_API_BEARER_TOKEN" in os.environ:
        headers["Authorization"] = f"Bearer {os.environ['REST_API_BEARER_TOKEN']}"
    response = requests.request(args.method, args.api_url.geturl(), headers=headers)
    # raise error if request did not return 200 status code.
    response.raise_for_status()

    # upload the response to s3
    s3 = boto3.client("s3")
    # [1:] to skip leading '/' in path
    bucket, key = args.s3_url.hostname, args.s3_url.path[1:]
    s3.upload_fileobj(BytesIO(response.content), bucket, key)
