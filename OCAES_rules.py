# ----------------
# Constraint and objective functions
# ----------------
def energy_balance(model, t):
    return model.E_WIND[t] + model.E_EXP[t] == model.E_Curtail[t] + model.E_GRID[t] + model.E_CMP[t]


def capacity_cmp(model, t):
    return model.E_CMP[t] <= model.X_OCAES[t] * model.delta_T


def capacity_exp(model, t):
    return model.E_EXP[t] <= model.X_OCAES[t] * model.delta_T


def reservoir_mass_limit(model, t):
    return model.M_RES[t] <= model.N_WELLS * model.M_WELL


def mass_balance(model, t):
    if t == 1:
        return model.M_RES[t] == model.M_RES0 + model.M_CMP[t] - model.M_EXP[t]
    else:
        return model.M_RES[t] == model.M_RES[t - 1] + model.M_CMP[t] - model.M_EXP[t]


def work_cmp(model, t):
    return model.E_CMP[t] == model.m_CMP[t] * model.delta_H / model.eta_CMP


def work_exp(model, t):
    return model.E_EXP[t] == model.m_EXP[t] * model.delta_H * model.eta_EXP


def revenue(model, t):
    return model.revenue == 1  # TODO Need to sum


def costs(model, t):
    model.X_WIND
    model.C_WIND
    model.F_WIND
    model.V_WIND
    model.C_WELL
    model.C_MACHINE
    model.F_OCAES
    model.V_OCAES
    model.CCR



    return model.costs == 1  # TODO


def profit(model, t):
    return model.profit[t] == model.revenue - model.costs


def objective(model):  # Objective - maximize profit
    return model.profit  # TODO Need to sum
