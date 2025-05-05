import os
import Database

import site_generator
import statistics


def main():
    env_vars = {
        "INFLUXDB_URL": os.getenv("INFLUXDB_URL"),
        "INFLUXDB_ADMIN_TOKEN": os.getenv("INFLUXDB_ADMIN_TOKEN"),
        "INFLUXDB_ORG": os.getenv("INFLUXDB_ORG"),
        "INFLUXDB_BUCKET": os.getenv("INFLUXDB_BUCKET")
    }
    db = Database.Database(env_vars)

    bucket = "benchmark_bucket"
    FROM_HOURS = 24

    # Get all measurements from benchmark bucket
    measurements = db.get_benchmark_measurements_names(bucket)
    print(measurements)

    print()
    total_run_count = db.get_total_uuid_count(bucket)
    print("Total executed TCs:", total_run_count)
    for measurement in measurements:
        mrc = db.get_measurement_uuid_count(bucket, measurement)
        print(f"\t{measurement} executed TCs: {mrc}")
    print()

    # Stats for a specific measurement (framework)
    for measurement in measurements:
        print("===================================================")
        print(">", measurement)
        print("===================================================")
        # Get all test cases for this measurement
        test_cases = db.get_measurement_test_cases(bucket, measurement, FROM_HOURS)
        print(f"Test Cases:", test_cases)

        # Get all measurement modes for this measurement
        mm = db.get_modes_of_measurement(bucket, measurement, FROM_HOURS)
        print(f"Modes:", mm)

        # Mean of all measurement fields across all modes and test cases
        afm = db.all_fields_mean(bucket, measurement, FROM_HOURS)
        print("Mean of all fields over all modes and TCs:", afm)

        ################################################################################################################
        server_metrics_analysis(FROM_HOURS, bucket, db, measurement)
        print()
        ################################################################################################################

        mm.sort()
        # Get mean of all fields for a specific mode over all test cases
        for mode in mm:
            spec_m = db.all_fields_mean_at_mode(bucket, measurement, mode, FROM_HOURS)
            print(f"Mean of all fields for {mode} mode over all TCs:", spec_m)

            server_metrics_analysis_mode(FROM_HOURS, bucket, db, measurement, mode)

            # Mean of all fields for a specific mode and test case
            for tc in test_cases:
                spec_m_tc = db.all_fields_mean_at_mode_case(bucket, measurement, mode, tc, FROM_HOURS)
                print(f"\tMean of all fields for {mode} mode and {tc} TC:", spec_m_tc)
            print()
        print()


def server_metrics_analysis(FROM_HOURS, bucket, db, measurement):
    # Get all server metrics associated with this framework container
    sm = db.get_server_metrics(bucket, measurement, FROM_HOURS)
    # Get all rows of this measurement's table, joined with start times
    jm = db.joined_measurement(bucket, measurement, FROM_HOURS)
    # We can now calculate the mean Mem / CPU usage for this measurement over all modes and TCs
    # We know the start and end time of each TC (this is in jm), so we need to get all metrics from sm which
    # fall into the interval of any sm item
    measurement_server_metrics = []
    for server_metrics_item in sm:
        item_time = server_metrics_item["_time"]
        # Check if this item_time is in any jm interval
        for test_case_item in jm:
            tc_start_time = test_case_item["_time_second"]
            tc_end_time = test_case_item["_time_first"]

            start = min(tc_start_time, tc_end_time)
            end = max(tc_start_time, tc_end_time)

            if start <= item_time <= end:
                # Server metrics item's time is inside jm interval
                measurement_server_metrics.append(server_metrics_item)
                break

    # Collect metrics we are interested im
    s_cpu_mean, s_memory_mean, s_memory_perc_mean = process_server_metrics(measurement_server_metrics)
    print("Mean CPU % over all modes and TCs:", s_cpu_mean)
    print("Mean Memory % over all modes and TCs:", s_memory_perc_mean)
    print("Mean Memory megabytes over all modes and TCs:", s_memory_mean)

def server_metrics_analysis_mode(FROM_HOURS, bucket, db, measurement, mode):
    sm = db.get_server_metrics(bucket, measurement, FROM_HOURS)
    jm = db.joined_measurement(bucket, measurement, FROM_HOURS)

    measurement_server_metrics = []
    for server_metrics_item in sm:
        # Skip all items which don't belong to this mode
        if server_metrics_item["mode"] != mode:
            continue

        item_time = server_metrics_item["_time"]
        for test_case_item in jm:
            # Skip all items which don't belong to this mode
            if test_case_item["mode"] != mode:
                continue
            tc_start_time = test_case_item["_time_second"]
            tc_end_time = test_case_item["_time_first"]

            start = min(tc_start_time, tc_end_time)
            end = max(tc_start_time, tc_end_time)

            if start <= item_time <= end:
                measurement_server_metrics.append(server_metrics_item)
                break

    # Collect metrics we are interested im
    s_cpu_mean, s_memory_mean, s_memory_perc_mean = process_server_metrics(measurement_server_metrics)
    print(f"Mean CPU % over {mode} and all TCs:", s_cpu_mean)
    print(f"Mean Memory % over {mode} and all TCs:", s_memory_perc_mean)
    print(f"Mean Memory megabytes over {mode} and all TCs:", s_memory_mean)


def process_server_metrics(measurement_server_metrics):
    s_cpu = []
    s_memory = []
    s_memory_perc = []
    for s_filtered_metric in measurement_server_metrics:
        s_cpu.append(s_filtered_metric["cpu_usage_perc"])
        s_memory.append(s_filtered_metric["mem_usage_MB"])
        s_memory_perc.append(s_filtered_metric["mem_usage_perc"])

    s_cpu_mean = None
    s_memory_mean = None
    s_memory_perc_mean = None
    if len(s_cpu) > 0:
        s_cpu_mean = statistics.fmean(s_cpu)
    if len(s_memory) > 0:
        s_memory_mean = statistics.fmean(s_memory)
    if len(s_memory_perc) > 0:
        s_memory_perc_mean = statistics.fmean(s_memory_perc)
    return s_cpu_mean, s_memory_mean, s_memory_perc_mean


if __name__ == '__main__':
    main()
