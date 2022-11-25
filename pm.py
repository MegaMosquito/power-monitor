#
# Code for my power monitor
#
# Written by Glen Darling, Oct. 2022.
#

import time
import datetime
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import ili9341
import serial
import json

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

# Draw left-aligned text at Y coordinate
def lefttext(y, font, fill, text):
  draw.text((0, y), text, font=font, fill=fill)

# Draw centered text at Y coordinate
def righttext(y, font, fill, text):
  (font_width, font_height) = font.getsize(text)
  draw.text((width - font_width, y), text, font=font, fill=fill)

# Draw centered text at Y coordinate
def centertext(y, font, fill, text):
  (font_width, font_height) = font.getsize(text)
  draw.text((width//2 - font_width//2, y), text, font=font, fill=fill)

# Show V, A, or W status:
def status(y, font, fill, heading, value):
  suffix = ' : '
  w = font.getsize(heading + suffix)[0]
  mw = 15 + font.getsize('W : ')[0]
  draw.text((mw - w, y), heading + suffix, font=font, fill=fill)
  draw.text((mw + 1, y), value, font=font, fill=fill)

# Load fonts. Other fonts to try: http://www.dafont.com/bitmap.php
large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
# Some useful font metrics
lh = 3 + large.getsize('X')[1]
nh = 2 + normal.getsize('X')[1]
sh = 1 + small.getsize('X')[1]

# Setup for serial communication with the Arduino power monitor
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
ser.reset_input_buffer()

# Note the start time of the program
start = datetime.datetime.now()

# Note when the power originally came on (or when program restarts)
powerup = datetime.datetime.now()

V = '*'
I = '*'
W = '*'
while True:

  if ser.in_waiting > 0:
    line = ser.readline().decode('utf-8').rstrip()
    if '{' == line[0] and '}' == line[-1]:
      try:
        j = json.loads(line)
        V = j['V']
        I = j['I']
        W = round(V * I)
      except:
        pass

  # Use a filled black rectangle to clear the canvas before each redraw
  draw.rectangle((0, 0, width, height), outline=0, fill=0)

  # Compute some metrics for use below
  y = 0

  # Draw stuff onto the canvas
  centertext(y, normal, '#AA00AA', 'Power Monitor')
  y += nh + 3
  now = datetime.datetime.now()
  centertext(y, small, '#BB00BB', now.strftime('%b/%d, %I:%M:%S%p'))
  y += sh
  diff = now - start
  diff_sec = diff.total_seconds()
  hr = divmod(diff_sec, 3600)[0]
  (min, sec) = divmod(diff_sec, 60)
  centertext(y, small, '#BB00BB', ('up:  %d:%d:%d' % (hr, min, sec)))
  y += sh + 12

  status(y, large, '#0000FF', 'V', str(V))
  y += lh
  status(y, large, '#00FF00', 'A', str(I))
  y += lh

  status(y, large, '#FF00FF', 'W', str(W))
  y += lh + 12

  centertext(y, small, '#DDDDDD', powerup.strftime('kwH since %Y/%m/%d:'))
  y += sh + 2
  centertext(y, normal, '#DDDDDD', '??.??? kwH')
  y += nh + 12 

  centertext(y, small, '#DDDDDD', powerup.strftime('aH since %Y/%m/%d:'))
  y += sh + 2
  centertext(y, normal, '#DDDDDD', '???? aH')
  y += nh + 12 

  # Display the canvas
  disp.image(canvas)

  # Pause briefly before redrawing
  time.sleep(0.1)

