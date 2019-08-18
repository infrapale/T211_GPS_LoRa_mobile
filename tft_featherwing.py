# The MIT License (MIT)
#
# Copyright (c) 2019 Melissa LeBlanc-Williams for Adafruit Industries LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_featherwing.minitft_featherwing`
====================================================
Helper for using the `Mini Color TFT with Joystick FeatherWing
<https://www.adafruit.com/product/3321>`_.
* Author(s): Melissa LeBlanc-Williams
* Tom Hoglund new button class

"""

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FeatherWing.git"

import time
from micropython import const
# from collections import namedtuple
import board
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.pwmout import PWMOut
import displayio
import terminalio
from adafruit_st7735r import ST7735R
from adafruit_display_text import label

# pylint: disable=bad-whitespace
BUTTON_RIGHT = const(7)
BUTTON_DOWN  = const(4)
BUTTON_LEFT  = const(3)
BUTTON_UP    = const(2)
BUTTON_SEL   = const(11)
BUTTON_A     = const(10)
BUTTON_B     = const(9)
# pylint: enable=bad-whitespace

class MiniTFTFeatherWing_T:
    """Class representing an `Mini Color TFT with Joystick FeatherWing
       <https://www.adafruit.com/product/3321>`_.
       Automatically uses the feather's I2C bus."""

    # pylint: disable-msg=too-many-arguments
    def __init__(self, address=0x5E, i2c=None, spi=None, cs=None, dc=None):
        print('MiniTFTFeatherWing_T')
        if i2c is None:
            i2c = board.I2C()
        if spi is None:
            spi = board.SPI()
        if cs is None:
            cs = board.D5
        if dc is None:
            dc = board.D6
        self._ss = Seesaw(i2c, address)
        self._backlight = PWMOut(self._ss, 5)
        self._backlight.duty_cycle = 0
        displayio.release_displays()
        while not spi.try_lock():
            pass
        spi.configure(baudrate=24000000)
        spi.unlock()
        self._ss.pin_mode(8, self._ss.OUTPUT)
        self._ss.digital_write(8, True)  # Reset the Display via Seesaw
        display_bus = displayio.FourWire(spi, command=dc, chip_select=cs)
        self.display = ST7735R(display_bus, width=160, height=80, colstart=24,
                               rotation=270, bgr=True)
    # pylint: enable-msg=too-many-arguments

        self.btn_mat = []
        self.btn_mat.append([1 << BUTTON_RIGHT, 0, 0, False, 'right'])
        self.btn_mat.append([1 << BUTTON_DOWN, 0, 0, False, 'down'])
        self.btn_mat.append([1 << BUTTON_LEFT, 0, 0, False, 'left'])
        self.btn_mat.append([1 << BUTTON_UP, 0, 0, False, 'up'])
        self.btn_mat.append([1 << BUTTON_SEL, 0, 0, False, 'select'])
        self.btn_mat.append([1 << BUTTON_A, 0, 0, False, 'A'])
        self.btn_mat.append([1 << BUTTON_B, 0, 0, False, 'B'])
        # print(btn_mat)
        self.btn_mask = 0
        for mask_indx in range(len(self.btn_mat)):
            self.btn_mask = self.btn_mask | self.btn_mat[mask_indx][0]
            # print(btn_mask)
        self._ss.pin_mode_bulk(self.btn_mask, self._ss.INPUT_PULLUP)

        self.state_dict = {'idle': 0, 'pressed': 1, 'pressed_deb': 2,
                           'released': 3, 'released_deb': 4}

        self.btn_repeat_time = 1.0
        self.btn_deb_time = 0.1
        # Make the display context
        self.row_group = displayio.Group(max_size=10)
        self.display.show(self.row_group)
        self.nbr_rows = 4
        self.row_len = 30
        self.row_hpos = [int((i * self.display.height /self.nbr_rows + 8)) for i in range(self.nbr_rows)]
        self.bkgd_colors = [0x00FF00,0x000000,0x050505,0xFF0000]
        self.row_bitmap =[]
        self.row_tile = []
        for i in range(self.nbr_rows):
            print(i)
            self.row_bitmap.append(displayio.Bitmap(80, 40, 1))
            color_palette = displayio.Palette(1)
            color_palette[0] = self.bkgd_colors[i]
            self.row_tile.append(displayio.TileGrid(self.row_bitmap[i],
                                 pixel_shader=color_palette,
                                 x=0, y=i*40))

            self.row_group.append(self.row_tile[i])


    def print_at(self, row_indx, txt):
        # this solution is not really elegant
        # need to find a fill option
        self.row_group[row_indx] = label.Label(terminalio.FONT, text=' '*self.row_len,
                                               x=0, y=self.row_hpos[row_indx],
                                               color=0xFFFF00)

        self.row_group[row_indx] = label.Label(terminalio.FONT, text=txt,
                                               x=0, y=self.row_hpos[row_indx],
                                               color=0xFFFF00)

    @property
    def backlight(self):
        """
        Return the current backlight duty cycle value
        """
        return self._backlight.duty_cycle / 255

    @backlight.setter
    def backlight(self, brightness):
        """
        Set the backlight duty cycle
        """
        self._backlight.duty_cycle = int(255 * min(max(brightness, 0.0), 1.0))

    def scan(self):
        """
        Class reading the buttons on Mini Color TFT with Joystick FeatherWing
        key pressed-released states implemented
        Keys are repeated if pressed over a time limit
        call btn_scan() as often as possible. no upper limited but slow scanning will
        decrease the performance
        btn_read() returns one key at a time as text. when no key is pressed an
        empty string will be reurned
        * Author Tom Hoglund 2019
        """
        time_now = time.monotonic()
        buttons = self._ss.digital_read_bulk(self.btn_mask)

        for mask_indx in range(len(self.btn_mat)):
            if not buttons & self.btn_mat[mask_indx][0]:
                if self.btn_mat[mask_indx][1] == self.state_dict['idle']:
                    self.btn_mat[mask_indx][1] = self.state_dict['pressed']
                    self.btn_mat[mask_indx][2] = time_now
                elif self.btn_mat[mask_indx][1] == self.state_dict['pressed']:
                    if time_now > self.btn_mat[mask_indx][2] + self.btn_deb_time:
                        self.btn_mat[mask_indx][1] = self.state_dict['pressed_deb']
                        self.btn_mat[mask_indx][2] = time_now
                elif self.btn_mat[mask_indx][1] == self.state_dict['pressed_deb']:
                    if time_now > self.btn_mat[mask_indx][2] + self.btn_repeat_time:
                        # btn_mat[mask_indx][1] = state_dict['pressed_deb']
                        self.btn_mat[mask_indx][2] = time_now
                        self.btn_mat[mask_indx][3] = True

            else:
                if self.btn_mat[mask_indx][1] == self.state_dict['pressed_deb']:
                    self.btn_mat[mask_indx][1] = self.state_dict['released']
                    self.btn_mat[mask_indx][2] = time_now
                elif self.btn_mat[mask_indx][1] == self.state_dict['released']:
                    if time_now > self.btn_mat[mask_indx][2] + self.btn_deb_time:
                        self.btn_mat[mask_indx][1] = self.state_dict['released_deb']
                        self.btn_mat[mask_indx][3] = True
            if self.btn_mat[mask_indx][1] == self.state_dict['released_deb']:
                if not self.btn_mat[mask_indx][3]:
                    self.btn_mat[mask_indx][1] = self.state_dict['idle']
                    self.btn_mat[mask_indx][2] = time_now

    def read(self):
        ret_val = ''
        for mask_indx in range(len(self.btn_mat)):
            if self.btn_mat[mask_indx][3]:
                self.btn_mat[mask_indx][3] = False
                self.btn_mat[mask_indx][1] = self.state_dict['idle']
                ret_val = self.btn_mat[mask_indx][4]
                break
        return ret_val