import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD
import serial
import pycard
import re
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
        while True:
            if self.ser.inWaiting() > 0:
                time.sleep(0.5)
                cardDataString = self.ser.read(self.ser.inWaiting()).lstrip('%B').rsplit('?')[0]
                break
            else:
                progString = "%-14s" % ((' ' * offsetLength) + progTemp)
                self.lcd.set_cursor(1,1)
                for c in  progString:
                    self.lcd.write8(ord(c), True)
                offsetLength = (offsetLength + 1) % (14 - len(progTemp) + 1)
                time.sleep(0.1)
        cardDataTokens = cardDataString.split('^',3)
        #-- Card number
        cardNumber = re.sub('[^0-9]','',cardDataTokens[0].strip())
        #-- Card owner
        try:
            cardOwner = cardDataTokens[1].strip().replace('/',' ')
        except:
            cardOwner = 'N/A'
        #-- Card expiration date
        try:
            cardExpDate = cardDataTokens[2].strip()[0:4]
        except:
            cardExpDate = 'N/A'
        #-- Card data validation
        try:
            cardObject = pycard.Card(number=cardNumber,month=int(cardExpDate[2:]),year=int('20'+cardExpDate[0:2]),cvc='')
            cardValid = cardObject.is_valid
            cardType = cardObject.brand.capitalize()
        except:
            cardType = 'N/A'
            cardValid = False
        #-- Report
        print '%-20s%s\n%-20s%s\n%-20s%s\n%-20s%s\n%-20s%s\n' % ('Number:',cardNumber,'Owner:',cardOwner,'Expiration date:',cardExpDate,'Type',cardType,'Valid:',cardValid)

if __name__ == '__main__':
    runner().start()