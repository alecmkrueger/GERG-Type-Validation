import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os
from typing import List

from gerg_type_validation.assertions import (
    assert_type,
    assert_not_none,
    assert_numeric,
    assert_string_like,
    assert_sequence,
    assert_mapping,
    assert_path,
    assert_range,
    assert_length
)


class TestAssertions(unittest.TestCase):

    def test_assert_type_valid_single_type(self):
        result = assert_type("hello", str)
        self.assertEqual(result, "hello")
        self.assertIsInstance(result, str)

    def test_assert_type_valid_multiple_types(self):
        result = assert_type(42, [int, str])
        self.assertEqual(result, 42)

    def test_assert_type_with_custom_message(self):
        with self.assertRaises(Exception) as context:
            assert_type(42, str, "Custom error message")
        # Verify custom message is passed through

    def test_assert_not_none_valid(self):
        result = assert_not_none("not none")
        self.assertEqual(result, "not none")

    def test_assert_not_none_with_zero(self):
        result = assert_not_none(0)
        self.assertEqual(result, 0)

    def test_assert_not_none_with_empty_string(self):
        result = assert_not_none("")
        self.assertEqual(result, "")

    def test_assert_not_none_with_false(self):
        result = assert_not_none(False)
        self.assertEqual(result, False)

    def test_assert_numeric_int(self):
        result = assert_numeric(42)
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)

    def test_assert_numeric_float(self):
        result = assert_numeric(3.14)
        self.assertEqual(result, 3.14)
        self.assertIsInstance(result, float)

    def test_assert_numeric_with_range(self):
        result = assert_numeric(50, min_val=0, max_val=100)
        self.assertEqual(result, 50)

    def test_assert_numeric_negative_numbers(self):
        result = assert_numeric(-10, min_val=-20, max_val=0)
        self.assertEqual(result, -10)

    def test_assert_numeric_boundary_values(self):
        result = assert_numeric(0, min_val=0, max_val=0)
        self.assertEqual(result, 0)

    def test_assert_string_like_str(self):
        result = assert_string_like("hello")
        self.assertEqual(result, "hello")
        self.assertIsInstance(result, str)

    def test_assert_string_like_bytes(self):
        byte_data = b"hello"
        result = assert_string_like(byte_data)
        self.assertEqual(result, byte_data)
        self.assertIsInstance(result, bytes)

    def test_assert_string_like_with_length_constraints(self):
        result = assert_string_like("hello", min_len=3, max_len=10)
        self.assertEqual(result, "hello")

    def test_assert_string_like_empty_string(self):
        result = assert_string_like("", min_len=0, max_len=5)
        self.assertEqual(result, "")

    def test_assert_string_like_unicode(self):
        unicode_str = "héllo wörld"
        result = assert_string_like(unicode_str)
        self.assertEqual(result, unicode_str)

    def test_assert_sequence_list(self):
        test_list = [1, 2, 3]
        result = assert_sequence(test_list)
        self.assertEqual(result, test_list)
        self.assertIsInstance(result, list)

    def test_assert_sequence_tuple(self):
        test_tuple = (1, 2, 3)
        result = assert_sequence(test_tuple)
        self.assertEqual(result, test_tuple)
        self.assertIsInstance(result, tuple)

    def test_assert_sequence_with_length_constraints(self):
        test_list = [1, 2, 3, 4, 5]
        result = assert_sequence(test_list, min_len=3, max_len=10)
        self.assertEqual(result, test_list)

    def test_assert_sequence_with_exact_length(self):
        test_list = [1, 2, 3]
        result = assert_sequence(test_list, length=3)
        self.assertEqual(result, test_list)

    def test_assert_sequence_empty_list(self):
        empty_list = []
        result = assert_sequence(empty_list, min_len=0)
        self.assertEqual(result, empty_list)

    def test_assert_sequence_nested_structures(self):
        nested_list = [[1, 2], [3, 4]]
        result = assert_sequence(nested_list)
        self.assertEqual(result, nested_list)

    def test_assert_mapping_dict(self):
        test_dict = {"key": "value"}
        result = assert_mapping(test_dict)
        self.assertEqual(result, test_dict)
        self.assertIsInstance(result, dict)

    def test_assert_mapping_with_required_keys_string(self):
        test_dict = {"name": "John", "age": 30}
        result = assert_mapping(test_dict, required_keys="name")
        self.assertEqual(result, test_dict)

    def test_assert_mapping_with_required_keys_list(self):
        test_dict = {"name": "John", "age": 30, "city": "NYC"}
        result = assert_mapping(test_dict, required_keys=["name", "age"])
        self.assertEqual(result, test_dict)

    def test_assert_mapping_empty_dict(self):
        empty_dict = {}
        result = assert_mapping(empty_dict)
        self.assertEqual(result, empty_dict)

    def test_assert_mapping_nested_dict(self):
        nested_dict = {"outer": {"inner": "value"}}
        result = assert_mapping(nested_dict)
        self.assertEqual(result, nested_dict)

    def test_assert_path_string_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = assert_path(temp_dir)
            self.assertIsInstance(result, Path)
            self.assertEqual(str(result), temp_dir)

    def test_assert_path_pathlib_input(self):
        path_obj = Path("/some/path")
        result = assert_path(path_obj)
        self.assertIsInstance(result, Path)
        self.assertEqual(result, path_obj)

    def test_assert_path_with_existence_check(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = assert_path(temp_dir, must_exist=True)
            self.assertIsInstance(result, Path)
            self.assertTrue(result.exists())

    def test_assert_path_file_validation(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        # File is now closed, safe to test and delete
        try:
            result = assert_path(temp_file_path, must_be_file=True)
            self.assertIsInstance(result, Path)
            self.assertTrue(result.is_file())
        finally:
            try:
                os.unlink(temp_file_path)
            except (OSError, PermissionError):
                # Handle case where file might already be deleted or locked
                pass

    def test_assert_path_directory_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = assert_path(temp_dir, must_be_dir=True)
            self.assertIsInstance(result, Path)
            self.assertTrue(result.is_dir())

    def test_assert_path_relative_path(self):
        result = assert_path("./relative/path")
        self.assertIsInstance(result, Path)

    def test_assert_path_with_create_parents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            new_path = Path(temp_dir) / "new" / "nested" / "path"
            result = assert_path(str(new_path), create_parents=True)
            self.assertIsInstance(result, Path)

    def test_assert_range_valid_int(self):
        result = assert_range(5, min_val=0, max_val=10)
        self.assertEqual(result, 5)

    def test_assert_range_valid_float(self):
        result = assert_range(3.14, min_val=0.0, max_val=10.0)
        self.assertEqual(result, 3.14)

    def test_assert_range_boundary_values(self):
        result = assert_range(0, min_val=0, max_val=10)
        self.assertEqual(result, 0)

        result = assert_range(10, min_val=0, max_val=10)
        self.assertEqual(result, 10)

    def test_assert_range_negative_numbers(self):
        result = assert_range(-5, min_val=-10, max_val=0)
        self.assertEqual(result, -5)

    def test_assert_range_no_constraints(self):
        result = assert_range(42)
        self.assertEqual(result, 42)

    def test_assert_range_only_min(self):
        result = assert_range(100, min_val=50)
        self.assertEqual(result, 100)

    def test_assert_range_only_max(self):
        result = assert_range(25, max_val=50)
        self.assertEqual(result, 25)

    def test_assert_length_string(self):
        result = assert_length("hello", min_len=3, max_len=10)
        self.assertEqual(result, "hello")

    def test_assert_length_list(self):
        test_list = [1, 2, 3, 4]
        result = assert_length(test_list, min_len=2, max_len=5)
        self.assertEqual(result, test_list)

    def test_assert_length_tuple(self):
        test_tuple = (1, 2, 3)
        result = assert_length(test_tuple, min_len=3, max_len=3)
        self.assertEqual(result, test_tuple)

    def test_assert_length_dict(self):
        test_dict = {"a": 1, "b": 2}
        result = assert_length(test_dict, min_len=1, max_len=5)
        self.assertEqual(result, test_dict)

    def test_assert_length_empty_collection(self):
        empty_list = []
        result = assert_length(empty_list, min_len=0, max_len=0)
        self.assertEqual(result, empty_list)

    def test_assert_length_no_constraints(self):
        test_string = "any length"
        result = assert_length(test_string)
        self.assertEqual(result, test_string)

    def test_assert_length_bytes(self):
        byte_data = b"hello"
        result = assert_length(byte_data, min_len=3, max_len=10)
        self.assertEqual(result, byte_data)


if __name__ == '__main__':
    unittest.main()