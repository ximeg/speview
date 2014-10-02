# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 15:02:30 2014

@author: ximeg
"""
import pylab as pl
import numpy as np

class FileReader():
    def __init__(self, config):
        # Figure out if we need to perform calibration
        calibrated = True
        if calibrated:
            xcal_coeffs = np.loadtxt("xcal_coeffs.csv")
        else:
            xcal_coeffs = [1, 0]  # - uncalibrated
        self.cal_f = lambda x: np.polyval(xcal_coeffs, x)
        return calibrated

    def read_spe(self, fname):
        x, y = 0, 0
        return (x, self.cal_f(y), fname)

class DataSet():
    def __init__(self):
        self.data = [()]

    def add(self, item):
        self.data.append(item)

    def replace(self, item):
        self.data[-1] = item

    def remove(self):
        del self.data[-1]


def read_spe(fname):
    x, y = 0, 0
    return (x, y, fname)


class Window():
    def __init__(self, spelist):
        self.spelist = spelist
        # Create a data container
        self.dataset = DataSet()

        # Read spectrum and place first data into the container
        self.dataset.add(read_spe(spelist[0]))
        # Create a figure and show it (start the event loop)
        self.figure = pl.figure()
        self.ax = self.figure.gca()
        self.canvas = self.figure.canvas
        self.canvas.mpl_connect("key_press_event", self.key_event)

        self.figure.show()

    def key_event(self, e):
        pass

    def draw(self):
        # draw our self.dataset.data
        # change figure title and plot params
        canvas.draw()

    def go_next():
        """ Open next SPE file (NOT calibration or dark, see config). """
        self.ax.cla()
        self.spelist.append(self.spelist.pop(0))
        read_spe(spelist[0])
        self.draw()











#