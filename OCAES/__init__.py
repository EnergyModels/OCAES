import os

# functions
from .OCAES import ocaes
from .monte_carlo_inputs import monteCarloInputs

# storing where resources folder is
resource_path = os.path.join(os.path.split(__file__)[0], "resources")