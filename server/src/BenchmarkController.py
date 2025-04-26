import json
import re
import subprocess
import threading

import ApiServer as api
import utils
import asyncio
from types import SimpleNamespace


class BenchmarkController:

    def __init__(self, params, db):
        self.params = SimpleNamespace(**params)
        self.db = db
        self.current_service = None
        self.available_services = []
        self.api_server = None

    def initialize(self):
        """
        Loads JSON config, enables the async function for reporting metrics, starts the API server
        """
        self.load_json_config()
        if self.available_services:
            self.switch_to_service(self.available_services[0])

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
        Loads the available benchmark services from the JSON config
        """
        try:
            with open(self.params.JSON_PATH, 'r') as file:
                parsed_config = json.load(file)
                self.available_services = [framework["name"] for framework in parsed_config["Frameworks"]]
        except Exception as e:
            print(f"Failed to load JSON configuration: {e}")

    def start_container(self, container_name):
        """
        Builds and starts a Docker container for the specified service
        """
        image_name = f"benchmark_{container_name}"
        check_image_cmd = ["docker", "images", "-q", image_name]
        image_result = subprocess.run(check_image_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if not image_result.stdout.strip():
            build_cmd = [
                "docker", "build",
                "-f", f"{self.params.DOCKER_FILES_PATH}/{container_name}/Dockerfile",
                "-t", image_name,
                f"{self.params.DOCKER_FILES_PATH}/{container_name}/"
            ]
            try:
                print("Building docker image")
                subprocess.run(build_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"Successfully built image {image_name}")
            except subprocess.CalledProcessError as e:
                print(f"Error building image {image_name}: {e.stderr}")
                return False

        check_container_cmd = ["docker", "ps", "-a", "-q", "-f", f"name=^{container_name}$"]
        container_result = subprocess.run(check_container_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          text=True)
        if container_result.stdout.strip():
            container_id = container_result.stdout.strip()
            try:
                subprocess.run(["docker", "rm", "-f", container_id], check=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
                print(f"Removed existing container {container_name}")
            except subprocess.CalledProcessError as e:
                print(f"Error removing container {container_name}: {e.stderr}")
                return False

        run_cmd = [
            "docker", "run", "-d",
            "-p", "80:80",
            "--name", container_name,
            image_name
        ]
        try:
            subprocess.run(run_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Started container {container_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error starting container {container_name}: {e.stderr}")
            return False

    def stop_container(self, container_name):
        """
        Stops and removes the specified Docker container
        """
        try:
            subprocess.run(["docker", "stop", container_name], check=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
            print(f"Stopped container {container_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error stopping container {container_name}: {e.stderr}")
            return

        try:
            subprocess.run(["docker", "rm", container_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Removed container {container_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error removing container {container_name}: {e.stderr}")

    def switch_to_service(self, service):
        """
        Switches to the specified service, stopping the current one if needed
        """
        if service not in self.available_services:
            print(f"Service {service} is not available.")
            return

        if self.current_service is not None:
            self.stop_container(self.current_service)

        success = self.start_container(service)
        if success:
            self.current_service = service
        else:
            print(f"Failed to switch to service {service}")

    async def report_metrics(self):
        """
        Periodically reports system metrics for the active container
        """
        while True:
            if self.current_service:
                stats = self.collect_container_stats(self.current_service)
                if stats:
                    self.db.write_server_metrics(
                        self.current_service,
                        stats["cpu_usage"],
                        stats["container_id"],
                        stats["mem_usage_perc"],
                        stats["block_io_write_mb"],
                        stats["block_io_read_mb"],
                        stats["mem_usage_mb"],
                        stats["mem_usable_mb"],
                        stats["net_io_sent_mb"],
                        stats["net_io_received_mb"]
                    )
            await asyncio.sleep(self.params.REPORT_METRICS_SECONDS)

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
