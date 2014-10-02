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







###############################################################################
class FileReader():
    def __init__(self, config):
        # Figure out if we need to perform calibration
        self.calibrated = False
        if self.calibrated:
            xcal_coeffs = np.loadtxt("xcal_coeffs.csv")
        else:
            xcal_coeffs = [1, 0]  # - uncalibrated
        self.cal_f = lambda x: np.polyval(xcal_coeffs, x)

    def read_spe(self, fname):
        spec = winspec.Spectrum(fname)
        if config.get("general", "use_dark") == "yes":
            if   os.path.exists(fname[:-3] + "dark.SPE"):  # it overrides config
                spec.background_correct(fname[:-3] + "dark.SPE")
            elif os.path.exists(fname[:-3] + "dark.spe"):
                spec.background_correct(fname[:-3] + "dark.spe")
            else:
                spec.background_correct(config.get("general", "darkfile"))

        return (self.cal_f(spec.wavelen), spec.lum, fname)


class DataSet():
    def __init__(self):
        self.data = [()]

    def add(self, item):
        self.data.append(item)

    def hold(self):
        """ Append an empty item, (changed by next call to replace)"""
        if not self.data[-1] == ([], [], ""):
            self.data.append(([], [], ""))

    def replace(self, item):
        self.data[-1] = item

    def remove(self, index):
        del self.data[index]



class Window():
    def __init__(self, config, fname):
        self.spelist = make_spelist(config, fname)

        # Create a data container
        self.dataset = DataSet()

        # Read spectrum and place first data into the container
        self.dataReader = FileReader(config)
        self.dataset.replace(self.dataReader.read_spe(self.spelist[0]))
        print self.dataset.data


        # Create a figure and show it (start the event loop)
        self.figure = pl.figure()
        self.ax = self.figure.gca()
        self.canvas = self.figure.canvas
        self.canvas.mpl_connect("key_press_event", self.key_event)
        self.draw()
        pl.show()



    def key_event(self,e):
        if e.key == "right":
            self.go_next()
        if e.key == "left":
            self.go_prev()
        if e.key == "a" or e == "A":
            self.add()
        if e.key == "d" or e == "D":
            self.delete()



    def draw(self):
        # draw our self.dataset.data
        for line in self.dataset.data:
            x, y, fname = line
            # Crop the middle of a very long filename and use the result in legend
            if len(fname) > 28:
                lbl = "%s~%s" % (fname[:12], fname[-16:-4])
            else:
                lbl = fname[:-4]
            pl.plot(x, y, label=lbl)
        # change figure title and plot params
        self.canvas.set_window_title(self.spelist[0])
        # Formatting - zero level, limits of axes
        self.ax.set_xlim(x.min(), x.max())
        pl.margins(0.0, 0.05)  # 5% vertical margins
        pl.hlines(0, x.min(), x.max(), "k", linestyles="--", lw=0.75, alpha=0.5)

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
        print "check 'from itertools import cycle' and http://stackoverflow.com/questions/7799156/can-i-cycle-through-line-styles-in-matplotlib"
        self.ax.cla()
        self.spelist.append(self.spelist.pop(0))  # rotate circle forward
        self.dataset.replace(self.dataReader.read_spe(self.spelist[0]))
        self.draw()

    def go_prev(self):
        """ Display previous SPE file. """
        self.ax.cla()
        self.spelist.insert(0, self.spelist.pop(-1))  # rotate circle backward
        self.dataset.replace(self.dataReader.read_spe(self.spelist[0]))
        self.draw()

    def add(self):
        """
        Move the current datafile back in the datastack, so it is
        considered to be the previous one.
        """
        self.dataset.hold()

    def delete(self):
        """
        Delete the current spectrum from the datastack.
        """
        # First of all we make sure, that it is already stored somewhere
        # in the dataset AND it is not the last element
        for i, item in enumerate(self.dataset.data[:-1]):
            if item[2] == self.spelist[0]:
                self.dataset.remove(i)

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






def hold():
    """ Mark actual plot and do not erase it. """
    print "hold(): NOT_IMPLEMENTED"


def key_event(e):
    if e.key == "right":
        go_next()
    if e.key == "left":
        go_prev()
    if e.key == "h" or e == "H":
        hold()


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
    try: spelist.remove(config.get("wavenum_calibration", "datafile"))
    except cp.NoOptionError: pass
    try: spelist.remove(config.get("wavenum_calibration", "darkfile"))
    except cp.NoOptionError: pass
    try: spelist.remove(config.get("general", "darkfile"))
    except cp.NoOptionError: pass

    # Rotate the circular buffer until the first element is our required file
    while not spelist[0] == fname:
        spelist.append(spelist.pop(0))
    return spelist


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
