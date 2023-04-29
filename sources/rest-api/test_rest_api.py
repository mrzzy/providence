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
from rest_api import ingest_api_s3


@patch("requests.request")
@patch("boto3.client")
def test_ingest_api_s3(s3_client: Mock, request: Mock):
    # test: rejects bad url schemes
    bad_scheme_urls = [
        ["grpc://test", "s3://test/test"],
        ["https://test", "gcs://test/test"],
    ]
    for api_url, s3_url in bad_scheme_urls:
        with pytest.raises(ValueError):
            ingest_api_s3("GET", urlparse(api_url), urlparse(s3_url))

    # test: mocked rest api request & write to s3
    response = Mock(spec=Response)
    response.json.return_value = {}
    response.headers = {"Content-Type": "application/json; charset=utf-8"}
    request.return_value = response

    s3 = Mock()
    s3_client.return_value = s3
    s3_url = "s3://bucket/key"
    api_method, api_url = "GET", "https://test"

    scraped_on = datetime.min

    test_cases = [
        # api_token, expected_headers
        [None, {}],
        ["test", {"Authorization": "Bearer test"}],
    ]

    for api_token, expected_headers in test_cases:
        ingest_api_s3(
            api_method, urlparse(api_url), urlparse(s3_url), api_token, scraped_on
        )

        request.assert_called_with("GET", api_url, headers=expected_headers)
        s3.upload_fileobj.assert_called()
        call_args = s3.upload_fileobj.call_args[0]
        assert (
            call_args[0].getvalue().decode()
            == '{"_rest_api_src_scraped_on": "0001-01-01T00:00:00"}'
        )
        assert call_args[1:] == ("bucket", "key")

    # test: rejects bad content type
    response.headers = {"Content-Type": "application/x-www-form-urlencoded"}
    with pytest.raises(RuntimeError):
        ingest_api_s3(
            api_method, urlparse(api_url), urlparse(s3_url), scraped_on=scraped_on
        )
