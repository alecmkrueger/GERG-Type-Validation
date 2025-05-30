import inspect
import ast
import re

from typing import Any,Optional,List,Union

from src.core import TypeValidationEngine

_default_engine = TypeValidationEngine()

class VariableNameExtractor:
    """Utility class for extracting variable names from source code."""

    VALIDATION_FUNCTIONS = [
        'assert_type', 'assert_range', 'assert_length',
        'assert_not_none', 'is_type', 'assert_numeric', 'assert_string_like',
        'assert_sequence', 'assert_mapping', 'assert_path', 'is_not_none'
    ]

    @classmethod
    def extract_from_frame(cls, frame) -> str:
        """Extract variable name from the calling frame using AST parsing."""
        try:
            context = inspect.getframeinfo(frame)
            if not context.code_context:
                return "value"

            source_line = context.code_context[0].strip()

            # Try AST parsing first
            try:
                tree = ast.parse(source_line)
            except SyntaxError:
                tree = ast.parse(f"dummy = {source_line}")

            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Name) and
                    node.func.id in cls.VALIDATION_FUNCTIONS):

                    if node.args:
                        return cls._extract_name_from_ast_node(node.args[0])

            # Fallback to regex
            return cls._extract_with_regex(source_line)

        except Exception:
            return "value"

    @classmethod
    def _extract_name_from_ast_node(cls, node) -> str:
        """Extract variable name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = cls._extract_name_from_ast_node(node.value)
            return f"{value_name}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            value_name = cls._extract_name_from_ast_node(node.value)
            return f"{value_name}[...]"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"{node.func.id}(...)"
            elif isinstance(node.func, ast.Attribute):
                return f"{cls._extract_name_from_ast_node(node.func)}(...)"

        return "expression"

    @classmethod
    def _extract_with_regex(cls, source_line: str) -> str:
        """Fallback method using regex to extract variable name."""
        func_names = '|'.join(cls.VALIDATION_FUNCTIONS)
        patterns = [
            rf'(?:{func_names})\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\[[^\]]*\])*)',
            rf'(?:{func_names})\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)',
            rf'(?:{func_names})\s*\(\s*([^,\)]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, source_line)
            if match:
                var_name = match.group(1).strip()
                var_name = re.sub(r'\s+', '', var_name)
                return var_name

        return "value"

# Utility functions for common validation patterns
class ValidationPatterns:
    """Collection of common validation patterns and utilities."""

    @staticmethod
    def validate_email(value: Any, engine: Optional[TypeValidationEngine] = None) -> str:
        """Validate that a value is a properly formatted email address."""
        if engine is None:
            engine = _default_engine

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
            engine = _default_engine
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
            engine = _default_engine

        return engine.assert_numeric(value, min_val=0.0001)  # Slightly above 0 to exclude 0

    @staticmethod
    def validate_non_negative_number(value: Any, engine: Optional[TypeValidationEngine] = None) -> Union[int, float]:
        """Validate that a value is a non-negative number (>= 0)."""
        if engine is None:
            engine = _default_engine

        return engine.assert_numeric(value, min_val=0)

    @staticmethod
    def validate_percentage(value: Any, engine: Optional[TypeValidationEngine] = None) -> Union[int, float]:
        """Validate that a value is a percentage (0-100)."""
        if engine is None:
            engine = _default_engine

        return engine.assert_numeric(value, min_val=0, max_val=100)

    @staticmethod
    def validate_non_empty_string(value: Any, engine: Optional[TypeValidationEngine] = None) -> str:
        """Validate that a value is a non-empty string."""
        if engine is None:
            engine = _default_engine

        validated_str = engine.assert_type(value, str)
        if not validated_str.strip():
            var_name = engine._get_variable_name()
            raise engine.config.custom_error_class(f"'{var_name}' must be a non-empty string")

        return validated_str

# Batch validation utilities
class BatchValidator:
    """Utility class for validating multiple values at once."""

    def __init__(self, engine: Optional[TypeValidationEngine] = None):
        self.engine = engine or _default_engine
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
