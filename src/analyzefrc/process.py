# Copyright (C) 2021                Department of Imaging Physics
# All rights reserved               Faculty of Applied Sciences
#                                   TU Delft
# Tip ten Brink
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Union
from functools import partial
from dataclasses import dataclass
from frc.deps_types import NoIntersectionException
import frc.frc_functions as frcf
import frc.utility as util
import numpy as np
from deco import concurrent, synchronized
from loess.loess_1d import loess_1d

from analyzefrc.read import MeasureProcessing, FRCMeasurement, FRCSet, Curve, CurveTask

__all__ = ['group_all', 'group_sets', 'group_measures', 'process_frc', 'group_curves']


@dataclass
class _ProcessTask:
    processings: list[MeasureProcessing]
    measure: FRCMeasurement


def _process_task(task: _ProcessTask, i, task_n) -> list[Curve]:
    print(f"Processing {i + 1} out of {task_n}...")
    for processing in task.processings:
        task.measure = processing(task.measure)
    return task.measure.curves


@concurrent
def _process_task_conc(task: _ProcessTask, i, task_n):
    print(f"Processing {i + 1} out of {task_n}...")
    for processing in task.processings:
        task.measure = processing(task.measure)
    return task.measure.curves


@synchronized
def _process_measures_conc(measure_tasks: list[_ProcessTask]) -> dict:
    processed_measures = {}
    task_n = len(measure_tasks)
    for i, task in enumerate(measure_tasks):
        processed_measures[(task.measure.set_id, task.measure.index)] = _process_task_conc(task, i, task_n)
    return processed_measures


def _process_measures(measure_tasks: list[_ProcessTask]) -> dict[str, list[Curve]]:
    processed_measures = {}
    task_n = len(measure_tasks)
    for i, task in enumerate(measure_tasks):
        processed_measures[task.measure.id] = _process_task(task, i, task_n)
    return processed_measures


def _create_tasks(frc_sets: Union[list[FRCSet], FRCSet], preprocess=True,
                  extra_processings: Optional[list[MeasureProcessing]] = None,
                  override_n: int = 0, frc1_method: int = 1) -> list[_ProcessTask]:
    if isinstance(frc_sets, FRCSet):
        frc_sets = [frc_sets]
    process_tasks = []
    for frc_set in frc_sets:
        for measure in frc_set.measurements:
            if preprocess:
                tasks = [preprocess_measure]
            else:
                tasks = []
            if extra_processings is not None:
                tasks += extra_processings
            if measure.extra_processings is not None:
                tasks += measure.extra_processings

            override_n_measure = partial(measure_curve, override_n=override_n, frc1_method=frc1_method)

            tasks.append(override_n_measure)
            process_tasks.append(_ProcessTask(tasks, measure))

    return process_tasks


def group_all(process_name: str, curves: list[Curve]) -> dict[str, list[Curve]]:
    """ Group all curves together, will result in a single plot with all curves. """
    return {process_name: curves}


def group_curves(curves: list[Curve]) -> dict[str, list[Curve]]:
    """ Grouped so each curve will be plotted individually. """
    curve_dict = {}
    for c in curves:
        base_c_id = f"{c.measure.id}-{c.key}"
        c_id = base_c_id
        i = 0
        while c_id in curve_dict:
            c_id = f"{base_c_id}-{i}"
        curve_dict[c_id] = [c]
    return curve_dict


def group_measures(curves: list[Curve]) -> dict[str, list[Curve]]:
    """ Grouped so all curves per measurement will be plotted together. """
    measure_dict = {}
    for c in curves:
        if c.measure.id not in measure_dict:
            measure_dict[c.measure.id] = [c]
        else:
            measure_dict[c.measure.id] += c
    return measure_dict


def group_sets(curves: list[Curve]) -> dict[str, list[Curve]]:
    """ Grouped so all curves per set will be plotted together. """
    group_dict = {}
    for c in curves:
        if c.measure.set_id not in group_dict:
            group_dict[c.measure.set_id] = [c]
        else:
            group_dict[c.measure.set_id].append(c)
    return group_dict


def process_frc(process_name: str, frc_sets: Union[list[FRCSet], FRCSet], preprocess=True, concurrency=False,
                grouping: str = 'measures', override_n: int = 0, frc1_method: int = 1,
                extra_processings: Optional[list[MeasureProcessing]] = None) -> dict[str, list[Curve]]:
    """
    Process prepared FRCSets and compute curves.

    :param str process_name: Name of the overall process. Used as plot title in case everything is grouped together.
    :param frc_sets: Single FRCSet or list of FRCSets to process.
    :param bool preprocess: Crop images to square dimensions and apply Tukey window to prevent FFT artifacts.
    :param bool concurrency: Use deco for additional multithreading, can result in speedup. Call this function from an
        if __name__ == '__main__' block if using this option.
    :param str grouping: Grouping name used to group curves for later plotting. By default, curves within an
        FRCMeasurement are grouped together.
    :param int override_n: Override the default number of curves calculated and averaged. Will override even custom-set
        options for *all* curves.
    :param int frc1_method: Override the 1FRC method used. Defaults to single split and then subtract.
    :param extra_processings: Additional processing functions that are performed after preprocessing and before
        per-measurement extra processings.
    """
    print("Processing FRC sets...")
    tasks = _create_tasks(frc_sets, preprocess, extra_processings, override_n, frc1_method)
    processed_measures = _process_measures_conc(tasks) if concurrency else _process_measures(tasks)
    processed_curves = [curve for curves in processed_measures.values() for curve in curves]
    print(f"Finished processing, returning curves grouped by {grouping}.")
    if grouping == 'sets':
        return group_sets(processed_curves)
    elif grouping == 'measures':
        return group_measures(processed_curves)
    elif grouping == 'curves':
        return group_curves(processed_curves)
    else:
        return group_all(process_name, processed_curves)


