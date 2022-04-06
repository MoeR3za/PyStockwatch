import contextlib
from os import devnull
from sys import argv
from tkinter import Tk, Button, Entry, Frame, Label, StringVar

from StockWatch import MainControl, AutoComplete, Link, ToolTip, DisplayWindow, TimeKeep


class Main(Frame):
    """
    Class that represents main application window it is designed to hold central control
        over display windows, as well as time keeping and database control,
        so that all windows would update time from the same source,
        and access database on the same connection useing different scoped sessions.
    """

    def __init__(self, parent):
        """
        Main object constructor.

        Args:
            parent: root Tk() window
        """
        super().__init__(parent)
        self.parent = parent
        self.parent.protocol("WM_DELETE_WINDOW", self.__close_window)

        # declare a TimeKeep instance for time control, and start its engine
        self.timeKeep = TimeKeep()
        self.timeKeep.start()

        # declare a MainControl instance for database control
        self.db_con = MainControl()
        self.symbols = self.db_con.symbols.get_symbols()

        # create window with geometry
        self.parent.title('PyStockWatch')
        self.parent.geometry('500x250')
        xLeft = int(self.winfo_screenwidth() / 2 - 500 / 2)
        yTop = int(self.winfo_screenheight() / 2 - 250 / 2)
        self.parent.geometry("+{}+{}".format(xLeft, yTop))
        self.parent.resizable(False, False)

        # a list of dicts of 8 cells of the screen, each dict has
        # x and y keys and a key 'taken' set to False by default
        self.prtWidth = self.winfo_screenwidth()
        self.prtHeight = self.winfo_screenheight()
        self.displayGrid = [{'x': int(self.prtWidth / 4) * i if i < 4 else int(self.prtWidth / 4) * (i - 4), 'y': 0 if i < 4 else int(
            self.prtHeight / 2), 'taken': False} for i in range(8)]  # WOHOHOHO, WHAT A RIDE

        # show this window
        self.__run_mainWindow()

    def __get_display_cell(self):
        """
        Private instance method __get_display_cell() returns the next free cell dict.

        Returns:
            dict: {'x': Integer, 'y', Integer, 'taken': Boolean}
        """
        # if all cells are taken, x and y points are increased by 100 points.
        if all(cell['taken'] for cell in self.displayGrid):
            for cell in self.displayGrid:
                cell['x'] += 100
                cell['y'] += 100
                cell['taken'] = False

        # return next free cell in the list
        for cell in self.displayGrid:
            if not cell['taken']:
                cell['taken'] = True
                return cell

    def __run_mainWindow(self):
        """
        Private instance method __run_manWindow() creates children widgets
            to represent an entry field for tickers input, and
            a button to start displaying symbols data
        """
        # Create Main Frame
        mainFrame = Frame(root)
        mainFrame.pack(pady=5)

        # adding a label to the Main Frame
        compTickerLbl = Label(mainFrame, text='Company Ticker: ')
        compTickerLbl.pack(pady=1)

        # adding Entry Field
        self.symInput = Entry(mainFrame, justify='center', width=25)
        self.symInput.pack(pady=6)
        ToolTip(self.symInput,
                text='Single Symbol: msft\nMultiple Symbols: msft aapl amzn')
        AutoComplete(self.symInput, self.symbols)

        # RUN BUTTON
        runButton = Button(mainFrame, text='Check', fg='red',
                           command=lambda: self.__run(), width=10)
        runButton.pack(pady=10)

        self.errorVar = StringVar()
        ErrorLbl = Link(mainFrame, 'https://www.nyse.com/listings_directory/stock', textvariable=self.errorVar,
                        fg='red')
        ErrorLbl.pack()

        # EXIT BUTTON
        exitButton = Button(root, text='Exit', fg='red',
                            command=lambda: self.__close_window(), width=8, height=1)
        exitButton.place(anchor='s', relx=1, rely=1, y=-15, x=-65)

    def __run(self):
        """
        Private instance method __run() is called when Check button is clicked
            to handle user input, it is designed to take single inputs like "tsla"
            or multiuple inputs like "tsla msft aapl" or as many symbols as
            the user enters separated by a SPACE, then it creates a data window
            for each "CORRECT" symbol in the entry in the next free partition
        """
        symInput = self.symInput.get().upper()
        if symInput == '':
            # if input is empty, display an error label linked to nyse.com ticker list
            self.errorVar.set(
                'Please enter company ticker\n(ex. \'msft\' for Microsoft)\nClick here for more info.')
        else:
            # strip input and split it into a list
            symList = symInput.strip().split(" ")
            self.errorVar.set('')
            for symbol in symList:  # for each symbol
                symbol = symbol.upper()
                # if the symbol is not in the database (AKA incorrect)
                # display and error message
                if not any(sym == symbol for sym in self.symbols['Symbol']):
                    self.errorVar.set(
                        f'ticker "{symbol}" is not a valid ticker')
                else:
                    # if a symbol is not already opened
                    if not self.__check_symbol_opened(symbol):
                        # if it's a single symbol
                        if len(symList) == 1:
                            # Create a display window object
                            DisplayWindow(self, symbol, xLeft=int(self.prtWidth / 3), yTop=int(self.prtHeight / 6))
                        else:
                            # get next free cell and create a display window object
                            cell = self.__get_display_cell()
                            x = cell['x']
                            y = cell['y']
                            DisplayWindow(self, symbol, xLeft=x, yTop=y)

    def __check_symbol_opened(self, sym):
        """
        Private instance method __check_symbol_opened(), namely,
            takes a symbol, and returns true if a child window
            of the given symbol exists.
        """
        for child in self.children.values():
            if child.sym == sym:
                return True
        return False

    def __close_window(self):
        """
        Private instance method __close_window to be called on window close
            for cleanup such as to kill timeKeep engine
            so the application exits gracefully
        """
        # stop engine in children and kill timeKeep engine
        for child in self.children.values():
            child.stop_engine()

        self.timeKeep.kill()

        # destroy window
        root.destroy()


#################################################
if __name__ == '__main__':
    root = Tk()
    if 'silent' in argv:
        with open(devnull, "w") as f, contextlib.redirect_stdout(f):
            run = Main(root)
            root.mainloop()
    else:
        run = Main(root)
        root.mainloop()