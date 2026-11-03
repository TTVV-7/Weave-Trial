"""Construction Set 3: one asset per module.

Each module is named after its asset key and defines

    ASSET = dict(key="wheel_loader", stem="Wheel_Loader_3yd", title="Wheel Loader (3 yd class)",
                 az=40, el=20, size="1200x900")      # az/el: preview camera, degrees

    def build(m: Model) -> None:
        m.add("part_name", FINISH, solid, ...)       # millimetres, X forward, Y left, Z up

`build_assets.py` finds them; the file ORDER lists the keys in catalogue order.
"""
