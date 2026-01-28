import numpy as np
import pandas as pd
import os



# Load Demand
demand_df = pd.read_excel("sensors_loops_amsterdam_data.xlsx")
demand_df["Sensor_ID"] = demand_df["Volgnummer"].astype(str) + "_" + demand_df["ID"].astype(str)
demand_df = demand_df[["Sensor_ID", "time", "flow", "speed"]]

# Load Real Speed Profile
# times = [i for i in range(0,24)]
real_speed_df = []
real_flow_df = []
log_files = os.listdir("logs")
for file in log_files:
    f = open("logs/"+file, "r")
    content = f.read()
    f.close()
    content = content.split("<detector xmlns:xsi")[1]
    content = content.split(".xsd\">")[1]
    content = content.split("</detector>")[0]
    lines = content.split("\n")
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if len(line)>0]
    times = [int(float(line.split("begin=\"")[1].split("\"")[0])/3600) for line in lines]
    flows = [float(line.split("flow=\"")[1].split("\"")[0]) for line in lines]
    speeds = [float(line.split("speed=\"")[1].split("\"")[0]) for line in lines]
    for idx in range(0, len(speeds)):
        real_speed_df.append([times[idx], speeds[idx], file.split(".xml")[0]])
    for idx in range(0, len(speeds)):
        real_flow_df.append([times[idx], flows[idx], file.split(".xml")[0]])
        
real_speed_df = pd.DataFrame(real_speed_df, columns=["time", "speed", "file"])
real_speed_df = real_speed_df[real_speed_df["speed"] != -1]
real_speed_df["Sensor_ID"] = real_speed_df["file"].str.rsplit("_", n=1).str[0]
real_speed_df = real_speed_df.drop(columns=["file"])
real_speed_df = real_speed_df.groupby(["time", "Sensor_ID"], as_index=False)["speed"].mean()
real_speed_df["time"] = real_speed_df["time"]+1

real_flow_df = pd.DataFrame(real_flow_df, columns=["time", "flow", "file"])
real_flow_df = real_flow_df[real_flow_df["flow"] != -1]
real_flow_df["Sensor_ID"] = real_flow_df["file"].str.rsplit("_", n=1).str[0]
real_flow_df = real_flow_df.drop(columns=["file"])
real_flow_df = real_flow_df.groupby(["time", "Sensor_ID"], as_index=False)["flow"].mean()
real_flow_df["time"] = real_flow_df["time"]+1

comparison_df = demand_df.merge(real_speed_df, on=["time", "Sensor_ID"], how="left")
comparison_df = comparison_df.merge(real_flow_df, on=["time", "Sensor_ID"], how="left")
comparison_df = comparison_df.dropna()
comparison_df_agg = comparison_df.groupby(["time"], as_index=False)[["flow_x", "flow_y", "speed_x", "speed_y"]].mean()
