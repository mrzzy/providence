#
# Providence
# SimplyGo Flow
# Integration Tests
#


from datetime import date

import pytest
from simplygo import ingest_simplygo


@pytest.mark.asyncio
async def test_ingest_simplygo(prefect):
    await ingest_simplygo(date(2024, 5, 1))
