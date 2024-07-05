
import pytest
from unittest import TestCase
from mock import patch, Mock

from base64 import b64encode
from lomos_api2.views_summary import top_anomaly  
from lomos_api2.lomos_api2 import app


class Test_top_anomaly(TestCase):
    @patch("opensearchpy.helpers.scan")
    def test_ok(self, mock_scan):
        dataset_a = [
            # dict(_source=dict(_id="id01", anomaly_score=0.10, timestamp="2024-01-08T01:00:01.200000Z", log_message="log-msg-01")),
            # dict(_source=dict(_id="id02", anomaly_score=0.20, timestamp="2024-01-08T01:00:02.200000Z", log_message="log-msg-02")),
            dict(_source=dict(_id="id03", anomaly_score=0.80, timestamp="2024-01-08T01:00:03.200000Z", log_message="log-msg-03")),
            dict(_source=dict(_id="id04", anomaly_score=0.60, timestamp="2024-01-08T01:00:04.200000Z", log_message="log-msg-04")),
        ]

        api_query = {
            "max_count": 2,
            "min_anomaly_score": 0.50,
            "from_timestamp": "2024-01-08T00:00:00.000000Z",
            "to_timestamp": "2024-01-08T02:00:00.000000Z",
        }
        expected_os_query = {
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": "2024-01-08T00:00:00.000000+0000",
                                    "lte": "2024-01-08T02:00:00.000000+0000"
                                }
                            }
                        },
                        {
                            "range": {
                                "anomaly_score": {
                                    "gte": "0.5"
                                }
                            }
                        }
                    ]
                }
            }
        }
        mock_scan.return_value = dataset_a
        expected_response = dict(
            aggregate=dict(
                count=2,
                max_anomaly_score=0.8,
                min_anomaly_score=0.6,
            ),
            messages=dataset_a,
        )

        headers = {
            "Authorization": "Bearer " + b64encode(b"tkn1").decode("utf8"),
        }
        response = app.test_client().get("/api/top_anomaly", headers=headers, query_string=api_query)
        
        assert response.status_code == 200
        assert expected_response == response.json
        mock_scan.assert_called_once()
        mock_scan_args, mock_scan_kwargs = mock_scan.call_args
        assert expected_os_query == mock_scan_kwargs["query"]
