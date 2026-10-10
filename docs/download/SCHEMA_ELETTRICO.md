# Alidu Otamatone (AliBreath) — schema elettronico

Revisione 4 del 10/10/2026 ("eterno"). Verificata con KiCad: **ERC 0 violazioni**.

> **Novità della rev. 4.** Il SoftPot è una membrana: regge circa un milione di
> pressioni, poi si consuma. È sostituito da un **nastro capacitivo** — 60 elettrodi
> a pettine su circuito stampato, sotto 2 mm di policarbonato o vetro, letti da due
> **Trill Craft** sul bus I2C. Nessun contatto, nessuna usura. Liberati A1, D9, D10.

> **AliBreath non è un Otamatone.** La guancia da strizzare e il filtro
> formantico sono stati eliminati. Restano due assi espressivi: il **nastro**
> per l'altezza e il **fiato** per la dinamica.

---

## 1. Distinta componenti — 29 pezzi (più il circuito degli elettrodi)

| Ref | Componente | Valore | Note |
|---|---|---|---|
| U1 | Teensy 4.1 | — | 3,3 V, **non tollera i 5 V sugli ingressi** |
| U2 | Sensore pressione | MPXV7002DP | canale fiato |
| U3 | Bela Trill Craft | 30 canali capacitivi | elettrodi 1–30, indirizzo I2C 0x30 |
| U4 | Bela Trill Craft | 30 canali capacitivi | elettrodi 31–60, indirizzo 0x31 (ponticello ADR) |
| — | Circuito elettrodi | 60 elettrodi a pettine, 500 mm | sotto lastra da 2 mm |
| J1 | Presa DIN 5 poli | — | MIDI OUT |
| J2 | Jack 6,35 mono | — | pedale sustain |
| J3 | Jack 6,35 stereo | — | pedale espressione |
| SW1…SW6 | Pulsanti momentanei | — | ottava ∓, suono ∓, shift, negative harmony |
| R1 | Resistore | 4,7 kΩ 1% | partitore fiato, ramo alto |
| R2 | Resistore | 12 kΩ 1% | partitore fiato, ramo basso |
| R3 | Resistore | 4,7 kΩ 1% | monitor rail, ramo alto |
| R4 | Resistore | 12 kΩ 1% | monitor rail, ramo basso |
| R5 | Resistore | 4,7 kΩ | pull-up I2C, SDA |
| R6 | Resistore | 4,7 kΩ | pull-up I2C, SCL |
| R7 | Resistore | 1 kΩ | serie di protezione pedale espressione |
| R8 | Resistore | 100 kΩ | pull-down espressione (jack sfilato → 0) |
| R9 | Resistore | **33 Ω** | MIDI, ramo +3,3 V |
| R10 | Resistore | **10 Ω** | MIDI, ramo dati |
| C1 | Ceramico | 100 nF | disaccoppiamento U2 |
| C2 | Ceramico | 1 µF | disaccoppiamento U2 |
| C3 | Ceramico | 1 nF | su VOUT, da datasheet |
| C4 | Ceramico | 100 nF | anti-alias canale fiato |
| C5 | Elettrolitico | 10 µF | bulk sul rail 5 V |
| C6 | Ceramico | 100 nF | anti-alias monitor rail |

---

## 2. Nodi

| Nodo | Piedini collegati |
|---|---|
| **+5V** | U1.VUSB · U2.2 · R3.1 · C1.1 · C2.1 · C5.1 |
| **+3V3** | U1.3V3 · J3.2 (anello) · R9.1 · U3.1 · U4.1 · R5.1 · R6.1 |
| **GND** | 22 piedini — tutti i ritorni, **a stella** (vedi §6) |
| U2 VOUT | U2.4 · C3.1 · R1.1 |
| A0 (pin 14) | R1.2 · R2.1 · C4.1 · U1.14 |
| A2 (pin 16) | R3.2 · R4.1 · C6.1 · U1.16 |
| A3 (pin 17) | R7.1 · U1.17 |
| SDA (pin 18) | U1.18 · U3.2 · U4.2 · R5.2 |
| SCL (pin 19) | U1.19 · U3.3 · U4.3 · R6.2 |
| Tip espressione | J3.1 · R7.2 · R8.1 |
| D2…D7 | un pulsante ciascuno verso massa |
| D8 | J2.1 (tip sustain) |
| TX1 (pin 1) | R10.1 |

**Pinout verificati sui datasheet.** MPXV7002DP (SOIC-8, case 1351):
**2 = VS, 3 = GND, 4 = VOUT**; i piedini 1, 5, 6, 7, 8 sono connessioni
interne e **non vanno collegati** — nello schema hanno il marcatore ✕.
Teensy 4.1: A0…A3 = **14…17**.

