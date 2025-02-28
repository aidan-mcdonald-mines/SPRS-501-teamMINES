import mars
import math

from abstract_resource import *
import resources as resourceLib
# This file defines an abstract process class used to standardize behavior throughout the simulation

# Data storage class used by Transforms to define the resources and conditions that
# make up that transform. Intentionally a subset of Resource information
class Component:
    def __init__(self, arg_name, arg_phase, arg_rate):
        self.Name = arg_name    # Resource name
        self.Phase = arg_phase
        self.Rate = arg_rate    # kg/s

# Data storage class used by Processes to define chemical or mechanical changes that process entails
class Transform:
    def __init__(self, arg_inputs=[], arg_outputs=[], arg_power=0):
        self.inputs = {component.Name: component for component in arg_inputs}   # List of Components
        self.outputs = {component.Name: component for component in arg_outputs} # List of Components
        self.Power = arg_power # W

    def get_input_masses(self, arg_time):
        return {name: arg_time*component.Rate for name, component in self.inputs.items()}

    def get_output_masses(self, arg_time):
        return {name: arg_time*component.Rate for name, component in self.outputs.items()}


# This class defines an abstract "process" type which defines a transformation
# between two sets of resources, taking into account power consumption and heat production
# TODO: Allow for _both_ a global process temperature/pressure and a specific temperature/pressure per resource!
class Process:
    def __init__(self, arg_name="process_undefined", arg_filter=False):
        self.Name = arg_name
        self.Whitelist = None
        self.RequestWhitelist = None
        self.Filter = arg_filter
        self.Transform = None
        self.Temperature = None
        self.Pressure = None
        self.energy_demand = 0
        self.duty_cycle = 0
        self.upstream_energy_demand = 0

    def setTransform(self, arg_transform):
        # Helper function, exposes several useful transform properties
        self.Transform = arg_transform
        self.Whitelist = list(self.Transform.inputs.keys())
        self.RequestWhitelist = list(self.Transform.outputs.keys())

    def configureInputs(self, input_resources):
        # Helper function used by run() and several child classes to modify input resource
        # pressures / temperatures as needed
        for resource_name in input_resources:
            if self.Pressure is not None:
                if input_resources[resource_name].Pressure < self.Pressure:
                    self.energy_demand += Compress(self.Pressure, input_resources[resource_name])
                elif input_resources[resource_name].Pressure > self.Pressure:
                    # As long as the target pressure is above Mars ambient, assume depressurization is free
                    if self.Pressure < mars.pressure:
                        raise ValueError("Attempting to depressurize below Mars ambient. Need new code to cover energy required")
                    input_resources[resource_name].Pressure = self.Pressure
            if self.Temperature is not None:
                if input_resources[resource_name].Temperature < self.Temperature:
                    self.energy_demand += Heat(self.Temperature, input_resources[resource_name])
                elif input_resources[resource_name].Temperature > self.Temperature:
                    # As long as the target temperature is above Mars ambient, assume cooling is free
                    if self.Temperature < mars.temperature:
                        raise ValueError("Attempting to depressurize below Mars ambient. Need new code to cover energy required")
                    input_resources[resource_name].Temperature = self.Temperature

    def run(self, delta_time, input_resources):
        # "Forward" direction of simulation. Step forward according to the transformation
        # given a list of input resources and a timestep
        # If the step is impossible, throw an error - possible TODO to reconsider this
        for resource_name, transform_resource in self.Transform.inputs.items():
            if resource_name == 'ANY': # Open matching case
                break
            if resource_name not in input_resources:
                raise ValueError("Process {} not provided with necessary resource {}".format(self.Name, resource_name))
            if input_resources[resource_name].Phase != transform_resource.Phase:
                raise ValueError("Process {} given resource {} with incorrect phase".format(self.Name, resource_name))
        # Update pressures and temperatures as needed
        self.energy_demand = 0
        self.configureInputs(input_resources)
        # Isolate resources that will not be used for passthrough
        passthrough_resources = {}
        for resource_name, input_resource in input_resources.items():
            if 'ANY' in self.Transform.inputs: # Open-ended processes only require specific phases to process
                if input_resource.Phase != self.Transform.inputs['ANY'].Phase:
                    passthrough_resources[resource_name] = input_resource
            else:
                if resource_name not in self.Transform.inputs:
                    passthrough_resources[resource_name] = input_resource
        for key in passthrough_resources:
            del input_resources[key]
        # Determine the potential mass of each product used given the time step,
        # then determine the limiting resource if needed
        max_used = self.Transform.get_input_masses(delta_time)
        used_ratio = 1
        input_masses = 0
        if 'ANY' in self.Transform.inputs:
            input_masses = sum(resource.Mass for name, resource in input_resources.items())
            used_ratio = min(used_ratio, input_masses / (self.Transform.inputs['ANY'].Rate*delta_time))
        else:
            for name, resource in input_resources.items():
                used_ratio = min(used_ratio, resource.Mass/max_used[name])
        self.duty_cycle = used_ratio
        # Increment process energy demand as needed
        process_energy = delta_time*self.Transform.Power*used_ratio
        self.energy_demand += process_energy
        step_outputs = {}
        # Create outputs given inputs
        for name, output_resource in self.Transform.outputs.items():
            output_mass = delta_time*used_ratio*output_resource.Rate
            newClass = getattr(resourceLib, name)
            step_outputs[name] = newClass(output_mass, self.Temperature, self.Pressure, output_resource.Phase)
        # Subtract mass from inputs; put what remains into overage
        for name, input_resource in input_resources.items():
            if 'ANY' in self.Transform.inputs:
                mass_removed = delta_time*used_ratio*self.Transform.inputs['ANY'].Rate*input_resource.Mass/input_masses
            else:
                mass_removed = delta_time*used_ratio*self.Transform.inputs[name].Rate
            # Account for floating point error - if 99.999% of an input resource has been used, the entire resource has been used
            if not abs(1-(input_resource.Mass/mass_removed)) <= ZERO_TOL:
                input_resource.setMass(input_resource.Mass - mass_removed)
                passthrough_resources[name] = input_resource
        # TODO: check for collisions
        step_outputs = step_outputs | passthrough_resources
        # Finally, return the created products
        return step_outputs


    def request(self, delta_time, request_resources):
        # "Backward" direction of simulation. Step backward according to the transformation
        # given a list of requested resources and a timestep
        # Safety protection, used in cases where a certain part of the chain is uninteresting / unconstrained
        if request_resources is None:
            return None
        # Confirm request is possible in the given time, then determine the required inputs and energy to fulfill it
        passthrough_requests = {}
        for resource_name, request_resource in request_resources.items():
            if resource_name not in self.Transform.outputs:
                passthrough_requests[resource_name] = request_resource
                continue
            if self.Transform.outputs[resource_name].Phase != request_resource.Phase:
                raise ValueError("Process {} received request for resource {} with incorrect phase".format(self.Name, resource_name))
            if request_resource.Mass / delta_time > self.Transform.outputs[resource_name].Rate:
                raise ValueError("Process {} cannot produce {} kg of resource {} in the given time".format(self.Name, request_resource.Mass, resource_name))
        # Remove any passthrough requests from consideration in the remaining steps
        for resource_name in passthrough_requests:
            del request_resources[resource_name]
        # Note energy spent updating pressures and temperatures as needed - compression / heating runs backwards in this case
        setup_energy_next = 0
        for resource_name, request_resource in request_resources.items():
            if request_resource.Pressure is not None:
                if request_resource.Pressure > self.Pressure:
                    setup_energy_next -= Compress(self.Pressure, request_resource)
            if request_resource.Temperature is not None:
                if request_resource.Temperature > self.Temperature:
                    setup_energy_next -= Heat(self.Temperature, request_resource)
        self.upstream_energy_demand = setup_energy_next # This energy is technically associated with the next process upstream
        # Determine the minimum rate needed to achieve all requested outputs
        max_made = self.Transform.get_output_masses(delta_time)
        used_ratio = 0
        for name, resource in request_resources.items():
            used_ratio = max(used_ratio, resource.Mass/max_made[name])
        self.duty_cycle = used_ratio
        # Note projected energy demand
        self.energy_demand = delta_time*self.Transform.Power*used_ratio
        step_requests = {}
        # Create requests given outputs - for now, treat Any as a None
        for name, input_resource in self.Transform.inputs.items():
            if name != 'ANY':
                input_mass = delta_time*used_ratio*input_resource.Rate
                newClass = getattr(resourceLib, name)
                step_requests[name] = newClass(input_mass, self.Temperature, self.Pressure, input_resource.Phase)
        step_requests = step_requests | passthrough_requests
        # Finally, return the requested products
        return step_requests


