import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# =====================================
# user inputs
# =====================================
# data input
results_filename = "sweep_results.csv"

# figure output
savename = "Fig_Optimization_Results_MA.png"
DPI = 600  # Set resolution for saving figures

x_var = "capacity"
x_label = "Storage power rating (MW)"
x_convert = 1.0
x_limit = [0.0, 500.0]

y_vars = ["eta_storage", "revenue", "LCOE",]
y_labels = ["Storage Efficiency\n(%)", "Revenue\n($/kWh)", "LCOE\n($/kWh)"]
y_converts = [100.0, 1.0, 1.0]
y_limits = [[60.0, 90.0], [], []]

series_var = 'sheetname'
series = ['wind_only', '4_hr_batt', '10_hr_ocaes', '24_hr_ocaes']
series_dict = {'wind_only': 'Wind only', '4_hr_batt': 'Battery (4 hr)', '10_hr_batt': 'Battery (10 hr)',
               '10_hr_ocaes': 'OCAES (10 hr)', '24_hr_ocaes': 'OCAES (24 hr)',
               '48_hr_ocaes': 'OCAES (48 hr)', '72_hr_ocaes': 'OCAES (72 hr)', '168_hr_ocaes': 'OCAES (168 hr)'}

column_var = 'scenario'
columns = ['PJM', 'ISONE', 'NYISO']
column_dict = {'ISONE': 'ISO New England', 'NYISO': 'NY ISO', 'PJM': 'PJM'}

colors = sns.color_palette("colorblind")
colors = [(0, 0, 0), colors[0], colors[5],
          colors[2], colors[1], colors[3], colors[4], colors[6]]  # black, blue, brown, green, orange
linestyles = ['solid', 'solid', 'solid',
              'dashed', 'dotted', 'solid', 'solid', 'solid']
markers = ['o', 's', 'D', '^', '.', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'o', 'X']

# =====================================
# process data
# =====================================

# Import results
df = pd.read_csv(results_filename)

# =====================================
# create plots
# =====================================

# Column width guidelines https://www.elsevier.com/authors/author-schemas/artwork-and-media-instructions/artwork-sizing
# Single column: 90mm = 3.54 in
# 1.5 column: 140 mm = 5.51 in
# 2 column: 190 mm = 7.48 i
width = 7.48  # inches
height = 7.0  # inches

# Create plot
f, a = plt.subplots(len(y_vars), len(columns), sharex='col', sharey='row', squeeze=False)

# Set size
f.set_size_inches(width, height)

# Set style and context
sns.set_style("white", {"font.family": "serif", "font.serif": ["Times", "Palatino", "serif"]})
sns.set_context("paper")
sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})

# Set marker shapes and sizes
marker_size = 2
markeredgewidth = 1.0
linewidth = 2.5

count = 0

# iterate through y-variables
for j, (y_var, y_label, y_convert, y_limit) in enumerate(zip(y_vars, y_labels, y_converts, y_limits)):

    # iterate through columns
    for i, column in enumerate(columns):

        # access subplot
        ax = a[j, i]

        # iterate through series
        for k, (serie, color, marker, linestyle) in enumerate(zip(series, colors, markers, linestyles)):
            ind = (df.loc[:, column_var] == column) & (df.loc[:, series_var] == serie)
            x = x_convert * df.loc[ind, x_var]
            y = y_convert * df.loc[ind, y_var]

            # points
            ax.plot(x, y, color=color, linestyle='-', marker=marker, markersize=marker_size,
                    markeredgewidth=markeredgewidth, markeredgecolor=color, markerfacecolor='None',
                    label=series_dict[serie])

        # axes labels
        # x-axis labels (only bottom)
        if j == len(y_vars) - 1:
            ax.set_xlabel(x_label)
        else:
            ax.get_xaxis().set_visible(False)

        # y-axis labels (only left side)
        if i == 0:
            ax.set_ylabel(y_label)
        else:
            ax.get_yaxis().set_visible(False)

        # Despine and remove ticks
        sns.despine(ax=ax, )
        ax.tick_params(top=False, right=False)

        # Axes limits
        if len(y_limit) == 2:
            ax.set_ylim(bottom=y_limit[0], top=y_limit[1])

        # Caption labels
        caption_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
        plt.text(0.1, 1.05, caption_labels[count], horizontalalignment='center', verticalalignment='center',
                 transform=ax.transAxes, fontsize='medium', fontweight='bold')
        count = count + 1

        # column labels
        if j == 0:
            plt.text(0.5, 1.1, column_dict[column], horizontalalignment='center', verticalalignment='center',
                     transform=ax.transAxes, fontsize='medium', fontweight='bold')

# Legend
leg = a[2, 1].legend(bbox_to_anchor=(0.5, -0.35), ncol=4, loc='upper center')

# Adjust layout
# plt.tight_layout()
plt.subplots_adjust(hspace=0.2, wspace=0.2, bottom=0.2)
f.align_ylabels(a[:, 0])  # align y labels

# Save Figure
plt.savefig(savename, dpi=DPI, bbox_extra_artists=leg)
# plt.close()
