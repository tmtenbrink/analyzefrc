from typing import Union, Optional

from dataclasses import dataclass, field

import numpy as np


__all__ = ['Curve',  'CurveTask', 'FRCSet', 'FRCMeasurement', 'FRCMeasureSettings', 'frc1_set', 'frc2_set', 'frc_set', 'frc_measure']


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
    id: str = None

    def __post_init__(self):
        self.update_id()

    def update_id(self, index: Optional[int] = None):
        if index is not None:
            self.index = index
        self.id = f"{self.group_name}-c{self.index}"
        return self


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
class CurveTask:
    key: str = ''
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





def frc_measure(img: np.ndarray, img_2: Optional[np.ndarray] = None, set_name='FRCmeasure', nm_per_pixel=1, **kwargs):
    settings = FRCMeasureSettings(nm_per_pixel, **kwargs)
    return FRCMeasurement(set_name, 0, settings, img, image_2=img_2)


def frc_set(measure: FRCMeasurement, *args: FRCMeasurement, name='FRCset'):
    measures = (measure, *args)
    indexed_measures = [measure.update_id(i) for i, measure in enumerate(measures)]
    return FRCSet(name, indexed_measures)


def frc1_set(img: np.ndarray, name='1FRCset', nm_per_pixel=1, **kwargs):
    settings = FRCMeasureSettings(nm_per_pixel=nm_per_pixel, **kwargs)
    measurement = FRCMeasurement(name, 0, settings, img)
    return FRCSet(name, [measurement])


def frc2_set(img1: np.ndarray, img2: np.ndarray, name='2FRCset', nm_per_pixel=1, **kwargs):
    settings = FRCMeasureSettings(nm_per_pixel=nm_per_pixel, **kwargs)
    measurement = FRCMeasurement(name, 0, settings, img1, image_2=img2)
    return FRCSet(name, [measurement])
