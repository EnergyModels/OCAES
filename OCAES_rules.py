# from pyomo.environ import *
import pyomo.environ as pyo


# ----------------
# Wind farm constraints
# ----------------
def energy_wind(model, t):
    return model.E_WIND[t] == model.N_WIND * model.E_WT[t]


def capacity_wind(model, t):
    return model.X_WIND == model.N_WIND * model.X_WT


# ----------------
# Machinery constraints
# ----------------

def capacity_cmp(model, t):
    return model.E_CMP[t] <= model.X_OCAES * model.delta_t


def capacity_exp(model, t):
    return model.E_EXP[t] <= model.X_OCAES * model.delta_t


def work_cmp(model, t):
    # return model.E_CMP[t] == model.M_CMP[t] * model.delta_H / model.eta_CMP
    return model.E_CMP[t] == model.M_CMP[t] * model.W_CMP * model.delta_t


def work_exp(model, t):
    # return model.E_EXP[t] == model.M_EXP[t] * model.delta_H * model.eta_EXP
    return model.E_EXP[t] == model.M_EXP[t] * model.W_EXP * model.delta_t


# ----------------
# Reservoir constraints
# ----------------
def initial_storage(model):
    return model.M_RES0 == 0.0#5 * model.N_WELLS * model.M_WELL  # Reservoir starts half full


def reservoir_capacity_limit(model, t):
    return model.M_RES[t] <= model.N_WELLS * model.M_WELL


def reservoir_rate_limit_in(model, t):
    return model.M_CMP[t] <= model.N_WELLS * model.M_DOT_WELL * model.delta_t


def reservoir_rate_limit_out(model, t):
    return model.M_EXP[t] <= model.N_WELLS * model.M_DOT_WELL * model.delta_t


# ----------------
# Energy and mass balances
# ----------------
def energy_balance(model, t):
    if t>360:
        return model.E_WIND[t] + model.E_EXP[t] == model.E_CURTAIL[t] + model.E_GRID[t] + model.E_CMP[t]
    else:
        return model.E_WIND[t] + model.E_EXP[t] == model.E_CURTAIL[t] + model.E_CMP[t]
    #
    # return model.E_WIND[t] == model.E_CURTAIL[t] + model.E_GRID[t]


def mass_balance(model, t):
    if t == 1:
        return model.M_RES[t] == model.M_RES0 + model.M_CMP[t] - model.M_EXP[t]
    else:
        return model.M_RES[t] == model.M_RES[t - 1] + model.M_CMP[t] - model.M_EXP[t]


# def grid_ramp_rate_limit1(model, t):
#     from pyomo.environ import Constraint
#     if t == 1:
#         return Constraint.Skip
#     else:
#         return model.E_GRID[t - 1] - model.E_GRID[t] <= model.GRID_RAMP_RATE * model.delta_t  # TODO add to docs


# def grid_ramp_rate_limit2(model, t):
#     from pyomo.environ import Constraint
#     if t == 1:
#         return Constraint.Skip
#     else:
#         return model.E_GRID[t] - model.E_GRID[t - 1] <= model.GRID_RAMP_RATE * model.delta_t  # TODO add to docs


# ----------------
# Economics
# ----------------


# def revenue(model):
#     return model.REVENUE == model.PRICE_MULTIPLIER * sum(model.E_GRID[t] * model.P[t] for t in model.t)


def costs(model):
    capital = model.CCR * (model.X_WIND * model.C_WIND + model.N_WELLS * model.C_WELL + model.X_OCAES * model.C_MACHINE)
    fixed = model.X_WIND * model.F_WIND + model.X_OCAES * model.F_OCAES
    variable1 = model.V_WIND * sum(model.E_WIND[t] for t in model.t)
    variable2 = model.V_OCAES * sum(model.E_CMP[t] + model.E_EXP[t] for t in model.t)
    return model.COSTS == capital + fixed + variable1 + variable2
    # return model.COSTS == model.CCR * model.X_WIND * model.C_WIND


# def profit(model):
#     return model.PROFIT == model.REVENUE - model.COSTS


def objective(model):  # Objective - maximize profit
    # return model.REVENUE
    return model.COSTS / sum(model.E_GRID[t] for t in model.t)
