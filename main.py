#!/usr/bin/env python

import pylab as pl
import numpy as np
import xcal_raman as xcal
import winspec
import PyZenity as pz
import os
import sys
import ConfigParser as cp
import pickle # TODO use it!

fname = sys.argv[1]
#fname = "Cyclohexan1.SPE"
if os.path.exists(".speview.conf"): # We have found config, lets use it!
    config = cp.SafeConfigParser()
    config.read(".speview.conf")
    calibrated = False
    if config.get("general", "wavenum_calibration") == "yes" :
        material = config.get("wavenum_calibration", "material")
        xcalfile = config.get("wavenum_calibration", "datafile")
        darkfile = config.get("wavenum_calibration", "darkfile")
        shift    = config.getint("wavenum_calibration", "shift")
        cal_f, p = xcal.calibrate_spe(xcalfile, darkfile, material=material,
                                      figure=pl.figure(), shift=shift)
        pl.savefig("calibration_report-" + material + ".pdf")
        pl.close(pl.gcf())
        # TODO: use pickle to save cal_f
        calibrated = True
    
    # We have a calibration function, lets plot the spectrum!
    spec = winspec.Spectrum(fname)
    if   os.path.exists(fname[:-3] + "dark.SPE"):  # it overrides config
        spec.background_correct(fname[:-3] + "dark.SPE")
    elif os.path.exists(fname[:-3] + "dark.spe"):
        spec.background_correct(fname[:-3] + "dark.spe")
    else:
        spec.background_correct(config.get("general", "darkfile"))

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
    
else: 
    ans = pz.Question("Should I just show the SPE file?\n" +
                     "If you answer 'No', then I will\n" +
                     "create a config with standard\n" +
                     "settings for this folder\n")
    if ans:
        pz.InfoMessage("You selected yes")
    
#cal_f, p = xcal.calibrate_spe("polystyrene.SPE", "dark.SPE",
#                              material="polystyrene", figure=figure())
#savefig("xcal-report-polystyrene.pdf")
# We have calibration function, lets plot spectrum of some substance
#s = winspec.Spectrum("substance.SPE")
#s.background_correct("dark.SPE")
#plot(cal_f(s.wavelen), s.lum)
#xlabel("Wavenumber, cm$^{-1}$")
#ylabel("Counts")
