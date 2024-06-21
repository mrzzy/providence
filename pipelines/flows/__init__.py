#
# Providence
# Pipelines
# Prefect flows
#

import asyncio
import os

from flows.dbt import transform_dbt
from flows.simplygo import ingest_simplygo
from flows.uob import ingest_uob
from flows.ynab import ingest_ynab
from prefect import flow


@flow
async def pipeline(bucket: str, ynab_budget_id: str):
    """Entrypoint to the Providence Data Pipeline.

    Args:
        bucket: Name of bucket to stage ingested data.
        ynab_budget_id: Id of the YNAB budget to retrieve.
    """
    await asyncio.gather(
        ingest_simplygo(bucket),
        ingest_ynab(bucket, ynab_budget_id),
        ingest_uob(bucket),
    )
    await transform_dbt(bucket)