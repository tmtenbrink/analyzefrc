import numpy as np
import diplib as dip
import frc.utility as frcu
import analyzefrc as afrc
from analyzefrc import FRCMeasurement, FRCSet

data_array: np.ndarray = afrc.get_image('./data/siemens.tiff')
# Blur the image (to create a frequency band)
data_array = frcu.gaussf(data_array, 7)
data_dip = dip.Image(data_array)
half_set_1 = np.array(dip.PoissonNoise(data_dip / 2))
half_set_2 = np.array(dip.PoissonNoise(data_dip / 2))
full_set = np.array(dip.PoissonNoise(data_dip))

if __name__ == '__main__':
    for i in range(3):
        frc_2: FRCMeasurement = afrc.frc_measure(half_set_1, half_set_2, set_name='2FRC vs 1FRC')
        frc_1: FRCMeasurement = afrc.frc_measure(full_set, set_name='2FRC vs 1FRC')
        frc_set: FRCSet = afrc.frc_set(frc_1, frc_2, name='2FRC vs 1FRC')
        plot_curve = afrc.process_frc("2FRC vs 1FRC", frc_set, concurrency=True, grouping='sets')
# afrc.plot_all(plot_curve)