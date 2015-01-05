import Adafruit_CharLCD as LCD
import threading, time, os, signal, sys

class Assassin(threading.Thread):
    def __init__(self, Worker):
        threading.Thread.__init__(self, name = 'Assassin')
        self.Worker = Worker
        self.daemon = True
    def run(self):
        terminateTimer = 0
        rebootTimer = 0
        while True:
            time.sleep(1.0)
            # Control Termination timer
            if self.Worker and self.Worker.lcd.is_pressed(LCD.SELECT):
                terminateTimer += 1
            else:
                terminateTimer = 0
            # Control reboot timer
            if self.Worker and self.Worker.lcd.is_pressed(LCD.LEFT) and self.Worker.lcd.is_pressed(LCD.RIGHT):
                rebootTimer += 1
            else:
                rebootTimer = 0
            # Terminate if needed
            if terminateTimer > 5:
                os.kill(os.getpid(), signal.SIGINT)
                break
            # Reboot if needed
            if rebootTimer > 5:
                os.kill(os.getpid(), signal.SIGUSR1)
                break
