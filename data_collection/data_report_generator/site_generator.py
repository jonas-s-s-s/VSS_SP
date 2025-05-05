from datetime import timezone, datetime

from jinja2 import Environment, FileSystemLoader
import os
import shutil

BUCKET = "benchmark_bucket"
FROM_HOURS = 24

EXCLUDED_DATA_COLUMNS = ["bytesRead", "bytesWritten", "mode", "others", "req1xx", "req3xx", "req4xx", "req5xx",
                         "test_case_id", "timeTakenSeconds"]

DETAIL_DATA_COLUMNS = ["rps_percentiles_95", "latency_percentiles_95", "latency_max", "rps_max", "latency_stddev",
                       "rps_stddev", "memory_mean_perc"]

DATA_NAME_MAP = {
    "bytesRead": "Bytes Read",
    "bytesWritten": "Bytes Written",
    "latency_max": "Lat Max",
    "latency_mean": "Lat Mean",
    "latency_percentiles_50": "Lat P50",
    "latency_percentiles_75": "Lat P75",
    "latency_percentiles_90": "Lat P90",
    "latency_percentiles_95": "Lat P95",
    "latency_percentiles_99": "Lat P99",
    "latency_stddev": "Lat Stddev",
    "mode": "Mode",
    "others": "Other",
    "req1xx": "Req 1xx",
    "req2xx": "Req 2xx",
    "req3xx": "Req 3xx",
    "req4xx": "Req 4xx",
    "req5xx": "Req 5xx",
    "rps_max": "RPS Max",
    "rps_mean": "RPS Mean",
    "rps_percentiles_50": "RPS P50",
    "rps_percentiles_75": "RPS P75",
    "rps_percentiles_90": "RPS P90",
    "rps_percentiles_95": "RPS P95",
    "rps_percentiles_99": "RPS P99",
    "rps_stddev": "RPS Stddev",
    "test_case_id": "Test Case ID",
    "timeTakenSeconds": "Time Taken (s)",
    "cpu_mean_perc": "CPU %",
    "memory_mean_MB": "Mem MB",
    "memory_mean_perc": "Mem %",
}


# A preprocessing step for data samples (to be displayed in tables)
# First validate the sample and check if it's an excluded field, if that's the case return none
# Then translate the data_name to readable format
def _preprocess_sample(data_name, data_value, exclude_detail=False, float_decimal_places=2):
    p_data_name = data_name
    p_data_value = data_value

    if data_name in EXCLUDED_DATA_COLUMNS:
        return None, None
    if exclude_detail and data_name in DETAIL_DATA_COLUMNS:
        return None, None

    if isinstance(p_data_value, float):
        p_data_value = round(p_data_value, float_decimal_places)

    if p_data_name in DATA_NAME_MAP:
        p_data_name = DATA_NAME_MAP[p_data_name]

    if data_value is None:
        return p_data_name, "NULL"

    return p_data_name, p_data_value


def _create_table_row(data_dict, init_name=None):
    table_row = {}
    if init_name is not None:
        table_row = {"name": init_name}

    for name in data_dict:
        value = data_dict[name]
        p_name, p_value = _preprocess_sample(name, value, True)
        if p_name is None:
            continue
        table_row[p_name] = p_value
    return table_row


def _append_to_table_row(data_dict, table_row):
    for name in data_dict:
        value = data_dict[name]
        p_name, p_value = _preprocess_sample(name, value, True)
        if p_name is None:
            continue
        table_row[p_name] = p_value


def _compute_total_reqs(data_dict, float_decimal_places=2):
    total_reqs = data_dict['others'] + data_dict['req1xx'] + data_dict['req2xx'] + \
                 data_dict['req3xx'] + data_dict['req4xx'] + data_dict['req5xx']
    return round(total_reqs, float_decimal_places)


def _create_metrics_table_row(table_data, server_metrics, framework_metrics, framework_name):
    # Create initial table row
    summary_table_row = _create_table_row(framework_metrics, framework_name)
    # Compute and append the total requests field
    summary_table_row["REQ Total"] = _compute_total_reqs(framework_metrics)
    # Add server metrics to the row
    _append_to_table_row(server_metrics, summary_table_row)
    # Append the complete table row
    table_data.append(summary_table_row)


def _create_mode_summary_graph(modes_list, modes_data, main_x_label, main_y_label, row_field):
    curves = []
    x_labels = modes_list
    curve_labels = []

    # Get the "name" field of each table row (this only needs to taken from one table)
    first_table = modes_data[0]
    for row_data in first_table['data']:
        curve_labels.append(row_data['name'])
        # Initialize the curves array, each name (framework) has its own curve
        curves.append([])
    # We can take the data to create curves from the struct that is used to render the tables
    for mode in modes_data:
        for i, row_data in enumerate(mode['data']):
            value = row_data[row_field]
            # Protect against "NULL" values
            if value == "NULL":
                curves[i].append(0.0)
            else:
                curves[i].append(value)

    return {"curves": curves, "x_labels": x_labels, "curve_labels": curve_labels, "main_x_label": main_x_label,
            "main_y_label": main_y_label}


