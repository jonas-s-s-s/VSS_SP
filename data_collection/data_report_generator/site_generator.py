from datetime import timezone, datetime

from jinja2 import Environment, FileSystemLoader
import os
import shutil

EXCLUDED_DATA_COLUMNS = ["bytesRead", "bytesWritten", "mode", "others", "req1xx", "req3xx", "req4xx", "req5xx",
                         "test_case_id", "timeTakenSeconds", "errors"]

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


#########################################
# DATA PREPROCESSING
#########################################

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


def _compute_total_reqs(data_dict, float_decimal_places=2):
    total_reqs = data_dict['others'] + data_dict['req1xx'] + data_dict['req2xx'] + \
                 data_dict['req3xx'] + data_dict['req4xx'] + data_dict['req5xx']
    return round(total_reqs, float_decimal_places)


#########################################
# TABLE CREATION
#########################################

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


def _create_metrics_table_row(table_data, server_metrics, framework_metrics, framework_name):
    row = _create_metrics_table_row_no_append(server_metrics, framework_metrics, framework_name)
    table_data.append(row)


def _create_metrics_table_row_no_append(server_metrics, framework_metrics, framework_name):
    # Create initial table row
    summary_table_row = _create_table_row(framework_metrics, framework_name)
    # Compute and append the total requests field
    summary_table_row["REQ Total"] = _compute_total_reqs(framework_metrics)
    # Add server metrics to the row
    _append_to_table_row(server_metrics, summary_table_row)
    return summary_table_row


#########################################
# GRAPH CREATION
#########################################

def _create_graph_from_tables_data(point_names_list, tables_data, main_x_label, main_y_label, column_name):
    curves = []
    x_labels = point_names_list
    curve_labels = []

    # Get the "name" field of each table row (this only needs to taken from one table)
    first_table = tables_data[0]
    for row_data in first_table['data']:
        curve_labels.append(row_data['name'])
        # Initialize the curves array, each name (framework) has its own curve
        curves.append([])
    # We can take the data to create curves from the struct that is used to render the tables
    for mode in tables_data:
        for i, row_data in enumerate(mode['data']):
            value = row_data[column_name]
            # Protect against "NULL" values
            if value == "NULL":
                curves[i].append(0.0)
            else:
                curves[i].append(value)

    return {"curves": curves, "x_labels": x_labels, "curve_labels": curve_labels, "main_x_label": main_x_label,
            "main_y_label": main_y_label}


#########################################
# HISTOGRAM CREATION
#########################################

def _create_summary_histogram(m_data, column_name):
    histogram_data = []
    for m in m_data:
        summary_data = m_data[m]['all_fields_mean']
        h_row = {"x_label": m, "y_value": summary_data[column_name]}
        histogram_data.append(h_row)
    return histogram_data


#########################################
# CREATION OF PAGES AND SITE COMPONENTS
#########################################

def _create_details_pages_data(modes_list, measurements_data):
    details_page_data = {}
    # For each mode iterate over measurements
    for mode in modes_list:
        details_page_data[mode] = {"test_cases": {}}
        # For each measurement iterate over the test cases associated with this mode
        for m in measurements_data:
            m_mode_test_cases = measurements_data[m]['modes_data'][mode]['test_cases']
            # Save each test case associated with this measurement and mode
            for tc in m_mode_test_cases:
                tc_data = m_mode_test_cases[tc]
                # Convert this data to a table row
                row = _create_metrics_table_row_no_append(tc_data['server_metrics'], tc_data['mean_fields'],
                                                          m)
                # Creates an empty list, if there is nothing on the tc key, then appends to it
                details_page_data[mode]["test_cases"].setdefault(tc, []).append(row)

        # Generate graphs for this mode
        tables_of_this_mode = []
        test_case_labels = []
        for tc in details_page_data[mode]["test_cases"]:
            table_data = details_page_data[mode]["test_cases"][tc]
            tables_of_this_mode.append({"data": table_data, "name": tc})
            test_case_labels.append(tc)

        # Graphs will be created from these table columns
        tracked_rows = ["Lat Mean", "RPS Mean", "Mem MB", "CPU %"]
        for row in tracked_rows:
            g = _create_graph_from_tables_data(test_case_labels, tables_of_this_mode, "Test Case", row, row)
            details_page_data[mode].setdefault("graphs", []).append(g)

    return details_page_data


