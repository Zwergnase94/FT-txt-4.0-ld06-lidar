#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time

ws_dir = os.path.dirname(os.path.abspath(__file__))
if ws_dir not in sys.path:
    sys.path.insert(0, ws_dir)

from lib.display import display
from ld06 import LD06

def on_txt_btn_exit_clicked(event):
    try:
        display.stop()
    except Exception:
        pass
    os._exit(0)

try:
    display.button_clicked("txt_btn_exit", on_txt_btn_exit_clicked)
except Exception:
    pass

def main():
    display.set_attr("txt_status.text", "LiDAR Verbinden...")
    
    lidar = None
    while lidar is None or not lidar.is_connected():
        try:
            lidar = LD06("/dev/ttyUSB0")
            if lidar.is_connected():
                break
        except Exception:
            pass
        display.set_attr("txt_status.text", "Warte auf USB...")
        time.sleep(0.5)

    sec_names = ["V", "VR", "R", "HR", "H", "HL", "L", "VL"]
    sec_labels = ["txt_v", "txt_vr", "txt_r", "txt_hr", "txt_h", "txt_hl", "txt_l", "txt_vl"]

    recent_scan = []
    last_update = time.time()
    last_rate_time = time.time()
    pts_count = 0
    current_rate = 0

    while True:
        try:
            pts = lidar.read_points(block_size=400)
            if pts:
                pts_count += len(pts)
                recent_scan.extend(pts)
                if len(recent_scan) > 550:
                    del recent_scan[:-450]

            now = time.time()
            if now - last_rate_time >= 1.0:
                current_rate = int(pts_count / (now - last_rate_time))
                pts_count = 0
                last_rate_time = now

            if now - last_update >= 0.2: # 5 Hz Display Update
                last_update = now

                sec_mins = [9999.0] * 8
                for angle, dist, conf in recent_scan:
                    if dist > 0:
                        s_idx = int((angle + 22.5) % 360 / 45)
                        d_cm = dist / 10.0
                        if d_cm < sec_mins[s_idx]:
                            sec_mins[s_idx] = d_cm

                overall_min = 9999.0
                min_sec = ""

                for i in range(8):
                    m = sec_mins[i]
                    lbl = sec_labels[i]
                    nm = sec_names[i]
                    if m < 9000:
                        display.set_attr(lbl + ".text", "{}: {:4.1f} cm".format(nm, m))
                        if m < overall_min:
                            overall_min = m
                            min_sec = nm
                    else:
                        display.set_attr(lbl + ".text", "{}: -- cm".format(nm))

                if overall_min < 9000:
                    display.set_attr("txt_min.text", "Min: {:4.1f} cm ({})".format(overall_min, min_sec))
                    if overall_min < 30:
                        display.set_attr("txt_min.color", "#ff3366")
                    elif overall_min < 80:
                        display.set_attr("txt_min.color", "#ffcc00")
                    else:
                        display.set_attr("txt_min.color", "#00ff88")

                display.set_attr("txt_status.text", "Sensor: {:d} Pkt/s".format(current_rate))
            else:
                time.sleep(0.01)
        except Exception:
            time.sleep(0.1)

if __name__ == "__main__":
    main()
