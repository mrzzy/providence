#
# Providence
# Pipelines
# B2 Storage Integration
#

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import aioboto3
from mypy_boto3_s3.service_resource import Bucket
from prefect.blocks.system import Secret
from prefect.filesystems import S3


@asynccontextmanager
async def b2_bucket(
    name, endpoint_url: str = "https://s3.us-west-004.backblazeb2.com"
) -> AsyncGenerator[Bucket, None]:
    """Creates a S3 bucket resource for the bucket of the given name.

    Loads Prefect Secret blocks 'b2-account-id' & 'b2-app-key' to obtain credentials.

    Args:
        name: Name of the bucket to write files against
        endpoint_url: B2
    """
    async with aioboto3.Session(
        aws_access_key_id=(await Secret.load("b2-account-id")).get(),
        aws_secret_access_key=(await Secret.load("b2-app-key")).get(),
    ).resource(service_name="s3", endpoint_url=endpoint_url) as s3:
        yield await s3.Bucket(name)


async def upload_path(bucket: Bucket, path: Path, key: str):
    """Recursively upload given path to bucket under key.

    Args:
        bucket: Bucket resource to upload to.
        path: Path on the local filesystem to recursively upload.
        key: Key within bucket under which to upload files.
    """
    # queue uploads
    uploads = []
    for subpath in path.rglob("*"):
        if not subpath.is_file():
            continue

        uploads.append(
            bucket.upload_file(
                Filename=str(subpath.resolve()),
                Key=f"{key}/{subpath.relative_to(path)}",
            )
        )  # type: ignore

    # wait for all uploads to complete
    await asyncio.gather(*uploads)


async def download_path(bucket: Bucket, key: str, path: Path):
    """Recursively download given path to bucket under key.

    Args:
        bucket: Bucket resource to upload to.
        path: Path on the local filesystem to recursively upload.
        key: Key within bucket under which to upload files.
    """
    # ensure destination path exists, create if necessary
    os.makedirs(path, exist_ok=True)

    # queue downloads
    downloads = []
    async for obj in bucket.objects.filter(Prefix=key):  # type: ignore
        dest_path = path / obj.key.replace(key, "./")
        downloads.append(
            bucket.download_file(Key=obj.key, Filename=str(dest_path.resolve()))
        )

    # wait for all downloads to complete
    await asyncio.gather(*downloads)
