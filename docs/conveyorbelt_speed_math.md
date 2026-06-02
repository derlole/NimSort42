# Förderband-Geschwindigkeitsschätzung (ConveyorSpeedEstimator)

## Überblick

Die `ConveyorSpeedEstimator`-Klasse schätzt die Geschwindigkeit eines Förderbandes basierend auf visuellen Positionsmessungen. Sie kombiniert mehrere mathematische Filter und Heuristiken, um eine robuste und stabile Geschwindigkeitsmessung zu ermöglichen.

---

## Mathematische Konzepte

### 1. **Rohgeschwindigkeitsberechnung**

```math
rawspeed = Δx / Δt = (x_n - x_{n-1}) / (t_n - t_{n-1})
```

**Was:** Die Geschwindigkeit wird als Änderung der Position pro Zeiteinheit berechnet.

**Warum gut:**
- Einfach und direkt aus verfügbaren Messdaten
- Basiert auf physikalischen Größen (Distanz / Zeit)

**Beispiel:** Wenn sich ein Objekt auf dem Förderband um 10 cm in 0,1 Sekunden bewegt, ist die Rohgeschwindigkeit:
```
raw_speed = 0.1 m / 0.1 s = 1.0 m/s
```

---

### 2. **Medianfilter**

```
filtered_speed = median(raw_speed[0:N])
```

Dabei ist `N` die Puffergröße (Standard: 11 Messwerte).

**Was:** Der Median wird aus den letzten N Rohgeschwindigkeitsmessungen berechnet.

**Warum gut:**
- **Ausreißerunterdrückung:** Der Median ist robust gegen einzelne fehlerhafte Messungen. Auch wenn eine Messung völlig falsch ist, beeinflusst sie den Median nicht stark.
- **Nicht-parametrisch:** Keine Annahmen über die Verteilung der Daten nötig.
- **Beispiel:** Messwerte `[0.95, 0.98, 1.02, 5.0, 1.01, 0.97, ...]` → Median ≈ 0.99 (der Ausreißer 5.0 wird ignoriert)

```
Messwerte: [0.95, 0.97, 0.98, 1.00, 1.01, 1.02, ...]
           ↓     ↓     ↓     ↓     ↓     ↓
Median der 11 Werte = der Mittelwert (6. Wert) ≈ 1.00
```

---

### 3. **Exponentiell gewichteter Durchschnitt (EMA)**

```math
v_smooth = α · v_filtered + (1 - α) · v_smooth_previous
```

Wobei:
- `α` = Glättungsfaktor (Standard: 0.3)
- `v_filtered` = gefilterte Geschwindigkeit
- `v_smooth_previous` = vorherige geglättete Geschwindigkeit

**Was:** Ein exponentieller Durchschnitt, der neuere Messungen stärker gewichtet, aber noch Vergangenheitswerte berücksichtigt.

**Warum gut:**
- **Sanfte Übergänge:** Verhindert sprunghafte Geschwindigkeitsänderungen
- **Speichereffizient:** Speichert nur die letzte Geschwindigkeit, nicht die gesamte Historie
- **Anpassungsgeschwindigkeit:** Mit `α = 0.3` werden neue Messungen zu 30% berücksichtigt, alte zu 70%

**Beispiel:**
```
Messung 1: v_filtered = 1.0 m/s
  → v_smooth = 0.3 × 1.0 + 0.7 × 0.0 = 0.3 m/s

Messung 2: v_filtered = 1.0 m/s
  → v_smooth = 0.3 × 1.0 + 0.7 × 0.3 = 0.51 m/s

Messung 3: v_filtered = 1.0 m/s
  → v_smooth = 0.3 × 1.0 + 0.7 × 0.51 = 0.657 m/s
  (nähert sich langsam dem wahren Wert an)
```

---

### 4. **Persistenzprüfung (Drop Detection)**

```math
\text{Falls } v_{filtered} < v_{smooth} · \text{drop\_threshold}:
  \text{drop\_counter += 1}
  
\text{Falls } \text{drop\_counter} ≥ \text{required\_drop\_frames}:
  \text{akzeptiere Geschwindigkeitsänderung}
\text{Sonst:}
  \text{ignoriere Ausreißer und halte alte Geschwindigkeit}
```

Wobei:
- `drop_threshold` = 0.8 (erlaubter Geschwindigkeitsabfall = 20%)
- `required_drop_frames` = 8 (nötige aufeinanderfolgende Frames)

**Was:** Ein Hysteresefilter, der nur signifikante und anhaltende Geschwindigkeitsabfälle akzeptiert.

**Warum gut:**
- **Ausreißerunterdrückung:** Einzelne fehlerhafte Messungen führen nicht zu Geschwindigkeitssprüngen
- **Verzögerung akzeptabel:** Im Anwendungsfall (Förderband) ändert sich die Geschwindigkeit nicht abrupt; daher ist eine kleine Verzögerung kein Problem
- **Robustheit:** Das System vertraut erst nach mehreren bestätigenden Messungen

