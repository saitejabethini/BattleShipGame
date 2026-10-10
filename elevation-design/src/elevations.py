"""Draw plan-aligned minimalist elevations for the Valamil residence.

Every opening, balcony and the stair enclosure is placed from model.py, which was
measured from the PDF plans. Run:  python3 elevations.py
"""

import base64
import io
import os
import sys

import pymupdf
from PIL import Image
import cairosvg

import model as M

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "v2")
UPLOADS = os.path.join(HERE, "..", "plans")

S = 26.0  # px per foot
L = M.LEVELS

VIEWS = {
    "north": dict(axis="Y", sign=+1, off=0.0, title="NORTH ELEVATION", sub="Faces North Road (front)"),
    "east": dict(axis="X", sign=-1, off=M.BLD_X, title="EAST ELEVATION", sub="Faces East Road, car porch and covered stair"),
    "south": dict(axis="Y", sign=-1, off=M.BLD_Y, title="SOUTH ELEVATION", sub="Side elevation, 3'-0\" setback"),
    "west": dict(axis="X", sign=+1, off=0.0, title="WEST ELEVATION", sub="Rear elevation, 4'-0\" setback"),
}

C = dict(
    wall="#F2F0EB", wall_shade="#E4E1DA", plinth="#77746E", slab="#E9E7E1", line="#2A2926",
    frame="#1C1C1C", glass_a="#9FB8C4", glass_b="#DCE7EB", door="#2B2A28", coping="#2B2A28",
    stair="#5D5A55", stair_groove="#6C6963", ground="#D9D5CB", glass_rail="#BFD9E3", rail="#3A3A3A",
    paper="#FAFAF8", dim="#6B6A66",
)


def fi(x):
    """feet -> feet-inches string"""
    sign = "-" if x < 0 else ""
    inches = round(abs(x) * 12)
    return f"{sign}{inches // 12}'-{inches % 12}\""


