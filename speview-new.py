#!/usr/bin/env python
# -*- coding: utf-8 -*-
# simple SPE file viewer (Raman spectra)
# license: GNU GPL
# author:  roman.kiselew@gmail.com
# date:    Sep.-Oct. 2014

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

fig = None
show_called = False


############################# Helper function #################################
def mklbl(fname):
    if len(fname) > 28:
        return "%s~%s" % (fname[:12], fname[-16:-4])
    else:
        return fname[:-4]


def make_spelist(config, fname):
    """
    Create a list of all SPE files in working directory, except those
    present in config. Also the list contains a pointer (active file)
    """
    global spelist
    spelist = [fl for fl in os.listdir(".") if
                        fl.endswith(".SPE") or fl.endswith(".spe")]

    # sort list and get rid of calibration/dark files
    spelist.sort()
    try:
        spelist.remove(config.get("wavenum_calibration", "datafile"))
    except cp.NoOptionError:
        pass
    try:
        spelist.remove(config.get("wavenum_calibration", "darkfile"))
    except cp.NoOptionError:
        pass
    try:
        spelist.remove(config.get("general", "darkfile"))
    except cp.NoOptionError:
        pass

    # Rotate the circular buffer until the first element is our required file
    while not spelist[0] == fname:
        spelist.append(spelist.pop(0))
    return spelist


################################### Classes ###################################
# LineColors  - management of colors for lines
# FileReader  - reading of SPE files and data calibration
# DataItem    - structure to save the data from files
# DataSet     - a set of DataItem's with methods to manage the data
# Window      - a Matplotlib figure with key press handlers
###############################################################################
class LineColors:
    """ Management of line colors on the plot """
    def __init__(self):
        self.seq = ["r", "k", "g", "m", "c", "y"]  # Sequence of colors
        self.status = [0] * len(self.seq)  # 1 if color is used, 0 otherwise
        self.default = "b"

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
        s = ""
        for i in range(len(self.seq)):
            s += "%s = %i\n" % (self.seq[i], self.status[i])
        return s

line_colors = LineColors()


class FileReader():
    """ Reading of SPE files and calibration of data """
    def __init__(self, config):
        # Figure out if we need to perform calibration
        self.calibrated = True
        if self.calibrated:
            xcal_coeffs = np.loadtxt("xcal_coeffs.csv")
        else:
            xcal_coeffs = [1, 0]  # - uncalibrated
        self.cal_f = lambda x: np.polyval(xcal_coeffs, x)

    def read_spe(self, fname):
        spec = winspec.Spectrum(fname)
        if config.get("general", "use_dark") == "yes":
            if os.path.exists(fname[:-3] + "dark.SPE"):  # it overrides config
                spec.background_correct(fname[:-3] + "dark.SPE")
            elif os.path.exists(fname[:-3] + "dark.spe"):
                spec.background_correct(fname[:-3] + "dark.spe")
            else:
                spec.background_correct(config.get("general", "darkfile"))

        return self.cal_f(spec.wavelen), spec.lum


class DataItem:
    """
    DataItem is a container to store data from one single file. It contains
    the following attributes:
        * self.fname - name of the SPE file
        * self.shape - number of spectra in the file
        * self.color - color for line on the plot
        * self.xvals - numpy array of x-values
        * self.yvals - numpy array of y-values
    """
    def __init__(self, fname):
        self.fname = fname
        self.shape = 0
        self.xvals = []
        self.yvals = []

    def __repr__(self):
        if self.shape:
            return ("\nstatus=%i color=%s X=%20.20s Y=%20.20s\n" %
                    (self.shape, repr(self.color),
                     repr(self.xvals), repr(self.yvals)))
        else:
            return ("empty!\n")

    def reset(self):
        self.__init__(self.fname)


