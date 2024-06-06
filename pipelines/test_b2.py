#
# Providence
# Integration Tests
# B2 Storage Integration
#

import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory, tempdir
from uuid import uuid4
from jinja2.bccache import Bucket
import pytest
from b2 import b2_bucket, download_path, upload_path


@pytest.mark.asyncio
async def test_b2_upload_download_path(prefect):
    with TemporaryDirectory() as src_dir:
        # create test files for upload
        paths, content = ["a", "b", "c"], "TEST"
        for path in paths:
            with open(os.path.join(src_dir, path), "w") as f:
                f.write(content)

        async with b2_bucket(os.environ["PVD_LAKE_BUCKET"]) as bucket:
            # test upload
            test_key = f"test-{uuid4()}"
            await upload_path(bucket, Path(src_dir), test_key)

            with TemporaryDirectory() as dest_dir:
                # test download
                await download_path(bucket, test_key, Path(dest_dir))

                # check contents of downloaded paths
                for path in paths:
                    with open(os.path.join(dest_dir, path)) as f:
                        assert f.read() == content
            # cleanup test files
            await bucket.objects.filter(Prefix=test_key).delete()  # type: ignore
