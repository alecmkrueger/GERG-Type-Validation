import unittest
import sys
import os

from src.exceptions import TypeAssertionError


class TestTypeAssertionError(unittest.TestCase):
    """Test cases for TypeAssertionError custom exception."""

    def test_type_assertion_error_inheritance(self):
        """Test that TypeAssertionError inherits from AssertionError."""
        self.assertTrue(issubclass(TypeAssertionError, AssertionError))

    def test_type_assertion_error_is_exception(self):
        """Test that TypeAssertionError is an Exception."""
        self.assertTrue(issubclass(TypeAssertionError, Exception))

    def test_type_assertion_error_instantiation_no_message(self):
        """Test creating TypeAssertionError without message."""
        error = TypeAssertionError()
        self.assertIsInstance(error, TypeAssertionError)
        self.assertIsInstance(error, AssertionError)

    def test_type_assertion_error_instantiation_with_message(self):
        """Test creating TypeAssertionError with message."""
        message = "Type validation failed"
        error = TypeAssertionError(message)
        self.assertEqual(str(error), message)

    def test_type_assertion_error_raise_and_catch(self):
        """Test raising and catching TypeAssertionError."""
        message = "Invalid type provided"

        with self.assertRaises(TypeAssertionError) as context:
            raise TypeAssertionError(message)

        self.assertEqual(str(context.exception), message)

    def test_type_assertion_error_catch_as_assertion_error(self):
        """Test that TypeAssertionError can be caught as AssertionError."""
        message = "Type mismatch"

        with self.assertRaises(AssertionError) as context:
            raise TypeAssertionError(message)

        self.assertIsInstance(context.exception, TypeAssertionError)
        self.assertEqual(str(context.exception), message)

    def test_type_assertion_error_with_multiple_args(self):
        """Test TypeAssertionError with multiple arguments."""
        args = ("Expected int", "got str", "at position 0")
        error = TypeAssertionError(*args)
        self.assertEqual(error.args, args)

    def test_type_assertion_error_docstring(self):
        """Test that TypeAssertionError has the correct docstring."""
        expected_docstring = "Custom assertion error for type validation failures."
        self.assertEqual(TypeAssertionError.__doc__, expected_docstring)
