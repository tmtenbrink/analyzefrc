# Copyright (C) 2021                Department of Imaging Physics
# All rights reserved               Faculty of Applied Sciences
#                                   TU Delft
# Tip ten Brink

from typing import Union, Optional, Callable

from dataclasses import dataclass, field
from frc.deps_types import Func1D

import numpy as np


__all__ = ['Curve',  'CurveTask', 'FRCSet', 'MeasureProcessing', 'FRCMeasurement', 'FRCMeasureSettings', 'frc1_set',
           'frc2_set', 'frc_set', 'frc_measure']


@dataclass
class FRCMeasureSettings:
    """
    Dataclass containing information about a specific FRCMeasurement. The scale (nm_per_pixel) is the most important.
    """
    nm_per_pixel: float
    extra: dict = field(default_factory=dict)  # Mutable variable requires special initializer
    NA: Optional[float] = None  # Numerical aperture
    lambda_excite_nm: Optional[float] = None  # Excitation wavelength


@dataclass
class Curve:
    """
    Dataclass containing the resulting curve of an FRC computation.
    It also contains the accompanying threshold function that was used to measure the resolution.
    """
    key: str  # Should be unique per measurement

    curve_x: np.ndarray
    curve_y: np.ndarray
    frc_res: float

    curve_title: str
    curve_label: str  # Used for label in matplotlib legend
    desc: str

    res_sd: float
    res_y: float
    thres: np.ndarray
    thres_name: str

    measure: 'FRCMeasurement'


@dataclass
class CurveTask:
    """
    Represents a task that will result in the computation of an FRC curve.
    Processing FRCMeasurement-objects will generate a Curve for each CurveTask
    """
    key: str = ''
    method: str = '1FRC1'  # 2FRC can be passed explicitly
    smooth: bool = False  # Use LOESS smoothing for the curve
    smooth_frac: float = 0.2  # Used for determining the fraction of points used for LOESS smoothing
    avg_n: int = None  # Number of curves used for averaging, can be overridden by process_frc
    threshold: Union[str, Func1D] = '1/7'  # Threshold corresponding to possible threshold in frc.frc_functions.frc_res

    def __post_init__(self):
        """
        If 2FRC is used, there was no randomization due to random binomial splitting,
        so using more than one curve is unnecessary. If there is smoothing, it also
        should not be the default.
        """
        if self.avg_n is None:
            if self.method == '2FRC' or self.smooth:
                self.avg_n = 1
            else:
                self.avg_n = 5


@dataclass
class FRCMeasurement:
    """
    An FRCMeasurement represents a single measurement within an FRCSet and contains the actual data as
    a NumPy array. If only one image is provided, it will calculate a 1FRC. If two are provided, it will calculate the
    standard FRC between 2 images.
    """
    group_name: str  # Should correspond to the FRCSet
    index: int  # Should be unique within an FRCSet, use frc_set(...) to index automatically
    settings: FRCMeasureSettings
    image: np.ndarray  # Image data
    extra_processings: Optional[list['MeasureProcessing']] = None  # Optional processing steps to be performed curve
    curve_tasks: Optional[list[CurveTask]] = None  # Curves to be computed from the measurement
    image_2: Optional[np.ndarray] = None  # Used for 2FRC
    curves: list[Curve] = None  # Output curves, set after processing
    id: str = None  # Unique overall if updated and if group_name and index are unique

    def __post_init__(self):
        self.update_id()

    def update_id(self, index: Optional[int] = None) -> 'FRCMeasurement':
        if index is not None:
            self.index = index
        self.id = f"{self.group_name}-c{self.index}"
        return self


# Function transforming an FRCMeasurement
MeasureProcessing = Callable[[FRCMeasurement], FRCMeasurement]


class FRCSet:
    """
    The FRCSet represents a single measurement group, where each measurement in the group has the same
    image dimensions and, as a rule of thumb, would fit together in a single plot.
    Measurements should also have occurred under similar conditions, i.e. same camera, lens, with only
    some properties variable per image.
    """
    name: str
    measurements: list[FRCMeasurement]

    def __init__(self, name, measurements):
        self.name = name
        self.measurements = measurements


def frc_measure(img: np.ndarray, img_2: Optional[np.ndarray] = None, set_name='FRCmeasure', nm_per_pixel=1,
                **kwargs) -> FRCMeasurement:
    """ Convenience function to get an FRCMeasurement (with 1 or 2 images) from image data. """
    settings = FRCMeasureSettings(nm_per_pixel, **kwargs)
    return FRCMeasurement(set_name, 0, settings, img, image_2=img_2)


def frc_set(measure: FRCMeasurement, *args: FRCMeasurement, name='FRCset') -> FRCSet:
    """
    Convenience function to get an FRCSet from an arbitrary amount of FRCMeasurements.
    """
    measures = (measure, *args)
    indexed_measures = [measure.update_id(i) for i, measure in enumerate(measures)]
    return FRCSet(name, indexed_measures)


def frc1_set(img: np.ndarray, name='1FRCset', nm_per_pixel=1, **kwargs) -> FRCSet:
    """
    Convenience function to get an FRCSet directly from image data.
    Additional keyword arguments are passed to FRCMeasureSettings instantiation.
    """
    settings = FRCMeasureSettings(nm_per_pixel=nm_per_pixel, **kwargs)
    measurement = FRCMeasurement(name, 0, settings, img)
    return FRCSet(name, [measurement])


def frc2_set(img1: np.ndarray, img2: np.ndarray, name='2FRCset', nm_per_pixel=1, **kwargs):
    """
    Convenience function to get an FRCSet directly from image data for 2FRC.
    Additional keyword arguments are passed to FRCMeasureSettings instantiation.
    """
    settings = FRCMeasureSettings(nm_per_pixel=nm_per_pixel, **kwargs)
    measurement = FRCMeasurement(name, 0, settings, img1, image_2=img2)
    return FRCSet(name, [measurement])
