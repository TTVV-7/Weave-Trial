"""Toolpath geometry for the see-through woven lamp shade.

The shade is one continuous single-bead spiral whose height oscillates as it
travels around::

    z(theta) = zc(theta) + a * sin(w * theta)

``w`` (waves per turn) is a *half*-integer -- 30.5, 24.5, ... That half wave is
what makes the pattern weave. After one full revolution the sine term has
advanced by ``2*pi*w``, an odd multiple of pi, so it comes back inverted: turn
``k+1`` troughs exactly where turn ``k`` crests. The vertical gap between two
consecutive turns is therefore

    gap(theta) = dz - (a_k + a_k+1) * sin(w * theta)

which sweeps from ``dz + 2a`` (a wide open diamond) down to ``dz - 2a`` (the
turns meet and weld) twice per wave. That is the weave: 2*w bonded nodes per
revolution with an open lens between each pair.

Two numbers control it, and they are independent -- which is the whole point:

``rise_per_turn`` (dz)
    How far the spiral climbs per revolution. This alone decides how
    see-through the shade is, because each revolution lays exactly one bead
    into each ``dz`` of wall height::

        open area = 1 - bead_height / rise_per_turn

    At the 2.2 mm default with a 0.45 mm bead that is ~80% open air.

``weld_overlap``
    How far the nozzle dips below the previous turn's bead at a node, which
    sets how strongly the two weld. The amplitude follows from it::

        a = (dz + weld_overlap) / 2

WHY ``weld_overlap`` MUST STAY SMALL -- this is the trap.

It is tempting to crank the amplitude up for bigger holes. Doing that does not
work, and it is the failure mode that wrecks this print. The turns do not just
"touch more"; the descending half of turn ``k+1`` carries on down *past* turn
``k`` and keeps going. The nozzle then travels underneath a bead it already
laid, with the previous turn sitting directly over the nozzle shaft. It shears
the print off the plate.

The safe regime is a shallow dip -- roughly one bead height or less -- so the
node is an ordinary squished weld rather than a crash. Bigger holes come from
raising ``rise_per_turn``, never from raising the amplitude.
``check_support()`` measures the real dip on the generated path and fails
anything deeper.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace


TAU = 2.0 * math.pi


@dataclass
class LampSpec:
    """Every dimension of the shade, in mm."""

    # --- overall form -------------------------------------------------
    height: float = 150.0
    bottom_radius: float = 45.0
    top_radius: float = 45.0
    #: Extra bulge at mid-height. Positive = barrel, negative = waist.
    belly: float = 0.0

    # --- the weave ----------------------------------------------------
    #: Waves per revolution. MUST end in .5 -- that half wave is the weave.
    waves_per_turn: float = 30.5
    #: Climb per revolution (mm). The see-through control.
    rise_per_turn: float = 2.2
    #: Nozzle dip below the previous turn at a node (mm). The weld control.
    #: Keep at or under one bead height; see the module docstring.
    weld_overlap: float = 0.35
    #: Path resolution: straight segments per wave.
    segments_per_wave: int = 14

    # --- solid foot and rim -------------------------------------------
    foot_height: float = 3.0
    foot_walls: int = 3
    rim_height: float = 1.8
    rim_walls: int = 3
    layer_height: float = 0.25
    #: Revolutions spent fading the weave in at the foot and out at the rim.
    ramp_turns: int = 3

    # --- extrusion ----------------------------------------------------
    nozzle: float = 0.4
    #: Bead of the mesh itself. Round (w == h) is strongest in free air.
    mesh_bead_width: float = 0.45
    mesh_bead_height: float = 0.45
    #: Bead of the solid foot / rim walls.
    wall_width: float = 0.45
    filament_diameter: float = 1.75

    def __post_init__(self) -> None:
        if abs(self.waves_per_turn % 1.0 - 0.5) > 1e-9:
            raise ValueError(
                f"waves_per_turn must end in .5 (got {self.waves_per_turn}); "
                "a whole number stacks the waves instead of weaving them"
            )
        if self.rise_per_turn <= self.mesh_bead_height:
            raise ValueError(
                "rise_per_turn must exceed the bead height, or the turns close "
                "up into a solid wall and nothing is see-through"
            )
        if self.weld_overlap <= 0:
            raise ValueError("weld_overlap must be > 0 or the turns never weld")
        if self.height <= self.foot_height + self.rim_height:
            raise ValueError("height must exceed foot_height + rim_height")

    # -- derived ---------------------------------------------------------

    @property
    def amplitude(self) -> float:
        """Vertical half-swing of the wave. Derived from the weld overlap."""
        return (self.rise_per_turn + self.weld_overlap) / 2.0

    @property
    def open_area_fraction(self) -> float:
        """Fraction of the shade wall that is open air."""
        return 1.0 - self.mesh_bead_height / self.rise_per_turn

    @property
    def nodes_per_turn(self) -> int:
        """Welded contact points per revolution."""
        return int(round(2 * self.waves_per_turn))

    @property
    def max_hole_height(self) -> float:
        """Tallest opening between two turns (mm)."""
        return self.rise_per_turn + 2 * self.amplitude

    @property
    def wavelength(self) -> float:
        """Arc length of one wave at mid-height (mm)."""
        return TAU * self.radius_at(0.5) / self.waves_per_turn

    @property
    def free_span(self) -> float:
        """Longest unsupported run of bead between two welds (mm).

        The two turns are in contact wherever their gap has closed to within a
        bead height, i.e. where ``sin(w*theta) >= (dz - bead) / 2a``. Those
        contacts come in pairs straddling each crest; what is left of the wave
        is the bead bridging open air. Measured along the bead, not around the
        circumference, so the wave's own slope counts.
        """
        s = min(1.0, max(0.0, (self.rise_per_turn - self.mesh_bead_height)
                         / (2 * self.amplitude)))
        node_gap = math.pi - 2 * math.asin(s)
        arc = (TAU - node_gap) / TAU * self.wavelength
        return arc / math.cos(math.radians(self.wave_slope_deg))

    @property
    def wave_slope_deg(self) -> float:
        """Steepest angle of the bead from horizontal. Steeper prints better."""
        return math.degrees(math.atan(2 * self.amplitude / (self.wavelength / 2)))

    def radius_at(self, u: float) -> float:
        """Shade radius at height fraction ``u`` in [0, 1]."""
        u = max(0.0, min(1.0, u))
        r = self.bottom_radius + (self.top_radius - self.bottom_radius) * u
        return r + self.belly * math.sin(math.pi * u)

    def bead_area(self, width: float, height: float) -> float:
        """Cross-section of an extruded bead (rectangle plus semicircular ends)."""
        if width < height:
            width = height
        return (width - height) * height + math.pi * (height / 2) ** 2


@dataclass
class Segment:
    """One extruding move, with the bead it should lay down."""

    x: float
    y: float
    z: float
    kind: str = "weave"
    bead_w: float = 0.45
    bead_h: float = 0.45


@dataclass
class Toolpath:
    segments: list[Segment] = field(default_factory=list)
    #: Indices into ``segments`` that begin a new, disconnected path.
    breaks: set[int] = field(default_factory=set)
    #: (index, turn_number) for the spiral, used by check_support.
    turn_index: list[tuple[int, float]] = field(default_factory=list)

    def add(self, x, y, z, kind, bead_w, bead_h, *, new_path=False) -> None:
        if new_path:
            self.breaks.add(len(self.segments))
        self.segments.append(Segment(x, y, z, kind, bead_w, bead_h))

    def __len__(self) -> int:
        return len(self.segments)


def _rings(path, spec, z_start, total_height, walls, kind) -> float:
    """Stack plain concentric-wall layers. Returns the z reached."""
    if total_height <= 0 or walls <= 0:
        return z_start
    layers = max(1, int(round(total_height / spec.layer_height)))
    steps = max(64, int(spec.waves_per_turn * 4))
    z = z_start
    for layer in range(layers):
        z = z_start + (layer + 1) * spec.layer_height
        r_outer = spec.radius_at(z / spec.height)
        for wall in range(walls):
            # Walk outwards-in; the short radial step between walls is extruded
            # too, so the whole foot stays one uninterrupted path.
            r = r_outer - wall * spec.wall_width
            first = layer == 0 and wall == 0
            for s in range(steps + 1):
                th = TAU * s / steps
                path.add(r * math.cos(th), r * math.sin(th), z, kind,
                         spec.wall_width, spec.layer_height,
                         new_path=(first and s == 0))
    return z


def build(spec: LampSpec) -> Toolpath:
    """Generate the whole toolpath: foot, fade-in, weave, fade-out, rim."""
    path = Toolpath()
    foot_top = _rings(path, spec, 0.0, spec.foot_height, spec.foot_walls, "foot")

    ramp = spec.ramp_turns
    a_full = spec.amplitude
    lh = spec.layer_height
    ov = spec.weld_overlap

    def amp(turn: float, fade_start: int | None) -> float:
        """Wave amplitude. Ramps linearly in at the foot and out at the rim."""
        if turn < ramp:
            return a_full * turn / ramp
        if fade_start is not None and turn > fade_start:
            return a_full * max(0.0, 1.0 - (turn - fade_start) / ramp)
        return a_full

    def step(k: int, fade_start: int | None) -> float:
        """How far the centreline climbs between turn ``k`` and turn ``k+1``.

        Not a chosen ramp curve -- solved for. At the same angle, the gap
        between the two turns is ``step - (a_k + a_k+1) * sin(w * theta)``, so
        the deepest point of the weld node is ``step - (a_k + a_k+1)``. Pinning
        that to exactly ``-weld_overlap`` and solving for the step keeps every
        node the same depth from the first turn to the last, whatever the
        amplitude happens to be doing. Ramp curves picked by hand cannot: they
        leave the transition turns either floating apart or ploughing in.

        The floor at one layer height is what makes the bottom of the shade
        stack up as an ordinary solid wall while the wave is still too small
        to weld anything.
        """
        return max(lh, amp(k, fade_start) + amp(k + 1, fade_start) - ov)

    # The fade-out has a fixed shape, so its height is known up front -- which
    # is what lets us start it at the right turn to land on the target height.
    fade_climb = sum(
        max(lh, a_full * max(0.0, 1 - i / ramp) + a_full * max(0.0, 1 - (i + 1) / ramp) - ov)
        for i in range(ramp)
    )
    trigger = (spec.height - spec.rim_height) - fade_climb

    # 1. lay out the centreline and amplitude of every whole turn
    centres: list[float] = []
    amps: list[float] = []
    zc = foot_top + lh
    k = 0
    fade_start: int | None = None
    while True:
        if fade_start is None and zc >= trigger:
            fade_start = k
        centres.append(zc)
        amps.append(amp(k, fade_start))
        if fade_start is not None and k >= fade_start + ramp:
            break
        zc += step(k, fade_start)
        k += 1

    # 2. walk the spiral, interpolating between whole turns
    spt = int(round(spec.waves_per_turn * spec.segments_per_wave))
    for k in range(len(centres) - 1):
        dc = centres[k + 1] - centres[k]
        da = amps[k + 1] - amps[k]
        last = k == len(centres) - 2
        for i in range(spt + (1 if last else 0)):
            f = i / spt
            turn = k + f
            c = centres[k] + f * dc
            a = amps[k] + f * da
            z = c + a * math.sin(spec.waves_per_turn * TAU * turn)
            r = spec.radius_at(c / spec.height)
            kind = "weave" if ramp <= k and (fade_start is None or k < fade_start) else "fade"
            # A bead can only be as tall as the space it is laid into: while
            # the turns are still stacking solid, that is the local step.
            bead_h = min(spec.mesh_bead_height, max(lh, dc))
            path.add(r * math.cos(TAU * turn), r * math.sin(TAU * turn), z, kind,
                     spec.mesh_bead_width, bead_h, new_path=(k == 0 and i == 0))
            path.turn_index.append((len(path) - 1, turn))

    _rings(path, spec, centres[-1], spec.rim_height, spec.rim_walls, "rim")
    return path


# --------------------------------------------------------------------------
# printability
# --------------------------------------------------------------------------

@dataclass
class SupportReport:
    """What the generated path actually does, as opposed to what it should do."""

    max_dip: float          # deepest travel below the previous turn (mm)
    max_dip_z: float        # where that happens
    max_gap: float          # widest unwelded vertical gap (mm)
    max_gap_z: float
    max_free_span: float    # longest unsupported arc (mm)
    descends: float         # largest backwards step in z along the path (mm)
    ok: bool
    problems: list[str] = field(default_factory=list)


def check_support(spec: LampSpec, path: Toolpath, *,
                  dip_limit: float | None = None,
                  span_limit: float = 12.0) -> SupportReport:
    """Verify every turn is held up by the one below it.

    Compares each spiral sample against the point one full revolution earlier.
    ``dip`` is how far the nozzle goes below that bead: a little is the weld, a
    lot is the nozzle driving under its own extrusion. ``gap`` is the vertical
    opening; if the *smallest* gap in a revolution never reaches zero, that turn
    is floating and never welded to anything.
    """
    if dip_limit is None:
        dip_limit = spec.mesh_bead_height * 1.2

    idx = path.turn_index
    if not idx:
        return SupportReport(0, 0, 0, 0, 0, 0, False, ["no spiral generated"])
    steps_per_turn = int(round(spec.waves_per_turn * spec.segments_per_wave))

    max_dip = max_dip_z = 0.0
    max_gap = max_gap_z = 0.0
    unwelded: list[float] = []
    per_turn_min: dict[int, float] = {}
    per_turn_count: dict[int, int] = {}
    span = 0.0
    max_span = 0.0
    descends = 0.0

    for j in range(len(idx)):
        i, turn = idx[j]
        s = path.segments[i]
        if j >= 1:
            prev = path.segments[idx[j - 1][0]]
            descends = max(descends, prev.z - s.z - 0.0)
        if j < steps_per_turn:
            continue
        below = path.segments[idx[j - steps_per_turn][0]]
        gap = s.z - below.z
        if -gap > max_dip:
            max_dip, max_dip_z = -gap, s.z
        if gap > max_gap:
            max_gap, max_gap_z = gap, s.z
        # Two beads are welded once the gap closes to within a bead height:
        # the one being laid is bead_h tall and squashes onto the one below.
        touching = gap <= min(s.bead_h, below.bead_h) + 1e-9
        t = int(turn)
        per_turn_min[t] = min(per_turn_min.get(t, 1e9), gap - min(s.bead_h, below.bead_h))
        per_turn_count[t] = per_turn_count.get(t, 0) + 1
        # Arc length accumulated while the bead is bridging open air.
        before = path.segments[idx[j - 1][0]]
        step = math.dist((before.x, before.y, before.z), (s.x, s.y, s.z))
        if touching:
            span = 0.0
        else:
            span += step
            max_span = max(max_span, span)

    for t, g in sorted(per_turn_min.items()):
        # The spiral stops mid-turn, so the final bucket holds a handful of
        # samples and says nothing about whether that revolution is welded.
        if per_turn_count[t] >= steps_per_turn * 0.9 and g > 1e-9:
            unwelded.append(t)

    problems: list[str] = []
    if max_dip > dip_limit:
        problems.append(
            f"nozzle travels {max_dip:.2f} mm below the previous turn at "
            f"z={max_dip_z:.1f} mm (limit {dip_limit:.2f}); lower weld_overlap"
        )
    if unwelded:
        problems.append(
            f"{len(unwelded)} revolution(s) never touch the turn below "
            f"(first at turn {unwelded[0]}); raise weld_overlap"
        )
    if max_span > span_limit:
        problems.append(
            f"unsupported span of {max_span:.1f} mm exceeds {span_limit:.1f} mm; "
            "raise waves_per_turn or lower rise_per_turn"
        )
    return SupportReport(max_dip, max_dip_z, max_gap, max_gap_z, max_span,
                         descends, not problems, problems)


def stats(spec: LampSpec, path: Toolpath) -> dict:
    """Numbers worth checking before committing hours of printing."""
    length = 0.0
    weave_length = 0.0
    volume = 0.0
    z_max = 0.0
    prev: Segment | None = None
    for i, s in enumerate(path.segments):
        z_max = max(z_max, s.z)
        if prev is not None and i not in path.breaks:
            d = math.dist((prev.x, prev.y, prev.z), (s.x, s.y, s.z))
            length += d
            volume += d * spec.bead_area(s.bead_w, s.bead_h)
            if s.kind == "weave":
                weave_length += d
        prev = s
    fil_area = math.pi * (spec.filament_diameter / 2) ** 2
    return {
        "points": len(path),
        "actual_height_mm": z_max,
        "path_length_m": length / 1000.0,
        "weave_length_m": weave_length / 1000.0,
        "open_area_fraction": spec.open_area_fraction,
        "amplitude_mm": spec.amplitude,
        "weld_overlap_mm": spec.weld_overlap,
        "nodes_per_turn": spec.nodes_per_turn,
        "max_hole_height_mm": spec.max_hole_height,
        "wavelength_mm": spec.wavelength,
        "free_span_mm": spec.free_span,
        "wave_slope_deg": spec.wave_slope_deg,
        "filament_m": volume / fil_area / 1000.0,
        "filament_g": volume / 1000.0 * 1.24,
    }


def with_open_area(spec: LampSpec, fraction: float, *,
                   span_limit: float = 12.0) -> LampSpec:
    """Retune a spec to a target open-area fraction.

    Opening the shade up means climbing further per turn, which stretches the
    unsupported arc between welds. Past roughly 12 mm that arc stops holding
    its shape in free air and the bead droops, so the waves are packed in
    tighter to keep it short. The weld depth is untouched: it is what stops the
    nozzle ploughing under its own bead, and it is not a style choice.
    """
    if not 0.0 < fraction < 0.95:
        raise ValueError("open area fraction must be in (0, 0.95)")
    out = replace(spec, rise_per_turn=spec.mesh_bead_height / (1.0 - fraction))
    # Packing the waves tighter shortens the span roughly in proportion, but
    # only roughly, so close the loop on the measured path rather than trusting
    # the estimate.
    for _ in range(12):
        measured = check_support(spec := out, build(out)).max_free_span
        if measured <= span_limit:
            break
        needed = out.waves_per_turn * measured / span_limit
        bumped = math.ceil(needed - 0.5) + 0.5
        if bumped <= out.waves_per_turn:
            bumped = out.waves_per_turn + 1.0
        out = replace(out, waves_per_turn=bumped)
    return out
