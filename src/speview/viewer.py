"""
 simple SPE file viewer (Raman spectra) - file with definitions
 license: GNU GPL
 author:  roman.kiselew@gmail.com
 date:    Sep.-Oct. 2014
"""

# Force MPL to save figures in the current working directory
import matplotlib as m
m.rcParams["savefig.directory"] = None

import pylab as pl
import numpy as np
import xcal_raman as xcal
import winspec
import PyZenity as pz
import os
import sys
import ConfigParser as cp
import argparse as ap

from speview import __version__

########################### Texts and constants ###############################
DESC = \
"""
short description
  This application displays binary SPE files containing Raman spectra.
  It works in a similar fashion to a photoviewing application.
  Find more info at GitHub:
        https://github.com/ximeg/speview
"""

KEYSTROKES = \
"""
keystrokes
  In the main application window you can use the following keystrokes:
        KEY             FUNCTION
   <right arrow>  -  show next SPE file
    <left arrow>  -  show previous SPE file
     <space bar>  -  save current file (blue line) to the data buffer
      'g' or 'G'  -  toggle grid state
      'v' or 'V'  -  toggle visibility of current opened file
             'd'  -  subtract a line from the current line
             'D'  -  remove result of subtraction
             'l'  -  toggle scale of Y-axis (linear or log)
             'L'  -  toggle scale of X-axis (linear or log)
             's'  -  save current figure into a file
      'i' or 'I'  -  display file info ('I' produces a pop-up dialog)
            'F5'  -  select the default figure format
      'h' or 'H'  -  display help

speview, version %s
""" % __version__
###############################################################################


############################# Helper function #################################
# mklbl         - make a label for legend, which is not longer than 28 symbols
# make_spelist  - make a list of all SPE file in the folder
# quiz          - ask user several questions and create config file
###############################################################################
def mklbl(text):
    """ Make a label for legend, which is not longer than 28 symbols. """
    max_len = 24
    if len(text) > max_len:
        return "%s~%s" % (text[:(max_len/2)], text[-(max_len/2 + 4):-4])
    else:
        return text[:-4]


def make_spelist(cfg, filename):
    """
    Create a list of all SPE files in working directory, except those
    present in config. Also the list contains a pointer (active file)
    """
    spelist = [fl for fl in os.listdir(".") if
               fl.endswith(".SPE") or fl.endswith(".spe")]

    # sort list and get rid of calibration/dark files
    spelist.sort()
    try:
        spelist.remove(cfg.get("wavenum_calibration", "datafile"))
    except cp.NoOptionError:
        pass
    try:
        spelist.remove(cfg.get("wavenum_calibration", "darkfile"))
    except cp.NoOptionError:
        pass
    try:
        spelist.remove(cfg.get("general", "darkfile"))
    except cp.NoOptionError:
        pass

    # Rotate the circular buffer until the first element is our required file
    while not spelist[0] == filename:
        spelist.append(spelist.pop(0))
    return spelist


def quiz(cfg, filename):
    """ Ask user several questions and create config for this directory. """
    ans = pz.Question("Would you like to use\nwavenumber calibration?")
    spelist = [name for name in os.listdir(".") if
               name.endswith(".SPE") or name.endswith(".spe")]
    if ans:
        cfg.set("general", "wavenum_calibration", "yes")
        ans = None
        while not ans:
            ans = pz.List(("SPE files",), data=[spelist],
                          title="SPE file for calibration")
        cfg.set("wavenum_calibration", "datafile", ans[0])
        spelist.remove(ans[0])
        ans = None
        while not ans:
            ans = pz.List(("SPE files",), data=[spelist],
                          title="Corresponding dark current SPE file")
        cfg.set("wavenum_calibration", "darkfile", ans[0])
        spelist.remove(ans[0])
        ans = None
        materials = ["polystyrene",
                     "cyclohexane",
                     "paracetamol",
                     "naphthalene"]
        while not ans:
            ans = pz.List(("Known materials",), data=[materials],
                          title="Select the material")
        cfg.set("wavenum_calibration", "material", ans[0])
        ans = None
        while ans is None:
            ans = pz.GetText("Shift of x-axis (px)", entry_text="0")
            if ans:
                try:
                    ans = int(ans)
                    if abs(ans) > 50:
                        ans = None
                except ValueError:
                    ans = None
        cfg.set("wavenum_calibration", "shift", ans)

    ans = pz.Question("Would you like to use\ndark current correction?")
    if ans:
        cfg.set("general", "use_dark", "yes")
        ans = None
        while not ans:
            ans = pz.List(("SPE files",), data=[spelist],
                          title="Corresponding dark current SPE file")[0]
            cfg.set("general", "darkfile", ans)

    with open(".speview.conf", 'wb') as configfile:
        cfg.write(configfile)
    ans = pz.Question("Would you like to see the SPE file?\n" +
                      os.path.basename(sys.argv[1]))
    if ans:
        Window(cfg, filename)


