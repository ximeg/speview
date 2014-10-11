### Introduction

This program is able to read and display binary SPE files,
generated by `WinSpec` software (Princeton Instruments).
It works in a very similar to a photo-viewing application
fashion, i.e. the spectrum is displayed after the
file is clicked in a filemanager. Arrows keys are used to
show next/previous file in the folder. Press the space bar
to hold the current line.

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

### Installation
You should be able to install the package with the following two commands:
```
pip install pyzenity --allow-unverified pyzenity
pip install speview
```
PyZenity is not stored on _PyPi_ and therefore is considered by `pip` as
potentially dangerous package. For this reason you have to install it manually
with a separate command.

#### Troubleshooting
Please note, that you may encounter two troubles:
 1. The matplotlib uses a non-interactive backend (no window appears)
 2. Pylab has some problems with shared libraries of PySide:

>  ImportError: libpyside-python2.7.so.1.2: cannot open
>  shared object file: No such file or directory

##### Selecting default backend for matplotlib
You can select your default backend, e.g. _qt4agg_, in `matplotlibrc` file.
The location of this file can be determined from `python`:
```
import matplotlib as m
m.get_configdir()
```
Usually it is something like "`.config/matplotlib/`", and placing a file named
"`matplotlibrc`" there should work just fine. More info could be found at
http://matplotlib.org/users/customizing.html

You may wish to use a `qt4agg` backend, which requires `PySide`. If you install
`PySide` with `pip`, make sure that you have tools `cmake` and `qmake`. The last
one is typically found in something like `libqt4-dev`.

##### Fixing Pylab
Problem happens because for some reason the post-installation script
"`pyside_postinstall.py`" did not run. Fix it by executing:
```
python bin/pyside_postinstall.py -install
```

#### Description of requirements
I tested the package using virtual environment and generated a list of
dependencies with the "`pip freeze`" command.
Basically, you should have on your computer the following packages:
 * `pylab` for plotting (_note_: you need support for an interactive backend,
    e.g. qt4agg, wxagg, gtkagg, tkagg, etc.). You can test whether you have a
    suitable backend by running the following line of code in your python
    interpeter: `import pylab as p; p.gca(); p.show()`.
    If a window with empty axes will pop up, then everything is correct!
 * `xcal_raman` for x-axis calibration and reading of SPE files
    (available on https://pypi.python.org/pypi/xcal_raman)
 * `pyZenity` for graphical interaction with user

### Use
You can select this programm to be the default application to open SPE files.
Then if you click an SPE file, the programm gets its filename as a first
argument.

#### First run
If you start it for the first time in some specific folder, it will ask you a
couple of questions and create a config file `.speview.conf` based on your
answers.

#### User interaction
Then a standard matplotlib window with a plotted spectrum will popup. You can
use all features the matplotlib offers you:
  * Adjust figure size and line parameters
  * Pan and scale the plot with mouse and icons on top
  * Save figure (`S` key)
  * Turn grid on/off (`G` key)
  * Turn axis scale (log or linear) with `l` key for y-axis and `L` key for
    x-axis

Use the following keystrokes for additional functions, not offered by
matplotlib:
  * `Right` and `left` arrows: go to next/previous SPE file
  * `Space` bar: save current spectrum to buffer or remove it from buffer
  * `d` key to subtract a saved spectrum from the current one (the result is
     displayed in another scale)
  * `D` to remove the result of subtraction (opposite of `d`)
  * `v` or `V` to toggle the visibility of current spectrum (useful if you,
    for example, would like to see only the result of the subtraction)
  * **`h` or `H` to display the help message and the program version**

#### Future plans
What I would like to implement in the future:
 * Reading of SPE files with multiple spectra
 * Reading of CSV files generated by WinSpec
 * Display file information (acquisition settings,
   date/time, comments, etc...)

For more details, see https://github.com/ximeg/speview/issues
