from analyzefrc.process import FRCImage, plot_curves
from readlif.reader import LifFile
import numpy as np
from analyzefrc.read import lif_read


if __name__ == '__main__':
    x = lif_read('./data/sted/2021_10_05_XSTED_NileRed_variation_excitation_power_MLampe.lif', debug=True)
    plot_curves(x, concurrent=False)


print()

# sted = LifFile('./data/sted/2021_10_05_XSTED_NileRed_variation_excitation_power_MLampe.lif')
# imgs = [i for i in sted.get_iter_image()]

# img_1 = imgs[0]

# pixels_per_um = img_1.scale[0]
# um_per_pixel = 1 / pixels_per_um
# nm_pix_fact = 1 / um_per_pixel / 1000

# channel_list = [i for i in img_1.get_iter_c(t=0, z=0)]
# img = np.array(channel_list[0])
# single_curve(img, nm_pix_fact)