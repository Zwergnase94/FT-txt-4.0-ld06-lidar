#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni 8-Zonen App fuer den fischertechnik TXT 4.0 Controller.

Steuert einen 4-Rad Omniwheel-Roboter (M1-M4) per Bluetooth-Fernbedienung
(ESP32 BLE-zu-I2C Bridge 0x42 oder /dev/input/js0) mit LD06/YDLIDAR Hindernis-Schutz:
  - Linker Joystick (alle 8 Richtungen: V, VR, R, HR, H, HL, L, VL):
    Faehrt in die gewaehlte Richtung, reduziert ab 30 cm (300 mm) schrittweise
    die Geschwindigkeit bis auf 18 cm (180 mm) und bleibt bei <= 18 cm komplett stehen.
  - Rechter Joystick (Links / Rechts):
    Dreht den Roboter auf der Stelle um die eigene Achse.
  - Touch-Oberflaeche (240x230 QML Canvas):
    8-Zonen Sektor-Radar mit 18 cm Stopp-Ring, 8 Distanz-Karten und Live-Status.
"""

import atexit
import math
import os
import signal
import sys
import threading
import time

ws_dir = os.path.dirname(os.path.abspath(__file__))
if ws_dir not in sys.path:
    sys.path.insert(0, ws_dir)

try:
    from lib.display import display
except Exception:
    display = None

from lib import omni_drive
from lib.ft_bt_remote import DualJoystickReader
from ld06 import LD06

# Sicherheits- & Bremsabstaende:
# Ab 30 cm (300 mm) wird die Geschwindigkeit schrittweise reduziert,
# bei <= 18 cm (180 mm) wird komplett gestoppt!
STOP_DIST_MM = 180       # 18.0 cm Stopp-Schwelle
RELEASE_DIST_MM = 185    # 18.5 cm Freigabe-Hysterese gegen Ruckeln an der Stopp-Grenze
SLOW_DIST_MM = 300       # 30.0 cm Beginn der schrittweisen Geschwindigkeitsreduzierung

# Motor- & Joystick-Parameter
MAX_SPEED = 512
MIN_SPEED = 160
DEADZONE = 0.16          # 16 % Joystick-Totzone

SECTOR_NAMES = [
    ('Vorne', '0°'),
    ('V-Rechts', '45°'),
    ('Rechts', '90°'),
    ('H-Rechts', '135°'),
    ('Hinten', '180°'),
    ('H-Links', '225°'),
    ('Links', '270°'),
    ('V-Links', '315°'),
]
DIR_LABELS = ['V', 'VR', 'R', 'HR', 'H', 'HL', 'L', 'VL']

# 4-Rad Omniwheel Kinematik (M1..M4 Vorzeichen fuer Sektor 0..7):
# +1 = CCW (Vorwaerts), -1 = CW (Rueckwaerts), 0 = Stopp
# Diagonale 1: (M1, M4), Diagonale 2: (M2, M3)
SECTOR_MOTOR_SIGNS = [
    (+1, +1, +1, +1),  # 0: Vorne (0°)
    ( 0, +1, +1,  0),  # 1: V-Rechts (45°)
    (-1, +1, +1, -1),  # 2: Rechts (90°)
    (-1,  0,  0, -1),  # 3: H-Rechts (135°)
    (-1, -1, -1, -1),  # 4: Hinten (180°)
    ( 0, -1, -1,  0),  # 5: H-Links (225°)
    (+1, -1, -1, +1),  # 6: Links (270°)
    (+1,  0,  0, +1),  # 7: V-Links (315°)
]

# Drehung um die eigene Achse (Linke Seite M1/M3 gegen Rechte Seite M2/M4):
ROTATE_RIGHT_SIGNS = (+1, -1, +1, -1)  # Rechts drehen (im Uhrzeigersinn)
ROTATE_LEFT_SIGNS  = (-1, +1, -1, +1)  # Links drehen (gegen den Uhrzeigersinn)


class LidarOmniController:
    """
    Hauptsteuerung der Omni 8-Zonen App fuer den TXT 4.0:
    Kombiniert den 8-Zonen LiDAR-Scanner mit der 8-Wege Bluetooth-Steuerung (Linker Stick),
    der 30->18 cm Bremsrampe mit Kollisionsstopp und der Drehung um die eigene Achse (Rechter Stick).
    """

    def __init__(self, disp=None, joy=None, start_worker=True):
        self.display = disp if disp is not None else display
        self.running = True

        self.lidar = None
        self.pts_per_sec = 0
        self.pts_counter = 0
        self.pts_timer_t0 = time.time()
        self.last_any_pts_time = 0.0

        # 8 Sektor-Slots (0 Speicherallokation im LiDAR-Thread)
        self.sec_min = [99999] * 8
        self.sec_sum = [0] * 8
        self.sec_cnt = [0] * 8
        self.sec_time = [0.0] * 8
        self.last_display_min = [0] * 8
        self.sector_lock = threading.Lock()

        # Fahr- & Motor-Zustand
        self.drive_enabled = True
        self.invert_rotation = False
        self.blocked_sectors = [False] * 8

        self.cmd_sector = None
        self.cmd_blocked = False
        self.cmd_rotate = 0
        self.status_text = 'BEREIT (>18cm frei)'
        self.status_mode = 'IDLE'
        self._last_ui_key = None

        self.joy = joy if joy is not None else DualJoystickReader(i2c_bus=3, i2c_addr=0x42)
        omni_drive.stop()

        self._thread = None
        if start_worker:
            self._thread = threading.Thread(target=self._lidar_worker, daemon=True)
            self._thread.start()

    def set_motor_speeds(self, s1, s2, s3, s4):
        omni_drive.set_motor_speeds(s1, s2, s3, s4)

    def stop_motors(self):
        omni_drive.stop()

    def toggle_drive_enabled(self, *_args):
        self.drive_enabled = not self.drive_enabled
        if not self.drive_enabled:
            self.stop_motors()
        self._last_ui_key = None

    def toggle_invert_rotation(self, *_args):
        self.invert_rotation = not self.invert_rotation
        self._last_ui_key = None

    def _get_live_sector_dist_mm(self, idx, now):
        """
        Liefert den aktuellsten Minimalabstand (in mm) fuer Sektor idx (0..7).
        Kombiniert das laufende Scan-Intervall mit dem letzten vollstaendigen Scan-Fenster.
        """
        cnt = self.sec_cnt[idx]
        cur_min = self.sec_min[idx] if cnt > 0 else 99999
        last_min = self.last_display_min[idx]
        last_t = self.sec_time[idx]

        if (now - last_t) >= 1.0:
            return 0
        if cnt > 0 and last_min > 0:
            return min(cur_min, last_min)
        if cnt > 0:
            return cur_min
        return last_min

    def _is_sector_blocked(self, idx, dist_mm):
        """Prueft mit Hysterese (18.0 cm Stopp / 18.5 cm Freigabe), ob <= 18 cm blockiert ist."""
        if dist_mm <= 0:
            self.blocked_sectors[idx] = False
            return False
        if self.blocked_sectors[idx]:
            if dist_mm > RELEASE_DIST_MM:
                self.blocked_sectors[idx] = False
        else:
            if dist_mm <= STOP_DIST_MM:
                self.blocked_sectors[idx] = True
        return self.blocked_sectors[idx]

    @staticmethod
    def _calc_motor_pwm(mag):
        """Skaliert den Joystick-Ausschlag (DEADZONE..1.0) auf Motortempo (MIN_SPEED..MAX_SPEED)."""
        norm = max(0.0, min(1.0, (mag - DEADZONE) / (1.0 - DEADZONE)))
        raw_speed = MIN_SPEED + norm * (MAX_SPEED - MIN_SPEED)
        return min(MAX_SPEED, int(round(raw_speed / 16.0) * 16))

    def on_control_tick(self, now=None):
        """25 Hz Echtzeit-Regelschleife fuer Joystick-Abfrage, 30->18 cm Bremsrampe und Motorsteuerung."""
        if now is None:
            now = time.time()
        lx, ly, rx, _ = self.joy.poll()

        if not self.drive_enabled:
            self.stop_motors()
            self.cmd_sector = None
            self.cmd_blocked = False
            self.cmd_rotate = 0
            self.status_mode = 'PAUSED'
            self.status_text = 'PAUSE (Mitte tippen)'
            return

        mag_left = min(1.0, math.hypot(lx, ly))
        abs_rx = min(1.0, abs(rx))

        # 1. Rechter Joystick: Drehung um die eigene Achse
        if abs_rx >= DEADZONE and abs_rx >= mag_left:
            rot_dir = 1 if rx > 0 else -1
            if self.invert_rotation:
                rot_dir = -rot_dir
            pwm = self._calc_motor_pwm(abs_rx)
            signs = ROTATE_RIGHT_SIGNS if rot_dir > 0 else ROTATE_LEFT_SIGNS
            self.set_motor_speeds(
                signs[0] * pwm,
                signs[1] * pwm,
                signs[2] * pwm,
                signs[3] * pwm,
            )
            self.cmd_sector = None
            self.cmd_blocked = False
            self.cmd_rotate = 1 if rx > 0 else -1
            self.status_mode = 'ROTATE'
            rot_lbl = 'Rechts' if rx > 0 else 'Links'
            self.status_text = f'DREHEN: {rot_lbl} ({int(abs_rx * 100)}%)'
            return

        self.cmd_rotate = 0

        # 2. Linker Joystick: Alle 8 Richtungen erkennen + 30->18 cm Bremsrampe & 18 cm Stopp
        if mag_left >= DEADZONE:
            angle_deg = math.degrees(math.atan2(lx, ly)) % 360.0
            sec_idx = int((angle_deg + 22.5) % 360.0 // 45.0)
            sec_name = SECTOR_NAMES[sec_idx][0]
            self.cmd_sector = sec_idx

            lidar_ready = (now - self.last_any_pts_time) < 1.5
            dist_mm = self._get_live_sector_dist_mm(sec_idx, now)

            if not lidar_ready:
                self.stop_motors()
                self.cmd_blocked = True
                self.status_mode = 'BLOCKED'
                self.status_text = 'STOPP (Warte LiDAR)'
                return

            if self._is_sector_blocked(sec_idx, dist_mm):
                # <= 18 cm (180 mm) -> komplett stehen bleiben!
                self.stop_motors()
                self.cmd_blocked = True
                self.status_mode = 'BLOCKED'
                d_cm = dist_mm * 0.1
                self.status_text = f'STOPP {sec_name} ({d_cm:.0f}cm<=18)'
                return

            # Mehr als 18 cm frei -> Fahrt in diese Richtung (ggf. ab 30 cm schrittweise gebremst)
            self.cmd_blocked = False
            joy_pwm = self._calc_motor_pwm(mag_left)

            if 0 < dist_mm <= SLOW_DIST_MM:
                # Schrittweise Geschwindigkeitsreduzierung zwischen 30 cm (300 mm) und 18 cm (180 mm)
                ratio = max(0.0, min(1.0, (dist_mm - STOP_DIST_MM) / float(SLOW_DIST_MM - STOP_DIST_MM)))
                raw_pwm = MIN_SPEED + ratio * (joy_pwm - MIN_SPEED)
                pwm = max(MIN_SPEED, min(joy_pwm, int(round(raw_pwm / 16.0) * 16)))
                self.status_mode = 'SLOW'
                d_cm = dist_mm * 0.1
                pct = int(round(pwm * 100.0 / MAX_SPEED))
                self.status_text = f'BREMSE {sec_name} ({d_cm:.0f}cm {pct}%)'
            else:
                pwm = joy_pwm
                self.status_mode = 'DRIVE'
                if dist_mm > 0:
                    self.status_text = f'{sec_name} ({dist_mm * 0.1:.0f}cm frei)'
                else:
                    self.status_text = f'FAHRT: {sec_name} ({int(mag_left * 100)}%)'

            signs = SECTOR_MOTOR_SIGNS[sec_idx]
            self.set_motor_speeds(
                signs[0] * pwm,
                signs[1] * pwm,
                signs[2] * pwm,
                signs[3] * pwm,
            )
            return

        # 3. Beide Joysticks in Mittelstellung -> Stopp
        self.stop_motors()
        self.cmd_sector = None
        self.cmd_blocked = False
        self.status_mode = 'IDLE'
        if not getattr(self.joy, 'bt_connected', True):
            if getattr(self.joy, 'bt_i2c_ok', False):
                self.status_text = 'BT Sender aus...'
            else:
                self.status_text = 'Warte BT/I2C (0x42)'
        else:
            self.status_text = 'BEREIT (>18cm frei)'

    def on_ui_tick(self, now=None):
        """5 FPS UI-Aktualisierung mit Dirty-Check ueber ein atomares MQTT-Attribut."""
        if now is None:
            now = time.time()
        dt = now - self.pts_timer_t0
        if dt >= 1.0:
            self.pts_per_sec = int(self.pts_counter / dt)
            self.pts_counter = 0
            self.pts_timer_t0 = now

        sec_dists = [0] * 8
        min_overall_d = 99999
        min_overall_short = ''

        with self.sector_lock:
            for i in range(8):
                cnt = self.sec_cnt[i]
                if cnt > 0:
                    min_d = self.sec_min[i]
                    t = self.sec_time[i]
                    self.last_display_min[i] = min_d
                else:
                    prev_t = self.sec_time[i]
                    if prev_t > 0 and (now - prev_t) < 1.0:
                        min_d = self.last_display_min[i]
                        t = prev_t
                    else:
                        min_d = 0
                        t = 0.0

                self.sec_min[i] = 99999
                self.sec_sum[i] = 0
                self.sec_cnt[i] = 0

                if min_d > 0 and (now - t) < 1.0:
                    sec_dists[i] = min_d
                    if min_d < min_overall_d:
                        min_overall_d = min_d
                        min_overall_short = DIR_LABELS[i]

        if min_overall_d < 99999:
            min_text = f'Min:{min_overall_d * 0.1:.0f}cm({min_overall_short})'
        else:
            min_text = 'Warte LiDAR'

        ui_key = (
            tuple((d // 10) if d > 0 else -1 for d in sec_dists),
            self.cmd_sector,
            self.cmd_blocked,
            self.cmd_rotate,
            self.drive_enabled,
            self.invert_rotation,
            self.status_mode,
            self.status_text,
            min_text,
        )
        if ui_key == self._last_ui_key:
            return None

        safe_status = self.status_text.replace('|', '/')
        safe_min = min_text.replace('|', '/')
        state_str = '|'.join((
            ','.join(str(int(d)) for d in sec_dists),
            '-1' if self.cmd_sector is None else str(self.cmd_sector),
            '1' if self.cmd_blocked else '0',
            str(self.cmd_rotate),
            '1' if self.drive_enabled else '0',
            '1' if self.invert_rotation else '0',
            self.status_mode,
            safe_status,
            safe_min,
        ))

        if self.display is not None:
            try:
                ok = self.display.set_attrs({'omni_canvas.stateStr': state_str})
                if ok is False:
                    return None
            except Exception:
                return None

        self._last_ui_key = ui_key
        return state_str

    def _lidar_worker(self):
        last_pts_time = time.time()
        w_min = [99999] * 8
        w_sum = [0] * 8
        w_cnt = [0] * 8
        w_time = [0.0] * 8

        while self.running:
            if self.lidar is None or not self.lidar.is_connected():
                try:
                    self.lidar = LD06('/dev/ttyUSB0')
                except Exception:
                    self.lidar = None
                if self.lidar is None or not self.lidar.is_connected():
                    time.sleep(1.0)
                    continue
                last_pts_time = time.time()

            if not self.lidar.fill_buffer(block_size=400):
                time.sleep(0.2)
                continue

            now = time.time()
            for i in range(8):
                w_min[i] = 99999
                w_sum[i] = 0
                w_cnt[i] = 0

            # Paket-Dekodierung komplett ausserhalb von sector_lock
            n = self.lidar.read_into_sectors(
                w_min, w_sum, w_cnt, w_time, now, block_size=0
            )
            if n > 0:
                with self.sector_lock:
                    for i in range(8):
                        c = w_cnt[i]
                        if c > 0:
                            if w_min[i] < self.sec_min[i]:
                                self.sec_min[i] = w_min[i]
                            self.sec_sum[i] += w_sum[i]
                            self.sec_cnt[i] += c
                            self.sec_time[i] = now
                self.pts_counter += n
                last_pts_time = now
                self.last_any_pts_time = now
                time.sleep(0.025)
            else:
                if (now - last_pts_time) > 2.0:
                    self.lidar.close()
                    time.sleep(0.5)
                    try:
                        self.lidar = LD06('/dev/ttyUSB0')
                    except Exception:
                        self.lidar = None
                    last_pts_time = now
                else:
                    time.sleep(0.025)

    def cleanup(self):
        self.running = False
        self.stop_motors()
        if self.joy is not None:
            try:
                self.joy.close()
            except Exception:
                pass
        if self.lidar is not None:
            try:
                self.lidar.close()
            except Exception:
                pass


def main():
    ctrl = LidarOmniController(start_worker=True)

    if display is not None:
        try:
            display.button_clicked('txt_btn_drive', ctrl.toggle_drive_enabled)
            display.button_clicked('txt_btn_pause', ctrl.toggle_drive_enabled)
            display.button_clicked('txt_btn_rot', ctrl.toggle_invert_rotation)
        except Exception:
            pass

    atexit.register(ctrl.cleanup)

    def _handle_sig(*_args):
        ctrl.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_sig)
    signal.signal(signal.SIGINT, _handle_sig)

    last_ui = 0.0
    try:
        while ctrl.running:
            t_start = time.time()
            ctrl.on_control_tick(t_start)
            if (t_start - last_ui) >= 0.2:
                ctrl.on_ui_tick(t_start)
                last_ui = t_start

            elapsed = time.time() - t_start
            sleep_for = 0.04 - elapsed
            if sleep_for > 0.002:
                time.sleep(sleep_for)
    finally:
        ctrl.cleanup()


if __name__ == '__main__':
    main()
