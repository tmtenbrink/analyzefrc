from analyzefrc.deps_types import Optional, Union, Callable
from dataclasses import dataclass, field
from frc.deps_types import NoIntersectionException
import frc.frc_functions as frcf
import frc.utility as util
import numpy as np
import matplotlib.pyplot as plt
from deco import concurrent, synchronized
from loess.loess_1d import loess_1d


@dataclass
class FRCMeasureSettings:
    nm_per_pixel: float
    extra: dict = field(default_factory=dict)
    smooth_curve: bool = False
    NA: Optional[float] = None
    lambda_excite_nm: Optional[float] = None


@dataclass
class Curve:
    key: str

    curve_x: np.ndarray
    curve_y: np.ndarray
    frc_res: float

    curve_title: str
    curve_label: str
    desc: str

    res_sd: float
    res_y: float
    thres: np.ndarray
    thres_name: str

    measure: 'FRCMeasurement'


@dataclass
class FRCMeasurement:
    """
    An FRCMeasurement represents a single measurement within an FRCSet and contains the actual data as
    a DIP Image (which itself can be converted to a numpy array at no cost). If only one image is provided,
    it will calculate a 1FRC. If two are provided, it will calculate the standard FRC between 2 images.
    """
    group_name: str
    index: int
    settings: FRCMeasureSettings
    image: np.ndarray
    curve_tasks: Optional[list] = None
    image_2: Optional[np.ndarray] = None
    curves: list[Curve] = None


class FRCSet:
    """
    The FRCSet represents a single measurement group, where each measurement in the group has the same
    image dimensions, is square and is windowed to prevent FFT artifacts. I.e. they are fully preprocessed.
    Measurements should also have occurred under similar conditions, i.e. same camera, lens, with only
    some properties variable per image.
    """
    name: str
    measurements: list[FRCMeasurement]

    def __init__(self, name, measurements):
        self.name = name
        self.measurements = measurements


@dataclass
class PlotTask:
    method: str = '1FRC1'
    smooth: bool = False
    smooth_frac: float = 0.2
    avg_n: int = None
    plot_res: bool = True
    threshold: str = '1/7'

    def __post_init__(self):
        if self.avg_n is None:
            if self.method == '2FRC' or self.smooth:
                self.avg_n = 1
            else:
                self.avg_n = 5


@dataclass
class CurveTask:
    method: str = '1FRC1'
    smooth: bool = False
    smooth_frac: float = 0.2
    avg_n: int = None
    threshold: str = '1/7'

    def __post_init__(self):
        if self.avg_n is None:
            if self.method == '2FRC' or self.smooth:
                self.avg_n = 1
            else:
                self.avg_n = 5


@dataclass
class ProcessTask:
    processings: list[Callable]
    measure: FRCMeasurement


def process_task(task: ProcessTask):
    print(f"{task.measure.group_name} {task.measure.index}")
    for processing in task.processings:
        task.measure = processing(task.measure)
    return task.measure.curves


@concurrent
def process_task_conc(task: ProcessTask):
    for processing in task.processings:
        task.measure = processing(task.measure)
    return task.measure.curves


@synchronized
def process_all_tasks(tasks: list[ProcessTask], concurrency):
    if concurrency:
        for t in tasks:
            process_task_conc(t)
    else:
        for t in tasks:
            process_task(t)


@synchronized
def process_measures_conc(measure_tasks: list[ProcessTask]) -> dict:
    processed_measures = {}
    for task in measure_tasks:
        processed_measures[(task.measure.group_name, task.measure.index)] = process_task_conc(task)
    return processed_measures


def process_measures(measure_tasks: list[ProcessTask]) -> dict:
    processed_measures = {}
    for task in measure_tasks:
        processed_measures[(task.measure.group_name, task.measure.index)] = process_task(task)

    return processed_measures


def create_tasks(frc_sets: Union[list[FRCSet], FRCSet], preprocess=True, concurrency=True):
    if isinstance(frc_sets, FRCSet):
        frc_sets = [frc_sets]
    process_tasks = []
    for frc_set in frc_sets:
        for measure in frc_set.measurements:
            if preprocess:
                tasks = [preprocess_measure]
            else:
                tasks = []
            tasks.append(measure_curve)
            process_tasks.append(ProcessTask(tasks, measure))
    processed_measures = process_measures_conc(process_tasks) if concurrency else process_measures(process_tasks)
    processed = [curve for curves in processed_measures.values() for curve in curves]
    return processed


