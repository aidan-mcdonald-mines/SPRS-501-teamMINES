# This file defines a class for managing plant models consisting of a series of processes
# connecting a deposit to one or more depots.

import mars
import copy
from resources import *
from complex_process import *
from processes import *

DEBUG_PRINT = False

# Sample definition dictionary. TODO: remove when fully deprecated
sample_def = {
    'Basic_Regolith': {
        'Model': ResourceDeposit('Basic_Regolith', {'Mars_Regolith': 0.95, 'Water': 0.05}, 'SOLID'),
    },
    'Mars_Atmosphere': {
        'Model': ResourceDeposit('Mars_Atmosphere', mars.atmospheric_composition, 'GAS', mars.temperature, mars.pressure),
    },
    'Crushing': {
        'Model': Regolith_Pulverization(), 'From': ['Basic_Regolith']
    },
    'Heating': {
        'Model': Water_Sublimation(), 'From': ['Crushing']
    },
    'Bagging': {
        'Model': Regolith_Bagging(), 'From': ['Heating']
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

# TODO: Add support for multiple input sources to a process
class ISRUPlant():
    def __init__(self, model_definitions={}):
        # Class parameters used in processing and post-processing
        self.projected_energy = 0
        self.actual_energy = 0
        self.baseline_requests = {}
        self.input_consumed = {}
        self.output_produced = {}
        self.overages = {}
        # Base dictionaries for reference
        self.Deposits = {}
        self.Depots = {}
        self.Chain = {}
        # Copy and parse definitions into a doubly-linked list
        for key, data in model_definitions.items():
            model = data['Model']
            # Note deposits and depots separately for ease of post processing
            if isinstance(model, ResourceDeposit):
                self.Deposits[key] = model
            elif isinstance(model, ResourceDepot):
                self.Depots[key] = model
        self.Chain = model_definitions
        # Populate double-linkage information
        for key, data in self.Chain.items():
            if 'From' not in data:
                data['From'] = None
            else:
                for backlink in data['From']:
                    if backlink not in self.Chain:
                        raise ValueError("Found link to unknown model {}".format(backlink))
                    new_data = self.Chain[backlink]
                    if 'To' not in new_data:
                        new_data['To'] = []
                    new_data['To'].append(key)
        for key, data in self.Chain.items():
            if 'To' not in data:
                data['To'] = None


    def setup(self, requested_outputs, delta_t):
        # Runs through the plant chain backwards via process request() functions.
        # Necessary setup to execute the plant
        # Reset configuration parameters
        self.projected_energy = 0
        self.baseline_requests = {}
        for name, deposit in self.Deposits.items():
            deposit.output_rate = None
        # Requested_outputs should be a dictionary of the form {depotName: massRequest}
        for depot, mass in requested_outputs.items():
            if depot not in self.Depots:
                raise ValueError("Given unknown depot name {}".format(depot))
            self.Depots[depot].request_mass = mass

        # Set up chain for iteration
        for process in self.Chain:
            if self.Chain[process]['To'] is None:
                self.Chain[process]['Ready'] = True
            else:
                self.Chain[process]['Ready'] = False
            self.Chain[process]['Run'] = False
        process_outstanding = list(self.Chain.keys())

        # Iterate through the chain - run what is ready, then update new processes to run
        # If we ever go through the whole loop without enabling a new process, throw an error
        while len(process_outstanding) > 0:
            run_processes = []
            for process in process_outstanding:
                if self.Chain[process]['Ready']:
                    model = self.Chain[process]['Model']
                    requested_resources = None
                    if self.Chain[process]['To'] is not None:
                        requested_resources = {}
                        for downstream_process in self.Chain[process]['To']:
                            # TODO: Handle conflicts between downstream process requests?
                            if self.Chain[downstream_process]['Resource_Request'] is not None:
                                if len(self.Chain[downstream_process]['From']) > 1:
                                    # TODO: add logic to detect if a request goes untended at a split like this
                                    use_requests = {name: resource for name, resource in self.Chain[downstream_process]['Resource_Request'].items() if name in model.RequestWhitelist}
                                    requested_resources = requested_resources | use_requests
                                else:
                                    requested_resources = requested_resources | self.Chain[downstream_process]['Resource_Request']
                    # Note when we derive a starting resource quantity request
                    if process in self.Deposits:
                        self.baseline_requests[process] = requested_resources
                    #print(process)
                    self.Chain[process]['Resource_Request'] = model.request(delta_t, requested_resources)
                    #print("{} requested {}".format(process, self.Chain[process]['Resource_Request']))
                    self.Chain[process]['Energy_Request'] = model.energy_demand
                    self.Chain[process]['Run'] = True
                    self.projected_energy += model.energy_demand
                    run_processes.append(process)
            if len(run_processes) < 1:
                raise Exception("Plant failed to execute any new processes. Dead end in chain encountered")
            for process in run_processes:
                process_outstanding.remove(process)

            for process in process_outstanding:
                readyToRun = True
                for downstream_process in self.Chain[process]['To']:
                    if not self.Chain[downstream_process]['Run']:
                        readyToRun = False
                self.Chain[process]['Ready'] = readyToRun

        # When the request chain is complete, confirm all Deposits have received requests
        for name, deposit in self.Deposits.items():
            if deposit.output_rate is None:
                raise ValueError("Deposit {} received no output request".format(name))

        # Finally, convert energy to power
        self.projected_power = self.projected_energy / delta_t


    def run(self, delta_t):
        # Given known targets configured via setup(), execute the plant.
        # Reset configuration parameters
        self.actual_energy = 0
        self.input_consumed = {}
        self.output_produced = {}
        self.overages = {}

        # Set up chain for iteration
        for process in self.Chain:
            if self.Chain[process]['From'] is None:
                self.Chain[process]['Ready'] = True
            else:
                self.Chain[process]['Ready'] = False
            self.Chain[process]['Run'] = False
        process_outstanding = list(self.Chain.keys())

        # Iterate through the chain - run what is ready, then update new processes to run
        # If we ever go through the whole loop without enabling a new process, throw an error
        while len(process_outstanding) > 0:
            run_processes = []
            for process in process_outstanding:
                if self.Chain[process]['Ready']:
                    model = self.Chain[process]['Model']
                    input_resources = None
                    if self.Chain[process]['From'] is not None:
                        input_resources = {}
                        source_mapping = {}
                        for upstream_process in self.Chain[process]['From']:
                            unique_inputs = self.Chain[upstream_process]['Output_Resources']
                            # TODO: handle collisions?
                            for name in unique_inputs:
                                source_mapping[name] = upstream_process
                            if self.Chain[process]['Model'].Filter:
                                # Only pass along the resources allowed by the transform
                                filtered_resources = {name: resource for name, resource in unique_inputs.items() if name in model.Whitelist}
                                input_resources = input_resources | filtered_resources
                                # Also remove those resources from the output buffer to clearly define the overage at the end
                                for name in filtered_resources:
                                    del self.Chain[upstream_process]['Output_Resources'][name]
                            # Edge case: mix of filtered and non-filtered processes receiving from the same node
                            # If so, non-filtered process calculates a "negative whitelist" and uses that
                            # Of course, this means two non-filtered processes cannot receive from the same node
                            elif len(self.Chain[upstream_process]['To']) > 1:
                                blacklist = []
                                for output in self.Chain[upstream_process]['To']:
                                    if output != process:
                                        blacklist += self.Chain[output]['Model'].Whitelist
                                # Only pass along the resources allowed by the blacklist
                                filtered_resources = {name: resource for name, resource in unique_inputs.items() if name not in blacklist}
                                input_resources = input_resources | filtered_resources
                                # Also remove those resources from the output buffer
                                for name in filtered_resources:
                                    del self.Chain[upstream_process]['Output_Resources'][name]
                            else:
                                input_resources = input_resources | self.Chain[upstream_process]['Output_Resources']
                                self.Chain[upstream_process]['Output_Resources'] = {}
                    self.Chain[process]['Output_Resources'] = model.run(delta_t, input_resources)
                    self.Chain[process]['Energy_Used'] = model.energy_demand
                    self.Chain[process]['Run'] = True
                    # This debug is useful enough it's staying permanently
                    if DEBUG_PRINT:
                        if process in self.Depots:
                            print("Process {} storing:".format(process))
                            for name, resource in self.Chain[process]['Model'].Contents.items():
                                    print("    {} kg of {} ({})".format(round(resource.Mass, 3), name, resource.Phase))
                        else:
                            print("Process {} outputting:".format(process))
                            for name, resource in self.Chain[process]['Output_Resources'].items():
                                    print("    {} kg of {} ({})".format(round(resource.Mass, 3), name, resource.Phase))
                    # Note when we derive an initial or final resource quantity
                    if process in self.Depots:
                        self.output_produced[process] = self.Chain[process]['Model'].Contents
                    if process in self.Deposits:
                        self.input_consumed[process] = copy.deepcopy(self.Chain[process]['Output_Resources'])
                    self.actual_energy += model.energy_demand
                    run_processes.append(process)
            if len(run_processes) < 1:
                raise Exception("Plant failed to execute any new processes. Dead end in chain encountered")
            for process in run_processes:
                process_outstanding.remove(process)

            for process in process_outstanding:
                readyToRun = True
                for upstream_process in self.Chain[process]['From']:
                    if not self.Chain[upstream_process]['Run']:
                        readyToRun = False
                self.Chain[process]['Ready'] = readyToRun

        # At the conclusion of processing, note what overages remain across the system
        for process in self.Chain:
            if process in self.Depots:
                self.overages[process] = self.Chain[process]['Model'].Overage
            elif process not in self.Deposits and len(self.Chain[process]['Output_Resources']) > 0:
                self.overages[process] = self.Chain[process]['Output_Resources']

        # Finally, convert energy to power
        self.actual_power = self.actual_energy / delta_t
        if DEBUG_PRINT:
            print('\n------------------------\n')


    def reportSummary(self):
        dT = self.actual_energy / self.actual_power
        # Data output function - reports on power usage, products, and overages
        print("Used {} kWh at a rate of {} kW".format(round(self.actual_energy/3600000, 3), round(self.actual_power/1000, 3)))
        peak_power = 0
        for p_name, process in self.Chain.items():
            model = process['Model']
            p_power=0
            if model.duty_cycle > 0.0001:
                p_power = round(model.energy_demand/(dT*1000*model.duty_cycle), 3)
            peak_power += p_power
            if isinstance(model, Multiplex):
                print("    Process {} utilized {} kWh at a duty cycle of {} and {} instances -> {} kW".format(p_name, round(model.energy_demand/3600000, 3), round(model.duty_cycle,3), model.num_mocks, p_power))
            else:
                print("    Process {} utilized {} kWh at a duty cycle of {} -> {} kW".format(p_name, round(model.energy_demand/3600000, 3), round(model.duty_cycle,3), p_power))
        print("Peak plant power usage is {} kW".format(peak_power))
        for depot in self.Depots:
            print("Depot {} produced:".format(depot))
            if self.output_produced[depot] is not None:
                for name, output in self.output_produced[depot].items():
                    print("    {} kg of {} ({})".format(round(output.Mass, 3), name, output.Phase))
        if True or DEBUG_PRINT:
            for deposit in self.Deposits:
                print("Extracted from deposit {}:".format(deposit))
                if self.input_consumed[deposit] is not None:
                    for name, input in self.input_consumed[deposit].items():
                        print("    {} kg of {} ({})".format(round(input.Mass, 3), name, input.Phase))
            for process, resources in self.baseline_requests.items():
                print("Process {} reported a starting request for:".format(process))
                for name, resource in resources.items():
                    print("    {} kg of {} ({})".format(round(resource.Mass, 3), name, resource.Phase))
        for process, resources in self.overages.items():
            print("Process {} reported an overage of:".format(process))
            for name, resource in resources.items():
                print("    {} kg of {} ({})".format(round(resource.Mass, 3), name, resource.Phase))


if __name__ =='__main__':
    testPlant = ISRUPlant(sample_def)
    request = {'Fuel_Storage': 1} # 1kg of fuel
    dT = 3600*24 # In one day
    testPlant.setup(request, dT)
    testPlant.run(dT)
    testPlant.reportSummary()
