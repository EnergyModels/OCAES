import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from math import log


entries = ['Pr','n','eta']
df = pd.DataFrame(columns=entries)

Prs = np.linspace(2.5,300,num=100)
    # = [2.5, 25, 250]
ns = [1.01, 1.1, 1.2, 1.3, 1.4, 1.5]

for Pr in Prs:
    for n in ns:
        s = pd.Series(index=entries)
        s['Pr'] = Pr
        s['n'] = n
        num  = (log(Pr) - 1.0 + 1.0/ Pr)
        denom = (Pr**((n-1.0)/n)-1.0)/(n -1.0)+Pr**(-1.0/n)-1+(Pr-1.0)*(Pr**(-1.0/n)-1/Pr)
        s['eta'] = num / denom

        df = df.append(s,ignore_index=True)


sns.lineplot(x='Pr',y='eta',hue='n', data=df)
plt.savefig('etaIsothermal_v_polytropicIndex.png')