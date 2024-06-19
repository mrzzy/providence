#
# Providence
# Pipelines
# SimplyGo Flow
#

from datetime import date, datetime, timedelta, timezone
from os import path
from pathlib import Path
import subprocess
from typing import Optional
from prefect import flow, task, get_run_logger
from prefect.blocks.system import Secret
from prefect.concurrency.asyncio import rate_limit
from prefect.tasks import exponential_backoff
from prefect_shell import ShellOperation

from b2 import b2_bucket, download_path, upload_path

SIMPLYGO_RATE_LIMIT = "simplygo"


@task(retries=3, retry_delay_seconds=exponential_backoff(10))
async def scrape_simplygo(bucket: str, trips_on: date, window: timedelta) -> str:
    """Scrape SimplyGo with simplygo_src for the given 'trips_on' date & 'window' length
    Returns path in bucket where scraped data is stored.
    """

    log = get_run_logger()
    log.info(f"Scraping trips data on: {trips_on.isoformat()}")
    trips_to_iso = (trips_on + window).isoformat()
    trips_on_iso, local_path = trips_on.isoformat(), Path("/tmp/out")
    username = await Secret.load("simplygo-src-username")
    password = await Secret.load("simplygo-src-password")
    await rate_limit(SIMPLYGO_RATE_LIMIT)
    await ShellOperation(
        env={
            "SIMPLYGO_SRC_USERNAME": username.get(),
            "SIMPLYGO_SRC_PASSWORD": password.get(),
        },
        commands=[
            f"simplygo_src --trips-from {trips_on_iso} --trips-to {trips_to_iso} "
            f"--output-dir {local_path}"
        ],
    ).run()

    lake_path = f"raw/by=simplygo_src/date={trips_on_iso}"
    async with b2_bucket(bucket) as lake:
        log.info(f"Writing scrapped data to: {lake_path}")
        await upload_path(lake, local_path, lake_path)

    return lake_path


@task
async def transform_simplygo(bucket: str, raw_path: str) -> Optional[str]:
    """Transform raw SimplyGo data at given path with with simplygo_tfm.
    Returns path in the bucket where transformed data is stored."""
    log = get_run_logger()

    log.info(f"Transforming trips data from: {raw_path}")
    in_path, out_path = "/tmp/in", "/tmp/out.pq"

    async with b2_bucket(bucket) as lake:
        await download_path(lake, raw_path, Path(in_path))

        await ShellOperation(
            commands=[f"simplygo_tfm --input-dir {in_path} --output {out_path}"]
        ).run()

        if not path.exists(out_path):
            # output file not created: no records were transformed
            return None

        lake_path = raw_path.replace("raw", "staging").replace("src", "tfm") + "/out.pq"
        log.info(f"Writing transformed data to: {lake_path}")
        await lake.upload_file(Filename=out_path, Key=lake_path)  # type: ignore

    return lake_path


@flow
async def ingest_simplygo(
    bucket: str, trips_on: Optional[date] = None, window: timedelta = timedelta(days=3)
):
    """Ingest SimplyGo Trips data up to the given 'trips_on' date.

    Flow ingests a look back time window of data from 'trips_on' to account
    for late arriving data. According to the simplygo website, trip records
    "may take up to 3 days to be reflected in your account".

    Args:
        bucket: Name of bucket to stage ingested data.
        trips_on: Optional. Cut off date on which trips prior should be ingested.
            unspecified, uses todays date in the UTC timezone.
        window: Optional. Length of the look back window after 'trips_on' date
            in which trips should be ingested.
    """
    raw_path = await scrape_simplygo(
        bucket=bucket,
        trips_on=datetime.now(timezone.utc).date() if trips_on is None else trips_on,
        window=window,
    )
    await transform_simplygo(bucket, raw_path)
