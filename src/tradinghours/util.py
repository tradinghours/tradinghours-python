import csv
import json
import re
from io import StringIO
from typing import Dict

from zoneinfo import TZPATH
import importlib.metadata as metadata
import requests, warnings

from .validate import validate_instance_arg, validate_str_arg
from .exceptions import MissingTzdata
from .config import main_config

def snake_case(text):
    text = validate_str_arg("text", text, strip=True)
    if "-" in text:
        text = text.replace("-", "_")
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+|[a-z]+", text)
    return "_".join(words).lower()


def snake_dict(data: dict):
    data = validate_instance_arg("data", data, dict)
    snake_data = {}
    for key, value in data.items():
        snake_key = snake_case(key)
        snake_data[snake_key] = value
    return snake_data


def slugify(name):
    name = validate_str_arg("name", name, strip=True)
    slug = []
    just_added_dash = False

    for char in name.lower():
        if char.isalnum():  # Check if the character is alphanumeric
            slug.append(char)
            just_added_dash = False
        elif not just_added_dash:
            slug.append("-")
            just_added_dash = True

    return "".join(slug)


def create_table_structure(data, num_columns=3, suppress_empty_values=False):
    sorted_keys = sorted(data.keys())

    # Filter out empty values if suppress_empty_values is True
    if suppress_empty_values:
        sorted_keys = [key for key in sorted_keys if data[key] != ""]

    # Calculate the number of rows needed
    num_rows = len(sorted_keys) // num_columns
    if len(sorted_keys) % num_columns != 0:
        num_rows += 1

    # Initialize an empty table structure
    table = []

    for i in range(num_columns):
        column_keys = sorted_keys[i * num_rows : (i + 1) * num_rows]
        max_key_width = max(len(key) for key in column_keys)
        max_value_width = max(len(str(data[key])) for key in column_keys)

        column_data = [(key, data[key]) for key in column_keys]
        column_metadata = (max_key_width, max_value_width)

        table.append((column_metadata, column_data))

    return table


def render_ascii_table(table_structure, fixed_value_width=None, max_width=None):
    num_columns = len(table_structure)
    num_rows = max(len(column_data) for _, column_data in table_structure)

    table = ""

    for row_index in range(num_rows):
        for col_index in range(num_columns):
            metadata, rows = table_structure[col_index]
            max_key_width, max_value_width = metadata
            if row_index < len(rows):
                key, value = rows[row_index]
            else:
                key = ""
                value = ""

            # Use the fixed_value_width if provided, else use the max_value_width
            value_width = (
                fixed_value_width if fixed_value_width is not None else max_value_width
            )
            if max_width:
                value_width = min(max_width, value_width)

            # Truncate long string values to fit the width
            if len(value) > value_width:
                value = value[:value_width]

            # Calculate the number of dots to ensure at least one dot
            dots = "." * (max_key_width - len(key) + 1)

            if key == "" and value == "":
                key_width = len(key) + len(dots)
                table += " " * (key_width + value_width + 2)
            else:
                table += f"{key}{dots}: {value:{value_width}}"

            if col_index < num_columns - 1:
                table += "  "  # Add spacing between columns
            else:
                table += "\n"  # Newline at the end of the row

    return table


def pprint_data(data: Dict):
    table = create_table_structure(data, suppress_empty_values=True)
    ascii = render_ascii_table(table, max_width=15)
    print(ascii)


def get_csv_from_tuple(data: tuple) -> str:
    csv_data = StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(data)
    csv_string = csv_data.getvalue()
    csv_data.close()
    return csv_string


def get_tuple_from_csv(csv_string: str) -> tuple:
    csv_data = StringIO(csv_string)
    reader = csv.reader(csv_data)
    row = next(reader)
    csv_data.close()
    return tuple(row)


class StrEncoder(json.JSONEncoder):
    """Helps encoding flat data"""

    def default(self, obj):
        try:
            encoded = super().default(obj)
        except TypeError:
            encoded = str(obj)
        return encoded


def _get_latest_tzdata_version():
    try:
        response = requests.get(f"https://pypi.org/pypi/tzdata/json")
    except requests.exceptions.RequestException:
        return None

    if response.status_code == 200:
        return response.json()["info"]["version"]


def check_if_tzdata_required_and_up_to_date():
    """
    required installed # check for version
    required notinstalled # raise error
    notrequired installed # doesn't matter
    notrequired notinstalled # doesn't matter
    [don't check]

    if required (no tzpath)
        get version
        if not version:
            raise Error # required notinstalled
        else:
            check version/give warning # required installed
    else (tzpath):

    """
    if not main_config.getboolean("control", "check_tzdata"):
        return False

    required = len(TZPATH) == 0
    if required:
        try:
            installed_version = metadata.version('tzdata')
        except metadata.PackageNotFoundError:
            raise MissingTzdata("\nYour environment does not provide timezone data and\n"
                                "you don't have tzdata installed, please run:\n"
                                " pip install tzdata") from None

        latest_version = _get_latest_tzdata_version()
        if latest_version is None:
            warnings.warn("Failed to get latest version of tzdata. "
                          "Check your internet connection or set "
                          "check_tzdata = False under [control] in tradinghours.ini")
            return None

        if installed_version < latest_version:
            warnings.warn(f"\nThe installed version of tzdata is {installed_version}\n"
                          f"The latest version of tzdata is    {latest_version}\n"
                          f"Please run: pip install tzdata --upgrade")
            return None

    return True