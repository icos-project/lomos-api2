# About

LOMOS is a tool for unsupervised anomaly detection in application log files.
Firts AI based model is trained on normal log files -
e.g. logs with no or only small number of anomalies.
Next the model is used to detect anomalious log lines.
Eeach log line is assigned anomaly_score with value 0.0 to 1.0.

lomos-api2 is REST API to get summary about processed logs.
It returns number of log lines with anomaly_score above threashold in given time window.

Why lomos-api2 (and not just api) - because lomos-controller already includes api.

# Usage


Sample API call:

```shell
curl "http://127.0.0.1:5000/api/top_anomaly?min_anomaly_score=0.7&from_timestamp=2024-01-08T00:00:01.200000Z&to_timestamp=2024-01-18T00:00:01.200000Z" -v
```

Sample response:

```json
{
  "aggregate": {
    "count": 1,
    "max_anomaly_score": 0.7692307978868484,
    "min_anomaly_score": 0.7692307978868484
  },
  "messages": [
    {
      "_index": "some_app_backend",
      "_type": "_doc",
      "_id": "D01aa40BjZ7m1DvJ_-y0",
      "_score": 1,
      "_source": {
        "timestamp": "2024-01-17T10:06:03.000014",
        "logs_full": "2024-01-17 10:06:03.000014 DEBUG BaseJdbcLogger:159 - <==    Updates: 1",
        "anomaly_score": 0.7692307978868484
      }
    }
  ]
}
```

# Development

```shell
python3.9 -m venv .venv
source .venv/bin/activate

pip install -e .
cp .env.sample .env
nano .env

flask --app lomos_api2/lomos_api2 --debug run

curl http://127.0.0.1:5000/
# FLASK_LOMOS_API_USER_API_KEY=tkn1 -> dGtuMQ==
curl http://127.0.0.1:5000/auth/whoami -H "Authorization: Bearer dGtuMQ=="
curl "http://127.0.0.1:5000/api/top_anomaly?min_anomaly_score=0.7&from_timestamp=2024-01-08T00:00:01.200000Z&to_timestamp=2024-01-18T00:00:01.200000Z" -v
```

## Testing

Unit tests:

```
pip install -r requirements-dev.txt
pytest --cov=lomos_api2 --cov-report=html --cov-report=term tests/unit -vv
```

Integration tests:

```
docker run --name opensearch -d -p 9200:9200 -p 9600:9600 -e "discovery.type=single-node" -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=5b780509eb354374a48b287e132bde13#T" opensearchproject/opensearch:latest
nano .env
pytest --cov=lomos_api2 --cov-report=html --cov-report=term tests/integration -vv
```

# Build

```shell
LOMOS_API2_VERSION=0.0.1  # TODO use git tag
docker build --build-arg "LOMOS_API2_VERSION=$LOMOS_API2_VERSION" -t lomos-api2:$LOMOS_API2_VERSION .
```

# Run

```shell
docker run -it --name lomos-api2 --rm -p25001:25001 --env-file=.env lomos-api2:$LOMOS_API2_VERSION
# TODO container IP
curl "http://172.17.0.2:25001/api/top_anomaly?min_anomaly_score=0.7&from_timestamp=2024-01-08T00:00:01.200000Z&to_timestamp=2024-01-18T00:00:01.200000Z"
```

or

```shell
kubectl apply -f k8s/lomos-api2.yml
```

# Legal
The lomos-api2 is released under the comercial license.
Copyright © 2022-2024 XLAB d.o.o. All rights reserved.

🇪🇺 This work has received funding from the European Union's HORIZON research and innovation programme under grant agreement No. 101070177.
