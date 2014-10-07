#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 simple SPE file viewer (Raman spectra)
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


############################# Helper function #################################
# mklbl         - make a label for legend, which is not longer than 28 symbols
# make_spelist  - make a list of all SPE file in the folder
# quiz          - ask user several questions and create config file
###############################################################################
def mklbl(text):
    """ Make a label for legend, which is not longer than 28 symbols. """
    if len(text) > 28:
        return "%s~%s" % (text[:12], text[-16:-4])
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
                          title="SPE file for calibration")[0]
            cfg.set("wavenum_calibration", "datafile", ans)
        spelist.remove(ans)
        ans = None
        while not ans:
            ans = pz.List(("SPE files",), data=[spelist],
                          title="Corresponding dark current SPE file")[0]
            cfg.set("wavenum_calibration", "darkfile", ans)
        spelist.remove(ans)
        ans = None
        materials = ["polystyrene",
                     "cyclohexane",
                     "paracetamol",
                     "naphthalene"]
        while not ans:
            ans = pz.List(("Known materials",), data=[materials],
                          title="Select the material")[0]
            cfg.set("wavenum_calibration", "material", ans)
        ans = None
        while ans is None:
            try:
                ans = int(pz.GetText("Shift of x-axis (px)", entry_text="0"))
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
    You can place data from file <fname> in the following way:
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

    def plot(self):
        """ Draw the data stored in DataSet on the current axes. """
        for key in self.data:
            if self.data[key].shape:
                pl.plot(self.data[key].xvals,
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
        self.ax = self.figure.gca()
        self.canvas = self.figure.canvas
        self.canvas.mpl_connect("key_press_event", self.key_event)
        self.grid = True
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

    def draw(self):
        """ Redraw the plot. First draw stored data, then the current file. """
        self.ax.cla()
        self.dataset.plot()
        filename = self.spelist[0]
        x, y = self.reader.read_spe(filename)
        pl.plot(x, y, line_colors.default, lw=1.25, label=mklbl(filename))

        # change figure title and plot params
        self.canvas.set_window_title(filename)

        # Formatting - zero level, limits of axes
        self.ax.set_xlim(min(x), max(x))
        pl.margins(0.0, 0.05)  # 5% vertical margins
        pl.hlines(0, min(x), max(x), "k", linestyles="--", lw=.75, alpha=.5)

        # Formatting - labels and title
        pl.ylabel("Counts")
        pl.title(filename)
        if self.reader.calibrated:
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

        if self.grid:
            pl.grid(self.grid)
        self.canvas.draw()

    def go_next(self):
        """ Open next SPE file (NOT calibration or dark, see config). """
        self.spelist.append(self.spelist.pop(0))  # rotate circle forward
        self.draw()

    def go_prev(self):
        """ Display previous SPE file. """
        self.spelist.insert(0, self.spelist.pop(-1))  # rotate circle backward
        self.draw()

    def toggle(self):
        """ Toggle the state of the active line (saved or not). """
        filename = self.spelist[0]
        if self.dataset[filename].shape:
            self.dataset.remove(self.spelist[0])
        else:
            self.dataset[filename] = self.reader.read_spe(filename)
        self.draw()


##################################### START ###################################

# Detect the working directory: it contains data file given as argv[1]
print "HELLO"
fullname = sys.argv[1]
fname = os.path.basename(fullname)
if fullname.find("/") >= 0:
    os.chdir(os.path.dirname(fullname))

# Check if a config file is available and create it if necessary
if os.path.exists(".speview.conf"):
    config = cp.SafeConfigParser()
    config.read(".speview.conf")
    Window(config, fname)
else:
    reply = pz.Question("Should I just show the SPE file?\n" +
                        "If you answer 'No', then I will\n" +
                        "create a config with the standard\n" +
                        "settings for this folder\n")
    config = cp.RawConfigParser()
    config.add_section("general")
    config.add_section("wavenum_calibration")
    config.set("general", "wavenum_calibration", "no")
    config.set("general", "use_dark", "no")
    if not reply:
        quiz(config, fname)
    else:
        Window(config, fname)


