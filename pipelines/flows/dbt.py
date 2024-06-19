#
# Providence
# Pipelines
# DBT Flow
#

from prefect import flow, get_run_logger, task
from prefect.concurrency.asyncio import concurrency
from prefect.tasks import exponential_backoff
from prefect_dbt import DbtCliProfile
from prefect_dbt.cli.commands import run_dbt_build

DBT_CONCURRENCY = "dbt"


@task(retries=3, retry_delay_seconds=exponential_backoff(10))
async def build_dbt(bucket: str, selector: str):
    """Build DBT models with the given node selector."""
    async with concurrency(DBT_CONCURRENCY, occupy=1):
        log = get_run_logger()
        log.info("Building DBT models")
        await run_dbt_build(
            dbt_cli_profile=await DbtCliProfile.load("dbt-profile"),
            overwrite_profiles=True,
            extra_command_args=["--select", selector],
        )


@flow
async def transform_dbt(bucket: str, selector: str = "*"):
    """Transform data by building DBT models with the given node selector

    Args:
        bucket: Name of the bucket used as a a data source for DBT models.
        select: DBT node selector specifying the DBT models to build.
            Refer to https://docs.getdbt.com/reference/node-selection/syntax
    """
    await build_dbt(bucket, selector)
