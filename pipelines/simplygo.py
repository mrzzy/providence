#
# Providence
# Prefect Flows
# SimplyGo Flows
#

from datetime import date
from pathlib import Path
import subprocess
from prefect import flow, task, get_run_logger
from prefect.blocks.system import Secret
from prefect.tasks import exponential_backoff
from prefect_shell import ShellOperation
from prefect_aws import S3Bucket

lake = S3Bucket.load("pvd-data-lake")


@task(retries=3, retry_delay_seconds=exponential_backoff(10))
async def scrape_simplygo(trips_on: date) -> str:
    """Scrape SimplyGo with simplygo_src for the given 'trips_on'.
    Returns path in data lake where scraped data is stored.
    """

    log = get_run_logger()

    log.info(f"Scraping trips data on: {trips_on.isoformat()}")
    trips_on_iso = trips_on.isoformat()

    local_path = "/tmp/out"
    username = await Secret.load("simplygo-src-username")
    password = await Secret.load("simplygo-src-password")
    output = await ShellOperation(
        env={
            "SIMPLYGO_SRC_USERNAME": username.get(),
            "SIMPLYGO_SRC_PASSWORD": password.get(),
        },
        commands=[
            f"simplygo_src --trips-from {trips_on_iso} --trips-to {trips_on_iso} "
            f"--output-dir {local_path}"
        ],
    ).run()

    lake_path = f"raw/by=simplygo_src/date={trips_on_iso}"
    log.info(f"Writing scrapped data to: {lake_path}")
    await lake.put_directory(local_path, to_path=lake_path)

    return lake_path


@task
async def transform_simplygo(raw_path: str) -> str:
    """Transform raw SimplyGo data at given path with with simplygo_tfm.
    Returns path in data lake where transformed data is stored."""
    log = get_run_logger()

    log.info(f"Transforming trips data from: {raw_path}")
    in_path, out_path = "/tmp/in", "/tmp/out.pq"
    await lake.get_directory(from_path=raw_path, local_path=in_path)
    output = await ShellOperation(
        commands=[f"simplygo_tfm --input-dir {in_path} --output {out_path}"]
    ).run()

    lake_path = raw_path.replace("raw", "staging").replace("src", "tfm") + "/out.pq"
    log.info(f"Writing transformed data to: {lake_path}")
    await lake.upload_from_path(out_path, to_path=lake_path)

    return lake_path


@flow
async def ingest_simplygo(trips_on: date):
    """Ingest SimplyGo Trips data on the given date.

    Args:
        trips_on: Date on which trips should be ingested
    """
    log = get_run_logger()

    raw_path = await scrape_simplygo(trips_on)
    pq_path = await transform_simplygo(raw_path)
