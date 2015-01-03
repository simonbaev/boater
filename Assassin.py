import Adafruit_CharLCD as LCD
import threading, time, os, signal, sys

class Assassin(threading.Thread):
    def __init__(self, Worker):
        threading.Thread.__init__(self, name = 'Assassin')
        self.Worker = Worker
        self.daemon = True
    def run(self):
        wdTimer = 0
        try:
            while True:
                time.sleep(0.5)
                if self.Worker and self.Worker.lcd.is_pressed(LCD.SELECT):
                    wdTimer += 1
                else:
                    wdTimer = 0
                if wdTimer > 5:
                    os.kill(os.getpid(), signal.SIGINT)
        except:
            pass
        finally:
            print >> sys.stderr, 'Bla-Bla-Bla'




