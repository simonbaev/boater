import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD
import serial
import threading, sys, time


class runner(threading.Thread):
    """
    Default constructor that initializes serial port and LCD display
    """

    def __init__(self, port=None):
        # Call to constructor of superclass
        threading.Thread.__init__(self)
        # Serial port name
        if port == None:
            self.readerPort = '/dev/ttyUSB0'
        else:
            self.readerPort = port
        # Initialize port for magnetic card reader
        try:
            self.ser = serial.Serial(self.readerPort, 9600)
            self.ser.flushInput()
        except Exception, reason:
            print >> sys.stderr, 'Cannot open communication port for card reader: %s' % reason
            sys.exit(1)
        # Initialize LCD plate
        self.lcd = LCD.Adafruit_CharLCDPlate()
        self.lcd.clear()
        self.lcd.set_color(1.0, 1.0, 1.0)
        self.lcd.message('    Welcome    \nto Boater kiosk')

    def getBytes(self, nBytes=None):
        """
        Returns all data in waiting from the open serial port
        """
        inWaiting = self.ser.inWaiting()
        if (nBytes == None) or (nBytes > inWaiting):
            return self.ser.read(inWaiting)
        else:
            return self.ser.read(nBytes)

    def run(self):
        time.sleep(1)
        self.lcd.clear()
        offsetLength = 0
        progTemp = '>>>'
        self.lcd.message(' Slide the card ')
        time.sleep(2)
        while True:
            if self.ser.inWaiting() > 0:
                time.sleep(1)
                print self.ser.read(self.ser.inWaiting())
                break
            else:
                progString = "%-14s" % ((' ' * offsetLength) + progTemp)
                self.lcd.set_cursor(1,1)
                for c in  progString:
                    self.lcd.write8(ord(c), True)
                offsetLength = (offsetLength + 1) % (14 - len(progTemp) + 1)
                time.sleep(0.1)


if __name__ == '__main__':
    runner().start()