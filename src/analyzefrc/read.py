from pathlib import Path
from readlif.reader import LifFile
from analyzefrc.deps_types import np
from analyzefrc.deps_types import Union
from analyzefrc.process import FRCMeasurement, FRCImage, FRCMeasureSettings


def return_path(pth: str):
    return Path(pth).absolute()


def get_lif_file(pth: str):
    return LifFile(return_path(pth))


def lif_read(pth: str, debug=False) -> list[FRCImage]:
    """
    Read a LIF file. Assumes the scale is in pixels per um and is equal in all directions.
    If debug is True, it will only get the first image and channel.
    """
    images = []
    lif_file = get_lif_file(pth)
    imgs = lif_file.get_iter_image()
    if debug:
        imgs = [next(imgs)]
    for img in imgs:
        pixels_per_um = img.scale[0]
        name = img.name
        um_per_pixel = 1 / pixels_per_um
        nm_per_pixel = um_per_pixel * 1000
        NA = img.settings["NumericalAperture"] if "NumericalAperture" in img.settings else None
        lam = img.settings["StedDelayWavelength"] if "StedDelayWavelength" in img.settings else None
        measurements = []
        channels = img.get_iter_c(t=0, z=0)
        if debug:
            channels = [next(channels)]
        for i, c in enumerate(channels):
            dip_im = np.array(c)
            settings = FRCMeasureSettings(NA=NA, lambda_excite_nm=lam, nm_per_pixel=nm_per_pixel)
            measurement = FRCMeasurement(image=dip_im, group_name=name, index=i, settings=settings)
            measurements.append(measurement)
        frc_image = FRCImage(name, measurements)
        images.append(frc_image)
    return images


def frc_image(img: np.ndarray, name='image'):
    settings = FRCMeasureSettings(1)
    measurement = FRCMeasurement(img, name, 0, settings)
    return FRCImage(name, [measurement])
