"""
This example display a CircuitPython console and
print which button that is being pressed if any
"""
import time
from tft_featherwing import MiniTFTFeatherWing_T
from gps_handler import gps_handler
minitft = MiniTFTFeatherWing_T()
gps = gps_handler()
# minitft.backlight = 0.5
minitft.print_at(0, 'LoRa Drive Test')
last_show = time.monotonic()
last_btn_scan = time.monotonic()
last_gps_update = time.monotonic()
gps_update_interval = 1
btn_scan_interval = 0.1
show_interval = 0.5
while True:
    if time.monotonic() > last_btn_scan + btn_scan_interval:
        last_btn_scan = time.monotonic()
        minitft.scan()
    pressed = minitft.read()
    if len(pressed) > 0:
        print(pressed)
        minitft.print_at(2, pressed)
    if time.monotonic() > last_gps_update + gps_update_interval:
        last_gps_update = time.monotonic()
        gps.update()
    if time.monotonic() > last_show + show_interval:
        last_show = time.monotonic()
        print('show')
        minitft.print_at(1, gps.timestamp())

	