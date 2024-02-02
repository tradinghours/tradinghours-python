import pytest, json
from tradinghours.util import StrEncoder, slugify, snake_case, snake_dict


@pytest.mark.parametrize("name, expected", [
    ("Hello World", "hello-world"),
    ("Hello!@#$%^World", "hello-world"),
    ("Hello    World", "hello-world"),
])
def test_slugify(name, expected):
    assert slugify(name) == expected


@pytest.mark.parametrize("name, exception", [
    (None, ValueError),
    (123, TypeError),
])
def test_slugify_with_errors(name, exception):
    with pytest.raises(exception):
        slugify(name)


@pytest.mark.parametrize("text, expected", [
    ("hello-world", "hello_world"),
    ("helloWorld", "hello_world"),
    ("HELLO_WORLD", "hello_world"),
])
def test_snake_case(text, expected):
    assert snake_case(text) == expected


@pytest.mark.parametrize("text, exception", [
    (None, ValueError),
    (123, TypeError),
])
def test_snake_case_with_errors(text, exception):
    with pytest.raises(exception):
        snake_case(text)


def test_snake_dict():
    data = {"First Name": "John", "Last Name": "Doe", "Age": 30}
    expected = {"first_name": "John", "last_name": "Doe", "age": 30}
    assert snake_dict(data) == expected

def test_snake_dict_with_errors():
    with pytest.raises(TypeError):
        snake_dict("This is not a dictionary")

def test_str_encoder():
    data = {"name": "John", "age": 30}
    expected = '{"name": "John", "age": 30}'
    assert json.dumps(data, cls=StrEncoder) == expected

def test_str_encoder_non_serializable():
    data = {"name": "John", "age": 30, "non_serializable": set()}
    expected = '{"name": "John", "age": 30, "non_serializable": "set()"}'
    assert json.dumps(data, cls=StrEncoder) == expected