#
# Providence
# Integration Tests
# Flow Tests

import asyncio
import os
from datetime import date

import pytest
from flows import ingest_simplygo, ingest_uob, ingest_ynab, transform_dbt


@pytest.mark.asyncio
async def test_flows(prefect):
    bucket = os.environ["PVD_LAKE_BUCKET"]
    await ingest_simplygo(bucket, date(2024, 5, 1))
    await ingest_ynab(os.environ["PVD_LAKE_BUCKET"], os.environ["YNAB_BUDGET_ID"])
    await ingest_uob(
        bucket,
        export_path="raw/by=mrzzy/ACC_TXN_History_05062024124137.xls",
    )
    await transform_dbt(bucket)