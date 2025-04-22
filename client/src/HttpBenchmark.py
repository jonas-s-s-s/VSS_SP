import json
import subprocess
from types import SimpleNamespace


class HttpBenchmark:
    def __init__(self, params, db):
        self.params = SimpleNamespace(**params)
        self.db = db

    def run_benchmark(self, connection_count=10, requests_count=1000, service_name="default"):
        cmd = [
            "bombardier",
            "-c", str(connection_count),
            "-n", str(requests_count),
            self.params.server_url,
            "-l",
            "--print=r",
            "--format=j"
        ]
        print("Running benchmark...")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"Done. Connections: {connection_count}. Requests: {requests_count}. Service: {service_name}")
            self.db.write_result_json(data, f"C{connection_count}_R{requests_count}_{service_name}")
        else:
            print(f"Benchmark command failed with return code {result.returncode}")
            print(f"Error output: {result.stderr}")
