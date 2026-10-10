#!/usr/bin/env python3
"""Genera il progetto KiCad di AliBreath.

Revisione 4 - "eterno": niente piu' parti che si consumano.
  - il SoftPot (membrana, ~1 milione di pressioni) e' sostituito da un nastro
    capacitivo: 60 elettrodi su circuito stampato, sotto 2 mm di
    policarbonato, letti da due Trill Craft sul bus I2C (SDA 18, SCL 19);
  - liberati A1, D9, D10; via R5/R6/C7 del nastro, R5/R6 ora sono i
    pull-up I2C da 4,7 k.

Revisione 3 - AliBreath non e' piu' un Otamatone.
  - via il sensore guancia e tutto il suo apparato;
  - via il sensore di pressione del nastro: il tocco si rileva a due fasi
    (estremi entrambi a massa + pull-up interno sul cursore), quindi gli
    estremi del SoftPot vanno su due pin digitali invece che fissi;
  - restano DUE sensori: fiato e nastro;
  - aggiunti sei pulsanti, pedale sustain, pedale espressione e uscita
    MIDI DIN a 5 poli (33 e 10 ohm: valori per 3,3 V, spec MIDI CA-033).

Pinout verificati sui datasheet:
  MPXV7002DP (SOIC-8 case 1351): 2=VS 3=GND 4=VOUT; 1,5,6,7,8 NON collegare.
  Teensy 4.1: A0..A3 = 14..17.

Uso:  python3 genera_kicad.py
"""

import uuid
from pathlib import Path

QUI = Path(__file__).parent
PROG = "AliBreath"
GRIGLIA = 1.27
FP_DIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"


def uid():
    return str(uuid.uuid4())


def sn(v):
    return round(round(v / GRIGLIA) * GRIGLIA, 4)


