import contextlib
import os
import webbrowser
from functools import wraps
from string import ascii_letters, digits
from tkinter import LEFT, SOLID, Label, Listbox, Toplevel, Variable, font
from tkinter.constants import END


class Link(Label):
    """
    Class Link inherits superclass Label used in tkinter windows to create a linked lable,
        the lable changes color on hover, and opens browser on click,
        to the link provided on creation.
    """

    def __init__(self, master=None, link=None, fg='grey', font=('Arial', 10), *args, **kwargs):
        """
        Link object constructor.

        Args:
            link (String, optional): a string of the link to open on click
            Label (Tkinter Widget): usual tkinter label widget arguments(master, textvariable, fg.. etc)
        """
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.default_color = fg
        self.default_font = font
        self.hover_color = 'blue'
        self.link = link

        # provided font and color
        self['fg'] = fg
        self['font'] = font

        # bind label to mouse events
        self.bind('<Enter>', lambda event: self._mouse_in())
        self.bind('<Leave>', lambda event: self._mouse_out())
        self.bind('<Button-1>', lambda event: self._open_link())

    def _mouse_in(self):
        """
            Private instance method _mouse_in() handles event when mouse enters (hovers over) the label
        """
        # set label color to blue and underline it
        self['fg'] = self.hover_color
        self['font'] = self.default_font + ('underline',)

    def _mouse_out(self):
        """
            Private instance method _mouse_out() handles event when mouse leaves the label
        """
        # set label color to the default and remove underline
        self['fg'] = self.default_color
        self['font'] = self.default_font

    def _open_link(self):
        """
            Private instance method _open_link() handles event when label is clicked
        """
        # open web browser to the provided link
        webbrowser.open_new(self.link)


