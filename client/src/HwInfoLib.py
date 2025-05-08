
import html
import platform
import re
import socket
import uuid
from datetime import datetime

import psutil

HW_INFO_LIB_DEBUG = True

def _get_mac_address():
    return ':'.join(re.findall('..', '%012x' % uuid.getnode()))


def _get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


def get_basic_info():
    return {
        "System": platform.system(),
        "Node Name": platform.node(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Architecture": platform.machine(),
        "Processor": platform.processor(),
    }


def get_extended_info():
    info = get_basic_info()
    try:
        info["IP Address"] = socket.gethostbyname(socket.gethostname())
    except Exception:
        info["IP Address"] = "Unavailable"
    info["MAC Address"] = _get_mac_address()
    return info


def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "Total": _get_size(mem.total),
        "Available": _get_size(mem.available),
        "Used": _get_size(mem.used),
        "Usage Percentage": f"{mem.percent}%",
    }


def get_cpu_info():
    cpu_info = {
        "Physical Cores": psutil.cpu_count(logical=False),
        "Total Cores": psutil.cpu_count(logical=True),
    }

    try:
        freq = psutil.cpu_freq()
        if freq:
            cpu_info.update({
                "Max Frequency": f"{freq.max:.2f} MHz",
                "Min Frequency": f"{freq.min:.2f} MHz",
                "Current Frequency": f"{freq.current:.2f} MHz",
            })
    except Exception as e:
        _debug_print("HwInfoLib: get_cpu_info(): frequency info error:", e)

    try:
        cpu_info["Total CPU Usage"] = f"{psutil.cpu_percent()}%"
    except Exception as e:
        _debug_print("HwInfoLib: get_cpu_info(): CPU usage error:", e)

    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                info = f.read()
                model_match = re.search(r"model name\s+:\s+(.+)", info)
                if model_match:
                    cpu_info["Model Name"] = model_match.group(1)

                cache_match = re.search(r"cache size\s+:\s+(.+)", info)
                if cache_match:
                    cpu_info["Cache Size"] = cache_match.group(1)

        elif platform.system() == "Windows":
            import subprocess
            output = subprocess.check_output("wmic cpu get name", shell=True).decode()
            lines = [line.strip() for line in output.splitlines() if line.strip() and "Name" not in line]
            if lines:
                cpu_info["Model Name"] = lines[0]

        elif platform.system() == "Darwin":
            import subprocess
            model = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
            if model:
                cpu_info["Model Name"] = model

    except Exception as e:
        _debug_print("HwInfoLib: get_cpu_info(): model name error:", e)

    return cpu_info

def get_boot_time():
    bt = datetime.fromtimestamp(psutil.boot_time())
    return {
        "Boot Time": bt.strftime("%Y/%m/%d %H:%M:%S"),
    }


def get_disk_info():
    partitions_info = {}
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            continue
        partitions_info[partition.device] = {
            "Mountpoint": partition.mountpoint,
            "File System": partition.fstype,
            "Total Size": _get_size(usage.total),
            "Used": _get_size(usage.used),
            "Free": _get_size(usage.free),
            "Usage Percentage": f"{usage.percent}%",
        }
    return partitions_info


def get_network_info():
    network_data = {}
    for interface_name, addresses in psutil.net_if_addrs().items():
        details = []
        for addr in addresses:
            if str(addr.family).endswith("AF_INET"):
                details.append({
                    "Type": "IPv4",
                    "Address": addr.address,
                    "Netmask": addr.netmask,
                    "Broadcast": addr.broadcast,
                })
            elif str(addr.family).endswith("AF_PACKET"):
                details.append({
                    "Type": "MAC",
                    "Address": addr.address,
                    "Netmask": addr.netmask,
                    "Broadcast": addr.broadcast,
                })
        network_data[interface_name] = details
    return network_data


def _debug_print(param, e):
    # Print function for debugging purposes
    if HW_INFO_LIB_DEBUG:
        print(param, e)

