#!/usr/bin/env python
# -*- coding: utf-8 -*-
# simple SPE file viewer (Raman spectra)
# license: GNU GPL
# author:  roman.kiselew@gmail.com
# date:    Sep.-Oct. 2014

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

def visualize(data, calibrated=True):
    """ Plot the spectra contained in data (list of (x, y) arrays). """
    for line in data:
        x, y, fname = line
        if len(fname) > 24:
            lbl = "%s~%s" % (fname[:10], fname[-14:-4])
        else:
            lbl = fname[:-4]
        pl.plot(x, y, label=lbl)

    if calibrated:
        pl.xlabel("Wavenumber, cm$^{-1}$")
    else:
        pl.xlabel("pixel number")

    pl.gca().set_xlim(x.min(), x.max())
    pl.ylabel("Counts")
    pl.title(fname)
    pl.legend(loc="upper right", fontsize="small")
    global show_called
    if not show_called:
        show_called = True
        pl.show()


def read_spe(config, fname):
    """ Display SPE file based on current configuration """
    global fig
    global canvas
    if not fig:
        fig = pl.figure()
        canvas = fig.canvas
        canvas.mpl_connect("key_press_event", key_event)
    if not spelist:
        make_spelist(config, fname)
    calibrated = False
    if config.get("general", "wavenum_calibration") == "yes":
        # check if it is necessary
        if os.path.exists("xcal_coeffs.csv"):
            # just read calibration function from it!
            cal_f = lambda x: np.polyval(np.loadtxt("xcal_coeffs.csv"), x)
        else:
            material = config.get("wavenum_calibration", "material")
            xcalfile = config.get("wavenum_calibration", "datafile")
            darkfile = config.get("wavenum_calibration", "darkfile")
            shift = config.getint("wavenum_calibration", "shift")
            cal_f, p = xcal.calibrate_spe(xcalfile, darkfile,
                                          material=material,
                                          figure=pl.figure(), shift=shift)
            pl.savefig("calibration_report-" + material + ".pdf")
            pl.close(pl.gcf())
            np.savetxt("xcal_coeffs.csv", p)
        calibrated = True

    # Make dark current correction
    spec = winspec.Spectrum(fname)
    if config.get("general", "use_dark") == "yes":
        if   os.path.exists(fname[:-3] + "dark.SPE"):  # it overrides config
            spec.background_correct(fname[:-3] + "dark.SPE")
        elif os.path.exists(fname[:-3] + "dark.spe"):
            spec.background_correct(fname[:-3] + "dark.spe")
        else:
            spec.background_correct(config.get("general", "darkfile"))

    if calibrated:
        data[-1] = (cal_f(spec.wavelen), spec.lum, fname)
    else:
        data[-1] = (spec.wavelen, spec.lum, fname)
    visualize(data, calibrated)


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


def go_next():
    """ Open next SPE file (NOT calibration or dark, see config). """

    spelist.append(spelist.pop(0))
    print("Next file: " + spelist[0])
    print spelist
    read_spe(config, spelist[0])
    canvas.draw()


def go_prev():
    """ Display previous SPE file. """
    spelist.insert(0, spelist.pop(-1))
    print("Prev file: " + spelist[0])
    print spelist
    read_spe(config, spelist[0])
    canvas.draw()



def hold():
    """ Mark actual plot and do not erase it. """
    print "hold(): NOT_IMPLEMENTED"
    print data


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
    spelist.remove(config.get("wavenum_calibration", "datafile"))
    spelist.remove(config.get("wavenum_calibration", "darkfile"))
    spelist.remove(config.get("general", "darkfile"))

    # Rotate the circular buffer until the first element is our required file
    while not spelist[0] == fname:
        spelist.append(spelist.pop(0))



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
    read_spe(config, fname)
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
