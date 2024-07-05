# lomos-api2
# Copyright © 2022-2024 XLAB d.o.o.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This work has received funding from the European Union's HORIZON research
# and innovation programme under grant agreement No. 101070177.

from flask import Blueprint
from flask import current_app as app
from flask import jsonify, request
import flask_login

from datetime import datetime
import elasticsearch
import opensearchpy

# strptime will parse "2024-01-08T00:00:01.200000Z"
# strftime will print "2024-01-08T00:00:01.200000+0000"
_time_format = "%Y-%m-%dT%H:%M:%S.%f%z"
summary_api = Blueprint('summary', __name__, url_prefix="/summary")


def _date_from_str(ts_str):
    if not ts_str:
        return None
    ts = datetime.strptime(ts_str, _time_format)
    # timezone info required
    if not ts.tzinfo:
        raise ValueError("Missing timezone")
    return ts


def _date_to_str(ts):
    if not ts:
        return ""
    # timezone info required
    assert ts.tzinfo
    return ts.strftime(_time_format)

def str_to_bool(ss: str) -> bool:
    if ss.lower() in ["0", "0.0", "f", "false", "n", "no"]:
        return False
    return True

@summary_api.route('/top_anomaly')
@flask_login.login_required
def top_anomaly():
    from_timestamp_str = request.args.get("from_timestamp")
    to_timestamp_str = request.args.get("to_timestamp")
    min_anomaly_score_str = request.args.get("min_anomaly_score", "0.0")
    max_count_str = request.args.get("max_count", "10")
    try:
        time_from = _date_from_str(from_timestamp_str)
    except ValueError as ex:
        return jsonify(dict(detail=f"invalid input from_timestamp={from_timestamp_str} - exception {str(ex)}")), 400
    try:
        time_to = _date_from_str(to_timestamp_str)
    except ValueError as ex:
        return jsonify(dict(detail=f"invalid input to_timestamp={to_timestamp_str} - exception {str(ex)}")), 400
    try:
        min_anomaly_score = float(min_anomaly_score_str)
    except ValueError as ex:
        return jsonify(dict(detail=f"invalid input min_anomaly_score={min_anomaly_score_str} - exception {str(ex)}")), 400
    try:
        max_count = int(max_count_str)
    except ValueError as ex:
        return jsonify(dict(detail=f"invalid input max_count={max_count_str} - exception {str(ex)}")), 400
    print(f"params time_from={time_from} time_to={time_to} min_anomaly_score={min_anomaly_score} max_count={max_count}")

    # src_es = elasticsearch.Elasticsearch(hosts=[app.config["LOMOS_OPENSEARCH_API_URL"]])
    verify_certs = str_to_bool(app.config["LOMOS_OPENSEARCH_API_CERTIFICATE_VERIFY"])
    username = app.config["LOMOS_OPENSEARCH_API_USERNAME"]
    password = app.config["LOMOS_OPENSEARCH_API_PASSWORD"]
    if username and password:
        http_auth = (username, password)
    else:
        assert not username
        assert not password
        http_auth = None
    src_os = opensearchpy.OpenSearch(
        hosts=[app.config["LOMOS_OPENSEARCH_API_URL"]],
        http_auth=http_auth,
        verify_certs=verify_certs,
        ssl_show_warn=verify_certs,
    )
    try:
        docs = os_get_docs(src_os, app.config["LOMOS_INDEX_NAME"], time_from, time_to, min_anomaly_score)
    except (elasticsearch.NotFoundError, opensearchpy.exceptions.NotFoundError) as ex:
        return jsonify(dict(detail=f"Failed to get documents from server, exception={str(ex)}")), 400

    docs.sort(
        # some messages lack anomaly_score - the first 100 messages for example
        key=lambda doc: doc["_source"]["anomaly_score"],
        reverse=True,
    )

    min_anomaly_score = None
    max_anomaly_score = None
    if docs:
        min_anomaly_score = docs[-1]["_source"]["anomaly_score"]
        max_anomaly_score = docs[0]["_source"]["anomaly_score"]

    data = dict(
        aggregate=dict(
            count=len(docs),
            min_anomaly_score=min_anomaly_score,
            max_anomaly_score=max_anomaly_score,
        ),
        messages=docs[:max_count],
    )
    return jsonify(dict(data))


def os_get_docs(os: opensearchpy.OpenSearch, index_name: str, time_from: datetime, time_to: datetime, min_anomaly_score: float) -> list[dict]:
    # get all docs, or maybe only some (anomaly_score > 0.8, etc).
    time_from_str = _date_to_str(time_from)
    time_to_str = _date_to_str(time_to)
    time_range = dict()
    if time_from_str:
        time_range["gte"] = time_from_str
    if time_to_str:
        time_range["lte"] = time_to_str
    query = {
        "query": {
            "bool": {
                "filter": [],
            },
        },
    }
    if time_range:
        query["query"]["bool"]["filter"].append(
            # timestamp or @timestamp or ...
            {"range": {"timestamp": time_range}}
        )
    # this also ensure we return only docs with anomaly_score set
    query["query"]["bool"]["filter"].append(
        {"range": {"anomaly_score": {"gte": str(min_anomaly_score)}}}
    )

    # For elasticsearch
    # docs = elasticsearch.helpers.scan(es,
    #     query=query,
    #     index=index_name,
    #     size=10_000,
    # )
    # documents = [dd for dd in docs]

    # For opensearch
    docs = opensearchpy.helpers.scan(
        os,
        query=query,
        index=index_name,
        size=10_000,
    )
    documents = [dd for dd in docs]

    # print(documents)
    print(f"doc count {len(documents)}")
    return documents
