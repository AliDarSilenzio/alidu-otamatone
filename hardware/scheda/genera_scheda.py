#!/usr/bin/env python3
"""Genera il circuito stampato della scheda principale di Alidu Otamatone.

Va eseguito con il Python di KiCad (contiene il modulo pcbnew):
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 genera_scheda.py

Legge i collegamenti dalla netlist dello schema (../../AliBreath.net): la
scheda non puo' divergere dallo schema. Le parti montate sul guscio (prese
MIDI e jack, pulsanti, sensore di fiato, Trill Craft) arrivano alla scheda
con connettori JST XH a scatto, che non si sfilano con le vibrazioni.

Passi: piazzamento -> esportazione DSN -> Freerouting (fuori da qui) ->
importazione SES -> piani di massa -> salvataggio.  Vedi produci.sh.
"""

import re
import sys
from pathlib import Path

import pcbnew

QUI = Path(__file__).parent.resolve()
NETLIST = QUI.parent.parent / "AliBreath.net"
FP = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
NOME = "scheda"
LARGH, ALT = 110.0, 72.0
OX, OY = 100.0, 50.0           # posizione sul foglio


def mm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))


# ---------------------------------------------------------------------------
#  Netlist dello schema: {(ref, pin): nome_net}
# ---------------------------------------------------------------------------
def leggi_netlist():
    testo = NETLIST.read_text()
    blocco = testo[testo.index("(nets"):]
    nodi = {}
    for net in re.split(r"\n\t\t\(net\n", blocco)[1:]:
        nome = re.search(r'\(name "([^"]*)"\)', net).group(1)
        for ref, pin in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', net):
            nodi[(ref, pin)] = nome
    return nodi


# ---------------------------------------------------------------------------
#  Teensy 4.1: impronta generata (la libreria di KiCad non la contiene).
#  File esterna dall'alto, USB in alto. Solo i 48 piedini dei bordi lunghi.
# ---------------------------------------------------------------------------
SINISTRA = ["GND"] + [str(i) for i in range(13)] + ["3V3"] + [str(i) for i in range(24, 33)]
DESTRA = ["VIN", "GND", "3V3"] + [str(i) for i in range(23, 12, -1)] + ["GND"] + \
         [str(i) for i in range(41, 32, -1)]


def impronta_teensy(board):
    f = pcbnew.FOOTPRINT(board)
    f.SetFPID(pcbnew.LIB_ID("Alidu", "Teensy_4.1"))
    for lato, nomi in ((0.0, SINISTRA), (15.24, DESTRA)):
        for k, nome in enumerate(nomi):
            p = pcbnew.PAD(f)
            p.SetNumber(nome)
            p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            p.SetShape(pcbnew.PAD_SHAPE_RECT if (lato == 0 and k == 0) else pcbnew.PAD_SHAPE_CIRCLE)
            p.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.7), pcbnew.FromMM(1.7)))
            p.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
            p.SetLayerSet(pcbnew.PAD.PTHMask())
            p.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(lato), pcbnew.FromMM(k * 2.54)))
            f.Add(p)
    # sagoma della scheda Teensy (61 x 18 mm) sulla serigrafia
    x0, y0, x1, y1 = -1.38, -2.6, 16.62, 60.2
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        s = pcbnew.PCB_SHAPE(f)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
        s.SetLayer(pcbnew.F_SilkS)
        s.SetWidth(pcbnew.FromMM(0.15))
        f.Add(s)
    return f


# ---------------------------------------------------------------------------
#  Che cosa va sulla scheda e dove.  (ref_pcb, libreria, impronta, x, y, rot,
#  {pad_pcb: (ref_schema, pin_schema)}, etichetta)
# ---------------------------------------------------------------------------
R = ("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal")
C = ("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm")
CP = ("Capacitor_THT", "CP_Radial_D5.0mm_P2.00mm")


def xh(n):
    return ("Connector_JST", f"JST_XH_B{n}B-XH-A_1x0{n}_P2.50mm_Vertical")


def due(ref):
    return {"1": (ref, "1"), "2": (ref, "2")}


