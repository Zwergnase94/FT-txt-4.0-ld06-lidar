# Hardware & Pinbelegung (TXT 4.0)

## 1. Übersicht: LDROBOT LD06 LiDAR

Der **LD06** ist ein kompakter 360°-Laserscanner nach dem Direct-Time-of-Flight-Prinzip (DToF):
* **Abtastrate:** ca. 4.500 Messpunkte pro Sekunde (4,5 kHz)
* **Rotationsfrequenz:** ca. 10–13 Hz
* **Reichweite:** 0,02 m bis 12 m
* **Schnittstelle:** UART mit **230.400 Baud** (8N1, 3,3 V Pegel)
* **Wellenlänge:** 905 nm (Laserklasse 1, augensicher)
* **Stromaufnahme:** ca. 180 mA im Betrieb (5 V DC)

---

## 2. Steckerbelegung (4-Pin JST-ZH)

Der Sensor wird über ein 4-poliges Kabel mit der beiliegenden CP2102-USB-Adapterplatine verbunden:

| Pin | Farbe (typisch) | Signal | Verbindung am USB-Adapter |
|:---:|:---:|:---:|:---|
| **1** | Rot | **VCC (+5 V)** | `5V` (4,5 V – 5,5 V) |
| **2** | Gelb | **PWM** | *offen lassen (Standard-Drehzahl ~10 Hz)* |
| **3** | Schwarz | **GND** | `GND` |
| **4** | Weiß / Blau | **TX** | `RXD` (serieller Datenausgang des Sensors) |

> [!WARNING]
> **Steckverbindung prüfen:** Die kleinen JST-ZH-Stecker sitzen recht eng, können sich bei Zug am Kabel aber verkanten. Auf festen Sitz achten, um Wackelkontakte oder Kurzschlüsse auf der 5-V-Leitung zu vermeiden.

---

## 3. USB-Betrieb am fischertechnik TXT 4.0

Im Gegensatz zum älteren ROBOTICS TXT ist am **TXT 4.0** (Yocto Linux 5.10, Firmware 5.0.1+) keine spezielle Treiber- oder Systemanpassung nötig:

* **Integrierter Kernel-Treiber:** Das Modul `cp210x` für den Silicon Labs CP2102 USB-UART-Wandler ist ab Werk im Kernel enthalten.
* **Plug & Play:** Nach dem Einstecken an der USB-Host-Buchse steht der Sensor direkt unter `/dev/ttyUSB0` bereit und lässt sich regulär über `pyserial` mit `230400` Baud öffnen.
* **Stabile 5-V-Versorgung:** Der USB-Host-Port des TXT 4.0 fängt den kurzen Anlaufstrom des LiDAR-Motors problemlos ab; ein USB-Reset-Skript ist hier nicht erforderlich.
