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
DPI = 600  # Set resolution for saving figures

x_vars = ["capacity"]
x_labels = ["Storage power rating (MW)"]
x_converts = [1.0]
x_limits = [[0.0, 500.0]]

y_vars_all = ["X_dispatch", "LCOE"]
y_labels_all = ["Constant power output\n(MW)", "LCOE\n($/kWh)"]
y_converts_all = [1.0, 1.0]
y_limits_all = [[0.0, 120.0], [0.0, 2.5]]

series_var = 'scenario'
series = ['4_hr_batt', '10_hr_batt',
          '10_hr_ocaes', '24_hr_ocaes', '168_hr_ocaes']
series_dict = {'wind_only': 'Wind only', '4_hr_batt': 'Battery (4 hr)', '10_hr_batt': 'Battery (10 hr)',
               '10_hr_ocaes': 'OCAES (10 hr)', '24_hr_ocaes': 'OCAES (24 hr)',
               '48_hr_ocaes': 'OCAES (48 hr)', '72_hr_ocaes': 'OCAES (72 hr)', '168_hr_ocaes': 'OCAES (168 hr)'}

# Set Color Palette
colors = sns.color_palette("colorblind")
# colors = [colors[0], colors[5],
#           colors[2], colors[1], colors[3], colors[4], colors[6]]  # black, blue, brown, green, orange

colors = [colors[5], colors[0],
          colors[2], colors[1], colors[3], colors[4], colors[6]]  # black, blue, brown, green, orange
# linestyles = ['solid', 'solid',
#               'dashed', 'dotted', 'solid', 'solid', 'solid']

linestyles = [
    (0, (3, 1, 1, 1)), (0, (3, 5, 1, 5)), 'dashed', (0, (5, 5)),
    (0, (5, 10))]  # https://matplotlib.org/3.1.0/gallery/lines_bars_and_markers/linestyles.html
markers = ['s', 'D', '^', '.', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'o', 'X']

# =====================================
# process data
# =====================================

# Import results
df = pd.read_csv(results_filename)

# Only select results with CONST_DISPATCH objective
objective = 'CD_FIX_WIND_STOR'
df = df[df.loc[:, "objective"] == objective]

for v in range(1):
    # variable selection

    if v == 0:
        n = len(y_vars_all)
        y_vars = y_vars_all[0:n]
        y_labels = y_labels_all[0:n]
        y_converts = y_converts_all[0:n]
        y_limits = y_limits_all[0:n]
    elif v == 1:
        n = 2
        y_vars = y_vars_all[0:n]
        y_labels = y_labels_all[0:n]
        y_converts = y_converts_all[0:n]
        y_limits = y_limits_all[0:n]

    for timeseries_filename in df.timeseries_filename.unique():

        # name for saving results
        savename = timeseries_filename[:str.find(timeseries_filename, '.')]
        savename = savename + '_' + str(objective) + str(v) + '.png'
        print(savename)

        # =====================================
        # create plots
        # =====================================

        # Column width guidelines https://www.elsevier.com/authors/author-schemas/artwork-and-media-instructions/artwork-sizing
        # Single column: 90mm = 3.54 in
        # 1.5 column: 140 mm = 5.51 in
        # 2 column: 190 mm = 7.48 i
        width = 7.48  # inches
        height = 6.0  # inches

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
                    ind = (df.loc[:, "timeseries_filename"] == timeseries_filename) \
                          & (df.loc[:, 'objective'] == objective) \
                          & (df.loc[:, series_var] == serie)
                    x = x_convert * df.loc[ind, x_var]
                    y = y_convert * df.loc[ind, y_var]

                    # points
                    ax.plot(x, y, color=color, linestyle=linestyle, linewidth=2.0, label=series_dict[serie])
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

                # Axes limits
                if len(y_limit) == 2:
                    ax.set_ylim(bottom=y_limit[0], top=y_limit[1])

                # Axes limits
                if len(x_limit) == 2:
                    ax.set_xlim(left=x_limit[0], right=x_limit[1])

                # Caption labels
                caption_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
                plt.text(-0.1, 1.05, caption_labels[count], horizontalalignment='center', verticalalignment='center',
                         transform=ax.transAxes, fontsize='large', fontweight='bold')
                count = count + 1

        # Legend
        # y_pos = j / 2 + 0.5
        # leg = a[j, i].legend(bbox_to_anchor=(1.2, y_pos), ncol=1, loc='center')
        x_pos = 0.5
        leg = a[j, i].legend(bbox_to_anchor=(x_pos, -0.25), ncol=3, loc='upper center', handlelength=5)

        # Adjust layout
        # plt.tight_layout()
        plt.subplots_adjust(hspace=0.2, wspace=0.2, bottom=0.2)
        f.align_ylabels(a[:, 0])  # align y labels

        # Save Figure & rename those used in the study
        if savename == 'da_timeseries_inputs_2019_CD_FIX_WIND_STOR0.png':
            savename = 'Figure9_constant_dispatch.png'
        plt.savefig(savename, dpi=DPI, bbox_extra_artists=leg)
        plt.close()
