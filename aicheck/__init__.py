"""aicheck: kiểm tra văn bản (tiếng Việt và tiếng Anh) do AI hay người viết."""

from .detector import Detector, Report  # noqa: F401
from .heuristics import analyze  # noqa: F401

__version__ = "1.0.0"
