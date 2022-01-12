from time import sleep, time
from tkinter import *
from tkinter import ttk

from dateutil.relativedelta import relativedelta
from numerize import numerize

from ._data_control import DataControl
from ._helper_toolbox import ToolTip, diffCalc
from ._plot_graph import PlotGraph


class DisplayWindow(Toplevel, DataControl):
    """
    Class that represents a given symbol display window where data on the symbol is displayed, neatly enough,
        with emphasize on changing data such as Close price during market time.
    The class extends superclass DataControl that controls the data updates in object from outside(?) through
        instance methods update_name(), update_window(), and update_status().
    """

    def __init__(self, parent, sym, **kwargs):
        # create a display window with geometry
        # the initialization is designed to take
        # xLeft and yTop as named optional arguments
        print(f'>>> [{sym}]: INITIALIZING DISPLAY WINDOW')
        Toplevel.__init__(self, master=parent)
        self.protocol("WM_DELETE_WINDOW", self.__close_window)
        self.sym = sym
        self.title(sym)
        xLeft = kwargs['xLeft'] if 'xLeft' in kwargs else int(
            self.winfo_screenwidth() / 3)
        yTop = kwargs['yTop'] if 'yTop' in kwargs else int(
            self.winfo_screenheight() / 4)

        self.geometry("+{}+{}".format(xLeft, yTop))
        self.resizable(False, False)

        # initialize data control
        DataControl.__init__(self, parent.db_con, parent.timeKeep)

        # # show window and start engine
        self.__run_displayWindow()
        self.start_engine()

    def __run_displayWindow(self):
        """
        Instance method __run_displayWindow() creates children widgets
            to represent different fields of data, as well as local date/time
            and EST timezone date/time (timezone of the stock market)
        The destribution of widgets is set to be dynmic just enough as needed
        """
        # Define different tkinter variables to hold data,
        # each tkinter variable is linked to a label widget
        # that displays the value of the variable
        # Only time variables are not private becuase
        # they are controlled by timeGen() in DataControl
        ##### MISC VARS #####
        self.__compVar = StringVar()
        self.__compVar.set('...')
        self.__exchVar = StringVar()
        self.__statusVal = StringVar()
        self.__statusVal.set('...')
        self.__intervalVal = StringVar()
        self.__intervalVal.set('0')

        ##### TIME VARS #####
        self.localTimeVal = StringVar()
        self.localDateVal = StringVar()
        self.estTimeVal = StringVar()
        self.estDateVal = StringVar()
        self.marketStatusVal = StringVar()

        ##### DATA VARIABLES #####
        self.__openVal = StringVar()
        self.__closeVal = StringVar()
        self.__dayRangeVal = StringVar()
        self.__volVal = StringVar()
        self.__prevcloseVal = StringVar()
        self.__fiftyTwoVal = StringVar()
        self.__diffVal = StringVar()
        self.__avgVolVal = StringVar()
        self.__askVal = StringVar()
        self.__bidVal = StringVar()
        self.__marketCapVal = StringVar()

        valVarList = [
            self.__openVal,
            self.__closeVal,
            self.__dayRangeVal,
            self.__volVal,
            self.__prevcloseVal,
            self.__fiftyTwoVal,
            self.__diffVal,
            self.__avgVolVal,
            self.__askVal,
            self.__bidVal,
            self.__marketCapVal]

        for valVar in valVarList:
            valVar.set('------')
        self.marketStatusVal.set('Loading...')

        ##########################################################
        ################# DISPLAY WINDOW WIDGETS #################
        ##########################################################
        # create window children
        # I chose to pack most widgets immediately after their definitions
        # to split the design code intro separate chuncks considering
        # the relativity and relationship between widgets
        mainFrame = Frame(self, width=350, bd=2, relief=RIDGE)
        mainFrame.pack(fill=BOTH, expand=1)

        # frame for top time and date bar widgets
        timeFrameBar = Frame(mainFrame, bd=2, bg='gray70', relief=GROOVE)
        timeFrameBar.pack(fill=X)
        timeFrame = Frame(timeFrameBar)
        timeFrame.pack()

        localTimeAndDate = Label(
            timeFrame, text='Local Date & Time:', bd=2, bg='gray70')
        localDate = Label(
            timeFrame, textvariable=self.localDateVal, bd=2, bg='gray70')
        localSep = Label(timeFrame, text=' | ', bd=2, bg='gray70')
        localTime = Label(
            timeFrame, textvariable=self.localTimeVal, bd=2, bg='gray70')
        localTimeAndDate.pack(side=LEFT)
        localDate.pack(side=LEFT)
        localSep.pack(side=LEFT)
        localTime.pack(side=LEFT)

        # Frame for main info on the symbol.
        # Data in this frame is controlled by instance method update_name()
        mainInfoFrame = Frame(mainFrame)
        mainInfoFrame.pack(fill=X)

        # the mainInfoFrame is split into 3 frames
        # one vertical frame on top, and 2 parallel
        # horizontal frames below the top frame
        compNameFrame = Frame(mainInfoFrame)
        compNameFrame.pack(fill=X)
        rightInfoFrame = Frame(mainInfoFrame)
        rightInfoFrame.pack(fill=X, side=RIGHT, padx=20)
        leftInfoFrame = Frame(mainInfoFrame)
        leftInfoFrame.pack(fill=X, side=LEFT, padx=20)

        # company name and exchange labels in top frame
        CompLabel = Label(compNameFrame, textvariable=self.__compVar,
                          font=("Times", 22))
        CompLabel.pack(side=TOP, anchor=CENTER)
        exchDisp = Label(compNameFrame, textvariable=self.__exchVar,
                         font=('Times', 12, 'bold'))
        exchDisp.pack(anchor=CENTER)

        # frame for current and previous prices as well as the difference
        PriceFrame = Frame(leftInfoFrame)
        PriceFrame.pack()
        self.currPrice = Label(PriceFrame, textvariable=self.__closeVal, font=(
            'bold', 15), width=8, fg='blue', height=1, anchor=N)
        self.diffLabel = Label(
            PriceFrame, textvariable=self.__diffVal, font=('bold', 14))
        self.currPrice.pack(side=LEFT, anchor=W)
        self.diffLabel.pack(side=LEFT, anchor=W)

        # MarketStatus is here before the time and date because
        # the first to have the side as bottom will take the place.
        self.marketStatusDisp = Label(
            rightInfoFrame, textvariable=self.marketStatusVal, font=('Times', 12))
        self.marketStatusDisp.pack(side=BOTTOM, anchor=CENTER)

        # Frame for EST timezone time and date
        # the data will always be set to the last data update
        estDT = Frame(leftInfoFrame)
        estDT.pack(side=BOTTOM, anchor=CENTER)
        self.asOf = Label(estDT, text='as of', font=('Times', 12))
        estDateDisp = Label(
            estDT, textvariable=self.estDateVal, font=('Times', 12))
        estTimeDisp = Label(
            estDT, textvariable=self.estTimeVal, font=('Times', 12))
        self.asOf.pack(side=LEFT, anchor=W)
        estDateDisp.pack(side=LEFT, anchor=W)
        estTimeDisp.pack(side=LEFT, anchor=W)

        # separator between top
        sep = ttk.Separator(mainFrame)
        sep.pack(fill=X, pady=5)

        # ##########################################################################
        # ######################### BEGINNING OF THE TABLE #########################
        # ##########################################################################
        # Details frame, for details on the symbol
        # the frame is designed to look like a table
        # split into two left and right frames.
        # The data in this frame is controlled by instance method update_window()
        mainDetailsFrame = Frame(mainFrame)
        mainDetailsFrame.pack(fill=X)

        detailsFrame = Frame(mainDetailsFrame)
        detailsFrame.pack(fill=X)

        # left and right frames
        leftDetailsFrame = Frame(detailsFrame)
        leftDetailsFrame.pack(fill=X, side=LEFT, expand=1, padx=3)

        sep = ttk.Separator(detailsFrame, orient=VERTICAL)
        sep.pack(fill=Y, padx=2, side=LEFT, anchor=CENTER)

        rightDetailsFrame = Frame(detailsFrame)
        rightDetailsFrame.pack(fill=X, side=RIGHT, expand=1, padx=3)

        # A frame is declared to contain each value
        # this was due to the fact that the value
        # and its label are actually two labels
        prevCloseFrame = Frame(leftDetailsFrame, height=25)
        prevCloseFrame.pack(fill=X, expand=1)
        prevCloseLabel = Label(
            prevCloseFrame, text='Previous Close: ', anchor=W)
        prevcloseValue = Label(prevCloseFrame, textvariable=self.__prevcloseVal, height=1,
                               anchor=NE)
        prevCloseLabel.pack(side=LEFT)
        prevcloseValue.pack(side=RIGHT)

        # Frames are separated by separators
        sep = ttk.Separator(leftDetailsFrame)
        sep.pack(fill=X, pady=3)

        openFrame = Frame(leftDetailsFrame, height=25)
        openFrame.pack(fill=X, expand=1)
        openLabel = Label(openFrame, text='Open: ', anchor=W)
        openValue = Label(openFrame, textvariable=self.__openVal, height=1,
                          anchor=NE)
        openLabel.pack(side=LEFT)
        openValue.pack(side=RIGHT)

        sep = ttk.Separator(leftDetailsFrame)
        sep.pack(fill=X, pady=3)

        askFrame = Frame(leftDetailsFrame, height=25)
        askFrame.pack(fill=X, expand=1)
        askLabel = Label(askFrame, text='Ask: ', anchor=W)
        askValue = Label(askFrame, textvariable=self.__askVal, height=1,
                         anchor=NE)
        askLabel.pack(side=LEFT)
        askValue.pack(side=RIGHT)

        sep = ttk.Separator(leftDetailsFrame)
        sep.pack(fill=X, pady=3)

        bidFrame = Frame(leftDetailsFrame, height=25)
        bidFrame.pack(fill=X, expand=1)
        bidLabel = Label(bidFrame, text='Bid: ', anchor=W)
        bidValue = Label(bidFrame, textvariable=self.__bidVal, height=1,
                         anchor=NE)
        bidLabel.pack(side=LEFT)
        bidValue.pack(side=RIGHT)

        sep = ttk.Separator(leftDetailsFrame)
        sep.pack(fill=X, pady=3)

        dayRangeFrame = Frame(rightDetailsFrame, height=25)
        dayRangeFrame.pack(fill=X, expand=1)
        dayRangeLabel = Label(dayRangeFrame, text='Day\'s Range: ', anchor=W)
        dayRangeValue = Label(dayRangeFrame, textvariable=self.__dayRangeVal, height=1,
                              anchor=NE)
        dayRangeLabel.pack(side=LEFT)
        dayRangeValue.pack(side=RIGHT)

        sep = ttk.Separator(rightDetailsFrame)
        sep.pack(fill=X, pady=3)

        fiftyTwoWeeksFrame = Frame(rightDetailsFrame, height=25)
        fiftyTwoWeeksFrame.pack(fill=X, expand=1)
        fiftyTwoWeeksLabel = Label(
            fiftyTwoWeeksFrame, text='52 Weeks Range: ', anchor=W)
        fiftyTwoWeeksValue = Label(fiftyTwoWeeksFrame, textvariable=self.__fiftyTwoVal, height=1,
                                   anchor=NE)
        fiftyTwoWeeksLabel.pack(side=LEFT)
        fiftyTwoWeeksValue.pack(side=RIGHT)

        sep = ttk.Separator(rightDetailsFrame)
        sep.pack(fill=X, pady=3)

        volFrame = Frame(rightDetailsFrame, height=25)
        volFrame.pack(fill=X, expand=1)
        volLabel = Label(volFrame, text='Volume: ', anchor=W)
        volValue = Label(volFrame, textvariable=self.__volVal, height=1,
                         anchor=NE)
        volLabel.pack(side=LEFT)
        volValue.pack(side=RIGHT)

        sep = ttk.Separator(rightDetailsFrame)
        sep.pack(fill=X, pady=3)

        avgVolFrame = Frame(rightDetailsFrame, height=25)
        avgVolFrame.pack(fill=X, expand=1)
        avgVolLabel = Label(avgVolFrame, text='Avg. Volume: ', anchor=W)
        avgVolValue = Label(avgVolFrame, textvariable=self.__avgVolVal, height=1,
                            anchor=NE)
        avgVolLabel.pack(side=LEFT)
        avgVolValue.pack(side=RIGHT)

        sep = ttk.Separator(rightDetailsFrame)
        sep.pack(fill=X, pady=3)

        # The market cap frame widget is added to mainDetailsFrame
        # to be able to put it in the bottom center of the table
        marketCapFrame = Frame(mainDetailsFrame, height=25)
        marketCapFrame.pack(side=BOTTOM)
        marketCapLabel = Label(marketCapFrame, text='Market Cap.: ', anchor=W)
        marketCapValue = Label(marketCapFrame, textvariable=self.__marketCapVal, height=1,
                               anchor=NE)
        marketCapLabel.pack(side=LEFT)
        marketCapValue.pack(side=RIGHT)

        # Frame for graph data plot
        # The frame is empty because the plot is controlled
        # by a different class.
        self.graphFrame = Frame(mainFrame, bd=2)
        self.graphFrame.pack()

        # Frame for status bar
        # The data in the status bar is controlled by update_status() instance method
        statusBarFrame = Frame(mainFrame, bd=2, bg='gray70', relief=GROOVE)
        statusBarFrame.pack(fill=X, side=BOTTOM)

        statusDisp = Label(
            statusBarFrame, textvariable=self.__statusVal, bg='gray70', anchor=W)
        statusDisp.pack(side=LEFT)
        ToolTip(statusDisp, text='Update Status.')

        intervalDisp = Label(
            statusBarFrame, textvariable=self.__intervalVal, anchor=E, bg='gray70')
        intervalDisp.pack(side=RIGHT)
        ToolTip(intervalDisp, text='Update Interval (Perdion between each update in seconds).'
                '\nNote: This period is dependant on your internet connection speed.')

        sep2 = ttk.Separator(statusBarFrame, orient=VERTICAL)
        sep2.pack(padx=10, side=RIGHT, fill=Y)

        # Frame for a quit button
        # I decided to not include a close button in later stages is development
        # so.. depricated :D
        # quitFrame = Frame(mainFrame)
        # quitFrame.pack(fill=X, side=BOTTOM, pady=5, padx=5)
        # quitButton = Button(quitFrame, text='Close', font=(
        #     'bold'), command=lambda: self.close_window(), fg='red', bd=2)
        # quitButton.pack(side=RIGHT)

    def update_name(self):
        """
        Instance method update_name() updates values of name and exchange
            besed on an attribute defined and controlled by the DataControl class
        """
        compLongName = self.yahooQuote['longName'].to_string(
            index=False, header=False)
        compFullExch = self.yahooQuote['fullExchangeName'].to_string(
            index=False, header=False)

        self.__compVar.set(compLongName)
        self.__exchVar.set(f'({compFullExch}: ' + self.sym + ')')

    def update_window(self, first_run):
        """
        Instance method update_window() updates values of fields in the data table
            besed on an attributes defined and controlled by the DataControl class
        """
        # declare a variable for each data field value
        ask = self.yahooQuote['ask'].to_string(
            index=False, header=False)
        askSize = self.yahooQuote['askSize'].to_string(
            index=False, header=False)
        bid = self.yahooQuote['bid'].to_string(
            index=False, header=False)
        bidSize = self.yahooQuote['bidSize'].to_string(
            index=False, header=False)
        marketCap = self.yahooQuote['marketCap'].to_string(
            index=False, header=False)

        lastEntry = self.dbRead.tail(1)
        prevLastEntry = self.dbRead.tail(2).head(1)

        lastEntryDate = lastEntry.index.item()
        lastEntryDateStr = lastEntryDate.strftime('%Y-%m-%d')
        self.estDateVal.set(lastEntryDateStr)

        FTWeeksDate = lastEntryDate - \
            relativedelta(weeks=52) - relativedelta(days=1)
        FTWeeksHigh = self.dbRead['High'].loc[FTWeeksDate:]
        FTWeeksLow = self.dbRead['Low'].loc[FTWeeksDate:]
        # VolumeAvgDate = lastEntryDate - relativedelta(months=3) - relativedelta(days=1)
        VolumeAvgColumn = self.dbRead['Volume']

        Close = lastEntry['Close'].to_string(
            header=False, index=False)
        Open = lastEntry['Open'].to_string(
            header=False, index=False)
        High = lastEntry['High'].to_string(
            header=False, index=False)
        Low = lastEntry['Low'].to_string(
            header=False, index=False)
        Volume = lastEntry['Volume'].to_string(
            header=False, index=False).replace('.0', '')
        prevclose = prevLastEntry['Close'].to_string(
            header=False, index=False)
        FTWeeksMax = FTWeeksHigh.max()
        FTWeeksMin = FTWeeksLow.min()

        # this mini function takes a value
        # and returns a USD formatted string
        def usd(value): return f'$ {float(value):.2f}'

        # set values of previously linked tkinter variables
        # to new values of variables declared above
        self.__closeVal.set(usd(Close))
        self.__dayRangeVal.set(f'{usd(Low)} - {usd(High)}')
        self.__openVal.set(usd(Open))
        vol = f'{int(Volume):,}'
        self.__volVal.set(vol)
        self.__prevcloseVal.set(usd(prevclose))
        self.__fiftyTwoVal.set(f'{usd(FTWeeksMin)} - {usd(FTWeeksMax)}')
        volAvg = f'{sum(VolumeAvgColumn) / len(VolumeAvgColumn):,.0f}'
        self.__avgVolVal.set(volAvg)
        self.__askVal.set(f'{usd(ask)} x {askSize}00')
        self.__bidVal.set(f'{usd(bid)} x {bidSize}00')
        # self.__marketCapVal.set(f'$ {format(int(marketCap), ",")}')
        self.__marketCapVal.set(f'$ {numerize.numerize(int(marketCap), 3)}')


        # set difference to value returned from call to diffCalc
        diff = diffCalc(float(Close), float(prevclose))

        # set color of price difference to green or red
        # depending on whether the difference is incremental
        # or decremental respectively
        if '+' in diff:
            self.diffLabel.config(fg='green')
        elif '-' in diff:
            self.diffLabel.config(fg='red')
        self.__diffVal.set(diff)

        # while the market is open
        # apply a flashing effect on the price label
        # according to the change from last update
        if Close > self.latestClose:
            self.__flash_diff('green')
        elif Close < self.latestClose:
            self.__flash_diff('red')

        # this variable holds the close value of this iteration (update)
        # it is used in the next iteration for the flash effect
        self.latestClose = Close

        # if this is the first time the function is called
        # create a PlotGraph object and draw it
        if first_run:
            plot = PlotGraph(self)
            try:
                plot.plot_graph()
            except Exception as e:
                print(repr(e))
                raise e

    def update_status(self, **kwargs):
        """
        Instance method update_status() updates status fields besed on
            provided named arguments ('interval: float()' or 'status: str()').
        """
        if 'intervalUpdate' in kwargs:
            interval = kwargs['intervalUpdate']
            if isinstance(interval, str):
                self.__intervalVal.set('0')
            elif isinstance(interval, float):
                end_time = time()
                time_lapsed = end_time - interval
                sec = time_lapsed % 60
                self.__intervalVal.set(
                    str('Update Interval: {:.2f}s'.format(sec)))

        if 'status' in kwargs:
            self.__statusVal.set(kwargs['status'])

    def __flash_diff(self, change_color):
        """
        Private instance method __flash_diff() takes either 'green' or 'red'
            and applies a flash effect on the by rapidly changing its background color
            to 4 different shades of the given color
        """
        root_color = self.cget('background')
        if change_color == 'green':
            GREENSHADES = ['green3', 'green2', 'green1', 'pale green']
            for color in GREENSHADES:
                self.currPrice.config(bg=color)
                sleep(0.1)
            self.currPrice.config(bg=root_color)
        elif change_color == 'red':
            REDSHADES = ['red3', 'red2', 'red1', 'light salmon']
            for color in REDSHADES:
                self.currPrice.config(bg=color)
                sleep(0.1)
            self.currPrice.config(bg=root_color)

    def __close_window(self):
        """
        Private instance method __close_winow() to be called on window close
            for cleanup such as to stop DataControl engine
            so the application exits gracefully
        """
        self.stop_engine()
        self.destroy()
