from typing import List, Union
import math
M = "M"
L = "L"
BASE_STYLING = "<style>text {font: 18px sans-serif; fill: green;}</style>"
CLOSING = "</svg>"

def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    else:
        return 0
    
class SVG:   
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.draw = ""
        self.parts: List[SVGCircle | SVGPath] = []

    def path(self, instructions, stroke='white'):
        self.draw += "<path d='"
        for inst in instructions:
            #  inst is a tuple of (C, X, Y) where C is a command and x,y are positional arguments
            self.draw += f"{inst[0]} {inst[1]} {inst[2]} "
        self.draw += f"' stroke='{stroke}' fill='transparent' />"
        self.parts.append(SVGPath(instructions, stroke))
    def circle(self, x,y,radius,fill):
        self.parts.append(SVGCircle(x,y,radius))
        self.draw+= f"<circle cx='{x}' cy='{y}' r='{radius}' fill='{fill}' stroke='red' />"
    
    def text(self, x, y, text):
        self.draw += f"<text x='{x}' y='{y}' class='small'>{text}</text>"
    def save(self, filename):
        with open(filename, "w") as file:
            file.write(str(self))
            file.close()
        return filename

    def __str__(self):
        return f"<svg width='{self.x}' height='{self.y}' xmlns='http://www.w3.org/2000/svg'>" + BASE_STYLING + self.draw + CLOSING
    
    @staticmethod
    def create_n_zigzag(one, two, n, zig_size=1, svg=None):
        """
        Given a diagonal from (x1,y1) <> (x2,y2), create an n-zigzag according to those diagonals.
        ref: https://www.desmos.com/calculator/b8tq1khfwd
        """
        (x1, y1) = one
        (x2, y2) = two
        dx = x2 - x1
        dy = y2 - y1
        step_x = dx/n
        step_y = dy/n
        angle = math.atan2(dy, dx)
        points = []
        # i hate this
        for i in range(n):
            if i % 3 == 0:
                # no zig or zag :3
                x = (x1) + (i * step_x) 
                y = (y1) + (i * step_y)
            elif i % 3 == 1:
                # zag
                x = (x1) + (i * step_x) - zig_size*math.sin(angle) * sign(dy)
                y = (y1) + (i * step_y) + zig_size*math.cos(angle)*sign(dx)
            else:
                # zig
                x = (x1) + (i * step_x) + zig_size**math.sin(angle) * sign(dy)
                y = (y1) + (i * step_y) - zig_size*math.cos(angle)*sign(dx)
            points.append((x,y))
        points.append((x2,y2))
        if not svg:
            m = max([x1,x2,y1,y2])
            svg = SVG(m+200,m+200)
        
        instructions = [(M, x1,y1)]
        for (x,y) in points:
            instructions.append((L, x,y))

        svg.path(instructions)

        return svg

    @staticmethod
    def parse(path):
        """
        TODO: Parses an SVG file given the path to the svg.
        """
        pass

    def image(self, x,y,width,height,filename):
         # can i do this
         with open(filename) as f:
            svg = f.read()
            svg = svg[0:5] + f"x='{x}' y='{y}' width='{width}' height='{height}' " + svg[5:] # assume svg[4] == ' '
            self.draw+=svg


class SVGPath:
    def __init__(self, instructions, stroke):
        self.instructions = instructions
        self.stroke = stroke

class SVGCircle:
    def __init__(self, x, y, radius) -> None:
        self.x = x
        self.y = y
        self.radius = radius