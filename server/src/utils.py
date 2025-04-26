import re


def convert_to_mb(value_str):
    unit_to_mb = {
        'B': 1e-6,
        'kB': 1e-3,
        'MB': 1,
        'GB': 1e3,
        'TB': 1e6,
        'KiB': 1024 / 1e6,
        'MiB': (1024 ** 2) / 1e6,
        'GiB': (1024 ** 3) / 1e6,
        'TiB': (1024 ** 4) / 1e6,
    }

    match = re.match(r'^([0-9.]+)([A-Za-z]+)$', value_str)
    if not match:
        raise ValueError(f"Invalid format: {value_str}")

    number = float(match.group(1))
    unit = match.group(2)

    factor = unit_to_mb.get(unit)
    if factor is None:
        raise ValueError(f"Unsupported unit: {unit} in {value_str}")

    return number * factor
