"""aicheck: tell whether text was written by AI or a person."""

from .detector import Detector, Report  # noqa: F401
from .heuristics import analyze  # noqa: F401

__version__ = "2.0.0"
