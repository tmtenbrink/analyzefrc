# import numpy as np
# import diplib as dip
# import frc.utility as frcu
# import analyzefrc as afrc
# from analyzefrc import FRCMeasurement, FRCSet
#
# data_array: np.ndarray = afrc.get_image('./data/siemens.tiff')
# # Blur the image (to create a frequency band)
# data_array = frcu.gaussf(data_array, 30)
# data_dip = dip.Image(data_array)
# half_set_1 = np.array(dip.PoissonNoise(data_dip / 2))
# half_set_2 = np.array(dip.PoissonNoise(data_dip / 2))
# full_set = np.array(dip.PoissonNoise(data_dip))
#
# frc_2: FRCMeasurement = afrc.frc_measure(half_set_1, half_set_2, set_name='2FRC vs 1FRC')
# frc_1: FRCMeasurement = afrc.frc_measure(full_set, set_name='2FRC vs 1FRC')
# frc_set: FRCSet = afrc.frc_set(frc_1, frc_2, name='2FRC vs 1FRC')
# plot_curve = afrc.process_frc("2FRC vs 1FRC", frc_set, concurrency=False)
# afrc.plot_all(plot_curve)

import analyzefrc as afrc
from analyzefrc import FRCMeasurement
import numpy as np
from scipy.signal import windows as wins

# ./ means relative to the current folder
frc_sets = afrc.lif_read('./data/sted/2021_10_05_XSTED_NileRed_variation_excitation_power_MLampe.lif')


# def flip_window_data(measure: FRCMeasurement) -> FRCMeasurement:
#     measure.image = np.flip(measure.image)
#     size = measure.image.shape[0]
#     assert size == measure.image.shape[1]
#
#     cosine = wins.tukey(size)
#     cosine_square = np.ones((size, size)) * cosine.reshape((size, 1)) * cosine.reshape((1, size))
#     measure.image = cosine_square * measure.image
#
#     return measure


plot_curves = afrc.process_frc("XSTED_NileRed", frc_sets, preprocess=True,
                               concurrency=True)
save_folder = afrc.create_save('./results', 'XSTED_NileRed', add_timestamp=True)
afrc.plot_all(plot_curves, show=False, save=True, save_directory=save_folder, dpi=180)
