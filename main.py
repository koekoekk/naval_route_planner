# Importing required modules
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pickle
import random
import fiona
from plot.plot_on_GSHHS import plot_on_gshhs
from initialization import initialization
from shapely.geometry import shape
from shapely.prepared import prep
from nsga_ii import nsga_ii
from classes import Vessel
from rtree import index

random.seed(2)
np.random.seed(2)

# Main program starts here
# Algorithm parameters
pop_size = 40
offspring_size = pop_size
max_gen = 500
start_weight = 40
max_no_impr = 5
max_edge_length = 200  # nautical miles
swaps = ['insert', 'move', 'delete']

# Vessel characteristics
vessel_name = 'Fairmaster'
table = pd.read_excel('C:/dev/data/speed_table.xlsx', sheet_name=vessel_name)
speeds = [round(speed, 1) for speed in table['Speed']]
fuel_rates = {speed: round(table['Fuel'][i], 1) for i, speed in enumerate(speeds)}
vessel = Vessel(vessel_name, speeds, fuel_rates)

# Route characteristics and navigation area
lon_s, lat_s = -5.352121, 48.021295
# lon_e, lat_e = -52.865297, 46.403404
lon_e, lat_e = 53.131866, 13.521350
start = (lon_s, lat_s)
end = (lon_e, lat_e)
shorelines_shp_fp = 'C:/dev/data/gshhg-shp-2.3.7/GSHHS_shp/c/GSHHS_c_L1.shp'
shorelines = fiona.open(shorelines_shp_fp)
polygons = [shape(shoreline['geometry']) for shoreline in iter(shorelines)]
prepared_polygons = [prep(polygon) for polygon in polygons]

# Populate R-tree index with bounds of polygons
rtree_idx = index.Index()
for pos, polygon in enumerate(polygons):
    rtree_idx.insert(pos, polygon.bounds)

# Initialize population
initial_pop = initialization(start, end, vessel, pop_size, rtree_idx, prepared_polygons, max_edge_length, swaps)

population, fronts = nsga_ii(initial_pop, vessel, rtree_idx, prepared_polygons, offspring_size, max_gen,
                             max_edge_length, swaps)

# Get solutions from pareto front
pareto_front = fronts[0]
pareto_solutions = []
for solution_index in pareto_front:
    pareto_solutions.append(population[solution_index])

# Save solutions
output_file_name = 'pareto_solutions01'
with open('output/' + output_file_name, 'wb') as file:
    pickle.dump(pareto_solutions, file)

print('Save to: ' + output_file_name)

plot_on_gshhs(pareto_solutions[0])

#
# # Evaluate pareto objective values
# travel_times = [solution.travel_time for solution in pareto_solutions]
# fuels = [solution.fuel for solution in pareto_solutions]
#
# # Plot the final front
# print('Plotting')
# function1 = [travel_time for travel_time in travel_times]
# function2 = [fuel_consumption for fuel_consumption in fuels]
# plt.xlabel('Travel time [hours]', fontsize=15)
# plt.ylabel('Fuel consumption [tons]', fontsize=15)
# plt.scatter(function1, function2)
plt.show()