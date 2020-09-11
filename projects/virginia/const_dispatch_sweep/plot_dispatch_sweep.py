import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# =====================================
# user inputs
# =====================================
# data input
results_filename = "sweep_results.csv"
results_filename2 = "sweep_results_batt.csv"

# figure output
DPI = 600  # Set resolution for saving figures

x_vars = ["X_dispatch"]
x_labels = ["Dispatch power (MW)"]
x_converts = [1.0]
x_limits = [[0.0, 100.0]]

y_vars_all = ["LCOE", "X_wind", "X_exp", "yearly_curtailment_fr"]
y_labels_all = ["LCOE\n($/kWh)", "Wind\n(MW)", "Storage\n(MW)", "Curtailment\n(-)"]
y_converts_all = [1.0, 1.0, 1.0, 1.0]
y_limits_all = [[], [0.0,1000.0], [0.0,500.0], []]

series_var = 'scenario'
series = ['4_hr_batt', '10_hr_batt',
          '10_hr_ocaes', '24_hr_ocaes', '168_hr_ocaes']
series_dict = {'wind_only': 'Wind only', '4_hr_batt': 'Battery (4 hr)', '10_hr_batt': 'Battery (10 hr)',
               '10_hr_ocaes': 'OCAES (10 hr)', '24_hr_ocaes': 'OCAES (24 hr)',
               '48_hr_ocaes': 'OCAES (48 hr)', '72_hr_ocaes': 'OCAES (72 hr)', '168_hr_ocaes': 'OCAES (168 hr)'}

# Set Color Palette
colors = sns.color_palette("colorblind")
colors = [colors[0], colors[5],
          colors[2], colors[1], colors[3], colors[4], colors[6]]  # black, blue, brown, green, orange
linestyles = ['solid', 'solid',
              'dashed', 'dotted', 'solid', 'solid', 'solid']
markers = ['s', 'D', '^', '.', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'o', 'X']

# =====================================
# process data
# =====================================

# Import results
df1 = pd.read_csv(results_filename)
df2 = pd.read_csv(results_filename2)


df3 = pd.DataFrame()
# Filter df1 results
for timeseries_filename in df1.timeseries_filename.unique():
    for objective in df1.objective.unique():
        for sheetname in df1.sheetname.unique():
            for capacity in df1.capacity.unique():
                dfix = df1[(df1.loc[:, "timeseries_filename"] == timeseries_filename) &
                         (df1.loc[:, "objective"] == objective) &
                         (df1.loc[:, "sheetname"] == sheetname) &
                         (df1.loc[:, "capacity"] == capacity)]

                min_LCOE = dfix.LCOE.min()
                ind = dfix.LCOE==min_LCOE
                df3 = pd.concat([df3,dfix.loc[ind]],ignore_index=True)




###########
df2 = df2[(df2.loc[:, "objective"] == 'CONST_DISPATCH') &
          ((df2.loc[:, "sheetname"] == '4_hr_batt') | (df2.loc[:, "sheetname"] == '10_hr_batt'))]
df = pd.concat([df3, df2])
# Only select results with CONST_DISPATCH objective
objective = 'CONST_DISPATCH_FIX'
# df = df[df.loc[:, "objective"] == objective]

for v in range(2):
    # variable selection

    if v == 0:
        n = len(y_vars_all)
        y_vars = y_vars_all[0:n]
        y_labels = y_labels_all[0:n]
        y_converts = y_converts_all[0:n]
        y_limits = y_limits_all[0:n]
    elif v == 1:

        y_vars = [y_vars_all[0]]
        y_labels = [y_labels_all[0]]
        y_converts = [y_converts_all[0]]
        y_limits = [y_limits_all[0]]

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
        height = 8.0  # inches

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
                          & (df.loc[:, series_var] == serie)
                    x = x_convert * df.loc[ind, x_var]
                    y = y_convert * df.loc[ind, y_var]

                    # points
                    ax.plot(x, y, color=color, linestyle='None', marker=marker, markersize=marker_size,
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

                # Axes limits
                if len(y_limit) == 2:
                    ax.set_ylim(bottom=y_limit[0], top=y_limit[1])
                if len(x_limit) == 2:
                    ax.set_xlim(left=x_limit[0], right=x_limit[1])

                # Caption labels
                if v==0:
                    caption_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
                    plt.text(-0.1, 1.05, caption_labels[count], horizontalalignment='center', verticalalignment='center',
                             transform=ax.transAxes, fontsize='medium', fontweight='bold')
                    count = count + 1

        # Legend
        # y_pos = j / 2 + 0.5
        # leg = a[j, i].legend(bbox_to_anchor=(1.2, y_pos), ncol=1, loc='center')
        x_pos = 0.45
        leg = a[j, i].legend(bbox_to_anchor=(x_pos, -0.4), ncol=3, loc='upper center')

        # Adjust layout
        # plt.tight_layout()
        plt.subplots_adjust(hspace=0.2, wspace=0.2, bottom=0.2)
        f.align_ylabels(a[:, 0])  # align y labels

        # Save Figure
        plt.savefig(savename, dpi=DPI, bbox_extra_artists=leg)
        plt.close()
