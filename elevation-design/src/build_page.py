"""Generate elevation-design/index.html from the plan-derived model."""

import os
import html

import model as M
from elevations import VIEWS, fi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "index.html")

KIND = {"door": "Door", "win": "Window", "vent": "Toilet window (frosted)", "slider": "Sliding glass door"}


def rows(view):
    v = VIEWS[view]
    out = []
    for floor, level, data in (("Ground", M.LEVELS["plinth"], M.GF), ("First", M.LEVELS["ff"], M.FF)):
        for o in data[view]:
            u0, u1 = sorted((v["off"] + v["sign"] * o["a"], v["off"] + v["sign"] * o["b"]))
            z0, z1 = M.opening_z(o["kind"], level)
            out.append((u0, floor, KIND[o["kind"]], o["label"], u0, u1, z0 - level, z1 - level))
    out.sort(key=lambda t: (t[1] != "Ground", t[0]))
    return out


def table(view):
    r = []
    for _, floor, kind, label, u0, u1, s0, s1 in rows(view):
        r.append(
            f"<tr><td>{floor}</td><td>{html.escape(kind)}</td><td>{html.escape(label)}</td>"
            f"<td>{fi(u0)} to {fi(u1)}</td><td>{fi(u1 - u0)}</td><td>{fi(s0)} to {fi(s1)}</td></tr>"
        )
    return "\n".join(r)


