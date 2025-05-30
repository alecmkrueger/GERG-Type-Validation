# variable_name_extractor.py

import inspect
import ast
import re

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