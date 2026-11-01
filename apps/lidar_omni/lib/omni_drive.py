#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omniwheels 4-Motor Drive Module for fischertechnik TXT 4.0.
Supports 8-directional holonomic motion and emergency stop.
"""

import time
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

CURRENT_MOTION = "STOP"

def stop():
    global CURRENT_MOTION
    CURRENT_MOTION = "STOP"
    try:
        M1.stop_sync(M2, M3, M4)
    except Exception:
        pass

def fwd(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "VORNE"
    M1.set_speed(int(v), Motor.CCW)
    M2.set_speed(int(v), Motor.CCW)
    M3.set_speed(int(v), Motor.CCW)
    M4.set_speed(int(v), Motor.CCW)
    M1.start_sync(M2, M3, M4)

def bwd(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "HINTEN"
    M1.set_speed(int(v), Motor.CW)
    M2.set_speed(int(v), Motor.CW)
    M3.set_speed(int(v), Motor.CW)
    M4.set_speed(int(v), Motor.CW)
    M1.start_sync(M2, M3, M4)

def left(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "LINKS"
    M1.set_speed(int(v), Motor.CCW)
    M2.set_speed(int(v), Motor.CW)
    M3.set_speed(int(v), Motor.CW)
    M4.set_speed(int(v), Motor.CCW)
    M1.start_sync(M2, M3, M4)

def right(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "RECHTS"
    M1.set_speed(int(v), Motor.CW)
    M2.set_speed(int(v), Motor.CCW)
    M3.set_speed(int(v), Motor.CCW)
    M4.set_speed(int(v), Motor.CW)
    M1.start_sync(M2, M3, M4)

def fwd_left(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "VORNE-LINKS"
    M2.stop()
    M3.stop()
    M1.set_speed(int(v), Motor.CCW)
    M4.set_speed(int(v), Motor.CCW)
    M1.start()
    M4.start()

def fwd_right(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "VORNE-RECHTS"
    M1.stop()
    M4.stop()
    M2.set_speed(int(v), Motor.CCW)
    M3.set_speed(int(v), Motor.CCW)
    M2.start()
    M3.start()

def bwd_left(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "HINTEN-LINKS"
    M1.stop()
    M4.stop()
    M2.set_speed(int(v), Motor.CW)
    M3.set_speed(int(v), Motor.CW)
    M2.start()
    M3.start()

def bwd_right(v=300):
    global CURRENT_MOTION
    CURRENT_MOTION = "HINTEN-RECHTS"
    M2.stop()
    M3.stop()
    M1.set_speed(int(v), Motor.CW)
    M4.set_speed(int(v), Motor.CW)
    M1.start()
    M4.start()

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
    "STOP": stop
}

def move_dir(dir_name, v=300):
    fn = MOVE_MAP.get(dir_name, stop)
    if fn == stop:
        stop()
    else:
        fn(v)
