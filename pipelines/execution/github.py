#
# Providence
# Prefect Tasks
# Github Workflow Integration
#

import json
import httpx
import asyncio
from typing import Any, Dict, cast
from prefect import Flow, flow, get_run_logger, task
from prefect_github import GitHubCredentials
from prefect.concurrency.asyncio import rate_limit
from uuid import uuid4
from logging import Logger

from dataclasses import dataclass

GITHUB_API_LIMIT = "github_api"


@dataclass
class GitRef:
    """
    Fully qualified reference to a Github commit.

    owner: User or Organisation that owns the Github repository.
    repository: Name of of the Github Repository hosting the workflow.
    ref: Branch or tag reference specifying the commit that contains the workflow
        Must be fully qualified (eg. heads/main).
    """

    owner: str
    repo: str
    ref: str

    def __str__(self) -> str:
        return f"{self.owner}/{self.repo}@{self.ref}"

    @property
    def name(self) -> str:
        """Returns the unqualified name of the Git ref."""
        return self.ref.split("/")[-1]


@dataclass
class WorkflowRef:
    """Fully qualified reference to a Github workflow.

    ref: Ref specifying the commit containing the workflow.
    id_: Id specifying the workflow to run.
    """

    ref: GitRef
    id_: str

    def __str__(self) -> str:
        return f"{self.id_} on {self.ref}"


async def github_preamble() -> tuple[Logger, httpx.AsyncClient]:
    """Premable to be run at the start of all GitHub tasks."""
    await rate_limit(GITHUB_API_LIMIT)
    creds = await GitHubCredentials.load("github-credentials")
    client = httpx.AsyncClient(
        base_url="https://api.github.com",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {creds.token.get_secret_value()}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    return (get_run_logger(), client)  # type: ignore


@task
async def query_sha(ref: GitRef) -> str:
    """Query the SHA hash of the given fully qualified Git ref."""
    log, gh = await github_preamble()
    async with gh:
        response = await gh.get(f"/repos/{ref.owner}/{ref.repo}/git/ref/{ref.ref}")
    response.raise_for_status()
    return response.json()["object"]["sha"]


@task
async def branch_workflow(workflow: WorkflowRef) -> WorkflowRef:
    """Create a unique branch to run Workflow
    Updates workflow.ref to the unique branch and returns the Workflow reference."""
    log, gh = await github_preamble()
    new_ref = f"heads/workflow-{uuid4()}"
    async with gh:
        response = await gh.post(
            f"/repos/{workflow.ref.owner}/{workflow.ref.repo}/git/refs",
            json={"ref": f"refs/{new_ref}", "sha": await query_sha(workflow.ref)},
        )
    response.raise_for_status()

    workflow.ref.ref = new_ref
    return workflow


@task
async def create_workflow(
    workflow: WorkflowRef,
    inputs: Dict[str, Any],
):
    """Create a Workflow run by sending a dispatch to the Github API."""
    log, gh = await github_preamble()

    log.info(f"Dispatching workflow run: {workflow}")
    async with gh:
        response = await gh.post(
            f"/repos/{workflow.ref.owner}/{workflow.ref.repo}/actions/workflows/{workflow.id_}/dispatches",
            json={"ref": workflow.ref.name, "inputs": inputs},
        )
    print(response.text)

    response.raise_for_status()


@task
async def wait_workflow(
    workflow: WorkflowRef, duration: int = 1200, interval: int = 10
) -> str:
    """Wait for the Workflow run to conclude, returning the final status.
    Assumes workflow.ref is unique for Workflow Run."""
    log, gh = await github_preamble()
    n_polls = duration // interval

    async with gh:
        for i in range(n_polls):
            log.info(f"Querying workflow run {i+1}/{n_polls}: {workflow}")
            response = await gh.get(
                f"/repos/{workflow.ref.owner}/{workflow.ref.repo}/actions/workflows/{workflow.id_}/runs",
                params={"branch": workflow.ref.name},
            )
            response.raise_for_status()
            body = response.json()

            # return conclusion if workflow run is done
            if (
                body["total_count"] > 0
                and body["workflow_runs"][0]["conclusion"] is not None
            ):
                return body["workflow_runs"][0]["conclusion"]

            log.warning("Workflow run has not concluded")
            await asyncio.sleep(interval)

    raise TimeoutError("Timed out waiting for workflow to conclude")


@task
async def delete_ref(ref: GitRef):
    """Delete the given Git Ref"""
    log, gh = await github_preamble()

    log.info(f"Deleting Git Ref: {ref}")
    async with gh:
        response = await gh.delete(
            f"/repos/{ref.owner}/{ref.repo}/git/refs/{ref.ref}",
        )
    response.raise_for_status()


@task
async def run_workflow(
    owner: str,
    repo: str,
    ref: str,
    workflow_id: str,
    inputs: Dict[str, Any],
) -> str:
    """Run Github Workflow specified by the given given repository.
    Waits for the workflow to complete before exiting.

    Args:
        owner: User or Organisation that owns the github workflow.
        repo: Name of the repository that the workflow resides in.
        ref: Fully qualified git commit reference that containers the workflow to run
            eg. 'heads/main'.
        workflow_id: Id specifying the workflow to run.
        inputs: Dict of inputs

    Returns:
        the status of the of the completed workflow.
    """
    workflow = await branch_workflow(WorkflowRef(GitRef(owner, repo, ref), workflow_id))
    await create_workflow(workflow, inputs)
    status = await wait_workflow(workflow)
    await delete_ref(workflow.ref)

    return status


@task
async def run_container(image: str, command: str, env: dict[str, str] = {}):
    """Run Container Task with args & env on Pipeline Task Github Actions workflow.

    Args:
        image: Fully qualified container image tag to run.
        command: Command to run in the container.
        env: Dict of environment variables to set in the container's runtime environment.
    """
    status = await run_workflow(
        owner="mrzzy",
        repo="providence",
        ref="heads/main",
        workflow_id="task.yaml",
        inputs={
            "image": image,
            "command": command,
            "env": json.dumps(env),
        },
    )

    if status != "success":
        raise RuntimeError(
            f"Container Task {image} didn't succeed. Check Github Actions logs."
        )
