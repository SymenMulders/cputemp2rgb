#!/usr/bin/env python3
"""
cputemp2rgb: Synchronize Motherboard RGB Lighting to CPU Temperature
====================================================================

Copyright (C) 2023, Symen Mulders. All Rights Reserved.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

cputemp2rgb is a small daemon that changes the color of your motherboard's
built-in RGB lighting as your CPU temperature changes. It calculates the
RGB value based on the physics of blackbody radiation. Algorithm shamelessly
stolen^H^H^H^H^H^H borrowed from:

https://tannerhelland.com/2012/09/18/convert-temperature-rgb-algorithm-code.html

This algorithm was meant to work with degrees K values in the visible light
spectrum, but it adapts easily to degrees C values two orders of magnitude
smaller.

Requirements:
-------------

 - Your system must have thermal sensors that are supported by/can be read
   by your operating system and the psutil library. Currently supported
   platforms are Linux and FreeBSD as of 20230212.
 - Your motherboard must be supported by OpenRGB (https://openrgb.org/),
   which you must have installed and working.
 - Python libraries:
   - numpy (https://numpy.org/)
   - daemonize (https://github.com/thesharp/daemonize/)
   - psutil >=5.1.0 (https://github.com/giampaolo/psutil/)
   - OpenRGB-Python (https://github.com/jath03/openrgb-python/)

Usage:
------

  $ python3 ./cputemp2rgb.py

This program has no parameters, and it will background itself once launched.
It shouldn't require any special permissions to access your hardware, that
is all handled through OpenRGB and udev wizardry. It uses almost no system
resources, as the vast majority of execution time is spent in sleep() system
calls.

To stop the program:

  $ kill -9 $(cat /tmp/cputemp2rgb.pid)

"""

"""
Configuration:
==============
"""
"""
COLORSHIFT
----------

COLORSHIFT is used to shift the overall color gradient toward red or blue per
your preference. Negative numbers shift the color more red, positive numbers
shift more blue. By default, cputemp2rgb will output pure white at around
85 C. Negative numbers will raise this value, positive numbers will lower it.
"""
COLORSHIFT = 0
"""
Do not^H^H^H^H^H^H Send a pull request if you edit below this line!
-------------------------------------------------------------------
"""

from sys import exit
from time import sleep
from numpy import log
from psutil import sensors_temperatures
from daemonize import Daemonize
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor, DeviceType

"""
Retrieves your CPU temperature.

The highest value of multiple CPUs/cores is returned.

:returns: float representing your CPU's temperature in Celsius.
:raises: Exits if it can't read the sensors.
"""
def cputemp():
    temps = sensors_temperatures()
    if not temps:
        exit("Unable to read temperature sensors!")
    temp = 0.0
    for name, entries in temps.items():
        if name == 'coretemp' or name == 'k10temp':
            for entry in entries:
                if entry.current > temp: # Take the highest temp
                    temp = entry.current
    return temp

"""
Converts/constrains a number to a value between 0 and 255.

Negative numbers are returned as 0, and numbers greater than 255 as 255.

:param num: A number, either integer or floating point.
:returns: integer between 0 and 255.
"""
def c8bit(num):
    if num < 0:
        return 0
    if num > 255:
        return 255
    return int(num)

"""
Computes a red value for a given temperature.

:param temp: int/float representing a temperature in C.
:returns: int between 0 and 255.
"""
def r(temp):
    if temp <= 0.0:
        temp = 0.1
    if temp <= 66.0:
        red = 255
    else:
        red = temp - 60.0
        red = 329.698727446 * (red ** -0.1332047592)
    return c8bit(red)

"""
Computes a green value for a given temperature.

:param temp: int/float representing a temperature in C.
:returns: int between 0 and 255.
"""
def g(temp):
    if temp <= 0.0:
        temp = 0.1
    if temp <= 66.0:
        green = temp
        green = 99.4708025861 * log(green) - 161.1195681661
    else:
        green = temp - 60
        green = 288.1221695283 * (green ** -0.0755148492)
    return c8bit(green)

"""
Computes a blue value for a given temperature.

:param temp: int/float representing a temperature in C.
:returns: int between 0 and 255.
"""
def b(temp):
    if temp <= 0.0:
        temp = 0.1
    if temp >= 66:
        blue = 255
    else:
        if temp <= 19:
            blue = 0
        else:
            blue = temp - 10
            blue = 138.5177312231 * log(blue) - 305.0447927307
    return c8bit(blue)

"""
Initializes the RGB hardware and synchronizes CPU temperature to it.

This runs infinitely, updating the RGB hardware every 5 seconds.
As such, it has no parameters or return values.
"""
def cputemp2rgb():
    rgb = OpenRGBClient()
    rgb.clear() # Turn off the lights, so we know what state they're in.
    motherboard = rgb.get_devices_by_type(DeviceType.MOTHERBOARD)[0]
    # Now turn them on, but dimmed all the way.
    motherboard.set_color(RGBColor(0, 0, 0))
    # Initially, subtract room temperature in degrees Celsius from the raw temperature.
    # This is just a guess at ambient, since most computers don't have a sensor for that.
    # If the raw temperature drops below ambient, we'll use that value instead.
    offset = 20
    temp = cputemp()
    while True:
        if temp < offset:
            offset = temp
        # Take the average of the last temperature and the current to set with.
        # This gives us a smoother ramp, as every read has a decay time.
        temp = ((temp + cputemp()) / 2.0)
        # Pull in the fudge factors to make it look good.
        output = temp - offset + COLORSHIFT
        motherboard.set_color(RGBColor(r(output), g(output), b(output)))
        sleep(5.0)

"""
main function. Daemonizes cputemp2rgb()
:returns: 0.
"""
def main():
    pid = '/tmp/cputemp2rgb.pid'
    daemon = Daemonize(app='cputemp2rgb', pid=pid, action=cputemp2rgb)
    daemon.start()
    return 0

if __name__ == '__main__':
    main()
