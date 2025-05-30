# schema_validator.py
from typing import Any, Optional

from src.core import TypeValidationEngine


# Schema validation for complex data structures
class SchemaValidator:
    """Validator for complex data structures using schema definitions."""

    def __init__(self, engine: Optional[TypeValidationEngine] = None):
        self.engine = engine or TypeValidationEngine()

    def validate_dict_schema(self, data: Any, schema: dict, strict: bool = True) -> dict:
        """
        Validate a dictionary against a schema.

        Args:
            data: The data to validate
            schema: Dictionary defining the expected structure
            strict: If True, no extra keys are allowed

        Schema format:
        {
            'key_name': {
                'type': Type or List[Type],
                'required': bool (default True),
                'validator': callable (optional),
                'default': Any (optional)
            }
        }
        """
        validated_data = self.engine.assert_mapping(data)
        result = {}

        # Check required fields and validate types
        for key, field_spec in schema.items():
            field_type = field_spec.get('type')
            required = field_spec.get('required', True)
            validator = field_spec.get('validator')
            default = field_spec.get('default')

            if key in validated_data:
                value = validated_data[key]

                # Type validation
                if field_type:
                    value = self.engine.assert_type(value, field_type)

                # Custom validator
                if validator:
                    value = validator(value)

                result[key] = value

            elif required:
                raise self.engine.config.custom_error_class(f"Required field '{key}' is missing")

            elif default is not None:
                result[key] = default

        # Check for extra keys in strict mode
        if strict:
            extra_keys = set(validated_data.keys()) - set(schema.keys())
            if extra_keys:
                raise self.engine.config.custom_error_class(f"Unexpected keys found: {list(extra_keys)}")

        return result

