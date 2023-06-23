#
# Providence
# REST API Source
# Unit Tests
#

from datetime import datetime
from http import HTTPStatus
from io import BytesIO
import json
from socket import socket
from threading import Thread
from requests import Response
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from unittest.mock import Mock, PropertyMock, patch
from urllib.parse import urlparse

import pytest

from testcontainers.minio import MinioContainer
from rest_api import ingest_api


def allocate_port() -> int:
    """Obtain a free port by binding a socket to port picked by the OS."""
    with socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@patch("requests.request")
@patch("subprocess.run")
@pytest.mark.unit
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


@pytest.mark.integration
def test_ingest_api_minio():
    # setup http server that emulates a rest api
    class RestAPI(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"key":"value"}')
            self.server.shutdown()

    address, port = "127.0.0.1", allocate_port()
    server = ThreadingHTTPServer((address, port), RestAPI)
    thread = Thread(target=server.serve_forever)
    thread.start()

    # ingest from rest api intos minio
    with MinioContainer(image="minio/minio:RELEASE.2023-06-09T07-32-12Z") as minio:
        mc = minio.get_client()
        bucket, obj = "test", "key"
        mc.make_bucket(bucket)

        config = minio.get_config()
        conn_str = f":s3,provider='Minio',access_key_id='{config['access_key']}',secret_access_key='{config['secret_key']}',endpoint='http://{config['endpoint']}'"

        ingest_api(
            "GET", urlparse(f"http://{address}:{port}"), f"{conn_str}:{bucket}/{obj}"
        )

        # test: check for ingested file
        with mc.get_object(bucket, obj) as resp:
            data = json.loads(resp.data.decode())
            assert data["key"] == "value"

    thread.join()
