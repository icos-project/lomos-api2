
import pytest
import os
from unittest import TestCase
import requests
from requests.auth import HTTPBasicAuth
from copy import copy
from base64 import b64encode

from lomos_api2.views_summary import str_to_bool
from lomos_api2.lomos_api2 import app


dataset_a = [
    dict(_id="id01", _source=dict(anomaly_score=0.10, timestamp="2024-01-08T01:00:01.200000Z", log_message="log-msg-01")),
    dict(_id="id02", _source=dict(anomaly_score=0.20, timestamp="2024-01-08T01:00:02.200000Z", log_message="log-msg-02")),
    dict(_id="id03", _source=dict(anomaly_score=0.80, timestamp="2024-01-08T01:00:03.200000Z", log_message="log-msg-03")),
    dict(_id="id04", _source=dict(anomaly_score=0.60, timestamp="2024-01-08T01:00:04.200000Z", log_message="log-msg-04")),
]

testdata_ok = [
    [
        # api_query
        {
            "max_count": 2,
            "min_anomaly_score": 0.50,
            "from_timestamp": "2024-01-08T00:00:00.000000Z",
            "to_timestamp": "2024-01-08T02:00:00.000000Z",
        },
        # expected_response_aggregate
        dict(
            count=2,
            max_anomaly_score=0.8,
            min_anomaly_score=0.6,  # TODO remove from response
        ),
        # expected_response_message_source
        copy(dataset_a[2:4]),
    ],
    [
        {
            "max_count": 1,
            "min_anomaly_score": 0.50,
            "from_timestamp": "2024-01-08T00:00:00.000000Z",
            "to_timestamp": "2024-01-08T02:00:00.000000Z",
        },
        dict(
            count=2,
            max_anomaly_score=0.8,
            min_anomaly_score=0.6,
        ),
        copy(dataset_a[2:3]),
    ],
    [
        {
            "max_count": 10,
            "min_anomaly_score": 0.10,
            "from_timestamp": "2024-01-08T00:00:00.000000Z",
            "to_timestamp": "2024-01-08T02:00:00.000000Z",
        },
        dict(
            count=4,
            max_anomaly_score=0.8,
            min_anomaly_score=0.1,
        ),
        copy(dataset_a[0:4]),
    ],
    [
        {
            "max_count": 10,
            "min_anomaly_score": 0.10,
            "from_timestamp": "2024-01-08T00:00:00.000000Z",
            "to_timestamp": "2024-01-08T01:00:01.200001Z",
        },
        dict(
            count=1,
            max_anomaly_score=0.1,
            min_anomaly_score=0.1,
        ),
        copy(dataset_a[0:1]),
    ],
    [
        {
            "max_count": 10,
            "min_anomaly_score": 0.10,
            "from_timestamp": "2024-01-08T01:00:02.201000Z",
            "to_timestamp": "2024-01-08T02:00:00.000000Z",
        },
        dict(
            count=2,
            max_anomaly_score=0.8,
            min_anomaly_score=0.6,
        ),
        copy(dataset_a[2:4]),
    ],
    # surprise, microsecond time resolution is not respected :/
    [
        {
            "max_count": 10,
            "min_anomaly_score": 0.10,
            "from_timestamp": "2024-01-08T01:00:02.200999Z",
            "to_timestamp": "2024-01-08T02:00:00.000000Z",
        },
        dict(
            count=3,
            max_anomaly_score=0.8,
            min_anomaly_score=0.2,
        ),
        copy(dataset_a[1:4]),
    ],
    [
        {
        },
        dict(
            count=4,
            max_anomaly_score=0.8,
            min_anomaly_score=0.1,
        ),
        copy(dataset_a[0:4]),
    ],
]

testdata_err = [
    [
        {
            "max_count": "not-int",
            "min_anomaly_score": 0.50,
            "from_timestamp": "2024-01-08T00:00:00.000000Z",
            "to_timestamp": "2024-01-08T02:00:00.000000Z",
        },
        "dummy",
    ],
    [
        {
            "max_count": 1,
            "min_anomaly_score": "not-float",
            "from_timestamp": "2024-01-08T00:00:00.000000Z",
            "to_timestamp": "2024-01-08T02:00:00.000000Z",
        },
        "dummy",
    ],
    [
        {
            "max_count": 1,
            "min_anomaly_score": 0.50,
            "from_timestamp": "not-date",
            "to_timestamp": "2024-01-08T02:00:00.000000Z",
        },
        "dummy",
    ],
    [
        {
            "max_count": 1,
            "min_anomaly_score": 0.50,
            "from_timestamp": "2024-01-08T00:00:00.000000Z",
            "to_timestamp": "2024-01-08T02:00:00.000000",  # not Z
        },
        "dummy",
    ],
    [
        {
            "max_count": 1,
            "min_anomaly_score": 0.50,
            "from_timestamp": "2024-01-08T00:00:00.000000Z",
            "to_timestamp": "2024-01-08T02:00:00.000000",  # not Z
        },
        "dummy",
    ],
]

class Test_top_anomaly:
    def setUp(self):
        api_url = os.environ["FLASK_LOMOS_OPENSEARCH_API_URL"]
        index_name = os.environ["FLASK_LOMOS_INDEX_NAME"]
        cert_verify = str_to_bool(os.environ["FLASK_LOMOS_OPENSEARCH_API_CERTIFICATE_VERIFY"])
        basic_auth = HTTPBasicAuth("admin", "admin")

        response = requests.delete(
            f"{api_url}/{index_name}",
            auth=basic_auth,
            verify=cert_verify,
        )
        assert response.ok or response.status_code == 404

        for doc in dataset_a:
            response = requests.put(
                f"{api_url}/{index_name}/_doc/{doc['_id']}",
                json=doc['_source'],
                auth=basic_auth,
                verify=False,
            )
            assert response.status_code == 201
        response = requests.post(
            f"{api_url}/{index_name}/_refresh",
            auth=basic_auth,
            verify=False,
        )
        assert response.status_code == 200

    @pytest.mark.parametrize("api_query,expected_response_aggregate,expected_response_message_source", testdata_ok)
    def test_ok(self, api_query, expected_response_aggregate, expected_response_message_source):
        expected_response_message_source.sort(reverse=True, key=lambda obj: obj["_source"]["anomaly_score"])
        headers = {
            "Authorization": "Bearer " + b64encode(b"tkn1").decode("utf8"),
        }
        response = app.test_client().get("/api/top_anomaly", headers=headers, query_string=api_query)
        
        assert response.status_code == 200
        assert expected_response_aggregate == response.json["aggregate"]
        for ii, msg in enumerate(response.json["messages"]):
            assert expected_response_message_source[ii]["_source"] == msg["_source"]

    @pytest.mark.parametrize("api_query,dummy", testdata_err)
    def test_ok(self, api_query, dummy):
        headers = {
            "Authorization": "Bearer " + b64encode(b"tkn1").decode("utf8"),
        }
        response = app.test_client().get("/api/top_anomaly", headers=headers, query_string=api_query)
        
        assert response.status_code == 400
        assert ["detail"] == list(response.json.keys())
