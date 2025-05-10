from types import SimpleNamespace
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

# Define all DB measurements which do NOT contain data about framework here
NON_FRAMEWORK_MEASUREMENTS = ["test_case_start_times", "server_metrics", "server_hw_info", "client_hw_info"]


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

    def ping_db(self):
        return self.client.ping()

    def get_benchmark_measurements_names(self, bucket, start_time, stop_time):
        result = []
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
          |> keep(columns: ["_measurement"])
          |> unique(column: "_measurement")
          |> group()
        '''

        tables = self.query_api.query(query=query)
        # Query returns a list of tables, each table contains some records (rows)
        for table in tables:
            for record in table.records:
                measurement_name = record.values.get("_measurement")
                if measurement_name not in NON_FRAMEWORK_MEASUREMENTS:
                    result.append(measurement_name)
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

    def get_total_test_case_count(self, bucket, start_time, stop_time):
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
          |> filter(fn: (r) => r["_measurement"] == "test_case_start_times")
          |> group()
          |> keep(columns: ["test_case_uuid"])
          |> count(column: "test_case_uuid")
        '''
        tables = self.query_api.query(query=query)
        return tables[0].records[0].values["test_case_uuid"]

    def get_test_case_count_per_measurement(self, bucket, measurement, start_time, stop_time):
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
          |> filter(fn: (r) => r["_measurement"] == "test_case_start_times" and r["_value"] == "{measurement}")
          |> group()
          |> keep(columns: ["test_case_uuid"])
          |> count(column: "test_case_uuid")
        '''
        tables = self.query_api.query(query=query)
        return tables[0].records[0].values["test_case_uuid"]

    def get_field_mean(self, bucket, measurement, field, start_time, stop_time):
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: {start_time}, stop: {stop_time})
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
        return tables[0].records[0].values['_value']

    def all_fields_mean(self, bucket, measurement, start_time, stop_time):
        fields = self.get_measurement_fields(bucket, measurement)
        return {field: self.get_field_mean(bucket, measurement, field, start_time, stop_time) for field in fields}

    def get_modes_of_measurement(self, bucket, measurement, start_time, stop_time):
        result = []
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
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

    def get_field_mean_at_mode(self, bucket, measurement, field, mode, start_time, stop_time):
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
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

    def all_fields_mean_at_mode(self, bucket, measurement, mode, start_time, stop_time):
        fields = self.get_measurement_fields(bucket, measurement)
        return {
            field: self.get_field_mean_at_mode(bucket, measurement, field, mode, start_time, stop_time)
            for field in fields
        }

    def get_measurement_test_cases(self, bucket, measurement, start_time, stop_time):
        result = []
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: {start_time}, stop: {stop_time})
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

    def get_field_mean_at_mode_case(self, bucket, measurement, field, mode, case, start_time, stop_time):
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
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

    def all_fields_mean_at_mode_case(self, bucket, measurement, mode, case, start_time, stop_time):
        fields = self.get_measurement_fields(bucket, measurement)
        return {
            field: self.get_field_mean_at_mode_case(bucket, measurement, field, mode, case, start_time, stop_time)
            for field in fields
        }

    def joined_measurement(self, bucket, measurement, start_time, stop_time):
        # A list containing dictionaries which have the fields of this measurement, the fields include start time which
        # was obtained by joining it via test_case_uuid with test_case_start_times
        resulting_measurements = []
        query = f'''
            endResults = from(bucket: "{bucket}")
              |> range(start: {start_time}, stop: {stop_time})
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => exists r.test_case_uuid)
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            
            startTime = from(bucket: "{bucket}")
              |> range(start: {start_time}, stop: {stop_time})
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

    def get_server_metrics(self, bucket, measurement, start_time, stop_time):
        # Gets all server metrics that are associated with this measurement (i.e. framework / container)
        resulting_metrics = []
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
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

    def get_oldest_record(self, bucket, start_time, stop_time):
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
          |> keep(columns: ["_time"])
          |> min(column: "_time")
        '''
        tables = self.query_api.query(query=query)
        return tables[0].records[0].values["_time"]

    def get_newest_record(self, bucket, start_time, stop_time):
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
          |> keep(columns: ["_time"])
          |> max(column: "_time")
        '''
        tables = self.query_api.query(query=query)
        return tables[0].records[0].values["_time"]

    def get_last_hw_info(self, bucket, measurement, start_time, stop_time):
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
          |> filter(fn: (r) => r["_measurement"] == "{measurement}")
          |> filter(fn: (r) => r["_field"] == "info_string")
          |> last()
        '''
        tables = self.query_api.query(query=query)
        return {
            "time": tables[0].records[0].values["_time"].strftime('%Y-%m-%d %H:%M:%S %Z%z'),
            "value": tables[0].records[0].values["_value"]
        }

    def get_last_server_hw_info(self, bucket, start_time, stop_time):
        try:
            return self.get_last_hw_info(bucket, "server_hw_info", start_time, stop_time)
        except:
            return {"time": "NaN", "value": "No Server HW Data"}

    def get_last_client_hw_info(self, bucket, start_time, stop_time):
        try:
            return self.get_last_hw_info(bucket, "client_hw_info", start_time, stop_time)
        except:
            return {"time": "NaN", "value": "No Client HW Data"}
