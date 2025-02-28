# This file is for classes which mimic / wrap the Process() function signatures
# But have modified or overridden operations for specific use cases
import mars
import math
from abstract_resource import *
import resources as resourceLib
from abstract_process import *

# This class wraps a parallelizable process, and when request() is called it determines
# the minimum number of processing units needed to achieve the desired rate. It then mocks
# that number of units when run() is called
class Multiplex(Process):
    def __init__(self, arg_name="multiplex_undefined", arg_filter=False):
        super().__init__(arg_name, arg_filter)
        self.num_mocks = 1
        self.Transform = None


    def run(self, delta_time, input_resources):
        # Determine the minimum number of units needed to process all of the given input
        max_per_unit = self.Transform.get_input_masses(delta_time)
        use_ratio = 0
        for name, resource in input_resources.items():
            use_ratio = max(use_ratio, resource.Mass/max_per_unit[name])
        self.num_mocks = math.ceil(use_ratio)
        # Scale all resources and power down by the mock ratio
        for name in input_resources:
            input_resources[name].setMass(input_resources[name].Mass / self.num_mocks)
        # Call and capture the underlying transformation
        step_outputs = super().run(delta_time, input_resources)
        # Scale power and mass back up, then return
        self.energy_demand *= self.num_mocks
        for name in step_outputs:
            step_outputs[name].setMass(step_outputs[name].Mass * self.num_mocks)
        return step_outputs


    def request(self, delta_time, request_resources):
        # Determine the minimum rate needed to achieve all requested outputs
        # Safety protection, used in cases where a certain part of the chain is uninteresting / unconstrained
        if request_resources is None:
            return None
        max_per_unit = self.Transform.get_output_masses(delta_time)
        use_ratio = 0
        for name, resource in request_resources.items():
            use_ratio = max(use_ratio, resource.Mass/max_per_unit[name])
        self.num_mocks = math.ceil(use_ratio)
        # Scale all resources down by the mock ratio
        for name in request_resources:
            request_resources[name].setMass(request_resources[name].Mass / self.num_mocks)
        # Call and capture the underlying transformation
        step_requests = super().request(delta_time, request_resources)
        # Scale power and mass back up, then return
        self.energy_demand *= self.num_mocks
        for name in step_requests:
            step_requests[name].setMass(step_requests[name].Mass * self.num_mocks)
        return step_requests

# This class defines a starting point for a production chain. It contains resources at
# a fixed ratio but unlimited potential supply. Calling request() sets the necessary minimum
# output rate, which is then returned when run() is called
class ResourceDeposit(Process):
    def __init__(self, arg_name="deposit_undefined", arg_resources={},
                 arg_phase='SOLID', arg_temp=mars.temperature, arg_press=mars.pressure):
        super().__init__(arg_name)
        # Populate information on what resources are present in this deposit
        self.ResourceFractions = arg_resources # This should be a dict of Class name: fraction pairs
        self.Phase = arg_phase
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.output_rate = None
        self.RequestWhitelist = list(arg_resources.keys())

    def run(self, delta_time, input_resources):
        # Use the determined output rate to send resources to the next process in the chain
        # input_resources is expected/required to be None
        if self.output_rate is None:
            raise ValueError("Failed to request output rate from deposit {}".format(self.Name))
        if input_resources is not None:
            raise ValueError("Unexpected input resources given to deposit {}".format(self.Name))
        self.energy_demand = 0 # The deposit itself requires no energy to exist
        output_resources = {}
        for resource_name, mass_frac in self.ResourceFractions.items():
            resource_mass = delta_time * self.output_rate * mass_frac
            newClass = getattr(resourceLib, resource_name)
            output_resources[resource_name] = newClass(resource_mass, self.Temperature, self.Pressure, self.Phase)
        return output_resources

    def request(self, delta_time, request_resources):
        # Requests can effectively always be met - determine the correct rate and set the output accordingly
        # Also assume the downstream consumer can handle pressure / temperature changes as needed
        self.output_rate = 0
        for name, request_resource in request_resources.items():
            # TODO: Handle 'ANY' requests _somewhere_ along the chain
            # Will require using transform phases and such
            if name is not 'ANY':
                if name not in self.ResourceFractions:
                    raise ValueError("Requested resource {} not in deposit {}".format(name, self.Name))
                resource_target_rate = request_resource.Mass / (delta_time*self.ResourceFractions[name])
                self.output_rate = max(self.output_rate, resource_target_rate)
        self.energy_demand = 0 # The deposit itself requires no energy to exist
        return None # No further requests are needed in the processing chain

