"""Contains dataclasses for entries in a depth column."""

from typing import Any

import fitz


class DepthColumnEntry:  # noqa: D101
    """Class to represent a depth column entry."""

    def __init__(self, rect: fitz.Rect, value: float, page_number: int):
        self.rect = rect
        self.value = value
        self.page_number = page_number

    def __repr__(self) -> str:
        return str(self.value)

    def to_json(self) -> dict[str, Any]:
        """Convert the depth column entry to a JSON serializable format."""
        return {
            "value": self.value,
            "rect": [self.rect.x0, self.rect.y0, self.rect.x1, self.rect.y1],
            "page": self.page_number,
        }


class AnnotatedDepthColumnEntry(DepthColumnEntry):  # noqa: D101
    """Class to represent a depth column entry obtained from LabelStudio.

    The annotation process in label studio does not come with rectangles for depth column entries.
    Therefore, we set them to None.
    """

    def __init__(self, value):
        super().__init__(None, value, None)

    def to_json(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "rect": self.rect,
            "page": self.page_number,
        }


class LayerDepthColumnEntry:  # noqa: D101
    """Class to represent a layer depth column entry."""

    def __init__(self, start: DepthColumnEntry, end: DepthColumnEntry):
        self.start = start
        self.end = end

        assert start.page_number == end.page_number, "Start and end entries are on different pages."

    def __repr__(self) -> str:
        return f"{self.start.value}-{self.end.value}"

    @property
    def rect(self) -> fitz.Rect:
        """Get the rectangle of the layer depth column entry."""
        return fitz.Rect(self.start.rect).include_rect(self.end.rect)

    def to_json(self) -> dict[str, Any]:
        """Convert the layer depth column entry to a JSON serializable format."""
        return {
            "start": self.start.to_json(),
            "end": self.end.to_json(),
            "rect": [self.rect.x0, self.rect.y0, self.rect.x1, self.rect.y1],
            "page": self.start.page_number,
        }