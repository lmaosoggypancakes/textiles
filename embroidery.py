from svg import *
from helpers import generate_star
from pyembroidery import *
BASE_CONTENT  = """
import processing.embroider.*;
PEmbroiderGraphics E;

void setup() {
  size(650, 650); 
  E = new PEmbroiderGraphics(this, width, height);
  String outputFilePath = ("E:\\\\funny\\\\scary.vp3");
  E.setPath(outputFilePath); 
  
  
  E.stroke(5,10,1); 
  E.strokeWeight(0.5);
  E.hatchSpacing(1); 
  E.setStitch(30, 50, 0); 

  <CONTENT>

  E.optimize(); // slow, but good and very important
  E.visualize(true, true, true); // show jump stitches
  E.endDraw(); // write out the file
}

"""

def is_safe_path(path):
    """
    returns True if the distance between any 2 consecutive points on the graph >= the minimum threshold (around 10 units)
    """
    for i in range(1, len(path)):
        (xi,yi) = path[i-1]
        (xf,yf) = path[i]
        dx = abs(xf-xi)
        dy = abs(yf-yi)
        if math.sqrt(dx**2 + dy**2) < 10:
            return False
    return True
def export_svg_to_processing(svg: SVG, filename="") -> str:
    """
    Given an SVG file from svg.py, creates a valid Processing file for PEmbroider using basic line and circle commands.
    Reasoning: https://processing.org/reference/PShape.html
    > The loadShape() function supports SVG files created with Inkscape and Adobe Illustrator. It is not a full SVG implementation, but offers some straightforward support for handling vector data. 
    - define a scale 
    """
    content = ""
    for part in svg.parts:
        if isinstance(part, SVGPath):
            for i, (command, x2, y2) in enumerate(part.instructions):
                (_, x1, y1) = part.instructions[i-1]
                print(f"{(x1,y1)}<>{(x2,y2)}")
                if command == L:
                    content += f"E.line({x1}, {y1}, {x2}, {y2});\n"
        elif isinstance(part, SVGCircle):
            content += f"\tE.setStitch(5, 50, 0);\r\n\tE.circle({part.x},{part.y},{part.radius});\r\n\tE.setStitch(30, 50, 0);\r\n"

    file = BASE_CONTENT.replace("<CONTENT>", content)
    if filename != "":
        with open(filename, "w") as f:
            f.write(file)
    return file

def export_svg_to_vp3(svg: SVG, filename):
    pattern = EmbPattern()
    pattern.add_command(JUMP, 10, 10)
    pattern.add_command(JUMP, 10, svg.y - 10)
    pattern.add_command(JUMP, svg.x - 10, svg.y-10)
    pattern.add_command(JUMP, svg.x-10, 10)
    for part in svg.parts:
        # core units: 1/10 mm
        if isinstance(part, SVGPath):
            (_, x0, y0) = part.instructions[0]

            pattern.add_command(JUMP, x0, y0)
            start_star = generate_star(x0,y0, 15)
            for (x,y) in start_star:
                pattern.add_command(STITCH,x,y)
            for (_, x, y) in part.instructions:
                pattern.add_command(STITCH, x, y)

            (_, xf, yf) = part.instructions[-1]
            end_star = generate_star(xf,yf, 15)

            for (x,y) in end_star:
                pattern.add_command(STITCH,x,y)
        elif isinstance(part, SVGCircle):
            pass
    write_vp3(pattern, filename)