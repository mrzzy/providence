#
# Providence
# End to End Tests
#

from collections.abc import Iterator
import os
import json
import stat
import string
import boto3
import random
from pathlib import Path
from datetime import date, datetime, timedelta

import pytest
from testcontainers.compose import DockerCompose

DAG_IDS = [
    "pvd_schema",
    "pvd_ingest_account_map",
    "pvd_ingest_bank_card_map",
    "pvd_ingest_simplygo",
    "pvd_ingest_ynab",
    "pvd_ingest_uob",
    "pvd_transform_dbt",
    "pvd_reverse_ynab",
]


def random_suffix(n=8) -> str:
    """Generate a random suffix of the given length"""
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(n)
    )


@pytest.fixture
def e2e_suffix() -> str:
    suffix = random_suffix()
    return suffix


@pytest.fixture
def s3_bucket(e2e_suffix: str) -> Iterator[str]:
    # create test bucket for e2e test
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(f"mrzzy-co-providence-e2e-{e2e_suffix}")
    # by default buckets are created in us-east-1, use default region instead.
    bucket.create(
        CreateBucketConfiguration={
            "LocationConstraint": os.environ["AWS_DEFAULT_REGION"]
        },
    )

    # copy test data to test bucket
    test_data_keys = [
        # uob export
        # DAG locates export by mod time, not the date in the numeric suffix
        "providence/manual/uob/ACC_TXN_History_09042023114932.xls",
        # account mapping
        "providence/manual/mapping/account.csv",
        # bank card mapping
        "providence/manual/mapping/bank_card.csv",
    ]
    for key in test_data_keys:
        bucket.Object(key).copy_from(
            CopySource={"Bucket": "mrzzy-co-data-lake", "Key": key},
            # ensure that the LastModified timestamp metadata gets updated.
            MetadataDirective="REPLACE",
        )

    yield bucket.name

    # clean up test bucket
    bucket.objects.delete()
    bucket.delete()
