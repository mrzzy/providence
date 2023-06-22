#
# Providence
# Sources
# REST API Source
#

import json
import os
import sys
import subprocess
from io import BytesIO
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import ParseResult, urlparse
from dataclasses import asdict, dataclass, make_dataclass
from textwrap import dedent
from argparse import ArgumentParser


import requests

USAGE = dedent(
    """Error: Invalid arguments or environment variable.

   Usage: python rest_api.py <method> <api_url> <target_path>

   Ingest the response of a REST API call.

   Arguments:
   <method>  HTTP method to use in the REST API call.
   <api_url> URL to make the REST API call & read the response from.
   <target_path> Target Path or Rclone remote path to write scraped response to:
    - A simple path the response will write to a local file on disk.
    - A Rclone remote path in the format <RCLONE>:<REMOTE_PATH> will write
        the response to the rclone remote location. Requires that the rclon binary
        be installed and accessible on PATH.

   Environment Variables:
   REST_API_BEARER_TOKEN Optional. Bearer Token to pass for authentication.
"""
)


def ingest_api(
    api_method: str,
    api_url: ParseResult,
    target_path: str,
    api_token: Optional[str] = None,
    scraped_on: datetime = datetime.utcnow(),
):
    """Ingest the REST API response from the given URL.

    Args:
        api_method: HTTP method used to make the REST API call.
        api_url: URL to make the REST API call & read the response from.
        target_path: Target Path (local or rclone) to write the response to.
        api_token: Optional. Authorization bearer token to pass to the REST API
            when making the request.
        scraped_on: UTC timestamp defining when the REST API call was made.
    """
    # check given urls
    if api_url.scheme not in ["http", "https"]:
        raise ValueError(f"Unsupported API URI scheme: {api_url.scheme}://")

    # retrieve response from REST API
    headers = {}
    if api_token is not None:
        headers["Authorization"] = f"Bearer {api_token}"
    response = requests.request(api_method, api_url.geturl(), headers=headers)
    # raise error if request did not return 200 status code.
    response.raise_for_status()

    # check content type of response (only the first directive)
    content_type = response.headers.get("Content-Type", "missing").split(";")[0]
    if content_type != "application/json":
        raise RuntimeError(f"Expected JSON response, got Content-Type: {content_type}")
    # splice scraped_on timestamp into response
    content = response.json()
    content["_rest_api_src_scraped_on"] = scraped_on.isoformat()

    # write response with rclone
    # since rclone supports local path natively, there is no need to handle
    # the local path case
    subprocess.run(
        ["rclone", "rcat", target_path],
        input=json.dumps(content).encode(),
        # check status code upon rclone exit
        check=True,
    )


if __name__ == "__main__":
    # parse & check command line arguments
    parser = ArgumentParser(usage=USAGE)
    parser.add_argument("method")
    parser.add_argument("api_url", type=urlparse)
    parser.add_argument("target_path")
    args = parser.parse_args()

    ingest_api(
        args.method,
        args.api_url,
        args.target_path,
        os.environ.get("REST_API_BEARER_TOKEN"),
    )
