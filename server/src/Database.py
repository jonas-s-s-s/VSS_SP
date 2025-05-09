import json
from types import SimpleNamespace
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone


class Database:
    def __init__(self, params):
        self.params = SimpleNamespace(**params)
        self.client = InfluxDBClient(
            url=self.params.INFLUXDB_URL,
            token=self.params.INFLUXDB_ADMIN_TOKEN,
            org=self.params.INFLUXDB_ORG
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def ping_db(self):
        if not self.client.ping():
            print("Failed to ping InfluxDB instance. Aborting DB write operation.")
            return False
        return True

    def write_server_metrics(self, container_name, mode, cpu_usage_perc, container_id, mem_usage_perc,
                             block_io_write_MB,
                             block_io_read_MB, mem_usage_MB, mem_usable_MB, net_io_sent_MB, net_io_receive_MB
                             , measurement="server_metrics", time=None):
        point = self.create_server_metric_point(container_name, mode, cpu_usage_perc, container_id, mem_usage_perc,
                                                block_io_write_MB, block_io_read_MB, mem_usage_MB, mem_usable_MB,
                                                net_io_sent_MB,
                                                net_io_receive_MB, measurement, time)
        if not self.ping_db():
            return

        self.write_api.write(bucket=self.params.INFLUXDB_BUCKET, record=point)

    def write_server_metrics_bulk(self, points):
        if not self.ping_db():
            return

        self.write_api.write(bucket=self.params.INFLUXDB_BUCKET, record=points)

    def create_server_metric_point(self, container_name, mode, cpu_usage_perc, container_id, mem_usage_perc,
                                   block_io_write_MB, block_io_read_MB, mem_usage_MB, mem_usable_MB, net_io_sent_MB,
                                   net_io_receive_MB, measurement="server_metrics", time=None):
        point = Point(measurement)

        point.tag("container_name", container_name)
        point.field("mode", mode)
        point.field("cpu_usage_perc", cpu_usage_perc)
        point.field("container_id", container_id)
        point.field("mem_usage_perc", mem_usage_perc)
        point.field("block_io_write_MB", block_io_write_MB)
        point.field("block_io_read_MB", block_io_read_MB)
        point.field("mem_usage_MB", mem_usage_MB)
        point.field("mem_usable_MB", mem_usable_MB)
        point.field("net_io_sent_MB", net_io_sent_MB)
        point.field("net_io_receive_MB", net_io_receive_MB)
        if time is None:
            time = datetime.now(tz=timezone.utc)
        return point.time(time)

    def write_hw_info(self, info_string, measurement, time=None):
        point = Point(measurement)
        point.field("info_string", info_string)

        # Add time
        if time is None:
            time = datetime.now(tz=timezone.utc)
        point = point.time(time)

        if not self.ping_db():
            return

        self.write_api.write(bucket=self.params.INFLUXDB_BUCKET, record=point)

    def write_hw_info_client(self, info_string, time=None):
        self.write_hw_info(info_string, measurement="client_hw_info", time=time)

    def write_hw_info_server(self, info_string, time=None):
        self.write_hw_info(info_string, measurement="server_hw_info", time=time)
