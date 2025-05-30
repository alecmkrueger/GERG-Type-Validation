# factory_functions.py

from typing import Type

from src.exceptions import TypeAssertionError
from src.core import TypeValidationEngine,ValidationConfig

# Factory functions for creating custom configurations
def create_validation_engine(strict_mode: bool = True,
                           auto_extract_names: bool = True,
                           raise_on_failure: bool = True,
                           custom_error_class: Type[Exception] = TypeAssertionError) -> TypeValidationEngine:
    """Factory function to create a custom TypeValidationEngine with specific configuration."""
    config = ValidationConfig(
        strict_mode=strict_mode,
        auto_extract_names=auto_extract_names,
        raise_on_failure=raise_on_failure,
        custom_error_class=custom_error_class
    )
    return TypeValidationEngine(config)

def create_lenient_engine() -> TypeValidationEngine:
    """Factory function to create a lenient validation engine that doesn't raise exceptions."""
    return create_validation_engine(
        strict_mode=False,
        raise_on_failure=False
    )

def create_custom_validator_engine(custom_validators: dict) -> TypeValidationEngine:
    """Factory function to create an engine with custom validators."""
    engine = TypeValidationEngine()
    engine.validators.update(custom_validators)
    return engine
