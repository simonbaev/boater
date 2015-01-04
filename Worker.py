import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD
import paypalrestsdk
import serial
import pycard
import re
import sys, time, os, signal
import urllib2

class ExitCommand(Exception):
    pass

class Worker:
    """
    Default constructor that initializes serial port and LCD display
    """
    def __init__(self, port=None):
        # Class variables
        self.debugFlag = True
        # Register signal/interrupt handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGUSR1, self.signal_handler)
        # Initialize LCD plate
        try:
            self.initLCD()
        except Exception, reason:
            if self.debugFlag:
                print >> sys.stderr, "Cannot initialize LCD plate: %s" % reason
            sys.exit(1)
        # Initialize GPIO ports
        try:
            self.initGPIO()
        except Exception, reason:
            if self.debugFlag:
                print >> sys.stderr, "Cannot initialize GPIO ports: %s" % reason
            sys.exit(2)
        # Initialize UART interface (card reader)
        try:
            self.initUART(port)
        except Exception, reason:
            if self.debugFlag:
                print >> sys.stderr, "Cannot open communication port for card reader: %s" % reason
            self.lcd.set_color(1, 0, 0)
            self.printLCD(0, 'c', "Card Reader")
            self.printLCD(1, 'c', "Failure")
            time.sleep(1.0)
            sys.exit(3)
        # Initialize PayPal interface
        try:
            self.initPayPal()
        except Exception, reason:
            if self.debugFlag:
                print >> sys.stderr, "Cannot connect to PayPal: %s" % reason
            self.lcd.set_color(1, 0, 0)
            self.printLCD(0, 'c', "PayPal interface")
            self.printLCD(1, 'c', "Failure")
            time.sleep(1.0)
            sys.exit(4)
        # Welcome message
        self.printLCD(0, 'c', "Welcome")
        self.printLCD(1, 'c', "To Boater Kiosk")

    def initLCD(self):
        # Initialize LCD plate
        self.lcd = LCD.Adafruit_CharLCDPlate()
        self.lcd.set_color(1.0, 1.0, 1.0)
        # Up character
        self.lcd.create_char(1, [0, 0, 4, 14, 31, 0, 0, 0])
        # Down character
        self.lcd.create_char(2, [0, 0, 31, 14, 4, 0, 0, 0])
        # Left character
        self.lcd.create_char(3, [1, 3, 7, 15, 15, 7, 3, 1])
        # Right character
        self.lcd.create_char(4, [16, 24, 28, 30, 30, 28, 24, 16])

    def initGPIO(self):
        GPIO.setmode(GPIO.BOARD)
        self.relayList = [11, 12, 13, 15, 16, 18, 22, 7, 31, 32, 33, 35, 36, 37, 38, 40]
        GPIO.setup(self.relayList, GPIO.IN)

    def initUART(self, port):
        # Serial port name
        if port == None:
            self.readerPort = '/dev/ttyUSB0'
        else:
            self.readerPort = port
        # Initialize port for magnetic card reader
        try:
            self.ser = serial.Serial(self.readerPort, 9600)
            self.ser.flushInput()
        except Exception:
            raise Exception(sys.exc_info()[1])

    def initPayPal(self):
        try:
            urllib2.urlopen('https://paypal.com',timeout=5)
            paypalrestsdk.configure({
                'mode':             'sandbox',
                'client_id':        'AQvHZBAWpd-nwPq9dBf92g7x9Rb7Qnu-c6HvMlUtG3YJ4Dk9SKLBMGRjs3KK',
                'client_secret':    'EE12TxCGjMqmr1N2Z1Z8VKv4UhefqowqKGfkQbg5mBxFhtlpULonFsRLd137'
            })
        except Exception:
            raise Exception(sys.exc_info()[1])

    def printLCD(self, line=0, align='c', text=""):
        if align == 'l':
            text = text.ljust(16)
        elif align == 'r':
            text.rjust(16)
        else:
            text = text.center(16)
        if line > 1 or line < 0:
            line = 0
        self.lcd.set_cursor(0, line)
        for c in text:
            self.lcd.write8(ord(c), True)

    def signal_handler(self, signum, frame):
        raise ExitCommand(signum)

    def cardStringParser(self, rawData):
        # Sanity check
        if rawData == None:
            return None
        # Tokenize raw data
        cardDataTokens = rawData.split('^', 3)
        # -- Card number
        cardNumber = re.sub('[^0-9]', '', cardDataTokens[0].strip())
        #-- Card owner
        try:
            cardOwner = cardDataTokens[1].strip().replace('/', ' ')
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
            cardObject = pycard.Card(number=cardNumber, month=int(cardExpDate[:2]), year=int('20' + cardExpDate[3:]),
                                     cvc='')
            cardValid = cardObject.is_valid
            cardType = cardObject.brand.capitalize()
        except:
            cardType = None
            cardValid = False
            cardObject = None
        #-- Format return value using dict
        return {
            'fmtLogData': '%-20s%s\n%-20s%s\n%-20s%s\n%-20s%s\n%-20s%s\n' % (
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
            'fmtLCDData': '%-7sXXXX-%s\n%-11s%5s' % (
                'N/A' if cardType == None else cardType[:6],
                cardNumber[-4:],
                'Exp.Date',
                'N/A' if cardExpDate == None else cardExpDate
            ),
            'rawData': rawData,
            'cardNumber': cardNumber,
            'cardOwner': cardOwner,
            'cardExpDate': cardExpDate,
            'cardObject': cardObject,
            'cardValid': cardValid,
            'cardType': cardType
        }

    def doIt(self):
        try:
            while True:
                self.lcd.clear()
                offsetLength = 0
                progTemp = '>>>'
                self.printLCD(0, 'c', "Swipe the card")
                cardDataString = None
                while True:
                    if self.ser.inWaiting() > 0:
                        time.sleep(0.5)
                        cardDataString = self.ser.read(self.ser.inWaiting()).lstrip('%B').rsplit('?')[0]
                        break
                    else:
                        progString = "%-14s" % ((' ' * offsetLength) + progTemp)
                        self.lcd.set_cursor(1, 1)
                        for c in progString:
                            self.lcd.write8(ord(c), True)
                        offsetLength = (offsetLength + 1) % (14 - len(progTemp) + 1)
                        time.sleep(0.1)
                # -- Parse card data string
                cardData = self.cardStringParser(cardDataString)
                if self.debugFlag:
                    print cardData['fmtLogData']
                #-- Display card info on LCD
                self.lcd.set_cursor(0, 0)
                self.lcd.message(cardData['fmtLCDData'])
                if cardData['cardValid'] == False:
                    self.lcd.set_color(1, 0, 0)
                    time.sleep(5.0)
                    self.lcd.set_color(1, 1, 1)
                    continue
                time.sleep(3.0)
                #-- Select the locker
                self.lcd.clear()
                self.lcd.set_cursor(0, 0)
                self.lcd.message(" Select locker ")
                lockID = 0
                mod = len(self.relayList)
                while True:
                    self.lcd.set_cursor(0, 1)
                    self.lcd.message('     \x03 %02d \x04     ' % (lockID + 1))
                    if self.lcd.is_pressed(LCD.LEFT) or self.lcd.is_pressed(LCD.DOWN):
                        lockID = (lockID - 1 + mod) % mod
                    elif self.lcd.is_pressed(LCD.RIGHT) or self.lcd.is_pressed(LCD.UP):
                        lockID = (lockID + 1) % mod
                    elif self.lcd.is_pressed(LCD.SELECT):
                        break
                    time.sleep(0.04)
                GPIO.setup(self.relayList[lockID], GPIO.OUT)
                time.sleep(3.0)
                GPIO.setup(self.relayList[lockID], GPIO.IN)

        except ExitCommand, reason:
            time.sleep(1)
            self.lcd.clear()
            self.lcd.set_color(1, 0, 0)
            if int(str(reason)) == signal.SIGINT:
                if self.debugFlag:
                    print >> sys.stderr, "Worker gets terminated..."
                self.printLCD(0, 'c', "Terminated")
                self.printLCD(1)
                time.sleep(1)
                sys.exit(100)
            else:
                if self.debugFlag:
                    print >> sys.stderr, "RasPI gets rebooted..."
                self.printLCD(0, 'c', "Rebooting")
                self.printLCD(1)
                time.sleep(1)
                os.system('reboot')





