"""
This is an example to show how to build cross-GUI applications using
matplotlib event handling to interact with objects on the canvas

"""
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.artist import Artist
from matplotlib.mlab import dist_point_to_segment


class PolygonInteractor:
    """
    An polygon editor.

    Key-bindings

      't' toggle vertex markers on and off.  When vertex markers are on,
          you can move them, delete them

      'd' delete the vertex under point

      'i' insert a vertex at point.  You must be within epsilon of the
          line connecting two existing vertices

    """

    showverts = True
    epsilon = 5  # max pixel distance to count as a vertex hit

    def __init__(self, ax):
        self.ax = ax
        canvas = plt.gcf().canvas


        canvas.mpl_connect('draw_event', self.draw_callback)
        canvas.mpl_connect('button_press_event', self.button_press_callback)
        canvas.mpl_connect('key_press_event', self.key_press_callback)
        canvas.mpl_connect('button_release_event', self.button_release_callback)
        canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        self.canvas = canvas


    def draw_callback(self, event):
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.canvas.blit(self.ax.bbox)



    def get_ind_under_point(self, event):
        'get the index of the vertex under point if within epsilon tolerance'
        print "X=%i   Y=%i" % (event.x, event.y)
        return 1

    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        plt.plot(np.random.normal(size=100), np.random.normal(size=100), "+")
        if event.inaxes==None: return
        if event.button != 1: return
        self._ind = self.get_ind_under_point(event)
        self.canvas.draw()

    def button_release_callback(self, event):
        'whenever a mouse button is released'
        if event.button != 1: return
        self._ind = None

    def key_press_callback(self, event):
        'whenever a key is pressed'
        if not event.inaxes: return
        plt.plot(np.random.normal(size=10), np.random.normal(size=10), ".")
        if event.key=='t':
            print "Key is 't'"
        elif event.key=='d':
            print "Key is 'd'"
        elif event.key=='i':
            print "Key is 'i'"
        self.canvas.draw()

    def motion_notify_callback(self, event):
        'on mouse movement'
        if not self.showverts: return
        if event.inaxes is None: return
        if event.button != 1: return
        x,y = event.xdata, event.ydata


        self.canvas.restore_region(self.background)
        self.canvas.blit(self.ax.bbox)


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    p = PolygonInteractor(ax)

    plt.show()

