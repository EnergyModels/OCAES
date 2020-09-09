import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Set resolution
DPI = 600

# read-in simulation results
df = pd.read_csv('results_timeseries.csv')

# add entry for time
df.loc[:, 'time'] = df.index

# Set Color Palette
colors = sns.color_palette("colorblind")

# set style
sns.set_style("white", {"font.family": "serif", "font.serif": ["Times", "Palatino", "serif"]})
sns.set_context("paper")
sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})

# Column width guidelines https://www.elsevier.com/authors/author-schemas/artwork-and-media-instructions/artwork-sizing
# Single column: 90mm = 3.54 in
# 1.5 column: 140 mm = 5.51 in
# 2 column: 190 mm = 7.48 i
width = 7.48  # inches
height = 6.0  # inches

# create figure
nrows = 4
f, a = plt.subplots(nrows=nrows, ncols=1, sharex='col', squeeze=False)

# x-variable (same for each row)
x_var = 'time'
x_label = 'Time [hr]'
x_convert = 1.0
n_entries = [0, 72]  # start and end entries - leave empty to plot all

# array to hold legends
leg = []

for i in range(nrows):

    # get axis
    ax = a[i, 0]

    # indicate y-variables for each subplot(row)
    if i == 0:
        y_label = 'Electricity price\n[$/MWh]'
        y_convert = 1.0
        y_vars = ['price_grid']
        y_var_labels = ['Price']
        c_list = [(0,0,0)]
        markers = ['o']
        styles = ['-']

    elif i == 1:
        y_label = 'Power\n[MW]'
        y_convert = 1.0
        y_vars = ['P_wind', 'P_grid_sell', 'P_curtail']
        y_var_labels = ['Wind', 'Sold to grid', 'Curtailment']
        c_list = [colors[2], colors[5], colors[3]]
        markers = ['^', 'v', 'X']
        styles = ['-', '-', '-']

    elif i == 2:
        y_label = 'OCAES power\n[MW]'
        y_convert = 1.0
        y_vars = ['P_cmp', 'P_exp']
        y_var_labels = ['Compressor', 'Expander']
        c_list = [colors[0], colors[1]]
        markers = ['+', 's']
        styles = ['-', '-']

    else:  # if i == 3:
        y_label = 'Energy storage\n[MWh]'
        y_convert = 1.0
        y_vars = ['E_well']
        y_var_labels = ['Storage']
        c_list = [colors[7]]
        markers = ['^']
        styles = ['-']

    for y_var, y_var_label, c, marker, style in zip(y_vars, y_var_labels, c_list, markers, styles):
        # get data
        if len(n_entries) > 0:
            x = df.loc[n_entries[0]:n_entries[1], x_var] * x_convert
            y = df.loc[n_entries[0]:n_entries[1], y_var] * y_convert
        else:  # otherwise plot all
            x = df.loc[:, x_var] * x_convert
            y = df.loc[:, y_var] * y_convert

        # plot as lines
        ax.plot(x, y, c=c, label=y_var_label, linewidth=1.5, linestyle=style)

    # labels
    ax.set_ylabel(y_label)
    if i == nrows - 1:
        ax.set_xlabel(x_label)

    # Despine and remove ticks
    sns.despine(ax=ax, )
    ax.tick_params(top=False, right=False)

    # Caption labels
    caption_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']
    txt = plt.text(-0.1, 1.05, caption_labels[i], horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize='medium', fontweight='bold')
    leg.append(txt)

    # legend
    if len(y_var_labels) > 1:
        l = ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5), fancybox=True, fontsize=12)
        leg.append(l)

# align labels
f.align_ylabels(a[:, 0])

# Set size
f = plt.gcf()
f.set_size_inches(width, height)

# save and close
plt.savefig('results_COVE.png', dpi=600, bbox_extra_artists=leg, bbox_inches='tight')
# plt.close()