################################### Classes ###################################
# LineColors  - management of colors for lines
# FileReader  - reading of SPE files and data calibration
# DataItem    - structure to save the data from files
# DataSet     - a set of DataItem's with methods to manage the data
# Window      - a Matplotlib figure with key press handlers
###############################################################################
class LineColors(object):
    """ Management of line colors on the plot """
    def __init__(self):
        self.seq = ["#800000", "r", "g", "m", "k", "y"]  # Sequence of colors
        self.status = [0] * len(self.seq)  # 1 if color is used, 0 otherwise
        self.default = "#0000b0"
        self.diff    = "#008000"

    def use(self):
        """ Use the next available color. """
        if 0 in self.status:
            for i, color in enumerate(self.seq):
                if not self.status[i]:
                    self.status[i] = 1
                    return color
        else:
            print "All colors are used, cannot add one more line!"
            return False

    def free(self, key):
        """ Mark color given by <key> as unused """
        idx = self.seq.index(key)
        self.status[idx] = 0
        print "Color '%s' is now free" % key

    def __repr__(self):
        desc = ""
        for i in range(len(self.seq)):
            desc += "%s = %i\n" % (self.seq[i], self.status[i])
        return desc

line_colors = LineColors()


class FileReader(object):
    """ Reading of SPE files and calibration of data """
    def __init__(self, cfg):
        """ Check if the calibration is required and perform it. """
        self.cfg = cfg
        self.calibrated = False
        if cfg.get("general", "wavenum_calibration") == "yes":
            # check if calibration coefficients are available
            if os.path.exists("xcal_coeffs.csv"):
                self.cal_f = lambda x: \
                        np.polyval(np.loadtxt("xcal_coeffs.csv"), x)
            else:
                material = cfg.get("wavenum_calibration", "material")
                xcalfile = cfg.get("wavenum_calibration", "datafile")
                darkfile = cfg.get("wavenum_calibration", "darkfile")
                shift = cfg.getint("wavenum_calibration", "shift")
                self.cal_f, coeffs = \
                        xcal.calibrate_spe(xcalfile, darkfile,
                                           material=material,
                                           figure=pl.figure(), shift=shift)
                pl.savefig("calibration_report-" + material + ".pdf")
                pl.close(pl.gcf())
                np.savetxt("xcal_coeffs.csv", coeffs)
            self.calibrated = True
        else:
            self.cal_f = lambda x: np.polyval([1, 0], x)

    def read_spe(self, filename):
        """ Read data from SPE file and apply calibration function on it. """
        spec = winspec.Spectrum(filename)
        if self.cfg.get("general", "use_dark") == "yes":
            if os.path.exists(filename[:-3] + "dark.SPE"):  # overrides config
                spec.background_correct(filename[:-3] + "dark.SPE")
            elif os.path.exists(filename[:-3] + "dark.spe"):
                spec.background_correct(filename[:-3] + "dark.spe")
            else:
                spec.background_correct(self.cfg.get("general", "darkfile"))

        return self.cal_f(spec.wavelen), spec.lum

    def read_info(self, filename):
        """ Read acquisition information and comments from the file. """
        spec = winspec.Spectrum(filename)
        return spec.fileinfo

    def read_other_data_format(self, filename):
        """ TODO Use data from some other file. """
        print self.calibrated
        print "read_other_data_format({}) - NOT IMPLEMENTED".format(filename)
        raise NotImplementedError


class DataItem(object):
    """
    DataItem is a container to store data from one single file. It contains
    the following attributes:
        * self.filename - name of the SPE file
        * self.shape - number of spectra in the file
        * self.color - color for line on the plot
        * self.xvals - numpy array of x-values
        * self.yvals - numpy array of y-values
    """
    def __init__(self, filename):
        self.filename = filename
        self.shape = 0
        self.color = None
        self.xvals = []
        self.yvals = []

    def __repr__(self):
        if self.shape:
            return ("\nstatus=%i color=%s X=%20.20s Y=%20.20s\n" %
                    (self.shape, repr(self.color),
                     repr(self.xvals), repr(self.yvals)))
        else:
            return "empty!\n"

    def reset(self):
        """ Mark data item as unused and remove the data. """
        self.__init__(self.filename)


