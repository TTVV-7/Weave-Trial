"""Parametric see-through woven lamp shade, printed as one continuous bead."""

from .geometry import LampSpec, Toolpath, build, check_support, stats, with_open_area
from .profiles import LAMPS, MATERIALS, PRINTERS, Material, Printer

__all__ = [
    "LampSpec", "Toolpath", "build", "check_support", "stats", "with_open_area",
    "LAMPS", "MATERIALS", "PRINTERS", "Material", "Printer",
]
