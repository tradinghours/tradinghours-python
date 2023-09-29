import json
import re


def snake_case(text):
    if "-" in text:
        text = text.replace("-", "_")
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", text)
    return "_".join(words).lower()


def snake_dict(data: dict):
    snake_data = {}
    for key, value in data.items():
        snake_key = snake_case(key)
        snake_data[snake_key] = value
    return snake_data


def slugify(name):
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


class StrEncoder(json.JSONEncoder):
    """Helps encoding flat data"""

    def default(self, obj):
        try:
            encoded = super().default(obj)
        except TypeError:
            encoded = str(obj)
        return encoded