class DataSet(object):
    """
    This class contains a list of SPE files and the corresponding data.

    Data format
    ---
      data = { <filename> : <item> }
    where <item> is an instance of class DataItem

    Methods
    ---
    You can place your data from the file <filename> in the following way:
      dataset[<filename>] = xvals, yvals
    The corresponding DataItem will automatically get next free line color

    Remove item from dataset:
      dataset.remove(<filename>)

    Plot all lines:
      dataset.plot()
    """
    def __init__(self, files):
        self.data = dict((key, DataItem(key)) for key in files)

    def __setitem__(self, key, item):
        if self.data[key].shape == 0:
            self.data[key].xvals, self.data[key].yvals = item
            self.data[key].color = line_colors.use()
            if self.data[key].color:
                self.data[key].shape = 1
        else:
            print "File '%.35s' is already opened, nothing to do" % key

    def __getitem__(self, key):
        return self.data[key]

    def __repr__(self):
        return repr(self.data)

    def remove(self, key):
        """ Delete data from DataItem and mark associated color as unused. """
        if self.data[key].shape:
            line_colors.free(self.data[key].color)
            self.data[key].reset()

    def get_lines(self):
        """ Return names of files being stored. """
        keys = []
        for key in self.data:
            if self.data[key].shape:
                keys.append(key)
        return keys

    def plot(self, axes):
        """ Draw the data stored in DataSet on the current axes. """
        for key in self.data:
            if self.data[key].shape:
                axes.plot(self.data[key].xvals,
                          self.data[key].yvals,
                          self.data[key].color, lw=1.0, label=mklbl(key))