SIMBOLI = {
    "R": {
        "rif": "R", "desc": "Resistore", "pin_len": 1.27,
        "lbl": (3.8, -1.5, 3.8, 1.5), "num": False,
        "grafica": [("rect", -1.016, -2.54, 1.016, 2.54)],
        "pin": [("~", "1", 0, 3.81, 270, "passive"),
                ("~", "2", 0, -3.81, 90, "passive")],
    },
    "C": {
        "rif": "C", "desc": "Condensatore", "pin_len": 3.048,
        "lbl": (3.8, -1.5, 3.8, 1.5), "num": False,
        "grafica": [("line", -1.524, 0.762, 1.524, 0.762),
                    ("line", -1.524, -0.762, 1.524, -0.762)],
        "pin": [("~", "1", 0, 3.81, 270, "passive"),
                ("~", "2", 0, -3.81, 90, "passive")],
    },
    "MPXV7002DP": {
        "rif": "U", "desc": "Sensore pressione differenziale +/-2 kPa",
        "pin_len": 2.54, "lbl": (0, -13.0, 0, 13.0), "num": True,
        "grafica": [("rect", -6.35, -8.89, 6.35, 8.89)],
        "pin": [("NC", "1", -8.89, 6.35, 0, "no_connect"),
                ("VS", "2", -8.89, 2.54, 0, "power_in"),
                ("GND", "3", -8.89, -2.54, 0, "power_in"),
                ("VOUT", "4", 8.89, 0, 180, "output"),
                ("NC", "5", 8.89, 6.35, 180, "no_connect"),
                ("NC", "6", -8.89, -6.35, 0, "no_connect"),
                ("NC", "7", 8.89, -6.35, 180, "no_connect"),
                ("NC", "8", 8.89, 3.81, 180, "no_connect")],
    },
    "Trill_Craft": {
        "rif": "U", "desc": "Bela Trill Craft - 30 canali capacitivi, I2C",
        "pin_len": 2.54, "lbl": (0, -13.0, 0, 13.0), "num": True,
        "grafica": [("rect", -6.35, -10.16, 6.35, 10.16)],
        "pin": [("3V3", "1", 8.89, 7.62, 180, "power_in"),
                ("SDA", "2", 8.89, 2.54, 180, "bidirectional"),
                ("SCL", "3", 8.89, -2.54, 180, "input"),
                ("GND", "4", 8.89, -7.62, 180, "power_in")],
    },
    "SW_Push": {
        "rif": "SW", "desc": "Pulsante momentaneo verso massa",
        "pin_len": 1.27, "lbl": (0, -6.0, 0, 6.0), "num": False,
        "grafica": [("line", -3.81, 0, -1.27, 0), ("line", 1.27, 0, 3.81, 0),
                    ("line", -1.905, 1.905, 1.905, 1.905),
                    ("line", 0, 1.905, 0, 3.175)],
        "pin": [("1", "1", -5.08, 0, 0, "passive"),
                ("2", "2", 5.08, 0, 180, "passive")],
    },
    "Jack_TS": {
        "rif": "J", "desc": "Presa 6,35 mm mono (pedale a interruttore)",
        "pin_len": 2.54, "lbl": (0, -9.0, 0, 9.0), "num": True,
        "grafica": [("rect", -5.08, -5.08, 5.08, 5.08)],
        "pin": [("T", "1", -7.62, 2.54, 0, "passive"),
                ("S", "2", -7.62, -2.54, 0, "passive")],
    },
    "Jack_TRS": {
        "rif": "J", "desc": "Presa 6,35 mm stereo (pedale espressione)",
        "pin_len": 2.54, "lbl": (0, -11.0, 0, 11.0), "num": True,
        "grafica": [("rect", -5.08, -7.62, 5.08, 7.62)],
        "pin": [("T", "1", 7.62, 5.08, 180, "passive"),
                ("R", "2", 7.62, 0, 180, "passive"),
                ("S", "3", 7.62, -5.08, 180, "passive")],
    },
    "DIN5": {
        "rif": "J", "desc": "Presa DIN 5 poli 180 gradi - MIDI OUT",
        "pin_len": 2.54, "lbl": (0, -16.0, 0, 16.0), "num": True,
        "grafica": [("rect", -6.35, -12.7, 6.35, 12.7)],
        "pin": [("1", "1", -8.89, 10.16, 0, "no_connect"),
                ("4", "4", -8.89, 5.08, 0, "passive"),
                ("5", "5", -8.89, 0, 0, "passive"),
                ("3", "3", -8.89, -5.08, 0, "no_connect"),
                ("2", "2", -8.89, -10.16, 0, "passive")],
    },
    "Teensy_4.1": {
        "rif": "U", "desc": "Modulo Teensy 4.1 (solo i piedini usati)",
        "pin_len": 2.54, "lbl": (0, -30.0, 0, 30.0), "num": True,
        "grafica": [("rect", -12.7, -43.18, 12.7, 25.4)],
        "pin": [("A0", "14", -15.24, 20.32, 0, "input"),
                ("A2", "16", -15.24, 10.16, 0, "input"),
                ("A3", "17", -15.24, 5.08, 0, "input"),
                ("SDA", "18", -15.24, -5.08, 0, "bidirectional"),
                ("SCL", "19", -15.24, -10.16, 0, "output"),
                ("VUSB", "VUSB", 15.24, 20.32, 180, "power_out"),
                ("3V3", "3V3", 15.24, 15.24, 180, "power_out"),
                ("GND", "GND", 15.24, 10.16, 180, "power_out"),
                ("D2", "2", 15.24, 0, 180, "bidirectional"),
                ("D3", "3", 15.24, -5.08, 180, "bidirectional"),
                ("D4", "4", 15.24, -10.16, 180, "bidirectional"),
                ("D5", "5", 15.24, -15.24, 180, "bidirectional"),
                ("D6", "6", 15.24, -20.32, 180, "bidirectional"),
                ("D7", "7", 15.24, -25.4, 180, "bidirectional"),
                ("D8", "8", 15.24, -30.48, 180, "bidirectional"),
                ("TX1", "1", 15.24, -38.1, 180, "output")],
    },
    "+5V": {
        "rif": "#PWR", "desc": "Alimentazione 5 V", "pin_len": 0,
        "lbl": (0, -5.5, 0, 0), "num": True, "potenza": True,
        "grafica": [("line", -1.905, 2.54, 1.905, 2.54),
                    ("line", 0, 0, 0, 2.54)],
        "pin": [("+5V", "1", 0, 0, 90, "power_in")],
    },
    "+3V3": {
        "rif": "#PWR", "desc": "Alimentazione 3,3 V", "pin_len": 0,
        "lbl": (0, -5.5, 0, 0), "num": True, "potenza": True,
        "grafica": [("line", -1.905, 2.54, 1.905, 2.54),
                    ("line", 0, 0, 0, 2.54)],
        "pin": [("+3V3", "1", 0, 0, 90, "power_in")],
    },
    "GND": {
        "rif": "#PWR", "desc": "Massa", "pin_len": 0,
        "lbl": (0, 7.5, 0, 0), "num": True, "potenza": True,
        "grafica": [("line", 0, 0, 0, -2.54), ("line", -2.54, -2.54, 2.54, -2.54),
                    ("line", -1.524, -3.556, 1.524, -3.556),
                    ("line", -0.508, -4.572, 0.508, -4.572)],
        "pin": [("GND", "1", 0, 0, 270, "power_in")],
    },
}

