#
# Providence
# Pipelines
# YNAB Flow
#

from datetime import datetime, timezone
from io import BytesIO, StringIO
from typing import Optional

from botocore.exceptions import ClientError
from httpx import AsyncClient
from prefect import flow, get_run_logger, task
from prefect.blocks.system import Secret
from prefect.concurrency.asyncio import rate_limit
from prefect.tasks import exponential_backoff

from b2 import b2_bucket

YNAB_API_RATE_LIMIT = "ynab-api"


@task(retries=3, retry_delay_seconds=exponential_backoff(10))
async def get_ynab(
    bucket: str,
    budget_id: str,
    knowledge_path: str = "raw/by=ynab/server_knowlege",
) -> str:
    """Get incremental YNAB budget data from YNAB API.

    Performs a delta GET request against the YNAB API, passing 'server_knowlege'
    read form given path if it exists.

    Args:
        bucket: Name of bucket to stage ingested data.
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
    async with b2_bucket(bucket) as lake:
        if knowledge_path is not None:
            with BytesIO() as buf:
                try:
                    await lake.download_fileobj(Key=knowledge_path, Fileobj=buf)  # type: ignore
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
                params=(
                    {} if knowledge is None else {"last_knowledge_of_server": knowledge}
                ),
            )
            response.raise_for_status()

        lake_path = f"staging/by=ynab/date={datetime.now(timezone.utc).date().isoformat()}.json"
        log.info(f"Uploading retrieved data to: {lake_path}")
        await lake.upload_fileobj(Fileobj=BytesIO(response.content), Key=lake_path)  # type: ignore

        log.info(f"Uploading server_knowlege to: {knowledge_path}")
        await lake.upload_fileobj(
            Fileobj=BytesIO(str(response.json()["data"]["server_knowledge"]).encode()),
            Key=knowledge_path,
        )  # type: ignore

    return lake_path


@flow
async def ingest_ynab(bucket: str, budget_id: str):
    """Ingest YNAB budget data for the budget with the given id.

    Args:
        bucket: Name of bucket to stage ingested data.
        budget_id: Id of the budget to retrieve.
    """
    await get_ynab(bucket, budget_id)
