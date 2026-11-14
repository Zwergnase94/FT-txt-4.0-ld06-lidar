# Omniwheel-Fahrwerk & Omni 8-Zonen Hindernisschutz

Dieses Dokument beschreibt die Ansteuerung des 4-motorischen Omniwheel-/Mecanum-Fahrwerks am fischertechnik TXT 4.0 in der App `lidar_omni` („Omni 8-Zonen“).

---

## 1. Motoranordnung (M1–M4)

Die vier Encodermotoren sind direkt an den Ausgängen **M1 bis M4** des TXT 4.0 angeschlossen:

```text
        ▲ VORNE (0°)
        │
┌───────┴───────┐
│ [M1]     [M2] │   M1: Vorne-Links
│               │   M2: Vorne-Rechts
│               │   M3: Hinten-Links
│ [M3]     [M4] │   M4: Hinten-Rechts
└───────┬───────┘
        │
        ▼ HINTEN (180°)
```

### Drehrichtungen (`Motor.CCW` / `Motor.CW`)

| Fahrtrichtung / Aktion | M1 | M2 | M3 | M4 | Ansteuerung |
|---|---|---|---|---|---|
| **VORNE** (`0°`) | CCW | CCW | CCW | CCW | `M1.start_sync(M2, M3, M4)` |
| **HINTEN** (`180°`) | CW | CW | CW | CW | `M1.start_sync(M2, M3, M4)` |
| **LINKS** (`270°`) | CCW | CW | CW | CCW | `M1.start_sync(M2, M3, M4)` |
| **RECHTS** (`90°`) | CW | CCW | CCW | CW | `M1.start_sync(M2, M3, M4)` |
| **VORNE-LINKS** (`315°`) | CCW | Stopp | Stopp | CCW | Diagonale `(M1, M4)` |
| **VORNE-RECHTS** (`45°`) | Stopp | CCW | CCW | Stopp | Diagonale `(M2, M3)` |
| **HINTEN-LINKS** (`225°`) | Stopp | CW | CW | Stopp | Diagonale `(M2, M3)` |
| **HINTEN-RECHTS** (`135°`) | CW | Stopp | Stopp | CW | Diagonale `(M1, M4)` |
| **DREHEN RECHTS** | CCW | CW | CCW | CW | `M1.start_sync(M2, M3, M4)` |
| **DREHEN LINKS** | CW | CCW | CW | CCW | `M1.start_sync(M2, M3, M4)` |
| **STOPP** | Stopp | Stopp | Stopp | Stopp | `M1.stop_sync(M2, M3, M4)` |

*(Über die Touch-Schaltfläche **„Dreh: L/R“** oben rechts lässt sich die Drehrichtung bei Bedarf invertieren.)*

---

## 2. Bluetooth-Steuerung & 8-Zonen Hindernisschutz

Der 360°-Scan des LiDARs wird in **8 Sektoren zu je 45°** aufgeteilt:

```text
              VORNE (0°)
                 [0]
       [7]                 [1]
   V-LINKS            V-RECHTS
        │                  │
LINKS [6] ─── ROBOTER ─── [2] RECHTS
        │                  │
   H-LINKS            H-RECHTS
       [5]                 [3]
                 [4]
             HINTEN (180°)
```

### Steuerung (25 Hz Regelschleife)
* **Bluetooth-Eingabe:** Liest die blaue fischertechnik Bluetooth-Fernsteuerung bzw. die BT Control App über die ESP32 BLE-zu-I²C-Bridge (`EXT1`/`EXT2`, Bus `3`, Adresse `0x42`) oder `/dev/input/js0`.
* **Rechter Joystick (Links/Rechts):** Dreht den Roboter proportional um die eigene Achse.
* **Linker Joystick (360° → 8 Sektoren):** Bestimmt Fahrtrichtung (`0..7`) und Soll-Geschwindigkeit (`MIN_SPEED = 160` bis `MAX_SPEED = 512`, `DEADZONE = 0.16`).
* **Bremsrampe (`30 cm → 18 cm`):** Befindet sich im gewählten Fahrsektor ein Hindernis zwischen `SLOW_DIST_MM = 300` (`30 cm`, gelbe Zone) und `STOP_DIST_MM = 180` (`18 cm`), wird das Motortempo linear heruntergeregelt.
* **Kollisionsstopp (`<= 18 cm`):** Sinkt der Abstand im gewählten Sektor auf `<= 18 cm` (rote Zone) oder liegen keine aktuellen LiDAR-Daten vor, bleiben alle Motoren sofort stehen. Erst ab `> RELEASE_DIST_MM = 185` (`18,5 cm` Hysterese) wird die Richtung wieder freigegeben; alle freien Richtungen bleiben jederzeit fahrbar.
