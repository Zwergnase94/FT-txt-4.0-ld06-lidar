# Omniwheel-Fahrwerk & 8-Wege-Ausweichlogik

Dieses Dokument beschreibt die Ansteuerung des 4-motorischen Omniwheel-/Mecanum-Fahrwerks am fischertechnik TXT 4.0 in der App `lidar_omni`.

---

## 1. Motoranordnung (M1–M4)

Die vier Encodermotoren sind direkt an den Ausgängen **M1 bis M4** des TXT 4.0 angeschlossen:

```text
        ▲ VORNE (0°)
        │
┌───────┴───────┐
│ [M1]     [M2] │   M1: Vorne-Links
│               │   M2: Vorne-Rechts
│               │   M3: Hinten-Rechts
│ [M4]     [M3] │   M4: Hinten-Links
└───────┬───────┘
        │
        ▼ HINTEN (180°)
```

### Drehrichtungen (`Motor.CCW` / `Motor.CW`)

| Fahrtrichtung | M1 (VL) | M2 (VR) | M3 (HR) | M4 (HL) | Ansteuerung |
|---|---|---|---|---|---|
| **VORNE** | CCW | CCW | CCW | CCW | `M1.start_sync(M2, M3, M4)` |
| **HINTEN** | CW | CW | CW | CW | `M1.start_sync(M2, M3, M4)` |
| **LINKS** | CCW | CW | CW | CCW | `M1.start_sync(M2, M3, M4)` |
| **RECHTS** | CW | CCW | CCW | CW | `M1.start_sync(M2, M3, M4)` |
| **VORNE-LINKS** | CCW | Stopp | Stopp | CCW | Diagonal (M1, M4) |
| **VORNE-RECHTS** | Stopp | CCW | CCW | Stopp | Diagonal (M2, M3) |
| **HINTEN-LINKS** | Stopp | CW | CW | Stopp | Diagonal (M2, M3) |
| **HINTEN-RECHTS** | CW | Stopp | Stopp | CW | Diagonal (M1, M4) |
| **STOPP** | Stopp | Stopp | Stopp | Stopp | `M1.stop_sync(M2, M3, M4)` |

---

## 2. 8-Wege-Ausweichalgorithmus

Der 360°-Scan des LiDARs wird in **8 Sektoren zu je 45°** aufgeteilt:

```text
              VORNE (0°)
                 [0]
       [7]                 [1]
   VORNE-LINKS        VORNE-RECHTS
        │                  │
LINKS [6] ─── ROBOTER ─── [2] RECHTS
        │                  │
  HINTEN-LINKS       HINTEN-RECHTS
       [5]                 [3]
                 [4]
             HINTEN (180°)
```

### Ablauf im Betrieb
1. **Hindernis erkennen:** Fällt der Abstand in einem Sektor unter `TRIGGER_DIST = 20,0 cm`, wird ein Ausweichmanöver in die gegenüberliegende Richtung vorbereitet.
2. **Fluchtweg prüfen:** Der gegenüberliegende Sektor muss mindestens `CLEAR_ESCAPE_MIN = 22,0 cm` Platz bieten. Ist auch dieser Weg versperrt, stoppen alle Motoren (`BLOCKIERT`).
3. **Hysterese:** Das Ausweichen läuft weiter, bis der Abstand zum auslösenden Hindernis wieder über `RELEASE_DIST = 25,0 cm` liegt. Die 5-cm-Hysterese verhindert ruckartiges Umschalten an der Auslösegrenze.