class DataSet:
    """
    This class contains a list of SPE files and the corresponding data.

    Data format
    ---
      data = { <fname> : <item> }
    where <item> is an instance of class DataItem

    Methods
    ---
    You can place data from file <fname> in the following way:
      dataset[<fname>] = xvals, yvals
    The corresponding DataItem will automatically get next free line color

    Remove item from dataset:
      dataset.remove(<fname>)

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
        if self.data[key].shape:
            self.data[key].reset()
            line_colors.free(self.data[key].color)

    def plot(self):
        for key in self.data:
            if self.data[key].shape:
                pl.plot(self.data[key].xvals,
                        self.data[key].yvals,
                        self.data[key].color, lw=1.0, label=mklbl(key))


class Window():
    """ A matplotlib figure used to display plots """
    def __init__(self, config, fname):
        self.spelist = make_spelist(config, fname)

        # Create a data container and a file reader instance
        self.dataset = DataSet(self.spelist)
        self.dataReader = FileReader(config)

        # Create a figure and show it (start the event loop)
        self.figure = pl.figure()
        self.ax = self.figure.gca()
        self.canvas = self.figure.canvas
        self.canvas.mpl_connect("key_press_event", self.key_event)
        self.draw()
        pl.show()

    def key_event(self, e):
        if e.key == "right":
            self.go_next()
        if e.key == "left":
            self.go_prev()
        if e.key == "a" or e == "A":
            self.add()
        if e.key == "d" or e == "D":
            self.delete()

    def draw(self):
        self.dataset.plot()
        fname = self.spelist[0]
        x, y = self.dataReader.read_spe(fname)
        pl.plot(x, y, line_colors.default, lw=1.25, label=mklbl(fname))

        # change figure title and plot params
        self.canvas.set_window_title(fname)

        # Formatting - zero level, limits of axes
        self.ax.set_xlim(x.min(), x.max())
        pl.margins(0.0, 0.05)  # 5% vertical margins
        pl.hlines(0, x.min(), x.max(), "k", linestyles="--", lw=.75, alpha=.5)

        # Formatting - labels and title
        pl.ylabel("Counts")
        pl.title(fname)
        if self.dataReader.calibrated:
            pl.xlabel("Wavenumber, cm$^{-1}$")
        else:
            pl.xlabel("pixel number")

        # Formatting - legend
        legend = pl.legend(loc="upper right", fontsize="small", fancybox=True,
                           frameon=True, framealpha=0.6)
        legend.draggable(True)
        if len(legend.get_texts()) > 1:
            legend.set_title("Opened files")
        else:
            legend.set_title("Opened file")

        self.canvas.draw()

    def go_next(self):
        """ Open next SPE file (NOT calibration or dark, see config). """
        self.ax.cla()
        self.spelist.append(self.spelist.pop(0))  # rotate circle forward
        self.draw()

    def go_prev(self):
        """ Display previous SPE file. """
        self.ax.cla()
        self.spelist.insert(0, self.spelist.pop(-1))  # rotate circle backward
        self.draw()

    def add(self):
        """
        Move the current datafile back in the datastack, so it is
        considered to be the previous one.
        """
        fname = self.spelist[0]
        self.dataset[fname] = self.dataReader.read_spe(fname)

    def delete(self):
        """
        Delete the current spectrum from the datastack.
        """
        self.dataset.remove(self.spelist[0])

###############################################################################





























def quiz(config, fname):
    """ Ask user several questions and create config for this directory """
    ans = pz.Question("Would you like to use\nwavenumber calibration?")
    spelist = [file for file in os.listdir(".") if
                            file.endswith(".SPE") or file.endswith(".spe")]
    if ans:
        config.set("general", "wavenum_calibration", "yes")
        ans = None
        while not ans:
            ans = pz.List(("SPE files",), data=[spelist],
                     title="SPE file for calibration")[0]
            config.set("wavenum_calibration", "datafile", ans)
        spelist.remove(ans)
        ans = None
        while not ans:
            ans = pz.List(("SPE files",), data=[spelist],
                     title="Corresponding dark current SPE file")[0]
            config.set("wavenum_calibration", "darkfile", ans)
        spelist.remove(ans)
        ans = None
        materials = ["polystyrene",
                     "cyclohexane",
                     "paracetamol",
                     "naphthalene"]
        while not ans:
            ans = pz.List(("Known materials",), data=[materials],
                     title="Select the material")[0]
            config.set("wavenum_calibration", "material", ans)
        ans = None
        while ans is None:
            try:
                ans = int(pz.GetText("Shift of x-axis (px)", entry_text="0"))
            except ValueError:
                ans = None
        config.set("wavenum_calibration", "shift", ans)

    ans = pz.Question("Would you like to use\ndark current correction?")
    if ans:
        config.set("general", "use_dark", "yes")
        ans = None
        while not ans:
            ans = pz.List(("SPE files",), data=[spelist],
                     title="Corresponding dark current SPE file")[0]
            config.set("general", "darkfile", ans)

    with open(".speview.conf", 'wb') as configfile:
        config.write(configfile)
    ans = pz.Question("Would you like to see the SPE file?\n" +
                                      os.path.basename(sys.argv[1]))
    if ans:
        read_spe(config, fname)








# Detect the working directory: it contains data file given as argv[1]
fullname = sys.argv[1]
fname = os.path.basename(fullname)
if fullname.find("/") >= 0:
    os.chdir(os.path.dirname(fullname))

# Create a container for the datasets
data = [()]

# Create a container for list of SPE files in the working directory
# This is a circular buffer, i.e. sorted list of files with element [0]
# being the currently displayed SPE file
spelist = []
mpl_cnc = False

# Check if a config file is available and create it if necessary
if os.path.exists(".speview.conf"):
    config = cp.SafeConfigParser()
    config.read(".speview.conf")
#    read_spe(config, fname)
    w = Window(config, fname)
else:
    ans = pz.Question("Should I just show the SPE file?\n" +
                     "If you answer 'No', then I will\n" +
                     "create a config with the standard\n" +
                     "settings for this folder\n")
    config = cp.RawConfigParser()
    config.add_section("general")
    config.add_section("wavenum_calibration")
    config.set("general", "wavenum_calibration", "no")
    config.set("general", "use_dark", "no")
    if not ans:
        quiz(config, fname)
    else:
        read_spe(config, fname)
















#
