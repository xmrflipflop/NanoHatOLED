#!/usr/bin/env python
#
# BakeBit code based on BakeBit 128x64 OLED (http://wiki.friendlyarm.com/wiki/index.php/BakeBit_-_OLED_128x64)
#
# The BakeBit connects the NanoPi NEO and BakeBit sensors.
# You can learn more about BakeBit here:  http://wiki.friendlyarm.com/BakeBit
#
# Have a question about this code?  Ask on the forums here:  http://www.friendlyarm.com/Forum/
#
'''
## License

The MIT License (MIT)

BakeBit: an open source platform for connecting BakeBit Sensors to the NanoPi NEO.
Copyright (C) 2016 FriendlyARM

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import bakebit_128_64_oled as oled
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import time
import sys
import subprocess
import threading
import signal
import os
import socket
import re

global width
width = 128
global height
height = 64

global pageCount
pageCount = 3
global pageIndex
pageIndex = 0
global showPageIndicator
showPageIndicator = True

oled.init()  # initialze SEEED OLED display
oled.setNormalDisplay()  # Set display to normal mode (i.e non-inverse mode)
oled.setHorizontalMode()

global drawing
drawing = False

global image
image = Image.new('1', (width, height))
global draw
draw = ImageDraw.Draw(image)
global fontb24
fontb24 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 24)
global font14
font14 = ImageFont.truetype('DejaVuSansMono.ttf', 14)
global smartFont
smartFont = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 10)
global fontb14
fontb14 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 14)
global font11
font11 = ImageFont.truetype('DejaVuSansMono.ttf', 11)

global lock
lock = threading.Lock()


class PageIndex(object):
    _LEVEL1_MIN = 0
    TIME = 0
    STATS = 1
    MENU = 2
    _LEVEL1_MAX = 2

    SHUTDOWN_NO = 20
    SHUTDOWN_YES = 21
    SHUTTING_DOWN = 100


def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def is_valid_ip(ip):
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
    return bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups()))


def get_wan_ip():
    # Relies on duckdns responses.
    try:
        tokens = []
        with open('/tmp/duck.response', 'r') as f:
            tokens = f.read().split()
        return next(x for x in tokens if is_valid_ip(x))
    except:
        return "--.--.--.--"


def get_cpu_usage():
    """
    Returns CPU usage as %
    See: https://rosettacode.org/wiki/Linux_CPU_utilization
    """
    cmd = "iostat -c | sed -n '/avg-cpu/{n;p;}' | awk '{print $NF}'"
    idle = subprocess.check_output(cmd, shell=True)
    return 100.0 - float(idle)


def draw_page():
    global drawing
    global image
    global draw
    global oled
    global font
    global font14
    global smartFont
    global width
    global height
    global pageCount
    global pageIndex
    global showPageIndicator
    global width
    global height
    global lock

    lock.acquire()
    is_drawing = drawing
    page_index = pageIndex
    lock.release()

    if is_drawing:
        return

    lock.acquire()
    drawing = True
    lock.release()

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    # Draw current page indicator
    if showPageIndicator:
        dotWidth = 4
        dotPadding = 2
        dotX = width-dotWidth-1
        dotTop = (height-pageCount*dotWidth-(pageCount-1)*dotPadding)/2
        for i in range(pageCount):
            if i == page_index:
                draw.rectangle((dotX, dotTop, dotX+dotWidth,
                                dotTop+dotWidth), outline=255, fill=255)
            else:
                draw.rectangle((dotX, dotTop, dotX+dotWidth,
                                dotTop+dotWidth), outline=255, fill=0)
            dotTop = dotTop+dotWidth+dotPadding

    if page_index == PageIndex.TIME:
        padding = 0
        top = padding

        text = time.strftime("%A")
        draw.text((2, top), text, font=font14, fill=255)
        text = time.strftime("%e %b %Y")
        draw.text((2, top+16), text, font=font14, fill=255)
        text = time.strftime("%X")
        draw.text((2, top+38), text, font=fontb24, fill=255)
    elif page_index == PageIndex.STATS:
        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        padding = 1
        top = padding
        bottom = height-padding
        # Move left to right keeping track of the current x position for drawing shapes.
        x = 0
        LANIP = get_lan_ip()
        WANIP = get_wan_ip()
        CPU = get_cpu_usage()
        cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
        MemUsage = subprocess.check_output(cmd, shell=True)
        cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
        Disk = subprocess.check_output(cmd, shell=True)
        tempI = int(open('/sys/class/thermal/thermal_zone0/temp').read())
        if tempI > 1000:
            tempI = tempI/1000
        tempStr = "CPU TEMP: %sC" % str(tempI)
        cpuStr = "CPU: {0:.2f} %  {1}C".format(CPU, tempI)

        draw.text((x, top),       "LAN: {0}".format(LANIP),  font=smartFont, fill=255)
        draw.text((x, top+12),    "WAN: {0}".format(WANIP), font=smartFont, fill=255)
        draw.text((x, top+24),    cpuStr,  font=smartFont, fill=255)
        draw.text((x, top+36),    str(MemUsage),  font=smartFont, fill=255)
        draw.text((x, top+48),    str(Disk),  font=smartFont, fill=255)

    elif page_index == PageIndex.MENU:
        draw.text((4, 22),  'Shutdown?',  font=fontb14, fill=255)

    elif page_index == PageIndex.SHUTDOWN_NO:
        draw.text((2, 2),  'Shutdown?',  font=fontb14, fill=255)

        draw.rectangle((2, 20, width-4, 20+16), outline=0, fill=0)
        draw.text((4, 22),  'Yes',  font=font11, fill=255)

        draw.rectangle((2, 38, width-4, 38+16), outline=0, fill=255)
        draw.text((4, 40),  'No',  font=font11, fill=0)

    elif page_index == PageIndex.SHUTDOWN_YES:
        draw.text((2, 2),  'Shutdown?',  font=fontb14, fill=255)

        draw.rectangle((2, 20, width-4, 20+16), outline=0, fill=255)
        draw.text((4, 22),  'Yes',  font=font11, fill=0)

        draw.rectangle((2, 38, width-4, 38+16), outline=0, fill=0)
        draw.text((4, 40),  'No',  font=font11, fill=255)

    elif page_index == PageIndex.SHUTTING_DOWN:
        draw.text((2, 2),  'Shutting down',  font=fontb14, fill=255)
        draw.text((2, 20),  'Please wait',  font=font11, fill=255)

    oled.drawImage(image)

    lock.acquire()
    drawing = False
    lock.release()


def is_showing_power_msgbox(page_index):
    return page_index == PageIndex.SHUTDOWN_NO or page_index == PageIndex.SHUTDOWN_YES


def update_page_index(pi):
    global pageIndex
    lock.acquire()
    pageIndex = pi
    lock.release()


def receive_signal(signum, stack):
    global pageIndex

    lock.acquire()
    page_index = pageIndex
    lock.release()

    if page_index == PageIndex.SHUTTING_DOWN:
        return

    if signum == signal.SIGUSR1:
        # Toggle page
        print('K1 pressed')
        if page_index == PageIndex._LEVEL1_MAX:
            update_page_index(PageIndex._LEVEL1_MIN)
        elif page_index < PageIndex._LEVEL1_MAX:
            update_page_index(page_index + 1)

        elif page_index == PageIndex.SHUTDOWN_NO:
            update_page_index(PageIndex.SHUTDOWN_YES)
        elif page_index == PageIndex.SHUTDOWN_YES:
            update_page_index(PageIndex.SHUTDOWN_NO)

    elif signum == signal.SIGUSR2:
        # Home or back
        print('K2 pressed')
        if is_showing_power_msgbox(page_index):
            update_page_index(PageIndex.MENU)
        else:
            update_page_index(PageIndex.TIME)

    elif signum == signal.SIGALRM:
        # Select
        print('K3 pressed')
        if page_index == PageIndex.MENU:
            update_page_index(PageIndex.SHUTDOWN_NO)
        elif page_index == PageIndex.SHUTDOWN_NO:
            update_page_index(PageIndex.MENU)
        elif page_index == PageIndex.SHUTDOWN_YES:
            update_page_index(PageIndex.SHUTTING_DOWN)

    # draw_page()


image0 = Image.open('friendllyelec.png').convert('1')
oled.drawImage(image0)
time.sleep(2)

signal.signal(signal.SIGUSR1, receive_signal)
signal.signal(signal.SIGUSR2, receive_signal)
signal.signal(signal.SIGALRM, receive_signal)

while True:
    try:
        draw_page()

        lock.acquire()
        page_index = pageIndex
        lock.release()

        if page_index == PageIndex.SHUTTING_DOWN:
            time.sleep(2)
            while True:
                lock.acquire()
                is_drawing = drawing
                lock.release()
                if not is_drawing:
                    lock.acquire()
                    drawing = True
                    lock.release()
                    oled.clearDisplay()
                    break
                else:
                    time.sleep(.1)
                    continue
            time.sleep(1)
            os.system('systemctl poweroff')
            break
        elif page_index == PageIndex.TIME:
            time.sleep(0.25)
        else:
            time.sleep(0.5)
    except KeyboardInterrupt:
        break
    except IOError:
        print("Error")
