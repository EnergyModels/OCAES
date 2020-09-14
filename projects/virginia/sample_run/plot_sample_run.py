import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Set resolution
DPI = 600

# read-in simulation results
df = pd.read_csv('results_timeseries.csv')

# drop first row
# df = df.loc[1:, :]

# create columns to represent compressor and expander power and m_dot
# ind_cmp = df.loc[:, 'm_dot'] > 0
# ind_exp = df.loc[:, 'm_dot'] < 0
# df.loc[ind_cmp, 'pwr_cmp'] = df.loc[ind_cmp, 'pwr']
# df.loc[ind_exp, 'pwr_exp'] = df.loc[ind_exp, 'pwr']
# df.loc[ind_cmp, 'm_dot_cmp'] = df.loc[ind_cmp, 'm_dot']
# df.loc[ind_exp, 'm_dot_exp'] = -1.0 * df.loc[ind_exp, 'm_dot']
# df = df.fillna(0.0)

# add entries for hydrostatic pressure and MAOP
# df.loc[:, 'hydrostatic'] = 14.0235
# df.loc[:, 'MAOP'] = 17.34005775

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
x_lims = [0.0, 80.0]

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
        y_lims = [0.0, 40.0]

    elif i == 1:
        y_label = 'Power\n[MW]'
        y_convert = 1.0
        y_vars = ['P_wind', 'P_grid_sell']
        y_var_labels = ['Wind power production', 'Net delivered to grid']
        c_list = [colors[2], colors[5]]
        markers = ['^', 'v']
        styles = ['-', '-']
        y_lims = [0.0, 600.0]

    elif i == 2:
        y_label = 'OCAES power\n[MW]'
        y_convert = 1.0
        y_vars = ['P_cmp', 'P_exp']
        y_var_labels = ['Compressor', 'Expander']
        c_list = [colors[0], colors[1]]
        markers = ['+', 's']
        styles = ['-', '-']
        y_lims = [0.0, 300.0]

    else:  # if i == 3:
        y_label = 'Energy storage\n[MWh]'
        y_convert = 1.0
        y_vars = ['E_well']
        y_var_labels = ['Storage']
        c_list = [colors[7]]
        markers = ['^']
        styles = ['-']
        y_lims = [0.0, 6000.0]

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

        # plot as points
        # marker_size = 4
        # markeredgewidth = 1
        # ax.plot(x, y, label=y_var_label, linestyle='', marker=marker, markersize=marker_size,
        #         markeredgewidth=markeredgewidth, markeredgecolor=c, markerfacecolor='None')

    # labels
    ax.set_ylabel(y_label)
    if i == nrows - 1:
        ax.set_xlabel(x_label)

    # Despine and remove ticks
    sns.despine(ax=ax, )
    ax.tick_params(top=False, right=False)

    # Axes limits
    if len(y_lims) == 2:
        ax.set_ylim(bottom=y_lims[0], top=y_lims[1])

    # Axes limits
    if len(x_lims) == 2:
        ax.set_xlim(left=x_lims[0], right=x_lims[1])

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
plt.savefig('Fig_Optimization_Model_Overview.png', dpi=600, bbox_extra_artists=leg, bbox_inches='tight')
# plt.close()
