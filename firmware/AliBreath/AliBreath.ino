// =============================================================================
//  Alidu Otamatone (AliBreath) - firmware revisione 4 ("eterno")
//  Progetto di Dario Amabile - licenza GNU GPL v3 (vedi licenze/GPL-3.0.txt)
//  Teensy 4.1 - USB Type: "MIDI" (oppure "Serial + MIDI" per il monitor)
//
//  Altezza  : nastro CAPACITIVO da 500 mm sotto una lastra protettiva,
//             letto da due Trill Craft (60 elettrodi). Nessuna parte mobile,
//             nessun contatto che si consuma.
//  Dinamica : fiato nel beccuccio -> MPXV7002DP -> CC2 (breath) + CC11.
//  Uscite   : MIDI USB (senza driver) e MIDI DIN 5 poli su TX1, in parallelo.
//  Comandi  : 6 pulsanti, pedale sustain, pedale espressione.
//
//  Librerie : Trill (Bela) - dal Gestore librerie di Arduino, cercare "Trill".
// =============================================================================

#include <Wire.h>
#include <EEPROM.h>
#include <Trill.h>

// ----------------------------------------------------------------------------
//  IMPOSTAZIONI - si cambiano qui
// ----------------------------------------------------------------------------
const uint8_t  CANALE_MIDI       = 1;      // 1..16
const uint8_t  NOTA_BASE         = 48;     // nota all'estremo grave (48 = Do3)
const float    ESTENSIONE        = 24.0f;  // semitoni lungo tutto il nastro
const uint8_t  BEND_SEMITONI     = 12;     // deve coincidere col synth (inviato via RPN)
const uint8_t  CC_FIATO          = 2;      // Breath Controller
const uint8_t  CC_FIATO_COPIA    = 11;     // Expression: molti synth ignorano il CC2
const uint8_t  CC_PEDALE_ESPR    = 4;      // Foot Controller
const uint8_t  CC_NEG_HARMONY    = 85;     // per AliChord: 127 attivo, 0 spento
const bool     SERVE_IL_FIATO    = true;   // false = suona al solo tocco (modo Otamatone)

// soglie del fiato in frazione del fondo scala (0..1)
const float FIATO_ACCESO  = 0.035f;        // sopra: la nota parte
const float FIATO_SPENTO  = 0.020f;        // sotto: la nota si chiude (isteresi)
const float FIATO_CURVA   = 0.6f;          // <1 = piu' sensibile ai soffi leggeri

// nastro
const uint8_t  TRILL_ADDR_1      = 0x30;   // Craft, ponticello ADR aperto
const uint8_t  TRILL_ADDR_2      = 0x31;   // Craft, ponticello ADR chiuso
const int      SOGLIA_TOCCO      = 180;    // somma minima dei valori diff
const uint8_t  N_ELETTRODI       = 60;

// ----------------------------------------------------------------------------
//  PIEDINI (rev. 4)
// ----------------------------------------------------------------------------
const uint8_t PIN_FIATO   = A0;   // 14
const uint8_t PIN_RAIL    = A2;   // 16 - monitor del 5 V per compensare il sensore
const uint8_t PIN_ESPR    = A3;   // 17
const uint8_t PIN_SUSTAIN = 8;
enum { P_OTT_GIU, P_OTT_SU, P_SUONO_GIU, P_SUONO_SU, P_SHIFT, P_NEG, N_PULSANTI };
const uint8_t PIN_PULSANTE[N_PULSANTI] = {2, 3, 4, 5, 6, 7};

// ----------------------------------------------------------------------------
//  MIDI su USB e DIN insieme
// ----------------------------------------------------------------------------
static void dinInvia(uint8_t a, uint8_t b, int c = -1) {
  Serial1.write(a); Serial1.write(b); if (c >= 0) Serial1.write((uint8_t)c);
}
static const uint8_t ch0 = CANALE_MIDI - 1;