FP_R = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
FP_C = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_CP = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"

COMPONENTI = {}
FILI = []
NC = []
_npwr = [0]


def metti(rif, simb, val, x, y, fp=""):
    COMPONENTI[rif] = [simb, val, sn(x), sn(y), fp]


def pwr(tipo, x, y):
    _npwr[0] += 1
    COMPONENTI[f"#PWR{_npwr[0]:02d}"] = [tipo, tipo, sn(x), sn(y), ""]


def pin(rif, num):
    simb, _v, x, y, _f = COMPONENTI[rif]
    for _nm, n, px, py, _a, _t in SIMBOLI[simb]["pin"]:
        if n == num:
            return (sn(x + px), sn(y - py))
    raise KeyError(f"{rif}.{num}")


def filo(*punti):
    for a, b in zip(punti, punti[1:]):
        a, b = (sn(a[0]), sn(a[1])), (sn(b[0]), sn(b[1]))
        if a != b:
            FILI.append((a, b))


# ==========================================================================
# DISPOSIZIONE
# ==========================================================================

metti("U1", "Teensy_4.1", "Teensy 4.1", 259.08, 152.4)

# --- canale fiato: sensore -> filtro -> partitore -> A0 -------------------
YS = 63.5
metti("U2", "MPXV7002DP", "MPXV7002DP", 76.2, YS)
metti("C3", "C", "1n", 101.6, YS + 13.97, FP_C)
metti("R1", "R", "4k7", 127.0, YS + 13.97, FP_R)
metti("R2", "R", "12k", 127.0, YS + 34.29, FP_R)
metti("C4", "C", "100n", 147.32, YS + 34.29, FP_C)

filo(pin("U2", "2"), (67.31, YS - 12.7));            pwr("+5V", 67.31, YS - 12.7)
filo(pin("U2", "3"), (59.69, YS + 2.54), (59.69, YS + 7.62)); pwr("GND", 59.69, YS + 7.62)
for n in ("1", "5", "6", "7", "8"):
    NC.append(pin("U2", n))
filo(pin("U2", "4"), (101.6, YS), (127.0, YS))
filo((101.6, YS), pin("C3", "1"))
filo(pin("C3", "2"), (101.6, YS + 22.86));           pwr("GND", 101.6, YS + 22.86)
filo((127.0, YS), pin("R1", "1"))
filo(pin("R1", "2"), (127.0, YS + 22.86), pin("R2", "1"))
filo(pin("R2", "2"), (127.0, YS + 43.18));           pwr("GND", 127.0, YS + 43.18)
filo((127.0, YS + 22.86), (147.32, YS + 22.86), pin("C4", "1"))
filo(pin("C4", "2"), (147.32, YS + 43.18));          pwr("GND", 147.32, YS + 43.18)
filo((147.32, 86.36), (215.9, 86.36), (215.9, 132.08), pin("U1", "14"))

# --- monitor del rail 5 V -> A2 -------------------------------------------
metti("R3", "R", "4k7", 180.34, 187.96, FP_R)
metti("R4", "R", "12k", 180.34, 208.28, FP_R)
metti("C6", "C", "100n", 196.85, 208.28, FP_C)
filo(pin("R3", "1"), (180.34, 179.07));              pwr("+5V", 180.34, 179.07)
filo(pin("R3", "2"), (180.34, 198.12), pin("R4", "1"))
filo(pin("R4", "2"), (180.34, 217.17));              pwr("GND", 180.34, 217.17)
filo((180.34, 198.12), (196.85, 198.12), pin("C6", "1"))
filo(pin("C6", "2"), (196.85, 217.17));              pwr("GND", 196.85, 217.17)
filo((196.85, 198.12), (222.25, 198.12), (222.25, 142.24), pin("U1", "16"))

