"""Novel2Video PromptEngine MVP package."""

from .pipeline import generate_from_text, generate_markdown_report

__all__ = ["generate_from_text", "generate_markdown_report"]
__version__ = "0.1.0"