static void midiNotaOn(uint8_t n, uint8_t v) { usbMIDI.sendNoteOn(n, v, CANALE_MIDI);  dinInvia(0x90 | ch0, n, v); }
static void midiNotaOff(uint8_t n)           { usbMIDI.sendNoteOff(n, 0, CANALE_MIDI); dinInvia(0x80 | ch0, n, 0); }
static void midiCC(uint8_t cc, uint8_t v)    { usbMIDI.sendControlChange(cc, v, CANALE_MIDI); dinInvia(0xB0 | ch0, cc, v); }
static void midiProgramma(uint8_t p)         { usbMIDI.sendProgramChange(p, CANALE_MIDI); dinInvia(0xC0 | ch0, p); }
static void midiBend(int v) {                // v in -8192..8191
  v = constrain(v, -8192, 8191);
  usbMIDI.sendPitchBend(v, CANALE_MIDI);
  unsigned u = v + 8192;
  dinInvia(0xE0 | ch0, u & 0x7F, (u >> 7) & 0x7F);
}
static void midiBendRange(uint8_t semitoni) { // RPN 0,0 = pitch bend sensitivity
  midiCC(101, 0); midiCC(100, 0); midiCC(6, semitoni); midiCC(38, 0);
  midiCC(101, 127); midiCC(100, 127);         // RPN null: chiude la sequenza
}

// ----------------------------------------------------------------------------
//  STATO PERSISTENTE - scritto in EEPROM solo se cambia, dopo 5 s di quiete
// ----------------------------------------------------------------------------
struct Preset { uint8_t firma, banco, programma; int8_t ottava; uint8_t magnetismo; };
const uint8_t FIRMA = 0xA4;
Preset preset = {FIRMA, 0, 0, 0, 0};
Preset salvato;
uint32_t ultimaModifica = 0;

static void caricaPreset() {
  EEPROM.get(0, salvato);
  if (salvato.firma == FIRMA && salvato.banco < 128 && salvato.programma < 128 &&
      abs(salvato.ottava) <= 3 && salvato.magnetismo <= 100) preset = salvato;
  salvato = preset;
}
static void forseSalva() {
  if (memcmp(&preset, &salvato, sizeof preset) != 0 && millis() - ultimaModifica > 5000) {
    EEPROM.put(0, preset);
    salvato = preset;
  }
}
static void inviaSuono() {
  midiCC(0, preset.banco);
  midiProgramma(preset.programma);
}

// ----------------------------------------------------------------------------
//  FIATO
// ----------------------------------------------------------------------------
float fiatoZero = 0;           // rapporto sensore/rail a riposo
float fiato = 0;              // 0..1, filtrato
uint8_t ultimoCCfiato = 255;

static float leggiRapporto() {
  // Il sensore e' raziometrico: dividere per il rail cancella le oscillazioni
  // dei 5 V dell'USB. Entrambi passano da partitori identici (4k7/12k).
  int s = analogRead(PIN_FIATO), r = analogRead(PIN_RAIL);
  return r > 100 ? (float)s / r : 0.5f;
}
static void calibraFiato() {
  float acc = 0;
  for (int i = 0; i < 256; i++) { acc += leggiRapporto(); delay(2); }
  fiatoZero = acc / 256;
}
static void aggiornaFiato(bool aRiposo) {
  // MPXV7002DP: 0,5..4,5 V su 5 V -> rapporto 0,1..0,9, zero a 0,5.
  // Soffiare = pressione positiva: fondo scala a +0,4 sopra lo zero.
  float r = leggiRapporto();
  float x = constrain((r - fiatoZero) / 0.4f, 0.0f, 1.0f);
  fiato += (x - fiato) * 0.25f;                   // passa-basso leggero
  // Deriva termica: quando nessuno soffia lo zero insegue lentamente.
  if (aRiposo && x < FIATO_SPENTO) fiatoZero += (r - fiatoZero) * 0.0005f;
}
static uint8_t fiatoMidi() {
  return (uint8_t)constrain(lroundf(powf(fiato, FIATO_CURVA) * 127.0f), 0, 127);
}

// ----------------------------------------------------------------------------
//  NASTRO CAPACITIVO
// ----------------------------------------------------------------------------
Trill craft1, craft2;
bool craftOk = false;
int  diffVal[N_ELETTRODI];

static bool avviaCraft(Trill &t, uint8_t addr) {
  if (t.setup(Trill::TRILL_CRAFT, addr) != 0) return false;
  delay(10);
  t.setMode(Trill::DIFF);       // valori gia' sottratti della linea di base
  delay(10);
  t.setPrescaler(3);            // sensibilita' adatta a 2 mm di policarbonato
  delay(10);
  t.setNoiseThreshold(30);
  delay(10);
  t.updateBaseline();           // a vuoto: non toccare il nastro all'accensione
  return true;
}
static void leggiCraft(Trill &t, int *dest) {
  // Senza argomento: Trill 1.1.7 con un numero esplicito chiede 0 byte.
  // 30 canali x 2 = 60 byte, entrano nel buffer Wire del Teensy 4 (136).
  t.requestRawData();
  int i = 0;
  while (t.rawDataAvailable() > 0 && i < 30) dest[i++] = t.rawDataRead();
  while (i < 30) dest[i++] = 0;
}

