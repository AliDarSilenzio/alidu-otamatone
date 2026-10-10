#!/bin/bash
# Prepara docs/download/: compila il firmware e impacchetta tutto il progetto.
# Da rilanciare dopo ogni modifica, prima di caricare su GitHub.
set -e
cd "$(dirname "$0")"
D=docs/download
mkdir -p "$D"

arduino-cli compile --fqbn teensy:avr:teensy41:usb=midi \
  --output-dir firmware/build firmware/AliBreath >/dev/null
cp firmware/AliBreath/AliBreath.ino firmware/build/AliBreath.ino.hex \
   AliBreath_schema.pdf SCHEMA_ELETTRICO.md "$D/"

rm -f "$D"/*.zip
cp hardware/nastro/nastro-gerber.zip hardware/scheda/scheda-gerber.zip "$D/"
zip -q -r "$D/AliBreath-circuiti-kicad.zip" hardware/produci.sh \
  hardware/nastro/genera_nastro.py hardware/nastro/nastro.kicad_pcb hardware/nastro/nastro.kicad_pro \
  hardware/scheda/genera_scheda.py hardware/scheda/scheda.kicad_pcb hardware/scheda/scheda.kicad_pro \
  hardware/scheda/scheda_posizioni.csv licenze/CERN-OHL-S-2.0.txt
(cd hardware/meccanica && zip -q -r "../../$D/AliBreath-stampa-3d.zip" alidu_otamatone.scad produci_stl.sh stl immagini -x '*.DS_Store')
zip -q "$D/AliBreath-kicad.zip" AliBreath.kicad_pro AliBreath.kicad_sch \
  AliBreath.kicad_sym AliBreath.kicad_prl AliBreath.net sym-lib-table \
  fp-lib-table genera_kicad.py SCHEMA_ELETTRICO.md licenze/CERN-OHL-S-2.0.txt
zip -q -r "$D/AliBreath-progetto-completo.zip" README.md SCHEMA_ELETTRICO.md \
  AliBreath.kicad_pro AliBreath.kicad_sch AliBreath.kicad_sym AliBreath.kicad_prl \
  AliBreath.net sym-lib-table fp-lib-table genera_kicad.py AliBreath_schema.pdf \
  firmware/AliBreath firmware/build/AliBreath.ino.hex licenze docs/img docs/video \
  docs/costruzione.html hardware -x '*.DS_Store' -x '*.kicad_prl' -x '*.dsn' -x '*.ses' -x '*/produzione/*'
ls -la "$D"