#########################################
# MAIN SITE GENERATION FUNC
#########################################

def generate(framework_data):
    env = Environment(loader=FileSystemLoader('templates'))

    # m is used as a short for "measurement"
    m_data = framework_data['measurements_data']

    # Data for the timestamp overview table
    datetime_now = datetime.now(timezone.utc)
    current_time = datetime_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    # Data for the table which displays test case run counts
    m_run_count = []
    for m in m_data:
        m_run_count.append(
            {
                "name": m,
                "run_count": m_data[m]['uuid_count']
            })

    # Data for the main summary table
    benchmark_results_summary_table_data = []
    for m in m_data:
        mean_summary_data = m_data[m]['all_fields_mean']
        _create_metrics_table_row(benchmark_results_summary_table_data, m_data[m]['server_metrics'], mean_summary_data,
                                  m)

    # Data for the main summary latency mean histogram
    summary_latency_histogram_data = _create_summary_histogram(m_data, 'latency_mean')

    # Data for the main summary RPS mean histogram
    summary_rps_histogram_data = _create_summary_histogram(m_data, 'rps_mean')

    # Data for the main summary REQ histogram
    summary_req_histogram_data = _create_summary_histogram(m_data, 'req2xx')

    # Prepare data for the modes summary section
    modes_data = []
    # Get modes list from the first framework
    modes_list = m_data[framework_data['measurements'][0]]['modes']
    for mode in modes_list:
        this_mode_data = []
        # Collect data of this mode for each measurement
        for m in m_data:
            m_mode_data = m_data[m]['modes_data'][mode]
            m_mode_data_mean = m_mode_data['mean_fields']
            m_mode_server_metrics = m_mode_data['server_metrics']
            _create_metrics_table_row(this_mode_data, m_mode_server_metrics, m_mode_data_mean,
                                      m)

        # Write all of this mode data into the summary modes data list
        modes_data.append({"name": mode, "data": this_mode_data})

    # data for the mode summary latency mean compare graph
    ms_latency_graph = _create_graph_from_tables_data(modes_list, modes_data, "Test Modes", "Latency Mean (us)",
                                                      "Lat Mean")
    # data for the mode summary CPU compare graph
    ms_cpu_graph = _create_graph_from_tables_data(modes_list, modes_data, "Test Modes", "CPU %", "CPU %")
    # data for the mode summary Memory compare graph
    ms_memory_graph = _create_graph_from_tables_data(modes_list, modes_data, "Test Modes", "Mem MB", "Mem MB")
    # data for the mode summary RPS compare graph
    ms_rps_graph = _create_graph_from_tables_data(modes_list, modes_data, "Test Modes", "RPS Mean", "RPS Mean")

    # Data for the various mode details pages
    details_pages_data = _create_details_pages_data(modes_list, m_data)

    #########################################
    # Prepare pages
    #########################################

    # Create a details page for each mode
    mode_details_pages = []
    for mode in details_pages_data:
        mode_details_pages.append(
            {'label': f"{mode} details", 'template': 'mode_details.html', 'output': f'{mode}.html', 'context': {
                "title": f"{mode.upper()} Details",
                "mode": mode,
                "tables_data": details_pages_data[mode]['test_cases'],
                "graphs_data": details_pages_data[mode]['graphs']
            }})

    # Create the index page
    index_page = {'label': "index", 'template': 'index.html', 'output': 'index.html', 'context': {
        "title": "Benchmark Results",
        "benchmark_results_summary_table_data": benchmark_results_summary_table_data,
        "measurement_run_count": m_run_count,
        "summary_latency_histogram_data": summary_latency_histogram_data,
        "summary_rps_histogram_data": summary_rps_histogram_data,
        "summary_req_histogram_data": summary_req_histogram_data,
        "modes_data": modes_data,
        "ms_latency_graph": ms_latency_graph,
        "ms_cpu_graph": ms_cpu_graph,
        "ms_memory_graph": ms_memory_graph,
        "ms_rps_graph": ms_rps_graph,
    }}

    pages = [
        index_page,
        *mode_details_pages
    ]

    #########################################
    # Prepare nav bar objects
    #########################################
    nav_items = []

    for page in pages:
        nav_items.append({'label': page['label'], 'href': page['output']})

    print("All pages have been generated.")
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
    print("All files have been written to disk.")
