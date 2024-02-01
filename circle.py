import math 
from svg import *

def top(x):
    return math.sqrt(256 - x*x)

def bottom(x):
    return -1 * math.sqrt(256 - x*x)

svg = SVG(100,100)

x = 20
y = 20
instructions = [(M,x,y)]
i = -8
while i != 8:
    instructions.append((L,x+i,y+top(i)))
    i+=0.5


svg.path(instructions)

svg.save("circle.svg")