class Canvas:
    def __init__(self, view, umin, umax, zmax, ml=90, mr=170, mt=70, mb=40):
        self.v = VIEWS[view]
        self.view = view
        self.umin, self.umax, self.zmax = umin, umax, zmax
        self.ml, self.mr, self.mt, self.mb = ml, mr, mt, mb
        self.w = ml + (umax - umin) * S + mr
        self.ground_y = mt + zmax * S
        self.h = self.ground_y + mb
        self.el = []
        self.defs = []

    def x(self, u):
        return self.ml + (u - self.umin) * S

    def y(self, z):
        return self.ground_y - z * S

    def u_of(self, coord):
        return self.v["off"] + self.v["sign"] * coord

    def span(self, a, b):
        u0, u1 = sorted((self.u_of(a), self.u_of(b)))
        return u0, u1

    def add(self, s):
        self.el.append(s)

    def rect(self, u0, u1, z0, z1, fill, stroke=None, sw=1.0, opacity=None, extra=""):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        op = f' fill-opacity="{opacity}"' if opacity is not None else ""
        self.add(f'<rect x="{self.x(u0):.2f}" y="{self.y(z1):.2f}" width="{(u1-u0)*S:.2f}" height="{(z1-z0)*S:.2f}" fill="{fill}"{op}{st} {extra}/>')

    def line(self, u0, z0, u1, z1, stroke, sw=1.0, dash=None, opacity=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        op = f' stroke-opacity="{opacity}"' if opacity is not None else ""
        self.add(f'<line x1="{self.x(u0):.2f}" y1="{self.y(z0):.2f}" x2="{self.x(u1):.2f}" y2="{self.y(z1):.2f}" stroke="{stroke}" stroke-width="{sw}"{d}{op}/>')

    def text(self, px, py, s, size=11, fill="#222", anchor="start", weight="400", family="Helvetica, Arial, sans-serif", extra=""):
        self.add(f'<text x="{px:.1f}" y="{py:.1f}" font-family="{family}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {extra}>{s}</text>')


GRADS = f"""
<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C['glass_a']}"/><stop offset="1" stop-color="{C['glass_b']}"/></linearGradient>
<linearGradient id="frost" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#D6DFE2"/><stop offset="1" stop-color="#F0F4F5"/></linearGradient>
<linearGradient id="rail" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#C6DEE7" stop-opacity="0.55"/><stop offset="0.5" stop-color="#E8F3F7" stop-opacity="0.35"/><stop offset="1" stop-color="#C6DEE7" stop-opacity="0.55"/></linearGradient>
<linearGradient id="shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0.30"/><stop offset="1" stop-color="#000" stop-opacity="0.04"/></linearGradient>
<linearGradient id="wallg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F7F5F1"/><stop offset="1" stop-color="#ECE9E2"/></linearGradient>
"""


def glass_fill(kind):
    return "url(#frost)" if kind == "vent" else "url(#glass)"


def draw_window(cv, u0, u1, z0, z1, kind="win", shade=0.0):
    f = 0.14
    cv.rect(u0, u1, z0, z1, C["frame"])
    cv.rect(u0 + f, u1 - f, z0 + f, z1 - f, glass_fill(kind))
    mid = (u0 + u1) / 2
    if kind == "vent":
        n = 5
        for i in range(1, n):
            zz = z0 + f + (z1 - z0 - 2 * f) * i / n
            cv.line(u0 + f, zz, u1 - f, zz, "#9AA7AB", 0.6)
    else:
        cv.rect(mid - 0.05, mid + 0.05, z0 + f, z1 - f, C["frame"])
        cv.add(f'<polygon points="{cv.x(u0+f):.1f},{cv.y(z0+f+0.6):.1f} {cv.x(u0+f+0.7):.1f},{cv.y(z0+f):.1f} {cv.x(u0+f+1.1):.1f},{cv.y(z0+f):.1f} {cv.x(u0+f):.1f},{cv.y(z0+f+1.5):.1f}" fill="#fff" fill-opacity="0.28"/>')
    if shade:
        cv.rect(u0, u1, z0, z1, "#000", opacity=shade)


def draw_door(cv, u0, u1, z0, z1, shade=0.0):
    cv.rect(u0, u1, z0, z1, C["frame"])
    cv.rect(u0 + 0.1, u1 - 0.1, z0, z1 - 0.1, C["door"])
    hx = u1 - 0.45
    cv.rect(hx, hx + 0.07, z0 + 3.0, z0 + 4.2, "#B9B6AE")
    if shade:
        cv.rect(u0, u1, z0, z1, "#000", opacity=shade)


def draw_slider(cv, u0, u1, z0, z1, panels=4, shade=0.0):
    f = 0.14
    cv.rect(u0, u1, z0, z1, C["frame"])
    pw = (u1 - u0 - 2 * f) / panels
    for i in range(panels):
        a = u0 + f + i * pw
        cv.rect(a + 0.03, a + pw - 0.03, z0 + f, z1 - f, "url(#glass)")
        cv.rect(a + pw - 0.12, a + pw + 0.02, z0 + f, z1 - f, C["frame"])
        cv.rect(a, a + 0.1, z0 + f, z1 - f, C["frame"])
        cv.add(f'<polygon points="{cv.x(a+0.2):.1f},{cv.y(z1-f-0.1):.1f} {cv.x(a+0.9):.1f},{cv.y(z1-f-0.1):.1f} {cv.x(a+0.2):.1f},{cv.y(z1-f-3.2):.1f}" fill="#fff" fill-opacity="0.26"/>')
    cv.rect(u0, u1, z0, z0 + f + 0.05, C["frame"])
    if shade:
        cv.rect(u0, u1, z0, z1, "#000", opacity=shade)


def draw_openings(cv, floor, wall, level, shade=0.0, skip=lambda o: False):
    data = (M.GF if floor == "gf" else M.FF)[wall]
    for o in data:
        if skip(o):
            continue
        z0, z1 = M.opening_z(o["kind"], level)
        u0, u1 = cv.span(o["a"], o["b"])
        if o["kind"] == "door":
            draw_door(cv, u0, u1, z0, z1, shade)
        elif o["kind"] == "slider":
            draw_slider(cv, u0, u1, z0, z1, o.get("panels", 3), shade)
        else:
            draw_window(cv, u0, u1, z0, z1, o["kind"], shade)


def wall_mass(cv, u0, u1, ztop=None, fill="url(#wallg)", with_plinth=True, coping=True):
    ztop = ztop or L["parapet"]
    cv.rect(u0, u1, 0, ztop, fill, stroke=C["line"], sw=0.8)
    if with_plinth:
        cv.rect(u0, u1, 0, L["plinth"], C["plinth"], stroke=C["line"], sw=0.8)
    if coping:
        cv.rect(u0 - 0.12, u1 + 0.12, ztop - 0.02, ztop + 0.2, C["coping"])
    cv.line(u0, L["ff"], u1, L["ff"], "#CFCBC2", 0.7)


def stair_mass(cv, u0, u1, with_plinth=True):
    top = L["stair_roof"]
    cv.rect(u0, u1, 0, top, C["stair"], stroke=C["line"], sw=0.8)
    n = int((u1 - u0) / 1.0)
    for i in range(1, n + 1):
        uu = u0 + i * 1.0
        if uu < u1 - 0.05:
            cv.line(uu, 0.05, uu, top - 0.05, C["stair_groove"], 0.6)
    if with_plinth:
        cv.rect(u0, u1, 0, L["plinth"], "#45433F", stroke=C["line"], sw=0.8)
    cv.rect(u0 - 0.12, u1 + 0.12, top - 0.02, top + 0.2, C["coping"])


def slot(cv, uc, z0, z1, w=M.STAIR_SLOT_W):
    cv.rect(uc - w / 2, uc + w / 2, z0, z1, C["frame"])
    cv.rect(uc - w / 2 + 0.1, uc + w / 2 - 0.1, z0 + 0.1, z1 - 0.1, "url(#frost)")


def balcony_front(cv, u0, u1, plane_note=None):
    """Slab edge + frameless glass balustrade seen from the front."""
    cv.rect(u0, u1, L["gf_ceiling"], L["ff"], C["slab"], stroke=C["line"], sw=0.9)
    gh = 3.5
    n = max(1, round((u1 - u0) / 4.5))
    pw = (u1 - u0) / n
    for i in range(n):
        a = u0 + i * pw
        cv.rect(a + 0.04, a + pw - 0.04, L["ff"] + 0.25, L["ff"] + gh, "url(#rail)", stroke="#7FA3B2", sw=0.8)
        for k in (0.2, 0.8):
            cv.add(f'<circle cx="{cv.x(a+pw*k):.1f}" cy="{cv.y(L["ff"]+0.55):.1f}" r="2" fill="#8D8D8D"/>')
    cv.rect(u0, u1, L["ff"], L["ff"] + 0.25, "#6E6E6E")
    cv.rect(u0, u1, L["ff"] + gh, L["ff"] + gh + 0.12, C["rail"])


def shadow_under(cv, u0, u1, depth=3.5):
    cv.rect(u0, u1, L["gf_ceiling"] - depth, L["gf_ceiling"], "url(#shade)")


def ground(cv):
    cv.rect(cv.umin - 1.5, cv.umax + 1.5, -0.8, 0, C["ground"])
    cv.line(cv.umin - 1.5, 0, cv.umax + 1.5, 0, "#111", 2.2)


def levels(cv, ux):
    marks = [
        (0.0, "GROUND LEVEL", "+0'-0\""),
        (L["plinth"], "GF LEVEL (PLINTH)", f"+{fi(L['plinth'])}"),
        (L["ff"], "FIRST FLOOR LEVEL", f"+{fi(L['ff'])}"),
        (L["roof"], "TERRACE LEVEL", f"+{fi(L['roof'])}"),
        (L["parapet"], "PARAPET TOP", f"+{fi(L['parapet'])}"),
    ]
    if cv.view in ("north", "east", "south", "west"):
        marks.append((L["stair_roof"], "STAIR CAP", f"+{fi(L['stair_roof'])}"))
    x0 = cv.x(ux)
    for z, name, val in marks:
        yy = cv.y(z)
        cv.add(f'<line x1="{x0:.1f}" y1="{yy:.1f}" x2="{x0+22:.1f}" y2="{yy:.1f}" stroke="{C["dim"]}" stroke-width="0.8"/>')
        cv.add(f'<polygon points="{x0+22:.1f},{yy:.1f} {x0+30:.1f},{yy-5:.1f} {x0+38:.1f},{yy:.1f} {x0+30:.1f},{yy+5:.1f}" fill="none" stroke="{C["dim"]}" stroke-width="0.8"/>')
        cv.text(x0 + 44, yy + 4, f"{val}", 10, "#333", weight="600")
        cv.text(x0 + 44, yy + 15, name, 8, C["dim"])


def figure(cv, u):
    h = 5.6
    cv.add(f'<circle cx="{cv.x(u):.1f}" cy="{cv.y(h-0.45):.1f}" r="{0.42*S:.1f}" fill="#B5B2AA"/>')
    cv.rect(u - 0.55, u + 0.55, 1.6, h - 1.0, "#B5B2AA")
    cv.rect(u - 0.45, u - 0.05, 0, 1.7, "#B5B2AA")
    cv.rect(u + 0.05, u + 0.45, 0, 1.7, "#B5B2AA")


def title_block(cv, view):
    v = VIEWS[view]
    cv.text(cv.ml, 34, v["title"], 22, "#111", weight="700")
    cv.text(cv.ml, 54, v["sub"] + "   |   dimensions in feet-inches, measured from the left edge of the building", 11, "#666")


def dim_chain(cv, floor, wall, row_y, color, label):
    data = (M.GF if floor == "gf" else M.FF)[wall]
    pts = []
    for o in data:
        u0, u1 = cv.span(o["a"], o["b"])
        pts.append((u0, u1, o))
    pts.sort(key=lambda t: t[0])
    cv.text(cv.x(cv.umin) - 6, row_y + 3, label, 9, color, anchor="end", weight="700")
    for u0, u1, o in pts:
        x0, x1 = cv.x(u0), cv.x(u1)
        cv.add(f'<line x1="{x0:.1f}" y1="{row_y:.1f}" x2="{x1:.1f}" y2="{row_y:.1f}" stroke="{color}" stroke-width="1"/>')
        for xx in (x0, x1):
            cv.add(f'<line x1="{xx:.1f}" y1="{row_y-4:.1f}" x2="{xx:.1f}" y2="{row_y+4:.1f}" stroke="{color}" stroke-width="1"/>')
        cv.text((x0 + x1) / 2, row_y - 4, fi(u1 - u0), 8.5, color, anchor="middle", weight="600")
        cv.text(x0, row_y + 14, fi(u0), 7.5, color, anchor="middle")
        cv.text(x1, row_y + 14, fi(u1), 7.5, color, anchor="middle")


# --------------------------------------------------------------------- views


def build_view(view, sheet=False):
    bx, by = M.BLD_X, M.BLD_Y
    st = M.STAIR
    top = L["stair_roof"] + 0.5
    if view == "north":
        umin, umax = -M.BAL_E, by
    elif view == "east":
        umin, umax = 0.0, bx + M.BAL_N
    elif view == "south":
        umin, umax = 0.0, by + M.BAL_E
    else:
        umin, umax = -M.BAL_N, bx
    cv = Canvas(view, umin - 0.5, umax + 0.5, top, mb=(40 if not sheet else 150))
    title_block(cv, view)
    ground(cv)

    if view == "north":
        su0, su1 = sorted((cv.u_of(st["y0"]), cv.u_of(st["y1"])))
        stair_mass(cv, su0, su1)
        wall_mass(cv, 0, by)
        shadow_under(cv, su0, by)
        cv.rect(su0, by, L["plinth"], L["gf_ceiling"], "#000", opacity=0.07)
        g0, g1 = sorted((cv.u_of(M.STAIR_DOORS["gf"][0]), cv.u_of(M.STAIR_DOORS["gf"][1])))
        draw_door(cv, g0, g1, L["plinth"], L["plinth"] + M.HEAD, 0.12)
        f0, f1 = sorted((cv.u_of(M.STAIR_DOORS["ff"][0]), cv.u_of(M.STAIR_DOORS["ff"][1])))
        draw_door(cv, f0, f1, L["ff"], L["ff"] + M.HEAD)
        draw_openings(cv, "gf", "north", L["plinth"], shade=0.10)
        draw_openings(cv, "ff", "north", L["ff"])
        balcony_front(cv, su0, by)
        figure(cv, 21.0)

    elif view == "east":
        wall_mass(cv, 0, bx)
        cv.rect(14.3, bx, L["plinth"], L["gf_ceiling"], "#000", opacity=0.07)
        shadow_under(cv, cv.u_of(st["x0"]), bx)
        draw_openings(cv, "gf", "east", L["plinth"], shade=0.10)
        draw_openings(cv, "ff", "east", L["ff"])
        su0, su1 = sorted((cv.u_of(st["x0"]), cv.u_of(st["x1"])))
        # stair enclosure: hide anything behind it
        stair_mass(cv, su0, su1)
        for xc in M.STAIR_SLOT_X:
            for z0, z1 in M.STAIR_SLOT_TIERS:
                slot(cv, cv.u_of(xc), z0, z1)
        # light ribbon at stair head
        cv.rect(su0 + 1.5, su1 - 1.5, 26.6, 28.4, C["frame"])
        cv.rect(su0 + 1.62, su1 - 1.62, 26.72, 28.28, "url(#frost)")
        # balcony wraps from stair wall to the north end of the building
        bu0, bu1 = su1, cv.u_of(-M.BAL_N)
        balcony_front(cv, bu0, bu1)
        figure(cv, 23.5)

    elif view == "south":
        wall_mass(cv, 0, by)
        su0, su1 = sorted((cv.u_of(st["y0"]), cv.u_of(st["y1"])))
        stair_mass(cv, su0, su1)
        draw_openings(cv, "gf", "south", L["plinth"])
        draw_openings(cv, "ff", "south", L["ff"])
        uc = cv.u_of(-3.04)
        for z0, z1 in M.STAIR_SLOT_TIERS:
            slot(cv, uc, z0, z1)
        figure(cv, 5.0)

    else:  # west
        su0, su1 = sorted((cv.u_of(st["x0"]), cv.u_of(st["x1"])))
        stair_mass(cv, su0, su1, with_plinth=False)
        wall_mass(cv, 0, bx)
        draw_openings(cv, "gf", "west", L["plinth"])
        draw_openings(cv, "ff", "west", L["ff"])
        bu0, bu1 = -M.BAL_N, 0.0
        balcony_front(cv, bu0, bu1)
        figure(cv, 5.5)

    levels(cv, umax + 0.9)
    return cv


# ------------------------------------------------------------ plan underlay


def plan_image(floor_key, view, z_px_per_ft):
    """Render a plan sheet rotated so the elevation's front wall is at the bottom."""
    sh = M.SHEETS[floor_key]
    doc = pymupdf.open(os.path.join(UPLOADS, sh["file"]))
    page = doc[0]
    Zm = z_px_per_ft / sh["s"]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(Zm, Zm))
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    Xa, Xb, Ya, Yb = -5.0, 38.5, -7.5, 31.5
    box = (
        int((sh["ox"] + Xa * sh["s"]) * Zm), int((sh["oy"] + Ya * sh["s"]) * Zm),
        int((sh["ox"] + Xb * sh["s"]) * Zm), int((sh["oy"] + Yb * sh["s"]) * Zm),
    )
    im = im.crop(box)
    rot = {"west": 0, "north": 90, "east": 180, "south": -90}[view]
    if rot:
        im = im.rotate(rot, expand=True)
    return im, (Xa, Xb, Ya, Yb)


