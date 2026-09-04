"""A replacement windshield washer nozzle, generated as STL from the hole.

The hole in the panel is the only fixed dimension in this problem. Everything
else -- the plug that fills it, the wedge clip that holds it, the jet -- is
derived from that outline, so re-measuring the hole re-cuts the whole part.

    python nozzle.py --check-only
    python nozzle.py --part all --out out/washer.stl
"""

from .spec import NozzleSpec, PRESETS  # noqa: F401

__all__ = ["NozzleSpec", "PRESETS"]
