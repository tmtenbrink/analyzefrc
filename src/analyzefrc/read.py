from os import PathLike
from pathlib import Path
from PIL import Image
from readlif.reader import LifFile
from analyzefrc.deps_types import np
from analyzefrc.deps_types import Union, Optional
from analyzefrc.process import FRCMeasurement, FRCSet, FRCMeasureSettings


__all__ = ['get_lif_file', 'get_image', 'lif_read', 'image_read', 'frc1_image', 'frc2_image']


def return_path(pth: str):
    return Path(pth).absolute()


def get_lif_file(pth: str) -> LifFile:
    return LifFile(return_path(pth))


def get_image(pth: Union[str, PathLike]) -> np.array:
    """ Uses PIL to load an image as an array in grayscale ('L' mode)."""
    with Image.open(return_path(pth)) as im:
        im = im.convert(mode="L")
        return np.array(im)


def lif_read(pth: str, debug: str = '') -> list[FRCSet]:
    """
    Read a LIF file. Assumes the scale is in pixels per um and is equal in all directions.
    If debug is True, it will only get the first image and channel.
    """
    images = []
    lif_file = get_lif_file(pth)
    imgs = lif_file.get_iter_image()
    if debug == 'single':
        imgs = [next(imgs)]
    elif debug == 'two_set':
        imgs_itered = [img for img in imgs]
        imgs = [imgs_itered[0], imgs_itered[-1]]
    for img in imgs:
        pixels_per_um = img.scale[0]
        name = img.name
        um_per_pixel = 1 / pixels_per_um
        nm_per_pixel = um_per_pixel * 1000
        NA = img.settings["NumericalAperture"] if "NumericalAperture" in img.settings else None
        lam = img.settings["StedDelayWavelength"] if "StedDelayWavelength" in img.settings else None
        measurements = []
        channels = img.get_iter_c(t=0, z=0)
        if debug == 'single':
            channels = [next(channels)]
        elif debug == 'two_set':
            channels_itered = [channel for channel in channels]
            channels = [channels_itered[0], channels_itered[-1]]
        for i, c in enumerate(channels):
            dip_im = np.array(c)
            settings = FRCMeasureSettings(NA=NA, lambda_excite_nm=lam, nm_per_pixel=nm_per_pixel)
            measurement = FRCMeasurement(image=dip_im, group_name=name, index=i, settings=settings)
            measurements.append(measurement)
        frc_image = FRCSet(name, measurements)
        images.append(frc_image)
    return images


def image_read(pth: str, pth2: Optional[str] = None):
    img1 = get_image(pth)
    if pth2 is not None:
        img2 = get_image(pth2)
        return frc2_image(img1, img2)
    else:
        return frc1_image(img1)


def frc1_image(img: np.ndarray, name='1FRCimage'):
    settings = FRCMeasureSettings(1)
    measurement = FRCMeasurement(name, 0, settings, img)
    return FRCSet(name, [measurement])


def frc2_image(img1: np.ndarray, img2: np.ndarray, name='2FRCimage'):
    settings = FRCMeasureSettings(1)
    measurement = FRCMeasurement(name, 0, settings, img1, image_2=img2)
    return FRCSet(name, [measurement])
