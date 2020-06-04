import pyomo.environ as pyo


# ----------------
# Capacity constraints
# ----------------

# power

def pwr_capacity_cmp(model, t):
    return model.P_cmp[t] <= model.X_cmp


def pwr_capacity_exp(model, t):
    return model.P_exp[t] <= model.X_exp


def pwr_capacity_well_in(model, t):
    return model.P_cmp[t] <= model.X_well


def pwr_capacity_well_out(model, t):
    return model.P_exp[t] <= model.X_well


# energy
def energy_capacity_well_min(model, t):
    return 0.0 <= model.E_well[t]


def energy_capacity_well_max(model, t):
    return model.E_well[t] <= model.E_well_max


# ----------------
# Power balance
# ----------------
def power_balance(model, t):
    return model.P_wind[t] + model.P_exp[t] == model.P_curtail[t] + model.P_grid[t] + model.P_cmp[t]


# ----------------
# Energy stored
# ----------------
def energy_stored(model, t):
    if t == 1:
        return model.E_well[t] == model.E_well_init
    else:
        return model.E_well[t] == model.E_well[t - 1] + \
               model.eta_storage_single * model.P_cmp[t] * model.delta_t - \
               model.eta_storage_single * model.P_exp[t] ** model.delta_t


def energy_stored_final(model):
    return model.E_well[model.T - 1] == model.E_well_init


# ----------------
# Avoided emissions
# ----------------
def emissions(model):
    return model.avoided_emissions == sum(model.P_grid[t] * model.delta_t * model.emissions_grid[t] for t in model.t)


# ----------------
# Economics
# ----------------
def revenue(model):
    return model.revenue == sum(model.P_grid[t] * model.delta_t * model.price_grid[t] for t in model.t)


def costs(model):
    capital = model.CCR * (
            model.X_wind * model.C_wind + model.X_well * model.C_well + model.X_cmp * model.C_cmp + model.X_exp * model.C_exp)
    fixed = model.X_wind * model.F_wind + model.X_well * model.F_well + model.X_cmp * model.F_cmp + model.X_exp * model.F_exp
    variable = model.V_wind * model.delta_t * sum(model.P_wind[t] for t in model.t) + \
               model.V_cmp * model.delta_t * sum(model.P_cmp[t] for t in model.t) + \
               model.V_exp * model.delta_t * sum(model.P_exp[t] for t in model.t)
    return model.costs == capital + fixed + variable


def profit(model):
    return model.profit == model.revenue - model.costs


# ----------------
# Economics
# ----------------
def objective(model):  # Objective - maximize profit
    return model.revenue
    # return model.costs / sum(model.E_grid[t] * model.delta_t for t in model.t) # LCOE
