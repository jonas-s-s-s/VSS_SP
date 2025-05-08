import os
import sys
from ApiClient import ApiClient
from HttpBenchmark import HttpBenchmark
from Database import Database
import HwInfoLib


# Gather our code in a main() function
def main():
    print("Loading environment variables...")

    server_url = os.environ.get("SERVER_URL")
    print("SERVER_URL:", server_url)

    influxdb_url = os.environ.get("INFLUXDB_URL")
    influxdb_token = os.environ.get("INFLUXDB_ADMIN_TOKEN")
    influxdb_org = os.environ.get("INFLUXDB_ORG")
    influxdb_bucket = os.environ.get("INFLUXDB_BUCKET")

    print("INFLUXDB_URL:", influxdb_url)
    print("INFLUXDB_ADMIN_TOKEN:", influxdb_token)
    print("INFLUXDB_ORG:", influxdb_org)
    print("INFLUXDB_BUCKET:", influxdb_bucket)

    benchmark_config_file = os.environ.get("BENCHMARK_CONFIG_FILE")
    print("BENCHMARK_CONFIG_FILE:", benchmark_config_file)

    server_api_port = os.environ.get("SERVER_API_PORT")
    print("SERVER_API_PORT:", server_api_port)

    sleep_interval = os.environ.get("SLEEP_INTERVAL")
    print("SLEEP_INTERVAL:", sleep_interval)

    # How many times will the run_benchmark() function be called - used only in this file
    benchmark_runs = os.environ.get("BENCHMARK_RUNS")
    print("BENCHMARK_RUNS:", sleep_interval)

    # Check for required variables
    if not all([server_url, influxdb_url, influxdb_token, influxdb_org, influxdb_bucket, benchmark_config_file,
                server_api_port, sleep_interval]):
        print("Error: One or more required environment variables are missing.")
        sys.exit(1)

    parameters_all = {
        "server_url": server_url,
        "influxdb_url": influxdb_url,
        "influxdb_token": influxdb_token,
        "influxdb_org": influxdb_org,
        "influxdb_bucket": influxdb_bucket,
        "benchmark_config_file": benchmark_config_file,
        "server_api_port": server_api_port,
        "sleep_interval": sleep_interval,
    }

    # Create objects and pass params
    db = Database(parameters_all)
    api_client = ApiClient(f"{server_url}:{server_api_port}")
    http_benchmark = HttpBenchmark(parameters_all, db, api_client)

    # Save HW info of this system into DB
    hw_info_string = HwInfoLib.get_minimal_html_report()
    db.write_hw_info_client(hw_info_string)

    # Run benchmark client - possibly multiple times
    for i in range(int(benchmark_runs)):
        print("-----------------------------------------------------------------------------------------------------")
        print(f"> Starting benchmark client run {i + 1} / {benchmark_runs}")
        http_benchmark.run_benchmark()
        print("-----------------------------------------------------------------------------------------------------")
        print(f"> Finished benchmark client run no. {i + 1}")


if __name__ == '__main__':
    main()
