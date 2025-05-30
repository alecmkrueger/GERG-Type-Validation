# assertions.py
from pathlib import Path
from typing import Any,Union,Type,List,Optional,TypeVar

from gerg_type_validation.type_validation_engine import TypeValidationEngine

T = TypeVar('T')

_default_engine = TypeValidationEngine()


def assert_type(value: Any, expected_type: Union[Type[T], List[Type]],
                msg: Optional[str] = None) -> T:
    """Assert that a value matches the expected type(s) and return it with proper typing."""
    return _default_engine.assert_type(value, expected_type, msg)

def assert_not_none(value: Optional[T], msg: Optional[str] = None) -> T:
    """Assert that a value is not None and return it with proper typing."""
    return _default_engine.assert_not_none(value, msg)

def assert_numeric(value: Any, min_val: Optional[Union[int, float]] = None,
                   max_val: Optional[Union[int, float]] = None,
                   msg: Optional[str] = None) -> Union[int, float]:
    """Assert that a value is numeric (int or float) and optionally within range."""
    return _default_engine.assert_numeric(value, min_val, max_val, msg)

def assert_string_like(value: Any, min_len: Optional[int] = None,
                       max_len: Optional[int] = None,
                       msg: Optional[str] = None) -> Union[str, bytes]:
    """Assert that a value is string-like (str or bytes) and optionally check length."""
    return _default_engine.assert_string_like(value, min_len, max_len, msg)

def assert_sequence(value: Any, min_len: Optional[int] = None,
                    max_len: Optional[int] = None,
                    length: Optional[int] = None,
                    msg: Optional[str] = None) -> Union[list, tuple]:
    """Assert that a value is a sequence (list or tuple) and optionally check length."""
    return _default_engine.assert_sequence(value, min_len, max_len, length, msg)

def assert_mapping(value: Any, required_keys: Optional[Union[str, List[str]]] = None,
                   msg: Optional[str] = None) -> dict:
    """Assert that a value is a mapping (dict) and optionally check for required keys."""
    return _default_engine.assert_mapping(value, required_keys, msg)

def assert_path(value: Any, must_exist: Optional[bool] = None,
                must_be_file: bool = False, must_be_dir: bool = False,
                create_parents: bool = False, msg: Optional[str] = None) -> Path:
    """Assert that a value can be converted to a pathlib.Path and optionally validate its existence."""
    return _default_engine.assert_path(value, must_exist, must_be_file, must_be_dir, create_parents, msg)

def assert_range(value: Union[int, float], min_val: Optional[Union[int, float]] = None,
                 max_val: Optional[Union[int, float]] = None, msg: Optional[str] = None) -> Union[int, float]:
    """Assert that a numeric value is within the specified range."""
    return _default_engine.assert_range(value, min_val, max_val, msg)

def assert_length(value: Any, min_len: Optional[int] = None, max_len: Optional[int] = None,
                  msg: Optional[str] = None) -> Any:
    """Assert that a value has a length within the specified range."""
    return _default_engine.assert_length(value, min_len, max_len, msg)