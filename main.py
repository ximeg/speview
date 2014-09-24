#!/usr/bin/env python

import pylab as pl
import numpy as np
import xcal_raman as xcal
import winspec
import PyZenity as pz
import os


if os.path.exists(".speview.conf"): # We have found config, lets use it!
    config = cp.SafeConfigParser()
    config.read(".speview.conf")
    if config.get("general", "wavenum_calibration") == "yes" :
        print "FIXME: perform wl calibration"
        calibrated = True
    
else: 
    ans = pz.Question("Should I just show the SPE file?\n" +
                     "If you answer 'No', then I will\n" +
                     "create a config with standard\n" +
                     "settings for this folder\n")
    if ans:
        pz.InfoMessage("You selected yes")
    
pl.plot([],[])

#cal_f, p = xcal.calibrate_spe("polystyrene.SPE", "dark.SPE",
#                              material="polystyrene", figure=figure())
#savefig("xcal-report-polystyrene.pdf")
# We have calibration function, lets plot spectrum of some substance
#s = winspec.Spectrum("substance.SPE")
#s.background_correct("dark.SPE")
#plot(cal_f(s.wavelen), s.lum)
#xlabel("Wavenumber, cm$^{-1}$")
#ylabel("Counts")
