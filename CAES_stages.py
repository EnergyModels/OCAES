import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import os
import pandas as pd
import numpy as np
from math import log
import seaborn as sns

# Inputs
power = [10, 50, 100, 500, 1000]  # MW
P_amb = 1.01325  # bar
T_amb = 25.0  # C
depth = [500, 1000, 1500, 2000, 2500, 3000]  # m
eta_CMP = 0.9
eta_EXP = 0.9

# Convert Inputs
# p_in = p_in * 1E5  # from bar to Pa
# T_in = T_in + 273.15  # from C to K

# Constants
rho = 1000 # density of water, kg/m3
g = 9.81 # gravitational constant, m/s^2

# Calculations
entries = ['power', 'depth', 'P_amb', 'T_amb', 'P_res', 'eta_CMP', 'eta_EXP', 'W_CMP', 'W_EXP','m_dot_CMP','m_dot_EXP', 'N_stg_cent', 'N_stg_piston', 'RTE']
df = pd.DataFrame(columns=entries)

for pwr in power:
    for z in depth:


        P_res = rho * g * z * 1E-5 # kg/m3 * m/s^2 * m = N/m^2 = Pa

        # Mouli-Castillo methodology
        s = 3  # number of stages (Qin & Loth 2014)
        k = 1.4  # dimensionless gas constant
        R_const = 8.314  # kJ/kmol-K
        R_air = R_const / 28.97  # kJ/kg-K
        W_CMP = s * k * R_air * T_amb / (k - 1) * (
                    (P_res / P_amb) ** ((k - 1) / (eta_CMP * s * k)) - 1.0)  # Specific work (kJ/kg)
        W_EXP = s * k * R_air * T_amb / (k - 1) * (
                    (P_res / P_amb) ** (eta_EXP * (k - 1) / (s * k)) - 1.0)  # Specific work (kJ/kg)

        RTE = W_EXP / W_CMP


        # Other calcs
        m_dot_CMP = pwr * 1000 / W_CMP # kg/s
        m_dot_EXP = pwr * 1000 / W_EXP

        # Ideal Gas

        # Store data
        s = pd.Series(index=entries)
        s['power'] = pwr
        s['depth'] = z
        s['P_amb'] = P_amb
        s['T_amb'] = T_amb
        s['P_res'] = P_res
        s['eta_CMP'] = eta_CMP
        s['eta_EXP'] = eta_EXP
        s['W_CMP'] = W_CMP
        s['W_EXP'] = W_EXP
        s['m_dot_CMP'] = m_dot_CMP
        s['m_dot_EXP'] = m_dot_EXP
        s['N_stg_cent'] = round(log(P_res)/log(3),0)
        s['N_stg_piston'] = round(log(P_res)/log(10),0)
        s['RTE'] = RTE

        df = df.append(s,ignore_index=True)


sns.lineplot(x='depth',y='RTE',hue='power',data=df)
plt.savefig('CAES_RTE.png')

sns.lineplot(x='depth',y='m_dot_CMP',hue='power',data=df)
plt.savefig('CAES_m_dot_CMP.png')