---

## 3. Canale fiato

`U2.VOUT → C3 (1 nF) → R1 (4,7 k) → nodo → R2 (12 k) e C4 (100 nF) a massa → A0`

Il sensore esce 0,5–4,5 V, il partitore scala di 0,719 → all'ADC arrivano
0,36–3,23 V. Il 100 nF taglia sopra i ~470 Hz e fa da serbatoio di carica
per il convertitore, la cui sorgente vede 4,7 k ∥ 12 k = 3,4 kΩ.

---

## 4. Nastro capacitivo (rev. 4)

Due Trill Craft sul bus I2C (SDA 18, SCL 19, 400 kHz), 30 canali ciascuno:
60 elettrodi su 500 mm, passo ~8,3 mm. Gli elettrodi sono **a pettine
intrecciati** con i vicini: un dito appoggiato ne copre sempre 2–3, e il
baricentro delle letture dà una posizione continua, molto più fine del passo.

- **Lastra**: policarbonato o vetro da 2 mm, incollata sul circuito senza aria
  in mezzo (l'aria abbassa molto la sensibilità).
- **Tocco / non tocco**: lo dà direttamente la somma dei valori, non serve più
  la lettura a due fasi della rev. 3.
- **Indirizzi**: 0x30 di fabbrica (verificato nella libreria Trill 1.1.7), il
  secondo a 0x31 chiudendo il ponticello ADR — verificare sulla scheda.
- **Pull-up 4,7 kΩ**: se i moduli li hanno già a bordo restano in parallelo,
  è innocuo; si possono anche omettere.
- **Libreria Trill 1.1.7**: chiamare `requestRawData()` senza argomento; con un
  numero esplicito la libreria chiede zero byte.

## 5. Monitor del rail, comandi, MIDI

**Monitor rail (A2).** L'uscita di U2 è una *frazione* della sua alimentazione:
se i 5 V dell'USB ballano, balla la lettura. R3/R4 formano un partitore
identico a quello del sensore e portano il rail su A2. In firmware dividi
l'uno per l'altro e l'errore si cancella.

**Pulsanti.** Nessun resistore: il Teensy ha i pull-up interni, il pulsante fa
solo da ponte verso massa. Debounce in firmware.

**Pedale sustain (J2).** Jack mono: tip su D8 con pull-up interno, sleeve a
massa. I pedali esistono normalmente aperti e normalmente chiusi: la polarità
si rileva in firmware leggendo lo stato all'accensione.

**Pedale espressione (J3).** Jack stereo cablato **alla Roland**: tip =
cursore, anello = +3,3 V, sleeve = massa. ⚠️ **Yamaha inverte tip e anello** —
verifica il tuo pedale prima di saldare. R8 da 100 kΩ fa leggere zero quando
il jack è sfilato.

**MIDI OUT (J1).** **33 Ω** fra i 3,3 V e il piedino 4, **10 Ω** fra TX1 e il
piedino 5, piedino 2 a massa, piedini 1 e 3 liberi. Non sono i 220 Ω dello
standard a 5 V: a 3,3 V la corrente scenderebbe a ~2 mA invece dei 5 mA
richiesti. Valori dalla specifica MIDI Association CA-033.

**MIDI USB.** Non richiede alcun componente: è la presa del Teensy, che si
presenta al computer come strumento MIDI senza driver.

---

## 6. Regole di montaggio

1. **Massa a stella.** Tutti i ritorni a un solo punto sotto il Teensy, mai in
   cascata.
2. **Disaccoppiamento ai piedini di U2.** A 3 cm non serve a niente.
3. **Partitori vicini al Teensy**, non al sensore: sulla pista lunga deve
   viaggiare il segnale alto (0,5–4,5 V), più immune.
4. **Piano di massa** sotto la parte analogica, unito al digitale in un punto.

---

## 7. Prima di ordinare

- **Pinout esatto del tuo MPXV7002DP**: molti moduli già montati espongono
  solo tre pin (VCC, GND, OUT) invece degli otto del chip nudo.
- **Indirizzo del secondo Trill Craft**: ponticello ADR chiuso → 0x31.
- **Se saturi col fiato**, l'MPXV7007DP (±7 kPa) è il fratello maggiore —
  verifica package e pinout, non darlo per scontato.
- **Cablaggio del tuo pedale espressione**: Roland o Yamaha.

---

## 8. Come rigenerare

```
python3 genera_kicad.py
```

Riscrive `AliBreath.kicad_sch`, la libreria dei simboli e le tabelle.
Cambia un valore nel file e rigenera: dieci secondi.
