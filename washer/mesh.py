"""Triangle meshes, built only out of things that cannot leak.

Two constructors carry the whole part:

  loft/tube   a stack of rings with a shared parameterisation, side-walled with
              quads and capped with annuli. A tube built this way is closed and
              two-manifold by construction -- the fluid channel is not cut out
              of the body, it *is* the body's inner wall.
  hexahedron  eight corners, twelve triangles. The clip and the gauge are made
              of these.

`check()` is not decoration. It re-derives closure from the triangle soup that
actually gets written: every directed edge exactly once, its reverse exactly
once, and a positive enclosed volume. A mesh that fails that is refused rather
than shipped, the same way the lamp refuses unprintable g-code.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

Vec = tuple[float, float, float]
Ring = list[Vec]


def _sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def centroid(ring: Ring) -> Vec:
    n = len(ring)
    return (sum(p[0] for p in ring) / n,
            sum(p[1] for p in ring) / n,
            sum(p[2] for p in ring) / n)


@dataclass
class Report:
    closed: bool
    manifold: bool
    volume: float
    triangles: int
    degenerate: int
    solids: int = 1
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.closed and self.manifold and self.volume > 0 and not self.problems


class Mesh:
    """A triangle soup. May hold several closed solids; slicers union them."""

    def __init__(self) -> None:
        self.tris: list[tuple[Vec, Vec, Vec]] = []
        #: [start, end) of each closed solid. A part may be several overlapping
        #: solids -- slicers union them -- so closure is checked per solid, not
        #: over the whole soup, where two touching boxes would look like a fault.
        self.solids: list[tuple[int, int]] = []
        self._mark = 0

    def __len__(self) -> int:
        return len(self.tris)

    def _close(self) -> None:
        if len(self.tris) > self._mark:
            self.solids.append((self._mark, len(self.tris)))
        self._mark = len(self.tris)

    # -- primitives ----------------------------------------------------------
    def tri(self, a: Vec, b: Vec, c: Vec) -> None:
        self.tris.append((a, b, c))

    def quad(self, a: Vec, b: Vec, c: Vec, d: Vec) -> None:
        """Quad a-b-c-d, wound so the normal follows the right hand rule."""
        self.tri(a, b, c)
        self.tri(a, c, d)

    def add(self, other: "Mesh") -> "Mesh":
        base = len(self.tris)
        self.tris.extend(other.tris)
        self.solids.extend((a + base, b + base) for a, b in other.solids)
        self._mark = len(self.tris)
        return self

    # -- lofts ---------------------------------------------------------------
    def wall(self, lower: Ring, upper: Ring, outward: bool = True) -> None:
        """Quad strip between two rings of equal length."""
        if len(lower) != len(upper):
            raise ValueError("rings must share a parameterisation")
        n = len(lower)
        for i in range(n):
            j = (i + 1) % n
            a, b, c, d = lower[i], lower[j], upper[j], upper[i]
            if outward:
                self.quad(a, b, c, d)
            else:
                self.quad(d, c, b, a)

    def fan(self, ring: Ring, up: bool) -> None:
        """Cap a star-shaped ring from its centroid."""
        c = centroid(ring)
        n = len(ring)
        for i in range(n):
            j = (i + 1) % n
            if up:
                self.tri(c, ring[i], ring[j])
            else:
                self.tri(c, ring[j], ring[i])

    def annulus(self, outer: Ring, inner: Ring, up: bool) -> None:
        """Flat ring between an outer and an inner boundary at the same level."""
        n = len(outer)
        for i in range(n):
            j = (i + 1) % n
            if up:
                self.quad(outer[i], outer[j], inner[j], inner[i])
            else:
                self.quad(inner[i], inner[j], outer[j], outer[i])

    def loft(self, rings: list[Ring], cap_bottom: bool = True,
             cap_top: bool = True) -> None:
        for lo, up in zip(rings, rings[1:]):
            self.wall(lo, up)
        if cap_bottom:
            self.fan(rings[0], up=False)
        if cap_top:
            self.fan(rings[-1], up=True)
        self._close()

    def tube(self, outer: list[Ring], inner: list[Ring]) -> None:
        """A solid with a hole through it: outer skin, inner skin, two end faces."""
        for lo, up in zip(outer, outer[1:]):
            self.wall(lo, up, outward=True)
        for lo, up in zip(inner, inner[1:]):
            self.wall(lo, up, outward=False)
        self.annulus(outer[0], inner[0], up=False)
        self.annulus(outer[-1], inner[-1], up=True)
        self._close()

    def hexahedron(self, bottom: list[Vec], top: list[Vec]) -> None:
        """Six faces from two counter-clockwise quads. Corners may be anywhere."""
        b0, b1, b2, b3 = bottom
        t0, t1, t2, t3 = top
        self.quad(b0, b3, b2, b1)          # bottom, facing down
        self.quad(t0, t1, t2, t3)          # top, facing up
        self.quad(b0, b1, t1, t0)
        self.quad(b1, b2, t2, t1)
        self.quad(b2, b3, t3, t2)
        self.quad(b3, b0, t0, t3)
        self._close()

    def box(self, x0: float, x1: float, y0: float, y1: float,
            z0: float, z1: float) -> None:
        self.hexahedron([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
                        [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])

    # -- transforms ----------------------------------------------------------
    def _like(self) -> "Mesh":
        out = Mesh()
        out.solids = list(self.solids)
        return out

    def flipped(self) -> "Mesh":
        """Turn the part over (rotate 180 about x) and keep the winding right."""
        out = self._like()
        f = lambda p: (p[0], -p[1], -p[2])
        for a, b, c in self.tris:
            # A half turn is a proper rotation, so the winding stays as it is.
            out.tri(f(a), f(b), f(c))
        return out

    def translated(self, dx: float, dy: float, dz: float) -> "Mesh":
        out = self._like()
        for a, b, c in self.tris:
            f = lambda p: (p[0] + dx, p[1] + dy, p[2] + dz)
            out.tri(f(a), f(b), f(c))
        return out

    def bbox(self) -> tuple[Vec, Vec]:
        pts = [p for t in self.tris for p in t]
        lo = tuple(min(p[i] for p in pts) for i in range(3))
        hi = tuple(max(p[i] for p in pts) for i in range(3))
        return lo, hi  # type: ignore[return-value]

    # -- checks --------------------------------------------------------------
    def volume(self, lo: int = 0, hi: int | None = None) -> float:
        """Signed volume in mm^3. Positive when normals point outwards.

        Overlapping solids double-count where they overlap, so this is an upper
        bound on the material of a multi-solid part, not the slicer's answer.
        """
        v = 0.0
        for a, b, c in self.tris[lo:hi if hi is not None else len(self.tris)]:
            v += _dot(a, _cross(b, c))
        return v / 6.0

    def check(self) -> Report:
        problems: list[str] = []
        degenerate = 0
        open_solids = 0
        nonmanifold = 0
        inverted = 0
        spans = self.solids or [(0, len(self.tris))]
        for lo, hi in spans:
            edges: dict[tuple[Vec, Vec], int] = {}
            for a, b, c in self.tris[lo:hi]:
                if a == b or b == c or c == a:
                    degenerate += 1
                    continue
                for e in ((a, b), (b, c), (c, a)):
                    edges[e] = edges.get(e, 0) + 1
            unmatched = sum(1 for (a, b), n in edges.items()
                            if edges.get((b, a), 0) != n)
            over = sum(1 for n in edges.values() if n > 1)
            if unmatched:
                open_solids += 1
            if over:
                nonmanifold += 1
            if self.volume(lo, hi) <= 0:
                inverted += 1
        if open_solids:
            problems.append(f"{open_solids} of {len(spans)} solids are not closed")
        if nonmanifold:
            problems.append(f"{nonmanifold} solids have an edge in three faces")
        if inverted:
            problems.append(f"{inverted} solids are inside out")
        if degenerate:
            problems.append(f"{degenerate} zero-area triangles")
        return Report(closed=not open_solids, manifold=not nonmanifold,
                      volume=self.volume(), triangles=len(self.tris),
                      degenerate=degenerate, solids=len(spans),
                      problems=problems)

    # -- output --------------------------------------------------------------
    def to_stl(self, name: str = "washer-nozzle") -> bytes:
        out = bytearray()
        header = name.encode()[:79].ljust(80, b"\0")
        out += header
        out += struct.pack("<I", len(self.tris))
        for a, b, c in self.tris:
            n = _cross(_sub(b, a), _sub(c, a))
            ln = (n[0] ** 2 + n[1] ** 2 + n[2] ** 2) ** 0.5
            if ln:
                n = (n[0] / ln, n[1] / ln, n[2] / ln)
            out += struct.pack("<12fH", *n, *a, *b, *c, 0)
        return bytes(out)
