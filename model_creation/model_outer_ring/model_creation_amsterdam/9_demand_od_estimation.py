# #############################################################################
# ## IMPORTS ##################################################################
# #############################################################################
import pandas as pd
import cvxpy as cp




# #############################################################################
# ## PARAMETERS ###############################################################
# #############################################################################
route_file = "./8_Routes.rou.xml"
network_file = "./osm_reduced_kevin.net.xml"
sensor_file = "./sensors_loops_amsterdam.add.xml"
sensor_data_path = "./sensors_loops_amsterdam_data.xlsx"




# #############################################################################
# ## METHODS ##################################################################
# #############################################################################

def load_routes(route_file):
    f = open(route_file, "r")
    content = f.read()
    f.close()
    lines = content.split("\n")
    lines = [line.strip() for line in lines if line.strip().startswith("<route ")]
    routes = [line.split("id=\"")[1].split("\"")[0] for line in lines]
    lst_edges = [line.split("edges=\"")[1].split("\"")[0] for line in lines]
    lst_edges = [edge.split(" ") for edge in lst_edges]
    edges = {}
    for ctr in range(0, len(routes)):
        edges[routes[ctr]] = lst_edges[ctr]
    return routes, edges

def load_edge_lengths(network_file):
    f = open(network_file, "r")
    content = f.read()
    f.close()
    parts = content.split("</edge>")[:-1]
    parts[0] = "<edge "+parts[0].split("<edge ")[1]
    edge_part_ids = [part.split("id=\"")[1].split("\"")[0] for part in parts]
    edge_lengths = {}
    for edge_ctr in range(0, len(edge_part_ids)):
        edge = edge_part_ids[edge_ctr]
        part = parts[edge_ctr]
        edge_lengths[edge] = float(part.split("length=\"")[1].split("\"")[0])
    return edge_lengths

def load_route_lengths(route_edges, network_file):
    edge_lengths = load_edge_lengths(network_file)
    route_lengths = {}
    for route in route_edges:
        lst_edges = route_edges[route]
        lst_lengths = [edge_lengths[edge] for edge in lst_edges]
        route_lengths[route] = sum(lst_lengths)
    return route_lengths

def determine_lanefree_sensor_name(sensor):
    if all(not sensor.endswith(f"_L{i}") for i in range(1, 9)):
        return sensor
    else:
        return "_".join(sensor.split("_")[:-1])

def determine_sensor_number_from_name(sensor):
    if len(sensor.split("_"))==2:
        return sensor.split("_")[0].replace("A", "")
    else:
        return sensor.split("_")[1]
    
def load_sensors(sensor_file):
    f = open(sensor_file, "r")
    content = f.read()
    f.close()
    lines = content.split("\n")
    lines = [line.strip() for line in lines if line.strip().startswith("<inductionLoop ")]
    sensors = [line.split("id=\"")[1].split("\"")[0] for line in lines]
    sensors = ["_".join(sensor.split("_")[:-1]) for sensor in sensors]
    lst_sensor_edges = [line.split("lane=\"")[1].split("\"")[0].split("_")[0] for line in lines]
    sensor_edges = {}
    for sensor_ctr in range(0, len(sensors)):
        sensor = sensors[sensor_ctr]
        sensor_clean = determine_lanefree_sensor_name(sensor)
        sensor_edges[sensor_clean] = lst_sensor_edges[sensor_ctr]
    sensors = list(sensor_edges.keys())
    return sensors, sensor_edges

def determine_sensor_routes(route_edges, sensor_edges):
    sensor_routes = {}
    for sensor in sensor_edges:
        sensor_routes[sensor] = []
    for route in route_edges:
        edges = route_edges[route]
        for edge in edges:
            for sensor in sensor_edges:
                if sensor_edges[sensor] == edge:
                    if route not in sensor_routes[sensor]:
                        sensor_routes[sensor].append(route)
    return sensor_routes

def determine_sensor_data_values(sensor_data, sensor_times, time):
    sensor_data_values = {}
    for sensor in sensor_data:
        values = sensor_data[sensor]
        times = sensor_times[sensor]
        try:
            value_at_time = values[times.index(time)]
        except ValueError:
            value_at_time = 0 # unknown vehicles, not appear in data
        sensor_data_values[sensor] = value_at_time
    return sensor_data_values

def determine_solution_to_optimization_problem(sensor_routes, sensor_data_values, routes_all, route_lengths, verbose=False):
    # Define variables: number of vehicles on each route
    route_variables = {route: cp.Variable(nonneg=True) for route in routes_all}
    # Define auxiliary variables for absolute differences
    abs_diff = cp.Variable(len(sensor_routes), nonneg=True)
    # Constraints: Absolute difference between total_count and sensor_data_values[sensor]
    constraints = []
    for sensor_idx, (sensor, routes) in enumerate(sensor_routes.items()):
        total_count = sum(route_variables[route] for route in routes)
        constraints.append(abs_diff[sensor_idx] >= total_count - sensor_data_values[sensor])
        constraints.append(abs_diff[sensor_idx] >= sensor_data_values[sensor] - total_count)
    # for route in routes_all:
    #     constraints.append(route_variables[route] >= 10)
    # Objective function: Minimize total vehicle count and absolute differences
    objective = cp.Minimize(
        cp.sum(list(route_variables.values())) + 
        # Penalization for route length, but this affects the total number of vehicles assigned, therefore
        # small factor like 0.001 or 0.002 to not affect total number of vehicles too much
        0.05 * cp.sum([route_lengths[route] * route_variables[route] for route in routes_all]) +
        10000 * cp.sum(abs_diff))
    # Solve problem
    problem = cp.Problem(objective, constraints)
    problem.solve(verbose=False)
    error = sum(abs_diff.value)
    max_error = max(abs_diff.value)
    total_flow = sum([sensor_data_values[sensor] for sensor in sensor_routes])
    # for sensor_idx, (sensor, routes) in enumerate(sensor_routes.items()):
    #     print(sensor_idx, sensor, abs_diff[sensor_idx].value)
    # import sys
    # sys.exit(0)
    # Extract results
    route_counts = {route: route_variables[route].value for route in routes_all}    
    return route_counts, problem, error, total_flow, max_error




# #############################################################################
# ## MAIN LOGIC ###############################################################
# #############################################################################

    # LOAD INFORMATION
routes_all, route_edges = load_routes(route_file)
route_lengths = load_route_lengths(route_edges, network_file)
sensors, sensor_edges = load_sensors(sensor_file)
sensor_data = pd.read_excel(sensor_data_path)
sensor_routes = determine_sensor_routes(route_edges, sensor_edges)
all_times = sensor_data["time"].unique().tolist()


    # SOLVE OPTIMIZATION PROBLEM FOR EACH TIME
count_df = []
for time in all_times:
    sensor_data_sub = sensor_data[sensor_data["time"]==time].fillna(0)
    sensor_data_values = {}
    for idx, row in sensor_data_sub.iterrows():
        sensor_data_values[str(row["Volgnummer"])+"_"+str(row["ID"])] = row["flow"]
    route_counts, problem, error, total_flow, max_error = determine_solution_to_optimization_problem(sensor_routes, sensor_data_values, routes_all, route_lengths)
    print(time, "Total vehicles assigned: ", sum([route_counts[val] for val in route_counts]))
    print("\t", error/total_flow*100, "%", error, total_flow, max_error)
    for route in route_counts:
        count_df.append([time, route, route_counts[route]])
count_df = pd.DataFrame(count_df, columns=["time", "route", "flow"])
count_df.to_excel("10_route_demand.xlsx")