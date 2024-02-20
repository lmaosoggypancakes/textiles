from kinparse import parse_netlist
from helpers import * 
from graphs import *
from springs import *
from processing import *
from typing import Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class File(BaseModel):
    data: str

app = FastAPI()

@app.get("/")
def index():
    return {"data": "lmao"}

@app.post("/parse")
def parse_file(data: File):
    try:
        netlist = parse_netlist(data.data)
        return {
            "file": netlist
        }
    except Exception as e:
        print(f"There was an error: {e}")
        raise HTTPException(status_code=400, detail="File didn't parse successfully. Are you use you uploaded a netlist?")


# st.set_page_config(layout="wide")
# st.sidebar.write("# KiCad :3")
# file = st.sidebar.file_uploader("Upload your KiCad schematic netlist")
# if file is not None:
#     data = file.read().decode("utf-8")
#     netlist = parse_netlist(data)
#     # create nodes
#     radius=100
#     if len(nodes) == 0: 
#         for (i,part) in enumerate(netlist.parts):
#             angle = 2 * math.pi * i/len(netlist.parts)
#             x = 400+radius+math.cos(angle)
#             y = 400+radius+math.cos(angle)
#             nodes.append(PhysicalNode(x, y, part.ref))
#     with st.container():

#         # refuse larger schematics for now
#         if len(netlist.parts) > 10 or len(netlist.nets) > 10:
#             st.write("""## Schematic too big </3""")
#             exit()
#         st.write("""## Awesome! Here's your netlist: """)
#         st.write("""### Parts""")
        
#         for part in netlist.parts:
#             st.write(f"""- ({part.ref}) {part.name}, {part.desc}""")
#         st.write("""### Connections""")
#         for connection in netlist.nets:
#             if len(connection.pins) == 2:
#                 st.write(f"""- {connection.name}, {connection.pins[0].ref} <    > {connection.pins[1].ref}""")
#             elif len(connection.pins) == 1:
#                 st.write(f"""- {connection.name}, {connection.pins[0].ref} (OPEN)""")
#         st.divider()
#         # messing around with this for a bit
#         # if n = stretchification on a given connection of length x, we convert the straight line to an equation of y=sin(nt), 0<=t<=x
#         # given y=sin(nt) which is continous, to convert to point-to's we sample 2n-times (peak-to-peak), so ~~~ becomes /\/\/\/\/\/\/\/\
#         # how do we determine x? for now, arbitrarily choose x as some fixed constant for all connections (hopefully i can find someway to get the connection length/direction)
#         # we can try sampling more for a more continous line, however
#         # TODO: given this, draw and display the SVG file
        
#         optimize, simulate  = st.tabs(["Optimize", "Simulate"])
#         with optimize:
#             if st.button("Shuffle"):
#                 random.shuffle(nodes)
#             with st.spinner("Calculating"):
#                 best_energy = float("inf")
#                 best_nodes = []
#                 best_connections = []
#                 for t in range(100):
#                     new_nodes = copy.deepcopy(nodes)
#                     new_connections = []
#                     for conn in netlist.nets:
#                         if len(conn.pins) == 2:
#                             p1 = list(filter(lambda x: x.ref == conn.pins[0].ref,new_nodes))[0]
#                             p2 = list(filter(lambda x: x.ref == conn.pins[1].ref,new_nodes))[0]
#                             c = PhysicalConnection(p1,p2,conn.code)
#                             new_connections.append(c)

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


