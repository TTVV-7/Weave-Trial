"""Construction Set 4 (port and bulk-terminal works): one asset per module.

Each module is named after its asset key and defines

    ASSET = dict(key="water_truck", stem="Water_Truck_4000gal", title="Water Truck (4,000 gal)",
                 az=40, el=20, size="1200x900")      # az/el: preview camera, degrees

    def build(m: Model) -> None:
        m.add("part_name", FINISH, solid, ...)       # millimetres, X forward, Y left, Z up

`build_assets.py` finds them; the file ORDER lists the keys in catalogue order.
"""