# --- nastro capacitivo: due Trill Craft sul bus I2C ----------------------
# Indirizzi 0x30 e 0x31 (ponticello ADR sul secondo). R5/R6 pull-up 4,7 k.
for rif, yc in (("U3", 231.14), ("U4", 274.32)):
    metti(rif, "Trill_Craft", "Trill Craft", 76.2, yc)
    p3, pg = pin(rif, "1"), pin(rif, "4")
    filo(p3, (91.44, p3[1]), (91.44, p3[1] - 5.08)); pwr("+3V3", 91.44, p3[1] - 5.08)
    filo(pg, (91.44, pg[1]), (91.44, pg[1] + 5.08)); pwr("GND", 91.44, pg[1] + 5.08)
filo(pin("U3", "2"), (132.08, 228.6))
filo(pin("U4", "2"), (132.08, 271.78))
filo((132.08, 271.78), (132.08, 228.6), (132.08, 224.79), (154.94, 224.79),
     (232.41, 224.79), (232.41, 157.48), pin("U1", "18"))
filo(pin("U3", "3"), (137.16, 233.68))
filo(pin("U4", "3"), (137.16, 276.86))
filo((137.16, 233.68), (137.16, 276.86), (137.16, 284.48), (210.82, 284.48),
     (237.49, 284.48), (237.49, 162.56), pin("U1", "19"))
metti("R5", "R", "4k7", 154.94, 213.36, FP_R)
filo(pin("R5", "2"), (154.94, 224.79))
filo(pin("R5", "1"), (154.94, 204.47));              pwr("+3V3", 154.94, 204.47)
metti("R6", "R", "4k7", 210.82, 274.32, FP_R)
filo(pin("R6", "2"), (210.82, 284.48))
filo(pin("R6", "1"), (210.82, 265.43));              pwr("+3V3", 210.82, 265.43)

# --- pedale espressione -> A3 --------------------------------------------
metti("J3", "Jack_TRS", "Espressione", 76.2, 309.88)
metti("R8", "R", "100k", 127.0, 313.69, FP_R)
metti("R7", "R", "1k", 152.4, 293.37, FP_R)
filo(pin("J3", "2"), (96.52, 309.88), (96.52, 299.72));  pwr("+3V3", 96.52, 299.72)
filo(pin("J3", "3"), (109.22, 314.96), (109.22, 320.04)); pwr("GND", 109.22, 320.04)
filo(pin("J3", "1"), (127.0, 304.8), (152.4, 304.8), pin("R7", "2"))
filo((127.0, 304.8), pin("R8", "1"))
filo(pin("R8", "2"), (127.0, 322.58));               pwr("GND", 127.0, 322.58)
filo(pin("R7", "1"), (170.18, 289.56), (170.18, 147.32), pin("U1", "17"))

# --- alimentazioni del Teensy --------------------------------------------
filo(pin("U1", "VUSB"), (330.2, 132.08), (330.2, 121.92)); pwr("+5V", 330.2, 121.92)
filo(pin("U1", "3V3"), (322.58, 137.16), (322.58, 124.46)); pwr("+3V3", 322.58, 124.46)
filo(pin("U1", "GND"), (312.42, 142.24), (312.42, 147.32)); pwr("GND", 312.42, 147.32)

# --- sei pulsanti verso massa (pull-up interni del Teensy) ----------------
# passo 17,78 mm: sotto i 15 l'etichetta di un pulsante finisce addosso
# alla sigla di quello dopo.  Le y non devono coincidere con quelle dei
# piedini del Teensy, altrimenti due tratti orizzontali si sovrappongono.
PULSANTI = [("SW1", "Ottava -", "2", 152.4, None),
            ("SW2", "Ottava +", "3", 170.18, 281.94),
            ("SW3", "Suono -", "4", 187.96, 284.48),
            ("SW4", "Suono +", "5", 205.74, 287.02),
            ("SW5", "Shift", "6", 223.52, 289.56),
            ("SW6", "Neg.harmony", "7", 241.3, 292.1)]
