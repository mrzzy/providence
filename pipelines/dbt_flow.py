#
# Providence
# Pipelines
# DBT Flow
#

import os

from prefect import flow, get_run_logger, task
from prefect.blocks.system import Secret
from prefect.concurrency.asyncio import concurrency
from prefect.tasks import exponential_backoff
from prefect_dbt import DbtCliProfile, DbtCoreOperation
from prefect_dbt.cli.commands import trigger_dbt_cli_command

DBT_CONCURRENCY = "dbt"


@task(retries=3, retry_delay_seconds=exponential_backoff(10))
async def build_dbt(bucket: str, selector: str):
    """Build DBT models with the given node selector."""
    async with concurrency(DBT_CONCURRENCY, occupy=1):
        log = get_run_logger()

        # pass args via environment
        old_env = dict(os.environ)
        log.info("Building DBT models")
        await DbtCoreOperation(
            commands=["dbt build"],
            extra_command_args=["--select", selector],
            env={
                "PVD_LAKE_BUCKET": bucket,
                "motherduck_token": (await Secret.load("motherduck-token")).get(),
            },
            dbt_cli_profile=await DbtCliProfile.load("dbt-profile"),
            overwrite_profiles=True,
            stream_output=True,
        ).run()


@flow
async def transform_dbt(bucket: str, selector: str = "*"):
    """Transform data by building DBT models with the given node selector

    Args:
        bucket: Name of the bucket used as a a data source for DBT models.
        select: DBT node selector specifying the DBT models to build.
            Refer to https://docs.getdbt.com/reference/node-selection/syntax
    """
    await build_dbt(bucket, selector)
