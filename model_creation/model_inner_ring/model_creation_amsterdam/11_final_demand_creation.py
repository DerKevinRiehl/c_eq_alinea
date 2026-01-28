import numpy as np
import pandas as pd


# Load Demand File
f = open("8_Routes.rou.xml", "r")
content = f.read()
f.close()
demand_file = content.split("\t<!-- Define Vehicles Types-->")[0]

# Load Demand
demand_df = pd.read_excel("10_route_demand.xlsx")

# Load Vehicle Types
f = open("11_template_vehicle_types.txt", "r")
content = f.read()
f.close()
vehicle_types = content

# this needs to be optimized that observed speed pattern matches real speed pattern / congestion
# Vehicle Type Shares
car_share = 0.844 
mot_share = 0.071
trans_share = 0.075
truck_share = 0.003 + 0.007
vehicle_type_shares = {
    "car_aggr1": 0.2 * car_share,
    "car_aggr2": 0.2 * car_share,
    "car_aggr3": 0.2 * car_share,
    "car_aggr4": 0.2 * car_share,
    "car_aggr5": 0.2 * car_share,
    
    "mot_aggr1": 0.2 * mot_share,
    "mot_aggr2": 0.2 * mot_share,
    "mot_aggr3": 0.2 * mot_share,
    "mot_aggr4": 0.2 * mot_share,
    "mot_aggr5": 0.2 * mot_share,
    
    "transporter_aggr1": 0.2 * trans_share,
    "transporter_aggr2": 0.2 * trans_share,
    "transporter_aggr3": 0.2 * trans_share,
    "transporter_aggr4": 0.2 * trans_share,
    "transporter_aggr5": 0.2 * trans_share,
    
    "truck_aggr1": 0.2 * truck_share,
    "truck_aggr2": 0.2 * truck_share,
    "truck_aggr3": 0.2 * truck_share,
    "truck_aggr4": 0.2 * truck_share,
    "truck_aggr5": 0.2 * truck_share,
}

DEMAND_SCALE_FACTOR = {
     0: 1.00,
     1: 1.00,
     2: 1.00,
     3: 1.00,
     4: 1.00,
     5: 1.00,
     6: 1.00,
     7: 1.00,
     8: 0.75, 
     9: 0.10,
    10: 0.25, 
    11: 0.52, 
    12: 0.60, 
    13: 0.55, 
    14: 0.62,
    15: 0.57,
    16: 0.58,
    17: 0.01, #
    18: 0.03,
    19: 0.03, 
    20: 0.25,
    21: 0.35, 
    22: 0.35,
    23: 0.35,
}

# Create Final Demand Final
final_demand = demand_file
final_demand += vehicle_types
final_demand += "\n\t<!-- Flows -->\n"

# Scale flow and filter rows where flow > 0
demand_df["scaled_flow"] = demand_df["flow"] * demand_df["time"].map(DEMAND_SCALE_FACTOR)
filtered_demand_df = demand_df[demand_df["scaled_flow"] > 0]

# Create a function to generate the flow lines
def generate_flow_lines(row):
    flow_lines = []
    for vehicle_type, share in vehicle_type_shares.items():
        specific_flow = (row["scaled_flow"] * share) / 3600
        new_line = (
            f'\t<flow id="flow_{row["route"]}_{row["time"]}_{vehicle_type}" '
            f'departLane="best" type="{vehicle_type}" probability="{specific_flow}" '
            f'route="{row["route"]}" begin="{row["time"] * 3600}" '
            f'end="{(row["time"] + 1) * 3600}"> </flow>\n'
        )
        flow_lines.append(new_line)
    return flow_lines

# Apply the function to each row and flatten the results
final_demand_list = filtered_demand_df.apply(generate_flow_lines, axis=1).explode().tolist()

# Join all lines into a single string
final_demand += "".join(final_demand_list)


f = open("demand_model_amsterdam.rou.xml", "w+")
f.write(final_demand)
f.close()