// Restituisce la posizione 0..1 lungo il nastro, oppure -1 se non toccato.
static float leggiNastro() {
  leggiCraft(craft1, diffVal);
  leggiCraft(craft2, diffVal + 30);
  int imax = 0, somma = 0;
  for (int i = 0; i < N_ELETTRODI; i++) {
    if (diffVal[i] > diffVal[imax]) imax = i;
    somma += diffVal[i];
  }
  if (somma < SOGLIA_TOCCO) return -1;
  // baricentro su una finestra di +-3 elettrodi attorno al massimo:
  // un dito appoggiato copre 2-3 elettrodi intrecciati -> interpolazione lineare
  long num = 0, den = 0;
  for (int i = max(0, imax - 3); i <= min(N_ELETTRODI - 1, imax + 3); i++) {
    num += (long)diffVal[i] * i; den += diffVal[i];
  }
  return den > 0 ? ((float)num / den) / (N_ELETTRODI - 1) : -1;
}

// Filtro "One Euro": fermo quando il dito e' fermo, pronto quando scivola.
struct OneEuro {
  float minCut = 1.5f, beta = 0.02f, dCut = 1.0f, x = 0, dx = 0; bool primo = true;
  static float alfa(float fc, float dt) { float tau = 1.0f / (6.2832f * fc); return 1.0f / (1.0f + tau / dt); }
  float filtra(float v, float dt) {
    if (primo) { primo = false; x = v; dx = 0; return v; }
    float d = (v - x) / dt;
    dx += alfa(dCut, dt) * (d - dx);
    x  += alfa(minCut + beta * fabsf(dx), dt) * (v - x);
    return x;
  }
} filtroAltezza;

// Magnetismo: 0 = fretless puro, 100 = semitoni esatti. In mezzo il dito
// viene attirato verso il semitono ma vibrato e glissando restano.
static float applicaMagnetismo(float semitoni) {
  float m = preset.magnetismo / 100.0f;
  float vicino = roundf(semitoni);
  return vicino + (semitoni - vicino) * (1.0f - m);          // scarto -0,5..0,5 ridotto
}

// ----------------------------------------------------------------------------
//  NOTE: una nota MIDI + pitch bend continuo. Se il dito esce dall'escursione
//  del bend, si riparte in legato sulla nota piu' vicina.
// ----------------------------------------------------------------------------
int  notaAccesa = -1;
int  ultimoBend = 99999;
bool negHarmony = false;

static void suona(float altezza, bool deveSuonare) {
  if (!deveSuonare) {
    if (notaAccesa >= 0) { midiNotaOff(notaAccesa); notaAccesa = -1; }
    return;
  }
  int vicina = constrain(lroundf(altezza), 0, 127);
  if (notaAccesa < 0 || fabsf(altezza - notaAccesa) > BEND_SEMITONI - 0.5f) {
    int vecchia = notaAccesa;
    notaAccesa = vicina;
    int b = lroundf((altezza - notaAccesa) * 8192.0f / BEND_SEMITONI);
    midiBend(b); ultimoBend = b;                       // il bend prima della nota
    midiNotaOn(notaAccesa, max<uint8_t>(1, fiatoMidi()));
    if (vecchia >= 0) midiNotaOff(vecchia);           // legato: off dopo on
    return;
  }
  int b = lroundf((altezza - notaAccesa) * 8192.0f / BEND_SEMITONI);
  if (abs(b - ultimoBend) >= 4) { midiBend(b); ultimoBend = b; }
}

// ----------------------------------------------------------------------------
//  PULSANTI E PEDALI
// ----------------------------------------------------------------------------
bool     premuto[N_PULSANTI];
uint32_t cambioPulsante[N_PULSANTI];
bool     sustainNormaleChiuso = false, sustainPrima = false;
uint8_t  ultimoEspr = 255;

static void tuttoSpento() {
  if (notaAccesa >= 0) { midiNotaOff(notaAccesa); notaAccesa = -1; }
  midiCC(123, 0); midiCC(64, 0); midiBend(0); ultimoBend = 0;
}

