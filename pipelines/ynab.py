#
# Providence
# Pipelines
# YNAB Flow
#

from datetime import datetime
from io import BytesIO, StringIO
from typing import Optional

from botocore.exceptions import ClientError
from httpx import AsyncClient
from prefect import flow, get_run_logger, task
from prefect.blocks.system import Secret
from prefect.concurrency.asyncio import rate_limit
from prefect_aws import S3Bucket

YNAB_API_RATE_LIMIT = "ynab-api"
lake = S3Bucket.load("pvd-data-lake")


@task
# @task(retries=3, retry_delay_seconds=exponential_backoff(10))
async def get_ynab(
    budget_id: str, knowledge_path: str = "raw/by=ynab-pipeline/server_knowlege"
) -> str:
    """Get incremental YNAB budget data from YNAB API.

    Performs a delta GET request against the YNAB API, passing 'server_knowlege'
    read form given path if it exists.

    Args:
        budget_id: Id of the budget to retrieve.
        knowledge_path: Optional. Path of the server knowledge returned by YNAB API
            in the previous request to perform a delta request. If set to None or
            the specified path does not exist, performs a full request instead.
    Returns:
        Path in data lake of the budget data JSON retrieved from YNAB API.
    """
    log = get_run_logger()

    log.info("Attempting to retrieve last server_knowlege")
    knowledge = None
    if knowledge_path is not None:
        with BytesIO() as buf:
            try:
                await lake.download_object_to_file_object(knowledge_path, buf)
                knowledge = buf.getvalue().decode()
            except ClientError as e:
                log.warning(
                    f"Could not retrieve server_knowlege, defaulting to full request: {e}"
                )

    log.info("Performing GET request against YNAB API")
    token = await Secret.load("ynab-access-token")
    async with AsyncClient(
        base_url="https://api.ynab.com/v1",
        headers={"Authorization": f"Bearer {token.get()}"},
    ) as ynab:
        await rate_limit(YNAB_API_RATE_LIMIT)
        response = await ynab.get(
            f"/budgets/{budget_id}",
            params={} if knowledge is None else {"last_knowledge_of_server": knowledge},
        )
        response.raise_for_status()

    lake_path = f"raw/by=ynab-get-ynab/date={datetime.utcnow().date().isoformat()}.json"
    log.info(f"Uploading retrieved data to: {lake_path}")
    await lake.upload_from_file_object(BytesIO(response.content), to_path=lake_path)

    log.info(f"Uploading server_knowlege to: {knowledge_path}")
    await lake.upload_from_file_object(
        BytesIO(str(response.json()["data"]["server_knowledge"]).encode()),
        to_path=knowledge_path,
    )

    return lake_path


@flow
async def ingest_ynab(budget_id: str):
    """Ingest SimplyGo Trips data on the given date.

    Args:
        trips_on: Date on which trips should be ingested
    """
    json_path = await get_ynab(budget_id)