for rif, etichetta, pin_t, ysw, xjog in PULSANTI:
    metti(rif, "SW_Push", etichetta, 304.8, ysw)
    p = pin("U1", pin_t)
    if xjog is None:
        filo(p, pin(rif, "1"))
    else:
        filo(p, (xjog, p[1]), (xjog, ysw), pin(rif, "1"))
    filo(pin(rif, "2"), (325.12, ysw));               pwr("GND", 325.12, ysw)

# --- pedale sustain -> D8 -------------------------------------------------
metti("J2", "Jack_TS", "Sustain", 349.25, 182.88)
filo(pin("U1", "8"), (294.64, 182.88), (294.64, 180.34), pin("J2", "1"))
filo(pin("J2", "2"), (334.01, 185.42), (334.01, 190.5)); pwr("GND", 334.01, 190.5)

# --- uscita MIDI DIN 5 poli (33 e 10 ohm: valori 3,3 V, spec CA-033) ------
metti("J1", "DIN5", "MIDI OUT", 400.05, 269.24)
metti("R9", "R", "33", 360.68, 260.35, FP_R)
metti("R10", "R", "10", 345.44, 265.43, FP_R)
filo(pin("R9", "1"), (360.68, 251.46));              pwr("+3V3", 360.68, 251.46)
filo(pin("R9", "2"), pin("J1", "4"))
filo(pin("U1", "1"), (279.4, 190.5), (279.4, 261.62), pin("R10", "1"))
filo(pin("R10", "2"), pin("J1", "5"))
filo(pin("J1", "2"), (380.99, 279.4), (380.99, 284.48)); pwr("GND", 380.99, 284.48)
NC.append(pin("J1", "1"))
NC.append(pin("J1", "3"))

# --- disaccoppiamento e bulk ---------------------------------------------
for i, (rif, val, fp) in enumerate([("C1", "100n", FP_C), ("C2", "1u", FP_C),
                                    ("C5", "10u", FP_CP)]):
    x = 33.02 + i * 17.78
    metti(rif, "C", val, x, 180.34, fp)
    filo(pin(rif, "1"), (x, 171.45));                pwr("+5V", x, 171.45)
    filo(pin(rif, "2"), (x, 189.23));                pwr("GND", x, 189.23)


# ==========================================================================
# SCRITTURA
# ==========================================================================

def sym_def(nome, s, tab):
    t = "\t" * tab
    o = [f'{t}(symbol "{PROG}:{nome}"', f'{t}\t(pin_names (offset 0.508))']
    if s.get("potenza"):
        o += [f'{t}\t(power)', f'{t}\t(pin_numbers (hide yes))']
    elif not s.get("num", True):
        o.append(f'{t}\t(pin_numbers (hide yes))')
    o += [f'{t}\t(exclude_from_sim no)(in_bom yes)(on_board yes)',
          f'{t}\t(property "Reference" "{s["rif"]}" (at 0 6 0)'
          '(effects (font (size 1.27 1.27))))',
          f'{t}\t(property "Value" "{nome}" (at 0 -6 0)'
          '(effects (font (size 1.27 1.27))))',
          f'{t}\t(property "Footprint" "" (at 0 0 0)'
          '(effects (font (size 1.27 1.27))(hide yes)))',
          f'{t}\t(property "Datasheet" "" (at 0 0 0)'
          '(effects (font (size 1.27 1.27))(hide yes)))',
          f'{t}\t(property "Description" "{s["desc"]}" (at 0 0 0)'
          '(effects (font (size 1.27 1.27))(hide yes)))',
          f'{t}\t(symbol "{nome}_0_1"']
    for g in s["grafica"]:
        if g[0] == "rect":
            o.append(f'{t}\t\t(rectangle (start {g[1]} {g[2]})(end {g[3]} {g[4]})'
                     '(stroke (width 0.254)(type default))(fill (type none)))')
        else:
            o.append(f'{t}\t\t(polyline (pts (xy {g[1]} {g[2]})(xy {g[3]} {g[4]}))'
                     '(stroke (width 0.254)(type default))(fill (type none)))')
    o += [f'{t}\t)', f'{t}\t(symbol "{nome}_1_1"']
    for nm, num, x, y, ang, tipo in s["pin"]:
        o.append(f'{t}\t\t(pin {tipo} line (at {x} {y} {ang})'
                 f'(length {s["pin_len"]})'
                 f'(name "{nm}" (effects (font (size 1.27 1.27))))'
                 f'(number "{num}" (effects (font (size 1.27 1.27)))))')
    o += [f'{t}\t)', f'{t})']
    return "\n".join(o)


