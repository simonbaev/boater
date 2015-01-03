import Worker
import Assassin

if __name__ == '__main__':
    W = Worker.Worker()
    Assassin.Assassin(W).start()
    W.doIt()

