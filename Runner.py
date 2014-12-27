import Worker
import Assassin

if __name__ == '__main__':
    W = Worker()
    A = Assassin(W)
    W.start()
    A.start()

