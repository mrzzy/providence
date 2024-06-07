#
# Providence
# Integration Tests
# Flow Tests

import os
from datetime import date

import pytest
from simplygo import ingest_simplygo
from uob import ingest_uob
from ynab import ingest_ynab


@pytest.mark.asyncio
async def test_ingest_simplygo(prefect):
    await ingest_simplygo(os.environ["PVD_LAKE_BUCKET"], date(2024, 5, 1))


@pytest.mark.asyncio
async def test_ingest_ynab(prefect):
    await ingest_ynab(os.environ["PVD_LAKE_BUCKET"], os.environ["YNAB_BUDGET_ID"])


@pytest.mark.asyncio
async def test_ingest_uob(prefect):
    await ingest_uob(
        bucket=os.environ["PVD_LAKE_BUCKET"],
        export_path="raw/by=mrzzy/ACC_TXN_History_05062024124137.xls",
    )