def encode(im, quality=80):
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode()


def sheet_svg(view):
    cv = build_view(view, sheet=True)
    v = VIEWS[view]
    # dimension chains under the ground line
    base = cv.ground_y + 38
    dim_chain(cv, "gf", view, base, "#1f6feb", "GF")
    dim_chain(cv, "ff", view, base + 52, "#e8590c", "FF")
    cur_y = cv.h + 10
    # elevation uses full width; plan blocks placed below
    blocks = []
    front = {"north": 0.0, "east": 0.0, "south": M.BLD_X, "west": M.BLD_Y}[view]
    plan_tops = {}
    for fk, lab, colr in (("F", "FIRST FLOOR PLAN", "#e8590c"), ("G", "GROUND FLOOR PLAN", "#1f6feb")):
        im, (Xa, Xb, Ya, Yb) = plan_image(fk, view, S * 2)
        # horizontal range in u
        if v["axis"] == "Y":
            a, b = Ya, Yb
        else:
            a, b = Xa, Xb
        ua, ub = sorted((v["off"] + v["sign"] * a, v["off"] + v["sign"] * b))
        wpx = (ub - ua) * S
        hpx = im.height * (wpx / im.width)
        x = cv.x(ua)
        y = cur_y + 22
        blocks.append((fk, lab, colr, im, x, y, wpx, hpx))
        # front wall y within block
        if view == "north":
            wy = y + (Xb - front) * S
        elif view == "east":
            wy = y + (Yb - front) * S
        elif view == "south":
            wy = y + (front - Xa) * S
        else:
            wy = y + (front - Ya) * S
        plan_tops[fk] = (y, wy)
        cur_y = y + hpx + 12
    total_h = cur_y + 20

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{cv.w:.0f}" height="{total_h:.0f}" viewBox="0 0 {cv.w:.0f} {total_h:.0f}">',
             f"<defs>{GRADS}</defs>", f'<rect width="100%" height="100%" fill="{C["paper"]}"/>']
    parts += cv.el
    # plans
    for fk, lab, colr, im, x, y, wpx, hpx in blocks:
        parts.append(f'<text x="{cv.ml}" y="{y-6:.0f}" font-family="Helvetica, Arial" font-size="12" font-weight="700" fill="{colr}">{lab} - rotated to match this elevation (building front wall at the bottom edge)</text>')
        parts.append(f'<image x="{x:.1f}" y="{y:.1f}" width="{wpx:.1f}" height="{hpx:.1f}" xlink:href="data:image/jpeg;base64,{encode(im)}" preserveAspectRatio="none"/>')
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{wpx:.1f}" height="{hpx:.1f}" fill="none" stroke="#bbb" stroke-width="0.8"/>')
    # projection lines
    for fk, floor, colr, zlevel in (("G", "gf", "#1f6feb", L["plinth"]), ("F", "ff", "#e8590c", L["ff"])):
        y_plan, wy = plan_tops[fk]
        for o in (M.GF if floor == "gf" else M.FF)[view]:
            z0, z1 = M.opening_z(o["kind"], zlevel)
            u0, u1 = cv.span(o["a"], o["b"])
            for u in (u0, u1):
                xx = cv.x(u)
                parts.append(f'<line x1="{xx:.1f}" y1="{cv.y(z1):.1f}" x2="{xx:.1f}" y2="{wy:.1f}" stroke="{colr}" stroke-width="0.7" stroke-dasharray="4 3" stroke-opacity="0.65"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def plain_svg(view):
    cv = build_view(view)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{cv.w:.0f}" height="{cv.h:.0f}" viewBox="0 0 {cv.w:.0f} {cv.h:.0f}">',
             f"<defs>{GRADS}</defs>", f'<rect width="100%" height="100%" fill="{C["paper"]}"/>']
    parts += cv.el
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    os.makedirs(OUT, exist_ok=True)
    for view in VIEWS:
        svg = plain_svg(view)
        open(os.path.join(OUT, f"{view}-elevation.svg"), "w").write(svg)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(OUT, f"{view}-elevation.png"), scale=1.6)
        sv = sheet_svg(view)
        pass
        cairosvg.svg2png(bytestring=sv.encode(), write_to=os.path.join(OUT, f"{view}-plan-check.png"), scale=1.0)
        print("wrote", view)


if __name__ == "__main__":
    main()
