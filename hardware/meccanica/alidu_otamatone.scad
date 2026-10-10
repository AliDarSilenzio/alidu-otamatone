// =============================================================================
//  Alidu Otamatone - meccanica stampabile in 3D
//  Progetto di Dario Amabile - licenza CERN-OHL-S v2
//
//  Un solo file, tutti i pezzi. Si sceglie il pezzo con la variabile "pezzo":
//    openscad -D 'pezzo="corpo_anteriore"' -o corpo_anteriore.stl alidu_otamatone.scad
//  Pezzi: corpo_anteriore, corpo_posteriore, collare, testa, testa_coperchio,
//         innesto_bocchino, guida_nastro
//  Viste (non si stampano): assieme, esploso, corpo, spaccato, tavola
//
//  Assi: X = larghezza, Y = profondita' (+Y = davanti, verso chi guarda),
//        Z = altezza. Misure in millimetri.
//  Materiale consigliato: PETG, pareti 4 perimetri, riempimento 30-40%.
// =============================================================================

pezzo = "assieme";

/* [Corpo] */
A = 70;          // semiasse X del guscio (larghezza 140)
B = 60;          // semiasse Y (profondita' 120)
C = 75;          // semiasse Z (altezza 150)
PARETE = 3;
PIANO_Y = 53;    // piani piatti davanti (pulsanti) e dietro (prese)
TOP_Z = 62;      // piano superiore, dove si avvita il collare
BASE_Z = -68;    // base piatta: lo strumento sta in piedi
SPESS_TOP = 8;   // spessore del piano superiore (accoglie gli inserti)

/* [Manico] */
MANICO = 35;     // profilato a U 35 x 35
GIOCO = 0.4;
INSERIMENTO = 22;  // quanto il manico entra nel corpo, sotto il piano superiore
VETRO = 2.2;       // spessore del vetro sul davanti del profilato, con gioco

/* [Scheda principale 110 x 72] */
SCHEDA = [110, 72];
SCHEDA_Y = -10;  // faccia inferiore della scheda (componenti verso il davanti)
FORI_SCHEDA = 4.5;

/* [Pulsanti tipo Cherry MX] */
FORO_MX = 14.0;  // foro quadro per piastra da 1,5 mm
PASSO_MX = 19;

$fn = 96;
eps = 0.01;

// ---------------------------------------------------------------- utilita'
module ellissoide(a, b, c) { scale([a, b, c]) sphere(1); }
module semispazio_y(segno) {          // segno +1: y >= 0 ; -1: y <= 0
    translate([-200, segno > 0 ? 0 : -400, -200]) cube([400, 400, 400]);
}
module inserto_m3(h = 6) { cylinder(d = 4.0, h = h); }   // inserto filettato a caldo M3

// forma esterna e cavita' del corpo
module corpo_esterno() {
    intersection() {
        ellissoide(A, B, C);
        translate([-200, -PIANO_Y, BASE_Z]) cube([400, 2 * PIANO_Y, TOP_Z - BASE_Z]);
    }
}
module corpo_cavita() {
    intersection() {
        ellissoide(A - PARETE, B - PARETE, C - PARETE);
        translate([-200, -PIANO_Y + 2, BASE_Z + PARETE])
            cube([400, 2 * PIANO_Y - 2 - 1.5, TOP_Z - SPESS_TOP - BASE_Z - PARETE]);
    }
}

// viti della giunzione: lontane dalla scheda, in alto e in basso
VITI_GIUNZIONE = [[-38, 52], [38, 52], [-38, -52], [38, -52]];
// viti del collare sul piano superiore
VITI_COLLARE = [[-24, -22], [24, -22], [-24, 22], [24, 22]];

module guscio() {
    difference() {
        corpo_esterno();
        corpo_cavita();
        // passaggio del manico nel piano superiore
        translate([-(MANICO + GIOCO) / 2, -(MANICO + GIOCO) / 2, TOP_Z - SPESS_TOP - 1])
            cube([MANICO + GIOCO, MANICO + GIOCO, SPESS_TOP + 2]);
        // inserti per il collare
        for (v = VITI_COLLARE) translate([v[0], v[1], TOP_Z - 6]) inserto_m3(6.5);
    }
}

