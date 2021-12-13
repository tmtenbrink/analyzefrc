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
