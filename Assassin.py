import Adafruit_CharLCD as LCD
import threading, time, sys

class Assassin(threading.Thread):
    def __init__(self, Worker):
        threading.Thread.__init__(self, name = 'Assassin')
        self.lcd = LCD.Adafruit_CharLCDPlate()
        self.Worker = Worker
    def run(self):
        wdTimer = 0
        while True:
            time.sleep(0.5)
            if self.lcd.is_pressed(LCD.SELECT):
                wdTimer += 1
            else:
                wdTimer = 0
            if wdTimer > 5:
                wdTimer = 0
                print >> sys.stderr, 'Worker thread gets restarted...'
                self.Worker._Thread__stop()




