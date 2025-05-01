import json
from types import SimpleNamespace
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone


class Database:
    def __init__(self, params):
        self.params = SimpleNamespace(**params)
        self.client = InfluxDBClient(
            url=self.params.influxdb_url,
            token=self.params.influxdb_token,
            org=self.params.influxdb_org
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def write_test_case_result_json(self, mode, test_case_id, data, test_case_uuid, measurement="default_test_case",
                                    time=None):
        result = data.get("result", {})
        point = Point(measurement)
        point.tag("test_case_uuid", test_case_uuid)
        point.field("mode", mode)
        point.field("test_case_id", test_case_id)

        # Add time
        if time is None:
            time = datetime.now(tz=timezone.utc)
        point = point.time(time)

        # Remove nested fields
        def flatten_and_add_fields(prefix, d):
            for k, v in d.items():
                key = f"{prefix}_{k}" if prefix else k
                if isinstance(v, dict):
                    flatten_and_add_fields(key, v)
                elif isinstance(v, list):
                    # Convert the list to JSON string
                    point.field(key, json.dumps(v))
                elif isinstance(v, int):
                    point.field(key, float(v))
                else:
                    point.field(key, v)

        flatten_and_add_fields("", result)
        try:
            self.write_api.write(bucket=self.params.influxdb_bucket, record=point)
        except Exception as e:
            print("Failed to write point:", e)

    def write_test_case_start(self, case_name, test_case_uuid, measurement="test_case_start_times", time=None):
        point = Point(measurement)
        point.tag("test_case_uuid", test_case_uuid)
        point.field("case_name", case_name)

        # Add time
        if time is None:
            time = datetime.now(tz=timezone.utc)
        point = point.time(time)

        self.write_api.write(bucket=self.params.influxdb_bucket, record=point)
