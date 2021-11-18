import frc.frc_functions as frcf
import frc.utility as util
from frc.deps_types import Img, np, Optional, NoIntersectionException
from analyzefrc.deps_types import plt
from loess.loess_1d import loess_1d


def compute_plot_frc(img: Img, um_per_pixel, max_val, c_max, NA, methods='1FRC1', mxs=None, window='default', smooth=False,
                     avg=10, title='', save=False, save_path=None, extra_res_plot: Optional[float] = None):
    if not isinstance(methods, list):
        methods = [methods]
    if mxs is None:
        mxs = np.array([1])
    img = np.array(img)
    img_size = np.ma.size(img, axis=0)
    # print("{} {}".format(title, np.average(img)))
    img = util.square_image(img, False)
    res_pix = None
    res_curve = None
    res_nm = None
    frc_curve_list = None
    fig, ax = plt.subplots()

    smooth_frac = 0.2
    smooth_desc = ""
    if smooth:
        smooth_desc = " LOESS smoothing (point frac: {}).".format(smooth_frac)

    for method in methods:
        for mx in mxs:
            if not mx == 1:
                if mx <= 10:
                    mx *= max_val
                mxd_img = img * (mx / max_val)
            else:
                mxd_img = img

            if window == 'default':
                tukey = True
            else:
                tukey = False

            if tukey:
                frc_prepared = util.apply_tukey(mxd_img)
            else:
                frc_prepared = False

            if method == '1FRC1':

                def frc_func(img_frc):
                    return frcf.one_frc(img_frc, 1)
            elif method == '1FRC2':

                def frc_func(img_frc):
                    return frcf.one_frc(img_frc, 1)
            else:
                raise ValueError("Unknown method {}, use one of {}".format(method, ", ".join(methods)))

            frc_curve = frc_func(frc_prepared)
            frc_curves = [frc_curve]
            for i in range(avg - 1):
                calculated_frc = frc_func(frc_prepared)
                frc_curve += calculated_frc
                frc_curves.append(calculated_frc)

            frc_curve /= avg

            xs_pix = np.arange(len(frc_curve)) / img_size
            xs_nm = xs_pix / um_per_pixel / 1000
            label = method + (" mx {0:.0f}".format(mx) if mx != 0 else "")

            smooth_frac = 0.2
            if smooth:
                xs_pix, frc_curve, wout = loess_1d(xs_pix, frc_curve, frac=smooth_frac)

            ax.plot(xs_nm, frc_curve, label=label, zorder=2)

            if res_pix is None:
                res_pix = xs_pix
            if res_nm is None:
                res_nm = xs_nm
            if res_curve is None:
                res_curve = frc_curve
            if frc_curve_list is None:
                frc_curve_list = frc_curves

    min_y = -0.1
    max_y = 1.1

    ax.set_xlabel("Spatial frequency ($\\mathrm{nm}^{-1}$)")
    ax.set_ylabel("FRC")

    frc_res = 0
    res_sd = 0
    try:
        frc_res_1o7, res_y_1o7, thres_1o7 = frcf.frc_res(res_pix, res_curve, img_size, '1/7')
        frc_res_1o7 *= um_per_pixel * 1000
        ax.plot(res_nm, thres_1o7(res_pix), c='darkgoldenrod', label="Threshold curve (1/7)", zorder=1)
        ax.vlines(1 / frc_res_1o7, min_y, res_y_1o7, ls='dashed', colors=['darkgoldenrod'], zorder=3)

        frc_res, res_y, thres = frcf.frc_res(res_pix, res_curve, img_size, 'half_bit')
        frc_res *= um_per_pixel * 1000
        ax.plot(res_nm, thres(res_pix), c='mediumvioletred', label="Threshold curve (1/2 bit)", zorder=1)
        ax.vlines(1 / frc_res, min_y, res_y, ls='dashed', colors=['mediumvioletred'], zorder=3)

        frc_res = frc_res_1o7

        if extra_res_plot is not None:
            extra_res_x = 1 / extra_res_plot
            extra_res_x_i = int(extra_res_x * um_per_pixel * 1000 * img_size)
            extra_res_closest_x = res_nm[extra_res_x_i]
            extra_res_y = res_curve[extra_res_x_i]
            ax.vlines(extra_res_closest_x, min_y, extra_res_y, ls='dashed', colors=['orange'], label="Diffr. limit", zorder=3)

        frc_res_list = []
        for frc_curve_v in frc_curve_list:
            try:
                frc_res_v, _res_y, _thres = frcf.frc_res(res_pix, frc_curve_v, img_size, 'half_bit')
                res_for_sd = (frc_res_v * um_per_pixel * 1000)
                frc_res_list.append(res_for_sd)
            except NoIntersectionException:
                pass
        res_sd = np.std(np.array(frc_res_list))
    except ValueError as e:
        print(e)
    ax.legend()
    ax.set_ylim(min_y, max_y)
    sd_str = ''
    if res_sd > 0:
        sd_str = "± {:.2g} ".format(res_sd)
    ax.set_title(title)
    desc = "Resolution (1/7 threshold): {:.3g} {}nm.{} {} curves averaged.".format(frc_res, sd_str, smooth_desc, avg)
    if extra_res_plot:
        desc += " {:.3g} nm diffr. limit".format(extra_res_plot)
    # desc = "Resolution: {0:.4g} nm.{1} Img max: {2}/{3}. {4} curves averaged.".format(frc_res, smooth_desc, max_val,
    #                                                                                  c_max, avg)
    fig.supxlabel(desc, fontsize='small')
    fig.set_tight_layout(True)
    if save:
        fig.savefig(save_path, dpi=180)
    plt.close(fig)
    if frc_res > 0:
        return frc_res, res_sd, NA
