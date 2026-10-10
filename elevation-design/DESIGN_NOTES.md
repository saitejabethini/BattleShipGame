# Valamil Residence - plan-aligned minimalist elevations

Open `index.html` for the full presentation (3D views, four elevations, opening tables, alignment sheets).

## What changed from the previous version

The earlier AI-generated images did not follow the plans: north and east were mirrored, balconies were on the wrong sides, and openings were invented. These elevations are now drawn from the measured geometry of the two PDFs.

## How the plan reads

The plan sheets are rotated. Reading them upright:

- **North Road is on the left**, **East Road is on top** (north arrow points left).
- Plot 45' (N-S) x 42' (E-W). Building 36'-6" (N-S) x 30'-0" (E-W).
- Setbacks: east 9' (car park and external stair), west 4', south 3'.
- First floor: **4'-0" balcony on the north side**, **6'-6" balcony on the east side**, joined at the north-east corner. The stair sits at the south end of the east side, beside the east balcony.

## Openings (feet-inches from the building's left edge as seen in each elevation)

See the tables in `index.html`, generated from `src/model.py`. Summary:

| Face | Ground floor | First floor |
| --- | --- | --- |
| North | entry door, Drawing window | 4-panel sliding glass door to 4'-0" balcony, toilet window |
| East | main entrance, Drawing window, Pooja window, Kitchen window (now inside the covered stair) | sliding door to 6'-6" balcony, two windows |
| South | kitchen service door, dining window, master bedroom window | toilet window, bedroom window |
| West | toilet window, two master bedroom windows | three bedroom windows |

## Design

- Minimalist: white plaster, slim black frames, flat roof with dark coping.
- Frameless glass balustrade (3'-6") on both balconies, wrapping the north-east corner.
- The external stair is enclosed as a charcoal-clad vertical volume, flush with the south wall and the balcony edge, with slim light slots and a head ribbon.

## Assumptions to confirm

- Heights: plinth 1'-6", first floor level 12'-0", terrace 22'-0", parapet 25'-0", stair cap 30'-6".
- Stair doors (ground entry and first-floor landing) are placed on the stair's north face; light slots are design additions.
- Plan shows folding doors from the sit-out; these are drawn as sliding glass.
- The kitchen window on the east wall opens into the enclosed stair and needs a vent or jali.
- The east balcony is labelled 6'-6" but measures about 6'-1" on the drawing; the label was used.

## Regenerating

```bash
cd src
python3 elevations.py      # elevations + plan-alignment sheets -> ../v2
python3 build_page.py      # ../index.html
npm install three@0.160.0 --prefix three && ./render3d.sh ne nw se sw   # 3D views
```

Plan PDFs are kept in `plans/`.
