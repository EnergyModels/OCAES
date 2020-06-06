import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from OCAES import ocaes

# ----------------------
# create and run model
# ----------------------
data = pd.read_csv('data_manual.csv')
inputs = ocaes.get_default_inputs()
model = ocaes(data, inputs)
df, s = model.get_full_results()

# ----------------------
# plot results
# ----------------------
n_plots = 3

# Column width guidelines https://www.elsevier.com/authors/author-schemas/artwork-and-media-instructions/artwork-sizing
# Single column: 90mm = 3.54 in
# 1.5 column: 140 mm = 5.51 in
# 2 column: 190 mm = 7.48 i
width = 7.48  # inches
height = 5.5  # inches

f, axes = plt.subplots(n_plots, 1, sharex='col')  # ,constrained_layout=True)

# style
sns.set_style("white", {"font.family": "serif", "font.serif": ["Times", "Palatino", "serif"]})
sns.set_context("paper")
sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
colors = sns.color_palette("Paired")

# x variable
x_var = df.index
x_convert = 1.0
x_label = 'Timestep [-]'

for i, ax in enumerate(axes):
    if i == 0:
        y_vars = ['P_cmp', 'P_exp', 'P_curtail', 'P_grid', 'P_wind']
        y_colors = [colors[0], colors[1], colors[2], colors[3], colors[4]]
        y_convert = 1.0
        y_label = 'Power [MW]'

    elif i == 1:
        y_vars = ['E_well']
        y_colors = [colors[0]]
        y_convert = 1.0
        y_label = 'Energy [MWh]'

    else:  # if i == 2:
        y_vars = ['emissions_grid']
        y_colors = [colors[0]]
        y_convert = 1.0
        y_label = 'Profit [$]'

    for y_var, y_color in zip(y_vars, y_colors):
        x = df.index * x_convert
        y = df.loc[:, y_var] * y_convert
        ax.plot(x, y, )

    # Despine and remove ticks
    sns.despine(ax=ax, )
    ax.tick_params(top=False, right=False)

    # Labels
    if i == n_plots - 1:
        ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

# Set size
f = plt.gcf()
f.set_size_inches(width, height)
