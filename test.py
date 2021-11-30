import numpy as np
import diplib as dip

from analyzefrc.process import plot_curves, create_tasks
from analyzefrc.read import lif_read, frc2_image, image_read, get_image, frc1_image
from frc import utility as frcu

if __name__ == '__main__':
    # x = get_image('./data/siemens.tiff')
    # x = frcu.gaussf(x, 10)
    # x_dip = dip.Image(x)
    # x_dip.Show()
    # y1 = np.array(dip.PoissonNoise(x_dip/2))
    # y2 = np.array(dip.PoissonNoise(x_dip/2))
    # y3 = np.array(dip.PoissonNoise(x_dip))
    #
    # z = frc2_image(y1, y2)
    # z_one = frc1_image(y3)
    # plot_curves(z, concurrency=False)
    # plot_curves(z_one, concurrency=False)

    x = lif_read('./data/sted/2021_10_05_XSTED_NileRed_variation_excitation_power_MLampe.lif', debug=True)
    z = create_tasks(x, concurrency=True)
    print(z)
    print()

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
