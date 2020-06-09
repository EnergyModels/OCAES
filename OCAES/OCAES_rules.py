# ----------------
# capacity constraints
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


def pwr_grid(model, t):
    return model.P_grid[t] <= model.X_wind


# energy
def energy_capacity_well_min(model, t):
    return 0.0 <= model.E_well[t]


def energy_capacity_well_max(model, t):
    return model.E_well[t] <= model.E_well_max


# ----------------
# power balance
# ----------------
def power_balance(model, t):
    return model.P_wind[t] + model.P_exp[t] == model.P_curtail[t] + model.P_grid[t] + model.P_cmp[t]


# ----------------
# energy stored
# ----------------
def energy_stored(model, t):
    if t == 1:
        return model.E_well[t] == model.E_well_init
    else:
        return model.E_well[t] == model.E_well[t - 1] + \
               model.eta_storage_single * model.P_cmp[t] * model.delta_t - \
               model.eta_storage_single * model.P_exp[t] * model.delta_t


def energy_stored_final(model):
    return model.E_well[model.T - 1] == model.E_well_init


# ----------------
# avoided emissions
# ----------------
def emissions(model):
    return model.avoided_emissions == model.delta_t * sum(model.P_grid[t] * model.emissions_grid[t] for t in model.t)


# ----------------
# electricity delivered to the grid
# ----------------
def total_electricity(model):
    return model.total_electricity == sum(model.P_grid[t] for t in model.t)


def yearly_electricity(model):
    return model.yearly_electricity == sum(model.P_grid[t] for t in model.t) * 8760 / (model.T * model.delta_t)


# ----------------
# economics
# ----------------
def revenue(model, t):
    return model.revenue[t] == model.P_grid[t] * model.delta_t * model.price_grid[t]


def total_revenue(model):
    return model.total_revenue == model.delta_t * sum(model.P_grid[t] * model.price_grid[t] for t in model.t)


def yearly_revenue(model):
    return model.yearly_revenue == model.delta_t * sum(model.P_grid[t] * model.price_grid[t] for t in model.t) * 8760 / (
            model.T * model.delta_t)


def yearly_costs(model):
    # capital costs = capacity * annual costs
    capital = model.X_wind * model.AC_wind + model.X_well * model.AC_well + model.X_cmp * model.AC_cmp + model.X_exp * model.AC_exp

    # fixed costs
    fixed = model.X_wind * model.F_wind + model.X_well * model.F_well + \
            model.X_cmp * model.F_cmp + model.X_exp * model.F_exp

    # variable costs
    variable = model.V_wind * model.delta_t * sum(model.P_wind[t] for t in model.t) + \
               model.V_cmp * model.delta_t * sum(model.P_cmp[t] for t in model.t) + \
               model.V_exp * model.delta_t * sum(model.P_exp[t] for t in model.t)
    variable = variable * 8760 / (model.T * model.delta_t)  # scale to one year

    return model.yearly_costs == capital + fixed + variable


def yearly_profit(model):
    return model.yearly_profit == model.yearly_revenue - model.yearly_costs


# ----------------
# objective
# ----------------
def objective(model):  # Objective - maximize total revenue
    return model.total_revenue
    # return model.costs / sum(model.E_grid[t] * model.delta_t for t in model.t) # LCOE