class ToolTip():
    """
    Class ToolTip used in tkinter windows to create a hovering tip,
        that is, a hovering label that appears when mouse enters provided widget,
        and disappears when mouse leaves the widget.
    """

    def __init__(self, widget, text):
        """
        ToolTip object constructor.

        Args:
            widget (Tkinter widget): the tkinter widget to include the tip.
            text (String): text to appear in the tip.
        """
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

        # bind widget to mouse events
        widget.bind('<Enter>', lambda event: self._show_tip(text))
        widget.bind('<Leave>', lambda event: self._hide_tip())

    def _show_tip(self, text):
        """
        Private instance method _show_tip() handles event when mouse enters (hovers over) the widget.

        Args:
            text (String): text to appear in the tip.
        """
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + cx + self.widget.winfo_rootx() + 15
        y = y + cy + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, justify=LEFT,
                      background="#ffffe0", relief=SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def _hide_tip(self):
        """
        Private instance method __hide_tip() handles event when mouse leaves the widget.
        """
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class AutoComplete():
    """
    Class AutoComplete used in a tkinter Entry wiget to display an auto-complete list
        of symbols/companies starting with current user input in the entry field from
        a provided symbols pandas dataframe.
    """

    def __init__(self, widget, symbols):
        """
        AutoComplete object constructor.
        Args:
            widget (Tkinter widget): a tkinter Entry widget
            symbols (Dataframe): a pandas dataframe of the symbols in the database.
        """
        self.widget = widget
        self.symbols = symbols
        self.acBox = None
        self.boxIndexes = None
        widget.bind('<KeyRelease>', lambda event: self._auto_complete(event))
        widget.bind('<FocusOut>', lambda event: self._hide_auto_complete())

    def _auto_complete(self, event):
        """
        Private instance method _auto_complete() handles event when a user enters a key in the Entry widget

        Args:
            event (KeyRelease Event): an event of a keyboard key release
        """
        # unlike most event handlers so far, this one actually uses the generated event
        # to decide what to do according to the key pressed in the event, including
        # showing and hiding the auto-complete list

        input = self.widget.get().upper()
        keysym = event.keysym

        # if the entry is empty, do nothing
        if input == '':
            self._hide_auto_complete()
            return
        # if the pressed key is Escape of a space, hide auto complete
        elif keysym in ['space', 'Escape']:
            self._hide_auto_complete()
        # if the pressed key is alphanumerical or a Backspace or a Delete
        elif keysym in ascii_letters + digits or keysym in ['BackSpace', 'Delete']:
            # get last part of the entry (chars after last space)
            inputList = input.strip().split(" ")
            lastInput = inputList[-1]
            # get matching symbols/names
            data = self.symbols.loc[self.symbols.Symbol.str.startswith(
                lastInput) | self.symbols.Security_Name.str.upper().str.startswith(lastInput)].to_dict(orient='records')
            self.boxIndexes = [i for i in range(len(data))]
            # show auto complete list
            self._show_auto_complete(data)
        # if the pressed key is Up or Down
        elif keysym in ['Up', 'Down']:
            # index of selection
            selectionIndex = self.listbox.curselection()
            # if no selection, set selection to the first index
            if not selectionIndex:
                self.listbox.selection_set(0)
                return
            # The following routine changes selection according to the keypress
            # it uses boxIndexes list to make sure the next selection index is not out of bounds
            if selectionIndex[0] in self.boxIndexes:
                self.listbox.selection_clear(0, END)
                if keysym == 'Up':
                    newSelectionIndex = self.boxIndexes[selectionIndex[0] - 1]
                if keysym == 'Down':
                    newSelectionIndex = self.boxIndexes[selectionIndex[0] +
                                                        1] if selectionIndex[0] + 1 in self.boxIndexes else 0
                self.listbox.selection_set(newSelectionIndex)
                self.listbox.see(newSelectionIndex)
                self.listbox.activate(newSelectionIndex)
                self.listbox.selection_anchor(newSelectionIndex)
        # if the pressed key is Return
        elif keysym == 'Return':
            # generate a ListboxSelect event to trigger __select_auto_complete() handler
            self.listbox.event_generate('<<ListboxSelect>>')

    def _show_auto_complete(self, data):
        """
        Private instance method _show_auto_complete() displays a listbox of the data in the provided dataframe

        Args:
            data (DataFrame): a pandas dataframe of companies' symbols/names.
        """
        if self.acBox:
            self.acBox.destroy()
        self.acBox = ac = Toplevel(self.widget)
        symCount = len(data) if len(data) <= 4 else 4
        width = self.widget.winfo_width()
        height = int(self.widget.winfo_height() * 0.8 * symCount)
        ac.geometry(f'{width}x{height}')

        ac.wm_overrideredirect(1)
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        ac.wm_geometry("+%d+%d" % (x, y))

        # a custom fond size for listbox size control
        custom_font = font.Font(size=10)
        self.listVar = Variable()
        self.listbox = Listbox(ac, font=custom_font,
                               justify=LEFT, listvariable=self.listVar)
        self.listbox.pack()

        # add suggestions to the listbox
        self.listVar.set(
            [f'{sym["Symbol"]}: {sym["Security_Name"].split("-")[0]}' for sym in data])

        # bind listbox to a selection event
        self.listbox.bind('<<ListboxSelect>>',
                          lambda event: self._select_auto_complete())

    def _hide_auto_complete(self):
        """
            Private instance method _hide_auto_complete() hides auto-complete listbox
        """
        if self.acBox:
            self.acBox.destroy()
        self.acBox = None

    def _select_auto_complete(self):
        """
        Private instance method _select_auto_complete() handles events generates when
            a list item in the listbox is selected.
        """
        # index of selection
        selectionIndex = self.listbox.curselection()

        # if no selection, return
        if not selectionIndex:
            return

        # get symbol from selection text
        symbol = self.listbox.get(selectionIndex).split(':')[0]

        # current input to list, add selection to list, list to string again
        input = self.widget.get()
        inputList = input.strip().split(" ")
        newInput = " ".join(inputList[:-1] + [symbol + ' '])

        # replace current input with new input
        self.widget.delete(0, END)
        self.widget.insert(0, newInput)

        # hide auto complete
        self._hide_auto_complete()


def diffCalc(currPrice, prevPrice):
    """
        Method diffCalc() calculates difference between current price and previous price
            and returns a formatted string of the difference.

        Args:
            currPrice (Float): the current price
            prevPrice (Float): the previous price

        Returns:
            String: a formatted string of the difference with either + or - depending on the difference
    """
    ARRUP = u'\u2197'  # Arrow Up
    ARRDN = u'\u2198'  # Arrow Down

    # the function is written this way for better control over formatting
    if currPrice > prevPrice:
        diff = currPrice - prevPrice
        percentage = diff * 100 / prevPrice
        result = "+" + str("{:.2f}".format(diff)) + " (+" + \
            str("{:.2f}".format(percentage)) + " %)" + ARRUP

    elif prevPrice > currPrice:
        diff = prevPrice - currPrice
        percentage = diff * 100 / prevPrice
        result = "-" + str("{:.2f}".format(diff)) + " (-" + \
            str("{:.2f}".format(percentage)) + "%)" + ARRDN

    return result


# Debug messages control wrapper function currently unused
def debugger(debug=False):
    """
    (currently unused)
    Wrapper method to enable/disable debugging, it redirects prints to null file if debug==Flase

    Args:
        debug (bool, optional): True to enable debugging messages. Defaults to False.
    """
    # double wraps for better argument control
    def outer_wrap(func):
        @wraps(func)
        def inner_wrap(*args, **kwargs):
            if debug:
                return func(*args, **kwargs)
            else:
                with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
                    return func(*args, **kwargs)
        return inner_wrap
    return outer_wrap
