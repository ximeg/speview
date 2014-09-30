### Introduction

This program is able to read and display binary SPE files,
generated by `WinSpec` software (Princeton Instruments).
It works in a very similar to a photo-viewing application
fashion, i.e. the spectrum is displayed after the
file is clicked in a filemanager.

The program is able to subtract a dark file and perform
a wavenumber calibration.

### Details

#### Data storage model
The basic idea is that all your SPE files, which are relevant
to each other (e.g. data, calibration, dark), should be
placed into a single folder. `speview` reads the relevant
files that are necessary to display the data, as well as
creates some new files in the same folder. Ideally, all the
spectra should be taken with the same settings (accumulations,
gain, exposure time, slit width, readout rate and so on).

So remember, `speview` can work _only_ with those files, which
are located in the same directory.

#### How it works, or short manual
To display an SPE file correctly, `speview` requires a simple
configuration file, called "`.speview.conf`". The file
is created if it is not present. If this is the case,
speview would ask user the following questions:
* Do you want to perform wavenumber calibration?
  - If yes, then select an SPE file with the spectrum of a
    standard substance, then select the corresponding dark file.
* Do you want to subtract dark from your actual data
  to be displayed?
  - If yes, then select the corresponding dark file.

`speview` accepts only a single argument, which is a filename
of the SPE file to be displayed. The directory of this file
becomes the working directory. The spectrum is obtained from
the binary SPE file using module "`winspec`". If the wavenumber
calibration is required, it is performed with a module called
"`xcalraman`". The calibration report and calibration
coefficients are stored in files "`calibration_report-<substance>.pdf`"
and "`xcal_coeffs.csv`", respectively.

After the data are processed, speview calls matplotlib to
create a plot and displays it with the default backend, e.g.
`qt4agg`. A window with a plot will pop up.

#### Requirements
I tested the package using virtual environment and generated a list of
dependencies (see the "`requirenments.txt`" file)
Basically, you should have on your computer the following packages:
 * `pylab` for plotting (_note_: you need support for an interactive backend,
    e.g. qt4agg, wxagg, gtkagg, tkagg, etc.). You can test whether you have a
    suitable backend by running the following line of code in your python
    interpeter: `import pylab as p; p.gca(); p.show()`.
    If a window with empty axes will pop up, then everything is correct!
 * `xcal_raman` for x-axis calibration and reading of SPE files
    (available on https://pypi.python.org/pypi/xcal_raman)
 * `pyZenity` for graphical interaction with user

##### Automatic installation of dependencies
Run `pip install -r requirenments.txt` to automatically install the
dependencies.

#### Future plans
What I would like to implement in the future:
 * Support for keystokes, e.g. user presses -> or <- and speview
   displays next/previous SPE file, like a photo-viewer
 * Reading of SPE files with multiple spectra
 * Reading of CSV files generated by WinSpec
 * Display file information (acquisition settings,
   date/time, comments, etc...)
 * Ability to compare visually several spectra from different files.
   
