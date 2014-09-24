#!/usr/bin/env python

import xcal_raman as xcal
import winspec
cal_f, p = xcal.calibrate_spe("polystyrene.SPE", "dark.SPE",
                              material="polystyrene", figure=figure())
savefig("xcal-report-polystyrene.pdf")
# We have calibration function, lets plot spectrum of some substance
s = winspec.Spectrum("substance.SPE")
s.background_correct("dark.SPE")
plot(cal_f(s.wavelen), s.lum)
xlabel("Wavenumber, cm$^{-1}$")
ylabel("Counts")
