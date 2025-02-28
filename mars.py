# This file defines constants related to the physical properties of Mars.
# Utilized where needed throughout the simulation.
# Citations present in comments where needed.

# https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html
surface_gravity = 3.73 # m/s^2

# TODO: Definitely modify these based on time of Martian year, location, etc.
# Need a good data source for that
temperature = -65+273.15 # K
pressure = 610           # Pa

# TODO: Consider even more trace elements?
# TODO: Vary by time or location?
# Photochemistry and stability of the atmosphere of Mars
atmospheric_composition = {
    "Carbon_Dioxide": 0.9532,
    "Nitrogen": 0.027,
    "Argon": 0.016,
    "Oxygen": 0.0013,
    "Carbon_Monoxide": 0.0007,
    "Water": 0.0002
}
