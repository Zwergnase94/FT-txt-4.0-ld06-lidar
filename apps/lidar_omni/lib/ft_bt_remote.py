#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ft_bt_remote.py - Bluetooth- & Joystick-Treiber fuer den fischertechnik TXT 4.0

Unterstuetzt:
  1. Blaue fischertechnik Bluetooth-Fernsteuerung (BT Control Set) ueber die
     ESP32 BLE-zu-I2C-Bridge am EXT1/EXT2-Port des TXT 4.0 (I2C-Bus 3, 0x42).
  2. Linux Joystick-Device (/dev/input/js0), falls vorhanden.
"""

import os
import struct
import time

try:
    from smbus2 import SMBus, i2c_msg
    HAS_SMBUS = True
except Exception:
    SMBus = None
    i2c_msg = None
    HAS_SMBUS = False


class FtBtRemote:
    """
    Treiberklasse fuer die ESP32 BLE-zu-I2C Bridge am fischertechnik TXT 4.0.
    Standard-Bus am TXT 4.0 fuer EXT1/EXT2 ist I2C-Bus 3, Slave-Adresse 0x42.
    """

    def __init__(self, i2c_bus: int = 3, i2c_addr: int = 0x42, deadzone: int = 6):
        self.i2c_bus = i2c_bus
        self.i2c_addr = i2c_addr
        self.deadzone = deadzone

        self.i2c_ok = False
        self.connected = False
        self.channel = 0
        self.joy_left_y = 0   # M1: -100 bis +100 (+ = Vorne)
        self.joy_left_x = 0   # M2: -100 bis +100 (+ = Rechts)
        self.joy_right_y = 0  # M3: -100 bis +100 (+ = Oben)
        self.joy_right_x = 0  # M4: -100 bis +100 (+ = Rechts)

        self._bus = None
        self._last_err_time = 0.0

    def _apply_deadzone(self, val: int) -> int:
        if abs(val) < self.deadzone:
            return 0
        # Sender liefert -128 .. +127 -> sauber auf -100 .. +100 Prozent skalieren
        scaled = int(round((val / 127.0) * 100.0))
        return max(-100, min(100, scaled))

    def _read_packet(self):
        if not HAS_SMBUS:
            raise OSError("smbus2 nicht verfuegbar")
        if self._bus is None:
            self._bus = SMBus(self.i2c_bus)
        msg = i2c_msg.read(self.i2c_addr, 6)
        self._bus.i2c_rdwr(msg)
        raw = bytes(list(msg))
        return struct.unpack("<BBbbbb", raw)

    def _reset_axes(self):
        self.joy_left_y = 0
        self.joy_left_x = 0
        self.joy_right_y = 0
        self.joy_right_x = 0

    def update(self) -> bool:
        """
        Liest die 6 Status-Bytes vom ESP32 ueber I2C aus.
        Gibt True zurueck, wenn die I2C-Kommunikation erfolgreich war.
        """
        if not HAS_SMBUS:
            self.i2c_ok = False
            self.connected = False
            self._reset_axes()
            return False

        now = time.time()
        if not self.i2c_ok and (now - self._last_err_time) < 0.5:
            return False

        try:
            conn, ch, ly, lx, ry, rx = self._read_packet()
            # Falls vorher z.B. i2cdetect ausgefuehrt wurde, einmalig FIFO synchronisieren
            if conn not in (0, 1) or ch not in (0, 1):
                conn, ch, ly, lx, ry, rx = self._read_packet()

            self.i2c_ok = True
            self.connected = bool(conn == 1)
            self.channel = 1 if ch == 1 else 0

            if self.connected:
                self.joy_left_y = self._apply_deadzone(ly)
                self.joy_left_x = self._apply_deadzone(lx)
                self.joy_right_y = self._apply_deadzone(ry)
                self.joy_right_x = self._apply_deadzone(rx)
            else:
                self._reset_axes()

            return True

        except OSError:
            self._last_err_time = now
            self.i2c_ok = False
            self.connected = False
            self._reset_axes()
            self.close()
            return False

    def close(self):
        if self._bus is not None:
            try:
                self._bus.close()
            except Exception:
                pass
            self._bus = None

    @staticmethod
    def to_motor_speed(axis_value: int, max_speed: int = 512) -> int:
        return int(round((axis_value / 100.0) * max_speed))


class DualJoystickReader:
    """
    Kombiniert fuer den TXT 4.0 die blaue Bluetooth-Fernsteuerung ueber die
    ESP32 I2C-Bridge (0x42) sowie optional /dev/input/js0 (falls vorhanden).
    Liefert normierte Achsenwerte (lx, ly, rx, ry) im Bereich [-1.0 .. +1.0].
    """

    def __init__(self, i2c_bus: int = 3, i2c_addr: int = 0x42, js_dev: str = "/dev/input/js0"):
        self.remote = FtBtRemote(i2c_bus=i2c_bus, i2c_addr=i2c_addr, deadzone=6)
        self.js_dev = js_dev
        self.js_fd = None
        self.last_open_try = 0.0

        self.js_lx = 0.0
        self.js_ly = 0.0
        self.js_rx = 0.0
        self.js_ry = 0.0

        self._try_open_js()

    def _try_open_js(self):
        if self.js_fd is not None:
            return True
        now = time.time()
        if (now - self.last_open_try) < 1.0:
            return False
        self.last_open_try = now
        if not self.js_dev or not os.path.exists(self.js_dev):
            return False
        try:
            self.js_fd = os.open(self.js_dev, os.O_RDONLY | os.O_NONBLOCK)
            return True
        except Exception:
            self.js_fd = None
            return False

    @staticmethod
    def _norm_js_axis(val: int, invert: bool = False) -> float:
        if invert:
            val = -val
        res = (val / 32767.0) if val < 0 else (val / 32512.0)
        return max(-1.0, min(1.0, res))

    def _poll_js(self):
        if self.js_fd is None:
            self._try_open_js()
        if self.js_fd is None:
            return

        while True:
            try:
                buf = os.read(self.js_fd, 8)
                if not buf or len(buf) < 8:
                    break
                _, val, evt_type, axis_num = struct.unpack("IhBB", buf)
                if evt_type & 0x02:  # JS_EVENT_AXIS
                    if axis_num == 0:
                        self.js_lx = self._norm_js_axis(val, invert=False)
                    elif axis_num == 1:
                        self.js_ly = self._norm_js_axis(val, invert=True)
                    elif axis_num == 2:
                        self.js_rx = self._norm_js_axis(val, invert=False)
                    elif axis_num == 3:
                        self.js_ry = self._norm_js_axis(val, invert=True)
            except BlockingIOError:
                break
            except OSError:
                try:
                    os.close(self.js_fd)
                except Exception:
                    pass
                self.js_fd = None
                self.js_lx = 0.0
                self.js_ly = 0.0
                self.js_rx = 0.0
                self.js_ry = 0.0
                break

    @property
    def bt_i2c_ok(self) -> bool:
        return self.remote.i2c_ok

    @property
    def bt_connected(self) -> bool:
        return self.remote.connected or (self.js_fd is not None)

    @property
    def channel(self) -> int:
        return self.remote.channel

    def poll(self):
        """
        Gibt (lx, ly, rx, ry) im Bereich [-1.0 .. +1.0] zurueck:
          lx: Links (-1.0) .. Rechts (+1.0)
          ly: Hinten (-1.0) .. Vorne (+1.0)
          rx: Links drehen (-1.0) .. Rechts drehen (+1.0)
          ry: Unten (-1.0) .. Oben (+1.0)
        """
        self.remote.update()
        self._poll_js()

        bt_lx = self.remote.joy_left_x / 100.0
        bt_ly = self.remote.joy_left_y / 100.0
        bt_rx = self.remote.joy_right_x / 100.0
        bt_ry = self.remote.joy_right_y / 100.0

        lx = bt_lx if abs(bt_lx) >= abs(self.js_lx) else self.js_lx
        ly = bt_ly if abs(bt_ly) >= abs(self.js_ly) else self.js_ly
        rx = bt_rx if abs(bt_rx) >= abs(self.js_rx) else self.js_rx
        ry = bt_ry if abs(bt_ry) >= abs(self.js_ry) else self.js_ry
        return lx, ly, rx, ry

    def close(self):
        self.remote.close()
        if self.js_fd is not None:
            try:
                os.close(self.js_fd)
            except Exception:
                pass
            self.js_fd = None
