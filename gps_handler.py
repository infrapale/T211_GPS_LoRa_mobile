# Simple GPS module demonstration.
# Will wait for a fix and print a message every second with the current location
# and other details.
import board
import busio

import adafruit_gps

class gps_handler:
    """ class for reading GPS data and updating information for main code to utilize"""

    # pylint: disable-msg=too-many-arguments
    def __init__(self):
        # Define RX and TX pins for the board's serial port connected to the GPS.
        # These are the defaults you should use for the GPS FeatherWing.
        # For other boards set RX = GPS module TX, and TX = GPS module RX pins.
        RX = board.RX
        TX = board.TX
        self.gps_dict = {'has_fix': True, 'Latitude': 0.0, 'Longitude': 0.0,
                         'fix_quality': '', 'year': 0, 'month': 0, 'day': 0,
                         'hour': 0, 'minute': 0, 'second': 0,
                         'satellites': 0, 'altitude': 0.0,  'speed': 0.0,
                         'latitude': 0.0, 'longitude': 0.0, 'fix_quality': ''}
        # Create a serial connection for the GPS connection using default speed and
        # a slightly higher timeout (GPS modules typically update once a second).
        self.uart = busio.UART(TX, RX, baudrate=9600, timeout=30)

        # for a computer, use the pyserial library for uart access
        # import serial
        # uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=3000)

        # Create a GPS module instance.
        self.gps = adafruit_gps.GPS(self.uart, debug=False)
        self.gps_has_fix = False
        # Initialize the GPS module by changing what data it sends and at what rate.
        # These are NMEA extensions for PMTK_314_SET_NMEA_OUTPUT and
        # PMTK_220_SET_NMEA_UPDATERATE but you can send anything from here to adjust
        # the GPS module behavior:
        #   https://cdn-shop.adafruit.com/datasheets/PMTK_A11.pdf

        # Turn on the basic GGA and RMC info (what you typically want)
        self.gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn on just minimum info (RMC only, location):
        # gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn off everything:
        # gps.send_command(b'PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Tuen on everything (not all of it is parsed!)
        # gps.send_command(b'PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0')

        # Set update rate to once a second (1hz) which is what you typically want.
        self.gps.send_command(b'PMTK220,1000')
        # Or decrease to once every two seconds by doubling the millisecond value.
        # Be sure to also increase your UART timeout above!
        # gps.send_command(b'PMTK220,2000')
        # You can also speed up the rate, but don't go too fast or else you can lose
        # data during parsing.  This would be twice a second (2hz, 500ms delay):
        # gps.send_command(b'PMTK220,500')

        # Main loop runs forever printing the location, etc. every second.

    def update(self):
        # Make sure to call gps.update() every loop iteration and at least twice
        # as fast as data comes from the GPS unit (usually every second).
        # This returns a bool that's true if it parsed new data (you can ignore it
        # though if you don't care and instead look at the has_fix property).
        self.gps.update()
        # Every second print out current location details if there's a fix.
        if not self.gps_has_fix:
            # Try again if we don't have a fix yet.
            print('Waiting for fix...')
            self.gps_has_fix = False
        else:
            # We     have a fix! (gps.has_fix is true)
            # Print out details about the fix like location, date, etc.
            self.gps_dict['year'] = self.gps.timestamp_utc.tm_year
            self.gps_dict['month'] = self.gps.timestamp_utc.tm_year
            self.gps_dict['day'] = self.gps.timestamp_utc.tm_year
            self.gps_dict['hour'] = self.gps.timestamp_utc.tm_year
            self.gps_dict['minute'] = self.gps.timestamp_utc.tm_year
            self.gps_dict['second'] = self.gps.timestamp_utc.tm_year
            self.gps_dict['satellites'] = self.gps.satellites
            self.gps_dict['altitude'] = self.gps.altititude_m
            self.gps_dict['speed'] = self.gps.speed_knots
            self.gps_dict['latitude'] = self.gps.latitude
            self.gps_dict['longitude'] = self.gps.longitude
            self.gps_dict['fix_quality'] = self.gps.fix_quality

            print('=' * 40)  # Print a separator line.
            print('Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}'.format(
                self.gps.timestamp_utc.tm_mon,   # Grab parts of the time from the
                self.gps.timestamp_utc.tm_mday,  # struct_time object that holds
                self.gps.timestamp_utc.tm_year,  # the fix time.  Note you might
                self.gps.timestamp_utc.tm_hour,  # not get all data like year, day,
                self.gps.timestamp_utc.tm_min,   # month!
                self.gps.timestamp_utc.tm_sec))
            print('Latitude: {0:.6f} degrees'.format(self.gps.latitude))
            print('Longitude: {0:.6f} degrees'.format(self.gps.longitude))
            print('Fix quality: {}'.format(self.gps.fix_quality))
            # Some attributes beyond latitude, longitude and timestamp are optional
            # and might not be present.  Check if they're None before trying to use!
            if self.gps.satellites is not None:
                print('# satellites: {}'.format(self.gps.satellites))
                if self.gps.altitude_m is not None:
                    print('Altitude: {} meters'.format(self.gps.altitude_m))
                if self.gps.speed_knots is not None:
                    print('Speed: {} knots'.format(self.gps.speed_knots))
                if self.gps.track_angle_deg is not None:
                    print('Track angle: {} degrees'.format(self.gps.track_angle_deg))
                if self.gps.horizontal_dilution is not None:
                    print('Horizontal dilution: {}'.format(self.gps.horizontal_dilution))
                if self.gps.height_geoid is not None:
                    print('Height geo ID: {} meters'.format(self.gps.height_geoid))

    def get_data(self, key):
        if key in self.gps_dict:
            return self.gps_dict[key]
        else:
            return None

    def timestamp(self):
        return '{:02}/{:02}/{:02} {:02}:{:02}:{:02}'.format(
                self.gps_dict['year'],
                self.gps_dict['month'],
                self.gps_dict['day'],
                self.gps_dict['hour'],
                self.gps_dict['minute'],
                self.gps_dict['second'])

    def fix(self):
        return self.gps_has_fix
