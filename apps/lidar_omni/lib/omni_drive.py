#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omniwheels 4-Motor Drive Module for fischertechnik TXT 4.0.
Supports 8-directional holonomic motion, in-place rotation, synchronized encoder speeds,
and emergency stop.
"""

try:
    import fischertechnik.factories as txt_factory
    from fischertechnik.controller.Motor import Motor

    txt_factory.init()
    txt_factory.init_motor_factory()
    txt_factory.init_counter_factory()

    TXT_M = txt_factory.controller_factory.create_graphical_controller()
    M1 = txt_factory.motor_factory.create_encodermotor(TXT_M, 1)
    M2 = txt_factory.motor_factory.create_encodermotor(TXT_M, 2)
    M3 = txt_factory.motor_factory.create_encodermotor(TXT_M, 3)
    M4 = txt_factory.motor_factory.create_encodermotor(TXT_M, 4)
    txt_factory.initialized()
    MOTORS = (M1, M2, M3, M4)
    HAS_HARDWARE = True
except Exception:
    TXT_M = None
    M1 = M2 = M3 = M4 = None
    MOTORS = ()
    Motor = None
    HAS_HARDWARE = False

CURRENT_MOTION = "STOP"
LAST_SPEEDS = (0, 0, 0, 0)


def _clamp_speed(val: int) -> int:
    val = int(val)
    if val > 512:
        return 512
    if val < -512:
        return -512
    return val


def set_motor_speeds(s1: int, s2: int, s3: int, s4: int):
    """
    Setzt die Geschwindigkeiten aller 4 Encodermotoren (M1..M4) im Bereich [-512 .. +512].
    + = Motor.CCW (Vorwaerts), - = Motor.CW (Rueckwaerts), 0 = Stopp.
    Nutzt Encoder-Synchronisation (start_sync / stop_sync) und vermeidet redundante Aufrufe.
    """
    global LAST_SPEEDS
    target = (_clamp_speed(s1), _clamp_speed(s2), _clamp_speed(s3), _clamp_speed(s4))
    if target == LAST_SPEEDS:
        return
    LAST_SPEEDS = target

    if not HAS_HARDWARE:
        return

    if target == (0, 0, 0, 0):
        try:
            M1.stop_sync(M2, M3, M4)
        except Exception:
            for m in MOTORS:
                try:
                    m.stop()
                except Exception:
                    pass
        return

    t1, t2, t3, t4 = target
    try:
        if t1 != 0 and t2 != 0 and t3 != 0 and t4 != 0:
            for m, s in zip(MOTORS, target):
                m.set_speed(abs(s), Motor.CCW if s > 0 else Motor.CW)
            M1.start_sync(M2, M3, M4)
        elif t1 != 0 and t4 != 0 and t2 == 0 and t3 == 0:
            M2.stop_sync(M3)
            M1.set_speed(abs(t1), Motor.CCW if t1 > 0 else Motor.CW)
            M4.set_speed(abs(t4), Motor.CCW if t4 > 0 else Motor.CW)
            M1.start_sync(M4)
        elif t2 != 0 and t3 != 0 and t1 == 0 and t4 == 0:
            M1.stop_sync(M4)
            M2.set_speed(abs(t2), Motor.CCW if t2 > 0 else Motor.CW)
            M3.set_speed(abs(t3), Motor.CCW if t3 > 0 else Motor.CW)
            M2.start_sync(M3)
        else:
            active = []
            for m, s in zip(MOTORS, target):
                if s == 0:
                    m.stop()
                else:
                    m.set_speed(abs(s), Motor.CCW if s > 0 else Motor.CW)
                    active.append(m)
            if len(active) > 1:
                active[0].start_sync(*active[1:])
            elif len(active) == 1:
                active[0].start()
    except Exception:
        for m, s in zip(MOTORS, target):
            try:
                if s == 0:
                    m.stop()
                else:
                    m.set_speed(abs(s), Motor.CCW if s > 0 else Motor.CW)
                    m.start()
            except Exception:
                pass


def stop():
    global CURRENT_MOTION
    CURRENT_MOTION = "STOP"
    set_motor_speeds(0, 0, 0, 0)


def fwd(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "VORNE"
    v = abs(int(v))
    set_motor_speeds(v, v, v, v)


def bwd(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "HINTEN"
    v = abs(int(v))
    set_motor_speeds(-v, -v, -v, -v)


def left(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "LINKS"
    v = abs(int(v))
    set_motor_speeds(v, -v, -v, v)


def right(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "RECHTS"
    v = abs(int(v))
    set_motor_speeds(-v, v, v, -v)


def fwd_left(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "VORNE-LINKS"
    v = abs(int(v))
    set_motor_speeds(v, 0, 0, v)


def fwd_right(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "VORNE-RECHTS"
    v = abs(int(v))
    set_motor_speeds(0, v, v, 0)


def bwd_left(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "HINTEN-LINKS"
    v = abs(int(v))
    set_motor_speeds(0, -v, -v, 0)


def bwd_right(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "HINTEN-RECHTS"
    v = abs(int(v))
    set_motor_speeds(-v, 0, 0, -v)


def rot_right(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "DREHEN-RECHTS"
    v = abs(int(v))
    set_motor_speeds(v, -v, v, -v)


def rot_left(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "DREHEN-LINKS"
    v = abs(int(v))
    set_motor_speeds(-v, v, -v, v)


# Direction command map: direction name -> function
MOVE_MAP = {
    "VORNE": fwd,
    "HINTEN": bwd,
    "LINKS": left,
    "RECHTS": right,
    "VORNE-LINKS": fwd_left,
    "VORNE-RECHTS": fwd_right,
    "HINTEN-LINKS": bwd_left,
    "HINTEN-RECHTS": bwd_right,
    "DREHEN-RECHTS": rot_right,
    "DREHEN-LINKS": rot_left,
    "STOP": stop,
}


def move_dir(dir_name, v=300):
    fn = MOVE_MAP.get(dir_name, stop)
    if fn == stop:
        stop()
    else:
        fn(v)
