# Alidu Otamatone

**Progetto di Dario Amabile** — strumento elettronico a fiato, open source.

L'Otamatone diventato strumento vero: un dito che scivola sul manico sceglie la
nota senza scalini, il fiato in un bocchino dà la dinamica, sei pulsanti cambiano
ottava e suono. Esce in MIDI, su USB e su presa DIN, e comanda qualsiasi
sintetizzatore. Il cervello è un Teensy 4.1.

Progettato per **non avere parti che si consumano**: le note si leggono con un
nastro capacitivo sotto una lastra protettiva, senza contatto.

🌐 **Sito del progetto**: cartella `docs/` (pubblicabile con GitHub Pages).

## Contenuto

| Cartella / file | Che cosa c'è |
|---|---|
| `docs/` | Il sito: presentazione, confronto con l'Otamatone, prova nel browser, download |
| `firmware/AliBreath/AliBreath.ino` | Firmware per Teensy 4.1 (Arduino / Teensyduino) |
| `hardware/nastro/` | Circuito stampato del nastro delle note (60 elettrodi in due metà uguali) |
| `hardware/scheda/` | Circuito stampato della scheda principale |
| `hardware/meccanica/` | Pezzi stampabili in 3D: sorgente OpenSCAD, 7 file STL, immagini |
| `hardware/produci.sh` | Rigenera i circuiti, li verifica (DRC) e prepara Gerber e immagini |
| `docs/costruzione.html` | Guida di costruzione completa |
| `AliBreath.kicad_sch`, `.kicad_sym`, `.kicad_pro` | Schema elettrico KiCad, revisione 4 |
| `genera_kicad.py` | Genera lo schema da codice: cambi un valore e rigeneri |
| `AliBreath_schema.pdf` | Schema in PDF |
| `SCHEMA_ELETTRICO.md` | Componenti, nodi, calcoli, regole di montaggio |
| `licenze/` | Testi completi delle licenze |

## Caricare il firmware

1. Installa Arduino IDE e Teensyduino.
2. Dal Gestore librerie installa **Trill** (Bela).
3. Apri `firmware/AliBreath/AliBreath.ino`.
4. Scheda: **Teensy 4.1** · USB Type: **MIDI**.
5. Carica. All'accensione non toccare il nastro e non soffiare per un secondo:
   lo strumento si tara.

Da riga di comando:

```
arduino-cli compile --fqbn teensy:avr:teensy41:usb=midi firmware/AliBreath
```

## Stato

- ✅ Schema elettrico rev. 4, ERC KiCad senza errori
- ✅ Firmware: compila per Teensy 4.1
- ⏳ Firmware: da provare sullo strumento, soglie da tarare al banco
- ✅ Circuiti stampati del nastro e della scheda principale: DRC KiCad 0 errori, 0 collegamenti mancanti
- ✅ Guida di costruzione
- ⏳ Circuiti da produrre e montare
- ✅ Meccanica stampabile (OpenSCAD → 7 STL)
- ⏳ Stampa, montaggio e primo prototipo

Foto e video nel sito sono immagini concettuali generate al computer: il
prototipo fisico non è ancora stato costruito.

## Licenze

- **Hardware** (schemi, file KiCad): CERN-OHL-S v2 — `licenze/CERN-OHL-S-2.0.txt`
- **Firmware**: GNU GPL v3 — `licenze/GPL-3.0.txt`
- **Testi, immagini, video**: CC BY-SA 4.0 — `licenze/CC-BY-SA-4.0.txt`

La libreria Trill usata dal firmware è di Augmented Instruments Ltd (Bela), con
licenza BSD.

"Otamatone" è un marchio dei rispettivi proprietari; questo progetto è
indipendente e non è affiliato con loro.
