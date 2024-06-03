#
# Providence
# Integration Tests
# SimplyGo Flow
#
from datetime import date
import os

import pytest
from simplygo import ingest_simplygo

from prefect import flow
from prefect.testing.utilities import prefect_test_harness

@pytest.mark.asyncio
async def test_ingest_simplygo(prefect):
    await ingest_simplygo(date(2024, 5, 1))
