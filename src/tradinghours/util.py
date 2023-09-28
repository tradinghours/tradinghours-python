import re


def snake_dict(data: dict):
    snake_data = {}
    for key, value in data.items():
        snake_key = re.sub(r"[^a-zA-Z0-9]+", "_", key).strip("_").lower()
        snake_data[snake_key] = value
    return snake_data
