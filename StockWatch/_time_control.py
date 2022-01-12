from datetime import date, datetime
from threading import Thread
from time import sleep

from pandas import bdate_range
from pytz import timezone


class TimeKeep():
    """
    Class TimeKeep represents a time generator object, it keeps track of local and EST timezone dates and times
        as instance attributes that can be accessed from outside.
    The class is intended to be initialized and started only once by the Main window object, and passed down
        as a shared source of time data program-wide.
    """

    def __init__(self):
        print('>>>> [MAIN]: INITIALIZING MAIN TIME GENERATOR')
        # primary switch
        self.alive = True

        # time and date attributes
        self.localTime = None
        self.localDate = None
        self.estTime = None
        self.estDate = None
        self.msBool = None

    def __time_update(self):
        """
        Private instance function __time_update() starts a loop that runs as long as
            the primary switch == True, the loop body keeps updating time and date attributes
            once every 0.1 second.
        """
        while self.alive:
            self.localTime = next(localTimeFunc())
            self.localDate = next(localDateFunc())
            self.estTime = next(estTimeFunc())
            self.estDate = next(estDateFunc())
            self.msBool = marketStatusCheck()
            sleep(0.1)
            continue
        print('>>>> [MAIN] time generator terminated - primary switch triggered')

    def start(self):
        """
        Instance method start() creates and starts a thread that runs __time_update() in daemon mode
        """
        timeThread = Thread(target=self.__time_update, daemon=True)
        timeThread.start()

    def kill(self):
        """
        Instance function kill() kills running threads by
            setting the primary switch to False so the loops break.
        """

        self.alive = False


est = timezone('EST')


# iterator functions for different times and dates
def localTimeFunc():
    while True:
        yield datetime.now().strftime("%H:%M:%S")


def localDateFunc():
    while True:
        yield date.today()


def estTimeFunc():
    while True:
        yield datetime.now(est).strftime("%H:%M:%S")


def estDateFunc():
    while True:
        yield datetime.now(est).strftime("%Y-%m-%d")


def timestamp():
    while True:
        yield datetime.now()


def marketStatusCheck():
    """
    Function marketStatusCheck() checks if the market is open based on current EST date and time

    Returns:
        Boolean: True if market is open, False if otherwise
    """
    currEstDate = next(estDateFunc())

    b_day = bool(len(bdate_range(currEstDate, currEstDate)))
    if b_day:
        if not '09:30:00' <= next(estTimeFunc()) <= '16:00:00':
            return False
        else:
            return b_day
    else:
        return b_day
