from svg import *
from embroidery import export_svg_to_vp3
from helpers import generate_star
big_square = SVG(800,800)
# big square
# big_square.path([(M, 10, 10), (L, 10, 760), (L, 760, 760), (L, 760, 10), (L, 10, 10)])
squares = SVG(800,800)
squares.path([(M, 10, 300), (L, 110, 200),(L, 210, 100), (L, 310, 200), (L, 410, 300),(L,310, 400), (L, 210, 500),(L,110,400), (L, 10, 300)])
squares.path([(M, 210, 300),(L, 310,200), (L, 410, 100),(L,510,200), (L, 610, 300),(L, 510, 400), (L, 410, 500),(L,310,400), (L, 210, 300), (L, 210, 150), (L, 175, 200)])
star = generate_star(210, 300, 20)
star_inst = []
for (x,y) in star:
    star_inst.append((L, x, y))
print(star_inst)
line = SVG(800,800)
squares.path(star_inst)
line.path([(M,310, 100), (L, 310, 500)])
line.path([(M, 20,300), (L,600, 300)])

big_square.save("paths/swatches/jobs/big_square.svg")
squares.save("paths/swatches/jobs/squares.svg")
line.save("paths/swatches/jobs/line.svg")

export_svg_to_vp3(big_square, "paths/swatches/jobs/big_square.vp3")
export_svg_to_vp3(squares, "paths/swatches/jobs/squares.vp3")
export_svg_to_vp3(line, "paths/swatches/jobs/line.vp3")
# for i in range(6):
#     sq = SVG(800,800)
#     if i % 2 == 0:
#         # rotated square
#         width = sq.parts[0].instructions[1][2]-10
#         inst = [(L, 10+width/2, 10), (L, 10+width, 10+width/2), (L, 10+width/2, 10+width), (L, 10, 10+width/2)]
#     else: 
#         inst = [(L, 10+width/2, 10), (L, 10+width, 10+width/2), (L, 10+width/2, 10+width), (L, 10, 10+width/2)]