PEZZI = [
    # canale fiato
    ("C3", *C, 40, 8, 0, due("C3"), "1n"),
    ("R1", *R, 52, 8, 0, due("R1"), "4k7"),
    ("R2", *R, 52, 15, 0, due("R2"), "12k"),
    ("C4", *C, 68, 15, 0, due("C4"), "100n"),
    ("C1", *C, 78, 8, 0, due("C1"), "100n"),
    ("C2", *C, 78, 15, 0, due("C2"), "1u"),
    ("C5", *CP, 89, 8, 0, due("C5"), "10u"),
    # monitor del rail 5 V
    ("R3", *R, 52, 24, 0, due("R3"), "4k7"),
    ("R4", *R, 52, 31, 0, due("R4"), "12k"),
    ("C6", *C, 68, 31, 0, due("C6"), "100n"),
    # bus I2C dei Trill Craft
    ("R5", *R, 52, 40, 0, due("R5"), "4k7"),
    ("R6", *R, 52, 47, 0, due("R6"), "4k7"),
    # pedale espressione
    ("R7", *R, 52, 56, 0, due("R7"), "1k"),
    ("R8", *R, 68, 56, 0, due("R8"), "100k"),
    # MIDI DIN
    ("R9", *R, 40, 24, 90, due("R9"), "33"),
    ("R10", *R, 40, 40, 90, due("R10"), "10"),
    # connettori verso il guscio (lungo il bordo destro e quello basso)
    ("J1", *xh(3), 97, 16, 90, {"1": ("U2", "2"), "2": ("U2", "3"), "3": ("U2", "4")}, "FIATO"),
    ("J2", *xh(4), 97, 31, 90, {"1": ("U3", "1"), "2": ("U3", "2"), "3": ("U3", "3"), "4": ("U3", "4")}, "TRILL A"),
    ("J3", *xh(4), 97, 45, 90, {"1": ("U4", "1"), "2": ("U4", "2"), "3": ("U4", "3"), "4": ("U4", "4")}, "TRILL B"),
    ("J4", *xh(3), 97, 56, 90, {"1": ("J1", "4"), "2": ("J1", "5"), "3": ("J1", "2")}, "MIDI"),
    ("J5", *xh(2), 97, 66, 90, {"1": ("J2", "1"), "2": ("J2", "2")}, "SUSTAIN"),
    ("J6", *xh(7), 38, 66, 0, {str(k): (f"SW{k}", "1") for k in range(1, 7)} | {"7": ("SW1", "2")}, "PULSANTI"),
    ("J7", *xh(3), 80, 66, 0, {"1": ("J3", "1"), "2": ("J3", "2"), "3": ("J3", "3")}, "ESPRESSIONE"),
]


def main():
    nodi = leggi_netlist()
    board = pcbnew.NewBoard(str(QUI / f"{NOME}.kicad_pcb"))
    nets = {}

    def net(nome):
        if nome not in nets:
            n = pcbnew.NETINFO_ITEM(board, nome)
            board.Add(n)
            nets[nome] = n
        return nets[nome]

    # Teensy: il pad si chiama come il piedino; i nomi dello schema coincidono,
    # tranne VUSB, che sulla Teensy 4.1 esce sul piedino VIN.
    t = impronta_teensy(board)
    t.SetReference("U1")
    t.SetValue("Teensy 4.1")
    t.SetPosition(mm(10, 9))
    t.Reference().SetPosition(mm(17.62, 30))
    board.Add(t)
    for (ref, pin), nome in nodi.items():
        if ref != "U1":
            continue
        pad_nome = "VIN" if pin == "VUSB" else pin
        for p in t.Pads():
            if p.GetNumber() == pad_nome:
                p.SetNet(net(nome))
    # tutti i GND e i 3V3 della Teensy sono gli stessi nodi
    for p in t.Pads():
        if p.GetNumber() in ("GND", "3V3") and p.GetNetname() == "":
            p.SetNet(net("GND" if p.GetNumber() == "GND" else "+3V3"))

    for ref, lib, nome_fp, x, y, rot, mappa, etichetta in PEZZI:
        f = pcbnew.FootprintLoad(f"{FP}/{lib}.pretty", nome_fp)
        if f is None:
            sys.exit(f"impronta mancante: {lib}:{nome_fp}")
        f.SetReference(ref)
        f.SetValue(etichetta)
        f.SetPosition(mm(x, y))
        f.SetOrientationDegrees(rot)
        board.Add(f)
        for p in f.Pads():
            sorgente = mappa.get(p.GetNumber())
            if sorgente and sorgente in nodi:
                p.SetNet(net(nodi[sorgente]))
            elif sorgente:
                sys.exit(f"{ref}.{p.GetNumber()}: {sorgente} non e' nello schema")

    # contorno e quattro fori M3
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(mm(0, 0)); s.SetEnd(mm(LARGH, ALT))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1))
    board.Add(s)
    for k, (x, y) in enumerate(((4.5, 4.5), (LARGH - 4.5, 4.5), (4.5, ALT - 4.5), (LARGH - 4.5, ALT - 4.5))):
        f = pcbnew.FootprintLoad(f"{FP}/MountingHole.pretty", "MountingHole_3.2mm_M3")
        f.SetReference(f"H{k + 1}"); f.SetPosition(mm(x, y))
        f.Reference().SetVisible(False)
        board.Add(f)

    # scritte
    def testo(t, x, y, h=1.2, livello=pcbnew.F_SilkS):
        s = pcbnew.PCB_TEXT(board)
        s.SetText(t); s.SetPosition(mm(x, y)); s.SetLayer(livello)
        s.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(h), pcbnew.FromMM(h)))
        s.SetTextThickness(pcbnew.FromMM(0.15))
        board.Add(s)
    testo("ALIDU OTAMATONE", 80, 41, 1.6)
    testo("rev.4 - CERN-OHL-S", 80, 44.5, 1.0)
    for ref, *_resto, etichetta in PEZZI:
        if ref.startswith("J"):
            f = board.FindFootprintByReference(ref)
            f.Value().SetLayer(pcbnew.F_SilkS)
            f.Value().SetVisible(True)

    # regole: pista 0,3 mm per i segnali, 0,5 per l'alimentazione
    ds = board.GetDesignSettings()
    ds.m_MinClearance = pcbnew.FromMM(0.2)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.2)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(pcbnew.FromMM(0.25))
    nc.SetTrackWidth(pcbnew.FromMM(0.3))
    nc.SetViaDiameter(pcbnew.FromMM(0.8))
    nc.SetViaDrill(pcbnew.FromMM(0.4))

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(QUI / f"{NOME}.kicad_pcb"), board)
    print(f"piazzati {len(PEZZI) + 1} componenti, {len(nets)} collegamenti")
    if not pcbnew.ExportSpecctraDSN(board, str(QUI / f"{NOME}.dsn")):
        sys.exit("esportazione DSN fallita")
    print("DSN esportato")


