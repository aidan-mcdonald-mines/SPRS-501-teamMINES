# This file defines process classes which inherit from the abstract Process type
# Where needed, sources are included as comments
import mars
from abstract_resource import *
from abstract_process import *
from complex_process import *
from resources import *

# General notes- clays and hydrated minerals will need to be heated to 200-1000 C to free water
# This same range allows for the release of sulphur dioxide starting at 500-600 C
# Check "Release of Volatiles from Possible Martian Analogs" for details

# Based on a SOXE electrolyzer
# See SOXE papers for details on working temperature / pressure
class Water_Electrolysis(Multiplex):
    def __init__(self, arg_filter=True):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = 700 + 273.15
        self.Pressure = 200*1000
        self.setTransform(Transform(
            [Component("Water", 'GAS', 0.72/3600)],
            [
                Component("Hydrogen", 'GAS', 0.08/3600),
                Component("Oxygen", 'GAS', 0.64/3600),
            ],
            3904 # Power consumption in W
        ))

# https://ntrs.nasa.gov/api/citations/20180004697/downloads/20180004697.pdf
class Methane_Sabatier(Multiplex):
    def __init__(self, arg_filter=True):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = 375 + 273.15
        self.Pressure = 517107
        self.setTransform(Transform(
            [
                Component("Hydrogen", 'GAS', 0.224/3600),
                Component("Carbon_Dioxide", 'GAS', 0.984/3600),
            ],
            [Component("Methane", 'LIQUID', 0.34/3600)],
            0 # In this case, gas heating / compression is responsible for the power consumption
        ))

# TODO: update some of the parameters of this class when processes support multiple distinct temperatures
# For now, low impact
# https://ntrs.nasa.gov/api/citations/20230014845/downloads/Ascend23_H2Liq_Paper_v1.pdf
class H2O2_Cryocooler(Multiplex):
    def __init__(self, arg_filter=False):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = mars.temperature
        self.setTransform(Transform(
            [
                Component("Hydrogen", 'GAS', 0.3/3600),
                Component("Oxygen", 'GAS', 2.4/3600),
            ],
            [
                Component("Hydrogen", 'LIQUID', 0.3/3600),
                Component("Oxygen", 'LIQUID', 2.4/3600),
            ],
            35000 # Power consumption in W
        ))

# TODO: update some of the parameters of this class when processes support multiple distinct temperatures
# For now, low impact
# TODO: narrow down mass flow and power usage here
# Based on industry standard performance of 700 kWh/mT, or 700 Wh/kg * 2.4 kg/hr = 1700W
class O2_Cryocooler(Multiplex):
    def __init__(self, arg_filter=False):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = mars.temperature
        self.setTransform(Transform(
            [ Component("Oxygen", 'GAS', 2.4/3600), ],
            [ Component("Oxygen", 'LIQUID', 2.4/3600), ],
            1700 # Power consumption in W
        ))

# Phase changers modeled as high-capacity processes for simplicity
class Water_Sublimation(Process):
    def __init__(self, arg_filter=False):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = 600 + 273.15
        self.Pressure = mars.pressure
        self.setTransform(Transform(
            [Component("Water", 'SOLID', 100/3600)],
            [Component("Water", 'GAS', 100/3600)],
            0 # Power consumption in W - low working pressure makes this free; heating the ice to working temp will take energy
        ))

# Liberation of water from clays / hydrates via heating. Temperature chosen to maximize
# water liberated while allowing little to no sulfide contamination. However, this does
# result in ~1/3 of the water remaining in the regolith. Of what is liberated, these
# hydrates are about 20% water by mass.
class Hydrate_Liberation_LowTemp(Process):
    def __init__(self, arg_filter=False):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = 600 + 273.15
        self.Pressure = mars.pressure
        self.setTransform(Transform(
            [Component("Mars_Mineral_Hydrate_Wet", 'SOLID', 100/3600)],
            [
             Component("Mars_Mineral_Hydrate_Wet", 'SOLID', 33.3/3600),
             Component("Mars_Mineral_Hydrate_Dry", 'SOLID', 53.3/3600),
             Component("Water", 'GAS', 13.3/3600)
            ],
            0 # Power consumption in W
        ))