# def analyze(imgs: Union[list[FRCSet], FRCSet], plot_groups: list[PlotGroup], preprocess=True, concurrency=True):
#     processed = create_tasks(imgs, preprocess, concurrency)


def plot_curves(imgs: Union[list[FRCSet], FRCSet], preprocess=True, concurrency=True, save=True):
    if isinstance(imgs, FRCSet):
        imgs = [imgs]
    process_tasks = []
    for img in imgs:
        for measure in img.measurements:
            print(f"{img.name} {measure.index}")
            if preprocess:
                tasks = [preprocess_measure]
            else:
                tasks = []
            tasks.append(single_curve)
            process_tasks.append(ProcessTask(tasks, measure))
    process_all_tasks(process_tasks, concurrency)


def preprocess_measure(measure: FRCMeasurement):
    measure.image = preprocess_img(measure.image)
    if measure.image_2 is not None:
        measure.image_2 = preprocess_img(measure.image_2)
    return measure


def preprocess_img(img: np.ndarray):
    img = util.square_image(img, add_padding=False)
    return util.apply_tukey(img)


def measure_curve(measure: FRCMeasurement):
    img = measure.image
    # Can be None
    img2 = measure.image_2
    img_size = img.shape[0]
    nm_per_pixel = measure.settings.nm_per_pixel
    frc_curve = frcf.one_frc(img, 1)
    xs_pix = np.arange(len(frc_curve)) / img_size
    xs_nm_freq = xs_pix * (1 / nm_per_pixel)

    if measure.curve_tasks is None:
        if measure.image_2 is None:
            measure.curve_tasks = [CurveTask()]
        else:
            measure.curve_tasks = [CurveTask(method='2FRC', avg_n=1)]

    curves = []
    for curve_i, curve_task in enumerate(measure.curve_tasks):

        if curve_task.method == '1FRC' or curve_task.method == '1FRC1':
            def frc_func(img_frc, _img2):
                return frcf.one_frc(img_frc, 1)
        elif curve_task.method == '2FRC':
            def frc_func(img_frc_1, img_frc_2):
                return frcf.two_frc(img_frc_1, img_frc_2)
        else:
            raise ValueError("Unknown method {}".format(curve_task.method))
        frc_curve = frc_func(img, img2)
        frc_curves = [frc_curve]
        for i in range(curve_task.avg_n - 1):
            calculated_frc = frc_func(img, img2)
            frc_curve += calculated_frc
            frc_curves.append(calculated_frc)

        frc_curve /= curve_task.avg_n

        label = curve_task.method

        smooth_desc = ""
        if curve_task.smooth:
            smooth_desc = " LOESS smoothing (point frac: {}).".format(curve_task.smooth_frac)
            xs_pix, frc_curve, wout = loess_1d(xs_pix, frc_curve, frac=curve_task.smooth_frac)

        frc_res = -1
        sd_str = " "

        res_sd = 0
        res_y = 0
        thres_curve = None

        try:
            frc_res, res_y, thres = frcf.frc_res(xs_nm_freq, frc_curve, img_size, threshold=curve_task.threshold)
            thres_curve = thres(xs_pix)
            frc_res_list = []
            for res_curve in frc_curves:
                try:
                    frc_res, _, _ = frcf.frc_res(xs_nm_freq, res_curve, img_size, threshold=curve_task.threshold)
                    frc_res_list.append(frc_res)
                except NoIntersectionException:
                    pass
            res_sd = np.std(np.array(frc_res_list))
            if res_sd > 0:
                sd_str = "± {:.2g} ".format(res_sd)

        except NoIntersectionException as e:
            print(e)
        avg_desc = f"{curve_task.avg_n} curves averaged." if curve_task.avg_n > 1 else ""
        desc = "Resolution ({} threshold): {:.3g} {}nm. {} {}".format(curve_task.threshold, frc_res, sd_str,
                                                                      smooth_desc,
                                                                      avg_desc)

        curve = Curve(f"{measure.group_name}-{measure.index}-{curve_i}", xs_nm_freq, frc_curve, frc_res,
                      f"{measure.group_name} measurement {measure.index}", label, desc,
                      res_sd, res_y, thres_curve, curve_task.threshold, measure)
        curves.append(curve)
    measure.curves = curves
    return measure


