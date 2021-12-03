# Copyright (C) 2021                Department of Imaging Physics
# All rights reserved               Faculty of Applied Sciences
#                                   TU Delft
# Tip ten Brink

from typing import Union, Callable

from pathlib import Path

import matplotlib.pyplot as plt

from analyzefrc.read import Curve


__all__ = ['CurvePlot', 'plot_all']


class CurvePlot:
    """ Represents a series of curves to be plotted in one figure. """
    title: str
    curves: list[Curve]

    def __init__(self, *args: Union[Curve, list[Curve]], title='Title'):
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

    def plot(self, show=False, save=False, save_directory: Path = None, ax_fig_ops: Callable = None, dpi=180, **kwargs):
        min_y = -0.1
        max_y = 1.1

        fig, ax = plt.subplots()

        descs = []
        for curve in self.curves:
            ax.plot(curve.curve_x, curve.curve_y, label=curve.curve_label, zorder=2)

            ax.plot(curve.curve_x, curve.thres, c='darkgoldenrod', label=f"Threshold curve ({curve.thres_name})",
                    zorder=1)
            ax.vlines(1 / curve.frc_res, min_y, curve.res_y, ls='dashed', colors=['darkgoldenrod'], zorder=3)
            descs.append(curve.desc)

        ax.set_xlabel("Spatial frequency ($\\mathrm{nm}^{-1}$)")
        ax.set_ylabel("FRC")

        ax.legend()
        ax.set_ylim(min_y, max_y)

        ax.set_title(self.title)

        fig.supxlabel('\n'.join(descs), fontsize='small')
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
            fig.savefig(save_path, dpi=dpi, **kwargs)
        if show:
            plt.show()
        plt.close(fig)


def plot_all(*multiple_groups: dict[str, list[Curve]], show=True, save=False, save_directory=None, dpi=180):
    """
    Plot each entry in the supplied dictionaries (can be separate arguments) in a single plot.

    :param multiple_groups: Multiple dictionaries containing lists of Curves. Each entry is a plot.
    :param bool show: Show the plot.
    :param bool save: Save each plot as an image, requires save_directory.
    :param save_directory: Exact directory where each plot can be saved. Use analyzefrc.helper.create_save.
    :param dpi: Plot image size.
    """
    curve_plots = []
    for multiple_group in multiple_groups:
        for group_name, group in multiple_group.items():
            curve_plots.append(CurvePlot(group, title=group_name))
    for curve_plot in curve_plots:
        curve_plot.plot(show=show, save=save, save_directory=save_directory, dpi=dpi)
