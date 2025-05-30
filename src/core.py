# type_validation_engine.py
import re
import inspect
from pathlib import Path
from typing import Any, Union, List, Type, Optional, TypeGuard, TypeVar, get_type_hints

T = TypeVar('T')

from src.exceptions import TypeAssertionError
from src.validators import TypeValidator,RangeValidator,LengthValidator,PathValidator
from src.utils import VariableNameExtractor
from src.core import TypeValidationEngine



class ValidationConfig:
    """Configuration class for type validation behavior."""

    def __init__(self,
                 strict_mode: bool = True,
                 auto_extract_names: bool = True,
                 raise_on_failure: bool = True,
                 custom_error_class: Type[Exception] = TypeAssertionError):
        self.strict_mode = strict_mode
        self.auto_extract_names = auto_extract_names
        self.raise_on_failure = raise_on_failure
        self.custom_error_class = custom_error_class


class TypeValidationDecorator:
    """Decorator class for function parameter type checking."""

    def __init__(self, engine: Optional[TypeValidationEngine] = None):
        self.engine = engine or TypeValidationEngine()

    def type_checked(self, func):
        """Decorator that validates function arguments against their type hints."""
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)

        def wrapper(*args, **kwargs):
            bound_args = signature.bind(*args, **kwargs)
            bound_args.apply_defaults()

            for param_name, param_value in bound_args.arguments.items():
                if param_name in type_hints:
                    expected_type = type_hints[param_name]
                    try:
                        self.engine.assert_type(param_value, expected_type)
                    except TypeAssertionError as e:
                        # Replace the auto-detected name with the parameter name for clarity
                        error_msg = str(e)
                        if "'" in error_msg:
                            # Replace the first quoted variable name with the parameter name
                            error_msg = re.sub(r"'[^']*'", f"'{param_name}'", error_msg, count=1)
                        raise TypeError(f"In call to {func.__name__}: {error_msg}")

            return func(*args, **kwargs)

        return wrapper

# Context manager for temporary validation configuration
class ValidationContext:
    """Context manager for temporarily changing validation behavior."""

    def __init__(self, engine: TypeValidationEngine, **config_overrides):
        self.engine = engine
        self.original_config = engine.config
        self.config_overrides = config_overrides

    def __enter__(self):
        # Create new config with overrides
        new_config = ValidationConfig(
            strict_mode=self.config_overrides.get('strict_mode', self.original_config.strict_mode),
            auto_extract_names=self.config_overrides.get('auto_extract_names', self.original_config.auto_extract_names),
            raise_on_failure=self.config_overrides.get('raise_on_failure', self.original_config.raise_on_failure),
            custom_error_class=self.config_overrides.get('custom_error_class', self.original_config.custom_error_class)
        )
        self.engine.config = new_config
        return self.engine

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original config
        self.engine.config = self.original_config

