#
# Providence
# Pipelines
# Deploy Pipelines to Prefect
#

import asyncio
from pathlib import Path
from prefect import deploy
from prefect.deployments.runner import DeploymentImage
from simplygo import ingest_simplygo
from ynab import ingest_ynab


async def deploy_pipelines(work_pool: str = "azure-container-instances"):
    """Deploy pipelines to Prefect."""
    await deploy(
        await ingest_simplygo.to_deployment(name="pvd-ingest-simplygo", cron="@daily"),
        await ingest_ynab.to_deployment(name="pvd-ingest-ynab", cron="@daily"),
        work_pool_name=work_pool,
        image="ghcr.io/mrzzy/pvd-pipeline:latest",
        build=False,
    )


if __name__ == "__main__":
    asyncio.run(deploy_pipelines())
