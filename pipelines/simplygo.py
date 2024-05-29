#
# Providence
# Prefect Flows
# SimplyGo Flow
#

from datetime import date
from prefect import flow, get_run_logger
from prefect.tasks import exponential_backoff
from execution.github import run_container


@flow(
    retries=3,
    retry_delay_seconds=30,
)
async def ingest_simplygo(trips_on: date):
    """Ingest SimplyGo Trips data on the given date.

    Args:
        trips_on: Date on which trips should be ingested
    """
    log = get_run_logger()

    log.info(f"Scraping SimplyGo Trips data on: {trips_on.isoformat()}")
    await run_container(
        "ghcr.io/mrzzy/pvd-simplygo-src:latest",
        command=f"bash entrypoint.sh {trips_on.isoformat()}",
    )

    log.info(f"Extracting SimplyGo Trips data on: {trips_on.isoformat()}")
    await run_container(
        "ghcr.io/mrzzy/pvd-simplygo-tfm:latest",
        command=f"bash entrypoint.sh {trips_on.isoformat()}",
    )
