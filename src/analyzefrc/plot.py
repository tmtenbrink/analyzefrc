from dataclasses import dataclass
from analyzefrc.process import Curve
import matplotlib.pyplot as plt


class PlotGroup:
    title: str
    curves: list[Curve]

    def __init__(self, *args, title='Title'):
        self.title = title
        curves = []
        for arg in args:
            if isinstance(arg, list):
                curves += arg
            else:
                curves.append(arg)
        self.curves = curves

    def plot(self):
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
        plt.show()