def _try_to_get_all():
    basic_info = extended_info = memory_info = cpu_info = boot_time = disk_info = network_info = "Unavailable"
    try:
        extended_info = get_extended_info()
    except Exception as e:
        _debug_print("HwInfoLib: _try_to_get_all(): Error getting extended_info:", e)
    try:
        memory_info = get_memory_info()
    except Exception as e:
        _debug_print("HwInfoLib: _try_to_get_all(): Error getting memory_info:", e)
    try:
        cpu_info = get_cpu_info()
    except Exception as e:
        _debug_print("HwInfoLib: _try_to_get_all(): Error getting cpu_info:", e)
    try:
        boot_time = get_boot_time()
    except Exception as e:
        _debug_print("HwInfoLib: _try_to_get_all(): Error getting boot_time:", e)
    try:
        disk_info = get_disk_info()
    except Exception as e:
        _debug_print("HwInfoLib: _try_to_get_all(): Error getting disk_info:", e)
    try:
        network_info = get_network_info()
    except Exception as e:
        _debug_print("HwInfoLib: _try_to_get_all(): Error getting disk_info:", e)
    try:
        basic_info = get_basic_info()
    except Exception as e:
        _debug_print("HwInfoLib: _try_to_get_all(): Error getting disk_info:", e)
    return extended_info, basic_info, boot_time, cpu_info, disk_info, memory_info, network_info

###########################################
# HTML output
###########################################

def _dict_to_html_table(title, data):
    table = f"<h2>{html.escape(title)}</h2>\n<table class=\"pure-table pure-table-bordered\">\n"
    try:
        for k, v in data.items():
            table += f"<tr><th>{html.escape(str(k))}</th><td>{html.escape(str(v))}</td></tr>\n"
    except Exception as e:
        _debug_print("HwInfoLib: _dict_to_html_table():", e)
        table += f"<tr><th>No Data</th><td>No Data</td></tr>\n"
    table += "</table>\n"
    return table


def _nested_dict_to_html_table(title, data):
    table = f"<h2>{html.escape(title)}</h2>\n"
    for key, subdata in data.items():
        table += f"<h3>{html.escape(key)}</h3>\n<table class=\"pure-table pure-table-bordered\">\n"
        try:
            for subkey, subvalue in subdata.items():
                table += f"<tr><th>{html.escape(str(subkey))}</th><td>{html.escape(str(subvalue))}</td></tr>\n"
        except Exception as e:
            _debug_print("HwInfoLib: _nested_dict_to_html_table():", e)
            table += f"<tr><th>No Data</th><td>No Data</td></tr>\n"
        table += "</table>\n"
    return table


def get_minimal_html_report():
    extended_info, basic_info, boot_time, cpu_info, disk_info, memory_info, network_info = _try_to_get_all()

    # Return only limited info
    html_report = ""
    html_report += _dict_to_html_table("System Information", basic_info)
    html_report += _dict_to_html_table("Memory Information", memory_info)
    html_report += _dict_to_html_table("CPU Information", cpu_info)
    html_report += _dict_to_html_table("Boot Time", boot_time)
    html_report += _nested_dict_to_html_table("Disk Partitions", disk_info)
    return html_report

def get_full_html_report():
    extended_info, basic_info, boot_time, cpu_info, disk_info, memory_info, network_info = _try_to_get_all()

    # Return full info including IPs
    html_report = ""
    html_report += _dict_to_html_table("Extended System Information", extended_info)
    html_report += _dict_to_html_table("Memory Information", memory_info)
    html_report += _dict_to_html_table("CPU Information", cpu_info)
    html_report += _dict_to_html_table("Boot Time", boot_time)
    html_report += _nested_dict_to_html_table("Disk Partitions", disk_info)
    html_report += _nested_dict_to_html_table("Network Interfaces", network_info)
    return html_report
