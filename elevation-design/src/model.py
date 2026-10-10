"""Plan-derived model of the Valamil residence (all dimensions in feet).

Coordinate system (matches the plan sheets once rotated to read normally):
  X : along the building from NORTH (0) to SOUTH (36.5)
  Y : across the building from EAST (0) to WEST (30.0)
  Z : height above ground level

Openings were measured from the vector geometry of the two PDF plans.
The plan scale was calibrated from the column grid so that the outer
column faces are exactly 36'-6" x 30'-0" (the stated building size).
"""

import json

BLD_X = 36.5
BLD_Y = 30.0

# Plan sheet calibration: origin (PDF points, readable orientation) and points per foot.
SHEETS = {
    "G": {"file": "VALAMIL_FINAL_G_FLOOR_6a1b.pdf", "ox": 320.8, "oy": 202.2, "s": 307.5 / BLD_X},
    "F": {"file": "VALAMILFINAL_F.FLOOR_3d4d.pdf", "ox": 217.1, "oy": 130.5, "s": 480.2 / BLD_X},
}

# raw plan measurements were taken at a nominal 37.5 x 30.8 ft; this converts them to real feet
RAW = BLD_X / 37.5


def r(a, b):
    return (round(a * RAW, 2), round(b * RAW, 2))


LEVELS = {
    "ground": 0.0,
    "plinth": 1.5,        # ground floor finished level
    "gf_ceiling": 11.5,   # underside of first floor slab
    "ff": 12.0,           # first floor finished level
    "ff_ceiling": 21.5,
    "roof": 22.0,         # terrace slab top
    "parapet": 25.0,
    "stair_roof": 30.5,   # stair headroom cover
}

BAL_N = 4.0   # north balcony depth (plan: 4'-0")
BAL_E = 6.5   # east balcony depth (plan: 6'-6")

# Covered stair: plan footprint X 22.9-36.5, Y -6.1-0.0 ; enclosure adds a 0.7' wall on its north side
STAIR = {"x0": 22.2, "x1": 36.5, "y0": -BAL_E, "y1": 0.0}

# Openings. Intervals are along the wall: Y for north/south walls, X for east/west walls.
# kind: door | win | vent (frosted toilet window) | slider
GF = {
    "north": [
        {"kind": "door", "a": r(3.4, 6.3)[0], "b": r(3.4, 6.3)[1], "label": "Door (north entry)"},
        {"kind": "win", "a": r(10.1, 13.0)[0], "b": r(10.1, 13.0)[1], "label": "Drawing window"},
    ],
    "east": [
        {"kind": "door", "a": r(3.5, 6.4)[0], "b": r(3.5, 6.4)[1], "label": "Main entrance"},
        {"kind": "win", "a": r(6.7, 9.6)[0], "b": r(6.7, 9.6)[1], "label": "Drawing window"},
        {"kind": "win", "a": r(16.9, 19.8)[0], "b": r(16.9, 19.8)[1], "label": "Pooja window"},
        {"kind": "win", "a": r(27.1, 30.0)[0], "b": r(27.1, 30.0)[1], "label": "Kitchen window (opens into covered stair)"},
    ],
    "south": [
        {"kind": "door", "a": r(7.6, 10.6)[0], "b": r(7.6, 10.6)[1], "label": "Kitchen service door"},
        {"kind": "win", "a": r(10.9, 13.7)[0], "b": r(10.9, 13.7)[1], "label": "Dining window"},
        {"kind": "win", "a": r(15.7, 18.6)[0], "b": r(15.7, 18.6)[1], "label": "Master bedroom window"},
    ],
    "west": [
        {"kind": "vent", "a": r(11.2, 14.1)[0], "b": r(11.2, 14.1)[1], "label": "Toilet window"},
        {"kind": "win", "a": r(16.6, 19.5)[0], "b": r(16.6, 19.5)[1], "label": "Master bedroom window"},
        {"kind": "win", "a": r(29.9, 32.8)[0], "b": r(29.9, 32.8)[1], "label": "Master bedroom window"},
    ],
}

FF = {
    "north": [
        {"kind": "slider", "a": r(2.3, 12.5)[0], "b": r(2.3, 12.5)[1], "panels": 4, "label": "Sit-out sliding door to north balcony"},
        {"kind": "vent", "a": r(23.3, 26.2)[0], "b": r(23.3, 26.2)[1], "label": "Toilet window"},
    ],
    "east": [
        {"kind": "slider", "a": r(2.7, 10.3)[0], "b": r(2.7, 10.3)[1], "panels": 3, "label": "Sit-out door to east balcony"},
        {"kind": "win", "a": r(11.3, 14.2)[0], "b": r(11.3, 14.2)[1], "label": "Sit-out window"},
        {"kind": "win", "a": r(16.1, 19.0)[0], "b": r(16.1, 19.0)[1], "label": "Sit-out window"},
    ],
    "south": [
        {"kind": "vent", "a": r(5.0, 7.9)[0], "b": r(5.0, 7.9)[1], "label": "Toilet window"},
        {"kind": "win", "a": r(15.7, 18.6)[0], "b": r(15.7, 18.6)[1], "label": "Bedroom window"},
    ],
    "west": [
        {"kind": "win", "a": r(6.8, 9.7)[0], "b": r(6.8, 9.7)[1], "label": "Bedroom window"},
        {"kind": "win", "a": r(21.7, 24.6)[0], "b": r(21.7, 24.6)[1], "label": "Bedroom window"},
        {"kind": "win", "a": r(31.2, 34.1)[0], "b": r(31.2, 34.1)[1], "label": "Bedroom window"},
    ],
}

SILL = 3.0       # window sill above finished floor
HEAD = 7.0       # window / door head above finished floor
VENT_SILL = 4.5  # toilet windows


def opening_z(kind, floor_level):
    if kind == "door" or kind == "slider":
        return floor_level, floor_level + HEAD
    if kind == "vent":
        return floor_level + VENT_SILL, floor_level + HEAD
    return floor_level + SILL, floor_level + HEAD


# Stair enclosure openings (design decisions, not on plan)
STAIR_DOORS = {
    # north face of the enclosure (X = 22.2), along Y
    "gf": (-5.9, -3.15),
    "ff": (-2.95, -0.2),
}
STAIR_SLOT_X = [25.6, 29.4, 33.2]   # centres of vertical slots on the east face
STAIR_SLOT_W = 1.3
STAIR_SLOT_TIERS = [(4.5, 10.5), (15.0, 21.0)]


def dump():
    return {
        "bld": {"X": BLD_X, "Y": BLD_Y},
        "levels": LEVELS,
        "balcony": {"north": BAL_N, "east": BAL_E},
        "stair": STAIR,
        "gf": GF,
        "ff": FF,
        "stairDoors": STAIR_DOORS,
        "stairSlots": {"x": STAIR_SLOT_X, "w": STAIR_SLOT_W, "tiers": STAIR_SLOT_TIERS},
        "sill": SILL, "head": HEAD, "ventSill": VENT_SILL,
    }


if __name__ == "__main__":
    print(json.dumps(dump(), indent=1))
