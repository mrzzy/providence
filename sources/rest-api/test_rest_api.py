#
# Providence
# REST API Source
# Unit Tests
#

from datetime import datetime
from io import BytesIO
from requests import Response
from unittest.mock import Mock, PropertyMock, patch
from urllib.parse import urlparse

import pytest
from rest_api import ingest_api


@patch("requests.request")
@patch("subprocess.run")
def test_ingest_api(subprocess_run: Mock, request: Mock):
    # test: rejects bad url schemes
    bad_scheme_urls = [
        "grpc://test",
        "tcp://test",
    ]
    target_path = ":s3,key=value:/target/path"
    for api_url in bad_scheme_urls:
        with pytest.raises(ValueError):
            ingest_api("GET", urlparse(api_url), target_path)

    # test: mocked rest api request & write with rclone
    response = Mock(spec=Response)
    response.json.return_value = {}
    response.headers = {"Content-Type": "application/json; charset=utf-8"}
    request.return_value = response
    api_method, api_url = "GET", "https://test"
    scraped_on = datetime.min
    test_cases = [
        # api_token, expected_headers
        [None, {}],
        ["test", {"Authorization": "Bearer test"}],
    ]

    for api_token, expected_headers in test_cases:
        ingest_api(api_method, urlparse(api_url), target_path, api_token, scraped_on)

        request.assert_called_with("GET", api_url, headers=expected_headers)
        subprocess_run.assert_called_with(
            ["rclone", "rcat", target_path],
            input=b'{"_rest_api_src_scraped_on": "0001-01-01T00:00:00"}',
            capture_output=True,
            check=True,
        )

    # test: rejects bad content type
    response.headers = {"Content-Type": "application/x-www-form-urlencoded"}
    with pytest.raises(RuntimeError):
        ingest_api(api_method, urlparse(api_url), target_path, scraped_on=scraped_on)
