from PIL import Image as PILImage
from readlif.reader import LifFile, LifImage
import analyzefrc.lif_util as lu
import numpy as np
import analyzefrc.frc_util as frcu
import pathlib as path
import time
from deco import concurrent, synchronized
import pickle


# img_1 = imgs[0]
#
# pixels_per_um = img_1.scale[0]
# um_per_pixel = 1 / pixels_per_um
#
# channel_list = [i for i in img_1.get_iter_c(t=0, z=0)]
# c1 = channel_list[1]
# c_arr = np.array(c1)
# lu.show(c_arr)
# frcu.compute_plot_frc(c_arr, um_per_pixel, method='1FRC2')


class Image:
    name: str
    channels: list[PILImage]
    scale: float
    settings: dict

    def __init__(self, img: LifImage):
        self.name = img.name
        self.channels = [i for i in img.get_iter_c(t=0, z=0)]
        # size = channels[0].shape[0]
        # self.channels = [cv2.resize(i, (2048, 2048)) for i in channels]
        self.scale = img.scale[0]
        self.settings = img.settings


@concurrent
def do_channel(i, c, name, result_path, method, c_l, scale, smooth, NA, max_val=None, diffr_res=None, group_title=''):
    c_arr = np.array(c)
    c_max = np.amax(c_arr)
    if not max_val:
        max_val = c_max
    elif 0 < max_val <= 1:
        max_val *= c_max
    c_arr = c_arr * (max_val / c_max)
    title = "{}_{}: {}/{}".format(group_title, name, i + 1, c_l)
    print(title)
    save_title = title.replace('/', 'o').replace(': ', '-')
    save_file_curve = save_title + "-crve.png"
    save_file_img = save_title + ".png"
    curve_save = result_path.joinpath(save_file_curve)
    img_save = result_path.joinpath(save_file_img)

    lu.show(c_arr, title=title, save=True, save_path=img_save)
    pixels_per_um = scale
    um_per_pixel = 1 / pixels_per_um
    # mxs = np.arange(0.2, 1.4, step=0.2)
    # mxs = np.array([3500])
    return save_title, frcu.compute_plot_frc(c_arr, um_per_pixel, max_val, c_max, NA, methods=method, mxs=None,
                                             smooth=smooth, title=title, save=True, save_path=curve_save,
                                             extra_res_plot=diffr_res)


@synchronized
def do_imgs(imgs: list[Image], result_path: path.Path, method: str, smooth=False, group_title=''):
    resolutions = {}

    for k, img in enumerate(imgs):
        name = img.name
        channel_list = img.channels
        c_l = len(channel_list)
        scale = img.scale
        NA = 0
        for i, c in enumerate(channel_list):
            # do_channel(i, c, name, result_path, method, c_l, scale, max_val=mx)
            diffr_res = None
            if i == 0:
                NA = img.settings["NumericalAperture"]
                lam = img.settings["StedDelayWavelength"]
                diffr_res = 0.5 * float(lam) / float(NA)
            resolutions["{}_{}".format(k, i)] = do_channel(i, c, name, result_path, method, c_l, scale, smooth, NA,
                                                           diffr_res=diffr_res, group_title=group_title)

    return resolutions


if __name__ == '__main__':
    frc_method = '1FRC1'

    sted = LifFile('../data/sted/2021_10_05_XSTED_NileRed_variation_excitation_power_MLampe.lif')

    imgs_do = [Image(i) for i in sted.get_iter_image()]
    # imgs_do = [Image(sted.get_image(0))]
    #
    # imgs_do[0].channels = [imgs_do[0].channels[0]]

    timestamp = int(time.time())
    path_results = path.Path('../results/{}-{}'.format(timestamp, frc_method))
    path_results.mkdir()

    res = do_imgs(imgs_do, path_results, frc_method, smooth=False, group_title="(2021_10_5_XSTED_NileRed)")
    print(res)
    pickle_file = path_results.joinpath("./res.pickle")
    with open(pickle_file, 'wb') as handle:
        pickle.dump(res, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # res = {value[0]: value[1] for value in res.values()}
    # print(res)
    # img_0 = sted.get_image(0)
    print()