# High-temperature equivalent of the above. This does release some sulphur dioxide -
# estimate here is 1.5% of hydrate mass, though it is not produced by the hydrate.
# Actual mass of SO2 contamination isn't incredibly important for this process- any
# future filtering step will use a power estimate based on the mass of input water vapor
class Hydrate_Liberation_HighTemp(Process):
    def __init__(self, arg_filter=False):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = 1000 + 273.15
        self.Pressure = mars.pressure
        self.setTransform(Transform(
            [Component("Mars_Mineral_Hydrate_Wet", 'SOLID', 100/3600)],
            [
             Component("Mars_Mineral_Hydrate_Dry", 'SOLID', 80/3600),
             Component("Water", 'GAS', 20/3600),
             Component("Sulphur_Dioxide", 'GAS', 1.5/3600)
            ],
            0 # Power consumption in W
        ))

# Need to dial in rate and energy usage
class Regolith_Pulverization(Process):
    def __init__(self, arg_filter=False):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = mars.temperature
        self.Pressure = mars.pressure
        self.setTransform(Transform(
            [Component("Mars_Regolith", 'SOLID', 30/3600)],
            [Component("Mars_Regolith", 'SOLID', 30/3600)],
            2000
        ))


# https://ntrs.nasa.gov/api/citations/19900015907/downloads/19900015907.pdf
# Note that this system is designed for only 8 hours of operation per day to recharge.
# We will assume continuous usage is possible; intermittent operation will be optimized by a separate section
bagging_rate = 120*0.0283 * 1400 /(3600) # Cubic feet of bags, converted to cubic meters, scaled by regolith density, converted to a per-second rate
class Regolith_Bagging(Process):
    def __init__(self, arg_filter=False):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = mars.temperature
        self.Pressure = mars.pressure
        self.setTransform(Transform(
            [Component("ANY", 'SOLID', bagging_rate)],
            [Component("Mars_Regolith_Bagged", 'SOLID', bagging_rate)],
            3760
        ))

# hhttps://oro.open.ac.uk/66214/1/Manuscript_2nd_revision_Final%20-%20without%20track%20changes.pdf
# Estimates are for _lunar_ regolith, but the general power-mass trend should be similar
# The best case scenario for the above paper sinters ~20g of regolith with 1000 W of power in ~200s
class Regolith_Sintering(Process):
    def __init__(self, arg_filter=False):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = mars.temperature
        self.Pressure = mars.pressure
        self.setTransform(Transform(
            [Component("ANY", 'SOLID', 10*0.02/200)],
            [Component("Mars_Basaltic_Glass", 'LIQUID', 10*0.02/200)], # This isn't really right, but it prevents some pipeline filtering issues
            10*1000
        ))

# Based on power estimates from Guerrero-Gonzalez et al. for a lunar MRE plant
# producing 25 mT of refined metal per year. For this estimate, assume half of the
# input material remains as slag, an additional 23.9 mT/year of O2 is produced as well
class Molten_Regolith_Electrolysis(Process):
    def __init__(self, arg_filter=False):
        super().__init__(self.__class__.__name__, arg_filter)
        self.Temperature = mars.temperature # Heating is accounted for in the power estimate in this case due to phase change
        self.Pressure = mars.pressure
        self.setTransform(Transform(
            [Component("Mars_Regolith", 'SOLID', 73.9*1000/(365*3600))],
            [
             Component("Mars_Metal_Alloy", 'SOLID', 25*1000/(365*3600)),
             Component("Mars_Slag", 'SOLID', 25*1000/(365*3600)),
             Component("Oxygen", 'GAS', 23.9*1000/(365*3600)),
            ],
            300000
        ))


if __name__=="__main__":
    input_water = Water(0.72, arg_phase='GAS', arg_temp=200+273.15, arg_press=138000)
    electrolyzer = Water_Electrolysis()
    electrolyzer.energy_supply = 4000*3600*2
    outputs = electrolyzer.run(3600, {'Water': input_water})
    for name, output in outputs.items():
        print(output.Name, output.Phase, output.Mass)
    requests = electrolyzer.request(3600, outputs)
    for name, request in requests.items():
        print(request.Name, request.Phase, request.Mass)
    print(electrolyzer.num_mocks)
