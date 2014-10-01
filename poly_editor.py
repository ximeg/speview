"""
This is an example to show how to build cross-GUI applications using
matplotlib event handling to interact with objects on the canvas

"""
import numpy as np
import matplotlib.pyplot as plt


class Interactor():
    def __init__(self):
        self.canvas = plt.gcf().canvas
        self.ax = plt.gca()

        self.canvas.mpl_connect('button_press_event', self.button_press_callback)
        self.canvas.mpl_connect('key_press_event', self.key_press_callback)

    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        if not event.inaxes: return
        if event.button == 2:
            plt.plot(np.random.normal(size=100), np.random.normal(size=100), "+")
        else:
            plt.plot(np.random.normal(size=100), np.random.normal(size=100), "x")
        self.canvas.draw()

    def key_press_callback(self, event):
        'whenever a key is pressed'
        plt.plot(np.random.normal(size=10), np.random.normal(size=10), ".")
        if event.key=='t':
            print "Key is 't'"
        elif event.key=='d':
            print "Key is 'd'"
        elif event.key=='i':
            print "Key is 'i'"
        self.canvas.draw()

p = Interactor()
plt.show()

