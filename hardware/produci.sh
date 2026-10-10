#!/bin/bash
# Rigenera i due circuiti stampati, li verifica e prepara i file di produzione.
#   nastro/  : sensore delle note (se ne ordinano 2 identici)
#   scheda/  : scheda principale con il Teensy 4.1
# Richiede: KiCad 9 o successivo, Java 21, Freerouting 2.1 (FREEROUTING=percorso del .jar)
set -e
cd "$(dirname "$0")"
KC=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
JAVA="${JAVA:-/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin/java}"
FREEROUTING="${FREEROUTING:?indica il percorso di freerouting-2.1.0.jar}"
zitto() { grep -v -E "Fontconfig|wxApp|swig" || true; }

controlla() {   # $1 = file .kicad_pcb ; fallisce se ci sono errori o collegamenti mancanti
  $KC pcb drc --severity-error --refill-zones --exit-code-violations -o "${1%.kicad_pcb}_drc.txt" "$1" 2>&1 | zitto
}

produzione() {  # $1 = cartella, $2 = nome
  local d=$1/produzione
  rm -rf "$d"; mkdir -p "$d"
  $KC pcb export gerbers -o "$d/" -l F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts "$1/$2.kicad_pcb" 2>&1 | zitto
  $KC pcb export drill -o "$d/" --excellon-separate-th "$1/$2.kicad_pcb" 2>&1 | zitto
  (cd "$d" && zip -q "../$2-gerber.zip" *)
  $KC pcb render -o "$1/$2_fronte.png" -w 2000 -h 1200 --quality high "$1/$2.kicad_pcb" 2>&1 | zitto
  $KC pcb render -o "$1/$2_retro.png" --side bottom -w 2000 -h 1200 --quality high "$1/$2.kicad_pcb" 2>&1 | zitto
  $KC pcb render -o "$1/$2_3d.png" -w 1600 -h 1000 --quality high --rotate "-45,0,30" --perspective "$1/$2.kicad_pcb" 2>&1 | zitto
}

echo "== nastro delle note"
(cd nastro && python3 genera_nastro.py)
controlla nastro/nastro.kicad_pcb
produzione nastro nastro

echo "== scheda principale"
(cd scheda && $PY genera_scheda.py 2>&1 | zitto)
"$JAVA" -Djava.awt.headless=true -jar "$FREEROUTING" -de scheda/scheda.dsn -do scheda/scheda.ses -mp 40 --gui.enabled=false >/dev/null 2>&1
(cd scheda && $PY genera_scheda.py --importa 2>&1 | zitto)
controlla scheda/scheda.kicad_pcb
produzione scheda scheda
$KC pcb export pos -o scheda/scheda_posizioni.csv --format csv --units mm scheda/scheda.kicad_pcb 2>&1 | zitto

echo "fatto: nastro/nastro-gerber.zip  scheda/scheda-gerber.zip"
