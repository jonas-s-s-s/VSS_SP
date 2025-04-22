import os
import sys

from HttpBenchmark import HttpBenchmark
from Database import Database


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

    # Check for required variables
    if not all([server_url, influxdb_url, influxdb_token, influxdb_org, influxdb_bucket]):
        print("Error: One or more required environment variables are missing.")
        sys.exit(1)

    parameters_all = {
        "server_url": server_url,
        "influxdb_url": influxdb_url,
        "influxdb_token": influxdb_token,
        "influxdb_org": influxdb_org,
        "influxdb_bucket": influxdb_bucket,
    }

    # Create objects and pass params
    db = Database(parameters_all)
    http_benchmark = HttpBenchmark(parameters_all, db)

    # Run actions
    http_benchmark.run_benchmark()


if __name__ == '__main__':
    main()
