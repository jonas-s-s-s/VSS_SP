import os
import statistics
from datetime import timezone

import Database

BUCKET = "benchmark_bucket"
FROM_HOURS = os.getenv("OLDEST_ALLOWED_DATA_SAMPLE","24")


def get_framework_data():
    db = Database.Database(_load_env_vars())

    # Check DB connection
    if not db.ping_db():
        print("Error: Cannot connect to the Database.")
        print("Make sure that the DB IP and secrets in config.env are correct.")
        exit(1)

    # Measurement = a single table inside of InfluxDB benchmark_bucket
    # Each framework has its own measurement (table)
    # A measurement contains fields (columns)

    # Get all measurement (framework) names from the DB
    measurements = db.get_benchmark_measurements_names(BUCKET)

    return {
        "time_range": _get_time_range_summary(db),
        "measurements": measurements,
        "total_run_count": db.get_total_uuid_count(BUCKET),
        "measurements_data": {
            m: _process_measurement(db, m) for m in measurements
        }
    }


def _load_env_vars():
    """
    Load env variables for DB
    """
    return {
        "INFLUXDB_URL": os.getenv("INFLUXDB_URL"),
        "INFLUXDB_ADMIN_TOKEN": os.getenv("INFLUXDB_ADMIN_TOKEN"),
        "INFLUXDB_ORG": os.getenv("INFLUXDB_ORG"),
        "INFLUXDB_BUCKET": os.getenv("INFLUXDB_BUCKET")
    }


def _get_time_range_summary(db):
    """
    Get time of the newest and oldest record from DB
    """
    oldest = db.get_oldest_record(BUCKET, FROM_HOURS).replace(tzinfo=timezone.utc)
    newest = db.get_newest_record(BUCKET, FROM_HOURS).replace(tzinfo=timezone.utc)
    print("Oldest data sample:", oldest)
    print("Newest data sample:", newest)
    return {
        "oldest": oldest.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
        "newest": newest.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    }


def _process_measurement(db, measurement):
    """
    Gathers information about a single measurement (framework)
    :param db: db object
    :param measurement: string name of the measurement (framework)
    :return:
    """
    print("\nProcessing measurement:", measurement)
    test_cases = db.get_measurement_test_cases(BUCKET, measurement, FROM_HOURS)
    print("Test cases:", test_cases)
    modes = db.get_modes_of_measurement(BUCKET, measurement, FROM_HOURS)
    print("Modes:", modes)
    return {
        # How many test cases were executed for this framework (each has its own UUID)
        "uuid_count": db.get_measurement_uuid_count(BUCKET, measurement),
        # Names of all test case types that were executed for this framework
        "test_cases": test_cases,
        # All modes of this framework (i.e. raw, sql, ...)
        "modes": modes,
        # Mean of all the framework's fields (over all test cases and modes)
        "all_fields_mean": db.all_fields_mean(BUCKET, measurement, FROM_HOURS),
        # Get all server metrics which contain the name of this framework
        "server_metrics": _aggregate_server_metrics(db, measurement),
        # Get mean and server metrics for all the different modes (this includes test case metrics as nested struct)
        "modes_data": {
            mode: _process_mode(db, measurement, mode, test_cases)
            for mode in sorted(modes)
        }
    }


def _process_mode(db, measurement, mode, test_cases):
    """
    Gather information about a certain mode (of specified framework)
    Includes info of each test case as nested struct
    """
    print("Processing mode:", mode)
    return {
        "mean_fields": db.all_fields_mean_at_mode(BUCKET, measurement, mode, FROM_HOURS),
        "server_metrics": _aggregate_server_metrics(db, measurement, mode=mode),
        "test_cases": {
            tc: _process_test_case(db, measurement, mode, tc)
            for tc in test_cases
        }
    }


def _process_test_case(db, measurement, mode, tc):
    """
    Gathers server metrics and mean of all fields of a specified test case (of mode and framework)
    """
    print("Processing test case:", tc)
    return {
        "mean_fields": db.all_fields_mean_at_mode_case(BUCKET, measurement, mode, tc, FROM_HOURS),
        "server_metrics": _aggregate_server_metrics(db, measurement, mode=mode, test_case=tc)
    }


def _aggregate_server_metrics(db, measurement, mode=None, test_case=None):
    """
    This function can:
    1) Collect server metrics of all modes and test cases of a measurement (framework)
    2) Collect server metrics of a SPECIFIC mode and all test cases of a measurement
    3) Collect server metrics of a SPECIFIC mode and SPECIFIC test cases of a measurement
    """
    server_metrics = db.get_server_metrics(BUCKET, measurement, FROM_HOURS)
    joined_measurement_fields = db.joined_measurement(BUCKET, measurement, FROM_HOURS)
    print("Collecting server metrics:", measurement, mode, test_case)

    # This makes the for loop be able to skip over items that aren't "relevant"
    # I.e. if either a mode or a test_case is specified, we need to skip those which don't match them
    def is_relevant(item, ref):
        if mode and item.get("mode") != mode:
            return False
        if test_case and ref.get("test_case_id") != test_case:
            return False
        if mode and ref.get("mode") != mode:
            return False
        return True

    matched_metrics = []
    for sm_field in server_metrics:
        sm_time = sm_field["_time"]
        for jm_field in joined_measurement_fields:
            # Skip this joined_measurement field if it's of incorrect mode or test_case
            if not is_relevant(sm_field, jm_field):
                continue
            # Sort to make sure that start is the earlier time value
            start, end = sorted([jm_field["_time_first"], jm_field["_time_second"]])
            # Add sm_field to matched_metrics if it's in the time interval of this joined_measurement field
            if start <= sm_time <= end:
                matched_metrics.append(sm_field)
                break

    return _summarize_server_metrics(matched_metrics)


def _summarize_server_metrics(metrics):
    """
    Extracts CPU and Memory from the server metrics struct
    """
    cpu = [m["cpu_usage_perc"] for m in metrics if "cpu_usage_perc" in m]
    mem = [m["mem_usage_MB"] for m in metrics if "mem_usage_MB" in m]
    mem_perc = [m["mem_usage_perc"] for m in metrics if "mem_usage_perc" in m]

    return {
        "cpu_mean_perc": statistics.fmean(cpu) if cpu else None,
        "memory_mean_MB": statistics.fmean(mem) if mem else None,
        "memory_mean_perc": statistics.fmean(mem_perc) if mem_perc else None
    }
