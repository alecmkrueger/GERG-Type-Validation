import re
from typing import Any,Optional,List,Union

from gerg_type_validation.type_validation_engine import TypeValidationEngine

# Utility functions for common validation patterns
class ValidationPatterns:
    """Collection of common validation patterns and utilities."""

    @staticmethod
    def validate_email(value: Any, engine: Optional[TypeValidationEngine] = None) -> str:
        """Validate that a value is a properly formatted email address."""
        if engine is None:
            engine = TypeValidationEngine()

        validated_str = engine.assert_string_like(value, min_len=1)

        # Simple email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, validated_str):  #type:ignore
            var_name = engine._get_variable_name()
            raise engine.config.custom_error_class(f"'{var_name}' must be a valid email address")

        return validated_str  #type:ignore

    @staticmethod
    def validate_url(value: Any, schemes: Optional[List[str]] = None,
                     engine: Optional[TypeValidationEngine] = None) -> str:
        """Validate that a value is a properly formatted URL."""
        if engine is None:
            engine = TypeValidationEngine()
        if schemes is None:
            schemes = ['http', 'https']

        validated_str = engine.assert_string_like(value, min_len=1)

        # Simple URL validation
        url_pattern = engine.assert_string_like(r'^(' + '|'.join(schemes) + r')://[^\s/$.?#].[^\s]*$')
        if not re.match(url_pattern, validated_str, re.IGNORECASE):  #type:ignore
            var_name = engine._get_variable_name()
            raise engine.config.custom_error_class(f"'{var_name}' must be a valid URL with scheme {schemes}")

        return validated_str  #type:ignore

    @staticmethod
    def validate_positive_number(value: Any, engine: Optional[TypeValidationEngine] = None) -> Union[int, float]:
        """Validate that a value is a positive number."""
        if engine is None:
            engine = TypeValidationEngine()

        return engine.assert_numeric(value, min_val=0.0001)  # Slightly above 0 to exclude 0

    @staticmethod
    def validate_non_negative_number(value: Any, engine: Optional[TypeValidationEngine] = None) -> Union[int, float]:
        """Validate that a value is a non-negative number (>= 0)."""
        if engine is None:
            engine = TypeValidationEngine()

        return engine.assert_numeric(value, min_val=0)

    @staticmethod
    def validate_percentage(value: Any, engine: Optional[TypeValidationEngine] = None) -> Union[int, float]:
        """Validate that a value is a percentage (0-100)."""
        if engine is None:
            engine = TypeValidationEngine()

        return engine.assert_numeric(value, min_val=0, max_val=100)

    @staticmethod
    def validate_non_empty_string(value: Any, engine: Optional[TypeValidationEngine] = None) -> str:
        """Validate that a value is a non-empty string."""
        if engine is None:
            engine = TypeValidationEngine()

        validated_str = engine.assert_type(value, str)
        if not validated_str.strip():
            var_name = engine._get_variable_name()
            raise engine.config.custom_error_class(f"'{var_name}' must be a non-empty string")

        return validated_str

# Batch validation utilities
class BatchValidator:
    """Utility class for validating multiple values at once."""

    def __init__(self, engine: Optional[TypeValidationEngine] = None):
        self.engine = engine or TypeValidationEngine()
        self.errors = []

    def add_validation(self, value: Any, validator_func, *args, **kwargs):
        """Add a validation to the batch."""
        try:
            validator_func(value, *args, **kwargs)
        except Exception as e:
            self.errors.append(str(e))

    def validate_all(self, raise_on_error: bool = True) -> bool:
        """Execute all validations and optionally raise on any errors."""
        if self.errors and raise_on_error:
            error_msg = "Batch validation failed:\n" + "\n".join(f"  - {error}" for error in self.errors)
            raise self.engine.config.custom_error_class(error_msg)

        return len(self.errors) == 0

    def get_errors(self) -> List[str]:
        """Get all validation errors."""
        return self.errors.copy()

    def clear_errors(self):
        """Clear all accumulated errors."""
        self.errors.clear()
