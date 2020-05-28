import pyomo.environ as pyo


# ----------------
# Capacity constraints
# ----------------
def capacity_cmp(model, t):
    return model.P_cmp[t] <= model.X_cmp


def capacity_exp(model, t):
    return model.P_exp[t] <= model.X_exp


def capacity_well_in(model, t):
    return model.P_cmp[t] <= model.X_well


def capacity_well_out(model, t):
    return model.P_exp[t] <= model.X_well


# ----------------
# Power balances
# ----------------
def power_balance(model, t):
    return model.P_wind[t] + model.P_exp[t] == model.P_curtail[t] + model.P_grid[t] + model.P_cmp[t]


# ----------------
# Energy stored
# ----------------
def energy_stored(model, t):
    return model.P_wind[t] + model.P_exp[t] == model.P_curtail[t] + model.P_grid[t] + model.P_cmp[t]


# ----------------
# Avoided emissions
# ----------------
def revenue(model):
    return model.avoided_emissions == sum(model.P_grid[t] * model.delta_t * model.Q_grid[t] for t in model.t)

# ----------------
# Economics
# ----------------


def revenue(model):
    return model.revenue == sum(model.P_grid[t] * model.delta_t * model.LMP_grid[t] for t in model.t)


def costs(model):
    capital = model.CCR * (
            model.X_wind * model.C_Wind + model.X_well * model.C_well + model.X_cmp * model.C_cmp + model.X_exp * model.C_exp)
    fixed = model.X_wind * model.F_wind + model.X_well * model.F_well + model.X_cmp * model.F_cmp + model.X_exp * model.F_exp
    variable = model.V_wind * sum(model.E_wind[t] for t in model.t) + model.V_cmp * sum(
        model.E_cmp[t] for t in model.t) + model.V_exp * sum(model.E_exp[t] for t in model.t)
    return model.costs == capital + fixed + variable


# def profit(model):
#     return model.profit == model.REVENUE - model.COSTS


def objective(model):  # Objective - maximize profit
    return model.REVENUE
    # return model.costs / sum(model.E_grid[t] * model.delta_t for t in model.t) # LCOE
