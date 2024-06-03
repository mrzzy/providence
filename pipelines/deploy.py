#
# Providence
# Prefect Flows
# Deploy Pipelines
#

import asyncio
from pathlib import Path
from prefect import deploy
from prefect.deployments.runner import DeploymentImage
from simplygo import ingest_simplygo


async def deploy_pipelines(work_pool: str = "azure-container-instances"):
    """Deploy pipelines to Prefect."""
    await deploy(
        await ingest_simplygo.to_deployment(name="pvd-ingest-simplygo"),
        work_pool_name=work_pool,
        image="ghcr.io/mrzzy/pvd-pipeline:latest",
        build=False,
    )


if __name__ == "__main__":
    asyncio.run(deploy_pipelines())
