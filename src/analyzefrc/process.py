from analyzefrc.deps_types import Optional, Union, Callable
from analyzefrc.deps_types import dip
from dataclasses import dataclass
from frc.deps_types import Img
import frc.frc_functions as frcf
import frc.utility as util
import numpy as np
from readlif.reader import LifFile
import matplotlib.pyplot as plt
from deco import concurrent, synchronized


@dataclass
class FRCMeasureSettings:
    nm_per_pixel: float
    NA: Optional[float] = None
    lambda_excite_nm: Optional[float] = None


@dataclass
class FRCMeasurement:
    """
    An FRCMeasurement represents a single measurement within an FRCImage and contains the actual data as
    a DIP Image (which itself can be converted to a numpy array at no cost). If only one image is provided,
    it will calculate a 1FRC. If two are provided, it will calculate the standard FRC between 2 images.
    """
    group_name: str
    index: int
    settings: FRCMeasureSettings
    image: np.ndarray
    image_2: Optional[np.ndarray] = None


class FRCImage:
    """
    The FRCImage represents a single measurement group, where each measurement in the group has the same
    image dimensions, is square and is windowed to prevent FFT artifacts. I.e. they are fully preprocessed.
    Measurements should also have occurred under similar conditions, i.e. same camera, lens, with only
    some properties variable per image.
    """
    name: str
    measurements: list[FRCMeasurement]

    def __init__(self, name, measurements) -> None:
        self.name = name
        self.measurements = measurements


@dataclass
class ProcessTask:
    processings: list[Callable]
    measure: FRCMeasurement


def process_task(task: ProcessTask):
    for processing in task.processings:
        task.measure = processing(task.measure)


@concurrent
def process_task_conc(task: ProcessTask):
    process_task(task)

@synchronized
def process_all_tasks(tasks: list[ProcessTask], concurrent):
    if concurrent:
        for t in tasks:
            process_task_conc(t)
    else:
        for t in tasks:
            process_task(t)


def plot_curves(imgs: Union[list[FRCImage], FRCImage], preprocess=True, concurrent=True):
    if isinstance(imgs, FRCImage):
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
    process_all_tasks(process_tasks, concurrent)


def preprocess_measure(measure: FRCMeasurement):
    measure.image = preprocess_img(measure.image)
    if measure.image_2 is not None:
        measure.image_2 = preprocess_img(measure.image_2)
    return measure


def preprocess_img(img: np.ndarray):
    img = util.square_image(img, add_padding=False)
    return util.apply_tukey(img)


def single_curve(measure: FRCMeasurement):
    img = measure.image
    img_size = img.shape[0]
    nm_per_pixel = measure.settings.nm_per_pixel
    frc_curve = frcf.one_frc(img, 1)
    xs_pix = np.arange(len(frc_curve)) / img_size
    xs_nm_freq = xs_pix * (1 / nm_per_pixel)

    fig, ax = plt.subplots()

    smooth_frac = 0.2 # TODO parameter
    smooth_desc = ""
    if smooth:
        smooth_desc = " LOESS smoothing (point frac: {}).".format(smooth_frac)

    frc_res, res_y, thres = frcf.frc_res(xs_nm_freq, frc_curve, img_size)
    # plt.plot(xs_nm_freq, thres(xs_nm_freq))
    # plt.plot(xs_nm_freq, frc_curve)
    # plt.show()
    return measure
