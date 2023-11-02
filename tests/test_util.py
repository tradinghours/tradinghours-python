import json
import unittest

from tradinghours.util import StrEncoder, slugify, snake_case, snake_dict


class TestSnakeCase(unittest.TestCase):
    def test_snake_case_with_dash(self):
        text = "hello-world"
        result = snake_case(text)
        self.assertEqual(result, "hello_world")

    def test_snake_case_no_dash(self):
        text = "helloWorld"
        result = snake_case(text)
        self.assertEqual(result, "hello_world")

    def test_snake_case_all_caps(self):
        text = "HELLO_WORLD"
        result = snake_case(text)
        self.assertEqual(result, "hello_world")

    def test_snake_case_none(self):
        text = None
        with self.assertRaises(ValueError):
            snake_case(text)

    def test_snake_case_int(self):
        text = 123
        with self.assertRaises(TypeError):
            snake_case(text)


class TestSnakeDict(unittest.TestCase):
    def test_snake_dict(self):
        data = {
            "First Name": "John",
            "Last Name": "Doe",
            "Age": 30,
        }
        result = snake_dict(data)
        expected_result = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 30,
        }
        self.assertEqual(result, expected_result)

    def test_snake_dict_non_dict_input(self):
        data = "This is not a dictionary"
        with self.assertRaises(TypeError):
            snake_dict(data)


class TestSlugify(unittest.TestCase):
    def test_slugify_basic(self):
        name = "Hello World"
        result = slugify(name)
        self.assertEqual(result, "hello-world")

    def test_slugify_special_characters(self):
        name = "Hello!@#$%^World"
        result = slugify(name)
        self.assertEqual(result, "hello-world")

    def test_slugify_multiple_spaces(self):
        name = "Hello    World"
        result = slugify(name)
        self.assertEqual(result, "hello-world")

    def test_slugify_none(self):
        name = None
        with self.assertRaises(ValueError):
            slugify(name)

    def test_slugify_int(self):
        name = 123
        with self.assertRaises(TypeError):
            slugify(name)


class TestStrEncoder(unittest.TestCase):
    def test_str_encoder(self):
        encoder = StrEncoder
        data = {"name": "John", "age": 30}
        json_data = json.dumps(data, cls=encoder)
        self.assertEqual(json_data, '{"name": "John", "age": 30}')

    def test_str_encoder_non_serializable(self):
        encoder = StrEncoder
        data = {"name": "John", "age": 30, "non_serializable": set()}
        result = json.dumps(data, cls=encoder)
        expected_result = '{"name": "John", "age": 30, "non_serializable": "set()"}'
        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()
