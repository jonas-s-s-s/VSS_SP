import json
from types import SimpleNamespace
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone

from influxdb_client.rest import ApiException


class Database:
    def __init__(self, params):
        self.params = SimpleNamespace(**params)
        self.client = InfluxDBClient(
            url=self.params.INFLUXDB_URL,
            token=self.params.INFLUXDB_ADMIN_TOKEN,
            org=self.params.INFLUXDB_ORG
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

    def get_benchmark_measurements_names(self, bucket):
        result = []
        query = f'import "influxdata/influxdb/schema" schema.measurements(bucket: "{bucket}")'

        tables = self.query_api.query(query=query)
        # Query returns a list of tables, each table contains some records (rows)
        for table in tables:
            for record in table.records:
                # Those are the names of the measurements
                result.append(record['_value'])

        # Remove all non-framework measurements
        result.remove("test_case_start_times")
        result.remove("server_metrics")

        return result

    def get_measurement_fields(self, bucket, measurement):
        result = []
        query = f'''
        import "influxdata/influxdb/schema"
        
        schema.measurementFieldKeys(
            bucket: "{bucket}",
            measurement: "{measurement}",
        )
        '''
        tables = self.query_api.query(query=query)
        for table in tables:
            for record in table.records:
                result.append(record['_value'])

        return result

    def get_field_mean(self, bucket, measurement, field, from_hours):
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: -{from_hours}h)
            |> filter(fn: (r) => r._measurement == "{measurement}")
            |> filter(fn: (r) => r._field == "{field}")
            |> group()
            |> mean()
        '''

        try:
            tables = self.query_api.query(query=query)
        except:
            # This will be returned for all fields which aren't of int or float type
            return None
        # Return value of the first table's first record
        return tables[0].records[0].values['_value']

    def all_fields_mean(self, bucket, measurement, from_hours):
        fields = self.get_measurement_fields(bucket, measurement)
        results_dict = {}

        for field in fields:
            results_dict[field] = self.get_field_mean(bucket, measurement, field, from_hours)

        return results_dict

    def get_modes_of_measurement(self, bucket, measurement, from_hours):
        result = []
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -{from_hours}h)
          |> filter(fn: (r) => r["_measurement"] == "{measurement}")
          |> filter(fn: (r) => r["_field"] == "mode")
          |> group()
          |> keep(columns: ["_value"])
          |> unique()
        '''
        tables = self.query_api.query(query=query)
        for table in tables:
            for record in table.records:
                result.append(record['_value'])

        return result

    def get_field_mean_at_mode(self, bucket, measurement, field, mode, from_hours):
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -{from_hours}h)
          |> filter(fn: (r) => r["_measurement"] == "{measurement}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> filter(fn: (r) => r["mode"] == "{mode}")
          |> keep(columns: ["_time", "{field}"])
          |> group()
          |> mean(column: "{field}")
        '''

        try:
            tables = self.query_api.query(query=query)
        except:
            return None
        return tables[0].records[0].values[field]

    def all_fields_mean_at_mode(self, bucket, measurement, mode, from_hours):
        fields = self.get_measurement_fields(bucket, measurement)
        results_dict = {}

        for field in fields:
            results_dict[field] = self.get_field_mean_at_mode(bucket, measurement, field, mode, from_hours)

        return results_dict

    def get_measurement_test_cases(self, bucket, measurement, from_hours):
        result = []
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: -{from_hours}h)
              |> filter(fn: (r) => r["_measurement"] == "{measurement}")
              |> filter(fn: (r) => r["_field"] == "test_case_id")
              |> group()
              |> keep(columns: ["_value"])
              |> unique()
            '''
        tables = self.query_api.query(query=query)
        for table in tables:
            for record in table.records:
                result.append(record['_value'])

        return result

    def get_field_mean_at_mode_case(self, bucket, measurement, field, mode, case, from_hours):
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -{from_hours}h)
          |> filter(fn: (r) => r["_measurement"] == "{measurement}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> filter(fn: (r) => r["mode"] == "{mode}")
          |> filter(fn: (r) => r["test_case_id"] == "{case}")
          |> keep(columns: ["_time", "{field}"])
          |> group()
          |> mean(column: "{field}")
        '''

        try:
            tables = self.query_api.query(query=query)
        except:
            return None
        return tables[0].records[0].values[field]

    def all_fields_mean_at_mode_case(self, bucket, measurement, mode, case, from_hours):
        fields = self.get_measurement_fields(bucket, measurement)
        results_dict = {}

        for field in fields:
            results_dict[field] = self.get_field_mean_at_mode_case(bucket, measurement, field, mode, case, from_hours)

        return results_dict

    def joined_measurement(self, bucket, measurement, from_hours):
        # A list containing dictionaries which have the fields of this measurement, the fields include start time which
        # was obtained by joining it via test_case_uuid with test_case_start_times
        resulting_measurements = []
        query = f'''
            endResults = from(bucket: "{bucket}")
              |> range(start: -{from_hours}h)
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => exists r.test_case_uuid)
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            
            startTime = from(bucket: "{bucket}")
              |> range(start: -{from_hours}h)
              |> filter(fn: (r) => r._measurement == "test_case_start_times")
              |> filter(fn: (r) => exists r.test_case_uuid)
            
            join(
              tables: {{first: endResults, second: startTime}},
              on: ["test_case_uuid"]
            ) 
            |> drop(columns: ["_start_first", "_start_second", "_stop_first","_stop_second", "_measurement_second", "_measurement_first", "_value", "_field"])
            |> group()
        '''

        tables = self.query_api.query(query=query)
        for table in tables:
            for record in table.records:
                resulting_measurements.append(record.values)

        return resulting_measurements

    def get_server_metrics(self, bucket, measurement, from_hours):
        # Gets all server metrics that are associated with this measurement (i.e. framework / container)
        resulting_metrics = []
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -{from_hours}h)
          |> filter(fn: (r) => r["_measurement"] == "server_metrics")
          |> filter(fn: (r) => r["container_name"] == "{measurement}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> group()
          |> drop(columns: ["_start", "_stop", "_measurement", "container_name"])
        '''

        tables = self.query_api.query(query=query)
        for table in tables:
            for record in table.records:
                resulting_metrics.append(record.values)

        return resulting_metrics
