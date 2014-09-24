#!/usr/bin/env python

import pylab as pl
import numpy as np
import xcal_raman as xcal
import winspec
import PyZenity as pz
import os
import sys
import ConfigParser as cp

def display_spe(config):
    calibrated = False
    if config.get("general", "wavenum_calibration") == "yes" :
        # check if it is necessary
        if os.path.exists("xcal_coeffs.csv"):
            # just read calibration function from it!
            cal_f = lambda x: np.polyval(np.loadtxt("xcal_coeffs.csv"), x)
        else:
            material = config.get("wavenum_calibration", "material")
            xcalfile = config.get("wavenum_calibration", "datafile")
            darkfile = config.get("wavenum_calibration", "darkfile")
            shift    = config.getint("wavenum_calibration", "shift")
            cal_f, p = xcal.calibrate_spe(xcalfile, darkfile, material=material,
                                          figure=pl.figure(), shift=shift)
            pl.savefig("calibration_report-" + material + ".pdf")
            pl.close(pl.gcf())
            np.savetxt("xcal_coeffs.csv", p)
        calibrated = True
    
    # Make dark current correction
    fname = sys.argv[1]
    spec = winspec.Spectrum(fname)
    if config.get("general", "use_dark") == "yes":
        if   os.path.exists(fname[:-3] + "dark.SPE"):  # it overrides config
            spec.background_correct(fname[:-3] + "dark.SPE")
        elif os.path.exists(fname[:-3] + "dark.spe"):
            spec.background_correct(fname[:-3] + "dark.spe")
        else:
            spec.background_correct(config.get("general", "darkfile"))

    # Make a plot
    if calibrated:
        pl.plot(cal_f(spec.wavelen), spec.lum)
        pl.xlabel("Wavenumber, cm$^{-1}$")
        pl.gca().set_xlim(cal_f(spec.wavelen.min()), cal_f(spec.wavelen.max()))
    else:
        pl.plot(spec.wavelen, spec.lum)
        pl.xlabel("pixel number")
        pl.gca().set_xlim(spec.wavelen.min(), spec.wavelen.max())
    pl.ylabel("Counts")
    pl.title(fname)
    pl.show()


if os.path.exists(".spevisew.conf"): # We have found config, lets use it!
    config = cp.SafeConfigParser()
    config.read(".speview.conf")
    display_spe(config)
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
    if ans:
        pz.InfoMessage("You selected yes")
    else:
        display_spe(config)    