class TypeValidationEngine:
    """Main engine for type validation operations."""

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self.validators = {
            'type': TypeValidator(self.config),
            'range': RangeValidator(self.config),
            'length': LengthValidator(self.config),
            'path': PathValidator(self.config)
        }
        self.name_extractor = VariableNameExtractor()

    def _find_original_caller_frame(self):
        """Find the original caller frame, skipping internal function calls."""
        frame = inspect.currentframe()
        internal_functions = [
            'assert_type', 'assert_range',
            'assert_length', 'assert_not_none', 'is_type', 'assert_numeric',
            'assert_string_like', 'assert_sequence', 'assert_mapping', 'assert_path',
            'is_not_none', '_validate_with_engine', '_assert_with_engine'
        ]

        while frame:
            frame = frame.f_back
            if frame is None:
                break

            func_name = frame.f_code.co_name
            if func_name not in internal_functions:
                return frame

        return inspect.currentframe().f_back  #type:ignore

    def _get_variable_name(self) -> str:
        """Get the variable name from the calling context."""
        if not self.config.auto_extract_names:
            return "value"

        frame = self._find_original_caller_frame()
        return self.name_extractor.extract_from_frame(frame)

    def _validate_with_engine(self, validator_name: str, value: Any,
                             custom_msg: Optional[str] = None, **kwargs) -> bool:
        """Internal method to validate using specified validator."""
        validator = self.validators[validator_name]
        is_valid = validator.validate(value, **kwargs)

        if not is_valid and self.config.raise_on_failure:
            var_name = self._get_variable_name()
            error_msg = custom_msg or validator.get_error_message(value, var_name, **kwargs)
            raise self.config.custom_error_class(error_msg)

        return is_valid

    def _assert_with_engine(self, validator_name: str, value: Any,
                           custom_msg: Optional[str] = None, **kwargs) -> Any:
        """Internal method to assert using specified validator and return value."""
        self._validate_with_engine(validator_name, value, custom_msg, **kwargs)
        return value

    # Type validation methods
    def is_type(self, value: Any, expected_type: Type[T]) -> TypeGuard[T]:
        """Type guard function that checks if a value is of the expected type."""
        return isinstance(value, expected_type)

    def is_not_none(self, value: Optional[T]) -> TypeGuard[T]:
        """Type guard function that checks if a value is not None."""
        return value is not None

    def assert_type(self, value: Any, expected_type: Union[Type[T], List[Type]],
                    msg: Optional[str] = None) -> T:
        """Assert that a value matches the expected type(s)."""
        return self._assert_with_engine('type', value, msg, expected_type=expected_type)

    def assert_not_none(self, value: Optional[T], msg: Optional[str] = None) -> T:
        """Assert that a value is not None."""
        if value is None:
            var_name = self._get_variable_name()
            error_msg = msg or f"'{var_name}' must not be None"
            raise self.config.custom_error_class(error_msg)
        return value
    def assert_numeric(self, value: Any, min_val: Optional[Union[int, float]] = None,
                       max_val: Optional[Union[int, float]] = None,
                       msg: Optional[str] = None) -> Union[int, float]:
        """Assert that a value is numeric (int or float) and optionally within range."""
        # First check if it's numeric
        self._assert_with_engine('type', value, msg, expected_type=(int, float))
        # Then check range if specified
        if min_val is not None or max_val is not None:
            self._validate_with_engine('range', value, msg, min_val=min_val, max_val=max_val)
        return value

    def assert_string_like(self, value: Any, min_len: Optional[int] = None,
                           max_len: Optional[int] = None,
                           msg: Optional[str] = None) -> Union[str, bytes]:
        """Assert that a value is string-like (str or bytes) and optionally check length."""
        # First check if it's string-like
        self._assert_with_engine('type', value, msg, expected_type=(str, bytes))
        # Then check length if specified
        if min_len is not None or max_len is not None:
            self._validate_with_engine('length', value, msg, min_len=min_len, max_len=max_len)
        return value

    def assert_sequence(self, value: Any, min_len: Optional[int] = None,
                        max_len: Optional[int] = None, length: Optional[int] = None,
                        msg: Optional[str] = None) -> Union[list, tuple]:
        """Assert that a value is a sequence (list or tuple) and optionally check length."""
        # First check if it's a sequence
        self._assert_with_engine('type', value, msg, expected_type=(list, tuple))
        # Then check length if specified
        if min_len is not None or max_len is not None or length is not None:
            self._validate_with_engine('length', value, msg, min_len=min_len, max_len=max_len, length=length)
        return value

    def assert_mapping(self, value: Any, required_keys: Optional[Union[str, List[str]]] = None,
                       msg: Optional[str] = None) -> dict:
        """Assert that a value is a mapping (dict) and optionally check for required keys."""
        # First check if it's a mapping
        self._assert_with_engine('type', value, msg, expected_type=dict)

        # Check required keys if specified
        if required_keys is not None:
            var_name = self._get_variable_name()

            # Convert single string to list for uniform processing
            if isinstance(required_keys, str):
                keys_to_check = [required_keys]
            else:
                keys_to_check = required_keys

            missing_keys = [key for key in keys_to_check if key not in value]
            if missing_keys:
                if len(missing_keys) == 1:
                    error_msg = msg or f"'{var_name}' missing required key: '{missing_keys[0]}'"
                else:
                    error_msg = msg or f"'{var_name}' missing required keys: {missing_keys}"
                raise self.config.custom_error_class(error_msg)

        return value

    def assert_path(self, value: Any, must_exist: Optional[bool] = None,
                    must_be_file: bool = False, must_be_dir: bool = False,
                    create_parents: bool = False, msg: Optional[str] = None) -> Path:
        """Assert that a value can be converted to a pathlib.Path and optionally validate its existence."""
        var_name = self._get_variable_name()

        # Try to convert to Path
        try:
            if isinstance(value, Path):
                path_obj = value
            elif isinstance(value, (str, bytes)):
                path_obj = Path(str(value))
            else:
                path_obj = Path(value)
        except (TypeError, ValueError) as e:
            error_msg = msg or f"'{var_name}' cannot be converted to a Path: {e}"
            raise self.config.custom_error_class(error_msg)

        # Validate string-like input wasn't empty
        if isinstance(value, (str, bytes)) and len(value.strip() if isinstance(value, str) else value) == 0:
            error_msg = msg or f"'{var_name}' cannot be an empty path"
            raise self.config.custom_error_class(error_msg)

        # Create parent directories if requested
        if create_parents and not path_obj.parent.exists():
            try:
                path_obj.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                error_msg = msg or f"'{var_name}' parent directories could not be created: {e}"
                raise self.config.custom_error_class(error_msg)

        # Use path validator for existence and type checks
        self._validate_with_engine('path', path_obj, msg,
                                 must_exist=must_exist, must_be_file=must_be_file, must_be_dir=must_be_dir)

        return path_obj

    def assert_range(self, value: Union[int, float], min_val: Optional[Union[int, float]] = None,
                     max_val: Optional[Union[int, float]] = None, msg: Optional[str] = None) -> Union[int, float]:
        """Assert that a numeric value is within the specified range."""
        self._validate_with_engine('range', value, msg, min_val=min_val, max_val=max_val)
        return value

    def assert_length(self, value: Any, min_len: Optional[int] = None, max_len: Optional[int] = None,
                      msg: Optional[str] = None) -> Any:
        """Assert that a value has a length within the specified range."""
        self._validate_with_engine('length', value, msg, min_len=min_len, max_len=max_len)
        return value