// ---------------------------------------------------------------- davanti
module corpo_anteriore() {
    difference() {
        union() {
            intersection() { guscio(); semispazio_y(1); }
            // colonne delle viti della giunzione, fuse nella parete
            intersection() {
                corpo_esterno();
                for (v = VITI_GIUNZIONE) translate([v[0], 0, v[1]])
                    rotate([-90, 0, 0]) cylinder(r = 4.5, h = 60);
            }
        }
        for (v = VITI_GIUNZIONE) translate([v[0], 0, v[1]]) rotate([-90, 0, 0]) {
            translate([0, 0, -eps]) cylinder(d = 3.4, h = 61);           // passante M3
            translate([0, 0, 12]) cylinder(d = 6.5, h = 61);             // sede della testa
        }
        // sei pulsanti: due colonne da tre
        for (x = [-PASSO_MX / 2, PASSO_MX / 2], z = [-PASSO_MX, 0, PASSO_MX])
            translate([x - FORO_MX / 2, PIANO_Y - 5, z - FORO_MX / 2]) cube([FORO_MX, 10, FORO_MX]);
        // battuta per l'aletta del guscio posteriore
        intersection() {
            ellissoide(A - PARETE + 0.2, B - PARETE + 0.2, C - PARETE + 0.2);
            translate([-200, -eps, -200]) cube([400, 2.7, 400]);
        }
    }
}