def giunzioni():
    c = {}
    for a, b in FILI:
        for p in (a, b):
            c[p] = c.get(p, 0) + 1
    return [p for p, n in c.items() if n >= 3]


def main():
    root = uid()
    out = ['(kicad_sch', '\t(version 20250114)', f'\t(generator "{PROG}")',
           '\t(generator_version "9.0")', f'\t(uuid "{root}")', '\t(paper "A2")',
           '\t(lib_symbols']
    for nome, s in SIMBOLI.items():
        out.append(sym_def(nome, s, 2))
    out.append('\t)')

    for (x1, y1), (x2, y2) in FILI:
        out.append(f'\t(wire (pts (xy {x1} {y1})(xy {x2} {y2}))'
                   f'(stroke (width 0)(type default))(uuid "{uid()}"))')
    for x, y in giunzioni():
        out.append(f'\t(junction (at {x} {y})(diameter 0)(color 0 0 0 0)'
                   f'(uuid "{uid()}"))')
    for x, y in NC:
        out.append(f'\t(no_connect (at {x} {y})(uuid "{uid()}"))')

    for rif, (simb, val, x, y, fp) in sorted(COMPONENTI.items()):
        s = SIMBOLI[simb]
        lx, ly, vx, vy = s["lbl"]
        h = '(hide yes)' if s.get("potenza") else ''
        out.append(f"""\t(symbol
\t\t(lib_id "{PROG}:{simb}")
\t\t(at {x} {y} 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)(in_bom yes)(on_board yes)(dnp no)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "{rif}" (at {sn(x + lx)} {sn(y + ly)} 0)(effects (font (size 1.27 1.27)){h}))
\t\t(property "Value" "{val}" (at {sn(x + vx)} {sn(y + vy)} 0)(effects (font (size 1.27 1.27)){h}))
\t\t(property "Footprint" "{fp}" (at {x} {y} 0)(effects (font (size 1.27 1.27))(hide yes)))
\t\t(property "Datasheet" "" (at {x} {y} 0)(effects (font (size 1.27 1.27))(hide yes)))
\t\t(instances (project "{PROG}" (path "/{root}" (reference "{rif}")(unit 1))))
\t)""")

    out += ['\t(sheet_instances (path "/" (page "1")))', ')']
    (QUI / f"{PROG}.kicad_sch").write_text("\n".join(out) + "\n")

    lib = ['(kicad_symbol_lib', '\t(version 20251024)', f'\t(generator "{PROG}")']
    for nome, s in SIMBOLI.items():
        lib.append(sym_def(nome, s, 1))
    lib.append(')')
    (QUI / f"{PROG}.kicad_sym").write_text("\n".join(lib) + "\n")

    (QUI / "sym-lib-table").write_text(
        '(sym_lib_table\n\t(version 7)\n'
        f'\t(lib (name "{PROG}")(type "KiCad")'
        f'(uri "${{KIPRJMOD}}/{PROG}.kicad_sym")(options "")(descr ""))\n)\n')
    fp = ['(fp_lib_table', '\t(version 7)']
    for n in ("Resistor_THT", "Capacitor_THT"):
        fp.append(f'\t(lib (name "{n}")(type "KiCad")'
                  f'(uri "{FP_DIR}/{n}.pretty")(options "")(descr ""))')
    fp.append(')')
    (QUI / "fp-lib-table").write_text("\n".join(fp) + "\n")

    reali = sorted(r for r in COMPONENTI if not r.startswith("#PWR"))
    print(f"componenti: {len(reali)}  ({' '.join(reali)})")
    print(f"fili: {len(FILI)}  giunzioni: {len(giunzioni())}  non-collegare: {len(NC)}")


if __name__ == "__main__":
    main()
