import os
import Database

import site_generator


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

    # Stats for a specific measurement (framework)
    for measurement in measurements:
        print(">", measurement)

        # Get all test cases for this measurement
        test_cases = db.get_measurement_test_cases(bucket, measurement, FROM_HOURS)
        print(f"Test Cases:", test_cases)

        # Get all measurement modes for this measurement
        mm = db.get_modes_of_measurement(bucket, measurement, FROM_HOURS)
        print(f"Modes:",mm)

        # Mean of all measurement fields across all modes and test cases
        afm = db.all_fields_mean(bucket, measurement, FROM_HOURS)
        print("Mean of all fields over all modes and TCs:", afm)

        # Get mean of all fields for a specific mode over all test cases
        for mode in mm:
            spec_m = db.all_fields_mean_at_mode(bucket, measurement, mode, FROM_HOURS)
            print(f"Mean of all fields for {mode} mode over all TCs:", spec_m)
            # Mean of all fields for a specific mode and test case
            for tc in test_cases:
                spec_m_tc = db.all_fields_mean_at_mode_case(bucket, measurement, mode, tc, FROM_HOURS)
                print(f"\tMean of all fields for {mode} mode and {tc} TC:", spec_m_tc)

        print()


if __name__ == '__main__':
    main()
