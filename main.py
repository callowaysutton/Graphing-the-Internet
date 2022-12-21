import requests
import tqdm
import gzip
import shutil
from tqdm import tqdm
from pyvis.network import Network
# import pyjion
import csv
# pyjion.enable()

MAX = 10_000

def downloadData(link):
    file_name = "tmp"
    with open(file_name, "wb") as f:
        response = requests.get(link, stream=True)
        total_length = response.headers.get('content-length')

        if total_length is None: # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in tqdm(response.iter_content(chunk_size=1024), total=((total_length/1024)+1)):
                dl += len(data)
                f.write(data)

def generateIPs(start, end):
    import socket, struct
    start = struct.unpack('>I', socket.inet_aton(start))[0]
    end = struct.unpack('>I', socket.inet_aton(end))[0]
    return [socket.inet_ntoa(struct.pack('>I', i)) for i in range(start, end)]

def getIPSize(ip1,ip2):
    import ipaddress
    ip1 = int(ipaddress.IPv4Address(ip1))
    ip2 = int(ipaddress.IPv4Address(ip2))
    return (ip2-ip1)+1

def main():
    print("Organizing Data...")
    table = []
    with open("data", 'r') as file:
        count = 0
        file = file.readlines()
        for line in tqdm(file):
            if count < MAX:
                formatted = line.split("\t")
                if formatted[2] != '0':
                    formatted = [i.strip() for i in formatted]
                    # ips = generateIPs(formatted[0], formatted[1]) # System needs 192GB of RAM Minimum
                    table.append((formatted[4],formatted[0], getIPSize(formatted[0],formatted[1]), formatted[3]))
                    count += 1
    
    print("Writing Data into CSV...")
    with open("output.csv", "w", encoding="UTF8", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(["from", "to", "weight", "country"])
        for line in tqdm(table, total=len(table)):
            writer.writerow([line[1], line[0], line[2], line[3]])

    print("Generating Network...")
    net = Network(height="100%", width="100%", bgcolor="#222222", font_color="white")

    # set the physics layout of the network
    net.barnes_hut()
    net.toggle_physics(False)
    
    edge_data = zip([i[1] for i in table], [i[0] for i in table], [i[2] for i in table], [i[3] for i in table])

    print("Constructing Nodes, Edges and Weights...")
    for e in tqdm(edge_data, total=len(table)):
        src = e[0]
        dst = (str)(e[1])
        w = e[2]
        c = e[3]

        if c == 'US':
            newColor = "grey"
        else:
            newColor = "blue"

        net.add_node(src, src, title=src, color = newColor)
        net.add_node(dst, dst, title=dst, color = newColor)
        net.add_edge(src, dst, value=w)

    neighbor_map = net.get_adj_list()

    print("Adding finishing touches...")
    for node in net.nodes:
        node["title"] += " Neighbors:<br>" + "<br>".join(neighbor_map[node["id"]])
        node["value"] = len(neighbor_map[node["id"]])

    print("Exporting to HTML...")
    net.show("index.html")

if __name__ == "__main__":
    main()
