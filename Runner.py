import Worker
import Assassin

if __name__ == '__main__':
    W = Worker.Worker()
    A = Assassin.Assassin(W)
    W.start()
    A.start()