def section(view, blurb):
    v = VIEWS[view]
    return f"""
    <section id="{view}">
      <h2>{v['title'].title()}</h2>
      <p class="sub">{blurb}</p>
      <figure><img src="v2/{view}-elevation.png" alt="{v['title']}" /></figure>
      <details>
        <summary>Openings on this face, measured from the plan</summary>
        <table>
          <thead><tr><th>Floor</th><th>Type</th><th>Room / use</th><th>Position from left edge</th><th>Width</th><th>Sill to head (above floor)</th></tr></thead>
          <tbody>{table(view)}</tbody>
        </table>
      </details>
      <details>
        <summary>Alignment check: this elevation projected from both floor plans</summary>
        <figure><img src="v2/{view}-plan-check.png" alt="{v['title']} aligned with plans" loading="lazy" /></figure>
      </details>
    </section>"""


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Valamil Residence - Minimalist Elevations (plan-aligned)</title>
<style>
  :root { --ink:#141414; --muted:#5d5d5a; --paper:#f6f5f2; --line:rgba(0,0,0,.1); --blue:#1f6feb; --orange:#e8590c; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family: Inter, "Helvetica Neue", Arial, sans-serif; color:var(--ink); background:var(--paper); line-height:1.55; }
  .wrap { max-width:1180px; margin:0 auto; padding:2.5rem 1.25rem 4rem; }
  header { margin-bottom:2rem; padding-bottom:1.5rem; border-bottom:1px solid var(--line); }
  h1 { font-size:clamp(2rem,4.5vw,3rem); letter-spacing:-.02em; line-height:1.05; }
  .lede { color:var(--muted); max-width:46rem; margin-top:.75rem; font-size:1.05rem; }
  nav { display:flex; flex-wrap:wrap; gap:.5rem; margin-top:1.1rem; }
  nav a { color:var(--ink); text-decoration:none; font-size:.82rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; padding:.4rem .7rem; border:1px solid var(--line); background:#fff; }
  nav a:hover { background:var(--ink); color:#fff; }
  section { margin-bottom:3rem; }
  h2 { font-size:1.45rem; letter-spacing:-.01em; margin-bottom:.3rem; }
  .sub { color:var(--muted); font-size:.95rem; margin-bottom:1rem; max-width:50rem; }
  figure { background:#fff; border:1px solid var(--line); overflow:hidden; }
  figure img { display:block; width:100%; height:auto; }
  figcaption { padding:.7rem 1rem; font-size:.85rem; color:var(--muted); border-top:1px solid var(--line); }
  .grid-2 { display:grid; gap:1rem; grid-template-columns:1fr; }
  @media (min-width:820px) { .grid-2 { grid-template-columns:1fr 1fr; } }
  details { margin-top:.9rem; background:#fff; border:1px solid var(--line); }
  summary { cursor:pointer; padding:.7rem 1rem; font-size:.88rem; font-weight:600; }
  details figure, details table { margin:0; border:0; border-top:1px solid var(--line); }
  table { width:100%; border-collapse:collapse; font-size:.82rem; }
  th, td { text-align:left; padding:.5rem .7rem; border-bottom:1px solid var(--line); vertical-align:top; }
  th { background:#faf9f7; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }
  .cards { display:grid; gap:1rem; grid-template-columns:1fr; }
  @media (min-width:820px) { .cards { grid-template-columns:repeat(3,1fr); } }
  .card { background:#fff; border:1px solid var(--line); padding:1rem 1.1rem; }
  .card h3 { font-size:.74rem; text-transform:uppercase; letter-spacing:.1em; margin-bottom:.45rem; }
  .card ul { padding-left:1.1rem; font-size:.9rem; color:var(--muted); }
  .card li + li { margin-top:.3rem; }
  .tag { display:inline-block; font-size:.7rem; font-weight:700; padding:.1rem .45rem; color:#fff; margin-right:.3rem; }
  .tag.b { background:var(--blue); } .tag.o { background:var(--orange); }
  footer { font-size:.84rem; color:var(--muted); border-top:1px solid var(--line); padding-top:1.1rem; }
  code { background:#eceae5; padding:.05rem .3rem; font-size:.85em; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Valamil Residence - minimalist elevations</h1>
    <p class="lede">Redrawn from the measured geometry of your two floor plans. Every door, window, balcony and the stair position comes from the PDF drawings, so each elevation lines up with the plan. The external stair is now a covered volume that forms part of the east facade.</p>
    <nav>
      <a href="#views3d">3D views</a><a href="#north">North</a><a href="#east">East</a><a href="#south">South</a><a href="#west">West</a><a href="#read">How the plan was read</a><a href="#assumptions">Assumptions</a>
    </nav>
  </header>

  <section id="views3d">
    <h2>3D views</h2>
    <p class="sub">Generated from the same data as the elevations. North and East are the two road-facing fronts.</p>
    <figure>
      <img src="v2/view3d-ne.png" alt="North-east corner view" />
      <figcaption>North-east corner: 4'-0" north balcony with sliding glass doors, 6'-6" east balcony, covered stair tower at the south end of the east face.</figcaption>
    </figure>
    <div class="grid-2" style="margin-top:1rem">
      <figure><img src="v2/view3d-nw.png" alt="North-west view" loading="lazy" /><figcaption>North-west corner</figcaption></figure>
      <figure><img src="v2/view3d-se.png" alt="South-east view" loading="lazy" /><figcaption>South-east corner</figcaption></figure>
      <figure><img src="v2/view3d-sw.png" alt="South-west view" loading="lazy" /><figcaption>South-west corner (rear)</figcaption></figure>
    </div>
  </section>

  @@SECTIONS@@

  <section id="read">
    <h2>How the plan was read</h2>
    <p class="sub">The sheets are rotated: on the plan, <b>North Road is on the left</b> and <b>East Road is on top</b> (the north arrow points left). Earlier concept images had the sides mirrored.</p>
    <div class="cards">
      <div class="card"><h3>Orientation</h3><ul>
        <li>Plot 45' (north-south) x 42' (east-west), corner plot</li>
        <li>Building 36'-6" (north-south) x 30'-0" (east-west)</li>
        <li>Setbacks: east 9' (car park + stair), west 4', south 3'</li>
        <li>Gates are on the North Road side</li></ul></div>
      <div class="card"><h3>Ground floor (as per plan)</h3><ul>
        <li>North wall: entry door and one Drawing window</li>
        <li>East wall: main entrance, Drawing window, Pooja window, Kitchen window</li>
        <li>South wall: kitchen service door, dining window, master bedroom window</li>
        <li>West wall: toilet window and two master bedroom windows</li></ul></div>
      <div class="card"><h3>First floor</h3><ul>
        <li>Sit-out opens to the <b>4'-0" north balcony</b> through an opening about 10'-0" wide, drawn as sliding glass doors</li>
        <li>Sit-out also opens to the <b>6'-6" east balcony</b> (about 7'-5" opening) plus two windows</li>
        <li>Bedrooms and toilets keep their plan windows on the south and west</li></ul></div>
    </div>
    <p class="sub" style="margin-top:1rem">Each elevation has an alignment sheet: the plan is rotated so the facade faces you, and dashed lines run from every opening on the plan up into the elevation (<span class="tag b">GF</span> blue, <span class="tag o">FF</span> orange).</p>
  </section>

  <section id="assumptions">
    <h2>Assumptions to confirm</h2>
    <p class="sub">The plans give plan positions only, so these items are design choices rather than plan data.</p>
    <div class="cards">
      <div class="card"><h3>Heights</h3><ul>
        <li>Plinth 1'-6", floor-to-floor 10'-6" (12'-0" first floor level)</li>
        <li>Terrace slab at 22'-0", 3'-0" parapet</li>
        <li>Windows 3'-0" sill to 7'-0" head; toilet windows 4'-6" sill</li>
        <li>Stair headroom cover rises to 30'-6"</li></ul></div>
      <div class="card"><h3>Covered stair</h3><ul>
        <li>Footprint taken from the plan: 14'-4" x 6'-6" (including its 8" north wall) at the south end of the east side, flush with the south wall and the balcony edge</li>
        <li>Entry door and first floor landing door are on the stair's north face, onto the car porch and the east balcony</li>
        <li>Light slots and a head ribbon are design additions</li></ul></div>
      <div class="card"><h3>Things the plan raises</h3><ul>
        <li>The kitchen window (east wall) now opens into the covered stair, so it needs a vent or jali there</li>
        <li>The plan shows the sit-out east and north openings as folding doors; both are drawn as sliding glass</li>
        <li>The east balcony label says 6'-6"; the drawn hatch measures about 6'-1". The label was used.</li></ul></div>
    </div>
  </section>

  <footer>
    Concept elevations for discussion, not construction drawings. Regenerate with <code>python3 src/elevations.py</code> and <code>python3 src/build_page.py</code>; 3D views with <code>src/render3d.sh</code>.
  </footer>
</div>
</body>
</html>
"""


def main():
    secs = "".join(
        [
            section("north", "Faces North Road. Ground floor: entry door and Drawing window. First floor: four-panel sliding glass door onto the 4'-0\" balcony behind a frameless glass balustrade, plus the toilet window."),
            section("east", "Faces East Road. The covered stair is the dark volume at the south end; the 6'-6\" balcony shades the car porch. Ground floor: main entrance, Drawing and Pooja windows (the Kitchen window is inside the stair enclosure)."),
            section("south", "Side elevation, 3'-0\" setback. Kitchen service door, dining and master bedroom windows below; toilet and bedroom windows above. The stair volume is flush with this face."),
            section("west", "Rear elevation, 4'-0\" setback. Three windows per floor as drawn on the plans; the north balcony's glass return shows at the left and the stair cap rises behind the parapet."),
        ]
    )
    open(OUT, "w").write(PAGE.replace("@@SECTIONS@@", secs))
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
