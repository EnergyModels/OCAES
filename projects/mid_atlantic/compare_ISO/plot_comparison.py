# General imports
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set Color Palette
colors = sns.color_palette("colorblind")
# Set resolution for saving figures
DPI = 300

# Column width guidelines https://www.elsevier.com/authors/author-schemas/artwork-and-media-instructions/artwork-sizing
# Single column: 90mm = 3.54 in
# 1.5 column: 140 mm = 5.51 in
# 2 column: 190 mm = 7.48 i
width = 7.48  # inches
height = 5.5  # inches

# %%=============================================================================#
# Figure 6 - LCOE
files = ["sweep_results_ISONE.csv","sweep_results_NYISO.csv","sweep_results_PJM.csv"]
savename = "Fig8_location_MC_OCAES.png"
# =============================================================================#
y_vars = ["revenue", "LCOE", "COVE"]
y_labels = ["Revenue\n($/kWh)", "LCOE\n($/kWh)", "COVE($/kWh)"]
y_converts = [1.0, 1.0, 1.0]
y_limits = [[], [], []]

df = pd.DataFrame()
for file in files:
    dfi = pd.read_csv(file)
    df = df.append(dfi,ignore_index=True)
df.reset_index()

df = df[df.loc[:,"sheetname"]=="24_hr_ocaes"]

#
f, a = plt.subplots(1, 3, sharey=True)
a = a.ravel()

# Set size
f.set_size_inches(width, height)
legend = [False,True,False]
for ax, y_var, y_label, y_convert, y_limit, leg in zip(a, y_vars, y_labels, y_converts, y_limits, legend):
    df.loc[:, y_var] = df.loc[:, y_var] * y_convert
    sns.histplot(data=df, x=y_var, ax=ax, hue='scenario', element='step', fill=False, legend=leg,bins=60)
    ax.set_xlabel(y_label)
    # sns.distplot(df[y_var], ax=ax)

# a[1].legend(bbox_to_anchor=(0.5, -0.3), ncol=3)

# Save Figure
plt.savefig(savename, dpi=DPI)
# plt.close()
