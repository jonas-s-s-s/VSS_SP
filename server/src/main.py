import os
import BenchmarkController as cl
from dotenv import load_dotenv
import Database as db
import atexit

database = None
controller = None


def main():
    load_dotenv(dotenv_path='../config.env')

    env_vars = {
        "JSON_PATH": os.getenv("JSON_PATH"),
        "DOCKER_FILES_PATH": os.getenv("DOCKER_FILES_PATH"),
        "API_HOST": os.getenv("API_HOST"),
        "API_PORT": int(os.getenv("API_PORT")),
        "REPORT_METRICS_SECONDS": int(os.getenv("REPORT_METRICS_SECONDS")),
        "INFLUXDB_URL": os.getenv("INFLUXDB_URL"),
        "INFLUXDB_ADMIN_TOKEN": os.getenv("INFLUXDB_ADMIN_TOKEN"),
        "INFLUXDB_ORG": os.getenv("INFLUXDB_ORG"),
        "INFLUXDB_BUCKET": os.getenv("INFLUXDB_BUCKET")
    }

    global database, controller

    database = db.Database(env_vars)
    controller = cl.BenchmarkController(env_vars, database)
    controller.initialize()


def on_exit():
    global controller
    print("Program is exiting...")
    controller.shutdown()


if __name__ == '__main__':
    atexit.register(on_exit)
    main()
