"""Abstract base for P Logo renderers."""

from __future__ import annotations
from abc import ABC, abstractmethod
from p_logo.types import PLogoSchema


class PLogoRenderer(ABC):
    """Base class for all P logo renderers."""

    def __init__(self, schema: PLogoSchema):
        self.schema = schema

    @abstractmethod
    def render(self, output_path: str, **kwargs) -> None:
        """Render the P logo to the given output path."""
