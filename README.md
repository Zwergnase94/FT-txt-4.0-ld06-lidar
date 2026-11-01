# LD06 DToF LiDAR für fischertechnik TXT 4.0 (Firmware 5.0.1+)

[![Release](https://img.shields.io/badge/Release-v1.0.0-brightgreen.svg)](https://github.com/Zwergnase94/FT-txt-4.0-ld06-lidar/releases)
[![TXT 4.0](https://img.shields.io/badge/Controller-TXT%204.0%20(Firmware%205.0.1+)-blue.svg)](https://www.fischertechnik.de)
[![OS](https://img.shields.io/badge/OS-Linux%205.10%20Yocto-green.svg)](https://www.yoctoproject.org/)
[![Python](https://img.shields.io/badge/Python-3.12.x-yellow.svg)](https://www.python.org/)
[![UI](https://img.shields.io/badge/GUI-QtQuick%202.2%20%2F%20QML-orange.svg)](https://www.qt.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

Dieses Repository enthält den **stabilen Python-Treiber**, **vier native Touchscreen-Apps** sowie die vollständige **8-Wege autonome Ausweich-Steuerung für Omniwheel-/Mecanum-Roboter** mit dem **LD06 DToF LiDAR** auf dem **fischertechnik TXT 4.0 Controller**.

---

## 📑 Inhaltsverzeichnis

- [Hardware-Übersicht: LD06 DToF LiDAR](#-hardware-übersicht-ld06-dtof-lidar)
- [Die 4 enthaltenen TXT 4.0 Apps](#-die-4-enthaltenen-txt-40-apps)
  - [1. lidar_omni (Flaggschiff: 8-Wege Omniwheels Ausweichen)](#1-lidar_omni-flaggschiff-8-wege-omniwheels-ausweichen)
  - [2. lidar_radar (360° Touch-Radar mit Zoom)](#2-lidar_radar-360-touch-radar-mit-zoom)
  - [3. lidar_8zones (8-Sektoren Hindernis-Dashboard)](#3-lidar_8zones-8-sektoren-hindernis-dashboard)
  - [4. lidar_web (Browser-Livestream via HTTP / WebSocket)](#4-lidar_web-browser-livestream-via-http--websocket)
- [Wichtige technische Erkenntnisse & System-Fixes](#-wichtige-technische-erkenntnisse--system-fixes)
  - [1. Display-Viewport: 240 x 230 Pixel Begrenzung](#1-display-viewport-240-x-230-pixel-begrenzung)
  - [2. ftgui MQTT Race Condition & Screen-Freeze Fix](#2-ftgui-mqtt-race-condition--screen-freeze-fix)
  - [3. DToF Sensor-Stabilität & Ausreißer-Filter (6cm Phantomwerte)](#3-dtof-sensor-stabilität--ausreißer-filter-6cm-phantomwerte)
- [Omniwheels 4-Motoren Kinematik](#-omniwheels-4-motoren-kinematik)
- [Verzeichnisstruktur](#-verzeichnisstruktur)
- [Installation & Schnelleinstieg](#-installation--schnelleinstieg)

---

## 📡 Hardware-Übersicht: LD06 DToF LiDAR

Der **LD06** (LDROBOT) ist ein extrem kompakter, 360°-Laser-Distanzsensor nach dem Direct Time-of-Flight (DToF) Messprinzip:
* **Messfrequenz:** ca. 4.500 Messpunkte pro Sekunde (4,5 kHz)
* **Scanrate:** ca. 10–13 Hz (360°-Umdrehungen pro Sekunde)
* **Messbereich:** 0,02 m bis 12 m
* **Winkelauflösung:** ca. 0,8° bis 1,0°
* **Schnittstelle:** Seriell (UART, 230.400 Baud) über CP2102-USB-Adapter an der USB-Host-Buchse des TXT 4.0 (`/dev/ttyUSB0`). Der Kernel-Treiber `cp210x` ist in Firmware 5.0.1+ bereits nativ integriert.

---

## 🚀 Die 4 enthaltenen TXT 4.0 Apps

Alle Apps sind als vollwertige fischertechnik-Workspaces für `/opt/ft/workspaces/` aufgebaut und lassen sich direkt über das Menü des TXT 4.0 Touchscreens bedienen.

### 1. `lidar_omni` (Flaggschiff: 8-Wege Omniwheels Ausweichen)
Autonome Navigation und Hindernisausweich-App für 4-Rad Omniwheel/Mecanum-Roboter:
* **Radar-Canvas auf dem Touchscreen:** Zeigt in Echtzeit die Punktwolke, eine rote **20 cm Sicherheitszone** und einen dynamischen gelben Bewegungsvektor-Pfeil.
* **8-Wege Holonomes Ausweichen:** Nähert sich ein Objekt in einem der 8 Sektoren auf unter **20 cm**, weicht der Roboter sofort ohne vorherige Drehung in die entgegengesetzte Richtung aus.
* **Fluchtweg-Prüfung:** Weicht nur aus, wenn in Fluchtrichtung mindestens **22 cm** frei sind; andernfalls stoppt das Fahrzeug mit Sicherheitsmeldung `BLOCKIERT`.
* **Hysterese-Regelung:** Beendet das Ausweichmanöver erst wieder, wenn der Abstand $> 25\text{ cm}$ beträgt (verhindert Oszillieren).
* **Touch-Bedienelemente:**
  * Button `Fahren: AUS / AN`: Sicherheits-Umschalter für die Motoren (startet standardmäßig in Pause, um die Messwerte in Ruhe prüfen zu können).
  * Button `Beenden`: Schließt die App sauber und stoppt alle Motoren synchron.

### 2. `lidar_radar` (360° Touch-Radar mit Zoom)
* Flüssiges QtQuick Canvas-Rendering (~3,3 FPS, dezimierte Punktwolke).
* **Zoom-Stufen:** Umschaltbar per Button zwischen $1,0\text{ m}$, $2,0\text{ m}$, $4,0\text{ m}$ und $8,0\text{ m}$.
* Farbige Distanzringe und Anzeige des nächsten Hindernisses mit Sektorbezeichnung (`Min: 42cm (VL)`).

### 3. `lidar_8zones` (8-Sektoren Hindernis-Dashboard)
* Balkenanzeige für 8 Richtungen (Vorne, VR, R, HR, Hinten, HL, L, VL) mit dynamischer Farbumschaltung (Grün > 60cm, Gelb 30-60cm, Rot < 30cm).

### 4. `lidar_web` (Browser-Livestream via HTTP / WebSocket)
* Integrierter Python-Webserver mit WebSocket-Streaming.
* Zeigt die 360°-Radaranzeige live in jedem Webbrowser (PC, Tablet, Smartphone) im lokalen WLAN an.

---

## 💡 Wichtige technische Erkenntnisse & System-Fixes

Ausführliche technische Berichte findest du in [`docs/TXT40_INTEGRATION_AND_INSIGHTS.md`](docs/TXT40_INTEGRATION_AND_INSIGHTS.md).

### 1. Display-Viewport: 240 x 230 Pixel Begrenzung
* **Physisches Display:** $240 \times 320$ Pixel.
* **Nutzbarer App-Viewport:** $240 \times 230$ Pixel (oberhalb von $y=230$ liegt die System-Menüleiste von `qtmenu`).
* **Lösung:** Alle Steuerelemente und Buttons müssen innerhalb von $y \le 225$ platziert werden, da sie sonst abgeschnitten werden.

### 2. `ftgui` MQTT Race Condition & Screen-Freeze Fix
* **Problem:** Nach ca. 10 Sekunden fror das Display ein, während das Python-Programm im Hintergrund weiterlief.
* **Ursache:** In `/usr/lib/python3.12/site-packages/ftgui.py` sendet `run_queue()` über localhost MQTT. Die Bestätigung (`on_publish`) traf schneller ein als die Zuweisung `self.setter_request = ...` im Hauptthread vollendet war. Dadurch blieb `self.setter_request` dauerhaft belegt und blockierte alle zukünftigen Display-Updates.
* **Lösung ([`lib/display.py`](apps/lidar_omni/lib/display.py)):** 
  - Atomare Verriegelung mit `setter_lock`.
  - Watchdog mit 150 ms Timeout zur automatischen Entriegelung.
  - Umstellung auf QoS 1.
  - Neue Methode `display.set_attrs({...})`, die alle UI-Updates einer Iteration in **einem einzigen** MQTT-Telegramm bündelt (Buslast um 66 % reduziert).

### 3. DToF Sensor-Stabilität & Ausreißer-Filter (6cm Phantomwerte)
* **Problem:** Trotz Stillstand sprangen die Minimalwerte gelegentlich extrem (z. B. von $43\text{ cm}$ auf $6\text{ cm}$).
* **Ursache:** Ferne Kanten oder Streulicht erzeugen vereinzelt Photonenpeaks mit sehr geringer Signalstärke (`conf: 22..25`), die als $62\text{ mm}$ fehlinterpretiert wurden. Reale Hindernisse haben eine Signalstärke von **150 bis 245**.
* **Lösung ([`driver/ld06.py`](driver/ld06.py)):**
  1. **CRC-8 Validierung:** Jedes 47-Byte-Paket wird per Hardware-Tabelle geprüft.
  2. **Signalstärken-Filter:** Punkte mit `conf < 100` oder `dist < 30 mm` werden verworfen.
  3. **2-Punkte-Bestätigung:** In jedem 45°-Sektor wird der 2.-kleinste Messwert verwendet. Einzelne Ausreißer haben dadurch mathematisch keine Auswirkung mehr.
  * *Testergebnis:* Über 12.900 aufeinanderfolgende Messpunkte mit **0 Ausreißern**.

---

## 🚗 Omniwheels 4-Motoren Kinematik

| Ausweich-Richtung | Auslösender Sektor | Motor M1 (VL) | Motor M2 (VR) | Motor M3 (HR) | Motor M4 (HL) |
|---|---|---|---|---|---|
| **HINTEN** | Vorne (V) | CW | CW | CW | CW |
| **HINTEN-LINKS** | Vorne-Rechts (VR) | Stopp | CW | CW | Stopp |
| **LINKS** | Rechts (R) | CCW | CW | CW | CCW |
| **VORNE-LINKS** | Hinten-Rechts (HR) | CCW | Stopp | Stopp | CCW |
| **VORNE** | Hinten (H) | CCW | CCW | CCW | CCW |
| **VORNE-RECHTS** | Hinten-Links (HL) | Stopp | CCW | CCW | Stopp |
| **RECHTS** | Links (L) | CW | CCW | CCW | CW |
| **HINTEN-RECHTS** | Vorne-Links (VL) | CW | Stopp | Stopp | CW |

Details siehe [`docs/OMNIWHEEL_AVOIDANCE.md`](docs/OMNIWHEEL_AVOIDANCE.md).

---

## 📂 Verzeichnisstruktur

```
FT-txt-4.0-ld06-lidar/
├── README.md                              <- Hauptdokumentation
├── LICENSE                                <- MIT Lizenz
├── driver/
│   └── ld06.py                            <- Robuster LD06 Treiber (CRC8 + Confidence-Filter)
├── docs/
│   ├── TXT40_INTEGRATION_AND_INSIGHTS.md  <- Architektur-, Display- & Filteranalyse
│   └── OMNIWHEEL_AVOIDANCE.md             <- 8-Wege Holonomes Fahrwerk & Kinematik
└── apps/
    ├── lidar_omni/                        <- 8-Wege Omniwheels Ausweich-App
    │   ├── lidar_omni.py
    │   ├── ld06.py
    │   ├── .project.json
    │   └── lib/
    │       ├── display.py                 <- Thread-sicherer ftgui-Patch (set_attrs)
    │       ├── display.qml                <- Radar Canvas & Steuerung
    │       └── omni_drive.py              <- 4-Motoren Kinematik-Treiber
    ├── lidar_radar/                       <- 360° Zirkular-Radar App
    ├── lidar_8zones/                      <- 8-Sektoren Dashboard
    └── lidar_web/                         <- Web-Streaming Server
```

---

## 🚀 Installation & Schnelleinstieg

### Auf den TXT 4.0 übertragen:
Kopiere die gewünschte App direkt in das Workspace-Verzeichnis des Controllers:

```bash
# Beispiel: lidar_omni übertragen
scp -r apps/lidar_omni ft@<TXT_IP>:/opt/ft/workspaces/
```

Nach dem Kopieren erscheint die App automatisch im Touchscreen-Menü des TXT 4.0 und kann mit einem Fingertipp gestartet werden.

---

## 📄 Lizenz
Dieses Projekt ist unter der **MIT-Lizenz** lizenziert – siehe [LICENSE](LICENSE).
