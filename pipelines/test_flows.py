#
# Providence
# Integration Tests
# Flow Tests

import os
from datetime import date

import pytest

from simplygo import ingest_simplygo
from ynab import ingest_ynab


@pytest.mark.asyncio
async def test_ingest_simplygo(prefect):
    await ingest_simplygo(os.environ["PVD_LAKE_BUCKET"], date(2024, 5, 1))


@pytest.mark.asyncio
async def test_ingest_ynab(prefect):
    await ingest_ynab(os.environ["PVD_LAKE_BUCKET"], os.environ["YNAB_BUDGET_ID"])
