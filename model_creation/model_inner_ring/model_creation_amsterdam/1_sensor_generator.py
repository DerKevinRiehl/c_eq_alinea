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
sensors_output_file = "sensors_loops_amsterdam.add.xml"




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

def place_e1_sensors_all_lanes(net, x, y, edge_id=None, sensor_prefix="e1_"):
    """
    Places E1 detectors on ALL lanes of the closest edge at position (x,y)
    
    Parameters:
        net: sumolib.net.Net object
        x, y: Coordinates in network space
        edge_id: Optional pre-specified edge ID
        sensor_prefix: Prefix for detector IDs
    
    Returns:
        List of tuples: [(sensor_id, lane_id, lane_pos), ...]
    """
    # 1. Find closest edge if not specified
    if edge_id is None:
        edge, _ = find_closest_edge(net, x, y)
        edge_id = edge.getID()
    else:
        edge = net.getEdge(edge_id)
    
    # 2. Process all lanes
    sensors = []
    for lane in edge.getLanes():
        # Get lane geometry
        shape = lane.getShape(True)
        
        # Find closest point on this specific lane
        lane_pos, _ = sumolib.geomhelper.polygonOffsetAndDistanceToPoint(
            (x, y), 
            shape
        )
        
        if lane_pos < 0 or lane_pos > lane.getLength():
            print("Corrected Invalid position", lane_pos, lane.getLength())
            lane_pos = lane.getLength()*0.9
        
        # Create sensor entry
        sensor_id = f"{sensor_prefix}_{lane.getIndex()}"
        sensors.append(
            (sensor_id, f"{edge_id}_{lane.getIndex()}", lane_pos)
        )
    
    return sensors

def create_e1_xml_str(sensors):
    """
    Generates SUMO additional XML configuration as string
    
    Parameters:
        sensors: List of (sensor_id, lane_id, pos) tuples
    
    Returns:
        str: Valid SUMO additional XML configuration
    """
    xml_lines = []
    for sensor_id, lane_id, pos in sensors:
        if np.random.random() < share_sensors:
            xml_lines.append(
                f'    <inductionLoop id="{sensor_id}" lane="{lane_id}" pos="{pos:.2f}" '
                f'period="3600.0" file="logs/{sensor_id}.xml"/>'
            )    
        else:
            xml_lines.append(
                f'    <inductionLoop id="{sensor_id}" lane="{lane_id}" pos="{pos:.2f}" '
                f'period="3600.0" file="nul"/>'
            )    
            
    return '\n'.join(xml_lines)

def generate_sensor_file(df_sensors, net, output_file):
    sensor_xml = '<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">\n'
    for idx, row in df_sensors.iterrows():
        sensors = place_e1_sensors_all_lanes(net, x=row["sumo_x"], y=row["sumo_y"], edge_id=row["sumo_edge"], sensor_prefix=str(row["Volgnummer"])+"_"+row["ID"])
        sensor_xml += create_e1_xml_str(sensors) + "\n"
    sensor_xml += '</additional>'
    f = open(output_file, "w+")
    f.write(sensor_xml)
    f.close()




# #############################################################################
# ## MAIN LOGIC ###############################################################
# #############################################################################

share_sensors = 0.8

df_sensors = load_sensors(folder_path, network_path)
df_sensors["unique_id"] = df_sensors["Volgnummer"].astype(str)+"_"+df_sensors["ID"].astype(str)
df_sensors = df_sensors.drop_duplicates(subset='unique_id', keep='first')
net = sumolib.net.readNet(network_path)
generate_sensor_file(df_sensors, net, sensors_output_file) 
