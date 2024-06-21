#
# Providence
# Pipelines
# UOB Flow
#

from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd
from prefect import flow, get_run_logger, task

from b2 import b2_bucket
from uob.transforms import extract_uob, parse_scraped_on


@task
async def transform_uob(bucket: str, export_path: Optional[str] = None) -> str:
    """Transform UOB export at given path to tabular Parquet data

    Args:
        bucket: Name of the bucket to read / store data.
        export_path: Optional. Path of the UOB XLSX export to ingest. If unspecified,
            Ingests the latest export file by filename.
    Returns:
        Path within the bucket the transformed Parquet file is written.
    """
    log = get_run_logger()
    async with b2_bucket(bucket) as lake:
        if export_path is None:
            # locate the latest export by filename
            # since exports have a numeric date-based suffix
            # the latest export is last in lexical order
            export_path = max(
                o.key
                async for o in lake.objects.filter(Prefix="raw/by=mrzzy/ACC_TXN_History_")  # type: ignore
            )
            if export_path is None:
                raise FileNotFoundError("No UOB export to import found")

            log.info(
                f"Export path not specified, using latest UOB export: {export_path}"
            )

        # parse scraped on date from uob export filename
        path = Path(export_path)
        scraped_date = parse_scraped_on(path.name).isoformat()

        log.info(f"Transforming UOB export: {export_path}")
        out_path = f"staging/by=uob/date={scraped_date}/{path.stem}.pq"

        with BytesIO() as export:
            await lake.download_fileobj(Key=export_path, Fileobj=export)  # type: ignore
            df = pd.read_excel(export)
        with BytesIO() as out_pq:
            extract_uob(df).to_parquet(out_pq)
            # seek buffer to start of parquet file
            out_pq.seek(0)
            await lake.upload_fileobj(Key=out_path, Fileobj=out_pq)  # type: ignore

    return out_path


@flow
async def ingest_uob(bucket: str, export_path: Optional[str] = None):
    """Ingest UOB export at given path.

    Args:
        bucket: Name of bucket to stage ingested data.
        export_path: Optional. Path of the UOB XLSX export to ingest. If unspecified,
            Ingests the latest export file by filename.
    """
    await transform_uob(bucket, export_path)
