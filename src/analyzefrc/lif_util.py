import diplib as dip
import matplotlib.pyplot as plt
import matplotlib.colors
import numpy as np


def _label_colormap():
    cm = np.array([
        [1.0000, 0.0000, 0.0000],
        [0.0000, 1.0000, 0.0000],
        [0.0000, 0.0000, 1.0000],
        [1.0000, 1.0000, 0.0000],
        [0.0000, 1.0000, 1.0000],
        [1.0000, 0.0000, 1.0000],
        [1.0000, 0.3333, 0.0000],
        [0.6667, 1.0000, 0.0000],
        [0.0000, 0.6667, 1.0000],
        [0.3333, 0.0000, 1.0000],
        [1.0000, 0.0000, 0.6667],
        [1.0000, 0.6667, 0.0000],
        [0.0000, 1.0000, 0.5000],
        [0.0000, 0.3333, 1.0000],
        [0.6667, 0.0000, 1.0000],
        [1.0000, 0.0000, 0.3333],
    ])
    n = len(cm)
    index = list(i % n for i in range(0, 255))
    cm = np.concatenate((np.array([[0, 0, 0]]), cm[index]))
    return matplotlib.colors.ListedColormap(cm)


def show(img, title='', range=(), complexMode='abs', projectionMode='mean', coordinates=(), dim1=0, dim2=1, colormap='',
         save=False, save_path=None):
    out = dip.ImageDisplay(img, range, complexMode=complexMode, projectionMode=projectionMode, coordinates=coordinates,
                           dim1=dim1, dim2=dim2)
    if out.Dimensionality() == 1:
        axes = plt.gca()
        axes.clear()
        axes.plot(out)
        axes.set_ylim((0, 255))
        axes.set_xlim((0, out.Size(0) - 1))
        axes.set_title(title)
    else:
        if colormap == '':
            if range == 'base' or range == 'based':
                colormap = 'coolwarm'
            elif range == 'modulo' or range == 'labels':
                colormap = 'labels'
            elif range == 'angle' or range == 'orientation':
                colormap = 'hsv'
            else:
                colormap = 'gray'
        if colormap == 'labels':
            cmap = _label_colormap()
        else:
            cmap = plt.get_cmap(colormap)
        plt.title(title)
        plt.imshow(out, cmap=cmap, norm=matplotlib.colors.NoNorm(), interpolation='none')
    plt.draw()
    if save:
        plt.savefig(save_path)
    plt.pause(0.001)