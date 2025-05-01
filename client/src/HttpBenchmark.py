import json
import subprocess
from types import SimpleNamespace
import uuid
import time


class HttpBenchmark:
    def __init__(self, params, db, api_client):
        # Convert dict to "SimpleNamespace" so it can be accessed via "dot notation"
        self.params = SimpleNamespace(**params)
        self.db = db
        self.api_client = api_client

        # Load test cases from config file
        bench_config_file = open(self.params.benchmark_config_file, 'r')
        parsed_config = json.load(bench_config_file)
        self.test_cases = parsed_config['TestCases']
        bench_config_file.close()

        # Get list of frameworks from server
        self.frameworks = []
        services_parsed = self.api_client.list_services()
        print(
            "-----------------------------------------------------------------------------------------------------")
        print("Server has the following framework services:")
        for service in services_parsed['services']:
            print("\t", service)
            self.frameworks.append(service)

        # Get list of modes from server:
        self.modes = []
        modes_parsed = self.api_client.list_modes()
        print(
            "-----------------------------------------------------------------------------------------------------")
        print("Server has the following modes:")
        for mode in modes_parsed['modes']:
            print("\t", mode)
            self.modes.append(mode)

    def run_benchmark(self):
        print("-----------------------------------------------------------------------------------------------------")

        for i, framework in enumerate(self.frameworks):
            print(f"> Framework {i + 1}/{len(self.frameworks)}: {framework}")

            for j, mode in enumerate(self.modes):
                print(f"> Mode {j + 1}/{len(self.modes)}: {mode}")
                # Check what framework + mode the server is running
                current_framework = self.api_client.get_current_service()['currentService']
                current_mode = self.api_client.get_current_service()['mode']

                if not current_framework == framework or not current_mode == mode:
                    # Call server API - switch to this framework + mode
                    print("Calling server API, change to:", framework, mode)
                    result = self.api_client.change_service(framework, mode)
                    if result is not None:
                        print("Change OK, sleeping for", self.params.sleep_interval, "ms...")
                        time.sleep(int(self.params.sleep_interval) / 1000.0)
                    else:
                        print("Change failed, skipping framework:", framework)
                        continue

                for k, test_case in enumerate(self.test_cases):
                    test_case_id = test_case['id']
                    connection_count = test_case['connection_count']
                    requests_count = test_case['requests_count']
                    http_type = test_case['http_type']
                    print(f"> Test case {k + 1}/{len(self.test_cases)}: {test_case_id}")

                    test_case_name = f"{framework}_{test_case_id}"
                    test_case_uuid = str(uuid.uuid4())
                    # Write test case start into DB
                    self.db.write_test_case_start(test_case_name, test_case_uuid)
                    # Run the test case
                    self.test_case(test_case_uuid, connection_count, requests_count, http_type,
                                   test_case_name)

    def test_case(self, test_case_uuid, connection_count=10, requests_count=1000, http_type="http1",
                  test_case_name="default"):
        cmd = [
            "bombardier",
            "-c", str(connection_count),
            "-n", str(requests_count),
            "-l",
            "--print=r",
            "--format=j",
            f"--{http_type}",
            self.params.server_url
        ]

        print("Running test case...")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(
                f"Done. Connections: {connection_count}. Requests: {requests_count}. Test case name: {test_case_name}")
            print("The results are:")
            print(json.dumps(data, indent=4, sort_keys=True))
            self.db.write_test_case_result_json(data, test_case_uuid, test_case_name)
            print(
                "-----------------------------------------------------------------------------------------------------")
        else:
            print(f"Benchmark command failed with return code {result.returncode}")
            print(f"Error output: {result.stderr}")
