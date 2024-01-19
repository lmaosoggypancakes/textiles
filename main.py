import streamlit as st
import streamlit_shadcn_ui as ui
from io import StringIO
from kinparse import parse_netlist
from helpers import * 
import random
from graphs import *
from springs import *
import matplotlib.pyplot as plt
import copy
import time

if 'nodes' not in st.session_state:
    st.session_state['nodes'] = []
nodes = st.session_state['nodes'] 
connections = []

st.set_page_config(layout="wide")
st.sidebar.write("# KiCad :3")
file = st.sidebar.file_uploader("Upload your KiCad schematic netlist")
if file is not None:
    data = file.read().decode("utf-8")
    netlist = parse_netlist(data)
    # create nodes
    if len(nodes) == 0: 
        for part in netlist.parts:
            x = random.random()*100+10
            y = random.random()*100
            nodes.append(PhysicalNode(x, y, part.ref))
    with st.container():

        # refuse larger schematics for now
        if len(netlist.parts) > 10 or len(netlist.nets) > 10:
            st.write("""## Schematic too big </3""")
            exit()
        st.write("""## Awesome! Here's your netlist: """)
        st.write("""### Parts""")
        
        for part in netlist.parts:
            st.write(f"""- ({part.ref}) {part.name}, {part.desc}""")
        st.write("""### Connections""")
        for connection in netlist.nets:
            if len(connection.pins) == 2:
                st.write(f"""- {connection.name}, {connection.pins[0].ref} <    > {connection.pins[1].ref}""")
            elif len(connection.pins) == 1:
                st.write(f"""- {connection.name}, {connection.pins[0].ref} (OPEN)""")
        st.divider()
        stretchification = ui.slider(default_value=[4], min_value=1, max_value=18, step=1, label="Stretchification", key="slider1")
        st.write(f"### {stretchification[0]}")
        # messing around with this for a bit
        # if n = stretchification on a given connection of length x, we convert the straight line to an equation of y=sin(nt), 0<=t<=x
        # given y=sin(nt) which is continous, to convert to point-to's we sample 2n-times (peak-to-peak), so ~~~ becomes /\/\/\/\/\/\/\/\
        # how do we determine x? for now, arbitrarily choose x as some fixed constant for all connections (hopefully i can find someway to get the connection length/direction)
        # we can try sampling more for a more continous line, however
        # TODO: given this, draw and display the SVG file
        if st.button("Optimize"):
            with st.spinner("Calculating"):
                best_energy = float("inf")
                best_nodes = []
                best_connections = []
                for t in range(100):
                    new_nodes = copy.deepcopy(nodes)
                    new_connections = []
                    for conn in netlist.nets:
                        if len(conn.pins) == 2:
                            p1 = list(filter(lambda x: x.ref == conn.pins[0].ref,new_nodes))[0]
                            p2 = list(filter(lambda x: x.ref == conn.pins[1].ref,new_nodes))[0]
                            c = PhysicalConnection(p1,p2,conn.code)
                            new_connections.append(c)

                    for _ in range(t):
                        for node in new_nodes:  
                            connected = PhysicalConnection.get_connections(node, new_connections)
                            forces = list(map(lambda x: x.spring_force_vector(node), connected))
                            node.next_state(forces)

                    energy = total_energy(new_connections)
                    if energy < best_energy:
                        best_energy = energy
                        best_nodes = new_nodes
                        best_connections = new_connections
                    
                for node in best_nodes:
                    plt.text(node.x, node.y+2,  node.ref)
                for c in best_connections:
                    plt.plot((c.one.x,c.two.x), (c.one.y,c.two.y), color='blue')

                x_points = list(map(lambda x: x.x, best_nodes))
                y_points = list(map(lambda y: y.y, best_nodes))
                # Plotting a line
                # Plotting points
                plt.scatter(x_points, y_points, color='red', label='Components')
                # plt.axis((min(x_points)-20,max(x_points)+20,min(y_points)-20,max(y_points)+20))
                # plt.plot(x_points, y_points, color='blue', linestyle='dashed', label='Line')
                # Adding labels and a legend
                fig = st.pyplot(plt,use_container_width=False)
                st.write(f"## Best energy: {best_energy} J")

        if st.button("Simulate"):
            t = st.slider('Time (ms)', 0, 100, 0)  
            nodes_copied = copy.deepcopy(nodes)
            connections_copied = []
            for conn in netlist.nets:
                if len(conn.pins) == 2:
                    p1 = list(filter(lambda x: x.ref == conn.pins[0].ref,nodes_copied))[0]
                    p2 = list(filter(lambda x: x.ref == conn.pins[1].ref,nodes_copied))[0]
                    c = PhysicalConnection(p1,p2,conn.code)
                    connections_copied.append(c)
            
            for _ in range(t):
                for node in nodes_copied:  
                    connected = PhysicalConnection.get_connections(node, connections_copied)
                    forces = list(map(lambda x: x.spring_force_vector(node), connected))
                    node.next_state(forces)

            print(nodes_copied)
            for node in nodes_copied:
                plt.text(node.x, node.y+2,  node.ref)
                # pass
            for c in connections_copied:
                plt.plot((c.one.x,c.two.x), (c.one.y,c.two.y), color='blue')

            st.write(f"### Graph energy: {round(total_energy(connections_copied),2)}J")
            x_points = list(map(lambda x: x.x, nodes_copied))
            y_points = list(map(lambda y: y.y, nodes_copied))
            # Plotting a line
            # Plotting points
            plt.scatter(x_points, y_points, color='red', label='Components')
            # plt.axis((min(x_points)-20,max(x_points)+20,min(y_points)-20,max(y_points)+20))
            # plt.plot(x_points, y_points, color='blue', linestyle='dashed', label='Line')
            # Adding labels and a legend
            fig = st.pyplot(plt,use_container_width=False, clear_figure=True)
    
        # Display the graph
        
        # with st.spinner("Stretchifying..."):
        #     col1,col2 = st.columns(2)
        #     for i, connection in enumerate(netlist.nets):
        #         if len(connection.pins) == 2:
        #             svg = create_n_zigzag(stretchification[0], connection.pins[0].ref, connection.pins[1].ref)
        #             if i % 2 == 0:
        #                 col1.image(str(svg), use_column_width="always")
        #             else: 
        #                 col2.image(str(svg), use_column_width="always") 


