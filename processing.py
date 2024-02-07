from svg import *

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
def export_svg_to_processing(svg: SVG, filename="") -> str:
    """
    Given an SVG file from svg.py, creates a valid Processing file for PEmbroider using basic line and circle commands.
    Reasoning: https://processing.org/reference/PShape.html
    > The loadShape() function supports SVG files created with Inkscape and Adobe Illustrator. It is not a full SVG implementation, but offers some straightforward support for handling vector data. 
    """
    content = ""
    # calculate max_x and max_y
    max_x = float("-inf")
    max_y = float("-inf")
    for part in svg.parts:
        if isinstance(part, SVGPath):
            max_x_part = max(map(lambda i: i[1], part.instructions))
            max_y_part = max(map(lambda i: i[2], part.instructions))
            if max_x_part > max_x:
                max_x = max_x_part
            if max_y_part > max_y:
                max_y = max_y_part
    
    for part in svg.parts:
        if isinstance(part, SVGPath):
            for i, (command, x2, y2) in enumerate(part.instructions):
                (_, x1, y1) = part.instructions[i-1]
                print(f"{(x1,y1)}<>{(x2,y2)}")
                if command == L:
                    content += f"E.line({x1*600/max_x}, {y1*600/max_y}, {x2*600/max_x}, {y2*600/max_y});\n"
        elif isinstance(part, SVGCircle):
            content += f"E.setStitch(5, 50, 0);\r\nE.circle({part.x*600/max_x},{part.y*600/max_y},{part.radius*600/max_y}); E.setStitch(30, 50, 0);\r\n"

    file = BASE_CONTENT.replace("<CONTENT>", content)
    if filename != "":
        with open(filename) as f:
            f.write(file)
    return file