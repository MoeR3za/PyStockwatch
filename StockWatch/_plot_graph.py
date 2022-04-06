
from tkinter import (CENTER, LEFT, RIGHT, TOP, BooleanVar, Button, Checkbutton,
                     Entry, Frame, IntVar, Label, StringVar, ttk)

import matplotlib
import mplfinance as mpf
import pandas as pd
from dateutil.relativedelta import relativedelta
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from mplfinance.plotting import plot

from ._helper_toolbox import ToolTip

matplotlib.use('agg')


class PlotGraph():
    """
    Class PlotGraph represents a graph plot of the data of a symbol,
        it should only be initialized after the data engine has started and a data read is available

    """

    def __init__(self, control):
        """
        PlotGraph object constructor.

        Args:
            control (DisplayWindow object): a tkinter DisplayWindow object that has a frame "graphFrame" declared and packed
        """
        # debug print
        print(f'>> [{control.sym}]: Plotting data')

        self.control = control

        # plot style
        self.myStyle = mpf.make_mpf_style(base_mpf_style='starsandstripes', rc={'font.size': 8}, y_on_right=False,
                                          gridstyle=':', gridcolor='grey')
        # first date from available data
        firstEntry = self.control.dbRead.head(1).index.item()
        firstEntryDate = pd.to_datetime(str(firstEntry).split()[0])

        # last date from available data
        lastEntry = self.control.dbRead.tail(1).index.item()
        self.lastEntryDate = pd.to_datetime(str(lastEntry).split()[0])

        # start date for different periods of time
        oneMonth = self.lastEntryDate - relativedelta(months=1)
        threeMonths = self.lastEntryDate - relativedelta(months=3)
        sixMonths = self.lastEntryDate - relativedelta(months=6)
        oneYear = self.lastEntryDate - relativedelta(years=1)
        threeYears = self.lastEntryDate - relativedelta(years=3)
        max = firstEntryDate

        self.periodsList = [oneMonth, threeMonths,
                            sixMonths, oneYear, threeYears, max]

        # default values of plot configurations
        self.plotConf = {
            'startDate': oneMonth,
            'type': 'line',
            'mav': 2
        }

    def _replot(self, plotData=None):
        """
        Private instance method _replot() replots data graph to the provided Dataframe

        Args:
            plotData (Dataframe, optional): timeseries dataframe to plot. Defaults to None.
        """
        if plotData is None:
            plotData = self.control.dbRead.loc[self.plotConf['startDate']                                               :self.lastEntryDate]

        # clear axs
        self.ax1.clear()
        self.ax2.clear()

        # replot with new data
        # the following code is split into two branches because if mav is provided, it must be a valid value
        # and cannot take None or False as values to ignore drawing a mav line
        if self.plotConf['mav'] == False:
            mpf.plot(plotData, ax=self.ax1, volume=self.ax2, returnfig=True, type=self.plotConf['type'],
                     xrotation=15, tight_layout=True, style=self.myStyle)
        else:
            mpf.plot(plotData, ax=self.ax1, volume=self.ax2, returnfig=True, type=self.plotConf['type'], mav=self.plotConf['mav'],
                     xrotation=15, tight_layout=True, style=self.myStyle)

        self.canvas.draw_idle()

    def _custom_replot(self):
        """
        Private instance method _custom_replot() is called when custom dates are entered.
        """
        try:
            startDate = pd.to_datetime(self.customStart.get())
            endDate = pd.to_datetime(self.customEnd.get())
        except Exception as e:
            self.control.update_status(status='error with custom date')
            print(repr(e))
            return

        plotData = self.control.dbRead.loc[startDate:endDate]
        self._replot(plotData)

    def _update_plotCont(self, event):
        """
        Private instance method _update_plotCont() handles plot control events
        based on where the events originated from.

        Args:
            event (event): Plot control widgets event
        """
        # if the event originated from a period box selection
        if event.widget._name == 'periodBox':
            if event.widget.get() == 'Custom':
                self.customStart.set(
                    self.plotConf['startDate'].strftime('%Y-%m-%d'))
                self.customEnd.set(self.lastEntryDate.strftime('%Y-%m-%d'))
                self.customPeriodFrame.pack()
            else:
                self.customPeriodFrame.pack_forget()
                self.plotConf['startDate'] = self.periodsList[event.widget.current()]

        # if the event originated from a type box selection
        elif event.widget._name == 'typeBox':
            self.plotConf['type'] = event.widget.get()

        self._replot()

    def _update_mav(self, event=None):
        """
        Private instance method _update_mav() handles events from mav widgets, it updates
            the moving average line in the plot as it is changed, the value for mav can be changed
            with direct value input, or keyboard Up and Down buttons, as well as enabling/disabling
            mav line from the checkbox.

        Args:
            event (event, optional): a mav widget event. Defaults to None.
        """
        # nested function sets mav to 2 as a default if invalid entry
        def _mavCheck():
            try:
                m = self.mavInputVal.get()
            except:
                m = 2
            finally:
                if m < 2:
                    m = 2
                    self.mavInputVal.set(m)
            return m

        # if the function was called with an event
        if event:
            key = event.keysym
            if key == 'Backspace':
                return
            mavVal = _mavCheck()
            if key == 'Up':
                mavVal = mavVal + 1
                self.mavInputVal.set(mavVal)
            elif key == 'Down':
                # special case to do nothing when mav is already at minimum (2)
                if mavVal == 2:
                    return
                else:
                    mavVal = mavVal - 1
                    self.mavInputVal.set(mavVal)

        # enable/disable update mav values in plotConf according to mav checkbox
        if self.mavCheck.get():
            self.mavInput.config(state='normal')
            self.plotConf['mav'] = _mavCheck()
        else:
            self.plotConf['mav'] = False
            self.mavInput.config(state='disabled')

        self._replot()

    def plot_graph(self):
        """
        Instance method to draw a graph plot and add it to the control window graphFrame frame.
        """
        
        graphControlFrame = Frame(self.control.graphFrame)
        graphControlFrame.pack()

        mainControlFrame = Frame(graphControlFrame)
        mainControlFrame.pack()

        # Period control
        periodBox = ttk.Combobox(mainControlFrame, name='periodBox', values=[
            '1-Month', '3-Months', '6-Months', '1-Year', '3-Years', 'Max', 'Custom'])
        periodBox.current(0)
        periodBox.bind('<<ComboboxSelected>>',
                       lambda event: self._update_plotCont(event))
        periodBox.pack(pady=5, padx=15, side=LEFT)
        ToolTip(periodBox, text='Plot Period')

        # Moving average control
        self.mavInputVal = IntVar(value=2)
        self.mavInput = Entry(mainControlFrame, justify=CENTER,
                              textvariable=self.mavInputVal, width='4')
        self.mavInput.pack(pady=5, side=LEFT)
        self.mavInput.bind(
            '<KeyRelease>', lambda event: self._update_mav(event))
        ToolTip(self.mavInput, text='Moving Average')

        self.mavCheck = BooleanVar(value=True)
        mavCheckBtn = Checkbutton(mainControlFrame, text='mav',
                                  variable=self.mavCheck, command=lambda: self._update_mav())
        mavCheckBtn.pack(pady=5, side=LEFT)

        # Plot type control
        typeBox = ttk.Combobox(mainControlFrame, name='typeBox', values=[
                               'line', 'candle', 'ohlc'])
        typeBox.current(0)
        typeBox.bind('<<ComboboxSelected>>',
                     lambda event: self._update_plotCont(event))
        typeBox.pack(pady=5, padx=15, side=RIGHT)
        ToolTip(typeBox, text='Plot Type')

        ## Custom period frame ##
        self.customPeriodFrame = Frame(graphControlFrame)

        self.customStart = StringVar()
        self.customEnd = StringVar()

        startInput = Entry(self.customPeriodFrame, justify=CENTER,
                           textvariable=self.customStart, width=12)
        startInput.pack(side=LEFT)
        ToolTip(startInput, text='Start Date')

        colonSeparator = Label(self.customPeriodFrame, text=":")
        colonSeparator.pack(side=LEFT)

        endInput = Entry(self.customPeriodFrame, justify=CENTER,
                         textvariable=self.customEnd, width=12)
        endInput.pack(side=LEFT)
        ToolTip(endInput, text='End Date')

        customPlotBtn = Button(
            self.customPeriodFrame, text='replot', command=lambda: self._custom_replot())
        customPlotBtn.pack(side=LEFT)

        # draw initial data plot
        start_date = self.periodsList[0]
        end_date = self.lastEntryDate

        plotData = self.control.dbRead.loc[start_date:end_date]
        plotFig, axlist = mpf.plot(plotData, volume=True, returnfig=True, figsize=(6, 3), type=self.plotConf['type'], mav=self.plotConf['mav'],
                                   title=self.control.sym.upper(), xrotation=15, tight_layout=True, style=self.myStyle)
        self.ax1 = axlist[0]
        self.ax2 = axlist[2]

        self.canvas = FigureCanvasTkAgg(
            plotFig, master=self.control.graphFrame)
        self.canvas.draw()

        toolbar = NavigationToolbar2Tk(
            self.canvas, self.control.graphFrame, pack_toolbar=True)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=TOP, anchor='sw')
