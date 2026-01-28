# PARAMETERS
# input_file = "xx_trajectory_log_shimaa_mobil_morning.csv"
# output_file = "xx_trajectory_log_relevant_shimaa_mobil_morning.csv"

# input_file = "xx_trajectory_log_shimaa_mobil_evening.csv"
# output_file = "xx_trajectory_log_relevant_shimaa_mobil_evening.csv"

# input_file = "xx_trajectory_log_shimaa_idms_morning.csv"
# output_file = "xx_trajectory_log_relevant_shimaa_idms_morning.csv"

input_file = "xx_trajectory_log_shimaa_combi_morning.csv"
output_file = "xx_trajectory_log_relevant_shimaa_combi_morning.csv"

# DETERMINE RELEVANT EDGES
    # added highway roads from XX_edge_highway_segment_number.csv
relevant_edges = ["1194747958", "128965109", "111873038", "221205619", "859704530", 
                  "1331091276", "221205615", "491590643#0", "1331091275", "221205616#0", 
                  "221205616#1", "221205616#2", "679563339", "679563336", "39911408#0", 
                  "39911408#1", "254282341", "1331091279", "7377811", "7377791", 
                  "1093958473", "7377853", "7376769", "1093958036", "495537084", 
                  "7376543", "7376553", "7042478", "7042483", "495536678", 
                  "7042488", "1093957498", "38524672", "495536350", "7040861#0", 
                  "722735725#0", "722735725#1", "7040879#0", "866749029#1", 
                  "495536083", "7039976", "7039979", "7045330", "495535093", 
                  "495535092", "7045317", "274383441", "1093814683", "495535097", 
                  "7046931", "7046905", "7047904", "7047916", "495530609", 
                  "7047881", "7047901", "7368902", "7368902-AddedOffRampEdge", 
                  "7370135", "1230633238", "7374415", "1230633242", "1359673887", 
                  "7374873", "7381774", "1359673884", "491573236", "76232191", 
                  "491578742", "7381798", "38245925", "491573232", "491574922", 
                  "1269104017", "491586085", "491586092", "7382655", "7382650", 
                  "1092346866", "491586076", "217164331", "7379509", "491592275", 
                  "75919461", "491590649", "1332839356", "48748939"]
    # added the last edge of on-ramps last edge before highway
relevant_edges += ["440995086", "130641962", "1332838359", "7377857#0", "7376540#0",
                   "945278807", "7040871#0", "299606600", "999040451", "479192364",
                   "761269150", "761458301", "7368875", "321003277", "1359673886",
                   "48662559#1", "7381817", "798505000", "7382654#0", "7379529"]
    # added the first edge from off-ramps before highway
relevant_edges += ["75919456", "1354687747", "7377781", "6595423", "7376559", 
                   "7042496", "76025458", "76024917", "7040607", "38572019", "7046900",
                   "1266120160", "7047879", "7047879", "761267546", "1230633240",
                   "1359673883", "1270857679", "1269325984", "75919472", "75919472", 
                   "217164329"]




# FILTER LOG FILE
fR = open(input_file, "r")
fW = open(output_file, "w+")

line = fR.readline()
fW.write(line)
fW.write("\n")

line = fR.readline()
while line!="":
    try:
        edge = line.split(",")[5]
        if edge in relevant_edges:
            fW.write(line)
            fW.write("\n")
    except:
        pass
    line = fR.readline()

fR.close()
fW.close()
