import streamlit as st
import streamlit_shadcn_ui as ui
from io import StringIO
from kinparse import parse_netlist
from helpers import * 
import uuid
st.set_page_config(layout="wide")
st.sidebar.write("# KiCad :3")
file = st.sidebar.file_uploader("Upload your KiCad schematic netlist")
if file is not None:
    data = file.read().decode("utf-8")
    try:
        netlist = parse_netlist(data)
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
                    st.write(f"""- {connection.name}, {connection.pins[0].ref} <-> {connection.pins[1].ref}""")
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
            with st.spinner("Stretchifying..."):
                col1,col2 = st.columns(2)
                for i, connection in enumerate(netlist.nets):
                    if len(connection.pins) == 2:
                        svg = create_n_zigzag(stretchification[0], connection.pins[0].ref, connection.pins[1].ref)
                        if i % 2 == 0:
                            col1.image(str(svg), use_column_width="always")
                        else: 
                            col2.image(str(svg), use_column_width="always") 
    except Exception as e:

        st.error(f'There is an error: {e}', icon="⚠️")
        
