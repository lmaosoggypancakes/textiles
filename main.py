from kinparse import parse_netlist
import math
from helpers import * 
from graphs import *
from springs import *
from embroidery import *
from typing import Dict, List
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from pyparsing.exceptions import ParseException
from fastapi.middleware.cors import CORSMiddleware
from parse_netlist import extract_netlist

class File(BaseModel):
    data: str

class WebSocketPayload(BaseModel):
    label: str
    data: Dict

class Pin(BaseModel):
    ref: str
    num: str

class Net(BaseModel):
    name: str
    code: str
    pins: List[Pin]

class Part(BaseModel):
    ref: str
    value: str
    name: str

class Library(BaseModel):
    name: str
    uri: str

class Netlist(BaseModel):
    # libraries: List[Library]
    parts: List[Part]
    nets: List[Net]

# class Constraint(BaseModel):
    # node: PhysicalNode
    # shape: List
app = FastAPI()

origins = [
        "http://localhost:5173",
        "https://stretchy.soggypancakes.tech"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return {"data": "lmao"}

@app.post("/parse")
def parse_file(data: File) -> Netlist:
    try:
        # netlist = parse_netlist(data.data)
        # nets = list(map(lambda net: {"name": net.name, "code": net.code, "pins": list(map(lambda pin: {"ref": pin.ref, "num": pin.num}, net.pins))}, netlist.nets))
        # parts = list(map(lambda part: {"ref": part.ref, "value": part.value, "name": part.name}, netlist.parts))
        (nets, parts) = extract_netlist(data.data)
        return {
                "nets": nets,
                "parts": parts
        }
    except ParseException as e:
        print(f"There was an error: {e}")
        raise HTTPException(status_code=400, detail="File didn't parse successfully. Are you sure you uploaded a netlist?")


@app.websocket("/session")
async def ws(socket: WebSocket):
    await socket.accept()
    await socket.send_json({"label": "message", "message": "welcome!"})
    nodes: List[PhysicalNode] = []
    connections: List[PhysicalConnection] = []
    netlist = None
    while True:
        payload: WebSocketPayload = await socket.receive_json()
        if payload["label"] == "netlist":
            if netlist:
                socket.send_json({"label": "message", "message": "You have already set your netlist in this transaction."})
            else:
                netlist = payload["data"]
                # create nodes
                radius=150
                if len(nodes) == 0: 
                    for (i,part) in enumerate(netlist["parts"]):
                        angle = 2 * math.pi * i/len(netlist["parts"])
                        x = 100+radius*(1 + math.cos(angle))
                        y = 100+radius*(1 + math.sin(angle))
                        nodes.append(PhysicalNode(x, y, part["ref"]))

                    for conn in netlist["nets"]:
                        for i in range(1, len(conn["pins"])):
                            p1 = list(filter(lambda x: x.ref == conn["pins"][i - 1]["ref"],nodes))[0]
                            p2 = list(filter(lambda x: x.ref == conn["pins"][i]["ref"],nodes))[0]
                            c = PhysicalConnection(p1,p2,conn["code"])
                            connections.append(c)

                await socket.send_json({"label": "graph", "nodes": [node.serialize() for node in nodes], "connections": [c.serialize() for c in connections]})

        elif payload["label"] == "get_graph":
            await socket.send_json({"label": "graph", "nodes": [node.serialize() for node in nodes], "connections": [c.serialize() for c in connections]})

        elif payload["label"] == "with_stretchification":
            points = []
            stretchification = int(payload["stretchification"])
            depth = int(payload["depth"])
            # handle duplicates
            for c in connections:
                x1 = c.one.x + 24*math.cos(c.angle_one)
                y1 = c.one.y + 24*math.sin(c.angle_one)


                x2 = c.two.x + 24*math.cos(c.angle_two)
                y2 = c.two.y + 24*math.sin(c.angle_two)

                points.append(create_r_zigzag((x1,y1), (x2,y2), stretchification, depth))
            await socket.send_json({"label": "paths", "nodes": [node.serialize() for node in nodes], "points": points})
        elif payload["label"] == "after_time":
            time = payload["time"]
            dict_nodes = payload["nodes"]
            new_nodes = list(map(lambda d: PhysicalNode.from_dict(d), dict_nodes))
            new_connections: List[PhysicalConnection] = []
            for conn in netlist["nets"]:
                    if len(conn["pins"]) == 2:
                        p1 = list(filter(lambda x: x.ref == conn["pins"][0]["ref"],new_nodes))[0]
                        p2 = list(filter(lambda x: x.ref == conn["pins"][1]["ref"],new_nodes))[0]
                        c = PhysicalConnection(p1,p2,conn["code"])
                        new_connections.append(c)
            stretchification = int(payload["stretchification"])
            depth = float(payload["depth"])
            constraints = payload["constraints"]
            max_len = max(map(lambda c: c.get_length() ,new_connections))
            for (i, c) in enumerate(constraints):
                constraints[i]["node"] = PhysicalNode.from_dict(constraints[i]["node"])
            if not all([new_nodes, depth]):
                await socket.send_json({"label": "message", "message": "one of the required fields is missing"})
                continue
            for _ in range(time):
                for node in new_nodes:
                    connected = PhysicalConnection.get_connections(node, new_connections)
                    forces = list(map(lambda x: x.spring_force_vector(node), connected))
                    constraint = None
                    for c in constraints:
                        if c["node"] == node:
                            constraint = c
                    
                    node.next_state(forces, constraint)
            # after the sim, create the zigzags
            new_points = []
            grouped = find_duplicate_connections(new_connections)
            for group in grouped:
                arc_offset = (math.pi) / 6*len(grouped)
                for i, conn in enumerate(group):
                    dx = conn.one.x - conn.two.x
                    dy = conn.one.y - conn.two.y
                    angle = math.atan2(dy, dx)

                    x1 = conn.one.x - 24*math.cos(angle+arc_offset*i*sign(dx))
                    y1 = conn.one.y - 24*math.sin(angle+arc_offset*i*sign(dx))

                    x2 = conn.two.x + 24*math.cos(angle-arc_offset*i*sign(dx))                    
                    y2 = conn.two.y + 24*math.sin(angle-arc_offset*i*sign(dx))                    
                    
                    print(f"{stretchification=}")
                    path = create_r_zigzag((x1, y1), (x2, y2), stretchification, depth)
                    new_points.append(path)
            await socket.send_json({"label": "paths", "nodes": [node.serialize() for node in new_nodes], "points": new_points})
        elif payload["label"] == "give_svg_pwease":
            dict_nodes = payload["nodes"]
            new_nodes = list(map(lambda d: PhysicalNode.from_dict(d), dict_nodes))
            points = payload["points"]
            new_connections = []
            for conn in netlist["nets"]:
                    if len(conn["pins"]) == 2:
                        p1 = list(filter(lambda x: x.ref == conn["pins"][0]["ref"],new_nodes))[0]
                        p2 = list(filter(lambda x: x.ref == conn["pins"][1]["ref"],new_nodes))[0]
                        c = PhysicalConnection(p1,p2,conn["code"])
                        new_connections.append(c)
            
            await socket.send_json({"label": "svg", "file": str(render_graph(new_nodes, points))})

        elif payload["label"] == "give_processing_pwease":
            dict_nodes = payload["nodes"]
            points = payload["points"]
            new_nodes = list(map(lambda d: PhysicalNode.from_dict(d), dict_nodes))
            new_connections = []
            for conn in netlist["nets"]:
                    if len(conn["pins"]) == 2:
                        p1 = list(filter(lambda x: x.ref == conn["pins"][0]["ref"],new_nodes))[0]
                        p2 = list(filter(lambda x: x.ref == conn["pins"][1]["ref"],new_nodes))[0]
                        c = PhysicalConnection(p1,p2,conn["code"])
                        new_connections.append(c)
            
            await socket.send_json({
                "label": "processing",
                "file": export_svg_to_processing(render_graph(new_nodes, points))
            }) 
#         # messing around with this for a bit
#         # if n = stretchification on a given connection of length x, we convert the straight line to an equation of y=sin(nt), 0<=t<=x
#         # given y=sin(nt) which is continous, to convert to point-to's we sample 2n-times (peak-to-peak), so ~~~ becomes /\/\/\/\/\/\/\/\
#         # how do we determine x? for now, arbitrarily choose x as some fixed constant for all connections (hopefully i can find someway to get the connection length/direction)
#         # we can try sampling more for a more continous line, however
#         # TODO: given this, draw and display the SVG file
        
#             if st.button("Shuffle"):
#                 random.shuffle(nodes)
#             with st.spinner("Calculating"):
#                 best_energy = float("inf")
#                 best_nodes = []
#                 best_connections = []
#                 for t in range(100):
#                     new_nodes = copy.deepcopy(nodes)
#                     new_connections = []
# 
#                     for _ in range(t):
#                         for node in new_nodes:  
#                             connected = PhysicalConnection.get_connections(node, new_connections)
#                             forces = list(map(lambda x: x.spring_force_vector(node), connected))
#                             node.next_state(forces)

#                     energy = total_energy(new_connections)
#                     if energy < best_energy:
#                         best_energy = energy
#                         best_nodes = new_nodes
#                         best_connections = new_connections
                    
#                 # plt.axis((min(x_points)-20,max(x_points)+20,min(y_points)-20,max(y_points)+20))
#                 # plt.plot(x_points, y_points, color='blue', linestyle='dashed', label='Line')
#                 # Adding labels and a legend
#                 st.write(f"## Best energy: {  round(best_energy)} J")
#                 stretchification = st.slider("Stretchification", value=4, min_value=1, max_value=50, step=1, key="optimize_slider")
#                 zig_size = st.slider("Zigzag size", 1.0, 5.0, 1.0   , 0.1)
#                 rendered = render_graph(best_nodes,best_connections,stretchification,zig_size)
#                 st.image(str(rendered), use_column_width=True)
#                 st.download_button("Download SVG", str(rendered), "text/svg")
#                 st.download_button("Export to PEmbroider", export_svg_to_processing(rendered), "funny.pde")
                

#         with simulate:
#             t = st.slider('Time (ms)', 0, 100, 0)
#             stretchification = st.slider("Stretchification", value=4, min_value=1, max_value=18, step=1, key="simulate_slider")
#             zig_size = st.slider("Zigzag size", 1.0, 5.0, 1.0, 0.1, key="zig_simulate")
#             nodes_copied = copy.deepcopy(nodes)
#             connections_copied = []
#             for conn in netlist.nets:
#                 if len(conn.pins) == 2:
#                     p1 = list(filter(lambda x: x.ref == conn.pins[0].ref,nodes_copied))[0]
#                     p2 = list(filter(lambda x: x.ref == conn.pins[1].ref,nodes_copied))[0]
#                     c = PhysicalConnection(p1,p2,conn.code)
#                     connections_copied.append(c)
            
#             for _ in range(t):
#                 for node in nodes_copied:  
#                     connected = PhysicalConnection.get_connections(node, connections_copied)
#                     forces = list(map(lambda x: x.spring_force_vector(node), connected))
#                     node.next_state(forces)

#             for node in nodes_copied:
#                 plt.text(node.x, node.y+2,  node.ref)
#                 # pass
#             for c in connections_copied:
#                 plt.plot((c.one.x,c.two.x), (c.one.y,c.two.y), color='blue')

#             st.write(f"### Graph energy: {round(total_energy(connections_copied))}J")
#             rendered = render_graph(nodes_copied, connections_copied, stretchification, zig_size)
#             st.image(str(rendered), use_column_width=True)
#         # Display the graph
        
#         # with st.spinner("Stretchifying..."):
#         #     col1,col2 = st.columns(2)
#         #     for i, connection in enumerate(netlist.nets):
#         #         if len(connection.pins) == 2:
#         #             svg = create_n_zigzag(stretchification[0], connection.pins[0].ref, connection.pins[1].ref)
#         #             if i % 2 == 0:
#         #                 col1.image(str(svg), use_column_width="always")
#         #             else: 
#         #                 col2.image(str(svg), use_column_width="always") 


