# The MIT License (MIT)
#
# Copyright (c) 2019 Tom Höglund
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
    """
    Row display for MiniTFT Featherwing
    """
    def __init__(self):
        self.reset_pin = 8
        self.i2c = board.I2C()
        self.ss = Seesaw(self.i2c, 0x5E)
        self.ss.pin_mode(self.reset_pin, self.ss.OUTPUT)

        self.spi = board.SPI()
        self.tft_cs = board.D5
        self.tft_dc = board.D6
        self._auto_show = True

        displayio.release_displays()
        self.display_bus = displayio.FourWire(self.spi, command=self.tft_dc, chip_select = self.tft_cs)

        self.ss.digital_write(self.reset_pin, True)
        self.display = ST7735R(self.display_bus, width=160, height=80, colstart=24, rotation=270, bgr=True)

        self.nbr_rows = 5
        self.row_height = int(self.display.height / self.nbr_rows)
        self.row_vpos = [int(i * self.row_height) for i in range(self.nbr_rows)]
        self.row_bkgnd_color = [0x808080, 0xFF0000, 0x000040, 0x0000FF, 0xAA0088]
        self.row_text_color = [0xFFFFFF, 0xFFFF00, 0xFF0000, 0xFFFF00, 0xFAFAFA]
        self.row_text = ['r1', 'r2', 'r3', 'r4', 'r5']
        # -----------------------------------------------------------------------------------
        # Button handler
        # -----------------------------------------------------------------------------------
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
        self.ss.pin_mode_bulk(self.btn_mask, self.ss.INPUT_PULLUP)

        self.state_dict = {'idle': 0, 'pressed': 1, 'pressed_deb': 2,
                           'released': 3, 'released_deb': 4}

        self.btn_repeat_time = 1.0
        self.btn_deb_time = 0.1

    def print_at(self, row_indx, txt):
        """
        Print one row a specific row number 0-4

        """
        try:
            self.row_text[row_indx] = txt
        except IndexError:
            self.row_text[self.nbr_rows - 1] = 'incorrect row index: ' + str(row_indx)
        if self._auto_show:
            self.show_rows()

    def show_rows(self):
        """
        Show printed rows on the display
        - use print_at to fill the rows first
        - background colors can be changed using the background_color function
        - text colors can be changed using the text_color function
        call show_rows when text and colors are OK
        """
        row_disp = displayio.Group(max_size=10)
        self.display.show(row_disp)
        print('show')
        for i in range(self.nbr_rows):

            # Draw row rectangles
            row_bitmap = displayio.Bitmap(self.display.width, self.row_height, 1)
            row_palette = displayio.Palette(1)
            row_palette[0] = self.row_bkgnd_color[i]
            row_block = displayio.TileGrid(row_bitmap,
                                           pixel_shader=row_palette,
                                           x=0, y=self.row_vpos[i])
            row_disp.append(row_block)
            text_group = displayio.Group(max_size=10, scale=1, x=8+i, y=6+i*self.row_height)
            text_area = label.Label(terminalio.FONT, text=self.row_text[i], color=self.row_text_color[i])
            text_group.append(text_area)   # Subgroup for text scaling
            row_disp.append(text_group)

    def background_color(self, row_indx, color_code):
        """
        change background color for one row
        row_indx = 0-4
        color_code = 24 bit binary input 0xrrggbb
        """
        try:
            self.row_bkgnd_color[row_indx] = color_code
        except IndexError:
            self.row_text[self.nbr_rows - 1] = 'incorrect row index: ' + str(row_indx)
    def text_color(self, row_indx, color_code):
        """
        change text color for one row
        row_indx = 0-4
        color_code = 24 bit binary input 0xrrggbb
        """
        try:
            self.row_text_color[row_indx] = color_code
        except IndexError:
            self.row_text[self.nbr_rows - 1] = 'incorrect row index: ' + str(row_indx)

    @property
    def auto_show(self):
        return self._auto_show
    @auto_show.setter
    def auto_show(self, t_f):
        _auto_show = t_f
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
    # -----------------------------------------------------------------------------------
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
        buttons = self.ss.digital_read_bulk(self.btn_mask)

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