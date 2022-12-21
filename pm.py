#
# Code for my power monitor
#
# Written by Glen Darling, Oct. 2022.
#

import time
import datetime
import statistics
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import ili9341
import json

# Use simulated data or real data?
USE_SIMULATED_DATA = False
if USE_SIMULATED_DATA:
  import random
  random.seed()
else:
  import serial

# Setup hardware SPI
spi = board.SPI()

# Set display baudrate (24mhz)
BAUDRATE = 24000000

# Configure CS, DC, and RESET  pins
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

# Create the display object and get display dimensions
disp = ili9341.ILI9341(
    spi,
    rotation=0,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

# Setup the display dimensions
if disp.rotation % 180 == 90:
    height = disp.width  # we swap height/width to rotate it to landscape!
    width = disp.height
else:
    width = disp.width  # we swap height/width to rotate it to landscape!
    height = disp.height

# Create blank RGB canvas for drawing
canvas = Image.new("RGB", (width, height))

# Get a draw object for drawing onto the canvas
draw = ImageDraw.Draw(canvas)

# Draw left-aligned text at Y coordinate (offset from left edge by X)
def lefttext(x, y, font, fill, text):
  draw.text((x, y), text, font=font, fill=fill)

# Draw right-aligned text at Y coordinate (offset from right edge by X)
def righttext(x, y, font, fill, text):
  (font_width, font_height) = font.getsize(text)
  draw.text((width - font_width - x, y), text, font=font, fill=fill)

# Draw centered text at Y coordinate
def centertext(y, font, fill, text):
  (font_width, font_height) = font.getsize(text)
  draw.text((width//2 - font_width//2, y), text, font=font, fill=fill)

# Format a number of seconds into a more readable time expression
def format_seconds(secs, brief=True):
  out=[]
  periods = [
    ('day', 60*60*24),
    ('hr',  60*60),
    ('min', 60),
    ('sec', 1)
  ]
  if 1 > secs:
    return "0 secs"
  for period_name, period_seconds in periods:
    if secs >= period_seconds:
      period_value, secs = divmod(secs, period_seconds)
      has_s = 's' if int(period_value) > 1 else ''
      out.append("%d %s%s" % (int(period_value), period_name, has_s))
  if brief and 0 < len(out):
    return out[0]
  else:
    return ", ".join(out)

# Show V, A, or W status:
def show_status(y, font, fill, heading, value):
  suffix = ' :'
  w = font.getsize(heading + suffix)[0]
  mw = 10 + font.getsize('W : ')[0]
  draw.text((mw - w, y), heading + suffix, font=font, fill=fill)
  righttext(24, y, font, fill, value)

# Load fonts. Other fonts to try: http://www.dafont.com/bitmap.php
large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
# Some useful font metrics
lh = 3 + large.getsize('X')[1]
nh = 2 + normal.getsize('X')[1]
sh = 1 + small.getsize('X')[1]

# Setup for serial communication with the Arduino power monitor
if not USE_SIMULATED_DATA:
  ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
  ser.reset_input_buffer()

# Note the start time of the program
start = datetime.datetime.now()

# Initialize the raw data globals
V = 120
I = 0.0
W = round(V * I)

# Initializae the power consumption variables
s = 0
AmpSec = [0.0] * 60
WattSec = [0] * 60
aH = 0
wH = 0

while True:

  if not USE_SIMULATED_DATA:
    tV = V
    tI = I
    if ser.in_waiting > 0:
      line = ser.readline().decode('utf-8').rstrip()
      if '{' == line[0] and '}' == line[-1]:
        try:
          j = json.loads(line)
          tV = j['V']
          tI = j['I']
        except:
          pass
  else:
    # Generate simulated data
    tV = 120 + random.randint(-15, 5)
    tI = 0.05 + (random.randint(0, 2500) / 100.0)

  # Prevent fast oscillations -- change by only 10% per second
  V += round((tV - V) * 0.1)
  I += ((tI - I) * 0.1)

  # Compute Watts from Volts and Amps
  W = round(V * I)

  # Compute aH and wH over time
  AmpSec[s] = I
  WattSec[s] = W
  s += 1
  if s == 60:
    s = 0
    aH += (statistics.mean(AmpSec) / 60.0)
    wH += (statistics.mean(WattSec) / 60.0)

  # Use a filled black rectangle to clear the canvas before each redraw
  draw.rectangle((0, 0, width, height), outline=0, fill=0)

  # Compute screen metrics using y
  y = 0

  # Draw title onto the canvas
  centertext(y, normal, '#AA00AA', 'Power Monitor')
  y += nh + 3

  # Show current date/time
  now = datetime.datetime.now()
  centertext(y, small, '#BB00BB', now.strftime('%b %d, %I:%M%p'))
  y += sh

  # Show uptime
  diff = now - start
  diff_sec = diff.total_seconds()
  centertext(y, small, '#BB00BB', '(up: %s)' % format_seconds(diff_sec))
  y += sh + 12

  # The primary display of r Volts, Amps, and Watts:
  show_status(y, large, '#0000FF', 'V', '%d' % V)
  y += lh
  show_status(y, large, '#00FF00', 'A', '%0.1f' % I)
  y += lh
  show_status(y, large, '#FF00FF', 'W', '%d' % W)
  y += lh + 12

  centertext(y, small, '#DDDDDD', 'aH since power on:')
  y += sh + 2
  centertext(y, normal, '#DDDDDD', '%0.3f aH' % aH)
  y += nh + 12 

  centertext(y, small, '#DDDDDD', 'kwH since power on:')
  y += sh + 2
  centertext(y, normal, '#DDDDDD', '%0.3f kwH' % (wH / 1000.0))
  y += nh + 12 

  # Display the canvas
  disp.image(canvas)

  # Pause briefly before redrawing (tweaked for 1 loop/second on Pi3A+)
  # print(now.strftime('%S, %f'))
  time.sleep(0.092)

