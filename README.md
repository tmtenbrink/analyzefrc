# AnalyzeFRC
Plots, analysis and resolution measurement of microscopy images using Fourier Ring Correlation (FRC).

AnalyzeFRC has native support for .lif files and can also easily read single images in formats supported by Pillow (PIL). Other formats require converting that image into a NumPy array and using that to instantiate AnalyzeFRC's native objects.

### Usage

To simply compute the 1FRC of all channels of a .lif dataset and plot the results, you can do the following:

```python
import analyzefrc as afrc

# ./ means relative to the current folder
frc_sets = afrc.lif_read('/data/sted/2021_10_05_XSTED_NileRed_variation_excitation_power_MLampe.lif')
plot_curves = afrc.process_frc("XSTED_NileRed", frc_sets, preprocess=True, concurrency=True)
afrc.plot_all(plot_curves)
```

If instead you want to plot each image inside a .lif file in a single plot, do the following:

```python
... # imports and processing

plot_curves = afrc.process_frc("XSTED_NileRed", frc_sets, grouping='sets', preprocess=True, concurrency=True)
afrc.plot_all(plot_curves)
```
Or if you already computed the curves with the default grouping ('all'):

```python
... # imports and processing

frc_per_set_sets = afrc.group_sets(plot_curves)
plot_all(frc_per_set_sets)
```

If you don't want to plot the results (in the case of many images the IDE plot buffer can easily be exceeded), but instead save them:

```python
... # imports and processing
import analyzefrc as afrc

# Will save to './results/<timestamp>-XSTED_NileRed'
save_folder = afrc.create_save('./results', 'XSTED_NileRed', add_timestamp=True)
afrc.plot_all(plot_curves, show=False, save=True, save_directory=save_folder, dpi=180)

```

A slightly more complex example: If you have a sample .tiff file and you want to compare the performance of 1FRC vs 2FRC, you could do the following:

```python
import numpy as np
import diplib as dip
import frc.utility as frcu
import analyzefrc as afrc
from analyzefrc import FRCMeasurement, FRCSet

data_array: np.ndarray = afrc.get_image('./data/siemens.tiff')
# Blur the image (to create a frequency band)
data_array = frcu.gaussf(data_array, 30)
data_dip = dip.Image(data_array)
half_set_1 = np.array(dip.PoissonNoise(data_dip / 2))
half_set_2 = np.array(dip.PoissonNoise(data_dip / 2))
full_set = np.array(dip.PoissonNoise(data_dip))

# Create seperate measurement objects
frc_2: FRCMeasurement = afrc.frc_measure(half_set_1, half_set_2, set_name='2FRC')
frc_1: FRCMeasurement = afrc.frc_measure(full_set, set_name='1FRC')
# Combine in one set so they can be plot together
frc_set: FRCSet = afrc.frc_set(frc_1, frc_2, name='2FRC vs 1FRC')
plot_curve = afrc.process_frc("2FRC vs 1FRC", frc_set)
afrc.plot_all(plot_curve)
```

### Details

The three operations of setting up the measurements, computing the curves and plotting them are all decoupled and each have their Python module (`analyzefrc.read`, `analyzefrc.process`, `analyzefrc.plot`, respectively). Furthermore, actual file reading convenience functions can be found in `analyzefrc.file_read`.

#### FRCSet, FRCMeasurement and FRCMeasureSettings

For setting up the measurements in preparation of processing, these three classes are essential. `FRCSet`-objects can be completely unrelated, they share no information. As such, if doing batch processing of different datasets, they can be divided over `FRCSet`-objects.
Within an `FRCSet`, there can be an arbitrary number of `FRCMeasurements`, which should have similar image dimensions and should, in theory, be able to be sensibly plotted in a single figure.


