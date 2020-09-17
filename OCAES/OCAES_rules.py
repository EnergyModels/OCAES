from pyomo.environ import *


def pwr_wind(model, t):
    return model.P_wind[t] == model.X_wind * model.P_wind_fr[t]


# ----------------
# Variable capacities - X_wind and X_storage are optimized variables
# ----------------
def capacity_well_var(model):
    return model.X_well == model.X_storage


def capacity_cmp_var(model):
    return model.X_cmp == model.X_storage


def capacity_exp_var(model):
    return model.X_exp == model.X_storage


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


def pwr_grid_sell(model, t):
    return model.P_grid_sell[t] <= model.X_wind


def pwr_grid_limit(model, t):
    return model.P_grid_sell[t] + model.P_grid_buy[t] <= model.X_wind


def pwr_grid_buy_enabled(model, t):
    return model.P_grid_buy[t] <= model.X_wind


def pwr_grid_buy_disabled(model, t):
    return model.P_grid_buy[t] <= 0.0  # turned off arbitrage


def pwr_dispatch_const(model, t):
    return model.P_grid_sell[t] == model.X_dispatch


# energy
def energy_capacity_well_min(model, t):
    return model.E_well_min_fr * model.E_well_duration * model.X_well <= model.E_well[t]


def energy_capacity_well_max(model, t):
    return model.E_well[t] <= model.E_well_max_fr * model.E_well_duration * model.X_well


# ----------------
# power balance
# ----------------
def power_balance(model, t):
    return model.P_wind[t] + model.P_exp[t] + model.P_grid_buy[t] == model.P_curtail[t] + model.P_grid_sell[t] + \
           model.P_cmp[t]


# ----------------
# energy stored
# ----------------
def energy_stored_init(model):
    return model.E_well_init == value(model.X_well) * model.E_well_init_fr * model.E_well_duration


def energy_stored(model, t):
    if t == 1:
        return model.E_well[t] == model.E_well_init
    else:
        return model.E_well[t] == model.E_well[t - 1] + \
               model.delta_t * model.P_cmp[t] * model.eta_storage_single - \
               model.delta_t * model.P_exp[t] / model.eta_storage_single


def energy_stored_final(model):
    return model.E_well[model.T - 1] == model.E_well_init


# ----------------
# avoided emissions
# ----------------
def emissions(model):
    return model.avoided_emissions == model.delta_t * sum(
        model.P_grid_sell[t] * model.emissions_grid[t] for t in model.t) - \
           model.delta_t * sum(model.P_grid_buy[t] * model.emissions_grid[t] for t in model.t)


# ----------------
# electricity
# ----------------
def total_electricity(model):
    return model.total_electricity == sum(model.P_wind[t] for t in model.t)


def yearly_electricity(model):
    return model.yearly_electricity == sum(model.P_grid_sell[t] for t in model.t) * 8760 / (model.T * model.delta_t)


def yearly_electricity_generated(model):
    return model.yearly_electricity_generated == sum(model.P_wind[t] for t in model.t) * 8760 / (
                model.T * model.delta_t)


def yearly_electricity_purchased(model):
    return model.yearly_electricity_purchased == sum(model.P_grid_buy[t] for t in model.t) * 8760 / (
            model.T * model.delta_t)


def yearly_curtailment(model):
    return model.yearly_curtailment == sum(model.P_curtail[t] for t in model.t) * 8760 / (model.T * model.delta_t)


def yearly_exp_usage(model):
    return model.yearly_exp_usage == sum(model.P_exp[t] for t in model.t) * 8760 / (model.T * model.delta_t)


def yearly_cmp_usage(model):
    return model.yearly_cmp_usage == sum(model.P_cmp[t] for t in model.t) * 8760 / (model.T * model.delta_t)


# ----------------
# economics
# ----------------
def electricity_revenue(model, t):
    return model.electricity_revenue[t] == (model.P_grid_sell[t] - model.P_grid_buy[t]) * \
           model.delta_t * model.price_grid[t]


def yearly_electricity_revenue(model):
    return model.yearly_electricity_revenue == model.delta_t * sum(
        (model.P_grid_sell[t] - model.P_grid_buy[t]) * model.price_grid[t] for t in model.t) * 8760 / (
                   model.T * model.delta_t)


def yearly_capacity_credit(model):
    return model.yearly_capacity_credit == model.CC_value * 365 * min(model.X_wind,
                                                                      model.X_wind * model.CC_wind + model.X_exp * model.CC_exp)


def yearly_capacity_credit_simple(model):
    return model.yearly_capacity_credit == model.CC_value * 365 * (
                model.X_wind * model.CC_wind + model.X_exp * model.CC_exp)


def yearly_total_revenue(model):
    return model.yearly_total_revenue == model.yearly_electricity_revenue + model.yearly_capacity_credit


def yearly_costs(model):
    # capital costs = capacity * annual costs
    capital = model.CRF_wind * model.X_wind * model.C_wind + \
              model.CRF_well * model.X_well * model.C_well + \
              model.CRF_cmp * model.X_cmp * model.C_cmp + \
              model.CRF_exp * model.X_exp * model.C_exp

    # fixed costs
    fixed = model.X_wind * model.F_wind + model.X_well * model.F_well + model.X_cmp * model.F_cmp + model.X_exp * model.F_exp

    # variable costs
    variable = model.V_wind * model.delta_t * sum(model.P_wind[t] for t in model.t) + model.V_cmp * model.delta_t * sum(
        model.P_cmp[t] for t in model.t) + model.V_exp * model.delta_t * sum(model.P_exp[t] for t in model.t)
    variable = variable * 8760 / (model.T * model.delta_t)  # scale to one year

    return model.yearly_costs == capital + fixed + variable


def yearly_profit(model):
    return model.yearly_profit == model.yearly_total_revenue - model.yearly_costs


# ----------------
# value of electricity (denominator of COVE)
# ----------------
def yearly_electricity_value(model):
    return model.yearly_electricity_value == model.delta_t * sum(
        model.P_grid_sell[t] * model.price_grid[t] for t in model.t) / model.price_grid_average * 8760 / (
                   model.T * model.delta_t)


# ----------------
# objective
# ----------------
def objective_revenue(model):
    return model.yearly_electricity_revenue


def objective_COVE(model):
    return model.yearly_electricity_value


def objective_PROFIT(model):
    return model.yearly_profit


def objective_COST(model):
    return model.yearly_costs
