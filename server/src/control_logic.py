import json
import re
import subprocess
import control_api
import utils
import asyncio
import Database
import os

# Retrieve constants from environment variables
JSON_PATH = os.getenv("JSON_PATH")
DOCKER_FILES_PATH = os.getenv("DOCKER_FILES_PATH")
API_HOST = os.getenv("API_HOST")
API_PORT = int(os.getenv("API_PORT"))
REPORT_METRICS_SECONDS = int(os.getenv("REPORT_METRICS_SECONDS"))

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_ADMIN_TOKEN = os.getenv("INFLUXDB_ADMIN_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

current_service = None
available_services = []

def initialize():
    global current_service

    load_json_config()
    start_container(available_services[0])
    current_service = available_services[0]

    control_api.run_api_server(API_HOST, API_PORT)
    # Begin reporting metrics
    asyncio.run(report_metrics())


def switch_to_service(service):
    global current_service
    if current_service is not None:
        stop_container(current_service)

    start_container(service)
    current_service = service


def load_json_config():
    bench_config_file = open(JSON_PATH, 'r')
    parsed_config = json.load(bench_config_file)
    frameworks = parsed_config['Frameworks']
    for framework in frameworks:
        available_services.append(framework["name"])

    bench_config_file.close()


def start_container(container_name):
    image_name = f"benchmark_{container_name}"

    # Check if image already exists
    check_image_command = ["docker", "images", "-q", image_name]
    result = subprocess.run(check_image_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.stdout.strip():
        print(f"Image {image_name} already exists. Skipping build.")
    else:
        # Build image
        build_command = [
            "docker", "build",
            "-f", f"{DOCKER_FILES_PATH}/{container_name}/Dockerfile",
            "-t", image_name,
            f"{DOCKER_FILES_PATH}/{container_name}/"  # Context directory
        ]

        try:
            print(f"Building image {image_name}...")
            subprocess.run(build_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"Image {image_name} built successfully.")
        except subprocess.CalledProcessError as e:
            print("Error building image:", e.stderr)
            return  # Exit if build failed

    # Check if container already exists
    check_container_command = ["docker", "ps", "-a", "-q", "-f", f"name=^{container_name}$"]
    result = subprocess.run(check_container_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    container_id = result.stdout.strip()
    if container_id:
        print(f"Container {container_name} already exists. Removing...")
        try:
            subprocess.run(["docker", "rm", "-f", container_id], check=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)
            print(f"Container {container_name} removed.")
        except subprocess.CalledProcessError as e:
            print(f"Error removing existing container {container_name}:", e.stderr)
            return  # Exit if cannot remove

    # Run the container
    run_command = [
        "docker", "run", "-d",
        "-p", "80:80",
        "--name", container_name,
        image_name
    ]

    try:
        result = subprocess.run(run_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"Container {container_name} started successfully. Container ID:", result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print("Error starting container:", e.stderr)


def stop_container(container_name):
    try:
        subprocess.run(["docker", "stop", container_name], check=True)
        print(f"Container {container_name} stopped successfully.")
    except subprocess.CalledProcessError as e:
        print("Error stopping container:", e.stderr)

    try:
        subprocess.run(["docker", "rm", container_name], check=True)
        print(f"Container {container_name} removed successfully.")
    except subprocess.CalledProcessError as e:
        print("Error removing container:", e.stderr)


def collect_container_stats(container_name):
    stats_command = [
        "docker", "stats", container_name, "-a", "--no-stream", "--format", "{{ json . }}"
    ]

    try:
        stats_result = subprocess.run(stats_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True)
        parsed_stats = json.loads(stats_result.stdout.strip())

        block_io_write = re.search(r"\A\d+\.*\d*\w+", parsed_stats["BlockIO"]).group(0)
        block_io_read = re.search(r"\d+\.*\d*\w+$", parsed_stats["BlockIO"]).group(0)  #
        cpu_usage_perc = re.search(r"\A\d+\.*\d*\w+", parsed_stats["CPUPerc"]).group(0)
        container_id = parsed_stats["ID"]
        mem_usage_perc = re.search(r"\A\d+\.*\d*\w+", parsed_stats["MemPerc"]).group(0)
        mem_usage = re.search(r"\A\d+\.*\d*\w+", parsed_stats["MemUsage"]).group(0)
        mem_usable = re.search(r"\d+\.*\d*\w+$", parsed_stats["MemUsage"]).group(0)  #
        net_io_sent = re.search(r"\A\d+\.*\d*\w+", parsed_stats["NetIO"]).group(0)
        net_io_received = re.search(r"\d+\.*\d*\w+$", parsed_stats["NetIO"]).group(0)  #

        block_io_write_MB = utils.convert_to_mb(block_io_write)
        block_io_read_MB = utils.convert_to_mb(block_io_read)
        mem_usage_MB = utils.convert_to_mb(mem_usage)
        mem_usable_MB = utils.convert_to_mb(mem_usable)
        net_io_sent_MB = utils.convert_to_mb(net_io_sent)
        net_io_receive_MB = utils.convert_to_mb(net_io_received)

        return container_name, cpu_usage_perc, container_id, mem_usage_perc, block_io_write_MB, block_io_read_MB, mem_usage_MB, mem_usable_MB, net_io_sent_MB, net_io_receive_MB

    except Exception as e:
        print("collect_container_stats() error: ", e)


async def report_metrics():
    while True:
        collect_container_stats(current_service)
        await asyncio.sleep(REPORT_METRICS_SECONDS)
