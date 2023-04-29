#
# Providence
# REST API Source
# Unit Tests
#

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
    response.content = b"{}"
    request.return_value = response
    s3 = Mock()
    s3_client.return_value = s3

    api_method, api_url = "GET", "https://test"

    test_cases = [
        # api_token, expected_headers
        [None, {}],
        ["test", {"Authorization": "Bearer test"}],
    ]

    for api_token, expected_headers in test_cases:
        ingest_api_s3(
            api_method, urlparse(api_url), urlparse("s3://bucket/key"), api_token
        )

        request.assert_called_with("GET", api_url, headers=expected_headers)
        s3.upload_fileobj.assert_called()
        call_args = s3.upload_fileobj.call_args[0]
        assert call_args[0].getbuffer() == response.content
        assert call_args[1:] == ("bucket", "key")
