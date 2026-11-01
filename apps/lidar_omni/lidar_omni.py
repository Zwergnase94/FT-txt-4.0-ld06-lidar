#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LD06 LiDAR + Omniwheels 8-Way Reactive Obstacle Avoidance App for TXT 4.0.
Displays live circular radar on the internal display and dodges obstacles automatically.
Features multi-point outlier rejection and confidence filtering for rock-solid stability.
"""

import os
import sys
import time

ws_dir = os.path.dirname(os.path.abspath(__file__))
if ws_dir not in sys.path:
    sys.path.insert(0, ws_dir)

from lib.display import display
from lib import omni_drive
from ld06 import LD06

TRIGGER_DIST = 20.0       # Hindernis naeher als 20cm loest Ausweichen aus
RELEASE_DIST = 25.0       # Ausweichen stoppt erst bei mehr als 25cm (Hysterese)
CLEAR_ESCAPE_MIN = 22.0   # Fluchtweg muss mindestens 22cm frei sein
SPEED = 280               # Sichere, moderate Geschwindigkeit

driving_enabled = False
current_escape_dir = "STOP"
active_threat_sector = None
lidar_instance = None

def on_txt_btn_drive_clicked(event):
    global driving_enabled
    driving_enabled = not driving_enabled
    if driving_enabled:
        display.set_attr("txt_btn_drive.text", "Fahren: AN")
    else:
        display.set_attr("txt_btn_drive.text", "Fahren: AUS")
        omni_drive.stop()

def on_txt_btn_exit_clicked(event):
    global lidar_instance
    omni_drive.stop()
    if lidar_instance:
        try:
            lidar_instance.close()
        except Exception:
            pass
    try:
        display.stop()
    except Exception:
        pass
    os._exit(0)

try:
    display.button_clicked("txt_btn_drive", on_txt_btn_drive_clicked)
    display.button_clicked("txt_btn_exit", on_txt_btn_exit_clicked)
except Exception:
    pass

# Opposite sector mapping for dodging: sector_index -> (escape_dir_name, escape_sector_index)
OPPOSITE_MAP = {
    0: ("HINTEN", 4),          # V  -> Flucht H
    1: ("HINTEN-LINKS", 5),    # VR -> Flucht HL
    2: ("LINKS", 6),           # R  -> Flucht L
    3: ("VORNE-LINKS", 7),     # HR -> Flucht VL
    4: ("VORNE", 0),           # H  -> Flucht V
    5: ("VORNE-RECHTS", 1),    # HL -> Flucht VR
    6: ("RECHTS", 2),          # L  -> Flucht R
    7: ("HINTEN-RECHTS", 3),   # VL -> Flucht HR
}

def main():
    global lidar_instance, driving_enabled, current_escape_dir, active_threat_sector

    display.set_attr("txt_info.text", "LiDAR Verbinden...")

    while lidar_instance is None or not lidar_instance.is_connected():
        try:
            lidar_instance = LD06("/dev/ttyUSB0")
            if lidar_instance.is_connected():
                break
        except Exception:
            pass
        display.set_attr("txt_info.text", "Warte auf USB...")
        time.sleep(0.5)

    recent_scan = []
    last_draw = time.time()
    last_rate_time = time.time()
    pts_count = 0
    current_rate = 0
    sec_names = ["V", "VR", "R", "HR", "H", "HL", "L", "VL"]

    while True:
        try:
            pts = lidar_instance.read_points(block_size=400)
            if pts:
                pts_count += len(pts)
                recent_scan.extend(pts)
                if len(recent_scan) > 450:
                    del recent_scan[:-350]

            now = time.time()
            if now - last_rate_time >= 1.0:
                current_rate = int(pts_count / (now - last_rate_time))
                pts_count = 0
                last_rate_time = now

            # 1. 8 Sektoren mit Ausreisser-Filterung auswerten
            sec_pts = [[] for _ in range(8)]
            for angle, dist, conf in recent_scan:
                s_idx = int((angle + 22.5) % 360 / 45)
                sec_pts[s_idx].append(dist / 10.0)

            sec_mins = [9999.0] * 8
            overall_min = 9999.0
            min_sec_idx = 0

            for s_idx in range(8):
                points = sec_pts[s_idx]
                if points:
                    points.sort()
                    # 2-Punkte-Robustheit: 2. kleinster Wert filtert vereinzelte Rauschpunkte heraus
                    robust_dist = points[1] if len(points) >= 2 else points[0]
                    sec_mins[s_idx] = robust_dist
                    if robust_dist < overall_min:
                        overall_min = robust_dist
                        min_sec_idx = s_idx

            # 2. Ausweich-Zustandsmaschine
            desired_move = "STOP"
            status_msg = ""

            if not driving_enabled:
                omni_drive.stop()
                current_escape_dir = "STOP"
                active_threat_sector = None
                if overall_min < 9000:
                    status_msg = "PAUSE (Min: {:.0f}cm {})".format(overall_min, sec_names[min_sec_idx])
                else:
                    status_msg = "PAUSE (Frei) | {:d} P/s".format(current_rate)
            else:
                if active_threat_sector is not None:
                    # Pruefe ob Bedrohung geloest (> 25cm)
                    threat_dist = sec_mins[active_threat_sector]
                    if threat_dist > RELEASE_DIST:
                        active_threat_sector = None
                        current_escape_dir = "STOP"
                        omni_drive.stop()
                    else:
                        esc_dir, esc_sec = OPPOSITE_MAP[active_threat_sector]
                        if sec_mins[esc_sec] > CLEAR_ESCAPE_MIN:
                            desired_move = esc_dir
                            status_msg = "AUSWEICHEN: {} ({:.0f}cm)".format(esc_dir, threat_dist)
                        else:
                            desired_move = "STOP"
                            status_msg = "BLOCKIERT: Weg ({}) belegt!".format(sec_names[esc_sec])
                else:
                    # Nicht im Ausweichen -> Pruefe ob Hindernis < 20cm
                    if overall_min < TRIGGER_DIST:
                        active_threat_sector = min_sec_idx
                        esc_dir, esc_sec = OPPOSITE_MAP[min_sec_idx]
                        if sec_mins[esc_sec] > CLEAR_ESCAPE_MIN:
                            desired_move = esc_dir
                            status_msg = "AUSWEICHEN: {} ({:.0f}cm)".format(esc_dir, overall_min)
                        else:
                            desired_move = "STOP"
                            status_msg = "BLOCKIERT: Weg ({}) belegt!".format(sec_names[esc_sec])
                    else:
                        desired_move = "STOP"
                        if overall_min < 9000:
                            status_msg = "BEREIT | Min: {:.0f}cm ({})".format(overall_min, sec_names[min_sec_idx])
                        else:
                            status_msg = "BEREIT | {:d} P/s".format(current_rate)

                # Fahrbewegung ausfuehren
                if desired_move != current_escape_dir:
                    current_escape_dir = desired_move
                    omni_drive.move_dir(desired_move, v=SPEED)

            # 3. Display aktualisieren (ca. 3.3 FPS = alle 300ms)
            if now - last_draw >= 0.3:
                last_draw = now

                total_pts = len(recent_scan)
                step = max(1, total_pts // 60) if total_pts > 0 else 1
                point_strs = []

                for i in range(0, total_pts):
                    if i % step == 0:
                        a, d, c = recent_scan[i]
                        point_strs.append("{:.1f},{:.0f}".format(a, d / 10.0))

                raw_data = ";".join(point_strs)

                # Ein einziger atomarer MQTT-Aufruf fuer alle UI-Elemente
                display.set_attrs({
                    "radar_canvas.rawPoints": raw_data,
                    "radar_canvas.motionDir": current_escape_dir,
                    "txt_info.text": status_msg
                })
            else:
                time.sleep(0.01)

        except Exception as e:
            time.sleep(0.05)

if __name__ == "__main__":
    main()
