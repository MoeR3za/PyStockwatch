from threading import Thread
from time import sleep, time

import pandas_datareader as fetch

from ._db_control import TableControl


class DataControl():
    """
    Class DataControl is a data controller object for a DisplayWindow object, it organizes the processes
        of table reading/writing and updating data on the symbol data display window.
    The class is designed to act as an engine, once started, two parallel threads for time generation
        and data generation are created, each thread runs a loop that keeps generating and updating data
        as long as the primary switch variable is True AND the window exists as a secondary kill switch.
    """

    def __init__(self, db_con, timeKeep):
        """
        DataControl contstructor

        Args:
            db_con (MainControl object): a MainControl database connection object
            timeKeep (TimeKeep object): a Time Keep object
        """
        print(f'>>> [{self.sym}]: INITIALIZING DATA CONTROL')
        # primary switch flag for time and data generators
        self.alive = True
        # reference timeKeep as an instance variable
        self.timeKeep = timeKeep
        # initialize database table control using passed database connection
        self.db = TableControl(self.sym, db_con, timeKeep)
        # instance varialbe of the current data in the table after initialization
        self.dbRead = self.db.read_table()
        # instance boolean variable of whather the market is open or closed
        self.msbool = None

    def start_engine(self):
        """
        Instance methos start_engine() is called to, well, start the engine.
        It creates a first thread that runs __timeGen(), and a second thread
            that runs __dataGet(), separately.
        The threads are started in daemon mode so they die on exceptions and returns.
        """
        print(f'>> [{self.sym}]: STARTING ENGINE')
        timeThread = Thread(target=self.__timeGen, daemon=True)
        timeThread.start()

        dataThread = Thread(target=self.__dataGen, daemon=True)
        dataThread.start()

    def stop_engine(self):
        """
        Instance function stop_engine() kills running threads by
            setting the primary switch to False so the loops break.
        """
        self.alive = False

    def __timeGen(self):
        """
        Private instance method __timeGen() starts a loop that runs as long as
            the primary switch == True, the loop body uses timeKeep object to keep track of time
            and update time in the display window once every 1 second.
        This part is designed to apply the changes directly so the time updates
            remains as accurate as possible no matter the amount of calls made to other instance methods
            in the display window object, or how long they take to run. 
        """
        print(f'>> [{self.sym}]: Starting time generator')
        while self.alive:
            self.msBool = self.timeKeep.msBool
            # The try except statements on data update act as secondary switches to kill the loop
            # in case the window is closed before a call to stop_engine() is made
            try:
                self.localTimeVal.set(self.timeKeep.localTime)
                self.localDateVal.set(self.timeKeep.localDate)
                # special case for estTimeVal to be set
                # at close time when market is closed
                if self.msBool == True:
                    self.estTimeVal.set(f'| {self.timeKeep.estTime} EST')
                    self.marketStatusVal.set('Markets Are Open')
                    self.marketStatusDisp.config(fg='green')
                elif self.msBool == False:
                    self.estTimeVal.set('| 16:00:00 EST')
                    self.asOf.config(text='At Close:')
                    self.marketStatusVal.set('Markets Are Closed')
                    self.marketStatusDisp.config(fg='red')
            except Exception as e:
                print(
                    f'>> [{self.sym}]: time generator terminated - secondary switch triggered')
                return
            sleep(1)

        # debug print
        print(
            f'>> [{self.sym}]: time generator terminated - primary switch triggered')
        return

    # DATA GENERATOR
    def __dataGen(self):
        """
        Private instance method __dataGen() starts a loop that runs as long as
            the primary switch == True, the loop body fetches necessery data and makes
            calls to database to update and read table, and then makes calls to update_window()
            to display the newly fetched data.
        The loop is controlled with multiple switches to fetch data only once when
            the market is closed to prevenet unnecessary requests.
        """
        print(f'>> [{self.sym}]: Starting data generator')
        self.update_status(status='Fetching Data..')

        first_run = True
        refetch = 1
        self.latestClose = ''
        while self.alive:
            if refetch == 1:
                start_time = time()
                self.update_status(status='Fetching Data..')
                connected = False
                # Attempt to make connection 3 times before deciding there's a connection error
                # I am aware that the error here might not be a connection error due to other
                # function calls made by called functions, so, fingers crossed.
                for i in range(1, 4):
                    try:
                        # fetch company name and some other data (ask/bid)
                        self.yahooQuote = fetch.data.get_quote_yahoo(
                            self.sym)
                        # on the first iteration, update name and write table
                        if first_run:
                            self.update_name()
                            self.db.write_table()
                        # on the remaining of the iterations, update last entry in the table
                        else:
                            self.db.update_last()

                        # read table
                        self.dbRead = self.db.read_table()

                        # At this point we know a connection has been made
                        # set connected to True and break from connection attempts loop
                        connected = True
                        break

                    except Exception as e:
                        # On exception, update status.
                        self.update_status(status='Error..')
                        print(repr(e))
                        sleep(0.5)

                        self.update_status(status=f'Error.. Retrying..{i}')
                        sleep(0.5)

                # if a connection has been made, set Status and Interval updates
                if connected:
                    # The try except statements on data update act as secondary switches to kill the loop
                    # in case the window is closed before a call to stop_engine() is made
                    try:
                        self.update_window(first_run)
                        self.update_status(intervalUpdate=start_time, status='Data Fetched')
                    except Exception as e:
                        print(
                            f'>> [{self.sym}]: data generator terminated - secondary switch triggered')
                # if no connection, update status to Connection Error
                else:
                    self.update_status(
                        status='Error: Unable to fetch data')
                    print(
                            f'>> [{self.sym}]: data generator terminated - secondary switch triggered')
                    raise ConnectionError

                first_run = False
            # if market is closed, update status instead of refetching data.
            else:
                self.update_status(
                    intervalUpdate='Off', status='Market Closed, Auto Update Disabled')

            # set refetch to market status
            refetch = self.msBool
            sleep(1)

        # debug print
        print(
            f'>> [{self.sym}]: data generator terminated - primary switch triggered')
        return
