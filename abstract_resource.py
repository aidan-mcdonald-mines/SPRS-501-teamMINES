import mars
# This file defines an abstract resource class used to standardize behavior throughout the simulation

# Array of matter phases, used in various calculations
matter_phases = ['SOLID', 'LIQUID', 'GAS', 'PLASMA']
ZERO_TOL = 0.00001

# This class defines an abstract "resource" type and its associated physical properties
class Resource:
    def __init__(self, arg_name="resource_undefined"):
        # Set up a baseline list of properties all materials have
        self.Name = arg_name # For ID and debugging purposes
        self.Mass = 0         # kg
        self.Volume = 0       # m^3
        self.Density = {}       #kg/m^3
        self.Molar_Mass = 0   # kg/mol
        self.Temperature = 0  # K
        self.Pressure = 0     # Pa, primarily used by gases but tracked regardless
        self.Phase = matter_phases[0] # Default to Solid

    def setMass(self, arg_mass):
        # Define the mass of the resource; populate volume based on phase
        # For now, don't do anything special for plasma since I don't think we'll need to model magnetohydrodynamics
        self.Mass = arg_mass
        if self.Phase in ['SOLID', 'LIQUID']:
            if self.Phase not in self.Density:
                raise ValueError("Unable to calculate volume for {} with density {}".format(self.Name, self.Density))
            if self.Phase in self.Density:
                self.Volume = self.Mass * self.Density[self.Phase]
            else:
                self.Volume = None
        else:
            if self.Pressure is None or self.Temperature is None:
                self.Volume = None
            else:
                if self.Pressure == 0:
                    raise ValueError("Unable to calculate volume for {} with pressure 0".format(self.Name))
                if self.Molar_Mass == 0:
                    raise ValueError("Unable to calculate volume for {} with molar mass 0".format(self.Name))
                self.setIdealGas('Volume')

    def setIdealGas(self, arg_solve_for):
        # Ideal gas law modeling solves for the specified attribute assuming the other fields have been set correctly
        if self.Phase == 'GAS':
            if arg_solve_for == "Pressure":
                self.Pressure = self.Mass*self.Temperature*8.314 / (self.Volume*self.Molar_Mass)
            elif arg_solve_for == "Volume":
                self.Volume = self.Mass*self.Temperature*8.314 / (self.Pressure*self.Molar_Mass)
            elif arg_solve_for == "Temperature":
                self.Temperature = self.Pressure*self.Volume*self.Molar_Mass / (8.314*self.Mass)
        else:
            raise ValueError("Unable to perform ideal gas calculation for {} in {} phase".format(self.Name, self.Phase))