# The following functions aren't 'Processes' but are "Process-like". They do not involve changes in material composition
# or phase, but do involve changes in pressure and/or temperature. The functions are phase-agnostic where possible, and
# are used by Processes to modify the parameters of incoming resources

COMPRESSOR_EFFICIENCY = 0.8 # Fairly realistic target for both liquid and gas compressors
def Compress(target_pressure, input_resource):
    if input_resource.Phase == 'SOLID':
        return 0
    elif input_resource.Phase == 'LIQUID':
        # In this case, the energy required, assuming a constant volume, is just V*dP
        delta_press = target_pressure - input_resource.Pressure
        energy = delta_press*input_resource.Volume / COMPRESSOR_EFFICIENCY
        input_resource.Pressure = target_pressure
        return energy
    else:
        # The gas phase requires knowing the gamma value (ratio of heat capacities) for the gas
        # Equations are NASA-derived: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/compression-and-expansion/
        pressure_ratio = target_pressure/input_resource.Pressure
        inv_vol_ratio = math.exp(math.log(pressure_ratio)/input_resource.Gamma)
        new_volume = input_resource.Volume / inv_vol_ratio
        temp_ratio = pressure_ratio**((input_resource.Gamma-1)/input_resource.Gamma)
        energy = (target_pressure-input_resource.Pressure)*(input_resource.Volume-new_volume) / COMPRESSOR_EFFICIENCY
        input_resource.Pressure = target_pressure
        input_resource.Volume = new_volume
        input_resource.Temperature *= temp_ratio
        return energy

def Heat(target_temperature, input_resource):
    delta_t = target_temperature - input_resource.Temperature
    if input_resource.Phase == 'SOLID' or input_resource.Phase == 'LIQUID':
        energy = input_resource.Mass*delta_t*input_resource.Cp
        input_resource.Temperature = target_temperature
        return energy
    else:
        use_cp = input_resource.Gamma * 8.314 * input_resource.Mass / (input_resource.Molar_Mass*(input_resource.Gamma-1))
        energy = input_resource.Mass*delta_t*use_cp
        input_resource.Volume *= target_temperature/input_resource.Temperature # At constant pressure, volume scales linearly
        input_resource.Temperature = target_temperature
        return energy
