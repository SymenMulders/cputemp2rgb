# cputemp2rgb
Synchronizes RGB lighting with CPU temperature.

cputemp2rgb is a small daemon that changes the color of your motherboard's built-in RGB lighting as your CPU temperature changes. It calculates the RGB value based on the physics of blackbody radiation. The algorithm for this has been shamelessly borrowed from [Tanner Helland](https://tannerhelland.com/2012/09/18/convert-temperature-rgb-algorithm-code.html). It was meant to work with temperatures in the thousands of degrees K, but it adapts nicely to degrees C values two orders of magnitude smaller.

## Requirements

- Your favorite Linux distribution.
- A relatively recent Intel or AMD CPU with a thermal sensor package supported by coretemp or k10temp, with Linux kernel support.
- A motherboard with RGB lighting supported by [OpenRGB](https://openrgb.org/), which must be installed and properly configured.
- Python libraries (installed by your preferred package manager):
  - [numpy](https://numpy.org/)
  - [daemonize](https://github.com/thesharp/daemonize/)
  - [psutil](https://github.com/giampaolo/psutil/) >=5.1.0
  - [OpenRGB-Python](https://github.com/jath03/openrgb-python/)

## Installation

The program is self-contained within `cputemp2rgb.py` and can be run from anywhere on your system. It could be trivially launched from `/etc/rc.local` or `systemd`, or as an autostart or login script in your favorite desktop environment. This is left as an exercise for the user.

## Configuration

`cputemp2rgb` contains the following configuration values which can be edited in the source code:

### COLORSHIFT

COLORSHIFT allows you to redshift or blueshift the color profile according to your preferences. By default, your lights will be pure white somewhere around 85 C, depending on how low your idle temperatures reach. Negative values will raise this threshold, positive values will lower it. Adjusting this is completely optional.

## Usage

```console
$ python3 ./cputemp2rgb.py
```

The program has no parameters currently, and it will background itself once launched. It shouldn't require any special permissions to access your hardware, as that is all handled through OpenRGB and udev wizardry. It uses negligible system resources, as it is asleep for the vast majority of its execution time.

To stop the program:

```console
$ kill -9 $(cat /tmp/cputemp2rgb.pid)
```
