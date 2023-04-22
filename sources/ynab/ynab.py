#
# Providence
# YNAB Source
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

import boto3
from ynab_sdk import YNAB
from ynab_sdk.api.models.responses.budget_detail import Budget


# extend YNAB budget dataclass with YNAB Source metadata
@dataclass
class MetaBudget(Budget):
    _ynab_src_scraped_on: datetime


def to_json(budget: MetaBudget) -> str:
    def serialize_json(obj) -> str:
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Could not serialize: {repr(obj)}")

    return json.dumps(asdict(budget), default=serialize_json)


def ingest_budget_s3(
    ynab: YNAB, s3, budget_id: str, s3_url: str, scraped_on=datetime.utcnow()
):
    """Ingest the YNAB budget as JSON into AWS S3 at the specified URL.

    Args:
        ynab: YNAB client used to access the YNAB API.
        s3: Boto3 S3 Client used to upload to AWS S3.
        budget_id: Id specifying the YNAB budget to ingest.
        s3_url: s3:// url specifying the bucket & key of the ingested object.
        scraped_on: UTC timestamp defining the YNAB budget was scraped.
    """
    # parse given s3 url
    url = urlparse(s3_url)
    if url.scheme != "s3":
        raise ValueError("Expected S3 URL to used the s3:// scheme")
    # path[1:] need to skip leading '/'
    bucket, key = url.hostname, url.path[1:]

    # get budget as json & add metadata
    budget = MetaBudget(
        _ynab_src_scraped_on=scraped_on,
        **asdict(ynab.budgets.get_budget(budget_id).data.budget),
    )
    # upload budget to s3
    s3.upload_fileobj(BytesIO(to_json(budget).encode()), bucket, key)


if __name__ == "__main__":
    # check args & env vars
    if not (
        all(
            env_var in os.environ
            for env_var in [
                "AWS_DEFAULT_REGION",
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "YNAB_SRC_ACCESS_TOKEN",
            ]
        )
        and len(sys.argv) == 3
    ):
        print(
            dedent(
                """Error: Invalid arguments or environment variables.

               Usage: python ynab.py <BUDGET_ID> <s3_url>

               Ingest the YNAB budget as JSON into AWS S3 at the specified URL.

               Arguments:
               <budget_id> Id specifying the YNAB budget to ingest.
               <s3_url>    Target URL in the format s3://<bucket>/<key> to ingest to.

               Environment Variables:
               AWS_ACCESS_KEY_ID     AWS access key id used to authenticate with AWS.
               AWS_SECRET_ACCESS_KEY AWS access key used to authenticate with AWS.
               AWS_DEFAULT_REGION    AWS Region to use.
               YNAB_SRC_ACCESS_TOKEN YNAB personal access token.
            """
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    ingest_budget_s3(
        YNAB(os.environ["YNAB_SRC_ACCESS_TOKEN"]), boto3.client("s3"), *sys.argv[1:]
    )