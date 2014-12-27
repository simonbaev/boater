import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD
import serial
import pycard
import re
import threading, sys, time

class Worker(threading.Thread):
    """
    Default constructor that initializes serial port and LCD display
    """

    def __init__(self, port=None):
        # Call to constructor of superclass
        threading.Thread.__init__(self, name='Worker')
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
        time.sleep(2)

    def getBytes(self, nBytes=None):
        """
        Returns all data in waiting from the open serial port
        """
        inWaiting = self.ser.inWaiting()
        if (nBytes == None) or (nBytes > inWaiting):
            return self.ser.read(inWaiting)
        else:
            return self.ser.read(nBytes)
    def cardStringParser(self, rawData):
        # Sanity check
        if rawData == None:
            return None
        # Tokenize raw data
        cardDataTokens = rawData.split('^',3)
        #-- Card number
        cardNumber = re.sub('[^0-9]','',cardDataTokens[0].strip())
        #-- Card owner
        try:
            cardOwner = cardDataTokens[1].strip().replace('/',' ')
        except:
            cardOwner = 'N/A'
        #-- Card expiration date
        try:
            tmp = cardDataTokens[2].strip()[0:4]
            cardExpDate = tmp[2:] + '/' + tmp[:2]
        except:
            cardExpDate = 'N/A'
        #-- Card data validation
        try:
            cardObject = pycard.Card(number=cardNumber,month=int(cardExpDate[:2]),year=int('20'+cardExpDate[3:]),cvc='')
            cardValid = cardObject.is_valid
            cardType = cardObject.brand.capitalize()
        except:
            cardType = 'N/A'
            cardValid = False
            cardObject = None
        #-- Format return value using dict
        return {
            'fmtLogData' : '%-20s%s\n%-20s%s\n%-20s%s\n%-20s%s\n%-20s%s\n' % ('Number:',cardNumber,'Owner:',cardOwner,'Expiration date:',cardExpDate,'Type',cardType,'Valid:',cardValid),
            'fmtLCDData' : '%-7sXXXX-%s\n%-11s%5s' % (cardType[:4],cardNumber[-4:],'Exp.Date',cardExpDate),
            'rawData' : rawData,
            'cardNumber' : cardNumber,
            'cardOwner' : cardOwner,
            'cardExpDate' : cardExpDate,
            'cardObject' : cardObject,
            'cardValid' : cardValid,
            'cardType' : cardType
        }

    def run(self):
        while True:
            self.lcd.clear()
            offsetLength = 0
            progTemp = '>>>'
            self.lcd.message(' Slide the card ')
            cardDataString = None
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
            #-- Parse card data string
            cardData = self.cardStringParser(cardDataString)
            print cardData['fmtLogData']
            #-- Display card info on LCD
            self.lcd.set_cursor(0,0)
            self.lcd.message(cardData['fmtLCDData'])
            if cardData['cardValid'] == False:
                self.lcd.set_color(1,0,0)
                time.sleep(3.0)
                self.lcd.set_color(1,1,1)
                continue