static void azione(uint8_t p) {
  bool shift = premuto[P_SHIFT];
  switch (p) {
    case P_SUONO_SU:
    case P_SUONO_GIU: {
      int d = (p == P_SUONO_SU) ? 1 : -1;
      if (shift) preset.banco = (preset.banco + d + 128) % 128;
      else       preset.programma = (preset.programma + d + 128) % 128;
      inviaSuono();
      break;
    }
    case P_OTT_SU:
    case P_OTT_GIU: {
      int d = (p == P_OTT_SU) ? 1 : -1;
      if (shift) preset.magnetismo = constrain(preset.magnetismo + d * 25, 0, 100);
      else       preset.ottava = constrain(preset.ottava + d, -3, 3);
      break;
    }
    case P_NEG:
      if (shift) {                                  // Shift + Neg = panico e ricalibra
        tuttoSpento();
        calibraFiato();
        if (craftOk) { craft1.updateBaseline(); craft2.updateBaseline(); }
      } else {
        negHarmony = !negHarmony;
        midiCC(CC_NEG_HARMONY, negHarmony ? 127 : 0);
      }
      return;
    default: return;
  }
  ultimaModifica = millis();
}

static void leggiPulsanti() {
  uint32_t ora = millis();
  for (uint8_t i = 0; i < N_PULSANTI; i++) {
    bool giu = digitalRead(PIN_PULSANTE[i]) == LOW;
    if (giu != premuto[i] && ora - cambioPulsante[i] > 15) {   // antirimbalzo 15 ms
      premuto[i] = giu; cambioPulsante[i] = ora;
      if (giu) azione(i);
    }
  }
  bool s = (digitalRead(PIN_SUSTAIN) == LOW) != sustainNormaleChiuso;
  if (s != sustainPrima) { sustainPrima = s; midiCC(64, s ? 127 : 0); }

  uint8_t e = analogRead(PIN_ESPR) >> 3;          // 10 bit -> 7 bit
  if (ultimoEspr == 255 || abs(e - ultimoEspr) >= 2 || (e == 0 && ultimoEspr != 0)) {
    ultimoEspr = e; midiCC(CC_PEDALE_ESPR, e);
  }
}

// ----------------------------------------------------------------------------
void setup() {
  Serial1.begin(31250);
  analogReadResolution(10);
  analogReadAveraging(8);
  for (uint8_t i = 0; i < N_PULSANTI; i++) pinMode(PIN_PULSANTE[i], INPUT_PULLUP);
  pinMode(PIN_SUSTAIN, INPUT_PULLUP);
  delay(50);
  sustainNormaleChiuso = digitalRead(PIN_SUSTAIN) == LOW;  // polarita' letta all'avvio

  Wire.begin();
  Wire.setClock(400000);
  craftOk = avviaCraft(craft1, TRILL_ADDR_1) && avviaCraft(craft2, TRILL_ADDR_2);

  caricaPreset();
  calibraFiato();                                // non soffiare all'accensione
  midiBendRange(BEND_SEMITONI);
  inviaSuono();
  midiBend(0); ultimoBend = 0;
}

void loop() {
  static uint32_t ultimo = micros();
  uint32_t ora = micros();
  if (ora - ultimo < 2000) { while (usbMIDI.read()) {} return; }   // ciclo a 500 Hz
  float dt = (ora - ultimo) * 1e-6f;
  ultimo = ora;

  float pos = craftOk ? leggiNastro() : -1;
  bool tocco = pos >= 0;
  aggiornaFiato(notaAccesa < 0);

  static bool fiatoSu = false;
  if (!fiatoSu && fiato > FIATO_ACCESO) fiatoSu = true;
  if (fiatoSu && fiato < FIATO_SPENTO)  fiatoSu = false;

  // dinamica: CC al massimo ogni 4 ms e solo se cambia
  static uint32_t ultimoCC = 0;
  uint8_t f = fiatoMidi();
  if (f != ultimoCCfiato && millis() - ultimoCC >= 4) {
    ultimoCCfiato = f; ultimoCC = millis();
    midiCC(CC_FIATO, f);
    if (CC_FIATO_COPIA) midiCC(CC_FIATO_COPIA, f);
  }

  if (tocco) {
    float semitoni = filtroAltezza.filtra(pos * ESTENSIONE, dt);
    float altezza = NOTA_BASE + preset.ottava * 12 + applicaMagnetismo(semitoni);
    suona(altezza, SERVE_IL_FIATO ? fiatoSu : true);
  } else {
    filtroAltezza.primo = true;                    // al prossimo tocco niente scivolata
    suona(0, false);
  }

  leggiPulsanti();
  forseSalva();
  while (usbMIDI.read()) {}                        // svuota l'ingresso USB
}
