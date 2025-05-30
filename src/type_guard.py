# type_guard.py

from typing import Any,Type,TypeVar,TypeGuard,Optional

from src.core import TypeValidationEngine

T = TypeVar('T')

# Export the methods as module-level functions for backward compatibility
def is_type(value: Any, expected_type: Type[T]) -> TypeGuard[T]:
    """Type guard function that checks if a value is of the expected type."""
    return TypeValidationEngine().is_type(value, expected_type)

def is_not_none(value: Optional[T]) -> TypeGuard[T]:
    """Type guard function that checks if a value is not None."""
    return TypeValidationEngine().is_not_none(value)