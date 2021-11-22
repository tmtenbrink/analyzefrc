from analyzefrc.deps_types import Optional
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
    NA: Optional[float]
    lambda_excite_nm: Optional[float]



@dataclass
class FRCMeasurement:
    """
    An FRCMeasurement represents a single measurement within an FRCImage and contains the actual data as
    a DIP Image (which itself can be converted to a numpy array at no cost).
    """
    image: np.ndarray
    group_name: str
    index: int
    settings: FRCMeasureSettings


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


def curves(imgs: list[FRCImage], preprocess=True):
    tasks = []
    for img in imgs:
        for measure in img.measurements:
            print(f"{img.name} {measure.index}")
            if preprocess:
                measure.image = preprocess_img(measure.image)
            single_curve(measure)

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
    frc_res, res_y, thres = frcf.frc_res(xs_nm_freq, frc_curve, img_size)
    plt.plot(xs_nm_freq, thres(xs_nm_freq))
    plt.plot(xs_nm_freq, frc_curve)
    plt.show()



def single_curve2(img: Img, scale):
    img = np.array(img)
    img = util.square_image(img, add_padding=False)
    img_size = img.shape[0]
    img = util.apply_tukey(img)
    frc_curve = frcf.one_frc(img, 1)
    xs_pix = np.arange(len(frc_curve)) / img_size
    xs_nm_freq = xs_pix * scale
    frc_res, res_y, thres = frcf.frc_res(xs_nm_freq, frc_curve, img_size)
    plt.plot(xs_nm_freq, thres(xs_nm_freq))
    plt.plot(xs_nm_freq, frc_curve)
    plt.show()



