from datetime import timezone, datetime

from jinja2 import Environment, FileSystemLoader
import os
import shutil

BUCKET = "benchmark_bucket"
FROM_HOURS = 24


def generate(db):
    env = Environment(loader=FileSystemLoader('templates'))

    time_now = datetime.now(timezone.utc)
    dt_oldest = db.get_oldest_record(BUCKET, FROM_HOURS)
    dt_newest = db.get_newest_record(BUCKET, FROM_HOURS)

    dt_utc_o = dt_oldest.replace(tzinfo=timezone.utc)
    old_date = dt_utc_o.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    dt_utc_n = dt_newest.replace(tzinfo=timezone.utc)
    new_date = dt_utc_n.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    time_now_str = time_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    # Get all measurements from benchmark bucket
    measurements = db.get_benchmark_measurements_names(BUCKET)
    print(measurements)

    total_run_count = db.get_total_uuid_count(BUCKET)
    measurement_run_count = []
    print("Total executed TCs:", total_run_count)
    for measurement in measurements:
        mrc = db.get_measurement_uuid_count(BUCKET, measurement)
        measurement_run_count.append({'measurement': measurement, 'run_count': mrc})
        print(f"\t{measurement} executed TCs: {mrc}")
    print()

    table_data = [
        {"date": "2023-01-01", "close": 45},
        {"date": "2023-02-01", "close": 50},
        {"date": "2023-03-01", "close": 55},
        {"date": "2023-04-01", "close": 50},
        {"date": "2023-05-01", "close": 45},
        {"date": "2023-06-01", "close": 50},
    ]

    #########################################
    # Prepare nav bar objects
    #########################################
    nav_items = [
        {'label': 'Index', 'href': 'index.html'},
    ]

    #########################################
    # Prepare pages
    #########################################
    pages = [
        {'template': 'index.html', 'output': 'index.html', 'context': {
            "benchmark_results": table_data,
            "measurement_run_count": measurement_run_count,
        }},
    ]

    #########################################
    # Generate each page
    #########################################
    os.makedirs('output', exist_ok=True)
    for page in pages:
        template = env.get_template(page['template'])
        # Merge nav items into each page's context
        context = {
            **page['context'],
            'nav': nav_items,
            "old_date": old_date,
            "new_date": new_date,
            "time_now_str": time_now_str,
            "total_run_count": total_run_count,
        }
        rendered = template.render(**context)
        with open(f"output/{page['output']}", 'w') as f:
            f.write(rendered)

    #########################################
    # Copy the static assets
    #########################################
    shutil.copytree('static', 'output/static', dirs_exist_ok=True)
