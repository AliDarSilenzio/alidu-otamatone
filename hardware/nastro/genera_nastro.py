#!/usr/bin/env python3
"""Genera il circuito stampato del nastro capacitivo di Alidu Otamatone.

Un circuito = mezzo nastro: 30 elettrodi a freccia ("chevron") su 250 mm.
Se ne ordinano DUE identici: la meta' A si monta ruotata di 180 gradi, cosi'
le linguette con il connettore stanno alle due estremita' del manico e al
centro gli elettrodi si toccano quasi (1 mm), senza buchi nel nastro.

  lato F (davanti) : 30 elettrodi, coperti dal solder mask (isolati)
  lato B (dietro)  : 30 piste parallele fino alla linguetta
  linguetta        : connettore 2x15 passo 2,54 mm -> Trill Craft

Il pin k del connettore e' l'elettrodo n = k-1, contando dalla linguetta:
il pin 1 e' l'elettrodo piu' vicino al connettore. Collegando il pin k al
canale k-1 della Trill Craft, il canale n e' l'elettrodo n.

Uso:  python3 genera_nastro.py   (poi DRC e Gerber: vedi produci.sh)
"""

import json
import uuid
from pathlib import Path

QUI = Path(__file__).parent
NOME = "nastro"

# --- geometria (mm) -------------------------------------------------------
N = 30              # elettrodi per circuito
L = 250.0           # lunghezza della zona sensibile
P = L / N           # passo, 8,333 mm
D = 0.9 * P         # profondita' della freccia: un dito copre sempre 2-3 elettrodi
G = 0.5             # spazio fra elettrodi
W = 27.0            # larghezza del circuito
H = W - 2.0         # altezza degli elettrodi (1 mm dal bordo)
T = 48.0            # linguetta del connettore
MARGINE = 0.5       # elettrodi dal bordo corto

PISTA = 0.2
PASSO_PISTE = 0.65  # via 0,6 + pista 0,2 + 0,2 di distanza
Y0_PISTE = 2.6      # prima corsia, fuori dai pad del connettore
VIA, FORO_VIA = 0.6, 0.3
PASSO_PIN = 2.54
X0, Y0 = 30.0, 60.0  # posizione sul foglio


def uid():
    return str(uuid.uuid4())


def tri(y):
    return 1.0 - abs(y) / (H / 2)


def confine(k, y):
    """Confine fra l'elettrodo k-1 e l'elettrodo k, all'altezza y."""
    if k == 0:
        return MARGINE
    if k == N:
        return L - MARGINE
    return k * P + D * (tri(y) - 0.5)


def bordi(i, y):
    sx = confine(i, y) + (G / 2 if i > 0 else 0)
    dx = confine(i + 1, y) - (G / 2 if i + 1 < N else 0)
    return sx, dx


def poligono(i):
    pts = []
    for y in (-H / 2, 0.0, H / 2):
        pts.append((bordi(i, y)[1], y))
    for y in (H / 2, 0.0, -H / 2):
        pts.append((bordi(i, y)[0], y))
    return pts


def corsia(n):
    """Corsia (y) e colonna del connettore dell'elettrodo n (0 = vicino alla linguetta)."""
    j = n // 2
    y = Y0_PISTE + j * PASSO_PISTE
    return (y if n % 2 else -y), j


def xcol(c):
    return L + 4.0 + c * PASSO_PIN


def ab(x, y):
    return round(X0 + x, 4), round(Y0 + y, 4)


LAYERS = """\t(layers
\t\t(0 "F.Cu" signal)
\t\t(31 "B.Cu" signal)
\t\t(32 "B.Adhes" user "B.Adhesive")
\t\t(33 "F.Adhes" user "F.Adhesive")
\t\t(34 "B.Paste" user)
\t\t(35 "F.Paste" user)
\t\t(36 "B.SilkS" user "B.Silkscreen")
\t\t(37 "F.SilkS" user "F.Silkscreen")
\t\t(38 "B.Mask" user)
\t\t(39 "F.Mask" user)
\t\t(40 "Dwgs.User" user "User.Drawings")
\t\t(41 "Cmts.User" user "User.Comments")
\t\t(44 "Edge.Cuts" user)
\t\t(45 "Margin" user)
\t\t(46 "B.CrtYd" user "B.Courtyard")
\t\t(47 "F.CrtYd" user "F.Courtyard")
\t\t(48 "B.Fab" user)
\t\t(49 "F.Fab" user)
\t)"""


