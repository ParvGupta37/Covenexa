"""
Base Prompt class.
Standard template structure for string interpolation of variables.
"""
from typing import Any


class BasePrompt:
    """
    Abstract base for reusable prompt templates.
    """

    def __init__(self, template: str) -> None:
        self._template = template

    def format(self, **kwargs: Any) -> str:
        """Interpolates variables dynamically into the template."""
        return self._template.format(**kwargs)
