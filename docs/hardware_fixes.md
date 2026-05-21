# ESP Pinpout
```cpp
/// Definition of encoder pins

#ifndef PIN_DEFINITIONS_H
#define PIN_DEFINITIONS_H
  
//static float const meterPerRev = 6.35e-3F;
static float const meterPerClick = 6.35e-3F/20.F;

/// On/Off switches per step that would invoke the position changed callback function?
static byte const rotary_steps_per_click = 4;

#define ROTARY_PIN_X1 D0
#define ROTARY_PIN_X2 D1
#define ROTARY_PIN_Y1 D2
#define ROTARY_PIN_Y2 D5
#define ROTARY_PIN_Z1 D6
#define ROTARY_PIN_Z2 D7

#endif
```

# Personen
- Louis Moser  
- Benjamin Keppler  

# Hardware Fixes
- geänderte Kabelführung  
- umgelöteter letzter Endstop  
- umgelötete Motorpins der Y-Achse am Arduino  
- Umverlegung der USB-Kabel  
- veränderte Befestigung des Kamerakabels  

# Geänderte Kabelführung
Auftrennung bestehender Kabelbinder-Konstruktionen und Zusammenführung aller möglichen Kabelführungen.  
Anschließende sinnvolle Befestigungen am Alugestell mit Kabelbindern, sofern möglich.

# Umgelöteter letzter Endstop
Entfernen der aktuellen Female-Pins.  
Anlöten von halbierten Female-Arduino-Jumpern.  
Isolierung mit innerem und äußerem Schrumpfschlauch.

# Umgelötete Motorpins der Y-Achse am Arduino
Entfernen der aktuellen Female-Pins.  
Anlöten von halbierten Female-Arduino-Jumpern.  
Isolierung mit innerem und äußerem Schrumpfschlauch.

# Umverlegung der USB-Kabel
Umverlegung vom Eck des Alugestells zum vorderen Ende der Steckerleiste.

# Veränderte Befestigung des Kamerakabels
Entfernung des Gaffabandes und Ersetzung durch Kabelbinder.

# Geplant, aber nicht gemacht
Geplant war zunächst ein Austausch der Motortreiber, zunächst bei der Y-Achse. Allerdings ist durch Zufall aufgefallen, dass dies nicht notwendig ist, da lediglich die Kontaktierung der Pins am Arduino ausgeleiert war.  
Deshalb wurden stattdessen die `umgelöteten Motorpins der Y-Achse am Arduino` vorgenommen, wodurch das ursprüngliche Problem behoben wurde.  

Dementsprechend wurde an keinem Motortreiber etwas verändert.