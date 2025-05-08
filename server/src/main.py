import os
import BenchmarkController as cl
from dotenv import load_dotenv
import Database as db
import atexit
import HwInfoLib

database = None
controller = None


def main():
    load_dotenv(dotenv_path='../config.env')

    env_vars = {
        "JSON_PATH": os.getenv("JSON_PATH"),
        "DOCKER_FILES_PATH": os.getenv("DOCKER_FILES_PATH"),
        "API_HOST": os.getenv("API_HOST"),
        "API_PORT": int(os.getenv("API_PORT")),
        "REPORT_METRICS_MS": int(os.getenv("REPORT_METRICS_MS")),
        "SAMPLE_METRICS_MS": int(os.getenv("SAMPLE_METRICS_MS")),
        "INFLUXDB_URL": os.getenv("INFLUXDB_URL"),
        "INFLUXDB_ADMIN_TOKEN": os.getenv("INFLUXDB_ADMIN_TOKEN"),
        "INFLUXDB_ORG": os.getenv("INFLUXDB_ORG"),
        "INFLUXDB_BUCKET": os.getenv("INFLUXDB_BUCKET")
    }

    global database, controller

    database = db.Database(env_vars)

    # Save HW info of this system into DB
    hw_info_string = HwInfoLib.get_minimal_html_report()
    database.write_hw_info_server(hw_info_string)

    controller = cl.BenchmarkController(env_vars, database)
    controller.initialize()


def on_exit():
    global controller
    print("Program is exiting...")
    controller.shutdown()


if __name__ == '__main__':
    atexit.register(on_exit)
    main()