**Beispiel:**
```
Aktuelle Geschwindigkeit: 1.0 m/s
drop_threshold = 0.8 → Trigger bei < 0.8 m/s

Messung: 0.5 m/s (großer Abfall)
  → drop_counter = 1 (< 8, ignorieren → 1.0 m/s bleiben)

Messung: 0.4 m/s (großer Abfall)
  → drop_counter = 2 (< 8, ignorieren → 1.0 m/s bleiben)

... (6 weitere schlechte Messungen) ...

Messung 8: 0.3 m/s
  → drop_counter = 8 (≥ 8, akzeptieren → neue Geschwindigkeit setzen)
```

---

## Ablauf des Algorithmus

```
update(x_m, ts_ms):
    
    1. Erste Messung?
       → Speichere Position und Zeit, gebe None zurück
    
    2. Berechne Rohgeschwindigkeit
       raw_speed = (x_m - x_last) / (t_ms - t_last)
    
    3. Geschwindigkeit <= 0? (Förderband bewegt sich nicht)
       → Gebe letzte Geschwindigkeit zurück
    
    4. Füge raw_speed zum Puffer (Größe 11) hinzu
    
    5. Puffer nicht voll?
       → Warte auf mehr Messungen, gebe None zurück
    
    6. Berechne Median der 11 Werte (Medianfilter)
    
    7. Ist dies die erste gültige Messung?
       → Setze v_smooth = filtered_speed
    
    8. Prüfe auf Geschwindigkeitsabfall (Persistenzprüfung)
       
       Falls filtered_speed < v_smooth × 0.8:
           drop_counter += 1
           Falls drop_counter < 8:
               gebe v_smooth zurück (ignoriere Ausreißer)
       Sonst:
           drop_counter = 0
    
    9. Wende EMA an
       v_smooth = 0.3 × filtered_speed + 0.7 × v_smooth
    
    10. Gebe v_smooth zurück
```

---

## Warum diese Kombination gut ist

| Technik | Problem, das gelöst wird | Alternative | Nachteil der Alternative |
|---------|---------------------------|-------------|--------------------------|
| **Medianfilter** | Ausreißer in Einzelmessungen | Mittelwertfilter | Mittelwert wird von Ausreißern stark beeinflusst |
| **EMA-Glättung** | Sprunghafte Übergänge | Kalman-Filter | Kalman-Filter sind komplexer, benötigen Systemmodell |
| **Persistenzprüfung** | Falsche Geschwindigkeitsstöße | Direkter EMA | Würde auf jeden Messfehler reagieren |

### Synergieeffekte

1. **Medianfilter** entfernt Ausreißer → **EMA** bekommt saubere Daten
2. **EMA** glättet → **Persistenzprüfung** erkennt echte Änderungen vs. Noise
3. **Persistenzprüfung** akzeptiert nur bestätigte Änderungen → System bleibt stabil

---

## Parameter Erklärung

### `smoothing = 0.3`
- Wie stark neue Messungen gewichtet werden
- Höher (z.B. 0.7) → schnellere Reaktion auf Änderungen, aber störanfälliger
- Niedriger (z.B. 0.1) → stabiler, aber langsamere Reaktion

### `median_window = 11`
- Anzahl der Rohwerte, aus denen der Median berechnet wird
- Größer → mehr Filterung, aber längere Verzögerung
- Standard 11 ist ein guter Kompromiss

### `drop_threshold = 0.8`
- Welcher Geschwindigkeitsabfall als signifikant gilt (20%)
- Bei 1.0 m/s gilt < 0.8 m/s als Abfall

### `required_drop_frames = 8`
- Wie viele aufeinanderfolgende Frames einen Abfall bestätigen müssen
- Mehr Frames → robuster gegen Noise, aber langsamere Reaktion auf echte Änderungen

---

## Besonderheiten

### Initialisierung
```python
self._last_x = None  # Speichert letzte Position
self._estimated_speed = 0.0  # Startet bei 0
self._speed_buffer = deque(maxlen=11)  # Ringpuffer (automatisches Verwerfen alter Werte)
self._drop_counter = 0  # Zähler für persistente Abfälle
```

### Reset-Funktion
Setzt den Estimator zurück (z.B. wenn Förderband stoppt oder Position verloren geht).

---

## Anwendungsbeispiel

```python
estimator = ConveyorSpeedEstimator(smoothing=0.3, median_window=11)

# Simulation: Förderband bewegt sich mit ~1.0 m/s
for frame_idx in range(100):
    x_position = 0.1 * frame_idx  # 0.1 m pro Frame
    timestamp_ms = frame_idx * 10  # 10 ms pro Frame
    
    speed = estimator.update(x_position, timestamp_ms)
    if speed is not None:
        print(f"Frame {frame_idx}: Geschwindigkeit = {speed:.3f} m/s")

# Output (nach Aufwärmphase):
# Frame 15: Geschwindigkeit = 1.000 m/s
# Frame 16: Geschwindigkeit = 1.000 m/s
# ...
```

---

## Zusammenfassung

Die `ConveyorSpeedEstimator`-Klasse ist gut weil sie:

✅ **Robust:** Mehrere Filter kombiniert (Median + EMA + Persistenzprüfung)
✅ **Stabil:** Keine sprunghaften Änderungen durch Noise
✅ **Einfach:** Konfigurierbar ohne komplexe mathematische Systeme
✅ **Effizient:** O(1) Speicher (ignoriert alte Messwerte)
✅ **Praktisch:** Passt sich an reale Förderbandbewegungen an
