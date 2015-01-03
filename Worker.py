import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD
import serial
import pycard
import re
import sys, time, os, signal

class ExitCommand(Exception):
    pass

class Worker:
    """
    Default constructor that initializes serial port and LCD display
    """
    def __init__(self, port=None):
        # Register signal/interrupt handling
        signal.signal(signal.SIGINT, self.signal_handler)
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
        # Relay board pins
        GPIO.setmode(GPIO.BOARD)
        self.relayList = [11,12,13,15,16,18,22,7,31,32,33,35,36,37,38,40]
        GPIO.setup(self.relayList,GPIO.IN)
        # Initialize LCD plate
        self.lcd = LCD.Adafruit_CharLCDPlate()
        # Default colors
        self.lcd.set_color(1.0, 1.0, 1.0)
        # Up
        self.lcd.create_char(1, [0,0,4,14,31,0,0,0])
        # Down
        self.lcd.create_char(2, [0,0,31,14,4,0,0,0])
        # Left
        self.lcd.create_char(3, [1,3,7,15,15,7,3,1])
        # Right
        self.lcd.create_char(4, [16,24,28,30,30,28,24,16])
        #-- Welcome message
        self.lcd.clear()
        self.lcd.message('    Welcome    \nto Boater kiosk')
        time.sleep(2)

    def signal_handler(self, signal, frame):
        raise ExitCommand()

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
            cardOwner = None
        #-- Card expiration date
        try:
            tmp = cardDataTokens[2].strip()[0:4]
            cardExpDate = tmp[2:] + '/' + tmp[:2]
        except:
            cardExpDate = None
        #-- Card data validation
        try:
            cardObject = pycard.Card(number=cardNumber,month=int(cardExpDate[:2]),year=int('20'+cardExpDate[3:]),cvc='')
            cardValid = cardObject.is_valid
            cardType = cardObject.brand.capitalize()
        except:
            cardType = None
            cardValid = False
            cardObject = None
        #-- Format return value using dict
        return {
            'fmtLogData' : '%-20s%s\n%-20s%s\n%-20s%s\n%-20s%s\n%-20s%s\n' % (
                'Number:',
                cardNumber,
                'Owner:',
                'N/A' if cardOwner == None else cardOwner,
                'Expiration date:',
                'N/A' if cardExpDate == None else cardExpDate,
                'Type',
                'N/A' if cardType == None else cardType,
                'Valid:',
                cardValid
            ),
            'fmtLCDData' : '%-7sXXXX-%s\n%-11s%5s' % (
                'N/A' if cardType == None else cardType[:6],
                cardNumber[-4:],
                'Exp.Date',
                'N/A' if cardExpDate == None else cardExpDate
            ),
            'rawData' : rawData,
            'cardNumber' : cardNumber,
            'cardOwner' : cardOwner,
            'cardExpDate' : cardExpDate,
            'cardObject' : cardObject,
            'cardValid' : cardValid,
            'cardType' : cardType
        }
    def doIt(self):
        try:
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
                    time.sleep(5.0)
                    self.lcd.set_color(1,1,1)
                    continue
                time.sleep(3.0)
                #-- Select the locker
                self.lcd.clear()
                self.lcd.set_cursor(0,0)
                self.lcd.message(' Select locker ')
                lockID = 0
                mod = len(self.relayList)
                while True:
                    self.lcd.set_cursor(0,1)
                    self.lcd.message('     \x03 %02d \x04     ' % (lockID + 1))
                    if self.lcd.is_pressed(LCD.LEFT) or self.lcd.is_pressed(LCD.DOWN):
                        lockID = (lockID - 1 + mod) % mod
                    elif self.lcd.is_pressed(LCD.RIGHT) or self.lcd.is_pressed(LCD.UP):
                        lockID = (lockID + 1) % mod
                    elif self.lcd.is_pressed(LCD.SELECT):
                         break
                    time.sleep(0.04)
                GPIO.setup(self.relayList[lockID],GPIO.OUT)
                time.sleep(3.0)
                GPIO.setup(self.relayList[lockID],GPIO.IN)

        except ExitCommand:
            pass
        finally:
            print >> sys.stderr, 'Worker gets terminated...'
            self.lcd.clear()
            self.lcd.set_cursor(0,0)
            self.lcd.message("Terminated...")
            time.sleep(1)



