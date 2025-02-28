# This file defines deposits, depots, and full ISRU plant networks for different plants under consideration
# Used by the simulation core to iterate through and compare the performance of different models

import mars
import copy
from resources import *
from complex_process import *
from processes import *
from plant_model import *

### Regolith models; vary based on site, ice content, and hydrates ###
# Worst-case scenario: no substantial ice content, ~12% hydrates for over all 2.5% water by mass
regolith_dry = ResourceDeposit('Site_Regolith', {'Mars_Regolith': 0.825, 'Mars_Mineral_Hydrate_Wet': 0.175}, 'SOLID')
# Hydrate ratio used by global simulants. Likely at the high end of the expected water mass %
regolith_hydrate = ResourceDeposit('Site_Regolith', {'Mars_Regolith': 0.6, 'Mars_Mineral_Hydrate_Wet': 0.4}, 'SOLID')
# Mix of porous regolith dust and ice, potentially found in areas such as Utopia Planitia. Likely rich in hydrates as well
regolith_icy = ResourceDeposit('Site_Regolith', {'Mars_Regolith': 0.5, 'Mars_Mineral_Hydrate_Wet': 0.25, 'Water': 0.25}, 'SOLID')
# Likely composition of a true glacial ice deposit. Estimates range from 75-90% pure
ice_deposit = ResourceDeposit('Site_Regolith', {'Water': 0.8, 'Mars_Regolith': 0.15, 'Mars_Mineral_Hydrate_Wet': 0.05}, 'SOLID')

### Martian atmospheric model. Invariant for all plants ###
mars_atmosphere_model = ResourceDeposit('Mars_Atmosphere', mars.atmospheric_composition, 'GAS', mars.temperature, mars.pressure)

### Plant component dictionaries. Not necessarily full chains, can be assembled somewhat interchangeably ###
# Base LO2/LH2 processing plant
plant_lo2_lh2 = {
    'Crushing': {
        'Model': Regolith_Pulverization(), 'From': ['Site_Regolith']
    },
    'Electrolysis': {
        'Model': Water_Electrolysis(), 'From': ['Heating']
    },
    'H2O2_Liquefication': {
        'Model': H2O2_Cryocooler(arg_filter=True), 'From': ['Electrolysis']
    },
    'Fuel_Storage': {
        'Model': ResourceDepot('Fuel_Storage', {'Oxygen': 0.857, 'Hydrogen': 0.143}, 'LIQUID'),
        'From': ['H2O2_Liquefication']
    },
}

# Base LO2/CH4 processing plant
plant_lo2_ch4 = {
    'Mars_Atmosphere': {
        'Model': copy.deepcopy(mars_atmosphere_model),
    },
    'Crushing': {
        'Model': Regolith_Pulverization(), 'From': ['Site_Regolith']
    },
    'Electrolysis': {
        'Model': Water_Electrolysis(), 'From': ['Heating']
    },
    'Methane_Production': {
        'Model': Methane_Sabatier(), 'From': ['Electrolysis', 'Mars_Atmosphere']
    },
    'O2_Liquefication': {
        'Model': O2_Cryocooler(arg_filter=True), 'From': ['Electrolysis']
    },
    'Fuel_Storage': {
        'Model': ResourceDepot('Fuel_Storage', {'Oxygen': 0.75, 'Methane': 0.25}, 'LIQUID'),
        'From': ['O2_Liquefication', 'Methane_Production']
    },
}

# TEMP: heating models because backpropagation is complicated
ice_heating = {
    'Model': Water_Sublimation(), 'From': ['Crushing']
}
hydrate_heating = {
    'Model': Hydrate_Liberation_LowTemp(), 'From': ['Crushing']
}

# Addon plant for regolith bagging
plant_bagging = {
    'Bagging': {
        'Model': Regolith_Bagging(), 'From': ['Heating']
    }
}

# Addon plant for regolith sintering, bagging overage
plant_sinter = {
    'Sinter': {
        'Model': Regolith_Sintering(), 'From': ['Heating']
    },
    'Bagging': {
        'Model': Regolith_Bagging(), 'From': ['Sinter']
    }
}

# Addon plant for regolith sintering, MRE overage
plant_sinter_mre = {
    'Sinter': {
        'Model': Regolith_Sintering(), 'From': ['Heating']
    },
    'MRE': {
        'Model': Molten_Regolith_Electrolysis(), 'From': ['Sinter']
    }
}

# Addon plant for regolith MRE alone
plant_mre = {
    'MRE': {
        'Model': Molten_Regolith_Electrolysis(), 'From': ['Heating']
    }
}

# MRE plant with water / fuel side products
plant_metals_base = {
    'Site_Regolith': {
        'Model': copy.deepcopy(regolith_hydrate)
    },
    'Crushing': {
        'Model': Regolith_Pulverization(), 'From': ['Site_Regolith']
    },
    'Heating': {
        'Model': Hydrate_Liberation_HighTemp(), 'From': ['Crushing']
    },
    'MRE': {
        'Model': Molten_Regolith_Electrolysis(), 'From': ['Heating']
    },
    'Metals_Storage': {
        'Model': ResourceDepot('Metals_Storage', {'Mars_Metal_Alloy': 1.0}, 'SOLID'),
        'From': ['MRE']
    },
}

# Addon module to condense O2 from MRE
plant_metals_refine_sideproducts = {
    'O2_Liquefication': {
        'Model': O2_Cryocooler(arg_filter=True), 'From': ['MRE']
    },
}


# Utility function to correctly populate a given ISRU plant definition map with the specified regolith model
def SetInputRegolith(arg_plant_def, arg_regolith, arg_name):
    arg_plant_def['Site_Regolith'] = {'Model': copy.deepcopy(arg_regolith)}
    # TEMP: set regolith handler appropriately as well
    if arg_name == 'yes_ice':
        arg_plant_def['Heating'] = copy.deepcopy(ice_heating)
    else:
        arg_plant_def['Heating'] = copy.deepcopy(hydrate_heating)
    return arg_plant_def
