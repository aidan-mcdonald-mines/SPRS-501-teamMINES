# This file defines resource classes which inherit from the abstract Resource type
# Where needed, sources are included as comments
import mars
from abstract_resource import *

# Densities are nominal pressure / temperature values; real density will vary with both.
# TODO: Especially for water, determine if higher fidelity is needed / if volume is used at all

class Water(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='SOLID'):
        super().__init__(self.__class__.__name__)
        self.Density = {'SOLID': 916, 'LIQUID': 1000}
        self.Molar_Mass = 0.01802
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.Phase = arg_phase
        self.Gamma = 1.32
        self.Cp = 2050
        self.setMass(arg_mass)

# Gaseous / diatomic oxygen
class Oxygen(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='GAS'):
        super().__init__(self.__class__.__name__)
        self.Density = {'LIQUID': 1141}
        self.Molar_Mass = 0.032
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.Phase = arg_phase
        self.Gamma = 1.4
        self.Cp = 1452
        self.setMass(arg_mass)

# Gaseous / diatomic nitrogen
class Nitrogen(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='GAS'):
        super().__init__(self.__class__.__name__)
        self.Density = {'LIQUID': 807}
        self.Molar_Mass = 0.02802
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.Phase = arg_phase
        self.Gamma = 1.45
        self.Cp = 2000
        self.setMass(arg_mass)

# Gaseous / diatomic hydrogen
class Hydrogen(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='GAS'):
        super().__init__(self.__class__.__name__)
        self.Density = {'LIQUID': 70.85}
        self.Molar_Mass = 0.002016
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.Phase = arg_phase
        self.Gamma = 1.41
        self.Cp = 14290
        self.setMass(arg_mass)


class Methane(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='GAS'):
        super().__init__(self.__class__.__name__)
        self.Density = {'SOLID': 433, 'LIQUID': 422}
        self.Molar_Mass = 0.016
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.Phase = arg_phase
        self.Gamma = 1.35
        self.Cp = 2191
        self.setMass(arg_mass)


class Carbon_Dioxide(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='GAS'):
        super().__init__(self.__class__.__name__)
        self.Density = {'SOLID': 1564}
        self.Molar_Mass = 0.044
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.Phase = arg_phase
        self.Gamma = 1.3
        self.Cp = 815
        self.setMass(arg_mass)

# Trace gas in Martian atmosphere
class Carbon_Monoxide(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='GAS'):
        super().__init__(self.__class__.__name__)
        self.Molar_Mass = 0.028
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.Phase = arg_phase
        self.Gamma = 1.4
        self.Cp = 1036
        self.setMass(arg_mass)

# Trace gas in Martian atmosphere
class Argon(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='GAS'):
        super().__init__(self.__class__.__name__)
        self.Molar_Mass = 0.03995
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.Phase = arg_phase
        self.Gamma = 1.67
        self.setMass(arg_mass)

# Released by regolith heating
class Sulphur_Dioxide(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='GAS'):
        super().__init__(self.__class__.__name__)
        self.Molar_Mass = 0.06401
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.Phase = arg_phase
        self.Gamma = 1.29
        self.Cp = 622
        self.setMass(arg_mass)

# Generic substitute for input Martian regolith.
class Mars_Regolith(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='SOLID'):
        super().__init__(self.__class__.__name__)
        # Average of several MGS-1 simulants
        self.Density = {'SOLID': 1300}
        self.Temperature = arg_temp
        self.Phase = arg_phase
        # https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/2024GL108600
        self.Cp = 620
        self.setMass(arg_mass)

# Generic substitute for bagged Martian regolith.
class Mars_Regolith_Bagged(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='SOLID'):
        super().__init__(self.__class__.__name__)
        # Average of several MGS-1 simulants
        self.Density = {'SOLID': 1300}
        self.Temperature = arg_temp
        self.Phase = arg_phase
        # https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/2024GL108600
        self.Cp = 620
        self.setMass(arg_mass)

# Generic standin for hydrated Martian minerals, such as clays or gypsum. Simulants contain around 40% of this by mass
# Density and CP for this and following regolith "components" are just the simulant standard; the distinction doesn't
# impact calculation as long as the hydrates are not separated from the rest of the regolith before heating
class Mars_Mineral_Hydrate_Wet(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='SOLID'):
        super().__init__(self.__class__.__name__)
        # Average of several MGS-1 simulants
        self.Density = {'SOLID': 1300}
        self.Temperature = arg_temp
        self.Phase = arg_phase
        # https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/2024GL108600
        self.Cp = 620
        self.setMass(arg_mass)

# Generic standin for hydrated Martian minerals, such as clays or gypsum, post-heating
class Mars_Mineral_Hydrate_Dry(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='SOLID'):
        super().__init__(self.__class__.__name__)
        # Average of several MGS-1 simulants
        self.Density = {'SOLID': 1300}
        self.Temperature = arg_temp
        self.Phase = arg_phase
        # https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/2024GL108600
        self.Cp = 620
        self.setMass(arg_mass)

# Generic standin for sintered Martian regolith - density and CP values don't matter unless
# the glass is further post-processed
class Mars_Basaltic_Glass(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='SOLID'):
        super().__init__(self.__class__.__name__)
        # Average of several MGS-1 simulants
        self.Density = {'SOLID': 1300, 'LIQUID': 1300}
        self.Temperature = arg_temp
        self.Phase = arg_phase
        # https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/2024GL108600
        self.Cp = 620
        self.setMass(arg_mass)

# Generic standin for the metal alloy produced by MRE, predominantly Al but with Si, Fe, Ti
# components as well. As with other regolith end products, density / CP are fairly unimportant
class Mars_Metal_Alloy(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='SOLID'):
        super().__init__(self.__class__.__name__)
        # Average of several MGS-1 simulants
        self.Density = {'SOLID': 1300}
        self.Temperature = arg_temp
        self.Phase = arg_phase
        # https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/2024GL108600
        self.Cp = 620
        self.setMass(arg_mass)

# Generic standin for the waste material produced by MRE
class Mars_Slag(Resource):
    def __init__(self, arg_mass, arg_temp=mars.temperature, arg_press=mars.pressure, arg_phase='SOLID'):
        super().__init__(self.__class__.__name__)
        # Average of several MGS-1 simulants
        self.Density = {'SOLID': 1300}
        self.Temperature = arg_temp
        self.Phase = arg_phase
        # https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/2024GL108600
        self.Cp = 620
        self.setMass(arg_mass)
