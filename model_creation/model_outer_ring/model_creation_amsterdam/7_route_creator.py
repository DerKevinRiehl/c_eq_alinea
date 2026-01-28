# Define Parameters
FLOW_PER_HOUR = 10
FROM_TIME = 0
TO_TIME = 10000
VEHICLE_TYPE = "DEFAULT_TAXITYPE"



# Read duaroute file
fR = open("6_duarouter_trips.xml", "r")
lines = fR.read().split("\n")
fR.close()
lines = [l.strip() for l in lines]


# Print new File
text = ""
text += "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
text += "<routes xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.dlr.de/xsd/routes_file.xsd\">\n"
text += "\t<!-- Routes -->\n"

ctr = 0
while ctr<len(lines):
    line = lines[ctr]
    if line.startswith("<vehicle id=\""):
        route_id = line.split("\"")[1]
        ctr+=1
        line = lines[ctr]
        route_edges = line.split("\"")[1]
        ctr+=1
        text += "\t<route id=\""+route_id+"\" edges=\""+route_edges+"\"/>\n"
    else:
        ctr+=1
        
text += "\n"
text += "\t<!-- Define Vehicles Types-->\n"
text += "\n"
text += "\t<!-- Define Flows -->\n"
text += "</routes>\n"

f = open("8_Routes.rou.xml", "w+")
f.write(text)
f.close()