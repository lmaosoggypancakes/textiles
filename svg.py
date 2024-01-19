import os

M = "M"
L = "L"
BASE_STYLING = "<style>text {font: 5px sans-serif; fill: white;}</style>"
CLOSING = "</svg>"

class SVG:   
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.draw = ""
    def path(self, instructions):
        self.draw += "<path d='"
        for inst in instructions:
            #  inst is a tuple of (C, X, Y) where C is a command and x,y are positional arguments
            self.draw += f"{inst[0]} {inst[1]} {inst[2]} "
        self.draw +=  "' stroke='white' fill='transparent' />"
    def circle(self, x,y,radius,label=""):
        self.draw+= f"<circle cx='{x}' cy='{y}' r='{radius}' fill='red' />"
    
    def text(self, x, y, text):
        self.draw += f"<text x='{x}' y='{y}' class='small'>{text}</text>"
    def save(self, filename):
        with open(filename, "w") as file:
            file.write(str(self))
            file.close()
        return filename

    def __str__(self):
        return f"<svg width='{self.x}' height='{self.y}' xmlns='http://www.w3.org/2000/svg'>" + BASE_STYLING + self.draw + CLOSING