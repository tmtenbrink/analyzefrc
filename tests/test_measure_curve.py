import numpy as np
import analyzefrc as afrc
import analyzefrc.process
from analyzefrc import FRCMeasurement


def test_measure_curve():
    data_array: np.ndarray = afrc.get_image('./siemens.tiff')

    frc_1: FRCMeasurement = afrc.frc_measure(data_array, set_name='1FRC')
    measure_with_curves = analyzefrc.process.measure_curve(frc_1)
    assert measure_with_curves.curves is not None