// ---------------------------------------------------------------- dietro
module corpo_posteriore() {
    difference() {
        union() {
            intersection() { guscio(); semispazio_y(-1); }
            // aletta di centraggio che entra nel guscio anteriore
            intersection() {
                difference() {
                    ellissoide(A - PARETE, B - PARETE, C - PARETE);
                    ellissoide(A - PARETE - 1.6, B - PARETE - 1.6, C - PARETE - 1.6);
                }
                translate([-200, 0, BASE_Z + PARETE]) cube([400, 2.5, TOP_Z - SPESS_TOP - BASE_Z - PARETE]);
            }
            // colonne per gli inserti della giunzione
            intersection() {
                corpo_esterno();
                for (v = VITI_GIUNZIONE) translate([v[0], -60, v[1]])
                    rotate([-90, 0, 0]) cylinder(r = 4.5, h = 60);
            }
            // quattro colonnine per la scheda principale
            intersection() {
                corpo_esterno();
                for (x = [-1, 1], z = [-1, 1])
                    translate([x * (SCHEDA[0] / 2 - FORI_SCHEDA), -60, z * (SCHEDA[1] / 2 - FORI_SCHEDA)])
                        rotate([-90, 0, 0]) cylinder(r = 3.8, h = 60 + SCHEDA_Y);
            }
        }
        for (v = VITI_GIUNZIONE) translate([v[0], eps, v[1]]) rotate([90, 0, 0]) inserto_m3(8);
        for (x = [-1, 1], z = [-1, 1])
            translate([x * (SCHEDA[0] / 2 - FORI_SCHEDA), SCHEDA_Y + eps, z * (SCHEDA[1] / 2 - FORI_SCHEDA)])
                rotate([90, 0, 0]) inserto_m3(7);
        // pannello delle prese
        translate([-14, -PIANO_Y - 1, 10]) rotate([-90, 0, 0]) cylinder(d = 16, h = 6);    // MIDI DIN
        translate([14, -PIANO_Y + 2, 10]) cube([12.5, 8, 6.5], center = true);           // USB-C
        for (x = [-12, 12]) translate([x, -PIANO_Y - 1, -14]) rotate([-90, 0, 0]) cylinder(d = 9.5, h = 6);
        // scritte incise
        for (t = [["MIDI", -14, 22], ["USB", 14, 22], ["SUST", -12, -26], ["ESPR", 12, -26]])
            translate([t[1], -PIANO_Y + 0.6, t[2]]) rotate([90, 0, 0])
                linear_extrude(1)
                    text(t[0], size = 3.6, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
    }
}

// ---------------------------------------------------------------- collare
COLLARE_H = 45;
module collare() {
    difference() {
        union() {
            // flangia ellittica appoggiata sul piano superiore
            intersection() {
                scale([39, 33.5, 1]) cylinder(r = 1, h = 5);
                translate([-50, -50, 0]) cube([100, 100, 5]);
            }
            // manicotto
            translate([-(MANICO + 8) / 2, -(MANICO + 8) / 2, 0]) cube([MANICO + 8, MANICO + 8 + VETRO, COLLARE_H]);
        }
        // sede del profilato, piu' profonda sul davanti dove passa il vetro
        translate([-(MANICO + GIOCO) / 2, -(MANICO + GIOCO) / 2, -eps]) cube([MANICO + GIOCO, MANICO + GIOCO + VETRO, COLLARE_H + 1]);
        for (v = VITI_COLLARE) translate([v[0], v[1], -eps]) {
            cylinder(d = 3.4, h = 6);
            translate([0, 0, 2.5]) cylinder(d = 6.5, h = 6);
        }
        // due grani M3 che stringono il manico (inserti nel manicotto)
        for (s = [-1, 1]) translate([s * (MANICO / 2 + 2), 0, COLLARE_H - 15])
            rotate([0, s * 90, 0]) translate([0, 0, -3]) inserto_m3(8);
    }
}

// ---------------------------------------------------------------- testa
TESTA = [47, 47, 75];
ZOCCOLO = 30;    // quanto la testa calza sul manico
module testa() {
    difference() {
        union() {
            translate([-TESTA[0] / 2, -TESTA[1] / 2, 0])
                minkowski() { translate([3, 3, 0]) cube([TESTA[0] - 6, TESTA[1] - 6, TESTA[2] - 3]); cylinder(r = 3, h = 3); }
            translate([0, 0, TESTA[2]]) cylinder(d = 22, h = 10);              // sede dell'innesto
        }
        // calza sul manico
        translate([-(MANICO + GIOCO) / 2, -(MANICO + GIOCO) / 2, -eps]) cube([MANICO + GIOCO, MANICO + GIOCO, ZOCCOLO]);
        // vano per camera della condensa, raccordo a T, sensore
        translate([-20.5, -20.5, ZOCCOLO - eps]) cube([41, 41, TESTA[2] - ZOCCOLO - 3]);
        // apertura posteriore chiusa dal coperchio
        translate([-17.5, -TESTA[1] / 2 - 1, ZOCCOLO + 4]) cube([35, 6, 34]);
        for (x = [-1, 1], z = [ZOCCOLO + 1.5, ZOCCOLO + 40.5])
            translate([x * 20.5, -TESTA[1] / 2 + 6, z]) rotate([90, 0, 0]) inserto_m3(6);
        // innesto del bocchino
        translate([0, 0, TESTA[2] - 4]) cylinder(d = 13.2, h = 20);
        // uscita dello sfiato, sul fianco
        translate([TESTA[0] / 2 - 4, 0, ZOCCOLO + 22]) rotate([0, 90, 0]) cylinder(d = 5, h = 10);
    }
}
module testa_coperchio() {
    difference() {
        translate([-20.5 - 4, 0, 0]) cube([49, 2.5, 46]);
        for (x = [-1, 1], z = [1.5, 40.5]) translate([x * 20.5, -1, z + 2.5]) rotate([-90, 0, 0]) {
            cylinder(d = 3.4, h = 5);
        }
    }
}

// ---------------------------------------------------------------- innesto bocchino
module innesto_bocchino() {
    difference() {
        union() {
            cylinder(d = 13.0, h = 10);                 // si incolla nella testa
            translate([0, 0, 10]) cylinder(d = 18, h = 4);
            translate([0, 0, 14]) cylinder(d = 13.0, h = 30);    // qui calza il bocchino (nastro di teflon o sughero)
            translate([0, 0, -8]) cylinder(d = 3.6, h = 8);      // portagomma per il tubo 3 x 5
            translate([0, 0, -5]) cylinder(d1 = 3.6, d2 = 4.2, h = 2);
        }
        translate([0, 0, -9]) cylinder(d = 2.0, h = 20);
        translate([0, 0, 10]) cylinder(d = 7, h = 40);
        translate([0, 0, 9]) cylinder(d1 = 2, d2 = 7, h = 1.01);
    }
}

// ---------------------------------------------------------------- guida del nastro
module guida_nastro() {   // due per meta' nastro: tengono il circuito a 2 mm dalle pareti
    cube([245, 2, 6]);
}

// ---------------------------------------------------------------- assieme
// ------------------------------------------- parti non stampate (solo per le viste)
Z_MANICO = TOP_Z - INSERIMENTO;          // fondo del manico
Z_VETRO = [Z_MANICO + 48, Z_MANICO + 48 + 505];
module scheda_fantasma() {
    translate([-SCHEDA[0] / 2, SCHEDA_Y, -SCHEDA[1] / 2]) {
        color("darkgreen") cube([SCHEDA[0], 1.6, SCHEDA[1]]);
        color("seagreen") translate([7, 1.6, 4]) cube([18, 12, 61 > SCHEDA[1] - 6 ? SCHEDA[1] - 8 : 61]);   // Teensy
        color("white") for (z = [8, 22, 36, 50, 62]) translate([SCHEDA[0] - 16, 1.6, z]) cube([6, 7, 9]);  // JST
    }
}
module nastro_fantasma() {        // due meta' del nastro sotto il vetro: frecce di rame
    P = 250 / 30; D = 0.9 * P; w = 12.5;
    color([0.12, 0.13, 0.12]) translate([-13.5, MANICO / 2 - 1.8, Z_VETRO[0]]) cube([27, 1.6, 505]);
    for (meta = [0, 1]) for (k = [1 : 29]) {
        zc = Z_VETRO[0] + 2 + meta * 252 + k * P;
        verso = meta == 0 ? -1 : 1;      // la meta' B e' montata ruotata
        color([0.85, 0.5, 0.25]) translate([0, MANICO / 2 - 0.15, 0])
            for (s = [-1, 1]) hull() {
                translate([0, 0, zc + verso * D / 2]) rotate([90, 0, 0]) cylinder(d = 0.7, h = 0.1, $fn = 8);
                translate([s * w, 0, zc - verso * D / 2]) rotate([90, 0, 0]) cylinder(d = 0.7, h = 0.1, $fn = 8);
            }
    }
}
module tasti() {
    color([0.78, 0.8, 0.83]) for (x = [-PASSO_MX / 2, PASSO_MX / 2], z = [-PASSO_MX, 0, PASSO_MX])
        translate([x, PIANO_Y - 0.5, z]) rotate([-90, 0, 0]) cylinder(d1 = 16, d2 = 15, h = 7);
}
module prese() {
    color([0.75, 0.76, 0.78]) {
        translate([-14, -PIANO_Y + 0.5, 10]) rotate([90, 0, 0]) difference() { cylinder(d = 21, h = 2); cylinder(d = 15, h = 5, center = true); }
        for (x = [-12, 12]) translate([x, -PIANO_Y + 0.5, -14]) rotate([90, 0, 0]) difference() { cylinder(d = 13, h = 2.5, $fn = 6); cylinder(d = 6.5, h = 6, center = true); }
    }
    color([0.1, 0.1, 0.1]) {
        translate([-14, -PIANO_Y + 1, 10]) rotate([90, 0, 0]) cylinder(d = 15, h = 0.6);
        translate([14, -PIANO_Y + 0.4, 10]) cube([9, 1, 3.2], center = true);
    }
}
module bocchino() {               // bocchino tipo sassofono contralto
    color([0.06, 0.06, 0.06]) hull() {
        cylinder(d = 21, h = 30);
        translate([0, 3, 66]) scale([1, 0.32, 1]) sphere(d = 16);
        translate([0, -1, 40]) scale([1, 0.75, 1]) cylinder(d = 19, h = 6);
    }
    color([0.7, 0.7, 0.72]) translate([0, 0, 8]) cylinder(d = 23, h = 6);   // fascetta
}
module manico_completo(z0 = Z_MANICO) {
    color([0.78, 0.79, 0.8]) translate([-MANICO / 2, -MANICO / 2, z0]) difference() {
        cube([MANICO, MANICO, 600]);
        translate([2, 2, -1]) cube([MANICO - 4, MANICO, 602]);
    }
    translate([0, 0, z0 - Z_MANICO]) {
        nastro_fantasma();
        color([0.05, 0.07, 0.08], 0.55) translate([-MANICO / 2, MANICO / 2, Z_VETRO[0]]) cube([MANICO, 2, 505]);
    }
}
Z_TESTA = Z_MANICO + 600 - ZOCCOLO;
module assieme() {
    color("white") corpo_anteriore();
    color("gainsboro") corpo_posteriore();
    tasti(); prese();
    scheda_fantasma();
    color([0.25, 0.26, 0.28]) translate([0, 0, TOP_Z]) collare();
    manico_completo();
    color([0.25, 0.26, 0.28]) translate([0, 0, Z_TESTA]) testa();
    color([0.25, 0.26, 0.28]) translate([0, -TESTA[1] / 2, Z_TESTA + ZOCCOLO + 2]) testa_coperchio();
    color("black") translate([0, 0, Z_TESTA + TESTA[2] - 4]) innesto_bocchino();
    translate([0, 0, Z_TESTA + TESTA[2] + 14]) bocchino();
}
module esploso() {                // le parti allontanate lungo il loro asse di montaggio
    color("white") translate([0, 70, 0]) corpo_anteriore();
    translate([0, 110, 0]) tasti();
    color("gainsboro") translate([0, -90, 0]) { corpo_posteriore(); prese(); }
    translate([0, -20, 0]) scheda_fantasma();
    color([0.25, 0.26, 0.28]) translate([0, 0, TOP_Z + 50]) collare();
    // manico aperto: profilato, circuito del nastro, vetro, ciascuno staccato
    translate([0, 0, 140]) {
        color([0.78, 0.79, 0.8]) translate([-MANICO / 2, -MANICO / 2, Z_MANICO]) difference() {
            cube([MANICO, MANICO, 600]); translate([2, 2, -1]) cube([MANICO - 4, MANICO, 602]); }
        translate([0, 45, 0]) nastro_fantasma();
        color([0.05, 0.07, 0.08], 0.5) translate([-MANICO / 2, MANICO / 2 + 90, Z_VETRO[0]]) cube([MANICO, 2, 505]);
    }
    color([0.25, 0.26, 0.28]) translate([0, 0, Z_TESTA + 220]) testa();
    color([0.25, 0.26, 0.28]) translate([0, -TESTA[1] / 2 - 40, Z_TESTA + 220 + ZOCCOLO + 2]) testa_coperchio();
    color("black") translate([0, 0, Z_TESTA + 220 + TESTA[2] + 30]) innesto_bocchino();
    translate([0, 0, Z_TESTA + 220 + TESTA[2] + 110]) bocchino();
}

// ---------------------------------------------------------------- scelta
if (pezzo == "corpo_anteriore") rotate([-90, 0, 0]) corpo_anteriore();     // giunzione sul piatto
else if (pezzo == "corpo_posteriore") rotate([90, 0, 0]) corpo_posteriore();
else if (pezzo == "collare") collare();
else if (pezzo == "testa") testa();
else if (pezzo == "testa_coperchio") rotate([90, 0, 0]) testa_coperchio();
else if (pezzo == "innesto_bocchino") innesto_bocchino();
else if (pezzo == "guida_nastro") guida_nastro();
else if (pezzo == "esploso") esploso();
else if (pezzo == "esploso_orizzontale") rotate([0, 90, 0]) esploso();
else if (pezzo == "spaccato") intersection() { assieme(); translate([-400, -200, -200]) cube([400, 400, 1200]); }
else if (pezzo == "corpo") { color("white") corpo_anteriore(); color("gainsboro") corpo_posteriore(); scheda_fantasma(); color("dimgray") translate([0, 0, TOP_Z]) collare(); }
else if (pezzo == "tavola") {          // tutti i pezzi come vanno sul piatto, per le immagini
    color("white") translate([-80, 0, 0]) rotate([-90, 0, 0]) corpo_anteriore();
    color("gainsboro") translate([80, 0, 0]) rotate([90, 0, 0]) corpo_posteriore();
    color("dimgray") translate([0, 110, 0]) collare();
    color("dimgray") translate([-90, 120, 0]) testa();
    color("dimgray") translate([90, 120, 0]) rotate([90, 0, 0]) testa_coperchio();
    color("black") translate([40, 170, 8]) innesto_bocchino();
    color("silver") translate([-122, -95, 0]) guida_nastro();
}
else assieme();