def importa_e_versa():
    """Dopo Freerouting: importa le piste e aggiunge i piani di massa."""
    board = pcbnew.LoadBoard(str(QUI / f"{NOME}.kicad_pcb"))
    if not pcbnew.ImportSpecctraSES(board, str(QUI / f"{NOME}.ses")):
        sys.exit("importazione SES fallita")
    # via i monconi lasciati dal router: un capo che non tocca altra pista,
    # foro passante o pad sullo stesso strato
    def vivo(t, punto, tracce, pads):
        for u in tracce:
            if u is not t and (u.GetClass() == "PCB_VIA" or u.GetLayer() == t.GetLayer()):
                if u.GetClass() == "PCB_VIA" and u.GetPosition() == punto:
                    return True
                if u.GetClass() == "PCB_TRACK" and punto in (u.GetStart(), u.GetEnd()):
                    return True
        return any(pd.IsOnLayer(t.GetLayer()) and pd.HitTest(punto) for pd in pads)

    # L'elenco si legge una volta sola: dopo board.Remove() la funzione
    # GetTracks() di questa versione di KiCad non e' piu' affidabile.
    tracce = list(board.GetTracks())
    da_togliere = []
    visti = set()
    for t in tracce:                               # piste doppie, anche al contrario
        if t.GetClass() != "PCB_TRACK":
            continue
        a, b = t.GetStart(), t.GetEnd()
        k = (t.GetLayer(), t.GetNetCode(), frozenset([(a.x, a.y), (b.x, b.y)]))
        if k in visti or a == b:
            da_togliere.append(t)
        visti.add(k)
    tracce = [t for t in tracce if t not in da_togliere]

    pads = list(board.GetPads())
    while True:
        morti = [t for t in tracce if t.GetClass() == "PCB_TRACK" and
                 not (vivo(t, t.GetStart(), tracce, pads) and vivo(t, t.GetEnd(), tracce, pads))]
        if not morti:
            break
        da_togliere += morti
        tracce = [t for t in tracce if t not in morti]
    for t in da_togliere:
        board.Remove(t)
    print(f"tolti {len(da_togliere)} pezzi di pista doppi o morti")
    gnd = board.FindNet("GND")
    for livello in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(livello)
        z.SetNet(gnd)
        z.SetLocalClearance(pcbnew.FromMM(0.4))
        z.SetMinThickness(pcbnew.FromMM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetThermalReliefGap(pcbnew.FromMM(0.3))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.35))
        o = z.Outline()
        o.NewOutline()
        for x, y in ((0.5, 0.5), (LARGH - 0.5, 0.5), (LARGH - 0.5, ALT - 0.5), (0.5, ALT - 0.5)):
            o.Append(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(QUI / f"{NOME}.kicad_pcb"), board)
    print(f"piste: {len(tracce)} elementi; piani di massa versati")


if __name__ == "__main__":
    importa_e_versa() if "--importa" in sys.argv else main()
