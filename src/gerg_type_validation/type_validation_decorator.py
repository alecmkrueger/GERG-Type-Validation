# type_validation_decorator.py
import re
import inspect
from typing import Optional,get_type_hints

from gerg_type_validation.type_validation_engine import TypeValidationEngine
from gerg_type_validation.exceptions import TypeAssertionError

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