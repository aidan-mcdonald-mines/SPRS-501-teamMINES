from isru_plants import *
from plant_model import *


# The following function executes planned tests for the SPRS501 group project presentation
# Notes to calibrate & scale plant model execution
# Canonical processing window for Martian ISRU fuel plant is 480 days (Kleinhenz et al., "Benefits of Mars ISRU...")
# Requires 29,855 kg of LO2/CH4 fuel at a 3.25:1 ratio (Ibid.) Impulse is ~312 s (QA1)
# Eiskowitz et al. use a dry mass estimate of 6.6mT, which yields a dV of 5.23 km/s .
# LO2/LH2 has an impulse of 450 s (QA1); solving backwards for fuel mass yields 14981 kg (at a 6:1 O2:H2 ratio)
# So an LO2/CH4 plant requires 62.2 kg/day fuel production, while LO2/LH2 only requires 31.2 kg/day
def RunPresentationTests():
    # Set up test constants
    target_lo2_lh2 = 14981 # kg
    target_lo2_ch4 = 29855 # kg
    scaledown_factor = 480 # days

    # Define ISRU plants under test and organize into dicts
    # For now, run on only a subset of the possible combinations
    base_plant_h2 = copy.deepcopy(plant_lo2_lh2)  #| copy.deepcopy(plant_bagging)
    full_plant_h2 = copy.deepcopy(plant_lo2_lh2)  | copy.deepcopy(plant_sinter)
    #metal_plant_h2 = copy.deepcopy(plant_lo2_lh2)  | copy.deepcopy(plant_sinter)
    base_plant_ch4 = copy.deepcopy(plant_lo2_ch4) #| copy.deepcopy(plant_bagging)
    full_plant_ch4 = copy.deepcopy(plant_lo2_ch4) | copy.deepcopy(plant_sinter)
    test_cases = {'base_h2': base_plant_h2, 'full_h2': full_plant_h2, 'base_ch4': base_plant_ch4, 'full_ch4': full_plant_ch4}
    regolith_opts = {'no_ice': regolith_hydrate, 'yes_ice': regolith_icy}

    # Iterate through test cases and record relevant results
    for case_name, case_dict in test_cases.items():
        for reg_name, regolith in regolith_opts.items():
            copy_dict = copy.deepcopy(case_dict)
            copy_dict = SetInputRegolith(copy_dict, regolith, reg_name)
            plant_model = ISRUPlant(copy_dict)
            time_step = 24*60*60 # One day in seconds
            if '_h2' in case_name:
                target_mass = target_lo2_lh2 / scaledown_factor
            else:
                target_mass = target_lo2_ch4 / scaledown_factor
            request = {'Fuel_Storage': target_mass}
            # Execute test
            plant_model.setup(request, time_step)
            plant_model.run(time_step)
            # Print header and results
            print("\n\n------ UUT {} with regolith {} ------".format(case_name, reg_name))
            plant_model.reportSummary()
            #print("\n")


# The following function executes planned tests for the SPRS501 group project final report
def RunReportTests():
    # Set up test constants
    target_lo2_lh2 = 14981 # kg
    target_lo2_ch4 = 29855 # kg
    scaledown_factor = 480 # days

    # Define ISRU plants under test and organize into dicts
    # For now, run on only a subset of the possible combinations
    base_plant_h2 = copy.deepcopy(plant_lo2_lh2)  #| copy.deepcopy(plant_bagging)
    full_plant_h2 = copy.deepcopy(plant_lo2_lh2)  | copy.deepcopy(plant_sinter)
    #metal_plant_h2 = copy.deepcopy(plant_lo2_lh2)  | copy.deepcopy(plant_sinter)
    base_plant_ch4 = copy.deepcopy(plant_lo2_ch4) #| copy.deepcopy(plant_bagging)
    full_plant_ch4 = copy.deepcopy(plant_lo2_ch4) | copy.deepcopy(plant_sinter)
    test_cases = {'base_h2': base_plant_h2, 'full_h2': full_plant_h2, 'base_ch4': base_plant_ch4, 'full_ch4': full_plant_ch4}

    # Iterate through test cases and record relevant results
    for case_name, case_dict in test_cases.items():
        copy_dict = copy.deepcopy(case_dict)
        copy_dict = SetInputRegolith(copy_dict, regolith_icy, 'yes_ice')
        plant_model = ISRUPlant(copy_dict)
        time_step = 24*60*60 # One day in seconds
        if '_h2' in case_name:
            target_mass = target_lo2_lh2 / scaledown_factor
        else:
            target_mass = target_lo2_ch4 / scaledown_factor
        request = {'Fuel_Storage': target_mass}
        # Execute test
        plant_model.setup(request, time_step)
        plant_model.run(time_step)
        # Print header and results
        print("\n\n------ UUT {} ------".format(case_name))
        plant_model.reportSummary()
        #print("\n")

    # Perform the same analysis on the metals plant
    metals_test = copy.deepcopy(plant_metals_base)
    metals_plant = ISRUPlant(metals_test)
    time_step = 24*60*60 # One day in seconds
    target_mass = 25000/365 # Rate of 25 mT/year
    request = {'Metals_Storage': target_mass}
    # Execute test
    metals_plant.setup(request, time_step)
    metals_plant.run(time_step)
    # Print header and results
    print("\n\n------ UUT metals_only ------")
    metals_plant.reportSummary()

    metals_addon_test = copy.deepcopy(plant_metals_base) | copy.deepcopy(plant_metals_refine_sideproducts)
    metals_addon_plant = ISRUPlant(metals_addon_test)
    # Execute test
    metals_addon_plant.setup(request, time_step)
    metals_addon_plant.run(time_step)
    # Print header and results
    print("\n\n------ UUT metals_full ------")
    metals_addon_plant.reportSummary()



if __name__ == '__main__':
    RunReportTests()
