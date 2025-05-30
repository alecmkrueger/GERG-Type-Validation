# validation_context.py
# Context manager for temporary validation configuration

from gerg_type_validation.type_validation_engine import TypeValidationEngine
from gerg_type_validation.validation_config import ValidationConfig

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