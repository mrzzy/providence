#
# Providence
# Pipelines
# UOB Flow
#

from io import BytesIO
from pathlib import Path
import pandas as pd
from prefect import task, flow, get_run_logger

from b2 import b2_bucket
from uob.transforms import extract_uob


@task
async def transform_uob(bucket: str, export_path: str) -> str:
    """Transform UOB export at given path to tabular Parquet data

    Args:
        bucket: Name of the bucket to read / store data.
        export_path: Path of the UOB XLSX export to read input data from.
    Returns:
        Path within the bucket the transformed Parquet file is written.
    """

    log = get_run_logger()
    log.info(f"Transforming UOB export: {export_path}")
    out_path = f"staging/by=uob-pipeline/{Path(export_path).stem}.pq"
    async with b2_bucket(bucket) as lake:
        with BytesIO() as export:
            await lake.download_fileobj(Key=export_path, Fileobj=export)  # type: ignore
            df = pd.read_excel(export)
        with BytesIO() as out_pq:
            extract_uob(df).to_parquet(out_pq)
            await lake.upload_fileobj(Key=out_path, Fileobj=out_pq)  # type: ignore

    return out_path


@flow
async def ingest_uob(bucket: str, export_path: str):
    """Ingest UOB export at given path.

    Args:
        bucket: Name of bucket to stage ingested data.
        export_path: Path of the UOB XLSX export to ingest
    """
    pq_path = await transform_uob(bucket, export_path)
