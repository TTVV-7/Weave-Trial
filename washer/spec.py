"""Every dimension of the nozzle, and where each one came from.

Three kinds of number live here and they are not equally trustworthy:

  measured   the hole, off the caliper and the photograph. +/- 0.5 mm, which is
             why `fit_scale` exists and why the gauge is part of the output.
  chosen     clearances, wall thicknesses, print angles. Ordinary design values.
  derived    anything computed in __post_init__ from the two above.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .geom import Sdf, hole_sdf, round_rect


@dataclass(frozen=True)
class NozzleSpec:
    # ---- the hole, measured -------------------------------------------------
    #: Long axis. Caliper, photo 1.
    hole_length: float = 13.5
    #: Across the narrow neck. Caliper, photo 2.
    hole_neck: float = 5.4
    #: Across the lobes. Photo ratio 0.81 x length, then rounded.
    lobe_width: float = 10.9
    #: How far along the length the lobes run. Photo ratio 0.75 x length.
    lobe_span: float = 10.1
    hole_corner_r: float = 0.8
    #: Sheet thickness at the hole. NOT measured -- set it before you print.
    panel: float = 1.0
    #: Multiplies every hole dimension. Set from the printed fit gauge.
    fit_scale: float = 1.0

    # ---- fit, chosen --------------------------------------------------------
    #: Gap per side between the plug and the hole.
    clearance: float = 0.35

    # ---- head, above the panel ---------------------------------------------
    head_margin: float = 1.6
    head_height: float = 3.6
    head_chamfer: float = 0.5
    head_chamfer_h: float = 0.8

    # ---- shank, below the panel --------------------------------------------
    #: Taper from the plug down to the waist. Steep on purpose: the clip has to
    #: reach past it, so it gets out of the way fast.
    taper_h: float = 0.7
    waist_hx: float = 2.0
    waist_h: float = 0.6
    #: Flare angle from vertical. This is both the print overhang and the wedge
    #: ramp the clip climbs, so it is the one angle two things depend on.
    flare_angle: float = 30.0
    flare_hx: float = 4.5
    #: Cone from the flare down to the barb stem.
    cone_h: float = 1.4

    # ---- barb ---------------------------------------------------------------
    hose_id: float = 4.0
    barb_len: float = 9.0
    barb_ridges: int = 2
    bore: float = 2.2

    # ---- jet ----------------------------------------------------------------
    #: Exit slot, measured in the plane normal to the jet.
    jet_w: float = 1.2
    jet_h: float = 0.55
    #: Tilt from vertical, and which way. az 0 points across the hole's neck.
    #: 45 is what the nozzle that came off the car threw, and it is also the
    #: steepest a channel can be and still print: the roof of a tilted bore is
    #: an overhang of exactly the tilt angle. Anything past this needs support
    #: inside a 2.2 mm hole, which is not a thing, so check_fit refuses it.
    aim_deg: float = 45.0
    aim_az: float = 0.0
    #: Height at which the bore stops being vertical and starts aiming.
    plenum_z: float = 1.0

    # ---- clip ---------------------------------------------------------------
    clip_thick: float = 1.8
    #: Height of the step between the part of the clip that touches the sheet
    #: and the prongs. Has to be deep enough that the prongs clear the waist.
    #: = taper_h + waist_h - 0.2 + margin: the prongs must start below the
    #: waist whatever the sheet thickness, because plug height tracks it.
    clip_rim: float = 1.35
    clip_taper_deg: float = 6.0
    clip_reach: float = 9.0
    clip_back: float = 5.0
    clip_wing: float = 3.0

    # ---- output -------------------------------------------------------------
    facets: int = 96

    # ------------------------------------------------------------------------
    @property
    def L(self) -> float:
        return self.hole_length * self.fit_scale

    @property
    def W(self) -> float:
        return self.hole_neck * self.fit_scale

    def hole(self) -> Sdf:
        """The hole itself."""
        s = self.fit_scale
        return hole_sdf(self.hole_length * s, self.hole_neck * s,
                        self.lobe_width * s, self.lobe_span * s,
                        self.hole_corner_r * s)

    def shank(self, hx: float) -> Sdf:
        """A below-panel section: free in x up to hx, pinned in y by the neck.

        Nothing below the head may exceed the hole in y -- the whole part goes
        in through the hole from above -- so the flare can only flare sideways.
        """
        hy = self.W / 2.0 - self.clearance
        return round_rect(hx, hy, min(0.8, hx, hy))

    @property
    def plug_h(self) -> float:
        """Full-section plug height. Kept just under the panel so the clip can
        reach the underside; a thicker panel rides on the taper instead."""
        return max(0.5, self.panel - 0.2)

    @property
    def z_plug(self) -> float:
        return -self.plug_h

    @property
    def z_waist_top(self) -> float:
        return self.z_plug - self.taper_h

    @property
    def z_waist_bot(self) -> float:
        return self.z_waist_top - self.waist_h

    @property
    def flare_h(self) -> float:
        import math
        return (self.flare_hx - self.waist_hx) / math.tan(math.radians(self.flare_angle))

    @property
    def z_flare_bot(self) -> float:
        return self.z_waist_bot - self.flare_h

    @property
    def z_barb_top(self) -> float:
        return self.z_flare_bot - self.cone_h

    @property
    def z_bottom(self) -> float:
        return self.z_barb_top - self.barb_len

    @property
    def barb_stem_r(self) -> float:
        return (self.hose_id - 0.1) / 2.0

    @property
    def barb_ridge_r(self) -> float:
        return (self.hose_id + 0.7) / 2.0

    def flare_hx_at(self, z: float) -> float:
        """Half-width of the shank at z, over the flare. The clip rides this."""
        import math
        if z >= self.z_waist_bot:
            return self.waist_hx
        if z <= self.z_flare_bot:
            return self.flare_hx
        return self.waist_hx + (self.z_waist_bot - z) * math.tan(
            math.radians(self.flare_angle))


PRESETS: dict[str, NozzleSpec] = {
    # As measured, with the caliper's long-axis reading taken at face value.
    "measured": NozzleSpec(),
    # If the gauge says the hole is bigger than the caliper read -- which is
    # what you expect when outside jaws are used inside a hole.
    "loose": replace(NozzleSpec(), fit_scale=1.05),
    "tight": replace(NozzleSpec(), fit_scale=0.95),
    # Thicker sheet, e.g. a plastic cowl rather than a hood skin.
    "thick-panel": replace(NozzleSpec(), panel=2.0),
    # Nearer vertical, for a cowl nozzle that sprays from below the glass line.
    "steep": replace(NozzleSpec(), aim_deg=20.0),
    # A flatter throw, and a gentler overhang inside the channel.
    "shallow": replace(NozzleSpec(), aim_deg=35.0),
}
