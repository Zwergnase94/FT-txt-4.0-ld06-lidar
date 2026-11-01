#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LD06 LiDAR Circular Radar App for TXT 4.0.
Displays live circular radar with zoom toggle on the internal capacitive touchscreen.
Includes confidence filtering and robust minimum distance calculation.
"""

import os
import sys
import time

ws_dir = os.path.dirname(os.path.abspath(__file__))
if ws_dir not in sys.path:
    sys.path.insert(0, ws_dir)

from lib.display import display
from ld06 import LD06

ZOOM_LEVELS = [100.0, 200.0, 400.0, 800.0]
zoom_idx = 1 # Start: 2.0 m
lidar_instance = None

def on_txt_btn_zoom_clicked(event):
    global zoom_idx
    zoom_idx = (zoom_idx + 1) % len(ZOOM_LEVELS)
    cur_cm = ZOOM_LEVELS[zoom_idx]
    display.set_attrs({
        "radar_canvas.maxDist": str(cur_cm),
        "txt_btn_zoom.text": "Zoom: {:.0f}m".format(cur_cm / 100.0)
    })

def on_txt_btn_exit_clicked(event):
    global lidar_instance
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
    display.button_clicked("txt_btn_zoom", on_txt_btn_zoom_clicked)
    display.button_clicked("txt_btn_exit", on_txt_btn_exit_clicked)
except Exception:
    pass

def main():
    global lidar_instance
    display.set_attr("txt_info.text", "Sensor verbinden...")

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

            # Render at ~3.3 FPS (every 300ms) for stability
            if now - last_draw >= 0.3:
                last_draw = now

                # Robust minimum calculation
                sorted_by_dist = sorted(recent_scan, key=lambda p: p[1])
                overall_min = 9999.0
                min_angle = 0

                # Use 2nd lowest point if available to avoid isolated outliers
                if len(sorted_by_dist) >= 2:
                    p = sorted_by_dist[1]
                    overall_min = p[1] / 10.0
                    min_angle = p[0]
                elif sorted_by_dist:
                    p = sorted_by_dist[0]
                    overall_min = p[1] / 10.0
                    min_angle = p[0]

                # Sample ~60 points for smooth painting
                total_pts = len(recent_scan)
                step = max(1, total_pts // 60) if total_pts > 0 else 1
                point_strs = []

                for i in range(0, total_pts):
                    if i % step == 0:
                        a, d, c = recent_scan[i]
                        point_strs.append("{:.1f},{:.0f}".format(a, d / 10.0))

                raw_data = ";".join(point_strs)

                if overall_min < 9000:
                    s_idx = int((min_angle + 22.5) % 360 / 45)
                    dir_name = sec_names[s_idx]
                    info_text = "Min: {:.0f}cm ({}) | {:d} Pkt/s".format(overall_min, dir_name, current_rate)
                else:
                    info_text = "Frei | {:d} Pkt/s".format(current_rate)

                display.set_attrs({
                    "radar_canvas.rawPoints": raw_data,
                    "txt_info.text": info_text
                })
            else:
                time.sleep(0.01)
        except Exception:
            time.sleep(0.05)

if __name__ == "__main__":
    main()
