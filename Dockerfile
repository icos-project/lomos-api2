# syntax=docker/dockerfile:1
FROM python:3.9-slim-buster AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git=1:2.20.* && apt-get clean
COPY requirements-dev.txt /app/
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY ./ /app/
RUN python -m build . -v


# ===================================================================
FROM python:3.9-slim-buster
WORKDIR /app

RUN pip install --no-cache-dir gunicorn==21.2.0

COPY --from=builder /app/dist /app/dist
RUN pip install --no-cache-dir /app/dist/lomos_api2*.whl

EXPOSE 25001
# CMD flask --app lomos_api2.lomos_api2:app --debug run --host=0.0.0.0
CMD ["gunicorn", "--bind", "0.0.0.0:25001", "lomos_api2.lomos_api2:app"]