class Window(object):
    """ A matplotlib figure used to display plots """
    def __init__(self, cfg, filename):
        self.spelist = make_spelist(cfg, filename)

        # Create a data container and a file reader instance
        self.dataset = DataSet(self.spelist)
        self.reader = FileReader(cfg)

        # Create a figure and show it (start the event loop)
        self.figure = pl.figure()
        self.axes = self.figure.gca()

        self.axes_diff = None
        self.diffdata = None
        self.visible = True
        self.help = False
        self.grid = True
        self.show_info = False
        self.boxprops = {"facecolor": "wheat",
                       "alpha": 0.9,
                       "edgecolor": "black",
                       "boxstyle": "round, pad=1"}

        self.canvas = self.figure.canvas
        self.canvas.mpl_connect("key_press_event", self.key_event)
        self.draw()
        pl.show()

    def key_event(self, event):
        """ Check which key was pressed and call the corresp. function. """
        if event.key == "right":
            self.go_next()
        if event.key == "left":
            self.go_prev()
        if event.key == " ":  # Space bar is pressed
            self.toggle()
        if event.key == "g" or event.key == "G":
            self.grid = not self.grid
            self.draw()
        if event.key == "d":
            self.diff()
        if event.key == "D":
            self.diff_off()
        if event.key == "v" or event.key == "V":
            self.visible = not self.visible
            self.draw()
        if event.key == "h" or event.key == "H":
            if not self.help:
                self.help = True
            else:
                self.help.set_visible(False)
                self.help = False
            self.draw()
        if event.key == "i":
            self.show_info = not self.show_info
            self.draw()
        if event.key == "I":
            pz.InfoMessage(self.reader.read_info(self.spelist[0]))
        if event.key == "f5":
            content = [(fmt, desc) for fmt, desc in
                       self.canvas.get_supported_filetypes().iteritems()]
            ans = pz.List(("Formats", "Descr"),
                          data=content, title="Select format for figures")
            if ans:
                print "Selected format for images: '{}'".format(ans[0])
                m.rcParams['savefig.format'] = ans[0]
            else:
                print "Canceled by user. Current format is '{}'".format(m.rcParams['savefig.format'])


    def draw(self):
        """ Redraw the plot. First draw stored data, then the current file. """
        if self.axes_diff:
            self.axes_diff.cla()
        self.axes.cla()
        pl.sca(self.axes)
        # Plot stored data
        self.dataset.plot(self.axes)
        filename = self.spelist[0]

        # Plot current spectrum
        x, y = self.reader.read_spe(filename)
        if self.visible:
            self.axes.plot(x, y, line_colors.default, lw=1.25,
                           label=mklbl(filename))

        # Plot difference (if any)
        if self.diffdata and self.axes_diff:
            y, label = self.diffdata
            self.axes_diff.plot(x, y, line_colors.diff, linestyle="-",
                                lw=0.8, label=label, alpha=0.7)
            legend_diff = self.axes_diff.legend(loc="center right",
                                                fontsize="small",
                                                fancybox=True,
                                                frameon=True, framealpha=0.6)
            legend_diff.draggable(True)
            legend_diff.set_title("Difference")
            self.axes_diff.set_ylabel("Difference in counts",
                                      color=line_colors.diff)
            self.axes_diff.hlines(0, min(x), max(x), color=line_colors.diff,
                                  linestyles="--", lw=.75, alpha=.5)
            for tl in self.axes_diff.get_yticklabels():
                tl.set_color(line_colors.diff)
        pl.sca(self.axes)

        # change figure title and plot params
        self.canvas.set_window_title(filename)

        # Formatting - zero level, limits of axes
        self.axes.set_xlim(min(x), max(x))
        pl.margins(0.0, 0.05)  # 5% vertical margins
        self.axes.yaxis.get_major_formatter().set_powerlimits((0, 4))
        self.axes.yaxis.get_major_formatter().set_powerlimits((0, 4))

        # Formatting - labels and title
        pl.ylabel("Counts")
        pl.title(filename)
        if self.reader.calibrated:
            pl.xlabel("Wavenumber, cm$^{-1}$")
        else:
            pl.xlabel("pixel number")

        # Formatting - legend
        if self.visible or len(self.dataset.get_lines()):
            pl.hlines(0, min(x), max(x), "k", linestyles="--", lw=.7, alpha=.5)
            legend = pl.legend(loc="upper right", fontsize="small",
                               fancybox=True, frameon=True, framealpha=0.6)
            legend.draggable(True)
            if len(legend.get_texts()) > 1:
                legend.set_title("Opened files")
            else:
                legend.set_title("Opened file")
            self.axes.yaxis.set_visible(True)
        else:
            self.axes.yaxis.set_visible(False)

        if self.grid:
            self.axes.grid(self.grid, which='major', axis='both')

        # Display program help
        if self.help is True:
            self.help = \
              self.figure.text(0.05, 0.5, KEYSTROKES, fontsize="medium",
                               ha="left", va="center", family="monospace",
                               bbox=self.boxprops)

        # Display the file-related information
        if self.show_info is True:
            self.axes.text(x.min(), 0.0, self.reader.read_info(filename),
                               fontsize="medium", ha="left", va="bottom",
                               family="monospace", bbox=self.boxprops)
        self.canvas.draw()

    def go_next(self):
        """ Open next SPE file (NOT calibration or dark, see config). """
        self.spelist.append(self.spelist.pop(0))  # rotate circle forward
        self.visible = True
        self.draw()

    def go_prev(self):
        """ Display previous SPE file. """
        self.spelist.insert(0, self.spelist.pop(-1))  # rotate circle backward
        self.visible = True
        self.draw()

    def toggle(self):
        """ Toggle the state of the active line (saved or not). """
        filename = self.spelist[0]
        if self.dataset[filename].shape:
            self.dataset.remove(self.spelist[0])
        else:
            self.dataset[filename] = self.reader.read_spe(filename)
        self.draw()

    def diff(self):
        """ Subtract one spectrum from another one and plot the difference. """
        filename = self.spelist[0]
        keys = self.dataset.get_lines()
        if filename in keys:
            keys.remove(filename)
        if len(keys):
            if not self.axes_diff:
                self.axes_diff = self.axes.twinx()
            if len(keys) == 1:  # No choice - subtract it!
                item = self.dataset[keys[0]]
            else:  # Ask user which line he wants to subtract
                ans = None
                while not ans:
                    ans = pz.List(("Saved spectra",), data=[keys],
                          title="Select line to subtract")
                item = self.dataset[ans[0]]
            xcurr, ycurr = self.reader.read_spe(filename)
            self.diffdata = (ycurr - item.yvals,
                             mklbl(filename) + "\n" +
                             mklbl(item.filename))
            self.draw()

    def diff_off(self):
        """ Get rid of difference line and axes """
        if self.axes_diff:
            self.axes_diff.cla()
            self.axes_diff.yaxis.set_visible(False)
            self.axes_diff = None
            self.draw()


