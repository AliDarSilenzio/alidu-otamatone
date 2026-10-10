#!/bin/bash
# Rigenera i file STL e le immagini della meccanica. Richiede OpenSCAD 2025 o successivo.
set -e
cd "$(dirname "$0")"
OS=${OPENSCAD:-openscad}
mkdir -p stl immagini
for p in corpo_anteriore corpo_posteriore collare testa testa_coperchio innesto_bocchino guida_nastro; do
  $OS --backend=manifold -D "pezzo=\"$p\"" -o "stl/$p.stl" alidu_otamatone.scad 2>&1 | grep -E "Status|ERROR|WARNING" | sed "s/^/$p: /"
done
img() { $OS -D "pezzo=\"$1\"" --imgsize=$2 --colorscheme="Tomorrow Night" --camera=$3 $4 -o "immagini/$5.png" alidu_otamatone.scad 2>/dev/null; }
img assieme   900,1500 0,0,250,75,0,215,1500 "--viewall --autocenter" assieme
img corpo     1200,1000 0,0,20,68,0,215,560 ""             corpo_fronte
img corpo     1200,1000 0,0,20,72,0,25,560 ""              corpo_retro
img spaccato  1200,1000 0,0,10,90,0,90,330 "--projection=o" spaccato
img tavola    1400,1000 0,40,0,45,0,20,620 ""              pezzi
echo "fatto"
