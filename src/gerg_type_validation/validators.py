# validators.py

from pathlib import Path
from typing import Any, Union, List, Type, Optional
from abc import ABC, abstractmethod

from gerg_type_validation.validation_config import ValidationConfig

class BaseValidator(ABC):
    """Abstract base class for all validators."""

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()

    @abstractmethod
    def validate(self, value: Any, **kwargs) -> bool:
        """Validate the value according to the validator's rules."""
        pass

    @abstractmethod
    def get_error_message(self, value: Any, var_name: str, **kwargs) -> str:
        """Generate an appropriate error message for validation failure."""
        pass

class TypeValidator(BaseValidator):
    """Validator for type checking."""

    def validate(self, value: Any, **kwargs) -> bool:
        """Include expected_type as a kwarg"""
        expected_type = kwargs.get('expected_type')
        if expected_type is None:
            raise ValueError("expected_type must be provided")

        if isinstance(expected_type, list):
            return any(isinstance(value, t) for t in expected_type)
        return isinstance(value, expected_type)

    def get_error_message(self, value: Any, var_name: str, **kwargs) -> str:
        """Include expected_type as a kwarg"""
        expected_type = kwargs.get('expected_type')
        if expected_type is None:
            raise ValueError("expected_type must be provided")

        given_type = type(value).__name__

        if isinstance(expected_type, list):
            type_names = [getattr(t, "__name__", str(t)) for t in expected_type]
            return f"'{var_name}' must be one of types {type_names}, but got '{given_type}'"
        else:
            type_name = getattr(expected_type, "__name__", str(expected_type))
            return f"'{var_name}' must be of type '{type_name}', but got '{given_type}'"


class RangeValidator(BaseValidator):
    """Validator for numeric range checking."""

    def validate(self, value: Any, min_val: Optional[Union[int, float]] = None,
                 max_val: Optional[Union[int, float]] = None, **kwargs) -> bool:
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True

    def get_error_message(self, value: Any, var_name: str,
                         min_val: Optional[Union[int, float]] = None,
                         max_val: Optional[Union[int, float]] = None, **kwargs) -> str:
        if min_val is not None and value < min_val:
            return f"'{var_name}' must be >= {min_val}, but got {value}"
        if max_val is not None and value > max_val:
            return f"'{var_name}' must be <= {max_val}, but got {value}"
        return f"'{var_name}' is out of valid range"

class LengthValidator(BaseValidator):
    """Validator for length checking."""

    def validate(self, value: Any, min_len: Optional[int] = None,
                 max_len: Optional[int] = None, length: Optional[int] = None, **kwargs) -> bool:
        try:
            val_len = len(value)
        except TypeError:
            return False

        if length is not None and val_len != length:
            return False
        if min_len is not None and val_len < min_len:
            return False
        if max_len is not None and val_len > max_len:
            return False
        return True

    def get_error_message(self, value: Any, var_name: str,
                         min_len: Optional[int] = None, max_len: Optional[int] = None,
                         length: Optional[int] = None, **kwargs) -> str:
        try:
            val_len = len(value)
        except TypeError:
            return f"'{var_name}' must have a length, but got {type(value).__name__}"

        if length is not None and val_len != length:
            return f"'{var_name}' must have length = {length}, but got {val_len}"
        if min_len is not None and val_len < min_len:
            return f"'{var_name}' must have length >= {min_len}, but got {val_len}"
        if max_len is not None and val_len > max_len:
            return f"'{var_name}' must have length <= {max_len}, but got {val_len}"
        return f"'{var_name}' has invalid length"

class PathValidator(BaseValidator):
    """Validator for path checking."""

    def validate(self, value: Any, must_exist: Optional[bool] = None,
                 must_be_file: bool = False, must_be_dir: bool = False, **kwargs) -> bool:
        try:
            if isinstance(value, Path):
                path_obj = value
            elif isinstance(value, (str, bytes)):
                if isinstance(value, (str, bytes)) and len(value.strip() if isinstance(value, str) else value) == 0:
                    return False
                path_obj = Path(str(value))
            else:
                path_obj = Path(value)
        except (TypeError, ValueError):
            return False

        if must_exist is True and not path_obj.exists():
            return False
        if must_exist is False and path_obj.exists():
            return False
        if must_be_file and (not path_obj.exists() or not path_obj.is_file()):
            return False
        if must_be_dir and (not path_obj.exists() or not path_obj.is_dir()):
            return False

        return True

    def get_error_message(self, value: Any, var_name: str, must_exist: Optional[bool] = None,
                         must_be_file: bool = False, must_be_dir: bool = False, **kwargs) -> str:
        try:
            if isinstance(value, Path):
                path_obj = value
            else:
                path_obj = Path(value)
        except (TypeError, ValueError) as e:
            return f"'{var_name}' cannot be converted to a Path: {e}"

        if isinstance(value, (str, bytes)) and len(value.strip() if isinstance(value, str) else value) == 0:
            return f"'{var_name}' cannot be an empty path"

        if must_exist is True and not path_obj.exists():
            return f"'{var_name}' path must exist, but '{path_obj}' does not exist"
        if must_exist is False and path_obj.exists():
            return f"'{var_name}' path must not exist, but '{path_obj}' already exists"
        if must_be_file and not path_obj.exists():
            return f"'{var_name}' must be an existing file, but '{path_obj}' does not exist"
        if must_be_file and not path_obj.is_file():
            return f"'{var_name}' must be a file, but '{path_obj}' is not a file"
        if must_be_dir and not path_obj.exists():
            return f"'{var_name}' must be an existing directory, but '{path_obj}' does not exist"
        if must_be_dir and not path_obj.is_dir():
            return f"'{var_name}' must be a directory, but '{path_obj}' is not a directory"

        return f"'{var_name}' path validation failed"