def preprocess_measure(measure: FRCMeasurement) -> FRCMeasurement:
    """ Preprocess the image data in an FRCMeasurement. """
    measure.image = preprocess_img(measure.image)
    if measure.image_2 is not None:
        measure.image_2 = preprocess_img(measure.image_2)
    return measure


def preprocess_img(img: np.ndarray) -> np.ndarray:
    """ Crop an image to square dimensions and apply a Tukey window with parameter alpha = 0.125. """
    img = util.square_image(img, add_padding=False)
    return util.apply_tukey(img)


def measure_curve(measure: FRCMeasurement, override_n: int = 0, frc1_method: int = 1) -> FRCMeasurement:
    """ Compute curves for an FRCMeasurement. """
    img = measure.image
    # Can be None
    img2 = measure.image_2
    img_size = img.shape[0]
    len_per_pixel = measure.settings.len_per_pixel
    # For correct dimensions we use the first curve calculation below
    xs_pix = None
    xs_len_freq = None

    # Initialize default curve tasks
    if measure.curve_tasks is None:
        if measure.image_2 is None:
            if frc1_method == 2:
                method_str = '1FRC2'
            else:
                method_str = '1FRC'
            measure.curve_tasks = [CurveTask(key='curve1', method=method_str)]
        else:
            measure.curve_tasks = [CurveTask(key='curve1', method='2FRC', avg_n=1)]

    curves = []
    for curve_i, curve_task in enumerate(measure.curve_tasks):
        # Do not compute multiple curves for averaging
        if override_n >= 1:
            curve_task.avg_n = override_n

        # Decide method
        if curve_task.method == '1FRC' or curve_task.method == '1FRC1':
            def frc_func(img_frc, _img2):
                return frcf.one_frc(img_frc, 1)
        elif curve_task.method == '2FRC':
            def frc_func(img_frc_1, img_frc_2):
                return frcf.two_frc(img_frc_1, img_frc_2)
        elif curve_task.method == '1FRC2':
            # Experimental
            def frc_func(img_frc, _img2):
                return frcf.one_frc(img_frc, 2)
        else:
            raise ValueError("Unknown method {}".format(curve_task.method))

        frc_curve = frc_func(img, img2)

        # Only calculate the first time
        xs_pix = np.arange(len(frc_curve)) / img_size if xs_pix is None else xs_pix
        xs_len_freq = xs_pix * (1 / len_per_pixel) if xs_len_freq is None else xs_len_freq

        # Curve averaging
        frc_curves = [frc_curve]
        for i in range(curve_task.avg_n - 1):
            calculated_frc = frc_func(img, img2)
            frc_curve += calculated_frc
            frc_curves.append(calculated_frc)

        frc_curve /= curve_task.avg_n

        curve_key = f"{measure.name}"

        if len(measure.curve_tasks) > 1:
            curve_key += f"-curve {curve_i}"
        label = curve_key

        smooth_desc = ""
        if curve_task.smooth:
            smooth_desc = " LOESS smoothing (point frac: {}). ".format(curve_task.smooth_frac)
            xs_pix, frc_curve, wout = loess_1d(xs_pix, frc_curve, frac=curve_task.smooth_frac)

        frc_res = -1
        sd_str = ""

        res_sd = 0
        res_y = 0
        thres_curve = None

        # Try catch-block since it is possible no resolution could be computed
        try:
            frc_res, res_y, thres = frcf.frc_res(xs_len_freq, frc_curve, img_size, threshold=curve_task.threshold)
            thres_curve = thres(xs_pix)
            frc_res_list = []
            for res_curve in frc_curves:
                try:
                    frc_res, _, _ = frcf.frc_res(xs_len_freq, res_curve, img_size, threshold=curve_task.threshold)
                    frc_res_list.append(frc_res)
                except NoIntersectionException:
                    pass
            res_sd = np.std(np.array(frc_res_list))
            if res_sd > 0:
                sd_str = "± {:.2g} ".format(res_sd)

        except NoIntersectionException as e:
            print(e)

        avg_desc = f"{curve_task.avg_n} curves averaged." if curve_task.avg_n > 1 else ""
        desc = "Resolution ({} threshold) for {}: {:.3g} {}{}. {}{}".format(curve_task.threshold, curve_key, frc_res,
                                                                            sd_str, measure.settings.len_unit,
                                                                            smooth_desc, avg_desc)

        # Create curve object
        curve = Curve(curve_key, xs_len_freq, frc_curve, frc_res,
                      f"{curve_key}", label, desc,
                      res_sd, res_y, thres_curve, curve_task.threshold, measure)
        curves.append(curve)
    measure.curves = curves
    return measure
