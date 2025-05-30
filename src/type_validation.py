import inspect
import ast
import re
import warnings
from pathlib import Path
from typing import Any, Union, List, Type, TypeVar, get_type_hints, Optional, TypeGuard

T = TypeVar('T')

class TypeAssertionError(AssertionError):
    """Custom assertion error for type validation failures."""
    pass

def _extract_variable_name_from_source(frame) -> str:
    """
    Extract the variable name from the calling source code using AST parsing.

    Args:
        frame: The calling frame

    Returns:
        str: The extracted variable name or 'value' as fallback
    """
    try:
        # Get the source line
        context = inspect.getframeinfo(frame)
        if not context.code_context:
            return "value"

        source_line = context.code_context[0].strip()

        # Parse the line as AST
        try:
            tree = ast.parse(source_line)
        except SyntaxError:
            # If it's not a complete statement, try wrapping it
            tree = ast.parse(f"dummy = {source_line}")

        # Find the validate_type or ensure_type call
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and
                isinstance(node.func, ast.Name) and
                node.func.id in ['validate_type', 'ensure_type', 'assert_type', 'assert_range', 'assert_length', 'assert_not_none', 'is_type', 'assert_numeric', 'assert_string_like', 'assert_sequence', 'assert_mapping']):

                if node.args:
                    first_arg = node.args[0]
                    return _extract_name_from_ast_node(first_arg)

        # Fallback: try regex pattern matching
        return _extract_variable_name_regex(source_line)

    except Exception:
        return "value"

