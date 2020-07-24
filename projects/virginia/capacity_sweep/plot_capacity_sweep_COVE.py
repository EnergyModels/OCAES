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
savename = "Fig_Optimization_Results_COVE.png"
DPI = 400  # Set resolution for saving figures

x_vars = ["capacity"]
x_labels = ["Storage power rating (MW)"]
x_converts = [1.0, 1.0]
x_limits = [[], []]

y_vars_all = ["COVE"]
y_labels_all = ["COVE\n($/kWh)"]
y_converts_all = [1.0]
y_limits_all = [[0.08, 0.18]]

series_var = 'scenario'
series = ['wind_only', '4_hr_batt', '10_hr_batt', '10_hr_ocaes', '24_hr_ocaes']
series_dict = {'wind_only': 'Wind only', '4_hr_batt': 'Battery (4 hr)', '10_hr_batt': 'Battery (10 hr)',
               '10_hr_ocaes': 'OCAES (10 hr)', '24_hr_ocaes': 'OCAES (24 hr)'}

# Set Color Palette
# colors = sns.color_palette("Paired")
# colors = [(0, 0, 0), colors[0], colors[1], colors[2], colors[3]]

colors = sns.color_palette("colorblind")
colors = [(0, 0, 0), colors[0], colors[5], colors[2], colors[1]]  # black, blue, brown, green, orange
linestyles = ['solid', 'solid', 'solid', 'dashed', 'dotted']
markers = ['o', 's', 'D', '^', '.', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'o', 'X']

# =====================================
# process data
# =====================================

# Import results
df = pd.read_csv(results_filename)

for timeseries_filename in df.timeseries_filename.unique():
    n = len(y_vars_all)
    if timeseries_filename == "timeseries_inputs_2015.csv":
        savename = "Fig_Optimization_Results_2015_COVE.png"
    elif timeseries_filename == "timeseries_inputs_2017.csv":
        savename = "Fig_Optimization_Results_2017_COVE.png"
    elif timeseries_filename == "timeseries_inputs_2019.csv":
        savename = "Fig_Optimization_Results_2019_COVE.png"
    elif timeseries_filename == "timeseries_inputs_multiyear.csv":
        savename = "Fig_Optimization_Results_multiyear_COVE.png"
    print(savename)

    y_vars = y_vars_all[0:n]
    y_labels = y_labels_all[0:n]
    y_converts = y_converts_all[0:n]
    y_limits = y_limits_all[0:n]

    # =====================================
    # create plots
    # =====================================

    # Column width guidelines https://www.elsevier.com/authors/author-schemas/artwork-and-media-instructions/artwork-sizing
    # Single column: 90mm = 3.54 in
    # 1.5 column: 140 mm = 5.51 in
    # 2 column: 190 mm = 7.48 i
    width = 5.51  # inches
    height = 4.5  # inches

    # Create plot
    f, a = plt.subplots(len(y_vars), len(x_vars), sharex='col', sharey='row', squeeze=False)

    # Set size
    f.set_size_inches(width, height)

    # Set style and context
    sns.set_style("white", {"font.family": "serif", "font.serif": ["Times", "Palatino", "serif"]})
    sns.set_context("paper")
    sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})

    # Set marker shapes and sizes
    marker_size = 4
    markeredgewidth = 1.0
    linewidth = 2.5

    count = 0
    # iterate through x-variables
    for i, (x_var, x_label, x_convert, x_limit) in enumerate(zip(x_vars, x_labels, x_converts, x_limits)):

        # iterate through y-variables
        for j, (y_var, y_label, y_convert, y_limit) in enumerate(zip(y_vars, y_labels, y_converts, y_limits)):

            # access subplot
            ax = a[j, i]

            # iterate through series
            for k, (serie, color, marker, linestyle) in enumerate(zip(series, colors, markers, linestyles)):
                ind = (df.loc[:, "timeseries_filename"] == timeseries_filename) & (df.loc[:, series_var] == serie)
                x = x_convert * df.loc[ind, x_var]
                y = y_convert * df.loc[ind, y_var]

                # points
                ax.plot(x, y, linestyle='', marker=marker, markersize=marker_size,
                        markeredgewidth=markeredgewidth, markeredgecolor=color, markerfacecolor='None',
                        label=series_dict[serie])
                #
                # lines
                # ax.plot(x, y, color=color, marker='None', linewidth=linewidth, linestyle=linestyle, label=series_dict[serie])

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

            if len(y_limit) == 2:
                plt.ylim(y_limit)

            # Axes limits

            # Caption labels
            # caption_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
            # plt.text(-0.075, 1.05, caption_labels[count], horizontalalignment='center', verticalalignment='center',
            #          transform=ax.transAxes, fontsize='medium', fontweight='bold')
            count = count + 1

    # Legend
    # y_pos = j / 2 + 0.5
    # leg = a[j, i].legend(bbox_to_anchor=(1.2, y_pos), ncol=1, loc='center')
    x_pos = 0.45
    leg = a[j, i].legend(bbox_to_anchor=(x_pos, -0.15), ncol=3, loc='upper center')

    # Adjust layout
    # plt.tight_layout()
    plt.subplots_adjust(hspace=0.2, wspace=0.2, bottom=0.2)
    f.align_ylabels(a[:, 0])  # align y labels

    # Save Figure
    plt.savefig(savename, dpi=DPI, bbox_extra_artists=leg)
    # plt.close()

# -----------
# save summary of results at lowest COVE
# -----------
# average groups by sheetname and capacity
df2 = df.groupby(['sheetname', 'capacity']).mean()
# reset index
df2 = df2.reset_index()
# # find lowest COVE
low = df2.COVE.min()
ind = df2.loc[:, 'COVE'] == low
# get capacity for lowest COVE
capacity = float(df2.loc[ind, 'capacity'].values)
# select all indices at that capacity
ind2 = df2.loc[:, 'capacity'] == capacity
df3 = df2.loc[ind2, :]

# calculate % diff from wind_only
ind = df3.loc[:, 'sheetname'] == 'wind_only'
df3.loc[:, 'basis'] = float(df3.loc[ind, 'COVE'].values)
df3.loc[:, 'pct_diff'] = (df3.COVE - df3.basis) / df3.basis * 100

# save entries
df3.to_csv('lowest_COVE.csv')
