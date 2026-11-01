# Omniwheels 4-Motor Holonomic Drive & Obstacle Avoidance

Dieses Dokument beschreibt die Ansteuerung des 4-Rad Omniwheel/Mecanum-Fahrwerks auf dem fischertechnik TXT 4.0 und die Implementierung des 8-Wege reaktiven Ausweichalgorithmus.

---

## 1. Hardware & Motor-Konfiguration

Das omnidirektionale Fahrwerk verwendet 4 fischertechnik Encodermotoren, die direkt an den Motorausgängen M1 bis M4 des TXT 4.0 angeschlossen sind:

```
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

### Motor-Drehrichtungen (`Motor.CCW` vs `Motor.CW`):

| Richtung | M1 | M2 | M3 | M4 | Synchronisation |
|---|---|---|---|---|---|
| **VORNE** | CCW | CCW | CCW | CCW | `M1.start_sync(M2, M3, M4)` |
| **HINTEN** | CW | CW | CW | CW | `M1.start_sync(M2, M3, M4)` |
| **LINKS** | CCW | CW | CW | CCW | `M1.start_sync(M2, M3, M4)` |
| **RECHTS** | CW | CCW | CCW | CW | `M1.start_sync(M2, M3, M4)` |
| **VORNE-LINKS** | CCW | Stopp | Stopp | CCW | Diagonal aktiv (M1, M4) |
| **VORNE-RECHTS** | Stopp | CCW | CCW | Stopp | Diagonal aktiv (M2, M3) |
| **HINTEN-LINKS** | Stopp | CW | CW | Stopp | Diagonal aktiv (M2, M3) |
| **HINTEN-RECHTS** | CW | Stopp | Stopp | CW | Diagonal aktiv (M1, M4) |
| **STOPP** | Stopp | Stopp | Stopp | Stopp | `M1.stop_sync(M2, M3, M4)` |

---

## 2. Der 8-Wege Ausweich-Algorithmus

Das LiDAR-Modul sammelt kontinuierlich 360°-Scans. Das Sichtfeld wird in **8 gleich große Sektoren zu je 45°** unterteilt:

```
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

### Reaktionslogik:
1. **Gefahr erkennen:** Unterschreitet der gemessene Abstand in einem Sektor den Schwellenwert von `TRIGGER_DIST = 20.0 cm`, wird dieser Sektor als aktive Bedrohung markiert.
2. **Fluchtweg prüfen:** Das System liest den Abstand im exakt gegenüberliegenden Sektor (`OPPOSITE_MAP`).
   - Wenn der Fluchtweg $> 22.0\text{ cm}$ frei ist, setzt sich der Roboter sofort in die Fluchtrichtung in Bewegung.
   - Wenn auch der Fluchtweg blockiert ist, stoppt der Roboter sofort aus Sicherheitsgründen.
3. **Hysterese & Entwarnung:**
   - Sobald das auslösende Hindernis wieder mehr als `RELEASE_DIST = 25.0 cm` entfernt ist, wird das Manöver beendet und der Roboter bremst sanft ab.
   - Diese Hysterese von 5 cm verhindert nervöses Ruckeln an der Erkennungsgrenze.