def _extract_name_from_ast_node(node) -> str:
    """
    Extract variable name from an AST node.

    Args:
        node: AST node representing the variable

    Returns:
        str: The variable name
    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        # Handle attribute access like obj.attr
        value_name = _extract_name_from_ast_node(node.value)
        return f"{value_name}.{node.attr}"
    elif isinstance(node, ast.Subscript):
        # Handle subscript access like obj[key]
        value_name = _extract_name_from_ast_node(node.value)
        return f"{value_name}[...]"
    elif isinstance(node, ast.Call):
        # Handle function calls
        if isinstance(node.func, ast.Name):
            return f"{node.func.id}(...)"
        elif isinstance(node.func, ast.Attribute):
            return f"{_extract_name_from_ast_node(node.func)}(...)"

    return "expression"

def _extract_variable_name_regex(source_line: str) -> str:
    """
    Fallback method using regex to extract variable name.

    Args:
        source_line: The source code line

    Returns:
        str: The extracted variable name
    """
    # Pattern to match assert functions
    patterns = [
        r'(?:validate_type|ensure_type|assert_type|assert_range|assert_length|assert_not_none|is_type|assert_numeric|assert_string_like|assert_sequence|assert_mapping|assert_path|is_not_none)\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\[[^\]]*\])*)',
        r'(?:validate_type|ensure_type|assert_type|assert_range|assert_length|assert_not_none|is_type|assert_numeric|assert_string_like|assert_sequence|assert_mapping|assert_path|is_not_none)\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)',
        r'(?:validate_type|ensure_type|assert_type|assert_range|assert_length|assert_not_none|is_type|assert_numeric|assert_string_like|assert_sequence|assert_mapping|assert_path|is_not_none)\s*\(\s*([^,\)]+)'
    ]


    for pattern in patterns:
        match = re.search(pattern, source_line)
        if match:
            var_name = match.group(1).strip()
            # Clean up common artifacts
            var_name = re.sub(r'\s+', '', var_name)
            return var_name

    return "value"

def _find_original_caller_frame():
    """
    Find the original caller frame, skipping internal function calls.

    Returns:
        frame: The frame of the original caller
    """
    frame = inspect.currentframe()

    # Skip frames until we find one that's not from our internal functions
    while frame:
        frame = frame.f_back
        if frame is None:
            break

        # Get the function name from the frame
        func_name = frame.f_code.co_name

        # Skip our internal functions
        if func_name not in ['validate_type', 'ensure_type', 'assert_type', 'assert_range',
                           'assert_length', 'assert_not_none', 'is_type', 'assert_numeric',
                           'assert_string_like', 'assert_sequence', 'assert_mapping', 'assert_path',
                           'is_not_none', '_extract_variable_name_from_source', '_extract_name_from_ast_node',
                           '_extract_variable_name_regex', '_find_original_caller_frame']:

            return frame

    # Fallback to immediate caller if we can't find a suitable frame
    return inspect.currentframe().f_back  # type:ignore

# Core TypeGuard functions for conditional type checking
def is_type(value: Any, expected_type: Type[T]) -> TypeGuard[T]:
    """
    Type guard function that checks if a value is of the expected type.
    Use this for conditional type checking without exceptions.

    Args:
        value: The value to check
        expected_type: The type to check against

    Returns:
        bool: True if the value is of the expected type

    Example:
        >>> data: Any = "hello"
        >>> if is_type(data, str):
        ...     # data is now known to be str by the type checker
        ...     print(data.upper())  # No type error
    """
    return isinstance(value, expected_type)

def is_not_none(value: Optional[T]) -> TypeGuard[T]:
    """
    Type guard function that checks if a value is not None.
    Use this for Optional type narrowing without exceptions.

    Args:
        value: The value to check

    Returns:
        bool: True if the value is not None

    Example:
        >>> data: Optional[str] = get_some_data()
        >>> if is_not_none(data):
        ...     # data is now known to be str (not Optional[str])
        ...     print(data.upper())  # No type error
    """
    return value is not None

# Unified assertion functions with TypeGuard benefits
def assert_type(value: Any, expected_type: Union[Type[T], List[Type]],
                msg: Optional[str] = None) -> T:
    """
    Assert that a value matches the expected type(s) and return it with proper typing.
    Combines NASA-style runtime assertion with TypeGuard benefits.

    Args:
        value: The value to check
        expected_type: A type or list of types to check against
        msg: Optional custom error message

    Returns:
        The original value with proper type annotation

    Raises:
        TypeAssertionError: If the value doesn't match the expected type(s)

    Example:
        >>> data: Any = "hello"
        >>> validated_data = assert_type(data, str)
        >>> # validated_data is now known to be str by the type checker
    """
    given_type = type(value)

    # Dynamically extract variable name from calling context
    frame = _find_original_caller_frame()
    var_name = _extract_variable_name_from_source(frame)

    # Check if the type is valid
    if isinstance(expected_type, list):
        if not any(isinstance(value, t) for t in expected_type):
            type_names = [getattr(t, "__name__", str(t)) for t in expected_type]
            error_msg = msg or f"'{var_name}' must be one of types {type_names}, but got '{given_type.__name__}'"
            raise TypeAssertionError(error_msg)
    else:
        if not isinstance(value, expected_type):
            type_name = getattr(expected_type, "__name__", str(expected_type))
            error_msg = msg or f"'{var_name}' must be of type '{type_name}', but got '{given_type.__name__}'"
            raise TypeAssertionError(error_msg)

    return value  # type: ignore[return-value]

def assert_not_none(value: Optional[T], msg: Optional[str] = None) -> T:
    """
    Assert that a value is not None and return it with proper typing.
    Acts as both assertion and type guard, narrowing Optional[T] to T.

    Args:
        value: The value to check
        msg: Optional custom error message

    Returns:
        The original value (with None type removed)

    Raises:
        TypeAssertionError: If the value is None

    Example:
        >>> data: Optional[str] = get_some_data()
        >>> validated_data = assert_not_none(data)
        >>> # validated_data is now known to be str (not Optional[str])
    """
    if value is None:
        frame = _find_original_caller_frame()
        var_name = _extract_variable_name_from_source(frame)
        error_msg = msg or f"'{var_name}' must not be None"
        raise TypeAssertionError(error_msg)

    return value

def assert_numeric(value: Any, min_val: Optional[Union[int, float]] = None,
                   max_val: Optional[Union[int, float]] = None,
                   msg: Optional[str] = None) -> Union[int, float]:
    """
    Assert that a value is numeric (int or float) and optionally within range.
    Returns the value with proper numeric typing.

    Args:
        value: The value to check
        min_val: Optional minimum allowed value (inclusive)
        max_val: Optional maximum allowed value (inclusive)
        msg: Optional custom error message

    Returns:
        The original value as Union[int, float]

    Raises:
        TypeAssertionError: If the value is not numeric or out of range

    Example:
        >>> speed: Any = 65.5
        >>> validated_speed = assert_numeric(speed, min_val=0, max_val=100)
        >>> # validated_speed is now known to be Union[int, float]
    """
    frame = _find_original_caller_frame()
    var_name = _extract_variable_name_from_source(frame)

    # Check if it's numeric
    if not isinstance(value, (int, float)):
        error_msg = msg or f"'{var_name}' must be numeric (int or float), but got '{type(value).__name__}'"
        raise TypeAssertionError(error_msg)

    # Check range if specified
    if min_val is not None and value < min_val:
        error_msg = msg or f"'{var_name}' must be >= {min_val}, but got {value}"
        raise TypeAssertionError(error_msg)

    if max_val is not None and value > max_val:
        error_msg = msg or f"'{var_name}' must be <= {max_val}, but got {value}"
        raise TypeAssertionError(error_msg)

    return value

def assert_string_like(value: Any, min_len: Optional[int] = None,
                       max_len: Optional[int] = None,
                       msg: Optional[str] = None) -> Union[str, bytes]:
    """
    Assert that a value is string-like (str or bytes) and optionally check length.
    Returns the value with proper string typing.

    Args:
        value: The value to check
        min_len: Optional minimum allowed length (inclusive)
        max_len: Optional maximum allowed length (inclusive)
        msg: Optional custom error message

    Returns:
        The original value as Union[str, bytes]

    Raises:
        TypeAssertionError: If the value is not string-like or length is invalid

    Example:
        >>> name: Any = "Aggienaut"
        >>> validated_name = assert_string_like(name, min_len=1, max_len=50)
        >>> # validated_name is now known to be Union[str, bytes]
    """
    frame = _find_original_caller_frame()
    var_name = _extract_variable_name_from_source(frame)

    # Check if it's string-like
    if not isinstance(value, (str, bytes)):
        error_msg = msg or f"'{var_name}' must be string-like (str or bytes), but got '{type(value).__name__}'"
        raise TypeAssertionError(error_msg)

    # Check length if specified
    if min_len is not None and len(value) < min_len:
        error_msg = msg or f"'{var_name}' must have length >= {min_len}, but got {len(value)}"
        raise TypeAssertionError(error_msg)

    if max_len is not None and len(value) > max_len:
        error_msg = msg or f"'{var_name}' must have length <= {max_len}, but got {len(value)}"
        raise TypeAssertionError(error_msg)

    return value

def assert_sequence(value: Any, min_len: Optional[int] = None,
                    max_len: Optional[int] = None,
                    length: Optional[int] = None,
                    msg: Optional[str] = None) -> Union[list, tuple]:
    """
    Assert that a value is a sequence (list or tuple) and optionally check length.
    Returns the value with proper sequence typing.

    Args:
        value: The value to check
        min_len: Optional minimum allowed length (inclusive)
        max_len: Optional maximum allowed length (inclusive)
        msg: Optional custom error message

    Returns:
        The original value as Union[list, tuple]

    Raises:
        TypeAssertionError: If the value is not a sequence or length is invalid

    Example:
        >>> coordinates: Any = [28.428598, -94.014643]
        >>> validated_coords = assert_sequence(coordinates, min_len=2, max_len=3)
        >>> # validated_coords is now known to be Union[list, tuple]
    """
    frame = _find_original_caller_frame()
    var_name = _extract_variable_name_from_source(frame)

    # Check if it's a sequence
    if not isinstance(value, (list, tuple)):
        error_msg = msg or f"'{var_name}' must be a sequence (list or tuple), but got '{type(value).__name__}'"
        raise TypeAssertionError(error_msg)

    # Check length if specified
    if min_len is not None and len(value) < min_len:
        error_msg = msg or f"'{var_name}' must have length >= {min_len}, but got {len(value)}"
        raise TypeAssertionError(error_msg)

    if max_len is not None and len(value) > max_len:
        error_msg = msg or f"'{var_name}' must have length <= {max_len}, but got {len(value)}"
        raise TypeAssertionError(error_msg)

    if length is not None and len(value) != length:
        error_msg = msg or f"'{var_name}' must have length = {length}, but got {len(value)}"
        raise TypeAssertionError(error_msg)

    return value

def assert_mapping(value: Any, required_keys: Optional[Union[str, List[str]]] = None,
                   msg: Optional[str] = None) -> dict:
    """
    Assert that a value is a mapping (dict) and optionally check for required keys.
    Returns the value with proper dict typing.

    Args:
        value: The value to check
        required_keys: Optional key(s) that must be present. Can be a single string or list of strings
        msg: Optional custom error message

    Returns:
        The original value as dict

    Raises:
        TypeAssertionError: If the value is not a dict or missing required keys

    Example:
        >>> config: Any = {"lat": 28.428598, "lon": -94.014643}
        >>> # Single key
        >>> validated_config = assert_mapping(config, required_keys="lat")
        >>> # Multiple keys
        >>> validated_config = assert_mapping(config, required_keys=["lat", "lon"])
        >>> # validated_config is now known to be dict
    """
    frame = _find_original_caller_frame()
    var_name = _extract_variable_name_from_source(frame)

    # Check if it's a mapping
    if not isinstance(value, dict):
        error_msg = msg or f"'{var_name}' must be a mapping (dict), but got '{type(value).__name__}'"
        raise TypeAssertionError(error_msg)

    # Check required keys if specified
    if required_keys is not None:
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
            raise TypeAssertionError(error_msg)

    return value

def assert_path(value: Any, must_exist: Optional[bool] = None,
                must_be_file: bool = False, must_be_dir: bool = False,
                create_parents: bool = False, msg: Optional[str] = None) -> Path:
    """
    Assert that a value can be converted to a pathlib.Path and optionally validate its existence.
    Returns a pathlib.Path object with proper typing.

    Args:
        value: The value to convert (str, bytes, Path, or path-like object)
        must_exist: If True, path must exist. If False, path must not exist. If None, no check
        must_be_file: If True, path must be an existing file
        must_be_dir: If True, path must be an existing directory
        create_parents: If True, create parent directories if they don't exist
        msg: Optional custom error message

    Returns:
        The value as pathlib.Path

    Raises:
        TypeAssertionError: If the value cannot be converted to Path or validation fails

    Example:
        >>> config_path: Any = "/etc/config.json"
        >>> validated_path = assert_path(config_path, must_exist=True, must_be_file=True)
        >>> # validated_path is now known to be Path and exists as a file

        >>> output_dir: Any = "logs"
        >>> log_dir = assert_path(output_dir, must_be_dir=True, create_parents=True)
        >>> # log_dir is now a Path, and parent dirs are created if needed
    """
    frame = _find_original_caller_frame()
    var_name = _extract_variable_name_from_source(frame)

    # Try to convert to Path
    try:
        if isinstance(value, Path):
            path_obj = value
        elif isinstance(value, (str, bytes)):
            path_obj = Path(str(value))
        else:
            # Try to handle path-like objects (os.PathLike)
            path_obj = Path(value)
    except (TypeError, ValueError) as e:
        error_msg = msg or f"'{var_name}' cannot be converted to a Path: {e}"
        raise TypeAssertionError(error_msg)

    # Validate string-like input wasn't empty
    if isinstance(value, (str, bytes)) and len(value.strip() if isinstance(value, str) else value) == 0:
        error_msg = msg or f"'{var_name}' cannot be an empty path"
        raise TypeAssertionError(error_msg)

    # Create parent directories if requested
    if create_parents and not path_obj.parent.exists():
        try:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            error_msg = msg or f"'{var_name}' parent directories could not be created: {e}"
            raise TypeAssertionError(error_msg)

    # Check existence requirements
    if must_exist is True and not path_obj.exists():
        error_msg = msg or f"'{var_name}' path must exist, but '{path_obj}' does not exist"
        raise TypeAssertionError(error_msg)

    if must_exist is False and path_obj.exists():
        error_msg = msg or f"'{var_name}' path must not exist, but '{path_obj}' already exists"
        raise TypeAssertionError(error_msg)

    # Check file/directory requirements
    if must_be_file:
        if not path_obj.exists():
            error_msg = msg or f"'{var_name}' must be an existing file, but '{path_obj}' does not exist"
            raise TypeAssertionError(error_msg)
        if not path_obj.is_file():
            error_msg = msg or f"'{var_name}' must be a file, but '{path_obj}' is not a file"
            raise TypeAssertionError(error_msg)

    if must_be_dir:
        if not path_obj.exists():
            error_msg = msg or f"'{var_name}' must be an existing directory, but '{path_obj}' does not exist"
            raise TypeAssertionError(error_msg)
        if not path_obj.is_dir():
            error_msg = msg or f"'{var_name}' must be a directory, but '{path_obj}' is not a directory"
            raise TypeAssertionError(error_msg)

    return path_obj


def assert_range(value: Union[int, float], min_val: Optional[Union[int, float]] = None,
                 max_val: Optional[Union[int, float]] = None, msg: Optional[str] = None) -> Union[int, float]:
    """
    Assert that a numeric value is within the specified range.
    Note: Use assert_numeric() if you also need type checking.

    Args:
        value: The numeric value to check
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        msg: Optional custom error message

    Returns:
        The original value

    Raises:
        TypeAssertionError: If the value is out of range
    """
    frame = _find_original_caller_frame()
    var_name = _extract_variable_name_from_source(frame)

    if min_val is not None and value < min_val:
        error_msg = msg or f"'{var_name}' must be >= {min_val}, but got {value}"
        raise TypeAssertionError(error_msg)

    if max_val is not None and value > max_val:
        error_msg = msg or f"'{var_name}' must be <= {max_val}, but got {value}"
        raise TypeAssertionError(error_msg)

    return value

def assert_length(value: Any, min_len: Optional[int] = None, max_len: Optional[int] = None,
                  msg: Optional[str] = None) -> Any:
    """
    Assert that a value has a length within the specified range.
    Note: Use assert_string_like() or assert_sequence() for combined type+length checking.

    Args:
        value: The value to check (must have __len__)
        min_len: Minimum allowed length (inclusive)
        max_len: Maximum allowed length (inclusive)
        msg: Optional custom error message

    Returns:
        The original value

    Raises:
        TypeAssertionError: If the length is out of range
    """
    frame = _find_original_caller_frame()
    var_name = _extract_variable_name_from_source(frame)

    try:
        length = len(value)
    except TypeError:
        error_msg = f"'{var_name}' must have a length, but got {type(value).__name__}"
        raise TypeAssertionError(error_msg)

    if min_len is not None and length < min_len:
        error_msg = msg or f"'{var_name}' must have length >= {min_len}, but got {length}"
        raise TypeAssertionError(error_msg)

    if max_len is not None and length > max_len:
        error_msg = msg or f"'{var_name}' must have length <= {max_len}, but got {length}"
        raise TypeAssertionError(error_msg)

    return value

def validate_type(value: Any, expected_type: Union[Type, List[Type]]) -> bool:
    """
    Validates that a value matches the expected type(s).
    Automatically extracts the variable name from the calling context.

    DEPRECATED: Use assert_type() for NASA-style assertions or is_type() for TypeGuard support.

    Args:
        value: The value to check
        expected_type: A type or list of types to check against

    Returns:
        bool: True if the value matches the expected type(s)

    Raises:
        TypeError: If the value doesn't match the expected type(s)
    """
    warnings.warn(
        "validate_type() is deprecated and will be removed in a future version. "
        "Use assert_type() for NASA-style runtime assertions or is_type() for TypeGuard support.",
        DeprecationWarning,
        stacklevel=2
    )

    given_type = type(value)

    # Dynamically extract variable name from calling context
    frame = _find_original_caller_frame()
    var_name = _extract_variable_name_from_source(frame)

    # Check if the type is valid
    if isinstance(expected_type, list):
        if not any(isinstance(value, t) for t in expected_type):
            type_names = [getattr(t, "__name__", str(t)) for t in expected_type]
            raise TypeError(f"'{var_name}' must be one of types {type_names}, but got '{given_type.__name__}'")
    else:
        if not isinstance(value, expected_type):
            type_name = getattr(expected_type, "__name__", str(expected_type))
            raise TypeError(f"'{var_name}' must be of type '{type_name}', but got '{given_type.__name__}'")

    return True

def ensure_type(value: Any, expected_type: Union[Type[T], List[Type]]) -> T:
    """
    Validates the type and returns the value if valid.
    This is useful for function chaining.
    Automatically extracts the variable name from the calling context.

    DEPRECATED: Use assert_type() instead for NASA-style assertions.

    Args:
        value: The value to check
        expected_type: A type or list of types to check against

    Returns:
        The original value if it matches the expected type(s)

    Raises:
        TypeError: If the value doesn't match the expected type(s)
    """
    warnings.warn(
        "ensure_type() is deprecated and will be removed in a future version. "
        "Use assert_type() instead for NASA-style runtime assertions.",
        DeprecationWarning,
        stacklevel=2
    )

    validate_type(value, expected_type)
    return value

# A decorator approach for function parameters
def type_checked(func):
    """
    Decorator that validates function arguments against their type hints.

    Args:
        func: The function to decorate

    Returns:
        Decorated function with type checking
    """
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)

    def wrapper(*args, **kwargs):
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()

        for param_name, param_value in bound_args.arguments.items():
            if param_name in type_hints:
                expected_type = type_hints[param_name]
                try:
                    assert_type(param_value, expected_type)
                except TypeAssertionError as e:
                    # Replace the auto-detected name with the parameter name for clarity
                    error_msg = str(e)
                    if "'" in error_msg:
                        # Replace the first quoted variable name with the parameter name
                        error_msg = re.sub(r"'[^']*'", f"'{param_name}'", error_msg, count=1)
                    raise TypeError(f"In call to {func.__name__}: {error_msg}")

        return func(*args, **kwargs)

    return wrapper
