# validation_config.py


class ValidationConfig:
    from typing import Type

    from gerg_type_validation.exceptions import TypeAssertionError
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
