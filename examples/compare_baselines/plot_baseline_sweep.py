import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------
# script inputs
# ---------------
results_filename = 'sweep_capacity.csv'
plot_filename = 'baseline_sweep.png'
DPI = 300

# ---------------
# create plot
# ---------------
df = pd.read_csv(results_filename)

# Column width guidelines
# https://www.elsevier.com/authors/author-schemas/artwork-and-media-instructions/artwork-sizing
# Single column: 90mm = 3.54 in
# 1.5 column: 140 mm = 5.51 in
# 2 column: 190 mm = 7.48 i
width = 7.48  # inches
height = 5.5  # inches

# create subplots
f, a = plt.subplots(3, 1, sharex='all')
axes = a.ravel()

# style
sns.set_style("white", {"font.family": "serif", "font.serif": ["Times", "Palatino", "serif"]})
sns.set_context("paper")
sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
colors = sns.color_palette("colorblind")

# x variable
x_var = 'capacity'
x_convert = 1.0
x_label = 'Capacity [MW]'

# y variables
y_vars = ['LCOE', 'revenue', 'emissions_avoided']
y_converts = [1.0, 1.0, 1.0]
y_labels = ['LCOE\n[$/kWh]', 'Revenue\n[$/kWh]', 'Avoided Emissions\n[ton CO2/kWh]']

# series
series_field = 'storage_type'
series_names = ['wind_only', 'battery', 'OCAES-10', 'OCAES-24']
series_labels = ['Wind only', 'Li-ion battery', 'OCAES 10hr', 'OCAES 24hr']
series_colors = [colors[0], colors[1], colors[2], colors[2]]
series_markers = ['x', 'o', 's', '<']

# by plot
for i, (ax, y_var, y_convert, y_label) in enumerate(zip(axes, y_vars, y_converts, y_labels)):

    # by series
    for series_name, series_label, series_color, series_marker in zip(series_names, series_labels, series_colors, series_markers):
        # select data from df
        x_data = df.loc[df.loc[:, series_field] == series_name, x_var]
        y_data = df.loc[df.loc[:, series_field] == series_name, y_var]

        # convert values and store as list
        x = x_data.values * x_convert
        y = y_data.values * y_convert

        # plot
        ax.plot(x, y, marker=series_marker, color=series_color, label=series_label)

    # despine and remove ticks
    sns.despine(ax=ax, )
    ax.tick_params(top=False, right=False)

    # y-axis label
    ax.set_ylabel(y_label)

    # last subplot
    if i == len(y_vars) - 1:
        # x-axis label
        ax.set_xlabel(x_label)

        # legend
        ax.legend()

# set size
f = plt.gcf()
f.set_size_inches(width, height)

# save and close plot
plt.savefig(plot_filename, dpi=DPI)
plt.close()