# This class defines an end point for a production chain. It requests resources at
# a fixed ratio and specified demand. Calling request() sets these parameters, while run()
# stores the process input at the specified mass fraction and puts the rest in overage
class ResourceDepot(Process):
    def __init__(self, arg_name="depot_undefined", arg_resources={},
                 arg_phase='LIQUID', arg_temp=None, arg_press=None, arg_mass=None):
        super().__init__(arg_name)
        # Populate information on what resources will be present in the depot
        self.ResourceFractions = arg_resources # This should be a dict of Class name: fraction pairs
        self.Phase = arg_phase
        self.Temperature = arg_temp
        self.Pressure = arg_press
        self.request_mass = arg_mass
        self.Contents = None # This is where end products are populated
        self.Whitelist = list(arg_resources.keys())

    def run(self, delta_time, input_resources):
        # Store resources only according to the specified mass fractions
        # TODO: Allow for an any/none option?
        if self.request_mass is None:
            raise ValueError("Failed to specify request mass from depot {}".format(self.Name))
        for name in self.ResourceFractions:
            if name not in input_resources:
                raise ValueError("Depot {} not provided with requested resource {}".format(name))
            if self.Phase != input_resources[name].Phase:
                raise ValueError("Depot {} given resource {} with incorrect phase".format(self.Name, name))
        # Update pressures and temperatures as needed
        self.energy_demand = 0
        self.configureInputs(input_resources)
        # Determine the correct amount of each resource to store
        input_masses = {name: resource.Mass for name, resource in input_resources.items() if name in self.ResourceFractions}
        use_mTot = 100*(self.request_mass)**2 # Choose a starting value so high no overage would ever be likely to exceed it
        for name, mass in input_masses.items():
            use_mTot = min(use_mTot, mass/self.ResourceFractions[name])
        # Subtract mass from inputs and place into Contents; put what remains into Overage
        self.Contents = {}
        self.Overage = {}
        for name, input_resource in input_resources.items():
            if name not in self.ResourceFractions:
                self.Overage[name] = input_resource
            else:
                mass_removed = use_mTot*self.ResourceFractions[name]
                # Account for floating point error - if 99.999% of an input resource has been used, the entire resource has been used
                if not abs(1-(input_resource.Mass/mass_removed)) <= ZERO_TOL:
                    input_resource.setMass(input_resource.Mass - mass_removed)
                    self.Overage[name] = input_resource
                resourceType = getattr(resourceLib, name)
                self.Contents[name] = resourceType(mass_removed, input_resource.Temperature, input_resource.Pressure, self.Phase)
        return None # This indicates the end of the running chain

    def request(self, delta_time, request_resources):
        # Use the pre-set rate to request resources from the next process in the chain
        if self.request_mass is None:
            raise ValueError("Failed to specify request mass from depot {}".format(self.Name))
        if request_resources is not None:
            # TODO: may change this later to allow more branching resource paths
            raise ValueError("Unexpected resource request given to depot {}".format(self.Name))
        request_resources = {}
        for resource_name, mass_frac in self.ResourceFractions.items():
            resource_mass = self.request_mass * mass_frac
            newClass = getattr(resourceLib, resource_name)
            request_resources[resource_name] = newClass(resource_mass, self.Temperature, self.Pressure, self.Phase)
        self.energy_demand = 0 # Depots request no energy, but may use energy to change resource temperature / pressure as needed
        return request_resources
