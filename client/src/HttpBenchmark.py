import json
import subprocess
from types import SimpleNamespace
import uuid


class HttpBenchmark:
    def __init__(self, params, db):
        self.params = SimpleNamespace(**params)
        self.db = db

    def run_benchmark(self):
        bench_config_file = open(self.params.benchmark_config_file, 'r')
        parsed_config = json.load(bench_config_file)
        test_cases = parsed_config['TestCases']
        frameworks = parsed_config['Frameworks']

        for framework in frameworks:
            framework_name = framework['name']
            for test_case in test_cases:
                test_case_id = test_case['id']
                connection_count = test_case['connection_count']
                requests_count = test_case['requests_count']
                http_type = test_case['http_type']

                test_case_name = f"{framework_name}_{test_case_id}"
                test_case_uuid = str(uuid.uuid4())
                # Write test case start into DB
                self.db.write_test_case_start(test_case_name, test_case_uuid)
                # Run the test case
                self.test_case(test_case_uuid, connection_count, requests_count, http_type,
                               test_case_name)

        bench_config_file.close()

    def test_case(self, test_case_uuid, connection_count=10, requests_count=1000, http_type="http1",
                  service_name="default"):
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

        print("Running benchmark...")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"Done. Connections: {connection_count}. Requests: {requests_count}. Service: {service_name}")
            self.db.write_test_case_result_json(data, f"C{connection_count}_R{requests_count}_{service_name}")
        else:
            print(f"Benchmark command failed with return code {result.returncode}")
            print(f"Error output: {result.stderr}")
