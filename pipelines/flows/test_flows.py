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
    await asyncio.gather(
        ingest_simplygo(os.environ["PVD_LAKE_BUCKET"], date(2024, 5, 1)),
        ingest_ynab(os.environ["PVD_LAKE_BUCKET"], os.environ["YNAB_BUDGET_ID"]),
        ingest_uob(
            bucket=os.environ["PVD_LAKE_BUCKET"],
            export_path="raw/by=mrzzy/ACC_TXN_History_05062024124137.xls",
        )
    )
    await transform_dbt()
