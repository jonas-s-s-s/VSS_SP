import asyncio
import json
import subprocess
import threading
from datetime import datetime, timezone
from types import SimpleNamespace

import ApiServer as api
import utils


class BenchmarkController:

    def __init__(self, params, db):
        self.params = SimpleNamespace(**params)
        self.db = db
        self.current_service = None
        self.current_mode = None
        self.available_services = []
        self.available_modes = []
        self.api_server = None

        self.metrics_report_buffer = []
        self.metrics_last_report_timestamp = None

    def initialize(self):
        """
        Loads JSON config, enables the async function for reporting metrics, starts the API server
        """
        self.load_json_config()
        if self.available_services:
            self.switch_to_service(self.available_services[0], self.available_modes[0])

        self.api_server = api.ApiServer(self.params.API_HOST, self.params.API_PORT, self)
        flask_thread = threading.Thread(target=self.api_server.run)
        flask_thread.daemon = True
        flask_thread.start()

        try:
            asyncio.run(self.report_metrics())
        except KeyboardInterrupt:
            print("Stopping metrics reporting.")

    def load_json_config(self):
        """
        Loads the available benchmark services and modes from the JSON config
        """
        try:
            with open(self.params.JSON_PATH, 'r') as file:
                parsed_config = json.load(file)
                self.available_services = [framework["name"] for framework in parsed_config["Frameworks"]]
                self.available_modes = [mode["mode"] for mode in parsed_config["Modes"]]
        except Exception as e:
            print(f"Failed to load JSON configuration: {e}")

    def compose_up(self, service_name, mode):
        """
        Runs docker compose up for the specified service
        """
        compose_up_cmd = [
            "docker", "compose", "--project-directory",
            f"{self.params.DOCKER_FILES_PATH}/{service_name}/{mode}", "up", "-d"
        ]

        try:
            subprocess.run(compose_up_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Docker compose went up: {service_name}, {mode}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error bringing docker compose up: {service_name}: {e.stderr}")
            return False

    def compose_down(self, service_name, mode):
        """
        Runs docker compose down for the specified service
        """
        compose_up_cmd = [
            "docker", "compose", "--project-directory",
            f"{self.params.DOCKER_FILES_PATH}/{service_name}/{mode}", "down"
        ]

        try:
            self.current_service = None
            self.current_mode = None
            subprocess.run(compose_up_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Docker compose went down: {service_name}, {mode}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error bringing docker compose down: {service_name}: {e.stderr}")
            return False

    def switch_to_service(self, service, mode):
        """
        Switches to the specified service, stopping the current one if needed
        """
        if service not in self.available_services:
            print(f"Service {service} is not available.")
            return

        if self.current_service is not None:
            self.compose_down(self.current_service, self.current_mode)

        success = self.compose_up(service, mode)
        if success:
            self.current_service = service
            self.current_mode = mode
        else:
            print(f"Failed to switch to service {service}")

    async def report_metrics(self):
        """
        Periodically reports system metrics for the active container
        """
        while True:
            if self.current_service:
                stats = self.collect_container_stats(self.current_service)
                # Append collected stats to the buffer
                if stats:
                    self.metrics_report_buffer.append({
                        "time": datetime.now(tz=timezone.utc),
                        "stats": stats,
                        "service": self.current_service,
                        "mode": self.current_mode,
                    })

                ms_since_last_report = (
                    datetime.now(tz=timezone.utc) - self.metrics_last_report_timestamp
                    if self.metrics_last_report_timestamp else None
                )

                # Check if it's time to send stats to server and empty buffer
                if ms_since_last_report is None or ms_since_last_report.total_seconds() * 1000.0 > self.params.REPORT_METRICS_MS:
                    self.metrics_last_report_timestamp = datetime.now(tz=timezone.utc)
                    points = []
                    for metric in self.metrics_report_buffer:
                        stats = metric["stats"]
                        point = self.db.create_server_metric_point(
                            metric["service"],
                            metric["mode"],
                            stats["cpu_usage"],
                            stats["container_id"],
                            stats["mem_usage_perc"],
                            stats["block_io_write_mb"],
                            stats["block_io_read_mb"],
                            stats["mem_usage_mb"],
                            stats["mem_usable_mb"],
                            stats["net_io_sent_mb"],
                            stats["net_io_received_mb"],
                            "server_metrics",
                            metric["time"]
                        )
                        points.append(point)

                    if points:
                        self.db.write_server_metrics_bulk(points)
                    self.metrics_report_buffer.clear()

            # Sleep till next sampling period
            await asyncio.sleep(self.params.SAMPLE_METRICS_MS / 1000.0)

    def collect_container_stats(self, container_name):
        """
        Collects stats for the specified container
        """
        stats_cmd = [
            "docker", "stats", container_name,
            "-a", "--no-stream", "--format", "{{ json . }}"
        ]
        try:
            result = subprocess.run(stats_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            data = json.loads(result.stdout.strip())

            block_io = data["BlockIO"].split()
            block_io_write = block_io[0]
            block_io_read = block_io[-1]

            cpu_usage = data["CPUPerc"].strip()[:-1]
            mem_usage_perc = data["MemPerc"].strip()[:-1]

            mem_usage = data["MemUsage"].split()[0]
            mem_usable = data["MemUsage"].split()[-1]

            net_io = data["NetIO"].split()
            net_io_sent = net_io[0]
            net_io_received = net_io[-1]

            return {
                "cpu_usage": float(cpu_usage),
                "container_id": data["ID"],
                "mem_usage_perc": float(mem_usage_perc),
                "block_io_write_mb": utils.convert_to_mb(block_io_write),
                "block_io_read_mb": utils.convert_to_mb(block_io_read),
                "mem_usage_mb": utils.convert_to_mb(mem_usage),
                "mem_usable_mb": utils.convert_to_mb(mem_usable),
                "net_io_sent_mb": utils.convert_to_mb(net_io_sent),
                "net_io_received_mb": utils.convert_to_mb(net_io_received)
            }
        except Exception as e:
            print(f"Error collecting container stats: {e}")
            return None

    def shutdown(self):
        """
        Intended to run before exiting the program
        """
        if self.current_service:
            self.compose_down(self.current_service, self.current_mode)
