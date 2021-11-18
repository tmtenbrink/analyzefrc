import pathlib as path
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

dir_path = path.Path("../results_sav/{}".format('1636714207-1FRC1 mike3'))
sheet = pd.read_excel('../data/sted/2021_10_05_XSTED_NileRed_variation_excitation_power_laser_settings.xlsx')
pth = dir_path.joinpath("./res.pickle")

with open(pth, 'rb') as handle:
    d = pickle.load(handle)

sheet = sheet.loc[~sheet['Series'].isna()]
sheet = sheet.astype({"Series": int, "Ch": int})
sheet = sheet.astype({"Series": str, "Ch": str})
series_df = sheet.set_index(['Series', 'Ch'])

v = {v[0]: v[1] for k, v in d.items()}
res = []
res_uncertain = []
for key, value in v.items():
    spl = key.split(')')[-1].split('-')
    sers = str(int("".join([n for n in spl[0] if n.isdigit()])))
    c = str(int(spl[1].split('o')[0]))
    res.append([sers, c, value[0], value[1], value[2]])
    res_uncertain.append([sers, c, value[1]])
res_df = pd.DataFrame(res, columns=['Series', 'Ch', 'res_nm', 'res_uncertain', 'NA']).set_index(['Series', 'Ch'])
# res_uncertain_df = pd.DataFrame(res_uncertain, columns=['Series', 'Ch', 'res_uncertain']).set_index(['Series', 'Ch'])

# series_list = {series_n: sheet.loc[series_col == series_n].set_index('Ch').drop('Series', 1)
#                for series_n in [3., 6., 12.]}


# for series_n, df in series_list.items():
series_df = series_df.join(res_df, on=['Series', 'Ch'])
# series_df = series_df.join(res_uncertain_df, on=['Series', 'Ch'])
series_df['res_relative'] = pd.Series([0] * len(series_df['res_nm']))
series_df['res_relative_uncertain'] = pd.Series([0] * len(series_df['res_nm']))
for srs_n in ['3', '6', '12']:
    srs = series_df.loc[srs_n, :]
    res_base = srs.loc['1', 'res_nm']
    series_df.loc[(srs_n, slice(None)), 'res_relative'] = series_df.loc[(srs_n, slice(None)), 'res_nm'] / res_base
    series_df.loc[(srs_n, slice(None)), 'res_relative_uncertain'] = series_df.loc[(srs_n, slice(
        None)), 'res_uncertain'] / res_base
ii = series_df.index.get_level_values('Series').to_numpy()
series_arr = series_df.to_numpy().astype(float)
series_colors = [np.empty(ii.shape, dtype=tuple)]
c_map = plt.cm.get_cmap(lut=3)
color_series = []
for i, srs_n in enumerate(['3', '6', '12']):
    srs_loc = ii == srs_n
    c_map_i = c_map(i)
    color_series.append((srs_loc, c_map_i))

std_data = series_arr[:, 1]
exc_data = series_arr[:, 0]
res_data = series_arr[:, 2]
NA_data = series_arr[:, 4]
res_data_relat = series_arr[:, 5]
res_err_data_relat = series_arr[:, 6]
res_err_data = series_arr[:, 3]
print()
fig, ax = plt.subplots()


def sted_func(NA, x, b):
    return 561 / (2 * NA * np.sqrt(1 + x / b))


for srs_loc, color in color_series:
    x_data = std_data[srs_loc] * 100
    y_data = res_data[srs_loc]
    y_err = res_err_data[srs_loc]
    NA = NA_data[srs_loc][0]
    series = ii[srs_loc][0]
    # init_a = y_data[0] * 2 * NA
    popt, pcov = curve_fit(lambda x, a: sted_func(NA, x, a), x_data, y_data, bounds=([1], [50]), p0=[25], sigma=y_err)
    ax.errorbar(x_data, y_data, yerr=y_err, c=color, ls='', marker='.',
                capsize=2, ms=4, label=f"Series{series} (NA={NA})")
    xs = np.linspace(0, 100)
    ax.plot(xs, sted_func(NA, xs, popt[0]), c=color, ls='dashed')

ax.legend()
ax.set_xlabel("STED intensity (%)")
ax.set_ylabel("Resolution 1/7 threshold (nm)")
ax.set_title("2021/10/5 XSTED NileRed STED equation")
desc = "STED 775nm. 561nm excitation."
fig.supxlabel(desc, fontsize='small')
fig.set_tight_layout(True)
fig.savefig(dir_path.joinpath("./stedcurves.png"), dpi=180)
series_df.to_excel(dir_path.joinpath("./resolutions.xlsx"))
plt.show()

# for srs_loc, color in color_series:
#     ax.errorbar(std_data[srs_loc], res_data_relat[srs_loc], yerr=res_err_data_relat[srs_loc], c=color, ls='', marker='.', capsize=2, ms=4)
# plt.show()
