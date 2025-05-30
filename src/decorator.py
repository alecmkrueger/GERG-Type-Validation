# decorator.py
from src.core import TypeValidationDecorator,TypeValidationEngine
# Decorator instance for backward compatibility
_default_decorator = TypeValidationDecorator(TypeValidationEngine())
type_checked = _default_decorator.type_checked