from svg import SVG
from embroidery import export_svg_to_processing, export_svg_to_vp3
from helpers import create_r_zigzag
import math

def generate_swatches_constant_stretch(num_traces, min_r, max_r):
    # assume each trace takes up max 75 px
    dr = (max_r - min_r) / num_traces
    svg = SVG(600, 100+(num_traces/2)*600)
    for i in range(num_traces):
        r = min_r + i*dr
        if i % 2 == 0:
            if i == 0:
                create_r_zigzag((150, 50), (150, 550),r, 20, svg) # 1500/2 = 150mm = 15cm
            else: 
                 create_r_zigzag((150, 150+600*(i-i/2)), (150, 50+600*(i-i/2+1)),r, 20, svg) # 1500/2 = 150mm = 15cm
        else:
           if i == 1:
                create_r_zigzag((450, 50), (450, 550),r, 20, svg) # 1500/2 = 150mm = 15cm
           else:
                create_r_zigzag((450, 150+600*(i-(i+1)/2)), (450, 50+600*(i-(i+1)/2+1)),r, 20, svg) # 1500/2 = 150mm = 15cm

    return svg

if __name__ == "__main__":
    s = generate_swatches_constant_stretch(6, 1, 3)
    
    # export_svg_to_processing(s, "./paths/swatches/with_ratio_megastitch.pde")
    export_svg_to_vp3(s, "./paths/swatches/wensleydale.vp3")

    s.save("./paths/swatches/wensleydale.svg")

    

