from analysis.deps_types import dip
from frc.deps_types import Img
import frc.frc_functions as frcf
import frc.utility as util
import numpy as np
import datatest
from readlif.reader import LifFile
import matplotlib.pyplot as plt

class FRCMeasurement:
    """
    An FRCMeasurement represents a single measurement within an FRCImage and contains the actual data as
    a DIP Image (which itself can be converted to a numpy array at no cost).
    """
    image: dip.Image
    measure_settings: dict


class FRCImage:
    """
    The FRCImage represents a single measurement group, where each measurement in the group has the same
    image dimensions, is square and is windowed to prevent FFT artifacts. I.e. they are fully preprocessed.
    Measurements should also have occurred under similar conditions, i.e. same camera, lens, with only
    some properties variable per image.
    """
    name: str
    nm_per_pixel: float
    measurements: list[FRCMeasurement]
    image_settings: dict


def single_curve(img: Img, scale):
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

sted = LifFile('../data/sted/2021_10_05_XSTED_NileRed_variation_excitation_power_MLampe.lif')
imgs = [i for i in sted.get_iter_image()]

img_1 = imgs[0]

pixels_per_um = img_1.scale[0]
um_per_pixel = 1 / pixels_per_um
nm_pix_fact = 1 / um_per_pixel / 1000

channel_list = [i for i in img_1.get_iter_c(t=0, z=0)]
img = np.array(channel_list[0])
single_curve(img, nm_pix_fact)

