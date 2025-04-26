import json
import subprocess
from types import SimpleNamespace
import uuid


class HttpBenchmark:
    def __init__(self, params, db, api_client):
        # Convert dict to "SimpleNamespace" so it can be accessed via "dot notation"
        self.params = SimpleNamespace(**params)
        self.db = db
        self.api_client = api_client

    def run_benchmark(self):
        print("-----------------------------------------------------------------------------------------------------")
        bench_config_file = open(self.params.benchmark_config_file, 'r')
        parsed_config = json.load(bench_config_file)
        test_cases = parsed_config['TestCases']
        frameworks = parsed_config['Frameworks']

        for i, framework in enumerate(frameworks):
            framework_name = framework['name']
            print(f"Framework {i + 1}/{len(frameworks)}: {framework_name}")
            for j, test_case in enumerate(test_cases):
                test_case_id = test_case['id']
                connection_count = test_case['connection_count']
                requests_count = test_case['requests_count']
                http_type = test_case['http_type']
                print(f"Test case {j + 1}/{len(test_cases)}: {test_case_id}")

                test_case_name = f"{framework_name}_{test_case_id}"
                test_case_uuid = str(uuid.uuid4())
                # Write test case start into DB
                self.db.write_test_case_start(test_case_name, test_case_uuid)
                # Run the test case
                self.test_case(test_case_uuid, connection_count, requests_count, http_type,
                               test_case_name)

        bench_config_file.close()

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
