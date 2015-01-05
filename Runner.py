import time
import Worker
import Assassin

if __name__ == '__main__':
    # Create instances of classes
    W = Worker.Worker()
    Assassin.Assassin(W).start()
    # Wait for LCD screen to settle down
    time.sleep(1)
    # Run main loop
    W.doIt()