def single_curve(measure: FRCMeasurement):
    img = measure.image
    # Can be None
    img2 = measure.image_2
    img_size = img.shape[0]
    nm_per_pixel = measure.settings.nm_per_pixel
    frc_curve = frcf.one_frc(img, 1)
    xs_pix = np.arange(len(frc_curve)) / img_size
    xs_nm_freq = xs_pix * (1 / nm_per_pixel)

    fig, ax = plt.subplots()

    # frc_res, res_y, thres = frcf.frc_res(xs_nm_freq, frc_curve, img_size)
    # plt.plot(xs_nm_freq, thres(xs_nm_freq))
    # plt.plot(xs_nm_freq, frc_curve)
    # plt.show()

    if measure.curve_tasks is None:
        if measure.image_2 is None:
            measure.curve_tasks = [PlotTask()]
        else:
            measure.curve_tasks = [PlotTask(method='2FRC', avg_n=1)]

    min_y = -0.1
    max_y = 1.1

    descs = []
    for plot_task in measure.curve_tasks:
        if plot_task.method == '1FRC' or plot_task.method == '1FRC1':
            def frc_func(img_frc, _img2):
                return frcf.one_frc(img_frc, 1)
        elif plot_task.method == '2FRC':
            def frc_func(img_frc_1, img_frc_2):
                return frcf.two_frc(img_frc_1, img_frc_2)
        else:
            raise ValueError("Unknown method {}".format(plot_task.method))
        frc_curve = frc_func(img, img2)
        frc_curves = [frc_curve]
        for i in range(plot_task.avg_n - 1):
            calculated_frc = frc_func(img, img2)
            frc_curve += calculated_frc
            frc_curves.append(calculated_frc)

        frc_curve /= plot_task.avg_n

        label = plot_task.method

        smooth_desc = ""
        if plot_task.smooth:
            smooth_desc = " LOESS smoothing (point frac: {}).".format(plot_task.smooth_frac)
            xs_pix, frc_curve, wout = loess_1d(xs_pix, frc_curve, frac=plot_task.smooth_frac)

        ax.plot(xs_nm_freq, frc_curve, label=label, zorder=2)

        frc_res = -1
        sd_str = " "

        try:
            frc_res, res_y, thres = frcf.frc_res(xs_nm_freq, frc_curve, img_size, threshold=plot_task.threshold)

            frc_res_list = []
            for res_curve in frc_curves:
                try:
                    frc_res, _, _ = frcf.frc_res(xs_nm_freq, res_curve, img_size, threshold=plot_task.threshold)
                    frc_res_list.append(frc_res)
                except NoIntersectionException:
                    pass
            res_sd = np.std(np.array(frc_res_list))
            if res_sd > 0:
                sd_str = "± {:.2g} ".format(res_sd)

            if plot_task.plot_res:
                ax.plot(xs_nm_freq, thres(xs_pix), c='darkgoldenrod', label=f"Threshold curve ({plot_task.threshold})",
                        zorder=1)
                ax.vlines(1 / frc_res, min_y, res_y, ls='dashed', colors=['darkgoldenrod'], zorder=3)
        except ValueError as e:
            print(e)
        avg_desc = f"{plot_task.avg_n} curves averaged." if plot_task.avg_n > 1 else ""
        desc = "Resolution ({} threshold): {:.3g} {}nm. {} {}".format(plot_task.threshold, frc_res, sd_str, smooth_desc,
                                                                      avg_desc)
        descs.append(desc)

    ax.set_xlabel("Spatial frequency ($\\mathrm{nm}^{-1}$)")
    ax.set_ylabel("FRC")

    ax.legend()
    ax.set_ylim(min_y, max_y)

    ax.set_title(f"{measure.group_name} measurement {measure.index}")

    desc = '\n'.join(descs)
    fig.supxlabel(desc, fontsize='small')
    fig.set_tight_layout(True)
    plt.show()
    # if save:
    #     fig.savefig(save_path, dpi=180)
    # plt.close(fig)
    # if frc_res > 0:
    #     return frc_res, res_sd, NA
