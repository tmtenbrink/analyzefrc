# AnalyzeFRC

[![PyPI version](https://badge.fury.io/py/analyzefrc.svg)](https://badge.fury.io/py/analyzefrc)

*Developed at the Department of Imaging Physics (ImPhys), Faculty of Applied Sciences, TU Delft.*

Plots, analysis and resolution measurement of microscopy images using Fourier Ring Correlation (FRC).

AnalyzeFRC has native support for .lif files and can also easily read single images in formats supported by Pillow (PIL). Other formats require converting that image into a NumPy array and using that to instantiate AnalyzeFRC's native objects.

AnalyzeFRC provides a lot of default options and convenience functions for a specific use case. However, its core functionality, the `measure_frc` function in `analyzefrc.process` can be adapted in other workflows. You can also directly use the [frc library](https://github.com/tmtenbrink/frc), on which this library is built.

### Defaults (please read)

- By default, when using `frc_process`, `preprocess` is set to True. It ensures that each input image is cropped into square form and that a Tukey window is applied. Supply `proprocess=False` to disable this behavior.
- By default, when using `frc_process`, `concurrency` is set to True. This leverages the `deco` package to leverage more cores for a 1.5x+ speedup (not higher because the most resource-intensive computations are already parallelized). !! However, please run the program inside a `if __name__ == '__main__':` block when concurrency is enabled! Otherwise it will fail! You can also disable concurrency instead by passing `concurrency=False` to `process_frc`.
- By default, if an `FRCMeasurement` is processed without any preset `CurveTask` and has two images, it sets the method to `2FRC`. Otherwise, `1FRC` is used.
- By default, plots are grouped by `measures`, i.e. every measurement will be plotted separately. Use the `group_<grouping>`. Other available groupings include `all` (all curves in one plot, use this only to retrieve them to use custom groupings), `sets` (all curves in the same set name in one plot) and `curves` (one plot per curve).
- By default, 1FRC curves are computed 5 times and averaged, this can be overriden by passing `override_n` to process_frc.

### Installation

#### With (Ana)conda

If you already have Anaconda installed (or miniconda), it is easiest to create a new Python 3.9 environment (here 'envanalyze' can be any environment name you like). Open the Anaconda/miniconda3 prompt and write:

```shell
conda create -n 'envanalyze' python=3.9
```

This package depends on a number of PyPI-only packages, some also with compiled extensions, which are difficult to port to conda. For this reason, it is recommended to have a seperate environment with only this package and then install using pip:

```shell
conda activate envanalyze
pip install analyzefrc
```

You now have an environment called 'envanalyze' with analyzefrc installed. Configure your favorite IDE to use the newly created environment and you're good to go!  See the usage examples for more details on how to use this package.


#### Without conda

Currently, this library only works on Python 3.9. Ensure you have a working installation. You can use tools like [pyenv](https://github.com/pyenv/pyenv) for managing Python versions. 

It is recommended to install this library into a [virtual environment](https://realpython.com/python-virtual-environments-a-primer/). Many tools exist for this today (most IDEs can do it for you), but I recommend [Poetry](https://github.com/python-poetry/poetry).

Install using:

```shell
pip install analyzefrc
```

If using Poetry:

```shell
poetry add analyzefrc
```

This library indirectly (through the `frc` library) depends on [rustfrc](https://github.com/tmtenbrink/rustfrc) (Rust extension) and [diplib](https://github.com/diplib) (C++ extension). These compiled extensions can sometimes cause issues, so refer to their pages as well.


### Usage

To simply compute the 1FRC of all channels of a .lif dataset and plot the results, you can do the following:

```python
import analyzefrc as afrc

# This if-statement is required because concurrency is enabled
if __name__ == '__main__':
    # ./ means relative to the current folder
    frc_sets = afrc.lif_read('./data/sted/2021_10_05_XSTED_NileRed_variation_excitation_power_MLampe.lif')
    plot_curves = afrc.process_frc("XSTED_NileRed", frc_sets, preprocess=True, concurrency=True)
    afrc.plot_all(plot_curves)
```

If instead you want to plot each image inside a .lif file in a single plot, do the following:

```python
... # imports and processing

plot_curves = afrc.process_frc("XSTED_NileRed", frc_sets, grouping='sets', preprocess=True, concurrency=False)
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
plot_curve = afrc.process_frc("2FRC vs 1FRC", frc_set, concurrency=False)
afrc.plot_all(plot_curve)
```

### Details

The three operations of setting up the measurements, computing the curves and plotting them are all decoupled and each have their Python module (`analyzefrc.read`, `analyzefrc.process`, `analyzefrc.plot`, respectively). Furthermore, actual file reading convenience functions can be found in `analyzefrc.file_read`.

#### FRCSet, FRCMeasurement and FRCMeasureSettings

For setting up the measurements in preparation of processing, these three classes are essential. `FRCSet`-objects can be completely unrelated, they share no information. As such, if doing batch processing of different datasets, they can be divided over `FRCSet`-objects.
Within an `FRCSet`, there can be an arbitrary number of `FRCMeasurement`-objects, which should have similar image dimensions and should, in theory, be able to be sensibly plotted in a single figure.

`FRCMeasurement` is the main data container class. It can be instantiated using an `FRCMeasureSettings`-object, which contains important parameters that are the same across all images within the measurement (such as the objective's NA value). If these differ across the images, multiple measurements should be used.

#### Changing default curves

By default, when processing, a single `CurveTask` will be generated for each `FRCMeasurement`, meaning a single curve will be generated for each measurement. However, if a different threshold (other than the 1/7) is desired, or multiple curves per figure are wanted, a `CurveTask` can be created beforehand and given to the `FRCMeasurement`.

Example:

```python
... # see .tiff example
from analyzefrc import CurveTask

# Create seperate measurement objects
# For example we want a smoothed curve for the 1FRC, as well as a non-smoothed curve
frc1_task_smooth = CurveTask(key='smooth_curve', smooth=True, avg_n=3, threshold='half_bit')
frc1_task = CurveTask(key='standard_curve', avg_n=3, threshold='half_bit')

frc_2: FRCMeasurement = afrc.frc_measure(half_set_1, half_set_2, set_name='2FRC')
frc_1: FRCMeasurement = afrc.frc_measure(full_set, set_name='1FRC', curve_tasks=[frc1_task, frc1_task_smooth])

... # process and plot
```

#### Changing default processing

If other measurement-based processings are desired, they can be added in two ways. Arbitrary functions (of the type `MeasureProcessing = Callable[[FRCMeasurement], FRCMeasurement]`) can be run for each measurement by passing them as a list to the `extra_processings`-argument for `process_frc`, or by populating the `FRCMeasurement`-objects' `extra_processings` attribute.

Note: each processing is performed in list order after the optional `preprocessing` step, with global extras performed before the measurement-defined extra processing tasks.

This can be useful when using a convenience file loading function. For example, to flip every image and apply a different window functon:

```python
... # .lif example
from analyzefrc import FRCMeasurement
import numpy as np
from scipy.signal import windows as wins

def flip_window_data(measure: FRCMeasurement) -> FRCMeasurement:
    measure.image = np.flip(measure.image)
    size = measure.image.shape[0]
    assert size == measure.image.shape[1]
    
    cosine = wins.tukey(size)
    cosine_square = np.ones((size, size)) * cosine.reshape((size, 1)) * cosine.reshape((1, size))
    measure.image = cosine_square * measure.image
    
    return measure

plot_curves = afrc.process_frc("XSTED_NileRed", frc_sets, preprocess=False, extra_processings=[flip_window_data], concurrency=False)

... # plot
```

#### Other internal details

The general processing flow is as follows:

1. (`read`/`read_file`) Create `FRCMeasureSettings` based on data acquisition parameters
2. (`read`/`read_file`) Create `FRCMeasurement` using the previous step.
3. (Optionally) create custom `CurveTask`-objects for the `FRCMeasurement`. Created by default in the `process` step if not provided.
4. (`read`/`read_file`) Create `FRCSet` using multiple `FRCMeasurement`-objects.
5. (`process`) Compute `Curve`-objects using `measure_frc`.
6. (`process`) Sort/group the `Curve`-objects into a dictionary with lists of `Curve`-objects as entries.
7. (`plot`) Plot the `list[Curve]`-dictionary, where each entry becomes a single figure.

All steps besides the `measure_frc`-step can be implemented in a custom way quite trivially. In a way, all steps except step 5 are for your convenience. Step 5, which is the only step that involves actually processing all the data using the `frc` library, forms the core of this package.

### Performance

Processing 32 measurements of 1024x1024 pixels takes about thirty seconds to read from a .lif file, process (computing each curve 5 times) and plot on my i7-8750H laptop CPU (which is decently performant even by today's standards). 

Over 80% of the time is spent processing, i.e. performing the binomial splitting and computing the FRCs (with the latter taking significantly longer). All these functions are implemented through Rust (rustfrc), C++ (diplib) or C (numpy) extensions, meaning they are as fast as can be.

10-15% of the time is spent plotting using matplotlib, meaning the overhead of this library is only 5-10%. 
