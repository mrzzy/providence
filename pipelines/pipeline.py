#
# Providence
# Pipelines
# Prefect flows
#

import asyncio
import os

from dbt_flow import transform_dbt
from simplygo_flow import ingest_simplygo
from uob_flow import ingest_uob
from ynab_flow import ingest_ynab
from prefect import flow


@flow
async def pipeline(bucket: str, budget_id: str):
    """Entrypoint to the Providence Data Pipeline.

    Args:
        bucket: Name of bucket to stage ingested data.
        budget_id: Id of the YNAB budget to retrieve.
    """
    await asyncio.gather(
        ingest_simplygo(bucket),
        ingest_ynab(bucket, budget_id),
        ingest_uob(bucket),
    )
    await transform_dbt(bucket)