def prop(nome, valore, x=0, y=0, livello="F.Fab", nascosta=True):
    h = "\n\t\t\t(hide yes)" if nascosta else ""
    return (f'\t\t(property "{nome}" "{valore}"\n\t\t\t(at {x} {y} 0)\n'
            f'\t\t\t(layer "{livello}"){h}\n\t\t\t(uuid "{uid()}")\n'
            f'\t\t\t(effects (font (size 1 1) (thickness 0.15)))\n\t\t)')


def main():
    o = ['(kicad_pcb', '\t(version 20241229)', '\t(generator "alidu_nastro")',
         '\t(generator_version "9.0")',
         '\t(general (thickness 1.6) (legacy_teardrops no))',
         '\t(paper "A3")', LAYERS,
         '\t(setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))',
         '\t(net 0 "")']
    for n in range(N):
        o.append(f'\t(net {n + 1} "CH{n:02d}")')

    # --- elettrodi: pad SMD a forma libera, solo rame (mask chiuso) -----
    for i in range(N):
        n = N - 1 - i
        pts = poligono(i)
        cx = sum(bordi(i, 0.0)) / 2          # centro della freccia, dentro il rame
        gx, gy = ab(cx, 0)
        prim = " ".join(f"(xy {round(x - cx, 4)} {round(y, 4)})" for x, y in pts)
        o.append(f"""\t(footprint "Alidu:Elettrodo"
\t\t(layer "F.Cu")
\t\t(uuid "{uid()}")
\t\t(at {gx} {gy})
{prop("Reference", f"E{n:02d}")}
{prop("Value", "Elettrodo")}
{prop("Footprint", "")}
{prop("Datasheet", "")}
{prop("Description", "")}
\t\t(attr smd exclude_from_pos_files exclude_from_bom)
\t\t(pad "1" smd custom
\t\t\t(at 0 0)
\t\t\t(size 0.5 0.5)
\t\t\t(layers "F.Cu")
\t\t\t(net {n + 1} "CH{n:02d}")
\t\t\t(zone_connect 0)
\t\t\t(options (clearance outline) (anchor circle))
\t\t\t(primitives (gr_poly (pts {prim}) (width 0) (fill yes)))
\t\t\t(uuid "{uid()}")
\t\t)
\t)""")

    # --- connettore 2x15 e fori di fissaggio -----------------------------
    pad = []
    for c in range(15):
        for riga, y in ((1, -1.27), (2, 1.27)):
            num = 2 * c + riga
            forma = "rect" if num == 1 else "circle"
            px = round(xcol(c) - xcol(0), 4)
            pad.append(f"""\t\t(pad "{num}" thru_hole {forma}
\t\t\t(at {px} {y})
\t\t\t(size 1.7 1.7)
\t\t\t(drill 1.0)
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(net {num} "CH{num - 1:02d}")
\t\t\t(uuid "{uid()}")
\t\t)""")
    gx, gy = ab(xcol(0), 0)
    o.append(f"""\t(footprint "Alidu:Connettore_2x15_P2.54"
\t\t(layer "F.Cu")
\t\t(uuid "{uid()}")
\t\t(at {gx} {gy})
{prop("Reference", "J1", 17.78, -3.6, "F.SilkS", False)}
{prop("Value", "2x15 2,54 mm", 17.78, 3.6)}
{prop("Footprint", "")}
{prop("Datasheet", "")}
{prop("Description", "")}
\t\t(attr through_hole)
\t\t(fp_line (start -1.6 -2.8) (end -1.6 2.8) (stroke (width 0.15) (type solid)) (layer "F.SilkS") (uuid "{uid()}"))
{chr(10).join(pad)}
\t)""")
    for k, yy in enumerate((-8.0, 8.0)):
        gx, gy = ab(L + T - 4.0, yy)
        o.append(f"""\t(footprint "Alidu:Foro_M2.5"
\t\t(layer "F.Cu")
\t\t(uuid "{uid()}")
\t\t(at {gx} {gy})
{prop("Reference", f"H{k + 1}")}
{prop("Value", "M2.5")}
{prop("Footprint", "")}
{prop("Datasheet", "")}
{prop("Description", "")}
\t\t(attr exclude_from_pos_files exclude_from_bom)
\t\t(pad "" np_thru_hole circle
\t\t\t(at 0 0)
\t\t\t(size 2.7 2.7)
\t\t\t(drill 2.7)
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(uuid "{uid()}")
\t\t)
\t)""")

    # --- piste: via sotto l'elettrodo, corsia sul retro, salita sul davanti
    def seg(a, b, livello, net):
        (x1, y1), (x2, y2) = ab(*a), ab(*b)
        o.append(f'\t(segment (start {x1} {y1}) (end {x2} {y2}) (width {PISTA})'
                 f' (layer "{livello}") (net {net}) (uuid "{uid()}"))')

    def via(p, net):
        x, y = ab(*p)
        o.append(f'\t(via (at {x} {y}) (size {VIA}) (drill {FORO_VIA})'
                 f' (layers "F.Cu" "B.Cu") (net {net}) (uuid "{uid()}"))')

    for n in range(N):
        i = N - 1 - n
        y, c = corsia(n)
        sx, dx = bordi(i, y)
        xv = (sx + dx) / 2
        net = n + 1
        via((xv, y), net)
        seg((xv, y), (xcol(c), y), "B.Cu", net)
        via((xcol(c), y), net)
        seg((xcol(c), y), (xcol(c), 1.27 if y > 0 else -1.27), "F.Cu", net)

    # --- contorno e scritte ----------------------------------------------
    (x1, y1), (x2, y2) = ab(0, -W / 2), ab(L + T, W / 2)
    o.append(f'\t(gr_rect (start {x1} {y1}) (end {x2} {y2})'
             f' (stroke (width 0.1) (type default)) (fill no) (layer "Edge.Cuts") (uuid "{uid()}"))')

    def testo(t, x, y, livello, ang=0, h=1.0):
        gx, gy = ab(x, y)
        spec = " (justify mirror)" if livello.startswith("B.") else ""
        o.append(f'\t(gr_text "{t}" (at {gx} {gy} {ang}) (layer "{livello}") (uuid "{uid()}")'
                 f' (effects (font (size {h} {h}) (thickness 0.15)){spec}))')

    testo("ALIDU OTAMATONE", L + T - 4.0, 0, "F.SilkS", 90, 1.2)
    testo("NASTRO 1/2 - CC BY-SA / CERN-OHL-S", L + 22, -11.8, "B.SilkS", 0, 0.9)
    testo("pin 1 = elettrodo vicino", L + 20, 11.8, "B.SilkS", 0, 0.9)
    o.append(')')
    (QUI / f"{NOME}.kicad_pcb").write_text("\n".join(o) + "\n")

    # progetto con le regole di fabbricazione (valori standard JLCPCB/PCBWay)
    pro = {"board": {"design_settings": {
        "rules": {"min_clearance": 0.15, "min_track_width": 0.15,
                  "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3,
                  "min_hole_clearance": 0.25, "min_copper_edge_clearance": 0.3,
                  "min_hole_to_hole": 0.25},
        "rule_severities": {"silk_over_copper": "ignore", "silk_overlap": "ignore",
                            "lib_footprint_issues": "ignore",
                            "lib_footprint_mismatch": "ignore"}}},
        "net_settings": {"classes": [{"name": "Default", "clearance": 0.2,
                                      "track_width": PISTA, "via_diameter": VIA,
                                      "via_drill": FORO_VIA}], "meta": {"version": 3}},
        "meta": {"filename": f"{NOME}.kicad_pro", "version": 1}}
    (QUI / f"{NOME}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")

    larg_min = min(bordi(i, y)[1] - bordi(i, y)[0] for i in range(N) for y in (-H / 2, 0, H / 2))
    print(f"circuito {L + T:.0f} x {W:.0f} mm, {N} elettrodi, passo {P:.3f} mm, "
          f"freccia {D:.2f} mm, larghezza minima elettrodo {larg_min:.2f} mm")


if __name__ == "__main__":
    main()
