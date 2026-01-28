# #############################################################################
# ## DESCRIPTION ##############################################################
# #############################################################################
"""
This script determines all unique sensors and matches the position of sensors with edges of the network.
"""

# #############################################################################
# ## IMPORTS ##################################################################
# #############################################################################
import pandas as pd
import os
import sumolib
import numpy as np




# #############################################################################
# ## PARAMETERS ###############################################################
# #############################################################################
folder_path = "../download_loops_amsterdam"
network_path = "osm_reduced_kevin.net.xml"
sensor_information_output = "sensors_loops_amsterdam_info.xlsx"
sensor_data_output = "sensors_loops_amsterdam_data.xlsx"




# #############################################################################
# ## METHODS ##################################################################
# #############################################################################
def load_sensors_from_file(folder_path, sensor_file, network_path):
    df_tbl = pd.read_excel(folder_path+"/"+sensor_file, sheet_name="Overzicht")
    # Find rows containing "Volgnummer"
    matches = df_tbl.isin(["Volgnummer"]).any(axis=1)
    matching_rows = df_tbl[matches]
    matching_idx = matching_rows.index[0]
    # Cut unnecessary part away
    df_tbl = df_tbl.iloc[matching_idx:]
    df_tbl.columns = df_tbl.iloc[0]  # Extract first row values
    df_tbl = df_tbl[1:].reset_index(drop=True)  # Remove first row and reset index
    df_tbl["file"] = sensor_file
    # calculate sumo coordinates
    sumo_net = sumolib.net.readNet(network_path)  # Pfad zur .net.xml-Datei
    df_tbl[['sumo_x', 'sumo_y']] = df_tbl.apply(lambda row: convert_to_sumo_coords(row, sumo_net), axis=1)
    # calculate edge of sensor
    df_tbl['sumo_edge'] = df_tbl.apply(lambda row: find_closest_edge(sumo_net, row), axis=1)
    return df_tbl

def convert_to_sumo_coords(row, sumo_net):
    try:
        x, y = sumo_net.convertLonLat2XY(row['Lengtegraad'],row['Breedtegraad'],)
        return pd.Series([x, y])
    except Exception as e:
        print(f"Fehler bei Umrechnung: {e}")
        return pd.Series([None, None])

def find_closest_edge(net, row, radius=100):
    x = row["sumo_x"]
    y = row["sumo_y"]
    # Get neighboring edges within the radius
    edges = net.getNeighboringEdges(x, y, radius)
    if len(edges) > 0:
        # Sort edges by distance and pick the closest one
        distances_and_edges = sorted([(dist, edge) for edge, dist in edges], key=lambda x: x[0])
        dist, closest_edge = distances_and_edges[0]
        return closest_edge.getID()#, dist
    else:
        print("No edges found within the given radius.")
        return "?"#, None
    
def load_sensors(folder_path, network_path):
    sensor_files = os.listdir(folder_path)
    sensor_files = [file for file in sensor_files if file.endswith(".xlsx")]
    sensor_files = [file for file in sensor_files if not file.startswith("~")]
    df_sensors = None
    for sensor_file in sensor_files:
        df_tbl = load_sensors_from_file(folder_path, sensor_file, network_path)
        if df_sensors is None:
            df_sensors = df_tbl.copy()
        else:
            df_sensors = pd.concat((df_sensors, df_tbl))
    return df_sensors

def load_sensor_data(folder_path, network_path):
    df_sensors = load_sensors(folder_path, network_path)
    df_data = None
    for idx, row in df_sensors.iterrows():
        sensor_id = row["ID"]
        file = row["file"]
        times = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        # Load Flows [veh/h]
        df_tbl = pd.read_excel(folder_path+"/"+file, sheet_name="Intensiteit")
        try:
            row_index = df_tbl[df_tbl.apply(lambda row: row.astype(str).str.contains(sensor_id).any(), axis=1)].index[0]
            row_index = row_index+1
            df_tbl = df_tbl.iloc[row_index:row_index+24+1]
            df_tbl.columns = df_tbl.iloc[0]  # Extract first row values
            df_tbl = df_tbl[1:].reset_index(drop=True)  # Remove first row and reset index
            flows = df_tbl["Intensiteit"].tolist()
        except:
            flows = [np.nan for i in range(0,24)]
        # Load Speeds [m/s]
        df_tbl = pd.read_excel(folder_path+"/"+file, sheet_name="Gemiddelde snelheid")
        try:
            row_index = df_tbl[df_tbl.apply(lambda row: row.astype(str).str.contains(sensor_id).any(), axis=1)].index[0]
            row_index = row_index+1
            df_tbl = df_tbl.iloc[row_index:row_index+24+1]
            df_tbl.columns = df_tbl.iloc[0]  # Extract first row values
            df_tbl = df_tbl[1:].reset_index(drop=True)  # Remove first row and reset index
            speeds = (df_tbl["Gemiddelde snelheid"]/3.6).tolist()
        except:
            speeds = [np.nan for i in range(0,24)]
        data = pd.DataFrame(data={"time": times, "flow": flows, "speed": speeds})
        data["Volgnummer"] = row["Volgnummer"]
        data["ID"] = row["ID"]
        data = data[["Volgnummer", "ID", "time", "flow", "speed"]]
        if df_data is None:
            df_data = data.copy()
        else:
            df_data = pd.concat((df_data, data))
    return df_sensors, df_data




# #############################################################################
# ## MAIN LOGIC ###############################################################
# #############################################################################

df_sensors, df_data = load_sensor_data(folder_path, network_path)
df_sensors.to_excel(sensor_information_output)
df_data.to_excel(sensor_data_output)