def generate(framework_data):
    env = Environment(loader=FileSystemLoader('templates'))

    # Data for the timestamp overview table
    datetime_now = datetime.now(timezone.utc)
    current_time = datetime_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    # Data for the table which displays test case run counts
    measurement_run_count = []
    for measurement in framework_data['measurements_data']:
        measurement_run_count.append(
            {
                "name": measurement,
                "run_count": framework_data['measurements_data'][measurement]['uuid_count']
            })

    # Data for the main summary table
    benchmark_results_summary_table_data = []
    for measurement in framework_data['measurements_data']:
        mean_summary_data = framework_data['measurements_data'][measurement]['all_fields_mean']
        _create_metrics_table_row(benchmark_results_summary_table_data,
                                  framework_data['measurements_data'][measurement]['server_metrics'], mean_summary_data,
                                  measurement)

    # Data for the main summary latency mean histogram
    summary_latency_histogram_data = []
    for measurement in framework_data['measurements_data']:
        mean_summary_data = framework_data['measurements_data'][measurement]['all_fields_mean']
        h_row = {"x_label": measurement, "y_value": mean_summary_data['latency_mean']}
        summary_latency_histogram_data.append(h_row)

    # Data for the main summary RPS mean histogram
    summary_rps_histogram_data = []
    for measurement in framework_data['measurements_data']:
        mean_summary_data = framework_data['measurements_data'][measurement]['all_fields_mean']
        h_row = {"x_label": measurement, "y_value": mean_summary_data['rps_mean']}
        summary_rps_histogram_data.append(h_row)

    # Data for the main summary REQ histogram
    summary_req_histogram_data = []
    for measurement in framework_data['measurements_data']:
        mean_summary_data = framework_data['measurements_data'][measurement]['all_fields_mean']
        h_row = {"x_label": measurement, "y_value": mean_summary_data['req2xx']}
        summary_req_histogram_data.append(h_row)

    # Prepare data for the modes summary section
    modes_data = []
    # Get modes list from the first framework
    modes_list = framework_data['measurements_data'][framework_data['measurements'][0]]['modes']
    for mode in modes_list:
        this_mode_data = []
        # Collect data of this mode for each measurement
        for measurement in framework_data['measurements_data']:
            measurement_mode_data = framework_data['measurements_data'][measurement]['modes_data'][mode]
            measurement_mode_data_mean = measurement_mode_data['mean_fields']
            measurement_mode_server_metrics = measurement_mode_data['server_metrics']
            _create_metrics_table_row(this_mode_data, measurement_mode_server_metrics, measurement_mode_data_mean,
                                      measurement)

        # Write all of this mode data into the summary modes data list
        modes_data.append({"name": mode, "data": this_mode_data})

    # data for the mode summary latency mean compare graph
    ms_latency_graph = _create_mode_summary_graph(modes_list, modes_data, "Test Modes", "Latency Mean (us)", "Lat Mean")
    # data for the mode summary CPU compare graph
    ms_cpu_graph = _create_mode_summary_graph(modes_list, modes_data, "Test Modes", "CPU %", "CPU %")
    # data for the mode summary Memory compare graph
    ms_memory_graph = _create_mode_summary_graph(modes_list, modes_data, "Test Modes", "Mem MB", "Mem MB")
    # data for the mode summary RPS compare graph
    ms_rps_graph = _create_mode_summary_graph(modes_list, modes_data, "Test Modes", "RPS Mean", "RPS Mean")

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
        # index.html
        {'template': 'index.html', 'output': 'index.html', 'context': {
            "benchmark_results_summary_table_data": benchmark_results_summary_table_data,
            "measurement_run_count": measurement_run_count,
            "summary_latency_histogram_data": summary_latency_histogram_data,
            "summary_rps_histogram_data": summary_rps_histogram_data,
            "summary_req_histogram_data": summary_req_histogram_data,
            "modes_data": modes_data,
            "ms_latency_graph": ms_latency_graph,
            "ms_cpu_graph": ms_cpu_graph,
            "ms_memory_graph": ms_memory_graph,
            "ms_rps_graph": ms_rps_graph,
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
            "oldest_sample": framework_data['time_range']['oldest'],
            "newest_sample": framework_data['time_range']['newest'],
            "current_time": current_time,
            "total_run_count": framework_data['total_run_count'],
        }
        rendered = template.render(**context)
        with open(f"output/{page['output']}", 'w') as f:
            f.write(rendered)

    #########################################
    # Copy the static assets
    #########################################
    shutil.copytree('static', 'output/static', dirs_exist_ok=True)
