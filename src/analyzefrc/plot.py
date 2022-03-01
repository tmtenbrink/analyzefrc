# Copyright (C) 2021                Department of Imaging Physics
# All rights reserved               Faculty of Applied Sciences
#                                   TU Delft
# Tip ten Brink

from typing import Union, Callable, Optional

from pathlib import Path

import numpy as np
import similaritymeasures as sim
import matplotlib.pyplot as plt

from analyzefrc.read import Curve

__all__ = ['CurvePlot', 'plot_all']


class CurvePlot:
    """ Represents a series of curves to be plotted in one figure. """
    title: str
    curves: list[Curve]
    len_unit: str

    def __init__(self, *args: Union[Curve, list[Curve]], title='Title', len_unit='nm'):
        self.title = title
        curves = []
        for arg in args:
            if isinstance(arg, list):
                curves += arg
            elif isinstance(arg, Curve):
                curves.append(arg)
            else:
                raise ValueError("Arguments must be Curves or lists of Curves!")
        self.curves = curves
        self.len_unit = len_unit

    def plot(self, show=False, save=False, save_directory: Path = None, desc_mode='supx', ax_fig_ops: Callable = None, dpi=180,
             save_kwargs: Optional[dict] = None):

        min_y = -0.1
        max_y = 1

        if save_kwargs is None:
            save_kwargs = dict()

        fig, ax = plt.subplots()

        descs = []

        if len(self.curves) == 2:
            curve1 = self.curves[0]
            lenlen = curve1.curve_x
            curve2 = self.curves[1]
            xy_curve1 = np.zeros((lenlen.shape[0], 2))
            xy_curve2 = np.zeros((lenlen.shape[0], 2))

            xy_curve1[:, 0] = curve1.curve_x
            xy_curve1[:, 1] = curve1.curve_y
            xy_curve2[:, 0] = curve2.curve_x
            xy_curve2[:, 1] = curve2.curve_y

            frech_dist = sim.frechet_dist(xy_curve1, xy_curve2)
            descs.append(f"The Frechet distance between the two curves is {frech_dist:.3g}.")

        plotted_thres = set()

        for curve in self.curves:
            ax.plot(curve.curve_x, curve.curve_y, label=curve.curve_label, zorder=2)

            if curve.thres_name not in plotted_thres and curve.thres is not None:
                ax.plot(curve.curve_x, curve.thres, c='darkgoldenrod', label=f"Threshold curve ({curve.thres_name})",
                        zorder=1)
                plotted_thres.add(curve.thres_name)
            if curve.frc_res != -1:
                ax.vlines(1 / curve.frc_res, min_y, curve.res_y, ls='dashed', colors=['darkgoldenrod'], zorder=3)
            descs.append(curve.desc)

        ax.set_xlabel(f"Spatial frequency ($\\mathrm{{{self.len_unit}}}^{{-1}}$)")
        ax.set_ylabel("FRC")

        ax.legend()
        ax.set_ylim(min_y, max_y)

        ax.set_title(self.title)

        if desc_mode == 'supx':
            fig.supxlabel('\n'.join(descs), fontsize='small')
        elif desc_mode == 'print':
            print('\n'.join(descs))
        else:
            raise ValueError("Unknown value for 'desc_mode'!")
        fig.set_tight_layout(True)

        if ax_fig_ops is not None:
            ax, fig = ax_fig_ops(self, ax, fig)

        if save:
            if save_directory is None:
                raise ValueError("Save folder path must be given when saving!")
            save_path = save_directory.joinpath(self.title)
            i = 0
            while save_path.exists():
                save_path = save_path.parent.joinpath(f"{self.title}{i}")
                i += 1
            fig.savefig(save_path, dpi=dpi, **save_kwargs)
        if show:
            plt.show()
        plt.close(fig)


def plot_all(*multiple_groups: dict[str, list[Curve]], show=True, save=False, desc_mode='supx', save_directory=None,
             dpi=180, ax_fig_ops: Optional[Callable] = None):
    """
    Plot each entry in the supplied dictionaries (can be separate arguments) in a single plot.

    :param multiple_groups: Multiple dictionaries containing lists of Curves. Each entry is a plot.
    :param bool show: Show the plot.
    :param bool save: Save each plot as an image, requires save_directory.
    :param save_directory: Exact directory where each plot can be saved. Use analyzefrc.helper.create_save.
    :param dpi: Plot image size.
    :param ax_fig_ops: Function to perform on ax and fig like: (curve_plot, ax, fig) -> ax, fig
    """

    curve_plots = []
    for multiple_group in multiple_groups:
        for title, group in multiple_group.items():
            len_unit = None
            if group:
                len_unit = group[0].measure.settings.len_unit
            curve_plots.append(CurvePlot(group, title=title, len_unit=len_unit))
    for curve_plot in curve_plots:
        curve_plot.plot(show=show, save=save, save_directory=save_directory, desc_mode=desc_mode, dpi=dpi,
                        ax_fig_ops=ax_fig_ops)
