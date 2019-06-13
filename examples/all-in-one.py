#!/usr/bin/env python

import time
import colorsys
import os
import sys
import ST7735
import ltr559

from bme280 import BME280
from pms5003 import PMS5003
from enviroplus import gas
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

print("""all-in-one.py - Displays readings from all of Enviro plus' sensors

Press Ctrl+C to exit!

""")

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# PMS5003 particulate sensor
pms5003 = PMS5003()

# Create ST7735 LCD display class
st7735 = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=10000000
)

# Initialize display
st7735.begin()

WIDTH = st7735.width
HEIGHT = st7735.height

# Set up canvas and font
img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
path = os.path.dirname(os.path.realpath(__file__))
font = ImageFont.truetype(path + "/fonts/Asap/Asap-Bold.ttf", 20)

message = ""

# The position of the top bar
top_pos = 25

# Displays data and text on the 0.96" LCD
def display_text(variable, data, unit):
    # Maintain length of list
    values[variable] = values[variable][1:] + [data]
    # Scale the values for the variable between 0 and 1
    colours = [(v - min(values[variable]) + 1) / (max(values[variable]) - min(values[variable]) + 1) for v in values[variable]]
    # Format the variable name and value
    message = "{}: {:.1f} {}".format(variable[:4], data, unit)
    print(message)
    draw.rectangle((0, 0, WIDTH, HEIGHT), (255, 255, 255))
    for i in range(len(colours)):
        # Convert the values to colours from red to blue
        colour = (1.0 - colours[i]) * 0.6
        r, g, b = [int(x * 255.0) for x in colorsys.hsv_to_rgb(colour, 1.0, 1.0)]
        # Draw a 1-pixel wide rectangle of colour
        draw.rectangle((i, top_pos, i+1, HEIGHT), (r, g, b))
        # Draw a line graph in black
        line_y = HEIGHT - (top_pos + (colours[i] * (HEIGHT - top_pos))) + top_pos
        draw.rectangle((i, line_y, i+1, line_y+1), (0, 0, 0))
    # Write the text at the top in black
    draw.text((0, 0), message, font=font, fill=(0, 0, 0))
    st7735.display(img)

delay = 0.5  # Debounce the proximity tap
mode = 0  # The starting mode
last_page = 0
light = 1

# Create a values dict to store the data
variables = ["temperature",
             "pressure",
             "humidity",
             "light",
             "oxidised",
             "reduced",
             "nh3",
             "pm1",
             "pm25",
             "pm10"]

values = {}

for v in variables:
    values[v] = [1] * WIDTH

# The main loop
try:
    while True:
        proximity = ltr559.get_proximity()

        # If the proximity crosses the threshold, toggle the mode
        if proximity > 1500 and time.time() - last_page > delay:
            mode += 1
            mode %= len(variables)
            last_page = time.time()

        # One mode for each variable
        if mode == 0:
            variable = "temperature"
            unit = "C"
            data = bme280.get_temperature()
            display_text(variable, data, unit)

        if mode == 1:
            variable = "pressure"
            unit = "hPa"
            data = bme280.get_pressure()
            display_text(variable, data, unit)

        if mode == 2:
            variable = "humidity"
            unit = "%"
            data = bme280.get_humidity()
            display_text(variable, data, unit)

        if mode == 3:
            variable = "light"
            unit = "Lux"
            if proximity < 10:
                data = ltr559.get_lux()
            else:
                data = 1
            display_text(variable, data, unit)

        if mode == 4:
            variable = "oxidised"
            unit = "kO"
            data = gas.read_all()
            data = data.oxidising / 1000
            display_text(variable, data, unit)

        if mode == 5:
            variable = "reduced"
            unit = "kO"
            data = gas.read_all()
            data = data.reducing / 1000
            display_text(variable, data, unit)

        if mode == 6:
            variable = "nh3"
            unit = "kO"
            data = gas.read_all()
            data = data.nh3 / 1000
            display_text(variable, data, unit)

        if mode == 7:
            variable = "pm1"
            unit = "ug/m3"
            data = pms5003.read()
            data = data.pm_ug_per_m3(1.0)
            display_text(variable, data, unit)

        if mode == 8:
            variable = "pm25"
            unit = "ug/m3"
            data = pms5003.read()
            data = data.pm_ug_per_m3(2.5)
            display_text(variable, data, unit)

        if mode == 9:
            variable = "pm10"
            unit = "g/m3"
            data = pms5003.read()
            data = data.pm_ug_per_m3(10)
            display_text(variable, data, unit)

# Exit cleanly
except KeyboardInterrupt:
    sys.exit(0)
